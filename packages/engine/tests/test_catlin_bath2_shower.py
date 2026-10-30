"""BATH2's stock front, supported custom return, and molded pan drain."""

import ifcopenshell
import pytest
from shapely.geometry import Point, Polygon

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.model.placeable_symbols._swanstone_flex import (
    door_swing_outline,
    front_opening_limits,
)
from typehaus.model.placeable_symbols._swanstone_flex_config import BATH2_SHOWER
from typehaus.resolve.paneling import _FLUSH_REVEAL_M

INCH = 0.0254


def _fixture(model):
    return next(obj for obj in model.canvas_objects if obj.tag == "FX-M-BATH2-SH")


def test_actual_finished_opening_and_outward_swing(catlin_model_ro):
    model = catlin_model_ro
    fixture = _fixture(model)
    dimensions = BATH2_SHOWER
    width, depth = dimensions.pan_width * INCH, dimensions.pan_depth * INCH
    north, south = front_opening_limits(width)
    assert (south - north) / INCH == pytest.approx(36)
    opening = (south - north) / INCH
    assert dimensions.front_minimum_width <= opening <= dimensions.front_maximum_width
    # Check the authored finish and deck, rather than trusting the nominal config alone.
    panel = next(panel for panel in model.panelings if panel.tag == "WP-M-BATH2-SURR")
    assert panel.material_ref == "solid-surface-panel"
    south_panel = next(panel for panel in model.panelings
                       if panel.tag == "WP-M-BATH2-SURR" and panel.wall_tag == "W-M-BDN1")
    south_face = max(point[1] for point in south_panel.outline)
    jamb = place_local([(south, -depth / 2)], fixture.position, fixture.rotation_degrees)[0]
    # A replacing band stands _FLUSH_REVEAL_M proud of the finish plane (z-fighting).
    # The owner moved the knee wall and unchanged pan south to close the jamb gap.
    finished_south_face = south_face - _FLUSH_REVEAL_M
    assert jamb[1] == pytest.approx(finished_south_face)
    north_jamb = place_local([(north, -depth / 2)], fixture.position, fixture.rotation_degrees)[0]
    actual_finished_opening = (north_jamb[1] - finished_south_face) / INCH
    assert actual_finished_opening == pytest.approx(36)
    deck = next(solid for solid in model.solids if solid.tag == "SL-M-TUBDK")
    assert min(y for _, y in deck.outline) == pytest.approx(north_jamb[1])
    east_panel = next(panel for panel in model.panelings
                      if panel.tag == "WP-M-BATH2-SURR" and panel.wall_tag == "W-M-BA2E2")
    # Its run is clipped by the room's clear face, which still counts W-M-BDN1's 0.01" paint
    # film; the south panel itself replaces that film, so the corner leaves a 0.01" sealant gap.
    assert min(y for _, y in east_panel.outline) == pytest.approx(
        finished_south_face + 0.01 * INCH)
    assert max(y for _, y in east_panel.outline) == pytest.approx(north_jamb[1])
    sweep = Polygon(place_local(door_swing_outline(width, depth), fixture.position,
                                fixture.rotation_degrees))
    vanity = next(obj for obj in model.canvas_objects if obj.tag == "FX-M-BATH2-SINK")
    door = next(opening for opening in model.openings if opening.tag == "D-M-BATH2")
    assert sweep.distance(Polygon(vanity.footprint)) > 0
    assert sweep.distance(Polygon(door.swing_clearance)) > 0
    # Threshold footprint is sufficient, but the FLAT land still needs a dealer submittal.
    assert dimensions.threshold_depth >= dimensions.minimum_flat_threshold


def test_pan_glass_datums_and_solid_surface_wire_material(catlin_model_ro):
    model = catlin_model_ro
    fixture = _fixture(model)
    product = next(t for t in model.plan.library.fixture_types if t.tag == fixture.type_ref)
    width, depth = (v.meters for v in product.footprint)
    parts = model_parts(product.model_representation.symbol, width, depth, product.height.meters,
                        material_refs=product.model_representation.material_refs)
    glasses = [p for p in parts if p["color"] == "clear-glass"]
    north = min(glasses, key=lambda p: p["center"][0])
    front = [p for p in glasses if p is not north]

    def datum(part, sign):
        return (fixture.z_m + part["center"][2] + sign * part["size"][2] / 2) / INCH

    assert datum(north, -1) == pytest.approx(22.75)
    assert datum(north, 1) == pytest.approx(106)
    assert max(datum(p, 1) for p in parts) == pytest.approx(106)
    assert fixture.z_m == pytest.approx(0.75 * INCH)
    assert max(datum(p, 1) for p in front) < 77.25  # glass sits within the top rail
    rails = [p for p in parts if p["color"] == "chrome"
             and p["size"][0] == pytest.approx(width)
             and p["size"][1] / INCH == pytest.approx(BATH2_SHOWER.rail_width)]
    assert max(datum(p, 1) for p in rails) == pytest.approx(77.25)
    assert fixture.body_z1_m == pytest.approx(106 * INCH)
    # The return is wholly supported on the deck, not floating over the pan.
    deck = next(s for s in model.solids if s.tag == "SL-M-TUBDK")
    # Resolved slab solids carry the footprint even though the deck has an opening.
    center = place_local([north["center"][:2]], fixture.position, fixture.rotation_degrees)[0]
    assert Polygon(deck.outline, deck.voids).covers(Point(center))
    drain = next(p for p in parts if p["color"] == "chrome" and p["points"])
    assert drain["center"][:2] == pytest.approx((0, 0))
    authored = next(e for e in model.plan.storey_elements("main") if e.tag == fixture.tag)
    assert authored.drain_position.xy_m != pytest.approx(fixture.position)
    wire = next(t for t in canvas_object_types(model.plan) if t["tag"] == product.tag)
    assert any(p.get("material_ref") == "solid-surface-base" for p in wire["model_parts"])
    assert any(p.get("opacity", 1) < 1 for p in wire["model_parts"])
    assert any(p.get("metalness") == 1 for p in wire["model_parts"])


def test_molded_pan_has_a_recessed_basin_and_published_threshold():
    dimensions = BATH2_SHOWER
    parts = model_parts("swanstone-flex-3636", dimensions.pan_width * INCH,
                        dimensions.pan_depth * INCH, dimensions.model_height * INCH)
    basin = next(p for p in parts if p["color"] == "solid-surface" and "mesh" in p)
    assert max(point[2] for point in basin["mesh"]["positions"]) / INCH == pytest.approx(2.25)
    threshold = next(p for p in parts if p["color"] == "solid-surface"
                     and p["size"][1] / INCH == pytest.approx(2.75))
    assert threshold["size"][0] / INCH == pytest.approx(36)
    assert (threshold["center"][2] + threshold["size"][2] / 2) / INCH == pytest.approx(4.5)


def test_glb_and_ifc_keep_parts_and_transparency(catlin_model_ro, catlin_ifc_path):
    model = catlin_model_ro
    fixture = _fixture(model)
    product = next(t for t in model.plan.library.fixture_types if t.tag == fixture.type_ref)
    mesh = _MeshBuilder()
    materials = {m.tag: m for m in model.plan.library.materials}
    assert _add_canvas_parts(mesh, fixture, product, materials)
    assert any(color[3] < 1 for color in mesh._buckets)
    assert len(mesh._buckets) >= 3
    scene = _SceneBuilder()
    scene.add_object(mesh, ("plumbing",), kind="canvas_object", uid=fixture.uid)
    document, _ = scene.build()
    assert "Swanstone solid surface" in {m["name"] for m in document["materials"]}
    positions = [document["accessors"][primitive["attributes"]["POSITION"]]
                 for mesh in document["meshes"] for primitive in mesh["primitives"]]
    assert min(accessor["min"][1] for accessor in positions) == pytest.approx(0.75 * INCH)
    assert max(accessor["max"][1] for accessor in positions) == pytest.approx(106 * INCH)
    file = ifcopenshell.open(str(catlin_ifc_path))
    element = next(e for e in file.by_type("IfcSanitaryTerminal") if e.Name == fixture.tag)
    items = element.Representation.Representations[0].Items
    assert len(items) > 15
    styles = [item.StyledByItem[0].Styles[0] for item in items]
    assert any(style.Name == "solid-surface-base" for style in styles)
    assert any(style.Styles[0].Transparency > 0 for style in styles)
    # IFC uses the same absolute support planes for both generated parts and generic units.
    fixtures = {item.tag: item for item in model.canvas_objects if item.kind == "Fixture"}
    bathing = {"FX-B-SAUNA-SH", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
               "FX-S-BATH1-SH", "FX-S-SUITEBATH-TUBSH", "FX-A-STUBATH-SH"}
    for product in file.by_type("IfcSanitaryTerminal"):
        if product.Name not in bathing:
            continue
        heights = []
        for shape in product.Representation.Representations[0].Items:
            if shape.is_a("IfcTriangulatedFaceSet"):
                heights.extend(point[2] for point in shape.Coordinates.CoordList)
            else:
                heights.append(shape.Position.Location.Coordinates[2])
        assert min(heights) == pytest.approx(fixtures[product.Name].z_m)
