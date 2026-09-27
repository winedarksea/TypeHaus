"""``mep.pex_water_heater_clearance`` — UPC 604.13, no PEX in the first 18" off a heater.

The cases edit a copy of catlin's resolved supply runs rather than authoring a plan: the
heater, its exact ports and the trunk are the real ones, so a "tee 6" up" is a tee on the
real trunk.
"""

from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from typehaus.checks.mep.water_heater import pex_water_heater_clearance
from typehaus.checks.registry import CheckContext
from typehaus.findings import Result

_IN = 0.0254


def _run(model):
    ctx = CheckContext(plan=model.plan, model=model, preferences=None, profile=None)
    return pex_water_heater_clearance(ctx)


@pytest.fixture
def model(catlin_model_ro):
    return copy.copy(catlin_model_ro)  # pipe_runs is reassigned, never mutated in place


def _hot_tap(model):
    from typehaus.resolve.mep_ports import placed_ports
    return next(p for p in placed_ports(model)
                if p.equipment_tag == "EQ-B-WH" and p.port_tag == "hot")


def _with(model, *runs):
    model.pipe_runs = [*model.pipe_runs, *runs]
    return model


def _pex_branch(model, tag, z_off_in, plan_off_in=0.0):
    """A PEX branch starting ``z_off_in`` above the hot tap and running 3' east."""
    tap = _hot_tap(model)
    trunk = next(r for r in model.pipe_runs if r.tag == "PR-B-HW-TRUNK")
    x, y, z = tap.x_m + plan_off_in * _IN, tap.y_m, tap.z_m + z_off_in * _IN
    return replace(trunk, uid=tag, tag=tag, path=((x, y), (x + 0.9144, y)),
                   z_m=(z, z), z_start_m=z, z_end_m=z, length_m=0.9144, material="pex")


def test_catlin_passes_and_names_its_tap_runs(catlin_model_ro) -> None:
    findings = _run(catlin_model_ro)
    assert [f.result for f in findings] == [Result.PASS]
    msg = findings[0].message
    assert "PR-B-HW-TRUNK" in msg and "PR-B-CW-WH" in msg
    assert "tees on 29\" out" in msg  # the five branches tee off the trunk 29" up


def test_a_pex_trunk_on_the_tap_fails(model) -> None:
    model.pipe_runs = [replace(r, material="pex") if r.tag == "PR-B-HW-TRUNK" else r
                       for r in model.pipe_runs]
    fails = [f for f in _run(model) if f.result is Result.FAIL]
    assert [f.element_tags for f in fails] == [("PR-B-HW-TRUNK", "EQ-B-WH")]
    assert "0\" along" in fails[0].message
    assert "604.13" in fails[0].code_ref


def test_a_pex_branch_teeing_six_inches_up_fails(model) -> None:
    fails = [f for f in _run(_with(model, _pex_branch(model, "PR-X-PEX", 6)))
             if f.result is Result.FAIL]
    assert [f.element_tags[0] for f in fails] == ["PR-X-PEX"]
    assert "6\" along" in fails[0].message


def test_a_pex_branch_teeing_beyond_18_inches_passes(model) -> None:
    findings = _run(_with(model, _pex_branch(model, "PR-X-PEX", 20)))
    assert [f.result for f in findings] == [Result.PASS]


def test_a_pex_run_20_inches_off_in_plan_is_not_connected(model) -> None:
    findings = _run(_with(model, _pex_branch(model, "PR-X-PEX", 0, plan_off_in=20)))
    assert [f.result for f in findings] == [Result.PASS]
    assert "PR-X-PEX" not in findings[0].message


def test_a_heater_with_no_exact_port_is_unknown_not_na(model, monkeypatch) -> None:
    from typehaus.resolve import mep_ports

    real = mep_ports.placed_ports
    monkeypatch.setattr(mep_ports, "placed_ports",
                        lambda m: [replace(p, exact=False) for p in real(m)])
    assert [f.result for f in _run(model)] == [Result.UNKNOWN]


def test_no_heater_is_na_only_without_hot_water(catlin_model_ro) -> None:
    from types import SimpleNamespace

    plan = SimpleNamespace(all_elements=lambda: [])
    hot = [r for r in catlin_model_ro.pipe_runs if r.system == "water_hot"]
    for runs, verdict in (([], Result.NOT_APPLICABLE), (hot, Result.UNKNOWN)):
        ctx = SimpleNamespace(plan=plan, model=SimpleNamespace(pipe_runs=runs))
        assert [f.result for f in pex_water_heater_clearance(ctx)] == [verdict]
