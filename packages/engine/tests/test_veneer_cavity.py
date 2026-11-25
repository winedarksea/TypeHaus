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


def test_the_brick_reads_six_and_a_half_inches_to_the_studs(catlin_brick_model_ro) -> None:
    reach = veneer_ties.measure(catlin_brick_model_ro, catlin_brick_model_ro.wall("W-B-BRICK"))
    assert reach.to_structure_in == pytest.approx(_TO_STUDS_IN, abs=1e-3)
    assert reach.airspace_in == pytest.approx(_AIRSPACE_IN, abs=1e-3)
    assert reach.backing in ("W-B-S2-FR", "W-B-S3-FR") and reach.unbacked_in == 0


def test_the_2024_w2_8_row_covers_it_and_prints_the_spacing(catlin_brick_ctx) -> None:
    finding = _grade(catlin_brick_ctx, "2024 IRC")[0]
    assert finding.result is Result.PASS
    assert "W2.8" in finding.message and "6.625\" to the backing" in finding.message
    # ASD Zone 5 suction 19.9 psf (L7's mean roof height from adjacent ground: q_h 21.03) is
    # under R703.8.4.1's 30 psf: 2.67 sf per tie.
    assert "one tie per 2.67 sf" in finding.message and "32\" o.c." in finding.message
    assert "19.9 psf" in finding.message


def test_the_2021_row_is_the_same_table(catlin_brick_ctx) -> None:
    assert _grade(catlin_brick_ctx, "2021 IRC")[0].result is Result.PASS


def test_the_adopted_2018_table_hands_it_to_veneer_anchor(catlin_brick_ctx) -> None:
    finding = _grade(catlin_brick_ctx, "2018 IRC + MN amendments")[0]
    assert finding.result is Result.UNKNOWN and finding.authority is Authority.ENGINEERED
    assert finding.engineering_item == "veneer_anchor/W-B-BRICK"
    assert "4.5\"" in finding.message
    # The detail names the edition and the dependency (decision 10).
    assert "2024 IRC row" in finding.message and "R104.11" in finding.message
    assert "2 pintle legs" in finding.message


def test_every_tie_lands_on_a_stud_and_none_into_the_concrete_ends(catlin_brick_model_ro) -> None:
    from typehaus import veneer_tie_layout

    wythe = catlin_brick_model_ro.wall("W-B-BRICK")
    reach = veneer_ties.measure(catlin_brick_model_ro, wythe)
    lay = veneer_tie_layout.layout(catlin_brick_model_ro, wythe, reach, veneer_ties.TIE_AREA_SF)
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


def test_the_layout_finding_passes_and_names_the_concrete_ends(catlin_brick_ctx) -> None:
    layout = next(f for f in _grade(catlin_brick_ctx, "2024 IRC")
                  if "stud stations" in f.message)
    assert layout.result is Result.PASS
    assert "none into the pour" in layout.message and "R703.8.4.1.1" in layout.message


def test_the_slotted_tie_takes_drag_and_wind_on_a_bond_break(catlin_brick_ctx) -> None:
    """Owner, G8: a bond break at the base and an adjustable slotted tie (TMS 402-22 Table 6:
    3,000 lb/in, 200 lb allowable, 330 lb design; TN 3C Table 7's 2.5 p At). Wind 133.1 lb plus
    drag at a stated friction upper bound of 1.0 (49.3 lb over 65 ties) = 182.4 of 200: PASS."""
    force = next(f for f in _grade(catlin_brick_ctx, "2024 IRC") if "bond break" in f.message)
    assert force.result is Result.PASS
    msg = force.message
    assert "adjustable slotted tie, a READING of Hohmann & Barnard HB-213-2X" in msg
    assert "does not use the word slotted" in msg and "over 200 lbf" in msg
    assert "FL-B-BRICK-BASE-E, FL-B-BRICK-BASE-W" in msg
    assert "3,204 lb on 65 ties (13 stations x 5 rows) = 49.3 lb" in msg
    assert "wind 2.5 p At = 2.5 x 19.93 psf x 2.67 sf = 133.1 lb" in msg
    assert "UPPER BOUND, unverified" in msg
    assert "drag 49.3 + wind 133.1 = 182.4 lb against 200 lb allowable, 330 lb design" in msg
    assert "d/c 0.91" in msg


def test_table_6_rows_are_the_published_ones() -> None:
    assert veneer_ties.TIE_TABLE_6["adjustable_slotted"] == (3000.0, 200.0, 330.0)
    assert veneer_ties.TIE_TABLE_6["adjustable_pintle"] == (2500.0, 125.0, 210.0)
    assert veneer_ties.DETAIL_TIE_KIND == "adjustable_slotted"


def test_a_wythe_with_no_flashing_runs_leaves_its_base_bare(catlin_brick_model_ro) -> None:
    """Without the runs the check FAILs: the brick follows the court and each tie takes
    2,500 lb/in x the closure (214 lb against 125)."""
    plan = catlin_brick_model_ro.plan

    class _Plan:
        def all_elements(self):
            return [e for e in plan.all_elements()
                    if not getattr(e, "tag", "").startswith("FL-B-BRICK")]

    class _Model:
        openings = catlin_brick_model_ro.openings

    _Model.plan = _Plan()
    runs, bare = veneer_ties.base_flashing(_Model, catlin_brick_model_ro.wall("W-B-BRICK"))
    assert runs == [] and bare == pytest.approx(203.0 - 63.3125, abs=1e-3)


def test_the_perimeter_and_rows_are_graded(catlin_brick_model_ro) -> None:
    from typehaus import veneer_tie_layout

    wythe = catlin_brick_model_ro.wall("W-B-BRICK")
    lay = veneer_tie_layout.layout(catlin_brick_model_ro, wythe,
                                   veneer_ties.measure(catlin_brick_model_ro, wythe), 2.67)
    # Bed-joint rows at most 24" apart; each head and sill band holds one (R703.8.4.1.1).
    assert lay.rows_in == pytest.approx((16.0, 34.667, 48.0, 61.333, 85.333), abs=1e-3)
    assert lay.rows_met and lay.met
    win = next(o for o in lay.openings if o.tag == "AO-B-BRICK-WIN")
    door = next(o for o in lay.openings if o.tag == "AO-B-BRICK-DOOR")
    assert win.head.row_in == pytest.approx(61.333, abs=1e-3)
    assert win.sill.row_in == pytest.approx(34.667, abs=1e-3)
    # The door's head band, over the 3" angle: 83"-87.6", on the head cripples and the packs.
    assert door.sill is None and door.head.stations == 7 and door.head.max_gap_in <= 36.0
    assert door.head.z_in == pytest.approx((83.0, 87.5625), abs=1e-3)
    assert door.head.row_in == pytest.approx(85.333, abs=1e-3)
