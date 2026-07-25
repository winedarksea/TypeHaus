"""Which way is outdoors — per storey, and per wall (→ 11 §Topology).

``topology.resolve_wall_geometry`` walks an assembly interior→exterior along the wall
axis' *left* normal (``geometry.normal``). That only points outdoors when the storey's
exterior wall loop is authored clockwise; a counter-clockwise loop builds every exterior
wall inside-out (gypsum outdoors, cladding indoors).

Nothing in the authored plan declares the loop direction, so we recover it: trace the
outer boundary of the wall graph geometrically, then ask whether the authored
start→end directions agree with that traversal.

That answers the question for the storey's outer loop, and is *meaningless* for an
interior partition — both sides are indoors, so there is no geometry to recover the
answer from. For an asymmetric partition (the sauna's foil-polyiso + T&G liner, which
must face the hot side) the side is authored: ``Wall.interior_room`` names the room that
layer 0 looks at, and :func:`wall_outward_sign` turns that into the same sign.
"""

from __future__ import annotations

import math

from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import Vec, normal, polygon_area, sub, unit


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


def storey_outward_sign(plan: PlanModel, storey_tag: str) -> float:
    """``-1.0`` when the storey's outer wall loop is authored counter-clockwise.

    Multiplying the layer offsets by this sign puts the exterior layers outdoors either
    way. Returns ``+1.0`` (leave the geometry alone) when the storey has no closed outer
    loop, so freestanding or partial storeys degrade predictably.
    """
    nodes = {
        e.tag: e.position.xy_m
        for e in plan.storey_elements(storey_tag)
        if e.element_kind == "Node"
    }
    adjacency: dict[str, list[str]] = {}
    directed: set[tuple[str, str]] = set()
    for wall in _walls(plan, storey_tag):
        a, b = wall.start_node, wall.end_node
        if a not in nodes or b not in nodes or a == b:
            continue
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
        directed.add((a, b))
    if not adjacency:
        return 1.0

    # A storey can contain multiple disconnected wall loops (the Catlin basement also
    # contains the sunken garden). Choose the largest closed loop rather than assuming
    # the globally lowest node belongs to the building's exterior boundary.
    candidate_walks: list[list[str]] = []
    for start in adjacency:
        walk: list[str] = [start]
        current, incoming = start, (1.0, 0.0)
        for _ in range(len(adjacency) + 1):
            candidates = adjacency[current]
            best, best_turn = None, None
            for nxt in candidates:
                if len(candidates) > 1 and len(walk) > 1 and nxt == walk[-2]:
                    continue  # never backtrack unless it is the only way out
                turn = _turn(incoming, unit(sub(nodes[nxt], nodes[current])))
                if best_turn is None or turn < best_turn:
                    best, best_turn = nxt, turn
            if best is None:
                break
            incoming = unit(sub(nodes[best], nodes[current]))
            current = best
            if current == start:
                break
            walk.append(current)
        if current == start and len(walk) >= 3:
            candidate_walks.append(walk)

    if not candidate_walks:
        return 1.0
    walk = max(candidate_walks,
               key=lambda candidate: abs(polygon_area([nodes[t] for t in candidate])))

    ring = [nodes[t] for t in walk]
    walk_ccw = polygon_area(ring) > 0.0

    # Do the authored wall directions run with the traversal, or against it?
    agree = sum(
        1 for i, tag in enumerate(walk)
        if (tag, walk[(i + 1) % len(walk)]) in directed
    )
    authored_ccw = walk_ccw if agree * 2 >= len(walk) else not walk_ccw
    return -1.0 if authored_ccw else 1.0


def wall_outward_sign(plan: PlanModel, wall, storey_tag: str, storey_sign: float) -> float:
    """The outward sign for one wall: its authored ``interior_room``, else ``storey_sign``.

    ``resolve_wall_geometry`` places layer 0 (the assembly's interior face) on the
    ``-storey_sign * normal(start→end)`` side. When the wall names an ``interior_room``, pick
    the sign that puts that side toward the room's authored seed instead.

    ``storey_sign`` is passed in rather than recomputed: ``storey_outward_sign`` traces the
    whole storey wall graph, so the caller resolves it once per storey and this stays O(1)
    per wall. Falls back to ``storey_sign`` whenever the reference cannot be resolved (no
    such room, missing nodes, a seed on the wall's own axis).
    """
    room_tag = getattr(wall, "interior_room", None)
    if not room_tag:
        return storey_sign
    room = next(
        (e for e in plan.storey_elements(storey_tag)
         if e.element_kind == "Room" and e.tag == room_tag),
        None,
    )
    if room is None:
        candidate = plan.by_tag(room_tag)
        room = candidate if candidate is not None and candidate.element_kind == "Room" else None
    if room is None:
        return storey_sign

    nodes = {e.tag: e for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}
    n0, n1 = nodes.get(wall.start_node), nodes.get(wall.end_node)
    if n0 is None or n1 is None:
        return storey_sign
    p0, p1 = n0.position.xy_m, n1.position.xy_m
    axis = sub(p1, p0)
    if abs(axis[0]) < 1e-12 and abs(axis[1]) < 1e-12:
        return storey_sign
    n = normal(unit(axis))
    mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    to_seed = sub(room.seed.xy_m, mid)
    side = to_seed[0] * n[0] + to_seed[1] * n[1]
    if abs(side) < 1e-9:  # seed sits on the wall axis — nothing to learn from it
        return storey_sign
    # Interior face lies at -sign * n, so it faces the seed when sign is the opposite side.
    return -1.0 if side > 0.0 else 1.0
