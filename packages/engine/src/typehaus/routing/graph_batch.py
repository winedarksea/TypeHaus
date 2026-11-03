"""Vectorised hard/soft/rail queries for a whole lattice at once.

Each function answers exactly what the scalar ``RoutingSpace`` method does, point for point
(same GEOS predicates, same float ops), so a graph built from them is bit-identical to the
scalar build. Only the call overhead goes: one STRtree query per level rather than per node
or edge. Order-dependent answers (which prism a lone terminal stands in, overlapping rooms)
stay on the scalar path."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import shapely
from shapely import STRtree

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.space import RoutingSpace

_GRID_M = 0.0015875


def _flags(tree: STRtree, geoms: np.ndarray, z: np.ndarray, z0: np.ndarray,
           z1: np.ndarray) -> np.ndarray:
    """True where a geometry meets a prism whose z range holds ``z``."""
    out = np.zeros(len(geoms), dtype=bool)
    if len(geoms) == 0:
        return out
    qi, pi = tree.query(geoms, predicate="intersects")
    keep = (z0[pi] <= z[qi]) & (z[qi] <= z1[pi])
    out[qi[keep]] = True
    return out


def points_blocked(space: RoutingSpace, xs: np.ndarray, ys: np.ndarray,
                   z: np.ndarray) -> np.ndarray:
    """``space.blocked(point, z) is not None`` for many points."""
    if not space.hard:
        return np.zeros(len(xs), dtype=bool)
    z0 = np.array([p.z0_m for p in space.hard])
    z1 = np.array([p.z1_m for p in space.hard])
    return _flags(space._index("hard"), shapely.points(np.column_stack((xs, ys))), z, z0, z1)


def edges_state(space: RoutingSpace, a: np.ndarray, b: np.ndarray, axis: np.ndarray):
    """``(blocked, soft)`` for level steps. ``a``/``b`` are (N, 3) x, y, z endpoints and
    ``axis`` is 0 for x, 1 for y. ``blocked`` mirrors ``edge_blocked(...) is not None`` with
    no ``ignore``; ``soft[i]`` is ``soft_at(mid, midz)``."""
    n = len(a)
    mx, my = (a[:, 0] + b[:, 0]) / 2.0, (a[:, 1] + b[:, 1]) / 2.0
    mz = (a[:, 2] + b[:, 2]) / 2.0
    blocked = np.zeros(n, dtype=bool)
    if space.hard:
        z0 = np.array([p.z0_m for p in space.hard])
        z1 = np.array([p.z1_m for p in space.hard])
        blocked = _flags(space._index("hard"), shapely.points(np.column_stack((mx, my))),
                         mz, z0, z1)
        live = np.flatnonzero(~blocked)
        lines = shapely.linestrings(np.stack((a[:, :2], b[:, :2]), axis=1))
        # Oblique or round footprints can be clipped between nodes: test the segment.
        shapes = [(k, s.context) for k, s in enumerate(space._exact_footprints())
                  if s is not None]
        if shapes and len(live):
            ids = np.array([k for k, _ in shapes])
            tree = STRtree([g for _, g in shapes])
            qi, pi = tree.query(lines[live], predicate="intersects")
            k = ids[pi]
            keep = (z0[k] <= mz[live][qi]) & (mz[live][qi] <= z1[k])
            blocked[live[qi[keep]]] = True
        live = np.flatnonzero(~blocked)
        if space.rails and len(live):
            blocked[live[_rail_hits(space, lines[live], a[live], b[live], axis[live])]] = True

    soft: list = [[]] * n
    if space.soft:
        szero = np.array([p.z0_m for p in space.soft])
        sone = np.array([p.z1_m for p in space.soft])
        qi, pi = space._index("soft").query(
            shapely.points(np.column_stack((mx, my))), predicate="intersects")
        keep = (szero[pi] <= mz[qi]) & (mz[qi] <= sone[pi])
        found: dict[int, list[int]] = {}
        for q, p in zip(qi[keep].tolist(), pi[keep].tolist(), strict=True):
            found.setdefault(q, []).append(p)
        for q, members in found.items():
            kinds = [space.soft[p].kind for p in members]
            if kinds.count("room") > 1 or kinds.count("wall") > 1:
                # Which overlapping room wins is the tree's order: ask the scalar path.
                soft[q] = space.soft_at((mx[q], my[q]), mz[q])
            else:
                soft[q] = [space.soft[p] for p in members]
    return blocked, soft


def _rail_hits(space: RoutingSpace, lines: np.ndarray, a: np.ndarray, b: np.ndarray,
               axis: np.ndarray) -> np.ndarray:
    """Indices into ``lines`` that ``space._rail_blocked`` would block."""
    if space._rail_index is None:
        space._rail_blocked((0.0, 0.0), (1.0, 0.0), 0.0)  # builds the index
    rails = space.rails
    r_axis = np.array([0 if r[0] == "x" else 1 for r in rails])
    r_station, r_lo, r_hi, r_half, r_z0, r_z1 = (
        np.array([r[i] for r in rails]) for i in (1, 2, 3, 4, 5, 6))
    grow = space.radius_m + space.clearance_m
    qi, pi = space._rail_index.query(lines, predicate="intersects")
    ax = axis[qi]
    station = np.where(ax == 0, a[qi, 1], a[qi, 0])
    lo_e = np.where(ax == 0, np.minimum(a[qi, 0], b[qi, 0]), np.minimum(a[qi, 1], b[qi, 1]))
    hi_e = np.where(ax == 0, np.maximum(a[qi, 0], b[qi, 0]), np.maximum(a[qi, 1], b[qi, 1]))
    z = ((a[qi, 2] + b[qi, 2]) / 2.0)
    ok = ((r_axis[pi] == ax)
          & ~(np.abs(station - r_station[pi]) >= r_half[pi] + grow - _GRID_M)
          & (r_z0[pi] - grow < z) & (z < r_z1[pi] + grow)
          & (np.minimum(hi_e, r_hi[pi]) - np.maximum(lo_e, r_lo[pi]) > _GRID_M))
    return np.unique(qi[ok])
