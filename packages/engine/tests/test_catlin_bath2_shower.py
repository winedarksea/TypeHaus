"""BATH2's stock front, stock clipped return, and molded pan drain."""

import ifcopenshell
import pytest
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

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
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.mep_sleeves import expected_port_point
from typehaus.model import Service
from typehaus.findings import Result

INCH = 0.0254


def _fixture(model):
    return next(obj for obj in model.canvas_objects if obj.tag == "FX-M-BATH2-SH")


def test_actual_finished_opening_and_outward_swing(catlin_model_ro):
    model = catlin_model_ro
    fixture = _fixture(model)
    dimensions = BATH2_SHOWER
    width, depth = dimensions.pan_width * INCH, dimensions.pan_depth * INCH
    north, south = front_opening_limits(width)
    assert (south - north) / INCH == pytest.approx(35.5)
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
    assert actual_finished_opening == pytest.approx(35.5)
    # One jamb plane: the Corian stall face below the deck, the post above it.
    stall = next(panel for panel in model.panelings if panel.tag == "WP-M-BATH2-TUBDK-STALL")
    assert min(y for _, y in stall.outline) == pytest.approx(north_jamb[1])
    deck = next(solid for solid in model.solids if solid.tag == "SL-M-TUBDK")
    east_panel = next(panel for panel in model.panelings
                      if panel.tag == "WP-M-BATH2-SURR" and panel.wall_tag == "W-M-BA2E2")
    # Its run is clipped by the room's clear face (paint takes no depth): no corner gap.
    assert min(y for _, y in east_panel.outline) == pytest.approx(finished_south_face)
    assert max(y for _, y in east_panel.outline) == pytest.approx(
        min(y for _, y in deck.outline))
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

    # A stock 80" panel on 1/4" setting blocks, 3" short of the ceiling; the post runs up.
    assert datum(north, -1) == pytest.approx(23)
    assert datum(north, 1) == pytest.approx(103)
    assert max(datum(p, 1) for p in parts) == pytest.approx(106)
    assert fixture.z_m == pytest.approx(0.75 * INCH)
    assert max(datum(p, 1) for p in front) < 77.25  # glass sits within the top rail
    rails = [p for p in parts if p["color"] == "chrome"
             and p["size"][0] == pytest.approx(width - BATH2_SHOWER.north_jamb_inset * INCH)
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
    assert authored.drain_position is None
    wire = next(t for t in canvas_object_types(model.plan) if t["tag"] == product.tag)
    assert any(p.get("material_ref") == "solid-surface-base" for p in wire["model_parts"])
    assert any(p.get("opacity", 1) < 1 for p in wire["model_parts"])
    assert any(p.get("metalness") == 1 for p in wire["model_parts"])


def test_center_drain_and_pipe_top_follow_the_manufacturer_station(catlin_model_ro):
    model = catlin_model_ro
    fixture = _fixture(model)
    drain = next(run for run in model.pipe_runs if run.tag == "PR-B-SH2-DRAIN")
    port = expected_port_point(model, fixture.tag, Service.DRAIN)
    assert port[:2] == pytest.approx(fixture.position)
    assert (*drain.path[0], drain.z_m[0]) == pytest.approx(port)
    assert drain.path[1] == pytest.approx(fixture.position)
    floor = next(floor for floor in model.floors if floor.tag == "FS-M-WEST")
    assert floor.deck_z1_m - drain.z_m[0] == pytest.approx(0.25 * INCH)
    assert drain.z_m[1] == pytest.approx(floor.deck_z0_m - 3 * INCH)


def test_drain_bay_keeps_full_span_joists_and_the_basement_ceiling(catlin_model_ro):
    model = catlin_model_ro
    floor = next(floor for floor in model.floors if floor.tag == "FS-M-WEST")
    joists = [member for member in floor.members if member.category == "joist"]
    stations = sorted({round(member.p0[1] / INCH, 6) for member in joists})
    assert [y for y in stations if 160 <= y <= 192] == [160, 170, 186, 192]
    assert max(b - a for a, b in zip(stations, stations[1:])) <= 16
    adjacent = [member for member in joists if round(member.p0[1] / INCH) in (170, 186)]
    assert len(adjacent) == 2
    assert all(member.profile == "11.875 TJI 230" for member in adjacent)
    assert adjacent[0].p0[0] == pytest.approx(adjacent[1].p0[0])
    assert adjacent[0].p1[0] == pytest.approx(adjacent[1].p1[0])
    assert all(member.length_m > 17 * 12 * INCH for member in adjacent)
    opening = model.plan.by_tag("FO-M-BATH2-SH-DRAIN")
    cut = Polygon([point.xy_m for point in opening.outline])
    assert cut.area == pytest.approx((6 * INCH) ** 2)
    assert (cut.centroid.x, cut.centroid.y) == pytest.approx(_fixture(model).position)
    assert any(Polygon(ring).equals(cut) for ring in floor.deck_voids)
    for member in adjacent:
        ring, _, _ = member_footprint(member)
        assert cut.distance(Polygon(ring)) >= 2 * INCH - 1e-8
    assert not [member for member in floor.members if opening.tag in member.child_key]
    assert opening.cuts_ceiling_below is False
    ceilings = unary_union([Polygon(ceiling.outline) for ceiling in model.ceilings
                            if ceiling.storey == "basement"])
    assert cut.difference(ceilings).area < 1e-8


def test_cleanout_takeoff_stays_on_the_straight_trap_arm(catlin_model_ro):
    model = catlin_model_ro
    drain = next(run for run in model.pipe_runs if run.tag == "PR-B-SH2-DRAIN")
    arm = LineString([drain.path[1], drain.path[3]])
    assert arm.distance(Point(drain.path[2])) < 1e-8
    cleanout = model.plan.by_tag("CO-M-SH2-HEAD")
    assert cleanout.position.xy_m == pytest.approx(drain.path[2])
    main_datum = model.plan.storey("main").elevation.meters
    assert cleanout.fitting_elevation.meters + main_datum == pytest.approx(drain.z_m[2])


def test_center_drain_has_a_vented_sloped_connected_branch(catlin_check_report):
    findings = catlin_check_report().findings
    expectations = {
        "mep.drain_slope": "PR-B-SH2-DRAIN",
        "mep.drain_tie_in": "PR-B-SH2-DRAIN",
        "mep.drain_cleanouts": "PR-B-SH2-DRAIN",
        "mep.trap_arm_length": "FX-M-BATH2-SH",
        "mep.vent_connection": "PR-M-BATH2-SH-VENT",
    }
    for check_id, tag in expectations.items():
        matching = [f for f in findings if f.check_id == check_id and tag in f.element_tags]
        assert matching, (check_id, tag)
        assert all(f.result is Result.PASS for f in matching), matching
    assert not [f for f in findings if f.result is Result.FAIL
                and (f.check_id.startswith("mep.") or f.check_id.startswith("structural."))]


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
