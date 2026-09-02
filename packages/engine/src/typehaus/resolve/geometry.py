"""Low-level 2D geometry helpers for the resolver (meters, project-north frame)."""

from __future__ import annotations

import math

Vec = tuple[float, float]


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])


def scale(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k)


def length(a: Vec) -> float:
    return math.hypot(a[0], a[1])


def unit(a: Vec) -> Vec:
    n = length(a)
    if n < 1e-12:
        return (0.0, 0.0)
    return (a[0] / n, a[1] / n)


def normal(direction: Vec) -> Vec:
    """Left-hand normal of a unit direction (90° CCW)."""
    return (-direction[1], direction[0])


def wall_frame(wall) -> tuple[Vec, Vec, Vec, float]:  # noqa: ANN001 — avoids an import cycle
    """``(origin, tangent, normal, axis_length)`` for a wall's axis.

    The one answer for every caller: a degenerate (zero-length) axis returns a zero
    tangent/normal and ``axis_length == 0.0``, so check ``axis_length`` rather than trust
    the direction vectors when it is near zero.
    """
    origin, end = wall.axis
    tangent_vec = sub(end, origin)
    axis_length = length(tangent_vec)
    if axis_length <= 1e-9:
        return origin, (0.0, 0.0), (0.0, 0.0), 0.0
    tangent = unit(tangent_vec)
    return origin, tangent, normal(tangent), axis_length


def opening_center(wall, opening) -> Vec | None:  # noqa: ANN001 — avoids an import cycle
    """The point on ``wall``'s axis at ``opening.center_along_m``, or ``None`` if the wall's
    axis is degenerate (→ ``wall_frame``)."""
    origin, tangent, _normal, axis_length = wall_frame(wall)
    if axis_length <= 1e-9:
        return None
    return add(origin, scale(tangent, opening.center_along_m))


def bbox(points: list[Vec]) -> tuple[Vec, Vec]:
    """``(min, max)`` corners of the axis-aligned bounding box of ``points``."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys)), (max(xs), max(ys))


def project_onto_axis(point: Vec, origin: Vec, direction: Vec) -> float:
    """Signed distance along ``direction`` (assumed unit) from ``origin`` to ``point``'s
    projection — i.e. the scalar ``t`` such that ``origin + t * direction`` is the foot of
    the perpendicular from ``point``."""
    d = sub(point, origin)
    return d[0] * direction[0] + d[1] * direction[1]


def rect_between(p0: Vec, p1: Vec, left: float, right: float,
                 extend0: float = 0.0, extend1: float = 0.0) -> list[Vec]:
    """A rectangle band around the p0→p1 axis, from ``left`` to ``right`` offsets.

    ``extend0``/``extend1`` push the band past each end along the axis — used to close
    orthogonal miter corners by extending each wall by the neighbor's half-thickness.
    """
    d = unit(sub(p1, p0))
    a = add(p0, scale(d, -extend0))
    b = add(p1, scale(d, extend1))
    n = normal(d)
    return [
        add(a, scale(n, left)),
        add(b, scale(n, left)),
        add(b, scale(n, right)),
        add(a, scale(n, right)),
    ]


def clip_half_plane(ring: list[Vec], origin: Vec, direction: Vec) -> list[Vec]:
    """The part of ``ring`` on the ``direction`` side of the line through ``origin``.

    Sutherland-Hodgman against a single half-plane, which is all any caller here needs: a
    band already mitred into its neighbours has to give up its inner inches to a cavity
    fill, and the answer is the same polygon with one edge moved. Returns ``[]`` when the
    ring is entirely on the far side.
    """
    if not ring:
        return []
    def side(point: Vec) -> float:
        return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]

    out: list[Vec] = []
    for index, current in enumerate(ring):
        previous = ring[index - 1]
        d_current, d_previous = side(current), side(previous)
        if (d_previous < 0.0) != (d_current < 0.0):
            t = d_previous / (d_previous - d_current)
            out.append((previous[0] + (current[0] - previous[0]) * t,
                        previous[1] + (current[1] - previous[1]) * t))
        if d_current >= 0.0:
            out.append(current)
    return out


def square(cx: float, cy: float, half_x: float, half_y: float) -> list[Vec]:
    """Axis-aligned plan rectangle about ``(cx, cy)``.

    Square to the *project* axes, not to any run — a member on a diagonal wants
    :func:`rect_between` instead, or it comes out a lozenge.
    """
    return [(cx - half_x, cy - half_y), (cx + half_x, cy - half_y),
            (cx + half_x, cy + half_y), (cx - half_x, cy + half_y)]


def bar(cx: float, cy: float, axis: str, run_m: float, dia_m: float) -> list[Vec]:
    """Plan footprint of a horizontal bar of diameter ``dia_m`` running ``run_m`` along axis."""
    if axis == "x":
        return square(cx, cy, run_m / 2.0, dia_m / 2.0)
    return square(cx, cy, dia_m / 2.0, run_m / 2.0)


def nominal_actual_m(size: str) -> float:
    """Actual cross-section (m) from a nominal like "2x2" (2" nominal → 1.5" actual).

    Dressed-lumber arithmetic, and *only* that: an extruded aluminium section states its
    true dimension, so a product fact (``RailingType.baluster_width``) is a ``Length`` and
    never goes through here.
    """
    try:
        nominal = float(size.lower().split("x")[0])
    except (ValueError, IndexError):
        nominal = 2.0
    return max(nominal - 0.5, 0.75) * 0.0254


def circle_outline(center: Vec, radius: float, facets: int) -> list[Vec]:
    """A regular ``facets``-gon approximating a circle of ``radius`` about ``center``.

    Round sections (sonotube columns, vent pipes) have no first-class representation in
    the prism-only solid IR, so every consumer renders them as this faceted plan outline
    extruded vertically. One helper keeps the facet geometry identical across resolvers.
    """
    return [(center[0] + radius * math.cos(2 * math.pi * index / facets),
             center[1] + radius * math.sin(2 * math.pi * index / facets))
            for index in range(facets)]


def polygon_area(ring: list[Vec]) -> float:
    """Signed area via the shoelace formula (positive = CCW)."""
    s = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s / 2.0


# --- linear luminaire (LightRun) cross-section ---------------------------------
# An LED tape in its aluminium channel. Half an inch square is the common extrusion, and
# it is the only cross-section a strip has — the run's *length* is the authored fact.
# Shared rather than duplicated: the IFC emitter sweeps this profile and the diff adapter
# projects the same swept extent, so a round trip against our own export matches instead of
# reporting every run as resized by the channel's own width (→ diff/ifc_adapter).
LIGHT_STRIP_WIDTH_M = 0.0127
LIGHT_STRIP_HEIGHT_M = 0.0127


def light_run_segment_profiles(path: list[Vec]) -> list[list[Vec]]:
    """The swept rectangle of every non-degenerate leg of a linear-luminaire run.

    A coincident authored pair is a typo, not a zero-width solid an IFC importer has to
    cope with, so those legs are skipped rather than emitted degenerate. This is the run's
    outer envelope — the diff adapter projects this same extent (→ diff/ifc_adapter), so it
    stays a plain half-inch-square sweep even though :func:`light_run_band_profiles` below
    now draws a channel, not a bar, inside that same envelope.
    """
    half = LIGHT_STRIP_WIDTH_M / 2.0
    profiles: list[list[Vec]] = []
    for index in range(len(path) - 1):
        p0, p1 = path[index], path[index + 1]
        if length(sub(p1, p0)) < 1e-6:
            continue
        profiles.append(rect_between(p0, p1, -half, half))
    return profiles


def light_run_band_profiles(
    path: list[Vec], width_m: float = LIGHT_STRIP_WIDTH_M, depth_m: float = LIGHT_STRIP_HEIGHT_M,
) -> list[tuple[str, list[list[Vec]], float, float]]:
    """The channel+tape cross-section of a linear-luminaire run, swept along every leg.

    One entry per band from :func:`~typehaus.resolve.trim_bands.led_cove_bands`: its key, the
    per-leg swept rectangles (same shape as :func:`light_run_segment_profiles`, one per
    non-degenerate leg), and the band's ``(bottom_drop, top_drop)`` below the run's mounted
    height — a caller turns each into a prism between ``z_m - bottom_drop`` and
    ``z_m - top_drop``. Every band's plan span sits inside the same ``[-width_m/2, width_m/2]``
    envelope :func:`light_run_segment_profiles` sweeps, so the two stay geometrically nested
    rather than drifting into different-sized runs on the same house.
    """
    from typehaus.resolve.trim_bands import led_cove_bands

    half = width_m / 2.0
    out: list[tuple[str, list[list[Vec]], float, float]] = []
    for key, offset, band_t, bottom_drop, top_drop in led_cove_bands(width_m, depth_m):
        left, right = -half + offset, -half + offset + band_t
        profiles: list[list[Vec]] = []
        for index in range(len(path) - 1):
            p0, p1 = path[index], path[index + 1]
            if length(sub(p1, p0)) < 1e-6:
                continue
            profiles.append(rect_between(p0, p1, left, right))
        out.append((key, profiles, bottom_drop, top_drop))
    return out
