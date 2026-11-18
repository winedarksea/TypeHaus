"""No-cantilever door approaches and the foam-bed tread's water path (2026-11-13)."""

import pytest

from typehaus import ApproachBearing, inch
from typehaus.resolve.exterior_door_bridge import (
    BridgeSupport,
    gap_landing_conflicts,
    slip_pad_bearing,
)

_IN = 0.0254


def _door(model, tag):
    return next(o for o in model.openings if o.tag == tag)


def test_catalog_extender_rests_on_the_sill_beam_short_of_the_court(catlin_model_ro):
    opening = _door(catlin_model_ro, "D-S-BALCONY")
    support = opening.doorway.exterior_placement.installation_report["support"]
    assert support["kind"] == "girt_bridge"
    # The beam's face stands at the XXXXW nose: nothing overhangs its bearing.
    assert support["girt_face_in"] == pytest.approx(7.5, abs=1e-3)
    assert support["extender_overhang_in"] == pytest.approx(-0.0425, abs=1e-3)
    assert support["pan_outlet_in"] == pytest.approx(7.5, abs=1e-3)
    # The door's buck sill lies flush with the rough sill, so the pan never steps up.
    assert support["buck_top_z_m"] == pytest.approx(opening.doorway.rough_opening_z_m)
    assert support["landing_member"].startswith("sister")
    assert support["landing"] == "gap"
    assert support["nose_gap_in"] == pytest.approx(1.0, abs=1e-3)
    assert not opening.doorway.conflicts


@pytest.mark.parametrize("tag, joint", (("D-M-PORCH", 2.125), ("D-M-ENTRY", 0.375)))
def test_main_floor_doors_take_a_cover_or_a_narrow_gap(catlin_model_ro, tag, joint):
    """notes/exterior_door_sill_beam.md §4: PORCH's 2 1/8" joint takes a cover sliding on a
    ledge, graded over +/-1/2"; ENTRY's landing stands 3/8" off the beam, open."""
    report = _door(catlin_model_ro, tag).doorway.exterior_placement.installation_report
    support = report["support"]
    assert support["nose_gap_in"] == pytest.approx(joint, abs=1e-3)
    if tag == "D-M-PORCH":
        assert support["landing"] == "cover"
        # 9/16" less the 0.020" drip leg the cover closes onto at the narrowest.
        assert support["cover_min_seat_bearing_in"] == pytest.approx(0.5425, abs=1e-4)
        assert support["cover_min_ledge_clearance_in"] == pytest.approx(0.0625, abs=1e-4)
        assert support["cover_thickness_in"] == pytest.approx(0.94, abs=1e-3)
    else:
        assert support["landing"] == "gap" and joint <= 0.5


def test_schematic_plate_rests_on_its_landing(catlin_model_ro):
    opening = _door(catlin_model_ro, "D-G-SERVICE")
    report = opening.doorway.exterior_placement.installation_report
    assert report["kind"] == "approach_bearing"
    assert report["pad_bearing_in"] >= 1.0 - 1e-6
    assert 0 <= report["pad_thickness_in"] <= 1.5
    assert not opening.doorway.conflicts


@pytest.mark.parametrize("tag, demand, span, deflection", (
    ("D-S-BALCONY", 126.29, 54.125, 0.0378), ("D-M-PORCH", 126.29, 54.125, 0.0378),
    ("D-M-ENTRY", 113.22, 29.1875, 0.0059)))
def test_end_seat_sill_beam_is_graded(catlin_model_ro, tag, demand, span, deflection):
    """notes/exterior_door_sill_beam.md §2-§3: the beam between its seats, and the worst seat
    screw's share of the 300 lb against the joint's 135 lb, laid out to ESR-1078 Table 5."""
    report = _door(catlin_model_ro, tag).doorway.exterior_placement.installation_report
    report = report["support"]
    assert report["connection_status"] == report["member_status"] == "PASS"
    assert report["connection_demand_lb"] == pytest.approx(demand, abs=0.01)
    assert report["connection_dcr"] == pytest.approx(demand / 135.0, abs=1e-4)
    assert report["sill_beam_span_in"] == pytest.approx(span, abs=1e-4)
    assert report["sill_beam_deflection_in"] == pytest.approx(deflection, abs=1e-4)
    assert (report["screw_shank_in"], report["screw_clamped_stack_in"]) == pytest.approx(
        (8.0, 7.5))
    assert report["screw_embedded_thread_in"] == pytest.approx(1.625)
    assert sorted({z for _, z in report["seat_screws"]})[1] - sorted(
        {z for _, z in report["seat_screws"]})[0] == pytest.approx(0.75)
    backers = [m for f in catlin_model_ro.floors for m in f.members
               if m.child_key.startswith(f"girt-sill-backer-{tag}-")]
    assert len(backers) == 4 and {m.stock_profile for m in backers} == {"2x6"}


def test_a_seat_row_inside_the_published_spacing_fails():
    from typehaus.engineering.exterior_door_support import screw_spacing_failures
    from typehaus.hardware.catalog import screw_by_part_number

    rule = screw_by_part_number("TLOK10")[0].spacing
    beam = ("beam", 0.0, 63.3125, -4.75, 0.75, "top")
    good = [(2.625, -2.625, "a"), (5.25, -2.625, "a"), (3.9375, -3.375, "b")]
    assert not screw_spacing_failures(good, [beam], rule)
    # The retired course's row: 1" from the end at 3/4" pitch.
    misses = screw_spacing_failures([(1.0, -2.625, "a"), (1.75, -2.625, "a")], [beam], rule)
    assert any("end distance" in m for m in misses)
    assert any("in-row spacing" in m for m in misses)
    # Rows 3/4" apart but not half a pitch along: Table 5's in-line 1 3/8" applies.
    in_line = [(2.625, -2.625, "a"), (5.25, -2.625, "a"), (2.625, -3.375, "b")]
    assert any("in-line row spacing" in m for m in screw_spacing_failures(in_line, [beam], rule))


def test_landing_conflicts_are_measured():
    bearing = ApproachBearing(landing_ref="deck")
    support = BridgeSupport(sheathing=0.0, member_inner=8.5 * _IN, member_outer=10 * _IN,
                            deck_edge=10 * _IN)
    assert "plank ends" in gap_landing_conflicts(support, bearing, 7.5 * _IN, 0.25 * _IN)[0]
    tight = BridgeSupport(sheathing=0.0, member_inner=8.5 * _IN, member_outer=10 * _IN,
                          deck_edge=8.5 * _IN)
    assert "closes" in gap_landing_conflicts(tight, bearing, 8.3 * _IN, 0.25 * _IN)[0]
    _, pad, conflicts = slip_pad_bearing(tight, bearing, 0.0, 1 * _IN)
    assert pad < 0 and "slip pad" in conflicts[0]


def test_foam_bed_slot_drains_down_the_isolation_joint(catlin_model_ro):
    report = _door(catlin_model_ro, "D-B-SUNKEN").doorway.exterior_placement.installation_report
    assert report["drain_slot_in"] == pytest.approx(0.479, abs=0.01)
    assert report["joint_drain_bed"] == "FB-SG-BRKBM"
    assert report["joint_drain_bed_gap_in"] <= 0.5
    assert report["sheet_lap_under_pan_in"] == pytest.approx(2.0)
    # 1/4" reserved each way over an ASTM C920 Class 50 sealant.
    assert report["box_side_joint_required_in"] == pytest.approx(0.5)


def test_a_joint_drain_names_all_three_parts():
    from typehaus import ExteriorDoorCatalogInstallation

    with pytest.raises(ValueError, match="joint drain"):
        ExteriorDoorCatalogInstallation(
            source_url="u", source_drawing="d", sill_outline_m=((0, 0), (0.1, 0), (0.1, 0.03)),
            support_kind="foam_bed", foam_rated_psi=40.0, support_ref="w",
            frame_material_ref="f", head_material_ref="h", transition_material_ref="t",
            joint_drain_wall_ref="W", sheet_lap_under_pan=inch(2))
