"""MN 1322 R403.5's whole-house rate, and the air-leakage summary beside it.

Both are the "one pure function, two consumers" shape: the check grades the summary and
G-004/G-005 print it, so a test that the finding is *built from* the summary is what stops
the sheet and the check report drifting apart.
"""

from __future__ import annotations

import pytest

from typehaus.checks.code.mn_energy import _MAX_ACH50, air_leakage_summary
from typehaus.checks.code.mn_residential.ventilation import whole_house_summary
from typehaus.checks.registry import Preferences
from typehaus.findings import Result


def test_the_formula_is_minnesotas_not_ashraes(catlin_model_ro) -> None:
    """MN R403.5 is 0.02 cfm/sf + 15 per (bedroom + 1). ASHRAE 62.2's 0.03 + 7.5 lands
    within a few cfm on this house, which is exactly why the wrong one survived so long."""
    summary = whole_house_summary(catlin_model_ro, catlin_model_ro.plan)
    assert summary is not None
    expected = 0.02 * summary.conditioned_area_ft2 + 15.0 * (summary.bedrooms + 1)
    assert summary.total_rate_cfm == pytest.approx(expected)


def test_the_continuous_rate_is_half_the_total_with_a_forty_cfm_floor(catlin_model_ro) -> None:
    summary = whole_house_summary(catlin_model_ro, catlin_model_ro.plan)
    assert summary is not None
    assert summary.continuous_rate_cfm == pytest.approx(
        max(summary.total_rate_cfm / 2.0, 40.0))
    assert summary.continuous_rate_cfm >= 40.0


def test_catlin_still_passes_on_the_minnesota_formula(catlin_model_ro) -> None:
    """The ERV's headroom is the reason to watch this: 210 cfm provided, and the switch
    from 62.2 raised the requirement rather than lowering it."""
    summary = whole_house_summary(catlin_model_ro, catlin_model_ro.plan)
    assert summary is not None
    assert summary.provided_cfm == pytest.approx(210.0)
    assert summary.provided_cfm >= summary.total_rate_cfm


def test_the_finding_prints_the_summarys_numbers(catlin_model_ro) -> None:
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    summary = whole_house_summary(catlin_model_ro, catlin_model_ro.plan)
    assert summary is not None
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE)
    matched = [f for f in report.findings
               if f.check_id == "code.N1103_6_whole_house_ventilation"]
    assert matched and all(f.result is Result.PASS for f in matched)
    assert f"{summary.total_rate_cfm:.0f} cfm total" in matched[0].message
    assert f"{summary.continuous_rate_cfm:.0f} cfm continuous" in matched[0].message
    # Minnesota's own rule, not the IRC article this check id is still spelled after.
    assert matched[0].code_ref == "MN 1322 R403.5"


def test_an_unrated_unit_is_a_different_gap_from_no_unit(catlin_model_ro) -> None:
    """"Nothing installed" and "installed, unrated" are both UNKNOWN, and only one of them
    is a datasheet away from an answer — so ``reason`` has to tell them apart."""
    plan = catlin_model_ro.plan
    stripped = tuple(t.model_copy(update={"ventilation_cfm": None})
                     for t in plan.library.equipment_types)
    library = plan.library.model_copy(update={"equipment_types": stripped})
    summary = whole_house_summary(catlin_model_ro, plan.model_copy(update={"library": library}))
    assert summary is not None
    assert summary.provided_cfm is None
    assert summary.unrated_tags and "ventilation_cfm" in (summary.reason or "")


def test_air_leakage_summary_exposes_the_target_the_sheet_has_to_print() -> None:
    assert _MAX_ACH50 == 3.0
    assert air_leakage_summary(Preferences(ach50=1.0)).result is Result.PASS
    assert air_leakage_summary(Preferences(ach50=1.0)).max_ach50 == 3.0
    assert air_leakage_summary(Preferences(ach50=4.0)).result is Result.FAIL
    assert air_leakage_summary(Preferences()).result is Result.UNKNOWN


def test_a_cfm50_with_no_ach50_is_not_converted() -> None:
    """A blower-door number is a measurement. Dividing it by a volume this engine does not
    resolve would quietly turn it into an estimate."""
    summary = air_leakage_summary(Preferences(cfm50=1200.0))
    assert summary.result is Result.UNKNOWN
    assert summary.ach50 is None and summary.cfm50 == 1200.0
