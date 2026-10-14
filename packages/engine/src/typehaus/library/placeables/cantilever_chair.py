"""A cantilevered wooden dining chair: bent side members under a plywood seat shell."""

from __future__ import annotations

from typehaus.model import FurnitureType, inch

# The tag names the chair-use zone of a table it is tucked at (see CHESS_TABLE_315). It is
# its own tag, not DINING_CHAIR_TAG, so the catalog can price the two chairs separately.
CANTILEVER_CHAIR_TAG = "FURN-CANTILEVER-CHAIR"

# Envelope from the IKEA LYCKAN chair, birch veneer (item 005.691.91; ikea.com/us, read
# 2026-10-14): 17 3/4" W x 20 1/8" D x 32 5/8" H, seat 18 1/8" high, 16 1/2" deep. The page
# names the cantilever and the materials but not the frame joinery, so the symbol's member
# path is an illustrative cantilever, not a measured one.
CANTILEVER_CHAIR = FurnitureType(
    tag=CANTILEVER_CHAIR_TAG, name="Cantilever wood chair",
    footprint=(inch(17.75), inch(20.125)), height=inch(32.625),
    plan_symbol="cantilever-chair",
    source=("IKEA LYCKAN chair, birch veneer (ikea.com/us item 005.691.91, read 2026-10-14): "
            "17 3/4 x 20 1/8 x 32 5/8 in., seat 18 1/8 in. high. Frame layout illustrative."),
)
