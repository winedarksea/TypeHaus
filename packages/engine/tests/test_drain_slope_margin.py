"""``mep.drain_slope_margin`` — how much grade a drain holds OVER the minimum.

``mep.drain_slope`` answers yes/no. A run at exactly 0.250"/ft passes it as cleanly as one
at 0.779"/ft, and the two are not the same building: the field method is rigid standoffs
stepped about an inch every four feet, and the trade's tolerance runs one way, toward more
pitch. BLD-05's finding #2 is exactly that, and the model could not state it.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN, check_context

from typehaus.checks.mep.drain_geometry import drain_slope_margin
from typehaus.checks.registry import MepPreferences, Preferences
from typehaus.findings import Result, Severity

_CID = "mep.drain_slope_margin"


def _run(plan, model, margin: float | None = None):
    """``margin=None`` means catlin's OWN preferences.toml — the house authors 0.0 there,
    and reading the file is the only way this test can assert that it does."""
    from typehaus.checks.run import load_preferences

    preferences = (load_preferences(CATLIN) if margin is None
                   else Preferences(mep=MepPreferences(
                       min_drain_slope_margin_in_per_ft=margin)))
    return drain_slope_margin(check_context(plan=plan, model=model,
                                            preferences=preferences))


def _margin_of(findings, tag) -> float:
    message = next(f for f in findings if tag in f.element_tags).message
    return float(message.split('/ft at its flattest')[1].split(', ')[1].split('"')[0])


def test_the_engine_default_is_a_sixteenth(catlin_plan, catlin_model_ro) -> None:
    """A quarter inch spread over the four feet a standoff is stepped at — and **not a code
    number**, which is the whole reason it is a preference."""
    assert MepPreferences().min_drain_slope_margin_in_per_ft == 0.0625
    fails = [f for f in _run(catlin_plan, catlin_model_ro, 0.0625)
             if f.result is Result.FAIL]
    # 12 since PR-SG-ARCH-OVERFLOW retired with the court overflow's move (2026-09-23).
    assert len(fails) == 12
    assert all(f.severity is Severity.WARN for f in fails), "ADVISORY, not a permit blocker"


def test_catlin_authors_zero_and_is_clean(catlin_plan, catlin_model_ro) -> None:
    """The house's own number, with the argument in ``preferences.toml`` beside it: the
    basement head budget is spent and there is nothing to buy the margin with."""
    from typehaus.checks.run import load_preferences

    assert load_preferences(CATLIN).mep.min_drain_slope_margin_in_per_ft == 0.0
    findings = _run(catlin_plan, catlin_model_ro)
    assert not [f for f in findings if f.result is Result.FAIL]
    assert findings


def test_the_margin_prints_on_pass_too(catlin_plan, catlin_model_ro) -> None:
    """**Most of this check's value.** "0.779"/ft, +0.529"/ft over the minimum" is the fact
    BLD-05 needed and could not get; a check that only spoke when unhappy would leave
    catlin's twelve thin runs as invisible as they were."""
    findings = _run(catlin_plan, catlin_model_ro)
    suite = next(f for f in findings if "PR-M-S-SUITE-WC-DRAIN" in f.element_tags)
    assert suite.result is Result.PASS
    assert '0.779"/ft' in suite.message
    assert '+0.529"/ft over' in suite.message


def test_pr_b_bath_drain_is_the_run_bld05_was_reaching_for(
        catlin_plan, catlin_model_ro) -> None:
    """Exactly the code minimum, zero in hand, buried under a slab — and the loosest of the
    thin set is the run BLD-05 actually named."""
    findings = _run(catlin_plan, catlin_model_ro)
    assert _margin_of(findings, "PR-B-BATH-DRAIN") == pytest.approx(0.0, abs=1e-9)
    assert _margin_of(findings, "PR-M-S-SUITE-WC-DRAIN") > 0.5


def test_it_never_restates_the_code_minimum(catlin_plan, catlin_model_ro) -> None:
    """The minimum comes from ``resolve/mep_slope.py``, the same owner ``mep.drain_slope``
    and ``routing/gravity`` read — so the three cannot disagree about what a run is being
    measured against."""
    import inspect

    from typehaus.checks.mep import drain_geometry
    from typehaus.resolve.mep_slope import minimum_drain_slope_in_per_ft

    function = drain_geometry.drain_slope_margin
    source = inspect.getsource(function)
    assert "minimum_drain_slope_in_per_ft" in source
    # The docstring quotes 0.250"/ft as prose; it is the CODE that must not restate it.
    body = source.replace(function.__doc__ or "", "")
    assert "0.25" not in body, "the minimum must not be hardcoded here"

    findings = _run(catlin_plan, catlin_model_ro)
    minimum = minimum_drain_slope_in_per_ft(0.0762)[0]
    assert f'over the {minimum}"/ft minimum' in findings[0].message


def test_a_run_below_the_minimum_is_left_to_drain_slope(
        catlin_plan, catlin_model_ro) -> None:
    """One defect, one finding. A run that does not hold the grade at all is
    ``mep.drain_slope``'s FAIL, and reporting "its margin is negative" beside it says the
    same thing twice."""
    import copy

    from typehaus.quantities import M_PER_IN

    model = copy.copy(catlin_model_ro)
    runs = list(model.pipe_runs)
    index, child = next((i, r) for i, r in enumerate(runs) if r.tag == "PR-B-BATH-DRAIN")
    flat = copy.copy(child)
    object.__setattr__(flat, "z_m", [*child.z_m[:-1], child.z_m[-2] - 0.001 * M_PER_IN])
    runs[index] = flat
    object.__setattr__(model, "pipe_runs", tuple(runs))

    findings = _run(catlin_plan, model)
    assert not [f for f in findings if "PR-B-BATH-DRAIN" in f.element_tags]


def test_no_drains_is_not_applicable_and_no_gradeable_segment_is_unknown(
        catlin_plan, catlin_model_ro) -> None:
    """N/A is earned from positive evidence of absence; a model that HAS drains and cannot
    measure one is a different, honest, UNKNOWN."""
    import copy

    model = copy.copy(catlin_model_ro)
    object.__setattr__(model, "pipe_runs",
                       tuple(r for r in model.pipe_runs if r.system != "drain"))
    verdict = _run(catlin_plan, model)
    assert len(verdict) == 1 and verdict[0].result is Result.NOT_APPLICABLE

    model = copy.copy(catlin_model_ro)
    stripped = []
    for run in model.pipe_runs:
        if run.system != "drain":
            continue
        blind = copy.copy(run)
        object.__setattr__(blind, "z_m", None)
        stripped.append(blind)
    object.__setattr__(model, "pipe_runs", tuple(stripped))
    verdict = _run(catlin_plan, model)
    assert len(verdict) == 1 and verdict[0].result is Result.UNKNOWN


def test_it_shares_the_vertical_tolerance_with_drain_offset_geometry() -> None:
    """The two must not drift into disagreeing about which segments exist."""
    import inspect

    from typehaus.checks.mep import drain_geometry

    for fn in (drain_geometry.drain_slope_margin,
               drain_geometry.drain_offset_geometry):
        assert "VERTICAL_PLAN_FT" in inspect.getsource(fn)
