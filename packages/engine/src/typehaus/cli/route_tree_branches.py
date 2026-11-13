"""A drain tree's accepted branches: what each serves, where it lies, and what it may carry.

A later branch ties onto an earlier one, so the earlier one carries more than the fixture
it was sized for, and every branch downstream of the tie does too. ``admits`` refuses a tie
that would need a larger pipe than the one laid (UPC Table 703.2, ``branch_diameter_m``),
and ``prisms`` makes every laid branch an obstacle for the ones searched after it, so two
branches of one tree no longer pass through each other (drain basis §13). ``remove``
lifts a branch for rip-up (``routing/tree_ripup``, tree rip-up note §1 P3).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass
class _Branch:
    tag: str
    size_m: float
    points: list[tuple[float, float, float]]
    served: set[str]
    down: int | None  # the branch its tie lies on; None for the main


@dataclass
class Branches:
    """Index 0 is the main the tree ties into; it carries anything."""

    main: str
    lines: list[_Branch] = field(default_factory=list)
    main_radius_m: float = 0.0  #: the main's outside radius, for its holes

    @classmethod
    def of_main(cls, main: str, points: list[tuple[float, float, float]],
                radius_m: float = 0.0) -> Branches:
        return cls(main, [_Branch(main, float("inf"), points, set(), None)], radius_m)

    def add(self, tag: str, size_m: float, points: list[tuple[float, float, float]],
            tie: int) -> int:
        """Lay a branch tying onto line ``tie``; its fixture loads every line downstream."""
        self.lines.append(_Branch(tag, size_m, points, {tag}, tie))
        index: int | None = tie
        while index is not None:
            self.lines[index].served.add(tag)
            index = self.lines[index].down
        return len(self.lines) - 1

    def index_of(self, tag: str) -> int | None:
        return next((i for i, b in enumerate(self.lines) if i and b.tag == tag), None)

    def remove(self, line: int) -> list[str]:
        """Lift ``line`` and every branch tied onto it, transitively; their tags in lay order.

        The survivors are re-indexed and their loads recomputed, so a fixture that rode on a
        lifted line no longer loads the lines below it."""
        doomed = {line}
        for index in range(line + 1, len(self.lines)):  # a tie is always laid after its line
            if self.lines[index].down in doomed:
                doomed.add(index)
        keep = [i for i in range(len(self.lines)) if i not in doomed]
        renumber = {old: new for new, old in enumerate(keep)}
        lines = [self.lines[i] for i in keep]
        for branch in lines:
            branch.down = None if branch.down is None else renumber[branch.down]
            branch.served = set() if branch.down is None else {branch.tag}
        for branch in lines[1:]:
            index: int | None = branch.down
            while index is not None:
                lines[index].served.add(branch.tag)
                index = lines[index].down
        removed = [self.lines[i].tag for i in sorted(doomed)]
        self.lines = lines
        return removed

    def copy(self) -> Branches:
        """Deep enough for a rollback: ``remove`` rewrites ``down`` and ``served`` in place."""
        return Branches(self.main, [replace(b, served=set(b.served)) for b in self.lines],
                        self.main_radius_m)

    def admits(self, model: Any, line: int, tag: str) -> bool:
        """Can ``tag`` tie onto ``line`` without any pipe downstream needing upsizing?"""
        from typehaus.cli.route_support import branch_diameter_m

        index: int | None = line
        while index is not None and index != 0:
            branch = self.lines[index]
            needed = branch_diameter_m(model, tuple(sorted(branch.served | {tag})), [], tag)
            if needed is None or needed > branch.size_m + 1e-6:
                return False
            index = branch.down
        return True

    def drop_top(self, line: int, at: tuple[float, float] | None = None) -> float | None:
        """The top of the plumb drop line ``line`` ends in, when it ends in one (at ``at``).

        The main is a stack as often as a run: any plumb leg of it at ``at`` takes a wye at
        any height down its side, so its top is the highest it reaches there."""
        if line <= 0:
            pts = self.lines[0].points
            tops = [max(a[2], b[2]) for a, b in zip(pts, pts[1:], strict=False)
                    if at is not None and abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-9
                    and abs(a[0] - at[0]) + abs(a[1] - at[1]) <= 0.0032]
            return max(tops, default=None)
        if len(self.lines[line].points) < 2:
            return None
        foot, above = self.lines[line].points[-1], self.lines[line].points[-2]
        if abs(foot[0] - above[0]) + abs(foot[1] - above[1]) >= 1e-9:
            return None
        if at is not None and abs(foot[0] - at[0]) + abs(foot[1] - at[1]) > 0.0032:
            return None
        return above[2]

    def owners(self, graph: Any) -> dict[int, int]:
        """Lattice node -> the line it lies on; the main wins where lines coincide."""
        from typehaus.cli.cmd_route_tree import TIE_TOLERANCE_M, _line_nodes

        out: dict[int, int] = {}
        for index in range(len(self.lines) - 1, -1, -1):
            plan = [(x, y) for x, y, _z in self.lines[index].points]
            for node in _line_nodes(graph, plan, TIE_TOLERANCE_M):
                out[node] = index
        for index, branch in enumerate(self.lines[1:], start=1):
            if self.drop_top(index) is not None:
                # Its plumb drop stands on the tie: a later branch enters the drop there.
                for node in _line_nodes(graph, [branch.points[-1][:2]], TIE_TOLERANCE_M):
                    out[node] = index
        return out

    def laid_lines(self) -> list:
        """Every laid line, the main included, as ``holes.laid_lines`` reads a proposal: the
        main is hidden from the space (``touch``), so its pockets would otherwise be free."""
        from typehaus.routing.trades.pipe import radius_m as pipe_radius_m

        return [(branch.tag, tuple(p[:2] for p in branch.points),
                 tuple(p[2] for p in branch.points),
                 self.main_radius_m if i == 0 else pipe_radius_m(branch.size_m))
                for i, branch in enumerate(self.lines) if len(branch.points) >= 2]

    def prisms(self, radius_m: float, clearance_m: float) -> list:
        """Every laid branch, inflated by its radius and this run's, as a banded run prism."""
        from shapely.geometry import LineString, Point

        from typehaus.routing.obstacles import HardPrism
        from typehaus.routing.trades.pipe import radius_m as pipe_radius_m

        out = []
        for branch in self.lines[1:]:
            grow = pipe_radius_m(branch.size_m) + radius_m + clearance_m
            for leg in _legs(branch.points):  # one prism per straight leg (§13: approach)
                a, b = leg[0], leg[-1]
                shape = (Point(a[:2]) if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-9
                         else LineString([a[:2], b[:2]]))
                zs = [p[2] for p in leg]
                out.append(HardPrism(tag=f"{branch.tag}-PROPOSED", kind="run",
                                     footprint=shape.buffer(grow),
                                     z0_m=min(zs) - grow, z1_m=max(zs) + grow))
        return out


def _legs(points: list[tuple[float, float, float]]) -> list[list[tuple[float, float, float]]]:
    """Consecutive points split where the plan direction changes; a plumb drop is a leg."""
    def heading(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        return (0 if abs(dx) < 1e-9 else 1 if dx > 0 else -1,
                0 if abs(dy) < 1e-9 else 1 if dy > 0 else -1)

    legs: list[list[tuple[float, float, float]]] = []
    for a, b in zip(points, points[1:], strict=False):
        if legs and heading(legs[-1][-2], legs[-1][-1]) == heading(a, b):
            legs[-1].append(b)
        else:
            legs.append([a, b])
    return legs
