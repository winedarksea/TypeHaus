"""SEKTION high frames with VOXTORP fronts and optional open lower storage.

Front modules are inches above a 90-inch frame's bottom; installed height includes legs.
The two open lower bays let a nearby toilet occupy the drawer sweep without moving it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.quantities import inch


@dataclass(frozen=True)
class SektionTallInterior:
    drawer_modules_inches: tuple[tuple[float, float], ...]
    open_shelf_heights_inches: tuple[float, ...] = ()


DRAWER_INTERIOR = SektionTallInterior(((0, 15), (15, 30), (30, 40)))
OPEN_LOWER_INTERIOR = SektionTallInterior(((30, 40),), (15, 30))
FRAME_HEIGHT_INCHES = 90.0
LEG_HEIGHT_INCHES = 4.5
PANEL_THICKNESS_M = inch(0.75).meters
BACK_THICKNESS_M = inch(0.125).meters
RAIL_STANDOFF_M = inch(0.375).meters
FRONT_THICKNESS_M = inch(0.875).meters
FRONT_REVEAL_M = inch(0.125).meters
TOE_RECESS_M = inch(2).meters
PULL_GROOVE_HEIGHT_M = inch(0.5).meters
PULL_GROOVE_DEPTH_M = inch(0.0625).meters
DRAWER_DEPTH_M = inch(21.375).meters
HIGH_DRAWER_HEIGHT_M = inch(8.375).meters
MEDIUM_DRAWER_HEIGHT_M = inch(5.625).meters
HIGH_DRAWER_MODULE_INCHES = 15
UPPER_SHELF_HEIGHTS_INCHES = (40, 55, 70, 80)
UPPER_DOOR_MODULES_INCHES = ((40, 70), (70, 90))


def sektion_cover_panel(width: float, depth: float, height: float) -> Geometry:
    return (rect(0, 0, width, depth),), (
        box(0, 0, 0, height, width, depth, "appliance-white"),)


def sektion_tall(interior: SektionTallInterior) -> Builder:
    """Keep the rail, fronts and recessed plinth inside the declared installed envelope."""

    def build(width: float, depth: float, height: float) -> Geometry:
        installed_scale = height / inch(FRAME_HEIGHT_INCHES + LEG_HEIGHT_INCHES).meters
        leg_height = inch(LEG_HEIGHT_INCHES).meters * installed_scale
        panel = min(PANEL_THICKNESS_M * installed_scale, width / 8, depth / 8)
        front_thickness = min(FRONT_THICKNESS_M, depth / 8)
        back_thickness = min(BACK_THICKNESS_M, panel)
        reveal = min(FRONT_REVEAL_M * installed_scale, panel / 2)
        front_y = -depth / 2
        carcass_front_y = front_y + front_thickness
        carcass_back_y = depth / 2 - min(RAIL_STANDOFF_M, depth / 16)
        carcass_depth = carcass_back_y - carcass_front_y
        carcass_center_y = (carcass_front_y + carcass_back_y) / 2
        opening_width = width - 2 * panel
        shelf_depth = carcass_depth - back_thickness
        shelf_center_y = carcass_center_y - back_thickness / 2

        def elevation(frame_inches: float) -> float:
            return leg_height + inch(frame_inches).meters * installed_scale

        strokes = (
            rect(0, 0, width, depth),
            line((-width / 2, carcass_front_y), (width / 2, carcass_front_y),
                 weight=DETAIL_WEIGHT),
        )
        parts = [
            box(-width / 2 + panel / 2, carcass_center_y, leg_height, height,
                panel, carcass_depth, "appliance-white"),
            box(width / 2 - panel / 2, carcass_center_y, leg_height, height,
                panel, carcass_depth, "appliance-white"),
            box(0, carcass_back_y - back_thickness / 2, leg_height, height,
                opening_width, back_thickness, "appliance-white"),
            box(0, shelf_center_y, leg_height, leg_height + panel,
                opening_width, shelf_depth, "appliance-white"),
            box(0, shelf_center_y, height - panel, height,
                opening_width, shelf_depth, "appliance-white"),
            box(0, carcass_front_y + min(TOE_RECESS_M, carcass_depth / 4) + panel / 2,
                0, leg_height, width, panel, "casework-shadow"),
        ]
        for shelf_inches in (*interior.open_shelf_heights_inches,
                             *UPPER_SHELF_HEIGHTS_INCHES):
            shelf_z = elevation(shelf_inches)
            parts.append(box(0, shelf_center_y, shelf_z, shelf_z + panel,
                             opening_width, shelf_depth, "appliance-white"))

        def add_front(bottom_inches: float, top_inches: float,
                      *, pull_at_bottom: bool = False) -> None:
            bottom = elevation(bottom_inches) + reveal / 2
            top = elevation(top_inches) - reveal / 2
            face_width = width - reveal
            groove_height = min(PULL_GROOVE_HEIGHT_M, (top - bottom) / 8)
            groove_depth = min(PULL_GROOVE_DEPTH_M, front_thickness / 4)
            groove_bottom = bottom if pull_at_bottom else top - groove_height
            parts.append(box(0, front_y + front_thickness / 2, bottom, top,
                             face_width, front_thickness, "porcelain"))
            # The integrated VOXTORP pull reads as a shallow shadow within the slab.
            parts.append(box(0, front_y + groove_depth / 2,
                             groove_bottom, groove_bottom + groove_height,
                             face_width - 2 * panel, groove_depth, "casework-shadow"))

        for bottom_inches, top_inches in interior.drawer_modules_inches:
            add_front(bottom_inches, top_inches)
            drawer_bottom = elevation(bottom_inches) + panel
            nominal_drawer_height = (HIGH_DRAWER_HEIGHT_M
                                     if top_inches - bottom_inches == HIGH_DRAWER_MODULE_INCHES
                                     else MEDIUM_DRAWER_HEIGHT_M)
            drawer_height = min(nominal_drawer_height * installed_scale,
                                elevation(top_inches) - drawer_bottom - panel)
            drawer_depth = min(DRAWER_DEPTH_M, shelf_depth - panel)
            drawer_center_y = carcass_front_y + drawer_depth / 2
            drawer_width = opening_width - reveal
            parts.append(box(0, drawer_center_y, drawer_bottom, drawer_bottom + panel,
                             drawer_width, drawer_depth, "appliance-white"))
            for sign in (-1, 1):
                parts.append(box(sign * (drawer_width - panel) / 2, drawer_center_y,
                                 drawer_bottom, drawer_bottom + drawer_height,
                                 panel, drawer_depth, "appliance-white"))
            parts.append(box(0, carcass_front_y + drawer_depth - panel / 2,
                             drawer_bottom, drawer_bottom + drawer_height,
                             drawer_width, panel, "appliance-white"))
        for bottom_inches, top_inches in UPPER_DOOR_MODULES_INCHES:
            add_front(bottom_inches, top_inches, pull_at_bottom=True)
        return strokes, tuple(parts)

    return build
