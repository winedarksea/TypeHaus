"""AP reference envelopes, face directions and shared viewer/export meshes."""

from collections import Counter

import numpy as np
import pytest

from typehaus.library.network_devices import ACCESS_POINT_DEVICE_TYPES
from typehaus.model.placeable_symbols import model_parts


@pytest.mark.parametrize("product", ACCESS_POINT_DEVICE_TYPES, ids=lambda p: p.tag)
def test_reference_envelope_face_direction_and_closed_meshes(product):
    dimensions = (*(length.meters for length in product.footprint), product.height.meters)
    wall = product.tag == "ED-T-AP-WALL"
    assert dimensions == pytest.approx((.197, .035, .197) if wall else (.197, .197, .035))
    parts = model_parts(product.model_representation.symbol, *dimensions)
    shell, status_ring, mount = parts
    all_points = np.concatenate([part["mesh"]["positions"] for part in parts])
    assert all_points.max(axis=0) - all_points.min(axis=0) == pytest.approx(dimensions)
    assert all_points.min(axis=0) == pytest.approx(
        (-dimensions[0] / 2, -dimensions[1] / 2, 0))
    face_axis = 1 if wall else 2
    assert status_ring["center"][face_axis] < shell["center"][face_axis]
    assert shell["center"][face_axis] < mount["center"][face_axis]
    assert status_ring["color"] == "unifi-status-blue"
    for part in parts:
        mesh = part["mesh"]
        triangles = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        cross = np.cross(triangles[:, 1] - triangles[:, 0],
                         triangles[:, 2] - triangles[:, 0])
        assert np.all(np.linalg.norm(cross, axis=1) > 0)
        assert np.sum(triangles[:, 0] * np.cross(triangles[:, 1], triangles[:, 2])) > 0
        normals = np.asarray(mesh["normals"])[np.asarray(mesh["triangles"])]
        assert np.all(np.sum(cross[:, None, :] * normals, axis=2) > 0)
        edges = Counter()
        for triangle in triangles:
            vertices = [tuple(np.round(vertex, 12)) for vertex in triangle]
            for a, b in zip(vertices, (*vertices[1:], vertices[0]), strict=True):
                edges[tuple(sorted((a, b)))] += 1
        assert set(edges.values()) == {2}


@pytest.mark.parametrize("product", ACCESS_POINT_DEVICE_TYPES, ids=lambda p: p.tag)
@pytest.mark.parametrize("rotation", [0, 90])
def test_access_point_mesh_reaches_viewer_glb_and_ifc(tmp_path, product, rotation):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import (
        Building,
        DeviceKind,
        ElectricalDevice,
        Library,
        Mount,
        MountKind,
        PlanModel,
        Project,
        Site,
        Storey,
        deg,
        ft,
        m,
        pt,
    )
    from typehaus.model.canvas import _symbol_geometry
    from typehaus.resolve import resolve

    wall = product.tag == "ED-T-AP-WALL"
    device = ElectricalDevice(
        tag="ED-AP", kind=DeviceKind.DATA_OUTLET, position=pt(ft(2), ft(3)),
        type_ref=product.tag, rotation=deg(rotation),
        mount=Mount(kind=MountKind.WALL if wall else MountKind.CEILING,
                    elevation=ft(7)))
    plan = PlanModel(
        project=Project(name="access-point", project_uuid="4b7c8626-5e33-4728-bf55-50c26ccc87d7",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
        library=Library(electrical_device_types=(product,)), elements={"main": (device,)})
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    parts = model_parts(product.model_representation.symbol,
                        *(length.meters for length in product.footprint), product.height.meters)
    wire = _symbol_geometry(product, product.footprint)
    assert [part["mesh"] for part in wire["model_parts"]] == [part["mesh"] for part in parts]
    builder = _MeshBuilder()
    item, = model.canvas_objects
    assert _add_canvas_parts(builder, item, product, {})
    glb_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                  for points, _ in builder._buckets.values() for x, z, minus_y in points}
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "ap.ifc")))
    appliance, = exported.by_type("IfcCommunicationsAppliance")
    assert appliance.PredefinedType == "NETWORKAPPLIANCE"
    representation, = appliance.Representation.Representations
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == len(parts)
    ifc_points = {tuple(round(value, 9) for value in point)
                  for part in representation.Items for point in part.Coordinates.CoordList}
    assert ifc_points == glb_points
