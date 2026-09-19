"""``--tree``: a main and every fixture it serves, as one directed Steiner tree.

Split out of ``cmd_route.py`` unchanged but for the sizing: every branch used to be 2"
because the CLI held a literal, and now each is sized from its own fixture's drainage load
through :func:`~typehaus.cli.route_support.branch_diameter_m`. The space is inflated at the
**largest** of them, which is the conservative direction and the only one a single search
world can honestly take.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.route_support import (
    _fall,
    _nearest,
    _storey_datum,
    _storey_of,
    branch_diameter_m,
)

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

    fixtures = [tag for tag in main.serves if tag.startswith("FX-")]
    if not fixtures:
        problems.append(f"{target}: serves no fixture, so nothing feeds it. `--run "
                        f"{target}` re-routes the main itself")
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

    replaced = {run.tag for run in model.pipe_runs
                if any(tag in run.serves for tag in points)}

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
            size=size, root_z=root_z, accepted=accepted, via=via, slope=slope,
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
                 via: list[tuple[float, float]], slope: float | None, margin_ft: float,
                 level: str | None, avoid: frozenset[str], touch: frozenset[str],
                 explain: bool, cost: Any, clock: Any
                 ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str]]:
    """One RSPH tree over the branches of a single size. Appends what it routes to
    ``accepted``, so the next (narrower) group can tie onto it."""
    from typehaus.routing.graph import build_graph
    from typehaus.routing.gravity import (
        HeadBudget,
        developed_lengths,
        minimum_slope,
        profile_for,
    )
    from typehaus.routing.gravity_search import (
        GravityProblem,
        GravityRefusal,
        member_constraints,
        sloped_route,
    )
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
                                cost=cost, touch=touch)
        with clock.stage(f"build-graph {size / 0.0254:.3g}in"):
            graph = build_graph(space, terminals_xyz, [root_z])
    except RoutingSpaceTooLarge as exc:
        return [], [f"{label}: {exc}"], []
    if level is not None and level not in space.storeys:
        return [], [f"{target}: --level {level} is not a storey in this model"], []
    clock.lattice(graph)

    goals: set[int] = set()
    for path, _z in accepted:
        goals |= _line_nodes(graph, path)
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
    report = GravityRefusal()

    def search(a_graph, a_space, start, targets):
        problem = GravityProblem(ceiling_m=max(floors.values()), grade_in_per_ft=grade,
                                 diameter_m=size,
                                 required_m={n: inverts[n] for n in targets
                                             if n in inverts})
        return sloped_route(a_graph, a_space, start, targets, problem,
                            constraints=constraints, refusal=report)

    with clock.stage(f"search {size / 0.0254:.3g}in"):
        built = build_tree(graph, space, min(goals), terminals, root_nodes=goals,
                           search=search)
    notices = [f"{label}: {line}" for line in explain_tree(built)] if explain else []
    for tag, shortfall in sorted(built.unserved.items()):
        problems.append(
            f"{tag}: no route in plan to {target} at "
            f'{size / 0.0254:.3g}" — every lane is blocked'
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
        arrival = inverts.get(route_found.nodes[-1])
        if arrival is None:
            problems.append(f"{tag}: it ties onto a branch whose own invert is not "
                            "known, so its head cannot be graded — route that branch "
                            "first with --fixture")
            continue
        budget = HeadBudget(ceiling_m=floors[tag], required_m=arrival,
                            developed_ft=lengths[-1], diameter_m=size)
        profile = profile_for(budget, grade_in_per_ft=grade)
        origin = (legs[0][0], legs[0][1], floors[tag])
        fallen = _fall(legs, origin, budget, grade, tag, problems)
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
    wye is cut at the invert of the thing actually under it.
    """
    best: tuple[float, float] | None = None
    for path, elevations in lines:
        for (ax, ay), az, (bx, by), bz in zip(path, elevations, path[1:], elevations[1:],
                                              strict=False):
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((point[0] - ax) * dx
                                                         + (point[1] - ay) * dy) / span))
            distance = ((ax + t * dx - point[0]) ** 2 + (ay + t * dy - point[1]) ** 2)
            if best is None or distance < best[0]:
                best = (distance, az + t * (bz - az))
        if len(path) == 1 and elevations:
            distance = (path[0][0] - point[0]) ** 2 + (path[0][1] - point[1]) ** 2
            if best is None or distance < best[0]:
                best = (distance, elevations[0])
    return best[1] if best is not None else 0.0


def _line_nodes(graph: Graph, path: Any, tolerance: float = 0.05,
                z_tolerance: float | None = None) -> set[int]:
    """Every lattice node lying on a run's plan polyline — the root of a tree.

    A main is a line and a branch ties in where it meets it. Modelling the root as one
    vertex is what makes a tree look like a manifold: every branch converges on the same
    point, and the wyes stack where no fitting could.

    **``z_tolerance`` is not optional for a pressurised run, and this is the one place the
    supply change can produce a confidently WRONG route.** Plan-only is right for the two
    callers it was written for: a drain searches in one plane, and a vent chase is vertical
    so every elevation on its plan line really is on the pipe. A supply trunk is neither —
    it runs level and rises at both ends, and `falls=False` means the search is fully
    three-dimensional. Without a z gate a branch could "arrive" on the trunk's plan line
    five feet below the trunk and the route would be reported as found; ``_root_nodes(...,
    with_z=True)`` would never catch it, because this returned a non-empty set first.

    Pass a per-vertex z on the polyline (3-tuples) together with a tolerance, and a node
    qualifies only where the line's own interpolated elevation is within it.
    """
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
            if (z_tolerance is not None and len(start) > 2 and len(end) > 2
                    and abs(start[2] + t * (end[2] - start[2])
                            - node.z) > z_tolerance):
                continue
            out.add(node.index)
            break
    return out
