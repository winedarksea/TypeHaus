"""``structural.veneer_cavity_width`` and the ``veneer_anchor`` keys against
notes/sunken_garden_veneer_beam.md §6k-§6l: W-B-BRICK's back at -6.0", the studs at +0.5",
the foam at -4.06" — 6.500" to the backing, 1.940" of airspace; the ties on the studs (13
stations, none into the 3.5" concrete ends) and the court's closure on the ties.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus import veneer_ties
from typehaus.findings import Authority, Result

#: §6k, by hand.
_TO_STUDS_IN = 6.500
_AIRSPACE_IN = 1.940


def _grade(ctx, irc_base):
    from typehaus.checks.structural.veneer_cavity import veneer_cavity_width

    return veneer_cavity_width(replace(ctx, profile=replace(ctx.profile, irc_base=irc_base)))


def test_the_brick_reads_six_and_a_half_inches_to_the_studs(catlin_model_ro) -> None:
    reach = veneer_ties.measure(catlin_model_ro, catlin_model_ro.wall("W-B-BRICK"))
    assert reach.to_structure_in == pytest.approx(_TO_STUDS_IN, abs=1e-3)
    assert reach.airspace_in == pytest.approx(_AIRSPACE_IN, abs=1e-3)
    assert reach.backing in ("W-B-S2-FR", "W-B-S3-FR") and reach.unbacked_in == 0


def test_the_2024_w2_8_row_covers_it_and_prints_the_spacing(catlin_ctx) -> None:
    finding = _grade(catlin_ctx, "2024 IRC")[0]
    assert finding.result is Result.PASS
    assert "W2.8" in finding.message and "6.625\" to the backing" in finding.message
    # ASD Zone 5 suction 19.9 psf (L7's mean roof height from adjacent ground: q_h 21.03) is
    # under R703.8.4.1's 30 psf: 2.67 sf per tie.
    assert "one tie per 2.67 sf" in finding.message and "32\" o.c." in finding.message
    assert "19.9 psf" in finding.message


def test_the_2021_row_is_the_same_table(catlin_ctx) -> None:
    assert _grade(catlin_ctx, "2021 IRC")[0].result is Result.PASS


def test_the_adopted_2018_table_hands_it_to_veneer_anchor(catlin_ctx) -> None:
    finding = _grade(catlin_ctx, "2018 IRC + MN amendments")[0]
    assert finding.result is Result.UNKNOWN and finding.authority is Authority.ENGINEERED
    assert finding.engineering_item == "veneer_anchor/W-B-BRICK"
    assert "4.5\"" in finding.message
    # The detail names the edition and the dependency (decision 10).
    assert "2024 IRC row" in finding.message and "R104.11" in finding.message
    assert "2 pintle legs" in finding.message


def test_every_tie_lands_on_a_stud_and_none_into_the_concrete_ends(catlin_model_ro) -> None:
    from typehaus import veneer_tie_layout

    wythe = catlin_model_ro.wall("W-B-BRICK")
    reach = veneer_ties.measure(catlin_model_ro, wythe)
    lay = veneer_tie_layout.layout(catlin_model_ro, wythe, reach, veneer_ties.TIE_AREA_SF)
    assert lay.length_in == pytest.approx(203.0, abs=1e-3)
    assert len(lay.stations_in) == 13
    # 2.67 sf over 24" rows carries 16.02": the 16" stud bays are exactly full.
    assert lay.allowed_in == pytest.approx(16.02, abs=1e-6)
    assert lay.widest_in == pytest.approx(16.0, abs=1e-3) and lay.met
    # §6l: the 3.5" in front of each concrete end is tied from the stud 4 1/4" in.
    assert {(s.wall, round(s.length_in, 2), round(s.to_first_tie_in, 2)) for s in lay.strips} \
        == {("W-B-S1", 3.5, 4.25), ("W-B-S4", 3.5, 4.25)}
    near = {o.tag: o.near_in for o in lay.openings}
    assert near["AO-B-BRICK-WIN"] == pytest.approx((1.0, 1.0), abs=1e-3)
    assert near["AO-B-BRICK-DOOR"] == pytest.approx((2.25, 0.75), abs=1e-3)


def test_the_layout_finding_passes_and_names_the_concrete_ends(catlin_ctx) -> None:
    layout = next(f for f in _grade(catlin_ctx, "2024 IRC")
                  if "stud stations" in f.message)
    assert layout.result is Result.PASS
    assert "none into the pour" in layout.message and "R703.8.4.1.1" in layout.message


def test_tie_travel_reads_the_courts_closure_from_the_thermal_break_record(catlin_ctx) -> None:
    """The ties take the closure L1's record bounds (0.0854"), and no tie maker publishes
    travel normal to the wall (only the 1/16" fit TMS 402-16 allows): UNKNOWN, gate G8."""
    from typehaus.engineering.thermal_break_joint import NAME

    closure = max(ls.demand for key in catlin_ctx.engineering
                  if key.startswith("thermal_break_transfer/")
                  for ls in catlin_ctx.engineering[key].limit_states if ls.name == NAME)
    travel = next(f for f in _grade(catlin_ctx, "2024 IRC") if "closure" in f.message)
    assert travel.result is Result.UNKNOWN
    assert f"{closure:.4f}" in travel.message and "0.0625" in travel.message


def test_the_veneer_anchor_item_retires_on_the_2024_irc(catlin_model_ro) -> None:
    from typehaus.engineering.deferred import _veneer_anchor_keys
    from typehaus.engineering.registry import EngineeringContext

    def keyed(irc_base):
        return _veneer_anchor_keys(EngineeringContext(
            plan=catlin_model_ro.plan, model=catlin_model_ro, irc_base=irc_base))

    assert keyed("2018 IRC + MN amendments") == ["W-B-BRICK"]
    assert keyed("2021 IRC") == [] and keyed("2024 IRC") == []
    # An edition the table is not transcribed for is never read as covered.
    assert keyed(None) == ["W-B-BRICK"]
