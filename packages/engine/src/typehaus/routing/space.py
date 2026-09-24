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
from typing import TYPE_CHECKING, Any

from typehaus.routing.corridor_lanes import lane_corridors
from typehaus.routing.corridors import (
    Corridor,
    chase_corridors,
    crossing_window,
    floor_corridors,
    soffit_corridors,
    wall_corridors,
)
from typehaus.routing.cost import RouteCost

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

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
#: that actually holds. It RAISES rather than coarsening, as above.
#:
#: **Raised from 120,000 to 150,000, having looked at why** (→ Phase 7,
#: ``tests/test_routing_perf_guard.py``). When the lattice was derived over the whole z band
#: and laid down on every plane in it, catlin's worst duct wanted 780,066 nodes and half the
#: ducts in the house refused; per-level derivation took the worst case to 123,248, and the
#: old cap sat 2.7% under it. One number away from letting every target in the house build a
#: lattice is exactly the case this constant's own instruction was written for. It is NOT a
#: statement that 150,000 nodes is quick: a lattice that size is tens of seconds of graph
#: build, which ``--timing`` reports and nothing here hides.
#:
#: **Raised again to 250,000 on 2026-09-19, and the cause is stated rather than absorbed.**
#: Two capabilities landed together (E6): ``graph._corridor_levels`` offers an OCCUPIED
#: channel its two tiers instead of one midpoint, and ``corridor_lanes`` offers an occupied
#: bay its free lane beside the centreline. Each is a plane or a line the router did not
#: have, and each is the thing that lets it reproduce a layout a person authored — two 4"
#: ducts stacked in an 8 7/8" web window, or side by side in a 12 1/2" bay.
#:
#: Catlin's worst duct, ``DU-B-ERV-R-SAUNA-SUP``, measured at each step:
#:
#:     123,248   9 levels   before E6
#:     151,826  11 levels   tiers + lanes, tiers inset by the clearance
#:     203,518  13 levels   tiers at the window's own EXTREMES, which is the buildable pair
#:
#: The middle row is a bug this constant nearly absorbed. Insetting the tiers by a further
#: clearance put them 3 7/8" apart in an 8 7/8" window, so neither of the two 4" ducts the
#: window actually takes would fit — the geometry refused the thing the tiers were added to
#: allow, and it refused it cheaply, which is how a cap comes to look satisfied. The
#: extremes are 4 7/8" apart and buildable, they qualify far more corridors, and they cost
#: 34% more nodes.
#:
#: Dropping the tiers to fit would have been the wrong trade and is worth saying out loud:
#: the cap exists to stop a lattice nobody can search, and what it would have bought here
#: is a router that refuses a bay a fitter would use. The cost is measured, not guessed —
#: worst case builds its graph in 7.1 s and searches it in 0.7 s (`--timing`, measured),
#: and the perf guard's own assertion is the number.
#:
#: **350,000 on 2026-09-24, and this time no capability moved: the house got denser.** The
#: same duct measured 279,016 before the ERV/vent clearance campaign and 308,441 after it —
#: new runs and humps are new prisms, and each prism's edges are lines on every level it
#: cuts. It builds in 15.1 s, searches in 1.8 s and peaks at 680 MB (`--timing`, measured).
MAX_LATTICE_NODES = 350_000

#: Default margin round the terminals' bounding box, in feet. Eight is about the width of
#: a room: enough for a route to step out of the direct line and back, and small enough
#: that a two-fixture branch does not build a lattice for the whole house.
DEFAULT_MARGIN_FT = 8.0

#: The grid the memos round onto: a sixteenth of an inch, which is what every coordinate in
#: this repo is authored on. Finer would memoise float noise; coarser would answer a
#: different question from the one asked.
_GRID_M = 0.0015875


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
    #: ``--level``'s band: the z range of one storey, or None for the whole model.
    #: ``candidate_lines`` drops every level outside it, which is what makes the option
    #: *do* something — it used to validate the storey name and then change nothing, so a
    #: route asked to stay on one floor happily rode a bay on another.
    z_band: tuple[float, float] | None = None
    #: Plan indices over ``hard`` and ``soft``, built lazily on first query. A lattice asks
    #: "what is here" once per node and twice per edge, so a linear scan over a hundred
    #: prisms is the whole cost of building a graph. Measured on the catlin suite-bath
    #: problem, indexing is worth roughly an order of magnitude on the graph build.
    _hard_index: Any = field(default=None, repr=False, compare=False)
    _soft_index: Any = field(default=None, repr=False, compare=False)
    #: Corridors bucketed by ``(axis, station rounded to 1/16")``. ``corridor_at`` is called
    #: once per lattice EDGE, so a linear scan over a hundred-odd corridors is tens of
    #: millions of comparisons on a real problem and was the single largest cost in
    #: building a graph — larger than the shapely work it sits beside.
    _corridor_index: dict[tuple[str, int], list[Corridor]] | None = field(
        default=None, repr=False, compare=False)
    #: **Off by default, and measured.** A memo over ``blocked``/``soft_at`` keyed on the
    #: 1/16" grid costs about 45% of a single graph build and saves nothing in it: one build
    #: asks each node once, so every lookup is a miss plus a key. It pays only when one
    #: space is searched more than once — a campaign over a storey, where the prism edges
    #: are identical target to target and only the terminals' own lines differ. So the
    #: caller that knows it is reusing turns it on, and a one-shot route does not pay for a
    #: cache it will never read.
    reuse: bool = False
    #: The memo itself. Rounding onto the grid is safe because nothing in this package
    #: authors a coordinate finer than it; a point that rounds onto another is that point.
    _blocked_memo: dict[tuple[int, int, int], str | None] = field(
        default_factory=dict, repr=False, compare=False)
    _soft_memo: dict[tuple[int, int, int], list[SoftPrism]] = field(
        default_factory=dict, repr=False, compare=False)
    #: Floor members a run may CROSS but not ride: ``(axis, station, lo, hi, half breadth,
    #: z0, z1, tag)`` per level joist, rim, trimmer or header in the window — see
    #: :func:`floor_rails`. Not hard prisms, so they add no lattice lines.
    rails: list[tuple] = field(default_factory=list)
    _rail_index: Any = field(default=None, repr=False, compare=False)
    #: Per hard prism: its footprint eroded by a sixteenth, prepared, when the midpoint
    #: test cannot be trusted for it — see :meth:`edge_blocked`. None for a boxy prism.
    _exact: list[Any] | None = field(default=None, repr=False, compare=False)

    def _index(self, which: str) -> Any:
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

    def _grid_key(self, point: tuple[float, float], z: float) -> tuple[int, int, int]:
        return (round(point[0] / _GRID_M), round(point[1] / _GRID_M), round(z / _GRID_M))

    def blocked(self, point: tuple[float, float], z: float) -> str | None:
        """The tag of the first hard prism containing this point, or None.

        Returns the tag rather than a bool because every refusal in this package should be
        able to say what refused it — ``--explain`` prints it, and "no feasible route" with
        no reason is the output nobody can act on.
        """
        from shapely.geometry import Point

        if not self.hard:
            return None
        if not self.reuse:
            probe = Point(point)
            for index in self._index("hard").query(probe):
                prism = self.hard[int(index)]
                if prism.z0_m <= z <= prism.z1_m and prism.footprint.covers(probe):
                    return prism.tag
            return None
        key = self._grid_key(point, z)
        if key in self._blocked_memo:
            return self._blocked_memo[key]
        probe = Point(point)
        for index in self._index("hard").query(probe):
            prism = self.hard[int(index)]
            if prism.z0_m <= z <= prism.z1_m and prism.footprint.covers(probe):
                self._blocked_memo[key] = prism.tag
                return prism.tag
        self._blocked_memo[key] = None
        return None

    def blocked_all(self, point: tuple[float, float], z: float) -> frozenset[str]:
        """Every hard prism's tag containing this point — what a terminal stands in."""
        from shapely.geometry import Point

        if not self.hard:
            return frozenset()
        probe = Point(point)
        return frozenset(self.hard[int(i)].tag for i in self._index("hard").query(probe)
                         if self.hard[int(i)].z0_m <= z <= self.hard[int(i)].z1_m
                         and self.hard[int(i)].footprint.covers(probe))

    def edge_blocked(self, a: tuple[float, float], b: tuple[float, float], za: float,
                     zb: float, *, ignore: frozenset[str] = frozenset()) -> str | None:
        """The first hard prism a lattice edge passes through, or None.

        The midpoint is exact for a boxy prism on a horizontal edge: the lattice's lines are
        its offset edges, so a step cannot enter and leave it between two nodes. It is not
        exact for a RISER, whose midpoint misses a thin prism anywhere else on its rise, nor
        for an OBLIQUE or round footprint, which a step can clip at a corner. Those two are
        tested against the segment itself. ``ignore`` names what the step's own terminal
        stands in — see ``graph.build_graph`` — and nothing else is pardoned.
        """
        from shapely.geometry import LineString, Point

        if not self.hard:
            return None
        if not ignore:
            hit = self.blocked(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), (za + zb) / 2.0)
            if hit is not None:
                return hit
        riser = abs(a[0] - b[0]) + abs(a[1] - b[1]) < _GRID_M
        low, high = sorted((za, zb))
        probe = Point(a) if riser else LineString([a, b])
        exact = self._exact_footprints()
        for index in self._index("hard").query(probe):
            prism = self.hard[int(index)]
            if prism.tag in ignore:
                continue
            if riser:
                # Open on both ends: a riser standing ON a prism's top is not inside it.
                if (prism.z0_m < high - _GRID_M and prism.z1_m > low + _GRID_M
                        and prism.footprint.covers(probe)):
                    return prism.tag
                continue
            if not prism.z0_m <= (za + zb) / 2.0 <= prism.z1_m:
                continue
            shape = exact[int(index)]
            if ignore and shape is None:
                if prism.footprint.covers(Point(((a[0] + b[0]) / 2.0,
                                                 (a[1] + b[1]) / 2.0))):
                    return prism.tag
            elif shape is not None and shape.intersects(probe):
                return prism.tag
        return None if riser else self._rail_blocked(a, b, (za + zb) / 2.0)

    def _rail_blocked(self, a: tuple[float, float], b: tuple[float, float],
                      z: float) -> str | None:
        """A level step riding along inside a floor member: its removal, not a bore."""
        from shapely import STRtree
        from shapely.geometry import LineString, box

        if not self.rails:
            return None
        if self._rail_index is None:
            self._rail_index = STRtree([
                box(lo, station - half, hi, station + half) if axis == "x"
                else box(station - half, lo, station + half, hi)
                for axis, station, lo, hi, half, _z0, _z1, _tag in self.rails])
        axis = "x" if abs(b[0] - a[0]) > abs(b[1] - a[1]) else "y"
        station = a[1] if axis == "x" else a[0]
        grow = self.radius_m + self.clearance_m
        for i in self._rail_index.query(LineString([a, b])):
            rail_axis, rail_station, lo, hi, half, z0, z1, tag = self.rails[int(i)]
            if rail_axis != axis or abs(station - rail_station) >= half + grow - _GRID_M:
                continue
            if not z0 - grow < z < z1 + grow:
                continue
            start, end = sorted((a[0], b[0]) if axis == "x" else (a[1], b[1]))
            if min(end, hi) - max(start, lo) > _GRID_M:
                return tag
        return None

    def _exact_footprints(self) -> list[Any]:
        """See :attr:`_exact`. A footprint filling under 90% of its bounding box is one the
        midpoint can miss — a buffered riser is 79%, an oblique run far less."""
        from shapely import prepared

        if self._exact is None:
            out: list[Any] = []
            for prism in self.hard:
                bounds = prism.footprint.envelope.area
                boxy = bounds <= 0 or prism.footprint.area / bounds >= 0.9
                out.append(None if boxy
                           else prepared.prep(prism.footprint.buffer(-_GRID_M)))
            self._exact = out
        return self._exact

    def soft_at(self, point: tuple[float, float], z: float) -> list[SoftPrism]:
        from shapely.geometry import Point

        if not self.soft:
            return []
        key = self._grid_key(point, z) if self.reuse else None
        if key is not None:
            hit = self._soft_memo.get(key)
            if hit is not None:
                return hit
        probe = Point(point)
        found = [self.soft[int(i)] for i in self._index("soft").query(probe)
                 if self.soft[int(i)].z0_m <= z <= self.soft[int(i)].z1_m
                 and self.soft[int(i)].footprint.covers(probe)]
        if key is not None:
            self._soft_memo[key] = found
        return found

    def corridor_at(self, axis: str, station: float, lo: float, hi: float,
                    z: float) -> Corridor | None:
        """The widest corridor a segment on this line and elevation rides, if any.

        Widest rather than first, because a segment lying in both a bay and the wall over
        it should be priced as the bay — the channel that actually carries it.
        """
        if self._corridor_index is None:
            index: dict[tuple[str, int], list[Corridor]] = {}
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


def build_space(model: ResolvedModel, *, radius_m: float,
                terminals: Any, cost: RouteCost | None = None,
                margin_ft: float = DEFAULT_MARGIN_FT,
                avoid: frozenset[str] = frozenset(),
                touch: frozenset[str] = frozenset(),
                z_band: tuple[float, float] | None = None,
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
    bays = floor_corridors(model)
    # **The free lane of an occupied bay, beside its centreline.** A 12 1/2" truss bay
    # holding one 4" duct has 8 1/2" left and none of it is on the centreline — the
    # occupant is sitting there. ``corridor_lanes`` derives where the width actually is
    # and offers it as a second corridor with ITS OWN width; the centreline one stays,
    # because a bay whose occupant sits off-centre still has its centreline free.
    bays = [*bays, *lane_corridors(model, bays, radius_m)]
    corridors = [corridor for corridor in
                 (*bays, *soffit_corridors(model),
                  *wall_corridors(model), *chase_corridors(model))
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
                        storeys=storeys, crossings=crossings, z_band=z_band,
                        rails=floor_rails(model, (minx, miny, maxx, maxy)))


def floor_rails(model: ResolvedModel, bbox: tuple[float, float, float, float]) -> list:
    """Every level, axis-aligned floor member in ``bbox``, as a rail — see ``rails``.

    ``mep.run_through_floor_member`` FAILs a leg "running along inside" a member, and the
    router laned catlin's kitchen vent along a truss line twice before this.
    """
    from typehaus.resolve.framing.profiles import cross_section

    minx, miny, maxx, maxy = bbox
    out = []
    for floor in model.floors:
        for member in floor.members:
            if member.z0_m is None or member.p0 == member.p1:
                continue
            (ax, ay), (bx, by) = member.p0, member.p1
            if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
                continue
            section = cross_section(member.profile)
            if section is None:
                continue
            axis = "x" if abs(bx - ax) > abs(by - ay) else "y"
            station = ay if axis == "x" else ax
            lo, hi = sorted((ax, bx) if axis == "x" else (ay, by))
            if (axis == "x" and not (miny <= station <= maxy and hi >= minx and lo <= maxx)) \
                    or (axis == "y" and not (minx <= station <= maxx
                                            and hi >= miny and lo <= maxy)):
                continue
            z1 = member.z1_m if member.z1_m is not None else member.z0_m + section.depth_m
            out.append((axis, station, lo, hi, section.width_m / 2.0, member.z0_m, z1,
                        floor.tag))
    return out


def _corridor_in(corridor: Corridor, minx: float, miny: float,
                 maxx: float, maxy: float) -> bool:
    if corridor.axis == "x":
        return (miny <= corridor.station <= maxy
                and corridor.hi_m >= minx and corridor.lo_m <= maxx)
    return (minx <= corridor.station <= maxx
            and corridor.hi_m >= miny and corridor.lo_m <= maxy)
