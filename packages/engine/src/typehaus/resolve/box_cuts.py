"""Framing stops at a device box: liner furring or resilient channel that a flush wall box
crosses is cut round it, a box width plus ``CLEAR_M`` each side; a backing band is notched,
keeping a strip over and under the box where ``MIN_STRIP_M`` of it remains.

Late (after ``backing_datums``), so every box and band is where it ends up. Pieces keep the
member's key with ``-box-<i>``; a piece shorter than ``MIN_PIECE_M`` is dropped. The takeoff
bills these members by the foot, so the cut only trims their length.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from shapely.geometry import Polygon

from typehaus.quantities import M_PER_IN
from typehaus.resolve.box_obstacles import cut_at_boxes
from typehaus.resolve.geometry_members import member_box

CLEAR_M = 0.125 * M_PER_IN
MIN_PIECE_M = 1.0 * M_PER_IN
MIN_STRIP_M = 0.75 * M_PER_IN
_TOL_M = 1e-4


def resolve_box_cuts(model: Any) -> None:
    boxes: dict[str, list[Any]] = {}
    for box in model.device_boxes:
        if box.wall_tag and box.mounting != "surface" and box.footprint:
            boxes.setdefault(box.wall_tag, []).append(box)
    for index, wall in enumerate(model.walls):
        mine = boxes.get(wall.tag)
        if not mine:
            continue
        members, changed = [], False
        for member in wall.members:
            pieces = _cut(member, mine) if cut_at_boxes(member) else None
            if pieces is None:
                members.append(member)
                continue
            changed = True
            members.extend(pieces)
        if changed:
            model.walls[index] = replace(wall, members=tuple(members))


def _cut(member: Any, boxes: list[Any]) -> list[Any] | None:
    """The member's pieces round every box it crosses, or None when it crosses none."""
    if member.p0 == member.p1 or member.plan_outline is not None:
        return None
    solid = member_box(member)
    if solid is None:
        return None
    plan = Polygon([(x, y) for x, y, _z in solid.corners_bottom])
    (ax, ay), (bx, by) = member.p0, member.p1
    run = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / run, (by - ay) / run)
    gaps = []
    for box in boxes:
        if min(member.z1_m, box.z1_m) - max(member.z0_m, box.z0_m) <= _TOL_M:
            continue
        footprint = Polygon(box.footprint)
        if plan.intersection(footprint).area <= _TOL_M * _TOL_M:
            continue
        along = [(x - ax) * u[0] + (y - ay) * u[1] for x, y in box.footprint]
        gaps.append((min(along) - CLEAR_M, max(along) + CLEAR_M,
                     box.z0_m - CLEAR_M, box.z1_m + CLEAR_M))
    if not gaps:
        return None
    spans, start = [], 0.0
    for lo, hi, _, _ in sorted(gaps):
        if lo > start:
            spans.append((start, min(lo, run)))
        start = max(start, hi)
    if start < run:
        spans.append((start, run))
    pieces = [(a, b, None) for a, b in spans if b - a >= MIN_PIECE_M]
    level = member.z0_end_m is None and member.z1_end_m is None
    if member.child_key.startswith("backing-") and level:  # the notch's strips
        for lo, hi, z0, z1 in sorted(gaps):
            a, b = max(lo, 0.0), min(hi, run)
            for band in ((member.z0_m, z0), (z1, member.z1_m)):
                if band[1] - band[0] >= MIN_STRIP_M and b - a >= MIN_PIECE_M:
                    pieces.append((a, b, band))
    return [_piece(member, i, a, b, run, u, band) for i, (a, b, band) in enumerate(pieces)]


def _piece(member: Any, i: int, a: float, b: float, run: float, u: tuple[float, float],
           band: tuple[float, float] | None = None) -> Any:
    (ax, ay) = member.p0
    raked = {}
    if member.z0_end_m is not None or member.z1_end_m is not None:
        def at(start: float, end: float | None, s: float) -> float:
            return start + ((start if end is None else end) - start) * s / run
        raked = dict(z0_m=at(member.z0_m, member.z0_end_m, a),
                     z1_m=at(member.z1_m, member.z1_end_m, a),
                     z0_end_m=at(member.z0_m, member.z0_end_m, b),
                     z1_end_m=at(member.z1_m, member.z1_end_m, b))
    elif band is not None:
        raked = dict(z0_m=band[0], z1_m=band[1])
    return replace(member, child_key=f"{member.child_key}-box-{i}",
                   p0=(ax + u[0] * a, ay + u[1] * a), p1=(ax + u[0] * b, ay + u[1] * b),
                   length_m=b - a, **raked,
                   cut_length_m=None if member.cut_length_m is None else b - a)
