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
    assert {f.message.split(": ")[1] for f in findings} == {"ED-G-RC-E", "ED-G-RC-240"}


def test_a_bay_without_its_receptacle_fails(catlin_model_ro):
    plan = catlin_model_ro.plan
    plan = plan.with_elements("garage", [e for e in plan.storey_elements("garage")
                                         if e.tag != "ED-G-RC-E"])
    model = copy.copy(catlin_model_ro)
    model.plan = plan
    results = sorted(f.result.value for f in _findings(model))
    assert results == ["fail", "pass"]
