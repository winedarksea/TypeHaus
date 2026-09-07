"""``mep.pocket_occupancy`` — a pocket is a hole in a wall, not a hole in a storey.

The check tested plan geometry alone, which is right for the thing it was written for (a
box or a pipe inside the leaf's travel) and wrong one floor up: ``D-M-LAUN``'s pocket runs
under the suite bathroom, so a second-storey lavatory branch in the floor trusses 32" over
the leaf read as occupying it. The elevation band is what separates the two.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.mep.pockets import _POCKET_HEAD_TRACK_M, _pocket_bands
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE)
    return [f for f in report.findings if f.check_id == "mep.pocket_occupancy"]


def test_the_check_is_registered() -> None:
    assert "mep.pocket_occupancy" in {cid for cid, _ in registered(Tier.CODE)}


def test_catlin_has_nothing_in_a_pocket(findings) -> None:
    assert findings
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]


def test_the_band_stops_just_above_the_leaf(catlin_model_ro) -> None:
    """The z band is the leaf's own travel, not the wall. ``D-M-LAUN`` is an 80" door on a
    wall based at the main floor, so the cavity ends a head track over 80" — not at
    ``W-M-HS4``'s 120" top, which is where a wall-shaped band would put it."""
    class _Ctx:
        model = catlin_model_ro
        plan = catlin_model_ro.plan

    bands = {(op.tag, wall): (low, high)
             for op, wall, _poly, (low, high) in _pocket_bands(_Ctx())}
    low, high = bands[("D-M-LAUN", "W-M-HS4")]
    assert low == pytest.approx(0.0, abs=1e-9)
    assert high == pytest.approx(80 * 0.0254 + _POCKET_HEAD_TRACK_M, abs=1e-9)


def test_a_pipe_over_the_head_track_is_not_in_the_pocket(catlin_model) -> None:
    """``PR-M-S-SUITE-LAV-DRAIN`` crosses ``D-M-LAUN``'s pocket squarely in plan and clears
    it by 32" in elevation. Drop that run to the leaf's own height and the finding comes
    back — same plan geometry, so it is the z term and nothing else deciding it."""
    original = next(r for r in catlin_model.pipe_runs
                    if r.tag == "PR-M-S-SUITE-LAV-DRAIN")
    assert not _fails(catlin_model)

    dropped = dataclasses.replace(original, z_m=tuple(40 * 0.0254 for _ in original.z_m))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(dropped if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    fails = _fails(model)
    assert [f.element_tags for f in fails] == [("D-M-LAUN", "W-M-HS4",
                                                "PR-M-S-SUITE-LAV-DRAIN")]


def _fails(model):
    return [f for f in run_from_model(model, [], tier=Tier.CODE).findings
            if f.check_id == "mep.pocket_occupancy" and f.result is Result.FAIL]
