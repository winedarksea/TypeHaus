"""A cold main and its branches as one tree: the pure parts (``cli/cmd_route_supply_tree``).

A trunk is the route to the farthest fixture, laid first inside a **z gate** — horizontal travel
only where the floor system hangs it: from a fixed drop under the joists up to the top of the
members' common window. A level run above the gate is a pipe flying through the living space,
which a lattice with a plane at the sink-stop height will gladly price as cheap. Each end of the
trunk gets a hole in the gate (a riser lane), and every other branch is free, farthest first,
teeing onto the trunk. ``mep_supply_trunk_basis.md`` §4 (order) and §5 (the gate) are worked by
hand; the tee stations are its §2.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN

#: The gate opens this far round each end of the trunk, for the riser: a stud bay either side.
HOLE_M = 24.0 * M_PER_IN
#: How far under the members the gate reaches. A pipe hung a foot under the joists is still the
#: ceiling's; one at the slab is not, which is why the gate has a floor at all.
UNDER_M = 12.0 * M_PER_IN
#: The plane offered under the members: the authored trunk's "old band" is ~3" below them.
UNDER_PLANE_M = 4.0 * M_PER_IN
_TOL_M = 0.0032  # a tee is ON a laid line: the 1/8" ``cmd_route_tree`` allows, no more


@dataclass(frozen=True)
class Gate:
    """Centreline band a trunk's level legs may ride, and the lattice planes that serve it."""

    lo_m: float
    hi_m: float
    planes: tuple[float, ...]


def gate_for(windows: Sequence[tuple[float, float]], member_low_m: float,
             radius_m: float) -> Gate | None:
    """The gate over floor members whose crossing windows are ``windows`` (z0, z1).

    Top: the tightest window top, less the pipe's radius. Bottom: ``UNDER_M`` under the members.
    ``None`` when the common window is narrower than the pipe, or there is none."""
    if not windows:
        return None
    low, high = max(w[0] for w in windows), min(w[1] for w in windows)
    if high - low < 2.0 * radius_m:
        return None
    top = high - radius_m
    return Gate(lo_m=member_low_m - UNDER_M + radius_m, hi_m=top,
                planes=(member_low_m - UNDER_PLANE_M, (low + radius_m + top) / 2.0))


def gate_prisms(bbox: tuple[float, float, float, float], gates: Gate | Sequence[Gate],
                holes: Iterable[tuple[float, float]]) -> list[Any]:
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
    footprint = box(*bbox).difference(MultiPoint(list(holes)).buffer(HOLE_M))
    edges = [-1.0e3, *[z for band in bands for z in band], 1.0e3]
    return [HardPrism(tag="SUPPLY-GATE", kind="avoid", footprint=footprint,
                      z0_m=lo + (1e-4 if i else 0.0), z1_m=hi - (1e-4 if i < len(bands) else 0.0))
            for i, (lo, hi) in enumerate(zip(edges[0::2], edges[1::2], strict=True))]


def plan_key(root: tuple[float, ...], point: tuple[float, ...]) -> float:
    """Manhattan plan distance from the root: the a-priori farthest-first key. The developed
    length is only known once a route exists, and ordering is what that would be for."""
    return abs(point[0] - root[0]) + abs(point[1] - root[1])


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
              tol_m: float = _TOL_M) -> float | None:
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
            if gap <= _TOL_M and (best is None or gap < best[0] - 1e-9):
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


def nodes_on(xyz: Any, points: Sequence[tuple[float, ...]], *, tol_m: float,
             z_tol_m: float) -> set[int]:
    """Indices of the lattice nodes (rows of ``xyz``) ON a 3-D polyline: within ``tol_m`` in
    plan, and at its elevation there. A riser holds every z between its ends."""
    import numpy as np

    out: set[int] = set()
    segments = list(zip(points, points[1:], strict=False)) or [(points[0], points[0])]
    for a, b in segments:
        dx, dy = b[0] - a[0], b[1] - a[1]
        span = dx * dx + dy * dy
        if span <= 1e-12:
            near = ((xyz[:, 0] - a[0]) ** 2 + (xyz[:, 1] - a[1]) ** 2 <= tol_m ** 2) & (
                xyz[:, 2] >= min(a[2], b[2]) - z_tol_m) & (
                xyz[:, 2] <= max(a[2], b[2]) + z_tol_m)
        else:
            t = np.clip(((xyz[:, 0] - a[0]) * dx + (xyz[:, 1] - a[1]) * dy) / span, 0.0, 1.0)
            gap = (a[0] + t * dx - xyz[:, 0]) ** 2 + (a[1] + t * dy - xyz[:, 1]) ** 2
            near = (gap <= tol_m ** 2) & (np.abs(a[2] + t * (b[2] - a[2]) - xyz[:, 2])
                                          <= z_tol_m)
        out.update(int(i) for i in np.nonzero(near)[0])
    return out


def capacity_wsfu(diameter_m: float, table: Iterable[tuple[float, float]]) -> float:
    """WSFU a run of this diameter carries, from a (size in, capacity) table; the 0.06" slack
    is ``mep.pipe_sizing``'s own, so a 0.5" PEX line (0.5 + 0.06 >= 0.5) reads as 0.5"."""
    inches = diameter_m / M_PER_IN
    return max((cap for size, cap in table if size <= inches + 0.06), default=0.0)
