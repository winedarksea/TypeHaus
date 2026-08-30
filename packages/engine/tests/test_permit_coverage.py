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

from pathlib import Path

import pytest

import typehaus.checks  # noqa: F401  - importing the package registers every check
from typehaus.checks.code.mn_residential.profile import (
    DEFAULT_PROFILE_NAME,
    PROFILES,
    UnknownProfile,
    get_profile,
)
from typehaus.checks.registry import Tier, registered

REPO = Path(__file__).resolve().parents[3]
CATLIN = REPO / "houses" / "catlin"
STARTER = REPO / "houses" / "starter"

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
# 21 -> 23 on 2026-08-02 for ESS (R327) and PV (NEC 705.12 / 690.12); 23 -> 24 on
# 2026-08-22 for the thermal barrier (R316.4); 24 -> 25 on 2026-08-25 for the ERV
# terminations (M1602.2). Three of those four rises shared one reason, recorded at length
# at the time: the rule is about equipment a house may simply not have, the check no-op'd
# when the equipment was absent, and an item with no matched findings resolves to UNKNOWN —
# so gating them would have failed the permit for every house without a battery on the wall.
#
# 25 -> 21 on 2026-08-30. That reason was real and is now gone, and it is gone structurally
# rather than by grinding: `Result.NOT_APPLICABLE` lets a check say "this house places no
# balanced ventilator" as a *verdict* instead of a silence, `_item_from_findings` resolves
# an all-N/A line to N/A, and `PermitChecklist.ok` treats N/A as nothing outstanding. The
# ESS, PV, ERV and structural-glass-guard items now gate, and both reference houses pass:
# catlin evaluates all four for real, starter answers N/A to all four.
#
# The thermal barrier (R316.4) stays staged, and its reason is untouched by any of this:
# it answers UNKNOWN for a PVC liner and a wood structural panel because the catalog has no
# field to classify them. That is a missing datum, not a missing barrier — a real gap, and
# exactly the thing N/A must never be used to paper over. Flipping it still needs the
# wood-structural-panel field first.
MAX_NON_BLOCKING_ITEMS = {"mn-2024": 21}

# The engineered lines (2026-08-30) are counted separately, and the split is not
# bookkeeping — the two lanes have different exit conditions. A staging item leaves its
# lane when *this engine* learns to answer the rule, which is work in this repo. An
# engineered item leaves its lane when a licensed professional signs a drawing, which is
# work no amount of code can do. Pooling them would let either one hide behind the other's
# excuse, and would have made this commit — which shrank the staging lane from 25 to 21 —
# look like it grew it back to 25.
#
# Both pins are ratchets. Lower one when an item flips; raising either needs a reason.
#
# 4 -> 6 on 2026-08-30, and the reason is a net honesty gain rather than a slip: "Uplift
# connection capacity" and "Deck equipment anchorage capacity" are what 61 coverage-only
# UNKNOWNs collapsed INTO. Those rules now pass under names that say what they grade, and
# the capacity question they used to carry as a trailing disclaimer is two named items a
# seal has to cover. Two rows a reviewer must act on beats 61 they scroll past.
MAX_UNSEALED_ITEMS = {"mn-2024": 6}


def _engineered_labels(profile) -> set[str]:
    """Which of this profile's items the *reference house* answers by engineered design.

    Derived from catlin rather than declared on PermitItemSpec, deliberately: whether a
    requirement is engineered is a property of a house's geometry — 10 feet of unbalanced
    fill here, 3 feet next door — so a jurisdiction profile cannot know it in advance.
    """
    from typehaus.checks import evaluate_permit_checklist, run
    from typehaus.source import load_plan

    result = load_plan(CATLIN)
    assert result.plan is not None
    checklist = evaluate_permit_checklist(run(result.plan, CATLIN, profile=profile.name),
                                          profile)
    return {item.label for item in checklist.engineered}


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_the_non_gating_lane_only_shrinks(profile) -> None:
    engineered = _engineered_labels(profile)
    staged = [item.label for item in profile.permit_items
              if not item.blocking and item.label not in engineered]
    limit = MAX_NON_BLOCKING_ITEMS[profile.name]
    assert len(staged) <= limit, (
        f"{profile.name} has {len(staged)} non-gating permit items (limit {limit}): "
        f"{staged}. Flip one to blocking, or state why the limit rises."
    )


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
def test_the_unsealed_lane_only_shrinks(profile) -> None:
    """Engineered items awaiting a calculation or a seal — a ratchet, like the lane above.

    Each of the four leaves this lane in the commit that registers its calculation in
    `typehaus/engineering/`, at which point it can gate at draft. `haus engineering` is
    the worklist.
    """
    unsealed = sorted(_engineered_labels(profile))
    limit = MAX_UNSEALED_ITEMS[profile.name]
    assert len(unsealed) <= limit, (
        f"{profile.name} has {len(unsealed)} engineered permit items awaiting a "
        f"calculation or a seal (limit {limit}): {unsealed}."
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


# --- engineered coverage ---------------------------------------------------------------
#
# The static coverage test above is scoped to Tier.CODE, which is why five engineered
# requirements — a 10' cantilever retaining wall, two round columns on belled piers, an
# I-joist rafter, a trussed garage roof — sat on no permit line at all until 2026-08-30. A
# reviewer reading the checklist could not see that they were carrying the submittal.
#
# This test closes that hole *dynamically*, because it has to be: whether a requirement is
# engineered is a property of a particular house's geometry (10 feet of unbalanced fill
# here, 3 feet next door), so no static scrape of the registry can answer it. It runs both
# reference houses and demands that every finding claiming Authority.ENGINEERED is on a
# permit item or explicitly excluded with a reason.

@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
@pytest.mark.parametrize("house", ["catlin", "starter"])
def test_every_engineered_finding_is_on_a_permit_item(profile, house) -> None:
    from typehaus.checks import run
    from typehaus.findings import Authority
    from typehaus.source import load_plan

    directory = CATLIN if house == "catlin" else STARTER
    result = load_plan(directory)
    assert result.plan is not None
    report = run(result.plan, directory, profile=profile.name)

    covered = profile.permit_check_ids()
    excluded = {check_id for check_id, _reason in profile.permit_exclusions}
    orphans = sorted({finding.check_id for finding in report.findings
                      if finding.authority is Authority.ENGINEERED
                      and finding.check_id not in covered
                      and finding.check_id not in excluded})
    assert not orphans, (
        f"{profile.name}/{house}: these checks report findings that rest on engineered "
        f"design, and they are on no permit item and in no exclusion list. Engineered work "
        f"a reviewer cannot see on the checklist is the exact drift this file exists to "
        f"stop: {orphans}"
    )


@pytest.mark.parametrize("profile", ALL_PROFILES, ids=lambda p: p.name)
@pytest.mark.parametrize("house", ["catlin", "starter"])
def test_every_engineered_finding_names_an_item_a_signoff_could_cover(profile, house) -> None:
    """An ENGINEERED verdict with no item id is the old prose handoff wearing a new label.

    The whole gain of the register is that the outstanding work has a *name* — an id in
    ``<kind>/<element-tag>`` form that ``engineering.toml`` can put a seal over. A finding
    that claims the authority and names nothing gives a reader no more than the paragraph
    it replaced.
    """
    from typehaus.checks import run
    from typehaus.findings import Authority
    from typehaus.source import load_plan

    directory = CATLIN if house == "catlin" else STARTER
    result = load_plan(directory)
    assert result.plan is not None
    report = run(result.plan, directory, profile=profile.name)

    nameless = [finding.check_id for finding in report.findings
                if finding.authority is Authority.ENGINEERED and not finding.engineering_item]
    assert not nameless, nameless

    malformed = [finding.engineering_item for finding in report.findings
                 if finding.engineering_item
                 and finding.engineering_item.count("/") != 1]
    assert not malformed, malformed
