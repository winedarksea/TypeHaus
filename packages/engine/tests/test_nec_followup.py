"""Printed numbers and Catlin readings from the follow-up read (nec-2026-paraphrase-followup)."""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.mep.electrical_circuit_sizing import _allowed
from typehaus.checks.mep.raceway_use import PVC_GROWTH_IN_PER_100FT_F
from typehaus.checks.registry import Tier
from typehaus.model.nec import NEC

_PRINTED = {
    "FLOOR_AREA": "120.5(C)", "GENERAL_LIGHTING_STANDARD": "120.41", "FEEDER_SPD": "215.18",
    "IMC_BENDS": "342.24", "RMC_BENDS": "344.24", "PVC_BENDS": "352.24", "EMT_BENDS": "358.24",
    "ENT_BENDS": "362.24", "EMT_SUPPORT": "358.30", "ENT_SUPPORT": "362.30",
    "PVC_SUPPORT": "Table 352.30(B)", "RMC_SUPPORT": "Table 344.30(B)",
    "PVC_EXPANSION": "352.44", "EMT_CORROSION": "358.10(B)(1)",
    "ENT_NOT_PERMITTED": "362.12", "EXTERIOR_WIRING_METHODS": "225.10",
    "MULTI_RECEPTACLE": "210.21(B)(3)", "INDIVIDUAL_CIRCUIT": "210.22",
    "BRANCH_LOAD_LIMITS": "210.23", "LIGHTING_TRACK_LOCATIONS": "410.150(C)",
}


def _findings(model, check_id, tier=Tier.ADVISORY):
    report = run_from_model(model, [], tier=tier, only=check_id)
    return [f for f in report.findings if f.check_id == check_id]


def test_printed_numbers():
    assert {name: getattr(NEC, name) for name in _PRINTED} == _PRINTED


def test_pvc_growth_matches_table_352_44():
    # Table 352.44 prints 2.03 in./100 ft at 50 degF and 8.11 at 200 degF.
    assert round(PVC_GROWTH_IN_PER_100FT_F * 50, 2) == 2.03
    assert round(PVC_GROWTH_IN_PER_100FT_F * 200, 2) == 8.11


def test_every_feeder_panel_holds_an_spd(catlin_model_ro):
    found = _findings(catlin_model_ro, "code.NEC_215_18_spd", Tier.CODE)
    assert {f.message.split()[0] for f in found if f.result.value == "pass"} == {
        "ED-B-PANEL", "ED-B-PANEL-2", "ED-B-BACKUP-PANEL"}
    assert len(found) == 3


def test_catlins_raceways_are_in_use_the_code_allows(catlin_model_ro):
    found = _findings(catlin_model_ro, "mep.raceway_use")
    assert [f.result.value for f in found] == ["pass"]
    assert "4 ENT runs" in found[0].message


def test_buried_emt_asks_for_approved_corrosion_protection(catlin_model_ro):
    found = _findings(catlin_model_ro, "electrical.underground_raceway")
    emt = [f for f in found if "EMT" in f.message and "corrosion" in f.message]
    assert emt and all("358.10(B)(1)" in f.message for f in emt)


def test_table_210_21_b_3():
    assert [_allowed(a) for a in (10, 15, 20, 30, 40, 50, 60)] == [
        (), (15,), (15, 20), (30,), (40, 50), (50,), (60,)]


def test_catlins_multi_receptacle_circuits_fit_the_table(catlin_model_ro):
    found = _findings(catlin_model_ro, "electrical.multi_receptacle_rating")
    assert not [f for f in found if f.result.value == "fail"]
    # Every type names its NEMA (Q14); the GDO's blank-face GFCI holds no receptacle.
    assert not [f for f in found if f.result.value == "unknown"]
    assert sum(f.result.value == "pass" for f in found) == 12
