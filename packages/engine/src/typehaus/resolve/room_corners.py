"""A room ring's corners: one classifier for the base runs and the drywall beads.

A ring is the room's ``clear_face`` turned counter-clockwise (the room on the left of every
edge), measured in arc length ``s``. A left turn is an inside corner of the room, a right
turn (a reflex vertex) an outside one.
"""

from __future__ import annotations

from typehaus.resolve import room_perimeter as rp


def ring_vertices(ring) -> list[float]:
    s, out = 0.0, []
    for i in range(len(ring)):
        out.append(s)
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % len(ring)]
        s += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return out


def corners_only(ring: list) -> list:
    """``ring`` without its collinear vertices: a straight face is one board, not two."""
    out = []
    for i, (bx, by) in enumerate(ring):
        (ax, ay), (cx, cy) = ring[i - 1], ring[(i + 1) % len(ring)]
        u = ((bx - ax), (by - ay))
        v = ((cx - bx), (cy - by))
        nu, nv = (u[0] ** 2 + u[1] ** 2) ** 0.5, (v[0] ** 2 + v[1] ** 2) ** 0.5
        if nu < 1e-9 or nv < 1e-9:
            continue
        if abs(u[0] * v[1] - u[1] * v[0]) / (nu * nv) > 1e-4 or u[0] * v[0] + u[1] * v[1] < 0:
            out.append((bx, by))
    return out if len(out) >= 3 else ring


def point_and_outward(ring, s):
    """The point at ``s`` and the unit vector from it into the wall (right of a CCW edge)."""
    x, y = rp.point_at(ring, s)
    ex, ey = edge_direction(ring, s)
    return (x, y), (ey, -ex)


def edge_direction(ring, s):
    vertices = ring_vertices(ring)
    index = max(i for i, v in enumerate(vertices) if v <= s + 1e-9)
    (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
    length = max(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, 1e-12)
    return (x1 - x0) / length, (y1 - y0) / length


def corner_kind(ring, s_vertex) -> str:
    """``inside`` at a convex vertex of the room (a left turn of a CCW ring), else outside."""
    vertices = ring_vertices(ring)
    index = min(range(len(vertices)), key=lambda i: abs(vertices[i] - s_vertex))
    (ax, ay), (bx, by), (cx, cy) = (ring[index - 1], ring[index],
                                    ring[(index + 1) % len(ring)])
    cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
    return "inside" if cross > 0 else "outside"
