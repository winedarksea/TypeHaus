"""Drywall accessories off catlin's DrywallStandard (decision #103)."""

import copy
import dataclasses

import pytest
from shapely.geometry import LineString, Polygon

from typehaus.resolve.drywall_led import drywall_standard, host_shadow_gap_runs

_IN = 0.0254
_COVES = {"LR-M-LIVING-W", "LR-M-LIVING-E", "LR-M-DINING-W", "LR-M-DINING-E",
          "LR-M-BATH2-TUB-CLG", "LR-S-HALL-GAP", "LR-S-HALL-GAP2"}


def test_the_coves_are_shadow_gaps_cut_from_their_host(catlin_model_ro):
    model = catlin_model_ro
    gaps = {run.tag: run for run in model.light_runs if run.profile == "shadow_gap"}
    assert set(gaps) == _COVES
    soffits = {soffit.tag: soffit for soffit in model.soffits}
    for run in gaps.values():
        # The 5/8" Z bead rises no further than the 5/8" board it sits in.
        assert run.aperture_m / _IN == pytest.approx(0.625)
        assert -min(d for _key, quad in run.section for _a, d in quad) / _IN == pytest.approx(
            0.625)
        slot = LineString(run.path).buffer(run.aperture_m / 2.0 - 1e-4, cap_style=2,
                                           join_style=2)
        if run.host_ref in soffits:
            boards = [Polygon(p.prism.ring, p.prism.voids)
                      for p in soffits[run.host_ref].finish_panels
                      if p.key.startswith("underside")]
            assert abs(run.z_m - soffits[run.host_ref].z0_m) < 1e-9
        else:
            boards = [Polygon(s.outline) for s in model.solids
                      if s.category == "ceiling" and s.uid.startswith(run.host_ref)]
        assert boards and sum(board.intersection(slot).area for board in boards) < 1e-9
        # The profile's record bills the run's own length.
        assert sum(t.length_m for t in model.drywall_trims
                   if t.kind == "led_profile" and run.tag in t.tags) == pytest.approx(
            run.length_m)


def test_trimless_door_bead_and_living_corner_by_hand(catlin_model_ro):
    model = catlin_model_ro
    # D-M-BED2's RO is 34.236" x 82.512" off the seat: 2 x 82.512 + 34.236 = 199.26" a face.
    bead = [t for t in model.drywall_trims if t.kind == "door_l_bead" and "D-M-BED2" in t.tags]
    assert len(bead) == 2
    assert sum(t.length_m for t in bead) / _IN == pytest.approx(2 * 199.26, abs=0.02)
    # RM-M-LIVING's outside corners run its cap top (+3/4", decision #111) to the 5/8" ceiling
    # face at 9'-1/8" less 5/8" = 107 1/2": 106 3/4".
    corners = [t for t in model.drywall_trims
               if t.kind == "outside_corner" and t.room == "RM-M-LIVING"]
    assert corners and all(t.length_m / _IN == pytest.approx(106.75, abs=1e-3)
                           for t in corners)


def test_a_cove_moves_onto_its_reveal_and_one_out_of_reach_is_an_error(catlin_model_ro):
    standard, findings = drywall_standard(catlin_model_ro.plan)
    assert standard is not None and not findings
    resolved = next(r for r in catlin_model_ro.light_runs if r.tag == "LR-M-LIVING-W")

    def host(shift_in):
        model = copy.copy(catlin_model_ro)
        model.solids = list(catlin_model_ro.solids)
        model.light_runs = [
            dataclasses.replace(run, profile="surface", section=(),
                                path=[(x + shift_in * _IN, y) for x, y in run.path])
            if run.tag == "LR-M-LIVING-W" else run
            for run in catlin_model_ro.light_runs]
        return model, host_shadow_gap_runs(model, standard)

    # 2" off the reveal, within the 4" reach: back onto its centre, 5/16" off the wall.
    model, found = host(2)
    moved = next(r for r in model.light_runs if r.tag == "LR-M-LIVING-W")
    assert not found and moved.path == pytest.approx(resolved.path)
    model, found = host(6)
    assert [(f.check_id, f.element_tags) for f in found] == [
        ("integrity.light_run_host", ("LR-M-LIVING-W",))]
    assert "6.31\"" in found[0].message


def test_jbead_stops_with_the_bare_face_and_slivers_are_not_corners(catlin_model_ro):
    trims = catlin_model_ro.drywall_trims
    # W-M-STRW's mudroom face is open bays to 7'-0" over a +0.94685" floor: the two vertical
    # J-beads stop there; the board above is a horizontal one.
    vertical = sorted(t.length_m / _IN for t in trims
                      if t.kind == "termination" and t.room == "RM-M-MUDROOM")[:2]
    assert vertical == pytest.approx([84 - 0.94685] * 2, abs=1e-3)
    # A clear face's ~1" mitre sliver (the closet's SW corner, the attic's building corners)
    # is an inside corner. SF-S-HP1 butts walls 0.1-0.6" off three sides and SF-S-DUCT's
    # higher board on the fourth: free are its 40 3/4" south edge and its west edge's
    # 35 3/4" over the hall, less the 1" a wall's gap reaches.
    rooms = {t.room for t in trims if t.kind == "outside_corner" and len(t.tags) == 1}
    assert not rooms & {"RM-S-NCLOSET", "RM-B-ESS", "RM-A-POCKET", "RM-S-SUITEBATH"}
    hp1 = sum(t.length_m for t in trims if "SF-S-HP1" in t.tags) / _IN
    assert hp1 == pytest.approx(40.75 + 35.74, abs=1.5)


def test_a_tile_end_reveal_stops_at_what_covers_the_board(catlin_model_ro):
    # WP-M-BATH2-SURR's north end meets W-M-TUBDK-S, the deck and the 6" splash: its reveal
    # runs from the splash top (28 3/4") to the panel top (102 1/4"). The free west end
    # starts on the pan (+6 1/4"). The TK-105 cap over the top edge takes no reveal under
    # it; the reveal runs along the cap's top and down its two free 3 7/8" ends.
    trims = catlin_model_ro.drywall_trims
    ends = sorted(t.length_m / _IN for t in trims
                  if t.kind == "tile_reveal" and "WP-M-BATH2-SURR" in t.tags)
    assert ends == pytest.approx([102.25 - 28.75, 102.25 - 6.25], abs=1e-3)
    cap = sorted(t.length_m / _IN for t in trims
                 if t.kind == "tile_reveal" and "WP-M-BATH2-SURR-CAP" in t.tags)
    assert cap == pytest.approx([3.875, 3.875, 36.0, 36.0], abs=1e-3)


def test_a_j_bead_is_picked_by_the_board_it_stops(catlin_model_ro):
    # A 1/2" J does not seat on 5/8" board (review I4-003): the ESS closet's Type X keeps the
    # 5/8" bead, the 1/2" walls take M401-10.
    beads = {}
    for trim in catlin_model_ro.drywall_trims:
        if trim.kind == "termination":
            beads.setdefault(trim.material_ref, set()).add(trim.room)
    assert set(beads) == {"dw-j-bead-metal", "dw-j-bead-metal-half"}
    assert "RM-B-ESS" in beads["dw-j-bead-metal"] - beads["dw-j-bead-metal-half"]
    assert "RM-M-MUDROOM" in beads["dw-j-bead-metal-half"] - beads["dw-j-bead-metal"]


def test_a_dropped_ceiling_lowers_the_clear_head(catlin_model_ro):
    # The sauna's furred T&G hangs below the joists (review I4-007): R305 reads its face.
    from typehaus.resolve.room_floor import room_finished_floor_elevation

    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-B-SAUNA")
    ceiling = min(c.z0_m for c in catlin_model_ro.ceilings if c.room_ref == room.tag)
    floor = room_finished_floor_elevation(catlin_model_ro, room)
    assert room.clear_height_m == pytest.approx(ceiling - floor, abs=1e-9)
    assert room.clear_height_m / _IN == pytest.approx(84.0625, abs=0.01)
