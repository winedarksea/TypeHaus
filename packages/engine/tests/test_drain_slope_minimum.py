"""One owner for the grade a drain must hold, and the code that actually says so.

``routing/gravity.minimum_slope`` and ``mep.drain_slope`` each carried their own copy of
the pair of numbers. A router that disagreed with the verdict about whether a route is
feasible would be worse than either being wrong alone, so ``resolve/mep_slope.py`` owns it
and both read that.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.quantities import inch
from typehaus.resolve.mep_slope import (
    MIN_DRAIN_SLOPE_IN_PER_FT,
    REDUCED_SLOPE_IN_PER_FT,
    REDUCED_SLOPE_MIN_DIAMETER_M,
    minimum_drain_slope_in_per_ft,
    reduced_slope_approval_is_valid,
)

_SIZES_IN = (1.5, 2.0, 3.0, 4.0, 6.0)


def test_router_and_check_never_disagree() -> None:
    """**The anti-drift assertion.** Two modules, one number, at every size that matters."""
    from typehaus.routing.gravity import minimum_slope

    for nominal in _SIZES_IN:
        diameter_m = inch(nominal).meters
        assert minimum_slope(diameter_m) == minimum_drain_slope_in_per_ft(diameter_m)[0], (
            nominal)


def test_the_minimum_is_a_quarter_inch_at_every_size() -> None:
    """UPC 708.0, not IRC P3005.3's two-row table.

    Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33 and P3005 is in chapter 30, so
    the ``> 3" -> 1/8"/ft`` row the engine used to carry has no force in Minnesota. It read
    catlin's 4" main as holding twice its required grade when it is 0.017"/ft over.
    """
    for nominal in _SIZES_IN:
        grade, citation = minimum_drain_slope_in_per_ft(inch(nominal).meters)
        assert grade == MIN_DRAIN_SLOPE_IN_PER_FT == 0.25, nominal
        assert "4714" in citation and "708.0" in citation
        assert "P3005" not in citation


def test_the_reduced_slope_exception_reaches_only_four_inch_and_larger() -> None:
    approval = "Ramsey County plan review PR-2026-118"
    grade, citation = minimum_drain_slope_in_per_ft(inch(4).meters, approval)
    assert grade == REDUCED_SLOPE_IN_PER_FT == 0.125
    # The finding says *approved*, quoting the paper — never *permitted*.
    assert approval in citation
    assert "approved by the building official" in citation
    assert reduced_slope_approval_is_valid(inch(4).meters, approval)

    # Below 4" the exception does not exist, so neither does the reduction.
    assert minimum_drain_slope_in_per_ft(inch(3).meters, approval)[0] == 0.25
    assert not reduced_slope_approval_is_valid(inch(3).meters, approval)
    assert REDUCED_SLOPE_MIN_DIAMETER_M == pytest.approx(inch(4).meters)


def test_no_approval_means_no_reduction() -> None:
    for approval in (None, ""):
        assert minimum_drain_slope_in_per_ft(inch(4).meters, approval)[0] == 0.25
        assert reduced_slope_approval_is_valid(inch(4).meters, approval)


def test_an_approval_on_small_pipe_is_a_drain_slope_fail(catlin_plan) -> None:
    """A FAIL, not an advisory: no official could have approved what the run claims."""
    from typehaus.checks.mep.plumbing_dwv import drain_slope
    from typehaus.findings import Result

    model, _ = _resolved(catlin_plan)
    target = next(r for r in model.pipe_runs
                  if r.system == "drain" and r.diameter_m < REDUCED_SLOPE_MIN_DIAMETER_M)
    object.__setattr__(target, "reduced_slope_approval", "PR-2026-118")
    findings = drain_slope(check_context(plan=catlin_plan, model=model))
    bad = [f for f in findings if target.tag in f.element_tags and f.result is Result.FAIL]
    assert bad, [f.message for f in findings if target.tag in f.element_tags]
    assert "reaches" in bad[0].message and "4" in bad[0].message


def test_drain_slope_emits_a_code_ref(catlin_plan) -> None:
    """``mep.drain_slope`` is ``Tier.CODE`` and carried no ``code_ref`` at all — a latent
    ``test_permit_coverage.py`` failure waiting for a house with drains to reach the
    starter fixture."""
    from typehaus.checks.mep.plumbing_dwv import drain_slope

    model, _ = _resolved(catlin_plan)
    findings = drain_slope(check_context(plan=catlin_plan, model=model))
    assert findings
    for finding in findings:
        assert finding.code_ref, finding.message
        assert "4714" in finding.code_ref


def _resolved(plan):
    from typehaus.resolve import resolve

    return resolve(plan)
