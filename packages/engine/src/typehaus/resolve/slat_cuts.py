"""A diagonal board clipped to the four actual bearing faces of its bay."""

from __future__ import annotations

import math


def clipped_slat_profile(slat, layout, face_m: float) -> tuple[tuple[float, float], ...]:
    """Bay-frame (u, z) ring; clips corners as well as the centreline's named ends.

    Clipping the whole strip matters for j=0: its centreline misses the sill and top,
    but both long points reach them. Pulling back a rectangular box loses those cuts.
    """
    slope = getattr(slat, "slope", 1.0)
    half_vertical = face_m * math.hypot(1.0, slope) / 2.0
    ring = [(0.0, 0.0), (layout.width, 0.0),
            (layout.width, layout.height), (0.0, layout.height)]
    for sign in (1.0, -1.0):
        clipped = []
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            da = half_vertical - sign * (a[1] - slope * a[0] + slat.c)
            db = half_vertical - sign * (b[1] - slope * b[0] + slat.c)
            if da >= 0.0:
                clipped.append(a)
            if (da < 0.0) != (db < 0.0):
                t = da / (da - db)
                clipped.append((a[0] + t * (b[0] - a[0]),
                                a[1] + t * (b[1] - a[1])))
        ring = clipped
    return tuple(ring)


def slat_blank_length(profile: tuple[tuple[float, float], ...], slope: float = 1.0) -> float:
    """Distance between the extreme long points along the board axis, before sawing."""
    stations = [(u + slope * z) / math.hypot(1.0, slope) for u, z in profile]
    return max(stations) - min(stations)
