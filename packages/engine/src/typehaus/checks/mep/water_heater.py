"""UPC 608.5 (as Minn. R. 4714.0608 amends it) relief discharge, UPC 507.5 the pan, and
UPC 604.13 the PEX clearance.

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

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import EquipmentKind
from typehaus.quantities import inch
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.solid_categories import in_slab_family

# Minn. R. 4714.0608 (UPC 608.5)(3): within 18" of the floor, through an air gap; (5): no
# part trapped — it runs downhill the whole way.
_MAX_TERMINATION = inch(18)
_RISE_TOLERANCE_M = 0.005  # 5 mm of routing noise is not a trap

#: The two citations, spelled as the rest of the plumbing checks spell ch. 4714.
_DISCHARGE = "MN Plumbing Code (ch. 4714) 608.5"
_PAN = "MN Plumbing Code (ch. 4714) 507.5"


@check(Tier.CODE, "code.MN_4714_0608_water_heater_relief")
def water_heater_relief(ctx: CheckContext) -> list[Finding]:
    """UPC 608.5 — every water heater's relief valve discharges through an unobstructed pipe."""
    cid, code = "code.MN_4714_0608_water_heater_relief", _DISCHARGE
    heaters = [e for e in ctx.plan.all_elements()
               if e.element_kind == "Equipment" and e.kind is EquipmentKind.WATER_HEATER]
    if not heaters:
        return [by_result(cid, Result.UNKNOWN, "no water heater is modeled", (), code)]
    runs = {r.tag: r for r in ctx.model.pipe_runs}
    storeys = {s.tag: s for s in ctx.plan.storeys}

    out: list[Finding] = []
    for heater in heaters:
        ref = heater.relief_discharge_ref
        if ref is None:
            out.append(by_result(cid, Result.UNKNOWN,
                                 f"{heater.tag} names no relief_discharge_ref, so the TPR "
                                 "discharge required by UPC 608.5 is not modeled",
                                 (heater.tag,), _DISCHARGE,
                                 "author the discharge as a PipeRun and name it on the "
                                 "heater"))
            continue
        run = runs.get(ref)
        if run is None:
            out.append(by_result(cid, Result.FAIL,
                                 f"{heater.tag} names relief discharge {ref}, which resolves "
                                 "to no pipe run", (heater.tag, ref), _DISCHARGE))
            continue
        elevations = list(run.z_m) if run.z_m else [run.z_start_m, run.z_end_m]
        # strict=False: an offset pairwise walk down the run's elevations — the second
        # iterable is one shorter by construction.
        rises = [(b - a) for a, b in zip(elevations, elevations[1:], strict=False)
                 if b - a > _RISE_TOLERANCE_M]
        if rises:
            out.append(by_result(cid, Result.FAIL,
                                 f"{heater.tag}'s relief discharge {ref} rises "
                                 f"{max(rises) / .0254:.1f}\" along its run; UPC 608.5 "
                                 "requires it to drain by gravity with no trap",
                                 (heater.tag, ref), _DISCHARGE))
            continue
        storey = storeys.get(_storey_of(ctx, heater.tag))
        floor = storey.elevation.meters if storey else None
        if floor is None:
            out.append(by_result(cid, Result.PASS,
                                 f"{heater.tag}'s relief discharge {ref} drains downhill "
                                 "(termination height unmeasured: no storey datum)",
                                 (), _DISCHARGE))
            continue
        above_floor = elevations[-1] - floor
        if 0.0 < above_floor <= _MAX_TERMINATION.meters:
            out.append(by_result(cid, Result.PASS,
                                 f"{heater.tag}'s relief discharge {ref} drains downhill and "
                                 f"terminates {above_floor / .0254:.0f}\" above the floor",
                                 (), _DISCHARGE))
        else:
            out.append(by_result(cid, Result.FAIL,
                                 f"{heater.tag}'s relief discharge {ref} terminates "
                                 f"{above_floor / .0254:.0f}\" above the floor; Minn. R. "
                                 "4714.0608 (UPC 608.5(3)) requires an air gap within 18\" "
                                 "of the floor", (heater.tag, ref), _DISCHARGE))

        # UPC 507.5: a pan wherever a leak damages what is below. A heater standing on a slab
        # has nothing below it to damage, which is why this is conditional rather than
        # universal — and it is the one part of the rule that needs the building, not the
        # appliance.
        if _stands_on_slab(ctx, heater):
            out.append(by_result(cid, Result.PASS,
                                 f"{heater.tag} stands on a slab — UPC 507.5 requires no pan",
                                 (), _PAN))
        elif heater.drain_pan:
            out.append(by_result(cid, Result.PASS, f"{heater.tag} sits in a drain pan",
                                 (), _PAN))
        else:
            out.append(by_result(cid, Result.FAIL,
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

    probe = Point(placed_xy(ctx.model, heater))
    for solid in ctx.model.solids:
        if (in_slab_family(solid.category) and len(solid.outline) >= 3
                and Polygon(solid.outline).covers(probe)):
            return True
    return False


# --- UPC 604.13: no PEX in the first 18" of piping on a water heater ---------------------

#: Minn. R. 4714.0050 incorporates UPC 604.13 unamended; a heat-pump heater is a water
#: heater, so it is not exempt.
_PEX_CODE = ("MN Plumbing Code (ch. 4714) 604.13 — no PEX within the first 18 in. of piping "
             "connected to a water heater")
_PEX_ZONE_M = inch(18).meters
_PEX_MATERIALS = frozenset({"pex", "pex-a", "pex-b"})
_JOINT_TOL_M = 0.0127  # 1/2": a run end is on a 3/4" stub or it is not
_WATER = frozenset({"water_hot", "water_cold"})


@check(Tier.CODE, "mep.pex_water_heater_clearance")
def pex_water_heater_clearance(ctx: CheckContext) -> list[Finding]:
    """UPC 604.13 — no PEX within 18" of developed piping from a water heater's taps.

    Distance is walked through the piping from each exact water port, run to run, so a branch
    teeing off the trunk 29" above the tap is outside the zone and one teeing 6" up is not.
    """
    from typehaus.resolve.mep_ports import placed_ports

    cid = "mep.pex_water_heater_clearance"
    heaters = [e.tag for e in ctx.plan.all_elements()
               if e.element_kind == "Equipment" and e.kind is EquipmentKind.WATER_HEATER]
    runs = [r for r in ctx.model.pipe_runs if r.system in _WATER and len(r.path) >= 2]
    if not heaters:
        # N/A is earned only by a house with no hot water at all; hot piping and no heater
        # is a gap in the model, not an absence in the building.
        if any(r.system == "water_hot" for r in runs):
            return [by_result(cid, Result.UNKNOWN, "hot-water piping is modeled but no water "
                              "heater is", (), _PEX_CODE)]
        return [by_result(cid, Result.NOT_APPLICABLE, "no water heater and no hot-water "
                          "piping is modeled", (), _PEX_CODE)]
    ports = [p for p in placed_ports(ctx.model) if p.service in _WATER]

    out: list[Finding] = []
    for tag in heaters:
        taps = [p for p in ports if p.equipment_tag == tag and p.exact]
        if not taps:
            out.append(by_result(cid, Result.UNKNOWN,
                                 f"{tag} declares no exact water port, so the piping "
                                 "connected to it cannot be located", (tag,), _PEX_CODE,
                                 "dimension the heater type's hot and cold ports"))
            continue
        reached = _reach(runs, [p.point for p in taps])
        if not reached:
            out.append(by_result(cid, Result.UNKNOWN,
                                 f"no supply run reaches {tag}'s water ports", (tag,),
                                 _PEX_CODE))
            continue
        bad = [(r, d) for r, d in reached.values()
               if d < _PEX_ZONE_M and (r.material or "").strip().lower() in _PEX_MATERIALS]
        for run, d in sorted(bad, key=lambda b: b[0].tag):
            out.append(by_result(
                cid, Result.FAIL,
                f"{run.tag} is PEX {d / .0254:.0f}\" along the piping from {tag}; UPC 604.13 "
                "allows none in the first 18\"", (run.tag, tag), _PEX_CODE,
                "make this run copper/CPVC for its first 18\", or split it at 18\" into a "
                "copper stub and a PEX run"))
        if not bad:
            near = sorted(r.tag for r, d in reached.values() if d < _PEX_ZONE_M)
            far = [d for _, d in reached.values() if d >= _PEX_ZONE_M]
            msg = f"{tag}: no PEX within 18\" — {', '.join(near)} non-PEX"
            if far:
                msg += f"; the nearest branch tees on {min(far) / .0254:.0f}\" out"
            out.append(by_result(cid, Result.PASS, msg, (), _PEX_CODE))
    return out


def _pts(run) -> list[tuple[float, float, float]]:
    """A run's vertices in 3D; a run with no inverts is taken as level at its start."""
    if run.z_m:
        return [(x, y, z) for (x, y), z in zip(run.path, run.z_m, strict=True)]
    z = run.z_start_m or 0.0
    return [(x, y, z) for x, y in run.path]


def _project(pts, q) -> tuple[float, float] | None:
    """(distance from vertex 0 along ``pts``, miss) of the closest point to ``q``."""
    best, along = None, 0.0
    for a, b in zip(pts, pts[1:], strict=False):
        seg = [b[i] - a[i] for i in range(3)]
        n2 = sum(c * c for c in seg)
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, sum((q[i] - a[i]) * seg[i]
                                                        for i in range(3)) / n2))
        miss = sum((a[i] + t * seg[i] - q[i]) ** 2 for i in range(3)) ** 0.5
        if best is None or miss < best[1]:
            best = (along + t * n2 ** 0.5, miss)
        along += n2 ** 0.5
    return best


def _reach(runs, sources) -> dict[str, tuple]:
    """Every run within 18" of piping of ``sources``: tag -> (run, developed distance).

    Two runs join where a vertex of one lies on the other (end-to-end or a tee, either way
    round); a source joins a run anywhere along it. A relaxation walk, cut at the zone: a run
    first met beyond it is returned but not walked.
    """
    geo = {r.tag: (r, _pts(r)) for r in runs}
    sta = {tag: [0.0] + _cumulative(pts) for tag, (_, pts) in geo.items()}
    entries: dict[str, list[tuple[float, float]]] = {}  # tag -> [(distance, station)]
    todo: list[tuple[str, float, float]] = []
    for q in sources:
        for tag, (_, pts) in geo.items():
            hit = _project(pts, q)
            if hit and hit[1] <= _JOINT_TOL_M:
                todo.append((tag, 0.0, hit[0]))
    while todo:
        tag, d0, s0 = todo.pop()
        seen = entries.setdefault(tag, [])
        if any(d + abs(s0 - s) <= d0 for d, s in seen):
            continue
        seen.append((d0, s0))
        if d0 >= _PEX_ZONE_M:
            continue  # named as teeing on beyond the zone, never walked
        pts = geo[tag][1]
        for other, (_, opts) in geo.items():
            if other == tag:
                continue
            for v, sv in zip(opts, sta[other], strict=True):  # other's vertex on this run
                hit = _project(pts, v)
                if hit and hit[1] <= _JOINT_TOL_M:
                    todo.append((other, d0 + abs(hit[0] - s0), sv))
            for v, sv in zip(pts, sta[tag], strict=True):  # this run's vertex on other
                hit = _project(opts, v)
                if hit and hit[1] <= _JOINT_TOL_M:
                    todo.append((other, d0 + abs(sv - s0), hit[0]))
    return {tag: (geo[tag][0], min(d for d, _ in seen))
            for tag, seen in entries.items() if seen}


def _cumulative(pts) -> list[float]:
    out, total = [], 0.0
    for a, b in zip(pts, pts[1:], strict=False):
        total += sum((b[i] - a[i]) ** 2 for i in range(3)) ** 0.5
        out.append(total)
    return out
