"""Receptacle relief, orientation and export contracts at real device sizes."""

import math
from collections import Counter
from types import SimpleNamespace

import ifcopenshell
import pytest

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
from typehaus.model.placeable_symbols._receptacle_config import RECEPTACLE_GEOMETRY as CFG
from typehaus.resolve.wall_hosting import resolve_location

CATALOG = {product.tag: product for product in ALL_ELECTRICAL_DEVICE_TYPES}
WALL_TYPES = [product for product in CATALOG.values()
              if product.model_representation and product.model_representation.symbol
              and product.model_representation.symbol.startswith("receptacle-")]
FLOOR_TYPE = ElectricalDeviceType(
    tag="FLOOR", name="Floor receptacle", footprint=(m(.168), m(.168)), height=m(.166),
    model_representation=ModelRepresentation(symbol="receptacle-floor"))


def _parts(product):
    width, depth = (dimension.meters for dimension in product.footprint)
    return model_parts(product.model_representation.symbol, width, depth, product.height.meters)


@pytest.mark.parametrize("tag", ["ED-T-RECEPTACLE", "ED-T-RECEPTACLE-GFCI",
                                 "ED-T-RECEPTACLE-520S"])
def test_single_gang_catalog_is_vertical(tag):
    product = CATALOG[tag]
    assert [dimension.inches for dimension in product.footprint] == pytest.approx([2.75, 2])
    assert product.height.inches == pytest.approx(4.5)


@pytest.mark.parametrize("product", [*WALL_TYPES, FLOOR_TYPE], ids=lambda p: p.tag)
def test_geometry_is_bounded_closed_and_in_budget(product):
    parts = _parts(product)
    width, depth = (dimension.meters for dimension in product.footprint)
    height = product.height.meters
    triangle_count = 0
    assert len(parts) <= CFG.maximum_parts
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
                assert sum(a * b for a, b in zip(normal, displacement, strict=True)) > 0
        assert all(count == 1 and edges[(end, start)] == 1
                   for (start, end), count in edges.items())
    assert triangle_count <= CFG.maximum_triangles
    assert parts[0]["color"] == "electrical-orange"


@pytest.mark.parametrize("tag,socket_count", [
    ("ED-T-RECEPTACLE", 2), ("ED-T-RECEPTACLE-520S", 1),
    ("ED-T-RECEPTACLE-620", 2), ("ED-T-RECEPTACLE-QUAD-520", 4),
    ("ED-T-EV-620", 1), ("ED-T-EV-1450", 1)])
def test_faces_project_in_front_of_plate_and_grounds_below_blades(tag, socket_count):
    housing, plate, *details = _parts(CATALOG[tag])
    faces = [part for part in details if part["color"] == "electrical-orange"]
    grounds = [part for part in details if part["color"] == "electrical-recess" and "mesh" in part]
    assert len(faces) == len(grounds) == socket_count
    assert plate["center"][1] < housing["center"][1]
    for face, ground in zip(faces, grounds, strict=True):
        assert ground["center"][1] < face["center"][1] < plate["center"][1]
        assert ground["center"][2] < face["center"][2]
        assert ground["center"][0] == pytest.approx(face["center"][0])
    assert len({face["center"][0] for face in faces}) == (2 if socket_count == 4 else 1)
    assert len({face["center"][2] for face in faces}) == (2 if socket_count > 1 else 1)


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


@pytest.mark.parametrize("product", [*WALL_TYPES, FLOOR_TYPE], ids=lambda p: p.tag)
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
