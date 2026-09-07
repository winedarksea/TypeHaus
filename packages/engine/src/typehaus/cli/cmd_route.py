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
    haus route houses/catlin --tree PR-M-S-SUITE-DRAIN     # a main and every fixture on it
    haus route houses/catlin --unconnected                 # one per fixture_drain_reach FAIL
    haus route houses/catlin --run DU-M-ERV-R-KITCH --explain
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph
    from typehaus.routing.proposal import RouteProposal


#: What a fixture branch is proposed at, in metres — 2". The size a branch actually wants
#: is a fixture-unit derivation ``checks/mep`` owns and this package must not import, so
#: the proposal states the common case and leaves the sizing to the person who accepts it:
#: a water closet's own 3" branch is an edit to one literal in what is printed.
_BRANCH_DIAMETER_M = 0.0508


def _load(house: Path | None) -> tuple[Path, Any]:
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


def _storey_datum(model: ResolvedModel, storey: str) -> float:
    return next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)


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


@app.command()
def route(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    run: str | None = typer.Option(
        None, "--run", help="Re-route one authored run, keeping its terminals."),
    fixture: str | None = typer.Option(
        None, "--fixture", help="Propose a branch from one fixture to its nearest main."),
    tree: str | None = typer.Option(
        None, "--tree", help="A main and every fixture it serves, as one Steiner tree."),
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
        targets = [t for t in (run, fixture) if t]

    if tree:
        proposals, problems, notices = _propose_tree(
            model, tree, slope=slope, margin_ft=margin_ft, level=level,
            avoid=frozenset(avoid), via=_points(via), explain=explain)
    else:
        proposals, problems = _propose(
            model, targets, mode=("run" if run else "fixture" if fixture
                                  else "unconnected"),
            slope=slope, margin_ft=margin_ft, level=level,
            avoid=frozenset(avoid), via=_points(via), explain=explain)
        notices = []

    for line in notices:
        console.print(f"[dim]{line}[/dim]")
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


def _propose(model: ResolvedModel, targets: list[str], *, mode: str,
             slope: float | None, margin_ft: float, level: str | None,
             avoid: frozenset[str], via: list[tuple[float, float]], explain: bool
             ) -> tuple[list[tuple[RouteProposal, str]], list[str]]:
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
        notes: list[str] = []
        if system == "drain":
            fallen = _fall(points, origin, budget, grade, target, problems)
            if fallen is None:
                continue
            points, note = fallen
            notes.append(note)

        proposals.append((RouteProposal(
            tag=f"{target}-PROPOSED", kind="pipe", points=list(points),
            diameter_m=diameter_m, serves=serves, system=system,
            cost=found.cost, bends=found.bends,
            terms=dict(found.terms) if explain else {}, notes=notes).snapped(), storey))
    return proposals, problems


def _propose_tree(model: ResolvedModel, target: str, *, slope: float | None,
                  margin_ft: float, level: str | None, avoid: frozenset[str],
                  via: list[tuple[float, float]], explain: bool
                  ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str]]:
    """A main and every fixture it serves, routed as one directed Steiner tree.

    This is the mode :mod:`typehaus.routing.tree` exists for, and the one where the order
    terminals are routed in decides the answer. Routing each fixture on its own — which is
    what ``--fixture`` does, once per fixture — gives every one of them the direct lane and
    proposes a bundle that cannot all be built; RSPH gives the lane to the fixture with the
    least head and makes the rest join what is already there, which is what a wye is.

    **The root is the whole main, not a point.** Goals are every lattice node lying on its
    plan polyline, so a branch ties in where it arrives rather than at whichever end
    happened to be nominated. ``search.shortest_route`` takes a set of goals for exactly
    this.

    Returns ``(proposals, problems, notices)``. The third channel is the tree's own
    ordering and its cost: it is not a problem and it is not source, and printing it as
    either would be a lie about what it is.
    """
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]
    from typehaus.routing.graph import build_graph
    from typehaus.routing.gravity import HeadBudget, minimum_slope
    from typehaus.routing.proposal import RouteProposal
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.trades import pipe as pipe_trade
    from typehaus.routing.tree import Terminal, build_tree
    from typehaus.routing.tree import explain as explain_tree

    problems: list[str] = []
    runs = {r.tag: r for r in model.pipe_runs}
    main = runs.get(target)
    if main is None or main.system != "drain":
        problems.append(f"{target}: not a drain run in this model, so there is no tree "
                        "to build round it")
        return [], problems, []
    if not main.z_m or len(main.z_m) != len(main.path):
        problems.append(f"{target}: no resolved elevations, so there is no invert to tie "
                        "into anywhere along it")
        return [], problems, []

    fixtures = [tag for tag in main.serves if tag.startswith("FX-")]
    if not fixtures:
        problems.append(f"{target}: serves no fixture, so nothing feeds it. `--run "
                        f"{target}` re-routes the main itself")
        return [], problems, []

    diameter_m = _BRANCH_DIAMETER_M

    points: dict[str, tuple[float, float]] = {}
    storeys: dict[str, str] = {}
    floors: dict[str, float] = {}
    for tag in fixtures:
        point = _expected_drain_point(model, tag)
        if point is None:
            problems.append(f"{tag}: no resolvable drain point — the same wording "
                            "mep.trap_arm_length uses, and the same cause")
            continue
        points[tag] = (point[0], point[1])
        storeys[tag] = _storey_of(model, tag)
        floors[tag] = _storey_datum(model, storeys[tag])
    if not points:
        return [], problems, []

    # **One storey per tree.** The branches are searched in a single plane — a drain's z is
    # a derived potential, not a free dimension — so fixtures on two floors are two trees
    # and saying so is the only honest answer. A stack serves both; a plan search does not.
    levels = sorted(set(floors.values()))
    if len(levels) > 1:
        problems.append(
            f"{target}: its fixtures sit on {len(levels)} storeys "
            f"({', '.join(sorted({storeys[t] for t in points}))}) and a branch tree is "
            "searched in one plane. Route each storey's group on its own")
        return [], problems, []
    floor_m = levels[0]

    # **The tie band is ``mep.fixture_drain_reach``'s**, and reusing it is the point: a
    # branch may tie in where the main passes within two feet below and six inches above
    # the fixture floor, and nowhere else. Without it a second-floor lavatory happily ties
    # into the basement leg of its own stack — the plan polyline says the two lines cross,
    # and only the invert says they are twelve feet apart.
    band = (floor_m - 2.0 * 0.3048, floor_m + 0.5 * 0.3048)
    reachable = [((x, y), z) for (x, y), z in zip(main.path, main.z_m, strict=False)
                 if band[0] <= z <= band[1]]
    if not reachable:
        problems.append(
            f"{target}: no vertex of it passes within 2 ft below and 6 in above the "
            f"{storeys[next(iter(points))]} floor, so nothing on that floor can tie into "
            "it — the same band mep.fixture_drain_reach grades against")
        return [], problems, []
    root_z = max(z for _p, z in reachable)
    tie_path = [p for p, _z in reachable]

    replaced = {run.tag for run in model.pipe_runs
                if any(tag in run.serves for tag in points)}
    terminals_xyz = [(x, y, root_z) for x, y in points.values()]
    terminals_xyz.extend((x, y, root_z) for x, y in tie_path)
    terminals_xyz.extend((p[0], p[1], root_z) for p in via)
    try:
        space = build_space(model, radius_m=pipe_trade.radius_m(diameter_m),
                            terminals=terminals_xyz, margin_ft=margin_ft, avoid=avoid,
                            touch=frozenset({target, *replaced}))
    except RoutingSpaceTooLarge as exc:
        problems.append(f"{target}: {exc}")
        return [], problems, []
    if level is not None and level not in space.storeys:
        problems.append(f"{target}: --level {level} is not a storey in this model")
        return [], problems, []

    graph = build_graph(space, terminals_xyz, [root_z])
    goals = _line_nodes(graph, tie_path)
    if not goals:
        problems.append(f"{target}: no lattice node lies on the reachable part of the "
                        "main, so there is nowhere to tie into. Narrow --margin or name "
                        "a --via on it")
        return [], problems, []

    grade = slope if slope is not None else minimum_slope(diameter_m)
    terminals = []
    for tag, (x, y) in points.items():
        node = _nearest(graph, (x, y, root_z))
        if node is None:
            problems.append(f"{tag}: no lattice node at its drain point")
            continue
        # A **lower bound** on the developed length, and stated as one: the ordering key is
        # slack, slack needs a length, and the length is not known until the route is. A
        # Manhattan estimate over-states every terminal's slack by the same kind of amount,
        # which is all an ORDER needs; the real budget is rebuilt below and can still
        # refuse. §5 of the oracle note is explicit that length is not a proxy for slack —
        # this uses it to order the question, never to answer it.
        reach = min(abs(x - mx) + abs(y - my) for mx, my in tie_path) / 0.3048
        terminals.append(Terminal(tag=tag, node=node, budget=HeadBudget(
            ceiling_m=floors[tag], required_m=root_z, developed_ft=reach,
            diameter_m=diameter_m)))
    if not terminals:
        return [], problems, []

    built = build_tree(graph, space, min(goals), terminals, root_nodes=goals)
    notices = [f"{target}: {line}" for line in explain_tree(built)] if explain else []
    for tag, shortfall in sorted(built.unserved.items()):
        problems.append(
            f"{tag}: no route in plan to {target} — every lane is blocked"
            if shortfall == float("inf") else
            f'{tag}: short {shortfall:.2f}" of head to {target} at the minimum grade')

    # **A terminal's required invert is the invert of whatever it lands on**, and in RSPH
    # that is usually not the main: the second branch routed ties into the first. So the
    # inverts are carried forward node by node as the tree grows — seeded from the main's
    # own profile, then extended by each branch's — and a wye onto a branch is graded
    # against the branch. Grading it against the main instead reads a tie twelve feet away
    # and calls a route feasible that is not.
    from typehaus.routing.gravity import developed_lengths, profile_for

    inverts = {index: _invert_at(main, (graph.nodes[index].x, graph.nodes[index].y, 0.0))
               for index in goals}
    proposals: list[tuple[RouteProposal, str]] = []
    for tag, _slack in built.order:
        route_found = built.routes.get(tag)
        if route_found is None:
            continue
        legs = route_found.polyline()
        lengths = developed_lengths(route_found.points)
        arrival = inverts.get(route_found.nodes[-1])
        if arrival is None:
            problems.append(f"{tag}: it ties onto a branch whose own invert is not "
                            "known, so its head cannot be graded — route that branch "
                            "first with --fixture")
            continue
        budget = HeadBudget(ceiling_m=floors[tag], required_m=arrival,
                            developed_ft=lengths[-1], diameter_m=diameter_m)
        profile = profile_for(budget, grade_in_per_ft=grade)
        origin = (legs[0][0], legs[0][1], floors[tag])
        fallen = _fall(legs, origin, budget, grade, tag, problems)
        if fallen is None:
            continue
        fell, note = fallen
        if profile is not None:
            for index, length in zip(route_found.nodes, lengths, strict=False):
                inverts.setdefault(index, profile.invert_at(length))
        proposals.append((RouteProposal(
            tag=f"{tag}-PROPOSED", kind="pipe", points=list(fell),
            diameter_m=diameter_m, serves=(tag,), system="drain",
            cost=route_found.cost, bends=route_found.bends,
            terms=dict(route_found.terms) if explain else {},
            notes=[note]).snapped(), storeys[tag]))
    return proposals, problems, notices


def _invert_at(run: Any, point: tuple[float, float, float]) -> float:
    """The main's own invert where a branch arrives, interpolated along its path.

    Taking the shallowest invert everywhere would price every branch against the hardest
    tie on the main, and taking the deepest would price it against a tie it may not reach.
    The invert at the arrival is neither: it is the number the wye is actually cut at.
    """
    best: tuple[float, float] | None = None
    for (ax, ay), az, (bx, by), bz in zip(run.path, run.z_m, run.path[1:], run.z_m[1:],
                                          strict=False):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        t = 0.0 if span <= 0 else max(0.0, min(1.0, ((point[0] - ax) * dx
                                                     + (point[1] - ay) * dy) / span))
        near = (ax + t * dx, ay + t * dy)
        distance = (near[0] - point[0]) ** 2 + (near[1] - point[1]) ** 2
        if best is None or distance < best[0]:
            best = (distance, az + t * (bz - az))
    return best[1] if best is not None else max(run.z_m)


def _line_nodes(graph: Graph, path: Any, tolerance: float = 0.05) -> set[int]:
    """Every lattice node lying on a run's plan polyline — the root of a tree.

    A main is a line and a branch ties in where it meets it. Modelling the root as one
    vertex is what makes a tree look like a manifold: every branch converges on the same
    point, and the wyes stack where no fitting could.
    """
    out: set[int] = set()
    # A stack's reachable part is ONE vertex — its head — so the degenerate polyline is the
    # common case here rather than an edge case, and zipping it against its own tail would
    # silently produce no goals at all.
    segments = (list(zip(path, path[1:], strict=False)) if len(path) > 1
                else [(path[0], path[0])])
    for node in graph.nodes:
        for (ax, ay), (bx, by) in segments:
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((node.x - ax) * dx
                                                         + (node.y - ay) * dy) / span))
            if ((ax + t * dx - node.x) ** 2
                    + (ay + t * dy - node.y) ** 2) <= tolerance ** 2:
                out.add(node.index)
                break
    return out


def _fall(points: list[tuple[float, float, float]],
          origin: tuple[float, float, float], budget: Any, grade: float,
          target: str, problems: list[str]
          ) -> tuple[list[tuple[float, float, float]], str] | None:
    """Put a found plan route on its gravity profile, or refuse and say by how much.

    The profile comes from ``gravity.profile_for`` rather than from a start elevation, so
    it is built from the ARRIVAL upward and the route lands exactly on the tie. Then the
    flange is prepended as its own vertex at the finished floor, which makes the first leg
    the vertical drop it is: a closet bend is a fitting, not a grade.

    A refusal names the grade the route WOULD hold. "No feasible route" is not actionable;
    "this needs 0.19"/ft and the code wants 0.25"" says how much shorter, higher or lower
    the problem has to get. That second refusal — a ``--slope`` steeper than the code
    minimum, which ``HeadBudget.feasible`` does not grade because it asks about the
    minimum — is why the profile is asked rather than the budget.
    """
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
    if origin[2] > fallen[0][2] + 1e-9:
        fallen = [(fallen[0][0], fallen[0][1], origin[2]), *fallen]
    return fallen, (f'gravity: {grade:.3f}"/ft over {budget.developed_ft:.2f} ft, '
                    f'{budget.slack_in:.2f}" of head to spare; the first leg is the '
                    "flange drop and takes no grade")


def _endpoints(model: ResolvedModel, target: str, mode: str,
               problems: list[str]) -> tuple[Any, ...]:
    """``(origin, root, diameter, serves, storey, system, touch)`` for one target.

    ``touch`` is the set of existing runs this proposal may occupy — see
    :func:`~typehaus.routing.obstacles.hard_prisms`. Everything is None on a refusal, and
    the reason is appended to ``problems`` rather than raised.

    A fixture's origin is its derived drain point at its own floor; a run's is its first
    vertex. The root is the nearest drain run's deepest vertex — which is the honest
    reading of "where does this discharge", and is the same derivation
    ``drain_tie_ins`` uses to link the load.
    """
    # Imported from the module that OWNS the derivation rather than re-derived: the same
    # point `mep.trap_arm_length` and `mep.fixture_drain_reach` measure from, so a router
    # aimed at a different point from the checks that judge it is impossible by construction.
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]

    runs = {r.tag: r for r in model.pipe_runs}
    if mode == "run" and target in runs:
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
        storey = _storey_of(model, target)
        floor_m = next((s.elevation.meters for s in model.plan.storeys
                        if s.tag == storey), 0.0)
        near = _nearest_main(model, point, floor_m, problems, target, exclude=target)
        if near is None:
            return (None,) * 7
        root, parent = near
        # The runs that already serve this fixture are what the proposal REPLACES, so they
        # are not obstacles to it — and one of them is usually the run the tie point sits
        # on, which is why leaving them hard reports "no lattice node at the root" for a
        # root that is perfectly reachable.
        replaced = {run.tag for run in model.pipe_runs if target in run.serves}
        return ((point[0], point[1], floor_m), root, _BRANCH_DIAMETER_M, (target,),
                storey, "drain", frozenset({parent, *replaced}))

    problems.append(f"{target}: not a run in this model")
    return (None,) * 7


def _discharge(model: ResolvedModel, run: Any,
               problems: list[str]) -> tuple[tuple[float, float, float], list[str]] | None:
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
    chain: list[str] = []
    cursor: str | None = parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    other = next(r for r in model.pipe_runs if r.tag == parent)
    z = other.z_m or ()
    if len(z) != len(other.path):
        problems.append(f"{run.tag}: its discharge {parent} carries no resolved "
                        "elevations, so there is no invert to tie into")
        return None
    index = min(range(len(other.path)), key=lambda i: z[i])
    return ((other.path[index][0], other.path[index][1], z[index]), chain)


def _nearest_main(model: ResolvedModel, point: tuple[float, float], floor_m: float,
                  problems: list[str], target: str, *, exclude: str | None = None
                  ) -> tuple[tuple[float, float, float], str] | None:
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


def _storey_of(model: ResolvedModel, tag: str) -> str:
    for storey in model.plan.storeys:
        if any(getattr(e, "tag", None) == tag
               for e in model.plan.storey_elements(storey.tag)):
            return str(storey.tag)
    return "main"


def _nearest(graph: Graph, point: tuple[float, float, float]) -> int | None:
    if not graph.nodes:
        return None
    return int(min(graph.nodes,
                   key=lambda n: (abs(n.x - point[0]) + abs(n.y - point[1])
                                  + abs(n.z - point[2]))).index)


def _root_nodes(graph: Graph, root: tuple[float, float, float]) -> set[int]:
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
