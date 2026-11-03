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

#: Systems that may never fall from their origin to their root. A vent is graded to drain
#: back to the drain it serves (MN 905.1, ``mep.vent_grade``) and a radon pipe back to its
#: pit, so a lane that dips under one duct and climbs over the next traps water in both.
#: ``notes/vent_grade_basis.md`` §"The router" is the oracle.
RISING_SYSTEMS = frozenset({"vent", "radon"})


def radius_m(diameter_m: float, material: str | None = None,
             insulation: str | None = None) -> float:
    """Half the REAL outside: OD for this material plus lagging, as ``run_radii`` reads it.

    The authored ``diameter`` is nominal, and 3" DWV is 3.5" across. An unstated material
    takes the IPS series (the larger), and lagging that states no thickness counts as none,
    the same reading ``mep_envelopes.run_envelope`` discloses.
    """
    from typehaus.resolve.mep_envelopes import insulation_thickness_m
    from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

    lagging = insulation_thickness_m(insulation) or 0.0
    return pipe_outside_diameter_m(diameter_m or 0.0, material) / 2.0 + lagging


def cavity_radius_m(diameter_m: float, system: str, material: str | None = None,
                    insulation: str | None = None) -> float:
    """Half what a stud cavity must hold: the HUB for DWV, so 3" cannot claim a 2x4."""
    from typehaus.resolve.mep_envelopes import insulation_thickness_m
    from typehaus.resolve.pipe_sections import hub_outside_diameter_m

    if system not in ("drain", "vent"):
        return radius_m(diameter_m, material, insulation)
    lagging = insulation_thickness_m(insulation) or 0.0
    return hub_outside_diameter_m(diameter_m or 0.0, material) / 2.0 + lagging


def bend_radius_m(diameter_m: float, system: str, material: str | None) -> float:
    """A pressure tube's minimum bend radius, the maker's ratio x OD; 0 where it is fitted.

    ``mep_fittings.tube_bend_rule`` is the rule the take-off grades a bend against, so the
    router never prices a bend the take-off will call a fitting. Copper and CPVC carry no
    rule; a drain or vent is never bent.
    """
    from typehaus.resolve.mep_fittings import tube_bend_rule
    from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

    system = getattr(system, "value", system)
    rule = tube_bend_rule(material) if system not in GRAVITY_SYSTEMS | {"vent"} else None
    return 0.0 if rule is None else rule[0] * pipe_outside_diameter_m(diameter_m, material)


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


def rises(system: str) -> bool:
    """Whether every step from origin to root must hold or gain elevation."""
    return system in RISING_SYSTEMS


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


#: Tube sold in coils: a straight run of it has no joint between lengths.
_COILED = frozenset({"pex", "pex-a"})


def coupling_disclosure(points: Sequence[tuple[float, float, float]],
                        material: str | None) -> str | None:
    """A rigid pipe's joins between stock lengths, which the proposal cannot count.

    One coupling per stock length of each straight leg; no material or catalog row here
    states a pipe's stock length, so the count is disclosed as a gap rather than guessed.
    """
    if (material or "").strip().lower() in _COILED:
        return None
    legs = [sum((pb - pa) ** 2 for pa, pb in zip(a, b, strict=True)) ** 0.5 / 0.3048
            for a, b in zip(points, points[1:], strict=False)]
    legs = [ft for ft in legs if ft > 1e-6]
    if not legs:
        return None
    what = f"rigid {material}" if material else "pipe of no stated material"
    return (f"couplings: {len(legs)} straight leg(s), {sum(legs):.1f} ft of {what}, "
            f"longest {max(legs):.1f} ft — one coupling per stock length of each leg, but "
            "no stock length is on record for it, so the joins between sticks are not "
            "counted")
