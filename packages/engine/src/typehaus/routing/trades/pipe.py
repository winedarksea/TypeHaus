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

from collections.abc import Sequence

from typehaus.routing.corridors import Corridor
from typehaus.routing.gravity import HeadBudget, apply, profile_for

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


def elevate(points: Sequence[tuple[float, ...]], budget: HeadBudget | None, *,
            grade_in_per_ft: float | None = None
            ) -> list[tuple[float, float, float]] | None:
    """Give a found plan route its elevations, or None when the head does not close.

    With no budget the route keeps whatever z the search chose — the supply case. With one,
    the elevations come from :func:`~typehaus.routing.gravity.profile_for` and nothing
    else, so the result is monotone by construction rather than by checking afterwards.

    **The profile is built from the ARRIVAL upward**, not from the ceiling down, and that
    is ``profile_for``'s decision rather than this function's: head spent early is head
    unavailable to whatever ties in downstream. Building it from ``ceiling_m`` instead
    would land the route above its own tie by exactly the slack and say nothing.

    None rather than a route means the grade asked for does not fit the budget — including
    a ``--slope`` steeper than the code minimum, which ``HeadBudget.feasible`` does not
    grade because it asks about the minimum.
    """
    if budget is None:
        return [(p[0], p[1], p[2]) for p in points]
    profile = profile_for(budget, grade_in_per_ft=grade_in_per_ft)
    if profile is None:
        return None
    return apply([(p[0], p[1]) for p in points], profile)
