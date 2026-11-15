"""NEC field labels, derived: one record per label, from the model fact that triggers it.

No label is authored. PV modules bring the 690.12(D) building label at the service and the
(D)(2) wording at each ``rsd_initiator``, the 690.7(D) voltage label at the inverter and the
690.31(D)(2) markings on every PV dc raceway (one per 10 ft of run, plus each junction-box
cover); a source circuit brings the 705.10 plaque (with 702.7(A)(1) on it when a backup panel
exists, the one placard the paraphrase allows), the 230.70(D) directory where the source
breakers are not at the service, and the 705.12(B)(2)(b) warning when (B)(1) does not hold; a
battery brings 706.15(C) at its disconnect and 480.7(F) beside it; a heating-cable circuit
424.47 at its panel; an EV circuit whose breaker is in another room 625.43(C) on the unit.

Wording comes only from ``docs/code-notes/nec-2026-paraphrase*.md``: ``literal`` words are the code's
own; otherwise ``wording`` states the content the code requires. A house input the label
prints and the model lacks (705.10's phone, the battery's voltage) is named in ``missing``
and ``electrical.label_inputs`` reports it UNKNOWN; nothing is defaulted. Billed by the each
in ``[electrical_labels]``; scheduled on E-605.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.model.nec import NEC
from typehaus.resolve.grounding import service_root

_FT = 0.3048
_MARK_EVERY_FT = 10.0  # 690.31(D)(2)
_WHITE_ON_RED = "white on red capitals at least 3/8 in."


@dataclass(frozen=True)
class ResolvedElectricalLabel:
    uid: str  # "label/<section>/<host>": stable across rebuilds
    section: str  # the NEC row (model/nec.py)
    wording: str
    literal: bool  # True: the code's own words; False: the content it requires
    host_ref: str | None
    location: str  # the placement rule
    quantity: int
    basis: str  # the model fact that derives it
    also: tuple[str, ...] = ()  # other rows the same label serves
    missing: tuple[str, ...] = ()  # house inputs it prints that are not authored
    condition: str | None = None  # applies only if an open question resolves so


def _label(section: str, host: str | None, wording: str, location: str, basis: str, *,
           literal: bool = True, quantity: int = 1, key: str | None = None,
           **extra: Any) -> ResolvedElectricalLabel:
    return ResolvedElectricalLabel(f"label/{section}/{key or host or '-'}", section, wording,
                                   literal, host, location, quantity, basis, **extra)


def _where(element: Any, rooms: dict[str, str | None]) -> str:
    return f"{element.tag} ({rooms.get(element.tag) or 'outdoors'})"


def resolve_electrical_labels(model: Any) -> None:
    plan = model.plan
    elements = list(plan.all_elements())
    dev_types = {t.tag: t for t in plan.library.electrical_device_types}
    eq_types = {t.tag: t for t in plan.library.equipment_types}
    devices = {e.tag: e for e in elements if e.element_kind == "ElectricalDevice"}
    circuits = list(plan.library.circuits)
    root = service_root(plan)
    from typehaus.resolve.room_lookup import room_owning

    # The room each device stands in: authored, else the one whose cell covers it.
    rooms: dict[str, str | None] = {t: d.room for t, d in devices.items()}
    for obj in model.canvas_objects:
        if obj.tag in devices and not rooms[obj.tag]:
            room = room_owning(model, obj.storey, obj.position)
            rooms[obj.tag] = room.tag if room is not None else None
    out = model.electrical_labels
    out.extend(_pv_labels(model, devices, dev_types, eq_types, elements, root))
    out.extend(_source_labels(model, elements, devices, dev_types, eq_types, circuits, root,
                              rooms))
    out.extend(_service_labels(plan, devices, dev_types, root))
    out.extend(_storage_labels(elements, circuits, eq_types))
    out.extend(_battery_emergency_labels(elements, devices, dev_types, eq_types))
    out.extend(_heat_labels(elements, devices, circuits))
    out.extend(_evse_labels(devices, circuits, rooms))


def _inverters(elements, eq_types) -> list:
    return sorted((e for e in elements if e.element_kind == "Equipment"
                   and getattr(eq_types.get(e.type_ref or ""), "inverter_kw_continuous", None)),
                  key=lambda e: e.tag)


def _pv_labels(model, devices, dev_types, eq_types, elements, root):
    if not model.solar_panels:
        return []
    out = []
    if root:
        out.append(_label(
            NEC.RAPID_SHUTDOWN_BUILDING_LABEL, root,
            'SOLAR PV SYSTEM EQUIPPED WITH RAPID SHUTDOWN. TURN RAPID SHUTDOWN SWITCH TO THE '
            '"OFF" POSITION TO SHUT DOWN PV SYSTEM AND REDUCE SHOCK HAZARD IN ARRAY.',
            "at the service equipment where the PV connects, or an approved visible spot; a "
            "simple building-and-roof diagram showing where the initiation devices are; "
            "heading capitals at least 3/8 in., reflective white on red",
            f"{len(model.solar_panels)} PV modules; service equipment {root}"))
    for tag in sorted(t for t, d in devices.items()
                      if getattr(dev_types.get(d.type_ref or ""), "rsd_initiator", False)):
        out.append(_label(NEC.RAPID_SHUTDOWN_SWITCH_LABEL, tag,
                          "RAPID SHUTDOWN SWITCH FOR SOLAR PV SYSTEM",
                          "on the switch or within 3 ft of it",
                          f"{tag} is typed rsd_initiator"))
    runs = sorted((r for r in model.conduits if r.service == "power_dc"), key=lambda r: r.tag)
    dc_ends = {ref for r in runs for ref in (r.from_ref, r.to_ref) if ref}
    inverter = next((e for e in _inverters(elements, eq_types) if e.tag in dc_ends), None)
    if inverter is not None:
        strings: dict[str, list] = {}
        for p in model.solar_panels:
            strings.setdefault(p.string or "(unstrung)", []).append(p)
        cold = [p.voc_cold for p in model.solar_panels]
        volts = max((sum(p.voc_cold or 0.0 for p in s) for s in strings.values()), default=0.0)
        missing = () if all(v is not None for v in cold) else ("module voc_cold",)
        wording = ("states the maximum PV dc voltage" if missing
                   else f"states the maximum PV dc voltage: {math.ceil(volts - 1e-9)} V")
        out.append(_label(NEC.PV_VOLTAGE_LABEL, inverter.tag, wording,
                          "permanent, readily visible, at the dc PV disconnect, the conversion "
                          "equipment or the distribution equipment (rounding up allowed)",
                          f"largest string {volts:.1f} V cold (690.7(A)(1)); PV dc lands on "
                          f"{inverter.tag}", literal=False, missing=missing))
    for run in runs:
        feet = run.length_m / _FT
        out.append(_label(NEC.PV_DC_MARKING, run.tag,
                          'PHOTOVOLTAIC POWER SOURCE (or "SOLAR PV DC CIRCUIT")',
                          f"on the exposed raceway, every section separated by a wall, "
                          f"partition, ceiling or floor, at 10 ft or less; {_WHITE_ON_RED}",
                          f"{feet:.1f} ft of PV dc raceway, one per {_MARK_EVERY_FT:g} ft "
                          "(the whole run counted; a concealed length needs none)",
                          quantity=max(1, math.ceil(feet / _MARK_EVERY_FT - 1e-9))))
    for tag in sorted(dc_ends):
        dev = devices.get(tag)
        if dev is not None and getattr(dev.kind, "value", "") == "junction_box":
            out.append(_label(NEC.PV_DC_MARKING, tag,
                              'PHOTOVOLTAIC POWER SOURCE (or "SOLAR PV DC CIRCUIT")',
                              f"on the box cover; {_WHITE_ON_RED}",
                              f"{tag} is a junction box on a PV dc raceway"))
    return out


def _source_breakers(circuits) -> list:
    return sorted((c for c in circuits if c.source), key=lambda c: c.tag)


def _source_labels(model, elements, devices, dev_types, eq_types, circuits, root, rooms):
    sources = _source_breakers(circuits)
    if not root or not (sources or model.solar_panels):
        return []
    rsd = sorted(t for t, d in devices.items()
                 if getattr(dev_types.get(d.type_ref or ""), "rsd_initiator", False))
    where = [f"{c.tag} breaker, "
             f"{_where(devices[c.panel_ref], rooms) if c.panel_ref in devices else c.panel_ref}"
             f" slot {c.slot}" for c in sources] + [f"{t} (PV rapid shutdown)" for t in rsd]
    standard = next((e for e in elements if e.element_kind == "LabelStandard"), None)
    contacts = getattr(standard, "source_service_contacts", None)
    phone = ("emergency phone: not authored" if contacts is None
             else "; ".join(contacts) or "no off-site entity services the sources")
    standby = any(c.backup_tier for c in circuits) and bool(_inverters(elements, eq_types))
    also = (NEC.STANDBY_SIGN,) if standby else ()
    out = [_label(
        NEC.SOURCE_PLAQUE, root,
        "CAUTION: MULTIPLE SOURCES OF POWER; where each source's disconnect is: "
        + "; ".join(where) + f"; {phone}"
        + ("; where the standby source's disconnect is (702.7(A)(1))" if standby else ""),
        "permanent plaque, label or directory at the service equipment or an approved visible "
        "spot" + ("; one placard serves 705.10 and 702.7(A)(1)" if standby else ""),
        f"the utility service plus {len(sources)} source circuit(s)"
        + (f" and {len(model.solar_panels)} PV modules" if model.solar_panels else "")
        + ("; backup-tier circuits on an inverter (optional standby)" if standby else ""),
        literal=False, also=also,
        missing=("LabelStandard.source_service_contacts",) if contacts is None else ())]
    remote = [w for c, w in zip(sources, where[:len(sources)], strict=True) if c.panel_ref != root]
    if remote:
        out.append(_label(NEC.SERVICE_OTHER_SOURCES, root,
                          "where each other energy source's disconnect is: " + "; ".join(remote),
                          "plaque or directory at the service disconnect",
                          "source breakers not next to the service disconnect", literal=False))
    out.extend(_busbar_labels(elements, devices, dev_types, eq_types, sources))
    return out


def _busbar_labels(elements, devices, dev_types, eq_types, sources):
    """705.12(B)(2)(b): only where (B)(1) fails, the arithmetic of the 705.12 check."""
    out = []
    by_panel: dict[str, list] = {}
    for c in sources:
        by_panel.setdefault(c.panel_ref, []).append(c)
    for panel, group in sorted(by_panel.items()):
        ptype = dev_types.get(getattr(devices.get(panel), "type_ref", None) or "")
        bus, main = getattr(ptype, "bus_amps", None), getattr(ptype, "service_amps", None)
        source = 0.0
        for c in group:
            kw = sum(float(getattr(eq_types.get(e.type_ref or ""), "inverter_kw_continuous",
                                   None) or 0.0)
                     for e in elements if e.element_kind == "Equipment"
                     and getattr(e, "circuit", None) == c.tag)
            volts = 240.0 if c.poles >= 2 else 120.0
            source += 1.25 * math.floor(kw * 1000.0 / volts + 0.5) if kw else c.breaker_amps
        slots = ", ".join(f"{c.tag} slot {c.slot}" for c in group)
        if bus is None or main is None:
            condition, basis = (f"{NEC.INTERCONNECTION_120PCT} is relied on",
                                f"{panel} states no bus or main rating")
        elif main + source <= bus + 1e-9:
            continue
        else:
            condition, basis = None, (f"{main:g} A main + {source:g} A source exceeds the "
                                      f"{bus:g} A bus, so {NEC.INTERCONNECTION_120PCT} governs")
        out.append(_label(NEC.INTERCONNECTION_LABEL, panel,
                          "WARNING: POWER SOURCE OUTPUT. DO NOT RELOCATE THIS OVERCURRENT "
                          "DEVICE.", f"permanent, next to the source OCPD ({slots})", basis,
                          condition=condition))
    return out


def _service_labels(plan, devices, dev_types, root):
    if not root:
        return []
    buildings = plan.project.buildings
    if buildings and not any(b.kind == "dwelling" for b in buildings):
        return []
    mains = sorted(t for t, d in devices.items() if t != root
                   and getattr(d.kind, "value", "") == "panel"
                   and getattr(dev_types.get(d.type_ref or ""), "service_amps", None))
    return [
        _label(NEC.SERVICE_DISCONNECT_MARKING, root, "SERVICE DISCONNECT",
               "on or next to each service disconnect", f"{root} is the service equipment; one "
               f"disconnect per feeder panel with a main ({', '.join(mains) or 'none'})",
               quantity=max(1, len(mains))),
        _label(NEC.SERVICE_EMERGENCY_MARKING, root, "EMERGENCY DISCONNECT",
               "on the outside front of the enclosure, white on red, letters at least 1/2 in.",
               "a one- or two-family dwelling's service enclosure"),
    ]


def _battery_emergency_labels(elements, devices, dev_types, eq_types):
    """480.7(B): an outdoor initiator whose loop the inverter's maker says also opens the ESS
    is the battery's remote control; the label is owed only if the AHJ applies (B) below 60 V."""
    batteries = [e for e in elements if e.element_kind == "Equipment"
                 and getattr(e.kind, "value", "") == "battery"]
    scoped = [e for e in _inverters(elements, eq_types)
              if "ess" in (getattr(eq_types[e.type_ref], "rsd_shutdown_scope", None) or ())]
    if not batteries or not scoped:
        return []
    return [_label(NEC.BATTERY_EMERGENCY_DISCONNECT, tag, "EMERGENCY DISCONNECT",
                   "on the outdoor initiator, beside the 690.12(D)(2) wording",
                   f"{tag} initiates {scoped[0].tag}'s ESS disconnect (rsd_shutdown_scope)",
                   condition="the AHJ reads 480.7(B) as standing apart from (A)'s 60 V")
            for tag in sorted(t for t, d in devices.items()
                              if getattr(dev_types.get(d.type_ref or ""), "rsd_initiator", False))]


def _storage_labels(elements, circuits, eq_types):
    out = []
    by_tag = {c.tag: c for c in circuits}
    for battery in sorted((e for e in elements if e.element_kind == "Equipment"
                           and getattr(e.kind, "value", "") == "battery"), key=lambda e: e.tag):
        circuit = by_tag.get(getattr(battery, "circuit", None) or "")
        if circuit is not None:
            volts = 240 if circuit.poles >= 2 else 120
            out.append(_label(NEC.ESS_DISCONNECT_MARKING, circuit.panel_ref,
                              f"ENERGY STORAGE SYSTEM DISCONNECT; nominal output {volts} V",
                              f"on the disconnect ({circuit.tag} breaker, slot {circuit.slot}), "
                              "which shows open or closed; a dwelling needs only the voltage",
                              f"{battery.tag} disconnects at {circuit.tag}", key=circuit.tag))
        nominal = getattr(eq_types.get(battery.type_ref or ""), "battery_nominal_voltage_v", None)
        out.append(_label(NEC.BATTERY_VOLTAGE_LABEL, battery.tag,
                          f"states the nominal battery voltage: {nominal:g} V dc" if nominal
                          else "states the nominal battery voltage",
                          "near the battery, where no dc disconnect is provided (a dwelling "
                          "under 150 V dc needs only the voltage)",
                          f"{battery.tag} is a stationary battery", literal=False,
                          missing=() if nominal else ("battery nominal voltage",)))
        if circuit is not None and circuit.source:
            out.append(_label(NEC.SWITCH_BACKFEED_SIGN, circuit.panel_ref,
                              "WARNING - LOAD SIDE TERMINALS MAY BE ENERGIZED BY BACKFEED",
                              f"on or beside the {circuit.tag} breaker (110.21(B))",
                              f"{circuit.tag} is a source circuit the inverter feeds",
                              key=circuit.tag,
                              condition="the inverter keeps its grid-port terminals energized "
                                        "with the breaker open (EG4; the 705.20(F) question)"))
    return out


def _heat_labels(elements, devices, circuits):
    by_tag = {c.tag: c for c in circuits}
    zones: dict[str, list[str]] = {}
    for e in elements:
        if e.element_kind == "FloorHeat" and getattr(e.system, "value", "") == "electric":
            stat = devices.get(e.thermostat_ref or "")
            if stat is not None and stat.circuit in by_tag:
                zones.setdefault(stat.circuit, []).append(e.tag)
    out = []
    for name, tags in sorted(zones.items()):
        c = by_tag[name]
        out.append(_label(NEC.SPACE_HEAT_LABEL, c.panel_ref,
                          "the cable maker's label: the space-heating installation "
                          "incorporates electric heating cable",
                          f"on the panelboard where {name} originates (slot {c.slot}), per "
                          "110.21(B)", f"{name} feeds heating cable {', '.join(sorted(tags))}, "
                          "covered after installation", literal=False, key=name))
    return out


def _evse_labels(devices, circuits, rooms):
    """625.43(C): a hardwired EVSE whose only disconnect, its breaker, is in another room.
    An EV circuit is the one whose description says EV charging (``service_load._bucket``)."""
    out = []
    for c in sorted(circuits, key=lambda c: c.tag):
        if c.source or "ev charging" not in c.description.lower():
            continue
        on = [d for d in devices.values() if d.circuit == c.tag]
        panel = devices.get(c.panel_ref)
        if len(on) != 1 or getattr(on[0].kind, "value", "") != "junction_box" or panel is None:
            continue
        unit = on[0]
        here, there = rooms.get(unit.tag), rooms.get(panel.tag)
        if here and here == there:
            continue
        out.append(_label(NEC.EVSE_DISCONNECT, unit.tag,
                          f"says where its disconnect is: {c.tag} breaker, {_where(panel, rooms)} "
                          f"slot {c.slot}", "a plaque on the EVSE",
                          f"{unit.tag} is hardwired on {c.tag}; its breaker is in "
                          f"{there or 'no room'}, not {here or 'outdoors'}",
                          literal=False))
    return out
