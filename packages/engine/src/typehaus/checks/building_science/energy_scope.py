"""What is inside the thermal boundary — and how much of it belongs to a zone.

The block load's two scoping questions, kept away from its arithmetic. First: which
storeys, walls and structures are envelope at all. Second: when the caller asks for a
*zone* rather than the whole house, what fraction of each envelope plane bounds it.

The first question used to be answered here, half by geometry and half by a tuple of one
house's tag prefixes. It now lives in :mod:`envelope_geometry`, derived and shared with
``checks.code.mn_energy`` so the block load and the prescriptive table cannot drift apart;
this module keeps :func:`_is_envelope_wall` as the two-argument front door onto it.
"""

from __future__ import annotations

from typehaus.checks.building_science.envelope_geometry import envelope_geometry
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M2_TO_FT2 = 10.7639104167


def _storey_is_conditioned(plan: PlanModel, storey_tag: str) -> bool:
    """Does this storey hold any conditioned room?

    A storey with no rooms at all stays in scope, because an empty storey is a modelling
    gap, not a declared unconditioned space.

    **The block load no longer uses this, and the policy is deliberately left alone for
    the three checks that do.** It is a coarse per-storey screen: catlin's detached garage
    shares the house's ``main`` storey key, so this admits the garage's walls and slab and
    the block load then needed a tag-prefix list to take them back out. ``envelope_geometry``
    answers per element instead. But *strengthening* this — say, requiring that the storey's
    rooms be conditioned where they exist — removes ``GARAGE_ICF_6`` from
    ``conditioned_envelope_assemblies``, which deletes the condensation FAIL that
    ``houses/catlin/CLAUDE.md`` records as the reason for the coil band's 1/4" vented
    standoff. ``checks.building_science.condensation``, ``checks.code.unvented_roof`` and
    ``checks.code.mn_energy`` want exactly the coarse answer: *could* this level hold
    conditioned space, i.e. is an assembly used here one whose vapour behaviour matters.
    """
    rooms = [el for el in plan.storey_elements(storey_tag) if el.element_kind == "Room"]
    if not rooms:
        return True
    return any(room.conditioned for room in rooms)


def _is_envelope_wall(wall: ResolvedWall, model: ResolvedModel) -> bool:
    """Is this wall on the thermal boundary? The two-argument front door onto
    :meth:`envelope_geometry.EnvelopeGeometry.is_envelope_wall`, whose module docstring
    carries the derivation and the measurements behind it."""
    return envelope_geometry(model).is_envelope_wall(wall)


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
