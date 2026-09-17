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


def test_a_plate_cut_past_half_is_UNKNOWN_and_carries_the_tie_as_its_remedy(
        catlin_ctx) -> None:
    """R602.6.1 PERMITS the cut with a tie, and this model has no vocabulary for a plate
    tie at all — so its absence is not evidence of absence. That is what UNKNOWN means
    here, and the message says what the detail is."""
    findings = run_through_plate(catlin_ctx)
    unknowns = [f for f in findings if f.result.value == "unknown"]
    assert unknowns
    assert all("16 ga" in f.message for f in unknowns)
    assert not [f for f in findings if f.result.value == "fail"]


def test_an_over_size_bore_names_the_member_the_limit_and_the_actual(catlin_ctx) -> None:
    """A builder with a finding needs to know WHICH stud. "The run is tight somewhere" is
    not an instruction."""
    findings = [f for f in run_through_stud(catlin_ctx) if f.result.value == "fail"]
    assert findings, "catlin has real over-bores; see preferences.toml"
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
    assert all("framed opening" in f.message for f in unknowns)
