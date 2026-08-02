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
3. **The 48-hour cycle** — the TODO's actual question: with strong sun every *other* day,
   does one solar day put back more than two days of load takes out? If it does the
   system rides indefinitely; if it does not, the battery is a countdown, not a buffer.
"""

from __future__ import annotations

from typehaus.model.enums import BackupTier
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.electrical import (
    _circuit_consumers,
    _connected_va as _va,
    backup_equipment,
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
# production model — no shading, soiling, snow, or hourly curve is modeled. (2026-08-02)
STRONG_DAY_KWH_PER_KW = 3.0

# Motor-start multiple applied to the largest single SHED-tier motor load when checking
# the inverter's surge rating. A soft-started VFD compressor (the Sapphire R32 on CKT-HP3)
# is the reason the surge column is small rather than the 5-7x a PSC compressor would
# demand; 3x is the conservative allowance for a soft-started inverter-driven motor.
MOTOR_START_MULTIPLE = 3.0

_HOURS_PER_DAY = 24.0


def _tier_rows(model: ResolvedModel, tier: BackupTier) -> list[dict[str, object]]:
    consumers = _circuit_consumers(model)
    rows: list[dict[str, object]] = []
    for circuit in model.plan.library.circuits:
        if circuit.backup_tier is not tier:
            continue
        va = _va(model, circuit, consumers.get(circuit.tag, []))
        duty = circuit.duty_cycle
        rows.append({
            "circuit": circuit.tag,
            "description": circuit.description,
            "connected_va": round(va, 0),
            "duty_cycle": duty,
            # Average draw over the event. None — never 0.0 — when the duty cycle is not
            # authored, so a consumer cannot add it up without noticing.
            "average_w": round(va * duty, 1) if duty is not None else None,
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


def backup_runtime_summary(
    model: ResolvedModel,
    *,
    depth_of_discharge: float = DEPTH_OF_DISCHARGE,
    strong_day_kwh_per_kw: float = STRONG_DAY_KWH_PER_KW,
) -> dict[str, object]:
    """Peak, autonomy, and the every-other-day-sun verdict for the backup microgrid.

    Returns an empty-ish dict with ``modeled: False`` when no ESS is placed and nothing is
    tiered, so every consumer can skip the block rather than print zeros.
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

    # --- Storage and conversion, from the placed equipment -----------------------------
    battery_rows = []
    nameplate_kwh = 0.0
    undeclared_batteries = []
    for element in sorted(placed["batteries"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kwh = getattr(product, "storage_kwh", None) if product is not None else None
        if kwh is None:
            undeclared_batteries.append(element.tag)
        else:
            nameplate_kwh += float(kwh)
        battery_rows.append({"equipment": element.tag, "type": element.type_ref or "",
                             "storage_kwh": kwh})
    usable_kwh = nameplate_kwh * depth_of_discharge

    inverter_kw = None
    surge_kw = None
    pv_input_kw = None
    inverter_rows = []
    for element in sorted(placed["inverters"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        cont = getattr(product, "inverter_kw_continuous", None) if product else None
        surge = getattr(product, "inverter_kw_surge", None) if product else None
        pv_in = getattr(product, "pv_input_kw", None) if product else None
        inverter_rows.append({"equipment": element.tag, "type": element.type_ref or "",
                              "kw_continuous": cont, "kw_surge": surge,
                              "pv_input_kw": pv_in})
        # Multiple inverters stack; None stays None so "not declared" survives the sum.
        if cont is not None:
            inverter_kw = (inverter_kw or 0.0) + float(cont)
        if surge is not None:
            surge_kw = (surge_kw or 0.0) + float(surge)
        if pv_in is not None:
            pv_input_kw = (pv_input_kw or 0.0) + float(pv_in)

    # --- Peak: everything on the microgrid at once -------------------------------------
    both_va = float(tiers["always_on"]["connected_va"]) + float(tiers["shed"]["connected_va"])
    largest_shed_va = max(
        [float(r["connected_va"]) for r in tiers["shed"]["circuits"]] or [0.0])
    peak: dict[str, object] = {
        "simultaneous_va": round(both_va, 0),
        "always_on_va": tiers["always_on"]["connected_va"],
        "inverter_kw_continuous": inverter_kw,
        "inverter_kw_surge": surge_kw,
        "largest_motor_start_va": round(largest_shed_va * MOTOR_START_MULTIPLE, 0),
        "motor_start_multiple": MOTOR_START_MULTIPLE,
    }
    if inverter_kw is None:
        peak["within_continuous"] = None
        peak["always_on_within_continuous"] = None
    else:
        peak["within_continuous"] = both_va <= inverter_kw * 1000.0
        peak["always_on_within_continuous"] = (
            float(tiers["always_on"]["connected_va"]) <= inverter_kw * 1000.0)
    peak["within_surge"] = (None if surge_kw is None
                            else largest_shed_va * MOTOR_START_MULTIPLE <= surge_kw * 1000.0)

    # --- Autonomy: battery alone, no sun -----------------------------------------------
    both_w = float(tiers["always_on"]["average_w"]) + float(tiers["shed"]["average_w"])
    always_w = float(tiers["always_on"]["average_w"])

    def _hours(watts: float) -> float | None:
        if usable_kwh <= 0.0 or watts <= 0.0:
            return None
        return round(usable_kwh * 1000.0 / watts, 1)

    autonomy = {
        "usable_kwh": round(usable_kwh, 2),
        "nameplate_kwh": round(nameplate_kwh, 2),
        "depth_of_discharge": depth_of_discharge,
        "hours_all_tiers": _hours(both_w),
        "hours_always_on_only": _hours(always_w),
        "basis": ("battery only, no solar; tier average draw = connected VA x authored "
                  "duty cycle"),
    }

    # --- The 48-hour cycle: strong sun every other day ---------------------------------
    array_kw = round(sum(panel.watts for panel in model.solar_panels) / 1000.0, 3)
    solar_day_kwh = array_kw * strong_day_kwh_per_kw
    always_2day = always_w * 2 * _HOURS_PER_DAY / 1000.0
    both_2day = both_w * 2 * _HOURS_PER_DAY / 1000.0
    cycle = {
        "array_kw": array_kw,
        "strong_day_kwh_per_kw": strong_day_kwh_per_kw,
        "solar_day_kwh": round(solar_day_kwh, 2),
        "two_day_load_kwh_all_tiers": round(both_2day, 2),
        "two_day_load_kwh_always_on": round(always_2day, 2),
        "net_kwh_all_tiers": round(solar_day_kwh - both_2day, 2),
        "net_kwh_always_on": round(solar_day_kwh - always_2day, 2),
        "sustains_all_tiers": solar_day_kwh >= both_2day,
        "sustains_always_on": solar_day_kwh >= always_2day,
        "basis": ("one strong solar day per 48h against 48h of tier load; the battery "
                  "buffers the dark day"),
    }

    complete = (bool(tiers["always_on"]["complete"]) and bool(tiers["shed"]["complete"])
                and not undeclared_batteries and inverter_kw is not None)
    return {
        "modeled": True,
        "estimate": True,
        "complete": complete,
        "batteries": battery_rows,
        "batteries_without_capacity": undeclared_batteries,
        "inverters": inverter_rows,
        "pv_input_kw": pv_input_kw,
        "tiers": tiers,
        "peak": peak,
        "autonomy": autonomy,
        "cycle_48h": cycle,
        "verdict": _verdict(complete, peak, autonomy, cycle),
    }


def _verdict(complete: bool, peak: dict, autonomy: dict, cycle: dict) -> str:
    """One sentence a plan reader can act on: keep this system, or add to it."""
    if not complete:
        return ("UNKNOWN — the model is missing a duty cycle, a battery capacity, or an "
                "inverter rating; the numbers below are a floor, not a total")
    problems = []
    if peak["within_continuous"] is False:
        problems.append(
            f"all backup loads at once ({peak['simultaneous_va']:,.0f} VA) exceed the "
            f"inverter's {peak['inverter_kw_continuous']:g} kW continuous output — the "
            "shed tier must not run with the always-on tier")
    if peak["within_surge"] is False:
        problems.append("the largest shed-tier motor start exceeds the inverter surge")
    if not cycle["sustains_always_on"]:
        problems.append(
            f"one strong solar day ({cycle['solar_day_kwh']:g} kWh) does not cover 48h of "
            f"even the always-on tier ({cycle['two_day_load_kwh_always_on']:g} kWh) — add "
            "array, not battery")
    elif not cycle["sustains_all_tiers"]:
        problems.append(
            "one strong solar day covers the always-on tier over 48h but not both tiers "
            "together — which is what the shed tier is for")
    if not problems:
        return (f"sufficient — {autonomy['usable_kwh']:g} kWh usable carries the always-on "
                f"tier {autonomy['hours_always_on_only']} h unaided, and one strong solar "
                f"day nets {cycle['net_kwh_all_tiers']:+g} kWh over 48h of both tiers")
    return "; ".join(problems)
