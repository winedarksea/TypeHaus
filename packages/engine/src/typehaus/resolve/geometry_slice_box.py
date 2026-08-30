"""Cutting a hexahedron — the upright test, the convexity test, and the hull cut.

Split out of :mod:`typehaus.resolve.geometry_slice` (AGENTS.md's 500-line rule) along the
line the sweep kernel drew through it: a ``GBox`` used to mean one thing, an extruded plan
footprint, and now means two, because a swept run's leg is a box whose rings are separated
along an arbitrary 3D axis (→ :mod:`typehaus.resolve.sweep`). Telling those apart, and
cutting the second kind, is a subject of its own.

``geometry_slice._box_profiles`` is the caller and stays there, because *choosing* between
the fast path and this one is the dispatch, not the geometry.
"""

from __future__ import annotations

from collections.abc import Iterable

from typehaus.resolve.geometry_ir import GBox, GMesh
from typehaus.resolve.geometry_slice_plane import CutPlane, SectionProfile, Vec2UZ

#: A ``GBox`` whose two rings differ only in Z is *upright*: its bottom ring is a plan
#: footprint and its top ring is that footprint at other elevations. Every member, panel and
#: closure band is one — which is what :func:`_box_profiles`'s fast path assumes.
_UPRIGHT_TOLERANCE_M = 1e-9


def _box_is_upright(solid: GBox) -> bool:
    return all(abs(top[0] - bottom[0]) <= _UPRIGHT_TOLERANCE_M
               and abs(top[1] - bottom[1]) <= _UPRIGHT_TOLERANCE_M
               # strict=True: a GBox's two rings are the same footprint at two elevations,
               # so they carry the same corner count — `_box_mesh` indexes on that too.
               for bottom, top in zip(solid.corners_bottom, solid.corners_top, strict=True))


def _box_mesh(solid: GBox) -> GMesh:
    """The hexahedron as a closed triangle mesh — caps fanned, one quad per ring edge.

    The same triangulation ``emit/gltf/mesh.py::add_gbox`` writes, so a section and a render
    of the same box are the same solid.
    """
    count = len(solid.corners_bottom)
    positions = tuple(solid.corners_bottom) + tuple(solid.corners_top)
    triangles: list[tuple[int, int, int]] = []
    for index in range(1, count - 1):
        triangles.append((0, index + 1, index))
        triangles.append((count, count + index, count + index + 1))
    for index in range(count):
        nxt = (index + 1) % count
        triangles.append((index, nxt, count + nxt))
        triangles.append((index, count + nxt, count + index))
    return GMesh(positions=positions, triangles=tuple(triangles))


#: How far off a face a crossing may sit and still count as *on* it. A hair above
#: :data:`WELD_M`, because the hull below inherits that tolerance from the rest of the file.
_ON_PLANE_M = 1e-9


def _box_is_convex(solid: GBox) -> bool:
    """Does the bottom ring turn the same way the whole way round?

    The hull cut below is only the section of a *convex* box. Every box the sweep kernel
    builds is one — a convex profile swept along a straight axis and capped by two planes is
    an intersection of convex sets — and both profiles it offers (a faceted circle, a
    rectangle) are convex. This is the guard that says so out loud, so a future non-convex
    section falls back to the mesh path rather than being silently drawn as its hull.
    """
    ring = solid.corners_bottom
    count = len(ring)
    if count < 3:
        return False
    # The ring is planar, so every corner's turn vector is parallel to the same normal;
    # convex means none of them points the other way along it.
    reference: tuple[float, float, float] | None = None
    for index in range(count):
        a, b, c = ring[index], ring[(index + 1) % count], ring[(index + 2) % count]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
        turn = (u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0])
        if max(abs(component) for component in turn) <= _ON_PLANE_M:
            continue  # collinear here; this corner says nothing either way
        if reference is None:
            reference = turn
            continue
        # strict=True: both are 3-vectors built right here.
        if sum(x * y for x, y in zip(reference, turn, strict=True)) < 0.0:
            return False
    return reference is not None


def _hull(points: list[Vec2UZ]) -> tuple[Vec2UZ, ...]:
    """Andrew's monotone chain, counter-clockwise, collinear points dropped."""
    ordered = sorted(set(points))
    if len(ordered) < 3:
        return ()
    def half(sequence: Iterable[Vec2UZ]) -> list[Vec2UZ]:
        out: list[Vec2UZ] = []
        for point in sequence:
            while len(out) >= 2:
                (x0, y0), (x1, y1) = out[-2], out[-1]
                if ((x1 - x0) * (point[1] - y0) - (y1 - y0) * (point[0] - x0)) > _ON_PLANE_M:
                    break
                out.pop()
            out.append(point)
        return out
    lower, upper = half(ordered), half(reversed(ordered))
    ring = tuple(lower[:-1] + upper[:-1])
    return ring if len(ring) >= 3 else ()


def _box_hull_profile(solid: GBox, plane: CutPlane) -> list[SectionProfile]:
    """A convex box's cut face: the hull of where ``plane`` crosses its edges.

    Every other path in this file walks faces and welds the segments they yield into a ring,
    which is the general answer and is fragile exactly where a tube needs it not to be. A cut
    that grazes a vertex leaves two sub-:data:`WELD_M` slivers, both are dropped as
    degenerate, and the ring falls open — and a 12-gon has two vertex rows *on its own axis
    plane*, so a section down the centreline of a drain stack is precisely the cut that
    breaks. Taking the hull of the crossings instead needs no welding and no chaining: the
    section of a convex solid is a convex polygon, so its vertices are its crossings and
    their order is not something to be recovered. A grazing cut degenerates into the cap ring
    itself, which is the right drawing rather than nothing at all.
    """
    bottom, top = solid.corners_bottom, solid.corners_top
    count = len(bottom)
    edges = [(bottom[i], bottom[(i + 1) % count]) for i in range(count)]
    edges += [(top[i], top[(i + 1) % count]) for i in range(count)]
    edges += [(bottom[i], top[i]) for i in range(count)]
    station = plane.station_m
    points: list[Vec2UZ] = []
    for p0, p1 in edges:
        a0, a1 = plane.perp_of(p0), plane.perp_of(p1)
        if abs(a1 - a0) <= _ON_PLANE_M:
            # The edge lies in the plane: both of its ends are on the cut face.
            if abs(a0 - station) <= _ON_PLANE_M:
                points.append((plane.u_of(p0), p0[2]))
                points.append((plane.u_of(p1), p1[2]))
            continue
        f = (station - a0) / (a1 - a0)
        if not -_ON_PLANE_M <= f <= 1.0 + _ON_PLANE_M:
            continue
        points.append((plane.u_of(p0) + f * (plane.u_of(p1) - plane.u_of(p0)),
                       p0[2] + f * (p1[2] - p0[2])))
    ring = _hull(points)
    return [SectionProfile(outline=ring)] if ring else []


