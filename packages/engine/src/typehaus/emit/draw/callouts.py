"""Detail callout and title bubbles — the two halves of a cross-reference (→ 30 §Graphics).

A set with details in it and no way to reach them is a set of unrelated drawings. NCS
closes that with a matched pair, and both halves have to exist or neither works:

**The callout**, on the plan or section where the condition IS — a split circle, detail
number over the sheet the detail is drawn on, with a leader to the place::

      ___
     /502\\      "detail 2, drawn on sheet A-502"
     \\A-5/

**The title bubble**, under the detail itself, carrying the back-reference — the same
number over the sheet the callout came FROM, so a reader who picked the detail sheet off
the pile can walk back to the plan.

Both are ``Polyline`` + ``Text``, for the reason ``keyed_notes`` documents at length: the
writers dispatch ``Symbol`` off a closed vocabulary and an unlisted name renders as a
window glass bar.

**The numbering cannot come from ``build_sheet_index``**, which is downstream of every
scene — a plan is built before the index that would tell it which sheet its details landed
on. So this module derives the same mapping from the same input, ``derive_detail_slices``
in authored order, and a test asserts the two agree. One ordering, computed twice, checked.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw.lineweights import REFERENCE
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, DIM_TEXT_PT, model_in_per_pt

CALLOUT_LAYER = "A-ANNO-REFR"

#: First derived-detail sheet number. Must agree with ``sheets.build_sheet_index``, and
#: ``test_ncs_sheet_identity`` is what holds them together.
FIRST_DETAIL_SHEET = 501

_SEGMENTS = 20


def bubble_radius_in(scale: float | None = None) -> float:
    """Radius in model inches — five characters wide, because ``A-502`` is five."""
    return 2.6 * DIM_TEXT_PT * CHAR_ASPECT * model_in_per_pt(scale or PLAN_RESERVATION_SCALE)


def detail_sheet_numbers(model) -> dict[str, str]:
    """``detail key -> sheet number``, in the order ``build_sheet_index`` will emit them.

    Authored detail ``Slice``s first, then derived transition details sorted by key —
    which is exactly what the index does, because both walk
    ``model.plan.elements_of_kind("Slice")`` and ``derive_detail_slices(model)`` in turn.
    Deriving it here rather than importing it is what breaks the cycle: ``sheets`` imports
    every scene builder, so a scene builder cannot import ``sheets``.
    """
    from typehaus.emit.draw.details import derive_detail_slices

    numbers: dict[str, str] = {}
    next_sheet = FIRST_DETAIL_SHEET
    for item in model.plan.elements_of_kind("Slice"):
        if item.kind.value == "detail":
            numbers[item.tag] = f"A-{next_sheet}"
            next_sheet += 1
    for derived in derive_detail_slices(model):
        numbers[derived.key] = f"A-{next_sheet}"
        next_sheet += 1
    return numbers


def callout_nodes(at: tuple[float, float], number: str, sheet: str,
                  scale: float | None = None) -> list:
    """A split-circle callout centred at ``at`` (model inches).

    ``number`` sits above the split line and ``sheet`` below it, which is the convention
    every reader of a construction set already has: *what* over *where*.
    """
    ux, uz = at
    radius = bubble_radius_in(scale)
    ring = tuple(
        (ux + radius * math.cos(2 * math.pi * i / _SEGMENTS),
         uz + radius * math.sin(2 * math.pi * i / _SEGMENTS))
        for i in range(_SEGMENTS)
    )
    return [
        Polyline(points=ring, layer=CALLOUT_LAYER, closed=True, lineweight=REFERENCE),
        # The split line is a chord across the full width, not a stub: a reader has to see
        # it at a glance to know which half is the sheet.
        Polyline(points=((ux - radius, uz), (ux + radius, uz)),
                 layer=CALLOUT_LAYER, lineweight=REFERENCE),
        Text(anchor=(ux, uz + radius * 0.38), content=number, height_pt=DIM_TEXT_PT,
             layer=CALLOUT_LAYER, align="center"),
        Text(anchor=(ux, uz - radius * 0.62), content=sheet, height_pt=DIM_TEXT_PT,
             layer=CALLOUT_LAYER, align="center"),
    ]


def title_bubble_nodes(at: tuple[float, float], number: str, title: str,
                       scale_label: str, sheet: str = "",
                       scale: float | None = None) -> list:
    """The bubble under a detail: its number, its name, its scale, and where it is called.

    NCS puts the scale with the DRAWING, not only in the title block — a sheet may carry
    several drawings at several scales, and a title block can only state one of them. That
    is why the scale is here even though the block already prints it.
    """
    ux, uz = at
    radius = bubble_radius_in(scale)
    ring = tuple(
        (ux + radius * math.cos(2 * math.pi * i / _SEGMENTS),
         uz + radius * math.sin(2 * math.pi * i / _SEGMENTS))
        for i in range(_SEGMENTS)
    )
    nodes: list = [
        Polyline(points=ring, layer=CALLOUT_LAYER, closed=True, lineweight=REFERENCE),
        Text(anchor=(ux, uz), content=number, height_pt=DIM_TEXT_PT,
             layer=CALLOUT_LAYER, align="center"),
        # The rule under the title, which is what separates a drawing's own name from the
        # drawing above it when two share a sheet.
        Polyline(points=((ux + radius, uz - radius), (ux + radius * 9.0, uz - radius)),
                 layer=CALLOUT_LAYER, lineweight=REFERENCE),
        Text(anchor=(ux + radius * 1.4, uz + radius * 0.25), content=title.upper(),
             height_pt=DIM_TEXT_PT, layer=CALLOUT_LAYER, align="left"),
        Text(anchor=(ux + radius * 1.4, uz - radius * 0.9), content=f"SCALE: {scale_label}",
             height_pt=DIM_TEXT_PT * 0.85, layer=CALLOUT_LAYER, align="left"),
    ]
    if sheet:
        nodes.append(Text(anchor=(ux + radius * 5.2, uz - radius * 0.9),
                          content=f"CALLED FROM {sheet}", height_pt=DIM_TEXT_PT * 0.85,
                          layer=CALLOUT_LAYER, align="left"))
    return nodes
