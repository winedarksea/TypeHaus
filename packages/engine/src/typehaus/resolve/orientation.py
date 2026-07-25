"""Which way is outdoors — per structure, and per wall (→ 11 §Topology).

``topology.resolve_wall_geometry`` walks an assembly interior→exterior along the wall
axis' *left* normal (``geometry.normal``). That only points outdoors when the exterior wall
loop the wall belongs to is authored clockwise; a counter-clockwise loop builds every
exterior wall inside-out (gypsum outdoors, cladding indoors).

Nothing in the authored plan declares the loop direction, so we recover it: trace the
outer boundary of the wall graph geometrically, then ask whether the authored
start→end directions agree with that traversal.

That recovery is per *structure*, not per storey. A storey key is a floor level, not a
building: the Catlin basement, the garage foundation, the retaining garden and the sunken
garden all share the ``basement`` storey while being four independent wall loops, each free
to be authored with its own winding. Resolving one scalar for the whole storey forced three
of them to inherit the fourth's answer and built them inside-out — the bug class
``advisory.cladding_side_mismatch`` could only detect after the fact. So the wall graph is
first split into connected components and each component gets its own sign.

The trace is *meaningless* for an interior partition — both sides are indoors, so there is
no geometry to recover the answer from. For an asymmetric partition (the sauna's
foil-polyiso + T&G liner, which must face the hot side) the side is authored:
``Wall.interior_room`` names the room that layer 0 looks at, and :func:`wall_outward_sign`
turns that into the same sign.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import Vec, normal, polygon_area, sub, unit

# Leave the authored geometry alone when the winding cannot be recovered: a component with
# no closed loop (a freestanding garden wall, a partially authored storey) has no inside to
# point away from, so flipping its layer stack would be a guess rather than a correction.
UNRECOVERABLE_WINDING_OUTWARD_SIGN = 1.0

# A closed walk needs at least a triangle before its signed area means anything.
_MINIMUM_LOOP_NODE_COUNT = 3


def _walls(plan: PlanModel, storey_tag: str) -> list:
    return [
        e for e in plan.storey_elements(storey_tag)
        if e.element_kind in ("Wall", "FoundationWall")
    ]


def _turn(d: Vec, e: Vec) -> float:
    """Signed turn angle from direction ``d`` to ``e``, in (-pi, pi]."""
    cross = d[0] * e[1] - d[1] * e[0]
    dot = d[0] * e[0] + d[1] * e[1]
    return math.atan2(cross, dot)


@dataclass(frozen=True)
class _StoreyWallGraph:
    """The storey's wall graph in the one shape the winding trace needs."""

    node_positions: dict[str, tuple[float, float]]
    adjacency: dict[str, list[str]]
    authored_directions: set[tuple[str, str]]


def _storey_wall_graph(plan: PlanModel, storey_tag: str) -> _StoreyWallGraph:
    node_positions = {
        e.tag: e.position.xy_m
        for e in plan.storey_elements(storey_tag)
        if e.element_kind == "Node"
    }
    adjacency: dict[str, list[str]] = {}
    authored_directions: set[tuple[str, str]] = set()
    for wall in _walls(plan, storey_tag):
        a, b = wall.start_node, wall.end_node
        if a not in node_positions or b not in node_positions or a == b:
            continue
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
        authored_directions.add((a, b))
    return _StoreyWallGraph(node_positions, adjacency, authored_directions)


def _component_key_by_node(adjacency: dict[str, list[str]]) -> dict[str, str]:
    """Flood-fill the wall graph into independent structures.

    The key is the component's lexicographically smallest node tag: stable across runs,
    independent of authoring order, and readable in a finding.
    """
    unvisited = set(adjacency)
    key_by_node: dict[str, str] = {}
    while unvisited:
        frontier = [min(unvisited)]
        members: list[str] = []
        unvisited.discard(frontier[0])
        while frontier:
            current = frontier.pop()
            members.append(current)
            for neighbour in adjacency[current]:
                if neighbour in unvisited:
                    unvisited.discard(neighbour)
                    frontier.append(neighbour)
        component_key = min(members)
        for member in members:
            key_by_node[member] = component_key
    return key_by_node


def _closed_walks(graph: _StoreyWallGraph, member_nodes: list[str]) -> list[list[str]]:
    """Every closed boundary walk reachable from a node of this component.

    Walks the graph always taking the sharpest right turn, which traces a face boundary of
    the planar wall graph.
    """
    walks: list[list[str]] = []
    for start in member_nodes:
        walk: list[str] = [start]
        current, incoming = start, (1.0, 0.0)
        for _ in range(len(member_nodes) + 1):
            candidates = graph.adjacency[current]
            best, best_turn = None, None
            for nxt in candidates:
                if len(candidates) > 1 and len(walk) > 1 and nxt == walk[-2]:
                    continue  # never backtrack unless it is the only way out
                turn = _turn(incoming, unit(sub(graph.node_positions[nxt],
                                                graph.node_positions[current])))
                if best_turn is None or turn < best_turn:
                    best, best_turn = nxt, turn
            if best is None:
                break
            incoming = unit(sub(graph.node_positions[best], graph.node_positions[current]))
            current = best
            if current == start:
                break
            walk.append(current)
        if current == start and len(walk) >= _MINIMUM_LOOP_NODE_COUNT:
            walks.append(walk)
    return walks


def _outward_sign_for_walk(graph: _StoreyWallGraph, walk: list[str]) -> float:
    ring = [graph.node_positions[tag] for tag in walk]
    walk_is_counter_clockwise = polygon_area(ring) > 0.0
    # Do the authored wall directions run with the traversal, or against it?
    agreeing_legs = sum(
        1 for i, tag in enumerate(walk)
        if (tag, walk[(i + 1) % len(walk)]) in graph.authored_directions
    )
    authored_counter_clockwise = (
        walk_is_counter_clockwise if agreeing_legs * 2 >= len(walk)
        else not walk_is_counter_clockwise
    )
    return -1.0 if authored_counter_clockwise else 1.0


def _component_winding(graph: _StoreyWallGraph,
                       member_nodes: list[str]) -> tuple[float, float]:
    """``(outward_sign, outer_loop_area)`` for one connected structure."""
    walks = _closed_walks(graph, member_nodes)
    if not walks:
        return UNRECOVERABLE_WINDING_OUTWARD_SIGN, 0.0
    # The largest closed loop is the structure's outer boundary; smaller walks are its
    # interior faces, which enclose rooms rather than the outdoors.
    outer = max(walks, key=lambda walk: abs(
        polygon_area([graph.node_positions[tag] for tag in walk])))
    outer_area = abs(polygon_area([graph.node_positions[tag] for tag in outer]))
    return _outward_sign_for_walk(graph, outer), outer_area


@dataclass(frozen=True)
class StoreyWindings:
    """Every independent structure on one storey and the outward sign it resolved to.

    Built once per storey by :func:`resolve_storey_windings`; ``sign_for_wall`` is then O(1),
    so a storey holding several structures still costs a single graph trace.
    """

    component_key_by_node: dict[str, str]
    sign_by_component_key: dict[str, float]
    outer_loop_area_by_component_key: dict[str, float]

    def component_key_for_wall(self, wall) -> str | None:
        """The structure a wall belongs to, or ``None`` when it touches no traced node."""
        return (self.component_key_by_node.get(wall.start_node)
                or self.component_key_by_node.get(wall.end_node))

    def sign_for_wall(self, wall) -> float:
        return self.sign_for_component(self.component_key_for_wall(wall))

    def sign_for_component(self, component_key: str | None) -> float:
        """The winding of one structure; ``None`` asks for the storey's largest structure."""
        if component_key is None:
            if not self.outer_loop_area_by_component_key:
                return UNRECOVERABLE_WINDING_OUTWARD_SIGN
            component_key = max(self.outer_loop_area_by_component_key,
                                key=self.outer_loop_area_by_component_key.get)
        return self.sign_by_component_key.get(component_key,
                                              UNRECOVERABLE_WINDING_OUTWARD_SIGN)


def resolve_storey_windings(plan: PlanModel, storey_tag: str) -> StoreyWindings:
    """Resolve one outward sign per connected wall-graph component of the storey."""
    graph = _storey_wall_graph(plan, storey_tag)
    component_key_by_node = _component_key_by_node(graph.adjacency)
    members_by_key: dict[str, list[str]] = {}
    for node_tag, component_key in component_key_by_node.items():
        members_by_key.setdefault(component_key, []).append(node_tag)
    windings = {component_key: _component_winding(graph, sorted(members))
                for component_key, members in members_by_key.items()}
    return StoreyWindings(
        component_key_by_node=component_key_by_node,
        sign_by_component_key={key: sign for key, (sign, _) in windings.items()},
        outer_loop_area_by_component_key={key: area for key, (_, area) in windings.items()},
    )


def storey_outward_sign(plan: PlanModel, storey_tag: str,
                        component_key: str | None = None) -> float:
    """``-1.0`` when the named structure's outer wall loop is authored counter-clockwise.

    Multiplying the layer offsets by this sign puts the exterior layers outdoors either way.
    ``component_key`` names one connected wall-graph component (see
    :func:`resolve_storey_windings`); omit it on a storey holding a single structure and the
    largest one answers, which is the only structure there is.

    Returns ``UNRECOVERABLE_WINDING_OUTWARD_SIGN`` when the component has no closed loop, so
    freestanding or partial structures degrade predictably.
    """
    return resolve_storey_windings(plan, storey_tag).sign_for_component(component_key)


def wall_outward_sign(plan: PlanModel, wall, storey_tag: str, component_sign: float) -> float:
    """The outward sign for one wall: its authored ``interior_room``, else ``component_sign``.

    ``resolve_wall_geometry`` places layer 0 (the assembly's interior face) on the
    ``-component_sign * normal(start→end)`` side. When the wall names an ``interior_room``,
    pick the sign that puts that side toward the room's authored seed instead.

    ``component_sign`` is passed in rather than recomputed: it is the winding of the
    structure this wall belongs to (:meth:`StoreyWindings.sign_for_wall`), resolved once per
    storey so this stays O(1) per wall. Falls back to ``component_sign`` whenever the
    reference cannot be resolved (no such room, missing nodes, a seed on the wall's own axis).
    """
    room_tag = getattr(wall, "interior_room", None)
    if not room_tag:
        return component_sign
    room = next(
        (e for e in plan.storey_elements(storey_tag)
         if e.element_kind == "Room" and e.tag == room_tag),
        None,
    )
    if room is None:
        candidate = plan.by_tag(room_tag)
        room = candidate if candidate is not None and candidate.element_kind == "Room" else None
    if room is None:
        return component_sign

    nodes = {e.tag: e for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}
    n0, n1 = nodes.get(wall.start_node), nodes.get(wall.end_node)
    if n0 is None or n1 is None:
        return component_sign
    p0, p1 = n0.position.xy_m, n1.position.xy_m
    axis = sub(p1, p0)
    if abs(axis[0]) < 1e-12 and abs(axis[1]) < 1e-12:
        return component_sign
    n = normal(unit(axis))
    mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    to_seed = sub(room.seed.xy_m, mid)
    side = to_seed[0] * n[0] + to_seed[1] * n[1]
    if abs(side) < 1e-9:  # seed sits on the wall axis — nothing to learn from it
        return component_sign
    # Interior face lies at -sign * n, so it faces the seed when sign is the opposite side.
    return -1.0 if side > 0.0 else 1.0
