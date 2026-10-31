"""Lighting take-off arithmetic: mark uniqueness, honest sums, and PSU sizing.

The schedule is keyed on marks, so a duplicate mark silently merges two products into one
row on a permit sheet. That is the one failure here that a reader could not spot.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.lighting import (
    PSU_SIZING_FACTOR,
    connected_lighting_va,
    light_run_materials,
    light_run_takeoff,
    lighting_controls,
    luminaire_schedule,
)

_M_TO_FT = 3.280839895013123


def test_every_schedule_mark_is_unique_and_stated(catlin_model):
    rows = luminaire_schedule(catlin_model)
    marks = [row["mark"] for row in rows]
    assert all(marks), "a luminaire type on the schedule with no mark cannot be referenced"
    assert len(set(marks)) == len(marks), sorted(marks)
    # Marks print in order, which is the order the sheet and the reader both scan.
    assert marks == sorted(marks)
    # "I" is never a mark: it reads as a 1 on a drawing.
    assert "I" not in marks


def test_every_installed_luminaire_names_a_product(catlin_model):
    """An installed type prints its brand and model on E-602; catalog-only types are exempt
    because they never reach the schedule."""
    products = {product.tag for product in catlin_model.plan.library.products}
    unnamed = [row["type"] for row in luminaire_schedule(catlin_model)
               if row["product"] is None or row["product"] not in products]
    assert not unnamed, f"installed luminaire types with no product_ref: {unnamed}"
    for row in luminaire_schedule(catlin_model):
        assert row["brand"], row["type"]


def test_the_schedule_counts_reconcile_with_the_placed_fixtures(catlin_model):
    rows = {row["type"]: row for row in luminaire_schedule(catlin_model)}
    placed: dict[str, int] = {}
    for storey in catlin_model.plan.storeys:
        for element in catlin_model.plan.storey_elements(storey.tag):
            if (element.element_kind == "ElectricalDevice"
                    and element.kind.value == "light"):
                placed[element.type_ref] = placed.get(element.type_ref, 0) + 1
    for type_ref, count in placed.items():
        assert rows[type_ref]["count"] == count, type_ref
    # Every placed type has a row, and no row invents a type that was never placed.
    run_types = {run.type_ref for run in catlin_model.light_runs}
    assert set(rows) == set(placed) | run_types


def test_a_run_type_reports_lineal_feet_instead_of_a_count(catlin_model):
    row = next(r for r in luminaire_schedule(catlin_model) if r["type"] == "ED-T-LT-STRIP24")
    assert row["count"] == 0 and row["length_ft"] > 0
    assert row["watts"] is None and row["watts_per_ft"] == 3.0
    assert row["volts"] == 24
    # Only this type's runs — a schedule row is per type.
    total = sum(run.length_m for run in catlin_model.light_runs
                if run.type_ref == "ED-T-LT-STRIP24") * _M_TO_FT
    assert row["length_ft"] == pytest.approx(round(total, 1))
    assert len({run.type_ref for run in catlin_model.light_runs}) > 1, \
        "this assertion only means something while more than one run type exists"


def test_unstated_photometrics_report_none_rather_than_zero(catlin_model):
    """A schedule that fills a blank with a plausible number is worse than one that admits it."""
    for row in luminaire_schedule(catlin_model):
        assert row["watts"] is None or row["watts"] > 0
        assert row["lumens"] is None or row["lumens"] > 0
        assert row["length_ft"] is None or row["length_ft"] > 0


def test_run_lengths_and_watts_sum_from_the_authored_polylines(catlin_model):
    takeoff = light_run_takeoff(catlin_model)
    by_tag = {row["tag"]: row for row in takeoff["runs"]}
    assert set(by_tag) == {run.tag for run in catlin_model.light_runs}
    for run in catlin_model.light_runs:
        assert by_tag[run.tag]["length_ft"] == pytest.approx(round(run.length_m * _M_TO_FT, 1))
    # The total is round(sum of exact); the by_type rows are each already rounded to 0.1,
    # so summing THEM can drift by up to 0.05 per row plus the total's own half-step. That
    # tolerance is not slack — it is the arithmetic: e.g. 3.3 + 94.9 + 8.9 = 107.1 against
    # an exact 107.1667 that rounds to 107.2.
    by_type = takeoff["by_type"]
    assert takeoff["total_length_ft"] == pytest.approx(
        sum(row["length_ft"] for row in by_type), abs=0.05 * (len(by_type) + 1))
    # 3 W/ft is the authored tape; the run watts are that times its own length.
    living = by_tag["LR-M-LIVING-W"]
    assert living["watts"] == pytest.approx(round(living["length_ft"] * 3.0, 1))


def test_light_run_materials_splits_the_blended_length_into_order_lines(catlin_model):
    """``light_run_takeoff`` bills one blended length per type; this is the real order
    sheet a channel/tape install needs: channel and tape by the foot, end caps and corner
    connectors by the piece."""
    materials = light_run_materials(catlin_model)
    by_key = {(row["type"], row["item"]): row for row in materials}
    assert {row["item"] for row in materials} == {
        "channel", "tape", "end_cap", "corner_connector"}

    strip24 = {run.tag: run for run in catlin_model.light_runs if run.type_ref == "ED-T-LT-STRIP24"}
    surface = {tag: run for tag, run in strip24.items() if run.profile == "surface"}
    # The shadow-gap coves' tape sticks in the drywall trade's bead (#103), so only the
    # surface runs bill channel and caps here; the tape rides every run.
    assert set(strip24) - set(surface) == {"LR-M-LIVING-W", "LR-M-LIVING-E", "LR-S-HALL-GAP"}
    channel = by_key[("ED-T-LT-STRIP24", "channel")]
    tape = by_key[("ED-T-LT-STRIP24", "tape")]
    assert channel["quantity"] == pytest.approx(
        round(sum(run.length_m * _M_TO_FT for run in surface.values()), 1))
    assert tape["quantity"] == pytest.approx(
        round(sum(run.length_m * _M_TO_FT for run in strip24.values()), 1))
    assert channel["unit"] == tape["unit"] == "LF"
    # Every surface run takes exactly two end caps, one per open end.
    end_cap = by_key[("ED-T-LT-STRIP24", "end_cap")]
    assert end_cap["quantity"] == 2 * len(surface)
    assert end_cap["unit"] == "EA"
    # A corner connector for every interior vertex of a surface run; a shadow-gap corner
    # (the hall cove's two) is the tape's own bend.
    corner = by_key[("ED-T-LT-STRIP24", "corner_connector")]
    assert corner["quantity"] == sum(max(len(run.path) - 2, 0) for run in surface.values())


def test_every_supply_is_sized_at_125_percent_of_what_it_drives(catlin_model):
    supplies = light_run_takeoff(catlin_model)["supplies"]
    assert supplies
    for supply in supplies:
        # Both figures are rounded to 0.1 W for display; the error bound is half a step on
        # each, the connected one scaled by the factor.
        assert supply["required_watts"] == pytest.approx(
            supply["connected_watts"] * PSU_SIZING_FACTOR, abs=0.05 * (1 + PSU_SIZING_FACTOR) + 1e-9)
        assert supply["adequate"] is True, supply
        assert supply["rated_watts"] >= supply["required_watts"]
    # Two runs share the living-room supply, so its demand is their sum, not the larger.
    living = next(s for s in supplies if s["psu"] == "ED-M-LIVING-LT-PSU")
    assert len(living["runs"]) == 2
    assert living["connected_watts"] == pytest.approx(
        round(sum(row["watts"] for row in light_run_takeoff(catlin_model)["runs"]
                  if row["psu"] == "ED-M-LIVING-LT-PSU"), 1))


def test_controls_name_a_resolvable_switch_or_carry_one_on_the_fixture(catlin_model):
    rows = lighting_controls(catlin_model)
    assert rows
    switches = {element.tag for storey in catlin_model.plan.storeys
                for element in catlin_model.plan.storey_elements(storey.tag)
                if element.element_kind == "ElectricalDevice"
                and element.kind.value == "switch"}
    for row in rows:
        assert row["switches"] or row["integral_switch"], row["tag"]
        assert set(row["switches"]) <= switches, row["tag"]
        assert "(missing)" not in row["controls"]
        assert not row["cross_circuit"], row


def test_multiway_and_control_kinds_survive_into_the_schedule(catlin_model):
    rows = {row["tag"]: row for row in lighting_controls(catlin_model)}
    # The main hall is a 3-way pair.
    assert rows["ED-M-HALL-CAN1"]["ways"] == 2
    # The plant-room tubes are on a timer, and the theatre sconces on a dimmer.
    assert rows["ED-S-PLANT-TUBE1"]["controls"] == ["smart"]
    assert rows["ED-B-PLAY-N-SCONCE1"]["controls"] == ["dimmer"]
    # The west loft's sconce is switched at the fixture and names nothing.
    assert (rows["ED-A-STUDIO-SCONCE"]["integral_switch"]
            and not rows["ED-A-STUDIO-SCONCE"]["switches"])
    # Supply-fed loads report the supply's branch and their DC source together.
    assert rows["LR-S-HALL-GAP"]["circuit"] == "CKT-LT-UPPER"
    assert rows["LR-S-HALL-GAP"]["psu"] == "ED-S-HALL-LT-PSU"


def test_connected_load_counts_supplies_not_tape_and_sits_under_the_allowance(catlin_model):
    load = connected_lighting_va(catlin_model)
    per_circuit = {row["circuit"]: row for row in load["per_circuit"]}
    assert set(per_circuit) == {"CKT-LT-BACKUP", "CKT-LT-MAIN", "CKT-LT-UPPER", "CKT-BATH-ATTIC"}
    assert load["total_connected_va"] == pytest.approx(
        round(sum(row["connected_va"] for row in load["per_circuit"]), 1))

    # The tape itself is 24V off a driver, so it contributes through its supply exactly
    # once — never as both the run and the PSU.
    supplies = {supply["psu"] for supply in light_run_takeoff(catlin_model)["supplies"]}
    assert supplies
    assert load["total_connected_va"] < load["allowance_va"], (
        "an all-LED house should come in well under the 3 VA/ft2 area allowance")

    # And that allowance is still the code-correct one the service calculation uses.
    from typehaus.takeoff.electrical import GENERAL_LIGHTING_VA_PER_FT2

    assert load["allowance_va_per_ft2"] == GENERAL_LIGHTING_VA_PER_FT2


def test_no_lighting_circuit_exceeds_its_continuous_rating(catlin_model):
    """Lighting is a continuous load: NEC 210.19(A)(1) caps it at 80% of the breaker."""
    circuits = {circuit.tag: circuit for circuit in catlin_model.plan.library.circuits}
    for row in connected_lighting_va(catlin_model)["per_circuit"]:
        circuit = circuits[row["circuit"]]
        limit = circuit.breaker_amps * 120 * 0.8
        assert row["connected_va"] <= limit, (row, limit)


def test_a_line_voltage_run_reaches_the_panel_schedule(catlin_model):
    """A 120V run is a load on its circuit, and both the lighting summary and the panel
    schedule say so — it has no ``load_va`` to bill, only watts per resolved foot. Catlin's
    exterior runs went 24V (2026-10-28), so one is put back on line voltage here."""
    import dataclasses

    from typehaus.takeoff.electrical import panel_schedule
    from typehaus.takeoff.lighting import line_voltage_run_va

    # As built, every run is on a driver and none is a branch load of its own.
    assert line_voltage_run_va(catlin_model) == {}
    lighting = {r["circuit"]: r for r in connected_lighting_va(catlin_model)["per_circuit"]}
    panel = {r["circuit"]: r for r in panel_schedule(catlin_model)}["CKT-LT-MAIN"]
    # The three 96 W drivers sum at their rating; the panel agrees with the lighting sum.
    assert panel["connected_va"] == pytest.approx(lighting["CKT-LT-MAIN"]["connected_va"],
                                                  abs=0.5)
    # The 20A branch stays below the 80% continuous-load allowance.
    assert panel["connected_va"] <= panel["breaker_amps"] * 120 * 0.8

    runs = list(catlin_model.light_runs)
    index = next(i for i, run in enumerate(runs) if run.tag == "LR-G-EAVE-W")
    run = runs[index]
    runs[index] = dataclasses.replace(run, psu_ref=None, circuit="CKT-LT-MAIN")
    original, catlin_model.light_runs = catlin_model.light_runs, runs
    try:
        va = line_voltage_run_va(catlin_model)
        per_circuit = {r["circuit"]: r
                       for r in connected_lighting_va(catlin_model)["per_circuit"]}
    finally:
        catlin_model.light_runs = original
    # 24' of eave at 3.0 W/ft.
    assert set(va) == {"LR-G-EAVE-W"}
    assert va["LR-G-EAVE-W"] == pytest.approx(run.length_m * _M_TO_FT * 3.0)
    assert per_circuit["CKT-LT-MAIN"]["runs"] == 1
    # The run's tape joins the branch and its idle 96 W driver leaves the lighting sum.
    assert per_circuit["CKT-LT-MAIN"]["connected_va"] == pytest.approx(
        lighting["CKT-LT-MAIN"]["connected_va"] + va["LR-G-EAVE-W"] - 96.0, abs=0.5)
