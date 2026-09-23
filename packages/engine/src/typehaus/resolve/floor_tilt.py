"""A joist field on tilted bearings: each joist end takes its own bearing's top.

A ``Beam.top_rise_end`` beam is one member out of level. The joists it carries sit on it, so
a joist's z at each end is that bearing's top at the joist's own station — read here off the
bearing, never authored a second time on the floor. Between bearings a joist is straight
(it rakes when its two bearings disagree); past the outermost ones it cantilevers on the
same line. Walls and level beams contribute no rise.

The finished deck is the PLANE through those joist tops (:class:`DeckPlane`). A field whose
bearings do not describe one plane — two beams tilted differently — twists; its joists are
still exact, but the deck sheet cannot be, so that is reported rather than drawn quietly.

Leaf: reads the plan's ``Beam`` + ``Node`` elements and nothing resolved.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from typehaus.model.structure import Beam
from typehaus.quantities import inch

#: Deviation of a bearing from the fitted deck plane that is reported as a twist.
_TWIST_TOL_M = inch(1 / 16).meters

RiseAt = Callable[[float, float], float]


@dataclass(frozen=True)
class DeckPlane:
    """How far a deck stands above its resolved datum at a plan point: a plane.

    ``lift_at_origin_m + gradient . (p - origin)``. ``ResolvedFloor.deck_z0_m``/``deck_z1_m``
    are the deck's bottom and top where this is zero — at the first bearing's own start.
    """

    origin: tuple[float, float]
    lift_at_origin_m: float
    gradient: tuple[float, float]

    def lift(self, x: float, y: float) -> float:
        return (self.lift_at_origin_m + self.gradient[0] * (x - self.origin[0])
                + self.gradient[1] * (y - self.origin[1]))


def bearing_rise(plan, tag: str) -> RiseAt | None:
    """A tilted beam's rise above its START node at the plan point's projection on its axis.

    ``None`` for anything that does not tilt — a wall, a level beam — which is the common
    case and lets a level floor skip the whole derivation.
    """
    beam = plan.by_tag(tag)
    if not isinstance(beam, Beam) or beam.top_rise_end is None:
        return None
    rise = beam.top_rise_end.meters
    if abs(rise) < 1e-12:
        return None
    for storey in plan.storeys:
        nodes = {e.tag: e.position.xy_m for e in plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        if p0 is None or p1 is None:
            continue
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-18:
            return None

        def rise_at(x: float, y: float, p0=p0, dx=dx, dy=dy, length_sq=length_sq) -> float:
            return rise * ((x - p0[0]) * dx + (y - p0[1]) * dy) / length_sq
        return rise_at
    return None


@dataclass(frozen=True)
class JoistLift:
    """A joist field's lift, piecewise-linear along each joist through its bearing lines."""

    along_x: bool
    #: (bearing-line coordinate along the joists, that line's rise function), ascending.
    lines: tuple[tuple[float, RiseAt | None], ...]

    def at(self, axis: float, perp: float) -> float:
        """Lift at ``axis`` along a joist on line ``perp``, extrapolated past the ends."""
        def rise(index: int) -> float:
            coord, fn = self.lines[index]
            if fn is None:
                return 0.0
            return fn(coord, perp) if self.along_x else fn(perp, coord)
        if len(self.lines) == 1:
            return rise(0)
        span = next((i for i in range(len(self.lines) - 1)
                     if axis <= self.lines[i + 1][0]), len(self.lines) - 2)
        a, b = self.lines[span][0], self.lines[span + 1][0]
        ra, rb = rise(span), rise(span + 1)
        return ra + (rb - ra) * (axis - a) / (b - a) if abs(b - a) > 1e-12 else ra

    def plane(self, perp0: float, perp1: float) -> tuple[DeckPlane, float]:
        """The deck plane through the outer bearings, and the worst bearing's miss (m)."""
        lo, hi = self.lines[0][0], self.lines[-1][0]
        base = self.at(lo, perp0)
        d_axis = (self.at(hi, perp0) - base) / (hi - lo) if abs(hi - lo) > 1e-12 else 0.0
        d_perp = ((self.at(lo, perp1) - base) / (perp1 - perp0)
                  if abs(perp1 - perp0) > 1e-12 else 0.0)
        origin = (lo, perp0) if self.along_x else (perp0, lo)
        gradient = (d_axis, d_perp) if self.along_x else (d_perp, d_axis)
        plane = DeckPlane(origin=origin, lift_at_origin_m=base, gradient=gradient)
        miss = 0.0
        for coord, _fn in self.lines:
            for perp in (perp0, perp1):
                xy = (coord, perp) if self.along_x else (perp, coord)
                miss = max(miss, abs(plane.lift(*xy) - self.at(coord, perp)))
        return plane, miss


def joist_lift(plan, bearings: list[tuple[str, float]], boundaries: list[float],
               along_x: bool) -> JoistLift | None:
    """The field's lift from ``(bearing tag, line coordinate)`` pairs, or ``None`` when no
    bearing tilts (every level floor)."""
    rises: dict[float, RiseAt | None] = {}
    any_tilt = False
    for tag, coord in bearings:
        fn = bearing_rise(plan, tag)
        key = next((b for b in boundaries if abs(b - coord) <= 1e-9), None)
        if key is None:
            continue
        if fn is not None:
            any_tilt = True
            rises[key] = fn
        else:
            rises.setdefault(key, None)
    if not any_tilt:
        return None
    return JoistLift(along_x=along_x,
                     lines=tuple((b, rises.get(b)) for b in boundaries))


def twisted(miss_m: float) -> bool:
    return miss_m > _TWIST_TOL_M
