"""LED waves are closed, smoothly shaded ribbons in the viewer contract and GLB export."""

from __future__ import annotations

import json
import math
from collections import Counter

import pytest

from typehaus.emit.gltf.buffers import _deindex_with_normals
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import PART_COLORS, lamp_role, model_parts


def test_wave_bands_are_connected_closed_solids_with_outward_smooth_normals() -> None:
    bands = [part for part in model_parts("wave-chandelier", 1.2192, 0.4064, 1.0668)
             if "mesh" in part]
    assert len(bands) == 10  # One brass body and one LED underside per strip.
    for part in bands:
        mesh = part["mesh"]
        positions, normals = mesh["positions"], mesh["normals"]
        edges = Counter()
        adjacency = {point: set() for point in positions}
        for triangle in mesh["triangles"]:
            points = [positions[index] for index in triangle]
            a, b, c = points
            ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            face_normal = (ab[1] * ac[2] - ab[2] * ac[1],
                           ab[2] * ac[0] - ab[0] * ac[2],
                           ab[0] * ac[1] - ab[1] * ac[0])
            assert math.hypot(*face_normal) > 0
            for index in triangle:
                assert sum(n * f for n, f in zip(normals[index], face_normal, strict=True)) > 0
            for start, end in zip(points, points[1:] + points[:1], strict=True):
                edges[tuple(sorted((start, end)))] += 1
                adjacency[start].add(end)
                adjacency[end].add(start)
        assert set(edges.values()) == {2}  # No gaps or internal segment caps.
        visited, pending = set(), [positions[0]]
        while pending:
            point = pending.pop()
            if point not in visited:
                visited.add(point)
                pending.extend(adjacency[point] - visited)
        assert visited == set(positions)
        assert all(math.hypot(*normal) == pytest.approx(1.0) for normal in normals)
        assert any(abs(normal[0]) > 0.1 and abs(normal[2]) > 0.1 for normal in normals)
        for axis in range(3):
            values = [point[axis] for point in positions]
            assert part["center"][axis] == pytest.approx((min(values) + max(values)) / 2)
            assert part["size"][axis] == pytest.approx(max(values) - min(values))

    for lamp, housing in zip(bands[::2], bands[1::2], strict=True):
        assert lamp["color"] == "lamp" and housing["color"] == "brass"
        # The shared boundary follows the same curve: no cracks or brass occluding the LED.
        lamp_tops = {}
        for x, y, z in lamp["mesh"]["positions"]:
            lamp_tops[(x, y)] = max(lamp_tops.get((x, y), z), z)
        housing_bottoms = {}
        for x, y, z in housing["mesh"]["positions"]:
            housing_bottoms[(x, y)] = min(housing_bottoms.get((x, y), z), z)
        assert lamp_tops == housing_bottoms


def test_dining_pendant_serializes_ribbons_and_exports_the_same_normals(catlin_model_ro) -> None:
    model = catlin_model_ro
    item = next(item for item in model.canvas_objects if item.tag == "ED-M-DINING-PEND")
    chandelier = next(kind for kind in model.plan.library.electrical_device_types
                      if kind.tag == item.type_ref)
    # Round-trip the actual wire contract: no special Python-only geometry values.
    record = json.loads(json.dumps(_symbol_geometry(chandelier, chandelier.footprint)))
    assert len(record["model_parts"]) == 21  # Previously 411 block parts.
    bands = [part for part in record["model_parts"] if part.get("shape") == "mesh"]
    assert len(bands) == 10 and all(part["mesh"]["normals"] for part in bands)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, chandelier, {})
    color = PART_COLORS[lamp_role(chandelier.cct_k)]
    positions, indices = mesh._buckets[color]
    exported_positions, exported_normals = _deindex_with_normals(positions, indices)
    expected_positions, expected_normals = [], []
    angle = math.radians(item.rotation_degrees)
    for part in bands[::2]:
        source = part["mesh"]
        for triangle in source["triangles"]:
            for index in triangle:
                x, y, z = source["positions"][index]
                expected_positions.append((x * math.cos(angle) - y * math.sin(angle)
                                           + item.position[0], z + item.z_m,
                                           -x * math.sin(angle) - y * math.cos(angle)
                                           - item.position[1]))
                nx, ny, nz = source["normals"][index]
                expected_normals.append((nx * math.cos(angle) - ny * math.sin(angle), nz,
                                         -nx * math.sin(angle) - ny * math.cos(angle)))
    assert len(exported_positions) == len(expected_positions)
    assert len(exported_normals) == len(expected_normals)
    assert all(actual == pytest.approx(expected) for actual, expected in
               zip(exported_positions, expected_positions, strict=True))
    assert all(actual == pytest.approx(expected) for actual, expected in
               zip(exported_normals, expected_normals, strict=True))
