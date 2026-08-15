"""Lighting take-offs: the luminaire schedule, its controls, the runs, and the real load.

Everything here is a projection of the authored fixtures and their ``LuminaireType``s. No
row is hand-summed and no wattage is invented — a fixture whose type states no lumens
reports ``None``, because a schedule that fills a blank with a plausible number is worse
than one that admits the gap.

The load section exists to answer a question NEC 220.82 deliberately does not. The service
calculation takes lighting as a 3 VA/ft2 area allowance and never looks at a fixture, which
is code-correct and tells a designer nothing about whether an all-LED house is anywhere
near that allowance. So the connected total is reported *beside* the allowance rather than
replacing it (→ takeoff/electrical.service_load_summary, which is unchanged).
"""

from __future__ import annotations

from typehaus.model.electrical import luminaire_types
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123
_M2_TO_FT2 = 10.7639104167

# Mirrors ``takeoff/electrical.GENERAL_LIGHTING_VA_PER_FT2``. Restated rather than imported
# so this module can be read on its own; the parity is pinned by the takeoff test.
GENERAL_LIGHTING_VA_PER_FT2 = 3.0

# The continuous-load factor a 24V driver is sized by (NEC 210.19(A)(1) basis), matching
# ``checks/mep/lighting.PSU_SIZING_FACTOR``.
PSU_SIZING_FACTOR = 1.25


def _device_types(model: ResolvedModel) -> dict:
    return {product.tag: product for product in model.plan.library.electrical_device_types}


def _luminaires(model: ResolvedModel) -> list:
    return [element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"
            and element.kind.value == "light"]


def _mount_label(element: object) -> str:
    mount = getattr(element, "mount", None)
    if mount is None:
        return "floor"
    kind = mount.kind.value
    if kind == "ceiling" and getattr(mount, "recessed_into_host_surface", False):
        return "recessed ceiling"
    if kind == "ceiling" and mount.drop is not None:
        return "suspended ceiling"
    return kind


def _rating_label(product: object) -> str:
    if product.wet_rated:
        return "wet"
    if product.damp_rated:
        return "damp"
    return "dry"


def luminaire_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per luminaire *type* that is actually installed, keyed by schedule mark.

    Rows are ordered by mark, which is the order the sheet prints and the order a reader
    scans. ``count`` counts point fixtures; a linear type installed as runs reports its
    lineal feet instead, because a cove has no unit to count.
    """
    types = luminaire_types(model.plan.library)
    counts: dict[str, int] = {}
    rooms: dict[str, set] = {}
    for element in _luminaires(model):
        if element.type_ref not in types:
            continue
        counts[element.type_ref] = counts.get(element.type_ref, 0) + 1
        rooms.setdefault(element.type_ref, set()).add(element.room or "(unassigned)")
    run_feet: dict[str, float] = {}
    for run in model.light_runs:
        run_feet[run.type_ref] = run_feet.get(run.type_ref, 0.0) + run.length_m * _M_TO_FT
        rooms.setdefault(run.type_ref, set()).add(run.room or "(unassigned)")

    mount_by_type: dict[str, set] = {}
    for element in _luminaires(model):
        if element.type_ref in types:
            mount_by_type.setdefault(element.type_ref, set()).add(_mount_label(element))

    rows: list[dict[str, object]] = []
    for tag in set(counts) | set(run_feet):
        product = types[tag]
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
            "cri": product.cri,
            "volts": product.voltage,
            "mount": ", ".join(sorted(mount_by_type.get(tag, set()))) or "run",
            "dimming": "dimmable" if product.dimmable else "switched",
            "rating": _rating_label(product),
            "count": counts.get(tag, 0),
            "length_ft": round(run_feet[tag], 1) if tag in run_feet else None,
            "rooms": sorted(rooms.get(tag, set())),
            "source": product.source,
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
    switches = {element.tag: element for storey in model.plan.storeys
                for element in model.plan.storey_elements(storey.tag)
                if element.element_kind == "ElectricalDevice"
                and element.kind.value == "switch"}

    loads: list[tuple[object, str]] = [(element, "fixture") for element in _luminaires(model)]
    loads.extend((run, "run") for run in model.light_runs)

    rows: list[dict[str, object]] = []
    for load, kind in loads:
        product = types.get(getattr(load, "type_ref", "") or "")
        names = tuple(getattr(load, "controlled_by", ()) or ())
        circuit = getattr(load, "circuit", None)
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
    by_type: dict[str, dict[str, object]] = {}
    by_psu: dict[str, dict[str, object]] = {}
    runs: list[dict[str, object]] = []

    for run in sorted(model.light_runs, key=lambda item: item.tag):
        product = types.get(run.type_ref)
        watts_per_ft = getattr(product, "watts_per_ft", None) or 0.0
        length_ft = run.length_m * _M_TO_FT
        watts = watts_per_ft * length_ft
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
        if run.psu_ref is None:
            continue
        supply = by_psu.setdefault(run.psu_ref, {
            "psu": run.psu_ref, "runs": [], "length_ft": 0.0, "watts": 0.0})
        supply["runs"].append(run.tag)  # type: ignore[union-attr]
        supply["length_ft"] = float(supply["length_ft"]) + length_ft
        supply["watts"] = float(supply["watts"]) + watts

    devices = {element.tag: element for storey in model.plan.storeys
               for element in model.plan.storey_elements(storey.tag)
               if element.element_kind == "ElectricalDevice"}
    supplies = []
    for psu_tag in sorted(by_psu):
        supply = by_psu[psu_tag]
        device = devices.get(psu_tag)
        rating = getattr(types.get(getattr(device, "type_ref", "") or ""), "load_va", None)
        required = float(supply["watts"]) * PSU_SIZING_FACTOR
        supplies.append({
            "psu": psu_tag,
            "type": getattr(device, "type_ref", None),
            "runs": sorted(supply["runs"]),  # type: ignore[arg-type]
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
    """Real order-sheet lines for every cove/LED run — channel stock and tape by the lineal
    foot, end caps and corner connectors by the count — where ``light_run_takeoff`` bills one
    blended length against the type.

    A run's channel and tape are the same length (the tape rides the channel end to end); a
    run always takes two end caps, one per open end; and it takes one corner connector per
    interior path vertex, the fitting a straight length of stock cannot become on its own.
    """
    types = _device_types(model)
    by_type: dict[str, dict[str, object]] = {}
    for run in model.light_runs:
        product = types.get(run.type_ref)
        row = by_type.setdefault(run.type_ref, {
            "type": run.type_ref, "mark": getattr(product, "type_mark", None) or "",
            "runs": 0, "length_ft": 0.0, "end_caps": 0, "corner_connectors": 0})
        row["runs"] = int(row["runs"]) + 1
        row["length_ft"] = float(row["length_ft"]) + run.length_m * _M_TO_FT
        row["end_caps"] = int(row["end_caps"]) + 2
        row["corner_connectors"] = int(row["corner_connectors"]) + max(len(run.path) - 2, 0)

    rows: list[dict[str, object]] = []
    for tag in sorted(by_type):
        row = by_type[tag]
        length_ft = round(float(row["length_ft"]), 1)
        for item, unit, quantity in (
            ("channel", "LF", length_ft),
            ("tape", "LF", length_ft),
            ("end_cap", "EA", int(row["end_caps"])),
            ("corner_connector", "EA", int(row["corner_connectors"])),
        ):
            rows.append({"type": tag, "mark": row["mark"], "item": item, "unit": unit,
                         "quantity": quantity, "runs": int(row["runs"])})
    return rows


def connected_lighting_va(model: ResolvedModel) -> dict[str, object]:
    """The real connected lighting load per circuit, against the 220.82 area allowance.

    A 24V run contributes nothing directly: its load is its supply's, and the supply is a
    device on a branch circuit like any other. Counting both would double the tape.
    """
    types = _device_types(model)
    luminaire_tags = set(luminaire_types(model.plan.library))
    psu_tags = {run.psu_ref for run in model.light_runs if run.psu_ref}

    by_circuit: dict[str, dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "ElectricalDevice":
                continue
            if not (element.type_ref in luminaire_tags or element.tag in psu_tags):
                continue
            circuit = element.circuit
            if circuit is None:
                continue
            va = getattr(types.get(element.type_ref or ""), "load_va", None) or 0.0
            row = by_circuit.setdefault(circuit, {"circuit": circuit, "fixtures": 0,
                                                  "connected_va": 0.0})
            row["fixtures"] = int(row["fixtures"]) + 1
            row["connected_va"] = float(row["connected_va"]) + va

    conditioned_ft2 = sum(room.area_m2 for room in model.rooms if room.conditioned) * _M2_TO_FT2
    total = sum(float(row["connected_va"]) for row in by_circuit.values())
    return {
        "per_circuit": [{"circuit": row["circuit"], "fixtures": int(row["fixtures"]),
                         "connected_va": round(float(row["connected_va"]), 1)}
                        for row in (by_circuit[key] for key in sorted(by_circuit))],
        "total_connected_va": round(total, 1),
        "conditioned_area_ft2": round(conditioned_ft2, 0),
        "allowance_va_per_ft2": GENERAL_LIGHTING_VA_PER_FT2,
        "allowance_va": round(GENERAL_LIGHTING_VA_PER_FT2 * conditioned_ft2, 0),
        "basis": ("NEC 220.82 takes general lighting as an area allowance and never reads a "
                  "fixture; this is what is actually connected, shown beside it."),
    }
