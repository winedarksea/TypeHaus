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
    #: Tags of hard prisms that a terminal node was standing in. Kept rather than dropped —
    #: see :func:`build_graph` — and reported by the caller.
    blocked_terminals: list[str] = field(default_factory=list)

    def neighbours(self, index: int) -> list[tuple[int, str]]:
        return [(other, axis)
                for axis, others in self.edges.get(index, {}).items()
                for other in others]


def candidate_lines(space: RoutingSpace,
                    terminals: list[tuple[float, float, float]],
                    levels: list[float] | None = None
                    ) -> tuple[list[float], list[float], list[float]]:
    """``(xs, ys, zs)`` — the lines the lattice is built at, sorted and de-duplicated.

    Sources, in the order they matter:

    1. **Each terminal's own x, y and z.** A route that cannot reach its own endpoint is
       not a route, so these are non-negotiable and are added first.
    2. **Every corridor centreline** on its own axis, plus the middle of its z window. This
       is what puts a node *in* a bay rather than merely beside one.
    3. **Every hard prism's edges**, already offset outward by ``radius + clearance`` when
       the space was built — but only for a prism whose z band the lattice can reach.
       Offsetting here rather than at query time is what lets a route hug an obstacle
       exactly and no closer; skipping the unreachable ones is what keeps the lattice a
       lattice rather than a grid.

    ``levels`` pins the z set instead of deriving it, and **a gravity run must pass one.**
    A drain's elevation is a derived monotone potential rather than a free dimension: search
    it in 3-D and the found route is free to dive into a cheap plane and climb back, which
    the profile then silently flattens into a plan detour. One level is a plan search, which
    is what "z is derived" actually means.

    Raises :class:`RoutingSpaceTooLarge` past :data:`MAX_CANDIDATE_LINES` on either plan
    axis, for the reason ``space.py`` gives: coarsening to fit is answering a different
    question.
    """
    minx, miny, maxx, maxy = space.bbox
    xs = [t[0] for t in terminals]
    ys = [t[1] for t in terminals]
    zs = [t[2] for t in terminals] if levels is None else list(levels)

    for corridor in space.corridors:
        window = corridor.z_window(space.radius_m)
        if window is None:
            continue
        (ys if corridor.axis == "x" else xs).append(corridor.station)
        if corridor.kind != "wall" and levels is None:
            # **A wall contributes a plan line and NOT a z level**, and that is the
            # difference between a lattice with three thousand nodes and one with three
            # hundred thousand. A wall cavity is a corridor a run may travel at any height
            # inside it, so its mid-height is not a plane anybody routes on; a bay's and a
            # soffit's are. Catlin resolves ~99 walls in a two-fixture window, and one z
            # level each multiplied the lattice by thirty for nothing.
            zs.append((window[0] + window[1]) / 2.0)

    # **Only prisms whose z band the lattice can actually reach.** A footing nine feet
    # under the terminals cannot block anything on the planes this route may use, and
    # nominating two x-lines and two y-lines for it is four lines' worth of lattice bought
    # for nothing. On catlin's suite-bath problem this is most of the plan lines.
    reach = (min(zs) - space.radius_m, max(zs) + space.radius_m)
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
    zs = _unique(zs)
    if max(len(xs), len(ys)) > MAX_CANDIDATE_LINES:
        raise RoutingSpaceTooLarge(
            f"{len(xs)} x-lines and {len(ys)} y-lines exceed MAX_CANDIDATE_LINES="
            f"{MAX_CANDIDATE_LINES}; narrow --margin or raise the cap deliberately")
    if len(xs) * len(ys) * len(zs) > MAX_LATTICE_NODES:
        # The line caps do not bound the lattice: 400 x 400 x 60 is inside both of them and
        # is nine million nodes. This is the guard that actually holds, and it RAISES for
        # the reason space.py gives — a router that coarsens to finish is answering a
        # different question from the one asked.
        raise RoutingSpaceTooLarge(
            f"{len(xs)} x {len(ys)} x {len(zs)} = {len(xs) * len(ys) * len(zs):,} lattice "
            f"nodes exceeds MAX_LATTICE_NODES={MAX_LATTICE_NODES:,}. Narrow --margin, "
            "split the problem, or raise the cap having looked at why")
    return xs, ys, zs


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
    xs, ys, zs = candidate_lines(space, terminals, levels)
    # **A terminal's own plan point is never dropped**, and this is a statement about what
    # the search is for rather than a leniency. A route has to start and end where it is
    # told; if the model puts something there — and it usually does, because a branch ties
    # into the very run that blocks its tie point — that is a fact about the model, not a
    # reason for the search to refuse. ``blocked_terminals`` records which, so the caller
    # can say so instead of the graph swallowing it.
    fixed = {(round(t[0], 6), round(t[1], 6)) for t in terminals}
    blocked_terminals: list[str] = []
    nodes: list[Node] = []
    lookup: dict[tuple[int, int, int], int] = {}
    for kz, z in enumerate(zs):
        for ky, y in enumerate(ys):
            for kx, x in enumerate(xs):
                offender = space.blocked((x, y), z)
                if offender is not None:
                    if (round(x, 6), round(y, 6)) not in fixed:
                        continue
                    blocked_terminals.append(offender)
                lookup[(kx, ky, kz)] = len(nodes)
                nodes.append(Node(index=len(nodes), x=x, y=y, z=z))

    graph = Graph(nodes=nodes, blocked_terminals=sorted(set(blocked_terminals)))
    for (kx, ky, kz), index in lookup.items():
        by_axis: dict[str, list[int]] = {}
        for axis, key in (("x", (kx + 1, ky, kz)),
                          ("y", (kx, ky + 1, kz)),
                          ("z", (kx, ky, kz + 1))):
            other = lookup.get(key)
            if other is None:
                continue
            priced = _price(space, nodes[index], nodes[other], axis)
            if priced is None:
                continue
            weight, terms = priced
            by_axis.setdefault(axis, []).append(other)
            graph.edges.setdefault(other, {}).setdefault(axis, []).append(index)
            graph.weights[(index, other)] = weight
            graph.weights[(other, index)] = weight
            graph.terms[(index, other)] = terms
            graph.terms[(other, index)] = terms
        if by_axis:
            existing = graph.edges.setdefault(index, {})
            for axis, others in by_axis.items():
                existing.setdefault(axis, []).extend(others)
    return graph


def _price(space: RoutingSpace, a: Node, b: Node,
           axis: str) -> tuple[float, dict[str, float]] | None:
    """One edge's cost and terms, or None when a hard prism sits between the two nodes.

    The midpoint test is the cheap approximation and it is honest here: the lattice's own
    lines are the offset edges of every hard prism, so a segment between two adjacent nodes
    cannot enter and leave one — if it touches a prism at all, its midpoint is inside it.
    """
    mid = ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)
    midz = (a.z + b.z) / 2.0
    if space.blocked(mid, midz) is not None:
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
    return cost, terms


def _unique(values: Iterable[float]) -> list[float]:
    out: list[float] = []
    for value in sorted(values):
        if not out or value - out[-1] > _LINE_TOL_M:
            out.append(value)
    return out
