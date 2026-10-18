"""A flood's aimed lens and shared geometry survive all three model consumers."""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._flood_light import flood_head_direction


def test_lens_faces_outward_and_down_without_being_buried_in_the_housing():
    parts = model_parts("flood-light", 0.127, 0.127, 0.2032)
    lens = next(part for part in parts if part["color"] == "lamp")
    direction = flood_head_direction()
    assert direction[1] < 0 and direction[2] < 0
    # A front lens face must have an outward normal along the actual beam axis.
    assert any(sum(a * b for a, b in zip(normal, direction, strict=True)) > 0.999
               for normal in lens["mesh"]["normals"])
    # Every head mesh is closed and outward-wound, including the hinge's round axle.
    for part in parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        volume = 0.0
        for a, b, c in mesh["triangles"]:
            p, q, r = (mesh["positions"][i] for i in (a, b, c))
            volume += (p[0] * (q[1] * r[2] - q[2] * r[1])
                       + p[1] * (q[2] * r[0] - q[0] * r[2])
                       + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6
        assert volume > 0


@pytest.mark.parametrize("rotation", [0, 90])
def test_viewer_glb_and_ifc_keep_the_same_flood_geometry(catlin_model_ro, tmp_path, rotation):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import Building, Library, PlanModel, Project, Site, Storey, deg, ft, m
    from typehaus.resolve import resolve

    original = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "ED-M-PORCH-FLOOD")
    product = next(kind for kind in catlin_model_ro.plan.library.electrical_device_types
                   if kind.tag == original.type_ref)
    item = dataclasses.replace(original, rotation_degrees=rotation)
    parts = model_parts(product.plan_symbol, *(d.meters for d in product.footprint),
                        product.height.meters)
    wire = _symbol_geometry(product, product.footprint)
    for part, record in zip(parts, wire["model_parts"], strict=True):
        if "mesh" in part:
            assert record["mesh"] == part["mesh"]

    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, product, {})
    glb_points = {(round(x, 9), round(-minus_y, 9), round(z, 9))
                  for points, _ in mesh._buckets.values() for x, z, minus_y in points}
    device = catlin_model_ro.plan.by_tag(original.tag).model_copy(update={
        "rotation": deg(rotation), "circuit": None, "controlled_by": (),
    })
    # A minimal export exercises the real device dispatch without paying for a second
    # whole-house IFC. The shared Catlin fixtures remain untouched.
    plan = PlanModel(
        project=Project(name="flood", project_uuid=catlin_model_ro.plan.project.project_uuid,
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=ft(0), default_ceiling_height=ft(9)),),
        library=Library(electrical_device_types=(product,)), elements={"main": (device,)},
    )
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "flood.ifc")))
    light, = exported.by_type("IfcLightFixture")
    representation, = light.Representation.Representations
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == len(parts)
    ifc_points = {tuple(round(value, 9) for value in point)
                  for part in representation.Items for point in part.Coordinates.CoordList}
    assert ifc_points == glb_points
