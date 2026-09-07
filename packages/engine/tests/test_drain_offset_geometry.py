"""``mep.drain_offset_geometry`` — a drop drawn as a slant.

The check and the geometry it exists for landed together, so the defect it was written
against is no longer in the house. These tests put it back: ``PR-A-STUBATH-DRAIN`` used to
run from the attic bay straight to the second-storey stack head in one diagonal, falling
114.5" over 4.16 ft of plan. ``mep.drain_slope`` reported it PASS — it grades the *flattest*
segment, and 27.5"/ft is not flat.

What is worth pinning is the conjunction. Slope alone fails a legitimate 45-degree offset;
fall alone fails a long branch at a steepish grade. Only both together say "this is a stack
and a branch drawn as one line".
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result
from typehaus.model import ft
from typehaus.quantities import M_PER_IN


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE)
    return [f for f in report.findings if f.check_id == "mep.drain_offset_geometry"]


def test_the_check_is_actually_registered() -> None:
    """**The trap.** ``drain_geometry.py`` has to be named in ``checks/mep/__init__.py``'s
    import list. A module nothing imports registers nothing, emits nothing, and every other
    test in this file still passes — a check that never runs produces no findings, which is
    indistinguishable from a check that found none."""
    assert "mep.drain_offset_geometry" in {cid for cid, _ in registered(Tier.CODE)}


def test_catlin_has_no_drain_segment_drawn_as_a_diagonal(findings) -> None:
    """The gate, and the state the 4a fix put the house in."""
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]
    assert [f.result for f in findings] == [Result.PASS]


def _regressed(model, run_tag: str, path, z):
    original = next(run for run in model.pipe_runs if run.tag == run_tag)
    replaced = dataclasses.replace(original, path=path, z_m=z)
    return dataclasses.replace(
        model,
        pipe_runs=tuple(replaced if run.tag == run_tag else run
                        for run in model.pipe_runs))


def _fails(model):
    return [f for f in run_from_model(model, [], tier=Tier.CODE).findings
            if f.check_id == "mep.drain_offset_geometry" and f.result is Result.FAIL]


def test_it_catches_the_dog_leg_it_was_written_for(catlin_model) -> None:
    """The original three-point ``PR-A-STUBATH-DRAIN``: attic bay straight to the stack head.

    114.5" of fall over 4.16 ft of plan. Both terms are exceeded by a factor of six, which
    is the margin that makes the two thresholds defensible rather than tuned."""
    model = _regressed(
        catlin_model, "PR-A-STUBATH-DRAIN",
        ((ft(11, 0.875).meters, ft(19, 4).meters),
         (ft(9, 7.5).meters, ft(19, 4).meters),
         (ft(13).meters, ft(16, 10.8).meters)),
        (ft(19, 4).meters, ft(19, 3.5).meters, ft(9, 9).meters))
    fails = _fails(model)
    assert len(fails) == 1, [f.message for f in fails]
    assert "PR-A-STUBATH-DRAIN" in fails[0].element_tags
    assert "segment 1" in fails[0].message
    assert "114.5\"" in fails[0].message and "27.5\"/ft" in fails[0].message


def test_a_steep_but_short_offset_passes(catlin_model) -> None:
    """A 45-degree fitting is exactly 12"/ft, and catlin's own steepest honest segment
    (``PR-M-DRYER-COND``, 15.2"/ft) is steeper than that. Slope alone would fail both.

    Here the same run drops 12" over 6" of plan — 24"/ft, twice the slope threshold — and
    passes, because 12" of fall is a fitting somebody stocks."""
    a = (ft(9, 7.5).meters, ft(19, 4).meters)
    b = (a[0] + 0.5 / 3.280839895013123, a[1])
    model = _regressed(catlin_model, "PR-A-STUBATH-DRAIN", (a, b),
                       (ft(10).meters, ft(10).meters - 12 * M_PER_IN))
    assert not _fails(model)


def test_a_long_branch_with_a_big_total_fall_passes(catlin_model) -> None:
    """The other half of the conjunction. Forty feet at 1/2"/ft descends 20" — past the fall
    threshold — and every foot of it is buildable, so fall alone would be a false positive."""
    a = (ft(9, 7.5).meters, ft(19, 4).meters)
    b = (a[0] + 40.0 / 3.280839895013123, a[1])
    model = _regressed(catlin_model, "PR-A-STUBATH-DRAIN", (a, b),
                       (ft(10).meters, ft(10).meters - 20 * M_PER_IN))
    assert not _fails(model)


def test_a_vertical_drop_is_exempt(catlin_model) -> None:
    """A stack falls its whole height at infinite slope and is not an offset at all. The
    exemption shares ``VERTICAL_PLAN_FT`` with ``mep.drain_slope`` so the two rules cannot
    disagree about which segments exist."""
    a = (ft(9, 7.5).meters, ft(19, 4).meters)
    model = _regressed(catlin_model, "PR-A-STUBATH-DRAIN", (a, a),
                       (ft(19, 3.5).meters, ft(9, 8.75).meters))
    assert not _fails(model)
