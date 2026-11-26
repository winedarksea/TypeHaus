"""All five shower stations share hardware, supply hubs and export geometry."""

import math

import ifcopenshell
import pytest

from typehaus.checks.mep.shower_assembly import shower_assembly_alignment
from typehaus.findings import Result
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._shower_hardware import shower_hardware_parts

SHOWER_TAGS = {"FX-B-BATH-SH", "FX-M-BATH2-SH", "FX-A-STUBATH-SH",
               "FX-S-BATH1-SH", "FX-S-SUITEBATH-TUBSH"}


def test_all_five_have_axial_connections_without_promoting_certainty(catlin_ctx):
    findings = shower_assembly_alignment(catlin_ctx)
    assert not [f for f in findings if f.result is Result.FAIL]
    connections = [f for f in findings if "VALVE-" in f.element_tags[-1]]
    assert len(connections) == 10
    assert all(f.result is Result.PASS and "approximate" in f.message for f in connections)


def test_controls_heads_and_handhelds_reach_viewer_and_ifc(catlin_model_ro, catlin_ifc_path):
    model = catlin_model_ro
    types = {t.tag: t for t in model.plan.library.fixture_types}
    wire = {t["tag"]: t for t in canvas_object_types(model.plan)}
    file = ifcopenshell.open(str(catlin_ifc_path))
    exported = {e.Name: e for e in file.by_type("IfcSanitaryTerminal")}
    for fixture in model.canvas_objects:
        if fixture.tag not in SHOWER_TAGS:
            continue
        product = types[fixture.type_ref]
        spec = product.shower_assembly
        hardware = shower_hardware_parts(spec)
        assert {c.kind for c in spec.components} >= {"head", "handheld"}
        parts = model_parts(product.model_representation.symbol if product.model_representation
                            else product.plan_symbol,
                            *[v.meters for v in product.footprint], product.height.meters,
                            shower_assembly=spec)
        assert len(wire[product.tag]["model_parts"]) == len(parts)
        mesh = _MeshBuilder()
        assert _add_canvas_parts(mesh, fixture, product,
                                 {material.tag: material for material in model.plan.library.materials})
        glb_vertices = {tuple(round(value, 7) for value in point)
                        for positions, _ in mesh._buckets.values() for point in positions}
        items = exported[fixture.tag].Representation.Representations[0].Items
        assert len(items) == len(parts)
        # Compare each mesh's world vertices after rotation and elevation, not only counts.
        for part, item in zip(parts[-len(hardware):], items[-len(hardware):], strict=True):
            if part["shape"] != "mesh":
                continue
            vertices = part["mesh"]["positions"]
            placed = place_local([(x, y) for x, y, z in vertices], fixture.position,
                                  fixture.rotation_degrees)
            expected = [(x, y, z + fixture.z_m) for (x, y), (_, _, z)
                        in zip(placed, vertices, strict=True)]
            for x, y, z in expected:
                assert tuple(round(value, 7) for value in (x, z, -y)) in glb_vertices
            actual = item.Coordinates.CoordList
            for point, target in zip(actual, expected, strict=True):
                assert point == pytest.approx(target)


def test_sauna_station_is_pan_centerline_and_thermo_uses_48_inches(catlin_model_ro):
    model = catlin_model_ro
    types = {t.tag: t for t in model.plan.library.fixture_types}
    for fixture in model.canvas_objects:
        if fixture.tag not in SHOWER_TAGS:
            continue
        spec = types[fixture.type_ref].shower_assembly
        head = next(c for c in spec.components if c.kind == "head")
        assert spec.component_point(head)[2] == pytest.approx(
            spec.standing_surface_height.meters + 78 * .0254)
        if fixture.tag == "FX-B-BATH-SH":
            # Valve on the pan's south wall (W-B-SA-N), 4" east of centre, mid-bay (2026-11-25).
            assert spec.valve_face[1].meters == pytest.approx(-18 * .0254)
            assert spec.valve_face[0].meters == pytest.approx(4 * .0254)
            assert (spec.valve_face[2].meters - spec.standing_surface_height.meters) / .0254 == pytest.approx(49.4375)
        if fixture.tag == "FX-M-BATH2-SH":
            assert spec.valve_face[2].meters / .0254 == pytest.approx(48)
            assert {c.kind for c in spec.components} >= {"temperature", "volume"}
        assert math.isfinite(fixture.z_m)
