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
#: A tee is ON a laid line: 3/16" in plan, 1/4" in z (the proposals are snapped to 1/16").
_ON_M, _ON_Z_M = 0.005, 0.0064


@dataclass
class Laid:
    """One laid route: its proposal, the authored run it stands in for, what it feeds itself."""

    tag: str  #: authored run tag (the trunk's own tag for the trunk and the kitchen end)
    proposal: Any
    own: tuple[str, ...]
    group: str
    terminal: str
    host: str | None = None  #: proposal tag of the run it tees onto


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
        lows = [m.z0_m for f in floors for m in f.members if m.z0_m is not None]
        gate = gate_for(windows, min(lows), radius_m) if lows else None
        if gate is not None:
            out[storey] = gate
    return out


def space_for(model: ResolvedModel, opts: RouteOptions, net: _Net, ends: Any, seeds: list,
              clock: Any, name: str, *, extra: Any = None, band: Any = None
              ) -> tuple[Any, Any]:
    """Space and lattice for ``ends``' pipe; ``extra(space)`` gives prisms to add first."""
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import build_space

    with clock.stage(f"build-space {name}"):
        space = build_space(model, radius_m=ends.radius_m, terminals=seeds,
                            margin_ft=opts.margin_ft, avoid=opts.avoid,
                            touch=frozenset({net.trunk.tag, *net.below, *net.chain}),
                            cost=opts.cost.for_run(ends.kind, ends.system), z_band=band,
                            cavity_radius_m=ends.cavity_radius_m or None)
    space.bend_radius_m = ends.bend_radius_m
    if extra is not None:
        space.hard.extend(extra(space))
        space._hard_index = None
    with clock.stage(f"build-graph {name}"):
        graph = build_graph(space, seeds, None)
    clock.lattice(graph)
    return space, graph


class _Loads:
    """WSFU on the laid tree: what each run feeds, and whether it can take one more."""

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
            cap = capacity_wsfu(route.proposal.diameter_m, SUPPLY_BRANCH_CAPACITY_WSFU)
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
    loads = _Loads(model, routes)
    for mode in modes:
        try:
            built = _build(model, tree, mode, opts, net, group, members, routes, clock, loads)
        except RoutingSpaceTooLarge as exc:
            if mode == modes[-1]:
                problems.extend(f"{tag}: {label}: {exc}" for tag in members)
                return
            notices.append(f"{label}: too large with every laid branch as a tee ({exc}); "
                           "tees limited to the trunk and its own group")
            continue
        _search(model, tree, opts, net, group, members, routes, clock, loads, built,
                problems, notices, refusals)
        return


def _build(model, tree, mode, opts, net, group, members, routes, clock, loads):
    """The group's ends, admission rule, space and lattice."""
    import numpy as np

    from typehaus.routing.campaign import proposal_prisms
    from typehaus.routing.obstacles import CLEARANCE_M
    from typehaus.routing.supply_tree import clip_polyline, gate_prisms

    label = f"group {group or 'END'}"
    ends = {t: net.ends[t] for t in members}
    if tree in ends:  # the trunk's own end is the kitchen sink: a branch size, not 1 1/4"
        other = [e.diameter_m for t, e in net.ends.items() if t != tree and net.own.get(t)]
        ends[tree] = resized(ends[tree], net.trunk, max(other, default=ends[tree].diameter_m))
    small = min(e.diameter_m for e in ends.values())
    # The lattice is cut at the size its carriers will be: the authored top branch's, if wider.
    top = net.runs.get(group)
    big = max(max(e.diameter_m for e in ends.values()), top.diameter_m if top else 0.0)
    widest = max(ends, key=lambda t: ends[t].diameter_m)
    template = resized(ends[widest], net.runs[widest], big)
    xs, ys = [e.origin[0] for e in ends.values()], [e.origin[1] for e in ends.values()]
    reach = (min(xs) - REACH_M, min(ys) - REACH_M, max(xs) + REACH_M, max(ys) + REACH_M)

    def listed(r: Laid) -> bool:  # on the tee list: the trunk, its own group, or all (tree)
        return r is routes[0] or mode == "tree" or r.group == group

    seeds = [e.origin for e in ends.values()]
    for r in routes:
        if listed(r) and r.proposal.diameter_m + 1e-9 >= small:
            seeds.extend(p for piece in clip_polyline(r.proposal.points, reach)
                         for p in piece)
    if len(seeds) == len(ends):  # nothing laid within reach: offer the trunk whole
        seeds.extend(routes[0].proposal.points)
    walls = [prism for r in routes if not listed(r)
             for prism in proposal_prisms(r.proposal, inflate_m=CLEARANCE_M)]
    flight = list(gates(model, template.radius_m).values())
    # A riser may stand at each fixture end, the trunk's two ends, and the far end of any branch
    # a later one may tee onto (its tee end sits on its host, which is in a gate).
    holes = [e.origin[:2] for e in ends.values()] + [
        p[:2] for r in routes if listed(r)
        for p in ((r.proposal.points[0], r.proposal.points[-1]) if r is routes[0]
                  else (r.proposal.points[-1],))]
    space, graph = space_for(
        model, opts, net, template, seeds, clock, label, band=opts.band,
        extra=lambda sp: [*walls, *(gate_prisms(sp.bbox, flight, holes) if flight else [])])
    xyz = np.array([(n.x, n.y, n.z) for n in graph.nodes]).reshape(-1, 3)
    space.reuse = True
    return ends, listed, space, graph, xyz


def _search(model, tree, opts, net, group, members, routes, clock, loads, built, problems,
            notices, refusals) -> None:
    from typehaus.cli.route_diagnose import refuse
    from typehaus.cli.route_proposal import one_proposal
    from typehaus.cli.route_support import _nearest
    from typehaus.routing.search import shortest_route
    from typehaus.routing.supply_tree import nodes_on

    ends, listed, space, graph, xyz = built
    label = f"group {group or 'END'}"
    if graph.blocked_terminals:
        notices.append(f"{label}: a terminal stands inside "
                       f"{', '.join(graph.blocked_terminals)} — routed anyway; the tie "
                       "itself is a detail somebody has to draw")
    for tag in members:
        ends_t, weight = ends[tag], loads.wsfu(net.own.get(tag, ()))
        goals: set[int] = set()
        for r in routes:
            if (listed(r) and r.proposal.diameter_m + 1e-9 >= ends_t.diameter_m
                    and loads.fits(r, weight)):
                goals |= nodes_on(xyz, r.proposal.points, tol_m=_ON_M, z_tol_m=_ON_Z_M)
        start = _nearest(graph, ends_t.origin)
        if start is None or not goals:
            problems.append(f"{tag}: {label}: no lattice node at its end, or no laid run "
                            "within reach that can carry it")
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
            refused = refuse(space, graph, start, goals, target=tag, ends=ends_t, report=None,
                             alternatives=1, margin_ft=opts.margin_ft, band=opts.band)
            refusals.append(refused)
            problems.append(refused.render())
            continue
        clock.route(found)
        scratch: list[str] = []
        target, suffix = (tree, "-END") if tag == tree else (tag, "")
        made = one_proposal(model, ends_t, found, target, suffix, opts.slope, opts.details,
                            scratch, space=space)
        problems.extend(scratch)
        if made is not None:
            host = _host(routes, loads, made.points[0], weight)
            routes.append(Laid(tag, made, net.own.get(tag, ()), group, tag,
                               host=host.proposal.tag if host else None))


def _host(routes: list[Laid], loads: _Loads, point: tuple[float, ...], weight: float
          ) -> Laid | None:
    """The laid run ``point`` stands on: of several meeting there, the first that can carry
    ``weight`` (the goals were built from exactly those)."""
    from typehaus.routing.supply_tree import tee_onto

    on = [r for r in routes if tee_onto({"r": r.proposal.points}, point)]
    return next((r for r in on if loads.fits(r, weight)), on[0] if on else None)
