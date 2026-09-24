"""``mep.run_through_stud`` and ``mep.run_through_plate`` on the reference house.

`test_mep_bores.py` pins the rules; this pins the two decisions the CHECKS make on top of
them — which walls are bearing, and what a plate cut past 50% is reported as.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.routing_bores import (
    bearing_wall_tags,
    run_through_plate,
    run_through_stud,
)

pytestmark = pytest.mark.slow


def test_bearing_walls_are_READ_from_the_model_not_guessed_from_exterior(catlin_ctx) -> None:
    """The difference is 25% against 40% of a stud's depth — nearly an inch of pipe on a
    2x6 — so it cannot be inferred. `JoistSpec.bearing_refs` is the model's own statement of
    what carries what."""
    tags = bearing_wall_tags(catlin_ctx)
    assert tags, "this house declares bearing walls"
    assert all(isinstance(tag, str) and tag for tag in tags)
    # Every foundation wall is bearing whatever else the joists name.
    assert {w.tag for w in catlin_ctx.model.walls if w.is_foundation} <= tags


def test_a_plate_cut_past_half_names_the_tie_that_would_permit_it() -> None:
    """R602.6.1 PERMITS the cut with a tie, and the verdict has to say so.

    Catlin carried the one live case — ``PR-B-SAUNA-VENT`` through ``W-B-ESS-S`` — until
    2026-09-23, when the check learned the section's own scope (below), so the mechanism is
    pinned on the verdict itself.
    """
    from typehaus.resolve.mep_bores import top_plate_cut

    untied = top_plate_cut("2x4", 2.375, tie=False)
    assert untied.ok is False and "R602.6.1" in untied.basis
    assert "16 ga" in untied.remedy
    assert top_plate_cut("2x4", 2.375, tie=True).ok is True


def test_R602_6_1_reaches_exterior_and_bearing_walls_only(catlin_ctx) -> None:
    """"An exterior wall or interior load-bearing wall" — a non-bearing partition's plate
    is not the section's business. ``W-M-CLN`` is one, which the suite stack bores since it
    left the master closet."""
    from typehaus.resolve.mep_bores import top_plate_cut

    assert top_plate_cut("2x4", 2.375, tie=False, governed=False).ok is True
    findings = run_through_plate(catlin_ctx)
    assert not [f for f in findings if f.result.value == "fail"]
    for pair in (("PR-M-S-SUITE-DRAIN", "W-M-CLN"),):
        passed = [f for f in findings if f.element_tags == pair]
        assert passed and passed[0].result.value == "pass", pair
        assert "non-bearing partition" in passed[0].message
    openings = [f for f in findings if f.result.value == "unknown"]
    assert openings
    assert all("framed opening" in f.message for f in openings)


def test_catlin_bores_no_stud_past_its_limit_any_more(catlin_ctx) -> None:
    """The wet-wall retype closed every one of them on 2026-09-20.

    Five walls moved: three 2" vent walls and `PR-B-WC2-DRAIN`'s, plus the staggered attic
    wall whose studs were 2x4 on 2x6 plates all along. This is the assertion that keeps them
    closed — an over-bore reappearing here is a regression, not a new finding.
    """
    # Per-member over-bores only: a run standing BESIDE a wall (``wall_cavity``) is a
    # different finding, and catlin carries several since 2026-09-23.
    assert not [f for f in run_through_stud(catlin_ctx)
                if f.result.value == "fail" and "would bore" in f.message]


def test_an_over_size_bore_names_the_member_the_limit_and_the_actual(catlin_ctx) -> None:
    """A builder with a finding needs to know WHICH stud. "The run is tight somewhere" is
    not an instruction.

    Catlin bores nothing past its limit since the retype, so the over-bore is made here:
    `PR-B-WC2-DRAIN` blown up to 4" in the 2x8 that was widened to take it at 3".
    """
    from dataclasses import replace

    model = catlin_ctx.model
    runs = [replace(r, diameter_m=0.1016) if r.tag == "PR-B-WC2-DRAIN" else r
            for r in model.pipe_runs]
    ctx = replace(catlin_ctx, model=replace(model, pipe_runs=tuple(runs)))
    findings = [f for f in run_through_stud(ctx) if f.result.value == "fail"
                and f.element_tags[0] == "PR-B-WC2-DRAIN"]
    assert findings, "a 4\" drain through a 2x8 is over R602.6"
    for finding in findings:
        assert "the worst is" in finding.message
        assert "may not exceed" in finding.message
        assert finding.fix_hint


def test_a_penetration_wider_than_the_stud_is_not_reported_as_an_over_size_bore(
        catlin_ctx) -> None:
    """A 6" duct does not go THROUGH a 2x6; it goes through a framed opening with a header
    over it, and R602.6 governs neither. Reporting it as an over-size bore is arithmetic
    about a hole nobody would drill."""
    findings = run_through_stud(catlin_ctx)
    unknowns = [f for f in findings if f.result.value == "unknown"]
    assert unknowns, "catlin runs 6\", 10\" and 18\" ducts through walls"
    assert all("framed opening" in f.message or "a block rather than a stud" in f.message
               for f in unknowns)


def test_the_conduit_through_the_short_cripple_over_the_gym_door_is_unknown(
        catlin_ctx) -> None:
    """`PR-B-COND` crosses `W-B-CS3`'s 5.75" cripple over the header: 1.05" is well under
    40% of a 2x6, and the depth rule alone read PASS about a hole in a block."""
    [finding] = [f for f in run_through_stud(catlin_ctx)
                 if f.element_tags == ("PR-B-COND", "W-B-CS3")]
    assert finding.result.value == "unknown"
    assert "cripple-head-0-02" in finding.message
    assert '5.75"' in finding.message and "a block rather than a stud" in finding.message


def test_the_sauna_vent_cuts_no_plate_since_its_re_line(catlin_ctx) -> None:
    """It severed W-B-ESS-W's 2x6 plate and cut W-B-ESS-S's 2x4 one 68% until 2026-09-24,
    when it turned north at x=4'-3 1/2" and stopped crossing either wall. Its suppression
    in preferences.toml went with it; this keeps the cut from coming back unseen."""
    mine = [f for f in run_through_plate(catlin_ctx) if "PR-B-SAUNA-VENT" in f.element_tags]
    assert not [f for f in mine if {"W-B-ESS-S", "W-B-ESS-W"} & set(f.element_tags)]
    assert all(f.result.value == "pass" for f in mine), [f.message for f in mine]
