"""``haus route --tree`` on a supply main, and ``--topology {tree,trunk}``.

The trunk is the route to the farthest fixture, laid first inside a z gate (the floor system
hangs it); the other branches follow farthest first, groups as the authored tie-ins hang
them, each a lattice of its own. ``trunk``: a branch tees onto the trunk or its own group;
``tree`` (the default): onto any branch laid before it. Cold only. Oracle:
``notes/mep_supply_trunk_basis.md``; the pure parts are ``routing/supply_tree``. docs/routing.md."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_options import RouteOptions
from typehaus.cli.route_supply_group import Laid, gates, lay_group, resized, space_for

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal

_SUPPLY = ("water_cold", "water_hot")
#: A branch looks this far (plan) beyond its group's fixtures for something to tee onto.
_REACH_M = 25.0 * 0.3048
_TRUNK_TRIES = 3  # farthest-first candidates for the trunk's far end before giving up


def is_supply_main(model: ResolvedModel, tree: str) -> bool:
    """True when ``--tree tree`` names a pressurised pipe run (this module routes it)."""
    return any(getattr(r, "tag", None) == tree
               and str(getattr(getattr(r, "system", None), "value",
                               getattr(r, "system", None))) in _SUPPLY
               for r in getattr(model, "pipe_runs", ()))


@dataclass
class _Net:
    """The authored cold network under one main: what it feeds, and its far ends."""

    runs: dict[str, Any]
    trunk: Any
    parent: dict[str, str | None]
    below: list[str]  #: every run downstream of the trunk
    terminals: list[str]  #: runs whose far end is a fixture, an equipment port or a stub
    own: dict[str, tuple[str, ...]]
    root: tuple[float, float, float]
    chain: list[str]
    ends: dict[str, Any] = field(default_factory=dict)
    keep: list[str] = field(default_factory=list)  #: buried outdoor runs, left as authored


def _network(model: ResolvedModel, tree: str, problems: list[str]) -> _Net | None:
    from typehaus.cli.route_roots import _supply_trunk
    from typehaus.cli.route_support import _endpoints, _storey_datum
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records
    from typehaus.routing.supply_tree import own_fixtures, terminal_tags

    runs = {r.tag: r for r in model.pipe_runs}
    trunk = runs[tree]
    if str(getattr(trunk.system, "value", trunk.system)) != "water_cold":
        problems.append(f"{tree}: a hot main is not a tree this router lays; only the cold "
                        "side's trunk gate is derived (hot rides its own band, a pair "
                        "1 7/8\" from the cold)")
        return None
    if not trunk.z_m or len(trunk.z_m) != len(trunk.path):
        problems.append(f"{tree}: no resolved elevations, so it cannot be routed")
        return None
    ports = placed_ports(model)
    parent: dict[str, str | None] = {rec.child: rec.parent for rec in
                                     supply_tie_in_records(model.pipe_runs, ports)}
    kids: dict[str, list[str]] = {}
    for child, up in parent.items():
        if up:
            kids.setdefault(up, []).append(child)
    below: list[str] = []
    stack = list(reversed(kids.get(tree, [])))
    while stack:
        tag = stack.pop()
        if tag in below:
            continue
        below.append(tag)
        stack.extend(reversed(kids.get(tag, [])))
    named = [tree, *below]
    own = own_fixtures({t: tuple(runs[t].serves) for t in named}, kids)
    at_port = frozenset(
        t for t in named if any(math.dist((*runs[t].path[-1], runs[t].z_m[-1]), p.point) < 0.03
                                for p in ports))
    terminals = terminal_tags(named, own, kids, at_port)
    scratch: list[str] = []
    found = _supply_trunk(model, trunk, scratch)
    if found is None:
        problems.extend(scratch)
        return None
    net = _Net(runs=runs, trunk=trunk, parent=parent, below=below, terminals=terminals,
               own=own, root=found[0], chain=found[1])
    for tag in terminals:
        run = runs[tag]
        if tag != tree and min(run.z_m) < _storey_datum(model, run.storey) - 24.0 * 0.0254:
            # Two feet under its own floor: buried in the soil. Frost depth, the slab sleeve
            # and the hose bib's shutoff are not a router's call.
            net.keep.append(tag)
            continue
        ends = _endpoints(model, tag, "run", scratch)
        if ends is None:
            problems.append(f"{tag}: its far end cannot be derived ({'; '.join(scratch[-1:])})")
        else:
            net.ends[tag] = ends
    return net


def propose_supply_tree(model: ResolvedModel, tree: str, topology: str | None,
                        opts: RouteOptions
                        ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                                   list]:
    """``_propose_tree``'s return shape for supply main ``tree``.

    ``topology`` is None or "tree" (a branch tees onto any laid branch) or "trunk" (onto the
    trunk or its own group). Returns (proposal/storey pairs, problems, notices, structured
    refusals); ``cmd_route`` evaluates and reports them."""
    from typehaus.routing.timing import Timer

    problems: list[str] = []
    notices: list[str] = []
    refusals: list[Any] = []
    if not is_supply_main(model, tree):
        return [], [f"{tree}: not a supply run in this model, so there is no tree to build "
                    "round it"], [], []
    if opts.via:
        notices.append(f"{tree}: --via is not used by a supply tree")
    net = _network(model, tree, problems)
    if net is None or not net.ends:
        return [], problems, notices, []
    clock = Timer(tree, enabled=opts.timing is not None)
    try:
        return _lay(model, tree, topology or "tree", opts, net, clock, problems, notices,
                    refusals)
    finally:
        if opts.timing is not None:
            opts.timing.extend(clock.lines())


def _lay(model: ResolvedModel, tree: str, topology: str, opts: RouteOptions, net: _Net,
         clock: Any, problems: list[str], notices: list[str], refusals: list[Any]):
    from typehaus.routing.supply_tree import developed_key, farthest_first, group_of, plan_key

    ends = net.ends
    # The trunk's far end is the farthest in PLAN (no route exists yet to develop a length on);
    # everything after is ordered by developed length by way of the laid trunk (the note's §4).
    order = farthest_first({t: plan_key(net.root, ends[t].origin) for t in ends})
    laid = _lay_trunk(model, tree, opts, net, order, clock, problems, notices, refusals)
    if laid is None:
        return [], problems, notices, refusals
    trunk_tag, trunk_prop, far = laid
    routes: list[Laid] = [Laid(trunk_tag, trunk_prop, net.own.get(far, ()), "", far)]
    keys = {t: developed_key(trunk_prop.points, ends[t].origin) for t in ends}
    groups: dict[str, list[str]] = {}
    for tag in farthest_first(keys):
        if tag != far:
            groups.setdefault(group_of(net.parent, tree, tag), []).append(tag)
    for group in sorted(groups, key=lambda g: (-keys[groups[g][0]], g)):
        lay_group(model, tree, topology, opts, net, group, groups[group], routes, clock,
                  problems, notices, refusals)
    return _finish(model, net, routes, notices), problems, notices, refusals


def _gate(model: ResolvedModel, net: _Net, radius_m: float) -> Any:
    """The trunk's gate: that of the floor system directly above its root."""
    from shapely.geometry import Point, Polygon

    rx, ry, rz = net.root
    over = [f for f in model.floors if f.deck_outline and f.deck_z0_m > rz
            and Polygon(f.deck_outline).buffer(0.01).contains(Point(rx, ry))]
    if not over:
        return None
    return gates(model, radius_m).get(min(over, key=lambda f: f.deck_z0_m).storey)


def _lay_trunk(model, tree, opts, net, order, clock, problems, notices, refusals):
    """The trunk: root to the farthest end that routes inside the gate. ``(tag, proposal, far)``."""
    from typehaus.cli.route_diagnose import refuse
    from typehaus.cli.route_proposal import one_proposal
    from typehaus.cli.route_support import _nearest, _root_nodes
    from typehaus.routing.search import shortest_route
    from typehaus.routing.space import RoutingSpaceTooLarge
    from typehaus.routing.supply_tree import HOLE_M, gate_prisms

    base = net.ends.get(tree) or next(iter(net.ends.values()))
    trunk_ends = replace(resized(base, net.trunk, net.trunk.diameter_m),
                         serves=tuple(net.trunk.serves),
                         touch=frozenset({tree, *net.below, *net.chain}))
    gate = _gate(model, net, trunk_ends.radius_m)
    if gate is None:
        problems.append(f"{tree}: no floor system above its root has a common crossing "
                        "window wide enough for it, so there is no z gate to hang a trunk in")
        return None
    rx, ry, rz = net.root
    tries = order[:_TRUNK_TRIES]
    for far in tries:
        fx, fy, fz = net.ends[far].origin
        seeds = [(rx, ry, rz), (fx, fy, fz),
                 *[(x, y, z) for x, y in ((rx, ry), (fx, fy)) for z in gate.planes]]
        try:
            space, graph = space_for(
                model, opts, net, trunk_ends, seeds, clock, f"trunk to {far}",
                extra=lambda sp, hole=(fx, fy): gate_prisms(sp.bbox, gate, [(rx, ry), hole]))
        except RoutingSpaceTooLarge as exc:
            notices.append(f"{tree}: trunk to {far}: {exc}")
            continue
        start = _nearest(graph, (fx, fy, fz))
        goals = _root_nodes(graph, net.root, with_z=True, exact=True)
        if start is None or not goals:
            notices.append(f"{tree}: trunk to {far}: no lattice node at an end")
            continue
        with clock.stage("search trunk"):
            found = shortest_route(graph, space, start, goals)
        if found is None:
            refused = refuse(space, graph, start, goals, target=tree, ends=trunk_ends,
                             report=None, alternatives=1, margin_ft=opts.margin_ft, band=None)
            notices.append(f"{tree}: no gated trunk to {far}: {refused.render()}")
            if far == tries[-1]:
                refusals.append(refused)
            continue
        ends = replace(trunk_ends, origin=(fx, fy, fz), origin_lead=net.ends[far].origin_lead)
        scratch: list[str] = []
        made = one_proposal(model, ends, found, tree, "", opts.slope, opts.details, scratch,
                            space=space)
        if made is None:
            problems.extend(scratch)
            continue
        notices.append(
            f"{tree}: trunk = the route to {far}, the farthest end in plan; level legs "
            f"inside the gate z {gate.lo_m / 0.0254:.2f}\" .. {gate.hi_m / 0.0254:.2f}\", "
            f"a riser lane {HOLE_M / 0.0254:.0f}\" round each end")
        return tree, made, far
    problems.append(f"{tree}: no trunk could be laid inside the z gate to any of the "
                    f"{len(tries)} farthest ends")
    return None


def _finish(model: ResolvedModel, net: _Net, routes: list[Laid], notices: list[str]
            ) -> list[tuple[Any, str]]:
    """Each route's ``serves`` (own fixtures plus every route teed on it) and what it
    replaces. A run is sized up to its load only within the clearance it was searched at."""
    from typehaus.routing.supply_tree import downstream_serves, tee_onto
    from typehaus.takeoff.plumbing_calc import (
        branch_load,
        fixture_units,
        required_supply_size_in,
    )

    units = {row.tag: row for row in fixture_units(model.plan)}
    tee: dict[str, str | None] = {r.proposal.tag: r.host for r in routes}
    serves = downstream_serves({r.proposal.tag: r.own for r in routes}, tee,
                               tuple(net.trunk.serves))
    named = {r.tag for r in routes if r is not routes[0]}
    gone = {net.trunk.tag, *(t for t in net.below if t not in named and t not in net.keep)}
    for tag in net.keep:  # its authored tee must still land on the new trunk
        run = net.runs[tag]
        if tee_onto({"trunk": routes[0].proposal.points},
                    (*run.path[0], run.z_m[0])) is None:
            notices.append(f"{tag}: left as authored, but its tee no longer lies on the new "
                           "trunk — re-route it with --run")
    out = []
    for r in routes:
        p, first = r.proposal, r is routes[0]
        mine = tuple(net.trunk.serves) if first else serves[p.tag]
        note = "trunk" if first else f"tees onto {tee.get(p.tag) or 'nothing laid'}"
        load, _unresolved = branch_load(mine, units, "water_cold")
        need = required_supply_size_in(load) if load is not None else None
        size = max(p.diameter_m, need * 0.0254) if need is not None else p.diameter_m
        if size > p.diameter_m + 1e-9:  # within its lattice's clearance: ``Laid.limit_m``
            note += (f"; sized {need}\" for {load:g} WSFU (the table mep.pipe_sizing grades), "
                     f"not the {p.diameter_m / 0.0254:.3g}\" authored")
            if size > max(r.limit_m, p.diameter_m) + 1e-9:
                notices.append(f"{p.tag}: needs {need}\" but was searched at "
                               f"{max(r.limit_m, p.diameter_m) / 0.0254:.3g}\"")
        made = replace(p, serves=mine, diameter_m=size, notes=[*p.notes, note])
        made = replace(made, replaces=tuple(sorted(
            gone if first else ({r.tag} if r.tag in net.runs else set()))))
        if first:
            seated = sorted(a.tag for a in model.pipe_accessories
                            if a.pipe_ref in {*gone, *named})
            made = replace(made, after=(
                *made.after, "AFTER PASTING delete the authored cold runs this tree stands "
                "in for: " + ", ".join(sorted(gone)),
                f"and re-seat the {len(seated)} accessories on them (stops, shutoffs, "
                "arrestors) on the new runs: " + ", ".join(seated)))
        out.append((made, str(net.runs[r.tag if r.tag in net.runs else net.trunk.tag].storey)))
    return out
