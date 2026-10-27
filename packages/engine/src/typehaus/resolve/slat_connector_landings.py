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


def slat_connector_ends(slat, layout, face_m: float) -> tuple[SlatConnectorEnd, ...]:
    """Open-knee heels: the support leg runs along the bearing face away from the brace.

    The heel sits on the long edge that lands on that face. That is the outside edge, unless
    the end lies in a frame corner (``corner_to_corner``): there the outside edge lands on
    the other member, so the heel and brace leaf move to the inside edge, the support leg
    still running back toward the corner.
    """
    cosine = 1.0 / math.hypot(1.0, slat.slope)
    sine = slat.slope * cosine
    half_vertical, half_horizontal = face_m / (2 * cosine), face_m / (2 * sine)
    ends = []
    for end, landing, u in (("low", slat.low, slat.u0), ("high", slat.high, slat.u1)):
        z = slat.elevation(u)
        if landing == "chord":
            edge = 1.0 if z - half_vertical < -1e-9 else -1.0
            z += edge * half_vertical
            support, support_face = (0.0, -1.0), (-1.0, 0.0)
            brace_face = (edge * sine, -edge * cosine)
        elif landing == "centre":
            edge = -1.0 if z + half_vertical > layout.height + 1e-9 else 1.0
            z += edge * half_vertical
            support, support_face = (0.0, 1.0), (1.0, 0.0)
            brace_face = (edge * sine, -edge * cosine)
        elif landing == "sill":
            edge = 1.0 if u - half_horizontal < -1e-9 else -1.0
            u += edge * half_horizontal
            support, support_face = (-1.0, 0.0), (0.0, -1.0)
            brace_face = (-edge * sine, edge * cosine)
        else:
            edge = -1.0 if u + half_horizontal > layout.width + 1e-9 else 1.0
            u += edge * half_horizontal
            support, support_face = (1.0, 0.0), (0.0, 1.0)
            brace_face = (-edge * sine, edge * cosine)
        direction = 1.0 if end == "low" else -1.0
        ends.append(SlatConnectorEnd(end, landing, u, z, support, support_face,
                                     (direction * cosine, direction * sine), brace_face))
    return tuple(ends)
