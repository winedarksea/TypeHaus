"""One size group of a drain tree: RSPH over the branches of one diameter, with rip-up.

Split out of ``cmd_route_tree`` (which keeps ``_propose_tree``, ``_line_nodes`` and
``TIE_TOLERANCE_M``). ``_Ledger`` is the group's laid state as ``routing/tree_ripup`` sees
it: lift a branch, roll a trial back exactly (``mep_tree_ripup_basis.md`` §1)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.cmd_route_tree import TIE_TOLERANCE_M, _line_nodes
from typehaus.cli.route_fall import _fall
from typehaus.cli.route_support import _nearest

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal

_PROPOSED = "-PROPOSED"

#: Labels each search inside a rip-up trial may spend (note §1 P5 caps their number, this
#: their cost). A terminal's own search keeps the full budget, so its refusal is the one it
#: always was; a trial that stops here is a trial that failed, and is rolled back. On catlin
#: a successful 1 1/2" branch took 13 to 604k labels, a refusal walks 1.5M (~50-130 s).
PROBE_LABELS = 200_000
#: Re-searches under a weir lowered one 1/16" step each, when a lane misses the grid.
_SNAP_RETRIES = 2
_SNAP_M = 0.0625 * 0.0254


class _Ledger:
    """What the group's searches have laid: lines, tie owners, inverts and arrivals.

    Each lay is recorded (its nodes, whether it ends in a plumb drop, the inverts it added)
    so a lift can be undone line by line and a trial rolled back whole."""

    def __init__(self, branches: Any, owners: dict[int, int], inverts: dict[int, float],
                 reports: dict[str, Any]) -> None:
        self.branches = branches
        self.base_owners = dict(owners)  # the group's start: the main and wider lines
        self.owners = owners
        self.inverts = inverts
        self.arrivals: dict[str, float] = {}
        self.reports = reports
        #: Per search, the laid lines it found full or standing in its ties (§1 P1).
        self.refused_ties: dict[str, set[str]] = {}
        self.laid: dict[str, tuple[list[int], bool, tuple[int, ...]]] = {}
        self.trial = False  # between a lift and its settle: every search is the trial's
        #: A search that found a lane its profile cannot hold on the 1/16" grid: the reason.
        self.unsnapped: dict[str, str] = {}

    def settle(self) -> None:
        self.trial = False

    def lay(self, tag: str, size: float, points: list, nodes: list[int], over: bool,
            added: set[int]) -> None:
        line = self.branches.add(tag, size, points, self.owners.get(nodes[-1], 0))
        self.laid[tag] = (list(nodes), over, tuple(added))
        self._own(line, nodes, over)

    def _own(self, line: int, nodes: list[int], over: bool) -> None:
        for index in nodes:
            self.owners.setdefault(index, line)
        if over:  # its plumb drop now stands on the tie: a later branch enters it there
            self.owners[nodes[-1]] = line

    def blockers(self, tag: str) -> list[str]:
        """The laid lines ``tag``'s refusal names: its tightest blocker when that is one of
        this tree's proposals; failing any blocker, the lines it found full or in its ties."""
        report = self.reports.get(tag)
        if tag in self.unsnapped:  # the grid refused it, not a sibling
            return []
        if report is not None and report.tightest is not None:
            what = report.tightest[0].split(" ")[0]
            return [what[:-len(_PROPOSED)]] if what.endswith(_PROPOSED) else []
        return sorted(self.refused_ties.get(tag, ()))

    def snapshot(self) -> Any:
        return (self.branches.copy(), dict(self.owners), dict(self.inverts),
                dict(self.arrivals), dict(self.reports), dict(self.laid),
                dict(self.unsnapped))

    def restore(self, state: Any) -> None:
        branches, owners, inverts, arrivals, reports, laid, unsnapped = state
        self.branches.lines = branches.lines
        for mine, saved in ((self.owners, owners), (self.inverts, inverts),
                            (self.arrivals, arrivals), (self.reports, reports),
                            (self.laid, laid), (self.unsnapped, unsnapped)):
            mine.clear()
            mine.update(saved)

    def lift(self, tag: str) -> list[str]:
        self.trial = True
        index = self.branches.index_of(tag)
        if index is None:
            return []
        lifted = self.branches.remove(index)
        for gone in lifted:
            _nodes, _over, added = self.laid.pop(gone, ([], False, ()))
            for node in added:
                self.inverts.pop(node, None)
            self.arrivals.pop(gone, None)
        self.owners.clear()
        self.owners.update(self.base_owners)
        for laid_tag, (nodes, over, _added) in self.laid.items():  # lay order survives
            line = self.branches.index_of(laid_tag)
            if line is not None:
                self._own(line, nodes, over)
        return lifted


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
    tag_at = {t.node: t.tag for t in terminals}
    ledger = _Ledger(branches, branches.owners(graph), inverts, reports)
    owners = ledger.owners  # cleared and refilled in place by a lift, never rebound
    base_banded = list(space.banded)

    def search(a_graph, a_space, start, targets):
        # Only a line that still carries the load at its size, all the way down (§13).
        tag = tag_at.get(start, "")
        report = reports[tag] = GravityRefusal()
        ledger.unsnapped.pop(tag, None)
        refused = ledger.refused_ties[tag] = set()
        full = {n for n in targets if n in owners and not branches.admits(model, owners[n], tag)}
        refused |= {branches.lines[owners[n]].tag for n in full}
        targets = set(targets) - full
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
                own = f"{branches.lines[owners[n]].tag}{_PROPOSED}"
                pardons[n] = pardons.get(n, frozenset()) | {own}
        obstacles = band_obstacles(a_space, a_graph, pardons, start)
        # A goal whose own plumb is inside a prism cannot be tied at: drop it, so the head
        # bound is taken over the ties that are really there (§13).
        inside = {n: [t for _a, _b, z0, z1, t in obstacles(n, n) if z0 < z < z1]
                  for n, z in required.items()}
        refused |= {t[:-len(_PROPOSED)] for hits in inside.values() for t in hits
                    if t.endswith(_PROPOSED)}
        live = {n for n, hits in inside.items() if not hits}
        if not live:
            report.notes.append("every tie in reach is inside something")
            return None
        targets = {n for n in targets if n in live or n not in inverts}
        cap = PROBE_LABELS if ledger.trial else None  # a retry is a probe too
        # A lane the search accepts can still miss the 1/16" grid by a step (its snap
        # allowance and ``route_fall._on_grid`` disagree on a knife edge), so a refused one
        # is searched again under a weir one step lower: a smaller feasible set, never a
        # looser one, and the knife-edge lane drops out of it.
        for lowered in range(_SNAP_RETRIES + 1):
            problem = GravityProblem(ceiling_m=ceiling - lowered * _SNAP_M,
                                     grade_in_per_ft=grade,
                                     diameter_m=2.0 * pipe_trade.radius_m(size),
                                     required_m={n: required[n] for n in live},
                                     nipple_m=nipple, heel_m=heel,
                                     **({} if cap is None and not lowered
                                        else {"max_labels": PROBE_LABELS}))
            found = sloped_route(a_graph, a_space, start, targets, problem,
                                 constraints=constraints, refusal=report,
                                 obstacles=obstacles, heels=heels)
            if found is None or found.nodes[-1] not in inverts or place(tag, found, problem):
                return found
        return None

    def place(tag, found, problem) -> bool:
        """Lay ``found`` in the tree, or refuse it when its profile misses the grid."""
        # Its own inverts, now: the next branch may tie onto this one (§13).
        lengths = developed_lengths(found.points)
        arrival = inverts[found.nodes[-1]]
        end = graph.nodes[found.nodes[-1]]
        top = branches.drop_top(owners.get(found.nodes[-1], 0), (end.x, end.y))
        if top is not None and found.start_m is not None:
            # Into the side of that plumb drop at its own height: no drop of its own.
            arrival = min(top, max(arrival, found.start_m - problem.fall_over(lengths[-1])))
        # On the grid now, not after the tree: a branch that cannot be proposed must not
        # stand in the tree for later branches to dodge or tie onto.
        legs, said = found.polyline(), []
        if _fall(legs, (legs[0][0], legs[0][1], floors[tag]),
                 HeadBudget(ceiling_m=floors[tag], required_m=arrival,
                            developed_ft=lengths[-1], diameter_m=size),
                 grade, tag, said, start_m=found.start_m) is None:
            ledger.unsnapped[tag] = said[0] if said else f"{tag}: off the 1/16\" grid"
            return False
        ledger.unsnapped.pop(tag, None)
        if top is not None and found.start_m is not None:
            ledger.arrivals[tag] = arrival
        # An "over" route runs at its start and drops plumb into the tie at the end.
        over = (found.start_m is not None
                and found.start_m > arrival + problem.fall_over(lengths[-1]) + 1e-6)
        before = set(inverts)
        for index, length in zip(found.nodes, lengths, strict=False):
            inverts.setdefault(index, found.start_m - problem.fall_over(length)
                               if over and index != found.nodes[-1]
                               else arrival + problem.fall_over(lengths[-1] - length))
        laid = [(graph.nodes[n].x, graph.nodes[n].y, inverts[n]) for n in found.nodes]
        laid[-1] = (*laid[-1][:2], arrival)
        if over:  # its plumb drop is a leg of its own
            laid.insert(-1, (*laid[-1][:2], found.start_m - problem.fall_over(lengths[-1])))
        ledger.lay(tag, size, laid, found.nodes, over, set(inverts) - before)
        return True

    with clock.stage(f"search {size / 0.0254:.3g}in"):
        built = build_tree(graph, space, min(goals), terminals, root_nodes=goals,
                           search=search, ripup=ledger)
    notices = [f"{label}: {line}" for line in explain_tree(built)] if explain else []
    if not explain:  # every lift is reported, kept or rolled back (§1)
        notices = [f"{label}: rip-up: {t.sentence()}" for t in built.trials]
    for tag, shortfall in sorted(built.unserved.items()):
        if tag in ledger.unsnapped:
            problems.append(ledger.unsnapped[tag])
            continue
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
    # twelve feet away and calls a route feasible that is not. ``routes`` is in LAY order,
    # which rip-up may have changed from ``order``.
    made: list[tuple[RouteProposal, str]] = []
    for tag, route_found in built.routes.items():
        legs = route_found.polyline()
        lengths = developed_lengths(route_found.points)
        arrival = ledger.arrivals.get(tag, inverts.get(route_found.nodes[-1]))
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
            tag=f"{tag}{_PROPOSED}", kind="pipe", points=list(fell), diameter_m=size,
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
