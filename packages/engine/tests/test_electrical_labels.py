"""Derived NEC labels (resolve/electrical_labels.py) on the reference house."""

from __future__ import annotations

import math
from types import SimpleNamespace

from typehaus.checks.mep.electrical_labels import label_inputs
from typehaus.findings import Result


def _by_uid(model):
    return {label.uid: label for label in model.electrical_labels}


def test_each_label_follows_its_trigger(catlin_model_ro) -> None:
    labels = _by_uid(catlin_model_ro)
    sections = {label.section for label in labels.values()}
    assert sections == {"690.12(D)", "690.12(D)(2)", "690.7(D)", "690.31(D)(2)", "705.10",
                        "230.70(D)", "705.12(B)(2)(b)", "230.70(B)(1)", "230.70(B)(2)",
                        "706.15(C)", "480.7(F)", "404.8(C)", "424.47", "625.43(C)"}
    assert labels["label/690.12(D)(2)/ED-M-RSD-INIT"].wording == \
        "RAPID SHUTDOWN SWITCH FOR SOLAR PV SYSTEM"
    assert labels["label/690.7(D)/EQ-B-ESS-INV"].wording.endswith("384 V")
    # 690.31(D)(2): one per 10 ft of each PV dc run.
    for run in (r for r in catlin_model_ro.conduits if r.service == "power_dc"):
        feet = run.length_m / 0.3048
        assert labels[f"label/690.31(D)(2)/{run.tag}"].quantity == math.ceil(feet / 10)
    assert {lbl.host_ref for lbl in labels.values() if lbl.section == "424.47"} == {"ED-B-PANEL"}
    assert "ED-B-PANEL-2" in labels["label/625.43(C)/ED-G-EV-1450"].wording
    assert labels["label/705.10/ED-M-METER"].also == ("702.7(A)(1)",)


def test_unauthored_house_inputs_are_unknown_never_defaulted(catlin_model_ro) -> None:
    findings = label_inputs(SimpleNamespace(model=catlin_model_ro))  # type: ignore[arg-type]
    unknown = sorted(f.code_ref for f in findings if f.result is Result.UNKNOWN)
    assert unknown == ["NEC 480.7(F)", "NEC 705.10 / 702.7(A)(1)"]
    assert "not authored" in _by_uid(catlin_model_ro)["label/705.10/ED-M-METER"].wording
