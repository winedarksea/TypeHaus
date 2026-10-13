"""The court's hanging daybed hangs clear of the walls, the patio door and the court's other
objects, from two derived 3-ply porch lines (``houses/catlin/notes/court_daybed_anchor.md``)."""

from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon

from typehaus.checks.structural.suspension_anchor import suspension_anchor
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.takeoff.hangers import joist_hanger_rows
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.placeables import placeables_takeoff

BED = "FURN-SG-DAYBED"
ANCHORS = ("HA-SG-DAYBED-SW", "HA-SG-DAYBED-SE", "HA-SG-DAYBED-NE", "HA-SG-DAYBED-NW")


def _bed(model):
    return next(item for item in model.canvas_objects if item.tag == BED)


def _wall_faces(model, tag):
    wall = model.wall(tag)
    return [Polygon(layer.polygon) for layer in wall.depth_layers() if len(layer.polygon) >= 3]


def test_body_and_sway_clear_the_walls_the_door_and_the_court(catlin_model_ro):
    bed = _bed(catlin_model_ro)
    body, [sway] = Polygon(bed.footprint), bed.recommended_clearances
    sway = Polygon(sway)
    for tag in ("W-SG-W1", "W-B-BRICK"):
        assert all(face.distance(sway) > 0 for face in _wall_faces(catlin_model_ro, tag)), tag
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-B-PATIO")
    assert Polygon(door.swing_clearance).distance(sway) >= inch(12).meters
    for other in catlin_model_ro.canvas_objects:
        if other.tag == BED or other.storey not in ("court-low", "court-main"):
            continue
        assert sway.intersection(Polygon(other.footprint)).area < 1e-8, other.tag
        for zone in (*other.required_clearances, *other.recommended_clearances):
            assert body.intersection(Polygon(zone)).area < 1e-8, other.tag


def test_the_four_anchors_frame_lines_003_and_006(catlin_model_ro):
    records = {r.tag: r for r in catlin_model_ro.suspension_anchors if r.tag in ANCHORS}
    assert {tag: (r.floor, r.line_key, r.reason) for tag, r in records.items()} == {
        "HA-SG-DAYBED-SW": ("FS-SG-PORCH", "003", None),
        "HA-SG-DAYBED-SE": ("FS-SG-PORCH", "003", None),
        "HA-SG-DAYBED-NE": ("FS-SG-PORCH", "006", None),
        "HA-SG-DAYBED-NW": ("FS-SG-PORCH", "006", None)}
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-PORCH")
    built = {m.child_key: m.p0[1] for m in floor.members
             if m.category == "joist" and m.profile == "3-2x12:kdat"}
    assert built == {"joist-0-003-0": pytest.approx(inch(-77.25).meters),
                     "joist-0-006-0": pytest.approx(inch(-41.25).meters)}


def test_the_check_passes_on_the_west_hanger(catlin_plan, catlin_model_ro):
    prefs = SimpleNamespace(structural=SimpleNamespace(hanging_seat_impact_factor=2.0))
    ctx = SimpleNamespace(plan=catlin_plan, model=catlin_model_ro, preferences=prefs)
    findings = [f for f in suspension_anchor(ctx)
                if set(f.element_tags) & {BED, *ANCHORS}]
    assert len(findings) == 4
    for finding in findings:
        assert finding.result is Result.PASS, finding.message
        assert "Governs: LUS210-3Z at BM-SG-LDGW (C_M 0.7) 0.88" in finding.message


def test_the_daybed_bills_its_bed_and_hardware(catlin_model_ro):
    rows = [row for row in placeables_takeoff(catlin_model_ro) if BED in row["tags"]]
    assert [row["count"] for row in rows] == [1]
    parts = {row["part_number"]: row["count"] for row in hardware_takeoff(catlin_model_ro)
             if row["scope"] == "suspension anchor"}
    assert parts == {"3-S-5": 1, "SADDLE-3.5-2x58": 1, "G-209-1/2": 4,
                     "SADDLE-4.5-2x58-HDG": 4}
    hung = {}
    for row in joist_hanger_rows(catlin_model_ro, _rules()):
        if row["size"] in ("2x12:kdat", "3-2x12:kdat"):
            hung[row["part_number"]] = hung.get(row["part_number"], 0) + row["count"]
    assert hung == {"LUS210SS": 16, "LUS210-3Z": 4}


def _rules():
    from typehaus.hardware.config import HangerDetectionRules

    return HangerDetectionRules()


def test_each_rope_is_within_the_kit(catlin_plan, catlin_model_ro):
    bed = _bed(catlin_model_ro)
    seat = next(t for t in catlin_plan.library.furniture_types if t.tag == bed.type_ref)
    lo, hi = (x.meters for x in seat.suspension_range)
    assert len(bed.suspension_points) == 4 and bed.suspended_from == "FS-SG-PORCH"
    for _, _, cable in bed.suspension_points:
        assert lo <= cable <= hi
        assert cable == pytest.approx(inch(51.1875).meters, abs=1e-4)
