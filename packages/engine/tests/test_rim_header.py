"""``structural.rim_header`` for D-B-SUNKEN against ``notes/sunken_door_band_header.md``
(§2-§5; the arithmetic is ``notes/engineering_review_2026-11-22/scratch/L3/hand.py``)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus.engineering import band_header as bh
from typehaus.findings import Result
from typehaus.resolve.band_headers import band_header_findings

_IN = 0.0254


def _findings(ctx):
    from typehaus.checks.structural.rim_header import rim_header

    return rim_header(ctx)


def test_the_header_is_the_published_two_ply_row_with_the_seats_carried(catlin_ctx) -> None:
    header = next(f for f in _findings(catlin_ctx) if "rim header over" in f.message)
    assert header.result is Result.PASS
    # §3: 35.68 plf strip + two 325.73 lb seats at 7.969" from the bearings' centres, as the
    # equivalent uniform (shear governs, 148.5 plf), against the 6'-0" row, 1,582 plf.
    assert "148.5 of 1,582 plf" in header.message and "0.094" in header.message
    assert "2 seat loads of 325.7, 325.7 lb" in header.message


def test_equivalent_uniform_matches_the_hand_numbers() -> None:
    L, a = 69.3125, 7.96875
    w = 50.0 * (1.125 + 14.875 / 2) / 12.0 / 12.0 * 12.0
    shear, moment, deflection = bh.equivalent_uniform_plf(
        w, L, [(a, 325.73), (L - a, 325.73)])
    assert (shear, moment, deflection) == pytest.approx((148.5, 87.5, 96.8), abs=0.06)
    assert bh.two_ply_row(L / 12.0) == (6.0, 1582.0)


def test_fastening_seat_introduction_and_jambs_are_graded_apart(catlin_ctx) -> None:
    by_title = {f.message.split(":")[0].split("D-B-SUNKEN ")[1]: f
                for f in _findings(catlin_ctx)}
    joint = next(f for f in _findings(catlin_ctx) if "rim joint" in f.message)
    # TJ-8000 p.5: a joint at least 12" beyond the opening. FS-M-EAST's edge rim runs 12" past the
    # 18' seam (FS-M-WEST's stops where it starts), so the splice is 20.34" from the west jamb.
    assert joint.result is Result.PASS and "20.34\"" in joint.message
    by_title = {t: f for t, f in by_title.items() if "rim joint" not in t}
    assert set(by_title) == {
        "2-ply 1 1/4\" LSL rim header over 63.31\" (5.776 ft c-c, the 6 ft row)",
        "ply fastening", "seat load introduction", "jamb bearing, band to foundation"}
    assert all(f.result is Result.PASS for f in by_title.values())
    intro = by_title["seat load introduction"].message
    assert "390.9 of 560 plf" in intro and "0.9647" in intro          # §4
    jamb = by_title["jamb bearing, band to foundation"].message
    # §5: the rim under the 1,708 lb pack governs, 0.633; the header's seat reactions add
    # 428.8 lb below the band; the pack's 4 studs on the plate under them, 64.8 psi.
    assert "governs rim, vertical load under the pack at d/c 0.633" in jamb
    assert "142.5 of 360 psi" in jamb and "64.76 of 425 psi" in jamb
    assert "full-height studs, west end 1 of 2" in jamb               # R602.7.5, V 115 Exp B


def test_the_lvl_plies_and_their_engineered_item_are_gone(catlin_ctx) -> None:
    assert "band_header/D-B-SUNKEN" not in catlin_ctx.engineering
    floor = next(f for f in catlin_ctx.model.floors if f.tag == "FS-M-EAST")
    assert not [m for m in floor.members if "LVL" in m.profile]
    header = [m for m in floor.members if m.category == "sister_joist"
              and m.profile == "1.25x11.875 rim"]
    assert len(header) == 1


def test_the_wall_frames_no_header_and_an_empty_band_is_an_error(catlin_model) -> None:
    wall = catlin_model.wall("W-B-S3-FR")
    assert not [m for m in wall.members if m.category == "header"]
    [nailer] = [m for m in wall.members if m.child_key.startswith("headnailer")]
    assert nailer.z1_m - nailer.z0_m == pytest.approx(1.5 * _IN)
    plate = min(m.z0_m for m in wall.members if m.child_key.startswith("plate-top"))
    assert all(m.z1_m == pytest.approx(plate) for m in wall.members if m.category == "jack")
    assert band_header_findings(catlin_model) == []
    index, floor = next((i, f) for i, f in enumerate(catlin_model.floors)
                        if f.tag == "FS-M-EAST")
    catlin_model.floors[index] = replace(floor, members=tuple(
        m for m in floor.members if m.category != "sister_joist"))
    [finding] = band_header_findings(catlin_model)
    assert finding.check_id == "integrity.header_in_band"


def test_one_rim_board_runs_past_the_seam(catlin_model_ro) -> None:
    """``JoistSpec.edge_rim_extend`` / ``edge_rim_trim``: the splice is where the crew puts it."""
    ends = {}
    for floor in catlin_model_ro.floors:
        if floor.tag in ("FS-M-WEST", "FS-M-EAST"):
            rim = next(m for m in floor.members if m.child_key.startswith("edge-rim-"))
            ends[floor.tag] = sorted(p[0] / _IN for p in (rim.p0, rim.p1))
    assert ends["FS-M-WEST"][1] == pytest.approx(204.0, abs=1e-3)
    assert ends["FS-M-EAST"][0] == pytest.approx(204.0, abs=1e-3)
