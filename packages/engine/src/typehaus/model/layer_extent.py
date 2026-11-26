"""A layer's vertical extent: datum-relative bounds, shared by ``Layer`` and ``LayerMaterial``."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import LayerDatum
from typehaus.quantities import Length, inch


class LayerBound(HausModel):
    """One end of a layer's vertical extent: a datum, plus a signed offset from it."""

    datum: LayerDatum
    offset: Length = inch(0)


class LayerExtent(HausModel):
    """How far up a wall one layer of the stack actually runs.

    This is the "vertically compound wall" of a BIM authoring tool — a layer row split into
    regions at a height — expressed on the *type* rather than on each wall, which is the only
    place it can live: an ``Assembly`` is shared by many walls and knows none of their
    elevations. Two layers with non-overlapping extents that name the same ``Layer.slot``
    are the two regions of one split row, and share one depth position in the stack.

    ``None`` on either end means the wall's own end.
    """

    bottom: LayerBound | None = None   # None -> the wall's base
    top: LayerBound | None = None      # None -> the wall's top


class SkinOverrun(HausModel):
    """The outboard layers of a wall carried past its axis ends, over the face beside it.

    A framed run whose node stops short of the wall it meets (its concrete neighbour owns
    the last inches) would leave its rainscreen open there. ``from_layer`` and every layer
    outboard of it run ``start``/``end`` further along the axis; the layers inboard stay
    on the node. Furring courses run to the band's end and a sheet-laid panel lays its
    columns, battens and end nailers over the longer run. Measured in plan, never negative.
    """

    from_layer: str
    start: Length = inch(0)
    end: Length = inch(0)
