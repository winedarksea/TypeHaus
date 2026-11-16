"""A round, open downlight rather than a square box with a flush luminous face."""

from collections import Counter

import numpy as np
import pytest

from typehaus.library.lighting import luminaire_class
from typehaus.model.placeable_symbols import model_parts


@pytest.mark.parametrize("dimensions", [(0.127, 0.127, 0.1524), (0.09525, 0.09525, 0.127),
                                       (0.127, 0.127, 0.0508), (0.30, 0.10, 0.04)])
def test_can_has_an_open_trim_regressed_lamp_and_closed_outward_meshes(dimensions):
    parts = model_parts("recessed-can", *dimensions)
    trim, baffle, lens, housing = parts
    assert trim["color"] == baffle["color"] == "appliance-white"
    assert lens["color"] == "lamp"
    lens_bottom = lens["center"][2] - lens["size"][2] / 2
    assert lens_bottom > trim["size"][2]
    assert housing["center"][2] - housing["size"][2] / 2 > lens_bottom
    assert lens["size"][0] < trim["size"][0]
    for part in parts:
        mesh = part["mesh"]
        positions = np.asarray(mesh["positions"])
        triangles = positions[np.asarray(mesh["triangles"])]
        cross = np.cross(triangles[:, 1] - triangles[:, 0],
                         triangles[:, 2] - triangles[:, 0])
        assert np.all(np.linalg.norm(cross, axis=1) > 0)
        assert np.sum(triangles[:, 0] * np.cross(triangles[:, 1], triangles[:, 2])) > 0
        normals = np.asarray(mesh["normals"])[np.asarray(mesh["triangles"])]
        assert np.all(np.sum(cross[:, None, :] * normals, axis=2) > 0)
        # Weld shading splits before checking that every edge bounds exactly two faces.
        edges = Counter()
        for triangle in triangles:
            vertices = [tuple(np.round(vertex, 12)) for vertex in triangle]
            for a, b in zip(vertices, (*vertices[1:], vertices[0]), strict=True):
                edges[tuple(sorted((a, b)))] += 1
        assert set(edges.values()) == {2}
    # No trim/baffle triangle may bridge the central opening, hiding the regressed lamp.
    for part in (trim, baffle):
        for triangle in part["mesh"]["triangles"]:
            points = [part["mesh"]["positions"][i] for i in triangle]
            centroid = np.mean(points, axis=0)
            assert np.linalg.norm(centroid[:2]) > lens["size"][0] * 0.45
    assert any(normal[2] == -1.0 for normal in lens["mesh"]["normals"])


@pytest.mark.parametrize("product_tag", ["ED-T-LT-CAN4-4000", "ED-T-LT-CAN3"])
@pytest.mark.parametrize("rotation", [0, 90])
def test_can_shared_mesh_reaches_viewer_glb_and_ifc(tmp_path, product_tag, rotation):
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

    product = luminaire_class(product_tag)
    device = ElectricalDevice(
        tag="ED-CAN", kind=DeviceKind.LIGHT, position=pt(ft(2), ft(3)),
        type_ref=product.tag, rotation=deg(rotation),
        mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True))
    plan = PlanModel(
        project=Project(name="can", project_uuid="403ba200-3cfe-498c-88fc-cff0bfecbca0",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
        library=Library(electrical_device_types=(product,)), elements={"main": (device,)})
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    parts = model_parts(product.plan_symbol, *(d.meters for d in product.footprint),
                        product.height.meters)
    wire = _symbol_geometry(product, product.footprint)
    assert [part["mesh"] for part in wire["model_parts"]] == [part["mesh"] for part in parts]
    builder = _MeshBuilder()
    item, = model.canvas_objects
    assert _add_canvas_parts(builder, item, product, {})
    glb_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                  for points, _ in builder._buckets.values() for x, z, minus_y in points}
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "can.ifc")))
    light, = exported.by_type("IfcLightFixture")
    representation, = light.Representation.Representations
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == len(parts)
    ifc_points = {tuple(round(value, 9) for value in point)
                  for part in representation.Items for point in part.Coordinates.CoordList}
    assert ifc_points == glb_points
