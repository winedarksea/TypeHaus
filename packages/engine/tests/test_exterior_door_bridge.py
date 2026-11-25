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
    assert support["nose_gap_in"] == pytest.approx(0.375, abs=1e-3)
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


@pytest.mark.parametrize("tag, demand, span, deflection, reaction, rotation", (
    ("D-S-BALCONY", 125.34, 53.375, 0.0363, 325.73, (0.8283, 0.9647)),
    ("D-M-PORCH", 125.34, 53.375, 0.0363, 325.73, (0.8283, 0.9647)),
    ("D-M-ENTRY", 116.33, 28.4375, 0.0055, 348.67, (0.7831, 0.9460))))
def test_end_seat_sill_beam_is_graded(catlin_model_ro, tag, demand, span, deflection,
                                      reaction, rotation):
    """notes/exterior_door_sill_beam.md §2-§3: the beam between its seats, the worst HLGM10's
    share of the 300 lb against Z' 145.5 into the rim and its backer, laid out to ESR-1078
    Table 5, and each seat's rotation by NDS 12.4.1 on both pull-through columns."""
    report = _door(catlin_model_ro, tag).doorway.exterior_placement.installation_report
    report = report["support"]
    assert report["connection_status"] == report["member_status"] == "PASS"
    assert report["connection_demand_lb"] == pytest.approx(demand, abs=0.01)
    assert report["connection_dcr"] == pytest.approx(demand / 145.5, abs=1e-4)
    assert report["sill_beam_span_in"] == pytest.approx(span, abs=1e-4)
    assert report["sill_beam_deflection_in"] == pytest.approx(deflection, abs=1e-4)
    assert (report["screw_shank_in"], report["screw_clamped_stack_in"]) == pytest.approx(
        (8.0, 7.5))
    # 1 1/4" in the rim and 3/4" in the backer nailed behind it (params/sill_seat_backers.py).
    assert report["screw_embedded_thread_in"] == pytest.approx(2.0)
    assert report["screw_backers"]
    assert report["girt_course_member"].startswith("edge-rim-")
    assert report["seat_rotation_status"] == "PASS"
    assert report["seat_reaction_max_lb"] == pytest.approx(reaction, abs=0.01)
    columns = report["seat_rotation_columns"]
    assert (columns["SG 0.55"]["dcr"], columns["SG 0.42"]["dcr"]) == pytest.approx(
        rotation, abs=1e-4)
    # §1: the beam's top is ripped 1/32" across its 1 1/2", 1/4"/ft, and the pan falls with it.
    assert report["pan_fall_in"] == pytest.approx(1 / 32)
    assert report["pan_fall_per_ft_in"] == pytest.approx(0.25)
    # §3: the band every member's edge distances leave is 1 1/4", rows staggered 3/4" in it.
    rows = sorted({z for _, z in report["seat_screws"]})
    assert rows[1] - rows[0] == pytest.approx(0.75)
    assert sorted({round(s, 4) for s, _ in report["seat_screws"]})[:4] == pytest.approx(
        [3.0, 4.3125, 5.625, 6.9375])


def test_a_seat_row_inside_the_published_spacing_fails():
    from typehaus.engineering.exterior_door_support import screw_spacing_failures
    from typehaus.hardware.catalog import screw_by_part_number

    rule = screw_by_part_number("TLOK10")[0].spacing
    beam = ("beam", 0.0, 63.3125, -4.75, 0.75, "top", rule)
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


def test_foam_bed_nose_drips_onto_the_rim_slab(catlin_model_ro):
    """LP court face (default): no beam, so the tread's nose drips onto SL-SG-FLOOR, clear of its
    edge. The brick switch keeps the isolation-joint drain (``joint_drain_*``)."""
    doorway = _door(catlin_model_ro, "D-B-SUNKEN").doorway
    report = doorway.exterior_placement.installation_report
    assert report["drain_slab"] == "SL-SG-FLOOR"
    assert report["drain_slab_nose_clear_in"] == pytest.approx(0.77, abs=0.02)
    assert report["drain_slab_drop_in"] > 3
    assert report["sheet_lap_under_pan_in"] == pytest.approx(2.0)
    assert not any("names no outlet" in u for u in doorway.unknown)


def test_a_joint_drain_names_all_three_parts():
    from typehaus import ExteriorDoorCatalogInstallation

    with pytest.raises(ValueError, match="joint drain"):
        ExteriorDoorCatalogInstallation(
            source_url="u", source_drawing="d", sill_outline_m=((0, 0), (0.1, 0), (0.1, 0.03)),
            support_kind="foam_bed", foam_rated_psi=40.0, support_ref="w",
            frame_material_ref="f", head_material_ref="h", transition_material_ref="t",
            joint_drain_wall_ref="W", sheet_lap_under_pan=inch(2))


def test_a_tread_drains_down_a_joint_or_onto_a_slab_not_both():
    from typehaus import ExteriorDoorCatalogInstallation

    with pytest.raises(ValueError, match="not both"):
        ExteriorDoorCatalogInstallation(
            source_url="u", source_drawing="d", sill_outline_m=((0, 0), (0.1, 0), (0.1, 0.03)),
            support_kind="foam_bed", foam_rated_psi=40.0, support_ref="w",
            frame_material_ref="f", head_material_ref="h", transition_material_ref="t",
            joint_drain_wall_ref="W", joint_drain_material_ref="m", joint_drain_bed_ref="b",
            drain_slab_ref="S")
