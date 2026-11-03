"""``--fixture``: a fixture's drain and its vent, searched together (``routing/trap_vent``).

The drain search carries the arm (UPC 1002.2); the take-offs it may close at are the
arm-reachable nodes in a wall cavity that holds the vent; each pays the ``h_vent`` one
backward rising search gives it. The vent is then read back off those distances, so it
rises to 6" over the flood rim before any level leg (UPC 905.3) by construction. The rim is
read as the fixture body's top, which no rim exceeds. ``mep_drain_routing_basis.md`` §9.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import Polygon

from typehaus.quantities import M_PER_IN

#: UPC 905.3: a vent rises this far over the flood-level rim before it may run level.
_OVER_RIM_M = 6 * M_PER_IN
#: How far in plan (Manhattan) a vent leg is offered as the vent's goal.
_STACK_REACH_M = 8.0
_LEGS = 8
#: The vent lattice's margin round its terminals, feet: room to step round a member.
_VENT_MARGIN_FT = 3.0
_TOL_M = 0.05


@dataclass
class VentContext:
    """What the drain search needs from the vent side, and what the vent proposal reads."""

    graph: Any
    dist: dict[int, float]
    level_floor_m: float
    diameter_m: float
    by_drain: dict[int, int] = field(default_factory=dict)


def arm_problem(model: Any, ends: Any, graph: Any, space: Any, start: int, goals: set[int],
                grade: float, obstacles: Any, report: Any
                ) -> tuple[dict[str, Any], VentContext | None]:
    """``(GravityProblem keywords, vent context)``; empty keywords when no arm applies."""
    from typehaus.resolve.plumbing_tables import trap_arm_limit_in
    from typehaus.routing.trades import pipe as pipe_trade
    from typehaus.routing.trap_vent import (
        arm_reach,
        arm_seeds,
        takeoff_candidates,
        vent_size_m,
    )

    if ends.fixture is None or _already_vented(model, ends.fixture):
        return {}, None
    limit_in = trap_arm_limit_in(ends.diameter_m)
    if limit_in is None:
        report.notes.append(f"no Table 1002.2 row for a {ends.diameter_m / M_PER_IN:g}\" "
                            "arm, so its vent is not searched")
        return {}, None
    vented = frozenset(g for g in goals if _on_stack(model, ends, graph.nodes[g]))
    reach = arm_reach(graph, space, start, limit_ft=limit_in / 12.0, weir_m=ends.origin[2],
                      grade_in_per_ft=grade, obstacles=obstacles)
    vent_d = vent_size_m(ends.diameter_m)
    keywords: dict[str, Any] = {"seeds": arm_seeds(reach, {}, vented)}
    rim = _rim_m(model, ends.fixture)
    if rim is None:
        report.notes.append(f"{ends.fixture} states no body height, so the 905.3 line (6\" "
                            "over its flood rim) is unknown and its vent is not searched")
        return keywords, None
    candidates = takeoff_candidates(graph, space, reach, rise_to_m=rim + _OVER_RIM_M,
                                    vent_od_m=2.0 * pipe_trade.cavity_radius_m(vent_d, "vent"))
    if not candidates:
        report.notes.append(f'no wall cavity that holds a {vent_d / M_PER_IN:g}" vent to 6" '
                            f'over the rim within {limit_in:g}" developed of the trap')
        return keywords, None
    context = _vent_context(model, ends, graph, space.cost, candidates, rim + _OVER_RIM_M,
                            vent_d, report)
    if context is not None:
        keywords["seeds"] = arm_seeds(
            reach, {c: context.dist[v] for c, v in context.by_drain.items()}, vented)
    return keywords, context


def _already_vented(model: Any, fixture: str) -> bool:
    """The check's own arm walk: a vent named in ``serves`` must also be reached in time."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point
    from typehaus.resolve.mep_trap_arm import arm_is_vented

    return arm_is_vented(model, fixture, _expected_drain_point(model, fixture))


def _on_stack(model: Any, ends: Any, node: Any) -> bool:
    """A tie on a vertical leg of a drain it may touch: a stack, vented above."""
    for run in model.pipe_runs:
        if run.tag not in ends.touch or run.system != "drain" or not run.z_m:
            continue
        for i in range(len(run.path) - 1):
            (ax, ay), (bx, by) = run.path[i], run.path[i + 1]
            low, high = sorted((run.z_m[i], run.z_m[i + 1]))
            if (abs(ax - bx) + abs(ay - by) < 1e-3 and abs(ax - node.x) < _TOL_M
                    and abs(ay - node.y) < _TOL_M and high - low > _TOL_M):
                return True
    return False


def _rim_m(model: Any, fixture: str) -> float | None:
    uid = getattr(model.plan.by_tag(fixture), "uid", None)
    obj = next((o for o in model.canvas_objects if o.uid == uid), None)
    return None if obj is None else obj.body_z1_m


def _vent_context(model: Any, ends: Any, drain_graph: Any, cost: Any, candidates: list[int],
                  level_floor_m: float, vent_d: float, report: Any) -> VentContext | None:
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.trades import pipe as pipe_trade
    from typehaus.routing.trap_vent import vent_cost_to_go

    legs = _vent_legs(model, ends.origin, level_floor_m, vent_d)
    if not legs:
        report.notes.append(f"no vent of {vent_d / M_PER_IN:g}\" or more within "
                            f"{_STACK_REACH_M:g} m stands 6\" over {ends.fixture}'s rim")
        return None
    terminals = [(n.x, n.y, z) for c in candidates for n in (drain_graph.nodes[c],)
                 for z in (n.z, level_floor_m)]
    terminals += [p for _t, a, b in legs for p in (a, b)]
    try:
        space = build_space(model, radius_m=pipe_trade.radius_m(vent_d), terminals=terminals,
                            cost=cost.for_run("pipe", "vent"), margin_ft=_VENT_MARGIN_FT,
                            touch=frozenset({*(t for t, *_ in legs), *ends.touch}),
                            cavity_radius_m=pipe_trade.cavity_radius_m(vent_d, "vent"))
        _close_finished_rooms(model, space)
        # A terminal in a closed room would be kept, and its edges excused from the room.
        graph = build_graph(space, [t for t in terminals
                                    if t[2] != level_floor_m or space.blocked(t[:2], t[2]) is None])
    except RoutingSpaceTooLarge as exc:
        report.notes.append(f"the vent lattice is too large to search ({exc})")
        return None
    goals = _leg_nodes(graph, legs)
    dist = vent_cost_to_go(graph, goals, level_floor_m=level_floor_m)
    context = VentContext(graph, dist, level_floor_m, vent_d)
    for c in candidates:
        d = drain_graph.nodes[c]
        v = next((n.index for n in graph.nodes if abs(n.x - d.x) < 1e-4
                  and abs(n.y - d.y) < 1e-4 and abs(n.z - d.z) < 1e-4), None)
        if v is not None and v in dist:
            context.by_drain[c] = v
    if not context.by_drain:
        report.notes.append("no take-off in reach rises clear to a vent stack"
                            + _first_blocker(space, drain_graph.nodes[candidates[0]],
                                             max(p[2] for _t, a, b in legs for p in (a, b))))
    return context


def _close_finished_rooms(model: Any, space: Any) -> None:
    """A dry vent never runs exposed through a finished room: its air is hard, not priced.

    Walls, floor depths and the space over a ceiling stay open, which is where a plumber
    runs one. ``mep.run_in_finished_volume`` grades the same band; a ``FollowRoof`` room,
    which builds no soft prism, is closed up to its sloped plane's highest corner.
    """
    from typehaus.checks.mep.routing_sloped import sloped_plane
    from typehaus.routing.obstacles import HardPrism

    space.hard.extend(
        HardPrism(tag=s.tag, kind="clear_zone", footprint=s.footprint.buffer(space.radius_m),
                  z0_m=s.z0_m, z1_m=s.z1_m)
        for s in space.soft if s.kind == "room" and space.cost.room_penalty(s.occupancy) > 0)
    occupancy = {r.tag: "living" if r.closed_to_services else r.occupancy for r in model.rooms}
    datum = {s.tag: s.elevation.meters for s in model.plan.storeys}
    for ceiling in model.ceilings:
        if (ceiling.z0_m is not None or len(ceiling.outline) < 3
                or space.cost.room_penalty(occupancy.get(ceiling.room_ref)) <= 0):
            continue
        plane = sloped_plane(model, model.plan, ceiling)
        if plane is not None:
            outline = Polygon(ceiling.outline)
            space.hard.append(HardPrism(
                tag=ceiling.room_ref, kind="clear_zone",
                footprint=outline.buffer(space.radius_m), z0_m=datum.get(ceiling.storey, 0.0),
                z1_m=max(plane.z_at(p) for p in ceiling.outline)))
    space._hard_index = space._exact = space._rail_index = None  # rebuilt on next query
    space._blocked_memo.clear()


def _vent_legs(model: Any, origin: tuple, floor_m: float, vent_d: float) -> list:
    """``(tag, a, b)``: every vent stack leg and vent run leg a branch vent may tie into.

    A vent's own system, at least this vent's size, wholly over the 905.3 line (a vertical
    is clipped to it), and within reach of the fixture in plan.
    """
    from typehaus.resolve.mep_envelopes import vent_risers

    lines = [(tag, [(*p, z) for p, z in zip(path, zs, strict=False)])
             for tag, path, zs, _d in vent_risers(model) if tag.rsplit("-", 1)[-1] == "vent"]
    lines += [(run.tag, [(*p, z) for p, z in zip(run.path, run.z_m, strict=False)])
              for run in model.pipe_runs if run.system == "vent" and run.z_m
              and (run.diameter_m or 0.0) + 1e-9 >= vent_d]
    out = []
    for tag, pts in lines:
        for a, b in zip(pts, pts[1:], strict=False):
            if max(a[2], b[2]) < floor_m:
                continue
            if a[:2] == b[:2]:
                a, b = (*a[:2], max(min(a[2], b[2]), floor_m)), (*a[:2], max(a[2], b[2]))
            elif min(a[2], b[2]) < floor_m - _TOL_M:
                continue
            near = min(abs(p[0] - origin[0]) + abs(p[1] - origin[1]) for p in (a, b))
            if near <= _STACK_REACH_M:
                out.append((near, tag, a, b))
    # The nearest few: every leg is two terminals, and the lattice's line cap is real.
    return [leg[1:] for leg in sorted(out)[:_LEGS]]


def _leg_nodes(graph: Any, legs: list) -> set[int]:
    """Lattice nodes standing on any leg, each leg tested only inside its own box."""
    import numpy as np

    xyz = np.array([(n.x, n.y, n.z) for n in graph.nodes])
    out: set[int] = set()
    for _t, a, b in legs:
        lo = np.minimum(a, b) - _TOL_M
        hi = np.maximum(a, b) + _TOL_M
        for i in np.nonzero(np.all((xyz >= lo) & (xyz <= hi), axis=1))[0]:
            if _on_leg(tuple(xyz[i]), a, b):
                out.add(int(i))
    return out


def _on_leg(p: tuple, a: tuple, b: tuple) -> bool:
    d = [b[i] - a[i] for i in range(3)]
    span = sum(c * c for c in d)
    t = 0.0 if span < 1e-12 else max(0.0, min(1.0, sum((p[i] - a[i]) * d[i]
                                                       for i in range(3)) / span))
    return math.dist(p, [a[i] + t * d[i] for i in range(3)]) < _TOL_M


def _on_drain(drain: list, at: tuple) -> tuple | None:
    """The drain's graded centreline under ``at`` — the take-off's tee, mid-leg or not."""
    for a, b in zip(drain, drain[1:], strict=False):
        span = math.dist(a[:2], b[:2])
        if span < 1e-9:
            continue
        t = ((at[0] - a[0]) * (b[0] - a[0]) + (at[1] - a[1]) * (b[1] - a[1])) / span ** 2
        if -1e-6 <= t <= 1 + 1e-6 and math.dist(
                at[:2], (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))) < 1e-3:
            return (at[0], at[1], a[2] + t * (b[2] - a[2]))
    return None


def _first_blocker(space: Any, node: Any, top_m: float) -> str:
    """What a plumb riser from the cheapest take-off meets first, for the refusal."""
    z, step = node.z, 0.25 * M_PER_IN
    while z <= top_m:
        tag = space.blocked((node.x, node.y), z)
        if tag is not None:
            return (f"; the cheapest, at ({node.x / M_PER_IN:.2f}\", "
                    f"{node.y / M_PER_IN:.2f}\"), rises into {tag} "
                    f"{(z - node.z) / M_PER_IN:.2f}\" above the arm")
        z += step
    members = getattr(space, "members", None)
    hit = None if members is None else members.riser_blocker(node.x, node.y, node.z, top_m)
    if hit is None:
        return ""
    return (f"; the cheapest, at ({node.x / M_PER_IN:.2f}\", {node.y / M_PER_IN:.2f}\"), "
            f"rises into {hit[0]}'s framing {(hit[1] - node.z) / M_PER_IN:.2f}\" above the arm "
            "(a member no hole is allowed through, or a stud plane the vent cannot fit)")


def vent_proposal(found: Any, drain: Any, ends: Any, target: str, suffix: str) -> Any:
    """The vent half of the pair, from the take-off the drain search closed its arm at."""
    from typehaus.routing.proposal import RouteProposal
    from typehaus.routing.trap_vent import vent_path

    context: VentContext = found.vent
    if found.takeoff not in context.by_drain:
        return None  # the arm reached a vented stack itself: no vent to propose
    start = context.by_drain[found.takeoff]
    nodes = vent_path(context.graph, context.dist, start,
                      level_floor_m=context.level_floor_m)
    if nodes is None:
        return None
    points = [(n.x, n.y, n.z) for n in (context.graph.nodes[i] for i in nodes)]
    tee = _on_drain(drain.points, points[0])
    if tee is not None:
        # Leave the arm at its graded centreline (905.2): the lattice node may sit off it.
        points = [tee, *(p for p in points if math.dist(p[:2], tee[:2]) > 1e-6
                         or p[2] > tee[2] + 1e-6)]
    return RouteProposal(
        tag=f"{target}-VENT-PROPOSED{suffix}", kind="pipe", points=points,
        diameter_m=context.diameter_m, serves=ends.serves, system="vent",
        cost=context.dist[start],
        notes=[f"vent for {target}'s trap arm, taken off within the Table 1002.2 limit; "
               "rises plumb to 6\" over the fixture's top (UPC 905.3) before any level leg"]
    ).snapped()
