"""``mep.supply_freeze_exposure``, against the hand-worked ``notes/supply_freeze_basis.md``."""

from __future__ import annotations

import pytest

from typehaus.checks.mep import supply_freeze as sf
from typehaus.checks.mep.supply_freeze_walk import (
    FreezeAdvisory,
    Profile,
    pipe_plane_profile,
    vent_trimmed,
    wall_frame,
)
from typehaus.findings import Result

INCH = 0.0254
# Note §3: 1/2" PEX centred 4.000" off the sheathing plane, OD 0.625".
LAV_X_M, LAV_RADIUS_M = 4.0 * INCH, 0.3125 * INCH


def _w1_profile(catlin_model_ro, catlin_plan, *, x_in=4.0, drop=None):
    wall = next(w for w in catlin_model_ro.walls if w.tag == "W-M-W1")
    outward, _ring = wall_frame(wall)
    layers = vent_trimmed(wall, catlin_plan.library.resolve_assembly(wall.assembly))
    layers = [ly for ly in layers if ly.name != drop]
    y_mid = (wall.axis[0][1] + wall.axis[1][1]) / 2
    return pipe_plane_profile(wall, layers, catlin_plan.library, (x_in * INCH, y_mid), 0.7,
                              outward, LAV_RADIUS_M, 70.0, -15.0)


def test_w_m_w1_stack_matches_the_hand_worked_note(catlin_model_ro, catlin_plan):
    lav = _w1_profile(catlin_model_ro, catlin_plan)
    assert lav.temperature_f == pytest.approx(51.94, abs=0.02)  # note §3
    assert lav.inboard_r == pytest.approx(10.4258, abs=1e-3)
    assert lav.outboard_r == pytest.approx(38.6459, abs=1e-3)
    assert lav.depth_in == pytest.approx(2.8125, abs=1e-3)
    # Note §4: centreline 0.8125" off the sheathing puts the outboard face on it.
    on_sheathing = _w1_profile(catlin_model_ro, catlin_plan, x_in=0.5 + 0.3125)
    assert on_sheathing.temperature_f == pytest.approx(31.51, abs=0.02)
    # Note §5: no ccSPF.
    bare = _w1_profile(catlin_model_ro, catlin_plan, drop="spray-foam")
    assert bare.temperature_f == pytest.approx(31.59, abs=0.02)
    assert bare.continuous_r == 0.0 and lav.continuous_r == pytest.approx(26.0, abs=1e-6)


def test_catlin_lav_runs_pass_and_hydrants_are_not_graded(catlin_ctx):
    findings = sf.supply_freeze_exposure(catlin_ctx)
    by_run = {f.element_tags[0]: f for f in findings}
    assert {"PR-M-BATH2-LAV-CW", "PR-M-BATH2-LAV-HW"} <= set(by_run)
    assert not any("HYD" in tag for tag in by_run)
    assert all(f.result is Result.PASS for f in findings), [f.message for f in findings]
    assert "not a code requirement" in by_run["PR-M-BATH2-LAV-CW"].message
    assert "51.9 F" in by_run["PR-M-BATH2-LAV-CW"].message


def test_no_exterior_cavity_length_is_not_applicable(catlin_ctx, monkeypatch):
    monkeypatch.setattr(sf, "_exterior_framed_walls", lambda ctx: [])
    [finding] = sf.supply_freeze_exposure(catlin_ctx)
    assert finding.result is Result.NOT_APPLICABLE


def _reading(profile, protection=None):
    return sf._Reading("PR-X", "W-X", "EXT", 1.0, profile, protection)


def _profile(temperature, continuous=26.0, missing=()):
    return Profile(temperature, 10.0, 38.0, continuous, "4\" foam", 2.8, (), tuple(missing))


def test_grading_flags_cold_bare_and_unknown_layers():
    line = FreezeAdvisory().threshold_f
    assert line == 42.0
    assert sf._grade(_reading(_profile(line + 0.1)), "").result is Result.PASS
    cold = sf._grade(_reading(_profile(line - 0.1)), "")
    assert cold.result is Result.FAIL and "within 10 F of freezing" in cold.message
    frozen = sf._grade(_reading(_profile(31.0)), "")
    assert "below freezing" in frozen.message
    bare = sf._grade(_reading(_profile(60.0, continuous=0.0)), "")
    assert bare.result is Result.FAIL and "no continuous insulation" in bare.message
    assert sf._grade(_reading(_profile(60.0, missing=("x",))), "").result is Result.UNKNOWN
    traced = sf._grade(_reading(_profile(31.0), "heat trace"), "")
    assert traced.result is Result.PASS and "heat trace" in traced.message
