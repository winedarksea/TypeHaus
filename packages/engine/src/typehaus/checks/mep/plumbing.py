"""Plumbing checks — sleeve alignment + drain slope (→ Permit-ready plan set Phase 2).

``mep.sleeve_alignment`` is the pre-pour guarantee: a cast-in-place sleeve that is more
than 1/2" off the fixture's expected drain point moves before the concrete crew pours, so
it is a CODE-tier FAIL, not an advisory suggestion.
"""

from __future__ import annotations

from typehaus.checks.mep.vent_path import evaluate_vent_path
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import PipeSystem, Service
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
        if sleeve.serves_fixture is None:
            # A supply riser, a wall crossing, a condensate drop: no fixture, so there is no
            # flange for the sleeve to line up under and nothing here to grade. Their
            # positions are not unchecked — `mep.sleeve_coverage` holds every one of them to
            # a routed run actually passing through it, which is the stronger contract.
            continue
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


# A frost-free hydrant's shutoff has to sit below the frost line, not merely below grade:
# the whole point of the fixture is that the valve is deep enough never to freeze and the
# barrel drains back to it. 72" is the bury this project specifies; MN frost design is 42",
# so the margin is deliberate and the check holds the authored number rather than the code
# minimum — a hydrant ordered with a 6' bury and installed at 4' is the defect.
_HYDRANT_BURY_M = 1.8288  # 72"


@check(Tier.CODE, "mep.hydrant_freeze_depth")
def hydrant_freeze_depth(ctx: CheckContext) -> list[Finding]:
    """A frost-free hydrant's supply must stay below frost for its whole buried length.

    Three things make a hydrant frost-free, and this check reports honestly on all three
    rather than passing silently on the two it cannot see:

    1. **Bury depth at the shutoff** — geometric, and a hard FAIL. The valve is at the deep
       end of the supply run; if that end is shallower than the specified bury, the fixture
       is not frost-free no matter what was ordered.
    2. **No high point along the run** — also geometric, also a FAIL. This is the failure
       people actually get: a supply routed up into the building and back down freezes at
       the high point even though both ends are deep. A run whose shallowest point is above
       frost has a freeze there.
    3. **The interior shutoff and the outlet's vacuum breaker** — UNKNOWN. The model has no
       valve or backflow-preventer element, so there is nothing to evaluate; both are
       recorded on the ``FixtureType.source`` and belong on the plumbing schedule. Reporting
       UNKNOWN names the modelling gap; reporting PASS would claim a review that did not
       happen (#32).
    """
    cid = "mep.hydrant_freeze_depth"
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    hydrants = [
        element for storey in ctx.plan.storeys
        for element in ctx.plan.storey_elements(storey.tag)
        if element.element_kind == "Fixture"
        and (types.get(element.type_ref) is not None
             and Service.WATER_COLD in types[element.type_ref].needs
             and (types[element.type_ref].plan_symbol == "hydrant"))
    ]
    if not hydrants:
        return []

    grade = ctx.plan.project.site.grade.meters
    supply = [run for run in ctx.model.pipe_runs if run.system == PipeSystem.WATER_COLD.value]
    out: list[Finding] = []
    for hydrant in hydrants:
        feeds = [run for run in supply if hydrant.tag in run.serves]
        if not feeds:
            out.append(_fail(cid, f"hydrant {hydrant.tag} has no WATER_COLD supply run "
                                  "serving it — nothing carries water to it, and nothing "
                                  "records how deep its shutoff sits",
                             (hydrant.tag,)))
            continue
        for run in feeds:
            if run.z_m is not None and len(run.z_m) >= 2:
                # Walk every vertex, not just the endpoints — a routed run freezes at its
                # shallowest point anywhere along it. The terminal standpipe (a repeated
                # final plan point rising through the slab) is the hydrant's own barrel,
                # which self-drains to the buried shutoff: it is exempt by design.
                elevations = list(run.z_m)
                while (len(elevations) >= 2 and len(run.path) >= 2
                       and run.path[-1] == run.path[-2]
                       and elevations[-1] > elevations[-2] + 1e-9):
                    elevations.pop()
            else:
                elevations = [z for z in (run.z_start_m, run.z_end_m) if z is not None]
            if not elevations:
                out.append(_unknown(cid, f"supply run {run.tag} authors no elevations, so "
                                         "its bury depth cannot be evaluated",
                                    (hydrant.tag, run.tag)))
                continue
            deepest = grade - min(elevations)
            shallowest = grade - max(elevations)
            if deepest + 1e-9 < _HYDRANT_BURY_M:
                out.append(_fail(
                    cid, f"hydrant {hydrant.tag}'s shutoff is buried "
                         f"{deepest * _M_TO_IN:.0f}\" on {run.tag}, under the "
                         f"{_HYDRANT_BURY_M * _M_TO_IN:.0f}\" this fixture is specified for",
                    (hydrant.tag, run.tag)))
            elif shallowest + 1e-9 < _HYDRANT_BURY_M:
                out.append(_fail(
                    cid, f"supply run {run.tag} rises to {shallowest * _M_TO_IN:.0f}\" "
                         f"below grade — above the {_HYDRANT_BURY_M * _M_TO_IN:.0f}\" bury "
                         f"{hydrant.tag} needs. A supply line freezes at its high point, "
                         "not at its ends",
                    (hydrant.tag, run.tag)))
            else:
                out.append(_pass(
                    cid, f"{hydrant.tag} is fed by {run.tag} at "
                         f"{deepest * _M_TO_IN:.0f}\" below grade over its whole length",
                    (hydrant.tag, run.tag)))
        # The penetration the supply comes up through: a hydrant whose sleeve is missing or
        # filed as a drain will be cored after the pour.
        sleeves = [s for s in ctx.model.sleeves if s.serves_fixture == hydrant.tag]
        if not sleeves:
            out.append(_fail(cid, f"hydrant {hydrant.tag} has no sleeve serving it — its "
                                  "supply has no pre-poured way through the slab",
                             (hydrant.tag,)))
        else:
            out.append(_pass(cid, f"{hydrant.tag} rises through {sleeves[0].tag}",
                             (hydrant.tag, sleeves[0].tag)))
        out.append(_unknown(
            cid, f"{hydrant.tag}'s interior shutoff and its outlet's hose-bib vacuum "
                 "breaker are recorded on the fixture type's `source` and belong on the "
                 "plumbing schedule; the model has no valve or backflow-preventer element, "
                 "so neither can be evaluated here",
            (hydrant.tag,)))
    return out


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
                seg_slope = (run.z_m[i] - run.z_m[i + 1]) * _M_TO_IN / plan_ft
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
        slope_in_per_ft = (run.z_start_m - run.z_end_m) * _M_TO_IN / length_ft
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


# ---------------------------------------------------------------------------------------
# Routed-run checks (→ Plumbing improvement pass). All geometry derivations live in
# resolve/mep.py (wet_wall_occupancy, concrete_crossings) and the fixture-unit tables in
# takeoff/plumbing_calc.py — this module only turns them into findings, so the plumbing
# reader and the permit set read the same numbers.

_UNDER_SLAB_COVER_M = 0.0254  # pipe crown clears the slab underside by >= 1" bedding
_SEWER_INVERT_TOLERANCE_M = 0.0127  # 1/2" — cast-in, like the sleeve alignment gate


@check(Tier.CODE, "mep.sleeve_coverage")
def sleeve_coverage(ctx: CheckContext) -> list[Finding]:
    """Every concrete crossing of a routed pipe must land in a cast-in sleeve, and every
    sleeve must have a crossing (or, pre-routing, a served fixture) to justify it.

    An unsleeved crossing is the pour-day defect this whole pass exists to prevent: the
    concrete cures and the run gets cored. A sleeve with no routed run near it is graded
    UNKNOWN rather than FAIL while its plumbing is not yet routed — the fixture-convention
    ``mep.sleeve_alignment`` still guards its position."""
    from typehaus.resolve.mep import concrete_crossings

    cid = "mep.sleeve_coverage"
    out: list[Finding] = []
    crossings = concrete_crossings(ctx.model)
    claimed: set[str] = set()
    for crossing in crossings:
        if crossing["sleeve"] is not None:
            claimed.add(crossing["sleeve"])
            out.append(_pass(
                cid, f"run {crossing['run']} crosses {crossing['host']} through sleeve "
                     f"{crossing['sleeve']}", (crossing["run"], crossing["sleeve"])))
        else:
            x, y = crossing["point"]
            out.append(_fail(
                cid, f"run {crossing['run']} (Ø{crossing['diameter_m'] * _M_TO_IN:.1f}\") "
                     f"passes through {crossing['host_category']} {crossing['host']} at "
                     f"({x * _M_TO_FT:.1f}', {y * _M_TO_FT:.1f}') with no cast-in sleeve "
                     "— it gets cored after the pour",
                (crossing["run"], crossing["host"])))
    # A sleeve is only "stale" against a routed run of its own purpose family — a cold
    # supply serving FX-1 says nothing about where FX-1's *drain* sleeve belongs.
    purpose_systems = {"drain": ("drain",), "vent": ("vent",),
                       "water_cold": ("water_cold",), "water_hot": ("water_hot",)}
    routed_by_system: dict[str, set[str]] = {}
    for run in ctx.model.pipe_runs:
        if run.z_m is not None:
            routed_by_system.setdefault(run.system, set()).update(run.serves)
    for sleeve in ctx.model.sleeves:
        if sleeve.tag in claimed:
            continue
        if (sleeve.host_category == "footing" and sleeve.center_z_m is not None
                and sleeve.center_z_m < sleeve.z0_m - 1e-6):
            # An under-footing protection sleeve (IRC P2604): the pipe passes *below* the
            # bearing plane, so `concrete_crossings` — which walks through-crossings of a
            # solid's own z-band — structurally cannot ever claim it, and reporting UNKNOWN
            # here would be permanent noise. `mep.footing_clearance` is the check that
            # requires these and matches run against sleeve; it owns them.
            continue
        routed_serves: set[str] = set()
        for system in purpose_systems.get(sleeve.purpose, ()):
            routed_serves |= routed_by_system.get(system, set())
        if sleeve.serves_fixture is not None and sleeve.serves_fixture in routed_serves:
            out.append(_fail(
                cid, f"sleeve {sleeve.tag} is cast into {sleeve.host_slab} but the routed "
                     f"run serving {sleeve.serves_fixture} never passes through it — a "
                     "stale sleeve position or a mis-routed run",
                (sleeve.tag, sleeve.host_slab)))
        else:
            out.append(_unknown(
                cid, f"sleeve {sleeve.tag} has no routed run to check against yet "
                     f"(serves {sleeve.serves_fixture})", (sleeve.tag,)))
    return out


@check(Tier.CODE, "mep.under_slab_burial")
def under_slab_burial(ctx: CheckContext) -> list[Finding]:
    """A drain running under a slab must actually clear its underside — a crown poured
    into the bottom inch of the slab is a void former, not a pipe with bedding."""
    from shapely.geometry import LineString, Polygon

    cid = "mep.under_slab_burial"
    # Only slabs bearing on grade: below a slab-on-grade is soil, and a pipe there is
    # buried with bedding. Below a suspended structural deck is a room — a ceiling-hung
    # pipe under it needs no cover. A slab is suspended when any resolved room of a lower
    # storey overlaps its footprint.
    storey_elevation = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    room_polys = [(storey_elevation.get(room.storey, 0.0), Polygon(room.clear_face))
                  for room in ctx.model.rooms if len(room.clear_face) >= 3]
    slabs = []
    for s in ctx.model.solids:
        if s.category != "slab" or len(s.outline) < 3:
            continue
        footprint = Polygon(s.outline)
        suspended = any(elev < s.z0_m - 0.1 and poly.intersects(footprint)
                        for elev, poly in room_polys)
        if not suspended:
            slabs.append((s, footprint))
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or run.z_m is None:
            continue
        worst: tuple[float, str] | None = None
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            if ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 < 1e-6:
                continue  # vertical drops are the sleeved crossings
            crown = max(run.z_m[i], run.z_m[i + 1]) + run.diameter_m / 2.0
            for slab, footprint in slabs:
                if not LineString((a, b)).intersects(footprint):
                    continue
                if crown >= slab.z1_m - 1e-6:
                    continue  # above the slab — not an under-slab segment
                gap = slab.z0_m - crown
                if worst is None or gap < worst[0]:
                    worst = (gap, slab.tag)
        if worst is None:
            continue  # this run has no under-slab segment; nothing here to grade
        gap, slab_tag = worst
        if gap >= _UNDER_SLAB_COVER_M - 1e-9:
            out.append(_pass(
                cid, f"run {run.tag}'s crown clears {slab_tag}'s underside by "
                     f"{gap * _M_TO_IN:.1f}\" (>= {_UNDER_SLAB_COVER_M * _M_TO_IN:.0f}\")",
                (run.tag, slab_tag)))
        else:
            out.append(_fail(
                cid, f"run {run.tag}'s crown sits {gap * _M_TO_IN:.1f}\" below "
                     f"{slab_tag}'s underside — under the "
                     f"{_UNDER_SLAB_COVER_M * _M_TO_IN:.0f}\" bedding cover it needs",
                (run.tag, slab_tag)))
    return out


class _Pour:
    """One continuous concrete pour: the footings that touch, measured as one."""

    def __init__(self, members):
        self.tags = frozenset(m.tag for m in members)
        self.tag = " + ".join(sorted(self.tags))
        # The shallowest bearing plane in the group governs: it is the one a pipe below the
        # group is closest to, and the one whose influence line reaches furthest.
        self.z0_m = min(m.z0_m for m in members)


def _footing_pours(solids, polygon_type):
    """Group footing solids into pours, unioning the footprints that abut.

    Same bearing elevation and touching in plan is the test — two footings at different
    depths meeting at a step are two pours, and each keeps its own edge.
    """
    from shapely.ops import unary_union

    remaining = [(s, polygon_type(s.outline)) for s in solids]
    pours = []
    while remaining:
        seed, seed_poly = remaining.pop()
        members, shapes = [seed], [seed_poly]
        grew = True
        while grew:
            grew = False
            for candidate in list(remaining):
                solid, poly = candidate
                if abs(solid.z0_m - seed.z0_m) > 1e-6:
                    continue
                if any(poly.distance(shape) <= 1e-6 for shape in shapes):
                    members.append(solid)
                    shapes.append(poly)
                    remaining.remove(candidate)
                    grew = True
        pours.append((_Pour(members), unary_union(shapes)))
    return pours


@check(Tier.CODE, "mep.footing_clearance")
def footing_clearance(ctx: CheckContext) -> list[Finding]:
    """A pipe deeper than a footing's bearing plane must stay outside its 45° influence
    line: lateral offset >= how far below the footing bottom the pipe sits. A crossing
    *through* the footing is legal only via a sleeve (mep.sleeve_coverage owns that).

    Abutting footings at the same bearing elevation are measured as one pour
    (``_footing_pours``). A strip footing is split into several ``Footing`` elements
    wherever the wall above it is — at a stem gap under a door, say — and the joints that
    creates are construction joints in continuous concrete, not free edges. Measuring the
    influence line off one would fail a pipe for being near the middle of a footing.
    """
    from shapely.geometry import LineString, Polygon

    from shapely.geometry import Point

    cid = "mep.footing_clearance"
    footings = _footing_pours([s for s in ctx.model.solids
                               if s.category == "footing" and len(s.outline) >= 3], Polygon)
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.z_m is None:
            continue
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            seg = LineString((a, b)) if ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) > 1e-12 \
                else LineString((a, (a[0] + 1e-9, a[1])))
            invert = min(run.z_m[i], run.z_m[i + 1])
            for footing, footprint in footings:
                depth_below = footing.z0_m - invert
                if depth_below <= 1e-9:
                    continue  # pipe is above the bearing plane — no influence
                if seg.intersects(footprint):
                    # Passing under (or through) the footing: legal per IRC P2604 only
                    # inside a protection sleeve / relieving arch authored on the footing.
                    protected = any(
                        s.host_slab in footing.tags
                        and seg.distance(Point(s.center)) < 0.3
                        for s in ctx.model.sleeves)
                    if protected:
                        out.append(_pass(
                            cid, f"run {run.tag} passes under footing {footing.tag} "
                                 "through an authored protection sleeve (IRC P2604)",
                            (run.tag, footing.tag)))
                    else:
                        out.append(_fail(
                            cid, f"run {run.tag} segment {i} passes under footing "
                                 f"{footing.tag} {depth_below * _M_TO_IN:.0f}\" below its "
                                 "bearing plane with no protection sleeve (IRC P2604)",
                            (run.tag, footing.tag)))
                    continue
                # ``.boundary``, not ``.exterior``: a pour is a union, which can come back as
                # a MultiPolygon when two footings meet at a corner only, and that has no
                # ``exterior``. The boundary is also the more correct edge — a hole through a
                # pour is as much an edge as its outside is.
                distance = seg.distance(footprint.boundary)
                if distance + 1e-9 < depth_below:
                    protected = any(
                        s.host_slab in footing.tags
                        and seg.distance(Point(s.center)) < 0.3
                        for s in ctx.model.sleeves)
                    if protected:
                        out.append(_pass(
                            cid, f"run {run.tag} encroaches on footing {footing.tag}'s "
                                 "influence line at an authored protection point "
                                 "(IRC P2604)", (run.tag, footing.tag)))
                        continue
                    out.append(_fail(
                        cid, f"run {run.tag} segment {i} sits "
                             f"{depth_below * _M_TO_IN:.0f}\" below footing "
                             f"{footing.tag}'s bearing plane only "
                             f"{distance * _M_TO_IN:.0f}\" away — inside its 45° "
                             "influence line; deepen the footing or move the run",
                        (run.tag, footing.tag)))
    if not out:
        routed = [r for r in ctx.model.pipe_runs if r.z_m is not None]
        if routed:
            out.append(_pass(cid, f"{len(routed)} routed runs all clear every footing's "
                                  "45° influence line", ()))
    return out


@check(Tier.CODE, "mep.sewer_exit_invert")
def sewer_exit_invert(ctx: CheckContext) -> list[Finding]:
    """The building drain's invert at every cast-in horizontal sleeve must match the
    centerline cast there — the one joint nobody can move after the pour.

    Two kinds of crossing qualify, because the foundation's own geometry decides which one a
    house gets. Where the drain leaves *through* concrete, `concrete_crossings` finds it. But
    where the sewer connection sits below the slab — deep, as cold climates bury them — the
    walls have already stopped at the slab and the drain leaves *under* a footing inside a
    protection sleeve (IRC P2604). That is not a through-crossing, so it has to be matched by
    proximity instead, with the invert interpolated along the run at the sleeve's plan point.
    """
    from typehaus.resolve.mep import concrete_crossings

    cid = "mep.sewer_exit_invert"
    out: list[Finding] = []
    exits = [s for s in ctx.model.sleeves
             if s.axis == "horizontal" and s.purpose == "drain"]
    if not exits:
        return []
    crossings_by_sleeve = {c["sleeve"]: c for c in concrete_crossings(ctx.model)
                           if c["sleeve"] is not None}
    for sleeve in exits:
        if sleeve.center_z_m is None:
            out.append(_unknown(cid, f"horizontal sleeve {sleeve.tag} authors no "
                                     "center_elevation", (sleeve.tag,)))
            continue
        crossing = crossings_by_sleeve.get(sleeve.tag)
        if crossing is None:
            crossing = _under_footing_crossing(ctx, sleeve)
        if crossing is None:
            out.append(_unknown(cid, f"no routed drain run reaches exit sleeve "
                                     f"{sleeve.tag} yet", (sleeve.tag,)))
            continue
        run_tag = crossing["run"]
        # The crossing's z is the pipe *invert* at the wall; the sleeve is set to the
        # pipe centerline, half a diameter above it.
        z_at = crossing["z_m"] + crossing["diameter_m"] / 2.0
        delta = z_at - sleeve.center_z_m
        if abs(delta) <= _SEWER_INVERT_TOLERANCE_M:
            out.append(_pass(
                cid, f"drain {run_tag} meets exit sleeve {sleeve.tag} within "
                     f"{abs(delta) * _M_TO_IN:.2f}\" of its cast centerline",
                (run_tag, sleeve.tag)))
        else:
            out.append(_fail(
                cid, f"drain {run_tag} arrives {abs(delta) * _M_TO_IN:.1f}\" "
                     f"{'above' if delta > 0 else 'below'} exit sleeve {sleeve.tag}'s "
                     "cast centerline", (run_tag, sleeve.tag)))
    return out


def _under_footing_crossing(ctx: CheckContext, sleeve) -> dict | None:
    """Match an under-footing protection sleeve to the drain run threading it.

    Mirrors how `mep.footing_clearance` claims the same sleeve — nearest drain segment whose
    plan line passes within the sleeve's own radius of its center — and interpolates the
    run's invert to that point so the comparison is against the pipe where the sleeve is,
    not at whichever vertex happens to be closest.
    """
    from shapely.geometry import LineString, Point

    if sleeve.host_category != "footing" or sleeve.center_z_m is None:
        return None
    center = Point(sleeve.center)
    reach = max(sleeve.sleeve_d_m, 0.05)
    best: tuple[float, dict] | None = None
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or run.z_m is None:
            continue
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            span = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            if span < 1e-9:
                continue  # a vertical drop threads no horizontal sleeve
            seg = LineString((a, b))
            gap = seg.distance(center)
            if gap > reach or (best is not None and gap >= best[0]):
                continue
            t = min(1.0, max(0.0, seg.project(center) / span))
            z_at = run.z_m[i] + (run.z_m[i + 1] - run.z_m[i]) * t
            best = (gap, dict(run=run.tag, host=sleeve.host_slab, host_category="footing",
                              point=sleeve.center, z_m=z_at,
                              diameter_m=run.diameter_m, sleeve=sleeve.tag))
    return best[1] if best is not None else None


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
    (``resolve/mep.py::accumulated_serves``) — trusting each run's own ``serves`` list
    let a branch's load silently escape the main it discharges into. Supply runs still
    grade on their authored ``serves`` (no supply topology derivation yet). UNKNOWN
    whenever the serves graph is incomplete: a partial sum passed off as a load is how a
    house ends up with a 1.5" line feeding three fixtures."""
    from typehaus.resolve.mep import accumulated_serves
    from typehaus.takeoff.plumbing_calc import (
        branch_load, fixture_units, required_drain_diameter_in, required_supply_size_in)

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
        diameter_in = run.diameter_m * _M_TO_IN
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
                         f"{trap_arm_d * _M_TO_IN:.2f}\" has no table row",
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
                       + (vent_point[1] - drain_point[1]) ** 2) ** 0.5) * _M_TO_IN
            if arm_in <= limit_in + 1e-6:
                out.append(_pass(
                    cid, f"fixture {fixture.tag}'s trap arm runs {arm_in:.0f}\" to its "
                         f"vent ({vent_via}), within the {limit_in:.0f}\" limit for "
                         f"Ø{trap_arm_d * _M_TO_IN:.2f}\"", (fixture.tag,)))
            else:
                out.append(_fail(
                    cid, f"fixture {fixture.tag}'s trap arm runs {arm_in:.0f}\" to its "
                         f"vent ({vent_via}) — over the {limit_in:.0f}\" limit for "
                         f"Ø{trap_arm_d * _M_TO_IN:.2f}\"", (fixture.tag,)))
    return out
