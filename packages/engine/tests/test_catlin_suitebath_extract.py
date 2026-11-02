"""The suite-bath extract has a buildable high-wall connection, away from wet floors."""

import pytest
from shapely.geometry import Point, Polygon

from typehaus import MountKind
from typehaus.checks.mep.duct_connectivity import duct_connectivity
from typehaus.checks.mep.fitting_pattern import fitting_pattern
from typehaus.checks.mep.framing_envelope import member_footprint
from typehaus.checks.mep.riser_through_deck import riser_through_deck
from typehaus.checks.mep.routing_bores import run_through_plate, run_through_stud
from typehaus.checks.mep.routing_ceiling import run_in_finished_volume
from typehaus.checks.mep.routing_members import run_member_crossing
from typehaus.checks.mep.routing_openings import run_through_opening
from typehaus.checks.mep.run_interference import run_interference
from typehaus.checks.mep.terminal_necks import terminal_neck_fit
from typehaus.findings import Result
from typehaus.model.enums import DuctSystem
from typehaus.quantities import inch
from typehaus.resolve.terminal_necks import neck_boxes

REGISTER = "REG-S-EXH3"
DUCT = "DU-M-ERV-R-SUITEBATH"


def test_extract_identity_airflow_and_high_wall_mount(catlin_plan, catlin_model_ro):
    register = catlin_plan.by_tag(REGISTER)
    duct = catlin_plan.by_tag(DUCT)
    assert register.uid == "CSRV03AAAA" and duct.uid == "DPAS57TPCG"
    assert register.kind is DuctSystem.EXHAUST
    assert register.room == "RM-S-SUITEBATH" and register.duct_ref == DUCT
    assert register.design_cfm == duct.design_cfm == 20
    catalog = next(t for t in catlin_plan.library.register_types if t.tag == register.type_ref)
    assert catalog.product_ref == "PROD-AIR-DISC-VALVE-100"
    assert catalog.neck.product_ref == "PROD-AIR-SUITEBATH-BOOT"
    assert any(part.product_ref == catalog.neck.product_ref for part in catalog.parts)
    assert register.mount.kind is MountKind.WALL
    assert register.mount.elevation.meters >= inch(95).meters
    attachment = register.location.attachment
    assert attachment.wall_ref == "W-S-DC2" and attachment.face == "right"
    obj = next(o for o in catlin_model_ro.canvas_objects if o.tag == REGISTER)
    wall = catlin_model_ro.wall(attachment.wall_ref)
    assert min(x for x, _y in obj.footprint) > wall.axis[0][0]
    assert obj.position[1] == pytest.approx(inch(196).meters)


def test_riser_meets_the_boot_bottom_inside_a_drawn_deck_hole(catlin_model_ro):
    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == DUCT)
    _tag, ring, bottom, top, _part = next(b for b in neck_boxes(model) if b[0] == REGISTER)
    # Bottom-entry boots use the legacy neck envelope: check the physical mouth in 3D,
    # since TerminalNeckInlet currently describes horizontal approaches only.
    assert duct.z_m[-1] == pytest.approx(bottom)
    assert duct.path[-2] == duct.path[-1]
    assert duct.z_m[-2] < bottom
    assert duct.diameter_m == pytest.approx(inch(4).meters)
    mouth = Point(duct.path[-1]).buffer(duct.diameter_m / 2)
    assert Polygon(ring).buffer(1e-9).covers(mouth)
    assert top - bottom == pytest.approx(inch(8).meters)
    obj = next(o for o in model.canvas_objects if o.tag == REGISTER)
    assert max(x for x, _y in ring) == pytest.approx(min(x for x, _y in obj.footprint))
    floor = next(f for f in model.floors if f.tag == "FS-S-WEST")
    hole = next(ring for tag, ring, names in floor.penetrations
                if tag == "FO-S-ERV-SUITEBATH" and DUCT in names)
    assert Polygon(hole).contains(mouth)
    assert not any("FO-S-ERV-SUITEBATH" in m.child_key for m in floor.members)
    assert model.plan.by_tag("FO-S-ERV-SUITEBATH").cuts_ceiling_below is False
    assert len([c for c in model.ceilings if c.room_ref == "RM-M-CLOSET"]) == 1


def test_full_riser_clears_backing_studs_and_top_plates(catlin_model_ro):
    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == DUCT)
    column = Point(duct.path[-1]).buffer(duct.diameter_m / 2)
    wall = model.wall("W-S-DC2")
    # Bores grade studs and top plates; this also catches the robe-peg backing that
    # ruled out the originally proposed station. The bottom plate has an authored bore.
    for member in wall.members:
        if member.child_key == "plate-bottom":
            continue
        shape = member_footprint(member)
        if shape is None:
            continue
        footprint, low, high = shape
        if min(duct.z_m[-1], high) > max(duct.z_m[-2], low):
            assert column.intersection(footprint).area < 1e-10, member.child_key
    _tag, _ring, _bottom, top, _part = next(b for b in neck_boxes(model) if b[0] == REGISTER)
    assert min(m.z0_m for m in wall.members if "plate-top" in m.child_key) - top >= inch(.5).meters


@pytest.mark.parametrize("check", [
    duct_connectivity, terminal_neck_fit, fitting_pattern, riser_through_deck,
    run_through_stud, run_through_plate, run_member_crossing, run_through_opening,
    run_in_finished_volume, run_interference,
], ids=lambda check: check.__name__)
def test_direct_checks_cannot_hide_a_bad_connection(catlin_ctx, check):
    findings = [f for f in check(catlin_ctx) if {REGISTER, DUCT}.intersection(f.element_tags)]
    assert all(f.result in (Result.PASS, Result.NOT_APPLICABLE) for f in findings), [
        f.message for f in findings]
    if check in (duct_connectivity, terminal_neck_fit, run_through_stud):
        assert findings, "the connection must be graded, not silently omitted"
