"""Plan-frame geometry primitives shared by every consumer of the derived-geometry IR.

These are the pure shape helpers the glTF emitter grew — ring cleanup, wall-layer edge
extraction, fractional slicing, arch-soffit sampling. None of them is glTF-specific (the one
that was, ``_to_gltf``'s axis swizzle, stays in the emitter), and the IR producer in
``resolve/`` needs exactly the same math, so they live here rather than under ``emit/``:
``resolve`` importing from ``emit`` would invert the layering.

Stdlib only — the Pyodide constraint that lets the in-browser engine emit its own GLB.
"""

from __future__ import annotations

import math

Vec3 = tuple[float, float, float]

def _dedupe_ring(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for pt in ring:
        if not out or (abs(pt[0] - out[-1][0]) > 1e-9 or abs(pt[1] - out[-1][1]) > 1e-9):
            out.append(pt)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def _ring_signed_area(ring: list[tuple[float, float]]) -> float:
    """Shoelace area of a plan ring; positive is counter-clockwise (planGeometry.ts)."""
    total = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return total / 2.0


# A soffit facet may deviate from the true circle by at most this. The segment count then falls
# out of the arch's radius, so an 8'-wide garden arch and a small niche head are equally smooth.
_ARCH_SOFFIT_CHORD_TOLERANCE_M = 0.0005
_ARCH_SOFFIT_MIN_SEGMENTS = 24
_ARCH_SOFFIT_MAX_SEGMENTS = 192
# A vertex this far off the chord between its neighbours is a real corner; closer is padding.
_COLLINEAR_VERTEX_TOLERANCE_M = 1e-6


def arch_soffit_circle(half_span_m: float, rise_m: float) -> tuple[float, float, float]:
    """``(radius, half_angle, springline_depth)`` of the circle through both springlines and
    the crown of an arch of half-span ``half_span_m`` rising ``rise_m`` above them.

    This is what makes a *segmental* arch possible. The soffit used to be hard-wired to a
    half-circle of ``width / 2``, so ``Arch.rise`` only chose where the springline sat and
    every head came out semicircular however shallow the rise said it was — a 2" rise on a
    14" opening still drew a 7" half-round. Solving the circle from both numbers instead
    makes the crown land exactly on the authored head.

    ``springline_depth`` is how far the circle's centre sits *below* the springline
    (``radius - rise``); a semicircle has none, which is why nothing needed it before.
    A rise at or above the half-span is the semicircle, and is clamped to it — a "rise"
    taller than that is a horseshoe arch, which no wall here can build.
    """
    span = max(half_span_m, 1e-9)
    rise = min(max(rise_m, 1e-9), span)
    radius = (span * span + rise * rise) / (2.0 * rise)
    half_angle = math.asin(max(-1.0, min(1.0, span / radius)))
    return radius, half_angle, radius - rise


def _arch_soffit_segment_count(radius_m: float,
                               half_angle_rad: float = math.pi / 2.0) -> int:
    """Segments for a soffit arc sampled at even angular steps. One step's mid-chord sagitta
    is ``r * (1 - cos(theta / 2n))``, so inverting it ties tessellation to the arch's actual
    size instead of a flat guess. ``half_angle_rad`` defaults to the half-circle this used to
    assume. Mirrors ``archSoffitSegmentCount`` in ui/src/three/builders/walls.ts."""
    if radius_m <= _ARCH_SOFFIT_CHORD_TOLERANCE_M:
        return _ARCH_SOFFIT_MIN_SEGMENTS
    half_step = math.acos(max(-1.0, 1.0 - _ARCH_SOFFIT_CHORD_TOLERANCE_M / radius_m))
    count = math.ceil(half_angle_rad / half_step)
    return max(_ARCH_SOFFIT_MIN_SEGMENTS, min(_ARCH_SOFFIT_MAX_SEGMENTS, count))


def _arch_soffit_sample(segment: int, segment_count: int, radius_m: float,
                        half_angle_rad: float = math.pi / 2.0) -> tuple[float, float]:
    """(offset from the arch centreline, height above the springline) at one angular step.

    The arc is walked by *angle*: stepping evenly in x collapses near the springlines, where a
    semicircle turns vertical, so the outermost step alone spanned ~40 cm of rise on the catlin
    arches — the "striping". Mirrors ``archSoffitSample`` in ui/src/three/builders/walls.ts.

    Sweeping ``-half_angle .. +half_angle`` and subtracting the circle's depth below the
    springline generalises this to a segmental arch; at the default ``pi/2`` the depth is zero
    and this is the same half-circle it always was, merely parameterised from the centre out.
    """
    angle = -half_angle_rad + 2.0 * half_angle_rad * segment / segment_count
    depth = radius_m * math.cos(half_angle_rad)
    return radius_m * math.sin(angle), radius_m * math.cos(angle) - depth


def _without_collinear_vertices(ring, tolerance_m: float = _COLLINEAR_VERTEX_TOLERANCE_M):
    """Drop vertices that sit on the straight line between their neighbours.

    Junction resolution splits a wall layer's long edges at every crossing wall, so an authored
    rectangle serializes as five, six or eight points (77 of catlin's 607 layers). Anything that
    needs to *recognise* a rectangle has to reduce first. Mirrors ``withoutCollinearVertices``
    in ui/src/components/Panel3D.tsx — keep the two in step.

    A fully collinear (degenerate) ring reduces to nothing; callers decide what that means.
    """
    deduped = _dedupe_ring(list(ring))
    if len(deduped) < 3:
        return deduped
    corners = []
    count = len(deduped)
    for index in range(count):
        (px, py) = deduped[index - 1]
        (cx, cy) = deduped[index]
        (qx, qy) = deduped[(index + 1) % count]
        span_x, span_y = qx - px, qy - py
        span = math.hypot(span_x, span_y)
        # Perpendicular distance, in metres, of this vertex from the chord between its neighbours.
        offset = (math.hypot(cx - px, cy - py) if span < tolerance_m
                  else abs((cx - px) * span_y - (cy - py) * span_x) / span)
        if offset > tolerance_m:
            corners.append((cx, cy))
    return corners


def _thin_rect_edges(poly, axis):
    """The two long edges of a wall layer's thin-rectangle footprint, each oriented
    start→end along the wall axis, so a fractional slice maps to along-axis position.

    The ring is reduced to real corners first, then the edges are read off *their* wall-local
    bounding rectangle. Sorting the raw ring instead picked two vertices off the same face of a
    collinear-padded ring, which exported the 16" sunken-garden arch wall as an 8" one — 182 of
    catlin's 607 layers reached the .glb at the wrong thickness that way.
    """
    (p0x, p0y), (p1x, p1y) = axis
    tx, ty = p1x - p0x, p1y - p0y
    length = math.hypot(tx, ty) or 1.0
    tx, ty = tx / length, ty / length
    nx, ny = -ty, tx
    # A fully collinear (degenerate) ring reduces to nothing; its raw extent is all there is.
    corners = _without_collinear_vertices(poly) or list(poly)
    alongs = [(v[0] - p0x) * tx + (v[1] - p0y) * ty for v in corners]
    perps = [(v[0] - p0x) * nx + (v[1] - p0y) * ny for v in corners]
    min_along, max_along = min(alongs), max(alongs)
    min_perp, max_perp = min(perps), max(perps)

    def at(along: float, perp: float) -> tuple[float, float]:
        return (p0x + tx * along + nx * perp, p0y + ty * along + ny * perp)

    return ((at(min_along, min_perp), at(max_along, min_perp)),
            (at(min_along, max_perp), at(max_along, max_perp)))


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _slice(edges, t0, t1):
    (a0, a1), (b0, b1) = edges
    return [_lerp(a0, a1, t0), _lerp(a0, a1, t1), _lerp(b0, b1, t1), _lerp(b0, b1, t0)]
