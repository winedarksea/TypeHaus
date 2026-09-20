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
from typehaus.resolve.mep_bores import _CUTTABLE_CATEGORIES, header_bore, top_plate_cut


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


def test_catlin_s_four_real_plate_cuts_fail_for_want_of_a_tie(catlin_model_ro) -> None:
    """The other nine are framed openings, which is a different question (§6)."""
    from typehaus.checks.mep.routing_bores import run_through_plate

    findings = run_through_plate(_ctx(catlin_model_ro))
    results = [f.result.value for f in findings]
    assert results.count("fail") == 4
    assert results.count("unknown") == 9
