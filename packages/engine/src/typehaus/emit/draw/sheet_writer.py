"""Fixed-size sheet composer — paper presets, border + title block, TRUE printed scale.

``compose_sheet`` turns a drawing-IR :class:`Scene` into a real permit sheet: a fixed
paper size (11x17 ledger by default), a border, a title block, the drawing placed at an
exact architectural scale (the largest standard scale that fits the viewport), a graphic
scale bar, and an optional north arrow. ``sheet_chrome`` applies the same border + title
block to table pages that compose their own matplotlib figures.

The truth rule: the scale printed in the title block is the scale the sheet is actually
drawn at — ``SheetSpec.scale_note`` is a hint only. When no standard scale fits the
viewport, the drawing is fit-to-page and honestly labeled N.T.S.

Rendering the IR stays in ``pdf_writer`` (imported read-only); this module only owns the
paper: where the viewport sits, what the data limits are, and what the chrome says.
"""

from __future__ import annotations

import math
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import TYPE_CHECKING

from typehaus.emit.draw.pdf_writer import _apply_text_scale, _render_nodes, _scene_bounds
from typehaus.emit.draw.scene import Scene

if TYPE_CHECKING:  # pragma: no cover — SheetSpec lives in sheets.py (which imports us)
    from typehaus.resolve.model import ResolvedModel

# Paper presets, landscape (width, height) in inches.
LEDGER = (17.0, 11.0)
ARCH_D = (36.0, 24.0)
# E-602 carries four stacked tables (22 luminaire types, ~120 control rows in two columns,
# the 24V runs and the connected load) — more vertical content than an 11x17 landscape sheet
# holds at a legible type size. It prints portrait rather than shrinking the control schedule
# to unreadable. Every other table sheet is LEDGER; this is the one deliberate exception, and
# it still gets the same border and title block.
PORTRAIT_LEDGER = (11.0, 17.0)

_MARGIN = 0.25       # border inset from the paper edge, inches
_TITLE_H = 0.75      # title-block strip height above the bottom border line, inches
_VIEW_PAD = 0.10     # air between chrome and the drawing viewport, inches
_BAR_LANE = 0.30     # reserved strip below the viewport for the graphic scale bar
_NOTES_W = 3.4       # reserved right-hand notes panel width, inches
_NOTES_PT = 9.0      # fixed notes lettering size, points (monospace)
_INK = "#1a1a1a"

# Standard architectural scales as (sheet inches per model foot, printed label),
# largest first so "first that fits" is "largest that fits".
ARCH_SCALES = (
    (3.0, "3\" = 1'-0\""),
    (1.5, "1-1/2\" = 1'-0\""),
    (1.0, "1\" = 1'-0\""),
    (0.75, "3/4\" = 1'-0\""),
    (0.5, "1/2\" = 1'-0\""),
    (0.375, "3/8\" = 1'-0\""),
    (0.25, "1/4\" = 1'-0\""),
    (0.1875, "3/16\" = 1'-0\""),
    (0.125, "1/8\" = 1'-0\""),
    (0.09375, "3/32\" = 1'-0\""),
    (0.0625, "1/16\" = 1'-0\""),
)
# Civil/engineering scales, tried only after the architectural ladder is exhausted —
# a parcel-scale site plan is the sheet that needs them (1" = 20' is the residential norm).
ENG_SCALES = (
    (0.05, "1\" = 20'"),
    (1.0 / 30.0, "1\" = 30'"),
    (0.025, "1\" = 40'"),
    (0.02, "1\" = 50'"),
    (1.0 / 60.0, "1\" = 60'"),
    (0.01, "1\" = 100'"),
)
NTS_LABEL = "N.T.S."


def select_scale(span_u_in: float, span_z_in: float, view_w_in: float,
                 view_h_in: float) -> "tuple[float | None, str]":
    """Largest standard scale whose printed drawing fits the viewport.

    Spans are model-space inches; the viewport is paper inches. At scale ``s`` (sheet
    inches per model foot) a model span of ``x`` inches prints ``x / 12 * s`` inches.
    Architectural scales are preferred; engineering scales only continue the ladder below
    1/16" = 1'-0" for parcel-scale drawings. Returns ``(None, "N.T.S.")`` when nothing
    fits — the caller then fits-to-page and must label the sheet not-to-scale.
    """
    for s, label in (*ARCH_SCALES, *ENG_SCALES):
        if span_u_in / 12.0 * s <= view_w_in and span_z_in / 12.0 * s <= view_h_in:
            return s, label
    return None, NTS_LABEL


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


def compose_sheet(scene: Scene, spec: object, model: "ResolvedModel",
                  size: "tuple[float, float] | None" = None):
    """Compose one Scene onto a fixed-size sheet at true printed scale.

    ``spec`` is duck-typed (``sheets.SheetSpec``): ``number``/``title`` are required,
    ``size`` and ``north_arrow`` are honoured when present. Returns the Figure; the
    caller saves and closes it.
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
    scaled_text = _render_nodes(ax, scene)

    scale_in: "float | None" = None
    scale_label = NTS_LABEL
    bounds = _scene_bounds(scene)
    if bounds is not None:
        u0, z0, u1, z1 = bounds
        span_u, span_z = max(u1 - u0, 1e-6), max(z1 - z0, 1e-6)
        scale_in, scale_label = select_scale(span_u, span_z, view[2], view[3])
        if scale_in is not None:
            per_paper_in = 12.0 / scale_in  # model inches per sheet inch — exact
        else:  # fit-to-page fallback, small pad so linework clears the border
            per_paper_in = max(span_u / view[2], span_z / view[3]) * 1.04
        cu, cz = (u0 + u1) / 2.0, (z0 + z1) / 2.0
        ax.set_xlim(cu - view[2] * per_paper_in / 2.0, cu + view[2] * per_paper_in / 2.0)
        ax.set_ylim(cz - view[3] * per_paper_in / 2.0, cz + view[3] * per_paper_in / 2.0)
        ax.set_aspect("equal", adjustable="box")
        if scale_in is not None:
            _draw_scale_bar(fig, scale_in, scale_label, view, size)
    else:
        ax.set_aspect("equal")
        ax.autoscale_view()
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
    """
    import matplotlib.pyplot as plt

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
    ax.text(dividers[2] + pad, low_y + 0.08, _shorten(title, 46), fontsize=6.5,
            family="monospace", va="center", color=_INK)


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

# 9pt monospace advance ≈ 9 * 0.6 / 72 = 0.075"; wrap to fit the reserved panel width.
_NOTES_WRAP = 40


def _scene_note_lines(scene: Scene) -> "list[str]":
    """Wrapped lines for ``Scene.notes`` (str or iterable of str); [] when absent.

    Scene-level notes are optional sheet text authored beside the drawing; the composer
    reserves a right-hand panel for them at fixed lettering size rather than letting them
    inflate the drawing's model-space bounds.
    """
    notes = getattr(scene, "notes", None)
    if not notes:
        return []
    blocks = [notes] if isinstance(notes, str) else list(notes)
    lines: "list[str]" = []
    for block in blocks:
        for raw in str(block).splitlines():
            stripped = raw.strip()
            if not stripped:
                lines.append("")
                continue
            lines.extend(textwrap.wrap(stripped, width=_NOTES_WRAP) or [stripped])
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
