"""Drains fall, and that is what makes DWV a different problem rather than a parameter.

A supply pipe's elevation is a choice the router makes; a drain's is a **derived monotone
potential**. Given a start elevation and a grade, the invert anywhere on the route is

    invert = start − slope × developed plan length

and nothing else — which means the search state already carries what it needs (how far it
has travelled), and z stops being a free dimension. Vertical edges are free drops and never
rises.

The terminal test is therefore the **head budget**, not the distance: a route is feasible
when its invert at the root is still at or above the root's own. And when it is not, the
useful thing to report is not "infeasible" but **the minimum slope at which it would be
feasible** — which is exactly the question the catlin kitchen-drain reroute turned on, and
the number a person can act on.

``houses/catlin/notes/mep_drain_routing_basis.md`` §2 is the hand-worked oracle.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN

#: IRC P3005.3's minimum for pipe of 3" and under: 1/4" per foot. The larger-pipe row
#: (1/8"/ft over 3") is ``mep.drain_slope``'s, and this module takes the governing minimum
#: from the caller rather than re-deriving it, so the two rules cannot disagree about a
#: diameter's grade.
MIN_SLOPE_SMALL_IN_PER_FT = 0.25
MIN_SLOPE_LARGE_IN_PER_FT = 0.125
LARGE_DIAMETER_M = 0.0762  # 3"


def minimum_slope(diameter_m: float) -> float:
    """The grade this diameter must hold, in inches per foot of developed plan length."""
    return (MIN_SLOPE_SMALL_IN_PER_FT if diameter_m <= LARGE_DIAMETER_M
            else MIN_SLOPE_LARGE_IN_PER_FT)


@dataclass(frozen=True)
class GravityProfile:
    """A start elevation and a grade — the whole of a drain's vertical description.

    ``start_m`` is the pipe's **centreline** at the profile's first horizontal vertex, per
    ``model/mep.py``'s note on ``PipeRun.elevations``. A profile says nothing about the
    drop above it: a flange drop and a stack are vertical legs, and a vertical leg has no
    grade to hold.
    """

    start_m: float
    slope_in_per_ft: float

    def invert_at(self, developed_ft: float) -> float:
        """The centreline this far along the route, in metres.

        §2 of the oracle note works this by hand for the suite bath's 3" collector: 116.5"
        at the drop bottom, 113.375" at 3.9854 ft, 112.0" at 5.7513 ft.
        """
        return self.start_m - developed_ft * self.slope_in_per_ft * M_PER_IN

    def fall_over(self, developed_ft: float) -> float:
        return developed_ft * self.slope_in_per_ft * M_PER_IN


@dataclass(frozen=True)
class HeadBudget:
    """Whether a route of this length fits between where it may start and where it must end.

    ``ceiling_m`` is the highest the pipe's centreline may start — a geometric bound, not a
    preference: §3's chord window puts a 3" pipe's ceiling at 117.0" on ``FS-S-WEST``, and
    the router must treat a crown resting on a chord as infeasible rather than tight.

    ``required_m`` is the lowest arrival the root accepts. For a stack that is a **range**,
    and this carries only its top: a vertical is a range of legal arrivals, so arriving
    lower than required is not a failure, and only arriving *higher than the ceiling allows*
    is.
    """

    ceiling_m: float
    required_m: float
    developed_ft: float
    diameter_m: float

    @property
    def available_in(self) -> float:
        return (self.ceiling_m - self.required_m) / M_PER_IN

    @property
    def needed_in(self) -> float:
        return self.developed_ft * minimum_slope(self.diameter_m)

    @property
    def slack_in(self) -> float:
        """Head left over after the minimum grade. §5's ordering key, negated.

        The oracle note's table: 0.062" for the water closet, 0.168" for the tub, 0.694"
        for the lavatory. A terminal with less slack has a route that is more nearly
        forced, which is why ``tree.py`` routes it first.
        """
        return self.available_in - self.needed_in

    @property
    def feasible(self) -> bool:
        return self.slack_in >= -1e-9

    def feasible_slope_in_per_ft(self) -> float | None:
        """The steepest grade this budget can hold, or None when the route has no length.

        **This is the number an infeasible route should report.** "No feasible route" is
        not actionable; "this route needs 0.19"/ft and the code wants 0.25" tells a person
        exactly how much shorter, higher or lower the problem has to get.
        """
        if self.developed_ft <= 0:
            return None
        return self.available_in / self.developed_ft

    def shortfall_in(self) -> float:
        """How many inches of head are missing. Zero when feasible."""
        return max(0.0, -self.slack_in)


def profile_for(budget: HeadBudget, *, grade_in_per_ft: float | None = None
                ) -> GravityProfile | None:
    """The profile a feasible budget should be built at, or None when it is not feasible.

    Defaults to the **minimum** legal grade rather than to the steepest available, and that
    is deliberate: head spent early is head unavailable to whatever ties in downstream, and
    the catlin suite bath's two arms both tie onto their collector rather than onto the
    stack. A caller that wants the head spent — because nothing downstream of it cares —
    passes ``grade_in_per_ft``.
    """
    if not budget.feasible:
        return None
    slope = grade_in_per_ft if grade_in_per_ft is not None else minimum_slope(
        budget.diameter_m)
    if slope * budget.developed_ft > budget.available_in + 1e-9:
        return None
    return GravityProfile(
        start_m=budget.required_m + slope * budget.developed_ft * M_PER_IN,
        slope_in_per_ft=slope)


def developed_lengths(points) -> list[float]:
    """Cumulative developed **plan** length at each vertex, in feet.

    Plan and not 3-D, because that is the datum every slope rule in this engine measures
    against — ``mep.drain_slope``, ``resolve/mep_slope`` and IRC P3005.3 alike. A vertical
    leg contributes nothing, which is the arithmetic reason a stack has no slope to hold.
    """
    out = [0.0]
    for a, b in zip(points, points[1:], strict=False):
        plan = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        out.append(out[-1] + plan / 0.3048)
    return out


def apply(points, profile: GravityProfile) -> list[tuple[float, float, float]]:
    """Re-elevate a plan polyline onto a gravity profile.

    Every vertex takes its own developed length's invert, so a route the search chose in
    plan comes back with the only vertical description a drain is allowed to have. Vertices
    that repeat a plan point — the drops — keep the elevation the profile gives them and
    are the caller's to author as real legs.
    """
    lengths = developed_lengths(points)
    return [(p[0], p[1], profile.invert_at(length))
            for p, length in zip(points, lengths, strict=False)]
