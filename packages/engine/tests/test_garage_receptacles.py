"""NEC 210.52(G)(1): a receptacle in each garage vehicle bay, bays derived from the doors."""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model

_CID = "code.NEC_210_52_G_garage_receptacles"


def _findings(model):
    return [f for f in run_from_model(model, [], only=[_CID]).findings if f.check_id == _CID]


def test_catlin_16ft_door_makes_two_bays_each_served(catlin_model_ro):
    findings = _findings(catlin_model_ro)
    assert [f.result.value for f in findings] == ["pass", "pass"]
    assert {f.message.split(": ")[1] for f in findings} == {"ED-G-RC-E", "ED-G-RC-W"}


def test_a_bay_without_its_receptacle_fails(catlin_model_ro):
    plan = catlin_model_ro.plan
    plan = plan.with_elements("garage", [e for e in plan.storey_elements("garage")
                                         if e.tag != "ED-G-RC-E"])
    model = copy.copy(catlin_model_ro)
    model.plan = plan
    results = sorted(f.result.value for f in _findings(model))
    assert results == ["fail", "pass"]


def test_the_opener_outlet_rides_a_blank_face_gfci_off_the_garage_circuit(catlin_model_ro):
    """210.11(C)(4)'s circuit feeds the bay receptacles only; the opener's ceiling outlet is
    GFCI from the load side of a reachable blank face (210.8), which counts as no receptacle."""
    plan = catlin_model_ro.plan
    devices = [e for s in plan.storeys for e in plan.storey_elements(s.tag)
               if e.element_kind == "ElectricalDevice"]
    assert {d.tag for d in devices if d.circuit == "CKT-RC-GARAGE"} == {"ED-G-RC-E", "ED-G-RC-W"}
    gdo = next(d for d in devices if d.tag == "ED-G-GDO-RC")
    assert (gdo.circuit, gdo.gfci_ref) == ("CKT-LT-MAIN", "ED-G-GDO-GFCI")
    gfci = [f for f in run_from_model(catlin_model_ro, [], only=["code.E3902_gfci_locations"])
            .findings if "ED-G-GDO-RC" in f.message]
    assert [f.result.value for f in gfci] == ["pass"]
    assert not any("ED-G-GDO-GFCI" in f.message for f in _findings(catlin_model_ro))
