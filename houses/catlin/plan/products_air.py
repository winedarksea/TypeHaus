"""Air-distribution products: one record per basis-of-design part (2026-10-31).

Every row is a PERFORMANCE SPEC plus a basis of design, "or equal": the owner wants
commodity sizes any maker fits, so the part a sub buys may differ as long as it meets the
spec the type carries (face, neck, loss curve). Identity only, never a price (#28).
Spec, sources and what is unverified: notes/air_distribution_products.md.

NOT ``# haus: editable``: catalog definitions, nothing placed.
"""

from __future__ import annotations

from typehaus import Product

_SPEC = "notes/air_distribution_products.md"

DISC_VALVE_100 = Product(
    tag="PROD-AIR-DISC-VALVE-100", brand="Vents-US", model="AM 100 VRF",
    name="100 and 125 mm round steel disc valves, white powder coat, supply or extract, with collar",
    url="https://hvacdirect.com/vents-us-am-100-vrf-air-metal-disc-valve-diffuser.html",
    source=f"Basis of design, or equal: Trox LVS/TVS-100, Lindab KU/KK 100, Zehnder "
           f"ComfoValve 100. Face 5 1/16\" (128.5 mm), collar spigot 98 mm into a 4\" "
           f"snap-lock collar (mastic and foil tape). Vents-US publishes no loss curve; the "
           f"types carry Trox LVS 100's published curve at +5 mm as the ceiling an or-equal "
           f"must meet. {_SPEC} §2.",
)
FLOOR_GRILLE_ERV = Product(
    tag="PROD-AIR-FLOOR-GRILLE-2X10", brand="Reggio Registers", model="412-AH",
    name="2 1/4 x 10 aluminium floor grille on a 2 1/4 x 10 x 4 stamped 90-degree boot",
    url="https://fergusonhome.com/reggio-registers-412-ah/s1246287",
    source=f"Basis of design, or equal: Reggio G412, Shoemaker AFP 2 1/4x10. Boot: Snappy "
           f"P13-204 (2 1/4 x 10 x 4, 90 degree) or equal. A disc valve cannot sit in a "
           f"floor. {_SPEC} §3.",
)
SIDEWALL_DD_OBD = Product(
    tag="PROD-AIR-SIDEWALL-DD-OBD", brand="TRUaire", model="A220VO",
    name="Aluminium double-deflection sidewall register with opposed-blade damper, white",
    url="https://hvacquick.com/products/residential/Grilles-Registers/Grilles/"
        "TRUaire-A220-Series-Aluminum-Double-Deflection-Adjustable-Bar-Grilles",
    source=f"Basis of design, or equal: Hart & Cooley HVD, Shoemaker 904-O. 12x06 face "
           f"13 3/4 x 7 3/4; 08X06 face 9 3/4 x 7 3/4 (hvacquick, read 2026-10-31). Damper "
           f"depth unpublished; H&C HVD's 3 7/16\" overall depth is the planning figure. "
           f"{_SPEC} §4.",
)
# RM-S-SUITE's supply (owner, 2026-11-19): a decorative face, Sun Gold to match its plates.
SIDEWALL_CHEVRON_SUN_GOLD = Product(
    tag="PROD-AIR-CHEVRON-1206-SG", brand="Reggio Register Co.", model="Chevron 6x12",
    name="Chevron grille, 6x12 duct / 8x14 overall, 3/16in laser-cut aluminium, Sun Gold, "
         "mounting holes",
    url="https://www.ventcoversunlimited.com/products/chevron-design-vent-covers-made-to-order",
    source=f"Made to order, 4-6 wk; price and free area unconfirmed, need >= 29 in2 (100 cfm "
           f"at 500 fpm) on the submittal. Or equal: any laser-cut 6x12 decorative grille "
           f"meeting that free area. {_SPEC} §4.",
)
LOUVER_DAMPER_814 = Product(
    tag="PROD-AIR-LOUVER-814", brand="Reggio Register Co.", model="814-BL",
    name="Steel louver damper behind a 6x12 grille, key-set at commissioning, 2 5/16in deep",
    url="https://www.fergusonhome.com/reggio-registers-814/s1246350",
    source=f"The Chevron has no damper of its own; this sits in the 6in register box. {_SPEC} §4.",
)
FLOOR_REGISTER_HP = Product(
    tag="PROD-AIR-FLOOR-REG-6X12", brand="Hart & Cooley", model="531SA 6x12",
    name="6x12 extruded aluminium floor register with multi-shutter damper",
    url="https://www.ecmdi.com/6-x-12-aluminum-floor-supply-register-531sa-series-white-49257",
    source=f"Basis of design, or equal: Reggio 6x12 aluminium, Shoemaker 600 series. Face "
           f"and damper depth unpublished at this size; planned at 7 3/8 x 13 3/8 x 2\" "
           f"(TRUaire 150's 2\" depth). Oak-match flush in RM-A-STUDY is a note only. "
           f"{_SPEC} §4.",
)
FILTER_RETURN_GRILLE = Product(
    tag="PROD-AIR-FILTER-RETURN-12X24", brand="Hart & Cooley", model="673 series",
    name="24x12 hinged filter-back return grille, aluminium, white, 1in filter rack",
    source=f"Basis of design, or equal: TRUaire 190RF, Shoemaker 620FG. 12x24x1 MERV 13 is a "
           f"stocked filter size: 228 fpm at 455 cfm, ~0.24in clean. 14x25x1 does not fit "
           f"SF-S-DUCT's 12.5in clear ({_SPEC} §5).",
)
FILTER_RETURN_GRILLE_1212 = Product(
    tag="PROD-AIR-FILTER-RETURN-12X12", brand="Hart & Cooley", model="673 series 12x12",
    name="12x12 hinged filter-back return grille, aluminium, white, 1in filter rack",
    source=f"Basis of design, or equal: TRUaire 190RF, Shoemaker 620FG. RM-S-SUITE's return; "
           f"12x12x1 MERV 13 is a stocked filter size. {_SPEC} §5.",
)
RETURN_GRILLE_1210 = Product(
    tag="PROD-AIR-RETURN-GRILLE-12X10", brand="TRUaire", model="A170 12X10",
    name="12x10 aluminium fixed-bar return grille, white (one grille per terminal)",
    source=f"Basis of design, or equal: Hart & Cooley A650. Acoustic alternative: Tamarack "
           f"RAPR return-air pathway (baffled, no published STC). {_SPEC} §6.",
)
RETURN_GRILLE_0606 = Product(
    tag="PROD-AIR-RETURN-GRILLE-6X6", brand="TRUaire", model="A170 6X6",
    name="6x6 aluminium fixed-bar return grille, white (one per face, offset)",
    source=f"Basis of design, or equal: Hart & Cooley A650. The steel 170 6x6 lists 0.17 sf "
           f"effective area. {_SPEC} §6.",
)
# RM-S-PLANT's high/low transfer pair to Study 2 (2026-11-12, notes/plant_room_moisture_budget.md §4).
RETURN_GRILLE_1006 = Product(
    tag="PROD-AIR-RETURN-GRILLE-10X6", brand="TRUaire", model="170 10X06",
    name="10x6 steel fixed-bar return grille, white (Study 2 face of the plant transfer pair)",
    source=f"Basis of design, or equal. ~0.29 sf (42 in2) free area, scaled from the 170 6x6's "
           f"0.17 sf listing; confirm on the submittal. {_SPEC} §6.",
)
RETURN_GRILLE_1006_OBD = Product(
    tag="PROD-AIR-RETURN-GRILLE-10X6-OBD", brand="TRUaire", model="170VO 10X06",
    name="10x6 steel return grille with face-operated opposed-blade damper, white",
    source=f"Basis of design, or equal. The OBD is the plant room's humidity control: set by "
           f"hand from the room RH sensor and held by its friction lever. {_SPEC} §6.",
)
XFER_SLEEVE_1006 = Product(
    tag="PROD-AIR-XFER-SLEEVE-10X6", brand="Project fabrication",
    model="TH-XFER-SLEEVE-1006",
    name="10x6 galvanized through-wall sleeve, 7 1/4in, 1in flange on the plant face",
    source="Shop-made. Flange taped to the plant room's Class I membrane (butyl), sleeve "
           "sealed to the gypsum on the study face, so plant air never enters the stud bay. "
           "notes/plant_room.md.",
)
ROUND_DAMPER_4_MANUAL = Product(
    tag="PROD-AIR-DAMPER-4-MANUAL", brand="Imperial",
    name="4in round manual volume damper, locking quadrant, galvanized",
    source="The DuctStandard's in-line damper (DU-B-ERV-R-BENCH, over the bench valve): closing "
           "the sauna hatches swings DU-B-ERV-R-SAUNA-EXH's flow to the valve. SKU picked at "
           "order; any retail 4in round volume damper with a quadrant lock.",
)
ROUND_DAMPER_6_MANUAL = Product(
    tag="PROD-AIR-DAMPER-6-MANUAL", brand="Imperial",
    name="6in round manual volume damper, locking quadrant, galvanized",
    source="The DuctStandard's in-line damper on DU-S-ERV-HP-FEED: sets the mixing box's "
           "92 cfm at commissioning. SKU picked at order; any retail 6in round volume damper "
           "whose quadrant locks (Minn. R. 1346.0603 subp. 10, IMC 603.18.3).",
)
STAIR_REGISTER_BOX = Product(
    tag="PROD-AIR-STAIR-REGISTER-BOX", brand="Project fabrication", model="TH-HP-STAIR-BOX-01",
    name="26ga galvanized 12x6x4in register box, centred 4in round back collar",
    source="12in along wall x 6in tall x 4in deep, including the A220VO OBD envelope. "
           "4in round galvanized branch at 50 cfm, 573 fpm; notes/stair_supply_connection.md.",
)
SUITEBATH_EXTRACT_BOOT = Product(
    tag="PROD-AIR-SUITEBATH-BOOT", brand="Project fabrication",
    model="TH-ERV-SUITEBATH-BOOT-01",
    name="26ga sealed galvanized 4x8x5-1/4in bottom-entry extract valve box",
    source="Overall envelope including front collar: 4in along wall x 8in tall x 5 1/4in "
           "into wall. 4in bottom inlet axis 3 1/4in behind front plane; 100 mm removable "
           "disc valve centred on front. Includes collar and mounting tabs within envelope. "
           "Fabrication specification, not a manufacturer submittal; notes/suitebath_extract.md.",
)
# The same box turned over (REG-M-RET-STUDY, 2026-11-16): the riser drops onto a top inlet.
STACK_TOP_EXTRACT_BOOT = Product(
    tag="PROD-AIR-STACK-TOP-BOOT", brand="Project fabrication",
    model="TH-ERV-STACK-TOP-BOOT-01",
    name="26ga sealed galvanized 4x8x5-1/4in top-entry extract valve box",
    source="TH-ERV-SUITEBATH-BOOT-01 inverted: 4in along wall x 8in tall x 5 1/4in into wall, "
           "4in top inlet axis 3 1/4in behind front plane, 100 mm disc valve centred on front. "
           "Fabrication specification; notes/suitebath_extract.md.",
)
# The suite-bath box made deep enough to reach a riser in the 2x6 leaf behind a 2x4 furring
# leaf (REG-A-STUBATH-EXH, W-A-STU-W, 2026-11-16).
STUBATH_EXTRACT_BOOT = Product(
    tag="PROD-AIR-STUBATH-BOOT", brand="Project fabrication",
    model="TH-ERV-STUBATH-BOOT-01",
    name="26ga sealed galvanized 4x7x9in bottom-entry extract valve box",
    source="TH-ERV-SUITEBATH-BOOT-01 at 9in deep, 7in tall (clears PR-A-STUBATH-VENT): 4in x 7in x 9in, "
           "spanning both leaves' stud bay; 4in bottom inlet on the riser (axis 6 3/4in behind "
           "the front plane), 100 mm disc valve centred on front. Fabrication specification; "
           "notes/suitebath_extract.md.",
)
WALL_HOOD_8 = Product(
    tag="PROD-AIR-HOOD-8", brand="RenewAire", model="FA8-P (102409)",
    name="8in wall hood, 1/4in screen, no damper, paintable galvanneal",
    url="https://renewaire.com/wp-content/uploads/2025/09/Hoods-Dampers-.pdf",
    source=f"Basis of design for both hoods, or equal: Fantech FML8 with its bug screen "
           f"swapped for 1/4in mesh (no published curve). 1/4in screen, not insect mesh, so "
           f"frost does not blind it. Painted to the north-face cladding. Either hood's plate "
           f"must lap the 9x9in RO (AO-M-ERV-OA/AO-S-ERV-EA): Fantech's FML8 card lists "
           f"9 x 9in, which does not; FA8-P's plate is unpublished, confirm. {_SPEC} §8.",
)
WALL_SEAL_FOAM = Product(
    tag="PROD-AIR-WALL-SEAL-FOAM", brand="Great Stuff Pro", model="Window & Door",
    name="Low-expansion polyurethane foam, gun grade, 20 oz",
    url="https://hemlockhardware.com/products/260448-great-stuff-pro-window-door-20-oz-straw-foam",
    source=f"The OA/EA wall seal's annulus fill, or equal DAP Touch 'n Foam Window & Door. "
           f"Low expansion so it does not bow the duct. {_SPEC} §9.",
)
ELASTOMERIC_SHEET = Product(
    tag="PROD-AIR-ELASTOMERIC-1IN", brand="Armacell", model="AP Armaflex sheet, 1in",
    name="1in closed-cell elastomeric sheet, two layers on the OA/EA legs (R-8.4)",
    url="https://cdn.bakerdist.com/armacell_aps_en_ss.pdf",
    source=f"k 0.25 at 75 F (R-4.2 per inch, datasheet). Two 1in layers, not one 2in: plain "
           f"AP is 25/50-rated only through 1in, and 2in FS reads R-7.1. Armaflex 520 "
           f"adhesive; or equal K-Flex Insul-Sheet. Its own vapour retarder. {_SPEC} §9.",
)
SPOT_NOZZLE_4 = Product(
    tag="PROD-AIR-SPOT-NOZZLE-4", brand="Shoemaker", model="1202-4",
    name="4in aluminium round spot diffuser / nozzle",
    url="https://hvacquick.com/products/residential/Grilles-Registers/Spot-Diffuser-Nozzles/"
        "Shoemaker-Aluminum-Round-Spot-Diffuser-Nozzles",
    source=f"Stall-fan discharge, or equal: Schako DSARR-V. Aluminium for the wet location; "
           f"a 4in gravity backdraft damper rides in the duct above it. Wet rating not "
           f"published. {_SPEC} §10.",
)

AIR_PRODUCTS = (
    SUITEBATH_EXTRACT_BOOT, STACK_TOP_EXTRACT_BOOT, STUBATH_EXTRACT_BOOT,
    DISC_VALVE_100, FLOOR_GRILLE_ERV, SIDEWALL_DD_OBD, FLOOR_REGISTER_HP,
    SIDEWALL_CHEVRON_SUN_GOLD, LOUVER_DAMPER_814,
    FILTER_RETURN_GRILLE, FILTER_RETURN_GRILLE_1212, RETURN_GRILLE_1210, RETURN_GRILLE_0606, ROUND_DAMPER_4_MANUAL, ROUND_DAMPER_6_MANUAL, STAIR_REGISTER_BOX, RETURN_GRILLE_1006, RETURN_GRILLE_1006_OBD, XFER_SLEEVE_1006,
    WALL_HOOD_8, WALL_SEAL_FOAM, ELASTOMERIC_SHEET, SPOT_NOZZLE_4,
)
