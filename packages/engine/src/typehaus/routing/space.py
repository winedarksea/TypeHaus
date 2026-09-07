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

#: How many lattice nodes the graph may build. The line caps above do not bound this —
#: 400 x 400 x 60 is inside both of them and is nine million nodes — so this is the guard
#: that actually holds. Fifty thousand is comfortably past a whole-storey problem and well
#: inside a second of A*; it RAISES rather than coarsening, for the reason above.
MAX_LATTICE_NODES = 120_000

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
    #: Plan indices over ``hard`` and ``soft``, built lazily on first query. A lattice asks
    #: "what is here" once per node and twice per edge, so a linear scan over a hundred
    #: prisms is the whole cost of building a graph. Measured on the catlin suite-bath
    #: problem, indexing is worth roughly an order of magnitude on the graph build.
    _hard_index: object | None = field(default=None, repr=False, compare=False)
    _soft_index: object | None = field(default=None, repr=False, compare=False)
    #: Corridors bucketed by ``(axis, station rounded to 1/16")``. ``corridor_at`` is called
    #: once per lattice EDGE, so a linear scan over a hundred-odd corridors is tens of
    #: millions of comparisons on a real problem and was the single largest cost in
    #: building a graph — larger than the shapely work it sits beside.
    _corridor_index: dict | None = field(default=None, repr=False, compare=False)

    def _index(self, which: str):
        from shapely import STRtree

        cached = self._hard_index if which == "hard" else self._soft_index
        if cached is None:
            prisms = self.hard if which == "hard" else self.soft
            cached = STRtree([p.footprint for p in prisms])
            if which == "hard":
                self._hard_index = cached
            else:
                self._soft_index = cached
        return cached

    def blocked(self, point: tuple[float, float], z: float) -> str | None:
        """The tag of the first hard prism containing this point, or None.

        Returns the tag rather than a bool because every refusal in this package should be
        able to say what refused it — ``--explain`` prints it, and "no feasible route" with
        no reason is the output nobody can act on.
        """
        from shapely.geometry import Point

        if not self.hard:
            return None
        probe = Point(point)
        for index in self._index("hard").query(probe):
            prism = self.hard[int(index)]
            if prism.z0_m <= z <= prism.z1_m and prism.footprint.covers(probe):
                return prism.tag
        return None

    def soft_at(self, point: tuple[float, float], z: float) -> list[SoftPrism]:
        from shapely.geometry import Point

        if not self.soft:
            return []
        probe = Point(point)
        return [self.soft[int(i)] for i in self._index("soft").query(probe)
                if self.soft[int(i)].z0_m <= z <= self.soft[int(i)].z1_m
                and self.soft[int(i)].footprint.covers(probe)]

    def corridor_at(self, axis: str, station: float, lo: float, hi: float,
                    z: float) -> Corridor | None:
        """The widest corridor a segment on this line and elevation rides, if any.

        Widest rather than first, because a segment lying in both a bay and the wall over
        it should be priced as the bay — the channel that actually carries it.
        """
        if self._corridor_index is None:
            index: dict = {}
            tolerance = self.radius_m + self.clearance_m
            for corridor in self.corridors:
                if not corridor.admits(self.radius_m):
                    continue
                # Bucket by the stations a query within `tolerance` could name, so a lookup
                # is one dict hit rather than a scan. The buckets are 1/16" wide, the same
                # grid every coordinate in this repo is authored on.
                low = int((corridor.station - tolerance) / 0.0015875)
                high = int((corridor.station + tolerance) / 0.0015875)
                for key in range(low, high + 1):
                    index.setdefault((corridor.axis, key), []).append(corridor)
            self._corridor_index = index
        bucket = self._corridor_index.get((axis, int(station / 0.0015875)), ())

        best: Corridor | None = None
        for corridor in bucket:
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
                touch: frozenset[str] = frozenset(),
                clearance_m: float = CLEARANCE_M) -> RoutingSpace:
    """Inflate the world once for a run of this radius, bounded around its terminals.

    ``terminals`` is any iterable of ``(x, y)`` or ``(x, y, z)`` — the points the route has
    to reach. They set the bounding box; the margin sets how far outside it the search may
    step to get round something.

    ``touch`` names the existing runs this proposal may occupy — the one it replaces and
    the one it ties into. See :func:`~typehaus.routing.obstacles.hard_prisms`.
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
    hard = [prism for prism in hard_prisms(model, radius_m, avoid=avoid, touch=touch,
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
