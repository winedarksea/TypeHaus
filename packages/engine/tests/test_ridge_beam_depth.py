"""The ridge-depth screen (checks/structural/ridge.py).

The check exists because catlin's ridge was 1.5" too shallow for a year and nothing in the
engine could say so — every neighbouring rule opts out of a ridge beam for its own good
reason. So the test that matters most is not "does the house pass" but **"would this have
caught it"**: the first case below rebuilds the old section and demands the FAIL.

The catlin model is the fixture rather than a synthetic roof, deliberately. The failure was
an interaction between four things — the beam's top pinned to the roof plane, the rafter
trimmed to the beam's face, the I-joist's perpendicular depth, and the slope — and a
hand-built two-rafter roof can be made to agree with whichever of them the author already
believes.
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus.checks.structural.ridge import CHECK_ID, ridge_beam_depth
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section


def _findings(model):
    return [f for f in ridge_beam_depth(check_context(model=model))
            if f.check_id == CHECK_ID]


def _reprofile(model, profile: str):
    """The same model with the ridge beam re-sectioned, top still on the roof plane."""
    roofs = []
    for roof in model.roofs:
        members = []
        for member in roof.members:
            if member.category == "ridge_beam":
                depth = cross_section(profile).depth_m
                member = replace(member, profile=profile,
                                 z0_m=member.z1_m - depth)
            members.append(member)
        roofs.append(replace(roof, members=tuple(members)))
    return replace(model, roofs=roofs)


def test_the_house_as_built_passes_with_the_margin_stated(catlin_model_ro) -> None:
    found = _findings(catlin_model_ro)
    assert len(found) == 1
    assert found[0].result is Result.PASS
    assert "RB-HOUSE" in found[0].element_tags
    # At 6:12: 13.28" plumb cut + 1.75" of half-width down the plane (0.875") = 14.15"
    # needed against the 16" bought. It was 13.10" against 14" at 4:12, and 14" FAILS the
    # new number by 0.15" — which is why the beam went to 16" with the pitch.
    assert "14.15\" needed" in found[0].message


@pytest.mark.parametrize("profile", ["3-1.75x11.875 LVL", "2-1.75x11.875 LVL"])
def test_11_875_fails_at_any_width_which_is_why_narrowing_was_not_the_lever(
        catlin_model_ro, profile: str) -> None:
    """3-1.75x11.875 LVL is the ridge as originally authored. Both widths fail.

    Worth parametrizing rather than pinning the one historical section: the tempting cheap
    fix when this was found was to drop a ply, and the reason that does not work is that
    width barely moves the answer. A narrower beam trims the rafter back LESS, so its cut
    face sits higher up the plane — but only by half-the-width-difference x the slope, which
    is 0.44" at 6:12 against the 2.28" that is missing.

    ``_reprofile`` re-sections the beam without re-trimming the rafters, so the shortfall it
    reports is the one for the CURRENT 3.5" trim rather than the one the house carried on
    its historical 5.25". That difference IS the half-width term above, arriving from the
    other direction.
    """
    found = _findings(_reprofile(catlin_model_ro, profile))
    assert len(found) == 1
    assert found[0].result is Result.FAIL
    assert found[0].fix_hint and "9.5/11.875/14/16/18" in found[0].fix_hint


def test_the_shortfall_it_reports_is_the_hand_arithmetic(catlin_model_ro) -> None:
    """Plumb cut minus what the beam reaches, to the thousandth, computed independently."""
    model = _reprofile(catlin_model_ro, "2-1.75x11.875 LVL")
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    beam = next(m for m in roof.members if m.category == "ridge_beam")
    rafter = next(m for m in roof.members if m.category == "rafter")

    slope_factor = math.hypot(1.0, 6.0 / 12.0)   # 6:12
    plumb_m = cross_section(rafter.profile).depth_m * slope_factor
    shortfall_in = (beam.z0_m - (rafter.z1_end_m - plumb_m)) / M_PER_IN

    assert shortfall_in == pytest.approx(2.277, abs=1e-3)
    assert f"{shortfall_in:.4g}\"" in _findings(model)[0].message


@pytest.mark.parametrize("profile", ["2-1.75x14 LVL", "3-1.75x14 LVL"])
def test_fourteen_inches_no_longer_reaches_at_six_twelve(catlin_model_ro,
                                                         profile: str) -> None:
    """14" was the answer at 4:12 and is 0.15" short at 6:12, at either width.

    This is the pitch change's one structural cost and it is worth pinning at both widths
    for the same reason the 11 7/8" case is: the tempting response to a 0.15" miss is to add
    a ply, and a ply buys 0.44".
    """
    found = _findings(_reprofile(catlin_model_ro, profile))
    assert found[0].result is Result.FAIL


@pytest.mark.parametrize("profile", ["2-1.75x16 LVL", "3-1.75x16 LVL", "2-1.75x18 LVL"])
def test_sixteen_inches_is_the_shallowest_stock_depth_that_works(catlin_model_ro,
                                                                 profile: str) -> None:
    found = _findings(_reprofile(catlin_model_ro, profile))
    assert found[0].result is Result.PASS


def test_a_truss_roof_is_not_this_check_s_business(catlin_model_ro) -> None:
    """RF-GARAGE carries its own ridge in every truss and authors no Beam.

    Reporting UNKNOWN on it would be noise: there is no ridge beam to grade, which is
    ``structural.ridge_support``'s question and not this one.
    """
    tagged = {tag for f in _findings(catlin_model_ro) for tag in f.element_tags}
    assert "RF-GARAGE" not in tagged


# --- the derivation both the splice and the tie rest on -------------------------------


def test_continuous_support_is_measured_not_taken_on_trust(catlin_model_ro) -> None:
    """Dropping W-A-C1B opens a 3'-9" hole, and the beam stops reading as continuous.

    This is the historical bug as a test. ``RB-HOUSE`` named W-A-C1 and W-A-C2 and omitted the
    middle third of its own bearing line for a year — harmless while nothing read the tuple,
    and not harmless now that two rules do: a beam wrongly believed continuous would be bought
    in spliced pieces it cannot be built from, and tied at a pitch instead of at the ends it
    actually has. So the refs are the claim and the walls are the evidence.
    """
    from typehaus.model.structure import Beam
    from typehaus.resolve.framing.roof import _continuously_supported

    beam = next(e for storey in catlin_model_ro.plan.storeys
                for e in catlin_model_ro.plan.storey_elements(storey.tag)
                if isinstance(e, Beam) and e.tag == "RB-HOUSE")
    start, end = (5.4864, 0.0), (5.4864, 10.9728)  # x=18', y 0'->36'

    assert _continuously_supported(catlin_model_ro, beam, start, end)
    # Five segments: W-A-C2 split twice when the guest studio's bath corner (N-A-B2,
    # y=15'-11") and the stair void's south partition (N-A-C3, y=22'-4") both landed on
    # this line and needed shared endpoints. The centreline itself did not move an inch —
    # the beam still bears on it continuously — which is the whole point of asserting the
    # refs rather than the geometry.
    assert beam.bearing_refs == ("W-A-C1", "W-A-C1B", "W-A-C2", "W-A-C2M", "W-A-C2B")

    gapped = beam.model_copy(update={"bearing_refs": ("W-A-C1", "W-A-C2")})
    assert not _continuously_supported(catlin_model_ro, gapped, start, end)

    # ...and a line that stops short of the far end is not continuous either.
    short = beam.model_copy(update={"bearing_refs": ("W-A-C1", "W-A-C1B")})
    assert not _continuously_supported(catlin_model_ro, short, start, end)


def test_a_beam_read_as_spanning_is_bought_and_tied_as_one_piece(catlin_model_ro) -> None:
    """The two consequences, asserted where they are actually spent."""
    from typehaus.resolve.framing.roof import _continuously_supported  # noqa: F401
    from typehaus.takeoff.framing import framing_takeoff

    ridge = next(row for row in framing_takeoff(catlin_model_ro)
                 if row["category"] == "ridge_beam")
    assert ridge["spliceable"]
    assert [(b["length_ft"], b["count"]) for b in ridge["stock"]] == [(12, 3)]
