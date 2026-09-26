"""A floor opening's lining: the finish closing the joist band on every edge of the well.

Inside a house the platform lap has nothing to lap: a wall's finish stops at its plate
(``layer_bands.clamp_to_plates``), and a stair well shows the truss ends and trimmers
between that plate and the deck above. ``FloorOpening.lining`` closes the band in the plane
of the finished hole — the outline — from the ceiling below to the joist tops, where the
deck sheet runs over it to that same edge. The framing behind it has already stepped back
by the stack's thickness (``floor_openings``).
"""

from __future__ import annotations

from typehaus.resolve.floor_openings import OpeningFrame
from typehaus.resolve.model import ResolvedSolid

_EDGES = ("south", "north", "west", "east")


def lining_solids(frame: OpeningFrame, storey: str, z0: float,
                  z1: float) -> tuple[list[ResolvedSolid], float]:
    """``(solids, well-face area m²)``: one solid per edge per layer, corners lapped.

    Layer ``i`` sits at offset ``o`` outboard of the outline. The south/north strips run
    the full outer corner; the west/east strips stop at the inner face of those, so no two
    strips of one layer overlap.
    """
    opening = frame.opening
    x0, x1, y0, y1 = frame.minx, frame.maxx, frame.miny, frame.maxy
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
                [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], z0, z1,
                material=layer.material_ref))
        offset = ot
    area = 2.0 * ((x1 - x0) + (y1 - y0)) * (z1 - z0) if opening.lining else 0.0
    return solids, area
