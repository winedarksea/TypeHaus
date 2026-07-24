"""Plumbing checks — sleeve alignment + drain slope (→ Permit-ready plan set Phase 2).

``mep.sleeve_alignment`` is the pre-pour guarantee: a cast-in-place sleeve that is more
than 1/2" off the fixture's expected drain point moves before the concrete crew pours, so
it is a CODE-tier FAIL, not an advisory suggestion.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import Service
from typehaus.model.mep import VentRun
from typehaus.resolve.vent_termination import (
    VENT_TERMINATION_CLEARANCE_M,
    derived_termination_elevation,
)

_ALIGNMENT_TOLERANCE_M = 0.0127  # 1/2"
_M_TO_IN = 39.37007874015748
_M_TO_FT = 3.280839895
_MIN_SLOPE_SMALL_IN_PER_FT = 0.25  # <= 3" diameter
_MIN_SLOPE_LARGE_IN_PER_FT = 0.125  # > 3" diameter
_LARGE_DIAMETER_M = 0.0762  # 3"
# A hand-authored termination is a dimension a builder reads off the plan set, so it only
# has to agree with the derived plane to within the 1" the elevation is drawn at.
_TERMINATION_TOLERANCE_M = 0.0254  # 1"


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    # Advisory findings never carry ERROR severity — that severity is reserved for
    # hard blockers, and permit.py's integrity gate treats any ERROR as a permit-set
    # blocker regardless of check_id.
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, result=Result.UNKNOWN)


@check(Tier.CODE, "mep.sleeve_alignment")
def sleeve_alignment(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for sleeve in ctx.model.sleeves:
        if sleeve.expected_center is None:
            out.append(_unknown(
                "mep.sleeve_alignment",
                f"sleeve {sleeve.tag} has no resolvable expected drain point "
                f"(serves_fixture={sleeve.serves_fixture})", (sleeve.tag,),
            ))
            continue
        if sleeve.offset_m <= _ALIGNMENT_TOLERANCE_M:
            out.append(_pass(
                "mep.sleeve_alignment",
                f"sleeve {sleeve.tag} is {sleeve.offset_m * _M_TO_IN:.2f}\" from its "
                "expected drain point (<= 1/2\" tolerance)", (sleeve.tag,),
            ))
            continue
        dx = (sleeve.expected_center[0] - sleeve.center[0]) * _M_TO_IN
        dy = (sleeve.expected_center[1] - sleeve.center[1]) * _M_TO_IN
        axis, delta = ("x", dx) if abs(dx) >= abs(dy) else ("y", dy)
        sign = "+" if delta >= 0 else "-"
        out.append(_fail(
            "mep.sleeve_alignment",
            f"sleeve {sleeve.tag} is {sleeve.offset_m * _M_TO_IN:.2f}\" off its expected "
            f"drain point — move sleeve {abs(delta):.1f}\" {sign}{axis}", (sleeve.tag,),
        ))
    out.extend(_missing_sleeve_findings(ctx))
    return out


def _missing_sleeve_findings(ctx: CheckContext) -> list[Finding]:
    """A storey tag alone isn't enough: multiple freestanding structures can share one
    (catlin's sunken-garden balcony slab is also tagged "second") — a fixture only needs a
    sleeve through the specific slab its footprint actually sits on."""
    from shapely.geometry import Point, Polygon

    out: list[Finding] = []
    slabs = [solid for solid in ctx.model.solids if solid.category == "slab"]
    served = {(sleeve.serves_fixture, sleeve.host_slab) for sleeve in ctx.model.sleeves
             if sleeve.serves_fixture is not None}
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    for storey in ctx.plan.storeys:
        storey_slabs = [solid for solid in slabs if solid.storey == storey.tag]
        if not storey_slabs:
            continue
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            point = Point(fixture.position.xy_m)
            host = next((s for s in storey_slabs if Polygon(s.outline).contains(point)), None)
            if host is None:
                continue  # fixture isn't over a structural slab at all
            if (fixture.tag, host.tag) not in served:
                out.append(_fail(
                    "mep.sleeve_alignment",
                    f"drain fixture {fixture.tag} sits above structural slab {host.tag} "
                    "with no sleeve serving it", (fixture.tag, host.tag),
                ))
    return out


@check(Tier.CODE, "mep.drain_slope")
def drain_slope(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain":
            continue
        if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
            out.append(_unknown(
                "mep.drain_slope", f"pipe run {run.tag} has no authored inverts to check",
                (run.tag,),
            ))
            continue
        length_ft = run.length_m * 3.280839895
        slope_in_per_ft = (run.z_start_m - run.z_end_m) * _M_TO_IN / length_ft
        minimum = (_MIN_SLOPE_SMALL_IN_PER_FT if run.diameter_m <= _LARGE_DIAMETER_M
                  else _MIN_SLOPE_LARGE_IN_PER_FT)
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
    clearance_in = VENT_TERMINATION_CLEARANCE_M * _M_TO_IN
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
            delta_in = (authored - derived) * _M_TO_IN
            if abs(delta_in) <= _TERMINATION_TOLERANCE_M * _M_TO_IN:
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
    """Each VENT-needing fixture's wet wall must continue up to the storey above."""
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
            elif fixture.wall_ref not in stacked_lower:
                out.append(_advisory_fail(
                    "mep.vent_reachability",
                    f"fixture {fixture.tag}'s wall {fixture.wall_ref} does not continue "
                    "up to the storey above — vent cannot rise", (fixture.tag, fixture.wall_ref),
                ))
            else:
                out.append(_pass(
                    "mep.vent_reachability",
                    f"fixture {fixture.tag}'s wall {fixture.wall_ref} continues up for the vent",
                    (fixture.tag,),
                ))
    return out
