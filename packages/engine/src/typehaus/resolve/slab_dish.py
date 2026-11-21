"""A pour's dish to a floor drain inside a level rim (decision #148, ``DrainDish``).

The surface is a fan of planar facets, one per rim edge, from the drain to that edge. The
drain sits ``rise = rate x h_max`` low, ``h_max`` being the drain's farthest perpendicular
distance to an edge, so the shallowest facet falls at exactly the rate. Top and bottom drop
together (constant thickness), and so does everything under them.

Leaf and pure: float math only (Pyodide-safe); ``resolve/model.py`` imports it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GMesh

_M_PER_FT = 0.3048
_EPS = 1e-12


@dataclass(frozen=True)
class DishSurface:
    """``lift(x, y) <= 0`` below the rim; 0 on and outside it. ``ring`` is counter-clockwise."""

    slab_uid: str  # the authored slab whose piece this is
    slab_tag: str
    drain: tuple[float, float]
    ring: tuple[tuple[float, float], ...]
    rise_m: float

    def _edge(self, i: int) -> tuple[float, float, float]:
        """Edge ``i``'s outward unit normal and the drain's perpendicular distance to it."""
        (ax, ay), (bx, by) = self.ring[i], self.ring[(i + 1) % len(self.ring)]
        length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        nx, ny = (by - ay) / length, -(bx - ax) / length
        return nx, ny, nx * (ax - self.drain[0]) + ny * (ay - self.drain[1])

    def sector(self, x: float, y: float) -> int | None:
        """The facet whose sector (drain, v_i, v_i+1) holds the point, else None at the drain."""
        dx, dy = x - self.drain[0], y - self.drain[1]
        if abs(dx) < _EPS and abs(dy) < _EPS:
            return None
        count = len(self.ring)
        for i in range(count):
            (ax, ay), (bx, by) = self.ring[i], self.ring[(i + 1) % count]
            ux, uy = ax - self.drain[0], ay - self.drain[1]
            vx, vy = bx - self.drain[0], by - self.drain[1]
            if ux * dy - uy * dx >= -_EPS and dx * vy - dy * vx >= -_EPS:
                return i
        return None

    def lift(self, x: float, y: float) -> float:
        i = self.sector(x, y)
        if i is None:
            return -self.rise_m
        nx, ny, h = self._edge(i)
        reach = (nx * (x - self.drain[0]) + ny * (y - self.drain[1])) / h
        return min(0.0, max(-self.rise_m, -self.rise_m * (1.0 - reach)))


def build_dish(slab_uid: str, slab_tag: str, drain: tuple[float, float],
               ring: list[tuple[float, float]], rate_in_per_ft: float) -> DishSurface:
    """The dish over ``ring`` to ``drain``; refuses a rim not star-shaped from the drain."""
    if _signed_area(ring) < 0:
        ring = ring[::-1]
    count = len(ring)
    turned = 0.0
    for i in range(count):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % count]
        ux, uy = ax - drain[0], ay - drain[1]
        vx, vy = bx - drain[0], by - drain[1]
        if ux * vy - uy * vx <= _EPS:
            raise ValueError("the dish rim is not star-shaped from its drain (or the drain "
                             "is on or outside it)")
        turned += math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    if abs(turned - 2 * math.pi) > 1e-6:
        raise ValueError("the dish rim winds round its drain more than once")
    surface = DishSurface(slab_uid, slab_tag, drain, tuple(ring), 0.0)
    h_max = max(surface._edge(i)[2] for i in range(count))
    return DishSurface(slab_uid, slab_tag, drain, tuple(ring),
                       rate_in_per_ft * M_PER_IN / _M_PER_FT * h_max)


def dish_mesh(solid: Any) -> GMesh:
    """A dish piece: its fan top, the bottom one thickness under it, and plumb rim sides."""
    dish = solid.dish
    count = len(dish.ring)
    thickness = solid.z1_m - solid.z0_m
    top = [(*dish.drain, solid.z1_m - dish.rise_m)] + [(x, y, solid.z1_m) for x, y in dish.ring]
    positions = tuple(top) + tuple((x, y, z - thickness) for x, y, z in top)
    n = count + 1
    triangles: list[tuple[int, int, int]] = []
    for i in range(count):
        a, b = 1 + i, 1 + (i + 1) % count
        triangles.append((0, a, b))  # counter-clockwise from above: faces up
        triangles.append((n, n + b, n + a))
        triangles.extend(((a, n + b, b), (a, n + a, n + b)))
    return GMesh(positions=positions, triangles=tuple(triangles))


def piece_at(model: Any, solid: Any, xy: tuple[float, float]) -> Any:
    """The dish piece of authored slab ``solid`` whose rim holds ``xy``, else ``solid``."""
    from shapely.geometry import Point, Polygon

    for piece in model.solids:
        if (piece.dish is not None and piece.dish.slab_uid == solid.uid
                and piece.category == solid.category
                and Polygon(piece.dish.ring).buffer(1e-6).contains(Point(xy))):
            return piece
    return solid


def _signed_area(ring) -> float:
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(ring, list(ring[1:]) + list(ring[:1]), strict=True)) / 2


def dish_pieces(model: Any, element: Any, solids: list[Any]) -> tuple[list[Any], list[Any]]:
    """Cut ``element``'s dishes out of its ``solids`` (the pour and its top finish).

    Returns ``(solids, findings)``: the solids with each dish rim added to their voids, and
    one piece per dish and solid: same category and assembly, ``z0``/``z1`` at the rim,
    carrying the surface. Void and piece net out, so the billed area does not change. A bad
    dish is an ERROR.
    """
    from dataclasses import replace

    from shapely.geometry import Point, Polygon

    from typehaus.findings import element_error

    findings, pieces, voids = [], [], []
    slab = Polygon([p.xy_m for p in element.outline])
    for i, dish in enumerate(element.drain_dishes):
        ring = [p.xy_m for p in dish.outline]
        fixture = model.plan.by_tag(dish.drain_ref)
        where = (getattr(fixture, "drain_position", None) or getattr(fixture, "position", None)
                 if getattr(fixture, "element_kind", None) == "Fixture" else None)
        problem = None
        if where is None:
            problem = f"drain {dish.drain_ref!r} is no Fixture"
        elif not Polygon(ring).contains(Point(where.xy_m)):
            problem = f"drain {dish.drain_ref} is not inside the dish outline"
        elif not slab.buffer(1e-6).covers(Polygon(ring)):
            problem = "the dish outline is not inside the slab"
        if problem is None:
            try:
                surface = build_dish(element.uid, element.tag, where.xy_m, ring,
                                     dish.rate_in_per_ft)
            except ValueError as exc:
                problem = str(exc)
        if problem is not None:
            findings.append(element_error("integrity.slab_drain_dish",
                                          f"slab {element.tag} dish {i}: {problem}", element.tag))
            continue
        voids.append(tuple(surface.ring))
        for s in solids:
            suffix = s.uid[len(element.uid):]  # "" for the pour, "-<layer>" for a finish
            pieces.append(replace(s, uid=f"{element.uid}-dish-{i}{suffix}",
                                  tag=f"{element.tag}:dish-{i}{s.tag[len(element.tag):]}",
                                  outline=list(surface.ring), voids=(), dish=surface))
    cut = [replace(s, voids=(*s.voids, *voids)) for s in solids] if voids else list(solids)
    return cut + pieces, findings
