"""Selected product silhouettes and export solids, independent of house generation."""

import pytest
import trimesh

from typehaus.model.placeable_symbols import model_parts, plan_symbol_strokes

INCH = .0254
PRODUCTS = (
    ("sconce-slim-updown", (4.5, 2.5, 12)),
    ("sconce-bantam", (9, 4, 3.5)),
    ("sconce-soren", (5, 4.8, 14.3)),
    ("sconce-tube", (4.5, 5, 5)),
    ("sconce-candle", (4.25, 7.75, 11.25)),
    ("sconce-bantam-down", (9, 4, 3.5)),
)


def _parts(symbol, size):
    return model_parts(symbol, *(value * INCH for value in size))


@pytest.mark.parametrize("symbol,size", PRODUCTS)
def test_sconce_meshes_have_closed_outward_surfaces(symbol, size):
    for part in _parts(symbol, size):
        if "mesh" not in part:
            continue
        mesh = trimesh.Trimesh(vertices=part["mesh"]["positions"],
                               faces=part["mesh"]["triangles"])
        assert mesh.is_watertight
        assert mesh.is_winding_consistent
        assert mesh.volume > 0


def test_roland_has_two_broad_diffusers_and_a_center_belt():
    parts = _parts(*PRODUCTS[0])
    diffusers = [part for part in parts if part["color"] == "lamp"]
    assert len(diffusers) == 2
    assert all(part["size"][0] == pytest.approx(4.5 * INCH) for part in diffusers)
    assert all(part["size"][2] == pytest.approx(5.3 * INCH) for part in diffusers)
    canopy = parts[0]
    assert canopy["size"] == pytest.approx((4.5 * INCH, INCH, 4.5 * INCH))


@pytest.mark.parametrize("symbol,downward", [
    ("sconce-bantam", False), ("sconce-bantam-down", True),
])
def test_bantam_shields_its_wall_side_lens_in_both_orientations(symbol, downward):
    parts = _parts(symbol, (9, 4, 3.5))
    shield, shelf = parts[:2]
    lens = next(part for part in parts if part["color"] == "lamp")
    # +y is the wall: a room-side sightline must meet the full-height shield first.
    assert shield["center"][1] - shield["size"][1] / 2 == pytest.approx(-2 * INCH)
    assert shelf["center"][1] + shelf["size"][1] / 2 == pytest.approx(2 * INCH)
    assert lens["center"][1] - lens["size"][1] / 2 > (
        shield["center"][1] + shield["size"][1] / 2)
    assert lens["size"][0] < shield["size"][0]
    assert shield["size"][2] == pytest.approx(3.5 * INCH)
    if downward:
        assert shelf["center"][2] + shelf["size"][2] / 2 == pytest.approx(3.5 * INCH)
        assert lens["center"][2] - lens["size"][2] / 2 == pytest.approx(2 * INCH)
        assert lens["center"][2] + lens["size"][2] / 2 == pytest.approx(
            shelf["center"][2] - shelf["size"][2] / 2)
    else:
        assert shelf["center"][2] - shelf["size"][2] / 2 == pytest.approx(0)
        assert lens["center"][2] + lens["size"][2] / 2 == pytest.approx(1.5 * INCH)
        assert lens["center"][2] - lens["size"][2] / 2 == pytest.approx(
            shelf["center"][2] + shelf["size"][2] / 2)
    strokes = plan_symbol_strokes(symbol, 9 * INCH, 4 * INCH)
    assert any(stroke["fill"] == "lamp" for stroke in strokes) is not downward


def test_soren_has_a_round_high_canopy_and_open_fluted_glass():
    parts = _parts(*PRODUCTS[2])
    assert parts[0]["size"] == pytest.approx((5 * INCH, .5 * INCH, 5 * INCH))
    assert parts[0]["center"][2] == pytest.approx(11.8 * INCH)
    glass = next(part for part in parts if part["color"] == "clear-glass")
    mesh = trimesh.Trimesh(vertices=glass["mesh"]["positions"],
                           faces=glass["mesh"]["triangles"])
    # An axial sightline must remain open through both ends of the glass sleeve.
    for triangle in mesh.triangles:
        radius = ((triangle[:, 0] ** 2
                   + (triangle[:, 1] + .9 * INCH) ** 2) ** .5)
        assert min(radius) > 1.3 * INCH
    bulb = next(part for part in parts if part["color"] == "lamp")
    assert bulb["size"][0] < glass["size"][0]


def test_tube_lens_is_recessed_above_cutoff_lip():
    parts = _parts(*PRODUCTS[3])
    lens = next(part for part in parts if part["color"] == "lamp")
    assert lens["center"][2] - lens["size"][2] / 2 == pytest.approx(.3 * INCH)
    assert lens["size"][0] < parts[2]["size"][0]


def test_candle_has_oval_plate_bent_arm_and_pointed_bulb():
    parts = _parts(*PRODUCTS[4])
    assert parts[0]["size"] == pytest.approx((4 * INCH, .36 * INCH, 6 * INCH))
    arm = parts[2]
    assert arm["center"][2] - arm["size"][2] / 2 < .2 * INCH
    bulb = next(part for part in parts if part["color"] == "lamp")
    assert bulb["center"][2] + bulb["size"][2] / 2 == pytest.approx(11.25 * INCH)


def test_catlin_uses_the_selected_product_builders(catlin_plan):
    types = {item.tag: item for item in catlin_plan.library.electrical_device_types}
    for tag, symbol, size in (
        ("ED-T-LT-SCONCE-STAIR", "sconce-bantam", (9, 4, 3.5)),
        ("ED-T-LT-SCONCE-BANTAM-DOWN", "sconce-bantam-down", (9, 4, 3.5)),
        ("ED-T-LT-SCONCE-VANITY", "sconce-soren", (5, 4.8, 14.3)),
        ("ED-T-LT-SCONCE-CANDLE", "sconce-candle", (4.25, 7.75, 11.25)),
    ):
        product = types[tag]
        assert product.plan_symbol == symbol
        assert tuple(value.meters for value in (*product.footprint, product.height)) == (
            pytest.approx(tuple(value * INCH for value in size)))


def test_selected_sconces_reach_viewer_and_both_exporters(catlin_model_ro):
    import ifcopenshell

    from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.ifc.placeable_parts import parts_representation
    from typehaus.model.canvas import _symbol_geometry, model_symbol_for

    types = {item.tag: item for item in catlin_model_ro.plan.library.electrical_device_types}
    for tag in ("ED-T-LT-SCONCE-UD", "ED-T-LT-SCONCE-STAIR", "ED-T-LT-SCONCE-BANTAM-DOWN",
                "ED-T-LT-SCONCE-VANITY",
                "ED-T-LT-SCONCE-EXT", "ED-T-LT-SCONCE-CANDLE"):
        fixture = next(item for item in catlin_model_ro.canvas_objects if item.type_ref == tag)
        product = types[tag]
        parts = model_parts(model_symbol_for(product), *(v.meters for v in product.footprint),
                            product.height.meters)
        wire = _symbol_geometry(product, product.footprint)
        assert len(wire["model_parts"]) == len(parts)
        mesh = _MeshBuilder()
        assert _add_canvas_parts(mesh, fixture, product, {})
        assert mesh._buckets
        file = ifcopenshell.file(schema="IFC4")
        context = file.create_entity("IfcGeometricRepresentationContext",
                                     CoordinateSpaceDimension=3)
        representation = parts_representation(file, context, parts, fixture.position,
                                               fixture.rotation_degrees, fixture.z_m)
        assert len(representation.Items) == len(parts)
