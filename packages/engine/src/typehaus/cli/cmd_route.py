"""``haus route`` — propose a route, and print it for a person to paste.

**This is the only place ``checks`` and ``routing`` meet, and it sits above both.** That is
what keeps the leaf rule true rather than merely stated: a check may not consult a router,
because a search result is not a fact about the building; a router may not consult a check,
because it would then be optimising against its own grader. The CLI reads both and shows
you the two side by side, which is the honest arrangement.

**Nothing is ever written.** ``--write`` does not exist and is not an omission — see
:mod:`typehaus.routing.proposal` for the reasons. (The one that used to be printed here,
"``_content_hash`` would stale every pinned engineering seal", is **false**: a seal is
pinned against ``engineering/fingerprint.fingerprint(record)`` and ``_content_hash`` is not
one of its inputs. What stales a seal is moving geometry, which a route proposal does — so
the concern was real and only the mechanism was wrong.)

    haus route houses/catlin --run PR-B-KITCH-DRAIN        # re-route one authored run
    haus route houses/catlin --fixture FX-S-SUITEBATH-WC   # propose a branch for one
    haus route houses/catlin --tree PR-M-S-SUITE-DRAIN     # a main and every fixture on it
    haus route houses/catlin --unconnected                 # one per fixture_drain_reach FAIL
    haus route houses/catlin --run DU-M-ERV-R-KITCH --explain --timing
    haus route houses/catlin --fixture FX-S-SUITEBATH-WC --alternatives 3 --evaluate
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli._shared import app, console
from typehaus.cli.cmd_route_tree import _line_nodes, _propose_tree
from typehaus.cli.route_roots import hold_upstream
from typehaus.cli.route_roots import search_for as _search_for
from typehaus.cli.route_support import (
    Endpoints,
    _endpoints,
    _fall,
    _load,
    _nearest,
    _points,
    _root_nodes,
    _storey_datum,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.proposal import RouteProposal

#: Letters an alternative is tagged with. Past 26 the caller has asked a different question
#: from "show me a few ways to do this", and `--alternatives` refuses rather than wrapping.
_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _unconnected_fixtures(directory: Path, model: ResolvedModel) -> list[str]:
    """Every fixture ``mep.fixture_drain_reach`` reports a FAIL on.

    Read from the CHECK rather than re-derived here, and that is the whole architecture in
    one line: what is wrong with the house is a finding, and the router is aimed at
    findings. A second reach derivation living in the CLI would be the same judgement
    written twice and free to drift from the one that gates the build.
    """
    from typehaus.checks import build_context, run_checks

    ctx, _ = build_context(model.plan, directory)
    report = run_checks(ctx)
    return sorted({tag
                   for finding in report.findings
                   if finding.check_id == "mep.fixture_drain_reach"
                   and finding.result.value == "fail"
                   for tag in finding.element_tags
                   if tag.startswith("FX-")})


def _route_cost(directory: Path) -> RouteCost:
    """The weights this house routes at, from ``preferences.toml``'s ``[mep.routing]``.

    ``cost_from_preferences`` existed and nothing called it, so every route in this repo
    was priced at the module defaults and ``--explain`` printed a breakdown from a table
    the house had never been asked about. The table is carried through ``checks`` as a
    plain dict — see ``MepPreferences.routing`` — because ``checks`` may not import
    ``routing``, and this is the one place the two are allowed to meet.
    """
    from typehaus.checks import load_preferences
    from typehaus.routing.cost import cost_from_preferences

    return cost_from_preferences(load_preferences(directory).mep.routing)


def _storey_band(model: ResolvedModel, level: str) -> tuple[float, float] | None:
    """``--level``'s z band: this storey's datum up to the next one's.

    The top storey runs to infinity, which is right: an attic run is on the top storey and
    there is no plane above it to stop at.
    """
    elevations = sorted({s.elevation.meters for s in model.plan.storeys})
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == level), None)
    if datum is None:
        return None
    above = [e for e in elevations if e > datum + 1e-9]
    return (datum, min(above) if above else float("inf"))


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
        None, "--out", help="With --house: write report.json and proposed.py here. With "
                            "--space: write one SVG overlay per level. Nothing under plan/ "
                            "is touched either way."),
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
) -> None:
    """Propose MEP routes. Prints dialect source; writes nothing."""
    from typehaus.routing.proposal import render

    directory, model = _load(house)
    selectors = [bool(run), bool(fixture), bool(tree), unconnected, whole_house,
                 bool(space_of)]
    if sum(selectors) != 1:
        console.print("[red]choose exactly one of --run, --fixture, --tree, "
                      "--unconnected, --house, --space[/red]")
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
        band = _storey_band(model, level)
        if band is None:
            console.print(f"[red]--level {level} is not a storey in this model[/red]")
            raise typer.Exit(2)

    cost = _route_cost(directory)

    if space_of:
        from typehaus.cli.route_space import print_space_view

        raise typer.Exit(print_space_view(
            model, space_of, margin_ft=margin_ft, band=band, avoid=frozenset(avoid),
            cost=cost, as_json=as_json, svg_path=out_dir))

    if whole_house:
        from typehaus.cli.cmd_route_house import run_house_campaign

        unknown = sorted(set(trades) - set(_CAMPAIGN_TRADES))
        if unknown:
            console.print(f"[red]--trades {unknown} is not a trade this campaign lays; "
                          f"the trades are {', '.join(_CAMPAIGN_TRADES)}[/red]")
            raise typer.Exit(2)
        code = run_house_campaign(
            model, directory=directory, trades=list(trades) or None, storey=storey,
            locked=frozenset(locked), margin_ft=margin_ft, band=band,
            avoid=frozenset(avoid), cost=cost, slope=slope, alternatives=alternatives,
            rip_up_budget=rip_up_budget, out_dir=out_dir, as_json=as_json,
            explain=explain, evaluate=evaluate or as_json, orders=orders)
        raise typer.Exit(code)

    clock: list[str] = [] if timing else None  # type: ignore[assignment]

    targets: list[str]
    if unconnected:
        targets = _unconnected_fixtures(directory, model)
        if not targets:
            console.print("[green]mep.fixture_drain_reach reports no FAIL — every drained "
                          "fixture is reached by a run that names it. Nothing to "
                          "propose.[/green]")
            return
        console.print(f"[yellow]{len(targets)} fixture(s) reported by "
                      "mep.fixture_drain_reach[/yellow]")
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
        proposals, problems, notices, refusals = _propose_tree(
            model, tree, slope=slope, margin_ft=margin_ft, level=level,
            avoid=frozenset(avoid), via=_points(via), explain=explain, cost=cost,
            timing=clock)
    else:
        proposals, problems, notices, refusals = _propose(
            model, targets, mode=("run" if run else "fixture" if fixture
                                  else "unconnected"),
            slope=slope, margin_ft=margin_ft, band=band,
            avoid=frozenset(avoid), via=_points(via), explain=explain, cost=cost,
            alternatives=alternatives, timing=clock,
            counterfactual=counterfactual, hold=hold_upstream)

    if explain:
        for line in cost.table():
            console.print(f"[dim]{line}[/dim]")
    for line in notices:
        console.print(f"[dim]{line}[/dim]")
    for line in clock or ():
        console.print(f"[dim]timing: {line}[/dim]")
    for line in problems:
        console.print(f"[yellow]{line}[/yellow]")
    if not proposals:
        console.print("[red]no proposal — see above. A route that cannot be found is "
                      "reported, never approximated.[/red]")
        raise typer.Exit(1)

    evaluations = []
    if evaluate or as_json:
        from typehaus.cli.route_eval import evaluate_proposals

        evaluations = evaluate_proposals(directory, model, [p for p, _s in proposals])

    if as_json:
        import json

        from typehaus.cli.route_eval import payload

        by_tag = {p.tag: s for p, s in proposals}
        console.print_json(json.dumps(payload(
            directory, proposals[0][1],
            lambda p: (0.0 if p.kind == "conduit"
                       else _storey_datum(model, by_tag[p.tag])),
            [p for p, _s in proposals], evaluations, problems, notices,
            refusals), default=str))
        return

    if evaluations:
        from typehaus.cli.route_eval import render_reports

        for line in render_reports(evaluations):
            console.print(line)

    storey = proposals[0][1]
    # A raceway's elevations are project-frame absolute, so it takes no datum. Mixing the
    # two in one printout would be silent, so a mixed set is printed in two blocks.
    for kind, datum in (("conduit", 0.0), (None, _storey_datum(model, storey))):
        group = [p for p, _s in proposals
                 if (p.kind == "conduit") == (kind == "conduit")]
        if group:
            console.print(render(group, storey_datum_m=datum, explain=explain))
    console.print(f"[dim]elevations are relative to the `{storey}` storey — file the run "
                  "there, or they are wrong and nothing will say so; a ConduitRun's are "
                  "project-frame absolute and are printed as such[/dim]")
    if len(proposals) > 1 and alternatives > 1:
        console.print("[yellow]these are ALTERNATIVES to the same problem and they share "
                      "a `serves` — paste exactly ONE[/yellow]")


def _propose(model: ResolvedModel, targets: list[str], *, mode: str,
             slope: float | None, margin_ft: float, band: tuple[float, float] | None,
             avoid: frozenset[str], via: list[tuple[float, float]], explain: bool,
             cost: RouteCost, alternatives: int = 1, timing: list[str] | None = None,
             counterfactual: bool = False, extra_prisms: list | None = None,
             hold: int = 0
             ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str], list]:
    """The one place the router is driven. ``(proposals, problems, notices, refusals)``.

    Every refusal comes back as a *line*, never as a silent omission: a fixture whose drain
    point cannot be derived, a run whose root cannot be identified, a head budget that does
    not close. ``routing`` says why it refused and this prints it.

    ``extra_prisms`` are obstacles that are not in the model: a campaign's own accepted
    proposals (→ :mod:`typehaus.routing.campaign`). They are appended to the space rather
    than authored into a candidate model, because a proposal is not an element — inventing
    one to make it an obstacle would mean the campaign routed against a house nobody has.
    """
    from typehaus.routing.alternatives import alternative_routes
    from typehaus.routing.diagnostics import Refusal, refusal
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.timing import Timer

    proposals: list[tuple[RouteProposal, str]] = []
    problems: list[str] = []
    notices: list[str] = []
    refusals: list[Refusal] = []

    for target in targets:
        ends = _endpoints(model, target, mode, problems)
        if ends is not None and hold:
            ends = hold_upstream(model, ends, target, hold, problems)
        if ends is None:
            continue
        if explain:
            notices.extend(ends.advice)
        terminals = [ends.origin, ends.root, *[(p[0], p[1], ends.root[2]) for p in via]]
        # Seed the lattice along the whole parent line where the tie may land anywhere on
        # it: a goal on a line the graph never built is worth nothing, which is the failure
        # mode `routing/corridors` exists to avoid and the same one applies here.
        # **Per-vertex z where the line carries one.** A vent chase is vertical so one
        # elevation describes its whole goal line; a supply trunk rises at both ends, and
        # seeding it at a single z builds the lattice at a height the trunk is nowhere near
        # for most of its length.
        terminals.extend((v[0], v[1], v[2] if len(v) > 2 else ends.root[2])
                         for path in ends.root_paths for v in path)
        clock = Timer(target, enabled=timing is not None)
        try:
            try:
                with clock.stage("build-space"):
                    space = build_space(model, radius_m=ends.radius_m, terminals=terminals,
                                        margin_ft=margin_ft, avoid=avoid, touch=ends.touch,
                                        cost=cost, z_band=band)
                    if extra_prisms:
                        # Appended after the build so the space's own inflation is not
                        # applied twice: a campaign's prisms are already grown by the
                        # clearance the campaign chose.
                        space.hard.extend(extra_prisms)
                        space._hard_index = None
            except RoutingSpaceTooLarge as exc:
                problems.append(f"{target}: {exc}")
                continue
            if band is not None and not any(band[0] - 1e-9 <= p[2] <= band[1] + 1e-9
                                            for p in (ends.origin, ends.root)):
                problems.append(f"{target}: neither of its ends stands inside the --level "
                                "band, so restricting the search to that storey asks for a "
                                "route that cannot reach where it is told")
                continue

            # **A falling run searches in PLAN, in the plane it has to ARRIVE at.** Its z is a
            # derived monotone potential, so a 3-D search would optimise an elevation the
            # profile is about to overwrite — and would happily dive through the floor into a
            # cheap mechanical room and climb back, which flattens into a plan detour nobody
            # asked for. A pressurised run, a duct and a raceway keep the full lattice: their
            # elevation IS a choice, and it is the search's to make.
            levels = [ends.root[2]] if ends.falls else None
            try:
                # The lattice cap raises from `build_graph`, not only from `build_space` —
                # the line caps do not bound the node count, so this is the guard that
                # actually holds on a duct, whose search is genuinely three-dimensional.
                with clock.stage("build-graph"):
                    graph = build_graph(space, terminals, levels)
            except RoutingSpaceTooLarge as exc:
                problems.append(f"{target}: {exc}")
                continue
            clock.lattice(graph)
            start = _nearest(graph, ends.origin)
            # **A vent ties in ANYWHERE along its parent, a drain at its invert.** A branch
            # vent joining a common vent is ordinary IRC P3104 work, and with the root
            # modelled as one vertex the search structurally could not propose the merge —
            # on catlin PR-S-BATH1-VENT runs 18.5 ft to the chase while its origin sits 0.9
            # INCHES from PR-S-SUITEBATH-VENT's north leg. `--tree` already does this for
            # drains (`cmd_route_tree._line_nodes`); vents never reached that code.
            goals = set()
            for path in ends.root_paths:
                # The z gate applies exactly where the search is 3-D and the goal line has
                # an elevation of its own — the supply case. A vent's line carries plain
                # 2-tuples and `_line_nodes` leaves it plan-only, as it always was.
                goals |= _line_nodes(graph, path,
                                     z_tolerance=None if ends.falls else 0.05)
            if not goals:
                goals = _root_nodes(graph, ends.root, with_z=not ends.falls,
                                    exact=ends.tie_is_the_goal)
            if start is None or not goals:
                problems.append(
                    f"{target}: no lattice node at "
                    f"{'the origin' if start is None else 'the root'} — every candidate line "
                    "there is inside a hard obstacle, which is a statement about the model "
                    "rather than about the search")
                continue
            if graph.blocked_terminals:
                problems.append(
                    f"{target}: a terminal stands inside {', '.join(graph.blocked_terminals)} "
                    "— routed anyway, because a route must reach where it is told, but the "
                    "tie itself is a detail somebody has to draw")
            search, report = _search_for(model, graph, ends, slope)
            with clock.stage("search"):
                if alternatives > 1:
                    found_all = alternative_routes(search, graph, space, start, goals,
                                                   alternatives)
                else:
                    one = search(graph, space, start, goals)
                    found_all = [] if one is None else [one]
            for found in found_all:
                clock.route(found)
            if not found_all:
                attempts = (f"{alternatives} alternative(s) asked for"
                            if alternatives > 1 else "one search",
                            f"{len(space.hard)} hard prism(s), "
                            f"{len(space.corridors)} corridor(s) in the space",
                            f"margin {margin_ft:.3g} ft"
                            + ("" if band is None else ", pruned to the --level band"))
                if report is not None and report.tightest is not None:
                    # A gravity refusal knows something a geometric one does not: whether
                    # the route ran out of HEAD, and where. Its number is the shortage, and
                    # the geometric record carries it rather than replacing it — "a quarter
                    # inch under the web fourteen feet in" and "what is standing there" are
                    # both wanted, and the two used to be mutually exclusive.
                    shortages = (report.sentence(),)
                else:
                    shortages = ()
                refused = refusal(space, graph, start, goals, target=target,
                                  service=str(ends.system), shortages=shortages,
                                  attempts=attempts)
                refusals.append(refused)
                problems.append(refused.render())
                if counterfactual and refused.movable():
                    from typehaus.cli.route_diagnose import counterfactual_lines
                    notices.extend(counterfactual_lines(
                        model, ends, refused, margin_ft=margin_ft, band=band,
                        avoid=avoid, cost=cost, via=via, slope=slope,
                        search_for=_search_for))
                continue
            if alternatives > 1 and len(found_all) < alternatives:
                notices.append(f"{target}: {len(found_all)} distinct route(s) found of "
                               f"{alternatives} asked for — the rest were the same lane at a "
                               "higher price, which is not an alternative")

            for index, found in enumerate(found_all):
                suffix = f"-{_LETTERS[index]}" if len(found_all) > 1 else ""
                made = _one_proposal(model, ends, found, target, suffix, slope, explain,
                                     problems)
                if made is not None:
                    proposals.append((made, ends.storey))
        finally:
            # Measurements survive a refusal. A target that could not be routed is
            # exactly the one whose build-space and lattice counts say why.
            if timing is not None:
                timing.extend(clock.lines())
    return proposals, problems, notices, refusals


def _one_proposal(model: ResolvedModel, ends: Endpoints, found: Any, target: str,
                  suffix: str, slope: float | None, explain: bool,
                  problems: list[str]) -> RouteProposal | None:
    """One found route, given its elevations and its concealment, or None with a reason."""
    from typehaus.routing.gravity import HeadBudget, minimum_slope
    from typehaus.routing.proposal import RouteProposal, bay_note, concealment
    from typehaus.routing.trades import conduit as conduit_trade

    points = found.polyline()
    if ends.tie_is_the_goal:
        # The search ran riser -> trunk because the fixture end is the fixed one; the run is
        # authored trunk -> riser, and every reader downstream (the dialect, `serves`, the
        # tie-in derivation itself) reads path[0] as the tee. No gravity profile is
        # involved, so this really is the one line it looks like.
        points = list(reversed(points))
    # **A route of one point is not a run.** It means the origin was already standing on the
    # goal — which is a true and useful FINDING, and on catlin it is exactly the one the
    # vent merge is about: PR-S-BATH1-VENT's origin sits 0.9" from PR-S-SUITEBATH-VENT's
    # north leg. But "paste this" is the wrong thing to say about it, and printing a 1-tuple
    # of points emits dialect that will not even parse. So it is reported, never proposed.
    if len({(round(x, 6), round(y, 6)) for x, y, _z in points}) < 2:
        problems.append(
            f"{target + suffix}: its origin already stands on what it is being routed to, "
            "so the shortest route is no route at all. That is not a lane to paste — it is "
            "a finding: the two are already in one place, and what to do about it (land "
            "this run's fixtures on the other, or move one of them) is a judgement, not a "
            "search")
        return None
    notes: list[str] = []
    if ends.falls:
        developed_ft = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                           for a, b in zip(points, points[1:], strict=False)) / 0.3048
        grade = slope if slope is not None else minimum_slope(ends.diameter_m)
        budget = HeadBudget(ceiling_m=ends.origin[2], required_m=ends.root[2],
                            developed_ft=developed_ft, diameter_m=ends.diameter_m)
        fallen = _fall(points, ends.origin, budget, grade, target + suffix, problems)
        if fallen is None:
            return None
        points, note = fallen
        notes.append(note)

    routing, floor_ref, soffit_ref = (None, None, None)
    if ends.kind == "duct":
        routing, floor_ref, soffit_ref = concealment(model, found.corridor_tags)
        note = bay_note(model, found.corridor_tags, ends.radius_m)
        if note:
            notes.append(note)
    if ends.kind == "conduit":
        disclosed = conduit_trade.disclosure(conduit_trade.legalize(list(points)))
        if disclosed:
            notes.append(disclosed)

    return RouteProposal(
        tag=f"{target}-PROPOSED{suffix}", kind=ends.kind, points=[*ends.held, *points],
        diameter_m=ends.diameter_m, width_m=ends.width_m, depth_m=ends.depth_m,
        serves=ends.serves, system=ends.system, cost=found.cost, bends=found.bends,
        terms=dict(found.terms) if explain else {}, notes=notes, routing=routing,
        floor_ref=floor_ref, soffit_ref=soffit_ref, echo=dict(ends.echo),
        after=ends.after_paste).snapped()
