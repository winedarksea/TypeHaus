"""Align's small hardware stays round, closed and metallic in the shared 3D path."""

import math
from collections import Counter

import pytest

from typehaus import FurnitureType, inch
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import PART_COLORS, model_parts


@pytest.mark.parametrize("symbol,width,depth", [
    ("pivoting-paper-holder", 8.11, 3.34),
    ("towel-bar", 9.17, 3.33),
    ("towel-bar", 25.34, 3.33),
    ("towel-hook", 1.34, 2.54),
])
def test_align_hardware_has_closed_round_solids_and_satin_finish(symbol, width, depth):
    parts = model_parts(symbol, width * .0254, depth * .0254, 1.34 * .0254)
    assert parts and all(part["shape"] == "mesh" for part in parts)
    for part in parts:
        mesh = part["mesh"]
        assert len(mesh["triangles"]) >= 100
        edges = Counter()
        for triangle in mesh["triangles"]:
            points = [mesh["positions"][i] for i in triangle]
            a, b, c = points
            ab, ac = [[p[i] - a[i] for i in range(3)] for p in (b, c)]
            normal = (ab[1] * ac[2] - ab[2] * ac[1],
                      ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
            assert math.hypot(*normal) > 0
            for i in triangle:
                assert sum(n * f for n, f in zip(mesh["normals"][i], normal, strict=True)) > 0
            # Hard cap edges have duplicate vertices for normals, so weld by position.
            rounded = [tuple(round(v, 10) for v in point) for point in points]
            for a, b in zip(rounded, rounded[1:] + rounded[:1], strict=True):
                edges[tuple(sorted((a, b)))] += 1
        assert set(edges.values()) == {2}
        assert all(math.hypot(*n) == pytest.approx(1) for n in mesh["normals"])
    product = FurnitureType(tag="ALIGN", name="Align test", plan_symbol=symbol,
                            footprint=(inch(width), inch(depth)), height=inch(1.34))
    payload = _symbol_geometry(product, product.footprint)["model_parts"]
    assert all(p["mesh"] and p["metalness"] == .85 and p["roughness"] == .32 for p in payload)
    glb = _SceneBuilder()
    material = glb._material(PART_COLORS["brushed-nickel"])
    surface = glb._materials[material]["pbrMetallicRoughness"]
    assert surface["metallicFactor"] == .85 and surface["roughnessFactor"] == .32


def test_hook_has_a_recessed_towel_seat_and_a_retaining_lip():
    rear, neck, lip = model_parts("towel-hook", .034036, .064516, .034036)
    assert neck["size"][2] == rear["size"][2] == lip["size"][2]
    center_y = neck["center"][1]
    middle = [p[2] for p in neck["mesh"]["positions"] if abs(p[1] - center_y) < 1e-8]
    assert max(middle) < lip["size"][2] * .60
    assert min(middle) == pytest.approx(0)
    assert lip["center"][1] < neck["center"][1] < rear["center"][1]
