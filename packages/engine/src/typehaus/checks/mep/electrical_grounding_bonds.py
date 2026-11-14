"""CODE-tier bonding checks (decision #123): 250.94 IBT, 250.104(A) water pipe (its size in
``electrical_grounding_service``), 250.106
lightning, 690.47 PV and 230.67 the service SPD. Each is graph connectivity on
``model.grounding``: a conductor is a solid bond, so "isolated" is simply "another system".
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_grounding import (
    METALS,
    device_types,
    grounding,
    objects,
    root_building,
    supplied_buildings,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.grounding_tables import larger
from typehaus.model.nec import NEC, cite

IBT_CID = "code.NEC_250_94_ibt"
WATER_CID = "code.NEC_250_104_water_bond"
LPS_CID = "code.NEC_250_106_lps_bond"
PV_CID = "code.NEC_690_47_pv_grounding"
SPD_CID = "code.NEC_230_67_service_spd"
#: "Immediately adjacent" to the service equipment, read as within this plan distance.
ADJACENT_M = 1.5
_WATER = ("water_cold", "water_hot")
_TOUCH_M = 0.05


def entering_data(ctx: CheckContext) -> list[tuple[Any, str]]:
    """(DATA conduit, its exterior source) for each data raceway fed from outside inward."""
    from typehaus.resolve.room_lookup import room_owning

    objs = objects(ctx)

    def outdoors(ref: str | None) -> bool | None:
        obj = objs.get(ref or "")
        return None if obj is None else room_owning(ctx.model, obj.storey, obj.position) is None

    return [(run, run.from_ref) for run in ctx.model.conduits
            if run.service == "data" and outdoors(run.from_ref) and outdoors(run.to_ref) is False]


def ibts(ctx: CheckContext) -> list[str]:
    types = device_types(ctx)
    return sorted(o.tag for o in ctx.model.canvas_objects
                  if getattr(types.get(o.type_ref or ""), "ibt", False))


def service_spds(ctx: CheckContext, root: str) -> list[str]:
    """Type 1/2 SPD devices beside ``root``, and SPD circuits in it."""
    objs, types = objects(ctx), device_types(ctx)
    here = objs.get(root)
    found = [c.tag for c in ctx.plan.library.circuits if c.panel_ref == root and c.spd]
    for obj in ctx.model.canvas_objects:
        spd = getattr(types.get(obj.type_ref or ""), "spd_class", None)
        if spd not in ("1", "2") or here is None:
            continue
        if obj.storey == here.storey and math.dist(obj.position, here.position) <= ADJACENT_M:
            found.append(obj.tag)
    return sorted(found)


@check(Tier.CODE, IBT_CID)
def intersystem_bonding(ctx: CheckContext) -> list[Finding]:
    """250.94(A) -- an IBT at the service, and at the disconnect of every building a feeder or
    branch circuit supplies, whether or not a communications raceway is modeled: bonded into
    that building's system, mounted outside the enclosures, three or more terminals."""
    code = cite(NEC.INTERSYSTEM_BONDING)
    g = grounding(ctx)
    if g.root is None:
        if not ctx.plan.library.circuits:
            return [not_applicable(IBT_CID, "no service and no circuit in the plan", code=code)]
        return [unknown(IBT_CID, "no service disconnect is modeled", code=code)]
    entries = ", ".join(run.tag for run, _ in entering_data(ctx))
    out = [_ibt_at(ctx, g, root_building(ctx, g), g.root_system, f"the service {g.root}",
                   entries, code)]
    for bldg in sorted(supplied_buildings(ctx)):
        system = frozenset().union(*(g.system_of(e.tag) for e in g.electrodes
                                     if e.building == bldg and e.use == "ges"))
        out.append(_ibt_at(ctx, g, bldg, system, f"{bldg}'s disconnect", "", code))
    return out


def _ibt_at(ctx: CheckContext, g, bldg: str | None, system: frozenset[str], what: str,
            entries: str, code: str) -> Finding:
    types, objs = device_types(ctx), objects(ctx)
    found = [t for t in ibts(ctx) if t in objs and ctx.plan.building_of(objs[t].storey) == bldg]
    serving = f" (serving {entries})" if entries else ""
    if not found:
        return failed(IBT_CID, f"no IBT at {what}{serving}", (), code,
                      fix="place an ibt=True device outside the enclosures, bonded to its GEC "
                          "or the building's electrode system")
    bonded = [t for t in found if t in system]
    if not bonded:
        return failed(IBT_CID, f"IBT {', '.join(found)} is not bonded into {what}'s electrode "
                      "system", tuple(found), code,
                      fix="run the IBT's bonding conductor to the GEC or the disconnect")
    tag = bonded[0]
    terminals = getattr(types.get(objs[tag].type_ref or ""), "bonding_terminals", None)
    gec6 = any(b.role == "gec" and b.material == "copper" and b.tag in system
               and larger(b.size, "6") for b in g.bonds)
    if terminals is not None and terminals < 3:
        return failed(IBT_CID, f"IBT {tag} has {terminals} bonding terminals, under three",
                      (tag,), code, fix="use an IBT with three or more terminals")
    if not gec6:
        return failed(IBT_CID, f"IBT {tag}: no #6 Cu or larger GEC in {what}'s system to mount "
                      "it by", (tag,), code)
    if terminals is None:
        return unknown(IBT_CID, f"IBT {tag} is bonded at {what}, but its type states no "
                       "bonding_terminals (250.94(A): three or more)", (tag,), code)
    return passed(IBT_CID, f"IBT {tag} at {what}{serving}: its own device outside the "
                  f"enclosures, {terminals} terminals, bonded to a system with a #6 Cu or larger "
                  "GEC", (tag,), code)


@check(Tier.CODE, WATER_CID)
def water_pipe_bond(ctx: CheckContext) -> list[Finding]:
    """250.104(A) -- metal water piping is bonded to the service's system."""
    code = cite(NEC.WATER_PIPE_BOND)
    runs = [r for r in ctx.model.pipe_runs if r.system in _WATER]
    if not runs:
        return [unknown(WATER_CID, "no water piping is modeled", code=code)]
    metal = [r for r in runs if (r.material or "").lower() in METALS]
    unstated = sorted(r.tag for r in runs if not r.material)
    if not metal:
        if unstated:
            return [unknown(WATER_CID, f"{len(unstated)} water runs state no material "
                            f"({', '.join(unstated[:4])})", tuple(unstated), code)]
        mats = sorted({r.material for r in runs})
        return [not_applicable(WATER_CID, f"no metal water piping: every run is "
                               f"{' or '.join(mats)}", code=code)]
    g = grounding(ctx)
    root = g.root_system
    reached = {r.tag for r in metal if r.tag in root and any(
        b.role == "water_bond" and r.tag in (b.from_ref, b.to_ref) for b in g.bonds)}
    reached = _spread(metal, reached)
    out = []
    service = g.root or "the service"
    for run in sorted(metal, key=lambda r: r.tag):
        if run.tag in reached:
            out.append(passed(WATER_CID, f"{run.tag} ({run.material}) is bonded to {g.root}",
                              (run.tag,), code))
        else:
            out.append(failed(WATER_CID, f"{run.tag} ({run.material}) is metal water piping "
                              "with no bond to the service", (run.tag,), code,
                              fix=f"add a water_bond BondingConductor from {service} to "
                                  f"{run.tag}"))
    from typehaus.checks.mep.electrical_grounding_service import water_bond_sizes

    return out + water_bond_sizes(ctx, code)


def _spread(metal: list, reached: set[str]) -> set[str]:
    """Metal runs touching a bonded metal run, end to path, are bonded through it."""
    from shapely.geometry import LineString, Point

    lines = {r.tag: LineString([p[:2] for p in r.path]) for r in metal if len(r.path) >= 2}
    ends = {r.tag: [Point(r.path[0][:2]), Point(r.path[-1][:2])] for r in metal if r.path}
    grown = True
    while grown:
        grown = False
        for tag in set(lines) - reached:
            if any(lines[b].distance(p) <= _TOUCH_M for b in reached if b in lines
                   for p in ends[tag]) or any(
                    lines[tag].distance(p) <= _TOUCH_M for b in reached for p in ends.get(b, ())):
                reached.add(tag)
                grown = True
    return reached


@check(Tier.CODE, LPS_CID)
def lightning_bond(ctx: CheckContext) -> list[Finding]:
    """250.106 -- a lightning electrode or down-lead is bonded solidly to the service's system.

    No isolated, resistor-, diode- or gap-tied ground: separated grounds are what side-flash
    jumps between (decision #123)."""
    code = cite(NEC.LIGHTNING_BOND)
    g = grounding(ctx)
    items = [(e.tag, "terminal") for e in g.electrodes if e.use == "lps_terminal"]
    items += [(b.tag, "down-lead") for b in g.bonds if b.role == "down_lead"]
    if not items:
        return [not_applicable(LPS_CID, "no lightning terminal or down-lead is authored",
                               code=code)]
    out = []
    for tag, what in sorted(items):
        if tag in g.root_system:
            out.append(passed(LPS_CID, f"{what} {tag} is solidly bonded to {g.root}", (tag,),
                              code))
        else:
            out.append(failed(LPS_CID, f"{what} {tag} is isolated from the service's "
                              "electrode system", (tag,), code,
                              fix="bond it with a solid conductor; an isolated or "
                                  "impedance-tied ground is not permitted"))
    return out


@check(Tier.CODE, PV_CID)
def pv_grounding(ctx: CheckContext) -> list[Finding]:
    """690.47(A) -- the array's bond reaches the service's system; a down-lead lands on an
    electrode in it. Printed text read 2026-11-14: the array EGCs join the building's
    electrode system (Art. 250 Part VII) on top of 690.43(C); size is not graded (690.45)."""
    code = cite(NEC.PV_GROUNDING)
    panels = {el.tag for el in ctx.plan.elements_of_kind("SolarPanel")}
    if not panels:
        return [not_applicable(PV_CID, "no PV module is modeled", code=code)]
    g = grounding(ctx)
    bonds = [b for b in g.bonds if panels & {b.from_ref, b.to_ref}]
    if not bonds:
        return [failed(PV_CID, "no conductor bonds the array to the electrode system", (),
                       code, fix="add a BondingConductor from a SolarPanel to the service's "
                                 "electrode system")]
    out = []
    for bond in sorted(bonds, key=lambda b: b.tag):
        system = g.system_of(bond.tag)
        lands = sorted(e.tag for e in g.electrodes if e.tag in system)
        if bond.tag not in g.root_system:
            out.append(failed(PV_CID, f"{bond.tag} bonds the array into a system apart from "
                              f"{g.root}", (bond.tag,), code))
        elif bond.role == "down_lead" and not lands:
            out.append(failed(PV_CID, f"down-lead {bond.tag} lands on no electrode",
                              (bond.tag,), code))
        else:
            out.append(passed(PV_CID, f"{bond.tag} bonds the array to {g.root}"
                              + (f" through {', '.join(lands[:3])}" if lands else ""),
                              (bond.tag,), code))
    return out


@check(Tier.CODE, SPD_CID)
def service_surge_protection(ctx: CheckContext) -> list[Finding]:
    """230.67 -- a Type 1 or 2 SPD integral to or immediately adjacent to the service."""
    code = cite(NEC.SERVICE_SPD)
    g = grounding(ctx)
    if g.root is None:
        if not ctx.plan.library.circuits:
            return [not_applicable(SPD_CID, "no service and no circuit in the plan",
                                   code=code)]
        return [unknown(SPD_CID, "no service disconnect is modeled", code=code)]
    found = service_spds(ctx, g.root)
    if found:
        return [passed(SPD_CID, f"{g.root} has its SPD ({', '.join(found)})",
                       (g.root, *found), code)]
    downstream = sorted(c.tag for c in ctx.plan.library.circuits if c.spd)
    if downstream:
        return [unknown(SPD_CID, f"no SPD beside {g.root}; {', '.join(downstream)} sit "
                        "downstream, which 230.67(B) Ex. accepts only at the next level of "
                        "distribution (feeder topology is not modeled)", (g.root,), code)]
    return [failed(SPD_CID, f"no Type 1 or 2 SPD at the service disconnect {g.root}",
                   (g.root,), code, fix="place an spd_class '1' or '2' SPD beside it")]
