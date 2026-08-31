"""``structural.door_framing_module`` — doors on their host wall's stud grid.

The check that ``window_module.py`` deliberately does not do. These tests pin the three
things that make it a different check rather than the same loop with the door filter removed:
what it must NOT inherit (the RO ladder), the one criterion it grades on, and the UNKNOWN
branch that keeps it honest about walls no move can fix.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Preferences, Tier, registered
from typehaus.findings import Result, Severity

_IN_M = 0.0254
_CID = "structural.door_framing_module"


@pytest.fixture(scope="module")
def findings(catlin_model):
    """Run WITHOUT the house's preferences, so its decided-advisory suppression is not in
    play — these tests are about what the check says, not about what catlin does with it."""
    report = run_from_model(catlin_model, [], preferences=Preferences())
    return [f for f in report.findings if f.check_id == _CID]


def test_the_check_is_registered():
    """A module missing from ``checks/structural/__init__.py`` registers nothing and every
    other test here still passes, because a check that never runs emits no findings."""
    assert _CID in {cid for cid, _ in registered(Tier.STRUCTURAL)}


def test_it_is_advisory_and_not_a_code_check(findings):
    """WARN severity paired with a FAIL result — the window check's shape. No IRC section
    requires an opening on a stud module, so there is no ``code_ref`` to carry and nothing
    for ``test_permit_coverage.py`` to demand a ``PermitItemSpec`` for."""
    assert findings
    assert all(f.severity is Severity.WARN for f in findings)
    assert all(f.code_ref is None for f in findings)


def test_it_grades_doors_and_bare_openings_and_nothing_else(catlin_model, findings):
    graded = {tag for f in findings for tag in f.element_tags}
    openings = {o.tag: o for o in catlin_model.openings}
    for tag in graded & set(openings):
        opening = openings[tag]
        assert opening.is_door or opening.type_ref is None, tag
    # ``type_ref is None`` is the clause that reaches D-S-STUDY2, a cased RoughOpening with
    # no leaf. It frames exactly like a door and the window check skips it too.
    assert "D-S-STUDY2" in graded


def test_the_ro_ladder_is_not_applied_to_doors(findings):
    """**The reason this is a second file.** ``window_module._ro_caps`` caps an opening's
    WIDTH at 27"/30". Run catlin's doors through it and four of them — ``D-M-PANTRY`` (60"),
    ``D-B-PLAY`` (60"), ``D-B-PATIO`` (60") and ``D-G-OVERHEAD`` (192", with a named
    engineered header) — report as over the limit. Those are four findings the house must not
    act on: nobody narrows a garage door to fit a stud module.

    So no finding here may mention a width limit, and the wide doors are graded on position
    like every other."""
    for finding in findings:
        assert "exceeds" not in finding.message
        assert "limit" not in finding.message
    named = {tag for f in findings for tag in f.element_tags}
    # D-G-OVERHEAD is graded — on POSITION, and it is the only one of the four wide doors
    # that is off its module at all.
    assert "D-G-OVERHEAD" in named
    assert {"D-B-PLAY", "D-B-PATIO"}.isdisjoint(named)


def test_the_criterion_is_studs_cut_not_distance_from_ideal(catlin_model, findings):
    """Narrower than the window check's, deliberately. An opening whose ``interrupted``
    already equals its ``minimum_interrupted`` is in the cheapest bay configuration its width
    allows; being an inch off the "ideal" centre costs nothing then, and saying so would be
    noise. ``D-B-BATH`` is the case — 1.9" off its module and cutting four studs where four
    is the minimum for a 32" leaf on an 8" staggered rhythm."""
    from typehaus.checks.structural._stud_grid import (
        module_origin,
        structure_framing,
        wall_module,
    )
    from typehaus.resolve.framing.stud_module import opening_stud_module
    from typehaus.resolve.framing.tables import member_actual

    named = {tag for f in findings for tag in f.element_tags}
    assert "D-B-BATH" not in named
    for opening in catlin_model.openings:
        if not (opening.is_door or opening.type_ref is None):
            continue
        wall = catlin_model.wall(opening.host_wall)
        framing = (structure_framing(catlin_model.plan.library.resolve_assembly(wall.assembly))
                   if wall is not None else None)
        if framing is None:
            continue
        spacing = wall_module(framing, 16.0) * _IN_M
        stud_m = member_actual(framing.member)[0] * _IN_M
        phase, _ = module_origin(_Ctx(catlin_model), wall, framing, spacing)
        module = opening_stud_module(opening.center_along_m, opening.width_m, spacing,
                                     stud_m, phase)
        costs = module.interrupted > module.minimum_interrupted
        assert (opening.tag in named) == costs, opening.tag


class _Ctx:
    """The two attributes ``module_origin`` reads, without building a full CheckContext."""

    def __init__(self, model):
        self.model = model


def test_a_fixable_door_fails_and_is_told_where_to_go(findings):
    """FAIL is the state that means "this is worth doing": a legal station exists, and the
    finding names it. An accusation with no address is not actionable."""
    fails = [f for f in findings if f.result is Result.FAIL]
    assert fails
    overhead = next(f for f in fails if "D-G-OVERHEAD" in f.element_tags)
    # 156" (13'-0") since GARAGE_WALL_2X6 went to 24" o.c. on 2026-08-31 — it was 152" on
    # the 16" grid.
    assert "156" in overhead.fix_hint  # the nearest legal centre, in inches along the wall
    # ...and the offset a plan author actually types, because `from_node` is to the near EDGE.
    assert "near EDGE" in overhead.fix_hint


def test_a_wall_no_move_can_fix_is_unknown_not_fail(findings):
    """The state that keeps the check honest. Six catlin openings sit in walls too short to
    hold their leaf on the module with a jamb pack at each end — ``D-M-ENTRY`` is 36" in a
    48" wall. "Shift the RO" is the wrong instruction there, and a FAIL would send somebody
    looking for a position that does not exist."""
    unknowns = {tag for f in findings if f.result is Result.UNKNOWN
                for tag in f.element_tags}
    assert {"D-M-ENTRY", "D-S-NCLOSET", "D-S-STUDY2", "D-M-PANTRY", "D-S-BED3",
            "D-S-BATH1"} <= unknowns
    for finding in findings:
        if finding.result is not Result.UNKNOWN:
            continue
        assert "NO position on this wall fixes it" in finding.message
        # The three remedies, none of which is moving the opening.
        assert "start/end nodes" in finding.fix_hint
        assert "layout_origin" in finding.fix_hint
        assert "narrower leaf" in finding.fix_hint


def test_catlin_carries_exactly_one_decided_advisory(catlin_model):
    """With the house's own preferences loaded, the report is clean — and it is clean because
    ONE finding is suppressed by tag with its reason written beside it, not because the check
    was silenced. The UNKNOWNs all survive."""
    from typehaus.checks.run import load_preferences

    prefs = load_preferences(Path(catlin_model.plan.source_root))
    report = run_from_model(catlin_model, [], preferences=prefs)
    mine = [f for f in report.findings if f.check_id == _CID]
    assert not [f for f in mine if f.result is Result.FAIL]
    assert [f for f in mine if f.result is Result.UNKNOWN]
    assert "structural.door_framing_module:D-G-OVERHEAD" in prefs.suppressed


# --- the mechanism the decided advisory rides on -------------------------------------------

def test_suppression_by_tag_drops_one_element_and_no_other():
    """``[checks] suppress`` took only whole check ids until 2026-08-30, which made it useless
    for an advisory a house has looked at and decided: silencing the rule to accept one
    finding also throws away every other finding it would ever make.

    ``check.id:ELEMENT-TAG`` accepts the one. It must not reach a second element, and the bare
    form must go on meaning what it always meant."""
    from typehaus.checks.registry import _suppressed
    from typehaus.findings import advisory

    def finding(cid, *tags):
        return advisory(cid, "m", tags, Result.FAIL)

    one = frozenset({"a.rule:X-1"})
    assert _suppressed(finding("a.rule", "X-1"), one)
    assert _suppressed(finding("a.rule", "X-1", "W-9"), one)  # any tag on the finding matches
    assert not _suppressed(finding("a.rule", "X-2"), one)
    assert not _suppressed(finding("b.rule", "X-1"), one)     # scoped to its own check
    # The whole-check form is unchanged.
    assert _suppressed(finding("a.rule", "X-2"), frozenset({"a.rule"}))


def test_the_house_file_parses_the_tag_form():
    """``load_preferences`` passes the strings through untouched, so a `:`-form entry in
    ``preferences.toml`` reaches the registry as written."""
    from typehaus.checks.run import load_preferences

    prefs = load_preferences(Path("houses/catlin"))
    assert any(":" in entry for entry in prefs.suppressed)
    # Nothing in this house silences a whole check.
    assert all(":" in entry for entry in prefs.suppressed), sorted(prefs.suppressed)
