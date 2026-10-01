"""Closed-position geometry for the purchased Murphy bookcase door.

The factory body is a shallow cabinet, not a solid swing leaf. Board dimensions and
the four interior shelves follow Murphy Door's published 8 1/4-inch kit specification;
the overall body and casing dimensions come from ``BookcaseDoorSpec``.
"""

from __future__ import annotations

from collections.abc import Callable

from typehaus.model.types import BookcaseDoorSpec
from typehaus.resolve.geometry_ir import GPart, GPrism


_INCH_M = 0.0254
_SIDE_THICKNESS_M = 0.75 * _INCH_M
_SHELF_THICKNESS_M = 0.75 * _INCH_M
_TOP_BOTTOM_THICKNESS_M = 1.5 * _INCH_M
_BACK_THICKNESS_M = 0.5 * _INCH_M
_SHELF_DEPTH_M = 6.5 * _INCH_M
_INTERIOR_SHELF_COUNT = 4  # one fixed and three adjustable, shown evenly spaced


def bookcase_door_parts(
    box: Callable[[float, float, float, float, float, float], GPrism],
    spec: BookcaseDoorSpec, opening_width_m: float, available_height_m: float,
    floor_z_m: float,
) -> tuple[GPart, ...]:
    """Return casing, cabinet boards, and recessed back in the host wall frame."""
    sign = -1.0 if spec.mounting_face == "negative_normal" else 1.0
    width = min(spec.body_width.meters, opening_width_m)
    height = min(spec.body_height.meters, available_height_m)
    depth = spec.body_depth.meters
    side = min(_SIDE_THICKNESS_M, width / 4)
    top_bottom = min(_TOP_BOTTOM_THICKNESS_M, height / 6)
    back = min(_BACK_THICKNESS_M, depth / 4)
    shelf_depth = min(_SHELF_DEPTH_M, depth - back)
    shelf_width = width - 2 * side
    floor = floor_z_m
    face = sign * depth

    # The factory casing spans the rough opening and sits at the cabinet face.
    casing_width = max(0.0, (spec.casing_overall_width.meters - opening_width_m) / 2)
    casing_solids = ()
    if casing_width > 0:
        casing_solids = (
            box(casing_width, available_height_m + casing_width, _SIDE_THICKNESS_M,
                -opening_width_m / 2 - casing_width / 2,
                floor + available_height_m / 2, face - sign * _SIDE_THICKNESS_M / 2),
            box(casing_width, available_height_m + casing_width, _SIDE_THICKNESS_M,
                opening_width_m / 2 + casing_width / 2,
                floor + available_height_m / 2, face - sign * _SIDE_THICKNESS_M / 2),
            box(opening_width_m + 2 * casing_width, casing_width, _SIDE_THICKNESS_M,
                0.0, floor + available_height_m + casing_width / 2,
                face - sign * _SIDE_THICKNESS_M / 2),
        )

    sides = tuple(box(side, height, depth, side_sign * (width - side) / 2,
                      floor + height / 2, face - sign * depth / 2)
                  for side_sign in (-1, 1))
    cap_elevations = (floor + top_bottom / 2, floor + height - top_bottom / 2)
    caps = tuple(box(shelf_width, top_bottom, depth - back, 0.0, elevation,
                     sign * (back + (depth - back) / 2)) for elevation in cap_elevations)
    shelf_center = sign * (back + shelf_depth / 2)
    clear_height = height - 2 * top_bottom
    shelves = tuple(box(shelf_width, _SHELF_THICKNESS_M, shelf_depth, 0.0,
                        floor + top_bottom + clear_height * index /
                        (_INTERIOR_SHELF_COUNT + 1), shelf_center)
                    for index in range(1, _INTERIOR_SHELF_COUNT + 1))
    cabinet_back = box(shelf_width, height - 2 * top_bottom, back, 0.0,
                       floor + height / 2, sign * back / 2)
    return (
        GPart(key="bookcase_casing", material_key="opening_frame", solids=casing_solids),
        GPart(key="bookcase_sides", material_key="opening_frame", solids=sides),
        GPart(key="bookcase_caps", material_key="opening_frame", solids=caps),
        GPart(key="bookcase_shelves", material_key="opening_frame", solids=shelves),
        GPart(key="bookcase_back", material_key="bookcase_back", solids=(cabinet_back,)),
    )
