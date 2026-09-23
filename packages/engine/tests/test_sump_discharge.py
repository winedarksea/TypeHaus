"""A pumped sump's discharge line: its own ``PipeSystem``, graded by ``drainage.pump_discharge``.

Stub contexts over catlin's real ``SM-B-RADON`` and ``TR-RF-LEADER-W``: a line leaves the pit,
rises to a high point, and falls to a wye on the leader's extension riser.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from typehaus.checks.mep.sump_discharge import pump_discharge
from typehaus.findings import Result
from typehaus.model.enums import PipeSystem
from typehaus.resolve.model import ResolvedPipeRun, ResolvedSolid

_IN = 0.0254
_FT = 0.3048
_PIT_XY = (1.0 * _FT, 34.5 * _FT)
_LEADER_XY = (-10.583 * _IN, 35.5 * _FT)   # TR-RF-LEADER-W; its riser spans -40" to +12"


def _line(system="sump_discharge", z=(-100.0, -21.0, -21.5, -22.0), end=_LEADER_XY):
    path = [_PIT_XY, (_PIT_XY[0], end[1]), (0.5 * _FT, end[1]), end]
    zs = tuple(v * _IN for v in z)
    return ResolvedPipeRun(uid="TSTSD00001", tag="PR-TEST-DISCH", storey="basement",
                           system=system, path=path, diameter_m=1.5 * _IN,
                           z_start_m=zs[0], z_end_m=zs[-1], length_m=3.0, z_m=zs)


def _ctx(catlin_plan, *, line=None, **pump):
    sump = catlin_plan.by_tag("SM-B-RADON")
    spec = dict(discharge="TR-RF-LEADER-W", discharge_line_ref="PR-TEST-DISCH",
                check_valve=True, freeze_relief=True)
    spec.update(pump)
    sump = sump.model_copy(update={"pump": sump.pump.model_copy(update=spec)})
    leader = catlin_plan.by_tag("TR-RF-LEADER-W")
    elements = {e.tag: e for e in (sump, leader)}
    plan = SimpleNamespace(all_elements=lambda: list(elements.values()),
                           by_tag=elements.get, project=catlin_plan.project)
    r = 9.0 * _IN
    x, y = _PIT_XY
    pit = ResolvedSolid(uid="p", tag="SM-B-RADON", storey="basement", category="sump",
                        outline=[(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)],
                        z0_m=-130 * _IN, z1_m=-105 * _IN)
    model = SimpleNamespace(plan=plan, pipe_runs=[line or _line()], solids=[pit])
    return SimpleNamespace(model=model, profile=SimpleNamespace(frost_depth_in=42.0))


def _fails(findings):
    return [f.message for f in findings if f.result is not Result.PASS]


def test_a_good_line_passes(catlin_plan):
    found = pump_discharge(_ctx(catlin_plan))
    assert not _fails(found) and found[0].result is Result.PASS


def test_a_receiver_with_no_line_is_unknown(catlin_plan):
    found = pump_discharge(_ctx(catlin_plan, discharge_line_ref=None))
    assert [f.result for f in found] == [Result.UNKNOWN]


@pytest.mark.parametrize(("line", "fragment"), [
    (_line(system="drain"), "not a sump_discharge line"),
    (_line(z=(-150.0, -21.0, -21.5, -22.0)), "does not start in"),
    (_line(end=(-4.0 * _FT, 35.5 * _FT)), "ends off TR-RF-LEADER-W"),
    (_line(z=(-100.0, -21.0, -40.0, -60.0)), "off TR-RF-LEADER-W's extension riser"),
    (_line(z=(-100.0, -21.0, -30.0, -25.0)), "re-rises after its high point"),
])
def test_a_line_that_does_not_do_its_job_fails(catlin_plan, line, fragment):
    assert any(fragment in m for m in _fails(pump_discharge(_ctx(catlin_plan, line=line))))


def test_no_check_valve_fails(catlin_plan):
    assert any("no check valve" in m
               for m in _fails(pump_discharge(_ctx(catlin_plan, check_valve=False))))


def test_a_shallow_receiver_without_freeze_relief_is_unknown(catlin_plan):
    found = pump_discharge(_ctx(catlin_plan, freeze_relief=False))
    assert [f.result for f in found] == [Result.UNKNOWN]
    assert "frost depth" in found[0].message


def test_dwv_rules_never_see_a_sump_discharge_line(catlin_model):
    """Every DWV rule filters on "drain"; a new system is outside them by construction."""
    from _helpers import check_context

    from typehaus.checks.mep import (
        drain_geometry,
        drain_inlet_spacing,
        drain_tie_in,
        plumbing_dwv,
    )
    from typehaus.checks.registry import registered

    model = copy.copy(catlin_model)
    model.pipe_runs = [*catlin_model.pipe_runs, _line()]
    ctx = check_context(model=model)
    modules = {m.__name__ for m in (drain_geometry, drain_inlet_spacing, drain_tie_in,
                                    plumbing_dwv)}
    ran = 0
    for check_id, fn in registered():
        if fn.__module__ not in modules:
            continue
        ran += 1
        for finding in fn(ctx):
            assert "PR-TEST-DISCH" not in finding.element_tags, check_id
            assert "PR-TEST-DISCH" not in finding.message, check_id
    assert ran >= 5
    assert PipeSystem.SUMP_DISCHARGE.value == "sump_discharge"


def test_the_line_files_under_stormwater_in_ifc():
    from typehaus.emit.ifc.mep import _PIPE_SYSTEM_TYPES, STORMWATER_PIPE_SYSTEM

    assert STORMWATER_PIPE_SYSTEM == PipeSystem.SUMP_DISCHARGE.value
    assert STORMWATER_PIPE_SYSTEM not in _PIPE_SYSTEM_TYPES, "no second system"
