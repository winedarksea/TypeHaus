"""Door/window corrections preserve wall-space coverage and required illumination."""

from dataclasses import replace
from math import dist

import pytest

from typehaus.checks.code.mn_residential.ventilation import habitable_light_and_ventilation
from typehaus.checks.mep.electrical_openings import wall_device_opening
from typehaus.checks.mep.electrical_room_lighting import room_lighting
from typehaus.checks.mep.electrical_spacing import receptacle_spacing
from typehaus.findings import Result
from typehaus.model import inch
from typehaus.resolve.device_boxes import boxes_by_device

_CORRECTED_DEVICES = {
    "ED-M-LIVING-RC10", "ED-M-LIVING-KGF7", "ED-M-LIVING-RC7", "ED-M-STUDY-SPOT",
    "ED-M-STUDY-SW", "ED-S-SUITEBATH-SW", "ED-S-SUITE-RC8", "ED-A-STUDY-LT",
    "ED-A-STUDY-SW", "ED-A-STAIR-RC1", "ED-A-STUDIO-WALL3", "ED-A-STUDIO-SW",
    "ED-S-STUDY2-SW",
}


def test_corrected_devices_clear_openings_and_trim(catlin_ctx):
    findings = wall_device_opening(catlin_ctx)
    assert not [finding for finding in findings if finding.result == Result.FAIL]
    for tag in _CORRECTED_DEVICES:
        assert any(f.result == Result.PASS and tag in f.element_tags for f in findings), tag
    conflicts = [finding for finding in catlin_ctx.resolve_findings
                 if set(finding.element_tags) & _CORRECTED_DEVICES]
    assert not conflicts, [finding.message for finding in conflicts]


def test_original_rc10_position_is_reported(catlin_ctx):
    body = next(body for body in catlin_ctx.model.canvas_objects
                if body.tag == "ED-M-LIVING-RC10")
    wall = catlin_ctx.model.wall(body.attachment_wall)
    (sx, sy), (ex, ey) = wall.axis
    shift = inch(6.40625 - 43).meters
    dx = shift * (ex - sx) / dist(wall.axis[0], wall.axis[1])
    dy = shift * (ey - sy) / dist(wall.axis[0], wall.axis[1])
    original = replace(body, position=(body.position[0] + dx, body.position[1] + dy),
                       footprint=tuple((x + dx, y + dy) for x, y in body.footprint))
    model = replace(catlin_ctx.model, canvas_objects=[
        original if item.tag == body.tag else item for item in catlin_ctx.model.canvas_objects])
    findings = wall_device_opening(replace(catlin_ctx, model=model))
    assert any(f.result == Result.FAIL and f.element_tags == (
        body.tag, "D-M-BATH1", "W-M-BAE") for f in findings)


def test_corrected_rooms_keep_coverage_and_study_lighting(catlin_ctx):
    assert not [f for f in receptacle_spacing(catlin_ctx) if f.result == Result.FAIL]
    lighting = [f for f in room_lighting(catlin_ctx) if "RM-M-STUDY-CLOSET" in f.element_tags]
    assert lighting and all(f.result == Result.PASS for f in lighting)
    # A study closet is not habitable space, so R303.1 does not reach it.
    assert not [f for f in habitable_light_and_ventilation(catlin_ctx)
                if f.message.startswith("RM-M-STUDY-CLOSET ")]


def test_attic_study_outlet_is_standard_15a_duplex(catlin_plan):
    outlet = next(element for element in catlin_plan.all_elements()
                  if element.tag == "ED-A-STAIR-RC1")
    assert outlet.type_ref == "ED-T-LEV-DUPLEX-15"
    assert outlet.circuit == "CKT-RC-ATTIC"
    assert outlet.mount.elevation.meters == pytest.approx(inch(12).meters)
    assert outlet.location.attachment.wall_ref == "W-A-C1"


def test_study2_switch_box_and_plate_clear_passthrough(catlin_ctx):
    box = boxes_by_device(catlin_ctx.model)["ED-S-STUDY2-SW"]
    opening = next(o for o in catlin_ctx.model.openings if o.tag == "D-S-STUDY2")
    wall = catlin_ctx.model.wall(opening.host_wall)
    west_jamb = wall.axis[0][0] + opening.center_along_m - opening.width_m / 2
    assert max(x for x, _ in box.footprint + box.plate_footprint) < west_jamb
    assert box.support_kind == "stud_side" and box.support_fault is None


def test_original_study2_switch_in_leafless_opening_is_reported(catlin_ctx):
    tag = "ED-S-STUDY2-SW"
    body = next(b for b in catlin_ctx.model.canvas_objects if b.tag == tag)
    shift = inch(13.75 - 8.5).meters
    original = replace(body, position=(body.position[0] + shift, body.position[1]),
                       footprint=tuple((x + shift, y) for x, y in body.footprint))
    box = boxes_by_device(catlin_ctx.model)[tag]
    original_box = replace(
        box, face_point=(box.face_point[0] + shift, box.face_point[1]),
        footprint=tuple((x + shift, y) for x, y in box.footprint),
        plate_footprint=tuple((x + shift, y) for x, y in box.plate_footprint))
    model = replace(catlin_ctx.model, canvas_objects=[original], device_boxes=[original_box])
    findings = wall_device_opening(replace(catlin_ctx, model=model))
    assert any(f.result == Result.FAIL and f.element_tags == (
        tag, "D-S-STUDY2", "W-S-SS1") for f in findings)
