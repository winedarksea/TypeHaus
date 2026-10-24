"""Purchased vanity massing; heights measure from the mounted body base."""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box
from typehaus.model.placeable_symbols._solid_surface_vanity import solid_surface_vanity

DRAWER_REVEAL_M = 0.003175
CARCASS_THICKNESS_M = 0.01905
TOP_DRAWER_FRACTION = 0.32
TOP_THICKNESS_M = 0.012
TOP_OVERHANG_M = 0.0254


def drawer_vanity(width: float, depth: float, height: float, *,
                  door_fronts: bool = False) -> Geometry:
    strokes, parts = solid_surface_vanity(width, depth, height, fronts=(0.5, 0.5))
    deck = height - min(0.14, height * 0.16)
    top_thickness = TOP_THICKNESS_M
    wall = CARCASS_THICKNESS_M
    case_width = width - TOP_OVERHANG_M
    case_depth = depth - CARCASS_THICKNESS_M
    body = [part for part in parts if part["color"] != "appliance-white"]
    for sign in (-1, 1):
        body.append(box(sign * (case_width - wall) / 2, 0, 0, deck - top_thickness,
                        wall, case_depth, "appliance-white"))
    body.append(box(0, 0, 0, wall, case_width, case_depth, "appliance-white"))
    front_y = -depth / 2 + wall / 2
    cabinet_top = deck - top_thickness
    reveal = DRAWER_REVEAL_M
    if door_fronts:
        drawer_bottom = cabinet_top * (1 - TOP_DRAWER_FRACTION)
        body.append(box(0, front_y, drawer_bottom + reveal, cabinet_top - reveal,
                        case_width - reveal, wall, "appliance-white"))
        for sign in (-1, 1):
            body.append(box(sign * case_width / 4, front_y, reveal, drawer_bottom - reveal,
                            case_width / 2 - reveal, wall, "appliance-white"))
    else:
        for index in range(2):
            bottom = index * cabinet_top / 2 + reveal
            top = (index + 1) * cabinet_top / 2 - reveal
            body.append(box(0, front_y, bottom, top,
                            case_width - reveal, wall, "appliance-white"))
    return strokes, tuple(body)
