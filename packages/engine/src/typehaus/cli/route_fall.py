"""A found plan route put on its gravity profile, snapped to the 1/16" grid."""

from __future__ import annotations

from typing import Any


def _fall(points: list[tuple[float, float, float]],
          origin: tuple[float, float, float], budget: Any, grade: float,
          target: str, problems: list[str], *, start_m: float | None = None
          ) -> tuple[list[tuple[float, float, float]], str] | None:
    """Put a found plan route on its gravity profile, or refuse and say by how much.

    The profile comes from ``gravity.profile_for``, built from the ARRIVAL upward so the
    route lands exactly on the tie — unless the search's band put the start higher
    (``start_m``, a route OVER a banded obstacle, §8a): then it starts there and drops into
    the tie at its last station. The flange is prepended at the finished floor, so the
    first leg is the vertical drop it is. Elevations are snapped to the 1/16" grid from the
    arrival upward, each leg's fall rounded UP, so snapping never costs grade.

    A refusal names the grade the route WOULD hold: "this needs 0.19"/ft and the code wants
    0.25"" says how much shorter, higher or lower the problem has to get.
    """
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
        return None
    over = ""
    if start_m is not None and start_m > fallen[0][2] + 1e-6:
        fallen = apply([(p[0], p[1]) for p in points], GravityProfile(start_m, grade))
        lift_in = (start_m - budget.required_m) / 0.0254 - grade * budget.developed_ft
        over = (f'; it starts {lift_in:.2f}" '
                "higher than the tie needs, to clear what it passes over, and drops into "
                "the tie at its last station")
        fallen.append((fallen[-1][0], fallen[-1][1], budget.required_m))
    fallen = _on_grid(fallen, grade)
    if fallen[0][2] > origin[2] + 1e-9:
        problems.append(f"{target}: on the 1/16\" grid the route needs "
                        f'{(fallen[0][2] - origin[2]) / 0.0254:.3f}" more head than its '
                        "start allows — raise the start or shorten the run")
        return None
    if origin[2] > fallen[0][2] + 1e-9:
        fallen = [(fallen[0][0], fallen[0][1], origin[2]), *fallen]
    return fallen, (f'gravity: {grade:.3f}"/ft over {budget.developed_ft:.2f} ft, '
                    f'{budget.slack_in:.2f}" of head to spare; the first leg is the '
                    f"flange drop and takes no grade{over}")


def _on_grid(points: list[tuple[float, float, float]], grade: float
             ) -> list[tuple[float, float, float]]:
    """Snap to 1/16", building z from the arrival up with each leg's fall rounded UP."""
    import math

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
