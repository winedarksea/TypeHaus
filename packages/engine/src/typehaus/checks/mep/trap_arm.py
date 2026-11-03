"""``mep.trap_arm_developed`` — the developed trap arm, walked in 3D along the drain.

MN 4714 (UPC) 1002.2: the developed length from the trap to the vent, against Table 1002.2
(``takeoff.plumbing_calc.TRAP_ARM_MAX_IN``); for a water closet, from the closet flange.
``mep.trap_arm_length`` (``plumbing_dwv.py``) still measures a plan ``hypot`` from the drain
point to the nearest serving vent, which never asks whether the vent reaches the drain
(C6-E7). This check is its replacement, ADVISORY until every vent meets its drain in 3D:
switched before then it would put an UNKNOWN on the permit gate per unvented fixture.

**The vent must meet the drain.** A vent tee is a serving VENT run's endpoint on a drain
segment in 3D (within ``_TEE_TOL_M``). The walk starts at the fixture's most upstream serving
drain (a run no other serving drain ends on), follows it downstream into each parent where it
ends, and stops at the first tee — or at a WET VENT: another drain joining the path that
carries a serving vent tee of its own, if ``grade_wet_vent`` finds it legal under UPC 908. A
wet vent that fails is skipped and the walk goes on. Verticals count. The walk itself is
``resolve/mep_trap_arm``, which the router reads too.
"""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory
from typehaus.model.enums import Service
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_trap_arm import START_TOL_M, arm_leaves, developed_arm, run_points

_CID = "mep.trap_arm_developed"
def _staged(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    """ADVISORY, not FAIL: the open vent work stays visible without gating (see above)."""
    return advisory(cid, msg, tags, Result.ADVISORY)


@check(Tier.ADVISORY, _CID)
def trap_arm_developed(ctx: CheckContext) -> list[Finding]:
    """Developed trap arm from each fixture to its vent tee, against Table 1002.2."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point
    from typehaus.takeoff.plumbing_calc import fixture_units, trap_arm_limit_in

    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    drains = {r.tag: pts for r in ctx.model.pipe_runs
              if r.system == "drain" and (pts := run_points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in ctx.model.pipe_runs if r.tag in drains}
    units = {u.tag: u for u in fixture_units(ctx.plan)}
    fx: dict[str, tuple] = {}  # tag -> (leaf drain run, DFU, symbol, storey) for wet_vent
    for storey in ctx.plan.storeys:
        for f in ctx.plan.storey_elements(storey.tag):
            row, pt = units.get(f.tag), _expected_drain_point(ctx.model, f.tag)
            serv = [r for r in ctx.model.pipe_runs
                    if r.system == "drain" and f.tag in r.serves and r.tag in drains]
            if f.element_kind == "Fixture" and row and row.dfu and pt and serv:
                fx[f.tag] = (arm_leaves(serv, pt, drains, radii)[0][1].tag, row.dfu, row.symbol,
                             storey.tag)
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
                out.append(_staged(_CID, f"fixture {fixture.tag} has no resolvable drain "
                                          "point or no drain run serving it", tags))
                continue
            starts = arm_leaves(serving, point, drains, radii)
            if starts[0][0][0] > START_TOL_M:
                out.append(_staged(_CID, f"fixture {fixture.tag}: no serving drain starts "
                                          "at its drain point, so there is no arm to walk",
                                    tags))
                continue
            arm_run = starts[0][1]
            limit_in = trap_arm_limit_in(arm_run.diameter_m)
            size = f"Ø{arm_run.diameter_m / M_PER_IN:.2f}\""
            if limit_in is None:
                out.append(_staged(_CID, f"fixture {fixture.tag}'s trap arm {size} has no "
                                          "Table 1002.2 row", tags))
                continue
            vents = [r for r in ctx.model.pipe_runs
                     if r.system == "vent" and fixture.tag in r.serves]
            ends = [p for r in vents if (pts := run_points(r)) for p in (pts[0], pts[-1])]
            arm_m, what, gap, notes = developed_arm(arm_run.tag, drains, radii, ends,
                                                    (fx, fixture.tag))
            if arm_m is None:
                why = (f"the nearest serving vent end is {gap / M_PER_IN:.1f}\" off any "
                       "drain" if ends else "no vent run serves it")
                if notes:
                    why = f"no true vent tee, and {'; '.join(notes)}"
                out.append(_staged(_CID, f"fixture {fixture.tag}: no vent meets its drain "
                                          f"in 3D downstream of the trap — {why}", tags))
                continue
            arm_in = arm_m / M_PER_IN
            skipped = f" [{'; '.join(notes)}]" if notes else ""
            said = (f"fixture {fixture.tag}'s trap arm develops {arm_in:.0f}\" from "
                    f"{arm_run.tag} to {what}, against Table 1002.2's {limit_in:.0f}\" for "
                    f"{size}{skipped}")
            out.append(_pass(_CID, said, tags) if arm_in <= limit_in + 1e-6
                       else _staged(_CID, said + " — over", tags))
    return out
