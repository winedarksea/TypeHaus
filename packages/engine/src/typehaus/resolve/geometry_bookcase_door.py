"""Closed-position geometry for the purchased Murphy bookcase door.

The factory body is a shallow cabinet, not a solid swing leaf. Board dimensions and
the four interior shelves follow Murphy Door's published 8 1/4-inch kit specification;
the overall body dimensions come from ``BookcaseDoorSpec``. A flush mount sits in the
rough opening with its face frame on the mounting face's finish and its back proud of the
other face. Its in-swing casing is applied wall trim, derived in ``interior_trim_casing``.
"""

from __future__ import annotations

from collections.abc import Callable

from typehaus.model.types import BookcaseDoorSpec
from typehaus.resolve.geometry_ir import GPart, GPrism, PartCatalogRef

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
    floor_z_m: float, mount_plane_m: float = 0.0,
) -> tuple[GPart, ...]:
    """Return cabinet boards and recessed back in the host wall frame.

    ``mount_plane_m`` is the normal offset of the mounting face's finish: the face frame.
    """
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
    face = mount_plane_m
    back_plane = face - sign * depth

    sides = tuple(box(side, height, depth, side_sign * (width - side) / 2,
                      floor + height / 2, face - sign * depth / 2)
                  for side_sign in (-1, 1))
    cap_elevations = (floor + top_bottom / 2, floor + height - top_bottom / 2)
    cap_center = back_plane + sign * (back + (depth - back) / 2)
    caps = tuple(box(shelf_width, top_bottom, depth - back, 0.0, elevation, cap_center)
                 for elevation in cap_elevations)
    shelf_center = back_plane + sign * (back + shelf_depth / 2)
    clear_height = height - 2 * top_bottom
    shelves = tuple(box(shelf_width, _SHELF_THICKNESS_M, shelf_depth, 0.0,
                        floor + top_bottom + clear_height * index /
                        (_INTERIOR_SHELF_COUNT + 1), shelf_center)
                    for index in range(1, _INTERIOR_SHELF_COUNT + 1))
    cabinet_back = box(shelf_width, height - 2 * top_bottom, back, 0.0,
                       floor + height / 2, back_plane + sign * back / 2)
    catalog = PartCatalogRef(material_ref=spec.material_ref, role="millwork")
    return (
        GPart(key="bookcase_sides", material_key="oak_bookcase", solids=sides, catalog=catalog),
        GPart(key="bookcase_caps", material_key="oak_bookcase", solids=caps, catalog=catalog),
        GPart(key="bookcase_shelves", material_key="oak_bookcase", solids=shelves,
              catalog=catalog),
        GPart(key="bookcase_back", material_key="oak_bookcase", solids=(cabinet_back,),
              catalog=catalog),
    )
