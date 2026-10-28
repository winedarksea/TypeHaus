"""Door/window corrections preserve wall-space coverage and required illumination."""

from dataclasses import replace
from math import dist

import pytest

from typehaus.checks.code.mn_residential.ventilation import habitable_light_and_ventilation
from typehaus.checks.mep.electrical import receptacle_spacing, room_lighting
from typehaus.checks.mep.electrical_openings import wall_device_opening
from typehaus.findings import Result
from typehaus.model import inch

_CORRECTED_DEVICES = {
    "ED-M-LIVING-RC10", "ED-M-LIVING-KGF7", "ED-M-LIVING-RC7", "ED-M-STUDY-SPOT",
    "ED-M-STUDY-SW", "ED-S-SUITEBATH-SW", "ED-S-SUITE-RC8", "ED-A-STUDY-LT",
    "ED-A-STUDY-SW", "ED-A-STAIR-RC1", "ED-A-STUDIO-WALL3", "ED-A-STUDIO-SW",
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
    for check in (room_lighting, habitable_light_and_ventilation):
        findings = [f for f in check(catlin_ctx) if "RM-M-STUDY" in f.element_tags]
        assert findings and all(f.result == Result.PASS for f in findings)


def test_attic_study_outlet_is_standard_15a_duplex(catlin_plan):
    outlet = next(element for element in catlin_plan.all_elements()
                  if element.tag == "ED-A-STAIR-RC1")
    assert outlet.type_ref == "ED-T-LEV-DUPLEX-15"
    assert outlet.circuit == "CKT-RC-ATTIC"
    assert outlet.mount.elevation.meters == pytest.approx(inch(12).meters)
    assert outlet.location.attachment.wall_ref == "W-A-C1"
