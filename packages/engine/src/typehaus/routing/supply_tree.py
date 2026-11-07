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
    return Gate(lo_m=low + radius_m, hi_m=high - radius_m,
                planes=(((low + radius_m) + (high - radius_m)) / 2.0,))


def gate_prisms(bbox: tuple[float, float, float, float], gates: Gate | Sequence[Gate],
                holes: Iterable[tuple[float, float]],
                tight: Iterable[tuple[float, float]] = ()) -> list[Any]:
    """Hard prisms over everything outside the gate(s), holed where a riser may stand.

    Several gates (one per floor system) leave every height between them blocked too: a
    branch hangs from a floor system or rises in a hole, and flies nowhere else."""
    from shapely.geometry import MultiPoint, box

    from typehaus.routing.obstacles import HardPrism

    bands: list[list[float]] = []
    for gate in sorted([gates] if isinstance(gates, Gate) else gates, key=lambda g: g.lo_m):
        if bands and gate.lo_m <= bands[-1][1]:
            bands[-1][1] = max(bands[-1][1], gate.hi_m)
        else:
            bands.append([gate.lo_m, gate.hi_m])
    opening = [shape for pts, size in ((list(holes), HOLE_M), (list(tight), TIGHT_M)) if pts
               for shape in (MultiPoint(pts).buffer(size, cap_style="square"),)]
    footprint = box(*bbox)
    for shape in opening:
        footprint = footprint.difference(shape)
    edges = [-1.0e3, *[z for band in bands for z in band], 1.0e3]
    return [HardPrism(tag="SUPPLY-GATE", kind="avoid", footprint=footprint,
                      z0_m=lo + (1e-4 if i else 0.0), z1_m=hi - (1e-4 if i < len(bands) else 0.0))
            for i, (lo, hi) in enumerate(zip(edges[0::2], edges[1::2], strict=True))]


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


def capacity_wsfu(diameter_m: float, table: Iterable[tuple[float, float]]) -> float:
    """WSFU a run of this diameter carries, from a (size in, capacity) table; the 0.06" slack
    is ``mep.pipe_sizing``'s own, so a 0.5" PEX line (0.5 + 0.06 >= 0.5) reads as 0.5"."""
    inches = diameter_m / M_PER_IN
    return max((cap for size, cap in table if size <= inches + 0.06), default=0.0)
