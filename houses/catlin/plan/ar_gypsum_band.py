"""Catlin's abuse-resistant gypsum band: the lower 4' of a face, plain gypsum above (catalog).

Bound on ``LayerMaterial(..., extent=...)`` in the storey files. The sheet is hung from the
plate seat, so the band stops a sheet's 48" over it: 48 3/4" off the datum where the wall
stands on the 3/4" subfloor (main, second), 48" where it stands on the slab or a stair
(basement, ``W-M-WELL``); both from ``notes/floor_heights.md``.
"""

from __future__ import annotations

from typehaus import LayerBound, LayerDatum, LayerExtent, inch

AR_LOWER_BAND = LayerExtent(top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(48.75)))
AR_LOWER_BAND_ON_SLAB = LayerExtent(
    top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(48)))
