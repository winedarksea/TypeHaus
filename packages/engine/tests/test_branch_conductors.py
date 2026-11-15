"""Authored branch conductors: 240.4 / 110.14(C)(1) / 250.122 / 210.23(B) (2026 NEC, lane A)."""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model.ampacity import max_ocpd, smallest_size_for, termination_column


def test_conductor_protection_arithmetic():
    # 110.14(C)(1): 60 °C to 100 A and 14-1 AWG; 75 °C above, or where authored.
    assert termination_column(50, "6") == 60 and termination_column(150, "1/0") == 75
    assert termination_column(50, "8", 75) == 75
    # 240.4(D) caps 14/12/10 Cu at 15/20/30 A whatever the table says.
    assert [max_ocpd("cu", s, 60, next_size_up=True) for s in ("14", "12", "10")] == [15, 20, 30]
    # #6 Cu at 60 °C is 55 A: 240.4(B) reaches 60 A only where the circuit allows it.
    assert max_ocpd("cu", "6", 60, next_size_up=True) == 60
    assert max_ocpd("cu", "6", 60, next_size_up=False) == 55
    assert max_ocpd("cu", "8", 75, next_size_up=False) == 50   # CKT-ESS-GRID's #8
    assert max_ocpd("cu", "16", 60, next_size_up=False) is None  # conditional (D) row
    assert [smallest_size_for(a, "cu") for a in (15, 20, 30, 40, 50)] == \
        ["14", "12", "10", "8", "6"]


def test_250_122_d_enlarges_the_egc_by_circular_mils():
    """#6 on 30 A (base #10): x2.53 by area, so the #10 table EGC grows to 26.25 kcmil;
    a #8 (16.51) falls short, a #6 (26.25, equal to the conductors) meets it."""
    from types import SimpleNamespace

    from typehaus.checks.mep.electrical_conductors import egc_size

    def grade(egc):
        circuit = SimpleNamespace(tag="CKT-T", spd=False, conductor_awg="6", egc_awg=egc,
                                  conductor_material="cu", breaker_amps=30,
                                  termination_temp_c=None)
        ctx = SimpleNamespace(plan=SimpleNamespace(library=SimpleNamespace(circuits=[circuit])))
        return egc_size(ctx)[0]

    short, met = grade("8"), grade("6")
    assert short.result.value == "fail" and "250.122(D)" in (short.code_ref or "")
    assert met.result.value == "pass" and "26.25 kcmil" in met.message


@pytest.mark.parametrize("cid", ["electrical.conductor_protection", "electrical.egc_size",
                                 "electrical.permissible_loads"])
def test_catlins_conductors_and_loads_hold(catlin_model_ro, cid):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY, only=cid)
    found = [f for f in report.findings if f.check_id == cid]
    assert found and {f.result.value for f in found} == {"pass"}
