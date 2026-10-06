"""Read the actual nailing face of rectangular or bevel-cut roof blocking."""

import math

from typehaus.resolve.framing.profiles import cross_section


def top_at(member, point):
    """Top elevation at a plan point; a bevel's bounding box is insufficient."""
    if member.elevation_profile is not None:
        return None
    if member.section_ring is None:
        return member.z1_m
    dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    offset = (-(point[0] - member.p0[0]) * dy
              + (point[1] - member.p0[1]) * dx) / length
    ring = member.section_ring
    heights = []
    for (a, za), (b, zb) in zip(ring, (*ring[1:], ring[0]), strict=True):
        if min(a, b) - 1e-9 <= offset <= max(a, b) + 1e-9:
            if abs(a - b) < 1e-9:
                heights.extend((za, zb))
            else:
                heights.append(za + (zb - za) * (offset - a) / (b - a))
    return member.z0_m + max(heights) if heights else None


def nailing_margins(member, point):
    """Distances to the two end faces and the side edges of a longitudinal block."""
    dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return -1.0, -1.0
    px, py = point[0] - member.p0[0], point[1] - member.p0[1]
    station = (px * dx + py * dy) / length
    offset = abs((-px * dy + py * dx) / length)
    width = member.plan_width_m or cross_section(member.profile).width_m
    return min(station, length - station), width / 2 - offset
