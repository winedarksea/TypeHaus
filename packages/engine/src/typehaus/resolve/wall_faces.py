"""A wall's plan body, from its own resolved layers — the solid a room stops at.

A room's axis cell (``_storey_faces``) runs to the wall centrelines; what is actually
floor is that cell minus every wall layer standing on the storey. Reading the layers
rather than one assembly lining is what makes a retype, a liner or a thick exterior wall
move the room it bounds.
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.overlay import difference, union_all

# A band touching the storey datum by a hair is not standing in the room.
_BAND_EPS_M = 1e-4
# An axis midpoint on a polygonized edge sits there to float noise (rooms.py's lining rule).
_ON_EDGE_M = 1e-6


def wall_body(wall: ResolvedWall, z0: float, z1: float) -> BaseGeometry:
    """Union of ``wall``'s non-cavity layer polygons whose band overlaps ``[z0, z1]``.

    Cavity fills share their host layer's polygon, so they add nothing and are skipped.
    """
    parts = []
    for layer in wall.layers:
        if layer.is_cavity or len(layer.polygon) < 3:
            continue
        b0, b1 = layer.band(wall)
        if b1 <= z0 + _BAND_EPS_M or b0 >= z1 - _BAND_EPS_M:
            continue
        poly = Polygon(layer.polygon)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            parts.append(poly)
    return union_all(parts)


def storey_wall_mass(model: ResolvedModel, storey_tag: str,
                     faces: list[Polygon]) -> BaseGeometry:
    """The body of every wall on ``storey_tag`` that closes a loop, over the storey band.

    ``faces`` are the storey's axis cells. A wall whose axis lies on none of their
    boundaries closes no loop — a tub-deck knee wall, a free-standing brick panel — and
    stands IN a room like furniture; subtracting it would cut the room in two.
    """
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    if storey is None:
        return union_all([])
    z0 = storey.elevation.meters
    z1 = z0 + storey.default_ceiling_height.meters
    edges = union_all([f.exterior for f in faces])
    return union_all(wall_body(w, z0, z1) for w in model.walls
                     if w.storey == storey_tag
                     and edges.distance(LineString(w.axis).interpolate(0.5, normalized=True))
                     <= _ON_EDGE_M)


def clear_cell(face: Polygon, mass: BaseGeometry, seed) -> Polygon | None:
    """``face`` minus the wall mass: the piece holding ``seed``, or None if it is in a wall."""
    clear = difference(face, mass) if not mass.is_empty else face
    for piece in getattr(clear, "geoms", (clear,)):
        if piece.geom_type == "Polygon" and piece.covers(seed):
            return piece
    return None
