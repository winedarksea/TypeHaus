"""Room macros + wall-draw — geometry-aware builders that emit :class:`MutationResult`s
(→ 21b §Room macros, §Mutation contract).

These are *server-side* helpers, not new grammar: each returns ordinary ``add|update|delete``
PatchOps that ride the standard :class:`~typehaus.source.coordinator.ProjectCoordinator`
patch/undo path, so undo/redo and revision-hash write safety come for free. Geometry math
lives here (the "server owns all geometry" rule, → 21b) — the client only sends screen intent
(draw endpoints, the wall to split, the drag delta). Node positions are read from the authored
:class:`~typehaus.model.plan.PlanModel`; new coordinates are emitted as :class:`RawExpr`
``pt(...)`` so no re-encoding round-trip can lose precision.

Implementations live in four sibling modules: :mod:`~typehaus.source.macros_common` (error
type, tolerances, lookup and coordinate helpers), :mod:`~typehaus.source.macros_geometry`
(pure plan-frame primitives), :mod:`~typehaus.source.macros_openings` (hosted placement —
openings, rooms, stairs), :mod:`~typehaus.source.macros_placeables` (placeable editing +
coupled drain followers), and :mod:`~typehaus.source.macros_walls` (draw, stretch, split,
heal). This module is the one public door: the server's macro dispatch
(``server/macros_api.py``) and every other caller import from ``typehaus.source.macros``.
"""

from __future__ import annotations

from typehaus.source.macros_common import (
    _PLACEABLE_KINDS,
    ROOM_BOUNDARY_NODE_TOLERANCE_M,
    ROTATION_SNAP_DEGREES,
    SNAP_M,
    XY,
    MacroError,
    _as_length,
    _copy_tag,
    _find_node_near,
    _meters,
    _next_tag,
    _nodes,
    _openings,
    _placeable,
    _point_expr,
    _point_expr_m,
    _rooms,
    _round_len,
    _walls,
)
from typehaus.source.macros_geometry import (
    COLLINEAR_TOL,
    _collinear,
    _dist,
    _point_in_polygon,
    _project_param,
)
from typehaus.source.macros_openings import (
    _STAIR_DEFAULT_WIDTH,
    _STAIR_MAX_RISER,
    _STAIR_TREAD,
    _destination_deck,
    _floor_openings,
    _opening_start_offset,
    _opening_width,
    _stairs,
    _storey_above,
    _validate_opening_station,
    move_opening,
    place_opening,
    place_room,
    place_rough_opening,
    place_stair,
    rehost_opening,
)
from typehaus.source.macros_placeables import (
    _containing_room,
    _convention_drain_point,
    _drain_follower_ops,
    _placeable_type,
    assign_placeable_room,
    attach_placeable,
    detach_placeable,
    duplicate_canvas_object,
    move_placeable,
    place_placeable,
    retype_placeable,
    rotate_placeable,
    set_placeable_mount,
)
from typehaus.source.macros_walls import (
    _opening_param,
    _pending_nodes,
    _rehost_openings,
    _rooms_with_moved_boundaries,
    _wall_list,
    draw_wall,
    heal_walls,
    move_nodes,
    split_wall,
)

# The underscore-prefixed helpers are here because callers outside this package already
# import them by that name (the canvas tests reach for ``_rooms_with_moved_boundaries``);
# they are not an invitation to reach for more.
__all__ = [
    "COLLINEAR_TOL", "MacroError", "ROOM_BOUNDARY_NODE_TOLERANCE_M", "ROTATION_SNAP_DEGREES",
    "SNAP_M", "XY", "assign_placeable_room", "attach_placeable", "detach_placeable",
    "draw_wall", "duplicate_canvas_object", "heal_walls", "move_nodes", "move_opening",
    "move_placeable", "place_opening", "place_placeable", "place_room", "place_rough_opening",
    "place_stair", "rehost_opening", "retype_placeable", "rotate_placeable",
    "set_placeable_mount", "split_wall",
    "_PLACEABLE_KINDS", "_STAIR_DEFAULT_WIDTH", "_STAIR_MAX_RISER", "_STAIR_TREAD",
    "_as_length", "_collinear", "_containing_room", "_convention_drain_point", "_copy_tag",
    "_destination_deck", "_dist", "_drain_follower_ops", "_find_node_near", "_floor_openings",
    "_meters", "_next_tag", "_nodes", "_opening_param", "_opening_start_offset",
    "_opening_width", "_openings", "_pending_nodes", "_placeable", "_placeable_type",
    "_point_expr", "_point_expr_m", "_point_in_polygon", "_project_param", "_rehost_openings",
    "_rooms", "_rooms_with_moved_boundaries", "_round_len", "_stairs", "_storey_above",
    "_validate_opening_station", "_wall_list", "_walls",
]
