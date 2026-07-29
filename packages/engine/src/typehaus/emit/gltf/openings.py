"""The door/window product in a wall's opening void, serialized from the IR.

The geometry — the four-piece frame, the centre mullion, the leaves, the glass pane, and the
rake clipping that keeps a door under a gable out of the roof plane — lives in
``resolve/geometry_openings.py``. This module is what is left of the emitter's own job: map
each part's ``material_key`` to a flat colour and hand its boxes to the mesh builder.

The constants are re-exported below because this module was one half of a documented
cross-language mirrored pair with ``ui/src/three/builders/walls.ts::buildOpening``, and tests
(plus the viewer-parity notes) import them from here by name.
"""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color
from typehaus.model.enums import DoorOperation
from typehaus.resolve.geometry_openings import (  # noqa: F401
    _DOOR_LEAF_THICKNESS_M,
    _DOUBLE_SWING_LEAF_COUNT,
    _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR,
    _OPENING_FRAME_DEPTH_M,
    _OPENING_FRAME_FACE_WIDTH_M,
    _OPENING_FRAME_SPAN_DIVISOR,
    _OPENING_MIN_PANEL_DIMENSION_M,
    _WINDOW_GLAZING_THICKNESS_M,
    opening_parts,
)
from typehaus.resolve.model import ResolvedWall


def _add_opening_filling(mb: _MeshBuilder, wall: ResolvedWall, opening,
                         operation: DoorOperation | None, is_glazed: bool = False,
                         is_trimless: bool = False) -> None:
    """Draw the product standing in ``opening`` — frame + panel/leaf/glass — as boxes.

    Emitted regardless of LOD so the leaf geometry shows for both the core wall prism and the
    framed stud model. A rough opening is a bare void and yields no parts at all.
    """
    for part in opening_parts(wall, opening, operation, is_glazed=is_glazed,
                              is_trimless=is_trimless):
        color = _color(part.material_key)
        for solid in part.solids:
            mb.add_prism(list(solid.ring), solid.z0_m, solid.z1_m, color)
