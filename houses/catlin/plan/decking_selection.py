"""The Trex colour this house chose: Enhance Basics in Tide Pool (owner 2026-10-22).

The library ships the board colour-unselected. The house swaps in its own copy under the
same tag, so every deck layer, tread, price row and golden keeps its reference and only
the look and the product identity change. Not ``# haus: editable``: the swap is a
comprehension, which the editable dialect forbids. notes/composite_decking.md.
"""

from __future__ import annotations

from typehaus.library import TREX_ENHANCE_BASICS, TREX_ENHANCE_BASICS_PRODUCT

# Mean of the centre half of Trex's own Tide Pool swatch photo
# (images.trex.com/.../enh-001-tp-decking-swatch-TP010608E2S56, read 2026-10-22). The 3"
# sample shot under studio light reads lighter, #a7a193; check a physical sample.
TIDE_POOL_COLOR = "#8e847b"

TREX_TIDE_POOL_PRODUCT = TREX_ENHANCE_BASICS_PRODUCT.model_copy(update={
    "model": "Enhance Basics, Tide Pool (TP)",
    "name": "Square-edge composite deck board, Tide Pool",
    "url": "https://www.trex.com/products/decking/enhance/tide-pool/",
    "source": "Owner selection 2026-10-22. Trex Enhance Basics in Tide Pool, colour prefix "
              "TP, heat-mitigating; actual 0.94 x 5.5 in stock.",
})
TREX_TIDE_POOL = TREX_ENHANCE_BASICS.model_copy(update={
    "name": "Trex Enhance Basics composite decking, Tide Pool (square edge)",
    "color": TIDE_POOL_COLOR,
    "source": TREX_ENHANCE_BASICS.source.replace("color unselected", "Tide Pool (2026-10-22)"),
})


def with_selected_decking(materials):
    """``materials`` with the library Trex row replaced by this house's colour."""
    return tuple(TREX_TIDE_POOL if m.tag == TREX_TIDE_POOL.tag else m for m in materials)
