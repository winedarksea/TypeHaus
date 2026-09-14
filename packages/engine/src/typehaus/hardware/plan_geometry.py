"""Small plan-frame geometry the hardware derivations share (meters, project frame)."""

from __future__ import annotations

import math


def distance_point_to_segment(point: tuple, p0: tuple, p1: tuple) -> float:
    """Shortest plan distance from ``point`` to the segment ``p0``→``p1``.

    Clamped to the segment, so a member ending beyond a beam's run is correctly *not*
    reported as touching it.
    """
    span_x, span_y = p1[0] - p0[0], p1[1] - p0[1]
    span_sq = span_x * span_x + span_y * span_y
    if span_sq <= 0.0:
        return math.hypot(point[0] - p0[0], point[1] - p0[1])
    t = ((point[0] - p0[0]) * span_x + (point[1] - p0[1]) * span_y) / span_sq
    t = max(0.0, min(1.0, t))
    return math.hypot(point[0] - (p0[0] + t * span_x), point[1] - (p0[1] + t * span_y))


def centerline_endpoints(ring: list) -> tuple:
    """The two ends of a thin plan strip's centreline (a sill plate, a beam footprint).

    Derived from the ring's longest edge rather than an axis-aligned bounding box, so a
    wall running on a diagonal reports its real ends.
    """
    if len(ring) < 2:
        raise ValueError("a centreline needs at least two ring points")
    edges = [(ring[index], ring[(index + 1) % len(ring)]) for index in range(len(ring))]
    start, end = max(edges, key=lambda edge: math.dist(edge[0], edge[1]))
    run = math.dist(start, end)
    if run <= 0.0:
        raise ValueError("degenerate ring has no centreline")
    direction = ((end[0] - start[0]) / run, (end[1] - start[1]) / run)
    center = (sum(point[0] for point in ring) / len(ring),
              sum(point[1] for point in ring) / len(ring))
    offsets = [(point[0] - center[0]) * direction[0] + (point[1] - center[1]) * direction[1]
               for point in ring]
    return (
        (center[0] + min(offsets) * direction[0], center[1] + min(offsets) * direction[1]),
        (center[0] + max(offsets) * direction[0], center[1] + max(offsets) * direction[1]),
    )


def merge_coincident_points(points: list, tolerance_m: float) -> list:
    """Collapse points within ``tolerance_m`` of each other to one representative point.

    Two sill runs that butt at a corner share one end; counting hardware at both would
    double the holdowns at every corner of the building.
    """
    merged: list = []
    for point in points:
        if not any(math.dist(point, kept) <= tolerance_m for kept in merged):
            merged.append(point)
    return merged


def point_in_ring(point: tuple, ring) -> bool:
    """Is ``point`` inside the closed plan ``ring``? Even-odd ray cast, boundary unspecified.

    A point exactly on an edge may answer either way, and every caller here is asking about a
    wall's MIDPOINT against a roof footprint — metres clear of the boundary either way — so
    the ambiguity is not reachable rather than merely tolerated.
    """
    points = list(ring)
    if len(points) < 3:
        return False
    x, y = point[0], point[1]
    inside = False
    previous = points[-1]
    for current in points:
        (x0, y0), (x1, y1) = previous, current
        if (y0 > y) != (y1 > y):
            t = (y - y0) / (y1 - y0)
            if x < x0 + t * (x1 - x0):
                inside = not inside
        previous = current
    return inside
