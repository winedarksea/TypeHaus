"""Product shape, physical hose attachment, and export parity without house rebuilds."""

from types import SimpleNamespace
from uuid import UUID

import ifcopenshell
import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.ifc.mep import _emit_pipe_accessories
from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.emit.ifc.structural import _solid_body
from typehaus.library.placeables.fixtures import WALL_HYDRANT, WALL_HYDRANT_SELF_DRAINING
from typehaus.model import PipeAccessory, PipeAccessoryKind, inch, pt
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._yard_hydrant import hose_outlet
from typehaus.model.placeable_symbols._yard_hydrant_config import (
    BREAKER_34HD,
    VACUUM_BREAKER_PRODUCT,
    Y34SS,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.fixture_accessories import resolve_fixture_accessory
from typehaus.resolve.geometry_ir import signed_volume


def _assembly(*, center=(1.0, 2.0), rotation=0.0, floor=-0.6):
    fixture = SimpleNamespace(tag="FX", kind="Fixture", type_ref=WALL_HYDRANT.tag,
                              position=center, rotation_degrees=rotation, body_z0_m=floor,
                              z_m=floor, room="ROOM", mount=None, model_frame=None)
    pipe = SimpleNamespace(tag="PR", system="water_cold", diameter_m=inch(.75).meters,
                           serves=("FX",))
    model = SimpleNamespace(plan=SimpleNamespace(library=SimpleNamespace(
        fixture_types=(WALL_HYDRANT,))), pipe_runs=[pipe], canvas_objects=[fixture],
        pipe_accessories=[], solids=[])
    accessory = PipeAccessory(uid="TESTVB0001", tag="VB", kind=PipeAccessoryKind.VACUUM_BREAKER,
                              fixture_ref="FX", pipe_ref="PR", product_ref=VACUUM_BREAKER_PRODUCT,
                              serves=("FX",))
    return model, accessory


def _parts():
    return model_parts("woodford-y34ss", *(v.meters for v in WALL_HYDRANT.footprint),
                       WALL_HYDRANT.height.meters)


def test_y34ss_has_catalog_dimensions_and_closed_casting_and_linkage():
    parts = _parts()
    points = [p for part in parts for p in part["mesh"]["positions"]]
    assert min(p[2] for p in points) == pytest.approx(0)
    assert max(p[2] for p in points) == pytest.approx(36.5 * M_PER_IN)
    assert parts[0]["size"][:2] == pytest.approx((1.315 * M_PER_IN,) * 2)
    assert len(parts) >= 14
    assert {p["color"] for p in parts} >= {"hydrant-orange", "brass", "metal"}
    for part in parts:
        mesh = part["mesh"]
        assert signed_volume(mesh["positions"], mesh["triangles"]) > 0
        assert len(mesh["normals"]) == len(mesh["positions"])
    # All fixture parts stop at the bare nozzle; the breaker is a separately selected device.
    nozzle = parts[-1]
    outlet, direction = hose_outlet(WALL_HYDRANT.height.meters)
    assert direction == (0, 0, -1)
    assert nozzle["center"][:2] == pytest.approx(outlet[:2])
    assert nozzle["center"][2] - nozzle["size"][2] / 2 == pytest.approx(outlet[2])
    assert outlet[2] == pytest.approx(27.5 * M_PER_IN)


@pytest.mark.parametrize("rotation", [0, 90, 37, 180])
@pytest.mark.parametrize("center,floor", [((1, 2), -.6), ((4, -7), 2.4)])
def test_breaker_tracks_nozzle_translation_rotation_and_floor(rotation, center, floor):
    model, accessory = _assembly(center=center, rotation=rotation, floor=floor)
    assert not resolve_fixture_accessory(model, accessory, "main")
    placed, = model.pipe_accessories
    solid, = model.solids
    local, direction = hose_outlet(WALL_HYDRANT.height.meters)
    expected = place_local([local[:2]], center, rotation)[0]
    assert placed.position == pytest.approx(expected)
    assert placed.z_m == pytest.approx(floor + local[2])
    assert placed.direction == direction
    assert solid.uid == accessory.uid
    assert solid.host_ref == "FX"
    assert solid.body_mesh is not None
    assert solid.z1_m == pytest.approx(placed.z_m + BREAKER_34HD.engagement * M_PER_IN)
    assert solid.z1_m - solid.z0_m == pytest.approx(BREAKER_34HD.length * M_PER_IN)
    # The upper collar overlaps the male thread, rather than floating beyond its end.
    assert solid.z0_m < placed.z_m < solid.z1_m


@pytest.mark.parametrize("changes", [
    {"fixture_ref": "MISSING"}, {"position": pt(inch(0), inch(0))},
    {"elevation": inch(2)}, {"product_ref": "UNKNOWN"},
    {"pipe_ref": "MISSING"}, {"kind": PipeAccessoryKind.SHUTOFF},
])
def test_invalid_attachment_does_not_emit_a_device(changes):
    model, accessory = _assembly()
    findings = resolve_fixture_accessory(model, accessory.model_copy(update=changes), "main")
    assert len(findings) == 1
    assert findings[0].check_id == "integrity.pipe_accessory_attachment"
    assert findings[0].result.value == "fail"
    assert not model.solids and not model.pipe_accessories


@pytest.mark.parametrize("unsupported", ["fixture", "supply"])
def test_attachment_requires_a_supported_hose_outlet_on_the_serving_pipe(unsupported):
    model, accessory = _assembly()
    if unsupported == "fixture":
        model.canvas_objects[0].type_ref = "FX-WALL-HYDRANT"
    else:
        model.pipe_runs[0].serves = ("OTHER",)
    assert resolve_fixture_accessory(model, accessory, "main")
    assert not model.solids


def _bounds(points):
    return tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))


@pytest.mark.parametrize("product", [WALL_HYDRANT, WALL_HYDRANT_SELF_DRAINING])
def test_hydrant_viewer_gltf_and_ifc_use_the_same_product_geometry(product):
    parts = model_parts(product.plan_symbol, *(v.meters for v in product.footprint),
                        product.height.meters)
    viewer = _symbol_geometry(product, product.footprint)["model_parts"]
    assert [p["mesh"] for p in viewer] == [p["mesh"] for p in parts]
    model, _ = _assembly(rotation=37)
    fixture = model.canvas_objects[0]
    builder = _MeshBuilder()
    assert _add_canvas_parts(builder, fixture, product, {})
    gltf = [p for points, _ in builder._buckets.values() for p in points]
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext")
    representation = parts_representation(file, context, parts, fixture.position,
                                          fixture.rotation_degrees, fixture.z_m)
    ifc = [(x, z, -y) for mesh in representation.Items
           for x, y, z in mesh.Coordinates.CoordList]
    for a, b in zip(_bounds(gltf), _bounds(ifc), strict=True):
        assert a == pytest.approx(b)


def test_breaker_ifc_and_gltf_preserve_resolved_mesh_instead_of_marker_box():
    model, accessory = _assembly(rotation=37)
    assert not resolve_fixture_accessory(model, accessory, "main")
    solid, = model.solids
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext")
    representation = _solid_body(file, context, solid)
    assert representation.RepresentationType == "Tessellation"
    mesh, = representation.Items
    assert len(mesh.Coordinates.CoordList) == len(solid.body_mesh.positions)
    builder = _MeshBuilder()
    builder.add_mesh(solid.body_mesh, (1, 1, 1, 1))
    gltf = [p for points, _ in builder._buckets.values() for p in points]
    ifc = [(x, z, -y) for x, y, z in mesh.Coordinates.CoordList]
    for a, b in zip(_bounds(gltf), _bounds(ifc), strict=True):
        assert a == pytest.approx(b)
    storey = file.create_entity("IfcBuildingStorey")
    emitted = _emit_pipe_accessories(file, context, model, {"main": storey},
                                     UUID("c471a000-93b5-4e6e-8f5a-000000000000"))
    _, valve = emitted[0]
    assert len(emitted) == 1
    assert valve.Name == accessory.tag
    assert valve.PredefinedType == "ANTIVACUUM"
    assert valve.Representation.Representations[0].RepresentationType == "Tessellation"


def test_catlin_has_one_attached_breaker_with_retained_identity(catlin_model_ro):
    model = catlin_model_ro
    accessory, = [a for a in model.pipe_accessories if a.tag == "PA-G-HYD-VB"]
    solid, = [s for s in model.solids if s.tag == accessory.tag]
    fixture = next(o for o in model.canvas_objects if o.tag == "FX-G-HYDRANT")
    local, _ = hose_outlet(Y34SS.height * M_PER_IN)
    assert accessory.uid == solid.uid == "J1DS4RQZ8X"
    assert accessory.fixture_ref == fixture.tag
    assert accessory.product_ref == VACUUM_BREAKER_PRODUCT
    assert accessory.pipe_ref == "PR-G-HYDRANT-CW"
    assert accessory.serves == (fixture.tag,)
    assert accessory.position == pytest.approx(place_local(
        [local[:2]], fixture.position, fixture.rotation_degrees)[0])
    assert accessory.z_m == pytest.approx(fixture.z_m + local[2])
    assert solid.body_mesh is not None
    assert solid.z1_m - solid.z0_m < 3 * M_PER_IN


def test_catlin_wall_hydrant_flange_meets_exterior_face_and_barrel_meets_feed(catlin_model_ro):
    from typehaus.model.placeable_symbols._wall_hydrant_config import MODEL_19
    from typehaus.resolve.mep_sleeves import placed_port_point
    from typehaus.resolve.wall_hosting import _finish_offset

    model = catlin_model_ro
    product = WALL_HYDRANT_SELF_DRAINING
    parts = model_parts(product.plan_symbol, *(v.meters for v in product.footprint),
                        product.height.meters)
    barrel, _, flange = parts[:3]
    for tag in ("FX-M-PORCH-HYD", "FX-S-BALCONY-HYD"):
        fixture = next(o for o in model.canvas_objects if o.tag == tag)
        wall = model.wall(model.plan.by_tag(tag).wall_ref)
        (x0, y0), (x1, y1) = wall.axis
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** .5
        left = (-(y1 - y0) / length, (x1 - x0) / length)
        face = _finish_offset(wall, wall.axis[0], left, -1,
                              (fixture.body_z0_m, fixture.body_z1_m))
        flange_back = (0, flange["center"][1] + flange["size"][1] / 2)
        flange_xy, = place_local([flange_back], fixture.position, fixture.rotation_degrees)
        assert sum((v - o) * n for v, o, n in zip(flange_xy, wall.axis[0], left, strict=True)
                   ) == pytest.approx(face)
        axis_z = fixture.z_m + barrel["center"][2]
        port_point = placed_port_point(model, tag, product.ports[0])
        storey = next(s for s in model.plan.storeys if s.tag == fixture.storey)
        assert port_point[2] + storey.elevation.meters == pytest.approx(axis_z)
        feed = next(r for r in model.pipe_runs if tag in r.serves and r.tag.endswith("CU"))
        assert feed.z_m[-1] == pytest.approx(axis_z)
        assert axis_z - fixture.body_z0_m == pytest.approx(MODEL_19.barrel_axis_height * M_PER_IN)
