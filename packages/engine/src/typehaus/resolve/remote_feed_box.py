"""Where a self-mounting ceiling fitting's junction box goes (decision #140).

A type with ``remote_box`` (a knuckle flood on its own plate) takes no box over its point. Its
whip lands in a surface box screwed to the underside of the nearest framing member of the deck
over it, at the member's point nearest the fitting, wherever the box clears the fitting's own
footprint and stays inside the deck's outline (an edge member's box would hang into its fascia
or rim cladding). No framed deck over the point, or no member clear of the body within a whip's
reach, is no box.

``member_under`` serves a fixture that mounts to a box under a bare deck: the box hangs from
the member whose plan footprint covers the fixture's point.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Point, Polygon

from typehaus.resolve.framing.footprint import member_footprint

#: Air between the fitting's body and the box, so the box is beside it, not under its plate.
CLEARANCE_M = 0.0127
#: NEC 350.30(A) Ex. 3: an unsupported liquidtight whip to a luminaire is at most 6 ft.
MAX_REACH_M = 1.8288


Found = tuple[tuple[float, float], float, str]


def _underside_at(member: Any, axis: LineString, at: Point) -> float:
    """The member's underside z at ``at``: a sloped member interpolates to ``z0_end_m``."""
    end = getattr(member, "z0_end_m", None)
    if end is None:
        return member.z0_m
    return member.z0_m + axis.project(at, normalized=True) * (end - member.z0_m)


def remote_box_point(floor: Any, xy: tuple[float, float], fitting_footprint: tuple,
                     box_width_m: float, base_z: float) -> Found | None:
    """(plan point, member underside z, member key) for the box, or None."""
    point = Point(xy)
    body = Polygon(fitting_footprint) if len(fitting_footprint) >= 3 else point
    keep_out = body.buffer(CLEARANCE_M)
    outline = getattr(floor, "deck_outline", ())
    deck = Polygon(outline).buffer(1e-4) if len(outline) >= 3 else None
    best = None
    for member in floor.members:
        if member.p0 == member.p1:
            continue
        axis = LineString([member.p0, member.p1])
        at = axis.interpolate(axis.project(point))
        distance = at.distance(point)
        disc = at.buffer(box_width_m / 2)
        if distance > MAX_REACH_M or disc.intersects(keep_out) or (
                deck is not None and not deck.covers(disc)):
            continue
        z = _underside_at(member, axis, at)
        if z < base_z:
            continue
        if best is None or distance < best[0]:
            best = (distance, (at.x, at.y), z, member.child_key)
    return None if best is None else best[1:]


def member_under(floor: Any, xy: tuple[float, float], base_z: float) -> tuple[float, str] | None:
    """(underside z, member key) of the lowest member of ``floor`` over ``xy``, or None."""
    point = Point(xy)
    best = None
    for member in floor.members:
        if member.p0 == member.p1:
            continue
        ring, _, _ = member_footprint(member)
        if len(ring) < 3 or not Polygon(ring).covers(point):
            continue
        z = _underside_at(member, LineString([member.p0, member.p1]), point)
        if z >= base_z and (best is None or z < best[0]):
            best = (z, member.child_key)
    return best
