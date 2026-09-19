"""The escape graph: candidate lines, lattice nodes, and the edges between them.

``houses/catlin/notes/mep_drain_routing_basis.md`` §4 is the spec, not a description of
one — its 3x3 lattice, its blocked node, its bend penalty and its eight-row expansion
table are what ``tests/test_routing_oracle.py`` asserts against this module and
:mod:`typehaus.routing.search`.

**Candidate lines, and why not a uniform grid.** A uniform grid has nodes where nothing is
and none where the route wants to turn. The escape-graph formulation instead nominates the
lines a route could plausibly follow — every hard prism's edge offset outward by
``radius + clearance``, every corridor centreline, and each terminal's own x and y — and
builds the lattice at their intersections. That is what makes "round this obstacle costs
two bends, not four" fall out of the graph rather than out of a tolerance.

**z is a level set, not a continuum.** A house's services live in a handful of planes: bay
centrelines, soffit interiors, wall cavities, the terminals' own elevations. The lattice
is built at those levels with vertical edges wherever the drop between two of them is
clear, which is both far smaller than a 3-D grid and closer to how the work is actually
laid out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from typehaus.routing.space import (
    MAX_CANDIDATE_LINES,
    MAX_LATTICE_NODES,
    RoutingSpace,
    RoutingSpaceTooLarge,
)

#: Two coordinates closer than this are one line. A sixteenth of an inch: finer than any
#: dimension this engine authors and coarser than any float noise it produces.
_LINE_TOL_M = 0.0015875


@dataclass(frozen=True)
class Node:
    """One lattice node. ``index`` is its id, and ids are the search's tie-break.

    Ordering is ``(z, y, x)`` ascending, assigned once at build time — see
    :func:`build_graph`. A stated, stable id is what makes A* deterministic, and a
    deterministic search is what makes an oracle note possible at all.
    """

    index: int
    x: float
    y: float
    z: float

    @property
    def plan(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Graph:
    """Nodes, and each node's neighbours by axis.

    ``edges[i]`` maps an axis (``"x"``, ``"y"``, ``"z"``) to the neighbour indices reachable
    from node ``i`` along it. The axis is kept on the edge rather than derived, because the
    search's state is ``(node, incoming axis)`` and the bend penalty is a function of the
    turn — see :mod:`typehaus.routing.search`.
    """

    nodes: list[Node]
    edges: dict[int, dict[str, list[int]]] = field(default_factory=dict)
    #: Per-edge pre-computed cost, keyed ``(from, to)``. Built once because the same edge is
    #: relaxed from two states (arriving along x and arriving along y) and the geometry it
    #: is priced from does not change between them.
    weights: dict[tuple[int, int], float] = field(default_factory=dict)
    #: Per-edge human-readable term breakdown, keyed the same way. This is the entire
    #: content of ``--explain``: a router that cannot say why it chose a line is one nobody
    #: will take a line from.
    terms: dict[tuple[int, int], dict[str, float]] = field(default_factory=dict)
    #: Which corridor each edge rides, keyed the same way; absent when it rides none. This
    #: is what lets a duct proposal print ``floor_ref=``/``soffit_ref=`` from the lanes the
    #: winning legs actually took rather than from a guess about where the run ought to be.
    corridors: dict[tuple[int, int], str] = field(default_factory=dict)
    #: Tags of hard prisms that a terminal node was standing in. Kept rather than dropped —
    #: see :func:`build_graph` — and reported by the caller.
    blocked_terminals: list[str] = field(default_factory=list)

    def neighbours(self, index: int) -> list[tuple[int, str]]:
        return [(other, axis)
                for axis, others in self.edges.get(index, {}).items()
                for other in others]


def candidate_levels(space: RoutingSpace,
                     terminals: list[tuple[float, float, float]],
                     levels: list[float] | None = None) -> list[float]:
    """The z planes the lattice is built at, sorted and de-duplicated.

    **z is a level set, not a continuum.** A house's services live in a handful of planes:
    bay centrelines, soffit interiors, the terminals' own elevations.

    **A wall contributes a plan line and NOT a z level**, and that is the difference between
    a lattice with three thousand nodes and one with three hundred thousand. A wall cavity
    is a corridor a run may travel at any height inside it, so its mid-height is not a plane
    anybody routes on; a bay's and a soffit's are. Catlin resolves ~99 walls in a two-fixture
    window, and one z level each multiplied the lattice by thirty for nothing.

    ``levels`` pins the set instead of deriving it, and **a gravity run must pass one.** A
    drain's elevation is a derived monotone potential rather than a free dimension: search it
    in 3-D and the found route is free to dive into a cheap plane and climb back, which the
    profile then silently flattens into a plan detour. One level is a plan search, which is
    what "z is derived" actually means.
    """
    zs = [t[2] for t in terminals] if levels is None else list(levels)
    if levels is None:
        for corridor in space.corridors:
            window = corridor.z_window(space.radius_m)
            if window is None or corridor.kind == "wall":
                continue
            zs.extend(_corridor_levels(corridor, window, space))
    zs = _unique(zs)
    if space.z_band is not None:
        # ``--level``: the lattice keeps only the planes inside one storey's band. A
        # terminal outside it is the caller's refusal to report, not this function's to
        # paper over — dropping a terminal's own level silently would make the search
        # answer a question about a route that cannot start where it was told to.
        low, high = space.z_band
        inside = [z for z in zs if low - _LINE_TOL_M <= z <= high + _LINE_TOL_M]
        if inside:
            zs = inside
    return zs


def _corridor_levels(corridor, window: tuple[float, float],
                     space: RoutingSpace) -> list[float]:
    """The plane(s) worth nominating inside one corridor's window.

    **An empty channel offers one plane and an occupied one offers two.** The midpoint is
    the right answer for a bay with nothing in it — there is no reason to prefer high or
    low, and one plane is thirty times cheaper than several. It is the WRONG answer for a
    bay that already holds a run, because the midpoint is very often the plane the occupant
    is on, and a lattice whose only offer is the taken plane makes a clear bay come back
    refused. Catlin's FS-S-WEST is the case: an 8 7/8" web window takes two 4" ducts
    stacked with 7/8" to spare, and the router could nominate neither of the two tiers.

    So: where the corridor has an occupant, nominate the two extremes of its own centreline
    window — a run pressed to the bottom of the window and one pressed to the top — but
    only when those two would actually clear each other, ``high - low >= 2r + clearance``.
    Otherwise the midpoint, unchanged.

    **The extremes, not an inset off them.** ``z_window`` has already taken the radius off
    both ends, so its bounds ARE the run hard against each chord, which is what a fitter
    does and what catlin's own note records: an 8 7/8" web window (109 5/8" .. 118 1/2")
    gives tiers at **111 5/8" and 116 1/2"**, 4 7/8" apart, two 4" ducts with 7/8" to
    spare. Insetting by a further clearance would put them 3 7/8" apart and neither tier
    would be buildable — the geometry would have refused the thing it was added to allow.

    The tiers are offered rather than the occupant's own band subtracted, because a
    corridor's ``occupied_z`` is a MEAN (``mep_packing.run_occupants`` bands each run once,
    not once per segment) and pricing a plane off a mean would be a precision the reading
    does not have.
    """
    low, high = window
    if corridor.occupied_z is None:
        return [(low + high) / 2.0]
    if high - low < 2.0 * space.radius_m + space.clearance_m - 1e-9:
        return [(low + high) / 2.0]
    return [low, high]


def candidate_lines_at(space: RoutingSpace,
                       terminals: list[tuple[float, float, float]],
                       z: float, *,
                       plan_search: bool = False) -> tuple[list[float], list[float]]:
    """``(xs, ys)`` — the plan lines the lattice is built at **on one level**.

    Sources, in the order they matter:

    1. **Each terminal's own x and y.** A route that cannot reach its own endpoint is not a
       route, so these are non-negotiable and are added first, on every level.
    2. **Every corridor centreline** whose z window this level reaches — unless this is a
       ``plan_search``, in which case every corridor, full stop. The exception is not a
       loosening: **a gravity run's z is a derived potential, not the plane it searches in.**
       A drain searches one nominal level while its real invert falls the whole way along,
       so the bay it ends up riding at station 14 ft is one whose z window the nominal plane
       never touched. Filtering these took ``PR-B-KITCH-DRAIN`` from a route to a four-node
       lattice with no lanes at all. A true 3-D search has no such excuse — it *is* at the
       level it is searching — and filtering there is what keeps catlin's worst duct inside
       the cap instead of 31,000 nodes over it.
    3. **Every hard prism's edges**, already offset outward by ``radius + clearance`` when
       the space was built — but only for a prism this level actually cuts through.

    **Per level, and that is the whole of Phase 7's first optimisation.** The lines used to
    be derived once for the whole z band and laid down on every plane in it, so a footing
    nine feet under the attic nominated two x-lines and two y-lines *in the attic* — turn
    points at the corners of an obstacle that is not there. On catlin that is the difference
    between ``DU-M-ERV-R-KITCH`` refusing at 159 x 161 x 8 = 204,792 nodes and routing.

    A single-level search — every gravity run, and the oracle note's own 3x3 lattice — gets
    exactly the lines it got before, because for one level "the band" and "this level" are
    the same set. Nothing that worked moves.

    Raises :class:`RoutingSpaceTooLarge` past :data:`MAX_CANDIDATE_LINES` on either plan
    axis, for the reason ``space.py`` gives: coarsening to fit is answering a different
    question.
    """
    minx, miny, maxx, maxy = space.bbox
    xs = [t[0] for t in terminals]
    ys = [t[1] for t in terminals]

    for corridor in space.corridors:
        window = corridor.z_window(space.radius_m)
        if window is None:
            continue
        if not plan_search and not (window[0] - space.radius_m <= z
                                    <= window[1] + space.radius_m):
            continue
        (ys if corridor.axis == "x" else xs).append(corridor.station)

    reach = (z - space.radius_m, z + space.radius_m)
    for prism in space.hard:
        if prism.footprint.is_empty:
            continue
        if prism.z1_m < reach[0] or prism.z0_m > reach[1]:
            continue
        px0, py0, px1, py1 = prism.footprint.bounds
        xs.extend((px0, px1))
        ys.extend((py0, py1))

    xs = _unique(v for v in xs if minx - _LINE_TOL_M <= v <= maxx + _LINE_TOL_M)
    ys = _unique(v for v in ys if miny - _LINE_TOL_M <= v <= maxy + _LINE_TOL_M)
    if max(len(xs), len(ys)) > MAX_CANDIDATE_LINES:
        raise RoutingSpaceTooLarge(
            f"{len(xs)} x-lines and {len(ys)} y-lines at z={z:.3f} exceed "
            f"MAX_CANDIDATE_LINES={MAX_CANDIDATE_LINES}; narrow --margin or raise the cap "
            "deliberately")
    return xs, ys


def candidate_lines(space: RoutingSpace,
                    terminals: list[tuple[float, float, float]],
                    levels: list[float] | None = None
                    ) -> tuple[list[float], list[float], list[float]]:
    """The UNION of every level's lines, for a reader that wants the whole picture.

    The lattice itself is built per level by :func:`build_graph`; this is what a diagnostic
    or a space view asks when it wants "every line this problem considered" in one list.
    """
    zs = candidate_levels(space, terminals, levels)
    xs: list[float] = []
    ys: list[float] = []
    for z in zs:
        level_xs, level_ys = candidate_lines_at(space, terminals, z,
                                                plan_search=levels is not None)
        xs.extend(level_xs)
        ys.extend(level_ys)
    return _unique(xs), _unique(ys), zs


def build_graph(space: RoutingSpace,
                terminals: list[tuple[float, float, float]],
                levels: list[float] | None = None) -> Graph:
    """The lattice, with every node priced against the world once.

    A node is dropped when it stands inside a hard prism; an edge is dropped when either
    end is gone or when the segment between them crosses one. Everything surviving carries
    a cost and a term breakdown.

    **Node ids are assigned in ``(z, y, x)`` order** and the search breaks ties on them, so
    two runs of the same problem return the same route. §4 of the oracle note depends on
    it, and so does anybody diffing two proposals.

    ``levels`` is passed through to :func:`candidate_lines`; a gravity run passes one level
    and searches in plan.
    """
    zs = candidate_levels(space, terminals, levels)
    # **Pinned levels mean a plan search**, which is what a gravity run is: the caller fixed
    # the plane because the elevation is derived along the route rather than chosen by it.
    per_level = [candidate_lines_at(space, terminals, z, plan_search=levels is not None)
                 for z in zs]
    total = sum(len(level_xs) * len(level_ys) for level_xs, level_ys in per_level)
    if total > MAX_LATTICE_NODES:
        # The line caps do not bound the lattice: 400 x 400 x 60 is inside both of them and
        # is nine million nodes. This is the guard that actually holds, and it RAISES for
        # the reason space.py gives — a router that coarsens to finish is answering a
        # different question from the one asked.
        shape = " + ".join(f"{len(lx)}x{len(ly)}" for lx, ly in per_level)
        raise RoutingSpaceTooLarge(
            f"{shape} = {total:,} lattice nodes exceeds "
            f"MAX_LATTICE_NODES={MAX_LATTICE_NODES:,}. Narrow --margin, split the problem, "
            "or raise the cap having looked at why")
    # **A terminal's own plan point is never dropped**, and this is a statement about what
    # the search is for rather than a leniency. A route has to start and end where it is
    # told; if the model puts something there — and it usually does, because a branch ties
    # into the very run that blocks its tie point — that is a fact about the model, not a
    # reason for the search to refuse. ``blocked_terminals`` records which, so the caller
    # can say so instead of the graph swallowing it.
    fixed = {(round(t[0], 6), round(t[1], 6)) for t in terminals}
    blocked_terminals: list[str] = []
    #: Terminal nodes kept despite standing in a hard prism. The edges LEAVING one of them
    #: are kept too — see below — because a node a route may not move off is a node it may
    #: as well not have.
    lenient: set[int] = set()
    nodes: list[Node] = []
    lookup: dict[tuple[int, int, int], int] = {}
    #: Per level, the node at each rounded plan point. A riser connects two levels at the
    #: same (x, y), and the two levels no longer share a line INDEX — only a coordinate.
    by_plan: list[dict[tuple[float, float], int]] = []
    for kz, z in enumerate(zs):
        level_xs, level_ys = per_level[kz]
        plan_index: dict[tuple[float, float], int] = {}
        for ky, y in enumerate(level_ys):
            for kx, x in enumerate(level_xs):
                offender = space.blocked((x, y), z)
                if offender is not None:
                    if (round(x, 6), round(y, 6)) not in fixed:
                        continue
                    blocked_terminals.append(offender)
                    lenient.add(len(nodes))
                lookup[(kx, ky, kz)] = len(nodes)
                plan_index[(round(x, 6), round(y, 6))] = len(nodes)
                nodes.append(Node(index=len(nodes), x=x, y=y, z=z))
        by_plan.append(plan_index)

    graph = Graph(nodes=nodes, blocked_terminals=sorted(set(blocked_terminals)))

    def connect(index: int, other: int, axis: str) -> None:
        # **One lattice step of leniency at a blocked terminal, and exactly one.** The node
        # rule above keeps a terminal that stands inside something — a branch's tie point
        # usually sits on the very run it ties into, and an ERV manifold packs ten ports
        # four inches apart so every lane out of one is inside its neighbour. Keeping the
        # node and dropping every edge off it produces "no route in plan; every lane is
        # blocked" about a route whose only obstruction is the fitting at its own end. The
        # blockage is not hidden: it is already in `blocked_terminals` and the caller prints
        # it as a detail somebody has to draw.
        priced = _price(space, nodes[index], nodes[other], axis,
                        lenient=index in lenient or other in lenient)
        if priced is None:
            return
        weight, terms, corridor = priced
        if corridor is not None:
            graph.corridors[(index, other)] = corridor
            graph.corridors[(other, index)] = corridor
        graph.edges.setdefault(index, {}).setdefault(axis, []).append(other)
        graph.edges.setdefault(other, {}).setdefault(axis, []).append(index)
        graph.weights[(index, other)] = weight
        graph.weights[(other, index)] = weight
        graph.terms[(index, other)] = terms
        graph.terms[(other, index)] = terms

    for (kx, ky, kz), index in lookup.items():
        for axis, key in (("x", (kx + 1, ky, kz)), ("y", (kx, ky + 1, kz))):
            other = lookup.get(key)
            if other is not None:
                connect(index, other, axis)

    # Vertical edges between consecutive levels, at every plan point BOTH levels hold. The
    # two levels no longer nominate the same lines, so a riser lands where the work actually
    # puts one: a terminal's own station, or a corridor both levels reach.
    for kz in range(len(zs) - 1):
        upper = by_plan[kz + 1]
        for plan, index in by_plan[kz].items():
            other = upper.get(plan)
            if other is not None:
                connect(index, other, "z")
    return graph


def _price(space: RoutingSpace, a: Node, b: Node, axis: str, *,
           lenient: bool = False) -> tuple[float, dict[str, float], str | None] | None:
    """``(cost, terms, corridor tag)`` for one edge, or None when a hard prism is between.

    The midpoint test is the cheap approximation and it is honest here: the lattice's own
    lines are the offset edges of every hard prism, so a segment between two adjacent nodes
    cannot enter and leave one — if it touches a prism at all, its midpoint is inside it.

    ``lenient`` is set for the one step off a terminal that stands inside something. See
    :func:`build_graph`; it buys one lattice step and never a lane.
    """
    mid = ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)
    midz = (a.z + b.z) / 2.0
    if not lenient and space.blocked(mid, midz) is not None:
        return None

    length_m = abs(b.x - a.x) + abs(b.y - a.y) + abs(b.z - a.z)
    if length_m <= 0:
        return None
    length_ft = length_m / 0.3048
    vertical = axis == "z"

    lo, hi = ((min(a.x, b.x), max(a.x, b.x)) if axis == "x"
              else (min(a.y, b.y), max(a.y, b.y)) if axis == "y"
              else (a.x, a.x))
    station = a.y if axis == "x" else a.x
    corridor = (None if vertical
                else space.corridor_at(axis, station, lo, hi, midz))

    room_ft, occupancy, in_wall_ft = 0.0, None, 0.0
    for prism in space.soft_at(mid, midz):
        if prism.kind == "room":
            room_ft, occupancy = length_ft, prism.occupancy
        elif prism.kind == "wall":
            in_wall_ft = length_ft

    cost = space.cost.segment_cost(
        length_ft, vertical=vertical, corridor=corridor is not None,
        in_wall_ft=in_wall_ft, room_ft=room_ft, occupancy=occupancy)
    terms = {"travel_in": length_ft * 12.0 * (space.cost.riser_per_ft if vertical else 1.0)}
    if corridor is not None:
        terms["corridor_in"] = -min(length_ft * space.cost.corridor_discount_per_ft,
                                    terms["travel_in"])
    if room_ft:
        terms["room_in"] = room_ft * space.cost.room_penalty(occupancy)
    if in_wall_ft:
        terms["in_wall_in"] = in_wall_ft * space.cost.in_wall_travel_per_ft
    return cost, terms, (corridor.tag if corridor is not None else None)


def _unique(values: Iterable[float]) -> list[float]:
    out: list[float] = []
    for value in sorted(values):
        if not out or value - out[-1] > _LINE_TOL_M:
            out.append(value)
    return out
