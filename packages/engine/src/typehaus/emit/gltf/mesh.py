"""Triangle accumulation for one source object: prisms, boxes and arched spandrels, bucketed
by colour so each object becomes one mesh of a few primitives."""

from __future__ import annotations

import math

from typehaus.emit.gltf.geometry import (
    Vec3,
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    _dedupe_ring,
    _lerp,
    _ring_signed_area,
    _to_gltf,
)


class _TriangleIndices(list):
    """A bucket's triangle index list, plus the analytic per-corner normals that a few faces
    want instead of the geometric one.

    Keyed by triangle ordinal (``index position // 3``). Only curved surfaces register — today
    just the arch soffit, whose facets lie on a true cylinder — so ``_deindex_with_normals`` can
    shade them as one curve while every other face keeps its crisp geometric normal. Carried on
    the list itself so a bucket still travels as one thing through the scene assembler.
    """

    __slots__ = ("smooth_face_normals",)

    def __init__(self) -> None:
        super().__init__()
        self.smooth_face_normals: dict[int, tuple[Vec3, Vec3, Vec3]] = {}


class _MeshBuilder:
    """Accumulates triangles bucketed by color; emits interleaved position + index buffers."""

    def __init__(self) -> None:
        # color -> (positions: list[Vec3], indices: _TriangleIndices)
        self._buckets: dict[tuple[float, float, float, float],
                            tuple[list[Vec3], _TriangleIndices]] = {}

    def _bucket(self, color: tuple[float, float, float, float]):
        return self._buckets.setdefault(color, ([], _TriangleIndices()))

    def add_prism(self, ring: list[tuple[float, float]], z0: float, z1: float,
                  color: tuple[float, float, float, float]) -> None:
        """Extrude a plan polygon ring between z0 and z1 into a closed solid."""
        ring = _dedupe_ring(ring)
        if len(ring) < 3:
            return
        # The fixed side/cap winding below faces outward only for a counter-clockwise ring
        # (same convention as add_raked_prism); normalize so every prism's faces — and the
        # per-face normals derived from them — point outward, which single-sided import needs.
        if _ring_signed_area(ring) < 0:
            ring = list(reversed(ring))
        positions, indices = self._bucket(color)
        base = len(positions)
        n = len(ring)
        for (x, y) in ring:  # bottom loop then top loop
            positions.append(_to_gltf(x, y, z0))
        for (x, y) in ring:
            positions.append(_to_gltf(x, y, z1))
        # side walls
        for i in range(n):
            j = (i + 1) % n
            b0, b1, t0, t1 = base + i, base + j, base + n + i, base + n + j
            indices += [b0, b1, t1, b0, t1, t0]
        # caps via fan triangulation (rings are convex-ish quads in practice)
        for i in range(1, n - 1):
            indices += [base, base + i + 1, base + i]                 # bottom (down)
            indices += [base + n, base + n + i, base + n + i + 1]     # top (up)

    def add_raked_prism(self, ring: list[tuple[float, float]], z0: float,
                        top_at, color: tuple[float, float, float, float]) -> None:
        """Extrude a plan ring from a flat ``z0`` to a per-vertex raked top ``top_at(x, y)``.

        A direct port of ui/src/three/planGeometry.ts ``createRakedPlanPrismGeometry``: a wall
        under a sloped roof (gable end, ToRoof) must stop at its actual rake, or its full
        bounding-height box engulfs and z-fights the roof it carries. Nothing normalizes winding
        for the fixed triangle order below, so the ring is reoriented counter-clockwise first.
        """
        ring = _dedupe_ring(ring)
        if len(ring) < 3:
            return
        if _ring_signed_area(ring) < 0:  # only CCW rings give outward side + upward cap normals
            ring = list(reversed(ring))
        n = len(ring)

        def top(pt):
            return top_at(pt[0], pt[1])

        def g(pt, elev):
            return _to_gltf(pt[0], pt[1], elev)

        triangles: list[tuple[Vec3, Vec3, Vec3]] = []
        for i in range(n):  # side walls, base loop → per-vertex raked top
            j = (i + 1) % n
            triangles.append((g(ring[i], z0), g(ring[j], z0), g(ring[j], top(ring[j]))))
            triangles.append((g(ring[i], z0), g(ring[j], top(ring[j])), g(ring[i], top(ring[i]))))
        for i in range(1, n - 1):  # flat bottom cap (down) + raked top cap (up) via fans
            triangles.append((g(ring[0], z0), g(ring[i + 1], z0), g(ring[i], z0)))
            triangles.append((g(ring[0], top(ring[0])), g(ring[i], top(ring[i])),
                              g(ring[i + 1], top(ring[i + 1]))))
        self.add_triangles(triangles, color)

    def add_prism_with_rectangular_voids(self, ring: list[tuple[float, float]],
                                         voids: tuple[tuple[tuple[float, float], ...], ...],
                                         z0: float, z1: float,
                                         color: tuple[float, float, float, float]) -> None:
        """Emit a rectangular slab as strips around rectangular voids.

        The floor-opening framing contract currently accepts orthogonal rectangles, so
        this produces a true hole without introducing a second polygon triangulator.
        Irregular solids intentionally retain their outer prism until they gain a general
        mesh path.
        """
        xs, ys = {p[0] for p in ring}, {p[1] for p in ring}
        if len(xs) != 2 or len(ys) != 2 or len(voids) != 1:
            self.add_prism(ring, z0, z1, color)
            return
        hole = voids[0]
        hx, hy = {p[0] for p in hole}, {p[1] for p in hole}
        if len(hx) != 2 or len(hy) != 2:
            self.add_prism(ring, z0, z1, color)
            return
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        hminx, hmaxx, hminy, hmaxy = min(hx), max(hx), min(hy), max(hy)
        for rect in (
            [(minx, miny), (maxx, miny), (maxx, hminy), (minx, hminy)],
            [(minx, hmaxy), (maxx, hmaxy), (maxx, maxy), (minx, maxy)],
            [(minx, hminy), (hminx, hminy), (hminx, hmaxy), (minx, hmaxy)],
            [(hmaxx, hminy), (maxx, hminy), (maxx, hmaxy), (hmaxx, hmaxy)],
        ):
            self.add_prism(rect, z0, z1, color)

    def add_box(self, p0: Vec3, p1: Vec3, size: float,
                color: tuple[float, float, float, float]) -> None:
        """A member segment as a box of half-width ``size`` around the p0→p1 axis (xy)."""
        (ax, ay, az), (bx, by, bz) = p0, p1
        dx, dy = bx - ax, by - ay
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return
        nx, ny = -dy / length * size, dx / length * size
        ring = [(ax + nx, ay + ny), (bx + nx, by + ny),
                (bx - nx, by - ny), (ax - nx, ay - ny)]
        self.add_prism(ring, az, bz, color)

    def add_member_box(self, p0: Vec3, p1: Vec3, half_width: float,
                       color: tuple[float, float, float, float],
                       z0_end: float | None = None, z1_end: float | None = None) -> None:
        """Add a real 3D member, including vertical studs and sloped top plates."""
        ax, ay, az0 = p0
        bx, by, az1 = p1
        lower_end = az0 if z0_end is None else z0_end
        upper_end = az1 if z1_end is None else z1_end
        dx, dy = bx - ax, by - ay
        run = (dx * dx + dy * dy) ** 0.5
        if run < 1e-9:
            ring = [(ax - half_width, ay - half_width), (ax + half_width, ay - half_width),
                    (ax + half_width, ay + half_width), (ax - half_width, ay + half_width)]
            self.add_prism(ring, az0, az1, color)
            return
        nx, ny = -dy / run * half_width, dx / run * half_width
        plan_vertices = [
            (ax + nx, ay + ny, az0), (bx + nx, by + ny, lower_end),
            (bx - nx, by - ny, lower_end), (ax - nx, ay - ny, az0),
            (ax + nx, ay + ny, az1), (bx + nx, by + ny, upper_end),
            (bx - nx, by - ny, upper_end), (ax - nx, ay - ny, az1),
        ]
        positions, indices = self._bucket(color)
        base = len(positions)
        positions.extend(_to_gltf(*point) for point in plan_vertices)
        for face in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                     (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            a, b, c, d = (base + index for index in face)
            indices.extend((a, b, c, a, c, d))

    def add_triangles(self, triangles: list[tuple[Vec3, Vec3, Vec3]],
                      color: tuple[float, float, float, float]) -> None:
        positions, indices = self._bucket(color)
        for triangle in triangles:
            base = len(positions)
            positions.extend(triangle)
            indices.extend((base, base + 1, base + 2))

    def add_arched_spandrel(self, edges, opening_start: float, opening_end: float,
                            z1: float, springline: float, radius: float,
                            color: tuple[float, float, float, float]) -> None:
        """Add one continuous curved concrete head, not a stack of prism strips.

        The soffit is a cylinder about a horizontal axis through the springlines, so each of its
        facets registers the analytic surface normal (:class:`_TriangleIndices`). Without that,
        an importer shades it as ``_arch_soffit_segment_count`` flat strips however finely it is
        tessellated. Every other face — flat top, wall-depth sides, jambs — keeps its crisp
        geometric normal.
        """
        positions, indices = self._bucket(color)
        segment_count = _arch_soffit_segment_count(radius)
        base = len(positions)
        # The soffit normal rotates in the vertical plane containing the wall axis.
        (edge_start, edge_end) = edges[0]
        run = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]) or 1.0
        ux, uy = (edge_end[0] - edge_start[0]) / run, (edge_end[1] - edge_start[1]) / run
        soffit_normals: list[Vec3 | None] = []
        for segment in range(segment_count + 1):
            offset, height = _arch_soffit_sample(segment, segment_count, radius)
            fraction = opening_start + (opening_end - opening_start) * (
                (offset + radius) / (2.0 * radius))
            crown = springline + height
            soffit = min(z1, crown)
            front = _lerp(edges[0][0], edges[0][1], fraction)
            back = _lerp(edges[1][0], edges[1][1], fraction)
            positions.extend((_to_gltf(*front, soffit), _to_gltf(*back, soffit),
                              _to_gltf(*front, z1), _to_gltf(*back, z1)))
            # A sample clipped by the wall top no longer sits on the circle, so it earns no
            # analytic normal and its facets fall back to the geometric one.
            soffit_normals.append(None if soffit < crown - 1e-9 else _to_gltf(
                offset / radius * ux, offset / radius * uy, height / radius))
        for segment in range(segment_count):
            current, next_ = base + segment * 4, base + (segment + 1) * 4
            here, there = soffit_normals[segment], soffit_normals[segment + 1]
            # Curved soffit — two triangles carrying the cylinder's own normals.
            for corners in ((current, next_ + 1, next_), (current, current + 1, next_ + 1)):
                ordinal = len(indices) // 3
                indices.extend(corners)
                if here is not None and there is not None:
                    indices.smooth_face_normals[ordinal] = tuple(
                        here if corner in (current, current + 1) else there
                        for corner in corners)
            # Flat top.
            indices.extend((current + 2, next_ + 2, next_ + 3,
                            current + 2, next_ + 3, current + 3))
            # The two wall-depth faces are continuous across the full arch.
            indices.extend((current, next_, next_ + 2, current, next_ + 2, current + 2,
                            current + 1, current + 3, next_ + 3, current + 1, next_ + 3, next_ + 1))
        # Close the jamb faces at each springline.
        for section in (base, base + segment_count * 4):
            indices.extend((section, section + 2, section + 3, section, section + 3, section + 1))

    def is_empty(self) -> bool:
        return not any(pos for pos, _ in self._buckets.values())

    def buckets(self):
        """Non-empty (color, positions, indices) tuples for the scene assembler."""
        for color, (positions, indices) in self._buckets.items():
            if positions:
                yield color, positions, indices
