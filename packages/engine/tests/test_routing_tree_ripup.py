"""Tree rip-up against ``houses/catlin/notes/mep_tree_ripup_basis.md`` §2, worked by hand.

The note's 24" lattice, priced 24 an edge and 6 a bend, no gravity. A laid branch's nodes
are obstacles; a terminal may end on one only where the line under it is at least its
size. ``_Toy`` is that world behind ``tree_ripup.Layer``; ``build_tree`` drives it."""

from __future__ import annotations

import heapq

from typehaus.cli.route_tree_branches import Branches
from typehaus.routing.search import Route
from typehaus.routing.tree import Terminal, build_tree

#      n3 ---- n4 ---- n5      y = 24   (n3-n0 is hard)
#              |       |
#      n0 ---- n1 ---- n2      y = 0    root n0
XY = {0: (0, 0), 1: (24, 0), 2: (48, 0), 3: (0, 24), 4: (24, 24), 5: (48, 24)}
EDGES = {(0, 1), (1, 2), (3, 4), (4, 5), (1, 4), (2, 5)}
ROOT = 0


class _Toy:
    def __init__(self, sizes: dict[str, float], starts: dict[int, str]) -> None:
        self.sizes, self.starts = sizes, starts
        self.lines: dict[str, tuple[list[int], str | None]] = {}  # lay order
        self.named: dict[str, set[str]] = {}
        self.refuse_relay: str | None = None  # this tag refuses once anything is lifted
        self._relaying = False

    def owner(self, node: int) -> str | None:
        return next((tag for tag, (nodes, _t) in self.lines.items() if node in nodes), None)

    def admits(self, line: str | None, size: float) -> bool:
        while line is not None:
            if self.sizes[line] < size:
                return False
            line = self.lines[line][1]
        return True

    def search(self, _graph, _space, start: int, targets: set[int]) -> Route | None:
        tag = self.starts[start]
        if tag == self.refuse_relay and self._relaying:
            return None
        size, named = self.sizes[tag], self.named.setdefault(tag, set())
        named.clear()
        heap = [(0.0, "", start, None, (start,))]
        seen: set[tuple[int, object]] = set()
        while heap:
            cost, _key, node, heading, path = heapq.heappop(heap)
            if (node, heading) in seen:
                continue
            seen.add((node, heading))
            if node != start and node in targets:
                line = self.owner(node) if node != ROOT else None
                if self.admits(line, size):
                    self.lines[tag] = (list(path), line)
                    pts = [(*XY[n], 0.0) for n in path]
                    return Route(nodes=list(path), points=pts, cost=cost)
                named.add(line)
                continue  # occupied: never passed through
            for a, b in EDGES:
                if node not in (a, b):
                    continue
                other = b if node == a else a
                step = (XY[other][0] - XY[node][0], XY[other][1] - XY[node][1])
                bend = 6.0 if heading is not None and heading != step else 0.0
                line = self.owner(other)
                key = line or ""  # P7: equal costs break on the tag of the line reached
                heapq.heappush(heap, (cost + 24.0 + bend, key, other, step, (*path, other)))
        return None

    def settle(self) -> None:
        pass

    def blockers(self, tag: str) -> list[str]:
        return sorted(self.named.get(tag, ()))

    def snapshot(self):
        return dict(self.lines)

    def restore(self, state) -> None:
        self.lines = dict(state)

    def lift(self, tag: str) -> list[str]:
        doomed = {tag}
        for other, (_nodes, tie) in self.lines.items():  # lay order: ties come after
            if tie in doomed:
                doomed.add(other)
        self._relaying = True
        out = [t for t in self.lines if t in doomed]
        for t in out:
            del self.lines[t]
        return out


def _tree(toy: _Toy, nodes: dict[str, int]):
    terminals = [Terminal(tag=tag, node=node) for tag, node in nodes.items()]
    return build_tree(None, None, ROOT, terminals, search=toy.search, ripup=toy)


def test_two_branches_swap_order_2a():
    toy = _Toy({"T1": 1.5, "T2": 3.0}, {4: "T1", 2: "T2"})
    tree = _tree(toy, {"T1": 4, "T2": 2})
    assert tree.unserved == {}
    assert tree.cost == 72.0  # 48 + 24, 6.0 ft
    assert list(tree.routes) == ["T2", "T1"]
    assert tree.lifts == [("T2", ["T1"])]
    assert len(tree.trials) == 1 and tree.nodes == {0, 1, 2, 4}


def test_cascade_and_rollback_2b():
    toy = _Toy({"A1": 1.5, "A2": 1.5, "B": 3.0}, {4: "A1", 5: "A2", 2: "B"})
    tree = _tree(toy, {"A1": 4, "A2": 5, "B": 2})
    assert tree.unserved == {}
    assert tree.cost == 96.0  # 48 + 24 + 24, 8.0 ft
    assert list(tree.routes) == ["B", "A1", "A2"]
    assert [t.candidate for t in tree.trials] == ["A2", "A1"]
    assert [t.kept for t in tree.trials] == [False, True]
    assert tree.lifts == [("B", ["A1", "A2"])]
    assert tree.nodes == {0, 1, 2, 4, 5}


def test_failed_relay_restores_the_tree_2b():
    toy = _Toy({"A1": 1.5, "A2": 1.5, "B": 3.0}, {4: "A1", 5: "A2", 2: "B"})
    toy.refuse_relay = "A1"
    tree = _tree(toy, {"A1": 4, "A2": 5, "B": 2})
    assert set(tree.unserved) == {"B"}
    assert list(tree.routes) == ["A1", "A2"] and tree.cost == 54.0 + 24.0
    assert len(tree.trials) == 2 and tree.lifts == []
    assert toy.lines["A2"][1] == "A1"  # the ledger is the pre-rip-up one


def test_branches_remove_cascades_down_the_chain():
    branches = Branches.of_main("MAIN", [(0.0, 0.0, 0.0)])
    pt = [(0.0, 0.0, 0.0)]
    a = branches.add("A", 0.04, pt, 0)
    b = branches.add("B", 0.04, pt, a)
    c = branches.add("C", 0.04, pt, 0)
    branches.add("D", 0.04, pt, b)
    assert branches.remove(a) == ["A", "B", "D"]
    assert [x.tag for x in branches.lines] == ["MAIN", "C"]
    assert branches.lines[1].down == 0 and branches.lines[0].served == {"C"}
    assert c == 3
