"""Product silhouette, fitting locations and rendering budget for the plug-in ProTerra."""

import dataclasses

import numpy as np
import pytest

from typehaus.model.canvas import _symbol_geometry, model_symbol_for
from typehaus.model.placeable_symbols import model_parts, plan_symbol_strokes

INCH_M = 0.0254
SYMBOL = "rheem-proterra-plugin-80"
SIZE_M = (24.25 * INCH_M, 24.25 * INCH_M, 74.1875 * INCH_M)


@pytest.fixture(scope="module")
def heater_parts():
    return model_parts(SYMBOL, *SIZE_M)


def test_tank_is_round_smooth_and_keeps_a_small_geometry_budget(heater_parts):
    tank = heater_parts[0]
    positions = np.asarray(tank["mesh"]["positions"])
    assert np.hypot(positions[:64, 0], positions[:64, 1]) == pytest.approx(12.125 * INCH_M)
    normals = np.asarray(tank["mesh"]["normals"])
    assert normals[:32, 2] == pytest.approx(0)
    assert normals[:32, :2] == pytest.approx(positions[:32, :2] / (12.125 * INCH_M))
    # Count all exported triangles, including box/prism caps and sides.
    triangle_count = sum(len(part["mesh"]["triangles"]) if "mesh" in part
                         else 4 * len(part["points"]) - 4 if part["points"] else 12
                         for part in heater_parts)
    assert triangle_count < 2000
    assert len(heater_parts) < 50
    assert max(p["center"][2] + p["size"][2] / 2 for p in heater_parts) == pytest.approx(SIZE_M[2])


def test_riser_has_a_narrow_lower_leg_and_stops_below_the_heat_pump(heater_parts):
    risers = [p for p in heater_parts if p["points"] and p["color"] == "metal-black"]
    lower, upper = risers
    assert lower["size"][0] < upper["size"][0]
    assert lower["center"][2] + lower["size"][2] / 2 == pytest.approx(
        upper["center"][2] - upper["size"][2] / 2)
    assert upper["center"][2] + upper["size"][2] / 2 == pytest.approx(54.3125 * INCH_M)
    assert lower["center"][0] > 0 and upper["center"][1] < 0


def test_mesh_normals_and_winding_survive_nonuniform_scaling():
    for part in model_parts(SYMBOL, 1.2, 0.8, 0.9):
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        points = np.asarray(mesh["positions"])
        normals = np.asarray(mesh["normals"])
        corners = points[np.asarray(mesh["triangles"])]
        face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        assert np.linalg.norm(normals, axis=1) == pytest.approx(1)
        assert np.all(np.linalg.norm(face_normals, axis=1) > 0)
        vertex_normals = normals[np.asarray(mesh["triangles"])[:, 0]]
        assert np.all(np.sum(face_normals * vertex_normals, axis=1) > 0)


def test_product_selects_the_model_and_each_fitting_reaches_its_service_port(
    catlin_plan, heater_parts,
):
    product = next(t for t in catlin_plan.library.equipment_types if t.tag == "EQ-T-WATER-HEATER")
    assert model_symbol_for(product) == SYMBOL
    wire = _symbol_geometry(product, product.footprint)
    plan_only = product.model_copy(update={"model_representation": None})
    assert wire["plan_strokes"] == _symbol_geometry(plan_only, product.footprint)["plan_strokes"]
    assert len(wire["model_parts"]) == len(heater_parts)
    ports = {port.tag: port for port in product.ports}
    for tag, fitting in zip(("hot", "cold", "relief", "condensate"), heater_parts[-4:],
                            strict=True):
        tip = np.array([dimension.meters for dimension in ports[tag].position])
        # Cap centers are explicit mesh vertices: the rendered end must meet the port,
        # rather than being a nipple on top as on the unrelated 240 V product.
        distances = np.linalg.norm(np.asarray(fitting["mesh"]["positions"]) - tip, axis=1)
        assert min(distances) < 1e-9
    assert plan_symbol_strokes("water-heater", *SIZE_M[:2])


@pytest.mark.parametrize("rotation", [0, -90])
def test_viewer_glb_and_ifc_use_the_same_equipment_parts(catlin_model_ro, tmp_path, rotation):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import Building, Library, PlanModel, Project, Site, Storey, deg, ft, m
    from typehaus.resolve import resolve

    original = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "EQ-B-WH")
    product = next(t for t in catlin_model_ro.plan.library.equipment_types
                   if t.tag == original.type_ref)
    item = dataclasses.replace(original, rotation_degrees=rotation)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, product, {})
    glb_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                  for points, _ in mesh._buckets.values() for x, z, minus_y in points}
    equipment = catlin_model_ro.plan.by_tag(original.tag).model_copy(update={
        "rotation": deg(rotation), "circuit": None, "room": None, "relief_discharge_ref": None,
    })
    plan = PlanModel(
        project=Project(name="heater", project_uuid=catlin_model_ro.plan.project.project_uuid,
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="basement", elevation=m(original.z_m),
                       default_ceiling_height=ft(9)),),
        library=Library(equipment_types=(product,)), elements={"basement": (equipment,)},
    )
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "heater.ifc")))
    heater, = [obj for obj in exported.by_type("IfcElement") if obj.Name == original.tag]
    representation, = heater.Representation.Representations
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == len(model_parts(SYMBOL, *SIZE_M))
    ifc_points = {tuple(round(value, 9) for value in point)
                  for part in representation.Items for point in part.Coordinates.CoordList}
    # Minimal storey uses the real basement datum so all three consumers compare in world space.
    assert ifc_points == glb_points
