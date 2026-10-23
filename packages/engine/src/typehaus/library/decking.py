"""Named deck boards: actual stock dimensions and manufacturer support limits.

Board thickness is shared by the deck layer and stair stock so a nominal 1-inch label
cannot independently set the walking surface and the wood supporting it.
"""

from typehaus.model.floors import DeckLayer
from typehaus.model.materials import Material
from typehaus.model.product import Product
from typehaus.quantities import inch

TREX_ENHANCE_BASICS_PRODUCT = Product(
    tag="PROD-TREX-ENHANCE-BASICS", brand="Trex", model="Enhance Basics",
    name="Square-edge composite deck board, Tide Pool",
    url="https://www.trex.com/professionals/products/decking/",
    source="Trex Enhance product guide; actual 0.94 x 5.5 inch stock.",
)
TREX_ENHANCE_BASICS = Material(
    tag="trex-enhance-basics",
    product_ref=TREX_ENHANCE_BASICS_PRODUCT.tag,
    name="Trex Enhance Basics composite decking (Tide Pool, square edge)",
    r_per_inch=1.0,
    density=1000.0,
    perm_rating=0.5,
    hatch="lumber",
    color="#a3a6a4",
    finish="composite-deck-board",
    # Approximate sRGB misty grey; lighting and displays affect the rendered match.
    source=(
        "Trex Enhance Basics, scalloped capped wood/plastic composite, Tide Pool. "
        "Actual 0.94 x 5.5 in: https://www.trex.com/professionals/products/decking/ ; "
        "9 in maximum stair stringer spacing, 1/4-3/8 in tread gaps: "
        "https://online.flippingbook.com/view/63974767/36/ . "
        "Nonstructural walking surface; square-edge, face-fastened on stairs. "
        "Density/thermal/vapor properties retain the generic composite-deck proxy, "
        "not product-certified values."
    ),
)
TREX_ENHANCE_BASICS_DECK_LAYER = DeckLayer(
    material_ref=TREX_ENHANCE_BASICS.tag, thickness=inch(0.94),
)
TREX_ENHANCE_BASICS_BOARD_WIDTH = inch(5.5)
TREX_ENHANCE_BASICS_STAIR_SUPPORT_SPACING = inch(9)
TREX_ENHANCE_BASICS_STAIR_BOARD_GAP = inch(0.25)
