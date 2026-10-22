"""Selected bathroom accessories; prices stay in the house price book."""

from typehaus import FurnitureType, Product, inch

MOEN_ALIGN_PAPER_HOLDER = Product(
    tag="PROD-MOEN-YB0408BN", brand="Moen", model="YB0408BN",
    name="Align pivoting toilet-paper holder, brushed nickel",
    url="https://shop.moen.com/products/yb0408ch?variant=49905631363382",
    source="Moen YB0408 technical specification, read 2026-10-22: 8.11 x 3.34 x 1.34 in. "
           "Post centres 6.77 in.; screw holes follow the supplied mounting template. "
           "https://assets.moen.com/shared/docs/product-specifications/yb0408sp.pdf",
)

PAPER_HOLDER = FurnitureType(
    tag="FT-MOEN-ALIGN-TP", name="Moen Align YB0408BN pivoting paper holder",
    footprint=(inch(8.11), inch(3.34)), height=inch(1.34),
    product_ref=MOEN_ALIGN_PAPER_HOLDER.tag, plan_symbol="pivoting-paper-holder",
    wall_fixing_points=((inch(-3.385), inch(0.67)), (inch(3.385), inch(0.67))),
    source="Bare hardware, not the roll. Bar centre 0.67 in. above base. "
           "Reserve 8.11 x 6 x 5.5 in. loaded space, bar at 26 in. AFF; "
           "pivot rises 6.77 in. plus post radius. Template controls final drilling.",
)

CABINET_BACKING_PAD = FurnitureType(
    tag="FT-TP-CABINET-BACKING-12", name='TP holder internal plywood backing pad, 12 x 5 1/2 in.',
    footprint=(inch(12), inch(0.75)), height=inch(5.5),
    plan_symbol="closet-board", wood_material_ref="cabinet-plywood",
    source="3/4 in. cabinet plywood inside the vanity side, covering both holder posts. "
           "Through-fasten both factory mounting plates with stainless machine screws "
           "sized to their holes, washers and locking nuts; trim length clear of storage. "
           "Check the supplied template against hinge pockets, shelf positions and trap. "
           "Do not rely on screw withdrawal from the cabinet side or treat as grab support.",
)

MOEN_ALIGN_PAPER_HOLDER_CHROME = MOEN_ALIGN_PAPER_HOLDER.model_copy(update={
    "tag": "PROD-MOEN-YB0408CH", "model": "YB0408CH",
    "name": "Align pivoting toilet-paper holder, chrome",
    "url": "https://shop.moen.com/products/yb0408ch",
})
PAPER_HOLDER_CHROME = PAPER_HOLDER.model_copy(update={
    "tag": "FT-MOEN-ALIGN-TP-CH", "name": "Moen Align YB0408CH pivoting paper holder",
    "product_ref": MOEN_ALIGN_PAPER_HOLDER_CHROME.tag, "plan_symbol": "pivoting-paper-holder-chrome",
})

BATH_ACCESSORY_PRODUCTS = (MOEN_ALIGN_PAPER_HOLDER, MOEN_ALIGN_PAPER_HOLDER_CHROME)
BATH_ACCESSORY_TYPES = (PAPER_HOLDER, PAPER_HOLDER_CHROME, CABINET_BACKING_PAD)
