"""The breezeway's polycarbonate: one continuous skin, and one channel where sheets meet.

The enclosure used to have two holes in it, both of them consequences of the "three 4'x8'
sheets, uncut" sheet economy the module was organised around:

* 8 1/4" of framing stood bare below each standing sheet — the sheet started at the deck
  surface (+1") while the structure goes down to the floor-beam soffit (-7 1/4"), so the
  beam band and the deck edge showed under the glazing;
* 14 1/2" of each E/W elevation was open — the wall sheet's head stopped at the post top
  (+8'-1") and the roof sheet's underside is at +9'-3 1/2", with nothing between them, and
  the two extrusions that should have met were 3 1/4" apart in plan and 13.4" apart in
  elevation.

The sheets now run the whole way and meet in one H channel. That premise is what these tests
hold — deliberately against *derived* elevations rather than the authored constants, so a
future change to the framing depth or the wedge rise moves the assertions with it.
"""

from __future__ import annotations

import pytest

M_TO_FT = 3.280839895


def _solid(model, tag):
    return next(s for s in model.solids if s.tag == tag)


def _solids(model, prefix):
    return [s for s in model.solids if s.tag.startswith(prefix)]


def _span_x(solid):
    xs = [p[0] * M_TO_FT for p in solid.outline]
    return min(xs), max(xs)


# --- 1. the standing sheets cover the structure they enclose -------------------------------

@pytest.mark.parametrize("side", ["W", "E"])
def test_a_standing_sheet_reaches_the_floor_beam_soffit(catlin_model, side):
    """Nothing of the floor structure shows below the glazing. The beam soffit is derived
    from the beams themselves, not from the authored _PIER_TOP, so this keeps holding if the
    framing depth changes."""
    sheet = _solid(catlin_model, f"GL-BW-WALL-{side}")
    beams = [s for s in _solids(catlin_model, "BM-BW-") if s.z1_m < 1.0]  # the floor beams
    assert beams, "the breezeway's floor beams must exist to bear the deck"
    soffit = min(s.z0_m for s in beams)
    assert sheet.z0_m == pytest.approx(soffit, abs=1e-9), (
        "the sheet must reach the beam soffit — 8 1/4\" of framing used to stand bare below it")


@pytest.mark.parametrize("side", ["W", "E"])
def test_a_standing_sheet_reaches_the_roof_sheet_it_meets(catlin_model, side):
    """No open band at the head. The roof sheet's underside is the target, derived."""
    sheet = _solid(catlin_model, f"GL-BW-WALL-{side}")
    roof_under = min(s.z0_m for s in _solids(catlin_model, "GL-BW-ROOF-"))
    assert sheet.z1_m == pytest.approx(roof_under, abs=1e-9), (
        "14 1/2\" of elevation used to be open between the wall sheet and the roof sheet")


def test_the_standing_sheet_is_cut_from_ten_foot_stock(catlin_model):
    """The retired premise, made explicit: these are no longer whole 8' sheets. 9'-10 3/4"
    is inside 10' stock and outside 8' — if a change ever pushed it past 10', the module's
    stated bill of materials would be wrong and nothing else would say so."""
    sheet = _solid(catlin_model, "GL-BW-WALL-W")
    height_ft = (sheet.z1_m - sheet.z0_m) * M_TO_FT
    assert height_ft == pytest.approx(9.895833, abs=1e-5)  # 9'-10 3/4"
    assert 8.0 < height_ft <= 10.0


def test_a_jamb_runs_the_sheets_full_height(catlin_model):
    """A jamb caps the sheet's vertical edge, so it moved with the sheet. Leaving its top at
    the post top while the panel height grew pushed its foot 1'-9 3/4" below the sheet, into
    the pier — which the geometry showed and no assertion would have."""
    sheet = _solid(catlin_model, "GL-BW-WALL-W")
    for tag in ("TR-BW-JAMB-WN-1", "TR-BW-JAMB-WS-1"):
        jamb = _solid(catlin_model, tag)
        assert jamb.z0_m == pytest.approx(sheet.z0_m, abs=1e-9), tag
        assert jamb.z1_m == pytest.approx(sheet.z1_m, abs=1e-9), tag


# --- 2. the shared channel -----------------------------------------------------------------

def test_the_roof_sheet_dies_on_the_standing_sheets_own_line(catlin_model):
    """The cost of the shared channel, asserted so it stays deliberate: the roof used to
    oversail the glazing line by 3 1/4" each side as a drip edge. It does not any more."""
    wall_w, wall_e = (_solid(catlin_model, f"GL-BW-WALL-{s}") for s in "WE")
    roof_w, roof_e = (_solid(catlin_model, f"GL-BW-ROOF-{s}") for s in "WE")
    assert min(_span_x(roof_w)) == pytest.approx(sum(_span_x(wall_w)) / 2.0, abs=1e-6)
    assert max(_span_x(roof_e)) == pytest.approx(sum(_span_x(wall_e)) / 2.0, abs=1e-6)


@pytest.mark.parametrize("side", ["W", "E"])
def test_one_h_channel_receives_both_sheets(catlin_model, side):
    """One extrusion where there were two — and it has to straddle the joint, not sit above
    or below it, or it is capturing one sheet and merely touching the other."""
    trim = catlin_model.plan.by_tag(f"TR-BW-HCH-{side}")
    assert trim.profile == "H"
    assert not trim.weep_holes, "the H is a joint, not a drain — the sill weeps now"
    channel = _solid(catlin_model, f"TR-BW-HCH-{side}-1")
    joint = min(s.z0_m for s in _solids(catlin_model, "GL-BW-ROOF-"))
    assert channel.z0_m < joint < channel.z1_m
    # ...and it sits on the sheets' shared line in plan.
    sheet = _solid(catlin_model, f"GL-BW-WALL-{side}")
    lo, hi = _span_x(channel)
    assert lo < sum(_span_x(sheet)) / 2.0 < hi


def test_the_eave_u_and_the_wall_head_are_gone(catlin_model):
    """Both were replaced by the H, not merely joined by it."""
    tags = {getattr(e, "tag", None) for e in catlin_model.plan.all_elements()}
    for retired in ("TR-BW-UCH-W", "TR-BW-UCH-E", "TR-BW-HEAD-W", "TR-BW-HEAD-E"):
        assert retired not in tags, retired


def test_the_sill_is_the_only_drainage_path_left(catlin_model):
    """The eave U-channel's weep holes went with it, so the sill's are all there is. A
    breezeway whose only vented channel lost its weeps drains nowhere."""
    weeping = [e for e in catlin_model.plan.all_elements()
               if getattr(e, "tag", "").startswith("TR-BW-") and getattr(e, "weep_holes", False)]
    assert {e.tag for e in weeping} == {"TR-BW-SILL-W", "TR-BW-SILL-E"}
    # The sill sits at the deck surface, which the sheet now passes rather than starts at.
    sill = _solid(catlin_model, "TR-BW-SILL-W-1")
    sheet = _solid(catlin_model, "GL-BW-WALL-W")
    assert sheet.z0_m < sill.z0_m, "the sheet runs below the sill, down to the beam soffit"


# --- 3. the takeoff ------------------------------------------------------------------------

def test_the_h_channel_bills_as_its_own_line(catlin_model):
    """glazing_trim_takeoff groups on (profile, material, weep_holes), so the H bills as a
    row of its own with no takeoff change — which is the reason "H" was the right spelling
    rather than a new kind."""
    from typehaus.takeoff.glazing import glazing_trim_takeoff

    rows = glazing_trim_takeoff(catlin_model)
    profiles = {row["profile"] for row in rows}
    assert "H" in profiles
    h_row = next(row for row in rows if row["profile"] == "H")
    # Two channels, one per side, each running the breezeway's 4'-0" N-S depth.
    assert h_row["length_ft"] == pytest.approx(8.0, abs=1e-6)
