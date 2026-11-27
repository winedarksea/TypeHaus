"""``mep.pipe_insulation``: R-3 per hot-water run (2012 IECC R403.4.2 via Minn. R. 1322.0010)."""

from __future__ import annotations

import dataclasses

from typehaus.checks import run_from_model
from typehaus.checks.mep.pipe_insulation import _run_limit_ft
from typehaus.checks.registry import Tier
from typehaus.findings import Result


def _verdict(model, tag: str) -> Result:
    found = run_from_model(model, [], tier=Tier.CODE, only="mep.pipe_insulation").findings
    return next(f.result for f in found if f.check_id == "mep.pipe_insulation"
                and tag in f.element_tags)


def _with(model, tag: str, **changes):
    runs = [dataclasses.replace(r, **changes) if r.tag == tag else r for r in model.pipe_runs]
    return dataclasses.replace(model, pipe_runs=runs)


def test_table_r403_4_2_run_lengths() -> None:
    assert [_run_limit_ft(d) for d in (0.375, 0.5, 0.75, 1.0)] == [30.0, 20.0, 10.0, 5.0]


def test_a_required_run_grades_its_spec_row(catlin_model_ro) -> None:
    model = catlin_model_ro  # PR-B-HW-TRUNK: 1" copper (item 1), 1" fiberglass R-3.5
    assert _verdict(model, "PR-B-HW-TRUNK") is Result.PASS
    assert _verdict(_with(model, "PR-B-HW-TRUNK", insulation=None), "PR-B-HW-TRUNK") \
        is Result.FAIL
    assert _verdict(_with(model, "PR-B-HW-TRUNK", insulation="1/4\" mystery wrap"),
                    "PR-B-HW-TRUNK") is Result.UNKNOWN


def test_a_run_serving_a_kitchen_outlet_needs_r3_wherever_the_room(catlin_model_ro) -> None:
    """PR-M-DW-HW is 4.2 ft of 1/2" to the dishwasher (a living-room kitchen): item 3 alone."""
    model = catlin_model_ro
    assert _verdict(model, "PR-M-DW-HW") is Result.PASS  # wrapped
    assert _verdict(_with(model, "PR-M-DW-HW", insulation=None), "PR-M-DW-HW") is Result.FAIL
