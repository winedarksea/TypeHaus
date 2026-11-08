"""Panel schedule and backup components — derived, never hand-summed.

The 120.82 service-load estimate lives in ``takeoff/service_load.py``; its public names are
re-exported here.

Circuits are authored (``Library.circuits``); everything here is a projection of them plus
the devices/equipment that reference them. Connected VA prefers the authored
``Circuit.load_va``; when unset it is summed from the referencing devices' typed
``ElectricalDeviceType.load_va``, plus any line-voltage ``LightRun`` on it at its type's
watts per resolved foot — a circuit with neither reports 0 and the schedule shows it, which
is the honest state, not an estimate.
"""

from __future__ import annotations

import math

from typehaus.model.enums import BackupTier
from typehaus.model.nec import NEC
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.raceways import conductor_takeoff as conductor_takeoff
from typehaus.takeoff.raceways import conduit_takeoff as conduit_takeoff
from typehaus.takeoff.service_load import DEFAULT_SERVICE_AMPS as DEFAULT_SERVICE_AMPS
from typehaus.takeoff.service_load import FIRST_8KVA as FIRST_8KVA
from typehaus.takeoff.service_load import GENERAL_LIGHTING_VA_PER_FT2 as GENERAL_LIGHTING_VA_PER_FT2
from typehaus.takeoff.service_load import REMAINDER_DEMAND_FACTOR as REMAINDER_DEMAND_FACTOR
from typehaus.takeoff.service_load import _circuit_consumers as _circuit_consumers
from typehaus.takeoff.service_load import _connected_va as _connected_va
from typehaus.takeoff.service_load import load_management_credits as load_management_credits
from typehaus.takeoff.service_load import service_load_summary as service_load_summary

_M2_TO_FT2 = 10.7639104167

# One Shelly Pro 4PM switches four circuits; the DIN rail carries one 24V PSU and one UPS
# regardless of relay count.
BACKUP_CIRCUITS_PER_RELAY = 4
# A Pro 4PM channel is rated 16A at 120V — a backup circuit breakered above that, or any
# 2-pole one, switches through a relay-driven DIN contactor instead (notes line 10:
# "Smart Relays (Shelly Pro 4PM) and contactors").
RELAY_CHANNEL_AMPS = 16

def panel_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per authored circuit: breaker, poles, NEMA, protection, load, consumers."""
    consumers = _circuit_consumers(model)
    rows = []
    for circuit in model.plan.library.circuits:
        served = consumers.get(circuit.tag, [])
        rows.append({
            "circuit": circuit.tag,
            "description": circuit.description,
            "breaker_amps": circuit.breaker_amps,
            "poles": circuit.poles,
            "volts": 240 if circuit.poles == 2 else 120,
            "nema": circuit.nema or "",
            "gfci": circuit.gfci,
            "gfci_class": getattr(circuit, "gfci_class", "A"),
            "afci": circuit.afci,
            "backup": circuit.backup_tier is not None,
            "backup_tier": circuit.backup_tier.value if circuit.backup_tier else "",
            "panel": circuit.panel_ref,
            "source": circuit.source,
            "connected_va": round(_connected_va(model, circuit, served), 0),
            "devices": sorted(element.tag for element in served),
        })
    return rows


def electrical_device_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Devices counted by kind + product type — what the electrician's order reads."""
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "ElectricalDevice":
                continue
            product = types.get(element.type_ref or "")
            key = (element.kind.value, element.type_ref or "(untyped)")
            row = groups.setdefault(key, {
                "kind": element.kind.value, "type": element.type_ref or "(untyped)",
                "name": product.name if product is not None else "",
                "nema": (product.nema or "") if product is not None else "",
                "count": 0})
            row["count"] = int(row["count"]) + 1
    return [groups[key] for key in sorted(groups)]


def solar_takeoff(model: ResolvedModel) -> dict[str, object]:
    """The array as installed: module count, total DC watts, per-product and per-string.

    Watts are summed from the resolved panels (the authored ``SolarPanel.watts`` carried
    through resolve), never a hand-typed total; the mounting kits are billed by the
    hardware take-off like every other modeled connector.

    The per-string rollup carries both Voc sums. ``voc_cold_v`` is the one that sizes
    conductors and gates the 690.12 grouping — a string that sums under the rated Voc
    limit can still be over it on a January morning — and either sum is None when any
    module in the string doesn't declare that voltage, because a partial sum of a series
    string is not a smaller string, it is a wrong number.
    """
    by_string: dict[str, dict[str, object]] = {}
    for panel in model.solar_panels:
        row = by_string.setdefault(panel.string or "(unstrung)", {
            "string": panel.string, "panels": 0, "watts": 0.0,
            "voc_v": 0.0, "voc_cold_v": 0.0, "voc_known": True, "voc_cold_known": True,
            "rsd_modules": 0, "tags": []})
        row["panels"] = int(row["panels"]) + 1
        row["watts"] = float(row["watts"]) + panel.watts
        if panel.voc is None:
            row["voc_known"] = False
        else:
            row["voc_v"] = float(row["voc_v"]) + panel.voc
        if panel.voc_cold is None:
            row["voc_cold_known"] = False
        else:
            row["voc_cold_v"] = float(row["voc_cold_v"]) + panel.voc_cold
        if panel.rsd:
            row["rsd_modules"] = int(row["rsd_modules"]) + 1
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(panel.tag)

    by_product: dict[str, dict[str, object]] = {}
    for panel in model.solar_panels:
        row = by_product.setdefault(panel.product or "(unspecified module)", {
            "product": panel.product, "panels": 0, "watts": 0.0, "tags": []})
        row["panels"] = int(row["panels"]) + 1
        row["watts"] = float(row["watts"]) + panel.watts
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(panel.tag)
    return {
        "panels": len(model.solar_panels),
        "total_watts": round(sum(panel.watts for panel in model.solar_panels), 0),
        "rsd_receivers": sum(1 for panel in model.solar_panels if panel.rsd),
        "by_product": [
            {"product": row["product"], "panels": int(row["panels"]),
             "watts": round(float(row["watts"]), 0), "tags": sorted(row["tags"])}
            for row in (by_product[key] for key in sorted(by_product))
        ],
        "by_string": [
            {"string": row["string"], "panels": int(row["panels"]),
             "watts": round(float(row["watts"]), 0),
             "voc_v": round(float(row["voc_v"]), 1) if row["voc_known"] else None,
             "voc_cold_v": (round(float(row["voc_cold_v"]), 1)
                            if row["voc_cold_known"] else None),
             "rsd_modules": int(row["rsd_modules"]), "tags": sorted(row["tags"])}
            for row in (by_string[key] for key in sorted(by_string))
        ],
    }


def backup_equipment(model: ResolvedModel) -> dict[str, list]:
    """The placed pieces of the backup microgrid, by role: batteries, inverters, panels.

    One place to ask "is there an ESS here", so the takeoff, the autonomy calc and the
    R327 checks all agree on the answer instead of each re-scanning the storeys.
    """
    batteries, inverters = [], []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment":
                continue
            kind = getattr(getattr(element, "kind", None), "value", None)
            if kind == "battery":
                batteries.append(element)
            elif kind == "inverter":
                inverters.append(element)
    return {"batteries": batteries, "inverters": inverters}


def backup_component_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """The backup microgrid's bill of components: the placed inverter and battery
    modules, the backup subpanel they feed, and the DIN gear that switches the SURPLUS tier.

    Derived twice over — the storage/inverter rows from placed ``Equipment`` (so a second
    battery module is a placement, not an edit here), the switching rows from the
    ``SURPLUS``-tier circuits (so re-tiering a circuit re-counts the relays). The ALWAYS_ON
    tier deliberately contributes no switching hardware: that is what the tier *means*.
    Empty when nothing is placed and nothing is tiered.
    """
    circuits = model.plan.library.circuits
    surplus = [c for c in circuits if c.backup_tier is BackupTier.SURPLUS]
    always_on = [c for c in circuits if c.backup_tier is BackupTier.ALWAYS_ON]
    placed = backup_equipment(model)
    if not (surplus or always_on or placed["batteries"] or placed["inverters"]):
        return []

    types = {t.tag: t for t in model.plan.library.equipment_types}
    device_types = {t.tag: t for t in model.plan.library.electrical_device_types}
    rows: list[dict[str, object]] = []

    for element in sorted(placed["inverters"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kw = getattr(product, "inverter_kw_continuous", None) if product else None
        rows.append({
            "component": (product.name if product is not None else "hybrid inverter"),
            "count": 1,
            "basis": (f"{element.tag}"
                      + (f" — {kw:g} kW continuous AC" if kw else "")),
        })
    for element in sorted(placed["batteries"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kwh = getattr(product, "storage_kwh", None) if product else None
        rows.append({
            "component": (product.name if product is not None else "battery module"),
            "count": 1,
            "basis": (f"{element.tag}"
                      + (f" — {kwh:g} kWh" if kwh else " — capacity not declared")),
        })

    # The backup subpanel: whichever panel the tiered circuits are homed to, when that is
    # not the same panel the rest of the house is on.
    backup_panels = sorted({c.panel_ref for c in (*always_on, *surplus)})
    main_panels = sorted({c.panel_ref for c in circuits if c.backup_tier is None})
    for panel_ref in backup_panels:
        if panel_ref in main_panels:
            continue
        spaces = getattr(device_types.get(_panel_type_ref(model, panel_ref) or ""),
                         "spaces", None)
        rows.append({
            "component": f"backup subpanel {panel_ref}", "count": 1,
            "basis": (f"{len(always_on) + len(surplus)} backup circuits"
                      + (f", {spaces}-space enclosure" if spaces else "")),
        })

    if surplus:
        relay_circuits = [c for c in surplus
                          if c.breaker_amps <= RELAY_CHANNEL_AMPS and c.poles == 1]
        contactor_circuits = [c for c in surplus
                              if c.breaker_amps > RELAY_CHANNEL_AMPS or c.poles == 2]
        if relay_circuits:
            rows.append({
                "component": "Shelly Pro 4PM 4-channel DIN relay",
                "count": math.ceil(len(relay_circuits) / BACKUP_CIRCUITS_PER_RELAY),
                "basis": (f"{len(relay_circuits)} surplus-tier circuit"
                          f"{'s' if len(relay_circuits) != 1 else ''} "
                          f"({', '.join(c.tag for c in relay_circuits)}) at "
                          f"{BACKUP_CIRCUITS_PER_RELAY} channels per relay"),
            })
        if contactor_circuits:
            rows.append({
                "component": "DIN contactor (relay-driven)",
                "count": len(contactor_circuits),
                "basis": (f"surplus-tier circuits over the {RELAY_CHANNEL_AMPS}A relay "
                          f"channel or 2-pole "
                          f"({', '.join(c.tag for c in contactor_circuits)})"),
            })
        # One relay channel drives however many contactors there are; a surplus tier made
        # entirely of contactor circuits still needs the relay that commands them.
        if contactor_circuits and not relay_circuits:
            rows.append({
                "component": "Shelly Pro 4PM 4-channel DIN relay", "count": 1,
                "basis": "one relay to drive the surplus-tier contactor coils",
            })

    rsd = sum(1 for panel in model.solar_panels if panel.rsd)
    if rsd:
        rows.append({
            "component": "SunSpec rapid-shutdown receiver (module level)",
            "count": rsd,
            "basis": f"{rsd} modules carrying rsd=True ({NEC.RAPID_SHUTDOWN}; inverter is the "
                     "transmitter)",
        })

    rows.extend([
        {"component": "24V DIN-rail power supply", "count": 1,
         "basis": "one 24V bus for LED backup lighting + PoE (notes lines 13-15)"},
        {"component": "DIN-rail 24V UPS module", "count": 1,
         "basis": "backup light/network ride-through (notes line 14)"},
    ])
    return rows


def _panel_type_ref(model: ResolvedModel, panel_tag: str) -> str | None:
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind == "ElectricalDevice" and element.tag == panel_tag:
                return element.type_ref
    return None
