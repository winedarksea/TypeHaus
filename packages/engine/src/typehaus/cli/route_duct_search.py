"""The one entry point every duct search goes through: the fitted A* (``routing/duct_search``).

``search_for`` stands in for ``route_roots.search_for`` at every call site in
``cmd_route``/``route_propose`` (proposal, counterfactual, sweep); non-ducts are untouched.
docs/routing.md; ``mep_duct_routing_basis.md`` §7-§8."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from typehaus.cli import route_roots
from typehaus.quantities import M_PER_IN


def search_for(model: Any, graph: Any, ends: Any, slope: float | None):
    """``route_roots.search_for``'s contract: (search callable, refusal report)."""
    if ends.kind == "duct":
        return duct_search(model, graph, ends, slope)
    return route_roots.search_for(model, graph, ends, slope)


def duct_search(model: Any, graph: Any, ends: Any, slope: float | None):
    """``(graph, space, start, goals) -> Route | None`` holding every elbow's take-off, and
    its refusal report. ``graph`` and ``slope`` are unused: a duct has no grade."""
    del graph, slope
    from typehaus.routing.duct_search import DuctRefusal, fitted_route

    problem = fitting_problem(model, ends)
    report = DuctRefusal()

    def search(a_graph, a_space, start, goals):
        jog = a_space.cost.offset_jog_max_in * M_PER_IN if problem.offsets else 0.0
        return fitted_route(a_graph, a_space, start, goals,
                            replace(problem, offset_jog_max_m=jog), refusal=report)

    return search, report


def z_radius_m(ends: Any) -> float | None:
    """The half-height a flat rectangular duct sweeps, where it is not ``radius_m`` (half the
    larger side, which a turn's diagonal needs in plan but a level run does not in z)."""
    if ends.kind != "duct" or not (ends.width_m and ends.depth_m):
        return None
    return ends.radius_m - (max(ends.width_m, ends.depth_m) - ends.depth_m) / 2.0


def fitting_problem(model: Any, ends: Any):
    """The take-off of this duct's 90-degree elbow, its fabrication premium, the 45 and 30
    an offset may be made with (round, and only where bought: a gored offset is no offset),
    and the lead headings."""
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.routing.duct_fittings import FABRICATED_ELBOW_IN, OFFSET_ANGLES, elbow
    from typehaus.routing.duct_search import DuctFittingProblem

    standard, _ = duct_standard(getattr(model, "plan", None))
    made = elbow(standard, 90.0, diameter_m=ends.diameter_m or None)
    offsets = []
    for theta in OFFSET_ANGLES:
        part = elbow(standard, theta, diameter_m=ends.diameter_m or None)
        if not part.fabricated:
            offsets.append((theta, part.takeoff_m(theta)))
    return DuctFittingProblem(
        takeoff_m=made.takeoff_m(90.0), offsets=tuple(offsets),
        fabricated_in=FABRICATED_ELBOW_IN if made.fabricated else 0.0,
        start_axis=_heading(ends.origin_lead), goal_axis=_heading(ends.root_lead, True))


def _heading(lead: Any, arriving: bool = False) -> str:
    """The signed heading off a lead's tip, or reversed: arriving, the route heads for the
    port."""
    if lead is None:
        return ""
    heading = lead.exit_heading
    sign = heading[0]
    return ({"+": "-", "-": "+"}[sign] if arriving else sign) + heading[-1]

