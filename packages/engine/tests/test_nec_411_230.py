"""2026 NEC 411, 210.70(C), 230.70(A)(3), 230.79(C): printed numbers and Catlin's readings.

Paraphrase: docs/code-notes/nec-2026-paraphrase-411-230.md.
"""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model.nec import NEC

_PRINTED = {
    "SERVICE_DISCONNECT_BATHROOM": "230.70(A)(3)", "SERVICE_DISCONNECT_MIN_RATING": "230.79(C)",
    "EQUIPMENT_SPACE_LIGHTING": "210.70(C)", "LOW_VOLTAGE_LIGHTING_VOLTAGE": "411.4(B)",
    "EQUIPMENT_SPACE_AUTOMATIC": "210.70(C)(3)", "LOW_VOLTAGE_LIGHTING_LISTING": "411.2",
    "LOW_VOLTAGE_LIGHTING_CONCEALED": "411.6(A)", "LOW_VOLTAGE_LIGHTING_ISOLATION": "411.7(B)",
}


def test_printed_numbers():
    assert {name: getattr(NEC, name) for name in _PRINTED} == _PRINTED


def _findings(model, check_id):
    report = run_from_model(model, [], tier=Tier.ADVISORY, only=check_id)
    return [f for f in report.findings if f.check_id == check_id]


def test_catlins_service_disconnect_is_outdoors_and_over_100_a(catlin_model_ro):
    found = _findings(catlin_model_ro, "electrical.service_disconnect_rules")
    assert [f.result.value for f in found] == ["pass", "pass"]
    assert "320 A" in found[1].message


def test_catlins_equipment_rooms_are_graded_for_210_70_c(catlin_model_ro):
    found = _findings(catlin_model_ro, "electrical.equipment_space_lighting")
    by_room = {f.element_tags[0]: f.result.value for f in found}
    # The 3-way pairs at D-B-FURN (2026-11-14); D-B-ESS is a closet door, not an entry.
    assert by_room == {"RM-A-EAST-UNFIN": "pass", "RM-B-ESS": "pass",
                       "RM-B-FURNACE": "pass", "RM-B-WORKSHOP": "pass"}


def test_laundry_track_is_in_another_room_than_the_tub(catlin_model_ro):
    found = _findings(catlin_model_ro, "electrical.bath_luminaire_zone")
    assert [(f.result.value, f.element_tags) for f in found] == [
        ("pass", ("ED-M-LAUNDRY-TRACK", "FX-M-BATH2-TUB"))]
    assert "the zone is the tub's own room" in found[0].message


def _with_device_types(plan, update, tags=None):
    types = tuple(t.model_copy(update=update) if (tags is None or t.tag in tags) else t
                  for t in plan.library.electrical_device_types)
    return plan.model_copy(update={"library": plan.library.model_copy(
        update={"electrical_device_types": types})})


def test_210_70_c3_automatic_only_control_is_unknown(catlin_plan, catlin_model_ro):
    from _helpers import check_context

    from typehaus.checks.mep.electrical_space_lighting import equipment_space_lighting

    switches = {e.type_ref for e in catlin_plan.all_elements()
                if e.element_kind == "ElectricalDevice" and e.kind.value == "switch"}
    plan = _with_device_types(catlin_plan, {"control": "occupancy"}, switches)
    found = {f.element_tags[0]: f for f in equipment_space_lighting(
        check_context(plan, catlin_model_ro))}
    assert found["RM-B-ESS"].result.value == "unknown"
    assert NEC.EQUIPMENT_SPACE_AUTOMATIC in found["RM-B-ESS"].message


def test_411_listing_rows(catlin_plan, catlin_model_ro):
    from _helpers import check_context

    from typehaus.checks.mep.lighting import light_run_psu

    def rows(plan):
        return {f.message.split(":")[0].replace("UNKNOWN — ", ""): f.result.value
                for f in light_run_psu(check_context(plan, catlin_model_ro))
                if "411." in (f.code_ref or "")}

    # Catlin: the 200 W Diode and the HLG-100H are not shown Class 2 on their sheets.
    found = [f for f in light_run_psu(check_context(catlin_plan, catlin_model_ro))
             if NEC.LOW_VOLTAGE_LIGHTING_CONCEALED in (f.code_ref or "")]
    assert found[0].result.value == "unknown" and "ED-T-LT-PSU-96-WE" in found[0].message
    listed = _with_device_types(catlin_plan, {"supply_listing": "UL 8750", "class_2": True,
                                              "isolating_secondary": True})
    assert rows(listed) == {"411.2": "pass", "411.6(A)": "pass", "411.7(B)": "pass"}
    assert rows(_with_device_types(listed, {"isolating_secondary": False}))["411.7(B)"] == "fail"
