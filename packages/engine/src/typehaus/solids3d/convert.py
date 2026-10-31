"""Geometry IR -> manifold3d solids.

Two pitfalls shape this module. IR ring winding is not normalised, so a flat ``GPrism`` is
filled NonZero (either winding fills) less the union of its voids, each filled on its own;
and every ring-pair solid (``GBox``, ``GSweep``, a raked ``GPrism``) is oriented by its
signed volume.
A ``GMesh`` is taken exactly as authored and never re-oriented: an inverted mesh comes back
with negative volume, and that is a finding, not something to fix here.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np

from typehaus.resolve.geometry_ir import (
    ElementGeometry,
    GBox,
    GMesh,
    GPrism,
    GSolid,
    GSweep,
    signed_volume,
)
from typehaus.solids3d import require_manifold3d

Vec3 = tuple[float, float, float]


def to_manifold(solid: GSolid):
    """One IR solid as a ``Manifold`` (check ``.status()`` before trusting it)."""
    m3d = require_manifold3d()
    if isinstance(solid, GPrism):
        if solid.top is None:
            return _flat_prism(m3d, solid.ring, solid.voids, solid.z0_m, solid.z1_m)
        bottom = [(x, y, solid.z0_m) for x, y in solid.ring]
        top = [(x, y, z) for (x, y), z in zip(solid.ring, solid.top, strict=True)]
        body = ring_pair_manifold(bottom, top)
        if solid.voids:  # none on catlin today; cut through the full raked height
            depth = max(solid.top) - solid.z0_m + 2.0
            body = body - _holes(m3d, solid.voids).extrude(depth).translate(
                (0.0, 0.0, solid.z0_m - 1.0))
        return body
    if isinstance(solid, GBox):
        return ring_pair_manifold(solid.corners_bottom, solid.corners_top)
    if isinstance(solid, GSweep):
        dx, dy, dz = solid.extrude
        return ring_pair_manifold(solid.profile,
                                  [(x + dx, y + dy, z + dz) for x, y, z in solid.profile])
    if isinstance(solid, GMesh):
        return mesh_manifold(solid.positions, solid.triangles)
    raise TypeError(f"not an IR solid: {type(solid).__name__}")


def element_manifold(element: ElementGeometry):
    """Every solid of every part of one element, unioned."""
    return union(to_manifold(solid) for part in element.parts for solid in part.solids)


def union(manifolds: Iterable):
    m3d = require_manifold3d()
    items = [item for item in manifolds if not item.is_empty()]
    if not items:
        return m3d.Manifold()
    if len(items) == 1:
        return items[0]
    return m3d.Manifold.batch_boolean(items, m3d.OpType.Add)


def _flat_prism(m3d, ring: Sequence, voids: Sequence, z0: float, z1: float):
    if z1 - z0 <= 0:
        return m3d.Manifold()
    section = m3d.CrossSection([list(ring)], m3d.FillRule.NonZero)
    if voids:
        section = section - _holes(m3d, voids)
    return section.extrude(z1 - z0).translate((0.0, 0.0, z0))


def _holes(m3d, voids: Sequence):
    """The union of the voids, each filled on its own: two overlapping voids wound opposite
    ways would cancel to winding 0 in one NonZero section, and their overlap stay solid."""
    sections = [m3d.CrossSection([list(void)], m3d.FillRule.NonZero) for void in voids]
    if len(sections) == 1:
        return sections[0]
    return m3d.CrossSection.batch_boolean(sections, m3d.OpType.Add)


def mesh_manifold(positions: Sequence[Vec3], triangles: Sequence[tuple[int, int, int]]):
    """A triangle soup as authored: coincident vertices merged, winding untouched."""
    m3d = require_manifold3d()
    if not triangles:
        return m3d.Manifold()
    mesh = m3d.Mesh64(vert_properties=np.asarray(positions, dtype=np.float64),
                      tri_verts=np.asarray(triangles, dtype=np.uint32))
    mesh.merge()
    return m3d.Manifold(mesh)


def ring_pair_manifold(bottom: Sequence[Vec3], top: Sequence[Vec3]):
    """A closed solid between two corresponding rings, flipped outward by signed volume."""
    m3d = require_manifold3d()
    count = len(bottom)
    positions = [*bottom, *top]
    cap = _cap_triangles(bottom)
    triangles: list[tuple[int, int, int]] = []
    for i in range(count):
        j = (i + 1) % count
        triangles += [(i, j, count + j), (i, count + j, count + i)]
    triangles += [(a, c, b) for a, b, c in cap]                          # bottom: against
    triangles += [(count + a, count + b, count + c) for a, b, c in cap]  # top: with the ring
    if signed_volume(positions, triangles) < 0:
        triangles = [(a, c, b) for a, b, c in triangles]
    mesh = m3d.Mesh64(vert_properties=np.asarray(positions, dtype=np.float64),
                      tri_verts=np.asarray(triangles, dtype=np.uint32))
    mesh.merge()
    return m3d.Manifold(mesh)


def _cap_triangles(ring: Sequence[Vec3]) -> list[tuple[int, int, int]]:
    """A cap triangulation wound in the ring's own rotational sense (its edges run i -> i+1)."""
    m3d = require_manifold3d()
    normal = _newell(ring)
    length = math.sqrt(sum(c * c for c in normal))
    if length < 1e-18:
        return []
    n = [c / length for c in normal]
    helper = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = _unit(_cross(n, helper))
    v = _cross(n, u)
    flat = np.array([[_dot(p, u), _dot(p, v)] for p in ring], dtype=np.float64)
    # Newell's normal makes the projected ring CCW in (u, v), which is what triangulate wants.
    return [tuple(int(i) for i in tri) for tri in m3d.triangulate([flat])]


def _newell(ring: Sequence[Vec3]) -> Vec3:
    x = y = z = 0.0
    for i, (ax, ay, az) in enumerate(ring):
        bx, by, bz = ring[(i + 1) % len(ring)]
        x += (ay - by) * (az + bz)
        y += (az - bz) * (ax + bx)
        z += (ax - bx) * (ay + by)
    return (x, y, z)


def _cross(a, b) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(a) -> Vec3:
    length = math.sqrt(_dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length)
