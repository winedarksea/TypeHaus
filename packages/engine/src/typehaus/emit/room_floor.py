"""Where a room's floor actually sits — shared by the glTF viewer and the IFC exporter.

Usually a room's storey walls bottom out exactly where its floor structure does, so the
wall base is a fine default. That assumption breaks when a room's real floor slab is filed
on a different storey than the room itself (the Catlin garage: its slab is poured at grade
and filed on "main", while its wood walls — and so the room — sit on the "garage" storey,
22" up on the ICF stem). Both emitters need the same answer here, or the viewer and the IFC
export disagree about where the garage floor is.
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
