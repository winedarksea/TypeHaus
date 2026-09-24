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


def _zone(points, purpose: str, source: str = PLANNING_SOURCE,
          occupant_types: tuple[str, ...] = ()) -> ClearanceZone:
    return ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(m(x), m(y)) for x, y in points)),
        purpose=purpose, policy=ClearancePolicy.RECOMMENDED, source=source,
        occupant_types=occupant_types,
    )


def front_zone(width: Length, depth: Length, reach: Length, purpose: str,
               *, inset: float = 1.0, occupant_types: tuple[str, ...] = ()) -> ClearanceZone:
    """The band a user occupies in front of the object — a walk path, a door swing, a pull-out.

    ``occupant_types`` names the product types the band exists to hold (a desk's pull-out zone
    holds its chair), so they group with the owner instead of reporting as encroachments.
    """
    half_width = width.meters / 2 * inset
    front = -depth.meters / 2
    return _zone(((-half_width, front - reach.meters), (half_width, front - reach.meters),
                  (half_width, front), (-half_width, front)), purpose,
                 occupant_types=occupant_types)


def side_zone(width: Length, depth: Length, reach: Length, purpose: str,
              sign: int = 1, *, occupant_types: tuple[str, ...] = ()) -> ClearanceZone:
    """The band alongside the object — bed side access, appliance service space.

    ``occupant_types`` names what the band exists to hold, the same way ``front_zone`` and
    ``surround_zone`` do: a nightstand in a bed's side access is the arrangement working,
    not an encroachment on it.
    """
    edge = sign * width.meters / 2
    far = edge + sign * reach.meters
    half_depth = depth.meters / 2
    return _zone(((min(edge, far), -half_depth), (max(edge, far), -half_depth),
                  (max(edge, far), half_depth), (min(edge, far), half_depth)), purpose,
                 occupant_types=occupant_types)


def surround_zone(width: Length, depth: Length, reach: Length, purpose: str,
                  *, occupant_types: tuple[str, ...] = ()) -> ClearanceZone:
    """A margin on all four sides — the chair-use zone around a dining table.

    ``occupant_types`` names what the margin is for: chairs tucked at the table are the zone
    working, so they join the table's group rather than reporting against it.
    """
    half_width = width.meters / 2 + reach.meters
    half_depth = depth.meters / 2 + reach.meters
    return _zone(((-half_width, -half_depth), (half_width, -half_depth),
                  (half_width, half_depth), (-half_width, half_depth)), purpose,
                 occupant_types=occupant_types)


def open_corner_zone(width: Length, depth: Length, reach: Length, purpose: str,
                     *, source: str = PLANNING_SOURCE,
                     occupant_types: tuple[str, ...] = ()) -> tuple[ClearanceZone, ClearanceZone]:
    """A rectangular table's chair-use margin as two crossed bands, not one bigger rectangle.

    ``surround_zone`` is right for a ROUND table, whose corners really seat a chair. On a
    rectangular one the four corner squares hold nothing: one band the table's width running
    past both long sides, one band its depth running past both ends. Strictly smaller than
    ``surround_zone``, and smaller only where nothing stands.
    """
    hw, hd, r = width.meters / 2, depth.meters / 2, reach.meters

    def band(x: float, y: float) -> ClearanceZone:
        return _zone(((-x, -y), (x, -y), (x, y), (-x, y)), purpose, source,
                     occupant_types=occupant_types)
    return band(hw, hd + r), band(hw + r, hd)
