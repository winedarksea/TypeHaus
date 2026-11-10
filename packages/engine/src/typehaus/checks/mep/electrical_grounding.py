"""CODE-tier NEC Art. 250 electrode checks, read off ``model.grounding`` (decision #123).

250.52(A)(3) the Ufer, 250.50 every electrode present bonded to the service, 250.53 rods,
250.66 GEC size and 250.32 a separate building's own electrode system. Geometry is never
re-derived here: ``resolve/grounding.py`` owns lengths, bar qualification and bonding systems.
Bonds, the service SPD and the advisories are in the sibling ``electrical_grounding_*``.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite
from typehaus.resolve.grounding import ResolvedGrounding

_FT = 0.3048
UFER_MIN_M = 20 * _FT
ROD_MIN_M = 8 * _FT
ROD_SPACING_M = 6 * _FT  # 250.53(A)(3), when no standard states one
METALS = frozenset({"copper", "steel", "galvanized", "black_steel", "brass", "iron",
                    "stainless", "cast_iron", "ductile_iron"})
#: A water run counts as leaving the building this far outside every ground-floor room.
_SERVICE_REACH_M = 0.5

UFER_CID = "code.NEC_250_52_ufer"
SYSTEM_CID = "code.NEC_250_50_electrode_system"
ROD_CID = "code.NEC_250_53_rods"
GEC_CID = "code.NEC_250_66_gec_size"
SEPARATE_CID = "code.NEC_250_32_separate_buildings"


# -- shared readers -------------------------------------------------------------------------

def grounding(ctx: CheckContext) -> ResolvedGrounding:
    return getattr(ctx.model, "grounding", None) or ResolvedGrounding()


def objects(ctx: CheckContext) -> dict[str, Any]:
    return {obj.tag: obj for obj in ctx.model.canvas_objects}


def device_types(ctx: CheckContext) -> dict[str, Any]:
    return {t.tag: t for t in ctx.plan.library.electrical_device_types}


def storey_of(ctx: CheckContext) -> dict[str, str]:
    out: dict[str, str] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            out[element.tag] = storey.tag
    return out


def building_of_tag(ctx: CheckContext, tag: str | None, storeys: dict[str, str]) -> str | None:
    storey = storeys.get(tag or "")
    return ctx.plan.building_of(storey) if storey else None


def root_building(ctx: CheckContext, g: ResolvedGrounding) -> str | None:
    return building_of_tag(ctx, g.root, storey_of(ctx)) if g.root else None


def ground_rooms(ctx: CheckContext) -> list:
    """Axis polygons of each building's lowest storey: the footprints a rod stays out of."""
    from typehaus.resolve.room_lookup import axis_polygon, axis_ring

    lowest = set()
    for b in ctx.plan.buildings():
        storeys = ctx.plan.storeys_of(b.tag)
        if storeys:
            lowest.add(min(storeys, key=lambda s: s.elevation.meters).tag)
    return [axis_polygon(r) for r in ctx.model.rooms
            if r.storey in lowest and len(axis_ring(r)) >= 3]


def outside_by(polys: list, xy: tuple[float, float]) -> float:
    """How far ``xy`` lies outside every polygon (0 when inside one; inf with none)."""
    from shapely.geometry import Point

    point = Point(xy[0], xy[1])
    return min((p.distance(point) for p in polys), default=math.inf)


def awg_rank(size: str) -> int | None:
    """Smaller is a bigger conductor: "6" -> 6, "1/0" -> 0, "4/0" -> -3."""
    size = size.strip().lstrip("#")
    if size.endswith("/0"):
        return 1 - int(size[:-2]) if size[:-2].isdigit() else None
    return int(size) if size.isdigit() else None


def crossing_circuits(ctx: CheckContext) -> dict[str, set[str]]:
    """Building -> circuits with a consumer in it whose panel stands in another building."""
    storeys = storey_of(ctx)
    panel_bldg = {c.tag: building_of_tag(ctx, c.panel_ref, storeys)
                  for c in ctx.plan.library.circuits}
    out: dict[str, set[str]] = {}
    for storey in ctx.plan.storeys:
        here = ctx.plan.building_of(storey.tag)
        for element in ctx.plan.storey_elements(storey.tag):
            ref = getattr(element, "circuit", None)
            if ref in panel_bldg and panel_bldg[ref] not in (None, here):
                out.setdefault(here, set()).add(ref)
    return out


# -- 250.52(A)(3) ---------------------------------------------------------------------------

@check(Tier.CODE, UFER_CID)
def concrete_encased_electrode(ctx: CheckContext) -> list[Finding]:
    """250.52(A)(3) -- 20 ft of #4 or larger conductive bar, in concrete in contact with earth."""
    code = cite(NEC.CONCRETE_ENCASED)
    g = grounding(ctx)
    ufers = [e for e in g.electrodes if e.kind == "concrete_encased"]
    if not ufers:
        if any(m >= UFER_MIN_M for m in g.footing_bar_m.values()):
            return [unknown(UFER_CID, "a footing carries qualifying bar but no concrete-encased "
                            "GroundingElectrode claims it (see 250.50)", code=code)]
        return [not_applicable(UFER_CID, "no concrete-encased electrode is authored and no "
                               "footing carries 20 ft of qualifying bar", code=code)]
    out = []
    for e in ufers:
        tags = (e.tag, *e.footings)
        why = f" ({'; '.join(e.excluded)})" if e.excluded else ""
        if not e.host_tag:
            out.append(failed(UFER_CID, f"{e.tag} names no host footing", (e.tag,), code,
                              fix="set host_ref= to the footing its bar is cast in"))
        elif e.length_m + 1e-6 < UFER_MIN_M:
            out.append(failed(UFER_CID, f"{e.tag}: {e.length_m / _FT:.1f} ft of qualifying bar "
                              f"through {', '.join(e.footings)}, under 20 ft{why}", tags, code,
                              fix="lay a continuous #4 electrode bar (BarSpec role "
                                  "'electrode') and tie it on with continues_into"))
        elif e.earth_contact == "no":
            out.append(failed(UFER_CID, f"{e.tag}: {e.earth_reason}", tags, code,
                              fix="host it in a footing bearing on earth"))
        elif e.earth_contact == "ahj":
            out.append(unknown(UFER_CID, f"{e.tag} has {e.length_m / _FT:.1f} ft of #{e.bar} "
                               f"{e.coating} bar, but {e.earth_reason}", tags, code))
        else:
            out.append(passed(UFER_CID, f"{e.tag}: {e.length_m / _FT:.1f} ft of #{e.bar} "
                              f"{e.coating} bar at 2 in+ cover in earth-contact concrete",
                              tags, code))
    return out


# -- 250.50 ---------------------------------------------------------------------------------

@check(Tier.CODE, SYSTEM_CID)
def electrode_system(ctx: CheckContext) -> list[Finding]:
    """250.50 -- every electrode present at the building is bonded into one system."""
    code = cite(NEC.ELECTRODE_SYSTEM, NEC.CONCRETE_ENCASED)
    g = grounding(ctx)
    if g.root is None:
        if not ctx.plan.library.circuits and not g.electrodes:
            return [not_applicable(SYSTEM_CID, "no service and no circuit in the plan",
                                   code=code)]
        return [unknown(SYSTEM_CID, "no service disconnect (a METER device whose type states "
                        "service_amps), so the electrode system has no root", code=code)]
    storeys = storey_of(ctx)
    home = building_of_tag(ctx, g.root, storeys)
    root_sys = g.root_system
    ges = [e for e in g.electrodes if e.use == "ges" and e.building == home]
    out: list[Finding] = []
    for e in ges:
        if e.tag in root_sys:
            out.append(passed(SYSTEM_CID, f"{e.tag} ({e.kind}) is bonded to {g.root}",
                              (e.tag,), code))
        else:
            out.append(failed(SYSTEM_CID, f"{e.tag} ({e.kind}) is present but not bonded to "
                              f"{g.root}", (e.tag,), code,
                              fix=f"run a GEC or bonding jumper from {e.tag} into {g.root}'s "
                                  "system"))
    claimed = {t for e in g.electrodes if e.kind == "concrete_encased" for t in e.footings}
    for tag, metres in sorted(g.footing_bar_m.items()):
        if metres + 1e-6 < UFER_MIN_M or tag in claimed:
            continue
        if building_of_tag(ctx, tag, storeys) not in (None, home):
            continue
        out.append(failed(SYSTEM_CID, f"{tag} carries {metres / _FT:.1f} ft of qualifying bar: "
                          "a concrete-encased electrode is present but not bonded", (tag,), code,
                          fix=f"author a concrete_encased GroundingElectrode with host_ref="
                              f"{tag!r} and a GEC to {g.root}"))
    if not any(e.tag in root_sys for e in ges):
        out.append(failed(SYSTEM_CID, f"{g.root} reaches no grounding electrode", (g.root,),
                          code, fix="author electrodes and a GEC to the service disconnect"))
    out.append(_water_service(ctx, root_sys, code))
    return out


def _water_service(ctx: CheckContext, root_sys: frozenset[str], code: str) -> Finding:
    """250.52(A)(1): a metal underground water service is an electrode; plastic earns none."""
    polys = ground_rooms(ctx)
    runs = [r for r in ctx.model.pipe_runs if r.system == "water_cold"
            and any(outside_by(polys, p[:2]) > _SERVICE_REACH_M for p in r.path)]
    if not runs:
        return unknown(SYSTEM_CID, "no cold-water run leaves the building, so whether a metal "
                       "underground water pipe electrode is present is not known", code=code,
                       fix="model the water service run")
    unstated = sorted(r.tag for r in runs if not r.material)
    metal = sorted(r.tag for r in runs if (r.material or "").lower() in METALS)
    if metal:
        loose = [t for t in metal if t not in root_sys]
        if loose:
            return failed(SYSTEM_CID, f"metal water service {', '.join(loose)} is an electrode "
                          "present but not bonded", tuple(loose), code,
                          fix="bond the service pipe within 5 ft of entry")
        return passed(SYSTEM_CID, f"metal water service {', '.join(metal)} is bonded", (), code)
    if unstated:
        return unknown(SYSTEM_CID, f"water service {', '.join(unstated)} states no material",
                       tuple(unstated), code, fix="set material= on the service run")
    said = ", ".join(f"{r.tag} is {r.material}" for r in runs)
    return passed(SYSTEM_CID, f"no metal underground water pipe: {said}",
                  tuple(r.tag for r in runs), code)


# -- 250.53 ---------------------------------------------------------------------------------

@check(Tier.CODE, ROD_CID)
def rod_electrodes(ctx: CheckContext) -> list[Finding]:
    """250.53 -- 8 ft rods, 6 ft apart, a supplemental electrode, outside the footprint."""
    code = cite(NEC.ROD_INSTALLATION)
    g = grounding(ctx)
    rods = [e for e in g.electrodes if e.kind == "rod" and e.use == "ges"]
    if not rods:
        return [not_applicable(ROD_CID, "no rod electrode is authored", code=code)]
    std = g.standard
    spacing = std.min_rod_spacing.meters if std is not None else ROD_SPACING_M
    polys = ground_rooms(ctx)
    out: list[Finding] = []
    for rod in rods:
        problems = []
        if rod.length_m + 1e-6 < ROD_MIN_M:
            problems.append(f"{rod.length_m / _FT:.1f} ft long, under 8 ft")
        if outside_by(polys, rod.xy) <= 0.0:
            problems.append("driven inside a building footprint")
        system = g.system_of(rod.tag)
        others = [e for e in g.electrodes if e.tag != rod.tag and e.tag in system
                  and e.use == "ges"]
        if not others:
            problems.append("a lone rod with no supplemental electrode in its system "
                            "(250.53(A)(2); a proven 25 ohm is not modeled)")
        for other in others:
            if other.kind == "rod" and other.tag > rod.tag:
                gap = math.dist(rod.xy, other.xy)
                if gap + 1e-6 < spacing:
                    problems.append(f"{gap / _FT:.1f} ft from {other.tag}, under "
                                    f"{spacing / _FT:.0f} ft")
        if problems:
            out.append(failed(ROD_CID, f"{rod.tag}: {'; '.join(problems)}", (rod.tag,), code,
                              fix="drive a second rod at least 6 ft away, bonded, outside "
                                  "the foundation"))
        else:
            out.append(passed(ROD_CID, f"{rod.tag}: {rod.length_m / _FT:.0f} ft rod outside the "
                              "footprint, supplemented in its system", (rod.tag,), code))
    return out


# -- 250.66 ---------------------------------------------------------------------------------

@check(Tier.CODE, GEC_CID)
def gec_size(ctx: CheckContext) -> list[Finding]:
    """250.66(A)/(B) -- the sole-connection caps: #6 Cu to a rod, #4 Cu to concrete."""
    code = cite(NEC.GEC_SIZE)
    g = grounding(ctx)
    gecs = [b for b in g.bonds if b.role == "gec"]
    if not gecs:
        if not g.electrodes:
            return [not_applicable(GEC_CID, "no electrode, so no GEC to size", code=code)]
        return [unknown(GEC_CID, "electrodes are authored but no conductor has role 'gec'",
                        code=code)]
    out = []
    for bond in gecs:
        ends = [g.electrode(bond.from_ref), g.electrode(bond.to_ref)]
        e = next((x for x in ends if x is not None), None)
        need = {"rod": 6, "concrete_encased": 4}.get(e.kind if e else "")
        rank = awg_rank(bond.size)
        tags = (bond.tag,)
        if need is None or bond.material != "copper" or rank is None:
            out.append(unknown(GEC_CID, f"{bond.tag} (#{bond.size} {bond.material}): only the "
                               "copper sole-connection caps are graded and the service "
                               "conductor size is not modeled", tags, code))
        elif rank <= need:
            out.append(passed(GEC_CID, f"{bond.tag}: #{bond.size} Cu to {e.kind} {e.tag} meets "
                              f"the #{need} Cu cap", tags, code))
        else:
            out.append(unknown(GEC_CID, f"{bond.tag}: #{bond.size} Cu to {e.tag} is under the "
                               f"#{need} cap; Table 250.66 needs the service conductor size, "
                               "which is not modeled", tags, code,
                               fix=f"use #{need} Cu, which no table row exceeds"))
    return out


# -- 250.32 ---------------------------------------------------------------------------------

@check(Tier.CODE, SEPARATE_CID)
def separate_buildings(ctx: CheckContext) -> list[Finding]:
    """250.32 -- a building fed by more than one circuit has its own electrode system."""
    code = cite(NEC.SEPARATE_BUILDING)
    g = grounding(ctx)
    crossing = crossing_circuits(ctx)
    if not crossing:
        return [not_applicable(SEPARATE_CID, "no circuit leaves its panel's building",
                               code=code)]
    storeys = storey_of(ctx)
    out = []
    for bldg, circuits in sorted(crossing.items()):
        names = ", ".join(sorted(circuits))
        if len(circuits) <= 1:
            out.append(not_applicable(SEPARATE_CID, f"{bldg} is fed by one circuit ({names}): "
                                      "250.32(A) Ex.", code=code))
            continue
        mine = [e for e in g.electrodes if e.building == bldg and e.use == "ges"]
        bonded = [e.tag for e in mine
                  if any(building_of_tag(ctx, t, storeys) == bldg and g.electrode(t) is None
                         and t not in {b.tag for b in g.bonds}
                         for t in g.system_of(e.tag))]
        if bonded:
            out.append(passed(SEPARATE_CID, f"{bldg} ({names}) has its own electrode system "
                              f"({', '.join(sorted(bonded))}) bonded to its equipment",
                              tuple(sorted(bonded)), code))
        elif mine:
            out.append(failed(SEPARATE_CID, f"{bldg}'s electrodes reach no equipment in it",
                              tuple(e.tag for e in mine), code,
                              fix="bond the electrodes to the building's EGC junction box"))
        else:
            out.append(failed(SEPARATE_CID, f"{bldg} is fed by {len(circuits)} circuits "
                              f"({names}) and has no grounding electrode system", (), code,
                              fix=f"drive electrodes at {bldg} and bond them to the circuits' "
                                  "EGCs"))
    return out
