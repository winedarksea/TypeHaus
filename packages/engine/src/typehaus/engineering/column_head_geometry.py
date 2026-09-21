"""Plan geometry at a column head, for ``column_head_joint``: where lateral force enters, where
the seat bears, and how much concrete surrounds the bearing plate.

Inches throughout, relative to the column's own axis. A beam is its node-to-node centreline
at its section width; a part is its authored ``Connector.position``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

_IN_PER_M = 1.0 / 0.0254


@dataclass(frozen=True)
class BeamFrame:
    """One beam bearing on the head, in its own axes: ``u`` along, ``v`` across."""

    tag: str
    origin: tuple[float, float]   # the start node, relative to the column axis
    u: tuple[float, float]        # unit vector along the beam
    length_in: float
    width_in: float

    @property
    def v(self) -> tuple[float, float]:
        return (-self.u[1], self.u[0])

    def local(self, point: tuple[float, float]) -> tuple[float, float]:
        dx, dy = point[0] - self.origin[0], point[1] - self.origin[1]
        return (dx * self.u[0] + dy * self.u[1], dx * self.v[0] + dy * self.v[1])

    def plan(self, s: float, t: float) -> tuple[float, float]:
        return (self.origin[0] + s * self.u[0] + t * self.v[0],
                self.origin[1] + s * self.u[1] + t * self.v[1])

    def faces_at_axis(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """The beam's two side faces at the station nearest the column axis."""
        s = min(max(self.local((0.0, 0.0))[0], 0.0), self.length_in)
        half = self.width_in / 2.0
        return (self.plan(s, -half), self.plan(s, half))


def relative_in(point_m: tuple[float, float], axis_m: tuple[float, float]) -> tuple[float, float]:
    return ((point_m[0] - axis_m[0]) * _IN_PER_M, (point_m[1] - axis_m[1]) * _IN_PER_M)


def beam_frame(plan: Any, beam: Any, axis_m: tuple[float, float]) -> BeamFrame | None:
    from typehaus.resolve.framing.profiles import cross_section

    start, end = plan.by_tag(beam.start_node or ""), plan.by_tag(beam.end_node or "")
    if start is None or end is None:
        return None
    a = relative_in(start.position.xy_m, axis_m)
    b = relative_in(end.position.xy_m, axis_m)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    if length <= 0.0:
        return None
    width = float(cross_section(beam.size).width_m) * _IN_PER_M
    return BeamFrame(tag=beam.tag, origin=a, u=((b[0] - a[0]) / length, (b[1] - a[1]) / length),
                     length_in=length, width_in=width)


def lever_in(points: list[tuple[float, float]], direction: tuple[float, float] | None) -> float:
    """The largest ``|r x d|`` over the entry points — or ``|r|`` for a force of any direction.

    A force entering at ``r`` makes a torque about the column axis of ``|r x F|``, and
    ``|r x F| <= |r||F|``: the bound holds however the parts share it.
    """
    if not points:
        return 0.0
    if direction is None:
        return max(math.hypot(x, y) for x, y in points)
    return max(abs(x * direction[1] - y * direction[0]) for x, y in points)


def seat_centroid(frame: BeamFrame, pack_centre: tuple[float, float], length_in: float,
                  width_in: float) -> tuple[float, float] | None:
    """Centroid of (bearing pack ∩ beam footprint), plan inches off the axis, or ``None``."""
    cu, cv = frame.local(pack_centre)
    u0, u1 = max(cu - length_in / 2.0, 0.0), min(cu + length_in / 2.0, frame.length_in)
    half = frame.width_in / 2.0
    v0, v1 = max(cv - width_in / 2.0, -half), min(cv + width_in / 2.0, half)
    if u1 <= u0 or v1 <= v0:
        return None
    return frame.plan((u0 + u1) / 2.0, (v0 + v1) / 2.0)


def confinement_ratio(frame: BeamFrame, pack_centre: tuple[float, float], length_in: float,
                      width_in: float, radius_in: float) -> float:
    """``sqrt(A2/A1)`` for ACI 318-19 §22.8.3.2 on a round top, uncapped.

    ``A2`` is the largest area similar to and concentric with the plate that fits inside the
    circle: scale ``k`` on the plate's half-dimensions until a corner touches it, so
    ``(|cu| + k a)^2 + (|cv| + k b)^2 = R^2`` and ``sqrt(A2/A1) = k``. Below 1 the plate
    itself overhangs the concrete.
    """
    # The pack's offset from the column axis, in the beam's directions.
    cu = abs(pack_centre[0] * frame.u[0] + pack_centre[1] * frame.u[1])
    cv = abs(pack_centre[0] * frame.v[0] + pack_centre[1] * frame.v[1])
    a, b = length_in / 2.0, width_in / 2.0
    qa = a * a + b * b
    qb = 2.0 * (cu * a + cv * b)
    qc = cu * cu + cv * cv - radius_in * radius_in
    disc = qb * qb - 4.0 * qa * qc
    if disc < 0.0 or qa <= 0.0:
        return 0.0
    return max((-qb + math.sqrt(disc)) / (2.0 * qa), 0.0)
