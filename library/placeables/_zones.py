"""Recommended clearance zones, authored once per access pattern.

Every zone here is ``ClearancePolicy.RECOMMENDED``: the resolver reports an encroachment as a
warning, not an error, so a tight room still builds and checks. These are the planning
allowances a designer wants flagged — the walk path in front of a sofa, the arc a refrigerator
door needs, the space a drawer occupies when it is open — not code minimums.

Zones are authored in the same local frame as the symbol: origin at the footprint centre,
``-y`` is the front of the object (the side that faces the room).
"""

from __future__ import annotations

from typehaus.model import ClearancePolicy, ClearanceZone, Footprint2D, Length, m, pt

PLANNING_SOURCE = "planning standard"


def _zone(points, purpose: str, source: str = PLANNING_SOURCE) -> ClearanceZone:
    return ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(m(x), m(y)) for x, y in points)),
        purpose=purpose, policy=ClearancePolicy.RECOMMENDED, source=source,
    )


def front_zone(width: Length, depth: Length, reach: Length, purpose: str,
               *, inset: float = 1.0) -> ClearanceZone:
    """The band a user occupies in front of the object — a walk path, a door swing, a pull-out."""
    half_width = width.meters / 2 * inset
    front = -depth.meters / 2
    return _zone(((-half_width, front - reach.meters), (half_width, front - reach.meters),
                  (half_width, front), (-half_width, front)), purpose)


def side_zone(width: Length, depth: Length, reach: Length, purpose: str,
              sign: int = 1) -> ClearanceZone:
    """The band alongside the object — bed side access, appliance service space."""
    edge = sign * width.meters / 2
    far = edge + sign * reach.meters
    half_depth = depth.meters / 2
    return _zone(((min(edge, far), -half_depth), (max(edge, far), -half_depth),
                  (max(edge, far), half_depth), (min(edge, far), half_depth)), purpose)


def surround_zone(width: Length, depth: Length, reach: Length, purpose: str) -> ClearanceZone:
    """A margin on all four sides — the chair-use zone around a dining table."""
    half_width = width.meters / 2 + reach.meters
    half_depth = depth.meters / 2 + reach.meters
    return _zone(((-half_width, -half_depth), (half_width, -half_depth),
                  (half_width, half_depth), (-half_width, half_depth)), purpose)
