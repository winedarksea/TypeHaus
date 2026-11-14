"""2026 NEC 411, 210.70(C), 230.70(A)(3), 230.79(C): printed numbers and Catlin's readings.

Paraphrase: docs/nec-2026-paraphrase-411-230.md.
"""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model.nec import NEC

_PRINTED = {
    "SERVICE_DISCONNECT_BATHROOM": "230.70(A)(3)", "SERVICE_DISCONNECT_MIN_RATING": "230.79(C)",
    "EQUIPMENT_SPACE_LIGHTING": "210.70(C)", "LOW_VOLTAGE_LIGHTING_VOLTAGE": "411.4(B)",
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
    assert "separated from the tub's room" in found[0].message
