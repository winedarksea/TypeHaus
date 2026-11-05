"""``mep.trap_arm_length`` — the developed trap arm, walked in 3D along the drain.

MN 4714 (UPC) 1002.2: the developed length from the trap to the vent, against Table 1002.2
(``takeoff.plumbing_calc.TRAP_ARM_MAX_IN``); for a water closet, from the closet flange. It
replaced a plan ``hypot`` from the drain point to the nearest serving vent, which never asked
whether the vent reaches the drain (C6-E7). 905.5/1002.4: a fall past one diameter before the
vent is an S-trap, a FAIL. MN 1002.2's twice-diameter minimum is ``mep.vent_connection``'s.

**The vent must meet the drain.** A vent tee is a serving VENT run's endpoint on a drain
segment in 3D (within ``_TEE_TOL_M``). The walk starts at the fixture's most upstream serving
drain (a run no other serving drain ends on), follows it downstream into each parent where it
ends, and stops at the first tee — or at a WET VENT: another drain joining the path that
carries a serving vent tee of its own, if ``grade_wet_vent`` finds it legal under UPC 908. A
wet vent that fails is skipped and the walk goes on. Verticals count. The walk itself is
``resolve/mep_trap_arm``, which the router reads too.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Service
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_trap_arm import START_TOL_M, arm_leaves, developed_arm

_CID = "mep.trap_arm_length"


@check(Tier.CODE, _CID)
def trap_arm_length(ctx: CheckContext) -> list[Finding]:
    """Developed trap arm from each fixture to its vent tee, against Table 1002.2."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point
    from typehaus.resolve.mep_trap_arm import wet_vent_data
    from typehaus.takeoff.plumbing_calc import trap_arm_limit_in

    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    data = wet_vent_data(ctx.model)
    drains, radii = data.drains, data.radii
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            tags = (fixture.tag,)
            point = _expected_drain_point(ctx.model, fixture.tag)
            serving = [r for r in ctx.model.pipe_runs
                       if r.system == "drain" and fixture.tag in r.serves and r.tag in drains]
            if point is None or not serving:
                out.append(_unknown(_CID, f"fixture {fixture.tag} has no resolvable drain "
                                          "point or no drain run serving it", tags))
                continue
            starts = arm_leaves(serving, point, drains, radii)
            if starts[0][0][0] > START_TOL_M:
                out.append(_unknown(_CID, f"fixture {fixture.tag}: no serving drain starts "
                                          "at its drain point, so there is no arm to walk",
                                    tags))
                continue
            arm_run = starts[0][1]
            limit_in = trap_arm_limit_in(arm_run.diameter_m)
            size = f"Ø{arm_run.diameter_m / M_PER_IN:.2f}\""
            if limit_in is None:
                out.append(_unknown(_CID, f"fixture {fixture.tag}'s trap arm {size} has no "
                                          "Table 1002.2 row", tags))
                continue
            ends = data.vent_ends.get(fixture.tag, [])
            arm_m, what, gap, notes = developed_arm(arm_run.tag, drains, radii, ends,
                                                    (data.fx, fixture.tag))
            if arm_m is None:
                why = (f"the nearest serving vent end is {gap / M_PER_IN:.1f}\" off any "
                       "drain" if ends else "no vent run serves it")
                if notes:
                    why = f"no true vent tee, and {'; '.join(notes)}"
                out.append(_unknown(_CID, f"fixture {fixture.tag}: no vent meets its drain "
                                          f"in 3D downstream of the trap — {why}", tags))
                continue
            arm_in = arm_m / M_PER_IN
            skipped = f" [{'; '.join(notes)}]" if notes else ""
            said = (f"fixture {fixture.tag}'s trap arm develops {arm_in:.0f}\" from "
                    f"{arm_run.tag} to {what}, against Table 1002.2's {limit_in:.0f}\" for "
                    f"{size}{skipped}")
            fall = _fall_before_vent(ctx.model, fixture.tag, fixture_type, storey, arm_run,
                                     arm_m, drains, radii)
            if arm_in > limit_in + 1e-6:
                out.append(_fail(_CID, said + " — over", tags))
            elif fall is not None:
                out.append(_fail(_CID, f"{said}, but it falls {fall:.2f}\" before the "
                                          f"vent, over its {size} (905.5/1002.4: the vent "
                                          "opening is below the weir, an S-trap)", tags))
            else:
                out.append(_pass(_CID, said, tags))
    return out


def _fall_before_vent(model, fixture: str, fixture_type, storey, arm_run, arm_m: float,
                      drains, radii) -> float | None:
    """Inches the arm falls from its weir to the tee past one diameter, or None (WCs exempt).

    The weir is ``resolve/mep_trap_arm.trap_weir_m``'s; a drop before the vent is arm, and a
    deep one an S-trap."""
    from typehaus.model.enums import Service
    from typehaus.resolve.mep_sleeves import expected_port_point
    from typehaus.resolve.mep_trap_arm import trap_weir_m, walk_to

    if (fixture_type.plan_symbol or "").startswith("toilet"):
        return None
    weir = trap_weir_m(model, fixture, storey.elevation.meters,
                       expected_port_point(model, fixture, Service.DRAIN), drains[arm_run.tag])
    fall = weir - walk_to(arm_run.tag, drains, radii, arm_m)[2]
    return fall / M_PER_IN if fall > arm_run.diameter_m + 1 / 16 * M_PER_IN else None
