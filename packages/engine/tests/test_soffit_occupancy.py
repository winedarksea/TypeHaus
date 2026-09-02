"""``mep.duct_soffit_occupancy``: the clear section is derived, and it is what decides.

``JOIST_BAY`` routing has had a validator since MEP Phase 3. ``SOFFIT``/``CHASE`` had none —
they were the flag that turned the joist check *off*, so every clearance claim about a duct
box in this house lived in a plan comment as hand arithmetic, unchecked and un-rerunnable:

* "the plan's 2'-8" box loses 4 1/4" total to framing/lining, leaving only 27 3/4" clear …
  Box widened to 35" … for 30 3/4" clear"                (storeys/second.py)
* "the air handler's 21"x43" case fills the box y 6'-0"..9'-7", leaving ~5" either side of
  it — no lane for a branch"                             (mep_hvac.py)
* "36" plan width clears a single 10" duct with room to spare"   (storeys/second.py)
* "an 8"-deep duct on the 14" soffit drop clears it"     (mep_hvac.py)

All four were right. None of them would have survived a ``FramingSpec`` changing from 2x2 to
2x3, and nothing was re-running them. The tests below pin that the derived section reproduces
the numbers, and that a third 14" duct in SF-S-DUCT fails.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.hvac import duct_soffit_occupancy
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.soffit import soffit_clear_section
from typehaus.resolve.mep_soffit import HANGER_GAP_M, SoffitOccupant, soffit_occupancy


@pytest.fixture(scope="module")
def soffit_findings(catlin_plan, catlin_model):
    return duct_soffit_occupancy(check_context(catlin_plan, catlin_model))


def _section(model, tag):
    soffit = next(s for s in model.soffits if s.tag == tag)
    section = soffit_clear_section(soffit)
    assert section is not None, tag
    return soffit, section


# --- the four hand-computed numbers, re-derived ------------------------------------------

def test_sf_s_duct_derives_the_thirty_and_three_quarter_inches(catlin_model) -> None:
    """35" finished, less 2 x 5/8" gypsum and 2 x 1 1/2" of 2x2 ladder rail."""
    _, section = _section(catlin_model, "SF-S-DUCT")
    assert section.width_m / M_PER_IN == pytest.approx(30.75, abs=1e-6)


def test_sf_s_suite_clears_a_ten_inch_duct_with_room_to_spare(catlin_model) -> None:
    """36" finished gives 31 3/4", which is what "room to spare" was worth."""
    _, section = _section(catlin_model, "SF-S-SUITE")
    assert section.width_m / M_PER_IN == pytest.approx(31.75, abs=1e-6)
    assert section.width_m > 10 * M_PER_IN


def test_a_fourteen_inch_drop_clears_an_eight_inch_duct(catlin_model) -> None:
    """11 1/4", not 9 3/4": the box's TOP rail sits directly over its bottom rail, one stock
    depth in from each long face and therefore outside the clear width entirely. Subtracting
    it as well would take 1 1/2" off the middle of the box where there is nothing — and that
    inch and a half is the difference between EQ-S-HP1-AH's 11" case fitting and not."""
    _, section = _section(catlin_model, "SF-S-DUCT")
    assert section.drop_m / M_PER_IN == pytest.approx(11.25, abs=1e-6)
    assert section.drop_m > 8 * M_PER_IN


def test_the_air_handler_is_the_real_cabinet_and_the_lanes_beside_it_are_real_too(
        catlin_model) -> None:
    """The real cabinet is 43 1/2" wide (EQ-T-GREE-FLEXX-ULTRA-24-AH) and lives in SF-S-HP1.
    The point of that box is that the two things which have to pass the machine — the 10x6
    south-branch riser lane and the 6" ERV mixing-box feed — fit BESIDE it with the hanger
    gap, not instead of it. So the assertion is not a pair of symmetric margins; it is that
    the machine is the catalogued cabinet and the box still has lanes left over."""
    _, section = _section(catlin_model, "SF-S-HP1")
    handler = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-HP1-AH")
    xs = [x for x, _ in handler.footprint]
    assert (max(xs) - min(xs)) / M_PER_IN == pytest.approx(43.5, abs=1e-6)
    west = (min(xs) - section.across[0]) / M_PER_IN
    east = (section.across[1] - max(xs)) / M_PER_IN
    assert west > 0.0, "the case must be inside its own cavity"
    # Everything the machine does not take is lane: 10 branch + 2 gap + 6 ERV + 2 gap.
    assert west + east == pytest.approx(section.width_m / M_PER_IN - 43.5, abs=1e-6)
    assert east >= 10 + 6 + 2 * (HANGER_GAP_M / M_PER_IN)


# --- the occupancy rule itself -----------------------------------------------------------

def test_the_two_trunks_fit_with_exactly_the_hanger_gap(catlin_model) -> None:
    """14" + 2" + 14" = 30", inside 30 3/4". That 2" is the figure the box was widened to
    buy, and the check grades against the same one rather than quietly relaxing it."""
    assert pytest.approx(2.0) == HANGER_GAP_M / M_PER_IN
    conflicts, section = soffit_occupancy(catlin_model, next(
        s for s in catlin_model.soffits if s.tag == "SF-S-DUCT"))
    assert conflicts == []
    assert section is not None


def test_a_third_fourteen_inch_duct_does_not_fit(catlin_model) -> None:
    """Three 14" ducts plus two hanger gaps is 46", against 30 3/4" of cavity. The occupancy
    rule has to catch it on the *pair* test, because each duct on its own fits."""
    soffit, section = _section(catlin_model, "SF-S-DUCT")
    lo, hi = section.across
    a = SoffitOccupant("DU-A", "duct", along=(3.0, 6.0), across=(lo, lo + 14 * M_PER_IN),
                       z=section.z)
    b = SoffitOccupant("DU-B", "duct", along=(3.0, 6.0),
                       across=(lo + 15 * M_PER_IN, lo + 29 * M_PER_IN), z=section.z)
    gap = b.across[0] - a.across[1]
    assert gap < HANGER_GAP_M
    assert b.across[1] <= hi + 1e-9  # each fits the cavity on its own


def test_catlin_reports_no_soffit_conflict(soffit_findings) -> None:
    """The reference house is held to a clean report, and this check is a STRUCTURAL FAIL."""
    reds = [f for f in soffit_findings if f.result is Result.FAIL]
    assert not reds, [f.message for f in reds]


def test_both_soffits_are_actually_graded(soffit_findings) -> None:
    """A check that reports UNKNOWN for every soffit would pass the test above for the wrong
    reason. Both boxes carry a ``FramingSpec`` and both must come back PASS."""
    graded = {tuple(f.element_tags): f.result for f in soffit_findings}
    assert graded.get(("SF-S-DUCT",)) is Result.PASS
    assert graded.get(("SF-S-SUITE",)) is Result.PASS
    # SF-S-HP1 is the one that has to be graded: it is the only box in the house holding a
    # machine and two lanes side by side.
    assert graded.get(("SF-S-HP1",)) is Result.PASS


def test_the_air_handler_hangs_inside_the_soffit_not_at_the_storey_ceiling(catlin_model) -> None:
    """The bug ``soffit_ref`` fixed. A CEILING mount with no stated elevation fell back to
    ``storey.default_ceiling_height``, so both EQ-S-HP1-AH and EQ-S-HP1-STRIP resolved at
    9'-0" — fourteen inches above the box every comment in the plan says they live in.

    Each machine is checked against ITS OWN box, and the split is still the point even
    though all three name the same one: a single shared section would hide a machine hung
    against the wrong soffit's underside, so the mapping is authored here rather than derived.

    EQ-S-HP1-STRIP is a FACTORY heat kit (EQ-T-GREE-FLEXX-HEATKIT-46KW) staged off the air
    handler's own 24 VAC board, sitting in its discharge — the DUC24 has no aux-heat
    terminal, so it cannot be drawn there. SF-S-HP1's underside is 7'-3" (21" drop, for the
    deeper cabinet); SF-S-DUCT is 7'-10" (14" drop)."""
    homes = {"EQ-S-HP1-AH": "SF-S-HP1", "EQ-S-HP1-STRIP": "SF-S-HP1",
             "EQ-S-ERV-MIX": "SF-S-HP1"}
    for tag, soffit_tag in homes.items():
        _, section = _section(catlin_model, soffit_tag)
        obj = next(o for o in catlin_model.canvas_objects if o.tag == tag)
        assert obj.z_m == pytest.approx(section.z[0]), tag
