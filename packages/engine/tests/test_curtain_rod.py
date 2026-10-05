"""Curtain hardware stays bare, closed and shared by the viewer and GLB export."""

import json
import math
from collections import Counter

import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.library.placeables.allowances import CURTAIN_ROD_48, CURTAIN_ROD_84
from typehaus.model.canvas import _symbol_geometry, model_symbol_for
from typehaus.model.placeable_symbols import model_parts
from typehaus.resolve.model import ResolvedCanvasObject


@pytest.mark.parametrize("product,support_count", [(CURTAIN_ROD_48, 2), (CURTAIN_ROD_84, 3)])
def test_rods_have_bare_round_hardware_without_a_floor_plan_glyph(product, support_count):
    record = json.loads(json.dumps(_symbol_geometry(product, product.footprint)))
    assert product.plan_symbol is None and record["plan_strokes"] == []
    parts = model_parts(model_symbol_for(product), *(length.meters for length in product.footprint),
                        product.height.meters)
    assert len(record["model_parts"]) == len(parts)
    assert {part["color"] for part in parts} == {"metal-black"}
    plates = [part for part in parts if part["shape"] == "cylinder-depth"]
    assert len(plates) == support_count
    assert all(plate["center"][1] + plate["size"][1] / 2 == pytest.approx(
        product.footprint[1].meters / 2) for plate in plates)
    rod = parts[0]
    assert rod["shape"] == "mesh"
    assert rod["size"][1] == rod["size"][2] == pytest.approx(0.0254)
    for part in parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        edges = Counter()
        for triangle in mesh["triangles"]:
            points = [mesh["positions"][index] for index in triangle]
            a, b, c = points
            ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
                      ab[0] * ac[1] - ab[1] * ac[0])
            assert math.hypot(*normal) > 0
            for index in triangle:
                assert sum(n * f for n, f in zip(mesh["normals"][index], normal, strict=True)) > 0
            for start, end in zip(points, points[1:] + points[:1], strict=True):
                edges[tuple(sorted((start, end)))] += 1
        assert set(edges.values()) == {2}
        assert all(math.hypot(*normal) == pytest.approx(1) for normal in mesh["normals"])


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_generated_model_without_plan_symbol_exports_at_the_mounting_height(rotation):
    product = CURTAIN_ROD_48
    item = ResolvedCanvasObject(
        uid="test-rod", tag="test-rod", storey="main", domain="furniture", kind="Furniture",
        type_ref=product.tag, room=None, position=(4, 6), z_m=2.1336,
        rotation_degrees=rotation, footprint=(),
    )
    builder = _MeshBuilder()
    assert _add_canvas_parts(builder, item, product, {})
    positions = [point for vertices, _ in builder._buckets.values() for point in vertices]
    assert min(point[1] for point in positions) == pytest.approx(item.z_m)
    assert max(point[1] for point in positions) == pytest.approx(item.z_m + product.height.meters)
    rod = _symbol_geometry(product, product.footprint)["model_parts"][0]["mesh"]
    angle = math.radians(rotation)
    expected = {(x * math.cos(angle) - y * math.sin(angle) + 4, z + item.z_m,
                 -x * math.sin(angle) - y * math.cos(angle) - 6)
                for x, y, z in rod["positions"]}
    assert {tuple(round(value, 9) for value in point) for point in expected} <= {
        tuple(round(value, 9) for value in point) for point in positions}
