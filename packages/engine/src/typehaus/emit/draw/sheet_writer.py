"""Fixed-size sheet composer — paper presets, border + title block, TRUE printed scale.

``compose_sheet`` turns a drawing-IR :class:`Scene` into a real permit sheet: a fixed
paper size (11x17 ledger by default), a border, a title block, the drawing placed at an
exact architectural scale (the largest standard scale that fits the viewport), a graphic
scale bar, and an optional north arrow. ``sheet_chrome`` applies the same border + title
block to table pages that compose their own matplotlib figures.

The truth rule: the scale printed in the title block is the scale the sheet is actually
drawn at — ``SheetSpec.scale_note`` is a hint only. When no standard scale fits the
viewport, the drawing is fit-to-page and honestly labeled N.T.S.

``frame_for_scene`` is the same decision taken *ahead* of composing, so a caller that is
not the permit set — ``haus render --paper`` — can put a plan, elevation or section on the
same paper at the same true scale, and know which scale it got.

Rendering the IR stays in ``pdf_writer`` (imported read-only); this module only owns the
paper: where the viewport sits, what the data limits are, and what the chrome says. The
sizes themselves and the scale ladder live in ``paper.py`` and are re-exported here.
"""

from __future__ import annotations

import math
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from datetime import date
from typing import TYPE_CHECKING

from typehaus.emit.draw.paper import (
    ARCH_D,
    ARCH_SCALES,
    ENG_SCALES,
    FIT_LABEL,
    LEDGER,
    NTS_LABEL,
    PAPER_SUFFIX,
    PAPERS,
    PORTRAIT_LEDGER,
    fit_scale,
    paper_for,
    resolve_paper,
    scale_for_label,
    select_scale,
)
from typehaus.emit.draw.pdf_writer import (
    _apply_text_scale,
    _draw_underlays,
    _render_nodes,
    _scene_bounds,
)
from typehaus.emit.draw.scene import Frame, Scene
from typehaus.emit.draw.typography import NOTES_PT, wrap_columns_for

if TYPE_CHECKING:  # pragma: no cover — SheetSpec lives in sheets.py (which imports us)
    from typehaus.resolve.model import ResolvedModel

# The paper presets and the scale ladder moved to ``paper.py``; they are re-exported here
# because "the sheet writer owns the paper" is how every caller (and every test) already
# spells it, and a module split is not a reason to churn their imports.
__all__ = [
    "ARCH_D", "ARCH_SCALES", "ENG_SCALES", "FIT_LABEL", "LEDGER", "NTS_LABEL", "PAPERS",
    "PAPER_SUFFIX", "PORTRAIT_LEDGER", "compose_sheet", "fit_scale", "frame_for_scene",
    "paper_for", "resolve_paper", "scale_for_label", "schedule_sheet", "section",
    "select_scale", "set_paper", "sheet_chrome", "viewport_box",
]

_MARGIN = 0.25       # border inset from the paper edge, inches
#: Minimum title-block strip height, inches — what a four-cell strip needed. The block is
#: a full NCS one now (identity, preparer, revision block, seal box, issue status), so it
#: takes ``title_height(size)`` instead: proportional to the sheet, clamped between this and
#: ``_TITLE_H_MAX``. A fixed height cannot serve both papers — 1.9" of block is right on the
#: 24"-tall ARCH D deliverable and eats a fifth of an 11"-tall ledger review print.
_TITLE_H = 0.75
_TITLE_H_MAX = 1.90
#: Fraction of sheet height the block takes between those bounds.
_TITLE_H_FRACTION = 0.085


#: Width of the RIGHT-EDGE title block, paper inches, used on scene sheets.
#:
#: **Why there are two title-block geometries, and why that is not a smell.** A scene sheet
#: and a table page compete for different things. A plan's viewport is computed — it takes
#: whatever the chrome leaves — and on ARCH D catlin's foundation plan needs 21.4" of the
#: 22.25" available HEIGHT while using 22.2" of 35.3" of WIDTH. Height there is the scarce
#: resource and width is free: a full NCS title block as a bottom strip costs S-100 a whole
#: step of scale (3/16" to 1/8"), and the same block on the right edge costs nothing.
#:
#: A table page is the mirror. It lays its content out in FIGURE FRACTIONS across the full
#: width, with the bottom already reserved at 0.11 — so a right-edge block would run through
#: every schedule on the sheet while the bottom strip costs it nothing.
#:
#: Same cells, same content, placed where each sheet has room. ``_draw_chrome(edge=...)``
#: is the switch and ``viewport_box`` reserves to match.
TITLE_W = 2.60


def title_height(size: tuple[float, float]) -> float:
    """Title-block strip height for this paper, inches.

    Bounded below by what the identity cells need and above by what a PE seal wants
    (~2" of clear area). Schedule pages lay their content out from figure fraction 0.11,
    so the block must also stay under ``0.11 * height - _MARGIN`` — which the fraction
    does by construction: 0.085 + 0.25/height < 0.11 for every paper this set prints on.
    """
    return max(_TITLE_H, min(_TITLE_H_MAX, _TITLE_H_FRACTION * size[1]))
_VIEW_PAD = 0.10     # air between chrome and the drawing viewport, inches
_BAR_LANE = 0.30     # reserved strip below the viewport for the graphic scale bar
_NOTES_W = 3.4       # reserved right-hand notes panel width, inches
_NOTES_PT = NOTES_PT  # fixed notes lettering size, points (monospace)
_INK = "#1a1a1a"
# Shrink applied when nothing on the ladder fits and the drawing is fitted to the page, so
# linework and its lettering clear the border instead of touching it.
_FIT_PAD = 1.04

#: The paper the *set currently being written* is on. A schedule page composes its own
#: matplotlib figure inside ``schedules/`` and names a preset there, which is the right
#: place for "this sheet is portrait" and the wrong place for "this set is 24x36". The set
#: writer parks its paper here (``set_paper``) and ``schedule_sheet`` resolves the two: the
#: caller's size decides the *orientation*, this decides the *size*.
_SET_PAPER: ContextVar[tuple[float, float]] = ContextVar("_SET_PAPER", default=LEDGER)


@contextmanager
def set_paper(paper: tuple[float, float]) -> Iterator[None]:
    """Make ``paper`` the paper every ``schedule_sheet`` in this block composes onto."""
    token = _SET_PAPER.set(paper)
    try:
        yield
    finally:
        _SET_PAPER.reset(token)


#: What the set currently being written may be used for. Every sheet carries it, and the
#: default is the honest one: this engine computes, it does not seal. ``haus print``
#: overrides it only when its own gate passes — the same gate that decides whether the set
#: may be printed at all, so the stamp and the gate cannot disagree.
NOT_FOR_CONSTRUCTION = "NOT FOR CONSTRUCTION"
FOR_PLAN_CHECK = "FOR PLAN CHECK ONLY"
_ISSUE: ContextVar[str] = ContextVar("_ISSUE", default=NOT_FOR_CONSTRUCTION)


@contextmanager
def set_issue_status(status: str) -> Iterator[None]:
    """Stamp ``status`` on every sheet composed in this block."""
    token = _ISSUE.set(status)
    try:
        yield
    finally:
        _ISSUE.reset(token)


#: Stamp ink. Red is a warning, and it belongs only on the engine's own two defaults —
#: they say the set may not be built from. A house that authored ``[print] issue`` has
#: made an affirmative statement about its own set, and printing that in alarm ink would
#: contradict it.
_ISSUE_WARNING_INK = "#8a1c1c"
_ISSUE_INK = "#1a1a1a"


def _issue_color(status: str) -> str:
    return (_ISSUE_WARNING_INK if status.split(" · ")[0]
            in (NOT_FOR_CONSTRUCTION, FOR_PLAN_CHECK) else _ISSUE_INK)


def viewport_box(size: tuple[float, float], notes_panel: bool = False,
                 ) -> tuple[float, float, float, float]:
    """(x, y, w, h) of the drawing viewport in paper inches: sheet minus chrome.

    A ``_BAR_LANE`` strip below the viewport is reserved for the graphic scale bar, so
    the bar never sits on top of scene content (legends and dimension strings routinely
    occupy a drawing's bottom-left corner).
    """
    width, height = size
    x = _MARGIN + _VIEW_PAD
    # No title strip along the bottom on a scene sheet — the block is on the right edge
    # (``TITLE_W``), where this sheet has room to spare. Only the scale-bar lane is here.
    y = _MARGIN + _VIEW_PAD + _BAR_LANE
    w = width - _MARGIN - _VIEW_PAD - x - TITLE_W - _VIEW_PAD
    h = height - _MARGIN - _VIEW_PAD - y
    if notes_panel:
        w -= _NOTES_W + _VIEW_PAD
    return (x, y, w, h)


def frame_for_scene(scene: Scene, size: tuple[float, float] = LEDGER, *,
                    scale_label: str | None = None) -> Frame | None:
    """The paper a plan/elevation/section lands on, decided before anything is drawn.

    ``compose_sheet`` already made this decision internally for the permit set. Pulling it
    out means a caller can ask *which* scale a sheet got without composing it, and can
    force one: ``scale_label`` takes an ``ARCH_SCALES``/``ENG_SCALES`` label, or ``"fit"``
    to fill the viewport under an honest N.T.S. A forced scale larger than fits is
    honoured and overflows — that is what asking for it means, and the alternative
    (silently substituting a smaller one) is the lie the truth rule exists to prevent.

    ``None`` when the scene has no measurable geometry: there is nothing to place, so the
    frameless fit stays the right answer and the caller keeps it.
    """
    bounds = _scene_bounds(scene)
    if bounds is None:
        return None
    view = viewport_box(size, notes_panel=bool(_scene_note_lines(scene)))
    u0, z0, u1, z1 = bounds
    span_u, span_z = max(u1 - u0, 1e-6), max(z1 - z0, 1e-6)
    if scale_label is None:
        scale, label = select_scale(span_u, span_z, view[2], view[3])
    elif "".join(scale_label.split()).lower() == FIT_LABEL:
        scale, label = None, NTS_LABEL
    else:
        entry = scale_for_label(scale_label)
        if entry is None:
            raise ValueError(f"unknown scale {scale_label!r} — expected one of "
                             f"{', '.join(name for _s, name in ARCH_SCALES)}, "
                             f"{', '.join(name for _s, name in ENG_SCALES)}, or "
                             f"{FIT_LABEL!r}")
        scale, label = entry
    if scale is None:
        scale, label = fit_scale(span_u, span_z, view[2], view[3], _FIT_PAD), NTS_LABEL
    return Frame(paper=size, viewport=view, center=((u0 + u1) / 2.0, (z0 + z1) / 2.0),
                 scale=scale, scale_label=label)


def compose_sheet(scene: Scene, spec: object, model: ResolvedModel,
                  size: tuple[float, float] | None = None, underlays=()):
    """Compose one Scene onto a fixed-size sheet at true printed scale.

    ``spec`` is duck-typed (``sheets.SheetSpec``): ``number``/``title`` are required,
    ``size`` and ``north_arrow`` are honoured when present. Returns the Figure; the
    caller saves and closes it.

    ``underlays`` are reference rasters drawn behind the linework, and they exist for the
    ``haus render`` snapshot loop only — ``write_permit_set`` never passes any, because a
    survey drawing is reference material and must not print on a permit sheet
    (→ 30 §Scaled underlays).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    size = size or getattr(spec, "size", None) or LEDGER
    fig = plt.figure(figsize=size)
    notes = _scene_note_lines(scene)
    view = viewport_box(size, notes_panel=bool(notes))
    ax = fig.add_axes([view[0] / size[0], view[1] / size[1],
                       view[2] / size[0], view[3] / size[1]])
    ax.axis("off")
    if underlays:
        _draw_underlays(ax, underlays)

    # A scene that arrived with its own Frame keeps it — a detail card chose its paper
    # before it was cut, and re-choosing here would print one scale over a drawing laid
    # out at another. Everything else gets the same decision made now, from the same
    # viewport and the same ladder.
    #
    # THE FRAME IS DECIDED BEFORE THE NODES ARE DRAWN, and the order is load-bearing. Every
    # scale-dependent decision the writer makes — the plan poché, and ``_band_linewidth``'s
    # cap on a band's outline — reads ``scene.frame``, so with the frame computed *after*
    # ``_render_nodes`` the only scenes that ever saw a scale were the detail cards that
    # brought their own. Neither fired on a single plan, elevation or section sheet in the
    # permit set. The scene the nodes are drawn from therefore carries the frame.
    frame = scene.frame if scene.frame is not None else frame_for_scene(scene, size)
    if frame is not None and scene.frame is None:
        scene = scene.model_copy(update={"frame": frame})
    scaled_text = _render_nodes(ax, scene)
    scale_label = NTS_LABEL
    if frame is None:  # nothing measurable on the sheet — nothing to scale
        ax.set_aspect("equal")
        ax.autoscale_view()
    else:
        scale_label = frame.scale_label
        per_paper_in = 12.0 / frame.scale  # model inches per sheet inch — exact
        cu, cz = frame.center
        ax.set_xlim(cu - view[2] * per_paper_in / 2.0, cu + view[2] * per_paper_in / 2.0)
        ax.set_ylim(cz - view[3] * per_paper_in / 2.0, cz + view[3] * per_paper_in / 2.0)
        ax.set_aspect("equal", adjustable="box")
        # The bar is drawn even under N.T.S., which is the one case it is indispensable:
        # a reader who cannot name the scale can still measure against a bar that was
        # plotted at the scale the drawing actually got.
        _draw_scale_bar(fig, frame.scale, scale_label, view, size)

    # Text artists default to clip_on=False; a label whose extent the bounds estimator
    # undershot would otherwise print across the border and title block.
    for artist in ax.texts:
        artist.set_clip_on(True)

    if getattr(spec, "north_arrow", False):
        _draw_north_arrow(fig, model, view, size)
    if notes:
        _draw_notes_panel(fig, notes, view, size)
    _draw_chrome(fig, model, getattr(spec, "number", ""), getattr(spec, "title", ""),
                 scale_label, size, edge=True)
    _apply_text_scale(fig, ax, scaled_text)
    return fig


@contextmanager
def schedule_sheet(pdf, model: ResolvedModel, number: str, name: str, *,
                   size: tuple[float, float] = LEDGER,
                   heading: str | None = None,
                   heading_xy: tuple[float, float] = (0.04, 0.945)) -> Iterator:
    """Open a table page, hand back the figure, then chrome/save/close it.

    Every ``_write_*`` schedule repeated the same six lines — create the figure at the
    paper preset, letter the sheet number, draw the body, apply ``sheet_chrome``, save,
    close. Two of them silently dropped the chrome call *and* passed a portrait figsize
    to a landscape preset, shipping two untitled sheets in the wrong orientation. Making
    the envelope a context manager makes that omission unrepresentable: the size the
    figure is opened at is the size the chrome is drawn at, by construction.

    ``heading`` defaults to ``"{number} · {name}"``; pass ``""`` for a page that letters
    its own title (the cover), or an explicit string to override it.

    ``size`` names a *preset*, and by the time it gets here only its orientation still
    matters: the set writer has parked the paper the whole set is printing on in
    ``set_paper``, and the two are resolved by ``paper_for``. That is what lets E-602 stay
    portrait on 24x36 without every schedule writer growing a paper argument.
    """
    import matplotlib.pyplot as plt

    size = paper_for(_SET_PAPER.get(), portrait=size[1] > size[0])
    fig = plt.figure(figsize=size)
    if heading is None:
        heading = f"{number} · {name}"
    if heading:
        fig.text(*heading_xy, heading, fontsize=16, family="monospace")
    try:
        yield fig
    except BaseException:
        plt.close(fig)
        raise
    sheet_chrome(fig, model, number, name, size=size)
    pdf.savefig(fig)
    plt.close(fig)


def section(fig, x: float, y: float, title: str, *, fontsize: float = 10, **kwargs):
    """A block header on a table page — bold monospace, one call rather than four kwargs.

    Repeated 23 times across the schedules with the styling spelled out each time, which
    is how the lettering drifted between sheets.
    """
    return fig.text(x, y, title, fontsize=fontsize, family="monospace", weight="bold",
                    **kwargs)


def content_box(size: tuple[float, float]) -> tuple[float, float, float, float]:
    """The area a table page may letter into: ``(x0, y0, x1, y1)`` in paper inches.

    :func:`sheet_chrome` states this bound in its docstring as "above ~0.10 on ledger" and
    every schedule writer then hard-codes figure *fractions* against it. A fraction is the
    wrong unit for a bound that is really the border plus the title strip — both fixed
    inches — so a layout tuned on 11x17 either crashes into the title block or floats a
    long way above it when the same page is composed on 24x36. Returning inches lets a page
    ask how much room it actually has, which is what the cover's sheet index needs in order
    to choose a column count instead of silently drawing rows off the edge.

    The extra ``_GUTTER`` inside the border is breathing room, not structure: lettering
    hard against a drawn border reads as an error even when it is inside it.
    """
    width, height = size
    return (_MARGIN + _GUTTER, _MARGIN + title_height(size) + _GUTTER,
            width - _MARGIN - _GUTTER, height - _MARGIN - _GUTTER)


#: Clear space between the drawn border and any lettering, inches.
_GUTTER = 0.35


def sheet_chrome(fig, model: ResolvedModel, number: str, title: str,
                 scale_label: str = NTS_LABEL,
                 size: tuple[float, float] = LEDGER) -> None:
    """Normalize an existing figure to the paper preset and draw border + title block.

    For table/cover pages that lay out their own matplotlib content: they keep their
    figure, gain the same paper identity as the scene sheets. Content must stay above
    ``y ≈ (margin + title strip) / height`` — in figure fraction, above ~0.10 on ledger.
    """
    fig.set_size_inches(*size, forward=True)
    _draw_chrome(fig, model, number, title, scale_label, size)


# --- chrome -------------------------------------------------------------------


def _draw_chrome(fig, model: ResolvedModel, number: str, title: str,
                 scale_label: str, size: tuple[float, float], *,
                 edge: bool = False) -> None:
    """Border rectangle + title block, drawn in paper-inch coordinates.

    ``edge`` puts the block down the right-hand side (scene sheets, where height is the
    scarce resource) instead of along the bottom (table pages, where width is). See
    :data:`TITLE_W` for the measurement behind that split.
    """
    from matplotlib.patches import Rectangle

    width, height = size
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], zorder=5)
    ax.set_xlim(0.0, width)
    ax.set_ylim(0.0, height)
    ax.axis("off")
    ax.patch.set_visible(False)

    m = _MARGIN
    ax.add_patch(Rectangle((m, m), width - 2 * m, height - 2 * m, fill=False,
                           edgecolor=_INK, linewidth=1.2))
    pad = 0.10

    # Six cells: identity · site · preparer + issue · revisions · seal · sheet. The order is
    # the reading order of a title block — who and where, then who drew it and what it may
    # be used for, then what changed, then who is answerable, then which sheet this is. The
    # sheet number is LAST because it is what a reader's thumb finds on the corner of a
    # stack, which on the right-edge block means the bottom of the column.
    #
    # Proportions are what each cell has to SAY, measured off the printed sheet rather than
    # split evenly: identity is a name and up to two address lines, the revision block needs
    # room for a description, and the seal box wants to be nearly square.
    fractions = (0.18, 0.32, 0.52, 0.76, 0.87)
    if edge:
        block_x0 = width - m - TITLE_W
        strip_h = height - 2 * m
        ax.plot([block_x0, block_x0], [m, height - m], color=_INK, linewidth=0.9)
        # Bottom-to-top: the sheet number sits at the bottom corner, so the cell order is
        # reversed against the fractions, which run "first cell first".
        cuts = [height - m - (height - 2 * m) * f for f in fractions]
        for y in cuts:
            ax.plot([block_x0, width - m], [y, y], color=_INK, linewidth=0.5)
        tops = [height - m, *cuts]
        bottoms = [*cuts, m]
        cells = [(block_x0, block_x0 + TITLE_W, top, bottom)
                 for top, bottom in zip(tops, bottoms, strict=True)]
    else:
        strip_h = title_height(size)
        strip_top = m + strip_h
        inner_w = width - 2 * m
        ax.plot([m, width - m], [strip_top, strip_top], color=_INK, linewidth=0.9)
        dividers = [m + inner_w * f for f in fractions]
        for x in dividers:
            ax.plot([x, x], [m, strip_top], color=_INK, linewidth=0.5)
        lefts = [m, *dividers]
        rights = [*dividers, width - m]
        cells = [(left, right, strip_top, m)
                 for left, right in zip(lefts, rights, strict=True)]

    edges = [cell[0] for cell in cells] + [cells[-1][1]]

    def rows(count: int, index: int = 0) -> list[float]:
        """``count`` evenly spaced text baselines down cell ``index``, top row first."""
        top, bottom = cells[index][2], cells[index][3]
        span = top - bottom
        step = span / (count + 0.6)
        return [top - step * (i + 0.8) for i in range(count)]

    def label(x: float, y: float, text: str, size_pt: float = 6.0,
              weight: str = "normal", color: str = _INK) -> None:
        ax.text(x, y, text, fontsize=size_pt, family="monospace", va="center",
                color=color, weight=weight)

    project = getattr(getattr(model, "plan", None), "project", None)
    site = getattr(project, "site", None)

    # --- cell 1: project identity and address -------------------------------------
    r = rows(4, 0)
    name = getattr(project, "name", "") or ""
    if name:
        label(edges[0] + pad, r[0], name, 10.5, "bold")
    address = _project_address(project, site)
    for row, line in zip(r[1:3], address, strict=False):
        label(edges[0] + pad, row, line, 6.5)
    label(edges[0] + pad, r[3], "TYPE:HAUS — generated construction set", 5.5,
          color="#555555")

    # --- cell 2: where on earth ----------------------------------------------------
    # Deliberately ragged: any row may be absent (no lat/lon, no CRS, no elevation), so a
    # shorter list simply fills the cell from the top rather than leaving labelled blanks.
    site_rows: list[str] = []
    lat, lon = getattr(site, "lat", None), getattr(site, "lon", None)
    if lat is not None and lon is not None:
        site_rows.append(f"SITE  {lat:.5f}, {lon:.5f}")
    crs = getattr(site, "crs", None)
    if crs:
        site_rows.append(f"CRS   {crs}")
    elevation = getattr(site, "elevation", None)
    if elevation is not None:
        with suppress(AttributeError):
            site_rows.append(f"ELEV  {elevation.meters:,.1f} m")
    for row, text in zip(rows(4, 1), site_rows, strict=False):
        label(edges[1] + pad, row, text, 6.0)

    # --- cell 3: preparer, project number, scale, date, and the issue stamp ---------
    r = rows(5, 2)
    label(edges[2] + pad, r[0], f"PROJECT NO  {_project_number(project)}", 6.0)
    label(edges[2] + pad, r[1], f"DRAWN BY    {_preparer(project)}", 6.0)
    # CHECKED BY is blank because nobody has checked it. A pre-filled name on a line whose
    # whole purpose is to record a human act would be a forgery of that act — the same
    # reasoning that keeps the seal box empty.
    label(edges[2] + pad, r[2], "CHECKED BY  ______________", 6.0)
    label(edges[2] + pad, r[3], f"SCALE  {scale_label}      "
                                f"DATE  {date.today().isoformat()}", 6.0)
    label(edges[2] + pad, r[4], _ISSUE.get(), 7.5, "bold", _issue_color(_ISSUE.get()))

    # --- cell 4: the revision block ------------------------------------------------
    # A real block with ruled rows and a header, empty. It replaces a hard-coded "REV —",
    # which said there is no revision system rather than that there are no revisions yet.
    # The engine cannot fill it: a revision is an issue to somebody, which is a human act.
    r = rows(4, 3)
    label(edges[3] + pad, r[0], "REV  DATE        DESCRIPTION", 5.5, "bold")
    for row in r[1:]:
        ax.plot([cells[3][0] + pad, cells[3][1] - pad], [row - 0.055, row - 0.055],
                color="#999999", linewidth=0.3)

    # --- cell 5: the seal box ------------------------------------------------------
    # An outlined reserved area and a caption, and the engine still never DRAWS a stamp.
    # ``schedules/structural.py`` puts it plainly: drawing a stamp would be forging one.
    seal_l, seal_r, seal_top, seal_bot = cells[4]
    box_x0, box_x1 = seal_l + pad, seal_r - pad
    ax.add_patch(Rectangle((box_x0, seal_bot + pad), box_x1 - box_x0,
                           (seal_top - seal_bot) - 2 * pad,
                           fill=False, edgecolor="#999999", linewidth=0.4,
                           linestyle=(0, (3, 2))))
    ax.text((box_x0 + box_x1) / 2.0, (seal_top + seal_bot) / 2.0, "SEAL", fontsize=6.0,
            family="monospace", va="center", ha="center", color="#999999")

    # --- cell 6: sheet number and title --------------------------------------------
    r = rows(3, 5)
    label(edges[5] + pad, r[0], number, 13.0, "bold")
    # The cell is as wide as the paper made it, so that — not a constant — is the limit.
    # A fixed 46 was a ledger number: it clipped a title at the same place on 24x36, where
    # this cell is more than twice as wide and had the room to print it whole.
    columns = wrap_columns_for(cells[5][1] - cells[5][0] - 2 * pad, 6.5)
    label(edges[5] + pad, r[2], _shorten(title, columns), 6.5)


def _project_address(project, site) -> list[str]:
    """Up to two lines of street address, or ``[]``.

    A permit set names the property it is for. Nothing here is invented: an address the
    model does not carry prints as nothing at all, because a plausible-looking address on a
    permit drawing is worse than a missing one.
    """
    for holder in (project, site):
        text = getattr(holder, "address", None)
        if text:
            return [line.strip() for line in str(text).splitlines() if line.strip()][:2]
    return []


def _project_number(project) -> str:
    """The project number a reviewer files the set under.

    Falls back to the first eight characters of ``project_uuid``, which is stable, unique
    and already in the model — a set with no number at all cannot be filed.
    """
    number = getattr(project, "number", None)
    if number:
        return str(number)
    uuid = str(getattr(project, "project_uuid", "") or "")
    return uuid[:8].upper() if uuid else "—"


def _preparer(project) -> str:
    """Who prepared the set. The engine did, unless the project names somebody."""
    for field in ("preparer", "firm", "architect"):
        value = getattr(project, field, None)
        if value:
            return str(value)[:16]
    return "TYPE:HAUS"


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --- graphic scale bar --------------------------------------------------------

# Candidate segment lengths in feet; a bar is 4 alternating segments.
_SEGMENT_FT = (50.0, 20.0, 10.0, 5.0, 4.0, 2.0, 1.0, 0.5, 0.25)
_BAR_SEGMENTS = 4


def _draw_scale_bar(fig, scale_in_per_ft: float, scale_label: str,
                    view: tuple[float, float, float, float],
                    size: tuple[float, float]) -> None:
    """Alternating filled/open graphic scale in the reserved lane below the viewport.

    Drawn in paper inches, so a segment of ``f`` feet is exactly ``f * scale`` sheet
    inches long — a reader with a ruler can check the sheet against the bar directly.
    Living in the chrome lane (not the viewport) means it can never sit on top of scene
    content.
    """
    from matplotlib.patches import Rectangle

    # Budget ~30% of the viewport width for the whole bar.
    budget_ft = view[2] / scale_in_per_ft * 0.30
    segment_ft = next((s for s in _SEGMENT_FT if s * _BAR_SEGMENTS <= budget_ft),
                      _SEGMENT_FT[-1])
    seg_w = segment_ft * scale_in_per_ft              # paper inches per segment
    bar_h = 0.10
    bx = view[0]
    by = view[1] - _BAR_LANE + 0.11                   # inside the reserved lane

    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], zorder=4)
    ax.set_xlim(0.0, size[0])
    ax.set_ylim(0.0, size[1])
    ax.axis("off")
    ax.patch.set_visible(False)
    for i in range(_BAR_SEGMENTS):
        ax.add_patch(Rectangle((bx + i * seg_w, by), seg_w, bar_h,
                               facecolor=_INK if i % 2 == 0 else "white",
                               edgecolor=_INK, linewidth=0.6))
    for i in range(_BAR_SEGMENTS + 1):
        ax.text(bx + i * seg_w, by - 0.03, _ft_label(i * segment_ft), fontsize=5.5,
                family="monospace", ha="center", va="top", color=_INK)
    ax.text(bx + _BAR_SEGMENTS * seg_w + 0.15, by + bar_h / 2.0,
            f"SCALE {scale_label}", fontsize=6, family="monospace", ha="left",
            va="center", color=_INK)


def _ft_label(feet: float) -> str:
    if feet == 0:
        return "0"
    if feet < 1.0 or feet != int(feet):
        return f"{feet * 12:g}\""
    return f"{int(feet)}'"


# --- north arrow --------------------------------------------------------------


def _draw_north_arrow(fig, model: ResolvedModel, view, size) -> None:
    """A circled north arrow, top-right inside the viewport, rotated by true north.

    Same convention as the site plan's authored arrow (``siteplan._emit_north_arrow``):
    direction ``(sin θ, cos θ)`` with θ = ``site.true_north``, so project-north pages and
    the site plan agree on where north points. Drawn as sheet furniture (its own small
    axes) rather than an IR Symbol — ``pdf_writer`` has no "north-arrow" glyph and an
    unknown symbol name falls through to the window-glass bar.
    """
    diameter = 0.55  # paper inches
    x = view[0] + view[2] - diameter - 0.12
    y = view[1] + view[3] - diameter - 0.12
    ax = fig.add_axes([x / size[0], y / size[1], diameter / size[0], diameter / size[1]],
                      zorder=6)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_visible(False)
    try:
        radians = model.plan.project.site.true_north.radians
    except AttributeError:
        radians = 0.0
    dx, dy = math.sin(radians), math.cos(radians)
    from matplotlib.patches import Circle

    ax.add_patch(Circle((0.0, 0.0), 1.0, fill=False, edgecolor="#204070", linewidth=0.8))
    ax.annotate("", xy=(dx * 0.82, dy * 0.82), xytext=(-dx * 0.55, -dy * 0.55),
                arrowprops=dict(arrowstyle="-|>", color="#204070", lw=1.2))
    ax.text(dx * 1.30, dy * 1.30, "N", fontsize=8, family="monospace", ha="center",
            va="center", color="#204070", weight="bold")


# --- notes panel --------------------------------------------------------------

def _scene_note_lines(scene: Scene) -> list[str]:
    """Wrapped lines for ``Scene.notes`` (str or iterable of str); [] when absent.

    Scene-level notes are optional sheet text authored beside the drawing; the composer
    reserves a right-hand panel for them at fixed lettering size rather than letting them
    inflate the drawing's model-space bounds.

    The wrap width is computed from ``_NOTES_W`` and ``NOTES_PT`` rather than being the
    hand-tuned 40 it was, so the panel's width and the column it wraps to cannot drift
    apart — the same ``wrap_columns_for`` the card path uses.
    """
    notes = getattr(scene, "notes", None)
    if not notes:
        return []
    columns = wrap_columns_for(_NOTES_W, NOTES_PT)
    blocks = [notes] if isinstance(notes, str) else list(notes)
    lines: list[str] = []
    for block in blocks:
        for raw in str(block).splitlines():
            stripped = raw.strip()
            if not stripped:
                lines.append("")
                continue
            indent = "  " if stripped.startswith("• ") else ""
            lines.extend(textwrap.wrap(stripped, width=columns,
                                       subsequent_indent=indent) or [stripped])
    return lines


def _draw_notes_panel(fig, lines: list[str], view, size) -> None:
    x_in = view[0] + view[2] + _VIEW_PAD
    top_in = view[1] + view[3] - 0.10
    step_in = _NOTES_PT * 1.5 / 72.0
    x = x_in / size[0]
    fig.text(x, top_in / size[1], "NOTES", fontsize=_NOTES_PT, family="monospace",
             va="top", weight="bold", color=_INK)
    y_in = top_in - 2.0 * step_in
    for line in lines:
        if y_in <= _MARGIN + title_height(size) + 0.1:
            fig.text(x, y_in / size[1], "…", fontsize=_NOTES_PT, family="monospace",
                     va="top", color=_INK)
            break
        fig.text(x, y_in / size[1], line, fontsize=_NOTES_PT, family="monospace",
                 va="top", color=_INK)
        y_in -= step_in
