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


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_every_code_finding_carries_a_citation(profile, starter_dir) -> None:
    """The profile's stated rigor is that "every rule carries a citation" — until now
    nothing enforced it, and an uncited CODE finding is unreviewable: a plan reviewer cannot
    check an assertion that names no section."""
    from typehaus.checks import run
    from typehaus.source import load_plan

    result = load_plan(starter_dir)
    assert result.plan is not None
    report = run(result.plan, starter_dir, profile=profile.name)
    code_ids = _registered_ids(Tier.CODE)
    uncited = sorted({finding.check_id for finding in report.findings
                      if finding.check_id in code_ids and not finding.code_ref})
    assert not uncited, f"{profile.name}: CODE findings with no code_ref: {uncited}"


# How many checklist items may sit in the non-gating staging lane (PermitItemSpec.blocking).
# Pinned so the lane can only shrink: an item goes non-blocking when its rule is newly
# encoded and the reference house cannot answer it yet, and flips to blocking in the commit
# that makes the house pass. Without a pin, "not yet gating" quietly becomes "never gating".
#
# Lower this number when you flip an item. Raising it needs a reason in the commit message.
#
# 21 -> 23 on 2026-08-02, and the reason is structural rather than "not yet": the two items
# added there — "Energy storage system" (R327) and "PV interconnection and rapid shutdown"
# (NEC 705.12 / 690.12) — are about equipment a house may simply not have. Their checks
# no-op when no ESS and no PV are placed, and an item with no matched findings resolves to
# UNKNOWN. Blocking on them would fail the permit gate for every house without a battery on
# the wall, which is the opposite of what the gate is for. These two stay non-gating by
# nature, not by staging, and flipping them would need a "this house has no ESS" concept
# the checklist does not have.
#
# 23 -> 24 on 2026-08-22 for "Thermal barrier over foam plastic" (R316.4), and the reason is
# the same kind as the two above rather than "not yet": the rule reads AUTHORED ASSEMBLY
# STACKS. It can say the drawn wall puts 5/8" of gypsum between the foam and the room; it
# cannot say the built one does, it does not model R316.5's exceptions, and it reports
# UNKNOWN for any barrier the catalog carries no field to identify — a PVC liner, a wood
# structural panel. Gating a permit on a specification check that answers UNKNOWN for
# materials it simply cannot classify would block houses over a missing datum rather than a
# missing barrier. Flipping it needs the wood-structural-panel field first.
MAX_NON_BLOCKING_ITEMS = {"mn-2024": 24}


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_the_non_gating_lane_only_shrinks(profile) -> None:
    staged = [item.label for item in profile.permit_items if not item.blocking]
    limit = MAX_NON_BLOCKING_ITEMS[profile.name]
    assert len(staged) <= limit, (
        f"{profile.name} has {len(staged)} non-gating permit items (limit {limit}): "
        f"{staged}. Flip one to blocking, or state why the limit rises."
    )


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
