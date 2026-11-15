"""Product selection, open-cage geometry and shared export path for the US Cilindro."""

import numpy as np
import pytest

from typehaus.model.canvas import _symbol_geometry, model_symbol_for
from typehaus.model.placeable_symbols import model_parts

SYMBOL = "harvia-cilindro-pc110e"
SIZE = (0.4064, 0.381, 1.143)


def test_sauna_heater_selects_cilindro_without_changing_plan_or_size(catlin_plan):
    product = next(item for item in catlin_plan.library.equipment_types
                   if item.tag == "EQ-T-SAUNA-HEATER")
    assert model_symbol_for(product) == SYMBOL
    assert tuple(value.inches for value in product.footprint) == (16, 15)
    assert product.height.inches == 45
    wire = _symbol_geometry(product, product.footprint)
    generic = product.model_copy(update={"model_representation": None})
    assert wire["plan_strokes"] == _symbol_geometry(generic, product.footprint)["plan_strokes"]
    assert wire["model_parts"] != _symbol_geometry(generic, product.footprint)["model_parts"]


def test_cilindro_has_rocks_down_the_tower_and_open_raised_guard():
    parts = model_parts(SYMBOL, *SIZE)
    steel, stones, feet = (np.asarray(part["mesh"]["positions"]) / SIZE for part in parts)
    assert stones[:, 2].min() == pytest.approx(0.17)
    assert stones[:, 2].max() == pytest.approx(0.958)
    assert feet[:, 2].min() == 0
    assert steel[:, 2].max() == 1
    # No steel skin across the front between the grille rows/wires. The back remains
    # shielded at that height, while individual stones can be seen through the front.
    middle_shell = steel[(steel[:, 2] > 0.2) & (steel[:, 2] < 0.9)]
    assert np.all(np.hypot(middle_shell[:, 0], middle_shell[:, 1]) > 0.46)
    # Cast a depth ray through an opening between grille wires: the rear shroud is
    # present, but there must be no front skin that would conceal the stone column.
    triangles = steel.reshape(-1, 3, 3)
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    denominator = (b[:, 2] - c[:, 2]) * (a[:, 0] - c[:, 0]) + (
        c[:, 0] - b[:, 0]) * (a[:, 2] - c[:, 2])
    a, b, c, denominator = (values[np.abs(denominator) > 1e-12]
                             for values in (a, b, c, denominator))
    u = ((b[:, 2] - c[:, 2]) * (0.04 - c[:, 0]) + (
        c[:, 0] - b[:, 0]) * (0.54 - c[:, 2])) / denominator
    v = ((c[:, 2] - a[:, 2]) * (0.04 - c[:, 0]) + (
        a[:, 0] - c[:, 0]) * (0.54 - c[:, 2])) / denominator
    hit_y = (u * a[:, 1] + v * b[:, 1] + (1 - u - v) * c[:, 1])[
        (u >= 0) & (v >= 0) & (u + v <= 1)]
    assert len(hit_y) > 0
    assert np.all(hit_y > 0)
    top_guard = steel[steel[:, 2] > 0.98]
    assert top_guard[:, 2].min() > stones[:, 2].max()
    assert len(parts) == 3


@pytest.mark.parametrize("size", [SIZE, (0.3, 0.1, 0.04)])
def test_cilindro_mesh_is_closed_outward_and_bounded(size):
    triangle_count = 0
    for part in model_parts(SYMBOL, *size):
        mesh = part["mesh"]
        positions = np.asarray(mesh["positions"])
        assert np.all(positions >= (-size[0] / 2 - 1e-9, -size[1] / 2 - 1e-9, -1e-9))
        assert np.all(positions <= (size[0] / 2 + 1e-9, size[1] / 2 + 1e-9, size[2] + 1e-9))
        corners = positions[np.asarray(mesh["triangles"])]
        face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        normals = np.asarray(mesh["normals"])[np.asarray(mesh["triangles"])]
        assert np.linalg.norm(normals, axis=2) == pytest.approx(1)
        assert np.all(np.sum(face_normals * normals[:, 0], axis=1) > 0)
        assert np.sum(corners[:, 0] * np.cross(corners[:, 1], corners[:, 2])) > 0
        edges = {}
        for triangle in corners:
            for index in range(3):
                edge = tuple(sorted((tuple(triangle[index]), tuple(triangle[(index + 1) % 3]))))
                edges[edge] = edges.get(edge, 0) + 1
        assert set(edges.values()) == {2}
        triangle_count += len(corners)
    assert triangle_count < 8000


def test_cilindro_ifc_and_gltf_export_the_same_placed_geometry(catlin_model_ro):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.placeable_parts import parts_representation

    heater = next(item for item in catlin_model_ro.canvas_objects if item.tag == "EQ-B-SAUNA-HTR")
    product = next(item for item in catlin_model_ro.plan.library.equipment_types
                   if item.tag == heater.type_ref)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, heater, product, {})
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext", CoordinateSpaceDimension=3)
    representation = parts_representation(file, context, model_parts(SYMBOL, *SIZE),
                                           heater.position, heater.rotation_degrees, heater.z_m)
    assert len(representation.Items) == 3
    gltf_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                   for vertices, _ in mesh._buckets.values() for x, z, minus_y in vertices}
    ifc_points = {tuple(round(value, 9) for value in point)
                  for item in representation.Items for point in item.Coordinates.CoordList}
    assert gltf_points == ifc_points
