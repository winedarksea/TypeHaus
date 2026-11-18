"""Lighting take-offs: the luminaire schedule, its controls, the runs, and the real load.

Everything here is a projection of the authored fixtures and their ``LuminaireType``s. No
row is hand-summed and no wattage is invented — a fixture whose type states no lumens
reports ``None``, because a schedule that fills a blank with a plausible number is worse
than one that admits the gap.

The load section exists to answer a question NEC 120.82 deliberately does not. The service
calculation takes lighting as a 2 VA/ft2 area allowance and never looks at a fixture, which
is code-correct and tells a designer nothing about whether an all-LED house is anywhere
near that allowance. So the connected total is reported *beside* the allowance rather than
replacing it (→ takeoff/electrical.service_load_summary, which is unchanged).
"""

from __future__ import annotations

from typing import TypedDict, TypeGuard

from typehaus.model.base import Element
from typehaus.model.electrical import luminaire_types
from typehaus.model.mep import ElectricalDevice
from typehaus.model.nec import NEC
from typehaus.model.placeables import Mount
from typehaus.model.types import ElectricalDeviceType, LuminaireType
from typehaus.resolve.model import ResolvedLightRun, ResolvedModel
from typehaus.takeoff.lighting_supplies import (
    PSU_SIZING_FACTOR,
    effective_lighting_circuit,
    electrical_devices,
    input_va,
    rated_output_w,
    supplied_loads,
)

_M_TO_FT = 3.280839895013123
_M2_TO_FT2 = 10.7639104167


def nec_floor_area_ft2(model: ResolvedModel) -> float:
    """NEC 120.5(C) floor area: outside dimensions, the one CFA the set prints (G-001),
    not the sum of room clear areas (D1-010). Falls back to rooms when no envelope resolves."""
    from typehaus.resolve.conditioned_area import conditioned_floor_area

    area_m2 = conditioned_floor_area(model).area_m2
    if area_m2 <= 1e-6:
        area_m2 = sum(room.area_m2 for room in model.rooms if room.conditioned)
    return area_m2 * _M2_TO_FT2

# Mirrors ``takeoff/electrical.GENERAL_LIGHTING_VA_PER_FT2``. Restated rather than imported
# so this module can be read on its own; the parity is pinned by the takeoff test.
GENERAL_LIGHTING_VA_PER_FT2 = 2.0  # 2026 NEC 120.82(B) / 120.41

class _RunTypeTotals(TypedDict):
    type: str
    mark: str
    runs: int
    length_ft: float
    watts: float


class _SupplyTotals(TypedDict):
    psu: str
    runs: list[str]
    fixtures: list[str]
    length_ft: float
    watts: float


class _CircuitTotals(TypedDict):
    circuit: str
    fixtures: int
    runs: int
    connected_va: float


def _device_types(model: ResolvedModel) -> dict[str, ElectricalDeviceType]:
    return {product.tag: product for product in model.plan.library.electrical_device_types}


def _is_electrical_device(element: Element) -> TypeGuard[ElectricalDevice]:
    # The element registry assigns this discriminator to ElectricalDevice instances.
    return element.element_kind == "ElectricalDevice"


def _luminaires(model: ResolvedModel) -> list[ElectricalDevice]:
    return [element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if _is_electrical_device(element)
            and element.kind.value == "light"]


def _mount_label(element: ElectricalDevice) -> str:
    mount: Mount | None = getattr(element, "mount", None)
    if mount is None:
        return "floor"
    kind = mount.kind.value
    if kind == "ceiling" and getattr(mount, "recessed_into_host_surface", False):
        return "recessed ceiling"
    if kind == "ceiling" and mount.drop is not None:
        return "suspended ceiling"
    return kind


def _rating_label(product: LuminaireType) -> str:
    if product.wet_rated:
        return "wet"
    if product.damp_rated:
        return "damp"
    return "dry"


def _run_watts(run: ResolvedLightRun, product: ElectricalDeviceType | None) -> float:
    """One run's connected watts: its type's per-foot draw over its *resolved* length.

    The single place that product is formed — the authored ``LightRun`` carries a ``path``,
    not a length, so every caller reads ``ResolvedLightRun.length_m``.
    """
    watts_per_ft = getattr(product, "watts_per_ft", None) or 0.0
    return watts_per_ft * getattr(run, "length_m", 0.0) * _M_TO_FT


def line_voltage_run_va(model: ResolvedModel) -> dict[str, float]:
    """``{run tag: connected VA}`` for every *line-voltage* run, indexed by tag.

    A line-voltage run is one with a ``circuit`` and no ``psu_ref``: it is a load on a
    branch circuit in its own right, and nothing else in the model accounts for it. A 24V
    run is deliberately absent — its load belongs to its supply, which is a device on a
    circuit like any other, and counting both would double the tape
    (→ ``takeoff/electrical._connected_va``, which indexes this by the authored element's
    tag). VA is taken as watts: an LED driver at unity power factor.
    """
    types = _device_types(model)
    return {run.tag: _run_watts(run, types.get(run.type_ref))
            for run in model.light_runs if run.circuit and run.psu_ref is None}


def luminaire_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per luminaire *type* that is actually installed, keyed by schedule mark.

    Rows are ordered by mark, which is the order the sheet prints and the order a reader
    scans. ``count`` counts point fixtures; a linear type installed as runs reports its
    lineal feet instead, because a cove has no unit to count.
    """
    types = luminaire_types(model.plan.library)
    counts: dict[str, int] = {}
    rooms: dict[str, set[str]] = {}
    for element in _luminaires(model):
        if element.type_ref not in types:
            continue
        counts[element.type_ref] = counts.get(element.type_ref, 0) + 1
        rooms.setdefault(element.type_ref, set()).add(element.room or "(unassigned)")
    run_feet: dict[str, float] = {}
    for run in model.light_runs:
        run_feet[run.type_ref] = run_feet.get(run.type_ref, 0.0) + run.length_m * _M_TO_FT
        rooms.setdefault(run.type_ref, set()).add(run.room or "(unassigned)")

    mount_by_type: dict[str, set[str]] = {}
    for element in _luminaires(model):
        if element.type_ref in types:
            mount_by_type.setdefault(element.type_ref, set()).add(_mount_label(element))

    products = {item.tag: item for item in model.plan.library.products}
    rows: list[dict[str, object]] = []
    for tag in set(counts) | set(run_feet):
        product = types[tag]
        chosen = products.get(product.product_ref or "")
        rows.append({
            "mark": product.type_mark or "",
            "type": tag,
            "description": product.name,
            "form": product.form.value,
            "lamp": product.lamp,
            "watts": product.watts,
            "watts_per_ft": product.watts_per_ft,
            "lumens": product.lumens,
            "cct_k": product.cct_k,
            "cct_range_k": list(product.cct_range_k) if product.cct_range_k else None,
            "color_mode": product.color_mode,
            "lamp_base": product.lamp_base,
            "replaceable_lamp": product.replaceable_lamp,
            "cri": product.cri,
            "volts": product.voltage,
            "mount": ", ".join(sorted(mount_by_type.get(tag, set()))) or "run",
            "dimming": "dimmable" if product.dimmable else "switched",
            "rating": _rating_label(product),
            "count": counts.get(tag, 0),
            "length_ft": round(run_feet[tag], 1) if tag in run_feet else None,
            "rooms": sorted(rooms.get(tag, set())),
            "source": product.source,
            # The chosen product (by ``product_ref``); None where the type names none.
            "product": chosen.tag if chosen else None,
            "brand": chosen.brand if chosen else None,
            "model": chosen.model if chosen else None,
        })
    return sorted(rows, key=lambda row: (str(row["mark"]), str(row["type"])))


def lighting_controls(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per switched load: what it is, what switches it, and how.

    This is the authoritative statement of the switch legs — the E-2xx plans draw them as
    straight dashed lines rather than the arcs a hand-drafted set would use, so the plan
    shows *that* a leg exists and this table says exactly which.
    """
    types = luminaire_types(model.plan.library)
    device_types = _device_types(model)
    devices = electrical_devices(model)
    switches = {element.tag: element for storey in model.plan.storeys
                for element in model.plan.storey_elements(storey.tag)
                if _is_electrical_device(element)
                and element.kind.value == "switch"}

    loads: list[tuple[ElectricalDevice | ResolvedLightRun, str]] = [
        (element, "fixture") for element in _luminaires(model)
    ]
    loads.extend((run, "run") for run in model.light_runs)

    rows: list[dict[str, object]] = []
    for load, kind in loads:
        product = types.get(getattr(load, "type_ref", "") or "")
        names = tuple(getattr(load, "controlled_by", ()) or ())
        circuit = effective_lighting_circuit(load, devices)
        controls = []
        crossed = []
        for name in names:
            switch = switches.get(name)
            if switch is None:
                controls.append("(missing)")
                continue
            switch_type = device_types.get(switch.type_ref or "")
            controls.append(getattr(switch_type, "control", None) or "toggle")
            if circuit is not None and switch.circuit not in (None, circuit):
                crossed.append(name)
        rows.append({
            "tag": load.tag,
            "kind": kind,
            "mark": getattr(product, "type_mark", None) or "",
            "room": getattr(load, "room", None),
            "circuit": circuit,
            "psu": getattr(load, "psu_ref", None),
            "switches": list(names),
            "controls": controls,
            "ways": len(names),
            "integral_switch": bool(getattr(product, "integral_switch", False)),
            "cross_circuit": sorted(crossed),
        })
    return sorted(rows, key=lambda row: str(row["tag"]))


def light_run_takeoff(model: ResolvedModel) -> dict[str, object]:
    """Lineal feet of tape by type, plus every supply sized against what it drives.

    ``required_watts`` is the connected tape at the 125% continuous factor — the number the
    supply has to be bought above, not the number it draws.
    """
    types = _device_types(model)
    by_type: dict[str, _RunTypeTotals] = {}
    by_psu: dict[str, _SupplyTotals] = {}
    runs: list[dict[str, object]] = []

    for run in sorted(model.light_runs, key=lambda item: item.tag):
        product = types.get(run.type_ref)
        length_ft = run.length_m * _M_TO_FT
        watts = _run_watts(run, product)
        runs.append({
            "tag": run.tag, "type": run.type_ref,
            "mark": getattr(product, "type_mark", None) or "",
            "storey": run.storey, "room": run.room,
            "length_ft": round(length_ft, 1), "watts": round(watts, 1),
            "volts": getattr(product, "voltage", 120) if product is not None else 120,
            "psu": run.psu_ref, "circuit": run.circuit,
        })
        row = by_type.setdefault(run.type_ref, {
            "type": run.type_ref, "mark": getattr(product, "type_mark", None) or "",
            "runs": 0, "length_ft": 0.0, "watts": 0.0})
        row["runs"] = int(row["runs"]) + 1
        row["length_ft"] = float(row["length_ft"]) + length_ft
        row["watts"] = float(row["watts"]) + watts
    for psu, tag, kind, watts, length_ft in supplied_loads(model):
        supply = by_psu.setdefault(psu, {
            "psu": psu, "runs": [], "fixtures": [], "length_ft": 0.0, "watts": 0.0})
        supply["runs" if kind == "run" else "fixtures"].append(tag)
        supply["length_ft"] += length_ft
        supply["watts"] += watts

    devices = {element.tag: element for storey in model.plan.storeys
               for element in model.plan.storey_elements(storey.tag)
               if _is_electrical_device(element)}
    supplies = []
    for psu_tag in sorted(by_psu):
        supply = by_psu[psu_tag]
        device = devices.get(psu_tag)
        rating = rated_output_w(types.get(getattr(device, "type_ref", "") or ""))
        required = float(supply["watts"]) * PSU_SIZING_FACTOR
        supplies.append({
            "psu": psu_tag,
            "type": getattr(device, "type_ref", None),
            "runs": sorted(supply["runs"]),
            "fixtures": sorted(supply["fixtures"]),
            "length_ft": round(float(supply["length_ft"]), 1),
            "connected_watts": round(float(supply["watts"]), 1),
            "required_watts": round(required, 1),
            "rated_watts": rating,
            "adequate": None if rating is None else rating + 1e-6 >= required,
        })
    return {
        "runs": runs,
        "by_type": [{"type": row["type"], "mark": row["mark"], "runs": int(row["runs"]),
                     "length_ft": round(float(row["length_ft"]), 1),
                     "watts": round(float(row["watts"]), 1)}
                    for row in (by_type[key] for key in sorted(by_type))],
        "supplies": supplies,
        "total_length_ft": round(sum(float(row["length_ft"]) for row in by_type.values()), 1),
    }


def light_run_materials(model: ResolvedModel) -> list[dict[str, object]]:
    """Order-sheet lines for every LED run, from its tape and channel (decision #137).

    Per type: ``tape`` by the net lineal foot (``reels`` beside it where the strip states a
    reel), or one ``module_<n>in`` row per rigid-bar length; ``channel`` and ``lens`` by the
    foot of whole sticks cut per run (net feet where the stick is unread); ``end_cap`` two per
    open run, ``clip`` ``ceil(len / spacing) + 1`` per run, ``corner_connector`` one per
    interior vertex. A shadow-gap run's tape sits in the drywall trade's bead
    (``drywall_trims``), so it bills tape alone. The 24 V leads bill from the house's
    ``LedStandard`` (``lead_<awg>awg`` by the foot, ``tape_connector`` one per feed).
    """
    import math

    from typehaus.resolve.led_sections import led_channels

    types = _device_types(model)
    channels = led_channels(model.plan)
    totals: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}
    for run in model.light_runs:
        product = types.get(run.type_ref)
        strip = getattr(product, "strip", None)
        row = totals.setdefault(run.type_ref, {})
        counts[run.type_ref] = counts.get(run.type_ref, 0) + 1
        run_ft = run.length_m * _M_TO_FT

        def add(item: str, qty: float, row=row) -> None:
            row[item] = row.get(item, 0.0) + qty

        if run.modules_m:
            for size in run.modules_m:
                add(f"module_{round(size / 0.0254, 2):g}in", 1)
        elif not (strip is not None and strip.modules):
            add("tape", run_ft)
        for item in ("channel", "end_cap", "corner_connector"):
            add(item, 0)  # a zero row still visits its price row
        if run.profile != "surface":
            continue
        channel = channels.get(run.channel_ref or "")
        stick = channel.stick_length.meters * _M_TO_FT if channel and channel.stick_length else 0
        bought = math.ceil(run_ft / stick - 1e-6) * stick if stick else run_ft
        if not run.modules_m:
            add("channel", bought)
        if channel is not None and channel.lens_product_ref:
            add("lens", bought)
        if channel is not None and channel.clip_spacing:
            add("clip", math.ceil(run.length_m / channel.clip_spacing.meters - 1e-6) + 1)
        add("end_cap", 2)
        add("corner_connector", max(len(run.path) - 2, 0))
    for lead in getattr(model, "led_leads", ()):
        row = totals.setdefault(lead.type_ref, {})
        if lead.awg is not None:
            row[f"lead_{lead.awg}awg"] = row.get(f"lead_{lead.awg}awg", 0.0) + \
                lead.length_m * _M_TO_FT
        if lead.leg == "feed":
            row["tape_connector"] = row.get("tape_connector", 0.0) + 1

    rows: list[dict[str, object]] = []
    for tag in sorted(totals):
        product = types.get(tag)
        strip = getattr(product, "strip", None)
        mark = getattr(product, "type_mark", None) or ""
        for item in sorted(totals[tag], key=_item_order):
            qty = totals[tag][item]
            unit = "LF" if item in _LF_ITEMS or item.startswith("lead_") else "EA"
            row: dict[str, object] = {
                "type": tag, "mark": mark, "item": item, "unit": unit,
                "quantity": round(qty, 1) if unit == "LF" else int(qty),
                "runs": counts.get(tag, 0)}
            if item == "tape" and strip is not None and strip.reel_length:
                row["reels"] = math.ceil(qty / (strip.reel_length.meters * _M_TO_FT) - 1e-6)
            named = _part_name(model, channels.get(strip.channel_ref or "") if strip else None,
                               item)
            if named:
                row["name"] = named
            rows.append(row)
    return rows


def _part_name(model: ResolvedModel, channel, item: str) -> str | None:
    """The product a channel part is bought as, for the order line's label."""
    ref = {"channel": "product_ref", "lens": "lens_product_ref", "end_cap": "end_cap_ref",
           "clip": "clip_ref"}.get(item)
    product = model.plan.library.product(getattr(channel, ref, None) or "") if ref else None
    if product is None:
        return None
    return product.name or " ".join(part for part in (product.brand, product.model) if part)


_LF_ITEMS = ("tape", "channel", "lens")
_ORDER = ("tape", "module", "channel", "lens", "end_cap", "clip", "corner_connector", "lead",
          "tape_connector")


def _item_order(item: str) -> tuple[int, str]:
    head = item.split("_")[0] if item.startswith(("module_", "lead_")) else item
    return (_ORDER.index(head) if head in _ORDER else len(_ORDER)), item


def connected_lighting_va(model: ResolvedModel) -> dict[str, object]:
    """The real connected lighting load per circuit, against the 120.82 area allowance.

    A 24V run contributes nothing directly: its load is its supply's, and the supply is a
    device on a branch circuit like any other. Counting both would double the tape. A
    *line-voltage* run is the opposite case — it is the load on its circuit, and it is
    counted here, under ``runs`` rather than in the ``fixtures`` count: a run has lineal
    feet, not a unit to count.
    """
    types = _device_types(model)
    luminaire_tags = set(luminaire_types(model.plan.library))
    psu_tags = {run.psu_ref for run in model.light_runs if run.psu_ref}
    psu_tags.update(device.psu_ref for device in _luminaires(model) if device.psu_ref)

    by_circuit: dict[str, _CircuitTotals] = {}

    def _row(circuit: str) -> _CircuitTotals:
        return by_circuit.setdefault(circuit, {"circuit": circuit, "fixtures": 0, "runs": 0,
                                               "connected_va": 0.0})

    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not _is_electrical_device(element):
                continue
            if not (element.type_ref in luminaire_tags or element.tag in psu_tags):
                continue
            circuit = element.circuit
            if circuit is None:
                continue
            va = input_va(types.get(element.type_ref or "")) or 0.0
            row = _row(circuit)
            row["fixtures"] = int(row["fixtures"]) + 1
            row["connected_va"] = float(row["connected_va"]) + va

    for run in model.light_runs:
        if run.circuit is None or run.psu_ref is not None:
            continue
        row = _row(run.circuit)
        row["runs"] = int(row["runs"]) + 1
        row["connected_va"] = float(row["connected_va"]) + _run_watts(run, types.get(run.type_ref))

    conditioned_ft2 = nec_floor_area_ft2(model)
    total = sum(float(row["connected_va"]) for row in by_circuit.values())
    return {
        "per_circuit": [{"circuit": row["circuit"], "fixtures": int(row["fixtures"]),
                         "runs": int(row["runs"]),
                         "connected_va": round(float(row["connected_va"]), 1)}
                        for row in (by_circuit[key] for key in sorted(by_circuit))],
        "total_connected_va": round(total, 1),
        "conditioned_area_ft2": round(conditioned_ft2, 0),
        "allowance_va_per_ft2": GENERAL_LIGHTING_VA_PER_FT2,
        "allowance_va": round(GENERAL_LIGHTING_VA_PER_FT2 * conditioned_ft2, 0),
        "basis": (f"{NEC.EDITION} {NEC.OPTIONAL_GENERAL_LOADS} takes general lighting as an "
                  "area allowance and never reads a fixture; this is what is actually "
                  "connected, shown beside it."),
    }
