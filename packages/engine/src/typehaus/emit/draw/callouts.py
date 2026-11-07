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

**The numbering lives here, not in ``build_sheet_index``**, which is downstream of every
scene — a plan is built before the index that would tell it which sheet its details landed
on. Both read :func:`detail_sheets`, and a test asserts they agree.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw.lineweights import REFERENCE
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, ROOM_NAME_PT, TAG_PT, model_in_per_pt
from typehaus.model.enums import ConditionKind

CALLOUT_LAYER = "A-ANNO-REFR"

#: Authored detail ``Slice``s take whole numbers from here, in authoring order.
FIRST_DETAIL_SHEET = 501

#: Each derived condition kind is one decimal series on its own base (A-540.1, A-540.2 …),
#: members in key order: a family grows without renumbering another, and the block no
#: longer fills (it did at A-599 when every detail took a whole number). Bottom up.
DERIVED_SERIES = {
    ConditionKind.WALL_FOUNDATION: 530,
    ConditionKind.WALL_SLAB: 535,
    ConditionKind.STOREY_STACK: 540,
    ConditionKind.STACK_WIDTH_CHANGE: 545,
    ConditionKind.ASSEMBLY_CHANGE: 550,
    ConditionKind.OPENING_PERIMETER: 560,
    ConditionKind.WALL_ROOF: 570,
    ConditionKind.ROOF_RIDGE: 575,
}

_SEGMENTS = 20


def bubble_radius_in(scale: float | None = None) -> float:
    """Radius in model inches — five characters wide, because ``A-502`` is five."""
    return 2.6 * TAG_PT * CHAR_ASPECT * model_in_per_pt(scale or PLAN_RESERVATION_SCALE)


def callout_label(sheet: str) -> tuple[str, str]:
    """``(number, sheet)`` for a callout's two halves: NCS's detail-over-sheet.

    A series member ``A-540.4`` reads ``4`` over ``A-540`` — detail 4 of that series, and
    a bubble five characters wide; a whole-number sheet carries one drawing, ``1``.
    """
    head, _, member = sheet.partition(".")
    return (member, head) if member else ("1", sheet)


def detail_sheets(model) -> list[tuple[str, object]]:
    """``(sheet number, authored Slice | DerivedDetail)`` in sheet-number order.

    Authored details first on whole numbers, then each ``DERIVED_SERIES`` family on its
    base. Numbered before any set filter, so a detail keeps its number in every set.
    """
    from typehaus.emit.draw.details import derive_detail_slices

    authored = [item for item in model.plan.elements_of_kind("Slice")
                if item.kind.value == "detail"]
    last = FIRST_DETAIL_SHEET + len(authored) - 1
    if authored and last >= min(DERIVED_SERIES.values()):
        raise ValueError(f"{len(authored)} authored details overrun A-{last}, the first "
                         "derived series; move DERIVED_SERIES up")
    out: list[tuple[str, object]] = [(f"A-{FIRST_DETAIL_SHEET + i}", item)
                                     for i, item in enumerate(authored)]
    families: dict[ConditionKind, list] = {}
    for derived in derive_detail_slices(model):  # sorted by key
        families.setdefault(derived.condition.kind, []).append(derived)
    for kind, base in sorted(DERIVED_SERIES.items(), key=lambda row: row[1]):
        out += [(f"A-{base}.{i}", derived)
                for i, derived in enumerate(families.pop(kind, ()), start=1)]
    if families:
        raise ValueError(f"no DERIVED_SERIES row for {sorted(k.value for k in families)}")
    return out


def detail_sheet_numbers(model) -> dict[str, str]:
    """``detail key -> sheet number``: an authored Slice's tag, a derived detail's key."""
    from typehaus.emit.draw.detail_derive import DerivedDetail

    return {item.key if isinstance(item, DerivedDetail) else item.tag: number
            for number, item in detail_sheets(model)}


def sheet_sort_key(number: str) -> tuple:
    """``A-540.10`` after ``A-540.9``: series, then each decimal part as an integer."""
    letter, _, rest = number.partition("-")
    return (letter, *(int(part) for part in rest.split(".") if part.isdigit()))


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
        Text(anchor=(ux, uz + radius * 0.38), content=number, height_pt=TAG_PT,
             layer=CALLOUT_LAYER, align="center"),
        Text(anchor=(ux, uz - radius * 0.62), content=sheet, height_pt=TAG_PT,
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
        Text(anchor=(ux, uz), content=number, height_pt=TAG_PT,
             layer=CALLOUT_LAYER, align="center"),
        # The rule under the title, which is what separates a drawing's own name from the
        # drawing above it when two share a sheet.
        Polyline(points=((ux + radius, uz - radius), (ux + radius * 9.0, uz - radius)),
                 layer=CALLOUT_LAYER, lineweight=REFERENCE),
        Text(anchor=(ux + radius * 1.4, uz + radius * 0.25), content=title.upper(),
             height_pt=ROOM_NAME_PT, layer=CALLOUT_LAYER, align="left"),
        Text(anchor=(ux + radius * 1.4, uz - radius * 0.9), content=f"SCALE: {scale_label}",
             height_pt=TAG_PT, layer=CALLOUT_LAYER, align="left"),
    ]
    if sheet:
        nodes.append(Text(anchor=(ux + radius * 5.2, uz - radius * 0.9),
                          content=f"CALLED FROM {sheet}", height_pt=TAG_PT,
                          layer=CALLOUT_LAYER, align="left"))
    return nodes
