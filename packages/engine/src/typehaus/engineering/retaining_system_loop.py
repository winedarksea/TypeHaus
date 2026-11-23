"""The wall graph's cycles: which walls close a loop through a cross-member.

An edge on no cycle is a bridge (Hopcroft-Tarjan lowlink), and a bridge is a wall whose
removal opens the loop. Two edges lie on a common cycle exactly when they survive here and
land in the same component of the bridge-free graph, which is what
``retaining_system._verify`` tests.
"""

from __future__ import annotations


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
