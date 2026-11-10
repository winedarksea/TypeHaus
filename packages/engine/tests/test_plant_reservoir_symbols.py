"""Shared reservoir meshes remain closed, finite, opaque and export without remeasurement."""

import math

import numpy as np
import pytest

from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.model.placeable_symbols import PART_COLORS, model_parts
from typehaus.model.plant_reservoir import RESERVOIR_GEOMETRY as G
from typehaus.quantities import M_PER_IN


@pytest.fixture(scope="module")
def tank_parts():
    return model_parts(
        "plant-reservoir",
        *(v * M_PER_IN for v in (G.handle_width_in, G.envelope_depth_in, G.installed_height_in)),
    )


def test_tank_shell_tapers_and_handles_reach_full_width(tank_parts):
    shell = next(p for p in tank_parts if p.get("role") == "reservoir:shell")
    points = np.asarray(shell["mesh"]["positions"])
    bottom = points[points[:, 2] < 0.001]
    upper = points[points[:, 2] > G.rim_height_in * M_PER_IN - 0.001]
    assert np.abs(bottom[:, 0]).max() < np.abs(upper[:, 0]).max()
    handles = [p for p in tank_parts if p.get("role") == "reservoir:handle"]
    assert len(handles) == 6
    assert max(p["center"][0] + p["size"][0] / 2 for p in handles) == pytest.approx(9 * M_PER_IN)
    assert all(PART_COLORS[p["color"]][3] == 1 for p in tank_parts)
    assert not any(p.get("role") == "water" for p in tank_parts)


def test_meshes_have_finite_unit_normals_positive_volume_and_small_budget(tank_parts):
    triangles = 0
    for part in tank_parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        assert all(math.isfinite(v) for p in mesh["positions"] for v in p)
        assert all(sum(v * v for v in n) == pytest.approx(1) for n in mesh["normals"])
        points = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        signed_volume = (
            np.einsum("ij,ij->i", points[:, 0], np.cross(points[:, 1], points[:, 2])).sum() / 6
        )
        assert signed_volume > 0
        triangles += len(mesh["triangles"])
    assert triangles < 2500


def test_rack_has_two_pumps_and_two_independent_timers():
    parts = model_parts("plant-irrigation-rack", 36 * M_PER_IN, 12 * M_PER_IN, 24 * M_PER_IN)
    assert len([p for p in parts if p.get("role") == "irrigation:pump"]) == 2
    assert len([p for p in parts if p.get("role") == "irrigation:timer"]) == 2
    assert len([p for p in parts if p.get("role") == "irrigation:outlet"]) == 4


def test_ifc_tessellates_the_same_vertices_as_the_viewer(tank_parts):
    import ifcopenshell

    model = ifcopenshell.file(schema="IFC4")
    origin = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
    placement = model.createIfcAxis2Placement3D(origin)
    context = model.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5, placement)
    representation = parts_representation(model, context, tank_parts, (0.0, 0.0), 0.0, 0.0)
    assert len(representation.Items) == len(tank_parts)
    for part, item in zip(tank_parts, representation.Items, strict=True):
        if "mesh" in part:
            assert np.asarray(item.Coordinates.CoordList) == pytest.approx(
                np.asarray(part["mesh"]["positions"])
            )
            assert (
                tuple(tuple(v - 1 for v in tri) for tri in item.CoordIndex)
                == part["mesh"]["triangles"]
            )


@pytest.mark.parametrize("rotation", [0, 180])
def test_installed_appliances_export_generated_parts_instead_of_prisms(
    catlin_plan,
    tmp_path,
    rotation,
):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import Building, Library, PlanModel, Project, Site, Storey, deg, ft, m
    from typehaus.model.canvas import model_symbol_for
    from typehaus.resolve import resolve

    appliances = tuple(
        a.model_copy(update={"room": None, "rotation": deg(rotation)})
        for a in catlin_plan.elements_of_kind("Appliance")
        if a.tag.startswith("APPL-S-PLANT-")
    )
    types = tuple(
        t for t in catlin_plan.library.appliance_types if t.tag in {a.type_ref for a in appliances}
    )
    references = {p.product_ref for t in types for p in t.parts}
    references.update(t.product_ref for t in types if t.product_ref)
    plan = PlanModel(
        project=Project(
            name="reservoir",
            project_uuid=catlin_plan.project.project_uuid,
            building=Building(name="test"),
            site=Site(lat=0, lon=0, elevation=m(0)),
        ),
        storeys=(Storey(tag="second", elevation=m(0), default_ceiling_height=ft(9)),),
        library=Library(
            appliance_types=types,
            products=tuple(catlin_plan.library.product(tag) for tag in references),
        ),
        elements={"second": appliances},
    )
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "reservoir.ifc")))
    for item in model.canvas_objects:
        product = next(t for t in types if t.tag == item.type_ref)
        (element,) = [e for e in exported.by_type("IfcElement") if e.Name == item.tag]
        (representation,) = element.Representation.Representations
        assert representation.RepresentationType == "Tessellation"
        parts = model_parts(
            model_symbol_for(product), *(d.meters for d in product.footprint), product.height.meters
        )
        assert len(representation.Items) == len(parts)
        mesh = _MeshBuilder()
        assert _add_canvas_parts(mesh, item, product, {})
        glb_points = {
            (round(x, 9), round(-minus_y, 9), round(z, 9))
            for points, _ in mesh._buckets.values()
            for x, z, minus_y in points
        }
        ifc_points = {
            tuple(round(v, 9) for v in point)
            for part in representation.Items
            for point in part.Coordinates.CoordList
        }
        assert ifc_points == glb_points
