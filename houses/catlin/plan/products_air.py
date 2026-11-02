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
    tag="PROD-AIR-FILTER-RETURN-28X12", brand="Hart & Cooley", model="673 series",
    name="28x12 hinged filter-back return grille, aluminium, white, 1in filter rack",
    source=f"Basis of design, or equal: TRUaire 190RF, Shoemaker 620FG. 12x28x1 is NOT a "
           f"stocked filter size; no stocked size fits EQ-S-ERV-MIX's 12x29 opening under "
           f"300 fpm (12x24x1 runs 347 fpm at 650 cfm), so the filter is ordered as a custom "
           f"size online. {_SPEC} §5.",
)
RETURN_GRILLE_1210 = Product(
    tag="PROD-AIR-RETURN-GRILLE-12X10", brand="TRUaire", model="A170 12X10",
    name="12x10 aluminium fixed-bar return grille, white (a pair through the wall)",
    source=f"Basis of design, or equal: Hart & Cooley A650. Acoustic alternative: Tamarack "
           f"RAPR return-air pathway (baffled, no published STC). {_SPEC} §6.",
)
ROUND_DAMPER_4_24V = Product(
    tag="PROD-AIR-DAMPER-4-24V", brand="EWC", model="4RSD",
    name="4in round 24 VAC spring-return motorised damper, galvanized",
    url="https://www.supplyhouse.com/EWC-4RSD-4-RSD-Spring-Return-Motorized-Damper",
    source=f"Basis of design, or equal: Duro Dyne NSPRD024-4, Zonefirst RDSC. RH-controlled "
           f"locally. Body length and actuator size unpublished online. {_SPEC} §7.",
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
PLANT_CEILING_GRILLE = Product(
    tag="PROD-AIR-PLANT-GRILLE-12X6", brand="TRUaire", model="A220V 12X06",
    name="12x6 aluminium double-deflection ceiling grille, white, without OBD",
    url="https://rectorseal.com/hvac/a220-adjustable-double-deflection/",
    source=f"Plain A220V, not A220VO: motorized damper provides isolation and balancing. {_SPEC} §7.",
)
PLANT_ZONE_DAMPER = Product(
    tag="PROD-AIR-PLANT-DAMPER-12X6", brand="Honeywell Home", model="ZD12X6TZ",
    name="12x6 rectangular 24 VAC power-close, spring-open zone damper, 4in body",
    url="https://customer.resideo.com/resources/Techlit/TechLitDocuments/33-00000s/33-00264.pdf",
    source=f"Vertical airflow; actuator on the west 6in side. Nominal passage; frame is "
           f"5/32in undersize per manufacturer. M847D actuator included, not a second purchase. {_SPEC} §7.",
)
PLANT_END_BOOT = Product(
    tag="PROD-AIR-PLANT-END-BOOT", brand="Project fabrication", model="TH-HP-PLANT-BOOT-01",
    name="26ga galvanized end boot, 10x6 east inlet to 12x6 downward outlet",
    source="Fabricated shell envelope 12in E-W x 10in N-S x 6in high; downward outlet "
           "centred, east inlet full 10x6. Closed west end; sealed seams and turning vane. "
           "Dimensioned section and service sequence: notes/plant_supply_connection.md.",
)
PLANT_COLLAR = Product(
    tag="PROD-AIR-PLANT-COLLAR", brand="Project fabrication", model="TH-HP-PLANT-COLLAR-01",
    name="26ga galvanized 12x6 grille collar, 1/2in installed face-to-damper extension",
    source="Removable collar and gasketed flange; membrane sealed to fixed perimeter. "
           "Slip engagements additional to installed extension; notes/plant_supply_connection.md.",
)
PLANT_SERVICE_HATCH = Product(
    tag="PROD-AIR-PLANT-SERVICE-HATCH", brand="Project fabrication", model="TH-HP-PLANT-HATCH-01",
    name="12x8 white PVC gasketed screw-fixed service cover, 10x6 clear opening",
    source="Matching Extrutech liner offcut, fixed flanged galvanized curb, closed-cell EPDM "
           "gasket and stainless captive screws. Membrane sealed to the fixed curb, never "
           "to the removable cover. Included in the terminal assembly allowance. "
           "notes/plant_supply_connection.md.",
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
BACKDRAFT_DAMPER_8 = Product(
    tag="PROD-AIR-BACKDRAFT-8", brand="RenewAire", model="BD8 (102401)",
    name="8in inline butterfly backdraft damper",
    url="https://www.ferguson.com/product/renewaire-8-in.-backdraft-damper-rbd8/4781816.html",
    source=f"On DU-ERV-EA only, inside the wall line; the intake stays undampered. {_SPEC} §8.",
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
    SUITEBATH_EXTRACT_BOOT,
    DISC_VALVE_100, FLOOR_GRILLE_ERV, SIDEWALL_DD_OBD, FLOOR_REGISTER_HP,
    FILTER_RETURN_GRILLE, RETURN_GRILLE_1210, ROUND_DAMPER_4_24V, STAIR_REGISTER_BOX, PLANT_CEILING_GRILLE, PLANT_ZONE_DAMPER, PLANT_END_BOOT, PLANT_COLLAR, PLANT_SERVICE_HATCH,
    WALL_HOOD_8, BACKDRAFT_DAMPER_8, WALL_SEAL_FOAM, ELASTOMERIC_SHEET, SPOT_NOZZLE_4,
)
