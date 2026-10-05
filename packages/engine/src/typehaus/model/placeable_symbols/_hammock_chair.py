"""A spreader-bar hammock chair hung from one ring: the bar, the fabric pod, its cords.

``height`` runs from the seat bottom (z = 0) to the ring (z = height); the suspension above
the ring is drawn by the resolver's cable (``resolve/suspension.py``), not here. Front is -y.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, ellipse, line
from typehaus.model.placeable_symbols._plant_primitives import _mesh_part, slender_segment

SPREADER_DROP_SHARE = 0.32   # ring to bar, as a share of the overall height
SPREADER_BACK_SHARE = 0.20   # bar behind the footprint centre, share of depth
SPREADER_RADIUS_M = 0.016
CORD_RADIUS_M = 0.004
LIP_HEIGHT_SHARE = 0.36      # front lip above the seat bottom
SEAT_SAG_SHARE = 0.10        # the pod's sag across its width
ACROSS, ALONG = 9, 9         # pod mesh resolution


def hammock_chair(width: float, depth: float, height: float) -> Geometry:
    """Plan: the spreader, the pod and its swing envelope. Model: bar, pod mesh, cords."""
    bar_z = height * (1 - SPREADER_DROP_SHARE)
    bar_y = depth * SPREADER_BACK_SHARE
    spreader = min(SPREADER_RADIUS_M, width * 0.02)
    cord = min(CORD_RADIUS_M, width * 0.005)
    half = width / 2 - spreader  # every part stays inside the declared box
    ring = (0.0, 0.0, height - cord)
    strokes = [
        ellipse(0, -depth * 0.05, half * 0.85, depth * 0.45, fill="cushion"),
        line((-half, bar_y), (half, bar_y), weight=0.35),
        # The swing envelope: the footprint the seat sweeps fore and aft.
        ellipse(0, 0, width / 2, depth / 2, weight=DETAIL_WEIGHT),
    ]
    parts = [slender_segment((-half, bar_y, bar_z), (half, bar_y, bar_z), spreader, "wood")]
    for sign in (-1, 1):
        end = (sign * half, bar_y, bar_z)
        parts.append(slender_segment(end, ring, cord, "mattress"))
        parts.append(slender_segment(end, (sign * half * 0.8, -depth / 2 + cord,
                                           height * LIP_HEIGHT_SHARE), cord, "mattress"))
    parts.append(_pod(width, depth, height, bar_y, bar_z))
    return tuple(strokes), tuple(parts)


def _pod(width, depth, height, bar_y, bar_z):
    """The fabric: from the bar, down to the seat bottom, forward and up to the front lip."""
    def profile(v: float) -> tuple[float, float, float]:
        if v <= 0.5:   # bar -> seat bottom
            t = v / 0.5
            return bar_y * (1 - t), bar_z * (1 - t) ** 1.6, 1.0 - 0.3 * t
        t = (v - 0.5) / 0.5  # seat bottom -> front lip
        return -depth / 2 * t, height * LIP_HEIGHT_SHARE * t ** 1.8, 0.7 + 0.1 * t

    positions = []
    for j in range(ALONG + 1):
        y, z, scale = profile(j / ALONG)
        for i in range(ACROSS + 1):
            u = -1 + 2 * i / ACROSS
            sag = SEAT_SAG_SHARE * height * (1 - u * u) * min(1.0, z / (height * 0.05) + 0.2)
            positions.append((u * width / 2 * scale, y, max(0.0, z - sag)))
    triangles = []
    for j in range(ALONG):
        for i in range(ACROSS):
            a = j * (ACROSS + 1) + i
            b, c, d = a + 1, a + ACROSS + 1, a + ACROSS + 2
            triangles += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]  # both faces
    return _mesh_part(positions, triangles, "cushion")
