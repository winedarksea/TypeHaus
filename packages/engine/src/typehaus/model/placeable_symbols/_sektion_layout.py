"""SEKTION front layout: the one door/drawer count both the glyph and the bill read.

``_sektion_kitchen`` draws from it and ``library/placeables/sektion_parts`` orders from it,
so a drawing with two doors cannot bill one. Heights are nominal inches (the 5" ladder).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# A front wider than this splits into a pair (IKEA sells no 30"+ door).
SINGLE_DOOR_MAX_WIDTH_IN = 24.0
BASE_FRAME_IN = 30.0
TALL_LOWER_FRONT_IN = 50.0
DRAWER_STACK_COUNT = 3
NOMINAL_GRID_PER_IN = 8

FrontKind = Literal["door", "drawer", "lift", "open"]


@dataclass(frozen=True)
class SektionCabinetConfiguration:
    installation: str = "wall"
    fronts: str = "doors"
    hinge_right: bool = False
    tall_front_heights_in: tuple[float, ...] = ()
    support_height_in: float = 3.5
    leveling_legs: bool = False


@dataclass(frozen=True)
class FrontRow:
    """One course of fronts, bottom to top: ``count`` fronts of ``height_in`` across."""

    kind: FrontKind
    height_in: float
    count: int = 1
    # False where the bay behind takes no shelf: a sink, an appliance garage.
    shelf_bay: bool = True


@dataclass(frozen=True)
class FrontLayout:
    frame_height_in: float
    rows: tuple[FrontRow, ...]


def fronts_across(width_in: float) -> int:
    return 1 if width_in <= SINGLE_DOOR_MAX_WIDTH_IN + 1e-6 else 2


def front_layout(config: SektionCabinetConfiguration, width_in: float,
                 height_in: float) -> FrontLayout:
    """The fronts a configured cabinet of this installed ``height_in`` carries."""
    across = fronts_across(width_in)
    if config.installation == "base":
        frame = BASE_FRAME_IN
    elif config.installation == "tall":
        frame = height_in - config.support_height_in
    else:
        frame = height_in
    # Nominal sizes are on an 1/8" grid; strip metre round-trip noise so they key a product.
    frame = round(frame * NOMINAL_GRID_PER_IN) / NOMINAL_GRID_PER_IN
    if config.fronts == "drawers":
        drawer = frame / DRAWER_STACK_COUNT
        return FrontLayout(frame, (FrontRow("drawer", drawer),) * DRAWER_STACK_COUNT)
    if config.fronts in ("lift", "garage"):
        return FrontLayout(frame, (FrontRow("lift", frame, across,
                                            shelf_bay=config.fronts == "lift"),))
    if config.installation != "tall":
        return FrontLayout(frame, (FrontRow("door", frame, across,
                                            shelf_bay=config.fronts != "sink"),))
    heights = config.tall_front_heights_in or (TALL_LOWER_FRONT_IN, frame - TALL_LOWER_FRONT_IN)
    return FrontLayout(frame, tuple(FrontRow("door", h, across) for h in heights))
