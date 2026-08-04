"""Where a room's floor actually sits — the one answer the whole pipeline shares.

Usually a room's storey walls bottom out exactly where its floor structure does, so the
wall base is a fine default. That assumption breaks when a room's real floor slab is filed
on a different storey than the room itself (the Catlin garage: its slab is poured at grade
and filed on "main", while its wood walls — and so the room — sit on the "garage" storey,
22" up on the ICF stem).

It lives in ``resolve`` rather than ``emit`` because ``resolve/placeables.py`` needs it too,
and needs it *before* either emitter runs: a placeable's mount elevation is measured off the
floor it stands on, not off its storey datum. While this was an emit-only helper, everything
standing in the garage — the hydrant, the workbench, every receptacle and switch — resolved
22" above the floor the viewer drew under it.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.resolve.model import ResolvedModel, ResolvedRoom

# A slab filed on a different storey than the room it floors is still a low step-up, not a
# full storey. Bounding the match to this tolerance lets it catch that step-up while
# refusing to let, say, a main-storey room fall through to the basement slab a full storey
# below — every storey in this house is taller than 4' between finish floors, so nothing
# legitimate is lost.
SLAB_MATCH_TOLERANCE_M = 1.2192  # 4 ft


def room_floor_elevation(model: ResolvedModel, room: ResolvedRoom) -> float:
    """The absolute elevation (m) of ``room``'s floor.

    Defaults to the base of the first wall sharing the room's storey. Where a slab under
    the room's footprint sits closer to that default than ``SLAB_MATCH_TOLERANCE_M``,
    prefers the slab's top instead (see module docstring).
    """
    wall_z = 0.0
    for w in model.walls:
        if w.storey == room.storey:
            wall_z = w.z0_m
            break
    if not room.clear_face:
        return wall_z
    centroid = Polygon(room.clear_face).centroid
    best = None
    for solid in model.solids:
        if solid.category != "slab":
            continue
        if abs(solid.z1_m - wall_z) >= SLAB_MATCH_TOLERANCE_M:
            continue
        if not Polygon(solid.outline).contains(centroid):
            continue
        if best is None or abs(solid.z1_m - wall_z) < abs(best.z1_m - wall_z):
            best = solid
    return best.z1_m if best is not None else wall_z
