"""``--fixture``: a bathroom-group drain as the arm's goal, a UPC 908.2 horizontal wet vent.

A tub beside a dry-vented lavatory is wet-vented by the lav's drain if the arm reaches it
within Table 1002.2 and 908.2 holds — group fixtures only, one floor, one wet-vented drain
upstream of the dry-vent connection, the water closet last. The router does not re-derive
any of that: each candidate join is graded by the check's own walk
(``resolve/mep_wet_tie.grade_hypothetical_tie``). A goal here is seeded at the arm's cost
alone, with no vent to search. ``houses/catlin/notes/mep_drain_routing_basis.md`` §14.
"""

from __future__ import annotations

import math
from typing import Any

#: Candidate drains, nearest first, and the cheapest joins graded on each.
_CANDIDATES = 4
_PER_DRAIN = 3


def wet_candidates(model: Any, fixture: str, point: tuple, floor_m: float) -> tuple[str, ...]:
    """Drains on the fixture's floor (``_nearest_main``'s gate) serving only bathroom-group
    fixtures, and not this one, nearest first."""
    from typehaus.resolve.plumbing_tables import BATHROOM_GROUP_SYMBOLS

    types = {t.tag: t.plan_symbol for t in model.plan.library.fixture_types}
    symbol = {f.tag: types.get(f.type_ref) for f in model.plan.all_elements()
              if f.element_kind == "Fixture"}
    if symbol.get(fixture) not in BATHROOM_GROUP_SYMBOLS:
        return ()
    ranked = []
    for run in model.pipe_runs:
        if (run.system != "drain" or not run.z_m or fixture in run.serves or not run.serves
                or any(symbol.get(t) not in BATHROOM_GROUP_SYMBOLS for t in run.serves)):
            continue
        near = [math.hypot(x - point[0], y - point[1])
                for (x, y), z in zip(run.path, run.z_m, strict=False)
                if floor_m - 2.0 * 0.3048 <= z <= floor_m + 0.5 * 0.3048]
        if near:
            ranked.append((min(near), run.tag))
    return tuple(tag for _d, tag in sorted(ranked)[:_CANDIDATES])


def wet_terminals(model: Any, ends: Any) -> list[tuple[float, float, float]]:
    """Lines along each candidate drain within the arm's Table 1002.2 reach of the trap:
    each segment's nearest point to it, and any vertex in reach. Nothing further is joinable."""
    from typehaus.resolve.plumbing_tables import trap_arm_limit_in

    limit = (trap_arm_limit_in(ends.diameter_m) or 0.0) * 0.0254
    runs = {r.tag: r for r in model.pipe_runs}
    o = ends.origin
    out = []
    for tag in ends.wet_candidates:
        pts = [(p[0], p[1], z) for p, z in zip(runs[tag].path, runs[tag].z_m, strict=False)]
        for a, b in zip(pts, pts[1:], strict=False):
            span = math.dist(a[:2], b[:2])
            t = 0.0 if span < 1e-9 else max(0.0, min(1.0, ((o[0] - a[0]) * (b[0] - a[0])
                                                          + (o[1] - a[1]) * (b[1] - a[1]))
                                                     / span ** 2))
            out += [p for p in ((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]),
                                 a[2] + t * (b[2] - a[2])), a, b)
                    if math.dist(p[:2], o[:2]) <= limit]
    return list(dict.fromkeys(out))


def wet_goals(model: Any, ends: Any, graph: Any, reach: dict, grade: float,
              limit_in: float, rejected: list[str] | None = None) -> dict[int, Any]:
    """``node -> WetTie`` for arm-reachable nodes on a candidate drain that grade legal.

    A join is offered only where the arm meets the drain at or above its centreline and
    within one arm diameter of it: lower is uphill, a bigger fall before the vent an S-trap.
    """
    from typehaus.cli.cmd_route_tree import TIE_TOLERANCE_M, _line_nodes
    from typehaus.resolve.mep_trap_arm import run_points, wet_vent_data
    from typehaus.resolve.mep_wet_tie import grade_hypothetical_tie
    from typehaus.routing.trap_vent import arm_invert_m

    if not ends.wet_candidates:
        return {}
    data = wet_vent_data(model)
    runs = {r.tag: r for r in model.pipe_runs}
    out: dict[int, Any] = {}
    for tag in ends.wet_candidates:
        pts = run_points(runs[tag])
        if pts is None:
            continue
        nodes = sorted(_line_nodes(graph, runs[tag].path, TIE_TOLERANCE_M) & set(reach),
                       key=lambda n: reach[n].cost)
        for n in nodes[:_PER_DRAIN]:
            node, z_arm = graph.nodes[n], arm_invert_m(reach[n], ends.weir, grade)
            z_drain = _centreline_z(pts, (node.x, node.y))
            if z_drain is None or not z_arm - ends.diameter_m - 1e-6 <= z_drain <= z_arm + 1e-6:
                continue
            arm = [(graph.nodes[i].x, graph.nodes[i].y, 0.0) for i in reach[n].nodes]
            arm = [(x, y, ends.weir - grade * _plan_ft(arm[:k + 1]) * 0.0254)
                   for k, (x, y, _z) in enumerate(arm)]
            if z_drain < z_arm - 1e-6:
                arm.append((node.x, node.y, z_drain))
            tie, notes = grade_hypothetical_tie(model, data, ends.fixture, arm, ends.radius_m,
                                                limit_in)
            if tie is not None:
                out[n] = tie
            elif rejected is not None:
                rejected += [n for n in notes if n not in rejected]
    return out


def disclosure(tie: Any, fixture: str) -> tuple[list[str], list[str]]:
    """``(notes, after_paste)`` for a proposal ending on a wet vent."""
    notes = [f"ends on {tie.parent} as a 908.2 horizontal wet vent: {tie.what}; the arm "
             f"develops {tie.arm_in:.0f}\" to it, and no vent is proposed"]
    after = [f"{run} must be Ø{d:g}\" from the join to the water-closet tie (908.2.2, whole "
             "length)" for run, d in tie.upsize]
    after += [f"add {fixture} to {vent}.serves — the check walks only vents that name it"
              for vent in tie.name_on_vent]
    return notes, after


def _plan_ft(points: list) -> float:
    return sum(math.dist(a[:2], b[:2]) for a, b in zip(points, points[1:], strict=False)) / 0.3048


def _centreline_z(pts: list, at: tuple[float, float]) -> float | None:
    for a, b in zip(pts, pts[1:], strict=False):
        span = math.dist(a[:2], b[:2])
        if span < 1e-9:
            continue
        t = ((at[0] - a[0]) * (b[0] - a[0]) + (at[1] - a[1]) * (b[1] - a[1])) / span ** 2
        foot = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        if -1e-6 <= t <= 1 + 1e-6 and math.dist(foot, at) < 0.0032:
            return a[2] + t * (b[2] - a[2])
    return None
