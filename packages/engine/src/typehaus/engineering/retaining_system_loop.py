"""The wall graph's cycles: which walls close a loop through a cross-member.

An edge on no cycle is a bridge (Hopcroft-Tarjan lowlink), and a bridge is a wall whose
removal opens the loop. Two edges lie on a common cycle exactly when they survive here and
land in the same component of the bridge-free graph, which is what
``retaining_system._verify`` tests.
"""

from __future__ import annotations

from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import _structure_thickness_in


def _bridges(edges: list[tuple[str, str, str]]) -> set[str]:
    """Tags of the edges that lie on **no** cycle, by Hopcroft-Tarjan lowlink.

    An edge on no cycle is a bridge, and a bridge is precisely a wall whose removal opens
    the loop. Two edges lie on a common cycle exactly when they survive here and land in the
    same component of the bridge-free graph, which is what :func:`_verify` tests.
    """
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for tag, a, b in edges:
        adjacency.setdefault(a, []).append((b, tag))
        adjacency.setdefault(b, []).append((a, tag))

    order: dict[str, int] = {}
    low: dict[str, int] = {}
    bridges: set[str] = set()
    counter = 0

    for root in sorted(adjacency):
        if root in order:
            continue
        # Iterative DFS: a house is small, but a recursive one is a latent stack limit and
        # this runs over every foundation wall on a storey.
        stack: list[tuple[str, str | None, int]] = [(root, None, 0)]
        order[root] = low[root] = counter
        counter += 1
        while stack:
            node, via, index = stack[-1]
            if index < len(adjacency[node]):
                stack[-1] = (node, via, index + 1)
                nxt, tag = adjacency[node][index]
                if tag == via:
                    continue
                if nxt in order:
                    low[node] = min(low[node], order[nxt])
                else:
                    order[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append((nxt, tag, 0))
            else:
                stack.pop()
                if stack:
                    parent = stack[-1][0]
                    low[parent] = min(low[parent], low[node])
                    if low[node] > order[parent] and via is not None:
                        bridges.add(via)
    return bridges


def _cycle_components(edges: list[tuple[str, str, str]]) -> dict[str, int]:
    """Edge tag -> the 2-edge-connected component it sits in; bridges are dropped.

    Every edge left here is on a cycle, and two edges sharing a component are on a *common*
    cycle. That is the whole geometric content of "closes the loop".
    """
    bridges = _bridges(edges)
    kept = [(tag, a, b) for tag, a, b in edges if tag not in bridges]
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for _tag, a, b in kept:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    labels: dict[str, int] = {}
    index: dict[str, int] = {}
    for tag, a, _b in kept:
        root = find(a)
        labels[tag] = index.setdefault(root, len(index))
    return labels


def _foundation_walls(ctx: EngineeringContext) -> list:
    from typehaus.model.structure import FoundationWall

    return [w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)]


def _cast_beams(ctx: EngineeringContext) -> list:
    from typehaus.resolve.assembly_material import is_cast_beam

    return [e for e in ctx.plan.all_elements() if is_cast_beam(ctx.plan, e)]


def _verify(ctx: EngineeringContext, ref: str, members: list) -> list[str]:
    """The conditions that have to hold for the restraint to be real. Names what does not.

    Every one of these is **derived from the model rather than asserted by the author**,
    which is the difference between a restraint and a free pass. Authoring
    ``base_restraint_ref`` states an intention; this function goes and checks it.
    """
    from typehaus.model.enums import LayerFunction
    from typehaus.model.structure import FoundationWall
    from typehaus.resolve.assembly_material import is_cast_beam

    missing: list[str] = []
    cross = ctx.plan.by_tag(ref)
    if not (isinstance(cross, FoundationWall) or is_cast_beam(ctx.plan, cross)):
        return [f"a FoundationWall or concrete Beam tagged {ref} — {len(members)} wall(s) name "
                f"it as the element restraining their base and the model has no such member"]

    edges = [(w.tag, w.start_node, w.end_node) for w in [*_foundation_walls(ctx),
                                                          *_cast_beams(ctx)]
             if w.start_node and w.end_node and w.start_node != w.end_node]
    components = _cycle_components(edges)

    if ref not in components:
        return [f"a closed structural loop through {ref} — it lies on no cycle of walls, so "
                f"it is a bridge and restrains nothing. An open U does not restrain its own "
                f"ends"]
    loop = components[ref]
    for member in members:
        if components.get(member.tag) != loop:
            missing.append(
                f"a closed structural loop through {ref} — {member.tag}'s base is not "
                f"restrained by it, because the two lie on no common cycle")

    # Continuity: a loop of cast concrete, or it is a diagram rather than a load path.
    for wall in [cross, *members]:
        if _structure_thickness_in(ctx, wall.assembly) is None:
            missing.append(f"a concrete STRUCTURE layer on {wall.tag} (assembly "
                           f"{wall.assembly}) — the loop has to be cast, not framed")
            continue
        assembly = ctx.plan.library.resolve_assembly(wall.assembly)
        if assembly is not None and not any(
                layer.function is LayerFunction.STRUCTURE
                and "concrete" in (layer.material_ref or "")
                for layer in assembly.layers):
            missing.append(f"a cast-concrete STRUCTURE layer on {wall.tag} — its structure "
                           f"layer is not concrete, so the corners cannot be cast continuous")
    return missing
