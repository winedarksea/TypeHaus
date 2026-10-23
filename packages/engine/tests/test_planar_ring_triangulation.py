"""Concave swept caps tile their silhouettes, including stair notches and collinear edges."""

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_slice import sweep_mesh
from typehaus.triangulation import planar_ring_triangles

_SIDE = ((0, 0), (3, 1.5), (3, 2.5), (2, 2.5), (2, 2),
         (1, 2), (1, 1.5), (0.5, 1.5), (0, 1.5))


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_concave_caps_cover_only_the_ring(axis, reverse):
    side = tuple(reversed(_SIDE)) if reverse else _SIDE
    ring = []
    for s, z in side:
        point = [s, z]
        point.insert(axis, 0.0)
        ring.append(tuple(point))
    triangles = planar_ring_triangles(ring)
    polygon = Polygon(side)
    caps = [Polygon([side[i] for i in tri]) for tri in triangles]
    assert unary_union(caps).symmetric_difference(polygon).area < 1e-12
    assert sum(cap.area for cap in caps) == pytest.approx(polygon.area)
    area = sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(side, side[1:] + side[:1], strict=True))
    for a, b, c in triangles:
        ax, ay = side[a]
        bx, by = side[b]
        cx, cy = side[c]
        assert area * ((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) > 0


def test_gltf_and_section_mesh_caps_preserve_the_sawtooth():
    sweep = GSweep(profile=tuple((s, 0, z) for s, z in _SIDE), extrude=(0, 0.0381, 0))
    mesh = sweep_mesh(sweep)
    builder = _MeshBuilder()
    color = (1, 1, 1, 1)
    builder.add_sweep(sweep, color)
    _, indices = builder._buckets[color]
    assert list(indices) == [i for triangle in mesh.triangles for i in triangle]
    count = len(_SIDE)
    caps = [Polygon([_SIDE[i] for i in tri]) for tri in mesh.triangles
            if all(i < count for i in tri)]
    assert sum(cap.area for cap in caps) == pytest.approx(Polygon(_SIDE).area)
    assert unary_union(caps).symmetric_difference(Polygon(_SIDE)).area < 1e-12


def test_invalid_ring_fails_explicitly():
    with pytest.raises(ValueError, match="zero-area"):
        planar_ring_triangles(((0, 0, 0), (1, 0, 0), (2, 0, 0)))
