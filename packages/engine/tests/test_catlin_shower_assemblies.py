"""All five shower stations share hardware, supply hubs and export geometry."""

import math

import ifcopenshell
import pytest
from shapely.geometry import Polygon

from typehaus.checks.mep.shower_assembly import shower_assembly_alignment
from typehaus.findings import Result
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._shower_hardware import shower_hardware_parts
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff

SHOWER_TAGS = {"FX-B-SAUNA-SH", "FX-M-BATH2-SH", "FX-A-STUBATH-SH",
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


def test_sauna_tile_replaces_wood_and_has_real_backer_and_stringer(catlin_model_ro):
    model = catlin_model_ro
    panels = [p for p in model.panelings if p.tag == "WP-B-SAUNA-SPLASH"]
    backing = [p for p in model.panelings if p.material_ref == "durock-half-inch"]
    assert len(panels) == len(backing) == 2
    assert sum(p.area_m2 for p in backing) == pytest.approx(sum(p.area_m2 for p in panels))
    for panel in panels:
        wall = next(w for w in model.walls if w.tag == panel.wall_tag)
        for layer in wall.layers:
            if layer.material_ref == "catlin-sauna-shiplap":
                assert Polygon(layer.polygon).intersection(Polygon(panel.outline)).area < 1e-8
    wall = next(w for w in model.walls if w.tag == "W-B-CS")
    blocks = [m for m in wall.members if m.category == "blocking" and m.profile == "2x4"
              and m.p0[0] / .0254 == pytest.approx(213.25)]
    assert blocks
    face = min(x for block in blocks for x, y in member_footprint(block)[0]) / .0254
    assert face == pytest.approx(209.75 + 2.75)
    panel = next(p for p in panels if p.wall_tag == "W-B-CS")
    assert min(x for x, y in panel.outline) / .0254 == pytest.approx(209.75)
    pocket_z = next(f.z_m for f in model.canvas_objects if f.tag == "FX-B-SAUNA-SH") + 51.4375*.0254
    for layer in wall.layers:
        if layer.material_ref != "foil-polyiso" or not (layer.band(wall)[0] < pocket_z < layer.band(wall)[1]):
            continue
        from shapely.geometry import box
        cavity = box(211.25*.0254, 94*.0254, 212.49*.0254, 102*.0254)
        assert Polygon(layer.polygon).intersection(cavity).area < 1e-10
    rows = wood_surfaces_takeoff(model)
    assert any(row.get("material") == "durock-half-inch" or row.get("material_ref") == "durock-half-inch"
               for row in rows)


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
        if fixture.tag == "FX-B-SAUNA-SH":
            assert spec.valve_face[1].meters == 0
            assert spec.valve_face[0].meters == pytest.approx(18 * .0254)
            assert (spec.valve_face[2].meters - spec.standing_surface_height.meters) / .0254 == pytest.approx(49.4375)
        if fixture.tag == "FX-M-BATH2-SH":
            assert spec.valve_face[2].meters / .0254 == pytest.approx(48)
            assert {c.kind for c in spec.components} >= {"temperature", "volume"}
        assert math.isfinite(fixture.z_m)
