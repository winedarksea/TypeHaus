"""A drain tree's accepted branches: what each serves, where it lies, and what it may carry.

A later branch ties onto an earlier one, so the earlier one carries more than the fixture
it was sized for, and every branch downstream of the tie does too. ``admits`` refuses a tie
that would need a larger pipe than the one laid (UPC Table 703.2, ``branch_diameter_m``),
and ``prisms`` makes every laid branch an obstacle for the ones searched after it, so two
branches of one tree no longer pass through each other (drain basis §13).
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

    @classmethod
    def of_main(cls, main: str, points: list[tuple[float, float, float]]) -> Branches:
        return cls(main, [_Branch(main, float("inf"), points, set(), None)])

    def add(self, tag: str, size_m: float, points: list[tuple[float, float, float]],
            tie: int) -> int:
        """Lay a branch tying onto line ``tie``; its fixture loads every line downstream."""
        self.lines.append(_Branch(tag, size_m, points, {tag}, tie))
        index: int | None = tie
        while index is not None:
            self.lines[index].served.add(tag)
            index = self.lines[index].down
        return len(self.lines) - 1

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
        """The top of the plumb drop line ``line`` ends in, when it ends in one (at ``at``)."""
        if line <= 0 or len(self.lines[line].points) < 2:
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
