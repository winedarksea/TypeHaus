"""Moen Align hardware: brushed nickel generally, chrome in Bath2."""

from typehaus import FurnitureType, Product, inch

HAND_TOWEL_PRODUCT = Product(
    tag="PROD-MOEN-YB0486BN",
    brand="Moen",
    model="YB0486BN",
    name="Align hand towel bar, brushed nickel",
    url="https://www.moen.com/products/YB0486BN",
    source="Moen YB0486 specification, read 2026-10-22: 9.17 x 3.33 x 1.34 in.; "
    "https://assets.moen.com/shared/docs/product-specifications/yb0486sp.pdf",
)
BATH_TOWEL_PRODUCT = Product(
    tag="PROD-MOEN-YB0424BN",
    brand="Moen",
    model="YB0424BN",
    name="Align 24 in. towel bar, brushed nickel",
    url="https://www.moen.com/products/YB0424BN",
    source="Moen YB0424 specification, read 2026-10-22: 25.34 x 3.33 x 1.34 in., "
    "24 in. post centres; https://assets.moen.com/shared/docs/product-specifications/yb0424sp.pdf",
)
TOWEL_HOOK_PRODUCT = Product(
    tag="PROD-MOEN-YB0403BN",
    brand="Moen",
    model="YB0403BN",
    name="Align single robe/towel hook, brushed nickel",
    url="https://www.moen.com/products/YB0403BN",
    source="Moen YB0403 specification, read 2026-10-22: 1.34 in. diameter, 2.54 in. projection; "
    "https://assets.moen.com/shared/docs/product-specifications/yb0403sp.pdf",
)

HAND_TOWEL_BAR = FurnitureType(
    tag="FT-MOEN-ALIGN-HAND-TOWEL",
    name="Moen Align YB0486BN hand towel bar",
    footprint=(inch(9.17), inch(3.33)),
    height=inch(1.34),
    product_ref=HAND_TOWEL_PRODUCT.tag,
    plan_symbol="towel-bar",
    wall_fixing_points=((inch(-3.915), inch(0.67)), (inch(3.915), inch(0.67))),
    source="Mount at 48 in. AFF on walls; 30 in. AFF on cabinet sides (suite 32.5). "
    "Allow 18 in. hanging drop and 4.5 in. loaded projection. "
    "Factory template governs final screw holes; fasten both plates to solid support.",
)
BATH_TOWEL_BAR = FurnitureType(
    tag="FT-MOEN-ALIGN-BATH-TOWEL",
    name="Moen Align YB0424BN 24 in. bath towel bar",
    footprint=(inch(25.34), inch(3.33)),
    height=inch(1.34),
    product_ref=BATH_TOWEL_PRODUCT.tag,
    plan_symbol="towel-bar",
    wall_fixing_points=((inch(-12), inch(0.67)), (inch(12), inch(0.67))),
    source="Bar centre 54 in. AFF (attic 51 in. to clear roof rake). "
    "Allow a folded bath towel 28 in. below the bar "
    "and 4.5 in. from the wall; these are planning allowances. "
    "Use the supplied template for drilling and screw both plates into solid support.",
)
TOWEL_HOOK = FurnitureType(
    tag="FT-MOEN-ALIGN-TOWEL-HOOK",
    name="Moen Align YB0403BN bath towel hook",
    footprint=(inch(1.34), inch(2.54)),
    height=inch(1.34),
    product_ref=TOWEL_HOOK_PRODUCT.tag,
    plan_symbol="towel-hook",
    wall_fixing_points=((inch(0), inch(0.67)),),
    source="Mounting centre 64 in. AFF. Allow a gathered towel 12 in. wide, "
    "55 in. down and 6 in. projecting, rather than assuming the bare hook is clear. "
    "Both factory plate screws into stud or backing; template governs drilling.",
)
TOWEL_CABINET_PAD = FurnitureType(
    tag="FT-TOWEL-CABINET-BACKING-12",
    name="Hand towel internal plywood pad, 12 x 3 in.",
    footprint=(inch(12), inch(0.75)),
    height=inch(3),
    plan_symbol="closet-board",
    wood_material_ref="cabinet-plywood",
    source="3/4 in. cabinet plywood inside the side panel, covering both mounting plates. "
    "Through-fasten with stainless machine screws, washers and locking nuts. "
    "Coordinate the supplied template with shelves, hinges, drawers and plumbing; "
    "trim bolts clear of storage. Suite pad sits above the separate TP pad.",
)

HAND_TOWEL_PRODUCT_CHROME = HAND_TOWEL_PRODUCT.model_copy(update={
    "tag": "PROD-MOEN-YB0486CH", "model": "YB0486CH",
    "name": "Align hand towel bar, chrome", "url": "https://shop.moen.com/products/yb0486ch",
    "source": HAND_TOWEL_PRODUCT.source + " Chrome variant; zinc posts, stainless steel bar.",
})
BATH_TOWEL_PRODUCT_CHROME = BATH_TOWEL_PRODUCT.model_copy(update={
    "tag": "PROD-MOEN-YB0424CH", "model": "YB0424CH",
    "name": "Align 24 in. towel bar, chrome", "url": "https://shop.moen.com/products/yb0424ch",
    "source": BATH_TOWEL_PRODUCT.source + " Chrome variant; specification lists zinc construction.",
})
TOWEL_HOOK_PRODUCT_CHROME = TOWEL_HOOK_PRODUCT.model_copy(update={
    "tag": "PROD-MOEN-YB0403CH", "model": "YB0403CH",
    "name": "Align single robe/towel hook, chrome", "url": "https://shop.moen.com/products/yb0403ch",
    "source": TOWEL_HOOK_PRODUCT.source + " Chrome variant; zinc construction.",
})
HAND_TOWEL_BAR_CHROME = HAND_TOWEL_BAR.model_copy(update={
    "tag": HAND_TOWEL_BAR.tag + "-CH", "name": "Moen Align YB0486CH hand towel bar",
    "product_ref": HAND_TOWEL_PRODUCT_CHROME.tag, "plan_symbol": "towel-bar-chrome",
})
BATH_TOWEL_BAR_CHROME = BATH_TOWEL_BAR.model_copy(update={
    "tag": BATH_TOWEL_BAR.tag + "-CH", "name": "Moen Align YB0424CH 24 in. bath towel bar",
    "product_ref": BATH_TOWEL_PRODUCT_CHROME.tag, "plan_symbol": "towel-bar-chrome",
})
TOWEL_HOOK_CHROME = TOWEL_HOOK.model_copy(update={
    "tag": TOWEL_HOOK.tag + "-CH", "name": "Moen Align YB0403CH bath towel hook",
    "product_ref": TOWEL_HOOK_PRODUCT_CHROME.tag, "plan_symbol": "towel-hook-chrome",
})

TOWEL_PRODUCTS = (HAND_TOWEL_PRODUCT, BATH_TOWEL_PRODUCT, TOWEL_HOOK_PRODUCT,
                  HAND_TOWEL_PRODUCT_CHROME, BATH_TOWEL_PRODUCT_CHROME, TOWEL_HOOK_PRODUCT_CHROME)
TOWEL_TYPES = (HAND_TOWEL_BAR, BATH_TOWEL_BAR, TOWEL_HOOK, TOWEL_CABINET_PAD,
               HAND_TOWEL_BAR_CHROME, BATH_TOWEL_BAR_CHROME, TOWEL_HOOK_CHROME)
