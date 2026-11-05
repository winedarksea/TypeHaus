"""A found plan route put on its gravity profile, snapped to the 1/16" grid."""

from __future__ import annotations

import math
from typing import Any

Point3 = tuple[float, float, float]


def _fall(points: list[Point3], origin: Point3, budget: Any, grade: float,
          target: str, problems: list[str], *, start_m: float | None = None,
          takeoff_xy: tuple[float, float] | None = None
          ) -> tuple[list[Point3], str] | None:
    """Put a found plan route on its gravity profile, or refuse and say by how much.

    The profile comes from ``gravity.profile_for``, built from the ARRIVAL upward so the
    route lands exactly on the tie — unless the search's band put the start higher
    (``start_m``, a route OVER a banded obstacle, §8a): then it starts there and drops into
    the tie at its last station. ``budget.ceiling_m`` is where the profile may start (the
    trap weir); the origin above it, a flange or a floor outlet's tailpiece, is prepended
    as the plumb drop it is. Elevations are snapped to the 1/16" grid from the arrival
    upward, each leg's fall rounded UP, so snapping never costs grade.

    ``takeoff_xy`` is a trap arm's vent take-off (§14): the arm holds grade off the weir to
    it, a plumb drop there takes the run to the rest's profile, and nothing is dropped at
    the trap — a plumber's trap in the bay, not an S-trap down to the tie.

    A refusal names the grade the route WOULD hold: "this needs 0.19"/ft and the code wants
    0.25"" says how much shorter, higher or lower the problem has to get.
    """
    split = None if takeoff_xy is None else _split_at(points, takeoff_xy)
    if takeoff_xy is not None and split is None:
        problems.append(f"{target}: the take-off is not on the drawn route")
        return None
    arm: list[Point3] = []
    rest = points
    if split is not None:
        arm, rest = split
    weir = budget.ceiling_m
    arm_ft = _plan_ft(arm)
    arm = [(p[0], p[1], weir - grade * _plan_ft(arm[:i + 1]) * 0.0254)
           for i, p in enumerate(arm)]
    if arm:
        from dataclasses import replace

        budget = replace(budget, ceiling_m=arm[-1][2], developed_ft=_plan_ft(rest))
        start_m = None if start_m is None else start_m - grade * arm_ft * 0.0254
    if len(rest) < 2:  # the arm ends on its tie: a wet-vent join (§14)
        fallen, over = [(*rest[0][:2], budget.required_m)], ""
    else:
        fallen, over = _profile(rest, budget, grade, target, problems, start_m)
    if fallen is None:
        return None
    fallen = _on_grid(fallen, grade)
    if arm:
        # The arm snaps DOWN off the weir, the rest UP off the tie; the take-off's tee is the
        # arm's last vertex and the plumb drop below it takes up the difference.
        arm = _arm_on_grid(arm, grade)
        if fallen[0][2] > arm[-1][2] + 1e-9:
            problems.append(f"{target}: on the 1/16\" grid the drain below the take-off "
                            f'needs {(fallen[0][2] - arm[-1][2]) / 0.0254:.3f}" more head '
                            "than the arm leaves it")
            return None
        fallen = [*arm, *(fallen[1:] if fallen[0][2] >= arm[-1][2] - 1e-9 else fallen)]
    if fallen[0][2] > weir + 1e-9:
        problems.append(f"{target}: on the 1/16\" grid the route needs "
                        f'{(fallen[0][2] - weir) / 0.0254:.3f}" more head than its '
                        "start allows — raise the start or shorten the run")
        return None
    if origin[2] > fallen[0][2] + 1e-9:
        fallen = [(fallen[0][0], fallen[0][1], origin[2]), *fallen]
    first = ("the arm holds grade off the trap weir for "
             f"{arm_ft * 12:.1f}\" and drops plumb at the vent take-off" if arm else
             "the first leg is the flange drop and takes no grade")
    return fallen, (f'gravity: {grade:.3f}"/ft over {budget.developed_ft + arm_ft:.2f} ft, '
                    f'{budget.slack_in:.2f}" of head to spare; {first}{over}')


def _profile(points: list[Point3], budget: Any, grade: float, target: str,
             problems: list[str], start_m: float | None
             ) -> tuple[list[Point3] | None, str]:
    from typehaus.routing.gravity import GravityProfile, apply
    from typehaus.routing.trades import pipe as pipe_trade

    fallen = pipe_trade.elevate(points, budget, grade_in_per_ft=grade)
    if fallen is None:
        feasible = budget.feasible_slope_in_per_ft()
        short = max(budget.shortfall_in(),
                    grade * budget.developed_ft - budget.available_in)
        problems.append(
            f'{target}: short {short:.2f}" of head over '
            f'{budget.developed_ft:.2f} ft. The route is feasible at '
            f'{feasible:.3f}"/ft and this asks for {grade:.3f}"/ft — raise the '
            f'start, lower the tie, or shorten the run by {short / grade:.2f} ft')
        return None, ""
    if start_m is None or start_m <= fallen[0][2] + 1e-6:
        return fallen, ""
    fallen = apply([(p[0], p[1]) for p in points], GravityProfile(start_m, grade))
    lift_in = (start_m - budget.required_m) / 0.0254 - grade * budget.developed_ft
    fallen.append((fallen[-1][0], fallen[-1][1], budget.required_m))
    return fallen, (f'; it starts {lift_in:.2f}" higher than the tie needs, to clear what it '
                    "passes over, and drops into the tie at its last station")


def _plan_ft(points: list[Point3]) -> float:
    return sum(math.dist(a[:2], b[:2]) for a, b in zip(points, points[1:], strict=False)) / 0.3048


def _split_at(points: list[Point3], at: tuple[float, float]
              ) -> tuple[list[Point3], list[Point3]] | None:
    """``(trap to take-off, take-off to tie)``, the take-off a vertex of both."""
    for i, (a, b) in enumerate(zip(points, points[1:], strict=False)):
        span = math.dist(a[:2], b[:2])
        t = 0.0 if span < 1e-9 else ((at[0] - a[0]) * (b[0] - a[0])
                                     + (at[1] - a[1]) * (b[1] - a[1])) / span ** 2
        foot = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        if -1e-6 <= t <= 1 + 1e-6 and math.dist(foot, at) < 1e-4:
            tee = (at[0], at[1], a[2])
            head = [*points[:i + 1], tee] if math.dist(a[:2], at) > 1e-6 else points[:i + 1]
            tail = [tee, *points[i + 1:]] if math.dist(b[:2], at) > 1e-6 else points[i + 1:]
            return head, tail
    return None


def _arm_on_grid(points: list[Point3], grade: float) -> list[Point3]:
    """Snap a trap arm to 1/16" from its weir DOWN, each leg's fall rounded up."""
    from typehaus.quantities import M_PER_IN
    from typehaus.routing.proposal import SNAP_IN, snap

    step = SNAP_IN * M_PER_IN
    plan = [(snap(x), snap(y)) for x, y, _z in points]
    z = [math.floor(points[0][2] / step + 1e-6) * step]
    for a, b in zip(plan, plan[1:], strict=False):
        run_ft = math.dist(a, b) / 0.3048
        z.append(z[-1] - (math.ceil(grade * run_ft * M_PER_IN / step - 1e-6) * step
                          if run_ft else 0.0))
    return [(x, y, zz) for (x, y), zz in zip(plan, z, strict=True)]


def _on_grid(points: list[Point3], grade: float) -> list[Point3]:
    """Snap to 1/16", building z from the arrival up with each leg's fall rounded UP."""
    from typehaus.quantities import M_PER_IN
    from typehaus.routing.proposal import SNAP_IN, snap

    step = SNAP_IN * M_PER_IN
    plan = [(snap(x), snap(y)) for x, y, _z in points]
    z = [snap(p[2]) for p in points]
    for i in range(len(points) - 2, -1, -1):
        run_ft = math.dist(plan[i], plan[i + 1]) / 0.3048
        fall = math.ceil(grade * run_ft * M_PER_IN / step - 1e-6) * step if run_ft else 0.0
        z[i] = max(z[i], z[i + 1] + fall)
    return [(x, y, zz) for (x, y), zz in zip(plan, z, strict=True)]
