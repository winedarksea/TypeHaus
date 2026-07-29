"""The profile's checklist and the check registry must not drift apart.

Two directions, both of which had already broken:

* a checklist item naming a check id that does not exist evaluates to UNKNOWN forever and
  looks like a modelling gap rather than a typo;
* a registered CODE-tier check that no item references is silently uncovered — which is
  exactly what happened to ``code.R401_3_grading`` and ``code.R401_3_impervious``, both
  registered, both claimed by the coverage statement, neither on the checklist.

Coverage is scraped by *importing* the check package, not by grepping: ``condensation.py``
registers its check through a module constant, so a text search misses it.
"""

from __future__ import annotations

import pytest

import typehaus.checks  # noqa: F401  - importing the package registers every check
from typehaus.checks.code.mn_residential.profile import (
    DEFAULT_PROFILE_NAME,
    PROFILES,
    UnknownProfile,
    get_profile,
)
from typehaus.checks.registry import Tier, registered

ALL_PROFILES = sorted(PROFILES.values(), key=lambda p: p.name)


def _registered_ids(tier: Tier | None = None) -> set[str]:
    return {check_id for check_id, _fn in registered(tier)}


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_every_referenced_check_exists(profile) -> None:
    known = _registered_ids()
    missing = sorted(profile.permit_check_ids() - known)
    assert not missing, f"{profile.name} references check ids nothing registers: {missing}"


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_every_code_check_is_covered_or_excluded_with_a_reason(profile) -> None:
    covered = profile.permit_check_ids()
    excluded = {check_id for check_id, _reason in profile.permit_exclusions}
    uncovered = sorted(_registered_ids(Tier.CODE) - covered - excluded)
    assert not uncovered, (
        f"{profile.name}: CODE-tier checks on no permit item and in no exclusion list "
        f"(add a PermitItemSpec, or a permit_exclusions entry saying why): {uncovered}"
    )


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_exclusions_are_real_checks_with_real_reasons(profile) -> None:
    known = _registered_ids()
    for check_id, reason in profile.permit_exclusions:
        assert check_id in known, f"{profile.name} excludes an unregistered check: {check_id}"
        assert len(reason.split()) >= 4, f"{profile.name}: {check_id} needs a real reason"
        assert check_id not in profile.permit_check_ids(), (
            f"{profile.name}: {check_id} is both excluded and on the checklist"
        )


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_checklist_labels_are_unique(profile) -> None:
    labels = [item.label for item in profile.permit_items]
    assert len(labels) == len(set(labels)), labels


def test_r401_3_is_actually_on_the_checklist() -> None:
    """The specific drift this test was written for: both R401.3 checks are registered and
    the coverage statement names lot drainage, but no permit item referenced them."""
    covered = get_profile(DEFAULT_PROFILE_NAME).permit_check_ids()
    assert {"code.R401_3_grading", "code.R401_3_impervious"} <= covered


def test_an_unknown_profile_name_is_refused() -> None:
    """`--profile wi-2024` used to silently evaluate the house against Minnesota."""
    with pytest.raises(UnknownProfile) as exc:
        get_profile("wi-2024")
    assert "mn-2024" in str(exc.value)  # the error lists what this build does define


def test_the_report_records_which_checks_ran(starter_dir) -> None:
    """A check emitting no findings is indistinguishable from one that never ran, so
    `ran` is what any honest coverage claim has to rest on."""
    from typehaus.checks import run
    from typehaus.source import load_plan

    result = load_plan(starter_dir)
    assert result.plan is not None
    report = run(result.plan, starter_dir)
    assert set(report.ran) == _registered_ids()
    assert len(report.ran) == len(set(report.ran))


def test_the_default_profile_states_a_climate_table() -> None:
    """The energy check reads ``profile.climate``; a profile without one must report
    UNKNOWN rather than silently applying Minnesota's numbers."""
    assert get_profile(DEFAULT_PROFILE_NAME).climate is not None
