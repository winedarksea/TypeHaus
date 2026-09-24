"""Where along a member its nodes fall, and folding two nodes at one station into one.

Split out of ``members.py`` (AGENTS.md's 500-line rule).
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.analytical.graph import NODE_SNAP_M

_Vec3 = tuple[float, float, float]


def stations(axis: Any, points: list[_Vec3], extra: Any = (),
              merged: dict[int, int] | None = None) -> list[tuple[float, int]]:
    """``(parameter, node index)`` for every node ON this axis, ends included, in order.

    A node within :data:`NODE_SNAP_M` of the axis is on it — the same distance two points
    merge at, so a node cannot be "nearly" on a member and be treated as elsewhere.

    Two nodes at one station are one node, and the one dropped here is recorded in
    ``merged`` so every OTHER member ending on it is folded onto the kept one (:func:`fold`):
    a post under a hung beam's seat joins the seat's node rather than being dropped from
    the carrier and left standing on nothing (catlin's PT-BW-IC under BM-BW-FC's hanger).
    """
    found: list[tuple[float, int]] = list(extra)
    length = axis.length_m
    for index, point in enumerate(points):
        param = _param_on(axis, point)
        if param is None:
            continue
        if all(index != seen for _param, seen in found):
            found.append((param, index))
    found.sort()
    # Two stations closer together than the snap distance are one station; keeping both
    # would mint a member shorter than the tolerance its own nodes were merged at.
    out: list[tuple[float, int]] = []
    for param, index in found:
        if out and abs(param - out[-1][0]) * length <= NODE_SNAP_M:
            kept = out[-1][1]
            if merged is not None and index != kept:
                merged[index] = kept
            continue
        out.append((param, index))
    return out


def fold(nodes: Any, merged: dict[int, int]) -> list[str]:
    """Node ids with every merged index pointing at the node it was folded into."""
    def root(index: int) -> int:
        while index in merged:
            index = merged[index]
        return index

    for index in merged:
        nodes.labels[root(index)] |= nodes.labels[index]
    ids = nodes.ids()
    return [ids[root(index)] for index in range(len(ids))]


def _param_on(axis: Any, point: _Vec3) -> float | None:
    """The parameter of ``point`` on ``axis``, or ``None`` where it is not on it."""
    d = (axis.p1[0] - axis.p0[0], axis.p1[1] - axis.p0[1], axis.p1[2] - axis.p0[2])
    denominator = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
    if denominator < 1e-18:
        return None
    raw = sum(d[axis_index] * (point[axis_index] - axis.p0[axis_index])
              for axis_index in range(3)) / denominator
    param = min(max(raw, 0.0), 1.0)
    return param if math.dist(axis.at(param), point) <= NODE_SNAP_M else None
