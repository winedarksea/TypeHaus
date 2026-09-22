"""§6 and §7 of `houses/catlin/notes/framing_bore_limits.md`, reproduced numerically.

Two halves of one question — what happens where a run meets a member R602.6 does not
describe. A header is collected and honestly ungraded; a cut top plate past 50% is now a
determinate verdict, because `PlateTie` gives the model somewhere to say the strap is there.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.model.registry import constructor_names, element_kinds
from typehaus.model.structure import PlateTie
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_bores import (
    _CUTTABLE_CATEGORIES,
    header_bore,
    leg_crossings,
    top_plate_cut,
)
from typehaus.resolve.model import FramedMember, ResolvedWall


def _ctx(model) -> CheckContext:
    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2020)

#: catlin's ordinary built-up header: 2-2x8 is 3.000" x 7.250".
HEADER = "2-2x8"
HEADER_DEPTH_IN = 7.25


# --- §6 headers --------------------------------------------------------------------------

def test_a_header_is_collected_at_all() -> None:
    """The one-literal bug: the member list left headers out, so a run over a door met
    nothing and the report was silent about it."""
    assert "header" in _CUTTABLE_CATEGORIES


def test_an_ordinary_hole_in_a_header_is_unknown_and_never_invented() -> None:
    """No IRC table publishes a bore limit for a header, and none is borrowed."""
    verdict = header_bore(HEADER, 4.0)
    assert verdict.ok is None
    assert "NO IRC table" in verdict.basis
    assert "R502.8.1 governs floor joists" in verdict.basis
    assert verdict.limit_in is None  # nothing was claimed as a limit


def test_the_joist_fraction_is_quoted_for_scale_and_binds_nothing() -> None:
    verdict = header_bore(HEADER, 4.0)
    assert "binding on nothing here" in verdict.basis
    assert f'{HEADER_DEPTH_IN / 3.0:.2f}"' in verdict.basis


def test_a_hole_under_the_joist_fraction_is_still_unknown() -> None:
    """2.38" is inside D/3 = 2.42" — and D/3 is a joist's rule, so it decides nothing."""
    assert header_bore(HEADER, 2.375).ok is None


def test_a_penetration_as_deep_as_the_header_severs_it_and_needs_no_table() -> None:
    verdict = header_bore(HEADER, HEADER_DEPTH_IN)
    assert verdict.ok is False
    assert "severed header does not carry the opening" in verdict.basis
    assert verdict.remedy is not None


@pytest.mark.parametrize("profile", ["2-1.75x14 LVL", "3-1.75x5.5 LVL"])
def test_an_engineered_header_is_the_fabricator_s_chart(profile: str) -> None:
    verdict = header_bore(profile, 4.0)
    assert verdict.ok is None
    assert "fabricator's chart" in verdict.basis


def test_catlin_s_six_header_crossings_are_all_reported(catlin_model_ro) -> None:
    """Six runs meet a header in this house and every one of them was silent before."""
    from typehaus.checks.mep.routing_bores import run_through_header

    findings = run_through_header(_ctx(catlin_model_ro))
    assert len(findings) == 6
    assert {f.result.value for f in findings} == {"unknown"}


# --- §6 where along the header, and how much of it ------------------------------------

#: catlin's own basement header, in inches: 39" long, 7.25" deep, its top at -22.19.
_H_X0, _H_X1 = 37.50, 76.50
_H_Z0, _H_Z1 = -29.44, -22.19


def _header_wall() -> ResolvedWall:
    member = FramedMember(
        parent_uid="W-TEST", child_key="header-0", category="header", profile=HEADER,
        p0=(_H_X0 * M_PER_IN, 0.0), p1=(_H_X1 * M_PER_IN, 0.0),
        z0_m=_H_Z0 * M_PER_IN, z1_m=_H_Z1 * M_PER_IN,
        length_m=(_H_X1 - _H_X0) * M_PER_IN)
    return ResolvedWall(uid="W-TEST", tag="W-TEST", storey="basement", assembly="INT",
                        axis=((_H_X0 * M_PER_IN, 0.0), (_H_X1 * M_PER_IN, 0.0)),
                        layers=(), z0_m=-96.0 * M_PER_IN, z1_m=_H_Z1 * M_PER_IN,
                        members=(member,))


def _cross(x_in: float, z_in: float, diameter_in: float):
    """One level leg crossing the header square on, at ``x_in``, centred at ``z_in``."""
    radius = diameter_in / 2.0 * M_PER_IN
    cuts = leg_crossings(_header_wall(), (x_in * M_PER_IN, -12.0 * M_PER_IN),
                         (x_in * M_PER_IN, 12.0 * M_PER_IN),
                         z_in * M_PER_IN, z_in * M_PER_IN, radius)
    assert len(cuts) == 1
    return cuts[0]


def test_a_crossing_of_a_horizontal_member_reports_the_crossing_not_the_midpoint() -> None:
    """The station is where the run MEETS the header, not the header's own centroid.

    Reading a header's centroid put every one of catlin's six crossings at dead midspan
    (57.00" on this member), which is a wrong z as well as a station no hole chart can be
    read against: a hole's cost to a bending member is a question about where along the span.
    """
    cut = _cross(39.25, -21.94, 4.0)
    midspan = (_H_X0 + _H_X1) / 2.0
    assert cut.station[0] / M_PER_IN == pytest.approx(39.25)
    assert abs(cut.station[0] / M_PER_IN - midspan) > 17.0


def test_a_partial_overlap_is_a_notch_depth_and_not_a_full_diameter_bore() -> None:
    """DU-B-ERV-R-SAUNA-SUP: a 4" duct 0.25" over the header top takes 1.75" off it."""
    cut = _cross(39.25, _H_Z1 + 0.25, 4.0)
    assert cut.diameter_in == pytest.approx(4.0)
    assert cut.through_in == pytest.approx(1.75)
    verdict = header_bore(cut.profile, cut.diameter_in, through_in=cut.through_in)
    assert verdict.kind == "notch"
    assert "notch off a face" in verdict.basis


def test_a_run_wholly_inside_the_member_loses_nothing_to_the_clip() -> None:
    cut = _cross(54.0, -27.21, 2.375)
    assert cut.through_in == pytest.approx(cut.diameter_in)
    assert header_bore(cut.profile, cut.diameter_in,
                       through_in=cut.through_in).kind == "bore"


def test_the_six_catlin_header_crossings_are_at_their_true_stations(
        catlin_model_ro) -> None:
    """§6's table, from the model. Every one of these printed 57.00" before 2026-09-22."""
    from typehaus.checks.mep.routing_bores import _crossings

    stations = {tag: (cut.station[0] / M_PER_IN, cut.station[1] / M_PER_IN, cut.through_in)
                for tag, _wall, cuts in _crossings(_ctx(catlin_model_ro))
                for cut in cuts if cut.category == "header"}
    expected = {
        "DU-B-ERV-R-SAUNA-SUP": (39.00, 216.0, 1.75),
        "DU-B-ERV-R-SAUNA-EXH": (45.00, 216.0, 3.25),
        "PR-B-KITCH-DRAIN": (54.00, 216.0, 2.375),
        "PR-M-S-BATH1-DRAIN": (54.77, 216.0, 3.50),
        "PR-B-MAIN-DRAIN": (72.00, 216.0, 4.50),
        "DU-B-ERV-R-GYM": (216.0, 156.0, 4.00),
    }
    assert set(stations) == set(expected)
    for tag, want in expected.items():
        assert stations[tag] == pytest.approx(want, abs=0.01), tag


# --- §7 the plate tie --------------------------------------------------------------------

def test_a_penetration_as_wide_as_the_plate_is_not_a_plate_cut() -> None:
    """An 18" duct does not notch a 2x4 top plate; it interrupts it. Nine of catlin's
    thirteen were reported as "18.00" out of a 3.50" plate"."""
    verdict = top_plate_cut("2x4", 18.0, tie=False)
    assert verdict.ok is None
    assert "framed opening with a header over it" in verdict.basis


def test_the_tie_authored_is_a_pass_and_absent_is_a_fail() -> None:
    assert top_plate_cut("2x4", 2.375, tie=True).ok is True
    fail = top_plate_cut("2x4", 2.375, tie=False)
    assert fail.ok is False
    assert "no PlateTie in this model covers it" in fail.basis
    assert fail.remedy is not None and "16 ga" in fail.remedy


def test_not_looking_is_not_the_same_as_looking_and_finding_nothing() -> None:
    """``tie=None`` keeps the pre-schema reading: conditional, with the detail stated."""
    verdict = top_plate_cut("2x4", 2.375)
    assert verdict.ok is True and verdict.remedy is not None


def test_a_cut_under_half_the_plate_is_a_pass_with_or_without_a_tie() -> None:
    for tie in (None, True, False):
        assert top_plate_cut("2x6", 1.375, tie=tie).ok is True


def test_plate_tie_is_a_registered_element_and_a_dialect_constructor() -> None:
    assert "PlateTie" in element_kinds()
    assert "PlateTie" in constructor_names()


def test_plate_tie_carries_r602_6_1_s_own_numbers() -> None:
    tie = PlateTie(tag="PTIE-W-B-ESS-W", wall="W-B-ESS-W")
    assert tie.gauge == pytest.approx(0.054)
    assert tie.width.inches == pytest.approx(1.5)
    assert tie.lap.inches == pytest.approx(6.0)
    assert tie.nails_each_side == 8


def test_an_empty_covers_ties_every_cut_in_that_wall() -> None:
    from typehaus.checks.mep.routing_bores import plate_ties

    plan = SimpleNamespace(all_elements=lambda: [
        PlateTie(tag="PTIE-A", wall="W-A"),
        PlateTie(tag="PTIE-B", wall="W-B", covers=("PR-B-KITCH-DRAIN",)),
    ])
    ties = plate_ties(SimpleNamespace(model=SimpleNamespace(plan=plan)))
    assert ties == {"W-A": frozenset({"*"}), "W-B": frozenset({"PR-B-KITCH-DRAIN"})}


def test_catlin_s_one_real_plate_cut_fails_for_want_of_a_tie(catlin_model_ro) -> None:
    """The other nine are framed openings, which is a different question (§6).

    It was four until the wet-wall retype on 2026-09-20. Three of those cuts were legal
    the moment their plates became 2x6: the R602.6.1 tie line is half the plate depth, so
    it went 1.75" -> 2.75" and the sauna vent's two cuts and the kitchen drain's one fell
    under it. What is left is `PR-B-SAUNA-VENT` through `W-B-ESS-S`, the one wall in that
    group nothing bores hard enough to have been retyped.
    """
    from typehaus.checks.mep.routing_bores import run_through_plate

    findings = run_through_plate(_ctx(catlin_model_ro))
    results = [f.result.value for f in findings]
    assert results.count("fail") == 1
    assert results.count("unknown") == 9
