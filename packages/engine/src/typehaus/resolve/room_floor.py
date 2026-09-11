"""Where a room's floor actually sits — the one answer the whole pipeline shares.

Usually a room's storey walls bottom out exactly where its floor structure does, so the
wall base is a fine default. That assumption breaks when a room's real floor slab is filed
on a different storey than the room itself (the Catlin garage: its slab is poured at grade
and filed on "main", while its wood walls — and so the room — sit on the "garage" storey,
22" up on the ICF stem).

It lives in ``resolve`` rather than ``emit`` because ``resolve/placeables.py`` needs it too,
and needs it *before* either emitter runs: a placeable's mount elevation is measured off the
floor it stands on, not off its storey datum, or everything standing in the garage — the
hydrant, the workbench, every receptacle and switch — resolves 22" above the floor the
viewer draws under it.

Two planes, two functions, and mixing them up is a real 1 1/2" error:
:func:`room_floor_elevation` is the structure and :func:`room_finished_floor_elevation` is
what a foot lands on. Anything authored "AFF" wants the second. The storey CEILING plane
wants the first — it is fixed by the frame above, and a thicker carpet eats the clear height
rather than lifting the ceiling.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.resolve.model import ResolvedModel, ResolvedRoom
from typehaus.resolve.walking_surface import surfaces_at

# A slab filed on a different storey than the room it floors is still a low step-up, not a
# full storey. Bounding the match to this tolerance lets it catch that step-up while
# refusing to let, say, a main-storey room fall through to the basement slab a full storey
# below — every storey in this house is taller than 4' between finish floors, so nothing
# legitimate is lost.
SLAB_MATCH_TOLERANCE_M = 1.2192  # 4 ft


def room_floor_elevation(model: ResolvedModel, room: ResolvedRoom) -> float:
    """The absolute elevation (m) of ``room``'s STRUCTURAL floor — subfloor or slab top.

    Defaults to the base of the first wall sharing the room's storey. Where a slab under
    the room's footprint sits closer to that default than ``SLAB_MATCH_TOLERANCE_M``,
    prefers the slab's top instead (see module docstring).

    ** THIS IS NOT THE PLANE "ABOVE THE FLOOR" MEANS. ** The floor covering stands on it.
    Use :func:`room_finished_floor_elevation` for anything measured AFF; this one is for
    what bears on the structure — and for the storey ceiling plane, which is fixed by the
    frame above and does NOT rise when a thicker carpet goes down.
    """
    wall_z = 0.0
    for w in model.walls:
        if w.storey == room.storey:
            # ``base_ref_z_m``, not ``z0_m``: a clad wall's skin is run down over the mudsill
            # and rim to lap the foundation (``resolve/platform.extend_walls_to_foundation``),
            # so its ``z0_m`` is 13 7/16" under the floor it stands on. Reading that put every
            # main-storey room's floor — and so every ceiling light hung off it — a rim band
            # too low, and only once enough of the ring was dropped for the first matching
            # wall to be one of the dropped ones. Whichever wall answers first, the framing
            # datum is the floor.
            wall_z = w.base_ref_z_m
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


def room_finished_floor_elevation(model: ResolvedModel, room: ResolvedRoom) -> float:
    """The absolute elevation (m) of the plane a foot lands on in ``room``.

    "48 inches AFF" on a drawing means above the FINISHED floor, so this is what
    ``Mount.elevation`` is measured from and what a floor-standing placeable's base sits on.
    Three planes stack and only the last is it: the storey datum is the TOP OF JOISTS, the
    deck's ``deck_z1_m`` is the top of the subfloor sheet, and the covering stands on that.
    Reading the structural plane instead put every mount on catlin's second storey 15/16"
    low and every one in the attic 1 1/2" low, silently (plans/TODO.md — same root as the
    stair-arrival bug ``walking_surface`` was written for).

    The covering is the one standing at the room's centroid, which is not always the room's
    own ``floor_finish``: a deck carrying its own outranks it (``surfaces_at``), and catlin's
    RM-M-LIVING is exactly that — authored LVP, and its centroid on SL-M-DECK's polished cap,
    which IS the finished floor there.

    ** AN UNSOURCED COVERING RESOLVES TO THE DECK, AND THAT IS NOT A PASS. ** A resolver
    returns a number and has nowhere to put UNKNOWN, so a covering whose depth the catalog
    does not state falls back to the plane it would have stood on — the deck's own top, the
    best structural answer available. ``advisory.floor_finish_depth`` reports those rooms,
    because a check is where UNKNOWN can be said (decision #32).
    """
    structural = room_floor_elevation(model, room)
    if not room.clear_face:
        return structural
    # The structural answer is the ANCHOR, not the base: it is a wall base or a slab top and
    # so it misses the subfloor sheet over a joisted bay entirely. What it is good for is
    # picking which of the surfaces standing at this point is the one underfoot — the same
    # job ``SLAB_MATCH_TOLERANCE_M`` already did, and the reason a main-storey room does not
    # fall through to the basement slab.
    centroid = Polygon(room.clear_face).centroid
    best = None
    for surface in surfaces_at(model, (centroid.x, centroid.y)):
        if abs(surface.deck_top_m - structural) >= SLAB_MATCH_TOLERANCE_M:
            continue
        if best is None or (abs(surface.deck_top_m - structural)
                            < abs(best.deck_top_m - structural)):
            best = surface
    if best is None:
        return structural
    return best.deck_top_m if best.surface_m is None else best.surface_m
