"""The take-off table a ``--fixture`` refusal prints: every candidate, and what stops it.

A refusal that names only the cheapest take-off's first blocker hides the answer when the
second-cheapest is one supply leg away from clear. Each row probes one candidate the way a
plumber looks up a wall: a plumb riser from the arm's real invert against
the vent space's hard prisms and then its framing. ``mep_drain_routing_basis.md`` §14.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN


@dataclass(frozen=True)
class TakeoffRow:
    """One candidate take-off: where, how far down the arm, which wall, what it meets."""

    station_in: tuple[float, float]
    arm_in: float
    wall: str | None
    #: ``routing.diagnostics.Blocker`` the riser meets first, or None.
    blocker: Any = None
    blocker_height_in: float | None = None
    #: The vent lattice reaches a stack from here.
    vent_reach: bool = False

    def line(self) -> str:
        x, y = self.station_in
        where = f'({x:.2f}", {y:.2f}") {self.wall or "no cavity"}, arm {self.arm_in:.0f}"'
        if self.blocker is not None:
            return (f"{where}: rises into {self.blocker.tag} ({self.blocker.mobility.value}) "
                    f'{self.blocker_height_in:.2f}" above the arm')
        if self.wall is None:
            return f"{where}: no wall cavity holds the vent here"
        return f"{where}: " + ("clear to a vent" if self.vent_reach else
                               "rises clear but meets no vent leg")

    def payload(self, *, coordinates: bool = True) -> dict:
        out = {"wall": self.wall, "arm_in": round(self.arm_in, 2),
               "blocker": None if self.blocker is None else self.blocker.tag,
               "blocker_height_in": (None if self.blocker_height_in is None
                                     else round(self.blocker_height_in, 2)),
               "vent_reach": self.vent_reach}
        if coordinates:
            out = {"station_in": [round(v, 3) for v in self.station_in], **out}
        return out


def takeoff_table(space_vent: Any, drain_graph: Any, reach: dict, candidates: list[int],
                  arm_z: dict[int, float], top_m: float, *, walls: dict[int, str],
                  by_drain: frozenset[int] = frozenset(), limit: int = 12
                  ) -> list[TakeoffRow]:
    """A row per candidate, cheapest first; with none, the cheapest arm-reachable nodes.

    ``space_vent`` is None where no vent lattice was built: the rows then say only where the
    arm reaches and that no cavity is there.
    """
    nodes = candidates or sorted(reach, key=lambda n: reach[n].cost)[:limit]
    rows = []
    for index in nodes[:limit]:
        node = drain_graph.nodes[index]
        z = arm_z.get(index, node.z)
        hit = (None if space_vent is None or index not in walls
               else _riser_blocker(space_vent, node.x, node.y, z, top_m))
        rows.append(TakeoffRow(
            station_in=(node.x / M_PER_IN, node.y / M_PER_IN),
            arm_in=reach[index].developed_ft * 12.0 if index in reach else 0.0,
            wall=walls.get(index), blocker=None if hit is None else hit[0],
            blocker_height_in=None if hit is None else (hit[1] - z) / M_PER_IN,
            vent_reach=index in by_drain))
    return rows


def _riser_blocker(space: Any, x: float, y: float, z0: float, top_m: float):
    """``(Blocker, z)`` a plumb riser from ``z0`` meets first: hard prisms, then framing.

    What the take-off itself stands in is pardoned, as ``graph.build_graph`` pardons it."""
    from shapely.geometry import Point

    from typehaus.routing.diagnostics import Blocker, mobility_of

    pardoned = space.blocked_all((x, y), z0)
    probe = Point(x, y)
    hard = [p for i in (space._index("hard").query(probe) if space.hard else ())  # noqa: SLF001
            if (p := space.hard[int(i)]).tag not in pardoned and p.z1_m >= z0
            and p.z0_m <= top_m and p.footprint.covers(probe)]
    if hard:
        prism = min(hard, key=lambda p: p.z0_m)
        z = max(prism.z0_m, z0)
        return Blocker(prism.tag, prism.kind, mobility_of(prism.kind), x, y, z), z
    members = getattr(space, "members", None)
    hit = None if members is None else members.riser_blocker(x, y, z0, top_m)
    if hit is None:
        return None
    return Blocker(hit[0], "member", mobility_of("member"), x, y, hit[1]), hit[1]
