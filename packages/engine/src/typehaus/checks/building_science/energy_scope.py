"""What is inside the thermal boundary — and how much of it belongs to a zone.

The block load's two scoping questions, kept away from its arithmetic. First: which
storeys, walls and structures are envelope at all (an unconditioned garage, a bearing wall
with conditioned rooms on both faces, a freestanding garden wall filed on a house storey
key — none of them carry UA against the outdoor design air). Second: when the caller asks
for a *zone* rather than the whole house, what fraction of each envelope plane bounds it.

``checks.code.mn_energy`` imports :func:`_storey_is_conditioned` from here through the
``typehaus.energy`` facade rather than keeping its own copy: the block load and the
prescriptive table must agree about what the conditioned envelope is.
"""

from __future__ import annotations

from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M2_TO_FT2 = 10.7639104167

# Tag prefixes of freestanding, unoccupied structures (sunken-garden porch/retaining walls,
# raised-garden planter, the detached garage's slab, breezeway decking) that are filed on
# one of the house's own storey keys because they share the plan frame, so
# ``_storey_is_conditioned`` cannot see past them. Minimal duplicate of the same scoping in
# ``checks.code.mn_energy`` (read-only to this module) — the block load and the
# prescriptive table must agree about what the conditioned envelope is.
# Walls that stand outside the thermal boundary and must not be summed into a block load.
# "W-B-BRICK" is not a freestanding *structure* like the sunken garden or raised garden — it
# is a brick veneer wythe standing 1" off the basement's south wall — but it is freestanding
# in the only sense this list cares about: the envelope it appears to be is already counted.
# The thermal boundary there is CATLIN_BASEMENT_12 behind it (W-B-S2/W-B-S3), and the real
# glazing is WIN-B-SAUNA / D-B-PATIO in that wall. Without this the veneer adds its own
# nine-foot wall area plus two unglazed rough openings to the load, and the openings have no
# window type, so they land in ``unknown_inputs`` and take the sizing verdict with them.
_FREESTANDING_WALL_PREFIXES = ("W-SG-", "W-RG-", "W-B-BRICK")
_FREESTANDING_SLAB_PREFIXES = ("SL-SG-", "SL-G-", "SL-BW-")


def _storey_is_conditioned(plan: PlanModel, storey_tag: str) -> bool:
    """Does this storey hold any conditioned room?

    The block load sums UA against the *interior setpoint*, so a storey whose rooms are all
    unconditioned (catlin's detached garage, ``conditioned=False``) carries no such UA and
    must not be summed. ``checks.code.mn_energy`` imports this rather than keeping its own
    copy — the block load and the prescriptive table must agree about what the conditioned
    envelope is. A storey with no rooms at all stays in scope, because an empty storey is a
    modelling gap, not a declared unconditioned space.
    """
    rooms = [el for el in plan.storey_elements(storey_tag) if el.element_kind == "Room"]
    if not rooms:
        return True
    return any(room.conditioned for room in rooms)


def _is_envelope_wall(wall: ResolvedWall, model: ResolvedModel) -> bool:
    """Is this wall on the thermal boundary — clad above grade, or below grade?

    Interior partitions separate two rooms at the same setpoint, so they carry no UA
    against the outdoor design temperature; summing them (and the doors hosted in them)
    inflates the block load by the entire interior wall area and fills ``unknown_inputs``
    with closet doors that have no business in an envelope report. Cladding is the same
    above-grade marker the condensation check scopes itself with.

    ``is_foundation`` alone is not that marker. A basement's centre bearing walls are cast
    the same way its perimeter is and carry the same flag, but they have conditioned space on
    *both* faces: no ΔT, no UA, and the interior doors through them are not envelope doors.
    Catlin's nine interior foundation walls put 810 ft2 of bare concrete into the block load
    and four closet-grade doors into ``unknown_inputs``, which is what left
    ``mep.heating_capacity`` UNKNOWN on a zone whose margin the number then decided.
    """
    if any(layer.function == "cladding" for layer in wall.layers):
        return True
    return wall.is_foundation and not _stands_between_conditioned_rooms(wall, model)


# How far off a wall face to sample for the room on that side: half the wall depth clears the
# construction, and the extra 3" clears the room clear-face inset without reaching across a
# 4" partition into the room beyond.
_WALL_SIDE_PROBE_SLOP_M = 3 * 0.0254
# Fractions along the axis to probe. Three, not one: a wall may be a room's boundary over part
# of its run only, and one midpoint sample on a wall that runs past a room's corner lies.
_WALL_SIDE_PROBE_FRACTIONS = (0.25, 0.5, 0.75)


def _stands_between_conditioned_rooms(wall: ResolvedWall, model: ResolvedModel) -> bool:
    """Does conditioned space stand on both faces of this wall?

    Sampled from the resolved room polygons rather than asked of the wall, because a wall
    records at most the one ``interior_room`` it was authored against — a bearing wall
    between two finished basement rooms names one of them and knows nothing of the other.
    """
    from shapely.geometry import Point, Polygon

    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if run < 1e-9:
        return False
    tangent = ((x1 - x0) / run, (y1 - y0) / run)
    normal = (-tangent[1], tangent[0])
    offset = wall.thickness_m / 2 + _WALL_SIDE_PROBE_SLOP_M
    faces = [Polygon(room.clear_face) for room in model.rooms
             if room.storey == wall.storey and room.conditioned and len(room.clear_face) >= 3]
    for sign in (1, -1):
        probes = [Point(x0 + tangent[0] * run * t + normal[0] * offset * sign,
                        y0 + tangent[1] * run * t + normal[1] * offset * sign)
                  for t in _WALL_SIDE_PROBE_FRACTIONS]
        if not any(face.covers(probe) for face in faces for probe in probes):
            return False
    return True


_M3_TO_FT3 = 35.31466672148859

# How far past a room's clear face an envelope wall may sit and still be that room's wall:
# the clear face is offset inward from the wall centerline by half the wall depth plus the
# lining, so the buffer is the wall's own depth plus a little slop for the finish.
_WALL_SCOPE_SLOP_M = 0.05


def _conditioned_rooms(
    model: ResolvedModel, storeys: frozenset[str] | None, rooms: frozenset[str] | None,
) -> list[object]:
    return [room for room in model.rooms if room.conditioned
            and (rooms is None or room.tag in rooms)
            and (storeys is None or room.storey in storeys)]


def _volume_ft3(model: ResolvedModel, rooms: list[object]) -> float:
    """Conditioned volume as room clear-face area × the storey's default ceiling height.

    Approximate on purpose: rooms with a dropped or vaulted ceiling are not modeled with a
    per-room ceiling plane, and the air-side terms this feeds are proportional to volume, so
    the error is a percentage of one term rather than a hidden invented input.
    """
    heights = {storey.tag: storey.default_ceiling_height.meters
               for storey in model.plan.storeys}
    return sum(room.area_m2 * heights.get(room.storey, 0.0) for room in rooms) * _M3_TO_FT3


def _room_scope(model: ResolvedModel, rooms: frozenset[str]) -> dict[str, object]:
    """Per-storey union of the selected rooms' clear faces, for attributing envelope area."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    by_storey: dict[str, list[object]] = {}
    for room in model.rooms:
        if room.tag in rooms and len(room.clear_face) >= 3:
            by_storey.setdefault(room.storey, []).append(Polygon(room.clear_face))
    return {storey: unary_union(polygons) for storey, polygons in by_storey.items()}


def _wall_scope_fraction(wall: ResolvedWall, scope: dict[str, object] | None) -> float:
    """What fraction of this wall's run bounds the scoped rooms (1.0 for whole-house)."""
    if scope is None:
        return 1.0
    footprint = scope.get(wall.storey)
    if footprint is None:
        return 0.0
    from shapely.geometry import LineString

    axis = LineString(wall.axis)
    if axis.length <= 0:
        return 0.0
    reach = footprint.buffer(wall.thickness_m + _WALL_SCOPE_SLOP_M)
    return min(1.0, axis.intersection(reach).length / axis.length)


def _opening_in_scope(wall: ResolvedWall, opening, scope: dict[str, object] | None) -> bool:
    """Does this opening's own plan point stand against one of the scoped rooms?"""
    if scope is None:
        return True
    footprint = scope.get(wall.storey)
    if footprint is None:
        return False
    from shapely.geometry import Point

    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if run <= 0:
        return False
    t = min(1.0, opening.center_along_m / run)
    point = Point(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    return footprint.buffer(wall.thickness_m + _WALL_SCOPE_SLOP_M).contains(point)


def _polygon_scope_fraction(outline, storey: str,
                            scope: dict[str, object] | None) -> float:
    """What fraction of a roof/slab plan outline lies over the scoped rooms."""
    if scope is None:
        return 1.0
    footprint = scope.get(storey)
    if footprint is None or len(outline) < 3:
        return 0.0
    from shapely.geometry import Polygon

    plan = Polygon(outline)
    if plan.area <= 0:
        return 0.0
    # A roof or slab plane over a storey is shared by every room under it; buffering by the
    # wall depth lets a room claim the plane out to its enclosing walls' centerlines rather
    # than only over its clear face, so the zone areas sum back to (nearly) the whole plane.
    return min(1.0, plan.intersection(footprint.buffer(0.15)).area / plan.area)
