"""A wall finish standing on a falling pour rides its plane (decision #138).

The board goes up after the pour and runs down to the slab, so its bottom is the higher of
its band floor and the pour's top. Stamped on ``ResolvedLayer.bottom_plane``;
``geometry_walls.layer_solids`` (every emitter) and the takeoff read it. A flat pour, or a
layer that starts above the pour or below it, is untouched.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve.floor_tilt import DeckPlane
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.solid_categories import is_pour_slab

_TOUCH_M = 0.002  # a board set against the slab edge still stands on it
_EPS_M = 1e-6


def seat_layers_on_falling_pours(model: ResolvedModel) -> None:
    """Give every finish layer whose foot lies within a falling pour that pour's top plane."""
    from shapely.geometry import Polygon

    pours = [(s, Polygon(s.outline)) for s in model.solids
             if s.top_plane is not None and is_pour_slab(s.category) and len(s.outline) >= 3]
    if not pours:
        return
    for index, wall in enumerate(model.walls):
        layers, changed = [], False
        for layer in wall.layers:
            plane = None
            if (layer.function == "finish" and not layer.coating and not layer.is_cavity
                    and len(layer.polygon) >= 3):
                plane = _seat(wall, layer, Polygon(layer.polygon), pours)
            if plane is not None:
                layer, changed = replace(layer, bottom_plane=plane), True
            layers.append(layer)
        if changed:
            model.walls[index] = replace(wall, layers=tuple(layers))


def _seat(wall: ResolvedWall, layer: ResolvedLayer, footprint, pours) -> DeckPlane | None:
    z0 = layer.band(wall)[0]
    for solid, outline in pours:
        if not footprint.buffer(_TOUCH_M).intersects(outline):
            continue
        top = max(solid.top_at(x, y) for x, y in layer.polygon)
        if solid.z0_m - _EPS_M <= z0 < top - _EPS_M:
            p = solid.top_plane
            return DeckPlane(origin=p.origin, lift_at_origin_m=solid.z1_m + p.lift_at_origin_m,
                             gradient=p.gradient)
    return None


def bottom_at(layer: ResolvedLayer, z0: float, z1: float):
    """The layer's bottom at a plan point, held in ``[z0, z1]``; None when it is flat."""
    plane = layer.bottom_plane
    if plane is None:
        return None
    return lambda x, y: min(max(z0, plane.lift(x, y)), z1)


def mean_bottom(layer: ResolvedLayer, z0: float, z1: float) -> float:
    """The bottom averaged over the layer's footprint vertices (a trapezoid's mean height)."""
    at = bottom_at(layer, z0, z1)
    if at is None or not layer.polygon:
        return z0
    return sum(at(x, y) for x, y in layer.polygon) / len(layer.polygon)
