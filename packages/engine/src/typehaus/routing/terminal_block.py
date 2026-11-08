"""A route's own end standing inside a hard prism: moved along its wall, or named.

``graph.build_graph`` keeps a terminal that stands in a hard prism (a route must reach where
it is told) and lets one lattice step off it pass through. For the prisms that are NOT part of
the tie (a door's buck or swing, an unrelated run such as a duct) that pardon hides a fixture
end somebody has to move. For each such end this finds the nearest point ON ITS OWN WALL, along
the wall's axis, that no hard prism covers, and either hands the lattice that point (``moved_to``)
or reports that there is none (``moved_to`` None: the caller refuses with the typed cause). It
never moves anything authored: a move is a lead the proposal puts back (``cli/route_supply_group``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.geometry import Point

from typehaus.quantities import M_PER_IN

#: A route end may not stand in an ``opening`` prism (a door buck OR its swing sector) or in a
#: ``run`` prism whose tag is in ``space.blocking_runs`` (the caller's ducts: a cold stop beside
#: its own hot stop stands in that pipe's grown prism by design).
#: How far along its wall an end may move: two stud bays.
REACH_M = 32.0 * M_PER_IN
STEP_M = 0.5 * M_PER_IN


@dataclass(frozen=True)
class TerminalBlock:
    """One route end inside a hard prism. ``kinds`` are ``HardPrism.kind`` values and
    ``prisms`` their tags, so a caller reads the cause without parsing text."""

    point: tuple[float, float, float]
    prisms: tuple[str, ...]
    kinds: tuple[str, ...]
    #: The wall the end stands in, or None when it stands in no stud plane.
    wall: str | None = None
    #: The nearest legal point on that wall (plan), or None: no legal point within ``REACH_M``.
    moved_to: tuple[float, float] | None = None
    #: True when the END is clear but its riser COLUMN, below it, passes through the prisms.
    column: bool = False

    @property
    def shift_m(self) -> float:
        if self.moved_to is None:
            return 0.0
        return abs(self.moved_to[0] - self.point[0]) + abs(self.moved_to[1] - self.point[1])

    @property
    def cause(self) -> str:
        """``door`` (a buck or swing), ``run`` (a duct), else the prism kinds."""
        return ("door" if "opening" in self.kinds else
                "run" if "run" in self.kinds else "+".join(self.kinds))

    def render(self) -> str:
        what = f"{', '.join(self.prisms)} ({self.cause})"
        at = f"({self.point[0] / 0.0254:.1f}\", {self.point[1] / 0.0254:.1f}\")"
        if self.column:
            return (f"its riser column at {at} passes through {what} and no lane around it "
                    "clears: the fixture end needs a house move")
        if self.moved_to is not None:
            return (f"its end {at} stands inside {what}; searched from the nearest legal point "
                    f"on {self.wall}, {self.shift_m / 0.0254:.1f}\" along it")
        where = f"on {self.wall} " if self.wall else ""
        return (f"its end {at} stands inside {what} and no point {where}within "
                f"{REACH_M / 0.0254:.0f}\" of it is clear: the fixture end needs a house move")

    def payload(self) -> dict[str, Any]:
        return {"point": list(self.point), "prisms": list(self.prisms),
                "kinds": list(self.kinds), "cause": self.cause, "wall": self.wall,
                "moved_to": None if self.moved_to is None else list(self.moved_to),
                "column": self.column,
                "shift_in": round(self.shift_m / 0.0254, 3)}


def _covering(space: Any, x: float, y: float, z: float) -> list[Any]:
    probe = Point(x, y)
    return [p for p in space.hard if p.z0_m <= z <= p.z1_m and p.footprint.covers(probe)]


def _blocks(space: Any, prism: Any) -> bool:
    return prism.kind == "opening" or (
        prism.kind == "run" and prism.tag in getattr(space, "blocking_runs", frozenset()))


def strict_block(space: Any, x: float, y: float, z: float) -> bool:
    """Whether a door swing/buck or a duct covers ``(x, y, z)``: not pardoned off its own level."""
    return any(_blocks(space, p) for p in _covering(space, x, y, z))


def _walls(space: Any, x: float, y: float) -> list[Any]:
    """Walls whose stud plane (grown 2") holds ``(x, y)``."""
    members = getattr(space, "members", None)
    if members is None:
        return []
    grow = 2.0 * M_PER_IN
    out = []
    for wall in members._walls_at("x", y) + members._walls_at("y", x):
        along, across = (x, y) if wall.axis == "x" else (y, x)
        if (wall.along[0] <= along <= wall.along[1]
                and wall.perp[0] - grow <= across <= wall.perp[1] + grow and wall not in out):
            out.append(wall)
    return out


def resolve_ends(space: Any, ends: Any) -> tuple[dict[tuple[float, float, float], tuple],
                                                  list[TerminalBlock]]:
    """``({end: point to build the lattice at}, blocks)`` for every end in ``ends`` that
    stands in a door prism or a duct. An end with no legal point keeps its own."""
    moved: dict[tuple[float, float, float], tuple] = {}
    blocks: list[TerminalBlock] = []
    for end in ends:
        x, y, z = end
        found = [p for p in _covering(space, x, y, z) if _blocks(space, p)]
        if not found:
            continue
        tags = tuple(sorted({p.tag for p in found}))
        kinds = tuple(sorted({p.kind for p in found}))
        best: tuple[float, float, float, str] | None = None
        walls = _walls(space, x, y)
        for wall in walls:
            along = x if wall.axis == "x" else y
            k = 1
            while best is None or k * STEP_M < best[0]:
                if k * STEP_M > REACH_M:
                    break
                for sign in (1, -1):
                    at = along + sign * k * STEP_M
                    if not wall.along[0] <= at <= wall.along[1]:
                        continue
                    px, py = (at, y) if wall.axis == "x" else (x, at)
                    if not _covering(space, px, py, z) and (best is None
                                                            or k * STEP_M < best[0]):
                        best = (k * STEP_M, px, py, wall.tag)
                k += 1
        if best is None:
            blocks.append(TerminalBlock(end, tags, kinds, walls[0].tag if walls else None))
            continue
        moved[end] = (best[1], best[2], z)
        blocks.append(TerminalBlock(end, tags, kinds, best[3], (best[1], best[2])))
    return moved, blocks


def column_block(space: Any, end: tuple[float, float, float]) -> TerminalBlock | None:
    """The door swings and ducts BELOW ``end`` in its plan column, as a block, else None. For
    an end the search could not leave: the pardon no longer lets a riser cross them."""
    x, y, z = end
    found = [p for p in space.hard if _blocks(space, p) and p.z0_m < z
             and p.footprint.covers(Point(x, y))]
    if not found:
        return None
    return TerminalBlock(end, tuple(sorted({p.tag for p in found})),
                         tuple(sorted({p.kind for p in found})), column=True)
