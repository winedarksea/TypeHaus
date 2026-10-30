"""A coating takes no depth (``Material.coating``): one predicate for every depth sum.

A paint, primer, sealer or wash is billed by area and drawn as a skin on its host face, but
it occupies no slice of a wall, floor or ceiling. Its authored ``Layer.thickness`` stays:
Glaser reads it for permeance, and the drawing legend lists it.
"""

from __future__ import annotations

from typing import Any

#: How far a renderer stands a zero-depth coating's display skin off its host face (~0.5 mm),
#: so it reads without z-fighting. Display only: no quantity or check reads it.
COATING_SKIN_M = 0.0005

_CACHE: dict[int, tuple[Any, frozenset[str]]] = {}


def coating_tags(library: Any) -> frozenset[str]:
    """Tags of the library's coating materials, cached per library instance."""
    hit = _CACHE.get(id(library))
    if hit is not None and hit[0] is library:
        return hit[1]
    tags = frozenset(m.tag for m in library.materials if getattr(m, "coating", False))
    if len(_CACHE) > 16:
        _CACHE.clear()
    _CACHE[id(library)] = (library, tags)
    return tags


def is_coating(library: Any, material_ref: str | None) -> bool:
    return material_ref in coating_tags(library)


def layer_depth_m(library: Any, layer: Any) -> float:
    """The depth an authored ``Layer`` takes: its thickness, or 0.0 for a coating."""
    return 0.0 if is_coating(library, layer.material_ref) else layer.thickness.meters


def _frame(wall: Any) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    tangent = ((x1 - x0) / run, (y1 - y0) / run)
    return (x0, y0), tangent, (-tangent[1], tangent[0])


def _coords(origin, tangent, normal, point) -> tuple[float, float]:
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    return dx * tangent[0] + dy * tangent[1], dx * normal[0] + dy * normal[1]


def _rect(origin, tangent, normal, t0, t1, n0, n1) -> list[tuple[float, float]]:
    def at(t, n):
        return (origin[0] + tangent[0] * t + normal[0] * n,
                origin[1] + tangent[1] * t + normal[1] * n)
    return [at(t0, n0), at(t1, n0), at(t1, n1), at(t0, n1)]


def strip_coatings(walls: list) -> tuple[list, dict[str, tuple]]:
    """Walls without their coating layers, plus what was taken, for :func:`restore_coatings`.

    The junction solver clips polygons, and a zero-width ring clips to nothing. A coating
    instead follows its host face once the host is clipped.
    """
    from dataclasses import replace

    stripped, taken = [], {}
    for wall in walls:
        if any(layer.coating for layer in wall.layers):
            taken[wall.tag] = wall.layers
            wall = replace(wall, layers=tuple(ly for ly in wall.layers if not ly.coating))
        stripped.append(wall)
    return stripped, taken


def restore_coatings(walls: list, taken: dict[str, tuple]) -> list:
    """Re-insert each coating in stack order, its ring laid on its solved host face."""
    from dataclasses import replace

    out = []
    for wall in walls:
        original = taken.get(wall.tag)
        if original is None:
            out.append(wall)
            continue
        solved = {layer.name: layer for layer in wall.layers}
        origin, tangent, normal = _frame(wall)
        layers = []
        for index, layer in enumerate(original):
            if not layer.coating:
                if layer.name in solved:
                    layers.append(solved[layer.name])
                continue
            offset = _coords(origin, tangent, normal, layer.polygon[0])[1]
            hosts = [ly for ly in reversed(original[:index]) if not (ly.coating or ly.is_cavity)]
            hosts = hosts[:1] + [ly for ly in original[index + 1:]
                                 if not (ly.coating or ly.is_cavity)][:1]
            ring = list(layer.polygon)
            for host in hosts:
                along = [t for t, n in (_coords(origin, tangent, normal, p)
                                        for p in solved.get(host.name, host).polygon)
                         if abs(n - offset) <= 1e-6]
                if len(along) >= 2:
                    ring = _rect(origin, tangent, normal, min(along), max(along),
                                 offset, offset)
                    break
            layers.append(replace(layer, polygon=ring))
        out.append(replace(wall, layers=tuple(layers)))
    return out


def coating_skin_ring(wall: Any, layer: Any, skin_m: float = COATING_SKIN_M) -> list:
    """A coating's display ring: its face line stood ``skin_m`` off, away from the body."""
    origin, tangent, normal = _frame(wall)
    points = [_coords(origin, tangent, normal, p) for p in layer.polygon]
    if not points:
        return []
    offset = sum(n for _t, n in points) / len(points)
    body = [_coords(origin, tangent, normal, p)[1] for ly in wall.layers
            if not (ly.coating or ly.is_cavity) for p in ly.polygon]
    centre = (min(body) + max(body)) / 2.0 if body else 0.0
    side = 1.0 if offset > centre else -1.0
    ring = _rect(origin, tangent, normal, min(t for t, _n in points),
                 max(t for t, _n in points), offset, offset + side * skin_m)
    return ring if side > 0 else ring[::-1]
