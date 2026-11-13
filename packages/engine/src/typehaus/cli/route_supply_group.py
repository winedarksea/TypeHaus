"""One branch group of a supply tree: its lattice, its gates, its searches.

Split from ``cmd_route_supply_tree`` (which derives the network, lays the trunk and finishes).
A branch tees only onto a laid run that can carry it: the WSFU it would add, up the whole host
chain, stays inside each run's own size (``plumbing_calc.SUPPLY_BRANCH_CAPACITY_WSFU``), so no
run needs resizing after the fact. docs/routing.md."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_options import RouteOptions

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.cmd_route_supply_tree import _Net
    from typehaus.resolve.model import ResolvedModel

#: A branch looks this far (plan) beyond its group's fixtures for something to tee onto.
REACH_M = 25.0 * 0.3048
#: First try: a lattice this far round the group costs about half; a group that fails there
#: (nothing to tee onto, no route) is tried again at ``REACH_M``.
NEAR_M = 10.0 * 0.3048


@dataclass
class Laid:
    """One laid route: its proposal, the authored run it stands in for, what it feeds itself."""

    tag: str  #: authored run tag (the trunk's own tag for the trunk and the kitchen end)
    proposal: Any
    own: tuple[str, ...]
    group: str
    terminal: str
    host: str | None = None  #: proposal tag of the run it tees onto
    limit_m: float = 0.0  #: the widest it may be sized to: the lattice it was found in


def resized(ends: Any, run: Any, diameter_m: float) -> Any:
    """``ends`` for a pipe of another diameter (radius and bend radius follow)."""
    from typehaus.routing.trades import pipe as pipe_trade

    return replace(
        ends, diameter_m=diameter_m,
        radius_m=pipe_trade.radius_m(diameter_m, run.material, run.insulation),
        bend_radius_m=pipe_trade.bend_radius_m(diameter_m, str(run.system), run.material))


def gates(model: ResolvedModel, radius_m: float) -> dict[str, Any]:
    """A z gate per floor system (storey), from its members' common crossing window."""
    from typehaus.resolve.mep_crossings import member_window
    from typehaus.routing.supply_tree import gate_for

    out: dict[str, Any] = {}
    for storey in sorted({f.storey for f in model.floors}):
        floors = [f for f in model.floors if f.storey == storey]
        windows = [(w.z0_m, w.z1_m) for w in map(member_window, floors) if w is not None]
        gate = gate_for(windows, radius_m)
        if gate is not None:
            out[storey] = gate
    return out


def space_for(model: ResolvedModel, opts: RouteOptions, net: _Net, ends: Any, seeds: list,
              clock: Any, name: str, *, extra: Any = None, band: Any = None,
              exempt: Any = None, fixture_ends: tuple = (), cover: bool = True,
              laid: Any = (), leads: tuple = (), serves: Any = ()) -> tuple[Any, Any]:
    """Space and lattice for ``ends``' pipe; ``extra(space)`` gives prisms to add first.

    A riser stands only in wall cover or a soffit (``resolve/riser_cover``) except at the
    route's own ends, ``exempt`` (default: every seed — the trunk's two ends), or inside a
    ``serves`` fixture's body holding one of them, under its top (``fixture_trim``). A
    ``fixture_ends`` point in a door or a duct is built at the nearest legal wall point.
    ``laid``: runs this campaign laid already, whose holes a new crossing keeps clear of.
    ``leads``: endpoints whose port stubs the lattice may not double back over."""
    from typehaus.cli.route_ports import forbid_port_reversal
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import build_space

    with clock.stage(f"build-space {name}"):
        space = build_space(model, radius_m=ends.radius_m, terminals=seeds,
                            margin_ft=opts.margin_ft, avoid=opts.avoid,
                            touch=frozenset({net.trunk.tag, *net.below, *net.chain}),
                            cost=opts.cost.for_run(ends.kind, ends.system), z_band=band,
                            cavity_radius_m=ends.cavity_radius_m or None, laid=laid)
    space.bend_radius_m = ends.bend_radius_m
    space.blocking_runs = frozenset(d.tag for d in model.ducts)
    if space.members is not None and cover:
        from typehaus.resolve.riser_cover import riser_cover

        space.members.riser_cover = riser_cover(
            model, space.bbox, seeds if exempt is None else exempt, serves=serves)
    if extra is not None:
        space.hard.extend(extra(space))
        space._hard_index = None
    with clock.stage(f"build-graph {name}"):
        graph = build_graph(space, seeds, None, ends=fixture_ends)
    for one in leads:
        forbid_port_reversal(graph, one)
    clock.lattice(graph)
    return space, graph


class _Loads:
    """WSFU on the laid tree: what each run feeds, and whether it can take one more. A run may
    grow to the size its lattice was cut at (``Laid.limit_m``) — it was searched with that
    clearance, so ``_finish`` can size it up without a second search."""

    def __init__(self, model: ResolvedModel, routes: list[Laid]) -> None:
        from typehaus.takeoff.plumbing_calc import fixture_units

        self.routes = routes
        self.units = {row.tag: row for row in fixture_units(model.plan)}

    def wsfu(self, fixtures: tuple[str, ...]) -> float:
        from typehaus.takeoff.plumbing_calc import branch_load

        return branch_load(fixtures, self.units, "water_cold")[0] or 0.0

    def load(self, route: Laid) -> float:
        return self.wsfu(route.own) + sum(self.load(r) for r in self.routes
                                          if r.host == route.proposal.tag)

    def fits(self, route: Laid, extra: float) -> bool:
        """``extra`` WSFU more on ``route`` and on every run above it, each within its size."""
        from typehaus.routing.supply_tree import capacity_wsfu
        from typehaus.takeoff.plumbing_calc import SUPPLY_BRANCH_CAPACITY_WSFU

        by_tag = {r.proposal.tag: r for r in self.routes}
        seen = 0
        while route is not None and seen <= len(self.routes):
            cap = capacity_wsfu(max(route.proposal.diameter_m, route.limit_m),
                                SUPPLY_BRANCH_CAPACITY_WSFU)
            if self.load(route) + extra > cap + 1e-9:
                return False
            route, seen = by_tag.get(route.host or ""), seen + 1
        return True


def lay_group(model: ResolvedModel, tree: str, topology: str, opts: RouteOptions, net: _Net,
              group: str, members: list[str], routes: list[Laid], clock: Any,
              problems: list[str], notices: list[str], refusals: list[Any]) -> None:
    """Lay ``members`` (farthest first). ``tree`` topology falls back to ``trunk`` for a group
    whose lattice, seeded with every laid branch, would be too large."""
    from typehaus.routing.space import RoutingSpaceTooLarge

    label = f"group {group or 'END'}"
    modes = ("tree", "trunk") if topology == "tree" else ("trunk",)
    attempts = [(mode, reach, True) for mode in modes for reach in (NEAR_M, REACH_M)]
    # What no wall, soffit or chase let rise is laid last through the room's air, and said so.
    attempts.append((modes[-1], REACH_M, False))
    loads = _Loads(model, routes)
    todo = list(members)
    for i, (mode, reach, cover) in enumerate(attempts):
        last = i == len(attempts) - 1
        try:
            built = _build(model, tree, mode, reach, opts, net, group, todo, routes, clock,
                           loads, cover)
        except RoutingSpaceTooLarge as exc:
            if last:
                problems.extend(f"{tag}: {label}: {exc}" for tag in todo)
                return
            if reach == REACH_M:
                notices.append(f"{label}: too large with every laid branch as a tee ({exc}); "
                               "tees limited to the trunk and its own group")
            continue
        found_problems: list[str] = []
        found_refusals: list[Any] = []
        before = len(routes)
        todo = _search(model, tree, opts, net, group, todo, routes, clock, loads, built,
                       found_problems, notices, found_refusals)
        if not cover:
            notices.extend(f"{r.proposal.tag}: no wall, soffit or chase carries its riser, so it "
                           "rises through a finished room's open air (mep.run_in_finished_volume)"
                           for r in routes[before:])
        if not todo or last:
            problems.extend(found_problems)
            refusals.extend(found_refusals)
            return


def _build(model, tree, mode, reach_m, opts, net, group, members, routes, clock, loads,
           cover=True):
    """The group's ends, admission rule, space and lattice."""
    import numpy as np

    from typehaus.routing.campaign import proposal_prisms
    from typehaus.routing.holes import laid_lines
    from typehaus.routing.obstacles import CLEARANCE_M
    from typehaus.routing.supply_tree import clip_polyline, gate_prisms

    label = f"group {group or 'END'}"
    ends = {t: net.ends[t] for t in members}
    if tree in ends:  # the trunk's own end is the kitchen sink: a branch size, not 1 1/4"
        other = [e.diameter_m for t, e in net.ends.items() if t != tree and net.own.get(t)]
        ends[tree] = resized(ends[tree], net.trunk, max(other, default=ends[tree].diameter_m))
    from typehaus.takeoff.plumbing_calc import required_supply_size_in

    for t in ends:  # a run is searched at the size its own load needs, never resized after
        need = required_supply_size_in(loads.wsfu(net.own.get(t, ())))
        if need is not None and need * 0.0254 > ends[t].diameter_m + 1e-9:
            ends[t] = resized(ends[t], net.runs[t], need * 0.0254)
    small = min(e.diameter_m for e in ends.values())
    # The lattice is cut at the size its carriers will be: the authored top branch's, if wider.
    top = net.runs.get(group)
    big = max(max(e.diameter_m for e in ends.values()), top.diameter_m if top else 0.0)
    widest = max(ends, key=lambda t: ends[t].diameter_m)
    template = resized(ends[widest], net.runs[widest], big)
    xs, ys = [e.origin[0] for e in ends.values()], [e.origin[1] for e in ends.values()]
    reach = (min(xs) - reach_m, min(ys) - reach_m, max(xs) + reach_m, max(ys) + reach_m)

    def listed(r: Laid) -> bool:  # on the tee list: the trunk, its own group, or all (tree)
        return r is routes[0] or mode == "tree" or r.group == group

    seeds = [e.origin for e in ends.values()]
    for r in routes:
        if listed(r) and r.proposal.diameter_m + 1e-9 >= small:
            seeds.extend(p for piece in clip_polyline(r.proposal.points, reach)
                         for p in piece)
    if len(seeds) == len(ends):  # nothing laid within reach: offer the trunk whole
        seeds.extend(routes[0].proposal.points)
    # Off the tee list, or too small to carry any member: a run to keep clear of, not a host
    # (a 3/4" branch rode a 1/2" one's lane; ``mep.run_interference``).
    walls = [prism for r in routes
             if not listed(r) or r.proposal.diameter_m + 1e-9 < small
             for prism in proposal_prisms(r.proposal, inflate_m=CLEARANCE_M)]
    flight = list(gates(model, template.radius_m).values())
    # A riser may stand at the trunk's two ends (a bay either side), and at each fixture end and
    # the far end of any branch a later one may tee onto (a foot either side).
    holes = [p[:2] for p in (routes[0].proposal.points[0], routes[0].proposal.points[-1])]
    tight = [e.origin[:2] for e in ends.values()] + [
        r.proposal.points[-1][:2] for r in routes[1:] if listed(r)]
    # ...and where the plan already stands the risers feeding each member (its own run and its
    # feeders up to the trunk): a hole and a lattice line, at the end's height. Basis §5a.
    stations = [(*p, ends[t].origin[2]) for t in ends for p in _plan_risers(net, t)]
    tight += [p[:2] for p in stations]
    seeds += stations
    stands = [routes[0].proposal.points[0], routes[0].proposal.points[-1],
              *(e.origin for e in ends.values()),
              *(r.proposal.points[-1] for r in routes[1:] if listed(r))]
    space, graph = space_for(
        model, opts, net, template, seeds, clock, label, band=opts.band,
        exempt=stands, fixture_ends=tuple(e.origin for e in ends.values()), cover=cover,
        laid=laid_lines(r.proposal for r in routes),
        leads=tuple(replace(e, root_lead=None) for e in ends.values()),
        serves={f for e in ends.values() for f in e.serves},
        extra=lambda sp: [*walls, *(gate_prisms(sp.bbox, flight, holes, tight) if flight else [])])
    xyz = np.array([(n.x, n.y, n.z) for n in graph.nodes]).reshape(-1, 3)
    space.reuse = True
    return ends, listed, space, graph, xyz, template.diameter_m


def _plan_risers(net: Any, tag: str) -> list[tuple[float, float]]:
    """Authored riser stations of ``tag`` and of its feeders, up to (not including) the trunk:
    the plan's own path for that water to rise (an attic bar fed down a hall wall)."""
    from typehaus.routing.supply_tree import riser_stations

    out: list[tuple[float, float]] = []
    seen: set[str] = set()
    while tag and tag != net.trunk.tag and tag not in seen and tag in net.runs:
        seen.add(tag)
        run = net.runs[tag]
        out.extend(p for p in riser_stations(run.path, run.z_m or ()) if p not in out)
        tag = net.parent.get(tag)
    return out


def _search(model, tree, opts, net, group, members, routes, clock, loads, built, problems,
            notices, refusals) -> list[str]:
    """Lay ``members``; the tags that found no route (their reasons are in ``problems``)."""
    from typehaus.cli.route_diagnose import refuse
    from typehaus.cli.route_proposal import one_proposal
    from typehaus.cli.route_support import _nearest
    from typehaus.routing.holes import drop_close_edges, laid_lines
    from typehaus.routing.search import shortest_route
    from typehaus.routing.supply_tree import nodes_on
    from typehaus.routing.terminal_block import column_block

    ends, listed, space, graph, xyz, limit = built
    label = f"group {group or 'END'}"
    if graph.blocked_terminals:
        notices.append(f"{label}: a terminal stands inside "
                       f"{', '.join(graph.blocked_terminals)} — routed anyway; the tie "
                       "itself is a detail somebody has to draw")
    failed: list[str] = []
    blocks = {b.point: b for b in graph.terminal_blocks}
    for tag in members:
        ends_t, weight = ends[tag], loads.wsfu(net.own.get(tag, ()))
        block = blocks.get(tuple(ends_t.origin[:3]))
        if block is not None and block.moved_to is None:
            refusals.append(_blocked_end(tag, ends_t, block, graph))
            problems.append(refusals[-1].render())
            failed.append(tag)
            continue
        goals: set[int] = set()
        for r in routes:
            if (listed(r) and r.proposal.diameter_m + 1e-9 >= ends_t.diameter_m
                    and loads.fits(r, weight)):
                goals |= nodes_on(xyz, r.proposal.points)
        start = _nearest(graph, (*block.moved_to, ends_t.origin[2]) if block else ends_t.origin)
        if start is None or not goals:
            problems.append(f"{tag}: {label}: no lattice node at its end, or no laid run "
                            "within reach that can carry it")
            failed.append(tag)
            continue
        if start in goals:  # its end already stands on the tree: served, no run of its own
            on = _host(routes, loads, ends_t.origin, weight)
            if on is not None:
                on.own = (*on.own, *net.own.get(tag, ()))
                notices.append(f"{tag}: its end stands on {on.proposal.tag}, so that run "
                               "serves it and it needs none of its own")
                continue
        with clock.stage(f"search {tag}"):
            found = shortest_route(graph, space, start, goals)
        if found is None:
            column = column_block(space, tuple(ends_t.origin[:3]))
            refused = (_blocked_end(tag, ends_t, column, graph) if column is not None else
                       refuse(space, graph, start, goals, target=tag, ends=ends_t, report=None,
                              alternatives=1, margin_ft=opts.margin_ft, band=opts.band))
            refusals.append(refused)
            problems.append(refused.render())
            failed.append(tag)
            continue
        clock.route(found)
        scratch: list[str] = []
        target, suffix = (tree, "-END") if tag == tree else (tag, "")
        made = one_proposal(model, ends_t, found, target, suffix, opts.slope, opts.details,
                            scratch, space=space)
        problems.extend(scratch)
        if made is not None and block is not None:
            made = _restore_end(made, ends_t.origin, block, notices)
        if made is not None:
            host = _host(routes, loads, made.points[0], weight)
            routes.append(Laid(tag, made, net.own.get(tag, ()), group, tag,
                               host=host.proposal.tag if host else None, limit_m=limit))
            # A sibling laid now is no hole in the space built before it: the lattice loses
            # the edges its I-joist holes close (``framing_bore_limits.md`` §14).
            drop_close_edges(graph, space, laid_lines([made]))
    return failed


def _blocked_end(tag: str, ends: Any, block: Any, graph: Any) -> Any:
    """The refusal for a fixture end inside a door or a duct with no legal point on its wall."""
    from typehaus.cli.route_propose import EndpointRefusal

    return EndpointRefusal(
        target=tag, service="water_cold", end="origin", reachable_nodes=0,
        total_nodes=len(graph.nodes), established=True, cause=block.render(),
        element=block.prisms[0], fix="move the fixture end (a house edit); the router will not",
        terminal=block.payload())


def _restore_end(made: Any, origin: tuple, block: Any, notices: list[str]) -> Any:
    """The run's fixture end put back: the search ended at the moved point, so the authored end
    is a short leg along the wall (``made`` runs tee to fixture)."""
    from dataclasses import replace

    x, y, _z = made.points[-1]
    if max(abs(x - block.moved_to[0]), abs(y - block.moved_to[1])) > 0.003:
        return made
    notices.append(f"{made.tag}: {block.render()}")
    return replace(made, points=[*made.points, tuple(origin[:3])], bends=made.bends + 1,
                   notes=[*made.notes, block.render()]).snapped()


def _host(routes: list[Laid], loads: _Loads, point: tuple[float, ...], weight: float
          ) -> Laid | None:
    """The laid run ``point`` stands on: of several meeting there, the first that can carry
    ``weight`` (the goals were built from exactly those)."""
    from typehaus.routing.supply_tree import tee_onto

    on = [r for r in routes if tee_onto({"r": r.proposal.points}, point)]
    return next((r for r in on if loads.fits(r, weight)), on[0] if on else None)
