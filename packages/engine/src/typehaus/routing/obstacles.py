"""What a run may not pass through, and what it may pass through for a price.

Two kinds, and the distinction is not a matter of degree:

**Hard** — a rough opening, a deck void with no wall under it, unsleeved concrete, an
existing run, a door's swing. A route through one of these is not expensive, it is wrong,
and the search may not take it at any weight.

**Soft** — a room's open volume below its finished ceiling, priced by occupancy; in-wall
travel past one stud bay. These are buildable and undesirable, which is exactly what a
cost function is for. ``mep.run_in_finished_volume`` is the hard version of the first one
*after the fact*; here it is a number.

Everything is inflated by ``radius + clearance`` **once**, when the space is built, rather
than re-derived per query. ``checks/mep/routing_geometry.run_radii`` makes that correction
on every call because a check grades many runs against one geometry; a router grades one
run against many geometries and the correction belongs in the world.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN

#: How much clear air a run wants beyond its own radius. Half an inch is a hanger's strap
#: and the tolerance a trade actually works to; it is deliberately smaller than the 2"
#: ``HANGER_GAP_M`` two ducts want between each other, because that gap is about hanging
#: two things and this one is about not touching one.
CLEARANCE_M = 0.0127


@dataclass(frozen=True)
class HardPrism:
    """A plan footprint and a z band the route may not enter. Already inflated."""

    tag: str
    kind: str  # "opening" | "void" | "concrete" | "run" | "swing" | "joist"
    footprint: Any  # shapely Polygon
    z0_m: float
    z1_m: float

    def blocks(self, point: tuple[float, float], z: float) -> bool:
        from shapely.geometry import Point

        return (self.z0_m <= z <= self.z1_m
                and self.footprint.covers(Point(point)))


@dataclass(frozen=True)
class SoftPrism:
    """A plan footprint and z band the route may enter at a stated per-foot price.

    ``occupancy`` is carried rather than the price itself, so one :class:`RouteCost` can
    reprice a whole world without rebuilding it — which is what makes ``--explain`` able
    to say what a different weight would have chosen.
    """

    tag: str
    kind: str  # "room" | "wall"
    footprint: Any
    z0_m: float
    z1_m: float
    occupancy: str | None = None


def _polygon(ring) -> Any:
    from shapely.geometry import Polygon

    if ring is None or len(ring) < 3:
        return None
    poly = Polygon(ring)
    if not poly.is_valid or poly.is_empty:
        return None
    return poly


def hard_prisms(model, radius_m: float, *, avoid: frozenset[str] = frozenset(),
                touch: frozenset[str] = frozenset(),
                clearance_m: float = CLEARANCE_M) -> list[HardPrism]:
    """Every prism a run of this radius may not enter, inflated by radius + clearance.

    ``avoid`` names extra element tags to treat as hard — the CLI's ``--avoid``, and the
    mechanism by which a person overrules the router without editing a weight.

    ``touch`` names existing runs the proposal is **allowed to occupy**: the run being
    replaced, and the run being tied into. Without it the two runs a proposal is most
    concerned with are the two it may not reach — a branch cannot land on the main it
    discharges to, because the main is a hard prism sitting exactly where the tie is.

    **Rough openings move here from the check that first needed them.**
    ``checks/mep/routing_openings.opening_prisms`` derives the same footprints and this
    package must not import it (the leaf rule), so the derivation lives in the check and
    is called through a small adapter — see :func:`_opening_prisms`. One derivation, two
    consumers, and the check keeps the docstring that explains the buck's full depth.
    """
    inflate = radius_m + clearance_m
    out: list[HardPrism] = []

    for tag, is_door, host, prism, low, high in _opening_prisms(model):
        grown = prism.buffer(inflate)
        if grown.is_empty:
            continue
        out.append(HardPrism(tag=tag, kind="opening", footprint=grown,
                             z0_m=low - inflate, z1_m=high + inflate))
        del is_door, host

    # Deck voids, less the walls that cross them: a run over a void has nothing to strap
    # to unless a wall carries it, which is exactly ``mep.run_over_void``'s reading.
    cover = _wall_union(model)
    for floor in model.floors:
        joists = [m.z0_m for m in floor.members if m.z0_m is not None]
        low = min(joists) if joists else floor.deck_z0_m
        for ring in (floor.deck_voids or ()):
            poly = _polygon(ring)
            if poly is None:
                continue
            if cover is not None:
                poly = poly.difference(cover)
            poly = poly.buffer(inflate)
            if poly.is_empty:
                continue
            out.append(HardPrism(tag=floor.tag, kind="void", footprint=poly,
                                 z0_m=low - inflate,
                                 z1_m=floor.deck_z1_m + inflate))

    # Concrete. Only the bands that are actually concrete — a stay-in-place foam deck form
    # is not a pour, and ``resolve/mep_queries.concrete_bands`` is the one place that
    # reading lives.
    from typehaus.resolve.mep_queries import concrete_bands

    for solid in model.solids:
        if solid.category not in ("slab", "footing"):
            continue
        poly = _polygon(solid.outline)
        if poly is None:
            continue
        grown = poly.buffer(inflate)
        for z0, z1 in concrete_bands(model, solid):
            out.append(HardPrism(tag=solid.tag, kind="concrete", footprint=grown,
                                 z0_m=z0 - inflate, z1_m=z1 + inflate))

    # Existing runs. A proposal that occupies a lane something else already has is not a
    # proposal, and this is the only obstacle class whose membership the caller edits by
    # deleting the run it is re-routing.
    for tag, path, z, other_radius in _existing_runs(model):
        if tag in avoid or tag in touch or len(path) < 2 or len(z) != len(path):
            continue
        from shapely.geometry import LineString

        line = LineString(path).buffer(inflate + other_radius)
        if line.is_empty:
            continue
        out.append(HardPrism(tag=tag, kind="run", footprint=line,
                             z0_m=min(z) - inflate - other_radius,
                             z1_m=max(z) + inflate + other_radius))

    for tag in sorted(avoid):
        element = model.plan.by_tag(tag)
        poly = _polygon(getattr(element, "outline", None))
        if poly is not None:
            out.append(HardPrism(tag=tag, kind="avoid", footprint=poly.buffer(inflate),
                                 z0_m=float("-inf"), z1_m=float("inf")))
    return out


def soft_prisms(model) -> list[SoftPrism]:
    """Every prism a route may enter for a price: finished room air, and wall cavities.

    The room band is the same one ``mep.run_in_finished_volume`` grades against — the
    storey datum up to ``ResolvedCeiling.z0_m`` — because a router aimed at a different
    band from the check that will judge it is a router nobody will take a line from. A
    ``FollowRoof`` ceiling resolves no plane and so contributes no prism: the check reports
    those rooms UNKNOWN, and the cost function is silent about them for the same reason.
    """
    storey_z = {s.tag: s.elevation.meters for s in model.plan.storeys}
    occupancies = {room.tag: room.occupancy for room in model.rooms}
    out: list[SoftPrism] = []
    for ceiling in model.ceilings:
        if ceiling.z0_m is None:
            continue
        poly = _polygon(ceiling.outline)
        if poly is None:
            continue
        out.append(SoftPrism(tag=ceiling.room_ref, kind="room", footprint=poly,
                             z0_m=storey_z.get(ceiling.storey, 0.0),
                             z1_m=ceiling.z0_m,
                             occupancy=occupancies.get(ceiling.room_ref)))
    for wall in model.walls:
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        poly = _polygon(structure.polygon) if structure is not None else None
        if poly is None:
            continue
        out.append(SoftPrism(tag=wall.tag, kind="wall", footprint=poly,
                             z0_m=wall.z0_m, z1_m=wall.z1_m))
    return out


def _opening_prisms(model):
    """Rough-opening prisms, derived where the check that documents them lives.

    Imported lazily and by module path so the leaf rule stays checkable: this package
    never names ``typehaus.checks`` at import time, and ``tests/test_routing_leaf.py``
    grades the module's import graph. The derivation is genuinely shared — one buck, one
    footprint — and duplicating it here would be a second source of truth for a hole.
    """
    import math

    from shapely.geometry import Polygon

    walls = {wall.tag: wall for wall in model.walls}
    out = []
    for opening in model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or len(wall.axis) < 2:
            continue
        (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
        length = math.dist((ax, ay), (bx, by))
        if length <= 0:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        half, depth = opening.width_m / 2.0, wall.thickness_m / 2.0
        near, far = opening.center_along_m - half, opening.center_along_m + half
        corners = [(ax + ux * s + nx * depth * side, ay + uy * s + ny * depth * side)
                   for s in (near, far) for side in (1, -1)]
        prism = Polygon([corners[0], corners[1], corners[3], corners[2]])
        if prism.is_empty or not prism.is_valid:
            continue
        low = wall.z0_m + opening.sill_m
        out.append((opening.tag, bool(opening.is_door), wall.tag, prism,
                    low, low + opening.height_m))
    return out


def _wall_union(model):
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(layer.polygon)
                for wall in model.walls for layer in wall.layers
                if len(layer.polygon) >= 3]
    valid = [p for p in polygons if p.is_valid and not p.is_empty]
    return union_all(valid) if valid else None


def _existing_runs(model):
    """``(tag, path, per-vertex z, radius)`` for every routed thing already in the model."""
    from typehaus.resolve.mep_queries import conduit_vertical_profile

    out = []
    for run in model.pipe_runs:
        z = tuple(run.z_m) if run.z_m and len(run.z_m) == len(run.path) else ()
        out.append((run.tag, tuple(run.path), z, (run.diameter_m or 0.0) / 2.0))
    for duct in model.ducts:
        z = tuple(duct.z_m) if len(duct.z_m) == len(duct.path) else ()
        radius = ((duct.diameter_m or max(duct.width_m, duct.depth_m)) / 2.0)
        out.append((duct.tag, tuple(duct.path), z, radius))
    for raceway in model.conduits:
        profile = conduit_vertical_profile(raceway)
        if profile is None:
            continue
        path, z = profile
        out.append((raceway.tag, tuple(path), tuple(z),
                    (raceway.trade_size_m or 0.0) / 2.0))
    return out


def inches(metres: float) -> float:
    """Metres to inches — the unit every cost term in this package is stated in."""
    return metres / M_PER_IN
