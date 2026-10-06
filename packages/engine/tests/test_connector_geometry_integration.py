"""Installed connector bodies, picking bounds and export parity on the shared house."""

import math

import pytest

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.joints import derived_joints
from typehaus.joints.model import marker_uid
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.fasteners import fastener_mesh
from typehaus.resolve.connector_geometry.placement import ConnectorPlacementIndex

SIMPSON_PREFIXES = ("LUS", "IUS", "LSSR", "LSC", "THA", "HU", "HHUS", "H2.5", "H10",
                    "ABU", "CBSQ", "CCQ", "PC", "AC", "ACE", "HL", "L50", "STHD",
                    "HETA", "MASA", "DTT", "LSTA", "MSTA", "LTP", "A35", "LS30", "KBS", "THD")


def _simpson_solids(model):
    return [solid for solid in model.solids if solid.category.startswith("connector")
            and (solid.product or "").startswith(SIMPSON_PREFIXES)]


def test_every_displayed_simpson_connector_has_a_dimensioned_body(catlin_model_ro):
    solids = _simpson_solids(catlin_model_ro)
    assert len(solids) > 600
    assert all(solid.body_mesh and solid.body_mesh.triangles for solid in solids)
    assert {"LUS", "LUSZ", "THA422", "ABU44", "LTP4", "THD50600H6SS"} <= {
        solid.product for solid in solids}


def test_connector_picking_bounds_follow_actual_meshes(catlin_model_ro):
    for solid in _simpson_solids(catlin_model_ro):
        xs, ys, zs = zip(*solid.body_mesh.positions, strict=True)
        assert all(math.isfinite(value) for point in solid.body_mesh.positions for value in point)
        assert solid.z0_m == pytest.approx(min(zs)), solid.tag
        assert solid.z1_m == pytest.approx(max(zs)), solid.tag
        assert min(x for x, _ in solid.outline) == pytest.approx(min(xs)), solid.tag
        assert max(y for _, y in solid.outline) == pytest.approx(max(ys)), solid.tag


def test_hanger_seats_use_carried_member_ends_and_face_into_them(catlin_model_ro):
    index = ConnectorPlacementIndex(catlin_model_ro)
    solids = {solid.uid: solid for solid in _simpson_solids(catlin_model_ro)}
    tested = []
    for joint in derived_joints(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG):
        if joint.outward_xy is None or marker_uid(joint.key) not in solids:
            continue
        member = index.members[joint.carried_member_key]
        end = min(range(2), key=lambda i: math.dist(joint.point, (member.p0, member.p1)[i]))
        expected_seat = member.z0_m if end == 0 or member.z0_end_m is None else member.z0_end_m
        assert joint.seat_z_m == pytest.approx(expected_seat)
        solid = solids[marker_uid(joint.key)]
        outward = joint.outward_xy
        local = [(sum((p[i] - joint.point[i]) * outward[i] for i in range(2)),
                  p[2] - joint.seat_z_m) for p in solid.body_mesh.positions]
        assert max(y for y, _ in local) > M_PER_IN, solid.tag
        assert any(y > 0 and abs(z - y * math.tan(joint.slope_radians)) < 1e-8
                   for y, z in local), solid.tag
        tested.append(outward)
    assert len(tested) > 50
    assert any(a[0] * b[0] + a[1] * b[1] < -0.99 for a in tested for b in tested)


def test_opposite_ridge_hangers_have_separate_bodies(catlin_model_ro):
    joints = [joint for joint in derived_joints(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG)
              if joint.part == "LSSR"]
    bodies = {solid.uid for solid in _simpson_solids(catlin_model_ro) if solid.product == "LSSR"}
    assert len(joints) == len({joint.key for joint in joints}) == len(bodies)
    assert len(joints) > 30


def test_canopy_joint_straps_follow_the_roof_and_cross_the_garage_joint(catlin_model_ro):
    from typehaus.resolve.roof_geometry import roof_height_at

    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    solids = {s.tag: s for s in catlin_model_ro.solids}
    for station in range(1, 8):
        tag = f"CN-BW-JOINT-{station}"
        element = catlin_model_ro.plan.by_tag(tag)
        solid = solids[tag]
        _, y = element.position.xy_m
        assert element.roof_mount == roof.tag
        assert element.elevation is None
        assert solid.z0_m > roof.bearing_z_m
        assert min(p[1] for p in solid.body_mesh.positions) == pytest.approx(y - 12 * M_PER_IN)
        assert max(p[1] for p in solid.body_mesh.positions) == pytest.approx(y + 12 * M_PER_IN)
        # Both ends sit on the plane: no spurious ridge bend along the strap's length.
        on_plane = [p for p in solid.body_mesh.positions
                    if abs(p[2] - roof_height_at(roof, p[:2])) < 1e-8]
        assert len(on_plane) >= 4, tag
        assert any(p[1] < y for p in on_plane) and any(p[1] > y for p in on_plane), tag


def test_canopy_joint_attachment_gap_matches_the_resolved_truss_layout(catlin_model_ro):
    roofs = {r.tag: r for r in catlin_model_ro.roofs}
    last_canopy_y = max(m.p0[1] for m in roofs["RF-BW-CANOPY"].members
                        if m.category == "roof_truss")
    garage_gable_y = min(m.p0[1] for m in roofs["RF-GARAGE"].members
                         if m.category == "roof_truss")
    strap_y = catlin_model_ro.plan.by_tag("CN-BW-JOINT-6").position.xy_m[1]
    assert strap_y - last_canopy_y == pytest.approx(23.375 * M_PER_IN)
    assert garage_gable_y - last_canopy_y == pytest.approx(24.125 * M_PER_IN)
    assert strap_y - 12 * M_PER_IN > last_canopy_y


def test_derived_lateral_plates_are_on_the_sill_face(catlin_model_ro):
    index = ConnectorPlacementIndex(catlin_model_ro)
    solids = {solid.uid: solid for solid in _simpson_solids(catlin_model_ro)}
    tested = 0
    for joint in derived_joints(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG):
        if joint.role != "lateral_tie_plate":
            continue
        tangent = (0.0, 1.0) if joint.axis == "y" else (1.0, 0.0)
        outward = (-tangent[1], tangent[0])
        width = index.support_width(joint.members[0], tangent, point=joint.point, z_m=joint.z_m)
        solid = solids[marker_uid(joint.key)]
        offsets = [sum((p[i] - joint.point[i]) * outward[i] for i in range(2))
                   for p in solid.body_mesh.positions]
        assert max(offsets) == pytest.approx(-width / 2), solid.tag
        tested += 1
    assert tested > 100


def test_paired_heavy_angles_project_away_from_their_tie_block(catlin_model_ro):
    solids = {solid.tag: solid for solid in catlin_model_ro.solids}
    for beam in ("FC", "FE"):
        left = solids[f"CN-BW-STEMTIE-{beam}-A"].body_mesh
        right = solids[f"CN-BW-STEMTIE-{beam}-B"].body_mesh
        block = solids[f"CN-BW-STEMTIE-{beam}-BLK"]
        west, east = min(x for x, _ in block.outline), max(x for x, _ in block.outline)
        assert max(x for x, _, _ in left.positions) == pytest.approx(west)
        assert min(x for x, _, _ in right.positions) == pytest.approx(east)
        assert min(z for _, _, z in left.positions) == pytest.approx(-12 * M_PER_IN)


def test_wall_end_angles_have_vertical_heels(catlin_model_ro):
    solids = {solid.tag: solid for solid in catlin_model_ro.solids}
    for tag in ("CN-BW-GWTIE-LO", "CN-BW-GWTIE-HI"):
        solid = solids[tag]
        assert solid.z1_m - solid.z0_m == pytest.approx(2.5 * M_PER_IN)
        assert min(y for _, y, _ in solid.body_mesh.positions) < (
            catlin_model_ro.plan.by_tag(tag).position.xy_m[1] - 3 * M_PER_IN)


def test_sill_anchors_use_their_local_run_despite_repeated_detail_tags(catlin_model_ro):
    index = ConnectorPlacementIndex(catlin_model_ro)
    solids = {solid.uid: solid for solid in _simpson_solids(catlin_model_ro)}
    for joint in derived_joints(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG):
        if joint.part != "MASA":
            continue
        run = index.return_at(joint.members[0], joint.point, joint.z_m)
        assert run.z0_m == pytest.approx(joint.z_m)
        mesh = solids[marker_uid(joint.key)].body_mesh
        assert min(math.dist(joint.point, p[:2]) for p in mesh.positions) < 4 * M_PER_IN


def test_derived_post_base_seats_clear_the_timber(catlin_model_ro):
    solids = {solid.tag: solid for solid in catlin_model_ro.solids}
    for tag in ("P-M-STRWELL-S", "P-M-STRWELL-SS"):
        post = solids[tag]
        support = solids[catlin_model_ro.plan.by_tag(tag).supported_by]
        assert post.z0_m - support.z1_m > M_PER_IN


def test_json_and_geometry_ir_share_connector_triangles(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    payload = model_to_dict(catlin_model_ro)
    serialized = {solid["uid"]: solid for solid in payload["solids"]}
    for solid in _simpson_solids(catlin_model_ro):
        body = serialized[solid.uid]["body_mesh"]
        assert tuple(tuple(p) for p in body["positions"]) == solid.body_mesh.positions
        assert tuple(tuple(t) for t in body["triangles"]) == solid.body_mesh.triangles
        element = catlin_model_ro.geometry.by_uid(solid.uid)
        assert any(solid.body_mesh == body for part in element.parts for body in part.solids)


def test_ifc_preserves_dimensioned_connectors_as_tessellation(catlin_model_ro, catlin_ifc_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    exported = ifcopenshell.open(str(catlin_ifc_path))
    fasteners = {element.Name: element for element in exported.by_type("IfcElement")}
    for solid in _simpson_solids(catlin_model_ro):
        body = fasteners[solid.tag].Representation.Representations[0]
        assert body.RepresentationType == "Tessellation", solid.tag
        face_set = body.Items[0]
        assert len(face_set.CoordIndex) == len(solid.body_mesh.triangles)
        assert tuple(tuple(p) for p in face_set.Coordinates.CoordList) == solid.body_mesh.positions


def test_titen_stock_shaft_length_and_wrench_size():
    mesh = fastener_mesh("THD50600H6SS")
    assert min(y for _, y, _ in mesh.positions) == pytest.approx(-6 * M_PER_IN)
    assert max(z for _, y, z in mesh.positions if y > 0) == pytest.approx(0.375 * M_PER_IN)
    assert fastener_mesh("THD50600H4SS") == mesh
    assert fastener_mesh("THD999") is None
