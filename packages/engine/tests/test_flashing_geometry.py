"""Water-plane placement, true sheet thickness, cutouts, and emitter contracts."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from typehaus.model import (
    Building,
    DoorType,
    Flashing,
    FormedFlashingSection,
    Library,
    PlanModel,
    Project,
    Site,
    Storey,
    m,
    pt,
)
from typehaus.model.enums import DoorOperation
from typehaus.resolve.flashing_caps import brace_cap_mesh, clipped_sheet, formed_run_mesh
from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.geometry_build import build_geometry
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.resolve.opening_flashing import (
    OpeningFlashingFrame,
    opening_flashing_frame,
    opening_flashing_meshes,
    resolve_opening_flashing,
)
from typehaus.resolve.sheet_geometry import extruded_quad, polygon_sheet
from typehaus.takeoff.edge_trim import edge_trim_takeoff
from typehaus.takeoff.framing import structural_solids_takeoff
from typehaus.takeoff.openings import opening_takeoff


def _plan():
    return PlanModel(
        project=Project(name="flashing", project_uuid="00000000-0000-0000-0000-000000000044",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(door_types=(DoorType(tag="OH", width=m(1), height=m(2),
                                           operation=DoorOperation.OVERHEAD),)),
        elements={"main": ()})


def _wall(angle=0.0, reversed_axis=False, exterior=True):
    def point(x, y):
        return (math.cos(angle) * x - math.sin(angle) * y,
                math.sin(angle) * x + math.cos(angle) * y)

    def layer(name, fn, lo, hi):
        return ResolvedLayer(name, name, fn, hi - lo,
                             [point(x, y) for x, y in ((0, lo), (4, lo), (4, hi), (0, hi))])

    axis = (point(0, 0), point(4, 0))
    layers = (layer("stud", "structure", -0.05, 0.05),
              layer("ply", "sheathing", 0.05, 0.06))
    if exterior:
        layers += (layer("skin", "cladding", 0.06, 0.08),)
    return ResolvedWall("wall", "W", "main", "TEST", axis[::-1] if reversed_axis else axis,
                        layers, 0.0, 3.0)


def _opening(kind="window", **kw):
    return ResolvedOpening("opening", "O", "W", None, 1, 1.2, 0.8, 2, kind, kind == "door", **kw)


def _signed_volume(mesh):
    total = 0
    for i, j, k in mesh.triangles:
        a, b, c = (mesh.positions[n] for n in (i, j, k))
        total += (a[0] * (b[1] * c[2] - b[2] * c[1])
                  + a[1] * (b[2] * c[0] - b[0] * c[2])
                  + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return total


@pytest.mark.parametrize("angle", [0, math.pi / 2, 0.63])
@pytest.mark.parametrize("reverse", [False, True])
def test_opening_faces_follow_the_resolved_stack_in_any_orientation(angle, reverse):
    wall = _wall(angle, reverse)
    model = ResolvedModel(_plan(), walls=[wall])
    frame = opening_flashing_frame(model, wall)
    assert frame is not None
    assert frame.outward == pytest.approx((-math.sin(angle), math.cos(angle)))
    assert frame.mount == pytest.approx(0.06)
    assert frame.clad == pytest.approx(0.08)
    meshes = opening_flashing_meshes(wall, _opening(), frame)
    assert len(meshes) == 3
    assert all(_signed_volume(mesh) > 0 for _, _, _, mesh in meshes)


def test_outie_pan_stays_behind_cladding_and_uses_real_membrane_thickness():
    frame = OpeningFlashingFrame((0, 0), (1, 0), (0, 1), 0.06, 0.16, 0.21, 0.24, True)
    meshes = opening_flashing_meshes(_wall(), _opening(), frame)
    _, _, _, pan = meshes[-1]
    assert max(y for _, y, _ in pan.positions) <= frame.mount + FLASHING.sill_membrane_m
    assert max(y for _, y, _ in pan.positions) < frame.clad
    # First sheet is the back dam: opposite surfaces are one 60-mil film apart.
    a, b = pan.positions[0], pan.positions[4]
    assert math.dist(a, b) == pytest.approx(FLASHING.sill_membrane_m)
    assert min(z for _, _, z in pan.positions) < _opening().sill_m


def test_arched_membrane_follows_the_opening_head():
    frame = OpeningFlashingFrame((0, 0), (1, 0), (0, 1), 0, 0.1, 0.2, 0.24, True)
    meshes = opening_flashing_meshes(_wall(), _opening(arch_rise_m=0.2), frame)
    membrane = meshes[1][-1]
    assert len(membrane.triangles) > 100
    assert _signed_volume(membrane) > 0


def test_no_interior_or_bare_opening_flashing_and_no_overhead_pan():
    model = ResolvedModel(_plan(), walls=[_wall(exterior=False)], openings=[_opening()])
    resolve_opening_flashing(model)
    assert model.solids == []
    model.walls = [_wall()]
    model.openings = [_opening("rough_opening")]
    resolve_opening_flashing(model)
    assert model.solids == []
    model.openings = [replace(_opening("door"), type_ref="OH")]
    resolve_opening_flashing(model)
    assert {s.category for s in model.solids} == {
        "opening_head_flashing", "opening_flashing_membrane"}


def test_sheet_cutouts_preserve_area_and_outward_winding():
    # The two holes leave a sheet area of 8 - 1 - 0.25.
    rings = [[(0, 0), (4, 0), (4, 2), (0, 2)],
             [(1, 0.5), (2, 0.5), (2, 1.5), (1, 1.5)],
             [(3, 0.5), (3.5, 0.5), (3.5, 1), (3, 1)]]
    mesh = polygon_sheet(rings, lambda x, y: (x, y, 0), (0, 0, 0.01))
    assert _signed_volume(mesh) == pytest.approx(6.75 * 0.01)
    obstacle = extruded_quad(((1, 0.5, -1), (2, 0.5, -1), (2, 1.5, -1), (1, 1.5, -1)),
                             (0, 0, 2))
    clipped = clipped_sheet((0, 0, 0), (0, 2, 0), (4, 0, 0), 0.01, [obstacle])
    assert _signed_volume(clipped) == pytest.approx(7 * 0.01)


def test_reversing_a_formed_run_does_not_move_either_sheet_face():
    element = Flashing(uid="edge", tag="TR", path=(pt(m(0), m(0)), pt(m(2), m(0))),
                       top_elevation=m(1), thickness=m(0.2), depth=m(0.1),
                       section=FormedFlashingSection(profile="counter", slope=0.25 / 12))
    reversed_element = element.model_copy(update={"path": element.path[::-1], "back_side": "right"})
    mesh = formed_run_mesh(element, element.path[0].xy_m, element.path[1].xy_m)
    reverse_mesh = formed_run_mesh(reversed_element, element.path[1].xy_m, element.path[0].xy_m)
    def rounded(mesh):
        return {tuple(round(value, 9) for value in p) for p in mesh.positions}
    assert rounded(mesh) == rounded(reverse_mesh)
    assert _signed_volume(mesh) == pytest.approx(_signed_volume(reverse_mesh))


def test_fitted_cap_and_openings_do_not_change_the_volume_bill(catlin_model_ro):
    model = catlin_model_ro
    sheets = [s for s in model.solids if s.category in {
        "opening_head_flashing", "opening_sill_pan", "opening_flashing_membrane"}
        or s.tag == "TR-BW-SCREEN-CAP"]
    baseline = replace(model, solids=[s for s in model.solids if s not in sheets])
    assert structural_solids_takeoff(model) == structural_solids_takeoff(baseline)
    assert opening_takeoff(model) == opening_takeoff(baseline)
    caps = [s for s in sheets if s.tag == "TR-BW-SCREEN-CAP"]
    assert len(caps) == 1
    cap = caps[0]
    assert cap.host_ref == "SB-BW-BAND"
    assert cap.material == "metal-dark-exterior"
    assert len(cap.body_mesh.triangles) > 100  # fitted around wood and steel, not a plain box
    rows = [r for r in edge_trim_takeoff(model) if cap.tag in r["tags"]]
    assert len(rows) == 1
    assert rows[0]["count"] == 1
    assert rows[0]["length_ft"] > 0
    for tag in ("D-M-ENTRY", "D-G-SERVICE"):
        assert {s.category for s in sheets if s.host_ref == tag} == {
            "opening_head_flashing", "opening_sill_pan", "opening_flashing_membrane"}


def test_screen_cap_falls_west_and_clears_the_centre_post_without_moving_wood(catlin_model_ro):
    from shapely.geometry import Polygon

    model = catlin_model_ro
    element = model.plan.by_tag("TR-BW-SCREEN-CAP")
    brace = next(b for b in model.braces if b.tag == element.host_ref)
    members = brace.members
    sill = next(m for m in members if m.child_key == "plate-sill")
    post = next(m for m in members if m.child_key == "post-centre")
    mesh = brace_cap_mesh(model, element, element.section)
    assert brace.members is members
    west = element.path[0].x.meters - element.thickness.meters / 2
    east = west + element.thickness.meters
    assert west < min(x for x, _y in next(w for w in model.walls
                                        if w.tag == "W-BW-SCREEN").layers[-1].polygon)
    slope = element.section.slope
    top_triangles = []
    for triangle in mesh.triangles:
        points = [mesh.positions[i] for i in triangle]
        residual = [z - sill.z1_m - (x - west) * slope for x, _y, z in points]
        if max(abs(r) for r in residual) < 1e-8:
            top_triangles.append(Polygon([(x, y) for x, y, _z in points]))
    assert top_triangles
    assert max(z for x, _y, z in mesh.positions if abs(x - east) < 1e-7) > \
        max(z for x, _y, z in mesh.positions if abs(x - west) < 1e-7)
    from typehaus.resolve.geometry_members import member_box

    footprint = Polygon([(x, y) for x, y, _z in member_box(post).corners_bottom])
    assert all(tri.intersection(footprint).area < 1e-10 for tri in top_triangles)


def test_shared_mesh_reaches_ir_json_glb_and_ifc(tmp_path):
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.ifc import emit_ifc
    from typehaus.server.model_json_fabric import shell_json

    model = ResolvedModel(_plan(), walls=[_wall()], openings=[_opening()])
    resolve_opening_flashing(model)
    model.geometry = build_geometry(model)
    payload = shell_json(model, None)
    for solid in model.solids:
        assert model.geometry.by_uid(solid.uid).parts[0].solids == (solid.body_mesh,)
        record = next(s for s in payload["solids"] if s["uid"] == solid.uid)
        assert record["body_mesh"]["positions"] == [list(p) for p in solid.body_mesh.positions]
        assert record["host_ref"] == "O"
    gltf, _ = emit_gltf_dict(model)
    nodes = [n for n in gltf["nodes"] if n.get("extras", {}).get("uid") in
             {s.uid for s in model.solids}]
    assert {n["extras"]["category"] for n in nodes} == {s.category for s in model.solids}
    path = emit_ifc(model, tmp_path / "flashing.ifc")
    import ifcopenshell

    file = ifcopenshell.open(str(path))
    coverings = file.by_type("IfcCovering")
    assert len(coverings) == 3
    assert all(c.Representation.Representations[0].RepresentationType == "Tessellation"
               for c in coverings)


def test_bad_formed_sections_fail_at_authoring():
    with pytest.raises(ValueError, match="positive"):
        FormedFlashingSection(sheet_thickness=m(0))
    with pytest.raises(ValueError):
        FormedFlashingSection(slope=-1)
