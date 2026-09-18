"""``--counterfactual`` and ``--sweep``: the two-way street's CLI surface.

Both answer a question ``haus route`` proper does not: not "where does this run go" but
**"why not, and what else could be tried"**. They are here rather than in ``cmd_route.py``
because that file drives the proposal loop and was already at the 500-line mark before
Phase 4 gave it two more jobs — and because the two really are one subject.

Each takes ``search_for`` as a parameter rather than importing it. ``cmd_route`` owns the
choice of which search a trade uses (a drain's is the gravity one), and a diagnostic priced
by a different search would be an argument about the wrong router.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console

from typehaus.cli.route_support import _endpoints, _nearest, _root_nodes

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost

console = Console()


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

    def build(extra: frozenset[str]):
        return build_space(model, radius_m=ends.radius_m, terminals=terminals,
                           margin_ft=margin_ft, avoid=avoid,
                           touch=ends.touch | extra, cost=cost, z_band=band)

    def search_one(space) -> float | None:
        levels = [ends.root[2]] if ends.falls else None
        graph = build_graph(space, terminals, levels)
        start = _nearest(graph, ends.origin)
        goals = _root_nodes(graph, ends.root, with_z=not ends.falls)
        if start is None or not goals:
            return None
        run, _report = search_for(model, graph, ends, slope)
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
