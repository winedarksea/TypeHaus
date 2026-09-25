"""UPC 608.5 (as Minn. R. 4714.0608 amends it) relief discharge, and UPC 507.5 the pan.

**Not IRC P2804 / P2801.6.** Minn. R. 1309.0010 subp. 3.D strikes IRC chapters 25-33, so
what governs a water heater here is the UPC as incorporated at Minn. R. 4714.0050 —
608.5 for the relief discharge and 507.5 for the pan (Minn. R. 4714.0507 deletes 507.6 to
507.11 and 507.14 to 507.23; 507.5 survives unamended).

The TPR valve is the only part of a water heater that exists to stop it exploding, and its
discharge pipe is routinely got wrong in ways that are geometry: it rises somewhere along
its length and holds water, or it was never run at all. Both are checkable once the run is
named, which is what ``Equipment.relief_discharge_ref`` is for.

Minn. R. 4714.0608 rewrites UPC 608.5 whole; its (3) reads "discharge independently by
gravity through an air gap to a safe place of disposal or within 18 inches of the floor"
(revisor.mn.gov/rules/4714.0608, verified 2026-09-23). The model UPC's 6"-24" band is
gone: 18" is the ceiling and there is no 6" floor — only the air gap, so a termination at
or below the floor fails.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EquipmentKind
from typehaus.quantities import inch
from typehaus.resolve.solid_categories import in_slab_family

# Minn. R. 4714.0608 (UPC 608.5)(3): within 18" of the floor, through an air gap; (5): no
# part trapped — it runs downhill the whole way.
_MAX_TERMINATION = inch(18)
_RISE_TOLERANCE_M = 0.005  # 5 mm of routing noise is not a trap

#: The two citations, spelled as the rest of the plumbing checks spell ch. 4714.
_DISCHARGE = "MN Plumbing Code (ch. 4714) 608.5"
_PAN = "MN Plumbing Code (ch. 4714) 507.5"


def _finding(cid, result, message, tags, code, fix=None) -> Finding:
    if result is Result.NOT_APPLICABLE:
        return not_applicable(cid, message, tags, code=code)
    if result is Result.PASS:
        return passed(cid, message, tags, code=code)
    if result is Result.UNKNOWN:
        return unknown(cid, message, tags, code=code, fix=fix)
    return failed(cid, message, tags, code=code, fix=fix)


@check(Tier.CODE, "code.MN_4714_0608_water_heater_relief")
def water_heater_relief(ctx: CheckContext) -> list[Finding]:
    """UPC 608.5 — every water heater's relief valve discharges through an unobstructed pipe."""
    cid, code = "code.MN_4714_0608_water_heater_relief", _DISCHARGE
    heaters = [e for e in ctx.plan.all_elements()
               if e.element_kind == "Equipment" and e.kind is EquipmentKind.WATER_HEATER]
    if not heaters:
        return [_finding(cid, Result.UNKNOWN, "no water heater is modeled", (), code)]
    runs = {r.tag: r for r in ctx.model.pipe_runs}
    storeys = {s.tag: s for s in ctx.plan.storeys}

    out: list[Finding] = []
    for heater in heaters:
        ref = heater.relief_discharge_ref
        if ref is None:
            out.append(_finding(cid, Result.UNKNOWN,
                                f"{heater.tag} names no relief_discharge_ref, so the TPR "
                                "discharge required by UPC 608.5 is not modeled",
                                (heater.tag,), _DISCHARGE,
                                "author the discharge as a PipeRun and name it on the "
                                "heater"))
            continue
        run = runs.get(ref)
        if run is None:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag} names relief discharge {ref}, which resolves "
                                "to no pipe run", (heater.tag, ref), _DISCHARGE))
            continue
        elevations = list(run.z_m) if run.z_m else [run.z_start_m, run.z_end_m]
        # strict=False: an offset pairwise walk down the run's elevations — the second
        # iterable is one shorter by construction.
        rises = [(b - a) for a, b in zip(elevations, elevations[1:], strict=False)
                 if b - a > _RISE_TOLERANCE_M]
        if rises:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag}'s relief discharge {ref} rises "
                                f"{max(rises) / .0254:.1f}\" along its run; UPC 608.5 "
                                "requires it to drain by gravity with no trap",
                                (heater.tag, ref), _DISCHARGE))
            continue
        storey = storeys.get(_storey_of(ctx, heater.tag))
        floor = storey.elevation.meters if storey else None
        if floor is None:
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag}'s relief discharge {ref} drains downhill "
                                "(termination height unmeasured: no storey datum)",
                                (), _DISCHARGE))
            continue
        above_floor = elevations[-1] - floor
        if 0.0 < above_floor <= _MAX_TERMINATION.meters:
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag}'s relief discharge {ref} drains downhill and "
                                f"terminates {above_floor / .0254:.0f}\" above the floor",
                                (), _DISCHARGE))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag}'s relief discharge {ref} terminates "
                                f"{above_floor / .0254:.0f}\" above the floor; Minn. R. "
                                "4714.0608 (UPC 608.5(3)) requires an air gap within 18\" "
                                "of the floor", (heater.tag, ref), _DISCHARGE))

        # UPC 507.5: a pan wherever a leak damages what is below. A heater standing on a slab
        # has nothing below it to damage, which is why this is conditional rather than
        # universal — and it is the one part of the rule that needs the building, not the
        # appliance.
        if _stands_on_slab(ctx, heater):
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag} stands on a slab — UPC 507.5 requires no pan",
                                (), _PAN))
        elif heater.drain_pan:
            out.append(_finding(cid, Result.PASS, f"{heater.tag} sits in a drain pan",
                                (), _PAN))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag} sits over occupied space with no drain pan; "
                                "UPC 507.5 requires one where a leak causes damage",
                                (heater.tag,), _PAN))
    return out


def _storey_of(ctx: CheckContext, tag: str) -> str | None:
    """The storey an element is filed on.

    Elements carry no ``storey`` field — the plan files them *under* a storey — so
    ``getattr(heater, "storey", None)`` was always None and every heater reported its
    discharge as "termination height unmeasured". UPC 608.5's 18" ceiling is the half of
    the rule most worth measuring, so the lookup walks the plan's own grouping instead.
    """
    storey_elements = getattr(ctx.plan, "storey_elements", None)
    if storey_elements is None:
        return None  # a synthetic context with no storey grouping to walk
    for storey in ctx.plan.storeys:
        if any(element.tag == tag for element in storey_elements(storey.tag)):
            return storey.tag
    return None


def _stands_on_slab(ctx: CheckContext, heater) -> bool:
    """Is there a slab directly under this heater, and no floor deck?"""
    from shapely.geometry import Point, Polygon

    probe = Point(heater.position.xy_m)
    for solid in ctx.model.solids:
        if (in_slab_family(solid.category) and len(solid.outline) >= 3
                and Polygon(solid.outline).covers(probe)):
            return True
    return False
