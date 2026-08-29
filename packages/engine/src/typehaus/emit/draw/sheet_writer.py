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
from contextlib import contextmanager
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
_TITLE_H = 0.75      # title-block strip height above the bottom border line, inches
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
_SET_PAPER: "ContextVar[tuple[float, float]]" = ContextVar("_SET_PAPER", default=LEDGER)


@contextmanager
def set_paper(paper: "tuple[float, float]") -> "Iterator[None]":
    """Make ``paper`` the paper every ``schedule_sheet`` in this block composes onto."""
    token = _SET_PAPER.set(paper)
    try:
        yield
    finally:
        _SET_PAPER.reset(token)


def viewport_box(size: "tuple[float, float]", notes_panel: bool = False,
                 ) -> "tuple[float, float, float, float]":
    """(x, y, w, h) of the drawing viewport in paper inches: sheet minus chrome.

    A ``_BAR_LANE`` strip below the viewport is reserved for the graphic scale bar, so
    the bar never sits on top of scene content (legends and dimension strings routinely
    occupy a drawing's bottom-left corner).
    """
    width, height = size
    x = _MARGIN + _VIEW_PAD
    y = _MARGIN + _TITLE_H + _VIEW_PAD + _BAR_LANE
    w = width - _MARGIN - _VIEW_PAD - x
    h = height - _MARGIN - _VIEW_PAD - y
    if notes_panel:
        w -= _NOTES_W + _VIEW_PAD
    return (x, y, w, h)


def frame_for_scene(scene: Scene, size: "tuple[float, float]" = LEDGER, *,
                    scale_label: "str | None" = None) -> "Frame | None":
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


def compose_sheet(scene: Scene, spec: object, model: "ResolvedModel",
                  size: "tuple[float, float] | None" = None, underlays=()):
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
                 scale_label, size)
    _apply_text_scale(fig, ax, scaled_text)
    return fig


@contextmanager
def schedule_sheet(pdf, model: "ResolvedModel", number: str, name: str, *,
                   size: "tuple[float, float]" = LEDGER,
                   heading: "str | None" = None,
                   heading_xy: "tuple[float, float]" = (0.04, 0.945)) -> "Iterator":
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
    return (_MARGIN + _GUTTER, _MARGIN + _TITLE_H + _GUTTER,
            width - _MARGIN - _GUTTER, height - _MARGIN - _GUTTER)


#: Clear space between the drawn border and any lettering, inches.
_GUTTER = 0.35


def sheet_chrome(fig, model: "ResolvedModel", number: str, title: str,
                 scale_label: str = NTS_LABEL,
                 size: "tuple[float, float]" = LEDGER) -> None:
    """Normalize an existing figure to the paper preset and draw border + title block.

    For table/cover pages that lay out their own matplotlib content: they keep their
    figure, gain the same paper identity as the scene sheets. Content must stay above
    ``y ≈ (margin + title strip) / height`` — in figure fraction, above ~0.10 on ledger.
    """
    fig.set_size_inches(*size, forward=True)
    _draw_chrome(fig, model, number, title, scale_label, size)


# --- chrome -------------------------------------------------------------------


def _draw_chrome(fig, model: "ResolvedModel", number: str, title: str,
                 scale_label: str, size: "tuple[float, float]") -> None:
    """Border rectangle + bottom title-block strip, drawn in paper-inch coordinates."""
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
    strip_top = m + _TITLE_H
    ax.plot([m, width - m], [strip_top, strip_top], color=_INK, linewidth=0.9)
    inner_w = width - 2 * m
    dividers = [m + inner_w * f for f in (0.36, 0.60, 0.78)]
    for x in dividers:
        ax.plot([x, x], [m, strip_top], color=_INK, linewidth=0.5)

    top_y = strip_top - 0.16    # first text row baseline
    mid_y = strip_top - 0.40
    low_y = strip_top - 0.62
    pad = 0.10

    # Cell 1 — project identity.
    project = getattr(getattr(model, "plan", None), "project", None)
    name = getattr(project, "name", "") or ""
    if name:
        ax.text(m + pad, top_y, name, fontsize=11, family="monospace", va="center",
                color=_INK, weight="bold")
    ax.text(m + pad, low_y, "TYPE:HAUS — generated construction set", fontsize=6,
            family="monospace", va="center", color="#555555")

    # Cell 2 — site rows; omit anything the model does not carry.
    site = getattr(project, "site", None)
    site_rows = []
    lat, lon = getattr(site, "lat", None), getattr(site, "lon", None)
    if lat is not None and lon is not None:
        site_rows.append(f"SITE  {lat:.5f}, {lon:.5f}")
    crs = getattr(site, "crs", None)
    if crs:
        site_rows.append(f"CRS   {crs}")
    elevation = getattr(site, "elevation", None)
    if elevation is not None:
        try:
            site_rows.append(f"ELEV  {elevation.meters:,.1f} m")
        except AttributeError:
            pass
    for row, text in zip((top_y, mid_y, low_y), site_rows):
        ax.text(dividers[0] + pad, row, text, fontsize=6.5, family="monospace",
                va="center", color=_INK)

    # Cell 3 — scale / date / revision.
    ax.text(dividers[1] + pad, top_y, f"SCALE {scale_label}", fontsize=7,
            family="monospace", va="center", color=_INK)
    ax.text(dividers[1] + pad, mid_y, f"DATE  {date.today().isoformat()}", fontsize=7,
            family="monospace", va="center", color=_INK)
    ax.text(dividers[1] + pad, low_y, "REV   —", fontsize=7, family="monospace",
            va="center", color=_INK)

    # Cell 4 — sheet number + title.
    ax.text(dividers[2] + pad, top_y, number, fontsize=13, family="monospace",
            va="center", color=_INK, weight="bold")
    # The cell is as wide as the paper made it, so that — not a constant — is the limit.
    # A fixed 46 was a ledger number: it clipped a title at the same place on 24x36, where
    # cell 4 is more than twice as wide and had the room to print it whole.
    ax.text(dividers[2] + pad, low_y + 0.08,
            _shorten(title, wrap_columns_for(width - m - pad - dividers[2] - pad, 6.5)),
            fontsize=6.5, family="monospace", va="center", color=_INK)


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --- graphic scale bar --------------------------------------------------------

# Candidate segment lengths in feet; a bar is 4 alternating segments.
_SEGMENT_FT = (50.0, 20.0, 10.0, 5.0, 4.0, 2.0, 1.0, 0.5, 0.25)
_BAR_SEGMENTS = 4


def _draw_scale_bar(fig, scale_in_per_ft: float, scale_label: str,
                    view: "tuple[float, float, float, float]",
                    size: "tuple[float, float]") -> None:
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


def _draw_north_arrow(fig, model: "ResolvedModel", view, size) -> None:
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

def _scene_note_lines(scene: Scene) -> "list[str]":
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
    lines: "list[str]" = []
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


def _draw_notes_panel(fig, lines: "list[str]", view, size) -> None:
    x_in = view[0] + view[2] + _VIEW_PAD
    top_in = view[1] + view[3] - 0.10
    step_in = _NOTES_PT * 1.5 / 72.0
    x = x_in / size[0]
    fig.text(x, top_in / size[1], "NOTES", fontsize=_NOTES_PT, family="monospace",
             va="top", weight="bold", color=_INK)
    y_in = top_in - 2.0 * step_in
    for line in lines:
        if y_in <= _MARGIN + _TITLE_H + 0.1:
            fig.text(x, y_in / size[1], "…", fontsize=_NOTES_PT, family="monospace",
                     va="top", color=_INK)
            break
        fig.text(x, y_in / size[1], line, fontsize=_NOTES_PT, family="monospace",
                 va="top", color=_INK)
        y_in -= step_in
