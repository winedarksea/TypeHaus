"""`houses/catlin/notes/framing_bore_limits.md`, reproduced numerically.

Every number here is read off the note, and the note was worked from the code text and this
house's own resolved members before the predicates existed.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.mep_bore_geometry import leg_crossings
from typehaus.resolve.mep_bores import (
    STUD_BORE_DOUBLED_MAX_SUCCESSIVE,
    joist_bore,
    joist_notch,
    stud_bore,
    stud_notch,
    top_plate_cut,
)

IN = 0.0254

#: §1's worked pipe: 2" DWV is 2.375" outside, and the nominal 2" is not the hole.
VENT_IN = 2.375


# --- §1 the three percentages ----------------------------------------------------------

def test_a_two_inch_vent_does_not_fit_a_2x4_stud() -> None:
    """60% x 3.500" = 2.100" against 2.375". The single line of arithmetic that makes a
    vent wall a 2x6 wall."""
    verdict = stud_bore("2x4", VENT_IN, bearing=False)
    assert verdict.ok is False
    assert verdict.limit_in == pytest.approx(2.100)


def test_the_same_vent_fits_a_non_bearing_2x6_with_an_inch_and_a_half_of_stud_each_side(
) -> None:
    verdict = stud_bore("2x6", VENT_IN, bearing=False)
    assert verdict.ok is True
    assert verdict.limit_in == pytest.approx(3.300)
    assert "1.562" in verdict.basis  # (5.500 - 2.375) / 2, past the 5/8" edge rule


def test_the_wall_s_JOB_flips_the_verdict_on_the_same_pipe_and_the_same_stud() -> None:
    """40% x 5.500" = 2.200" against 2.375". Nothing in the geometry says which it is, so
    the check reads the model's own statement of what carries what."""
    assert stud_bore("2x6", VENT_IN, bearing=True).ok is False
    assert stud_bore("2x6", VENT_IN, bearing=False).ok is True


def test_a_three_inch_drain_is_over_the_line_in_a_non_bearing_2x6_by_two_tenths() -> None:
    verdict = stud_bore("2x6", 3.500, bearing=False)
    assert verdict.ok is False
    assert verdict.actual_in - verdict.limit_in == pytest.approx(0.200, abs=1e-9)


def test_a_four_inch_radial_is_graded_and_fails_rather_than_going_unknown() -> None:
    """4.000" is still narrower than a 2x6's 5.500", so it IS a bore and it IS over."""
    verdict = stud_bore("2x6", 4.0, bearing=False)
    assert verdict.ok is False
    assert verdict.unknown is False


def test_a_penetration_as_wide_as_the_member_is_not_a_bore_at_all() -> None:
    """An 18" duct is a framed opening with a header over it. Reporting it as an over-size
    bore is arithmetic about a hole nobody would drill — and nothing here grades the header
    either, which the verdict says out loud."""
    verdict = stud_bore("2x6", 18.0, bearing=False)
    assert verdict.unknown
    assert "framed opening" in verdict.basis
    assert verdict.remedy


def test_a_bore_in_a_cripple_shorter_than_two_depths_is_unknown_with_its_numbers() -> None:
    """The note's §6 case: a 4.00" hole in D-B-FURN's 6.56" non-bearing 2x8 cripple is under
    60% of 7.25" and would PASS on depth alone, leaving two 1.28" slivers. Never a FAIL:
    nothing published governs a block that short."""
    verdict = stud_bore("2x8", 4.0, bearing=False, length_in=6.5625)
    assert verdict.unknown
    assert '6.56"' in verdict.basis and '2.56"' in verdict.basis and '14.50"' in verdict.basis
    assert verdict.remedy


def test_the_length_gate_is_two_depths_and_leaves_a_full_stud_alone() -> None:
    assert stud_bore("2x6", 1.05, bearing=True, length_in=5.75).unknown  # PR-B-COND's cripple
    assert stud_bore("2x6", 1.05, bearing=True, length_in=11.0).ok is True
    assert stud_bore("2x6", 1.05, bearing=True, length_in=91.5).ok is True


def test_a_doubled_stud_gets_sixty_percent_and_the_limit_on_successive_ones_is_stated(
) -> None:
    verdict = stud_bore("2x6", 3.0, bearing=True, doubled=True)
    assert verdict.ok is True
    assert str(STUD_BORE_DOUBLED_MAX_SUCCESSIVE) in verdict.basis


def test_a_notch_is_a_quarter_of_a_bearing_stud_and_two_fifths_of_a_partition() -> None:
    assert stud_notch("2x6", 1.375, bearing=True).ok is True     # 25% x 5.5 = 1.375
    assert stud_notch("2x6", 1.5, bearing=True).ok is False
    assert stud_notch("2x6", 2.2, bearing=False).ok is True      # 40% x 5.5 = 2.20


# --- §2 the staggered wall -------------------------------------------------------------

def test_the_staggered_wall_is_counted_stud_by_stud(catlin_model_ro) -> None:
    """§2's table: 11 studs at the axis, 5 on the north row, 6 on the south.

    Six against eleven from a two-inch move. That is the number a rule applied to "the
    wall" cannot produce, and the reviewer's framing policy names this case: a staggered
    wall uses the actual stud positions, never "the wall is empty".
    """
    wall = next(w for w in catlin_model_ro.walls if w.tag == "W-S-SN3")
    assert wall.assembly == "INT_2X6_STAGGERED_PLUMBING"
    counts = {}
    for y in (268.0, 270.0, 266.0):
        cuts = leg_crossings(wall, (120.0 * IN, y * IN), (210.0 * IN, y * IN),
                             180.0 * IN, 180.0 * IN, (VENT_IN / 2.0) * IN)
        counts[y] = len([c for c in cuts if c.category == "stud"])
    assert counts == {268.0: 11, 270.0: 5, 266.0: 6}, counts


def test_every_stud_of_that_wall_is_still_over_the_limit(catlin_model_ro) -> None:
    """The stagger changes how MANY studs are cut and not whether the hole fits."""
    wall = next(w for w in catlin_model_ro.walls if w.tag == "W-S-SN3")
    cuts = leg_crossings(wall, (120.0 * IN, 270.0 * IN), (210.0 * IN, 270.0 * IN),
                         180.0 * IN, 180.0 * IN, (VENT_IN / 2.0) * IN)
    studs = [c for c in cuts if c.category == "stud"]
    assert studs and all(c.profile == "2x4" for c in studs)
    assert all(stud_bore(c.profile, c.diameter_in, bearing=False).ok is False
               for c in studs)


# --- §3 top plates ---------------------------------------------------------------------

def test_a_cut_past_half_the_plate_is_conditional_and_names_its_condition() -> None:
    """R602.6.1 PERMITS it with a tie, so the verdict is not a refusal — it is the detail."""
    verdict = top_plate_cut("2x4", VENT_IN)   # 50% x 3.500" = 1.750"
    assert verdict.remedy is not None
    assert "16 ga" in verdict.remedy and "8 10d" in verdict.remedy
    assert "6\" past the opening" in verdict.remedy


def test_a_small_supply_through_either_plate_needs_nothing() -> None:
    assert top_plate_cut("2x6", 1.375).remedy is None
    assert top_plate_cut("2x4", 1.375).remedy is None


def test_a_run_across_the_plate_through_its_whole_thickness_severs_it() -> None:
    """PR-B-SAUNA-VENT x W-B-ESS-W: 2.38" is 43% of a 2x6's width, which alone reads PASS,
    but laid across the plate it takes all 1.50" of thickness. Both halves are needed."""
    severed = top_plate_cut("2x6", VENT_IN, through_in=1.5, spans_width=True)
    assert severed.unknown
    assert "severed" in severed.basis and "framed opening" in severed.basis
    assert "header" in severed.remedy
    assert top_plate_cut("2x6", VENT_IN, through_in=1.30, spans_width=True).ok is True
    assert top_plate_cut("2x6", VENT_IN, through_in=1.5, spans_width=False).ok is True


# --- §4 joists -------------------------------------------------------------------------

def test_a_hole_that_fits_the_window_can_still_be_over_D_over_3() -> None:
    """§4's disagreement: a 2 1/2" hole sits comfortably inside a 2x8's 3.250" window and is
    0.458" over the D/3 = 2.417" limit. Fitting and being legal are different questions."""
    verdict = joist_bore("2x8", 2.875)
    assert verdict.ok is False
    assert verdict.limit_in == pytest.approx(7.25 / 3.0)
    assert verdict.actual_in - verdict.limit_in == pytest.approx(0.458, abs=0.001)


def test_two_legal_holes_three_inches_apart_are_an_illegal_pair() -> None:
    """0.625" of wood between their edges against the 2" minimum. No per-run pass can see
    this, which is why the check keys every crossing on a floor by member first."""
    assert joist_bore("2x8", 2.0).ok is True
    assert joist_bore("2x8", 2.0, nearest_cut_in=0.625).ok is False


def test_there_is_no_notch_at_all_in_the_middle_third() -> None:
    assert joist_notch("2x10", 0.1, in_middle_third=True).ok is False
    assert joist_notch("2x10", 1.5, at_end=True).ok is True      # D/4 = 2.31"
    assert joist_notch("2x10", 1.6, at_end=False).ok is False    # D/6 = 1.54"


@pytest.mark.parametrize("profile", ["11.875 floor truss", "11.875 I-joist",
                                     "1.75x11.875 LVL", "1.25x11.875 rim"])
def test_an_engineered_member_is_unknown_and_never_graded(profile: str) -> None:
    """A generic "open webs are borable" is not evidence that THIS hole is. On catlin this
    covers nearly every floor, which is why §4 has no catlin FAIL to point at."""
    verdict = joist_bore(profile, 2.0)
    assert verdict.unknown
    assert verdict.remedy and "manufacturer" in verdict.remedy
