"""Serialize resolved opening product parts, catalog colors and surface finishes to GLB.

The geometry lives in ``resolve/geometry_openings.py`` and its focused product builders.
Legacy window constants remain re-exported for existing parity tests.
"""

from __future__ import annotations

from typehaus.emit.door_surfaces import door_part_color, door_part_surface
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.enums import DoorOperation
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_openings import (  # noqa: F401
    _DOOR_LEAF_THICKNESS_M,
    _DOUBLE_SWING_LEAF_COUNT,
    _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR,
    _OPENING_FRAME_DEPTH_M,
    _OPENING_FRAME_FACE_WIDTH_M,
    _OPENING_FRAME_SPAN_DIVISOR,
    _OPENING_MIN_PANEL_DIMENSION_M,
    _WINDOW_GLAZING_THICKNESS_M,
    _WINDOW_TRIM_FACE_WIDTH_M,
    _WINDOW_TRIM_PROUD_DEPTH_M,
    opening_parts,
)
from typehaus.resolve.model import ResolvedWall


def _add_opening_filling(mb: _MeshBuilder, wall: ResolvedWall, opening,
                         operation: DoorOperation | None, is_glazed: bool = False,
                         is_trimless: bool = False, bookcase_door=None,
                         authored: dict | None = None, leaf_set: str = "pull") -> dict:
    """Draw the product standing in ``opening`` — frame + panel/leaf/glass — as boxes.

    Emitted regardless of LOD so the leaf geometry shows for both the core wall prism and the
    framed stud model. A rough opening is a bare void and yields no parts at all.
    """
    surfaces = {}
    for part in opening_parts(wall, opening, operation, is_glazed=is_glazed,
                              is_trimless=is_trimless, bookcase_door=bookcase_door,
                              leaf_set=leaf_set):
        color = door_part_color(part, authored,
                                linear_paint_defaults=opening.cased_product is not None)
        surfaces[color] = door_part_surface(part)
        for solid in part.solids:
            if isinstance(solid, GSweep):
                mb.add_sweep(solid, color)
            else:
                mb.add_prism(list(solid.ring), solid.z0_m, solid.z1_m, color)
    return surfaces
