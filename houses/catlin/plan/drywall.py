# haus: editable
# Drywall accessories, declared once (decision #103): the engine finds every outside corner,
# bare-edge termination, tile stop, trimless door jamb, window return and LED shadow gap
# from the faces (resolve/drywall_trims.py) and bills them by the LF in [drywall_trims].
# Inside corners are paper tape, in the gwb rate. Parts researched 2026-10-30, retail or
# distributor listings; "confirm" marks a part number or price not yet read off the page.
#   * LED (owner 2026-10-30, replacing a 1.44"-deep plaster-in channel that rose into the
#     joists): a 5/8" x 5/8" Z shadow bead where the ceiling board stops 5/8" short of the
#     washed wall. Its reveal is the board's depth, so nothing rises past the board; the 8 mm
#     COB tape sticks to the bead's back, facing down. A run is moved onto the reveal centre.
#   * Tile stop: an F reveal where the BATH tile stops on painted board (materials.py tile
#     note: a shadow-gap reveal, not a profile).
#   * Window returns: 3/4" bullnose on the return corner (owner 2026-10-30), matching the
#     wood stools' expected look. A stone stool's notch wraps the finished return at the same
#     3/4" (window_corner_radius), above quartz's 3/8" and Corian's 1/2" minimums. Trim-Tex
#     350 Bull (3/8") fits quartz alone; one bead for every window was chosen over it.

from typehaus import DrywallStandard, Material, Product, ShadowGapProfile, ft, inch

LED_PROFILE_PRODUCT = Product(tag="PROD-TRIMTEX-AS6010", brand="Trim-Tex", model="AS6010", name="Architectural Z-Shadow Bead, 5/8 x 5/8 in., PVC, 10 ft", url="https://myfbm.com/fr-ca/all-products/drywall-trims/reveal-bead/10-ft-x-5-8-in-x-5-8-in-architectural%c2%a0z-shadow-bead-%2850-pieces-per-pack%29/p/ttx-as6010", pack_quantity=50, stock_length=ft(10), source="Foundation Building Materials listing, 50 per pack; price to confirm. A size 5/8 in. matches the board, B size 5/8 in. is the reveal (Trim-Tex sizing).")
REVEAL_PRODUCT = Product(tag="PROD-TRIMTEX-AS8710", brand="Trim-Tex", model="AS8710", name="Architectural F Reveal Bead, 1/2 x 1/2 in., PVC, 10 ft", url="https://myfbm.com/all-products/drywall-trims/reveal-bead/10-ft-x-1-2-in-x-1-2-in-architectural%c2%a0f-reveal-bead-%2825-pieces-per-pack%29/p/ttx-as8710", pack_quantity=25, stock_length=ft(10), source="Foundation Building Materials, $140.00 per carton of 25 (about $0.56/LF). Some listings ship 92 in. pieces: confirm the length on order.")
L_BEAD_PRODUCT = Product(tag="PROD-TRIMTEX-9010", brand="Trim-Tex", model="9010", name="Tear Away L Bead, 1/2 in., vinyl, 10 ft", url="https://trim-tex.com/products/tear-away-l-bead", pack_quantity=50, stock_length=ft(10), source="Trim-Tex stock 9010 (Home Hardware TT-9010). Price to confirm. Trimless door jambs and window-return frame edges.")
J_BEAD_PRODUCT = Product(tag="PROD-PHILLIPS-JT6HDGMEN10", brand="Phillips", model="JT6HDGMEN10", name="Metal J-Bead, 10 ft", url="https://www.menards.com/main/building-materials/drywall/corner-bead/phillips-metal-j-bead/jt6hdgmen10/p-1444450728312-c-13053.htm", stock_length=ft(10), source="Menards; listed for 5/8 in. board. Confirm the 1/2 in. part for the half-inch walls, and the price.")
CORNER_BEAD_PRODUCT = Product(tag="PROD-PHILLIPS-CBRVYLUPC10", brand="Phillips", model="CBRVYLUPC10", name="Vinyl Corner Bead, 10 ft", url="https://www.homedepot.com/p/10-ft-Vinyl-Corner-Bead-Drywall-CBRVYLUPC10/306632722", stock_length=ft(10), source="Home Depot; price to confirm. Outside corners and soffit edges.")
BULLNOSE_BEAD_PRODUCT = Product(tag="PROD-TRIMTEX-7010", brand="Trim-Tex", model="7010", name="3/4 in. Radius Vinyl Bullnose Corner Bead, 90 degree, 10 ft", url="https://myfbm.com/ca/all-products/drywall-trims/vinyl-corner-bead/bullnose-vinyl-corner-bead/10-ft-3-4-in-radius-vinyl-bullnose-corner-bead-7010-%2835-pieces-per-pack%29/p/ttx-7010", pack_quantity=35, stock_length=ft(10), source="Foundation Building Materials listing, 35 per pack; price to confirm. Window-return corners.")

DRYWALL_PRODUCTS = (LED_PROFILE_PRODUCT, REVEAL_PRODUCT, L_BEAD_PRODUCT, J_BEAD_PRODUCT, CORNER_BEAD_PRODUCT, BULLNOSE_BEAD_PRODUCT)

DRYWALL_MATERIALS = (
    Material(tag="led-shadow-gap-bead", name="LED shadow-gap Z bead, 5/8 x 5/8 in.", product_ref="PROD-TRIMTEX-AS6010", color="#ede9e2", source="Trim-Tex AS6010; set and mudded by the drywall trade, painted with the ceiling; tape by the electrician."),
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
        led_profile=ShadowGapProfile(material_ref="led-shadow-gap-bead", reveal=inch(0.625), depth=inch(0.625), flange=inch(1), wall_offset_max=inch(4)),
        stock_length=ft(10),
    ),
]
