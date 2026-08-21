"""Crop-window clipping and band primitives for the section cut (→ 30 §Details).

Split out of ``section.py`` unchanged: a detail's crop is a rectangle in section
coordinates (u, z) and every cut band has to be trimmed to it before it becomes IR. The
three clippers here are the standard trio — axis-aligned band, Liang–Barsky segment,
Sutherland–Hodgman polygon — and ``_rect_nodes``/``_quad_nodes`` are the metres → inches
conversion plus the outline/hatch pair that every family emits.

Coordinates in, metres; coordinates out, metres — only the node builders convert to the
IR's inches.
"""

from __future__ import annotations

from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.quantities import M_PER_IN


def clip_rect(u0, u1, z0, z1, crop) -> tuple[float, float, float, float] | None:
    if crop is None:
        return (u0, u1, z0, z1)
    (cu0, cz0), (cu1, cz1) = crop
    u0, u1 = max(u0, min(cu0, cu1)), min(u1, max(cu0, cu1))
    z0, z1 = max(z0, min(cz0, cz1)), min(z1, max(cz0, cz1))
    if u0 >= u1 or z0 >= z1:
        return None
    return (u0, u1, z0, z1)


def clip_segment(p0, p1, crop):
    """Liang–Barsky clip of a (u, z) segment to the crop rectangle, or None if outside."""
    if crop is None:
        return (p0, p1)
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    z_lo, z_hi = min(cz0, cz1), max(cz0, cz1)
    du, dz = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-du, p0[0] - u_lo), (du, u_hi - p0[0]),
                 (-dz, p0[1] - z_lo), (dz, z_hi - p0[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    if t0 > t1:
        return None
    return ((p0[0] + t0 * du, p0[1] + t0 * dz),
            (p0[0] + t1 * du, p0[1] + t1 * dz))


def clip_polygon(points, crop):
    """Sutherland–Hodgman clip of a (u, z) polygon to the crop rectangle.

    ``clip_rect`` only handles axis-aligned bands; a sloped roof band needs a real
    polygon clip or it runs straight off the detail's crop window.
    """
    if crop is None:
        return list(points)
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    z_lo, z_hi = min(cz0, cz1), max(cz0, cz1)

    def clip(poly, inside, intersect):
        out = []
        for index, current in enumerate(poly):
            previous = poly[index - 1]
            cur_in, prev_in = inside(current), inside(previous)
            if cur_in:
                if not prev_in:
                    out.append(intersect(previous, current))
                out.append(current)
            elif prev_in:
                out.append(intersect(previous, current))
        return out

    def cut(poly, axis, bound, keep_greater):
        def inside(p):
            return p[axis] >= bound if keep_greater else p[axis] <= bound

        def intersect(a, b):
            span = b[axis] - a[axis]
            t = 0.0 if abs(span) < 1e-12 else (bound - a[axis]) / span
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

        return clip(poly, inside, intersect)

    poly = list(points)
    for axis, bound, keep_greater in (
        (0, u_lo, True), (0, u_hi, False), (1, z_lo, True), (1, z_hi, False),
    ):
        if not poly:
            return []
        poly = cut(poly, axis, bound, keep_greater)
    return poly


def rect_nodes(u0, u1, z0, z1, layer, pattern, uid, tag, outline: bool = True,
               material: str | None = None) -> list:
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1), (u0, z1)))
    nodes: list = []
    if outline:
        nodes.append(Polyline(points=pts, layer=layer, closed=True,
                              lineweight=0.35 if layer == "A-WALL" else 0.18,
                              uid=uid, tag=tag))
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                           material=material))
    return nodes


def quad_nodes(u0, u1, z0, z1_left, z1_right, layer, pattern, uid, tag,
               material: str | None = None) -> list:
    """Like ``rect_nodes`` but with a sloped top: left/right top elevations differ.

    Sibling of ``rect_nodes`` for per-layer sloped terminations (Revit layer extension
    distances against a raked interface plane) — threads through detail cuts only.
    """
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1_right), (u0, z1_left)))
    nodes: list = [Polyline(points=pts, layer=layer, closed=True,
                            lineweight=0.35 if layer == "A-WALL" else 0.18,
                            uid=uid, tag=tag)]
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                           material=material))
    return nodes
