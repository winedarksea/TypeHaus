"""The glTF prism path cuts any hole and fills any simple outline (emit/gltf/triangulate.py)."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Point, Polygon

from typehaus.emit.gltf import triangulate
from typehaus.emit.gltf.mesh import _MeshBuilder, _subtract_rect

pytestmark = pytest.mark.skipif(not triangulate.HAS_CDT, reason="needs Shapely >= 2.1")

COLOR = (0.5, 0.5, 0.5, 1.0)
Z0, Z1 = 0.0, 0.1


def _circle(cx, cy, r, n=16):
    return tuple((cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
                 for k in range(n))


def _triangles(mb: _MeshBuilder):
    """Every triangle as three plan-frame (x, y, z) points (undoing the glTF swizzle)."""
    out = []
    for _color, positions, indices in mb.buckets():
        for i in range(0, len(indices), 3):
            out.append(tuple((p[0], -p[2], p[1]) for p in (positions[j] for j in indices[i:i + 3])))
    return out


def _normal_z(tri):
    (ax, ay, _), (bx, by, _), (cx, cy, _) = tri
    return (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)  # 2 x signed plan area


def _caps(mb, z):
    return [t for t in _triangles(mb) if all(abs(p[2] - z) < 1e-12 for p in t)]


SLAB = [(0.0, 0.0), (8.0, 0.0), (8.0, 8.0), (0.0, 8.0)]
HOLES = tuple(_circle(1 + 2 * i, 1 + 2 * j, 0.3) for i in range(4) for j in range(4))


def test_round_voids_are_cut_from_the_slab():
    mb = _MeshBuilder()
    mb.add_prism_with_rectangular_voids(SLAB, HOLES, Z0, Z1, COLOR)
    expected = Polygon(SLAB).area - sum(Polygon(h).area for h in HOLES)
    top, bottom = _caps(mb, Z1), _caps(mb, Z0)
    assert sum(_normal_z(t) for t in top) / 2 == pytest.approx(expected, abs=1e-5)
    assert all(_normal_z(t) > 0 for t in top)       # top faces up
    assert all(_normal_z(t) < 0 for t in bottom)    # bottom faces down
    assert sum(-_normal_z(t) for t in bottom) / 2 == pytest.approx(expected, abs=1e-5)
    holes = [Polygon(h) for h in HOLES]
    for tri in top:
        centroid = Point(sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3)
        assert not any(h.contains(centroid) for h in holes)


def test_hole_walls_face_into_the_hole():
    mb = _MeshBuilder()
    hole = _circle(4, 4, 1.0)
    mb.add_prism_with_rectangular_voids(SLAB, (hole,), Z0, Z1, COLOR)
    sides = [t for t in _triangles(mb) if abs(_normal_z(t)) < 1e-12]
    inner = [t for t in sides if all(math.hypot(p[0] - 4, p[1] - 4) < 1.01 for p in t)]
    assert len(inner) == 2 * len(hole)
    for tri in inner:
        a, b, c = (tuple(p) for p in tri)
        u = [b[k] - a[k] for k in range(3)]
        v = [c[k] - a[k] for k in range(3)]
        nx, ny = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2]
        mx, my = sum(p[0] for p in tri) / 3 - 4, sum(p[1] for p in tri) / 3 - 4
        assert nx * mx + ny * my < 0  # outward from the solid = toward the hole's centre


def test_concave_outline_fills_its_true_area():
    l_shape = [(0, 0), (4, 0), (4, 1), (1, 1), (1, 4), (0, 4)]
    # Fanned from (4, 1) the L spills outside itself; the old path would have done exactly that.
    rotated = l_shape[2:] + l_shape[:2]
    assert not triangulate.fan_is_exact(rotated)
    mb = _MeshBuilder()
    mb.add_prism(rotated, Z0, Z1, COLOR)
    top = _caps(mb, Z1)
    assert sum(_normal_z(t) for t in top) / 2 == pytest.approx(7.0)
    assert all(_normal_z(t) > 0 for t in top)
    shape = Polygon(l_shape)
    for tri in top:
        assert shape.buffer(1e-9).contains(Polygon([p[:2] for p in tri]))


def test_polygon_outline_with_a_polygon_hole():
    parcel = [(0, 0), (10, 0), (12, 6), (5, 9), (-1, 5)]
    hole = ((3, 2), (6, 2), (7, 4), (5, 6), (3, 5))
    mb = _MeshBuilder()
    mb.add_prism_with_rectangular_voids(parcel, (hole,), Z0, Z1, COLOR)
    expected = Polygon(parcel).area - Polygon(hole).area
    assert sum(_normal_z(t) for t in _caps(mb, Z1)) / 2 == pytest.approx(expected, abs=1e-5)


def _legacy_rect_path(ring, voids):
    """The strip path exactly as it stood before the general path existed."""
    mb = _MeshBuilder()
    xs, ys = {p[0] for p in ring}, {p[1] for p in ring}
    rects = [(min(xs), max(xs), min(ys), max(ys))]
    for hole in voids:
        hx, hy = {p[0] for p in hole}, {p[1] for p in hole}
        rects = [piece for rect in rects
                 for piece in _subtract_rect(rect, (min(hx), max(hx), min(hy), max(hy)))]
    for x0, x1, y0, y1 in rects:
        mb.add_prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], Z0, Z1, COLOR)
    return list(mb.buckets())


@pytest.mark.parametrize("voids", [
    (((2.0, 2.0), (3.0, 2.0), (3.0, 3.0), (2.0, 3.0)),),
    (((1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.0, 2.0)),
     ((5.0, 5.0), (7.0, 5.0), (7.0, 7.0), (5.0, 7.0))),
])
def test_rectangle_strip_path_is_unchanged(voids):
    mb = _MeshBuilder()
    mb.add_prism_with_rectangular_voids(SLAB, voids, Z0, Z1, COLOR)
    assert list(mb.buckets()) == _legacy_rect_path(SLAB, voids)


def test_convex_prism_keeps_the_fan():
    ring = [(0, 0), (3, 0), (4, 2), (1, 3)]
    mb = _MeshBuilder()
    mb.add_prism(ring, Z0, Z1, COLOR)
    (_c, positions, indices), = mb.buckets()
    n = len(ring)
    assert len(positions) == 2 * n
    assert list(indices[-6:]) == [0, 3, 2, n, n + 2, n + 3]  # the last fan pair, as before
