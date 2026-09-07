"""The world one route is searched in: obstacles, corridors, weights, and a bounding box.

A :class:`RoutingSpace` is built **once per run** and inflated by that run's own radius,
which is the difference between this package and the checks it is aimed at: a check grades
many runs against one geometry and corrects per query; a router grades one run against
many geometries and the correction belongs in the world.

It is also where the search is **bounded, explicitly**. The lattice is pruned to the
terminals' bounding box plus a margin and to the storeys they touch, and past
:data:`MAX_CANDIDATE_LINES` the build **raises** rather than coarsening quietly. A router
that silently drops resolution to finish is a router that answers a different question
from the one asked, and AGENTS.md §2.3 is explicit about which of the two is worse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.routing.corridors import (
    Corridor,
    crossing_window,
    floor_corridors,
    soffit_corridors,
    wall_corridors,
)
from typehaus.routing.cost import RouteCost
from typehaus.routing.obstacles import (
    CLEARANCE_M,
    HardPrism,
    SoftPrism,
    hard_prisms,
    soft_prisms,
)

#: How many candidate lines the graph may build before the space refuses. Four hundred is
#: roughly a 20x20 lattice on both plan axes, which is far past anything a house needs and
#: comfortably inside what A* explores in a second. **Raise it deliberately** if a real
#: model needs more; do not make the world coarser to fit under it.
MAX_CANDIDATE_LINES = 400

#: Default margin round the terminals' bounding box, in feet. Eight is about the width of
#: a room: enough for a route to step out of the direct line and back, and small enough
#: that a two-fixture branch does not build a lattice for the whole house.
DEFAULT_MARGIN_FT = 8.0


class RoutingSpaceTooLarge(RuntimeError):
    """The lattice would exceed :data:`MAX_CANDIDATE_LINES`.

    Raised rather than handled, on purpose. The caller's options are to narrow the margin,
    split the problem, or raise the cap having looked at why — and all three are decisions
    a person makes, not a default a library picks.
    """


@dataclass
class RoutingSpace:
    """Everything one search needs, and nothing about the search itself."""

    radius_m: float
    clearance_m: float
    cost: RouteCost
    hard: list[HardPrism]
    soft: list[SoftPrism]
    corridors: list[Corridor]
    bbox: tuple[float, float, float, float]
    storeys: tuple[str, ...]
    #: Per-floor z windows for a run CROSSING that floor's members — see
    #: ``corridors.crossing_window``. Keyed by floor tag.
    crossings: dict[str, tuple[float, float]] = field(default_factory=dict)

    def blocked(self, point: tuple[float, float], z: float) -> str | None:
        """The tag of the first hard prism containing this point, or None.

        Returns the tag rather than a bool because every refusal in this package should be
        able to say what refused it — ``--explain`` prints it, and "no feasible route" with
        no reason is the output nobody can act on.
        """
        for prism in self.hard:
            if prism.blocks(point, z):
                return prism.tag
        return None

    def soft_at(self, point: tuple[float, float], z: float) -> list[SoftPrism]:
        from shapely.geometry import Point

        probe = Point(point)
        return [prism for prism in self.soft
                if prism.z0_m <= z <= prism.z1_m and prism.footprint.covers(probe)]

    def corridor_at(self, axis: str, station: float, lo: float, hi: float,
                    z: float) -> Corridor | None:
        """The cheapest corridor a segment on this line and elevation rides, if any."""
        best: Corridor | None = None
        for corridor in self.corridors:
            if corridor.axis != axis or not corridor.admits(self.radius_m):
                continue
            if abs(corridor.station - station) > self.radius_m + self.clearance_m:
                continue
            window = corridor.z_window(self.radius_m)
            if window is None or not (window[0] <= z <= window[1]):
                continue
            if lo < corridor.lo_m - 1e-6 or hi > corridor.hi_m + 1e-6:
                continue
            if best is None or corridor.clear_width_m > best.clear_width_m:
                best = corridor
        return best


def build_space(model, *, radius_m: float, terminals, cost: RouteCost | None = None,
                margin_ft: float = DEFAULT_MARGIN_FT,
                avoid: frozenset[str] = frozenset(),
                clearance_m: float = CLEARANCE_M) -> RoutingSpace:
    """Inflate the world once for a run of this radius, bounded around its terminals.

    ``terminals`` is any iterable of ``(x, y)`` or ``(x, y, z)`` — the points the route has
    to reach. They set the bounding box; the margin sets how far outside it the search may
    step to get round something.
    """
    points = [(t[0], t[1]) for t in terminals]
    if not points:
        raise ValueError("a routing space needs at least one terminal")
    margin_m = margin_ft * 0.3048
    minx = min(p[0] for p in points) - margin_m
    maxx = max(p[0] for p in points) + margin_m
    miny = min(p[1] for p in points) - margin_m
    maxy = max(p[1] for p in points) + margin_m

    from shapely.geometry import box

    window = box(minx, miny, maxx, maxy)
    hard = [prism for prism in hard_prisms(model, radius_m, avoid=avoid,
                                           clearance_m=clearance_m)
            if prism.footprint.intersects(window)]
    soft = [prism for prism in soft_prisms(model)
            if prism.footprint.intersects(window)]
    corridors = [corridor for corridor in
                 (*floor_corridors(model), *soffit_corridors(model),
                  *wall_corridors(model))
                 if corridor.admits(radius_m)
                 and _corridor_in(corridor, minx, miny, maxx, maxy)]

    lines = len({(c.axis, round(c.station, 6)) for c in corridors}) + 2 * len(points)
    if lines > MAX_CANDIDATE_LINES:
        raise RoutingSpaceTooLarge(
            f"{lines} candidate lines from {len(corridors)} corridors and "
            f"{len(points)} terminals exceeds MAX_CANDIDATE_LINES="
            f"{MAX_CANDIDATE_LINES}. Narrow --margin, split the problem, or raise the cap "
            "deliberately — do not coarsen the world to fit under it")

    crossings = {}
    for floor in model.floors:
        band = crossing_window(model, floor)
        if band is not None:
            crossings[floor.tag] = band

    storeys = tuple(sorted({s.tag for s in model.plan.storeys}))
    return RoutingSpace(radius_m=radius_m, clearance_m=clearance_m,
                        cost=cost or RouteCost(), hard=hard, soft=soft,
                        corridors=corridors, bbox=(minx, miny, maxx, maxy),
                        storeys=storeys, crossings=crossings)


def _corridor_in(corridor: Corridor, minx: float, miny: float,
                 maxx: float, maxy: float) -> bool:
    if corridor.axis == "x":
        return (miny <= corridor.station <= maxy
                and corridor.hi_m >= minx and corridor.lo_m <= maxx)
    return (minx <= corridor.station <= maxx
            and corridor.hi_m >= miny and corridor.lo_m <= maxy)
