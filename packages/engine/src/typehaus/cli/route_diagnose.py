"""Counterfactual and drain-point sweep adapters; see docs/routing.md.

search_for is injected so diagnostics use the same trade search as the original attempt."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console

from typehaus.cli.route_support import _endpoints, _nearest, _root_nodes

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost

console = Console()


def refuse(space: Any, graph: Any, start: int, goals: set[int], *, target: str, ends: Any,
           report: Any, alternatives: int, margin_ft: float,
           band: tuple[float, float] | None) -> Any:
    """The structured refusal for a search that returned nothing, take-off table and all."""
    from typehaus.routing.diagnostics import refusal

    attempts = (f"{alternatives} alternative(s) asked for" if alternatives > 1
                else "one search",
                f"{len(space.hard)} hard prism(s), {len(space.corridors)} corridor(s) in the "
                "space", f"margin {margin_ft:.3g} ft"
                + ("" if band is None else ", pruned to the --level band"))
    # A gravity refusal knows whether the route ran out of HEAD, and where. Its number is
    # the shortage, and the geometric record carries it rather than replacing it.
    shortages = ((report.sentence(),) if report is not None
                 and (report.tightest is not None or report.notes) else ())
    takeoffs = report.takeoffs if report is not None else []
    return refusal(space, graph, start, goals, target=target, service=str(ends.system),
                   shortages=shortages, attempts=attempts, takeoffs=tuple(takeoffs),
                   extra_blockers=tuple(t.blocker for t in takeoffs if t.blocker is not None))


def counterfactual_lines(model: ResolvedModel, ends: Any, refused: Any, *,
                         margin_ft: float, band: tuple[float, float] | None,
                         avoid: frozenset[str], cost: RouteCost,
                         via: list[tuple[float, float]], slope: float | None,
                         search_for) -> list[str]:
    """``--counterfactual``: relax one movable blocker at a time and price what opens.

    The relaxation rides the ``touch`` channel the re-route already uses for the run it
    replaces — a prism a route is allowed to occupy — so lifting a blocker costs no new
    concept and cannot reach anything but the one tag named. The search is ``search_for``'s
    — the same one the real attempt used, picked by trade — because a counterfactual priced
    by a different search would be an argument about the wrong router.
    """
    from typehaus.routing.counterfactual import counterfactuals, render
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import build_space

    terminals = [ends.origin, ends.root, *[(p[0], p[1], ends.root[2]) for p in via]]
    lifted: list[frozenset[str]] = [frozenset()]

    def build(extra: frozenset[str]):
        # The vent lattice is built inside the search: the lifted tag reaches it via touch.
        lifted[0] = extra
        return build_space(model, radius_m=ends.radius_m, terminals=terminals,
                           margin_ft=margin_ft, avoid=avoid,
                           touch=ends.touch | extra, cost=cost, z_band=band,
                           cavity_radius_m=ends.cavity_radius_m or None,
                           panel_space=ends.kind != "conduit")

    def search_one(space) -> float | None:
        levels = [ends.root[2]] if ends.falls else None
        graph = build_graph(space, terminals, levels)
        start = _nearest(graph, ends.origin)
        goals = _root_nodes(graph, ends.root, with_z=not ends.falls,
                            exact=ends.tie_is_the_goal)
        if start is None or not goals:
            return None
        run, _report = search_for(model, graph, replace(ends, touch=ends.touch | lifted[0]),
                                  slope)
        found = run(graph, space, start, goals)
        return None if found is None else found.cost

    return render(counterfactuals(model, refused.blockers,
                                  build=build, search=search_one))


def run_sweep(model: ResolvedModel, fixture: str, *, margin_ft: float,
              band: tuple[float, float] | None, avoid: frozenset[str],
              cost: RouteCost, slope: float | None, reach_in: float,
              search_for) -> None:
    """``--sweep``: the fixture's own station as a design variable — see cmd_route_sweep."""
    from typehaus.cli.cmd_route_sweep import render, sweep

    problems: list[str] = []
    ends = _endpoints(model, fixture, "fixture", problems)
    for line in problems:
        console.print(f"[yellow]{line}[/yellow]")
    if ends is None:
        raise typer.Exit(1)
    found = sweep(model, fixture, ends, reach_in=reach_in, margin_ft=margin_ft,
                  band=band, avoid=avoid, cost=cost, slope=slope,
                  search_for=search_for)
    for line in render(fixture, found, model):
        console.print(line)
