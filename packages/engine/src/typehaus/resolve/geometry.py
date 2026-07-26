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


def offset_segment(p0: Vec, p1: Vec, offset: float) -> tuple[Vec, Vec]:
    """Offset a segment perpendicular by ``offset`` (positive = left of direction)."""
    d = unit(sub(p1, p0))
    n = scale(normal(d), offset)
    return (add(p0, n), add(p1, n))


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
    cope with, so those legs are skipped rather than emitted degenerate.
    """
    half = LIGHT_STRIP_WIDTH_M / 2.0
    profiles: list[list[Vec]] = []
    for index in range(len(path) - 1):
        p0, p1 = path[index], path[index + 1]
        if length(sub(p1, p0)) < 1e-6:
            continue
        profiles.append(rect_between(p0, p1, -half, half))
    return profiles
