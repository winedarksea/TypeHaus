"""Bearing-line blocking under walls above, its 2x6 pass-through boxes, and runs through beams."""

from __future__ import annotations

import pytest

from typehaus.checks.mep.routing_beams import _leg_overlap
from typehaus.quantities import M_PER_IN
from typehaus.resolve.blocking_parts import clip, pass_through_box
from typehaus.resolve.model import ResolvedFloor

_IN = M_PER_IN


def _floor(model, tag: str):
    return next(floor for floor in model.floors if floor.tag == tag)


def _blocking(floor):
    return [m for m in floor.members if m.child_key.startswith("bearing-block")]


def test_both_decks_block_their_own_side_of_the_shared_centreline(catlin_model_ro) -> None:
    west, east = _floor(catlin_model_ro, "FS-S-WEST"), _floor(catlin_model_ro, "FS-S-EAST")
    assert _blocking(west) and _blocking(east)
    # x = 18' is shared: each deck's course stays behind its own joist tips.
    assert max(max(m.p0[0], m.p1[0]) for m in _blocking(west)) <= west.ends.tip_hi + 1e-6
    assert min(min(m.p0[0], m.p1[0]) for m in _blocking(east)) >= east.ends.tip_lo - 1e-6


def test_the_bays_over_w_m_c3_are_blocked_though_no_deck_names_it(catlin_model_ro) -> None:
    # W-M-C3 runs y 18'..22'-4" under x = 18' and is in neither deck's bearing_refs.
    for tag in ("FS-S-WEST", "FS-S-EAST"):
        spans = [sorted((m.p0[1], m.p1[1])) for m in _blocking(_floor(catlin_model_ro, tag))]
        assert any(lo >= 216 * _IN and hi <= 268.1 * _IN for lo, hi in spans), tag


@pytest.mark.parametrize(("deck", "x_in", "lo_in", "hi_in"), [
    ("FS-M-MECH", 118.75, 309.38, 325.38),   # W-M-STRW ends at y=26'-6", past mid-bay
    # W-M-C3 ends at y=22'-4", short of mid-bay. Since decision #112 the I-joists take 2" of
    # the shared x=18' plate (tip 215.25"), and the block stays behind its own tip.
    ("FS-M-STAIR", 214.09, 261.38, 277.38),
])
def test_a_bearing_wall_ending_mid_bay_still_gets_its_block(catlin_model_ro, deck, x_in,
                                                            lo_in, hi_in) -> None:
    spans = [sorted((m.p0[1], m.p1[1])) for m in _blocking(_floor(catlin_model_ro, deck))
             if abs(m.p0[0] - x_in * _IN) < 0.01]
    assert any(lo > lo_in * _IN and hi < hi_in * _IN for lo, hi in spans)


def test_an_interior_line_is_blocked_on_its_axis(catlin_model_ro) -> None:
    attic = _floor(catlin_model_ro, "FS-ATTIC")
    solid = [m for m in _blocking(attic) if m.profile == "11.875 TJI 230"]
    assert solid and all(abs(m.p0[0] - 216 * _IN) < 1e-6 for m in solid)


def test_no_block_sits_under_a_flush_beam(catlin_model_ro) -> None:
    beam = next(s for s in catlin_model_ro.solids if s.tag == "BM-M-HALL")
    b_lo, b_hi = min(p[1] for p in beam.outline), max(p[1] for p in beam.outline)
    for tag in ("FS-S-WEST", "FS-S-EAST"):
        for member in _blocking(_floor(catlin_model_ro, tag)):
            lo, hi = sorted((member.p0[1], member.p1[1]))
            assert hi <= b_lo + 1e-6 or lo >= b_hi - 1e-6, member.child_key


def test_the_rerouted_erv_returns_cross_in_a_box(catlin_model_ro) -> None:
    keys = {m.child_key for m in _blocking(_floor(catlin_model_ro, "FS-S-EAST"))}
    assert any(key.endswith("-rail-top") for key in keys)
    assert not _floor(catlin_model_ro, "FS-S-EAST").blocking_conflicts


def test_a_wall_over_a_wall_along_the_joists_reads_its_ladder(catlin_model_ro) -> None:
    from types import SimpleNamespace

    from typehaus.checks.structural.stacked_ladder import stacked_line_ladder
    from typehaus.findings import Result

    lines = {line.lowers: line for line in catlin_model_ro.stacked_ladders}
    # W-S-SN3 over W-M-HS3/HS4 along FS-S-WEST's trusses: no block is laid (none is published);
    # the line is carried by the squash block, then the authored 1 1/4" LSL strip (TJ-8000 row).
    # Nonbearing SN2 is not on it (decision 22).
    west = lines[("W-M-HS3", "W-M-HS4")]
    assert west.open_web and west.uppers == ("W-S-SN3",)
    assert {s.status for s in west.stations} == {"carried"}
    assert {s.by for s in west.stations} == {"P-S-SN3-SQUASH", "sister-0-0"}
    assert all("5,400 plf" in s.detail for s in west.stations if s.by == "sister-0-0")
    assert max(b - a for a, b in zip([s.at_m for s in west.stations],
                                     [s.at_m for s in west.stations][1:], strict=False)
               ) <= west.spacing_m + 1e-9
    assert not any(m.child_key.startswith("ladder-block")
                   for m in _floor(catlin_model_ro, "FS-S-WEST").members)
    # FO-A-HALL's trimmer stands on W-S-SN3's plate, station by station.
    assert {s.status for s in lines[("W-S-SN3",)].stations} == {"carried"}
    findings = stacked_line_ladder(SimpleNamespace(plan=catlin_model_ro.plan,
                                                   model=catlin_model_ro))
    by_floor = {f.element_tags[0]: f.result for f in findings}
    assert by_floor["FS-S-WEST"] is Result.PASS and by_floor["FS-ATTIC"] is Result.PASS


def test_a_box_bears_only_where_a_cheek_stands_on_the_plate() -> None:
    from typehaus.resolve.stacked_ladder import seated

    plate = (9.5 * _IN, 13.0 * _IN)  # a 2x4 plate in the bay's north side
    block, _why = seated(_FLOOR, "k", "2x10", True, 0.0, _GAP, plate, _Z0, _Z1, [])
    assert block and len(block) == 1
    # A pipe lying along the plate pushes both cheeks off it: no load path, so no station.
    along = _crossing("PR", 9.0, 13.0, 3.0, 5.0)
    assert seated(_FLOOR, "k", "2x10", True, 0.0, _GAP, plate, _Z0, _Z1, [along])[0] is None
    # A pipe in the south of the bay leaves the hi cheek on the plate.
    south = _crossing("PR", 2.0, 4.0, 3.0, 5.0)
    box, _why = seated(_FLOOR, "k", "2x10", True, 0.0, _GAP, (4.5 * _IN, 8.0 * _IN), _Z0,
                       _Z1, [south])
    assert box and any(m.child_key.endswith("-cheek-hi") for m in box)


_FLOOR = ResolvedFloor(uid="F", tag="FS-T", storey="s", direction="x", members=())
_Z0, _Z1 = 0.0, 11.875 * _IN
_GAP = (0.0, 13.5 * _IN)


def _crossing(tag, p_lo_in, p_hi_in, z_lo_in, z_hi_in):
    return (tag, p_lo_in * _IN, p_hi_in * _IN, z_lo_in * _IN, z_hi_in * _IN)


def test_a_fitting_run_gets_rails_and_cheeks() -> None:
    box, conflicts = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                          [_crossing("DU", 4.0, 8.0, 2.0, 6.0)])
    assert not conflicts
    assert {m.child_key for m in box} == {"k-rail-top", "k-rail-bottom", "k-cheek-lo",
                                          "k-cheek-hi"}
    assert all(m.profile == "2x6" for m in box)


def test_a_run_on_the_plate_drops_the_bottom_rail() -> None:
    box, conflicts = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                          [_crossing("DU", 4.0, 10.0, 0.0, 6.0)])
    assert not conflicts
    assert "k-rail-bottom" not in {m.child_key for m in box}


@pytest.mark.parametrize("crossing", [
    _crossing("DU", 4.0, 8.0, 2.0, 11.0),    # crown above the top rail
    _crossing("DU", -0.5, 4.0, 2.0, 6.0),    # into the joist face
])
def test_a_misfit_is_a_conflict(crossing) -> None:
    _box_members, conflicts = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1, [crossing])
    assert [c.run_tag for c in conflicts] == ["DU"]


def test_clip_keeps_the_longest_piece_clear_of_a_beam() -> None:
    assert clip((0.0, 10.0), [(6.0, 20.0)]) == (0.0, 6.0)
    assert clip((0.0, 0.01), []) is None


def test_a_duct_along_its_bay_through_a_flush_beam_overlaps_it() -> None:
    from shapely.geometry import box

    beam = box(213 * _IN, 268 * _IN, 219 * _IN, 310 * _IN)
    depth = _leg_overlap((0.0, 296 * _IN), (300 * _IN, 296 * _IN), 111.6 * _IN, 111.6 * _IN,
                         2 * _IN, beam, 108.1 * _IN, 120 * _IN)
    assert depth == pytest.approx(4 * _IN)
    clear = _leg_overlap((0.0, 260 * _IN), (300 * _IN, 260 * _IN), 111.6 * _IN, 111.6 * _IN,
                         2 * _IN, beam, 108.1 * _IN, 120 * _IN)
    assert clear <= 0.0


def test_a_rectangular_run_is_boxed_by_its_width_and_depth() -> None:
    from typehaus.resolve.blocking_parts import crossing_runs

    w, h = 6 * M_PER_IN / 2.0, 4 * M_PER_IN / 2.0  # a 6 x 4 duct, centreline z 100"
    z = 100 * M_PER_IN
    runs = [("D", ((5.0, 0.0), (5.0, 10.0)), (z, z), w, h)]
    (tag, p_lo, p_hi, z_lo, z_hi), = crossing_runs(
        runs, False, 5.0, 0.04, (4.0, 6.0), z - 1.0, z + 1.0)
    assert (p_hi - p_lo, z_hi - z_lo) == pytest.approx((2 * w, 2 * h))


def test_a_riser_in_the_rails_opens_them_and_a_cheek_holds_the_rest() -> None:
    from typehaus.resolve.blocking_parts import riser_cuts

    z = 5 * _IN
    runs = [("R", ((1.0 * _IN, 6.0 * _IN), (1.0 * _IN, 6.0 * _IN)), (z, 20 * _IN),
             0.4 * _IN, 0.4 * _IN),
            ("far", ((9.0 * _IN, 6.0 * _IN), (9.0 * _IN, 6.0 * _IN)), (z, 20 * _IN),
             0.4 * _IN, 0.4 * _IN)]
    cuts = riser_cuts(runs, True, 0.0, _GAP, _Z0, _Z1)  # only the riser inside 5 1/2" counts
    assert len(cuts) == 1
    box, _ = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                              [_crossing("DU", 9.0, 11.0, 2.0, 6.0)], cuts)
    top = [m for m in box if m.child_key.endswith("rail-top")]
    assert len(top) == 2  # a rail piece each side of the hole
    assert sorted(m.p0[1] for m in top) == pytest.approx([0.0, cuts[0][1]])
    assert sorted(m.p1[1] for m in top) == pytest.approx([cuts[0][0], _GAP[1]])
    assert any("-cheek-r" in m.child_key for m in box)


def test_a_cheek_slides_off_a_run_and_never_doubles_another() -> None:
    from typehaus.resolve.blocking_parts import RAIL_W_M

    # A 2" pipe lying along the box's cheek spots (x = 1" is inside the 5 1/2" footprint).
    z = 5 * _IN
    pipe = ("PR", ((1.0 * _IN, 0.0), (1.0 * _IN, 13.5 * _IN)), (z, z), 1.0 * _IN, 1.0 * _IN)
    box, _ = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                              [_crossing("PR", 4.0, 8.0, 4.0, 6.0)], (), [pipe])
    assert not any("cheek" in m.child_key for m in box)
    assert RAIL_W_M / 2 > 1.0 * _IN  # the pipe really is inside the cheek's footprint
    # A riser cheek on top of the lo cheek's spot is not laid twice.
    riser = ("R", ((2.0 * _IN, 4.5 * _IN),) * 2, (z, 20 * _IN), 0.4 * _IN, 0.4 * _IN)
    box, _ = pass_through_box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                              [_crossing("PR", 6.0, 8.0, 4.0, 6.0)],
                              [(4.3 * _IN, 5.5 * _IN)], [riser])
    spots = [round(m.p0[1] / _IN, 3) for m in box if "cheek" in m.child_key]
    assert len(spots) == len(set(spots))
