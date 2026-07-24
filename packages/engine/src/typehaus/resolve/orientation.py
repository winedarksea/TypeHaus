"""Which way is outdoors — per storey (→ 11 §Topology).

``topology.resolve_wall_geometry`` walks an assembly interior→exterior along the wall
axis' *left* normal (``geometry.normal``). That only points outdoors when the storey's
exterior wall loop is authored clockwise; a counter-clockwise loop builds every exterior
wall inside-out (gypsum outdoors, cladding indoors).

Nothing in the authored plan declares the loop direction, so we recover it: trace the
outer boundary of the wall graph geometrically, then ask whether the authored
start→end directions agree with that traversal.
"""

from __future__ import annotations

import math

from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import Vec, polygon_area, sub, unit


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
