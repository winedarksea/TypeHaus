"""SEKTION frame panels and configurable installation supports."""

from typehaus.model.placeable_symbols._frame import box
from typehaus.quantities import inch

PANEL_M = inch(0.75).meters
BACK_M = inch(0.125).meters
BASEBOARD_DEPTH_M = inch(0.75).meters
LEVELING_LEG_WIDTH_M = inch(2).meters
LEVELING_LEG_INSET_M = inch(2).meters


def sektion_carcass(
    width: float,
    depth: float,
    z0: float,
    z1: float,
    front_y: float,
    shelves: tuple[float, ...] = (),
    *,
    include_top: bool = True,
    include_bottom: bool = True,
) -> list:
    """Sides and back with optional horizontal panels between ``z0`` and ``z1``."""
    panel = min(PANEL_M, width / 8, depth / 8, (z1 - z0) / 4)
    back_y = depth / 2
    carcass_depth = back_y - front_y
    cy = (front_y + back_y) / 2
    inner = width - 2 * panel
    shelf_depth = carcass_depth - BACK_M
    shelf_cy = cy - BACK_M / 2
    parts = [
        box(sign * (width / 2 - panel / 2), cy, z0, z1, panel, carcass_depth, "appliance-white")
        for sign in (-1, 1)
    ]
    parts.append(box(0, back_y - BACK_M / 2, z0, z1, inner, BACK_M, "appliance-white"))
    horizontal_panels = (
        *((z0,) if include_bottom else ()), *((z1 - panel,) if include_top else ()), *shelves
    )
    for z in horizontal_panels:
        parts.append(box(0, shelf_cy, z, z + panel, inner, shelf_depth, "appliance-white"))
    return parts


def sektion_plinth(width: float, depth: float, base_h: float, *, recess: float = 0.0) -> list:
    """The 2x4 base: a frame at the back and a baseboard flush with the fronts."""
    board = min(BASEBOARD_DEPTH_M, depth / 8)
    rail = min(inch(1.5).meters, depth / 8)
    return [
        box(0, depth / 2 - rail / 2, 0, base_h, width, rail, "appliance-white"),
        box(0, -depth / 2 + recess + board / 2, 0, base_h, width, board, "appliance-white"),
    ]


def sektion_leveling_legs(width: float, depth: float, base_h: float, *, recess: float) -> list:
    """Four floor-bearing legs behind a recessed, non-structural toe-kick panel."""
    leg_width = min(LEVELING_LEG_WIDTH_M, width / 4, depth / 4)
    side_inset = min(LEVELING_LEG_INSET_M, width / 4)
    rear_inset = min(LEVELING_LEG_INSET_M, depth / 4)
    board = min(BASEBOARD_DEPTH_M, depth / 8)
    front_leg_y = -depth / 2 + recess + board + leg_width / 2
    parts = [
        box(sign * (width / 2 - side_inset), y, 0, base_h,
            leg_width, leg_width, "metal-black")
        for sign in (-1, 1)
        for y in (front_leg_y, depth / 2 - rear_inset)
    ]
    parts.append(box(0, -depth / 2 + recess + board / 2, 0, base_h,
                     width, board, "appliance-white"))
    return parts
