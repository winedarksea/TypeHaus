"""Backup microgrid arithmetic — how long the ESS carries the house, and at what.

One module, three consumers (the BOM, the E-601 sheet, the model_json electrical block),
same rule as ``takeoff/plumbing_calc.py``: the number printed on the sheet and the number
served to the viewer come from the same function, so they cannot drift.

Everything here is explicitly an **estimate**, and the estimate's honesty rests on one
rule: a backup circuit without an authored ``duty_cycle`` is reported as an unknown
contributor and never counted as zero. A silent zero would make the array look like it
carries a house it does not carry — the exact failure this calc exists to catch.

Three questions get answered:

1. **Peak** — can the inverter's continuous output cover the backup loads running at
   once, and can its surge cover the largest motor start?
2. **Autonomy** — how many hours the battery alone carries each tier, with no sun.
3. **The 48-hour cycle** — with strong sun every *other* day, does one solar day put back
   more than two days of load takes out? Asked twice, at a summer and a December yield.
4. **The darkness bridge** — does the battery alone carry the always-on tier through a
   dark day and the longest night after it?

All of it is battery-side: AC load over the inverter's efficiency plus its idle draw, both
read off the inverter type. Missing either is an unknown, never a free inverter.
"""

from __future__ import annotations

import math

from typehaus.model.enums import BackupTier
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.data import poe_watts_by_tag
from typehaus.takeoff.electrical import (
    _circuit_consumers,
    backup_equipment,
)
from typehaus.takeoff.electrical import (
    _connected_va as _va,
)

# Usable fraction of nameplate battery energy. LFP packs are commonly cycled to ~90% DoD;
# the remaining 10% is the reserve the BMS keeps back. Authored here rather than on the
# type because it is an operating choice (how hard the owner is willing to cycle), not a
# datasheet fact — a battery is not a different product because you cycle it shallower.
DEPTH_OF_DISCHARGE = 0.90

# Energy a strong day yields per kW of installed DC array, kWh/kW/day. Deliberately
# conservative: the Catlin array is split E/W off a N-S ridge at 4:12, so neither row ever
# sees a normal-incidence noon, and MN's strong-sun days in the season that matters for an
# outage are short and cold. PVWatts-class annual averages for MN run ~3.5 kWh/kW/day for
# a south-facing array; 3.0 is that number haircut for the E/W split. Estimate, not a
# production model — no shading, soiling, snow, or hourly curve is modeled.
STRONG_DAY_KWH_PER_KW = 3.0
# The same strong day in December: PVWatts-class MN December yield is ~1.5-2 kWh/kW/day
# south-facing, and a low-pitch E/W split loses more of it than of the summer figure. A
# winter outage is the one the house cares about, so it is reported beside the summer one.
WINTER_STRONG_DAY_KWH_PER_KW = 1.5

# Sun altitude at sunrise/sunset: refraction plus the solar radius (NOAA convention).
_HORIZON_ALTITUDE_DEG = -0.833
_SOLSTICE_DECLINATION_DEG = -23.44

# Motor-start multiple applied to the largest backup circuit (either tier) when checking
# the inverter's surge rating. 3x is the allowance for a soft-started inverter-driven motor
# (the Sapphire R32 on CKT-HP3). An across-the-line motor such as a sump pump starts at
# 5-7x and is NOT covered by it: one that is not also the largest circuit is ungraded.
MOTOR_START_MULTIPLE = 3.0

# Efficiency of the PoE switch's supply, for what a shed port saves at the outlet. 88% is the
# DOE Level VI floor for a basic-voltage external supply over 49 W (10 CFR 430.32(w)), the
# same basis CKT-HA's duty cycle grosses its PoE load up by. Cable loss on the shed ports is
# saved too and is not credited, so the shed errs light.
POE_SUPPLY_EFFICIENCY = 0.88

_HOURS_PER_DAY = 24.0


def _governed_va(model: ResolvedModel, circuit, va: float) -> float:
    """The most this circuit can draw during a backup event.

    ``Circuit.backup_va`` where authored — a smart appliance held in a low-power mode while
    the house is on battery (the water heater forced to Heat-Pump-Only), which is a BACKUP
    fact and lives on the circuit beside ``backup_tier``. This used to read a
    single-circuit ``LoadManagement`` instead, which conflated a backup reserve with a
    service-calculation credit; those are different claims needing different evidence (2026
    NEC 130.2 wants a listing for the second and nothing for the first).
    """
    if circuit.backup_va is not None:
        return min(va, float(circuit.backup_va))
    return va


def _poe_shed(circuit, poe_watts: dict[str, float | None]) -> tuple[float, list[str]]:
    """Outlet watts saved by ``Circuit.backup_shed_poe``, and the tags it could not credit.

    A tag that is not a data device, or states no ``poe_watts``, is listed and saves nothing:
    an unrated shed must not flatter the calc.
    """
    rated = [poe_watts.get(tag) for tag in circuit.backup_shed_poe]
    unrated = [tag for tag, watts in zip(circuit.backup_shed_poe, rated, strict=True)
               if not watts]
    saved = sum(float(watts) for watts in rated if watts) / POE_SUPPLY_EFFICIENCY
    return saved, unrated


def _tier_rows(model: ResolvedModel, tier: BackupTier) -> list[dict[str, object]]:
    consumers = _circuit_consumers(model)
    poe_watts = poe_watts_by_tag(model)
    rows: list[dict[str, object]] = []
    for circuit in model.plan.library.circuits:
        if circuit.backup_tier is not tier:
            continue
        va = _governed_va(model, circuit,
                          _va(model, circuit, consumers.get(circuit.tag, [])))
        duty = circuit.duty_cycle
        shed_w, unrated = _poe_shed(circuit, poe_watts)
        rows.append({
            "circuit": circuit.tag,
            "description": circuit.description,
            "connected_va": round(va, 0),
            "duty_cycle": duty,
            "shed_poe": list(circuit.backup_shed_poe),
            "shed_w": round(shed_w, 1),
            "shed_unrated": unrated,
            # Average draw over the event, after the shed. None — never 0.0 — when the duty
            # cycle is not authored, so a consumer cannot add it up without noticing.
            "average_w": (round(max(0.0, va * duty - shed_w), 1)
                          if duty is not None else None),
        })
    return rows


def _tier_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    known = [r for r in rows if r["average_w"] is not None]
    unknown = [str(r["circuit"]) for r in rows if r["average_w"] is None]
    average_w = sum(float(r["average_w"]) for r in known)  # type: ignore[arg-type]
    return {
        "circuits": rows,
        "connected_va": round(sum(float(r["connected_va"]) for r in rows), 0),
        "average_w": round(average_w, 1),
        "daily_kwh": round(average_w * _HOURS_PER_DAY / 1000.0, 2),
        "unknown_duty_cycle": unknown,
        # The average is a floor, not a total, whenever a circuit is missing its estimate.
        "complete": not unknown,
    }


def longest_night_hours(latitude_deg: float) -> float:
    """Sunset to sunrise at the winter solstice, from the site's latitude.

    ``cos H = (sin h0 - sin L sin d) / (cos L cos d)``; day = 2H/15. St Paul (44.98 N) is
    15.2 h. Clamped so a polar site reads 24 h, not a math error. ``abs`` because the
    longest night south of the equator is the June solstice, by symmetry the same number.
    """
    lat = math.radians(abs(latitude_deg))
    dec = math.radians(_SOLSTICE_DECLINATION_DEG)
    cos_h = ((math.sin(math.radians(_HORIZON_ALTITUDE_DEG)) - math.sin(lat) * math.sin(dec))
             / (math.cos(lat) * math.cos(dec)))
    day_h = 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, cos_h)))) / 15.0
    return _HOURS_PER_DAY - day_h


def _storage(placed, types) -> tuple[list, float, list]:
    rows, nameplate_kwh, undeclared = [], 0.0, []
    for element in sorted(placed["batteries"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kwh = getattr(product, "storage_kwh", None) if product is not None else None
        if kwh is None:
            undeclared.append(element.tag)
        else:
            nameplate_kwh += float(kwh)
        rows.append({"equipment": element.tag, "type": element.type_ref or "",
                     "storage_kwh": kwh})
    return rows, nameplate_kwh, undeclared


def _conversion(placed, types) -> dict[str, object]:
    """Inverter ratings, summed where they stack. None stays None so "not declared"
    survives the sum; the idle draws add, and the worst efficiency governs."""
    rows = []
    totals: dict[str, float | None] = {"kw_continuous": None, "kw_surge": None,
                                       "pv_input_kw": None, "idle_w": None}
    efficiency = None
    unknown: list[str] = []
    for element in sorted(placed["inverters"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        row = {"equipment": element.tag, "type": element.type_ref or ""}
        for key, field in (("kw_continuous", "inverter_kw_continuous"),
                           ("kw_surge", "inverter_kw_surge"), ("pv_input_kw", "pv_input_kw"),
                           ("idle_w", "inverter_idle_w")):
            value = getattr(product, field, None) if product else None
            row[key] = value
            if value is not None:
                totals[key] = (totals[key] or 0.0) + float(value)
        eff = getattr(product, "inverter_efficiency", None) if product else None
        row["efficiency"] = eff
        if eff is not None:
            efficiency = eff if efficiency is None else min(efficiency, float(eff))
        unknown += [f"{element.tag}.{name}" for name in ("idle_w", "efficiency")
                    if row[name] is None]
        rows.append(row)
    return {"rows": rows, **totals, "efficiency": efficiency, "unknown": unknown}


def _battery_w(ac_w: float, conversion: dict) -> float:
    """What the battery supplies for ``ac_w`` of load. An undeclared idle or efficiency
    counts as free here, which is why it also makes the summary incomplete."""
    efficiency = conversion["efficiency"] or 1.0
    return ac_w / efficiency + float(conversion["idle_w"] or 0.0)


def _cycle(array_kw: float, kwh_per_kw: float, usable_kwh: float,
           always_w: float, both_w: float) -> dict[str, object]:
    """One strong solar day against 48 h of battery-side load. A system with no usable
    storage sustains nothing, however big the array: the dark day has nowhere to come from."""
    solar_day_kwh = array_kw * kwh_per_kw
    always_2day = always_w * 2 * _HOURS_PER_DAY / 1000.0
    both_2day = both_w * 2 * _HOURS_PER_DAY / 1000.0
    stores = usable_kwh > 0.0
    return {
        "array_kw": array_kw,
        "strong_day_kwh_per_kw": kwh_per_kw,
        "solar_day_kwh": round(solar_day_kwh, 2),
        "two_day_load_kwh_all_tiers": round(both_2day, 2),
        "two_day_load_kwh_always_on": round(always_2day, 2),
        "net_kwh_all_tiers": round(solar_day_kwh - both_2day, 2),
        "net_kwh_always_on": round(solar_day_kwh - always_2day, 2),
        "sustains_all_tiers": stores and solar_day_kwh >= both_2day,
        "sustains_always_on": stores and solar_day_kwh >= always_2day,
        "basis": ("one strong solar day per 48h against 48h of battery-side tier load; the "
                  "battery buffers the dark day"),
    }


def backup_runtime_summary(
    model: ResolvedModel,
    *,
    depth_of_discharge: float = DEPTH_OF_DISCHARGE,
    strong_day_kwh_per_kw: float = STRONG_DAY_KWH_PER_KW,
    winter_strong_day_kwh_per_kw: float = WINTER_STRONG_DAY_KWH_PER_KW,
) -> dict[str, object]:
    """Peak, autonomy, the two 48 h cycles and the darkness bridge for the backup microgrid.

    Returns ``{"modeled": False}`` when no ESS is placed and nothing is tiered, so every
    consumer can skip the block rather than print zeros.
    """
    placed = backup_equipment(model)
    tiers = {
        "always_on": _tier_summary(_tier_rows(model, BackupTier.ALWAYS_ON)),
        "shed": _tier_summary(_tier_rows(model, BackupTier.SHED)),
    }
    if not (placed["batteries"] or placed["inverters"]
            or tiers["always_on"]["circuits"] or tiers["shed"]["circuits"]):
        return {"modeled": False}

    types = {t.tag: t for t in model.plan.library.equipment_types}
    battery_rows, nameplate_kwh, undeclared_batteries = _storage(placed, types)
    usable_kwh = nameplate_kwh * depth_of_discharge
    conversion = _conversion(placed, types)
    inverter_kw, surge_kw = conversion["kw_continuous"], conversion["kw_surge"]

    # --- Peak: everything on the microgrid at once -------------------------------------
    always_va = float(tiers["always_on"]["connected_va"])
    both_va = always_va + float(tiers["shed"]["connected_va"])
    # Every backup circuit, not only the shed tier: the sump rides always-on and starts too.
    largest_va = max([float(r["connected_va"]) for tier in tiers.values()
                      for r in tier["circuits"]] or [0.0])
    peak: dict[str, object] = {
        "simultaneous_va": round(both_va, 0),
        "always_on_va": tiers["always_on"]["connected_va"],
        "inverter_kw_continuous": inverter_kw,
        "inverter_kw_surge": surge_kw,
        "largest_motor_start_va": round(largest_va * MOTOR_START_MULTIPLE, 0),
        "motor_start_multiple": MOTOR_START_MULTIPLE,
        "within_continuous": None if inverter_kw is None else both_va <= inverter_kw * 1000.0,
        "always_on_within_continuous": (None if inverter_kw is None
                                        else always_va <= inverter_kw * 1000.0),
        "within_surge": (None if surge_kw is None
                         else largest_va * MOTOR_START_MULTIPLE <= surge_kw * 1000.0),
    }

    # --- Battery-side draw: AC load through the inverter, plus its idle ----------------
    always_w = _battery_w(float(tiers["always_on"]["average_w"]), conversion)
    both_w = _battery_w(float(tiers["always_on"]["average_w"])
                        + float(tiers["shed"]["average_w"]), conversion)

    def _hours(watts: float) -> float | None:
        if usable_kwh <= 0.0 or watts <= 0.0:
            return None
        return round(usable_kwh * 1000.0 / watts, 1)

    autonomy = {
        "usable_kwh": round(usable_kwh, 2),
        "nameplate_kwh": round(nameplate_kwh, 2),
        "depth_of_discharge": depth_of_discharge,
        "battery_w_always_on": round(always_w, 1),
        "battery_w_all_tiers": round(both_w, 1),
        "inverter_idle_w": conversion["idle_w"],
        "inverter_efficiency": conversion["efficiency"],
        "hours_all_tiers": _hours(both_w),
        "hours_always_on_only": _hours(always_w),
        "basis": ("battery only, no solar; tier draw = connected VA x authored duty cycle, "
                  "less PoE ports shed, over inverter efficiency, plus inverter idle"),
    }

    array_kw = round(sum(panel.watts for panel in model.solar_panels) / 1000.0, 3)
    cycle = _cycle(array_kw, strong_day_kwh_per_kw, usable_kwh, always_w, both_w)
    winter = _cycle(array_kw, winter_strong_day_kwh_per_kw, usable_kwh, always_w, both_w)

    night_h = longest_night_hours(model.plan.project.site.lat)
    bridge_h = _HOURS_PER_DAY + night_h
    required_kwh = always_w * bridge_h / 1000.0
    bridge = {
        "longest_night_h": round(night_h, 2),
        "bridge_hours": round(bridge_h, 2),
        "required_kwh": round(required_kwh, 2),
        "usable_kwh": round(usable_kwh, 2),
        "bridges": usable_kwh > 0.0 and usable_kwh >= required_kwh,
        "basis": ("battery alone carries the always-on tier from one evening's last sun "
                  "through a dark day and the longest night after it"),
    }

    complete = (bool(tiers["always_on"]["complete"]) and bool(tiers["shed"]["complete"])
                and not undeclared_batteries and inverter_kw is not None
                and not conversion["unknown"])
    return {
        "modeled": True,
        "estimate": True,
        "complete": complete,
        "batteries": battery_rows,
        "batteries_without_capacity": undeclared_batteries,
        "inverters": conversion["rows"],
        "inverter_unknown": conversion["unknown"],
        "pv_input_kw": conversion["pv_input_kw"],
        "tiers": tiers,
        "peak": peak,
        "autonomy": autonomy,
        "cycle_48h": cycle,
        "cycle_48h_winter": winter,
        "darkness_bridge": bridge,
        "verdict": _verdict(complete, peak, autonomy, cycle, winter, bridge),
    }


def _verdict(complete: bool, peak: dict, autonomy: dict, cycle: dict, winter: dict,
             bridge: dict) -> str:
    """One sentence a plan reader can act on: keep this system, or add to it."""
    if not complete:
        return ("UNKNOWN — the model is missing a duty cycle, a battery capacity, or an "
                "inverter rating, idle or efficiency; the numbers below are a floor, not a "
                "total")
    if autonomy["usable_kwh"] <= 0.0:
        return ("no usable storage — the backup port carries nothing through a night, so "
                "nothing here is sustained however large the array")
    problems = []
    if peak["within_continuous"] is False:
        problems.append(
            f"all backup loads at once ({peak['simultaneous_va']:,.0f} VA) exceed the "
            f"inverter's {peak['inverter_kw_continuous']:g} kW continuous output — the "
            "shed tier must not run with the always-on tier")
    if peak["within_surge"] is False:
        problems.append("the largest backup motor start exceeds the inverter surge")
    if not cycle["sustains_always_on"]:
        # A bigger battery cannot fix a cycle that loses energy every 48 h; it can only fix
        # the bridge, so "not battery" is said only when the bridge already holds.
        remedy = "add array, not battery" if bridge["bridges"] else "add array"
        problems.append(
            f"one strong summer day ({cycle['solar_day_kwh']:g} kWh) does not cover 48h of "
            f"even the always-on tier ({cycle['two_day_load_kwh_always_on']:g} kWh) — "
            f"{remedy}")
    elif not cycle["sustains_all_tiers"]:
        problems.append(
            "one strong solar day covers the always-on tier over 48h but not both tiers "
            "together — which is what the shed tier is for")
    if cycle["sustains_always_on"] and not winter["sustains_always_on"]:
        problems.append(
            f"a strong December day ({winter['solar_day_kwh']:g} kWh) does not cover 48h of "
            f"the always-on tier ({winter['two_day_load_kwh_always_on']:g} kWh)")
    if not bridge["bridges"]:
        problems.append(
            f"{bridge['usable_kwh']:g} kWh usable does not bridge a dark day and the "
            f"{bridge['longest_night_h']:.1f} h longest night on the always-on tier "
            f"(needs {bridge['required_kwh']:g} kWh)")
    if not problems:
        return (f"sufficient — {autonomy['usable_kwh']:g} kWh usable carries the always-on "
                f"tier {autonomy['hours_always_on_only']} h unaided, and one strong solar "
                f"day nets {cycle['net_kwh_all_tiers']:+g} kWh over 48h of both tiers")
    return "; ".join(problems)
