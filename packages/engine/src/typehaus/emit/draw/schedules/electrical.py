"""The E-6xx schedule pages: panel and service load, luminaires and controls, low-voltage.

These are the sheets the E-1xx/E-2xx plans are unreadable without — the plans carry marks,
and a mark only becomes a product here.
"""

from __future__ import annotations

import textwrap

from typehaus.emit.draw.schedules.tables import _add_table, _number
from typehaus.emit.draw.sheet_writer import PORTRAIT_LEDGER, schedule_sheet, section
from typehaus.resolve.model import ResolvedModel

#: Schedule pages lay out above figure fraction 0.11, the title strip's top on every paper
#: (``title_block.title_height``). E-601's backup table once sat at 0.095, under the block.
_CONTENT_FLOOR = 0.11
#: E-601's lower half: two columns under the panel schedule, each block's top fixed.
_LEFT_X, _LEFT_W, _RIGHT_X, _RIGHT_W = 0.04, 0.54, 0.62, 0.34
_LOWER_TOP = 0.43


def _hours_label(hours: float | None) -> str:
    """An unknown autonomy prints as unknown — never as "0.0 h", which reads as a fact."""
    return "not computable (no storage or no authored draw)" if hours is None \
        else f"{hours:.1f} h"


def _write_panel_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """The panel schedule + NEC 220.82-style load summary + backup component list, all
    derived from Library.circuits (→ takeoff.electrical — nothing here is hand-summed)."""

    from typehaus.takeoff import (
        backup_component_rows,
        backup_runtime_summary,
        panel_schedule,
        service_load_summary,
    )
    with schedule_sheet(pdf, model, number, name) as fig:
        schedule = panel_schedule(model)
        section(fig, 0.04, 0.90, "PANEL SCHEDULE")
        # The backup column names the tier, not just the fact: a reader has to be able to tell
        # the circuits that ride through an outage from the ones a relay drops.
        _TIER_LABEL = {"always_on": "BKUP-ON", "surplus": "BKUP-SURP"}
        schedule_rows = [
            (row["circuit"], row["description"], f"{row['breaker_amps']}A/{row['poles']}p",
             f"{row['volts']}V", row["nema"] or "—", row["panel"],
             ("GFCI " if row["gfci"] else "")
             + ("AFCI " if row["afci"] else "")
             + _TIER_LABEL.get(str(row["backup_tier"]), "")
             + ("SOURCE" if row["source"] else "") or "—",
             f"{row['connected_va']:,.0f}")
            for row in schedule
        ]
        _add_table(fig, schedule_rows,
                   ("Circuit", "Description", "Breaker", "Volts", "NEMA", "Panel", "Prot.",
                    "VA"),
                   bbox=(0.04, 0.46, 0.92, 0.42), truncate=(1,))

        load = service_load_summary(model)
        section(fig, _LEFT_X, _LOWER_TOP, "SERVICE LOAD — " + str(load["method"]).upper())
        load_rows = [
            ("Conditioned floor area", f"{load['floor_area_ft2']:,.0f} ft2"),
            ("General lighting + small appliance/laundry",
             f"{load['general_lighting_va']:,.0f} VA"),
            ("Fixed appliances", f"{load['fixed_appliance_va']:,.0f} VA"),
            ("Heating/cooling at 100%", f"{load['hvac_va']:,.0f} VA"),
            ("EV charging (continuous)", f"{load['ev_va']:,.0f} VA"),
            ("DEMAND", f"{load['demand_va']:,.0f} VA = {load['demand_amps']:.1f} A"),
            ("Service / panel rating", f"{load['service_amps']}A service, "
                                       f"{load['panel_rating_amps']}A panel — "
                                       + ("OK" if load["within_service"] else "OVER")),
        ]
        # One row per panel stating a main: with the load split across two mains the
        # service total no longer says whether either feeder fits.
        load_rows.extend(
            (f"{row['panel']} feeder (estimate)",
             f"{row['demand_amps']:.1f} A of {row['main_amps']:.0f} A main")
            for row in _panel_feeder_rows(model))
        _add_table(fig, load_rows, ("Line", "Value"), bbox=(_LEFT_X, 0.29, _LEFT_W, 0.13))

        # Under the service load, down to the content floor: ``_add_table`` compresses or
        # splits a long list inside its box, so no row count reaches the title block.
        backup = backup_component_rows(model)
        if backup:
            section(fig, _LEFT_X, 0.265, "BACKUP MICROGRID COMPONENTS")
            backup_rows = [(row["component"], f"{row['count']}", row["basis"])
                           for row in backup]
            _add_table(fig, backup_rows, ("Component", "Qty", "Basis"),
                       bbox=(_LEFT_X, _CONTENT_FLOOR, _LEFT_W, 0.255 - _CONTENT_FLOOR),
                       truncate=(2,))

        # The runtime estimate rides beside the component list and is labeled an ESTIMATE on
        # the sheet, because that is exactly what it is (→ takeoff/backup_calc.py).
        runtime = backup_runtime_summary(model)
        if runtime.get("modeled"):
            autonomy = runtime["autonomy"]
            summer, winter = runtime["cycle_48h"], runtime["cycle_48h_winter"]
            bridge = runtime["darkness_bridge"]
            peak = runtime["peak"]
            # The right column, beside the service load and the component list.
            section(fig, _RIGHT_X, _LOWER_TOP, "BACKUP RUNTIME — ESTIMATE, NOT A GUARANTEE")
            idle, efficiency = autonomy["inverter_idle_w"], autonomy["inverter_efficiency"]
            runtime_rows = [
                ("Usable storage",
                 f"{autonomy['usable_kwh']:g} kWh of {autonomy['nameplate_kwh']:g} "
                 f"({autonomy['depth_of_discharge']:.0%} DoD)"),
                ("Simultaneous backup load",
                 f"{peak['simultaneous_va']:,.0f} VA vs "
                 + (f"{peak['inverter_kw_continuous']:g} kW cont."
                    if peak["inverter_kw_continuous"] is not None else "no rating")),
                ("Inverter idle / efficiency",
                 (f"{idle:g} W" if idle is not None else "not declared") + " / "
                 + (f"{efficiency:.0%}" if efficiency is not None else "not declared")),
                ("Autonomy, always-on (no sun)",
                 _hours_label(autonomy["hours_always_on_only"])),
                ("Surplus tier, strong day (summer / Dec)",
                 f"{summer['surplus_kwh']:g} / {winter['surplus_kwh']:g} kWh = "
                 f"{_hours_label(summer['surplus_hours'])} / "
                 f"{_hours_label(winter['surplus_hours'])}"),
                (f"48h always-on, {summer['array_kw']:g} kW (summer / Dec)",
                 f"{summer['net_kwh_always_on']:+g} / {winter['net_kwh_always_on']:+g} kWh"),
                (f"Dark day + {bridge['longest_night_h']:.1f} h night",
                 f"needs {bridge['required_kwh']:g} kWh, has {bridge['usable_kwh']:g}"),
            ]
            _add_table(fig, runtime_rows, ("Line", "Value"),
                       bbox=(_RIGHT_X, 0.29, _RIGHT_W, 0.13))
            # The verdict is a sentence, not a cell — it wraps as text under the table rather
            # than running off the right edge of a column sized for numbers.
            # Wrapped by hand: matplotlib's wrap runs to the figure edge, not the column.
            verdict = textwrap.fill(f"Verdict: {runtime['verdict']}", 82)
            fig.text(_RIGHT_X, 0.275, verdict, fontsize=7, family="monospace", va="top")


def _write_luminaire_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                              page: int = 0) -> None:
    """Three tables that between them make the E-2xx plans readable.

    The plans carry marks, not specifications — that is the whole point of a mark — so this
    sheet is where a mark becomes a product: what lamp and base, how many lumens, at what
    colour temperature or span, listed for how wet a place, whether the product can dim
    (whether a dimmer reaches it is the control schedule's), how many, where. Then the
    control schedule, which is the authoritative statement of the switch legs the plans can
    only draw as dashed lines. Then the runs, with each supply sized against the tape it
    actually drives (→ takeoff/lighting.py — nothing here is hand-summed).

    Two pages (D1-103, M3-101): on one, the ~250-row control schedule crushed the rest
    into clipped cells and pushed the load table onto the title block. ``page`` 1 is it.
    """
    from typehaus.takeoff import (
        connected_lighting_va,
        light_run_takeoff,
        lighting_controls,
        luminaire_schedule,
    )
    with schedule_sheet(pdf, model, number, name,
                        size=PORTRAIT_LEDGER, heading_xy=(0.04, 0.97)) as fig:
        if page == 1:
            controls = lighting_controls(model)
            section(fig, 0.04, 0.945, "LIGHTING CONTROL SCHEDULE")
            control_rows = [
                (row["tag"], row["mark"] or "—", row["room"] or "—",
                 row["circuit"] or (f"via {row['psu']}" if row["psu"] else "—"),
                 ", ".join(row["switches"]) or ("switch on fixture" if row["integral_switch"]
                                                else "—"),
                 ", ".join(sorted(set(row["controls"]))) or "—",
                 "3-way+" if row["ways"] > 1 else "",
                 "CROSS-CIRCUIT" if row["cross_circuit"] else "")
                for row in controls
            ]
            _add_table(fig, control_rows,
                       ("Load", "Mark", "Room", "Circuit", "Switched by", "Control", "Ways",
                        "Note"),
                       bbox=(0.03, 0.13, 0.94, 0.80), truncate=(4,))
            return
        schedule = luminaire_schedule(model)
        section(fig, 0.04, 0.945, "LUMINAIRE SCHEDULE")
        schedule_rows = [
            (row["mark"], _clip(row["description"], 22),
             _clip(" ".join(str(part) for part in (row["brand"], row["model"]) if part)
                   or "—", 18),
             _clip(row["lamp"] or "—", 14), _lamp_base(row),
             _number(row["watts"], "{:.0f}") or _number(row["watts_per_ft"], "{:.1f}/ft"),
             _number(row["lumens"], "{:,.0f}"), _kelvin(row),
             str(row["volts"]), str(row["mount"]).replace(" ceiling", "").replace(", ", "/"),
             "yes" if row["dimming"] == "dimmable" else "no",
             row["rating"],
             str(row["count"]) if row["count"] else f"{row['length_ft'] or 0:.0f} LF",
             _rooms(row["rooms"], 30))
            for row in schedule
        ]
        _add_table(fig, schedule_rows,
                   ("Mark", "Description", "Brand / Model", "Lamp", "Base", "W", "lm", "K",
                    "V", "Mount", "Dim-capable", "Listing", "Qty", "Locations"),
                   bbox=(0.03, 0.55, 0.94, 0.385), truncate=(13,))

        runs = light_run_takeoff(model)
        section(fig, 0.04, 0.525, "LED RUNS AND 24V SUPPLIES")
        run_rows = [
            (row["tag"], row["mark"], row["room"] or "—", f"{row['length_ft']:.1f}",
             f"{row['watts']:.0f}", f"{row['volts']}V", row["psu"] or "—")
            for row in runs["runs"]
        ]
        run_rows.append(("TOTAL", "", "", f"{runs['total_length_ft']:.1f}", "", "", ""))
        _add_table(fig, run_rows,
                   ("Run", "Mark", "Room", "LF", "Watts", "Volts", "Supply"),
                   bbox=(0.03, 0.31, 0.50, 0.20))
        supply_rows = [
            (row["psu"], row["type"] or "—", f"{row['connected_watts']:.0f}",
             f"{row['required_watts']:.0f}",
             "—" if row["rated_watts"] is None else f"{row['rated_watts']:.0f}",
             "OK" if row["adequate"] else ("?" if row["adequate"] is None else "UNDERSIZED"))
            for row in runs["supplies"]
        ]
        _add_table(fig, supply_rows,
                   ("Supply", "Type", "Connected W", "Req. W (125%)", "Rated W", ""),
                   bbox=(0.55, 0.31, 0.42, 0.20))

        load = connected_lighting_va(model)
        section(fig, 0.04, 0.285, "CONNECTED LIGHTING LOAD")
        load_rows = [(row["circuit"], str(row["fixtures"]), f"{row['connected_va']:,.0f}")
                     for row in load["per_circuit"]]
        load_rows.append(("TOTAL CONNECTED", "", f"{load['total_connected_va']:,.0f} VA"))
        load_rows.append(("NEC 220.82 allowance", f"{load['conditioned_area_ft2']:,.0f} ft2",
                          f"{load['allowance_va']:,.0f} VA at "
                          f"{load['allowance_va_per_ft2']:.0f} VA/ft2"))
        _add_table(fig, load_rows, ("Circuit", "Fixtures", "Connected VA"),
                   bbox=(0.03, 0.15, 0.52, 0.12))
        fig.text(0.57, 0.26, str(load["basis"]), fontsize=6, family="sans-serif", wrap=True)


_COLOR_MODE = {"tunable": "TW", "rgb": "RGB", "rgbw": "RGBW", "rgbcct": "RGBCCT"}


def _kelvin(row) -> str:
    """The CCT, or its span, and the colour mode (TW = tunable white) where not fixed."""
    span = row.get("cct_range_k")
    kelvin = f"{span[0]}-{span[1]}" if span else _number(row["cct_k"], "{:.0f}")
    return " ".join(p for p in (kelvin, _COLOR_MODE.get(row.get("color_mode"), "")) if p)


def _lamp_base(row) -> str:
    """The replaceable lamp's base, "integral" for a fixture whose source is not, else —."""
    if row.get("lamp_base"):
        return str(row["lamp_base"])
    return "integral" if row.get("replaceable_lamp") is False else "—"


def _clip(text: object, limit: int) -> str:
    """Text cut to ``limit`` characters with an ellipsis, so one long cell cannot claim the
    column width the numeric cells need."""
    text = str(text)
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _rooms(rooms, limit: int) -> str:
    """Room list kept to ``limit`` characters on a whole-name boundary, count of the rest."""
    kept: list[str] = []
    for room in rooms:
        if kept and len(", ".join([*kept, room])) > limit:
            break
        kept.append(room)
    more = len(rooms) - len(kept)
    return ", ".join(kept) + (f" +{more}" if more else "")


def _ft_in(feet: object) -> str:
    """Decimal feet as ft-in to the nearest 1/2", or an em dash."""
    if not isinstance(feet, (int, float)):
        return "—"
    halves = round(feet * 24)
    sign, halves = ("-" if halves < 0 else ""), abs(halves)
    ft, rem = divmod(halves, 24)
    whole, half = divmod(rem, 2)
    return f"{sign}{ft}'-{whole}{' 1/2' if half else ''}\""


def _has_data_content(model: ResolvedModel) -> bool:
    return any(element.element_kind == "ElectricalDevice"
               and element.kind.value == "data_outlet"
               for storey in model.plan.storeys
               for element in model.plan.storey_elements(storey.tag))


def _write_data_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """The low-voltage twin of E-602: what the devices are, what pipe reaches them, and
    what the PoE switch has to carry.

    The raceway table is here rather than folded into the power conduit schedule because
    comms and power are pulled by different trades on different days and may not share a
    raceway (NEC 800.133/725) — one combined lineal-foot number is not an order either of
    them can buy against. The spare appears with them: the reader who wants to know what can
    still be pulled is this one (→ takeoff/data.py — nothing here is hand-summed).
    """
    from typehaus.takeoff import data_device_schedule, data_raceway_takeoff, poe_budget
    with schedule_sheet(pdf, model, number, name) as fig:
        devices = data_device_schedule(model)
        section(fig, 0.04, 0.90, "LOW-VOLTAGE DEVICE SCHEDULE")
        device_rows = [
            (row["tag"], row["type_name"] or row["type_ref"] or "—", row["room"] or "—",
             row["mount"], _ft_in(row["mount_elevation_ft"]),
             _number(row["poe_watts"], "{:.0f} W") or "—",
             row["circuit"] or "PoE")
            for row in devices
        ]
        _add_table(fig, device_rows,
                   ("Tag", "Product", "Room", "Mount", "Elev AFF", "PoE", "Circuit"),
                   bbox=(0.03, 0.60, 0.94, 0.28))

        raceways = data_raceway_takeoff(model)
        section(fig, 0.04, 0.565, "DATA AND SPARE RACEWAYS")
        raceway_rows = [
            (f"{row['trade_size_in']:g}\"", str(row["service"]).upper(), str(row["runs"]),
             f"{row['length_ft']:.1f}", ", ".join(row["tags"]))
            for row in raceways
        ]
        _add_table(fig, raceway_rows,
                   ("Trade size", "Carries", "Runs", "LF", "Tags"),
                   bbox=(0.03, 0.38, 0.94, 0.17), truncate=(4,))

        budget = poe_budget(model)
        section(fig, 0.04, 0.345, "PoE BUDGET")
        budget_rows = [
            ("Data devices", str(budget.get("devices", 0))),
            ("Powered over ethernet", str(budget.get("powered_devices", 0))),
            ("Connected PoE load", f"{budget.get('connected_watts', 0):,.0f} W"),
        ]
        unknown = int(budget.get("unknown_devices", 0) or 0)
        if unknown:
            budget_rows.append(("Unrated devices", f"{unknown} — PoE draw not stated"))
        _add_table(fig, budget_rows, ("Item", "Value"), bbox=(0.03, 0.26, 0.52, 0.05))
        fig.text(0.57, 0.30, str(budget.get("basis", "")), fontsize=6, family="sans-serif",
                 wrap=True)
        fig.text(0.03, 0.21,
                 "PoE devices carry no branch circuit — their load lands on the switch, not the "
                 "panel schedule.\nComms conductors share no raceway with power (NEC 800.133, "
                 "725); shared penetrations are permitted.",
                 fontsize=7, family="sans-serif")


def _panel_feeder_rows(model) -> list[dict[str, object]]:
    """Per-panel 220.82 feeder demand — the same estimate `electrical.panel_feeder_load`
    grades, so the sheet and the finding cannot disagree."""
    from typehaus.takeoff import service_load_summary

    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    panels = {e.tag: e for e in model.plan.all_elements()
              if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"}
    by_panel: dict[str, set[str]] = {}
    for circuit in model.plan.library.circuits:
        by_panel.setdefault(circuit.panel_ref, set()).add(circuit.tag)
    rows = []
    for panel_ref in sorted(by_panel):
        product = types.get(getattr(panels.get(panel_ref), "type_ref", "") or "")
        main = getattr(product, "service_amps", None)
        if main is None:
            continue
        summary = service_load_summary(model, circuit_tags=frozenset(by_panel[panel_ref]))
        rows.append({"panel": panel_ref, "main_amps": float(main),
                     "demand_amps": float(summary["demand_va"]) / 240.0})
    return rows
