# haus: editable
# Drywall accessories, declared once (decision #103): the engine finds every outside corner,
# bare-edge termination, tile stop, trimless door jamb, window return and plaster-in LED
# slot from the faces (resolve/drywall_trims.py) and bills them by the LF in [drywall_trims].
# Inside corners are paper tape, in the gwb rate. Parts researched 2026-10-30, retail or
# distributor listings; "confirm" marks a part number or price not yet read off the page.
#   * LED: a 45-degree asymmetric wall-wash plaster-in channel in a 51 mm (2") slot, 21.7 mm
#     wings, 36.6 mm deep. The slot edge sits 1-3" off the washed wall, so its centre 2-4".
#   * Tile stop: an F reveal where the BATH tile stops on painted board (materials.py tile
#     note: a shadow-gap reveal, not a profile).
#   * Window returns: 3/4" bullnose on the return corner (owner 2026-10-30), matching the
#     wood stools' expected look. A stone stool's notch wraps the finished return at the same
#     3/4" (window_corner_radius), above quartz's 3/8" and Corian's 1/2" minimums. Trim-Tex
#     350 Bull (3/8") fits quartz alone; one bead for every window was chosen over it.

from typehaus import DrywallStandard, Material, PlasterInProfile, Product, deg, ft, inch

LED_PROFILE_PRODUCT = Product(tag="PROD-SLL-ALU-COVE-MS-9537", brand="SuperLightingLED", model="ALU-COVE-MS-9537", name="Plaster-in aluminium LED channel, 45-degree asymmetric wall wash, 94.4 x 36.6 mm, 51 mm drywall groove", url="https://www.superlightingled.com/product_spec.php?products_id=7219", stock_length=inch(96), source="Listed 1 m / 2 m / 2.44 m lengths; $26.98 base selection, length for that price to confirm. Wing width and slot-to-wall distance derived from the 94.4 mm width and 51 mm groove; confirm against the seller's section drawing.")
REVEAL_PRODUCT = Product(tag="PROD-TRIMTEX-AS8710", brand="Trim-Tex", model="AS8710", name="Architectural F Reveal Bead, 1/2 x 1/2 in., PVC, 10 ft", url="https://myfbm.com/all-products/drywall-trims/reveal-bead/10-ft-x-1-2-in-x-1-2-in-architectural%c2%a0f-reveal-bead-%2825-pieces-per-pack%29/p/ttx-as8710", pack_quantity=25, stock_length=ft(10), source="Foundation Building Materials, $140.00 per carton of 25 (about $0.56/LF). Some listings ship 92 in. pieces: confirm the length on order.")
L_BEAD_PRODUCT = Product(tag="PROD-TRIMTEX-9010", brand="Trim-Tex", model="9010", name="Tear Away L Bead, 1/2 in., vinyl, 10 ft", url="https://trim-tex.com/products/tear-away-l-bead", pack_quantity=50, stock_length=ft(10), source="Trim-Tex stock 9010 (Home Hardware TT-9010). Price to confirm. Trimless door jambs and window-return frame edges.")
J_BEAD_PRODUCT = Product(tag="PROD-PHILLIPS-JT6HDGMEN10", brand="Phillips", model="JT6HDGMEN10", name="Metal J-Bead, 10 ft", url="https://www.menards.com/main/building-materials/drywall/corner-bead/phillips-metal-j-bead/jt6hdgmen10/p-1444450728312-c-13053.htm", stock_length=ft(10), source="Menards; listed for 5/8 in. board. Confirm the 1/2 in. part for the half-inch walls, and the price.")
CORNER_BEAD_PRODUCT = Product(tag="PROD-PHILLIPS-CBRVYLUPC10", brand="Phillips", model="CBRVYLUPC10", name="Vinyl Corner Bead, 10 ft", url="https://www.homedepot.com/p/10-ft-Vinyl-Corner-Bead-Drywall-CBRVYLUPC10/306632722", stock_length=ft(10), source="Home Depot; price to confirm. Outside corners and soffit edges.")
BULLNOSE_BEAD_PRODUCT = Product(tag="PROD-TRIMTEX-7010", brand="Trim-Tex", model="7010", name="3/4 in. Radius Vinyl Bullnose Corner Bead, 90 degree, 10 ft", url="https://myfbm.com/ca/all-products/drywall-trims/vinyl-corner-bead/bullnose-vinyl-corner-bead/10-ft-3-4-in-radius-vinyl-bullnose-corner-bead-7010-%2835-pieces-per-pack%29/p/ttx-7010", pack_quantity=35, stock_length=ft(10), source="Foundation Building Materials listing, 35 per pack; price to confirm. Window-return corners.")

DRYWALL_PRODUCTS = (LED_PROFILE_PRODUCT, REVEAL_PRODUCT, L_BEAD_PRODUCT, J_BEAD_PRODUCT, CORNER_BEAD_PRODUCT, BULLNOSE_BEAD_PRODUCT)

DRYWALL_MATERIALS = (
    Material(tag="led-plaster-in-wallwash", name="Plaster-in LED wall-washer channel, 45-degree", product_ref="PROD-SLL-ALU-COVE-MS-9537", color="#c8c8c8", source="SuperLightingLED ALU-COVE-MS-9537; set and mudded by the drywall trade, tape and lens by the electrician."),
    Material(tag="dw-reveal-bead-f", name="F reveal bead (tile stop), 1/2 in.", product_ref="PROD-TRIMTEX-AS8710", source="Trim-Tex AS8710; the tile's top and free ends against painted board."),
    Material(tag="dw-l-bead-tearaway", name="Tear-away L-bead, 1/2 in.", product_ref="PROD-TRIMTEX-9010", source="Trim-Tex 9010; trimless door jambs and window-return frame edges."),
    Material(tag="dw-j-bead-metal", name="Metal J-bead", product_ref="PROD-PHILLIPS-JT6HDGMEN10", source="Phillips JT6HDGMEN10; board ending on a bare face."),
    Material(tag="dw-corner-bead-vinyl", name="Vinyl outside corner bead", product_ref="PROD-PHILLIPS-CBRVYLUPC10", source="Phillips CBRVYLUPC10; outside corners and soffit edges."),
    Material(tag="dw-bullnose-bead-vinyl", name="Vinyl bullnose corner bead, 3/4 in. radius", product_ref="PROD-TRIMTEX-7010", source="Trim-Tex 7010; window-return corners; past a stone stool to its underside, so the stool's notch seats against it."),
)

DRYWALL_STANDARD = [
    DrywallStandard(
        uid="AQAV6SJFW6", tag="DRYWALL-STANDARD",
        outside_corner_ref="dw-corner-bead-vinyl",
        termination_ref="dw-j-bead-metal",
        door_bead_ref="dw-l-bead-tearaway",
        tile_reveal_ref="dw-reveal-bead-f",
        window_corner_ref="dw-bullnose-bead-vinyl",
        window_corner_radius=inch(0.75),
        window_frame_ref="dw-l-bead-tearaway",
        led_profile=PlasterInProfile(material_ref="led-plaster-in-wallwash", aperture=inch(2), depth=inch(1.4375), flange=inch(0.875), tilt=deg(45), wall_offset_min=inch(2), wall_offset_max=inch(4)),
        stock_length=ft(10),
    ),
]
