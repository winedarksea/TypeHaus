"""Route a drain main's fixtures as one directed Steiner tree.

Each branch uses its fixture load's diameter; the shared space uses the largest radius.
Workflow: docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.route_fall import _fall
from typehaus.cli.route_support import (
    _nearest,
    _storey_datum,
    _storey_of,
    branch_diameter_m,
)
from typehaus.model.spatial import Fixture

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph
    from typehaus.routing.proposal import RouteProposal


def _propose_tree(model: ResolvedModel, target: str, *, slope: float | None,
                  margin_ft: float, level: str | None, avoid: frozenset[str],
                  via: list[tuple[float, float]], explain: bool, cost: Any = None,
                  timing: list[str] | None = None
                  ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                             list[Any]]:
    """Return (proposal/storey pairs, problems, notices, structured refusals).

    The whole main is the goal line, so branches may join at different stations. This is one
    coordinated tree; independent fixture searches cannot share the resulting branches."""
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]
    from typehaus.routing.timing import Timer

    problems: list[str] = []
    clock = Timer(target, enabled=timing is not None)
    runs = {r.tag: r for r in model.pipe_runs}
    main = runs.get(target)
    if main is None or main.system != "drain":
        problems.append(f"{target}: not a drain run in this model, so there is no tree "
                        "to build round it")
        return [], problems, [], []
    if not main.z_m or len(main.z_m) != len(main.path):
        problems.append(f"{target}: no resolved elevations, so there is no invert to tie "
                        "into anywhere along it")
        return [], problems, [], []

    fixtures = [tag for tag in main.serves if isinstance(model.plan.by_tag(tag), Fixture)]
    if not fixtures:
        problems.append(f"{target}: serves no fixture, so nothing feeds it. `--run "
                        f"{target}` re-routes the main itself")
        return [], problems, [], []
    # `--level` names one storey's group when the stack serves more than one: the tree is
    # then routed for those fixtures alone, which is the "each storey's group on its own"
    # the refusal below asks for.
    if level is not None:
        fixtures = [tag for tag in fixtures if _storey_of(model, tag) == level]
        if not fixtures:
            problems.append(f"{target}: no fixture it serves sits on the {level} storey")
            return [], problems, [], []

    points: dict[str, tuple[float, float]] = {}
    storeys: dict[str, str] = {}
    floors: dict[str, float] = {}
    diameters: dict[str, float] = {}
    for tag in fixtures:
        point = _expected_drain_point(model, tag)
        if point is None:
            problems.append(f"{tag}: no resolvable drain point — the same wording "
                            "mep.trap_arm_length uses, and the same cause")
            continue
        size = branch_diameter_m(model, (tag,), problems, tag)
        if size is None:
            continue
        points[tag] = (point[0], point[1])
        diameters[tag] = size
        storeys[tag] = _storey_of(model, tag)
        floors[tag] = _storey_datum(model, storeys[tag])
    if not points:
        return [], problems, [], []

    # **One storey per tree.** The branches are searched in a single plane — a drain's z is
    # a derived potential, not a free dimension — so fixtures on two floors are two trees
    # and saying so is the only honest answer. A stack serves both; a plan search does not.
    levels = sorted(set(floors.values()))
    if len(levels) > 1:
        problems.append(
            f"{target}: its fixtures sit on {len(levels)} storeys "
            f"({', '.join(sorted({storeys[t] for t in points}))}) and a branch tree is "
            "searched in one plane. Route each storey's group on its own")
        return [], problems, [], []
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
        return [], problems, [], []
    root_z = max(z for _p, z in reachable)
    tie_path = [p for p, _z in reachable]

    replaced = {run.tag for run in model.pipe_runs  # drains: never the basins' supplies
                if run.system == "drain" and any(tag in run.serves for tag in points)}

    # **One world per branch SIZE, widest first.** A tree used to be searched in a single
    # world inflated at one 2" literal; now every branch is sized from its own drainage
    # load and the sizes differ — catlin's suite bath is 3" / 1 1/2" / 1 1/4". Inflating
    # one shared world at the widest walls the narrow branches out of lanes they fit
    # perfectly well (the suite bath loses 1,355 of 2,508 lattice nodes at 3"), and
    # inflating it at the narrowest proposes a 3" lane verified at 1 1/4", which is the
    # dishonest direction. So each size gets its own lattice.
    #
    # RSPH still crosses the groups: a narrower branch may tie onto a wider one already
    # accepted, which is what a wye is and what §5's ordering argument turns on. What it
    # may NOT do is tie onto a branch of its own size routed in a later group, because
    # there is no later group — the sizes run widest first for exactly that reason.
    accepted: list[tuple[list[tuple[float, float]], list[float]]] = [
        (tie_path, [z for _p, z in reachable])]
    from typehaus.cli.route_tree_branches import Branches

    branches = Branches.of_main(target, [(x, y, z) for (x, y), z in reachable])
    proposals: list[tuple[RouteProposal, str]] = []
    notices: list[str] = []
    sizes = sorted({diameters[tag] for tag in points}, reverse=True)
    if len(sizes) > 1 and explain:
        spelled = ", ".join('%.3g"' % (d / 0.0254) for d in sizes)
        notices.append(f"{target}: {len(sizes)} branch sizes ({spelled}), so one lattice "
                       "each, widest first — a narrower branch may tie onto a wider one, "
                       "never the other way round")

    for size in sizes:
        group = sorted(tag for tag in points if diameters[tag] == size)
        made, group_problems, group_notices = _route_group(
            model, target, group, points=points, floors=floors, storeys=storeys,
            size=size, root_z=root_z, accepted=accepted, branches=branches, via=via,
            slope=slope,
            margin_ft=margin_ft, level=level, avoid=avoid,
            touch=frozenset({target, *replaced}), explain=explain, cost=cost,
            clock=clock)
        proposals.extend(made)
        problems.extend(group_problems)
        notices.extend(group_notices)
    if timing is not None:
        timing.extend(clock.lines())
    # No refusals channel yet: a tree refusal is reported per-terminal inside the RSPH
    # loop and has no single blocked terminal to classify. The shape matches ``_propose``
    # so the caller does not branch on which proposer it called.
    return proposals, problems, notices, []


def _route_group(model: ResolvedModel, target: str, group: list[str], *,
                 points: dict[str, tuple[float, float]], floors: dict[str, float],
                 storeys: dict[str, str], size: float, root_z: float,
                 accepted: list[tuple[list[tuple[float, float]], list[float]]],
                 branches: Any, via: list[tuple[float, float]], slope: float | None,
                 margin_ft: float,
                 level: str | None, avoid: frozenset[str], touch: frozenset[str],
                 explain: bool, cost: Any, clock: Any
                 ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str]]:
    """One RSPH tree over the branches of a single size. Appends what it routes to
    ``accepted``, so the next (narrower) group can tie onto it."""
    from typehaus.routing.fitting_room import fitting_terms
    from typehaus.routing.graph import build_graph
    from typehaus.routing.gravity import (
        HeadBudget,
        developed_lengths,
        minimum_slope,
        profile_for,
    )
    from typehaus.routing.gravity_band import (
        band_obstacles,
        member_constraints,
        prepare_falling,
        terminal_pardons,
    )
    from typehaus.routing.gravity_search import GravityProblem, GravityRefusal, sloped_route
    from typehaus.routing.proposal import RouteProposal
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.trades import pipe as pipe_trade
    from typehaus.routing.tree import Terminal, build_tree
    from typehaus.routing.tree import explain as explain_tree

    problems: list[str] = []
    label = f'{target} @ {size / 0.0254:.3g}"'
    terminals_xyz = [(*points[tag], root_z) for tag in group]
    for path, _z in accepted:
        terminals_xyz.extend((x, y, root_z) for x, y in path)
    terminals_xyz.extend((p[0], p[1], root_z) for p in via)
    try:
        with clock.stage(f"build-space {size / 0.0254:.3g}in"):
            space = build_space(model, radius_m=pipe_trade.radius_m(size),
                                terminals=terminals_xyz, margin_ft=margin_ft, avoid=avoid,
                                cost=cost, touch=touch,
                                cavity_radius_m=pipe_trade.cavity_radius_m(size, "drain"))
        # Inverts lie between the main's tie and the highest fixture floor (§8a).
        prepare_falling(space, (root_z, max(floors[tag] for tag in group)), model)
        with clock.stage(f"build-graph {size / 0.0254:.3g}in"):
            graph = build_graph(space, terminals_xyz, [root_z])
    except RoutingSpaceTooLarge as exc:
        return [], [f"{label}: {exc}"], []
    if level is not None and level not in space.storeys:
        return [], [f"{target}: --level {level} is not a storey in this model"], []
    clock.lattice(graph)
    # Searched once per terminal: the memo pays here (space.py), and so does a shared heel
    # memo, since both read hard prisms only and those are fixed within one size group.
    space.reuse = True
    heels: dict[tuple[int, int, int], bool] = {}

    goals: set[int] = set()
    for path, _z in accepted:  # on the line, not near it: its vertices are lattice lines (§13)
        goals |= _line_nodes(graph, path, TIE_TOLERANCE_M)
    if not goals:
        return [], [f"{label}: no lattice node lies on the reachable part of the main or "
                    "on any branch already accepted, so there is nowhere to tie into. "
                    "Narrow --margin or name a --via on it"], []

    terminals = []
    for tag in group:
        x, y = points[tag]
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
        reach = min(abs(x - mx) + abs(y - my)
                    for path, _z in accepted for mx, my in path) / 0.3048
        terminals.append(Terminal(tag=tag, node=node, budget=HeadBudget(
            ceiling_m=floors[tag], required_m=root_z, developed_ft=reach,
            diameter_m=size)))
    if not terminals:
        return [], problems, []

    # **The inverts before the search, not after it.** A terminal's required arrival is the
    # invert of whatever it lands on, and the sloped search needs that number as its GOAL
    # TEST rather than as a post-check — see the drain note's §8. Computing it afterwards is
    # what "search flat, slope after" meant here.
    inverts = {index: _invert_of(accepted,
                                 (graph.nodes[index].x, graph.nodes[index].y))
               for index in goals}
    grade = slope if slope is not None else minimum_slope(size)
    constraints = member_constraints(
        model, graph, (min(inverts.values()), max(floors.values())))
    reports: dict[str, GravityRefusal] = {}  # per terminal: a shared one reads as each's
    arrivals: dict[str, float] = {}  # a branch entering a plumb drop ends at its own height
    tag_at = {t.node: t.tag for t in terminals}
    owners = branches.owners(graph)
    base_banded = list(space.banded)

    def search(a_graph, a_space, start, targets):
        # Only a line that still carries the load at its size, all the way down (§13).
        tag = tag_at.get(start, "")
        report = reports[tag] = GravityRefusal()
        targets = {n for n in targets
                   if n not in owners or branches.admits(model, owners[n], tag)}
        if not targets:
            report.notes.append("every branch in reach is full at its size")
            return None
        a_space.banded = base_banded + branches.prisms(a_space.radius_m,
                                                       a_space.clearance_m)
        nipple, heel = fitting_terms(a_space.cost, "drain", size, None,
                                     pipe_trade.radius_m(size))
        ceiling = max(floors.values())
        required = {n: inverts[n] for n in targets if n in inverts}
        pardons = terminal_pardons(a_space, a_graph, {**required, start: ceiling}, start,
                                   frozenset({target}))
        for n in required:  # a tie is pardoned the branch it lies on, never a neighbour's wye
            if owners.get(n, 0):
                own = f"{branches.lines[owners[n]].tag}-PROPOSED"
                pardons[n] = pardons.get(n, frozenset()) | {own}
        obstacles = band_obstacles(a_space, a_graph, pardons, start)
        # A goal whose own plumb is inside a prism cannot be tied at: drop it, so the head
        # bound is taken over the ties that are really there (§13).
        live = {n for n, z in required.items()
                if not any(z0 < z < z1 for _a, _b, z0, z1, _t in obstacles(n, n))}
        if not live:
            report.notes.append("every tie in reach is inside something")
            return None
        targets = {n for n in targets if n in live or n not in inverts}
        problem = GravityProblem(ceiling_m=ceiling, grade_in_per_ft=grade,
                                 diameter_m=2.0 * pipe_trade.radius_m(size),
                                 required_m={n: required[n] for n in live},
                                 nipple_m=nipple, heel_m=heel)
        found = sloped_route(a_graph, a_space, start, targets, problem,
                             constraints=constraints, refusal=report, obstacles=obstacles,
                             heels=heels)
        if found is not None and found.nodes[-1] in inverts:
            # Its own inverts, now: the next branch may tie onto this one (§13).
            lengths = developed_lengths(found.points)
            arrival = inverts[found.nodes[-1]]
            end = a_graph.nodes[found.nodes[-1]]
            top = branches.drop_top(owners.get(found.nodes[-1], 0), (end.x, end.y))
            if top is not None and found.start_m is not None:
                # Into the side of that plumb drop at its own height: no drop of its own.
                arrival = arrivals[tag] = min(top, max(
                    arrival, found.start_m - problem.fall_over(lengths[-1])))
            # An "over" route runs at its start and drops plumb into the tie at the end.
            over = (found.start_m is not None
                    and found.start_m > arrival + problem.fall_over(lengths[-1]) + 1e-6)
            for index, length in zip(found.nodes, lengths, strict=False):
                inverts.setdefault(index, found.start_m - problem.fall_over(length)
                                   if over and index != found.nodes[-1]
                                   else arrival + problem.fall_over(lengths[-1] - length))
            laid = [(a_graph.nodes[n].x, a_graph.nodes[n].y, inverts[n]) for n in found.nodes]
            laid[-1] = (*laid[-1][:2], arrival)
            if over:  # its plumb drop is a leg of its own
                laid.insert(-1, (*laid[-1][:2], found.start_m - problem.fall_over(lengths[-1])))
            line = branches.add(tag, size, laid, owners.get(found.nodes[-1], 0))
            for index in found.nodes:
                owners.setdefault(index, line)
            if over:  # its plumb drop now stands on the tie: a later branch enters it there
                owners[found.nodes[-1]] = line
        return found

    with clock.stage(f"search {size / 0.0254:.3g}in"):
        built = build_tree(graph, space, min(goals), terminals, root_nodes=goals,
                           search=search)
    notices = [f"{label}: {line}" for line in explain_tree(built)] if explain else []
    for tag, shortfall in sorted(built.unserved.items()):
        problems.append(
            f"{tag}: no route to {target} at "
            f'{size / 0.0254:.3g}" — '
            + _refusal(reports.get(tag))
            if shortfall == float("inf") else
            f'{tag}: short {shortfall:.2f}" of head to {target} at the minimum grade')

    # **A terminal's required invert is the invert of whatever it lands on**, and in RSPH
    # that is usually not the main: the second branch routed ties into the first. So the
    # inverts are carried forward node by node as the tree grows — seeded from every line
    # already accepted, then extended by each branch's own profile — and a wye onto a
    # branch is graded against the branch. Grading it against the main instead reads a tie
    # twelve feet away and calls a route feasible that is not.
    made: list[tuple[RouteProposal, str]] = []
    for tag, _slack in built.order:
        route_found = built.routes.get(tag)
        if route_found is None:
            continue
        legs = route_found.polyline()
        lengths = developed_lengths(route_found.points)
        arrival = arrivals.get(tag, inverts.get(route_found.nodes[-1]))
        if arrival is None:
            problems.append(f"{tag}: it ties onto a branch whose own invert is not "
                            "known, so its head cannot be graded — route that branch "
                            "first with --fixture")
            continue
        budget = HeadBudget(ceiling_m=floors[tag], required_m=arrival,
                            developed_ft=lengths[-1], diameter_m=size)
        profile = profile_for(budget, grade_in_per_ft=grade)
        origin = (legs[0][0], legs[0][1], floors[tag])
        fallen = _fall(legs, origin, budget, grade, tag, problems,
                       start_m=route_found.start_m)
        if fallen is None:
            continue
        fell, note = fallen
        if profile is not None:
            for index, length in zip(route_found.nodes, lengths, strict=False):
                inverts.setdefault(index, profile.invert_at(length))
        proposal = RouteProposal(
            tag=f"{tag}-PROPOSED", kind="pipe", points=list(fell), diameter_m=size,
            serves=(tag,), system="drain", cost=route_found.cost,
            bends=route_found.bends,
            terms=dict(route_found.terms) if explain else {}, notes=[note]).snapped()
        made.append((proposal, storeys[tag]))
        accepted.append(([(x, y) for x, y, _z in proposal.points],
                         [z for _x, _y, z in proposal.points]))
    return made, problems, notices


def _invert_of(lines: list[tuple[list[tuple[float, float]], list[float]]],
               point: tuple[float, float]) -> float:
    """The invert of whichever accepted line passes nearest this plan point.

    Nearest, because a goal node may lie on the main and on a branch already accepted at
    once — a branch ties onto the main, so their nodes coincide where it does — and the
    wye is cut at the invert of the thing actually under it. Where two vertices share the
    point — a plumb drop — the lowest: a branch may enter the drop anywhere down its side.
    """
    best: tuple[float, float] | None = None

    def better(distance: float, z: float) -> bool:
        return best is None or distance < best[0] - 1e-9 or (
            distance <= best[0] + 1e-9 and z < best[1])

    for path, elevations in lines:
        for (ax, ay), az, (bx, by), bz in zip(path, elevations, path[1:], elevations[1:],
                                              strict=False):
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((point[0] - ax) * dx
                                                         + (point[1] - ay) * dy) / span))
            distance = ((ax + t * dx - point[0]) ** 2 + (ay + t * dy - point[1]) ** 2)
            if better(distance, az + t * (bz - az)):
                best = (distance, az + t * (bz - az))
        if len(path) == 1 and elevations:
            distance = (path[0][0] - point[0]) ** 2 + (path[0][1] - point[1]) ** 2
            if better(distance, elevations[0]):
                best = (distance, elevations[0])
    return best[1] if best is not None else 0.0


def _refusal(report: Any) -> str:
    if report is not None and report.reached:
        return report.sentence()
    return "; ".join(report.notes) if report is not None and report.notes else (
        "every lane is blocked")


#: A tie is ON a laid line: each group's lattice has lines through every accepted vertex,
#: so this only covers the 1/16" snap. Two inches made a band of near-ties a branch could
#: chain through and a wye that missed its collector's centreline (§13).
TIE_TOLERANCE_M = 0.0032


def _line_nodes(graph: Graph, path: Any, tolerance: float = 0.05,
                z_tolerance: float | None = None) -> set[int]:
    """Nodes on a goal polyline, optionally gated by its interpolated vertex elevations.

    A supply feeder requires per-vertex z and z_tolerance: plan-only arrival could land below
    its horizontal leg. Gravity plan searches need no z gate."""
    out: set[int] = set()
    # A stack's reachable part is ONE vertex — its head — so the degenerate polyline is the
    # common case here rather than an edge case, and zipping it against its own tail would
    # silently produce no goals at all.
    segments = (list(zip(path, path[1:], strict=False)) if len(path) > 1
                else [(path[0], path[0])])
    for node in graph.nodes:
        for start, end in segments:
            (ax, ay), (bx, by) = start[:2], end[:2]
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((node.x - ax) * dx
                                                         + (node.y - ay) * dy) / span))
            if ((ax + t * dx - node.x) ** 2
                    + (ay + t * dy - node.y) ** 2) > tolerance ** 2:
                continue
            if z_tolerance is not None and len(start) > 2 and len(end) > 2:
                # A RISER — one plan point, two elevations — holds every z between its ends;
                # interpolating at t=0 would put its whole rise at its foot.
                low, high = ((min(start[2], end[2]), max(start[2], end[2])) if span <= 0
                             else (start[2] + t * (end[2] - start[2]),) * 2)
                if not low - z_tolerance <= node.z <= high + z_tolerance:
                    continue
            out.add(node.index)
            break
    return out
