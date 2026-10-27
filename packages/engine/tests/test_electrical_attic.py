"""Catlin's attic power serves reachable walls and keeps the eave question visible."""

import pytest

from typehaus.checks import run_from_model
from typehaus.emit.draw.electricalplan import build_electrical_plan
from typehaus.emit.draw.scene import Text
from typehaus.resolve.roof_geometry import roof_slope_factor, roof_underside_at
from typehaus.takeoff.electrical import panel_schedule
from typehaus.takeoff.placeables import placeables_takeoff

REMOVED = {
    "ED-A-EAST-RC5", "ED-A-EAST-RC7", "ED-A-STUDY-RC2",
    "ED-A-STUDIO-RC8", "ED-A-STUDIO-RC9",
}
MOVED = {
    "ED-A-STUDIO-RC1": ("923GJB648D", "W-A-S1", "left", 72, 6),
    "ED-A-STUDIO-RC7": ("NZQNA1VMKW", "W-A-STU-N", "right", 72, 6),
    "ED-A-STUDY-RC1": ("NEC056AAAA", "W-A-S3", "left", 144, 30),
    "ED-A-POCKET-RC1": ("E6RNBJBD76", "W-A-BA-E", "right", 36, 9.728333333),  # on the painted face
}


def test_attic_boxes_move_to_walls_without_changing_identity_or_protection(catlin_model_ro):
    model = catlin_model_ro
    devices = {e.tag: e for e in model.plan.storey_elements("attic")
               if e.element_kind == "ElectricalDevice"}
    objects = {item.tag: item for item in model.canvas_objects}
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    assert REMOVED.isdisjoint(devices)
    assert REMOVED.isdisjoint(objects)
    for tag, (uid, wall, face, station, x_ft) in MOVED.items():
        device = devices[tag]
        assert device.uid == uid
        assert device.mount.kind.value == "wall"
        assert device.mount.elevation.inches == 16
        assert device.circuit == "CKT-RC-ATTIC"
        attachment = device.location.attachment
        assert (attachment.wall_ref, attachment.face) == (wall, face)
        assert attachment.distance_from_start.inches == station
        body = objects[tag]
        assert body.position[0] / .3048 == pytest.approx(x_ft)
        room = next(r for r in model.rooms if r.tag == body.room)
        lining = next(c.layers for c in model.ceilings if c.room_ref == room.tag)
        lining_vertical_m = (sum(layer.thickness.meters for layer in lining)
                             * roof_slope_factor(roof))
        assert body.body_z1_m < min(roof_underside_at(model, roof, xy) - lining_vertical_m
                                   for xy in body.footprint)
    assert devices["ED-A-STUDIO-RC7"].kind.value == "gfci"
    assert devices["ED-A-STUDIO-RC7"].type_ref == "ED-T-LEV-GFCI-15"
    floor_boxes = [d.tag for d in devices.values() if d.mount and d.mount.kind.value == "floor"]
    assert floor_boxes == []


def test_attic_drawing_and_schedules_follow_the_authored_layout(catlin_model_ro):
    model = catlin_model_ro
    labels = [node.content for node in build_electrical_plan(model, "attic").nodes
              if isinstance(node, Text)]
    assert all(tag.removeprefix("ED-") not in labels for tag in REMOVED)
    assert all(tag.removeprefix("ED-") in labels for tag in MOVED)
    assert not any(label.startswith("FLOOR BOX /") for label in labels)
    circuit = next(row for row in panel_schedule(model) if row["circuit"] == "CKT-RC-ATTIC")
    assert REMOVED.isdisjoint(circuit["devices"])
    assert set(MOVED) <= set(circuit["devices"])
    takeoff_tags = {tag for row in placeables_takeoff(model) if row["storey"] == "attic"
                    for tag in row["tags"]}
    assert REMOVED.isdisjoint(takeoff_tags)
    assert set(MOVED) <= takeoff_tags


def test_attic_protection_holds_and_no_attic_floor_box_remains(catlin_model_ro):
    checks = ("electrical.circuit_refs", "code.E3902_16_afci", "code.E3902_gfci_locations",
              "code.E3905_7_floor_boxes")
    findings = run_from_model(catlin_model_ro, [], only=checks).findings
    assert not [f.message for f in findings if f.result.value == "fail"]
    attic_floor_findings = [f for f in findings if f.check_id == "code.E3905_7_floor_boxes"
                           and any(tag.startswith("ED-A-") for tag in f.element_tags)]
    assert attic_floor_findings == []
