"""NEC 240.24(A) / 404.8(A): no panel's highest handle above 6'-7" (body top, conservatively)."""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.model import Mount, MountKind, inch

_CID = "electrical.panel_handle_height"


def _results(model) -> dict[str, str]:
    return {f.element_tags[0]: f.result.value
            for f in run_from_model(model, [], only=[_CID]).findings if f.check_id == _CID}


def test_catlin_panel_tops_hold_79_inches_and_a_raised_one_fails(catlin_model_ro):
    assert _results(catlin_model_ro) == dict.fromkeys(
        ("ED-B-BACKUP-ENCL", "ED-B-BACKUP-PANEL", "ED-B-PANEL", "ED-B-PANEL-2"), "pass")
    plan = catlin_model_ro.plan
    raised = [e.model_copy(update={"mount": Mount(kind=MountKind.WALL, elevation=inch(60))})
              if e.tag == "ED-B-PANEL" else e for e in plan.storey_elements("basement")]
    model = copy.copy(catlin_model_ro)
    model.plan = plan.with_elements("basement", raised)
    assert _results(model)["ED-B-PANEL"] == "fail"  # 60" + 39.37" can = 99.4"
