"""Receptacle relief, orientation and export contracts at real device sizes."""

import math
from collections import Counter
from types import SimpleNamespace

import ifcopenshell
import pytest
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.library.electrical import ALL_ELECTRICAL_DEVICE_TYPES
from typehaus.model import (
    ElectricalDeviceType,
    Location,
    ModelRepresentation,
    WallAttachment,
    deg,
    m,
)
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import PART_COLORS, model_parts, place_local
from typehaus.model.placeable_symbols._gfci_in_use_cover import (
    IN_USE_COVER_GEOMETRY as COVER_CFG,
)
from typehaus.model.placeable_symbols._receptacle_config import RECEPTACLE_GEOMETRY as CFG
from typehaus.resolve.wall_hosting import resolve_location

CATALOG = {product.tag: product for product in ALL_ELECTRICAL_DEVICE_TYPES}
WALL_TYPES = [product for product in CATALOG.values()
              if product.model_representation and product.model_representation.symbol
              and product.model_representation.symbol.startswith("receptacle-")]
HORIZONTAL_TYPES = [ElectricalDeviceType(
    tag=f"HORIZONTAL-{width}-{height}", name="Horizontal duplex",
    footprint=(m(width * .0254), m(.0508)), height=m(height * .0254),
    model_representation=ModelRepresentation(symbol="receptacle-duplex"))
    for width, height in ((4, 2), (4.5, 3))]
FLOOR_TYPE = ElectricalDeviceType(
    tag="FLOOR", name="Floor receptacle", footprint=(m(.168), m(.168)), height=m(.166),
    model_representation=ModelRepresentation(symbol="receptacle-floor"))
COVER_TYPES = [ElectricalDeviceType(
    tag=f"COVER-{amperage}", name="Covered GFCI",
    footprint=(m(3.63 * .0254), m(3.08 * .0254)), height=m(6.69 * .0254),
    model_representation=ModelRepresentation(symbol=symbol))
    for amperage, symbol in ((20, "receptacle-gfci-in-use-cover"),
                             (15, "receptacle-gfci-in-use-cover-15a"))]


def _parts(product):
    width, depth = (dimension.meters for dimension in product.footprint)
    return model_parts(product.model_representation.symbol, width, depth, product.height.meters)


@pytest.mark.parametrize("tag", ["ED-T-RECEPTACLE", "ED-T-RECEPTACLE-GFCI",
                                 "ED-T-RECEPTACLE-520S"])
def test_single_gang_catalog_is_vertical(tag):
    product = CATALOG[tag]
    # Face width and projection past the plate; the plate and box are derived solids.
    assert [dimension.inches for dimension in product.footprint] == pytest.approx([1.31, 0.2])
    assert product.height.inches == pytest.approx(2.63)


@pytest.mark.parametrize("product", [*WALL_TYPES, *HORIZONTAL_TYPES, FLOOR_TYPE, *COVER_TYPES],
                         ids=lambda p: p.tag)
def test_geometry_is_bounded_closed_and_in_budget(product):
    parts = _parts(product)
    width, depth = (dimension.meters for dimension in product.footprint)
    height = product.height.meters
    triangle_count = 0
    is_cover = product in COVER_TYPES
    budget = COVER_CFG if is_cover else CFG
    assert len(parts) <= budget.maximum_parts
    for part in parts:
        center, size = part["center"], part["size"]
        assert all(value > 0 for value in size)
        for coordinate, extent, lower, upper in zip(center, size,
                (-width / 2, -depth / 2, 0), (width / 2, depth / 2, height), strict=True):
            assert coordinate - extent / 2 >= lower - 1e-9
            assert coordinate + extent / 2 <= upper + 1e-9
        if "mesh" not in part:
            triangle_count += 4 * len(part["points"]) - 4 if part["points"] else 12
            continue
        mesh = part["mesh"]
        triangle_count += len(mesh["triangles"])
        edges = Counter()
        for triangle in mesh["triangles"]:
            points = [mesh["positions"][index] for index in triangle]
            for index in range(3):
                edge = (points[index], points[(index + 1) % 3])
                edges[edge] += 1
            for index in triangle:
                normal = mesh["normals"][index]
                assert math.sqrt(sum(value ** 2 for value in normal)) == pytest.approx(1)
                displacement = [mesh["positions"][index][axis] - center[axis] for axis in range(3)]
                if part.get("role") != "in-use-cover:cord-exits":
                    assert sum(a * b for a, b in zip(normal, displacement, strict=True)) > 0
        assert all(count == 1 and edges[(end, start)] == 1
                   for (start, end), count in edges.items())
    assert triangle_count <= budget.maximum_triangles
    assert parts[0]["color"] == ("weatherproof-cover" if is_cover else "device-face")
    assert {part["color"] for part in parts} <= {
        "device-face", "device-slot", "device-accent", "clear-glass", "weatherproof-cover"}


@pytest.mark.parametrize("tag,socket_count", [
    ("ED-T-RECEPTACLE", 2), ("ED-T-RECEPTACLE-520S", 1),
    ("ED-T-RECEPTACLE-620", 2), ("ED-T-RECEPTACLE-QUAD-520", 4),
    ("ED-T-RECEPTACLE-GFCI", 2), ("ED-T-EV-620", 1)])
def test_sockets_stand_on_the_slab_and_grounds_sit_below_blades(tag, socket_count):
    slab, *details = _parts(CATALOG[tag])
    faces = [part for part in details if part["color"] == "device-face"]
    grounds = [part for part in details if part["color"] == "device-slot" and "mesh" in part]
    assert len(faces) == len(grounds) == socket_count
    slab_front = slab["center"][1] - slab["size"][1] / 2
    for face, ground in zip(faces, grounds, strict=True):
        assert ground["center"][1] < face["center"][1] < slab_front + face["size"][1]
        assert face["center"][1] + face["size"][1] / 2 == pytest.approx(slab_front)
        assert ground["center"][2] < face["center"][2]
        assert ground["center"][0] == pytest.approx(face["center"][0])
    columns, rows = {"ED-T-RECEPTACLE-620": (2, 1), "ED-T-RECEPTACLE-QUAD-520": (2, 2)}.get(
        tag, (1, socket_count))
    assert len({face["center"][0] for face in faces}) == columns
    assert len({face["center"][2] for face in faces}) == rows


def test_gfci_buttons_sit_between_sockets_and_blank_gfci_has_only_buttons():
    details = _parts(CATALOG["ED-T-RECEPTACLE-GFCI"])[1:]
    buttons = [part for part in details if part["color"] == "device-accent"]
    sockets = [part for part in details if part["color"] == "device-face"]
    assert len(buttons) == 2
    top, bottom = sorted(sockets, key=lambda part: -part["center"][2])
    assert all(bottom["center"][2] < b["center"][2] < top["center"][2] for b in buttons)
    blank = model_parts("receptacle-blank-gfci", .0333, .0051, .0668)
    assert [part["color"] for part in blank].count("device-accent") == 2
    assert not [part for part in blank if "mesh" in part]


@pytest.mark.parametrize("product", HORIZONTAL_TYPES, ids=lambda p: p.tag)
def test_horizontal_duplex_rotates_sockets_and_slots_without_squashing(product):
    vertical_details = _parts(CATALOG["ED-T-RECEPTACLE"])[1:]
    horizontal_details = _parts(product)[1:]
    vertical_face = vertical_details[0]
    horizontal_face = horizontal_details[0]
    scale = horizontal_face["size"][0] / vertical_face["size"][2]
    for vertical, horizontal in zip(vertical_details, horizontal_details, strict=True):
        assert horizontal["size"][0] == pytest.approx(vertical["size"][2] * scale)
        assert horizontal["size"][2] == pytest.approx(vertical["size"][0] * scale)
        assert horizontal["color"] == vertical["color"]
    faces = [part for part in horizontal_details if part["color"] == "device-face"]
    grounds = [part for part in horizontal_details
               if part["color"] == "device-slot" and "mesh" in part]
    assert faces[0]["center"][0] > faces[1]["center"][0]
    for face, ground in zip(faces, grounds, strict=True):
        assert face["center"][2] == pytest.approx(product.height.meters / 2)
        assert ground["center"][0] < face["center"][0]
        assert ground["center"][2] == pytest.approx(face["center"][2])


@pytest.mark.parametrize("angle", [0, 90, 37])
@pytest.mark.parametrize("side,offset", [("right", 0), ("left", 180)])
def test_wall_attachment_keeps_socket_front_facing_room(angle, side, offset):
    radians = math.radians(angle)
    tangent = (math.cos(radians), math.sin(radians))
    left = (-tangent[1], tangent[0])
    wall = SimpleNamespace(tag="W", axis=((0, 0), (tangent[0] * 4, tangent[1] * 4)), layers=[])
    item = SimpleNamespace(tag="R", location=Location(attachment=WallAttachment(
        wall_ref="W", face=side, distance_from_start=m(2), rotation_offset=deg(offset))))
    width, depth = (value.meters for value in CATALOG["ED-T-RECEPTACLE"].footprint)
    footprint = [(-width / 2, -depth / 2), (width / 2, -depth / 2),
                 (width / 2, depth / 2), (-width / 2, depth / 2)]
    position, rotation, _, _ = resolve_location(
        item, SimpleNamespace(wall=lambda ref: wall), [], footprint)
    outward = place_local([(0, -1)], (0, 0), rotation)[0]
    sign = 1 if side == "left" else -1
    assert sum(outward[axis] * left[axis] * sign for axis in range(2)) == pytest.approx(1)
    assert position is not None
    assert rotation == pytest.approx(angle + offset)


@pytest.mark.parametrize("product", [*WALL_TYPES, *HORIZONTAL_TYPES, FLOOR_TYPE, *COVER_TYPES],
                         ids=lambda p: p.tag)
def test_viewer_gltf_and_ifc_keep_shared_relief_and_colors(product):
    parts = _parts(product)
    viewer = _symbol_geometry(product, product.footprint)["model_parts"]
    assert len(viewer) == len(parts)
    for serialized, part in zip(viewer, parts, strict=True):
        if "mesh" in part:
            assert serialized["shape"] == "mesh"
            assert serialized["mesh"] == part["mesh"]
    builder = _MeshBuilder()
    item = SimpleNamespace(position=(1, 2), rotation_degrees=37, z_m=1, mount=None)
    assert _add_canvas_parts(builder, item, product, {})
    assert set(builder._buckets) == {PART_COLORS[part["color"]] for part in parts}
    gltf_positions = [point for positions, _ in builder._buckets.values() for point in positions]
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext")
    representation = parts_representation(file, context, parts, item.position,
                                          item.rotation_degrees, item.z_m)
    assert len(representation.Items) == len(parts)
    ifc_positions = [point for mesh in representation.Items for point in mesh.Coordinates.CoordList]
    # glTF's axes are X east, Y up, Z south; compare transformed bounds with IFC.
    transformed = [(x, z, -y) for x, y, z in ifc_positions]
    for axis in range(3):
        assert min(point[axis] for point in gltf_positions) == pytest.approx(
            min(point[axis] for point in transformed))
        assert max(point[axis] for point in gltf_positions) == pytest.approx(
            max(point[axis] for point in transformed))
    assert all(mesh.Closed for mesh in representation.Items)


@pytest.mark.parametrize("product", COVER_TYPES, ids=lambda p: p.tag)
def test_in_use_cover_keeps_vertical_gfci_at_back_of_clear_plug_cavity(product):
    parts = _parts(product)
    face_parts = [part for part in parts if part["color"] in {
        "device-face", "device-slot", "device-accent"}]
    sockets = [part for part in face_parts if "mesh" in part and part["color"] == "device-face"]
    assert len(sockets) == 2
    assert sockets[0]["center"][0] == pytest.approx(sockets[1]["center"][0])
    assert abs(sockets[0]["center"][2] - sockets[1]["center"][2]) > .0254
    back = product.footprint[1].meters / 2
    # The cover projects 3.08 inches; the electrical face stays within 0.35 inches
    # of its mounting plane, leaving space for a plug behind the closed clear lid.
    front = min(p["center"][1] - p["size"][1] / 2 for p in face_parts)
    assert back - front <= .35 * .0254 + 1e-9
    assert sum(p["color"] == "device-accent" for p in parts) == 2
    appearance = _symbol_geometry(product, product.footprint)["model_parts"]
    assert sum(p.get("opacity", 1) < 1 for p in appearance) == 9


@pytest.mark.parametrize("scale", [.5, 1, 2])
def test_cover_tapers_toward_front_and_has_two_open_cord_ports(scale):
    unit = .0254 * scale
    parts = model_parts("receptacle-gfci-in-use-cover", COVER_CFG.width_in * unit,
                        COVER_CFG.depth_in * unit, COVER_CFG.height_in * unit)
    hood = [part for part in parts if part["color"] == "clear-glass"]
    front_pane = hood[0]
    assert front_pane["size"][0] < parts[0]["size"][0]
    assert front_pane["size"][2] < parts[0]["size"][2]
    # Inspect exported triangles, so a solid panel with painted port marks cannot pass.
    bottom_panel = next(part for part in hood if part.get("role") == "in-use-cover:cord-exits")
    mesh = bottom_panel["mesh"]
    bottom = COVER_CFG.body_bottom_in * unit
    horizontal_faces = []
    for indices in mesh["triangles"]:
        triangle = [mesh["positions"][index] for index in indices]
        if all(abs(z - bottom) < 1e-9 for _, _, z in triangle):
            horizontal_faces.append(Polygon([(x, y) for x, y, _ in triangle]))
    sheet = unary_union(horizontal_faces)
    assert sheet.is_valid
    assert sheet.geom_type == "Polygon"
    assert len(sheet.interiors) == 2
    port_y = (-COVER_CFG.depth_in / 2 + COVER_CFG.cord_exit_front_setback_in) * unit
    for sign in (-1, 1):
        assert not sheet.covers(Point(sign * COVER_CFG.cord_exit_spacing_in * unit / 2, port_y))
    assert sheet.covers(Point(0, port_y))


def test_catlin_weather_resistant_gfcis_use_cover_geometry(catlin_plan):
    products = {product.tag: product for product in catlin_plan.library.electrical_device_types}
    for tag, expected in zip(("ED-T-LEV-GFCI-WR", "ED-T-LEV-GFCI-WR-15"),
                             COVER_TYPES, strict=True):
        product = products[tag]
        assert product.model_representation.symbol == expected.model_representation.symbol
        assert product.footprint == expected.footprint
        assert product.height == expected.height


def test_catlin_hosted_receptacles_face_away_from_wall(catlin_model_ro):
    model = catlin_model_ro
    products = {product.tag: product for product in model.plan.library.electrical_device_types}
    inspected = 0
    for obj in model.canvas_objects:
        product = products.get(obj.type_ref)
        if product is None or product.model_representation is None:
            continue
        symbol = product.model_representation.symbol or ""
        if not symbol.startswith("receptacle-") or not obj.attachment_wall:
            continue
        wall = model.wall(obj.attachment_wall)
        dx = wall.axis[1][0] - wall.axis[0][0]
        dy = wall.axis[1][1] - wall.axis[0][1]
        angle = math.radians(obj.rotation_degrees)
        sign = 1 if obj.attachment_face == "left" else -1
        outward_projection = (math.sin(angle) * -dy - math.cos(angle) * dx) * sign
        assert outward_projection / math.hypot(dx, dy) == pytest.approx(1), obj.tag
        inspected += 1
    assert inspected > 100
