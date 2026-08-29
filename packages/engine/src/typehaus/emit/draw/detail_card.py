"""The paper a rendered detail is laid out on (→ 30 §Details).

``sheet_writer.compose_sheet`` was already the right model for a permit sheet: a fixed sheet,
a fixed viewport, a true architectural scale from ``select_scale``, a fixed notes band. The
``haus render`` path was not — ``pdf_writer._fig`` fitted the figure to its *content*,
lettering included, between a ``_MIN_FIG`` and a ``_MAX_FIG``. Content was the independent
variable, so a junction 40 inches across drew at whatever scale its 108-line construction
note left room for.

This module inverts that for a card. The sheet is chosen, the drawing is placed into it, and
the scale is *selected* from the standard ladder rather than falling out of a fit.

Who picks the scale, and from what
----------------------------------
:func:`card_for_crop`, from the **crop** — not from the drawn geometry. The crop is known
before any cutting, it is exactly what the geometry is clipped to, and using it avoids a
circular cut → measure → choose → re-lay-out → re-cut. One pass, deterministic.

The four authored ``Slice``\\ s that carry no crop have no such input, so they take a cheap
two-pass: cut once with ``frame=None``, measure the geometry, choose, cut again. That is
deliberate and it is not a heuristic waiting to be optimised — it is the price of a drawing
that never said how big it is.
"""

from __future__ import annotations

from typehaus.emit.draw.paper import ARCH_SCALES, NTS_LABEL, fit_scale
from typehaus.emit.draw.scene import Frame

#: Card presets. Portrait first — a wall junction is taller than it is wide far more often
#: than not, and ties go to the first entry.
PORTRAIT = (8.5, 11.0)
LANDSCAPE = (11.0, 8.5)

MARGIN_IN = 0.5      #: border inset from the paper edge
TITLE_H_IN = 0.9     #: title strip along the top
LEGEND_H_IN = 1.1    #: material legend strip along the bottom — five rows of three
NOTES_W_IN = 3.4     #: notes column down the right — the width sheet_writer already uses
PAD_IN = 0.15        #: air between a band and the drawing

#: Room reserved *inside* the viewport for the annotation that hangs off the drawing: the
#: layer ladder down the left, the seed-callout column on the right. Paper inches, because
#: that is what annotation costs — a 7 pt label is the same width of page at every scale,
#: which is exactly why reserving for it here creates no circular dependency on the drawing.
LADDER_GUTTER_IN = 1.35
#: Wider than the ladder's, because a seed callout wraps at ``LEADER_WRAP_COLUMNS`` and a
#: 40-column monospace line at ``TEXT_PT`` is 2.4 paper inches however the drawing is scaled.
CALLOUT_GUTTER_IN = 2.60


def bands(paper: tuple[float, float], notes: bool = True,
          ) -> dict[str, tuple[float, float, float, float]]:
    """The named paper-inch rectangles chrome lives in, measured from the lower left.

    They tile without overlapping, which is the property that matters: the notes column runs
    the full height beside everything else, and the legend takes the strip under the drawing
    *to the left of it*. A legend that ran the full width printed its third column straight
    through the notes.
    """
    w, h = paper
    inner_w = w - 2 * MARGIN_IN
    left_w = inner_w - (NOTES_W_IN + PAD_IN if notes else 0.0)
    out = {
        "title": (MARGIN_IN, h - MARGIN_IN - TITLE_H_IN, inner_w, TITLE_H_IN),
        "legend": (MARGIN_IN, MARGIN_IN, left_w, LEGEND_H_IN),
    }
    if notes:
        out["notes"] = (w - MARGIN_IN - NOTES_W_IN, MARGIN_IN, NOTES_W_IN,
                        h - 2 * MARGIN_IN - TITLE_H_IN - PAD_IN)
    return out


def viewport(paper: tuple[float, float], notes: bool = True,
             ) -> tuple[float, float, float, float]:
    """``(x, y, w, h)`` of the drawing window on ``paper``, paper inches.

    Fixed bands, so the drawing's room is a property of the card and not of the drawing.
    """
    w, h = paper
    x = MARGIN_IN
    y = MARGIN_IN + LEGEND_H_IN + PAD_IN
    width = w - 2 * MARGIN_IN
    height = h - MARGIN_IN - TITLE_H_IN - PAD_IN - y
    if notes:
        width -= NOTES_W_IN + PAD_IN
    return (x, y, width, height)


def drawing_box(view: tuple[float, float, float, float]) -> tuple[float, float]:
    """The part of the viewport the *geometry* may use, once the gutters are reserved."""
    return (max(0.1, view[2] - LADDER_GUTTER_IN - CALLOUT_GUTTER_IN),
            max(0.1, view[3]))


def card_for_crop(span_u_in: float, span_z_in: float, center: tuple[float, float],
                  *, notes: bool = True) -> Frame:
    """The card and scale for a drawing of this size — the larger scale wins.

    Both orientations are tried and the one that admits a *bigger* entry from
    ``ARCH_SCALES`` is taken, because the scale is what a reader gets out of a detail: at
    1-1/2" = 1'-0" a 1/2" layer is 1/16" of paper and reads; at 1/4" it is a line.

    ``(None, NTS_LABEL)`` from the ladder is kept rather than papered over. It means nothing
    standard fits, the writer must fit-to-viewport, and the sheet has to say so — which is a
    true statement about the drawing, unlike a scale that is off the ladder.
    """
    best: Frame | None = None
    best_scale = -1.0
    for paper in (PORTRAIT, LANDSCAPE):
        view = viewport(paper, notes=notes)
        draw_w, draw_h = drawing_box(view)
        scale, label = _select(span_u_in, span_z_in, draw_w, draw_h)
        rank = scale if scale is not None else 0.0
        if rank > best_scale or best is None:
            best_scale = rank
            chosen = scale if scale is not None else _fit(
                span_u_in, span_z_in, draw_w, draw_h)
            # The geometry is centred in its own box, which sits between the two gutters —
            # so the ladder has room on the left and the callouts on the right, and the
            # drawing lands in the middle of what is left rather than off the page.
            shift = (LADDER_GUTTER_IN - CALLOUT_GUTTER_IN) / 2.0 * 12.0 / chosen
            best = Frame(paper=paper, viewport=view,
                         center=(center[0] - shift, center[1]),
                         scale=chosen, scale_label=label, bands=bands(paper, notes))
    assert best is not None
    return best


def _select(span_u_in: float, span_z_in: float, view_w: float, view_h: float):
    """Largest architectural scale whose printed drawing fits, or ``(None, N.T.S.)``.

    A card is a *detail*, so only the architectural ladder is tried — the engineering
    scales below 1/16" = 1'-0" exist for parcel drawings and a detail printed at 1" = 20'
    is not a detail.
    """
    for scale, label in ARCH_SCALES:
        if span_u_in / 12.0 * scale <= view_w and span_z_in / 12.0 * scale <= view_h:
            return scale, label
    return None, NTS_LABEL


def _fit(span_u_in: float, span_z_in: float, view_w: float, view_h: float) -> float:
    """The non-standard scale that just fits — only ever reached under an N.T.S. label.

    No pad: a card's drawing box already sits inside the ladder and callout gutters, so the
    border it has to clear is two inches away. A sheet has no such gutters and pads.
    """
    return fit_scale(span_u_in, span_z_in, view_w, view_h)
