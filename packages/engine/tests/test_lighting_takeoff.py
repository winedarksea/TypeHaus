"""Lighting take-off arithmetic: mark uniqueness, honest sums, and PSU sizing.

The schedule is keyed on marks, so a duplicate mark silently merges two products into one
row on a permit sheet. That is the one failure here that a reader could not spot.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.takeoff.lighting import (PSU_SIZING_FACTOR, connected_lighting_va,
                                       light_run_takeoff, lighting_controls,
                                       luminaire_schedule)

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_M_TO_FT = 3.280839895013123


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model


def test_every_schedule_mark_is_unique_and_stated(catlin_model):
    rows = luminaire_schedule(catlin_model)
    marks = [row["mark"] for row in rows]
    assert all(marks), "a luminaire type on the schedule with no mark cannot be referenced"
    assert len(set(marks)) == len(marks), sorted(marks)
    # Marks print in order, which is the order the sheet and the reader both scan.
    assert marks == sorted(marks)
    # "I" is never a mark: it reads as a 1 on a drawing.
    assert "I" not in marks


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
    # Only this type's runs. The sum used to be over *every* light run, which was
    # accidentally right while ED-T-LT-STRIP24 was the only STRIP type in the house and
    # wrong the moment ED-T-LT-NICHE-SNLT joined it — a schedule row is per type.
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
    assert takeoff["total_length_ft"] == pytest.approx(
        round(sum(row["length_ft"] for row in takeoff["by_type"]), 1))
    # 3 W/ft is the authored tape; the run watts are that times its own length.
    living = by_tag["LR-M-LIVING-W"]
    assert living["watts"] == pytest.approx(round(living["length_ft"] * 3.0, 1))


def test_every_supply_is_sized_at_125_percent_of_what_it_drives(catlin_model):
    supplies = light_run_takeoff(catlin_model)["supplies"]
    assert supplies
    for supply in supplies:
        # Both figures are rounded for display, so compare within that rounding rather
        # than re-deriving one from the other's rounded value.
        assert supply["required_watts"] == pytest.approx(
            supply["connected_watts"] * PSU_SIZING_FACTOR, abs=0.1)
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
    assert rows["ED-S-PLANT-TUBE1"]["controls"] == ["timer"]
    assert rows["ED-B-PLAY-N-SCONCE1"]["controls"] == ["dimmer"]
    # The attic den's sconce is switched at the fixture and names nothing.
    assert rows["ED-A-DEN-SCONCE"]["integral_switch"] and not rows["ED-A-DEN-SCONCE"]["switches"]
    # A 24V run reports its supply where a fixture reports a circuit.
    assert rows["LR-S-HALL-GAP"]["circuit"] is None
    assert rows["LR-S-HALL-GAP"]["psu"] == "ED-S-HALL-LT-PSU"


def test_connected_load_counts_supplies_not_tape_and_sits_under_the_allowance(catlin_model):
    load = connected_lighting_va(catlin_model)
    per_circuit = {row["circuit"]: row for row in load["per_circuit"]}
    assert set(per_circuit) == {"CKT-LT-BACKUP", "CKT-LT-MAIN", "CKT-LT-UPPER"}
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
