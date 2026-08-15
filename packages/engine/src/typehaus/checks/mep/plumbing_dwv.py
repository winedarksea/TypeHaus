"""Drain, waste and vent checks — everything downstream of a fixture's trap.

Slope, vent termination height and reachability, trap-arm length, and the run-diameter vs
fixture-unit sizing gate. ``mep.wet_wall_occupancy`` and ``structural.wet_wall_bearing``
sit here too: the wet wall is the drain stack's wall, and both rules exist because a bored
or staggered stud is what a DWV riser does to framing.

Sizing tables are read from ``typehaus.takeoff.plumbing_calc`` — the same functions the
plumbing reader uses, so the permit finding and the public page can never disagree.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _M_TO_FT, _advisory_fail
from typehaus.checks.mep.vent_path import evaluate_vent_path
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Service
from typehaus.model.mep import VentRun
from typehaus.quantities import M_PER_IN
from typehaus.resolve.vent_termination import (
    VENT_TERMINATION_CLEARANCE_M,
    derived_termination_elevation,
)

_MIN_SLOPE_SMALL_IN_PER_FT = 0.25  # <= 3" diameter
_MIN_SLOPE_LARGE_IN_PER_FT = 0.125  # > 3" diameter
_LARGE_DIAMETER_M = 0.0762  # 3"
# A hand-authored termination is a dimension a builder reads off the plan set, so it only
# has to agree with the derived plane to within the 1" the elevation is drawn at.
_TERMINATION_TOLERANCE_M = 0.0254  # 1"


@check(Tier.CODE, "mep.drain_slope")
def drain_slope(ctx: CheckContext) -> list[Finding]:
    """Per-segment where the run carries a routed 3D path; whole-run for legacy inverts.

    Vertical drops (zero plan length) are exempt — a stack has no slope to hold. A
    reverse-sloped segment is called out as such, not just as "below minimum"."""
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain":
            continue
        minimum = (_MIN_SLOPE_SMALL_IN_PER_FT if run.diameter_m <= _LARGE_DIAMETER_M
                  else _MIN_SLOPE_LARGE_IN_PER_FT)
        if run.z_m is not None and len(run.z_m) == len(run.path):
            worst: tuple[float, int] | None = None
            for i in range(len(run.path) - 1):
                a, b = run.path[i], run.path[i + 1]
                plan_ft = (((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5) * _M_TO_FT
                if plan_ft <= 1e-6:
                    continue  # vertical drop
                seg_slope = (run.z_m[i] - run.z_m[i + 1]) / M_PER_IN / plan_ft
                if worst is None or seg_slope < worst[0]:
                    worst = (seg_slope, i)
            if worst is None:
                out.append(_pass("mep.drain_slope",
                                 f"pipe run {run.tag} is all vertical drop — no "
                                 "horizontal segment to hold slope", (run.tag,)))
            elif worst[0] < -1e-9:
                out.append(_fail(
                    "mep.drain_slope",
                    f"pipe run {run.tag} segment {worst[1]} slopes BACKWARD "
                    f"({worst[0]:.3f}\"/ft) — water stands in it", (run.tag,)))
            elif worst[0] >= minimum - 1e-9:
                out.append(_pass(
                    "mep.drain_slope",
                    f"pipe run {run.tag}: every segment holds >= {minimum}\"/ft "
                    f"(flattest {worst[0]:.3f}\"/ft)", (run.tag,)))
            else:
                out.append(_fail(
                    "mep.drain_slope",
                    f"pipe run {run.tag} segment {worst[1]} slopes {worst[0]:.3f}\"/ft, "
                    f"below the {minimum}\"/ft minimum", (run.tag,)))
            continue
        if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
            out.append(_unknown(
                "mep.drain_slope", f"pipe run {run.tag} has no authored inverts to check",
                (run.tag,),
            ))
            continue
        length_ft = run.length_m * 3.280839895
        slope_in_per_ft = (run.z_start_m - run.z_end_m) / M_PER_IN / length_ft
        if slope_in_per_ft >= minimum - 1e-9:
            out.append(_pass(
                "mep.drain_slope",
                f"pipe run {run.tag} slopes {slope_in_per_ft:.3f}\"/ft (>= {minimum}\"/ft "
                f"minimum)", (run.tag,),
            ))
        else:
            out.append(_fail(
                "mep.drain_slope",
                f"pipe run {run.tag} slopes {slope_in_per_ft:.3f}\"/ft, below the "
                f"{minimum}\"/ft minimum", (run.tag,),
            ))
    return out


@check(Tier.ADVISORY, "mep.vent_termination_height")
def vent_termination_height(ctx: CheckContext) -> list[Finding]:
    """A hand-authored ``roof_termination_elevation`` must agree with the roof it clears.

    The resolver terminates every riser 12" above the roof plane *at the riser's own plan
    point*, so an authored absolute is an assertion, not an input. Flagging the disagreement
    is what catches a riser authored above its own ridge — the plan set prints the authored
    number, and a builder sets the pipe from the print.
    """
    out: list[Finding] = []
    clearance_in = VENT_TERMINATION_CLEARANCE_M / M_PER_IN
    for storey in ctx.plan.storeys:
        for vent in ctx.plan.storey_elements(storey.tag):
            if not isinstance(vent, VentRun):
                continue
            derived = derived_termination_elevation(ctx.model, vent)
            if derived is None:
                out.append(_unknown(
                    "mep.vent_termination_height",
                    f"vent {vent.tag} clears no derivable roof (wall_ref={vent.wall_ref!r})",
                    (vent.tag,),
                ))
                continue
            if vent.roof_termination_elevation is None:
                out.append(_pass(
                    "mep.vent_termination_height",
                    f"vent {vent.tag} terminates at {derived * _M_TO_FT:.2f}', "
                    f"{clearance_in:.0f}\" above the roof plane at its riser", (vent.tag,),
                ))
                continue
            authored = vent.roof_termination_elevation.meters
            delta_in = (authored - derived) / M_PER_IN
            if abs(delta_in) <= _TERMINATION_TOLERANCE_M / M_PER_IN:
                out.append(_pass(
                    "mep.vent_termination_height",
                    f"vent {vent.tag}'s authored termination matches the roof plane "
                    f"{clearance_in:.0f}\" clearance", (vent.tag,),
                ))
            else:
                out.append(_advisory_fail(
                    "mep.vent_termination_height",
                    f"vent {vent.tag} authors a {authored * _M_TO_FT:.2f}' termination "
                    f"but the roof plane at its riser puts it at "
                    f"{derived * _M_TO_FT:.2f}' — {abs(delta_in):.0f}\" too "
                    f"{'high' if delta_in > 0 else 'low'}", (vent.tag,),
                ))
    return out


@check(Tier.ADVISORY, "mep.vent_reachability")
def vent_reachability(ctx: CheckContext) -> list[Finding]:
    """Every VENT-needing fixture must have a vent path that reaches the roof.

    Two legal paths, in the order a plumber would prefer them: rise inside the fixture's own
    wet wall where that wall continues to the storey above, or — where it stops at its own
    top plate — take the vent above the flood-level rim and run it to a ``VentRun`` chase
    that does reach the roof.  The second path is authored, never inferred
    (``checks/mep/vent_path.py``), so an unvented water closet still fails loudly.
    """
    out: list[Finding] = []
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    stacked_lower = {edge.lower_wall for edge in ctx.model.stack_edges}
    for storey in ctx.plan.storeys:
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.VENT not in fixture_type.needs:
                continue
            if fixture.wall_ref is None:
                out.append(_unknown(
                    "mep.vent_reachability", f"fixture {fixture.tag} has no wall_ref to vent",
                    (fixture.tag,),
                ))
                continue
            if fixture.wall_ref in stacked_lower:
                out.append(_pass(
                    "mep.vent_reachability",
                    f"fixture {fixture.tag}'s wall {fixture.wall_ref} continues up for the vent",
                    (fixture.tag,),
                ))
                continue
            wall = ctx.model.wall(fixture.wall_ref)
            if wall is None:
                out.append(_unknown(
                    "mep.vent_reachability",
                    f"fixture {fixture.tag} references missing wall {fixture.wall_ref}",
                    (fixture.tag, fixture.wall_ref),
                ))
                continue
            out.append(_vent_path_finding(ctx, fixture, wall))
    return out


def _vent_path_finding(ctx: CheckContext, fixture, wall) -> Finding:
    """Grade the authored offset-vent path for a fixture whose wet wall stops short."""
    path = evaluate_vent_path(ctx.model, fixture.tag, wall)
    tags = (fixture.tag, fixture.wall_ref)
    if path.run_tag is None:
        return _advisory_fail(
            "mep.vent_reachability",
            f"fixture {fixture.tag}'s wall {fixture.wall_ref} does not continue up to the "
            "storey above and no vent run carries it onward — author a VENT PipeRun from "
            "that wet wall to a VentRun chase", tags,
        )
    if path.chase_tag is None:
        return _advisory_fail(
            "mep.vent_reachability",
            f"fixture {fixture.tag}'s vent run {path.run_tag} ends at no VentRun chase — "
            "the vent has no way through the roof", (fixture.tag, path.run_tag),
        )
    if not path.touches_wet_wall:
        return _advisory_fail(
            "mep.vent_reachability",
            f"fixture {fixture.tag}'s vent run {path.run_tag} never reaches its wet wall "
            f"{fixture.wall_ref} — the vent cannot leave the fixture",
            (fixture.tag, path.run_tag, fixture.wall_ref),
        )
    return _pass(
        "mep.vent_reachability",
        f"fixture {fixture.tag} vents through {path.run_tag} to the {path.chase_tag} chase "
        f"({fixture.wall_ref} stops at its own ceiling)", (fixture.tag, path.run_tag),
    )


@check(Tier.CODE, "mep.wet_wall_occupancy")
def wet_wall_occupancy_check(ctx: CheckContext) -> list[Finding]:
    """Every in-wall pipe segment must actually fit the wall it claims (the pipe analogue
    of the duct bay-occupancy rule). Long horizontal travel through a single-layout wall
    is advisory — legal, but every stud on the way gets bored."""
    from typehaus.resolve.mep import wet_wall_occupancy

    cid = "mep.wet_wall_occupancy"
    out: list[Finding] = []
    any_refs = False
    for run in ctx.model.pipe_runs:
        if not run.wall_refs or not any(w is not None for w in run.wall_refs):
            continue
        any_refs = True
        problems = wet_wall_occupancy(run, ctx.model)
        if not problems:
            walls = sorted({w for w in run.wall_refs if w is not None})
            out.append(_pass(cid, f"run {run.tag} fits its declared wall(s) "
                                  f"{', '.join(walls)}", (run.tag, *walls)))
            continue
        for problem in problems:
            tags = (run.tag, problem["wall"]) if problem["wall"] else (run.tag,)
            if problem["kind"] == "long_horizontal":
                out.append(_advisory_fail(cid, problem["message"], tags))
            else:
                out.append(_fail(cid, problem["message"], tags))
    if not out and any_refs:
        return out
    return out


@check(Tier.CODE, "structural.wet_wall_bearing")
def wet_wall_bearing(ctx: CheckContext) -> list[Finding]:
    """A staggered-stud wall must never be load-bearing (neither face's studs align with
    the plates' bearing), and a bearing wall that hosts plumbing must keep continuous
    full-depth studs — the center-line rule this house is framed around."""
    from typehaus.model.elements import Wall
    from typehaus.model.enums import LayerFunction, PartitionLayout, StructuralRole

    cid = "structural.wet_wall_bearing"
    wet_walls = {w for run in ctx.model.pipe_runs for w in run.wall_refs if w is not None}
    out: list[Finding] = []
    for element in ctx.plan.all_elements():
        if not isinstance(element, Wall):
            continue
        assembly = ctx.plan.library.resolve_assembly(element.assembly)
        if assembly is None:
            continue
        spec = next((layer.framing for layer in assembly.layers
                     if layer.function is LayerFunction.STRUCTURE
                     and layer.framing is not None), None)
        if spec is None:
            continue
        staggered = spec.layout is PartitionLayout.STAGGERED
        bearing = element.structural_role is StructuralRole.BEARING
        if staggered and bearing:
            out.append(_fail(
                cid, f"wall {element.tag} is BEARING but framed with staggered studs "
                     f"({element.assembly}) — neither face's studs carry the plates' "
                     "load; use a continuous-stud assembly", (element.tag,)))
        elif bearing and element.tag in wet_walls:
            out.append(_pass(
                cid, f"bearing wall {element.tag} hosts plumbing with continuous "
                     f"{spec.member} studs ({element.assembly})", (element.tag,)))
        elif staggered and element.tag in wet_walls:
            out.append(_pass(
                cid, f"wet wall {element.tag} is non-bearing staggered "
                     f"({element.assembly}) — continuous cavity, no bored studs",
                (element.tag,)))
    return out


@check(Tier.CODE, "mep.pipe_sizing")
def pipe_sizing(ctx: CheckContext) -> list[Finding]:
    """Run diameter vs the fixture units it carries (MN Plumbing Code / UPC tables in
    takeoff/plumbing_calc.py — the reader shows the same numbers). Drain runs are graded
    on the union of ``serves`` over their whole upstream subtree, derived geometrically
    (``resolve/mep_queries.py::accumulated_serves``) — trusting each run's own ``serves`` list
    let a branch's load silently escape the main it discharges into. Supply runs still
    grade on their authored ``serves`` (no supply topology derivation yet). UNKNOWN
    whenever the serves graph is incomplete: a partial sum passed off as a load is how a
    house ends up with a 1.5" line feeding three fixtures."""
    from typehaus.resolve.mep import accumulated_serves
    from typehaus.takeoff.plumbing_calc import (
        branch_load,
        fixture_units,
        required_drain_diameter_in,
        required_supply_size_in,
    )

    cid = "mep.pipe_sizing"
    units_by_tag = {row.tag: row for row in fixture_units(ctx.plan)}
    rolled_up = accumulated_serves(ctx.model.pipe_runs)
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system not in ("drain", "water_hot", "water_cold"):
            continue
        serves = rolled_up.get(run.tag, run.serves) if run.system == "drain" else run.serves
        if not serves:
            continue
        load, unresolved = branch_load(serves, units_by_tag, run.system)
        if load is None:
            out.append(_unknown(
                cid, f"run {run.tag} serves {', '.join(unresolved)}, which carry no "
                     "fixture-unit table row — its load cannot be summed", (run.tag,)))
            continue
        diameter_in = run.diameter_m / M_PER_IN
        required = (required_drain_diameter_in(load) if run.system == "drain"
                    else required_supply_size_in(load))
        unit_name = "DFU" if run.system == "drain" else "WSFU"
        if required is None:
            out.append(_fail(
                cid, f"run {run.tag} carries {load:g} {unit_name} — beyond the sizing "
                     "table; it needs an engineered size", (run.tag,)))
        elif diameter_in + 0.06 >= required:
            out.append(_pass(
                cid, f"run {run.tag} Ø{diameter_in:.2f}\" carries {load:g} {unit_name} "
                     f"(needs >= {required}\")", (run.tag,)))
        else:
            out.append(_fail(
                cid, f"run {run.tag} Ø{diameter_in:.2f}\" carries {load:g} {unit_name} "
                     f"but the table requires {required}\"", (run.tag,)))
    return out


@check(Tier.CODE, "mep.trap_arm_length")
def trap_arm_length(ctx: CheckContext) -> list[Finding]:
    """Distance from each fixture's drain point to its vent takeoff, against the
    trap-arm table. The vent takeoff is the nearest point of a VENT run serving the
    fixture, or the fixture's wet wall where that wall continues up (stack vent).
    UNKNOWN when neither exists — never inferred."""
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points

    from typehaus.model.enums import Service
    from typehaus.resolve.mep import _expected_drain_point
    from typehaus.takeoff.plumbing_calc import trap_arm_limit_in

    cid = "mep.trap_arm_length"
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    stacked_lower = {edge.lower_wall for edge in ctx.model.stack_edges}
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            drain_point = _expected_drain_point(ctx.model, fixture.tag)
            if drain_point is None:
                out.append(_unknown(cid, f"fixture {fixture.tag} has no resolvable "
                                         "drain point", (fixture.tag,)))
                continue
            drain_runs = [r for r in ctx.model.pipe_runs
                          if r.system == "drain" and fixture.tag in r.serves]
            if not drain_runs:
                out.append(_unknown(cid, f"fixture {fixture.tag} has no drain run "
                                         "serving it yet", (fixture.tag,)))
                continue
            trap_arm_d = min(r.diameter_m for r in drain_runs)
            limit_in = trap_arm_limit_in(trap_arm_d)
            if limit_in is None:
                out.append(_unknown(
                    cid, f"fixture {fixture.tag}'s trap arm Ø"
                         f"{trap_arm_d / M_PER_IN:.2f}\" has no table row",
                    (fixture.tag,)))
                continue
            vent_point = None
            vent_via = None
            vent_runs = [r for r in ctx.model.pipe_runs
                         if r.system == "vent" and fixture.tag in r.serves]
            if vent_runs:
                # `nearest_points`, not project()/interpolate(): a vent that tees off right
                # at the drain point — which is where a floor-drained fixture's vent tee
                # actually sits — makes `LineString.project` warn about a NaN it then
                # returns 0.0 for. Same answer, no spurious RuntimeWarning on every build.
                nearest = min(
                    (nearest_points(LineString(r.path), Point(drain_point))[0]
                     for r in vent_runs if len(r.path) >= 2),
                    key=lambda p: p.distance(Point(drain_point)), default=None)
                if nearest is not None:
                    vent_point, vent_via = (nearest.x, nearest.y), vent_runs[0].tag
            if vent_point is None and fixture.wall_ref in stacked_lower:
                wall = ctx.model.wall(fixture.wall_ref)
                if wall is not None:
                    axis_line = LineString(wall.axis)
                    p = axis_line.interpolate(axis_line.project(Point(drain_point)))
                    vent_point, vent_via = (p.x, p.y), f"stack in {fixture.wall_ref}"
            if vent_point is None:
                out.append(_unknown(
                    cid, f"fixture {fixture.tag} has no vent run or continuing wet wall "
                         "to measure a trap arm against", (fixture.tag,)))
                continue
            arm_in = (((vent_point[0] - drain_point[0]) ** 2
                       + (vent_point[1] - drain_point[1]) ** 2) ** 0.5) / M_PER_IN
            if arm_in <= limit_in + 1e-6:
                out.append(_pass(
                    cid, f"fixture {fixture.tag}'s trap arm runs {arm_in:.0f}\" to its "
                         f"vent ({vent_via}), within the {limit_in:.0f}\" limit for "
                         f"Ø{trap_arm_d / M_PER_IN:.2f}\"", (fixture.tag,)))
            else:
                out.append(_fail(
                    cid, f"fixture {fixture.tag}'s trap arm runs {arm_in:.0f}\" to its "
                         f"vent ({vent_via}) — over the {limit_in:.0f}\" limit for "
                         f"Ø{trap_arm_d / M_PER_IN:.2f}\"", (fixture.tag,)))
    return out
