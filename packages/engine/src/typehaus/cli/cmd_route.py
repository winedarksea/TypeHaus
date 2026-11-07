"""Drive MEP proposals and independent evaluation; see docs/routing.md.

The CLI sits above routing and checks so the search never grades its own answer.
--out saves review artifacts; accepting a route requires editing its authored plan."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from typehaus.cli._shared import app, console
from typehaus.cli.cmd_route_tree import _propose_tree
from typehaus.cli.route_duct_search import search_for as _search_for
from typehaus.cli.route_options import RouteOptions
from typehaus.cli.route_propose import _LETTERS, _propose, _with_cleanouts  # noqa: F401
from typehaus.cli.route_support import _load, _points, storey_band
from typehaus.model.spatial import Fixture

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost


def _unconnected_fixtures(directory: Path, model: ResolvedModel) -> list[str]:
    """Fixture tags with mep.fixture_drain_reach FAILs, read from the check."""
    from typehaus.checks import build_context, run_checks

    ctx, _ = build_context(model.plan, directory)
    report = run_checks(ctx)
    return sorted({tag
                   for finding in report.findings
                   if finding.check_id == "mep.fixture_drain_reach"
                   and finding.result.value == "fail"
                   for tag in finding.element_tags
                   if isinstance(model.plan.by_tag(tag), Fixture)})


def _route_cost(directory: Path) -> RouteCost:
    """Load [mep.routing] weights through checks' plain preference dict.

    The CLI converts them to RouteCost because checks may not import routing."""
    from typehaus.checks import load_preferences
    from typehaus.routing.cost import cost_from_preferences

    return cost_from_preferences(load_preferences(directory).mep.routing)


#: The trades ``--house`` lays, named here so a typo is refused with the list rather than
#: silently emptying the campaign. Kept in step with ``routing.campaign.TRADE_ORDER`` by
#: ``tests/test_routing_campaign.py``.
_CAMPAIGN_TRADES = ("drain", "vent", "duct", "supply", "conduit")


@app.command()
def route(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    run: str | None = typer.Option(
        None, "--run", help="Re-route one authored run (pipe, duct or conduit), "
                            "keeping its terminals."),
    fixture: str | None = typer.Option(
        None, "--fixture", help="Propose a branch from one fixture to its nearest main."),
    tree: str | None = typer.Option(
        None, "--tree", help="A main and every fixture it serves, as one Steiner tree."),
    unconnected: bool = typer.Option(
        False, "--unconnected",
        help="One proposal per mep.fixture_drain_reach FAIL."),
    space_of: str | None = typer.Option(
        None, "--space", help="Classify the routing space this target would search — per "
                              "level, what is clear, what is priced, what refuses and what "
                              "is ungraded — instead of routing it."),
    scorecard: bool = typer.Option(
        False, "--scorecard", help="Search and grade the fixed scorecard targets "
                                   "(cli/route_scorecard.py); --out writes report.json "
                                   "and scorecard.md."),
    manifold: str | None = typer.Option(
        None, "--manifold", help="Lay every supply branch leaving this manifold's outlet "
                                 "ports as one campaign (shared occupancy, rip-up)."),
    whole_house: bool = typer.Option(
        False, "--house", help="Lay every run in scope as one coordinated campaign: a "
                               "stated trade order, one shared occupancy, bounded rip-up."),
    storey: str | None = typer.Option(
        None, "--storey", help="With --house: lay only the runs FILED on this storey. "
                               "Distinct from --level, which restricts the search's z "
                               "band: a basement drain is filed on the basement and hangs "
                               "below its datum, so scoping and banding are two questions."),
    trades: list[str] = typer.Option(
        [], "--trades", help="With --house: limit the campaign to these trades "
                             "(drain, vent, duct, supply, conduit)."),
    locked: list[str] = typer.Option(
        [], "--locked", help="With --house: these runs stay exactly where they are and "
                             "are obstacles, never targets."),
    orders: int = typer.Option(
        1, "--orders", help="With --house: try up to this many conflict ORDERS (max 3) and "
                            "rank the results — fewest refusals first, then cost."),
    rip_up_budget: int = typer.Option(
        4, "--rip-up", help="With --house: how many accepted proposals the campaign may "
                            "lift to make room for a refused one."),
    out_dir: Path | None = typer.Option(
        None, "--out", help="Write report.json and proposed.py here. With --space: "
                            "write one SVG overlay per level. House plan/ is untouched."),
    slope: float | None = typer.Option(
        None, "--slope", help="Inches per foot for a gravity run (default: the code "
                              "minimum for its diameter)."),
    margin_ft: float = typer.Option(
        8.0, "--margin", help="Feet of search space around the terminals' bounding box."),
    level: str | None = typer.Option(
        None, "--level", help="Restrict the search to one storey's z band."),
    avoid: list[str] = typer.Option(
        [], "--avoid", help="Treat these element tags as hard obstacles."),
    via: list[str] = typer.Option(
        [], "--via", help='Force the route through "X,Y" (feet), repeatable.'),
    alternatives: int = typer.Option(
        1, "--alternatives", help="How many distinct routes to offer. A is the "
                                  "unpenalised answer; paste exactly ONE."),
    evaluate: bool = typer.Option(
        False, "--evaluate", help="Run the MEP checks against a candidate model holding "
                                  "each proposal, and print what changed."),
    as_json: bool = typer.Option(
        False, "--json", help="Emit the network proposal and its evaluation as JSON. "
                              "Implies --evaluate."),
    summary: bool = typer.Option(
        False, "--summary", help="Compact decision JSON; requires --json --out DIR. "
                                 "Full details remain in report.json."),
    explain: bool = typer.Option(
        False, "--explain", help="Print the weights, the cost breakdown and the ordering."),
    sweep: float = typer.Option(
        0.0, "--sweep", help="With --fixture: walk the derived drain point this many "
                             "inches either way along its wall_ref, search each station, "
                             "and print the best as a Fixture(...) to paste."),
    counterfactual: bool = typer.Option(
        False, "--counterfactual", help="On a refusal, re-search with one MOVABLE blocker "
                                        "lifted at a time and report what a route would "
                                        "then cost. A diagnosis, never a proposal."),
    timing: bool = typer.Option(
        False, "--timing", help="Print build-space / build-graph / search ms and the "
                                "lattice and expansion counts."),
    hold_upstream: int = typer.Option(
        0, "--hold-upstream", help="With --run: keep the first N legs as authored and "
                                   "route from vertex N (a vent's wet-wall legs)."),
    group: str | None = typer.Option(
        None, "--group", help="A fixture group (tag or room) laid as ordered steps."),
    lift: list[str] = typer.Option(
        [], "--lift", help="With --tree: authored runs to lift and re-lay, repeatable."),
    topology: str | None = typer.Option(
        None, "--topology", help="With --tree on a supply main: tree or trunk."),
) -> None:
    """Propose MEP routes for review; --out saves reports outside the house's plan/."""
    from typehaus.cli.route_report import report_proposals, validate_output_directory

    if summary and (not as_json or out_dir is None or space_of or sweep > 0):
        raise typer.BadParameter("--summary requires --json --out DIR and a proposal mode; "
                                 "it cannot be used with --space or --sweep")
    directory, model = _load(house)
    validate_output_directory(out_dir, directory)
    selectors = [bool(run), bool(fixture), bool(tree), unconnected, whole_house,
                 bool(space_of), scorecard, bool(manifold), bool(group)]
    if sum(selectors) != 1:
        console.print("[red]choose exactly one of --run, --fixture, --tree, --unconnected, "
                      "--house, --manifold, --group, --space, --scorecard[/red]")
        raise typer.Exit(2)
    for flag, given in (("--lift", lift), ("--topology", topology)):
        if given and not tree:
            console.print(f"[red]{flag} applies to a --tree; it needs --tree[/red]")
            raise typer.Exit(2)
    if topology not in (None, "tree", "trunk"):
        console.print("[red]--topology wants tree or trunk[/red]")
        raise typer.Exit(2)
    if not 1 <= alternatives <= len(_LETTERS):
        console.print(f"[red]--alternatives wants 1..{len(_LETTERS)}[/red]")
        raise typer.Exit(2)
    if hold_upstream and not run:
        console.print("[red]--hold-upstream holds an authored run's legs; it needs --run[/red]")
        raise typer.Exit(2)
    if alternatives > 1 and tree:
        console.print("[red]--alternatives is refused with --tree: the alternatives are "
                      "per route and a tree is a set of them, so k routes per branch is "
                      "k^n trees and none of them has been priced as a tree[/red]")
        raise typer.Exit(2)

    band: tuple[float, float] | None = None
    if level is not None:
        band = storey_band(model, level)
        if band is None:
            console.print(f"[red]--level {level} is not a storey in this model[/red]")
            raise typer.Exit(2)

    cost = _route_cost(directory)

    if scorecard:
        from typehaus.cli.route_scorecard import write_scorecard

        raise typer.Exit(write_scorecard(directory, model, cost, out_dir))

    if space_of:
        from typehaus.cli.route_space import print_space_view

        raise typer.Exit(print_space_view(
            model, space_of, margin_ft=margin_ft, band=band, avoid=frozenset(avoid),
            cost=cost, as_json=as_json, svg_path=out_dir))

    clock: list[str] = [] if timing else None  # type: ignore[assignment]
    collect_details = explain or as_json or out_dir is not None

    def options() -> RouteOptions:  # built where a mode needs it: --via parses here, not before
        return RouteOptions(
            directory=directory, cost=cost, out_dir=out_dir, as_json=as_json,
            summary=summary, explain=explain, details=collect_details,
            evaluate=evaluate or as_json, margin_ft=margin_ft, level=level, band=band,
            avoid=frozenset(avoid), via=tuple(_points(via)), slope=slope,
            alternatives=alternatives, timing=clock)

    if group:
        from typehaus.cli.cmd_route_group import route_group

        raise typer.Exit(route_group(model, group, options()))

    if whole_house or manifold:
        from typehaus.cli.cmd_route_house import manifold_branches, run_house_campaign

        only = None if manifold is None else manifold_branches(model, manifold)
        if only is not None and not only:
            console.print(f"[red]--manifold {manifold}: no supply run starts on an outlet "
                          "port of it (resolve/mep_tie_ins)[/red]")
            raise typer.Exit(2)
        unknown = sorted(set(trades) - set(_CAMPAIGN_TRADES))
        if unknown:
            console.print(f"[red]--trades {unknown} is not a trade this campaign lays; "
                          f"the trades are {', '.join(_CAMPAIGN_TRADES)}[/red]")
            raise typer.Exit(2)
        code = run_house_campaign(
            model, directory=directory, only=only,
            trades=["supply"] if manifold else list(trades) or None, storey=storey,
            locked=frozenset(locked), margin_ft=margin_ft, band=band,
            avoid=frozenset(avoid), cost=cost, slope=slope, alternatives=alternatives,
            rip_up_budget=rip_up_budget, out_dir=out_dir, as_json=as_json,
            explain=explain, evaluate=evaluate or as_json, orders=orders, summary=summary)
        raise typer.Exit(code)

    targets: list[str]
    notices: list[str] = []
    if unconnected:
        targets = _unconnected_fixtures(directory, model)
        notices.append(f"{len(targets)} fixture(s) reported by mep.fixture_drain_reach"
                       if targets else "mep.fixture_drain_reach reports no FAIL — every "
                       "drained fixture is reached by a run that names it. Nothing to propose.")
    else:
        targets = [t for t in (run, fixture) if t]

    if sweep > 0:
        if not fixture:
            console.print("[red]--sweep moves a fixture's drain point, so it needs "
                          "--fixture[/red]")
            raise typer.Exit(2)
        from typehaus.cli.route_diagnose import run_sweep

        run_sweep(model, fixture, margin_ft=margin_ft, band=band,
                  avoid=frozenset(avoid), cost=cost, slope=slope, reach_in=sweep,
                  search_for=_search_for)
        return

    if tree:
        from typehaus.cli.cmd_route_supply_tree import is_supply_main, propose_supply_tree
        from typehaus.cli.route_tree_lift import propose_tree_lifted

        if topology or is_supply_main(model, tree):
            proposals, problems, route_notices, refusals = propose_supply_tree(
                model, tree, topology, options())
        elif lift:
            proposals, problems, route_notices, refusals = propose_tree_lifted(
                model, tree, tuple(lift), options())
        else:
            proposals, problems, route_notices, refusals = _propose_tree(
                model, tree, slope=slope, margin_ft=margin_ft, level=level,
                avoid=frozenset(avoid), via=_points(via), explain=collect_details,
                cost=cost, timing=clock)
    else:
        proposals, problems, route_notices, refusals = _propose(
            model, targets, mode=("run" if run else "fixture" if fixture
                                  else "unconnected"),
            slope=slope, margin_ft=margin_ft, band=band,
            avoid=frozenset(avoid), via=_points(via), explain=collect_details, cost=cost,
            alternatives=alternatives, timing=clock,
            counterfactual=counterfactual, hold=hold_upstream)

    notices.extend(route_notices)
    evaluations = []
    if proposals and (evaluate or as_json):
        from typehaus.cli.route_eval import evaluate_proposals

        laid = [p for p, _s in proposals]
        evaluations = evaluate_proposals(directory, model, laid)
        if tree and len(laid) > 1:
            # Alone, a branch meets the authored drain another branch replaces (§13).
            from typehaus.cli.route_eval import evaluate_network

            network = evaluate_network(directory, model, laid)
            network.tag = f"{tree} (all branches together)"
            evaluations.append(network)
    report_proposals(
        model, directory, proposals, evaluations=evaluations, problems=problems,
        notices=notices, refusals=refusals, clock=clock, cost=cost, explain=explain,
        as_json=as_json, summary=summary, out_dir=out_dir)
    if not proposals and (tree or targets) and (problems or refusals):
        raise typer.Exit(1)
