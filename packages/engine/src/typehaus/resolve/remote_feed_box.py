"""Where a self-mounting ceiling fitting's junction box goes (decision #140).

A type with ``remote_box`` (a knuckle flood on its own plate) takes no box over its point. Its
whip lands in a surface box screwed to the underside of the nearest framing member of the deck
over it, at the member's point nearest the fitting, wherever the box clears the fitting's own
footprint. No framed deck over the point, or no member clear of the body, is no box.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Point, Polygon

#: Air between the fitting's body and the box, so the box is beside it, not under its plate.
CLEARANCE_M = 0.0127


Found = tuple[tuple[float, float], float, str]


def remote_box_point(floor: Any, xy: tuple[float, float], fitting_footprint: tuple,
                     box_width_m: float, base_z: float) -> Found | None:
    """(plan point, member underside z, member key) for the box, or None."""
    point = Point(xy)
    body = Polygon(fitting_footprint) if len(fitting_footprint) >= 3 else point
    keep_out = body.buffer(CLEARANCE_M)
    best = None
    for member in floor.members:
        if member.p0 == member.p1 or member.z0_m < base_z:
            continue
        axis = LineString([member.p0, member.p1])
        at = axis.interpolate(axis.project(point))
        if at.buffer(box_width_m / 2).intersects(keep_out):
            continue
        distance = at.distance(point)
        if best is None or distance < best[0]:
            best = (distance, (at.x, at.y), member.z0_m, member.child_key)
    return None if best is None else best[1:]
