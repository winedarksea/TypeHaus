"""A port kit's flex lead that turns: one arc at centreline radius >= one duct diameter.

ADC *Flexible Duct Performance & Installation Standards* (4th ed.) s.4.2: "Radius at center
line shall not be less than one duct diameter"; s.4.8: let the duct "extend straight for a few
inches before making the bend" off a metal collar. So a flex lead is ``start`` straight, an
arc of ``R = k D`` and ``tail`` straight. Seen as a polyline it is one vertex (the corner)
with ``R tan(theta/2)`` of flex on each side of it; that vertex is a flex bend, not a stock
elbow, and ``fitting_records`` skips it. The flex is cut to ``max(kit length, start + arc)``:
an 8" lead's 90 degree arc alone is 12.57" against Broan's 12" section.

``houses/catlin/notes/flex_lead_bend_basis.md`` is the oracle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

#: A turn smaller than this is a grade change, not a bend (``mep_fittings.MIN_FITTING_TURN_DEG``).
MIN_BEND_DEG = 10.0


@dataclass(frozen=True)
class FlexBend:
    """One bend in a kit's flex: lengths in metres along the flex's centreline."""

    angle_deg: float
    radius_m: float
    start_m: float  # straight flex before the arc
    flex_m: float  # the flex as cut: max(kit length, start + arc)

    @property
    def arc_m(self) -> float:
        return self.radius_m * math.radians(self.angle_deg)

    @property
    def tangent_m(self) -> float:
        """``R tan(theta/2)``: flex either side of the corner vertex, along each leg."""
        return self.radius_m * math.tan(math.radians(self.angle_deg) / 2.0)

    @property
    def tail_m(self) -> float:
        return self.flex_m - self.start_m - self.arc_m

    @property
    def out_m(self) -> float:
        """Corner to where the rigid duct starts, along the leg after the turn."""
        return self.tangent_m + self.tail_m

    def corner_m(self, transition_m: float = 0.0) -> float:
        """Port face to the corner vertex, along the port's axis."""
        return transition_m + self.start_m + self.tangent_m


def flex_bend(kit: Any, diameter_m: float, angle_deg: float = 90.0, *,
              corner_m: float | None = None, transition_m: float = 0.0) -> FlexBend | None:
    """The bend ``kit``'s flex makes at ``diameter_m``, or None where it cannot.

    ``corner_m`` None lays the compact lead (``bend_start`` straight, then the arc: the
    router's); given, it is where an authored run's first vertex stands from the port face,
    and the straight is whatever that leaves. None too without a flex, for a vibration
    connector, below :data:`MIN_BEND_DEG`, or when the corner stands too close to seat the
    arc."""
    if (kit is None or kit.connector or not kit.flex_product_ref or not diameter_m
            or angle_deg < MIN_BEND_DEG):
        return None
    radius = max(1.0, kit.bend_radius_diameters) * diameter_m
    tangent = radius * math.tan(math.radians(angle_deg) / 2.0)
    start = kit.bend_start.meters if corner_m is None else corner_m - transition_m - tangent
    if start < kit.bend_start.meters - 1e-6:
        return None
    nominal = kit.flex_length.meters if kit.flex_length is not None else 0.0
    arc = radius * math.radians(angle_deg)
    return FlexBend(angle_deg, radius, start, max(nominal, start + arc))


def run_bend(duct: Any, index: int, kit: Any, standard: Any, *,
             transition_m: float = 0.0) -> tuple[FlexBend, int] | None:
    """``(bend, vertex)`` where ``duct``'s end ``index`` (0 or last raw point) turns inside the
    kit's lead, or None: the straight lead stays where it already fits.

    The first vertex off the port is a flex bend when the arc seats on the leg before it,
    the leg after holds the flex's tail, and the straight lead (flex then stock elbow's
    take-off) would not fit before it."""
    from typehaus.resolve.duct_standard import elbow_for_turn
    from typehaus.resolve.sweep import clean_path

    size = getattr(duct, "diameter_m", None)
    z = getattr(duct, "z_m", None)
    if not size or z is None or len(z) != len(duct.path):
        return None
    path = clean_path([(x, y, zz) for (x, y), zz in zip(duct.path, z, strict=True)])
    if len(path) < 3:
        return None
    if index != 0:
        path = path[::-1]
    a, b, c = path[0], path[1], path[2]
    leg0 = [q - p for p, q in zip(a, b, strict=True)]
    leg1 = [q - p for p, q in zip(b, c, strict=True)]
    d0, d1 = math.hypot(*leg0), math.hypot(*leg1)
    cos = sum(u * v for u, v in zip(leg0, leg1, strict=True)) / (d0 * d1) if d0 * d1 else 1.0
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
    bend = flex_bend(kit, size, angle, corner_m=d0, transition_m=transition_m)
    if bend is None or bend.out_m > d1 + 1e-6:
        return None
    # A corner the run names in ``adjustable_elbows`` takes the adjustable row's take-off.
    adjustable = any(math.dist(b, q) < 1e-3 for q in getattr(duct, "adjustable_points", ()) or ())
    hit = elbow_for_turn(standard, size, angle, adjustable)
    radius = (hit[0].radius_m() if hit else None) or 1.5 * size
    nominal = kit.flex_length.meters if kit.flex_length is not None else 0.0
    stock = transition_m + nominal + radius * math.tan(math.radians(angle) / 2.0)
    if d0 >= stock - 1e-6:
        return None
    return bend, (1 if index == 0 else len(path) - 2)


def flexed_vertices(model: Any) -> dict[tuple[str, int], Any]:
    """``(run tag, cleaned-path vertex) -> flex part`` for every flex bend the model derived."""
    return {(p.run_tag, p.bend_vertex): p for p in model.duct_parts
            if p.bend_vertex is not None}
