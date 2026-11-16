"""A duct elbow's centreline arc, off its ``FittingRecord`` (decision #114).

R is the radius the take-off reads (``checks/mep/fitting_pattern._takeoff_in``): a round
turn's bought ``DuctElbowRow.radius_m()``, else the pattern's ``bend_radius_in`` (a
rectangular turn's r/W x its in-plane side, ``rect_elbows``). The arc is set back
t = R tan(theta/2) each side of the vertex and drawn as a tangent polygon of chords no wider
than ``MAX_CHORD_DEG``: its first and last chords lie on the legs, so its end rings are
square to the stretches it butts, and every inner corner mitres in ``resolve/sweep``.
A record with a gap (no part) or no radius has no arc: the corner keeps its butt joint.

Stdlib only (Pyodide).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN

Vec3 = tuple[float, float, float]

#: The widest chord a drawn arc takes, degrees.
MAX_CHORD_DEG = 15.0
#: Past this a turn is a reversal, not one elbow.
_MAX_TURN_DEG = 179.0


@dataclass(frozen=True)
class ElbowArc:
    """One drawn elbow: tangent points ``start``/``end`` on the legs either side of path
    vertex ``index``, and the tangent polygon ``path`` from ``start`` to ``end``.
    ``radius_m`` is the drawn R: the record's, shrunk where the legs are too short for it."""

    index: int
    vertex: Vec3
    angle_deg: float
    radius_m: float
    setback_m: float
    start: Vec3
    end: Vec3
    path: tuple[Vec3, ...]


def _sub(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Sequence[float], d: Sequence[float], k: float) -> Vec3:
    return (a[0] + d[0] * k, a[1] + d[1] * k, a[2] + d[2] * k)


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(a: Sequence[float]) -> Vec3 | None:
    n = math.sqrt(_dot(a, a))
    return None if n < 1e-12 else (a[0] / n, a[1] / n, a[2] / n)


def turn_angle_rad(prev: Vec3, vertex: Vec3, nxt: Vec3) -> float | None:
    """The deviation from straight at ``vertex``, or None at a degenerate leg."""
    d1, d2 = _unit(_sub(vertex, prev)), _unit(_sub(nxt, vertex))
    if d1 is None or d2 is None:
        return None
    return math.acos(max(-1.0, min(1.0, _dot(d1, d2))))


def elbow_radius_m(record: Any, standard: Any) -> float | None:
    """The record's centreline R in metres, or None (a gap, a branch fitting, no radius)."""
    from typehaus.resolve.duct_standard import elbow_for_turn
    from typehaus.resolve.mep_fittings import FAMILY_DUCT

    if (record.family != FAMILY_DUCT or record.index is None or record.spec is None
            or record.gap is not None):
        return None
    radius = None
    if record.plane_in is None and standard is not None:
        hit = elbow_for_turn(standard, record.nominal_in * M_PER_IN, record.angle_deg,
                             record.adjustable)
        radius = hit[0].radius_m() if hit is not None else None
    if not radius:
        bend_in = getattr(record.spec, "bend_radius_in", None)
        radius = bend_in * M_PER_IN if bend_in else None
    return radius if radius and radius > 0.0 else None


def tangent_polygon(prev: Vec3, vertex: Vec3, nxt: Vec3, radius_m: float,
                    max_chord_deg: float = MAX_CHORD_DEG) -> tuple[Vec3, ...] | None:
    """``start``, the chord corners, ``end``: the arc of ``radius_m`` tangent to both legs.

    The corners sit on the circle of R / cos(step/2), so the first and last chords run along
    the legs. None for a straight, reversed or degenerate corner.
    """
    d1, d2 = _unit(_sub(vertex, prev)), _unit(_sub(nxt, vertex))
    if d1 is None or d2 is None or radius_m <= 0.0:
        return None
    theta = math.acos(max(-1.0, min(1.0, _dot(d1, d2))))
    if theta < 1e-6 or math.degrees(theta) > _MAX_TURN_DEG:
        return None
    t = radius_m * math.tan(theta / 2.0)
    start, end = _add(vertex, d1, -t), _add(vertex, d2, t)
    n = _unit(_add(d2, d1, -_dot(d1, d2)))  # toward the centre, perpendicular to d1
    if n is None:
        return None
    centre = _add(start, n, radius_m)
    k = max(1, math.ceil(math.degrees(theta) / max_chord_deg - 1e-9))
    step = theta / k
    reach = radius_m / math.cos(step / 2.0)
    corners = []
    for j in range(1, k + 1):
        phi = (j - 0.5) * step
        radial = _add(_add((0.0, 0.0, 0.0), n, -math.cos(phi)), d1, math.sin(phi))
        corners.append(_add(centre, radial, reach))
    return (start, *corners, end)


def elbow_arcs(path: Sequence[Vec3], radii: dict[int, float]) -> list[ElbowArc]:
    """The arcs at path vertices ``radii`` names (vertex index -> R), in path order.

    Each setback lies on its adjacent leg; where two setbacks (or one at an end leg) want more
    than the leg has, both shrink in proportion, so arcs meet but never cross.
    """
    pts = list(path)
    want: dict[int, tuple[float, float]] = {}  # index -> (theta, setback)
    for i, radius in radii.items():
        if not 0 < i < len(pts) - 1:
            continue
        theta = turn_angle_rad(pts[i - 1], pts[i], pts[i + 1])
        if theta is None or theta < 1e-6 or math.degrees(theta) > _MAX_TURN_DEG:
            continue
        want[i] = (theta, radius * math.tan(theta / 2.0))
    scale = dict.fromkeys(want, 1.0)
    for j in range(len(pts) - 1):
        ends = [i for i in (j, j + 1) if i in want]
        demand = sum(want[i][1] for i in ends)
        leg = math.dist(pts[j], pts[j + 1])
        if demand > leg > 0.0:
            for i in ends:
                scale[i] = min(scale[i], leg / demand)
    out: list[ElbowArc] = []
    for i in sorted(want):
        theta, setback = want[i]
        setback *= scale[i]
        radius = setback / math.tan(theta / 2.0)
        poly = tangent_polygon(pts[i - 1], pts[i], pts[i + 1], radius)
        if poly is None or setback < 1e-4:
            continue
        out.append(ElbowArc(index=i, vertex=tuple(pts[i]), angle_deg=math.degrees(theta),
                            radius_m=radius, setback_m=setback, start=poly[0],
                            end=poly[-1], path=poly))
    return out
