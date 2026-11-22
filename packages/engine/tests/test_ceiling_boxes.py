"""Ceiling boxes only where a fixture mounts to one (decision #140)."""

from __future__ import annotations

from dataclasses import replace
from math import isclose
from types import SimpleNamespace

from typehaus.findings import Result


def _boxes(model):
    return {b.device_tag: b for b in model.device_boxes if b.host == "ceiling"}


def test_a_fan_takes_the_fan_rated_brace_box_on_the_finished_ceiling(catlin_model_ro):
    box = _boxes(catlin_model_ro)["ED-M-BED-FAN"]
    ceiling = next(c for c in catlin_model_ro.ceilings if c.room_ref == "RM-M-BED")
    assert (box.box_product, box.box_use, box.mounting) == ("PROD-RACO-929", "fan", "flush")
    assert box.wall_tag is None and box.axis == (0.0, 0.0, -1.0)
    assert abs(box.z0_m - ceiling.z0_m) < 1e-6  # face on the board, body up into the bay


def test_housings_wafers_psu_fittings_and_battery_sensors_take_none(catlin_model_ro):
    boxes = _boxes(catlin_model_ro)
    for tag in ("ED-M-LIVING-LT", "ED-S-NCLOSET-LT", "AL-G-FREEZE"):
        assert tag not in boxes, tag
    assert boxes["AL-M-BED"].box_use == "ceiling"  # the alarm row falls back to "ceiling"


def test_keyless_lampholders_seat_against_flat_and_sloped_boxes(catlin_model_ro):
    boxes = _boxes(catlin_model_ro)
    solids = {solid.uid: solid for solid in catlin_model_ro.solids}
    product = next(product for product in catlin_model_ro.plan.library.electrical_device_types
                   if product.tag == "ED-T-LT-KEYLESS")
    tested_slopes = set()
    for item in catlin_model_ro.canvas_objects:
        if item.type_ref != product.tag:
            continue
        box = boxes[item.tag]
        frame = item.model_frame
        assert frame is not None
        assert frame.up == tuple(-component for component in box.axis)
        mount_point = frame.point(0, 0, product.height.meters)
        box_vertices = solids[box.uid].body_mesh.positions
        box_face = min(sum(a * b for a, b in zip(point, frame.up, strict=True))
                       for point in box_vertices)
        mount_face = sum(a * b for a, b in zip(mount_point, frame.up, strict=True))
        assert isclose(mount_face, box_face, abs_tol=1e-8), item.tag
        tested_slopes.add(frame.up[2] < 1.0)
    assert tested_slopes == {False, True}


def test_fill_oracle_luminaire_takes_no_yoke_and_an_alarm_counts_its_interconnect(
        catlin_model_ro):
    """Hand-worked, 14 AWG in the 21.5 in³ octagon, clamps counted:
    luminaire, through-fed 14/2: 2 x 2 = 4 conductors x 2.00 = 8.00, + EGC 2.00 + clamps
    2.00 = 12.00 in³ (no yoke). Alarm, through-fed 14/3: 2 x 3 = 6 x 2.00 = 12.00 + 2.00 +
    2.00 = 16.00 in³."""
    from typehaus.checks.mep.electrical_boxes import box_fill

    ctx = SimpleNamespace(model=catlin_model_ro, plan=catlin_model_ro.plan)
    found = {f.element_tags[0]: f.message for f in box_fill(ctx) if len(f.element_tags) == 1}
    assert "12.00 in³ of through-fed 14 AWG in 21.5 in³" in found["ED-S-STAIR-CHAND"]
    assert "16.00 in³ of through-fed 14 AWG in 21.5 in³" in found["AL-M-BED"]


class _Only:
    """The catlin model with one box record in place of all of them."""

    def __init__(self, model, box):
        self._model, self.device_boxes = model, [box]

    def __getattr__(self, name):
        return getattr(self._model, name)


def test_a_box_on_a_joist_fails_with_a_shift_and_a_pancake_under_it_passes(catlin_model_ro):
    from shapely.affinity import translate
    from shapely.geometry import Polygon

    from typehaus.checks.mep.electrical_ceiling import ceiling_box_framing
    from typehaus.checks.mep.framing_envelope import member_footprint

    box = _boxes(catlin_model_ro)["ED-M-BED-FAN"]
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    joist = next(m for m in floor.members if m.child_key == "joist-0-005-0")
    target = member_footprint(joist)[0].centroid
    ring = Polygon(box.footprint)
    moved = translate(ring, target.x - ring.centroid.x, target.y - ring.centroid.y)
    on_joist = replace(box, footprint=tuple(moved.exterior.coords)[:-1])

    def grade(record):
        ctx = SimpleNamespace(model=_Only(catlin_model_ro, record), plan=catlin_model_ro.plan)
        return ceiling_box_framing(ctx)[0]

    clash = grade(on_joist)
    assert clash.result is Result.FAIL and "joist-0-005-0" in clash.message
    assert "move ED-M-BED-FAN" in clash.fix_hint and '"' in clash.fix_hint
    pancake = replace(on_joist, z1_m=on_joist.z0_m + 0.0127, depth_m=0.0127, box_use="pancake")
    assert grade(pancake).result is Result.PASS


def test_a_remote_box_hangs_from_the_nearest_member_clear_of_the_fitting(catlin_model_ro):
    """The garden flood (``remote_box``) takes its junction box beside it, not over it."""
    from shapely.geometry import LineString, Point, Polygon

    box = _boxes(catlin_model_ro)["ED-M-PORCH-FLOOD"]
    flood = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-M-PORCH-FLOOD")
    floor_tag, key = box.host_layer.split("/")
    floor = next(f for f in catlin_model_ro.floors if f.tag == floor_tag)
    member = next(m for m in floor.members if m.child_key == key)
    assert (box.mounting, box.box_product) == ("surface", "PROD-BELL-5361-0")
    assert LineString([member.p0, member.p1]).distance(Point(box.face_point)) < 1e-6
    assert abs(box.z1_m - member.z0_m) < 1e-6  # screwed to the underside, hanging below
    assert not Polygon(box.footprint).intersects(Polygon(flood.footprint))


def test_a_fan_under_a_bare_deck_hangs_its_box_from_the_joist_over_it(catlin_model_ro):
    """No lining over the porch fan: a surface fan box under the joist covering its point."""
    box = _boxes(catlin_model_ro)["ED-M-PORCH-FAN"]
    fan = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-M-PORCH-FAN")
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-BALCONY")
    joist = next(m for m in floor.members if m.child_key == "joist-0-005-0")
    assert (box.mounting, box.box_product, box.box_use) == (
        "surface", "PROD-BELL-PRCF57550BZ", "fan")
    assert box.host_layer == "FS-SG-BALCONY/joist-0-005-0"
    assert abs(box.face_point[1] - joist.p0[1]) < 1e-6  # on the joist's centreline
    assert abs(box.z1_m - joist.z0_m) < 1e-6
    assert abs(fan.body_z1_m - box.z0_m) < 0.002  # the canopy hangs from the box face
