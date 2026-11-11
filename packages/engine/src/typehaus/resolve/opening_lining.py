"""A floor opening's lining: the finish closing the joist band on every edge of the well.

Inside a house the platform lap has nothing to lap: a wall's finish stops at its plate
(``layer_bands.clamp_to_plates``), and a stair well shows the truss ends and trimmers
between that plate and the deck above. ``FloorOpening.lining`` closes the band in the plane
of the finished hole — the outline — from the ceiling below, or the lower top of a wall
under that edge, to the joist tops, where the deck sheet runs over it to that same edge.
The framing behind it has already stepped back by the stack's thickness
(``floor_openings``). The face coat is drawn as a film; the bill reads ``ResolvedFloor``.
"""

from __future__ import annotations

from collections.abc import Iterable

from shapely.geometry import LineString, Polygon

from typehaus.resolve.coatings import COATING_SKIN_M
from typehaus.resolve.floor_openings import OpeningFrame
from typehaus.resolve.layer_bands import wall_body_band
from typehaus.resolve.model import ResolvedSolid, ResolvedWall
from typehaus.resolve.overlay import union_all

_EDGES = ("south", "north", "west", "east")
#: A wall finish stopping further than this under the ceiling plane is not closing the band.
_MAX_DROP_M = 0.1
#: A wall must run this far along an edge to carry it; a butting end does not.
_MIN_EDGE_RUN_M = 0.1
_FACE_TOLERANCE_M = 1e-3


def _edge_lines(frame: OpeningFrame) -> dict[str, LineString]:
    x0, x1, y0, y1 = frame.minx, frame.maxx, frame.miny, frame.maxy
    return {"south": LineString([(x0, y0), (x1, y0)]), "north": LineString([(x0, y1), (x1, y1)]),
            "west": LineString([(x0, y0), (x0, y1)]), "east": LineString([(x1, y0), (x1, y1)])}


def _edge_bases(frame: OpeningFrame, z0: float,
                walls: Iterable[ResolvedWall]) -> dict[str, float]:
    """Each edge's lining bottom: ``z0``, dropped to a wall top stopping just under it."""
    bases = dict.fromkeys(_EDGES, z0)
    lines = _edge_lines(frame)
    for wall in walls:
        top = wall_body_band(wall)[1]
        if not z0 - _MAX_DROP_M <= top < z0:
            continue
        polygons = [Polygon(layer.polygon) for layer in wall.depth_layers()
                    if len(layer.polygon) >= 3]
        if not polygons:
            continue
        face = union_all(polygons).buffer(_FACE_TOLERANCE_M)
        for edge, line in lines.items():
            if line.intersection(face).length >= _MIN_EDGE_RUN_M:
                bases[edge] = min(bases[edge], top)
    return bases


def _film_boxes(frame: OpeningFrame) -> tuple[tuple[float, float, float, float], ...]:
    """The face coat's display skin, inside the outline, one box per edge, tiled."""
    x0, x1, y0, y1 = frame.minx, frame.maxx, frame.miny, frame.maxy
    s = COATING_SKIN_M
    return ((x0, x1, y0, y0 + s), (x0, x1, y1 - s, y1),
            (x0, x0 + s, y0 + s, y1 - s), (x1 - s, x1, y0 + s, y1 - s))


def lining_solids(frame: OpeningFrame, storey: str, z0: float, z1: float,
                  coating: str | None = None, walls: Iterable[ResolvedWall] = (),
                  ) -> tuple[list[ResolvedSolid], float]:
    """``(solids, well-face area m²)``: one solid per edge per layer, corners lapped.

    Layer ``i`` sits at offset ``o`` outboard of the outline. The south/north strips run
    the full outer corner; the west/east strips stop at the inner face of those, so no two
    strips of one layer overlap.
    """
    opening = frame.opening
    x0, x1, y0, y1 = frame.minx, frame.maxx, frame.miny, frame.maxy
    bases = _edge_bases(frame, z0, walls)
    solids: list[ResolvedSolid] = []
    offset = 0.0
    for layer_index, layer in enumerate(opening.lining):
        t = layer.thickness.meters
        o, ot = offset, offset + t
        boxes = ((x0 - ot, x1 + ot, y0 - ot, y0 - o), (x0 - ot, x1 + ot, y1 + o, y1 + ot),
                 (x0 - ot, x0 - o, y0 - o, y1 + o), (x1 + o, x1 + ot, y0 - o, y1 + o))
        for edge, (bx0, bx1, by0, by1) in zip(_EDGES, boxes, strict=True):
            solids.append(ResolvedSolid(
                f"{opening.uid}-LN{layer_index}{edge[0].upper()}",
                f"{opening.tag}-lining-{edge}-{layer.name}", storey, "opening_lining",
                [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], bases[edge], z1,
                material=layer.material_ref))
        offset = ot
    if opening.lining and coating is not None:
        for edge, (bx0, bx1, by0, by1) in zip(_EDGES, _film_boxes(frame), strict=True):
            solids.append(ResolvedSolid(
                f"{opening.uid}-LNP{edge[0].upper()}", f"{opening.tag}-lining-{edge}-paint",
                storey, "opening_lining",
                [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], bases[edge], z1,
                material=coating))
    if not opening.lining:
        return solids, 0.0
    area = sum(line.length * (z1 - bases[edge]) for edge, line in _edge_lines(frame).items())
    return solids, area
