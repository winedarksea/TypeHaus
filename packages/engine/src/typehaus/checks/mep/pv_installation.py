"""CODE-tier PV installation rules from Article 690 (printed 2026 text, read 2026-11-14).

- **690.4(D)** no PV equipment or disconnect in a bathroom.
- **690.7** maximum dc voltage of a source circuit, 600 V on or in a dwelling.
- **690.31(D)(1)** PV dc over 30 V or 8 A inside a building runs in a metal raceway.
- **690.45** the array EGC is no smaller than Table 250.122 gives for the (assumed) OCPD.

Paraphrase and what is not graded: ``docs/code-notes/nec-2026-paraphrase-690-705-710.md``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_grounding import device_types, grounding
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.ampacity import egc_minimum, next_standard_rating, size_at_least
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import room_owning

BATH_CID = "code.NEC_690_4_pv_bathroom"
VOLT_CID = "code.NEC_690_7_max_voltage"
WIRING_CID = "code.NEC_690_31_dc_wiring"
EGC_CID = "code.NEC_690_45_pv_egc_size"

_DWELLING_LIMIT_V = 600.0  # 690.7(2)
_GENERAL_LIMIT_V = 1000.0  # 690.7(1); above it 690.31(G)
_PLAIN_V, _PLAIN_A = 30.0, 8.0  # 690.31(D)(1) applies over either


def _dwelling(ctx: CheckContext) -> bool:
    """A project naming no building, or naming a dwelling, is read as a dwelling."""
    buildings = ctx.plan.project.buildings
    return not buildings or any(b.kind == "dwelling" for b in buildings)


def _strings(ctx: CheckContext) -> dict[str, list]:
    out: dict[str, list] = {}
    for panel in ctx.model.solar_panels:
        out.setdefault(panel.string or "(unstrung)", []).append(panel)
    return out


@check(Tier.CODE, BATH_CID)
def pv_not_in_bathroom(ctx: CheckContext) -> list[Finding]:
    """690.4(D) — no PV equipment or disconnect in a bathroom.

    PV equipment is every inverter (an equipment type declaring ``inverter_kw_continuous``),
    rapid-shutdown initiator, PV dc SPD and non-panel endpoint of a ``power_dc`` raceway. The
    PV disconnect is not modeled, so a PASS names what was located and nothing more.
    """
    code = cite(NEC.PV_BATHROOM)
    eq_types = {t.tag: t for t in ctx.plan.library.equipment_types}
    dev_types = device_types(ctx)
    dc_ends = {ref for run in ctx.model.conduits if run.service == "power_dc"
               for ref in (run.from_ref, run.to_ref) if ref}
    panels = {e.tag for e in ctx.plan.all_elements()
              if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"}
    found = []
    for obj in ctx.model.canvas_objects:
        etype, dtype = eq_types.get(obj.type_ref or ""), dev_types.get(obj.type_ref or "")
        if (getattr(etype, "inverter_kw_continuous", None)
                or getattr(dtype, "rsd_initiator", False)
                or getattr(dtype, "spd_class", None) == "pv_dc"
                or (obj.tag in dc_ends and obj.tag not in panels)):
            found.append(obj)
    if not ctx.model.solar_panels and not found:
        return [not_applicable(BATH_CID, "no PV module or inverter is modeled", (), code)]
    out: list[Finding] = []
    where: list[str] = []
    for obj in sorted(found, key=lambda o: o.tag):
        room = room_owning(ctx.model, obj.storey, obj.position)
        if room is not None and room.occupancy == "bathroom":
            out.append(failed(BATH_CID, f"{obj.tag} is PV equipment in bathroom {room.tag}",
                              (obj.tag, room.tag), code, fix="move it out of the bathroom"))
        else:
            where.append(f"{obj.tag} ({room.tag if room else 'outdoors'})")
    if where:
        out.append(passed(BATH_CID, "no PV equipment is in a bathroom: " + ", ".join(where)
                          + "; the PV disconnect is not modeled", (), code))
    return out


@check(Tier.CODE, VOLT_CID)
def pv_max_voltage(ctx: CheckContext) -> list[Finding]:
    """690.7 — a source circuit's cold maximum voltage, at most 600 V on a dwelling.

    The sum is of ``voc_cold`` per string: the listed temperature coefficient to the design
    low, 690.7(A)(1). Table 690.7(A) (``model/pv_voltage.py``) is the alternative where no
    coefficient is listed and needs an ambient the plan does not carry, so it is not read.
    """
    code = cite(NEC.PV_MAX_VOLTAGE_DWELLING, NEC.PV_VOLTAGE_COEFFICIENT)
    strings = _strings(ctx)
    if not strings:
        return [not_applicable(VOLT_CID, "no PV module is modeled", (), code)]
    limit = _DWELLING_LIMIT_V if _dwelling(ctx) else _GENERAL_LIMIT_V
    out: list[Finding] = []
    for tag, modules in sorted(strings.items()):
        tags = tuple(sorted(p.tag for p in modules))
        if any(p.voc_cold is None for p in modules):
            out.append(unknown(VOLT_CID, f"string {tag}: a module declares no voc_cold, so "
                               "the cold maximum voltage is unknown", tags, code,
                               "author voc_cold from the datasheet coefficient at the design low"))
            continue
        volts = sum(p.voc_cold for p in modules)
        if volts > limit + 1e-9:
            out.append(failed(VOLT_CID, f"string {tag}: {volts:.1f}V cold exceeds the "
                              f"{limit:g}V limit", tags, code, fix="shorten the string"))
        else:
            out.append(passed(VOLT_CID, f"string {tag}: {volts:.1f}V cold ({len(modules)} "
                              f"modules, listed coefficient) within {limit:g}V", tags, code))
    return out


def _inside_building(ctx: CheckContext, run) -> bool:
    objs = {o.tag: o for o in ctx.model.canvas_objects}
    spots = [(run.storey, pt) for pt in run.path]
    spots += [(objs[r].storey, objs[r].position) for r in (run.from_ref, run.to_ref)
              if r in objs]
    return any(room_owning(ctx.model, storey, xy) is not None for storey, xy in spots)


@check(Tier.CODE, WIRING_CID)
def pv_dc_in_metal(ctx: CheckContext) -> list[Finding]:
    """690.31(D)(1) — PV dc over 30 V or 8 A inside a building is in metal raceway.

    A ``power_dc`` raceway with any vertex or end in a room is inside; EMT passes, ENT and PVC
    fail (a listed PVHCS or MC/metal enclosure alternative is not modeled). The (D)(2) cover
    markings are not modeled.
    """
    code = cite(NEC.PV_DC_WIRING_BUILDING)
    runs = sorted((r for r in ctx.model.conduits if r.service == "power_dc"),
                  key=lambda r: r.tag)
    if not runs:
        return [not_applicable(WIRING_CID, "no raceway carries PV dc", (), code)]
    panels = ctx.model.solar_panels
    volts = max((sum(p.voc_cold or p.voc or 0.0 for p in m) for m in _strings(ctx).values()),
                default=0.0)
    amps = max((1.25 * p.isc for p in panels if p.isc), default=0.0)
    if panels and all(p.voc_cold or p.voc for p in panels) and volts <= _PLAIN_V \
            and amps and amps <= _PLAIN_A:
        return [not_applicable(WIRING_CID, f"PV dc is {volts:.0f}V and {amps:.1f}A, under the "
                               "30 V / 8 A line", tuple(r.tag for r in runs), code)]
    out: list[Finding] = []
    for run in runs:
        if not _inside_building(ctx, run):
            continue
        if run.material == "emt":
            out.append(passed(WIRING_CID, f"{run.tag} is EMT inside the building",
                              (run.tag,), code))
        else:
            out.append(failed(WIRING_CID, f"{run.tag} is {run.material.upper()} inside the "
                              "building; PV dc over 30 V or 8 A needs a metal raceway, MC or "
                              "a metal enclosure (unless a listed PVHCS)", (run.tag,), code,
                              fix="run it in EMT or MC"))
    return out or [not_applicable(WIRING_CID, "every PV dc raceway lies outside the building",
                                  tuple(r.tag for r in runs), code)]


@check(Tier.CODE, EGC_CID)
def pv_egc_size(ctx: CheckContext) -> list[Finding]:
    """690.45 — the array's bonding conductors are no smaller than Table 250.122.

    The OCPD is the assumed one of 690.9(B): 125% of 690.8(A)(1)(a)'s 125% of module Isc (one
    module in parallel per string), to the next standard size. The bonds are those touching a
    module and any bond hanging off them. No module ``isc`` is UNKNOWN. Not graded: 250.122(D)
    upsizing, the 250.120 aluminium limits, and the 250.66 electrode-conductor cap.
    """
    code = cite(NEC.PV_EGC_SIZE, NEC.EGC_TABLE)
    panels = ctx.model.solar_panels
    if not panels:
        return [not_applicable(EGC_CID, "no PV module is modeled", (), code)]
    g = grounding(ctx)
    names = {p.tag for p in panels}
    chain = {b.tag for b in g.bonds if names & {b.from_ref, b.to_ref}}
    while True:
        more = {b.tag for b in g.bonds if b.tag not in chain and {b.from_ref, b.to_ref} & chain}
        if not more:
            break
        chain |= more
    if not chain:
        return [unknown(EGC_CID, "no bonding conductor leaves the array to size", (), code)]
    if any(p.isc is None for p in panels):
        return [unknown(EGC_CID, "a module declares no isc, so the assumed OCPD of 690.9(B) "
                        "and the Table 250.122 row are unknown", (), code,
                        "author isc from the module datasheet")]
    circuit = 1.25 * max(p.isc for p in panels)
    ocpd = next_standard_rating(1.25 * circuit)
    out: list[Finding] = []
    for bond in sorted((b for b in g.bonds if b.tag in chain), key=lambda b: b.tag):
        material = "cu" if bond.material == "copper" else "al"
        need = egc_minimum(ocpd, material)
        head = (f"{bond.tag}: {bond.size} {bond.material} against #{need} for an assumed "
                f"{ocpd}A OCPD ({circuit:.1f}A circuit)")
        if size_at_least(bond.size, need):
            out.append(passed(EGC_CID, head + ", meets Table 250.122", (bond.tag,), code))
        else:
            out.append(failed(EGC_CID, head + ", under the table", (bond.tag,), code,
                              fix=f"use at least #{need}"))
    return out
