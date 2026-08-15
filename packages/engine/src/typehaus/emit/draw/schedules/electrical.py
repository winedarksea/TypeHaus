"""The E-6xx schedule pages: panel and service load, luminaires and controls, low-voltage.

These are the sheets the E-1xx/E-2xx plans are unreadable without — the plans carry marks,
and a mark only becomes a product here.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.tables import _add_table, _number
from typehaus.emit.draw.sheet_writer import PORTRAIT_LEDGER, schedule_sheet, section
from typehaus.resolve.model import ResolvedModel


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
        section(fig, 0.04, 0.90, "PANEL SCHEDULE — ED-B-PANEL (225A, 200A SERVICE)")
        # The backup column names the tier, not just the fact: a reader has to be able to tell
        # the circuits that ride through an outage from the ones a relay drops.
        _TIER_LABEL = {"always_on": "BKUP-ON", "shed": "BKUP-SHED"}
        schedule_rows = [
            (row["circuit"], row["description"], f"{row['breaker_amps']}A/{row['poles']}p",
             f"{row['volts']}V", row["nema"] or "—", row["panel"],
             ("GFCI " if row["gfci"] else "")
             + _TIER_LABEL.get(str(row["backup_tier"]), "")
             + ("SOURCE" if row["source"] else "") or "—",
             f"{row['connected_va']:,.0f}")
            for row in schedule
        ]
        _add_table(fig, schedule_rows,
                   ("Circuit", "Description", "Breaker", "Volts", "NEMA", "Panel", "Prot.",
                    "VA"),
                   bbox=(0.04, 0.42, 0.92, 0.46))

        load = service_load_summary(model)
        section(fig, 0.04, 0.38, "SERVICE LOAD — " + str(load["method"]).upper())
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
        _add_table(fig, load_rows, ("Line", "Value"), bbox=(0.04, 0.18, 0.6, 0.18))

        backup = backup_component_rows(model)
        if backup:
            section(fig, 0.04, 0.165, "BACKUP MICROGRID COMPONENTS")
            backup_rows = [(row["component"], f"{row['count']}", row["basis"])
                           for row in backup]
            _add_table(fig, backup_rows, ("Component", "Qty", "Basis"),
                       bbox=(0.04, 0.095, 0.92, 0.06))

        # The runtime estimate rides beside the component list and is labeled an ESTIMATE on
        # the sheet, because that is exactly what it is (→ takeoff/backup_calc.py).
        runtime = backup_runtime_summary(model)
        if runtime.get("modeled"):
            autonomy = runtime["autonomy"]
            cycle = runtime["cycle_48h"]
            peak = runtime["peak"]
            # Beside the service load, not under the component list: the two bottom blocks
            # were overrunning each other, and this half of the sheet is otherwise empty.
            section(fig, 0.62, 0.38, "BACKUP RUNTIME — ESTIMATE, NOT A GUARANTEE")
            runtime_rows = [
                ("Usable storage",
                 f"{autonomy['usable_kwh']:g} kWh of {autonomy['nameplate_kwh']:g} "
                 f"({autonomy['depth_of_discharge']:.0%} DoD)"),
                ("Simultaneous backup load",
                 f"{peak['simultaneous_va']:,.0f} VA vs "
                 + (f"{peak['inverter_kw_continuous']:g} kW cont."
                    if peak["inverter_kw_continuous"] is not None else "no rating")),
                ("Autonomy, both tiers", _hours_label(autonomy["hours_all_tiers"])),
                ("Autonomy, always-on only", _hours_label(autonomy["hours_always_on_only"])),
                (f"48h cycle ({cycle['array_kw']:g} kW array)",
                 f"{cycle['solar_day_kwh']:g} kWh in vs "
                 f"{cycle['two_day_load_kwh_all_tiers']:g} kWh out "
                 f"= {cycle['net_kwh_all_tiers']:+g} kWh"),
            ]
            _add_table(fig, runtime_rows, ("Line", "Value"), bbox=(0.62, 0.24, 0.34, 0.12))
            # The verdict is a sentence, not a cell — it wraps as text under the table rather
            # than running off the right edge of a column sized for numbers.
            fig.text(0.62, 0.225, f"Verdict: {runtime['verdict']}", fontsize=7,
                     family="monospace", wrap=True, va="top")


def _write_luminaire_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """Three tables that between them make the E-2xx plans readable.

    The plans carry marks, not specifications — that is the whole point of a mark — so this
    sheet is where a mark becomes a product: what lamp, how many lumens, at what colour
    temperature, listed for how wet a place, dimmable or not, how many, and where. Then the
    control schedule, which is the authoritative statement of the switch legs the plans can
    only draw as dashed lines. Then the runs, with each supply sized against the tape it
    actually drives (→ takeoff/lighting.py — nothing here is hand-summed).
    """
    from typehaus.takeoff import (
        connected_lighting_va,
        light_run_takeoff,
        lighting_controls,
        luminaire_schedule,
    )
    with schedule_sheet(pdf, model, number, name,
                        size=PORTRAIT_LEDGER, heading_xy=(0.04, 0.97)) as fig:
        schedule = luminaire_schedule(model)
        section(fig, 0.04, 0.945, "LUMINAIRE SCHEDULE")
        schedule_rows = [
            (row["mark"], row["description"], row["lamp"] or "—",
             _number(row["watts"], "{:.0f} W") or _number(row["watts_per_ft"], "{:.1f} W/ft"),
             _number(row["lumens"], "{:,.0f}"), _number(row["cct_k"], "{:.0f}K"),
             f"{row['volts']}V", row["mount"], row["dimming"], row["rating"],
             str(row["count"]) if row["count"] else f"{row['length_ft'] or 0:.0f} LF",
             ", ".join(row["rooms"]))
            for row in schedule
        ]
        _add_table(fig, schedule_rows,
                   ("Mark", "Description", "Lamp", "Watts", "Lumens", "CCT", "V", "Mount",
                    "Dim", "Listing", "Qty", "Locations"),
                   bbox=(0.03, 0.72, 0.94, 0.215), truncate=(11,))

        controls = lighting_controls(model)
        section(fig, 0.04, 0.695, "LIGHTING CONTROL SCHEDULE")
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
                   ("Load", "Mark", "Room", "Circuit", "Switched by", "Control", "Ways", "Note"),
                   bbox=(0.03, 0.32, 0.94, 0.365))

        runs = light_run_takeoff(model)
        section(fig, 0.04, 0.295, "LED RUNS AND 24V SUPPLIES")
        run_rows = [
            (row["tag"], row["mark"], row["room"] or "—", f"{row['length_ft']:.1f}",
             f"{row['watts']:.0f}", f"{row['volts']}V", row["psu"] or "—")
            for row in runs["runs"]
        ]
        run_rows.append(("TOTAL", "", "", f"{runs['total_length_ft']:.1f}", "", "", ""))
        _add_table(fig, run_rows,
                   ("Run", "Mark", "Room", "LF", "Watts", "Volts", "Supply"),
                   bbox=(0.03, 0.195, 0.52, 0.09))
        supply_rows = [
            (row["psu"], row["type"] or "—", f"{row['connected_watts']:.0f}",
             f"{row['required_watts']:.0f}",
             "—" if row["rated_watts"] is None else f"{row['rated_watts']:.0f}",
             "OK" if row["adequate"] else ("?" if row["adequate"] is None else "UNDERSIZED"))
            for row in runs["supplies"]
        ]
        _add_table(fig, supply_rows,
                   ("Supply", "Type", "Connected W", "Req. W (125%)", "Rated W", ""),
                   bbox=(0.57, 0.195, 0.40, 0.09))

        load = connected_lighting_va(model)
        section(fig, 0.04, 0.17, "CONNECTED LIGHTING LOAD")
        load_rows = [(row["circuit"], str(row["fixtures"]), f"{row['connected_va']:,.0f}")
                     for row in load["per_circuit"]]
        load_rows.append(("TOTAL CONNECTED", "", f"{load['total_connected_va']:,.0f} VA"))
        load_rows.append(("NEC 220.82 allowance", f"{load['conditioned_area_ft2']:,.0f} ft2",
                          f"{load['allowance_va']:,.0f} VA at "
                          f"{load['allowance_va_per_ft2']:.0f} VA/ft2"))
        _add_table(fig, load_rows, ("Circuit", "Fixtures", "Connected VA"),
                   bbox=(0.03, 0.09, 0.52, 0.07))
        fig.text(0.57, 0.15, str(load["basis"]), fontsize=6, family="sans-serif", wrap=True)


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
             row["mount"], _number(row["mount_elevation_ft"], "{:.1f}'") or "—",
             _number(row["poe_watts"], "{:.0f} W") or "—",
             row["circuit"] or "PoE")
            for row in devices
        ]
        _add_table(fig, device_rows,
                   ("Tag", "Product", "Room", "Mount", "Elev", "PoE", "Circuit"),
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
        _add_table(fig, budget_rows, ("", ""), bbox=(0.03, 0.26, 0.52, 0.05))
        fig.text(0.57, 0.30, str(budget.get("basis", "")), fontsize=6, family="sans-serif",
                 wrap=True)
        fig.text(0.03, 0.21,
                 "PoE devices carry no branch circuit — their load lands on the switch, not the "
                 "panel schedule.\nComms conductors share no raceway with power (NEC 800.133, "
                 "725); shared penetrations are permitted.",
                 fontsize=7, family="sans-serif")
