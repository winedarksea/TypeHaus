"""Bearing-line blocking under walls above, its 2x6 pass-through boxes, and runs through beams."""

from __future__ import annotations

import pytest

from typehaus.checks.mep.routing_beams import _leg_overlap
from typehaus.quantities import M_PER_IN
from typehaus.resolve.floor_blocking import _box, _clip
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


def test_an_interior_line_is_blocked_on_its_axis(catlin_model_ro) -> None:
    attic = _floor(catlin_model_ro, "FS-ATTIC")
    solid = [m for m in _blocking(attic) if m.profile == "11.875 I-joist"]
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


_FLOOR = ResolvedFloor(uid="F", tag="FS-T", storey="s", direction="x", members=())
_Z0, _Z1 = 0.0, 11.875 * _IN
_GAP = (0.0, 13.5 * _IN)


def _crossing(tag, p_lo_in, p_hi_in, z_lo_in, z_hi_in):
    return (tag, p_lo_in * _IN, p_hi_in * _IN, z_lo_in * _IN, z_hi_in * _IN)


def test_a_fitting_run_gets_rails_and_cheeks() -> None:
    box, conflicts = _box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                          [_crossing("DU", 4.0, 8.0, 2.0, 6.0)])
    assert not conflicts
    assert {m.child_key for m in box} == {"k-rail-top", "k-rail-bottom", "k-cheek-lo",
                                          "k-cheek-hi"}
    assert all(m.profile == "2x6" for m in box)


def test_a_run_on_the_plate_drops_the_bottom_rail() -> None:
    box, conflicts = _box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1,
                          [_crossing("DU", 4.0, 10.0, 0.0, 6.0)])
    assert not conflicts
    assert "k-rail-bottom" not in {m.child_key for m in box}


@pytest.mark.parametrize("crossing", [
    _crossing("DU", 4.0, 8.0, 2.0, 11.0),    # crown above the top rail
    _crossing("DU", -0.5, 4.0, 2.0, 6.0),    # into the joist face
])
def test_a_misfit_is_a_conflict(crossing) -> None:
    _box_members, conflicts = _box(_FLOOR, "k", True, 0.0, _GAP, _Z0, _Z1, [crossing])
    assert [c.run_tag for c in conflicts] == ["DU"]


def test_clip_keeps_the_longest_piece_clear_of_a_beam() -> None:
    assert _clip((0.0, 10.0), [(6.0, 20.0)]) == (0.0, 6.0)
    assert _clip((0.0, 0.01), []) is None


def test_a_duct_along_its_bay_through_a_flush_beam_overlaps_it() -> None:
    from shapely.geometry import box

    beam = box(213 * _IN, 268 * _IN, 219 * _IN, 310 * _IN)
    depth = _leg_overlap((0.0, 296 * _IN), (300 * _IN, 296 * _IN), 111.6 * _IN, 111.6 * _IN,
                         2 * _IN, beam, 108.1 * _IN, 120 * _IN)
    assert depth == pytest.approx(4 * _IN)
    clear = _leg_overlap((0.0, 260 * _IN), (300 * _IN, 260 * _IN), 111.6 * _IN, 111.6 * _IN,
                         2 * _IN, beam, 108.1 * _IN, 120 * _IN)
    assert clear <= 0.0
