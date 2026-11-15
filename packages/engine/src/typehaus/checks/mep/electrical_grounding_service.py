"""CODE-tier Art. 250 checks that size off the service: 250.66 GEC (Table 250.66 rows and the
(A)/(B) caps, 250.64(D)(1) summed basis, 250.32(E) outbuildings), the 250.104(A)(1) water
bond (Table 250.102(C)(1), 3/0 Cu cap, the GEC it lands through) and 250.24 neutral bonding.

The basis is the house's ``ServiceEntrance``: an authored service conductor, else the
310.12(A) size for the rating (Table 250.102(C)(1) Note 4), and the summed disconnect
conductors where the service has several. The larger row governs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_grounding import (
    building_of_tag,
    grounding,
    panel_feeders,
    storey_of,
    supplied_buildings,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.ampacity import dwelling_service_conductor
from typehaus.model.grounding_tables import (
    GEC_CU,
    JUMPER_CU,
    WATER_BOND_CAP_CU,
    band,
    kcmil,
    larger,
)
from typehaus.model.nec import NEC, cite

GEC_CID = "code.NEC_250_66_gec_size"
NEUTRAL_CID = "code.NEC_250_24_neutral_bond"
#: 250.66(A)/(B): a sole connection to one electrode type never needs more than this Cu (Al).
_CAP = {"rod": ("6", "4"), "concrete_encased": ("4", None)}


@dataclass(frozen=True)
class Basis:
    row: int
    said: str


def service_entrance(ctx: CheckContext, root: str | None) -> Any | None:
    found = [el for el in ctx.plan.elements_of_kind("ServiceEntrance")
             if el.service_ref == root]
    return found[0] if found else None


def service_basis(ctx: CheckContext) -> tuple[Basis | None, str]:
    """The governing Table 250.66 / 250.102(C)(1) row at the service, or why there is none."""
    g = grounding(ctx)
    if g.root is None:
        return None, "no service disconnect is modeled"
    se = service_entrance(ctx, g.root)
    root = ctx.plan.by_tag(g.root)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    amps = getattr(types.get(getattr(root, "type_ref", None) or ""), "service_amps", None)
    bases: list[Basis] = []
    if se is not None and se.conductor_size:
        if se.conductor_material is None:
            return None, f"{se.tag} states a service conductor size but no material"
        area = kcmil(se.conductor_size) * se.conductor_sets
        bases.append(Basis(band(area, se.conductor_material),
                           f"{se.conductor_sets} x {se.conductor_size} "
                           f"{se.conductor_material} service conductors"))
    elif amps:
        try:
            cu, al = (dwelling_service_conductor(amps, m) for m in ("cu", "al"))
        except ValueError:
            return None, f"{amps} A is outside the 310.12(A) dwelling range"
        bases.append(Basis(max(band(kcmil(cu), "cu"), band(kcmil(al), "al")),
                           f"the 310.12(A) size for {amps} A ({cu} Cu / {al} Al: no service "
                           "conductor is authored, so the size the load calls for)"))
    else:
        return None, "neither a service conductor size nor a service rating is stated"
    if se is not None and len(se.disconnect_conductors) > 1 and not se.disconnect_material:
        return None, f"{se.tag} states parallel disconnect conductors but no material"
    if se is not None and len(se.disconnect_conductors) > 1 and se.disconnect_material:
        area = sum(kcmil(s) for s in se.disconnect_conductors)
        bases.append(Basis(band(area, se.disconnect_material),
                           f"the summed {' + '.join(se.disconnect_conductors)} "
                           f"{se.disconnect_material} = {area:.0f} kcmil (250.64(D)(1))"))
    top = max(b.row for b in bases)
    return Basis(top, " and ".join(b.said for b in bases if b.row == top)), ""


def _outbuilding_basis(ctx: CheckContext, bldg: str) -> tuple[Basis | None, str]:
    """250.32(E): the largest ungrounded supply conductor into ``bldg``."""
    supply = supplied_buildings(ctx).get(bldg)
    if supply is None or set(supply["panels"]) - set(panel_feeders(ctx)):
        return None, f"the feeder into {bldg} is not modeled"
    circuits = [c for c in ctx.plan.library.circuits if c.tag in supply["circuits"]]
    unsized = sorted(c.tag for c in circuits if not c.conductor_awg)
    if unsized or not circuits:
        return None, f"{', '.join(unsized) or bldg} states no conductor size"
    big = max(circuits, key=lambda c: band(kcmil(c.conductor_awg), c.conductor_material))
    return Basis(band(kcmil(big.conductor_awg), big.conductor_material),
                 f"{big.tag}'s {big.conductor_awg} {big.conductor_material} (250.32(E))"), ""


@check(Tier.CODE, GEC_CID)
def gec_size(ctx: CheckContext) -> list[Finding]:
    """250.66 -- Table 250.66 on the service (or 250.32(E) supply) conductor, capped by (A)/(B)."""
    code = cite(NEC.GEC_SIZE)
    g = grounding(ctx)
    gecs = [b for b in g.bonds if b.role == "gec"]
    if not gecs:
        if not g.electrodes:
            return [not_applicable(GEC_CID, "no electrode, so no GEC to size", code=code)]
        return [unknown(GEC_CID, "electrodes are authored but no conductor has role 'gec'",
                        code=code)]
    storeys = storey_of(ctx)
    home = building_of_tag(ctx, g.root, storeys)
    service = service_basis(ctx)
    out = []
    for bond in gecs:
        e = next((x for x in (g.electrode(bond.from_ref), g.electrode(bond.to_ref)) if x), None)
        cu_cap, al_cap = _CAP.get(e.kind if e else "", (None, None))
        cap = cu_cap if bond.material == "copper" else al_cap
        basis, why = service if bond.building == home else _outbuilding_basis(ctx, bond.building)
        row = GEC_CU[basis.row] if basis and bond.material == "copper" else None
        need = min((s for s in (row, cap) if s), key=kcmil, default=None)
        tags = (bond.tag,)
        to = f" to {e.kind} {e.tag}" if e else ""
        if need is None:
            out.append(unknown(GEC_CID, f"{bond.tag} (#{bond.size} {bond.material}){to}: "
                               + (why or "Table 250.66 holds only a copper GEC column"),
                               tags, code))
        elif larger(bond.size, need):
            said = (f"Table 250.66 gives #{row} Cu on {basis.said}" if row else why)
            capped = f", capped at #{cap} by 250.66(A)/(B)" if cap and need == cap else ""
            out.append(passed(GEC_CID, f"{bond.tag}: #{bond.size} {bond.material}{to} meets "
                              f"#{need} ({said}{capped})", tags, code))
        elif row is None:
            out.append(unknown(GEC_CID, f"{bond.tag}: #{bond.size}{to} is under the #{cap} cap "
                               f"and the table row is unknown: {why}", tags, code,
                               fix=f"use #{cap}, which no table row exceeds"))
        else:
            out.append(failed(GEC_CID, f"{bond.tag}: #{bond.size} {bond.material}{to} is under "
                              f"#{need} (Table 250.66 on {basis.said})", tags, code,
                              fix=f"use #{need} Cu"))
    return out


def water_bond_sizes(ctx: CheckContext, code: str) -> list[Finding]:
    """250.104(A)(1): each service-building water bond meets Table 250.102(C)(1) (3/0 Cu cap),
    and a bond landing on an electrode reaches the service through a GEC as large."""
    from typehaus.checks.mep.electrical_grounding_bonds import WATER_CID

    g = grounding(ctx)
    home = building_of_tag(ctx, g.root, storey_of(ctx))
    bonds = [b for b in g.bonds if b.role == "water_bond" and b.building == home]
    if not bonds:
        return []
    basis, why = service_basis(ctx)
    if basis is None:
        return [unknown(WATER_CID, f"water bond size is not graded: {why}",
                        tuple(b.tag for b in bonds), code)]
    need = JUMPER_CU[basis.row] or WATER_BOND_CAP_CU
    if not larger(WATER_BOND_CAP_CU, need):
        need = WATER_BOND_CAP_CU
    out = []
    for bond in sorted(bonds, key=lambda b: b.tag):
        tags = (bond.tag,)
        if bond.material != "copper":
            out.append(unknown(WATER_CID, f"{bond.tag} is {bond.material}; only the Cu column "
                               "is graded", tags, code))
            continue
        if not larger(bond.size, need):
            out.append(failed(WATER_CID, f"{bond.tag}: #{bond.size} Cu is under #{need} Cu "
                              f"(Table 250.102(C)(1) on {basis.said})", tags, code,
                              fix=f"use #{need} Cu"))
            continue
        thin = _thin_gec(g, bond, need)
        if thin:
            out.append(failed(WATER_CID, f"{bond.tag} lands on an electrode whose GEC "
                              f"{', '.join(thin)} is smaller than the #{need} bond", tags, code,
                              fix=f"raise the GEC to #{need} Cu or land the bond at the service"))
        else:
            out.append(passed(WATER_CID, f"{bond.tag}: #{bond.size} Cu meets #{need} Cu "
                              f"(Table 250.102(C)(1) on {basis.said})", tags, code))
    return out


def _thin_gec(g, bond, need: str) -> list[str]:
    """GECs from the electrode a water bond lands on that are smaller than the bond needs."""
    out = []
    for end in (bond.from_ref, bond.to_ref):
        if g.electrode(end) is None:
            continue
        gecs = [b for b in g.bonds if b.role == "gec" and end in (b.from_ref, b.to_ref)]
        if gecs and not any(larger(b.size, need) for b in gecs):
            out.extend(f"{b.tag} (#{b.size})" for b in gecs)
    return out


@check(Tier.CODE, NEUTRAL_CID)
def neutral_bond(ctx: CheckContext) -> list[Finding]:
    """250.24 / 250.32(B)(1) -- the main bonding jumper is in the service disconnect, and no
    panel downstream re-bonds the grounded conductor."""
    code = cite(NEC.SERVICE_GROUNDING)
    g = grounding(ctx)
    if g.root is None:
        if not ctx.plan.library.circuits:
            return [not_applicable(NEUTRAL_CID, "no service and no circuit in the plan",
                                   code=code)]
        return [unknown(NEUTRAL_CID, "no service disconnect is modeled", code=code)]
    se = service_entrance(ctx, g.root)
    panels = {c.panel_ref for c in ctx.plan.library.circuits}
    for supply in supplied_buildings(ctx).values():
        panels |= supply["panels"]
    panels.discard(g.root)
    if se is None or se.main_bonding_jumper_ref is None:
        return [unknown(NEUTRAL_CID, f"no ServiceEntrance states where {g.root}'s main bonding "
                        "jumper is", (g.root,), code,
                        fix="author a ServiceEntrance with main_bonding_jumper_ref and "
                            "neutral_isolated_refs")]
    out = []
    mbj = se.main_bonding_jumper_ref
    if mbj != g.root:
        out.append(failed(NEUTRAL_CID, f"the main bonding jumper is in {mbj}, not the service "
                          f"disconnect {g.root}", (mbj, g.root), code,
                          fix=f"bond the grounded conductor in {g.root} and isolate it beyond"))
    else:
        out.append(passed(NEUTRAL_CID, f"main bonding jumper in the service disconnect {mbj}",
                          (mbj,), code))
    for panel in sorted(panels - {mbj}):
        if panel in se.neutral_isolated_refs:
            out.append(passed(NEUTRAL_CID, f"{panel}'s grounded conductor is isolated from its "
                              "enclosure and EGCs", (panel,), code))
        else:
            out.append(unknown(NEUTRAL_CID, f"{panel} is downstream of {g.root} and is not "
                               "stated neutral-isolated", (panel,), code,
                               fix=f"add {panel} to {se.tag}.neutral_isolated_refs once the "
                                   "bonding screw or strap is out"))
    return out
