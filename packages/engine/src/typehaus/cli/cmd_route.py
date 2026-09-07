"""``haus route`` — propose a route, and print it for a person to paste.

**This is the only place ``checks`` and ``routing`` meet, and it sits above both.** That is
what keeps the leaf rule true rather than merely stated: a check may not consult a router,
because a search result is not a fact about the building; a router may not consult a check,
because it would then be optimising against its own grader. The CLI reads both and shows
you the two side by side, which is the honest arrangement.

**Nothing is ever written.** ``--write`` does not exist and is not an omission — see
:mod:`typehaus.routing.proposal` for the three reasons, of which the fatal one is that
``source/loader._content_hash`` hashes every ``plan/**/*.py`` and a machine edit would
stale every pinned engineering seal in the house.

    haus route houses/catlin --run PR-B-KITCH-DRAIN        # re-route one authored run
    haus route houses/catlin --fixture FX-S-SUITEBATH-WC   # propose a branch for one
    haus route houses/catlin --tree PR-M-S-SUITE-DRAIN     # a main and all that feeds it
    haus route houses/catlin --unconnected                 # one per fixture_drain_reach FAIL
    haus route houses/catlin --run DU-M-ERV-R-KITCH --explain
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console


def _load(house: Path | None):  # type: ignore[no-untyped-def]
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    if errors:
        _print_findings(errors)
        raise typer.Exit(1)
    return directory, model


def _storey_datum(model, storey: str) -> float:
    return next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)


def _unconnected_fixtures(directory: Path, model) -> list[str]:
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


@app.command()
def route(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    run: str | None = typer.Option(
        None, "--run", help="Re-route one authored run, keeping its terminals."),
    fixture: str | None = typer.Option(
        None, "--fixture", help="Propose a branch from one fixture to its nearest main."),
    tree: str | None = typer.Option(
        None, "--tree", help="A main and every fixture that names it."),
    unconnected: bool = typer.Option(
        False, "--unconnected",
        help="One proposal per mep.fixture_drain_reach FAIL."),
    slope: float | None = typer.Option(
        None, "--slope", help="Inches per foot for a gravity run (default: the code "
                              "minimum for its diameter)."),
    margin_ft: float = typer.Option(
        8.0, "--margin", help="Feet of search space around the terminals' bounding box."),
    level: str | None = typer.Option(
        None, "--level", help="Restrict the search to one storey."),
    avoid: list[str] = typer.Option(
        [], "--avoid", help="Treat these element tags as hard obstacles."),
    via: list[str] = typer.Option(
        [], "--via", help='Force the route through "X,Y" (feet), repeatable.'),
    explain: bool = typer.Option(
        False, "--explain", help="Print the cost breakdown and the ordering behind it."),
) -> None:
    """Propose MEP routes. Prints dialect source; writes nothing."""
    from typehaus.routing.proposal import render

    directory, model = _load(house)
    selectors = [bool(run), bool(fixture), bool(tree), unconnected]
    if sum(selectors) != 1:
        console.print("[red]choose exactly one of --run, --fixture, --tree, "
                      "--unconnected[/red]")
        raise typer.Exit(2)

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
        targets = [t for t in (run, fixture, tree) if t]

    proposals, problems = _propose(
        model, targets, mode=("run" if run else "fixture" if fixture
                              else "tree" if tree else "unconnected"),
        slope=slope, margin_ft=margin_ft, level=level,
        avoid=frozenset(avoid), via=_points(via), explain=explain)

    for line in problems:
        console.print(f"[yellow]{line}[/yellow]")
    if not proposals:
        console.print("[red]no proposal — see above. A route that cannot be found is "
                      "reported, never approximated.[/red]")
        raise typer.Exit(1)

    storey = proposals[0][1]
    console.print(render([p for p, _s in proposals],
                         storey_datum_m=_storey_datum(model, storey), explain=explain))
    console.print(f"[dim]elevations are relative to the `{storey}` storey — file the run "
                  "there, or they are wrong and nothing will say so[/dim]")


def _points(via: list[str]) -> list[tuple[float, float]]:
    out = []
    for item in via:
        try:
            x, y = (float(v) for v in item.split(","))
        except ValueError as exc:  # noqa: PERF203 - one message per bad argument
            raise typer.BadParameter(f'--via wants "X,Y" in feet, got {item!r}') from exc
        out.append((x * 0.3048, y * 0.3048))
    return out


def _propose(model, targets: list[str], *, mode: str, slope: float | None,
             margin_ft: float, level: str | None, avoid: frozenset[str],
             via: list[tuple[float, float]], explain: bool):
    """The one place the router is actually driven. Returns ``(proposals, problems)``.

    Every refusal comes back as a *line*, never as a silent omission: a fixture whose drain
    point cannot be derived, a run whose root cannot be identified, a head budget that does
    not close. ``routing`` says why it refused and this prints it.
    """
    from typehaus.routing.graph import build_graph
    from typehaus.routing.gravity import HeadBudget, minimum_slope
    from typehaus.routing.proposal import RouteProposal
    from typehaus.routing.search import shortest_route
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.trades import pipe as pipe_trade

    proposals: list[tuple[RouteProposal, str]] = []
    problems: list[str] = []

    for target in targets:
        origin, root, diameter_m, serves, storey, system, touch = _endpoints(
            model, target, mode, problems)
        if origin is None:
            continue
        radius = pipe_trade.radius_m(diameter_m)
        terminals = [origin, root, *[(p[0], p[1], root[2]) for p in via]]
        try:
            space = build_space(model, radius_m=radius, terminals=terminals,
                                margin_ft=margin_ft, avoid=avoid, touch=touch)
        except RoutingSpaceTooLarge as exc:
            problems.append(f"{target}: {exc}")
            continue
        if level is not None and level not in space.storeys:
            problems.append(f"{target}: --level {level} is not a storey in this model")
            continue

        # **A falling run searches in PLAN, in the plane it has to ARRIVE at.** Its z is a
        # derived monotone potential, so a 3-D search would optimise an elevation the
        # profile is about to overwrite — and would happily dive through the floor into a
        # cheap mechanical room and climb back, which flattens into a plan detour nobody
        # asked for. The root's own plane is the right one to search in rather than the
        # fixture's floor: the floor is where the flange is, and a flange is a drop rather
        # than a route. A pressurised run keeps the full lattice — its elevation IS a
        # choice, and it is the search's to make.
        levels = [root[2]] if system in ("drain",) else None
        graph = build_graph(space, terminals, levels)
        start = _nearest(graph, origin)
        goals = _root_nodes(graph, root)
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
        found = shortest_route(graph, space, start, goals)
        if found is None:
            problems.append(f"{target}: no route in plan; every lane is blocked")
            continue

        points = found.polyline()
        grade = slope if slope is not None else minimum_slope(diameter_m)
        developed_ft = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                           for a, b in zip(points, points[1:], strict=False)) / 0.3048
        budget = HeadBudget(ceiling_m=origin[2], required_m=root[2],
                            developed_ft=developed_ft, diameter_m=diameter_m)
        notes = []
        if system == "drain" and not budget.feasible:
            feasible = budget.feasible_slope_in_per_ft()
            problems.append(
                f'{target}: short {budget.shortfall_in():.2f}" of head over '
                f'{developed_ft:.2f} ft. The route is feasible at '
                f'{feasible:.3f}"/ft and the code wants {grade:.3f}"/ft — raise the '
                "start, lower the tie, or shorten the run by "
                f'{budget.shortfall_in() / grade:.2f} ft')
            continue
        if system == "drain":
            from typehaus.routing.gravity import GravityProfile, apply

            # The profile is built from the ARRIVAL upward — start = root + grade x length
            # — so the route lands exactly on the tie rather than wherever a start
            # elevation happened to put it. Then the flange is prepended as its own vertex
            # at the finished floor, which makes the first leg the vertical drop it is: a
            # closet bend is a fitting, not a grade.
            profile = GravityProfile(
                start_m=root[2] + grade * developed_ft * 0.0254,
                slope_in_per_ft=grade)
            points = apply([(p[0], p[1]) for p in points], profile)
            if origin[2] > points[0][2] + 1e-9:
                points = [(points[0][0], points[0][1], origin[2]), *points]
            notes.append(f'gravity: {grade:.3f}"/ft over {developed_ft:.2f} ft, '
                         f'{budget.slack_in:.2f}" of head to spare; the first leg is the '
                         "flange drop and takes no grade")

        proposals.append((RouteProposal(
            tag=f"{target}-PROPOSED", kind="pipe", points=list(points),
            diameter_m=diameter_m, serves=serves, system=system,
            cost=found.cost, bends=found.bends,
            terms=dict(found.terms) if explain else {}, notes=notes).snapped(), storey))
    return proposals, problems


def _endpoints(model, target: str, mode: str, problems: list[str]):
    """``(origin, root, diameter, serves, storey, system, touch)`` for one target.

    ``touch`` is the set of existing runs this proposal may occupy — see
    :func:`~typehaus.routing.obstacles.hard_prisms`. Everything is None on a refusal, and
    the reason is appended to ``problems`` rather than raised.

    A fixture's origin is its derived drain point at its own floor; a run's is its first
    vertex. The root is the nearest drain run's deepest vertex — which is the honest
    reading of "where does this discharge", and is the same derivation
    ``drain_tie_ins`` uses to link the load.
    """
    from typehaus.resolve.mep import _expected_drain_point

    runs = {r.tag: r for r in model.pipe_runs}
    if mode in ("run", "tree") and target in runs:
        run = runs[target]
        if not run.z_m or len(run.z_m) != len(run.path):
            problems.append(f"{target}: no resolved elevations, so it cannot be routed")
            return (None,) * 7
        origin = (run.path[0][0], run.path[0][1], run.z_m[0])
        found = _discharge(model, run, problems)
        if found is None:
            return (None,) * 7
        root, chain = found
        return (origin, root, run.diameter_m, run.serves, run.storey, run.system,
                frozenset({run.tag, *chain}))

    if mode in ("fixture", "unconnected"):
        point = _expected_drain_point(model, target)
        if point is None:
            problems.append(f"{target}: no resolvable drain point — the same wording "
                            "mep.trap_arm_length uses, and the same cause")
            return (None,) * 7
        element = model.plan.by_tag(target)
        storey = _storey_of(model, target)
        floor_m = next((s.elevation.meters for s in model.plan.storeys
                        if s.tag == storey), 0.0)
        found = _nearest_main(model, point, floor_m, problems, target, exclude=target)
        if found is None:
            return (None,) * 7
        root, parent = found
        del element
        # The runs that already serve this fixture are what the proposal REPLACES, so they
        # are not obstacles to it — and one of them is usually the run the tie point sits
        # on, which is why leaving them hard reports "no lattice node at the root" for a
        # root that is perfectly reachable.
        replaced = {run.tag for run in model.pipe_runs if target in run.serves}
        return ((point[0], point[1], floor_m), root, 0.0508, (target,), storey, "drain",
                frozenset({parent, *replaced}))

    problems.append(f"{target}: not a run in this model")
    return (None,) * 6


def _discharge(model, run, problems: list[str]):
    """``(root point, the whole downstream chain)`` for a run, or None.

    The chain, not just the parent, and that is what makes a tie reachable at all: a
    branch's root vertex usually sits ON its parent, and its parent's root sits on the
    GRANDparent, so leaving the rest of the chain hard walls the route off from the tie it
    is being routed to. ``drain_tie_ins`` derives the topology from the geometry and this
    walks it to the bottom.
    """
    from typehaus.resolve.mep_queries import drain_tie_ins

    ties = drain_tie_ins([r for r in model.pipe_runs if r.system == run.system])
    parent = ties.get(run.tag)
    if parent is None:
        problems.append(f"{run.tag}: nothing downstream of it is derivable, so there is "
                        "no root to route to. Name a --via, or route the parent first")
        return None
    chain, cursor = [], parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    other = next(r for r in model.pipe_runs if r.tag == parent)
    index = min(range(len(other.path)), key=lambda i: other.z_m[i])
    return ((other.path[index][0], other.path[index][1], other.z_m[index]), chain)


def _nearest_main(model, point, floor_m: float, problems: list[str], target: str, *,
                  exclude: str | None = None):
    """The nearest drain run's vertex on this fixture's own floor.

    The vertical gate is ``mep.fixture_drain_reach``'s: a run counts only where it passes
    within two feet below and six inches above the fixture's storey datum. Without it the
    nearest main is whatever happens to lie beneath, two storeys down.

    **A run that already serves this fixture is excluded**, and that is not a nicety: asking
    for a branch to a fixture that has one means asking for a REPLACEMENT, and routing to
    the run being replaced finds its own start and reports a negative feasible slope — a
    true statement about a question nobody asked.
    """
    best = None
    for run in model.pipe_runs:
        if run.system != "drain" or not run.z_m:
            continue
        if exclude is not None and exclude in run.serves:
            continue
        for (x, y), z in zip(run.path, run.z_m, strict=False):
            if not (floor_m - 2.0 * 0.3048 <= z <= floor_m + 0.5 * 0.3048):
                continue
            distance = ((x - point[0]) ** 2 + (y - point[1]) ** 2) ** 0.5
            if best is None or distance < best[0]:
                best = (distance, (x, y, z), run.tag)
    if best is None:
        problems.append(f"{target}: no drain run passes on this fixture's own floor, so "
                        "there is nothing to route it to")
        return None
    return (best[1], best[2])


def _storey_of(model, tag: str) -> str:
    for storey in model.plan.storeys:
        if any(getattr(e, "tag", None) == tag
               for e in model.plan.storey_elements(storey.tag)):
            return storey.tag
    return "main"


def _nearest(graph, point) -> int | None:
    if not graph.nodes:
        return None
    return min(graph.nodes,
               key=lambda n: (abs(n.x - point[0]) + abs(n.y - point[1])
                              + abs(n.z - point[2]))).index


def _root_nodes(graph, root) -> set[int]:
    """Every lattice node on the root's own plan point — a vertical, not a point.

    See :func:`~typehaus.routing.search.shortest_route`: a stack accepts arrivals over a
    range of elevations, and modelling it as one node throws away exactly the margin the
    oracle note's §5 turns on.

    **Plan only, with no z filter**, and that is not a shortcut. A gravity route searches in
    one plane and takes its elevations from the profile afterwards, so the lattice has no
    node at the root's own invert to find; a pressurised one may arrive at any height on the
    trunk it joins. Either way the elevation is settled after the plan route, not during it.
    """
    tolerance = 0.05
    return {node.index for node in graph.nodes
            if abs(node.x - root[0]) < tolerance and abs(node.y - root[1]) < tolerance}
