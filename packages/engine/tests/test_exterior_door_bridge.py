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


def test_catalog_extender_rests_on_the_girt_course_short_of_the_court(catlin_model_ro):
    opening = _door(catlin_model_ro, "D-S-BALCONY")
    support = opening.doorway.exterior_placement.installation_report["support"]
    assert support["kind"] == "girt_bridge"
    assert support["girt_face_in"] == pytest.approx(6.0, abs=1e-3)
    # The door's buck sill lies flush with the rough sill, so the pan never steps up.
    assert support["buck_top_z_m"] == pytest.approx(opening.doorway.rough_opening_z_m)
    assert support["landing_member"].startswith("sister")
    assert support["landing_deck_edge_in"] == pytest.approx(8.5, abs=1e-3)
    assert 0.25 < support["nose_gap_in"] < 1.5
    assert not opening.doorway.conflicts


@pytest.mark.parametrize("tag", ("D-M-PORCH", "D-M-ENTRY", "D-G-SERVICE"))
def test_schematic_plates_rest_on_their_landings(catlin_model_ro, tag):
    opening = _door(catlin_model_ro, tag)
    report = opening.doorway.exterior_placement.installation_report
    assert report["kind"] == "approach_bearing"
    assert report["pad_bearing_in"] >= 1.0 - 1e-6
    assert 0 <= report["pad_thickness_in"] <= 1.5
    assert not opening.doorway.conflicts


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
