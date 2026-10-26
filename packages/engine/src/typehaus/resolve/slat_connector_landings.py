"""KBS1Z heels and leaf directions on actual slat edges, in bay elevation coordinates."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SlatConnectorEnd:
    end: str
    landing: str
    u: float
    z: float
    support: tuple[float, float]
    support_face: tuple[float, float]
    brace_axis: tuple[float, float]
    brace_face: tuple[float, float]

    @property
    def included_angle_degrees(self) -> float:
        cosine = sum(a * b for a, b in zip(self.support, self.brace_axis, strict=True))
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def slat_connector_ends(slat, face_m: float) -> tuple[SlatConnectorEnd, ...]:
    """Closed bends use the opposite brace edge and reverse the support leg.

    The heel must move with that edge: keeping an open-bend heel while rotating its
    leaves falsely puts the connector outside the board at a clipped frame corner.
    """
    cosine = 1.0 / math.hypot(1.0, slat.slope)
    sine = slat.slope * cosine
    half_vertical, half_horizontal = face_m / (2 * cosine), face_m / (2 * sine)
    closed = -1.0 if slat.closed_connectors else 1.0
    ends = []
    for end, landing, u in (("low", slat.low, slat.u0), ("high", slat.high, slat.u1)):
        z = slat.elevation(u)
        if landing == "chord":
            z -= closed * half_vertical
            support, support_face = (0.0, -closed), (-1.0, 0.0)
            brace_face = (-closed * sine, closed * cosine)
        elif landing == "centre":
            z += closed * half_vertical
            support, support_face = (0.0, closed), (1.0, 0.0)
            brace_face = (closed * sine, -closed * cosine)
        elif landing == "sill":
            u -= closed * half_horizontal
            support, support_face = (-closed, 0.0), (0.0, -1.0)
            brace_face = (closed * sine, -closed * cosine)
        else:
            u += closed * half_horizontal
            support, support_face = (closed, 0.0), (0.0, 1.0)
            brace_face = (-closed * sine, closed * cosine)
        direction = 1.0 if end == "low" else -1.0
        ends.append(SlatConnectorEnd(end, landing, u, z, support, support_face,
                                     (direction * cosine, direction * sine), brace_face))
    return tuple(ends)
