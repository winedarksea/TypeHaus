"""A cold main and its branches as one tree: the pure parts (``cli/cmd_route_supply_tree``).

A trunk is the route to the farthest fixture, laid first inside a **z gate**: level travel only
inside the floor members' common crossing window (the note's §5 gate). A level run above it is a
pipe flying through the living space, which a lattice with a plane at the sink-stop height will
price as cheap. Each end of the trunk gets a hole in the gate (a riser lane), and every other
branch is laid farthest first, teeing onto the trunk. ``mep_supply_trunk_basis.md`` §4 (order),
§5 (the gate) and §2 (tee stations) are worked by hand.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN

#: The gate opens this far round each end of the trunk, for the riser: a stud bay either side.
HOLE_M = 24.0 * M_PER_IN
#: A branch's fixture end: its riser stands in the wall at the fixture, not across the room.
TIGHT_M = 12.0 * M_PER_IN
#: ONE tolerance for "on a laid line", in 3-D: 1/4", past the 1/16" snap of every coordinate.
ON_M = 0.0064
#: A tight hole inside a lane's band: the end's own riser column, no wider.
PIN_M = 1.0 * M_PER_IN


@dataclass(frozen=True)
class Gate:
    """Centreline band a trunk's level legs may ride, and the lattice planes that serve it."""

    lo_m: float
    hi_m: float
    planes: tuple[float, ...]


def gate_for(windows: Sequence[tuple[float, float]], radius_m: float) -> Gate | None:
    """The z gate over floor members whose crossing windows are ``windows`` (z0, z1): the
    note's §5 band, each end of the common window brought in by the pipe's radius. ``None``
    when the common window is narrower than the pipe, or there is none."""
    if not windows:
        return None
    low, high = max(w[0] for w in windows), min(w[1] for w in windows)
    if high - low < 2.0 * radius_m:
        return None
    lo, hi = low + radius_m, high - radius_m
    # The middle plane first, then the two extremes a run presses to: an authored run (catlin's
    # PR-B-HW-BATH2) may sit across the middle one, and only a lower or upper tier passes it.
    return Gate(lo_m=lo, hi_m=hi, planes=((lo + hi) / 2.0, *((lo, hi) if hi > lo else ())))


@dataclass(frozen=True)
class Lane:
    """Wall cover a branch may ride outside the gate: a plan area over one z band (§5b)."""

    footprint: Any
    lo_m: float
    hi_m: float


def lane_band(gates: Sequence[Gate], z: float) -> tuple[float, float] | None:
    """From a fixture end's height ``z`` to the nearest gate edge below it (else above it):
    the storey band its branch climbs or drops through. None inside a gate, or no gate."""
    if any(g.lo_m <= z <= g.hi_m for g in gates):
        return None
    below = [g.hi_m for g in gates if g.hi_m < z]
    if below:
        return max(below), z + ON_M
    above = [g.lo_m for g in gates if g.lo_m > z]
    return (z - ON_M, min(above)) if above else None


def wall_lanes(model: Any, gates: Sequence[Gate],
               ends: Iterable[tuple[Sequence[float], Sequence[tuple[float, float]]]]
               ) -> list[Lane]:
    """For each ``(end, stations)``: the layers of walls standing at the end's height, within a
    bay of the end and its plan's riser stations, opened over :func:`lane_band`. Storey-banded
    and local: a branch rides the walls its own plan rides, never every wall at every height."""
    from shapely.geometry import LineString, MultiPoint, Polygon

    from typehaus.resolve.overlay import union_all

    floor = {s.tag: s.elevation.meters for s in model.plan.storeys}
    out: list[Lane] = []
    for end, stations in ends:
        z = end[2]
        band = lane_band(gates, z)
        if band is None:
            continue
        near = MultiPoint([tuple(end[:2]), *stations]).envelope.buffer(
            HOLE_M, cap_style="square")

        def own(wall: Any, z: float = z) -> bool:
            """Stands at ``z`` on the end's own storey: no gate between its floor and z (the
            check's cover is per storey; a wall from below reaching up is not it)."""
            base = floor.get(wall.storey, wall.z0_m)
            return (wall.z0_m <= z <= wall.z1_m and base <= z
                    and not any(base < g.lo_m and g.hi_m < z for g in gates))

        polys = [Polygon(layer.polygon) for wall in model.walls if own(wall)
                 for layer in wall.layers if len(layer.polygon) >= 3]
        polys = [q for q in polys if q.is_valid and not q.is_empty and q.intersects(near)]
        # The end's own stub to a riser station beside it (the plan's short leg at its height): a
        # 1" slot joins the two pins, else a sliver of gate between them cuts the end off.
        polys += [LineString([tuple(end[:2]), st]).buffer(PIN_M, cap_style="square")
                  for st in stations if math.dist(end[:2], st) <= 2.0 * TIGHT_M]
        if polys:
            out.append(Lane(union_all(polys).intersection(near), *band))
    return out


def gate_prisms(bbox: tuple[float, float, float, float], gates: Gate | Sequence[Gate],
                holes: Iterable[tuple[float, float]],
                tight: Iterable[tuple[float, float]] = (),
                lanes: Sequence[Lane] = ()) -> list[Any]:
    """Hard prisms over everything outside the gate(s), holed where a riser may stand and,
    over each lane's band, over its walls.

    Several gates (one per floor system) leave every height between them blocked too: a
    branch hangs from a floor system, rises in a hole or rides a lane, and flies nowhere else."""
    from shapely.geometry import MultiPoint, box

    from typehaus.routing.obstacles import HardPrism

    bands: list[list[float]] = []
    for gate in sorted([gates] if isinstance(gates, Gate) else gates, key=lambda g: g.lo_m):
        if bands and gate.lo_m <= bands[-1][1]:
            bands[-1][1] = max(bands[-1][1], gate.hi_m)
        else:
            bands.append([gate.lo_m, gate.hi_m])
    tight = list(tight)
    footprint = box(*bbox)
    if holes := list(holes):
        footprint = footprint.difference(MultiPoint(holes).buffer(HOLE_M, cap_style="square"))
    # In a lane's band a tight hole shrinks to its own point: the riser stands in the walls or
    # on the end, and the hole's square is no room's air to ride level through.
    wide, narrow = (footprint.difference(MultiPoint(tight).buffer(size, cap_style="square"))
                    if tight else footprint for size in (TIGHT_M, PIN_M))
    edges = [-1.0e3, *[z for band in bands for z in band], 1.0e3]
    out = []
    for i, (lo, hi) in enumerate(zip(edges[0::2], edges[1::2], strict=True)):
        lo, hi = lo + (1e-4 if i else 0.0), hi - (1e-4 if i < len(bands) else 0.0)
        cuts = sorted({lo, hi, *(z for ln in lanes for z in (ln.lo_m, ln.hi_m) if lo < z < hi)})
        for z0, z1 in zip(cuts, cuts[1:], strict=False):
            mine = [ln.footprint for ln in lanes if ln.lo_m <= z0 and z1 <= ln.hi_m]
            shape = narrow if mine else wide
            for lane in mine:
                shape = shape.difference(lane)
            out.append(HardPrism(tag="SUPPLY-GATE", kind="avoid", footprint=shape,
                                 z0_m=z0, z1_m=z1))
    return out


def outside_prisms_holed(model: Any, space: Any, ends: Iterable[Sequence[float]]) -> list[Any]:
    """The house's outside as hard prisms for a pressure run: a pipe may leave only where a run
    ends (a wall hydrant stands on the face), a foot round each ``ends`` plan point. Drains get the
    same prisms unholed (``gravity_band.outside_prisms``); hydrant runs are no obstacle here."""
    from dataclasses import replace

    from shapely.geometry import MultiPoint

    from typehaus.routing.gravity_band import outside_prisms

    holes = MultiPoint([tuple(p[:2]) for p in ends]).buffer(TIGHT_M, cap_style="square")
    return [replace(p, footprint=p.footprint.difference(holes))
            for p in outside_prisms(model, space)]


def riser_stations(path: Sequence[Sequence[float]], z: Sequence[float]
                   ) -> list[tuple[float, float]]:
    """Plan points where an authored run rises (consecutive vertices on one plan point, at
    different heights): where the plan already stands a riser, in cover (§5a)."""
    out: list[tuple[float, float]] = []
    for (a, za), (b, zb) in zip(zip(path, z, strict=False), zip(path[1:], z[1:], strict=False),
                                 strict=False):
        if math.dist(a[:2], b[:2]) < ON_M and abs(za - zb) > ON_M and (a[0], a[1]) not in out:
            out.append((a[0], a[1]))
    return out


def plan_key(root: tuple[float, ...], point: tuple[float, ...]) -> float:
    """Manhattan plan distance from the root: the key that picks the trunk's far end, before
    any route exists to develop a length on."""
    return abs(point[0] - root[0]) + abs(point[1] - root[1])


def developed_key(trunk: Sequence[tuple[float, ...]], point: tuple[float, ...]) -> float:
    """Developed length from the source to ``point`` by way of the trunk: along the trunk to
    the best leaving point, then Manhattan in 3-D (a pipe runs square). The note's §4 key,
    with the branch's own developed length estimated rather than known. The trunk is sampled
    at 1" on each leg; the minimum over its length is the tee a router would pick."""
    best = math.inf
    run = 0.0
    for a, b in zip(trunk, trunk[1:], strict=False):
        length = math.dist(a, b)
        steps = max(1, int(length / M_PER_IN))
        for i in range(steps + 1):
            t = i / steps
            p = tuple(q + t * (r - q) for q, r in zip(a, b, strict=True))
            best = min(best, run + t * length + sum(abs(u - v) for u, v in zip(p, point,
                                                                              strict=True)))
        run += length
    return best


def farthest_first(keys: dict[str, float]) -> list[str]:
    """Tags farthest first; the tag breaks ties, so two runs return one tree."""
    return sorted(keys, key=lambda tag: (-keys[tag], tag))


def own_fixtures(serves: dict[str, tuple[str, ...]], kids: dict[str, list[str]]
                 ) -> dict[str, tuple[str, ...]]:
    """What each run feeds itself: its ``serves`` less what its children's cover."""
    out = {}
    for tag, mine in serves.items():
        covered = {f for kid in kids.get(tag, ()) for f in serves.get(kid, ())}
        out[tag] = tuple(f for f in mine if f not in covered)
    return out


def terminal_tags(order: Sequence[str], own: dict[str, tuple[str, ...]],
                  kids: dict[str, list[str]], at_port: frozenset[str]) -> list[str]:
    """The runs whose far end is a thing to feed: a fixture, an equipment port, or a bare stub.
    A distribution run (nothing of its own, children hanging off it) is none of those."""
    return [tag for tag in order if own.get(tag) or at_port & {tag} or not kids.get(tag)]


def group_of(parent: dict[str, str | None], trunk: str, tag: str) -> str:
    """The top-level branch ``tag`` hangs off (the child of ``trunk`` on its chain); the trunk
    itself is its own group, ``""``."""
    seen: set[str] = set()
    while tag != trunk and tag not in seen:
        seen.add(tag)
        up = parent.get(tag)
        if up is None or up == trunk:
            return tag
        tag = up
    return ""


def developed_m(points: Sequence[tuple[float, ...]]) -> float:
    """Sum of 3-D segment lengths, ``RouteProposal.developed_ft``'s formula in metres."""
    return sum(math.dist(a, b) for a, b in zip(points, points[1:], strict=False))


def station_m(points: Sequence[tuple[float, ...]], point: tuple[float, ...],
              tol_m: float = ON_M) -> float | None:
    """Developed distance along ``points`` to ``point``, or None when it is not on the line."""
    run = 0.0
    for a, b in zip(points, points[1:], strict=False):
        length = math.dist(a, b)
        if length > 0:
            t = max(0.0, min(1.0, sum((p - q) * (r - q) for p, q, r in zip(point, a, b,
                                                                          strict=True))
                            / (length * length)))
            foot = tuple(q + t * (r - q) for q, r in zip(a, b, strict=True))
            if math.dist(foot, point) <= tol_m:
                return run + t * length
        run += length
    return None


def tee_onto(laid: dict[str, Sequence[tuple[float, ...]]], point: tuple[float, ...]
             ) -> str | None:
    """The laid route ``point`` stands on (the nearest foot; ties to the earlier laid)."""
    best: tuple[float, str] | None = None
    for tag, points in laid.items():
        for a, b in zip(points, points[1:], strict=False):
            length = math.dist(a, b)
            t = 0.0 if length == 0 else max(0.0, min(1.0, sum(
                (p - q) * (r - q) for p, q, r in zip(point, a, b, strict=True))
                / (length * length)))
            gap = math.dist(tuple(q + t * (r - q) for q, r in zip(a, b, strict=True)), point)
            if gap <= ON_M and (best is None or gap < best[0] - 1e-9):
                best = (gap, tag)
    return None if best is None else best[1]


def downstream_serves(own: dict[str, tuple[str, ...]], tee: dict[str, str | None],
                      fixtures: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """Each laid route's ``serves``: its own fixtures plus every route teed onto it, deeply.
    Listed in ``fixtures`` order, so the printed tuple does not depend on the laying order."""
    below: dict[str, set[str]] = {tag: set(mine) for tag, mine in own.items()}
    # Children are laid after their parent, so one pass from the last laid is enough.
    for tag in reversed(list(own)):
        up = tee.get(tag)
        if up is not None and up in below:
            below[up] |= below[tag]
    rank = {f: i for i, f in enumerate(fixtures)}
    return {tag: tuple(sorted(found, key=lambda f: (rank.get(f, len(rank)), f)))
            for tag, found in below.items()}


def clip_polyline(points: Sequence[tuple[float, float, float]],
                  bbox: tuple[float, float, float, float]
                  ) -> list[list[tuple[float, float, float]]]:
    """The parts of a 3-D polyline inside a plan box, as pieces with z interpolated.

    Seeds the lattice of a branch search with the stretch of trunk near it, not the whole
    house: every seed adds its x and y lines to every level."""
    minx, miny, maxx, maxy = bbox
    pieces: list[list[tuple[float, float, float]]] = []
    current: list[tuple[float, float, float]] = []

    def inside(p: Sequence[float]) -> bool:
        return minx <= p[0] <= maxx and miny <= p[1] <= maxy

    for a, b in zip(points, points[1:], strict=False):
        lo, hi = _crop(a, b, bbox)
        if lo is None:
            if current:
                pieces.append(current)
            current = []
            continue
        if not current or math.dist(current[-1], lo) > 1e-9:
            if current:
                pieces.append(current)
            current = [lo]
        current.append(hi)
    if current:
        pieces.append(current)
    if not pieces and len(points) == 1 and inside(points[0]):
        pieces.append([points[0]])
    return pieces


def _crop(a: Sequence[float], b: Sequence[float], bbox: tuple[float, float, float, float]
          ) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
    """The part of segment a-b inside ``bbox`` (Liang-Barsky on plan), z interpolated."""
    minx, miny, maxx, maxy = bbox
    t0, t1 = 0.0, 1.0
    for lo, hi, p, d in ((minx, maxx, a[0], b[0] - a[0]), (miny, maxy, a[1], b[1] - a[1])):
        if abs(d) < 1e-12:
            if not lo <= p <= hi:
                return None, None
            continue
        u, v = sorted(((lo - p) / d, (hi - p) / d))
        t0, t1 = max(t0, u), min(t1, v)
        if t0 > t1:
            return None, None
    at = [tuple(q + t * (r - q) for q, r in zip(a, b, strict=True)) for t in (t0, t1)]
    return at[0], at[1]  # type: ignore[return-value]


def nodes_on(xyz: Any, points: Sequence[tuple[float, ...]], *, tol_m: float = ON_M
             ) -> set[int]:
    """Indices of the lattice nodes (rows of ``xyz``) within ``tol_m`` (3-D) of a polyline —
    the tolerance ``station_m`` and ``tee_onto`` use, so a goal and its host agree."""
    import numpy as np

    out: set[int] = set()
    for a, b in list(zip(points, points[1:], strict=False)) or [(points[0], points[0])]:
        d = np.array([b[i] - a[i] for i in range(3)])
        span = float(d @ d)
        rel = xyz - np.array(a[:3])
        t = np.zeros(len(xyz)) if span <= 1e-18 else np.clip(rel @ d / span, 0.0, 1.0)
        gap = np.linalg.norm(rel - t[:, None] * d, axis=1)
        out.update(int(i) for i in np.nonzero(gap <= tol_m)[0])
    return out


def bend_nodes(xyz: Any, points: Sequence[Sequence[float]], reach_m: float,
               among: Iterable[int] | None = None) -> set[int]:
    """Lattice nodes (of ``among``, else all) within ``reach_m`` (3-D) of a bend of ``points``.
    A branch teeing there runs its first leg beside the host's next leg (or down its own riser):
    ``mep.run_interference``."""
    import numpy as np

    ids = np.fromiter(range(len(xyz)) if among is None else among, dtype=int)
    if not len(ids) or len(points) < 3:
        return set()
    near = np.zeros(len(ids), dtype=bool)
    for corner in points[1:-1]:
        near |= np.linalg.norm(xyz[ids] - np.array(corner[:3]), axis=1) <= reach_m
    return {int(i) for i in ids[near]}


def cut_nodes(graph: Any, nodes: Iterable[int]) -> None:
    """Drop every lattice edge at ``nodes``: no route passes or stops there."""
    for node in nodes:
        for axis, others in graph.edges.get(node, {}).items():
            for other in others:
                graph.edges[other][axis].remove(node)
            others.clear()


def capacity_wsfu(diameter_m: float, table: Iterable[tuple[float, float]]) -> float:
    """WSFU a run of this diameter carries, from a (size in, capacity) table; the 0.06" slack
    is ``mep.pipe_sizing``'s own, so a 0.5" PEX line (0.5 + 0.06 >= 0.5) reads as 0.5"."""
    inches = diameter_m / M_PER_IN
    return max((cap for size, cap in table if size <= inches + 0.06), default=0.0)
