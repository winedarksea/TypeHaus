"""IKEA SEKTION assembly rules: the bought parts one configured frame needs.

The frame itself is the type's ``product_ref``; this derives everything else as
``ProductPart`` rows, so ``haus takeoff`` and ``haus order`` count them from the same
``front_layout`` the glyph draws. The house supplies the products (``SektionHardware``);
the library supplies only the arithmetic. A front or drawer size the house has no product
for raises at load, so an order list cannot be silently short.

Rules (oracle: houses/catlin/notes/ikea_sektion_order.md):

* hinges per door by door height — 2 up to 40", 3 to 60", 4 above (IKEA planner output;
  the installation guide prints no chart). A lift front takes one horizontal-hinge pair.
* one knob per door or lift front, one pull per drawer front.
* legs per floor-standing frame: 4, or 6 from 30" wide (assumed, as above).
* toe kick and suspension rail run the frame's width, rounded to sticks per run in takeoff.
* shelves: enough that no compartment exceeds 20", over each unbroken stack of door
  courses; a high frame ships with one fixed shelf, which counts toward that.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from typehaus.model import ProductPart, inch
from typehaus.model.placeable_symbols._sektion_kitchen import KITCHEN_SEKTION_CONFIGURATIONS
from typehaus.model.placeable_symbols._sektion_layout import (
    FrontLayout,
    FrontRow,
    front_layout,
)

TWO_HINGE_MAX_DOOR_IN = 40.0
THREE_HINGE_MAX_DOOR_IN = 60.0
LIFT_HINGES_PER_FRONT = 2
FOUR_LEG_MAX_WIDTH_IN = 24.0
MAX_SHELF_COMPARTMENT_IN = 20.0

Support = Literal["legs", "none"]


@dataclass(frozen=True)
class SektionHardware:
    """A house's product tag for each SEKTION role.

    ``fronts`` keys are (kind, width, height) in nominal inches with kind ``door``,
    ``drawer`` or ``lift``; ``drawers`` are (width, front height); ``shelves`` are
    (width, system depth).
    """

    fronts: Mapping[tuple[str, float, float], str] = field(default_factory=dict)
    drawers: Mapping[tuple[float, float], str] = field(default_factory=dict)
    shelves: Mapping[tuple[float, float], str] = field(default_factory=dict)
    hinge: str | None = None
    lift_hinge: str | None = None
    leg: str | None = None
    toe_kick: str | None = None
    rail: str | None = None
    knob: str | None = None
    pull: str | None = None


def hinges_per_door(door_height_in: float) -> int:
    if door_height_in <= TWO_HINGE_MAX_DOOR_IN + 1e-6:
        return 2
    return 3 if door_height_in <= THREE_HINGE_MAX_DOOR_IN + 1e-6 else 4


def legs_per_frame(width_in: float) -> int:
    return 4 if width_in <= FOUR_LEG_MAX_WIDTH_IN + 1e-6 else 6


def shelves_for(layout: FrontLayout, *, fixed_frame_shelf: bool) -> int:
    """Shelves so no bay tops 20". Stacked door courses are one bay stack (no shelf is
    implied at a door split); a drawer or a shelfless bay breaks the stack."""
    stacks, height = [], 0.0
    for row in layout.rows:
        if row.kind in ("door", "lift", "open") and row.shelf_bay:
            height += row.height_in
        else:
            stacks.append(height)
            height = 0.0
    stacks.append(height)
    needed = sum(max(0, math.ceil(h / MAX_SHELF_COMPARTMENT_IN - 1e-6) - 1) for h in stacks)
    return max(0, needed - (1 if fixed_frame_shelf else 0))


def kitchen_layout(symbol: str, width_in: float, height_in: float) -> FrontLayout:
    """The layout a ``sektion-axstad-kitchen-*`` glyph draws at this size."""
    return front_layout(KITCHEN_SEKTION_CONFIGURATIONS[symbol], width_in, height_in)


def _lookup(table: Mapping, key: tuple, what: str) -> str:
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"SEKTION {what} {key} has no product in the house's hardware") from None


def _required(tag: str | None, role: str) -> str:
    if tag is None:
        raise ValueError(f"SEKTION layout needs a {role} product")
    return tag


class _Counter:
    def __init__(self) -> None:
        self.counts: dict[tuple[str, str], int] = {}

    def add(self, role: str, tag: str, quantity: int) -> None:
        if quantity > 0:
            self.counts[(role, tag)] = self.counts.get((role, tag), 0) + quantity


def _row_parts(row: FrontRow, width_in: float, hardware: SektionHardware, out: _Counter) -> None:
    if row.kind == "open":
        return
    front_width = width_in / row.count
    if row.kind == "drawer":
        out.add("front", _lookup(hardware.fronts, ("drawer", front_width, row.height_in),
                                 "drawer front"), row.count)
        out.add("drawer", _lookup(hardware.drawers, (front_width, row.height_in), "drawer"),
                row.count)
        if hardware.pull:
            out.add("pull", hardware.pull, row.count)
        return
    out.add("front", _lookup(hardware.fronts, (row.kind, front_width, row.height_in),
                             f"{row.kind} front"), row.count)
    if row.kind == "lift":
        out.add("hinge", _required(hardware.lift_hinge, "lift hinge"),
                LIFT_HINGES_PER_FRONT * row.count)
    else:
        out.add("hinge", _required(hardware.hinge, "hinge"),
                hinges_per_door(row.height_in) * row.count)
    if hardware.knob:
        out.add("knob", hardware.knob, row.count)


def sektion_parts(width_in: float, depth_in: float, layout: FrontLayout, support: Support,
                  hardware: SektionHardware, *, rail: bool = True, shelves: int | None = None,
                  fixed_frame_shelf: bool = False, toe_kick_in: float | None = None,
                  extra: tuple[ProductPart, ...] = ()) -> tuple[ProductPart, ...]:
    """Every bought part one frame of this nominal size and layout needs, frame excluded.

    ``shelves`` overrides the shelf rule where an insert (a swing-out rack) fills a bay.
    """
    out = _Counter()
    for row in layout.rows:
        _row_parts(row, width_in, hardware, out)
    shelf_count = (shelves if shelves is not None
                   else shelves_for(layout, fixed_frame_shelf=fixed_frame_shelf))
    if shelf_count:
        out.add("shelf", _lookup(hardware.shelves, (width_in, depth_in), "shelf"), shelf_count)
    parts = [ProductPart(role=role, product_ref=tag, quantity=quantity)
             for (role, tag), quantity in out.counts.items()]
    if support == "legs":
        parts.append(ProductPart(role="leg", product_ref=_required(hardware.leg, "leg"),
                                 quantity=legs_per_frame(width_in)))
        parts.append(ProductPart(role="toe_kick",
                                 product_ref=_required(hardware.toe_kick, "toe kick"),
                                 length=inch(toe_kick_in if toe_kick_in is not None
                                             else width_in)))
    if rail:
        parts.append(ProductPart(role="rail", product_ref=_required(hardware.rail, "rail"),
                                 length=inch(width_in)))
    return (*parts, *extra)
