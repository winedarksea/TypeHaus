"""Plant heater catalog selection and exportable bowed grille geometry."""

import numpy as np
import pytest

from typehaus.model.canvas import _symbol_geometry, model_symbol_for
from typehaus.model.placeable_symbols import model_parts


def test_plant_heater_uses_detailed_model_with_existing_planning_envelope(catlin_plan):
    equipment = catlin_plan.by_tag("EQ-S-PLANT-HEATER")
    product = next(item for item in catlin_plan.library.equipment_types
                   if item.tag == equipment.type_ref)
    assert model_symbol_for(product) == "ceramic-fan-heater"
    assert tuple(value.inches for value in product.footprint) == (7, 7)
    assert product.height.inches == 9
    wire = _symbol_geometry(product, product.footprint)
    assert len(wire["model_parts"]) > 1
    plan_only = product.model_copy(update={"model_representation": None})
    assert wire["plan_strokes"] == _symbol_geometry(plan_only, product.footprint)["plan_strokes"]


def test_resolved_heater_exports_the_same_parts_to_gltf_and_ifc(catlin_model_ro):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.placeable_parts import parts_representation

    heater = next(item for item in catlin_model_ro.canvas_objects
                  if item.tag == "EQ-S-PLANT-HEATER")
    product = next(item for item in catlin_model_ro.plan.library.equipment_types
                   if item.tag == heater.type_ref)
    parts = model_parts(model_symbol_for(product), *(v.meters for v in product.footprint),
                        product.height.meters)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, heater, product, {})
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext", CoordinateSpaceDimension=3)
    representation = parts_representation(file, context, parts, heater.position,
                                           heater.rotation_degrees, heater.z_m)
    assert len(representation.Items) == len(parts) > 1
    gltf_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                   for vertices, _ in mesh._buckets.values() for x, z, minus_y in vertices}
    ifc_points = {tuple(round(value, 9) for value in point)
                  for item in representation.Items for point in item.Coordinates.CoordList}
    assert gltf_points == ifc_points


@pytest.mark.parametrize("size", [(0.1778, 0.1778, 0.2286), (0.3, 0.1, 0.04)])
def test_heater_meshes_are_closed_outward_and_fit_export_budget(size):
    parts = model_parts("ceramic-fan-heater", *size)
    triangle_count = 0
    for part in parts:
        if "mesh" not in part:
            triangle_count += 4 * len(part["points"]) - 4 if part["points"] else 12
            continue
        mesh = part["mesh"]
        corners = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        vertex_normals = np.asarray(mesh["normals"])[np.asarray(mesh["triangles"])]
        assert np.linalg.norm(vertex_normals, axis=2) == pytest.approx(1)
        assert np.all(np.sum(face_normals * vertex_normals[:, 0], axis=1) > 0)
        assert np.sum(corners[:, 0] * np.cross(corners[:, 1], corners[:, 2])) > 0
        # Every geometric edge must have two incident faces, even with split normals.
        edges = {}
        for triangle in corners:
            for index in range(3):
                edge = tuple(sorted((tuple(triangle[index]), tuple(triangle[(index + 1) % 3]))))
                edges[edge] = edges.get(edge, 0) + 1
        assert set(edges.values()) == {2}
        triangle_count += len(corners)
    assert triangle_count < 5000
    assert len(parts) < 64
