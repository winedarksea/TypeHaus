"""Corner fillets on a plan ring: one source for the DXF's true arcs and the 3D facets.

A fillet replaces vertex V with an arc tangent to both adjoining edges. The arc turns the
way the path turns at V, so a concave corner bulges the right way on either ring winding.
A radius whose tangent points would overrun an adjoining edge (shared with its neighbour's
fillet in proportion) is clamped and flagged; it is never silently dropped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True)
class Fillet:
    """One rounded corner: ``start``/``end`` are the tangent points in ring order."""

    index: int
    vertex: Point
    start: Point
    end: Point
    center: Point
    radius_m: float
    requested_m: float
    # DXF LWPOLYLINE bulge on the start->end segment: tan(sweep / 4), + counter-clockwise.
    bulge: float
    convex: bool

    @property
    def clamped(self) -> bool:
        return self.radius_m < self.requested_m - 1e-9


def signed_area(ring: tuple[Point, ...] | list[Point]) -> float:
    """Shoelace area; positive for a counter-clockwise ring."""
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                     in zip(ring, [*ring[1:], ring[0]], strict=True))


def vertex_is_convex(ring, index: int) -> bool:
    """True when the ring turns the same way as its winding at ``index``."""
    prev, here, nxt = ring[index - 1], ring[index], ring[(index + 1) % len(ring)]
    cross = ((here[0] - prev[0]) * (nxt[1] - here[1])
             - (here[1] - prev[1]) * (nxt[0] - here[0]))
    return cross * signed_area(ring) > 0.0


def _corner(ring, index: int):
    """(here, unit back, unit ahead, back length, ahead length, half interior angle)."""
    prev, here, nxt = ring[index - 1], ring[index], ring[(index + 1) % len(ring)]
    back = (prev[0] - here[0], prev[1] - here[1])
    ahead = (nxt[0] - here[0], nxt[1] - here[1])
    back_len, ahead_len = math.hypot(*back), math.hypot(*ahead)
    if back_len <= 1e-12 or ahead_len <= 1e-12:
        return None
    u1 = (back[0] / back_len, back[1] / back_len)
    u2 = (ahead[0] / ahead_len, ahead[1] / ahead_len)
    interior = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
    if interior <= 1e-9 or math.pi - interior <= 1e-9:
        return None  # a spike or a straight run: nothing to round
    return here, u1, u2, back_len, ahead_len, interior / 2.0


def corner_fillets(ring, radii_m) -> tuple[Fillet, ...]:
    """A fillet for every vertex with a positive radius (collinear vertices take none).

    Two fillets sharing an edge split it in proportion to what each asks for, so a 1/2"
    corner beside a square one may use the whole of a 3/4" horn end.
    """
    count = len(ring)
    corners = [_corner(ring, index) if radius > 0.0 else None
               for index, radius in enumerate(radii_m)]
    wanted = [radius / math.tan(corner[5]) if corner is not None else 0.0
              for radius, corner in zip(radii_m, corners, strict=True)]
    fillets: list[Fillet] = []
    for index, corner in enumerate(corners):
        if corner is None:
            continue
        here, u1, u2, back_len, ahead_len, half = corner
        tangent = wanted[index]
        for length, other in ((back_len, wanted[index - 1]),
                              (ahead_len, wanted[(index + 1) % count])):
            if tangent + other > length:
                tangent = min(tangent, length * wanted[index] / (wanted[index] + other))
        radius = tangent * math.tan(half)
        start = (here[0] + u1[0] * tangent, here[1] + u1[1] * tangent)
        end = (here[0] + u2[0] * tangent, here[1] + u2[1] * tangent)
        bisector = (u1[0] + u2[0], u1[1] + u2[1])
        bis_len = math.hypot(*bisector)
        reach = radius / math.sin(half)
        center = (here[0] + bisector[0] / bis_len * reach,
                  here[1] + bisector[1] / bis_len * reach)
        prev, nxt = ring[index - 1], ring[(index + 1) % count]
        turn = (here[0] - prev[0]) * (nxt[1] - here[1]) - (here[1] - prev[1]) * (nxt[0] - here[0])
        fillets.append(Fillet(
            index=index, vertex=here, start=start, end=end, center=center, radius_m=radius,
            requested_m=radii_m[index],
            bulge=math.copysign(math.tan((math.pi - 2.0 * half) / 4.0), turn),
            convex=vertex_is_convex(ring, index)))
    return tuple(fillets)


def arc_points(fillet: Fillet, segments: int) -> list[Point]:
    """``segments`` chords from ``start`` to ``end`` along the fillet's arc, ends included."""
    cx, cy = fillet.center
    a0 = math.atan2(fillet.start[1] - cy, fillet.start[0] - cx)
    sweep = 4.0 * math.atan(fillet.bulge)
    return [(cx + fillet.radius_m * math.cos(a0 + sweep * step / segments),
             cy + fillet.radius_m * math.sin(a0 + sweep * step / segments))
            for step in range(segments + 1)]


def filleted_ring(ring, radii_m, segments: int = 6) -> tuple[Point, ...]:
    """The ring with each filleted vertex replaced by a faceted arc (for shapely and 3D)."""
    by_index = {fillet.index: fillet for fillet in corner_fillets(ring, radii_m)}
    out: list[Point] = []
    for index, vertex in enumerate(ring):
        fillet = by_index.get(index)
        out.extend(arc_points(fillet, segments) if fillet is not None else [vertex])
    return tuple(out)
