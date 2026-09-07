"""Supply and drain pipe. The easiest consumer, and the right one to prove the graph on.

Supply has **no gravity predicate**: its elevation is a choice rather than a derived
potential, so a supply route is the plain A* case with nothing on top of it. That is why
the graph was proven on supply before ``gravity.py`` existed — a bug in the search and a
bug in the profile look identical once the two are stacked.

Drain adds :mod:`typehaus.routing.gravity`, and adds it *after* the plan route is found:
z is a function of developed plan length, so the search solves the plan and the profile
solves the elevations. That ordering is not an optimisation, it is what "monotone
potential" means.
"""

from __future__ import annotations

from typehaus.routing.corridors import Corridor
from typehaus.routing.gravity import GravityProfile, HeadBudget, apply, minimum_slope

#: Systems that fall. Everything else in ``PipeSystem`` is pressurised or is a vent, and a
#: vent rises to a roof rather than falling to a main — a different problem this package
#: does not claim to solve.
GRAVITY_SYSTEMS = frozenset({"drain"})


def radius_m(diameter_m: float) -> float:
    """Half the outside dimension — a pipe is round, so this is the whole of it."""
    return (diameter_m or 0.0) / 2.0


def crossing_admissible(corridor: Corridor, diameter_m: float,
                        window: tuple[float, float] | None) -> bool:
    """Whether a pipe may cross a floor's members inside this z window.

    The window is chord-to-chord for a truss and the borable web for an I-joist, and the
    pipe's whole OUTSIDE has to fit it — the note's §3 works it at 8 7/8" against an 11 7/8"
    truss, which puts a 3" pipe's centreline in [111.125, 117.0] on ``FS-S-WEST``.
    """
    del corridor  # the window is the constraint; which bay it is does not change it
    if window is None:
        return False
    low, high = window
    return (high - low) >= diameter_m - 1e-9


def falls(system: str) -> bool:
    return system in GRAVITY_SYSTEMS


def elevate(points, budget: HeadBudget | None, *,
            grade_in_per_ft: float | None = None):
    """Give a found plan route its elevations.

    With no budget the route keeps whatever z the search chose — the supply case. With one,
    the elevations are derived from a :class:`GravityProfile` and nothing else, so the
    result is monotone by construction rather than by checking afterwards.
    """
    if budget is None:
        return list(points)
    slope = (grade_in_per_ft if grade_in_per_ft is not None
             else minimum_slope(budget.diameter_m))
    profile = GravityProfile(start_m=budget.ceiling_m, slope_in_per_ft=slope)
    return apply([(p[0], p[1]) for p in points], profile)
