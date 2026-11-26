"""Shower door plan geometry in a fixture's local frame, shared by the glyph, the resolver
(``resolve/shower_enclosures.py``) and the BATH2 symbol, so a swept leaf has one definition.

Pure floats. A leaf hinges at ``hinge`` and starts closed along ``closed_dir``; it opens
toward ``out_normal`` (out of the compartment).
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import Point

Edge = tuple[Point, Point, Point]  # p0, p1, outward unit normal

_AXIS_NORMALS = {"-y": (0.0, -1.0), "+y": (0.0, 1.0), "-x": (-1.0, 0.0), "+x": (1.0, 0.0)}
SWEEP_SEGMENTS = 36


def ring_edges(ring: tuple[Point, ...]) -> list[Edge]:
    """Edges of ``ring`` (consecutive duplicates dropped) with outward normals."""
    pts = [p for i, p in enumerate(ring) if p != ring[i - 1]]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1], strict=True))
    sign = 1.0 if area > 0 else -1.0  # CCW: the outside is to the right of travel
    edges = []
    for a, b in zip(pts, pts[1:] + pts[:1], strict=True):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length > 1e-9:
            edges.append((a, b, (sign * dy / length, -sign * dx / length)))
    return edges


def entry_edge(ring: tuple[Point, ...], name: str) -> Edge | None:
    """The longest ring edge facing ``name`` (``diagonal``: the one facing no axis)."""
    def facing(edge: Edge) -> bool:
        nx, ny = edge[2]
        if name == "diagonal":
            return abs(nx) > 0.2 and abs(ny) > 0.2
        return nx * _AXIS_NORMALS[name][0] + ny * _AXIS_NORMALS[name][1] > 0.99

    found = [edge for edge in ring_edges(ring) if facing(edge)]
    return max(found, key=lambda e: math.dist(e[0], e[1])) if found else None


def hinge_frame(edge: Edge, hinge: str, hinge_inset: float = 0.0,
                plane_inset: float = 0.0) -> tuple[Point, Point]:
    """``(hinge point, closed direction)``; ``hinge`` is left/right seen from outside."""
    (ax, ay), (bx, by), (nx, ny) = edge
    left = (ny, -nx)  # facing in (-normal), left is the normal rotated +90 degrees of that
    near_a = (ax - bx) * left[0] + (ay - by) * left[1] > 0
    start, end = ((ax, ay), (bx, by)) if near_a == (hinge == "left") else ((bx, by), (ax, ay))
    length = math.dist(start, end)
    closed = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    return ((start[0] + closed[0] * hinge_inset - nx * plane_inset,
             start[1] + closed[1] * hinge_inset - ny * plane_inset), closed)


def leaf_sector(hinge: Point, closed_dir: Point, out_normal: Point, radius: float,
                sweep_degrees: float = 90.0, segments: int = SWEEP_SEGMENTS) -> tuple[Point, ...]:
    """Fan the leaf tip sweeps from closed to ``sweep_degrees``: the hinge, then the arc."""
    def tip(degrees: float) -> Point:
        c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
        return (hinge[0] + radius * (c * closed_dir[0] + s * out_normal[0]),
                hinge[1] + radius * (c * closed_dir[1] + s * out_normal[1]))

    return (hinge, *(tip(sweep_degrees * i / segments) for i in range(segments + 1)))


def passage_at(leaf_width: float, degrees: float) -> float:
    """Clear passage between the leaf's lateral position and the fixed edge at ``degrees``."""
    return leaf_width * (1.0 - math.cos(math.radians(degrees)))


def degrees_for_passage(leaf_width: float, passage: float) -> float | None:
    """Opening angle that gives ``passage``; ``None`` when even 90 degrees cannot."""
    if passage > leaf_width + 1e-9:
        return None
    return math.degrees(math.acos(max(-1.0, 1.0 - passage / leaf_width)))
