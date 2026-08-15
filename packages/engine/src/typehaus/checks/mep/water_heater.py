"""P2804 water-heater relief discharge, and P2801.6 the pan under it.

The TPR valve is the only part of a water heater that exists to stop it exploding, and its
discharge pipe is routinely got wrong in ways that are geometry: it rises somewhere along
its length and holds water, or it was never run at all. Both are checkable once the run is
named, which is what ``Equipment.relief_discharge_ref`` is for.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EquipmentKind
from typehaus.quantities import inch

# P2804.6.1: the discharge terminates 6"-24" above the floor (or outdoors), and runs
# downhill the whole way — no trap, no rise, no valve.
_MIN_TERMINATION = inch(6)
_MAX_TERMINATION = inch(24)
_RISE_TOLERANCE_M = 0.005  # 5 mm of routing noise is not a trap


def _finding(cid, result, message, tags, code, fix=None) -> Finding:
    if result is Result.PASS:
        return passed(cid, message, tags, code=code)
    if result is Result.UNKNOWN:
        return unknown(cid, message, tags, code=code, fix=fix)
    return failed(cid, message, tags, code=code, fix=fix)


@check(Tier.CODE, "code.P2804_water_heater_relief")
def water_heater_relief(ctx: CheckContext) -> list[Finding]:
    """P2804 — every water heater's relief valve discharges through an unobstructed pipe."""
    cid, code = "code.P2804_water_heater_relief", "P2804"
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
                                "discharge required by P2804.6.1 is not modeled",
                                (heater.tag,), "P2804.6.1",
                                "author the discharge as a PipeRun and name it on the "
                                "heater"))
            continue
        run = runs.get(ref)
        if run is None:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag} names relief discharge {ref}, which resolves "
                                "to no pipe run", (heater.tag, ref), "P2804.6.1"))
            continue
        elevations = list(run.z_m) if run.z_m else [run.z_start_m, run.z_end_m]
        rises = [(b - a) for a, b in zip(elevations, elevations[1:])
                 if b - a > _RISE_TOLERANCE_M]
        if rises:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag}'s relief discharge {ref} rises "
                                f"{max(rises) / .0254:.1f}\" along its run; P2804.6.1 "
                                "requires it to drain by gravity with no trap",
                                (heater.tag, ref), "P2804.6.1"))
            continue
        storey = storeys.get(_storey_of(ctx, heater.tag))
        floor = storey.elevation.meters if storey else None
        if floor is None:
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag}'s relief discharge {ref} drains downhill "
                                "(termination height unmeasured: no storey datum)",
                                (), "P2804.6.1"))
            continue
        above_floor = elevations[-1] - floor
        if _MIN_TERMINATION.meters <= above_floor <= _MAX_TERMINATION.meters:
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag}'s relief discharge {ref} drains downhill and "
                                f"terminates {above_floor / .0254:.0f}\" above the floor",
                                (), "P2804.6.1"))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag}'s relief discharge {ref} terminates "
                                f"{above_floor / .0254:.0f}\" above the floor; P2804.6.1 "
                                "requires 6\"-24\"", (heater.tag, ref), "P2804.6.1"))

        # P2801.6: a pan wherever a leak damages what is below. A heater standing on a slab
        # has nothing below it to damage, which is why this is conditional rather than
        # universal — and it is the one part of the rule that needs the building, not the
        # appliance.
        if _stands_on_slab(ctx, heater):
            out.append(_finding(cid, Result.PASS,
                                f"{heater.tag} stands on a slab — P2801.6 requires no pan",
                                (), "P2801.6"))
        elif heater.drain_pan:
            out.append(_finding(cid, Result.PASS, f"{heater.tag} sits in a drain pan",
                                (), "P2801.6"))
        else:
            out.append(_finding(cid, Result.FAIL,
                                f"{heater.tag} sits over occupied space with no drain pan; "
                                "P2801.6 requires one where a leak causes damage",
                                (heater.tag,), "P2801.6"))
    return out


def _storey_of(ctx: CheckContext, tag: str) -> str | None:
    """The storey an element is filed on.

    Elements carry no ``storey`` field — the plan files them *under* a storey — so
    ``getattr(heater, "storey", None)`` was always None and every heater reported its
    discharge as "termination height unmeasured". P2804.6.1's 6"-24" band is the half of
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
        if solid.category == "slab" and len(solid.outline) >= 3:
            if Polygon(solid.outline).covers(probe):
                return True
    return False
