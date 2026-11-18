# haus: editable
# Device boxes, declared once (decision #93): the engine derives each wall device's box from
# the face it lands on (resolve/device_boxes.py) and bills box plus cover/ring each.
#   * surface — bare basement concrete: RACO 232 4" square x 2 1/8" (30.3 in3, Table
#     314.16(A)) under a 1/2" raised industrial cover, fed by NM in a derived 3/4" EMT sleeve
#     from overhead (notes/basement_surface_wiring.md).
#   * flush — a framed cavity: a deep nonmetallic new-work box, which the owner prefers
#     because it is easier to make up.
#   * flush_raceway — a flush box an authored raceway or a floor-heat lead reaches: the steel
#     4" square with a 1-device ring, which clears Schluter's 35 mm thermostat minimum.
#   * luminaire, surface — a wall light on concrete: RACO 192 4" square x 1 1/2" under a flat
#     RACO 753, so a 4 1/2" square sconce backplate covers it (geometry review C6-E10, owner
#     2026-11-01). The box sides stay in view: field-paint them to the wall.
#   * luminaire-round — the WAC Sprig sconces (marks J, J1): a 4" round box, what the plate is
#     slotted for and what the 4 3/8" canopy covers with 3/16" to spare all round.
#   * recessed — the fridge and freezer receptacles: an Arlington IN BOX, plug inside the wall.
#     Its new-work screws want wood (Q-3), and both boxes sit mid-bay, so each gets a flat
#     2x4 block behind it, stud to stud, derived from the row (geometry review M3-107).
# Covers and rings are not credited a volume: none of these is marked with one.
# The blue nonmetallic boxes name box-pvc-blue; steel rows stay galvanized (material_ref None).

from typehaus import BoxRow, BoxStandard, PlateRow, Product, inch

_SOURCE = "Owner decision 2026-10-28, notes/basement_surface_wiring.md."

RACO_232 = Product(tag="PROD-RACO-232", brand="RACO", model="232",
                   name="4 in. square box, 2-1/8 in. deep, welded, 1/2 and 3/4 in. KOs",
                   url="https://www.hubbell.com/raco/en/Products/232", source=_SOURCE)
RACO_808C = Product(tag="PROD-RACO-808C", brand="RACO", model="808C",
                    name="4 in. square exposed-work cover, 1 Decorator device, 1/2 in. raised",
                    url="https://www.hubbell.com/raco/en/Products/808C", source=_SOURCE)
# Catalog 809C confirmed 2026-10-29 (Hubbell RACO page): "Exposed Work, Raised 1/2 in., 2-GFCI";
# the GFCI and Decorator openings are the same.
RACO_809C = Product(tag="PROD-RACO-809C", brand="RACO", model="809C",
                    name="4 in. square exposed-work cover, 2 GFCI/Decorator, 1/2 in. raised",
                    url="https://www.hubbell.com/raco/en/Products/Electrical-Electronic/Boxes/4-in-Square-Boxes-Covers/809C/p/2141600",
                    source=_SOURCE)
RACO_768 = Product(tag="PROD-RACO-768", brand="RACO", model="768",
                   name="4 in. square device ring, 1 device, 5/8 in. raised",
                   url="https://www.hubbell.com/raco/en/Products/768", source=_SOURCE)
# Checked 2026-10-29 against distributor catalogs (ABB's own e-catalog did not load): B122A-UPC
# is 22 cu. in. and 3-1/2" deep. There is no B235A; Carlon's 35 cu. in. 2-gang nail-on is the
# SuperBlue BH235A, also 3-1/2" deep.
CARLON_B122A = Product(tag="PROD-CARLON-B122A", brand="Carlon", model="B122A-UPC",
                       name="1-gang nonmetallic nail-on new-work box, 22 cu. in., 3-1/2 in. deep",
                       url="https://www.elliottelectric.com/P/Item/TAB/B122A-UPC", source=_SOURCE)
CARLON_BH235A = Product(tag="PROD-CARLON-BH235A", brand="Carlon", model="BH235A",
                        name="2-gang SuperBlue nail-on new-work box, 35 cu. in., 3-1/2 in. deep",
                        url="https://www.elliottelectric.com/P/Item/TAB/BH235A", source=_SOURCE)

# Hubbell RACO-192 / RACO-753 sheets, read 2026-11-01: drawn 4" square, 1.563" deep, 21.0 in3;
# flat cover 4 x 4 x 0.063", 1/2" centre KO for the fixture's nipple and crossbar.
RACO_192 = Product(tag="PROD-RACO-192", brand="RACO", model="192",
                   name="4 in. square box, 1-1/2 in. deep, drawn, 1/2 and 3/4 in. KOs",
                   url="https://hubbellcdn.com/specsheet/192.pdf", source=_SOURCE)
RACO_753 = Product(tag="PROD-RACO-753", brand="RACO", model="753",
                   name="4 in. square cover, flat, 1/2 in. centre KO (luminaire)",
                   url="https://hubbellcdn.com/specsheet/RACO-753-SPEC-EN.pdf", source=_SOURCE)
# Arlington catalog page Q-3 (PDF of 2025-05-01), re-read 2026-11-06: DVFR1W, UPC 14330,
# 21.0 in3, 4.200 x 6.698 x 3.875"; "New Work: Screws provided for fast and easy mounting
# to stud"; duplex plate included; "plugs don't extend past the wall".
ARLINGTON_DVFR1W = Product(tag="PROD-ARLINGTON-DVFR1W", brand="Arlington", model="DVFR1W",
                           name="IN BOX recessed 1-gang box, trim and duplex plate, 21 cu. in.",
                           url="https://www.aifittings.com/media/catalog-pages/Q-3.pdf",
                           source="Geometry review C5-E2, owner 2026-11-01.")

# Distributor listings read 2026-11-08 (Gexpro, Platt): 4" round, 2-1/4" deep, 20 cu. in., nail-on.
CARLON_B520A = Product(tag="PROD-CARLON-B520A", brand="Carlon", model="B520A-UPC",
                       name="4 in. round nonmetallic nail-on box, 20 cu. in., 2-1/4 in. deep",
                       url="https://www.gexpro.com/p/17618/carlon/4-round-ceiling-box-nail-on-2-1-4-deep-non-metallic/034481006213/b520a-upc",
                       source="Round box for the WAC Sprig sconces, 2026-11-08.")

# RM-S-PLANT's sealed liner (2026-11-12): every box through the Class I membrane is an
# air-sealed one, flange taped to the membrane, gasketed cable entries, an extension ring
# out to the PVC face. Volumes are the published class figure; confirm on the submittal.
AIRFOIL_1G = Product(tag="PROD-LESSCO-AIRFOIL-1G", brand="Lessco / Airfoil", model="Airfoil 1-gang",
                     name="Air-sealing 1-gang box, gasketed flange and cable entries, 20 cu. in.",
                     url="https://www.airfoilinc.com/",
                     source="Basis of design, or equal (Allied Moulded air-seal box). notes/plant_room.md, K6.")
AIRFOIL_ROUND = Product(tag="PROD-LESSCO-AIRFOIL-ROUND", brand="Lessco / Airfoil",
                        model="Airfoil 4 in. round",
                        name="Air-sealing 4 in. round ceiling/wall box, gasketed flange, 20 cu. in.",
                        url="https://www.airfoilinc.com/",
                        source="Basis of design, or equal: ED-S-PLANT-SPOT's sconce box. notes/plant_room.md, K6.")

# ED-M-FIRE-RC (owner, 2026-11-16): the fireplace pocket's 2 3/8" strip takes no wall plate, so a
# welded handy box screws to the pocket's back under a Decora/GFCI handy-box cover. The cover is
# the faceplate. Nominal 2 5/16" wide (Hubbell's table reads 2.425"): MEASURE IT ON DELIVERY.
# Eight 3/4" KOs and no internal clamps (external NM connectors), so 314.16(B)(2) adds nothing.
_HANDY_SOURCE = "Owner decision 2026-11-16, notes/wiring_device_geometry.md §4."
RACO_674 = Product(tag="PROD-RACO-674", brand="RACO", model="674",
                   name="4 x 2 in. handy box, welded, 2-1/8 in. deep, 16.5 cu. in.",
                   url="https://hubbellcdn.com/specsheet/RACO-674-SPEC-EN.pdf", source=_HANDY_SOURCE)
RACO_862 = Product(tag="PROD-RACO-862", brand="RACO", model="862",
                   name="4 x 2 in. handy box cover, Decora/GFCI, nominal 4-3/16 x 2-5/16 in.",
                   url="https://hubbellcdn.com/specsheet/RACO-862-SPEC-EN.pdf", source=_HANDY_SOURCE)

# Gang banks (resolve/device_banks.py): SuperBlue 3- and 4-gang nail-on, same family and depth
# as BH235A. Carlon SuperBlue catalog (via pdf.lowes.com): BH353A 5 7/8 x 3 3/4 x 3 1/2,
# BH464A 7 3/4 x 3 7/8 x 3 1/2; ABB's eCatalog lists 7.46 x 3.53 x 3.18 (body, not flange).
# The row keeps the catalog envelope: the deeper figure is the conservative cavity read.
CARLON_BH353A = Product(tag="PROD-CARLON-BH353A", brand="Carlon", model="BH353A",
                        name="3-gang SuperBlue nail-on new-work box, 53 cu. in., 3-1/2 in. deep",
                        url="https://www.elliottelectric.com/P/Item/TAB/BH353A", source=_SOURCE)
CARLON_BH464A = Product(tag="PROD-CARLON-BH464A", brand="Carlon", model="BH464A",
                        name="4-gang SuperBlue nail-on new-work box, 64 cu. in., 3-1/2 in. deep",
                        url="https://www.elliottelectric.com/P/Item/TAB/BH464A", source=_SOURCE)

# Wall plates (notes/wiring_device_geometry.md §2): Leviton Q-1289 and the product drawings,
# 1 13/16" per gang. Midway is the default: a Lever Edge strap (1.78") wants it; a standard
# plate needs the strap's breakaway tab removed. Claro for the Diva (Lutron spec guide).
_PLATE_SOURCE = "Wiring device geometry pass, 2026-11-15 (notes/wiring_device_geometry.md)."
PLATE_PJ26_W = Product(tag="PROD-LEVITON-PJ26-W", brand="Leviton", model="PJ26-W",
    name="Midway Decora wall plate, 1-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-31144-Dimensional%20Data.JPG",
    source=_PLATE_SOURCE)
PLATE_PJ262_W = Product(tag="PROD-LEVITON-PJ262-W", brand="Leviton", model="PJ262-W",
    name="Midway Decora wall plate, 2-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-31171-Dimensional%20Data.JPG",
    source=_PLATE_SOURCE)
PLATE_PJ263_W = Product(tag="PROD-LEVITON-PJ263-W", brand="Leviton", model="PJ263-W",
    name="Midway Decora wall plate, 3-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-31176-Dimensional%20Data.JPG",
    source=_PLATE_SOURCE)
PLATE_PJ264_W = Product(tag="PROD-LEVITON-PJ264-W", brand="Leviton", model="PJ264-W",
    name="Midway Decora wall plate, 4-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-31181-Dimensional%20Data.JPG",
    source=_PLATE_SOURCE)
PLATE_80401_NW = Product(tag="PROD-LEVITON-80401-NW", brand="Leviton", model="80401-NW",
    name="Standard Decora wall plate, 1-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/LC_DOC_DDG_PNG_80401.png",
    source=_PLATE_SOURCE)
PLATE_80409_NW = Product(tag="PROD-LEVITON-80409-NW", brand="Leviton", model="80409-NW",
    name="Standard Decora wall plate, 2-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/80409.png",
    source=_PLATE_SOURCE)
PLATE_80411_NW = Product(tag="PROD-LEVITON-80411-NW", brand="Leviton", model="80411-NW",
    name="Standard Decora wall plate, 3-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-145705-Dimensional%20Data.gif",
    source=_PLATE_SOURCE)
PLATE_80412_NW = Product(tag="PROD-LEVITON-80412-NW", brand="Leviton", model="80412-NW",
    name="Standard Decora wall plate, 4-gang, white",
    url="https://www.leviton.com/content/dam/leviton/residential/product_documents/none/Document-29687-Dimensional%20Data.gif",
    source=_PLATE_SOURCE)
PLATE_CW_1_WH = Product(tag="PROD-LUTRON-CW-1-WH", brand="Lutron", model="CW-1-WH",
    name="Claro Decora wall plate, 1-gang, white",
    url="https://assets.lutron.com/a/documents/369682.pdf",
    source=_PLATE_SOURCE)
PLATE_CW_2_WH = Product(tag="PROD-LUTRON-CW-2-WH", brand="Lutron", model="CW-2-WH",
    name="Claro Decora wall plate, 2-gang, white",
    url="https://assets.lutron.com/a/documents/369682.pdf",
    source=_PLATE_SOURCE)
PLATE_CW_3_WH = Product(tag="PROD-LUTRON-CW-3-WH", brand="Lutron", model="CW-3-WH",
    name="Claro Decora wall plate, 3-gang, white",
    url="https://assets.lutron.com/a/documents/369682.pdf",
    source=_PLATE_SOURCE)
PLATE_CW_4_WH = Product(tag="PROD-LUTRON-CW-4-WH", brand="Lutron", model="CW-4-WH",
    name="Claro Decora wall plate, 4-gang, white",
    url="https://assets.lutron.com/a/documents/369682.pdf",
    source=_PLATE_SOURCE)
# KET1's round 6-20R beside a Decora duplex (owner, 2026-11-16): no Leviton plate pairs them.
PLATE_MULBERRY_32442 = Product(tag="PROD-MULBERRY-32442", brand="Mulberry", model="32442",
    name="2-gang thermoplastic wall plate, 1 single receptacle (1.405 in.) + 1 Decora/GFI, white",
    url="https://mulberrymetal.com/shop/wallplates/thermoplastic/2-gang-thermoplastic/2-gang-with-1-single-receptacle-opening-1-405-in-id-1-gfi-standard-size-thermoplastic-wallplate/",
    source=_PLATE_SOURCE)
PLATE_80704_W = Product(tag="PROD-LEVITON-80704-W", brand="Leviton", model="80704-W",
    name="Standard single-receptacle wall plate (1.406 in. hole), white",
    url="https://www.leviton.com/products/80704-w",
    source=_PLATE_SOURCE)

BOX_PRODUCTS = (PLATE_PJ26_W, PLATE_PJ262_W, PLATE_PJ263_W, PLATE_PJ264_W, PLATE_80401_NW, PLATE_80409_NW, PLATE_80411_NW, PLATE_80412_NW, PLATE_CW_1_WH, PLATE_CW_2_WH, PLATE_CW_3_WH, PLATE_CW_4_WH, PLATE_80704_W, PLATE_MULBERRY_32442,
                RACO_232, CARLON_BH353A, CARLON_BH464A, RACO_808C, RACO_809C, RACO_768, CARLON_B122A, CARLON_BH235A,
                CARLON_B520A, RACO_192, RACO_753, ARLINGTON_DVFR1W, AIRFOIL_1G, AIRFOIL_ROUND,
                RACO_674, RACO_862)

BOX_STANDARD = [
    BoxStandard(
        uid="BXDRVSHNW8", tag="BOX-STANDARD",
        surface_drop=inch(0.75),
        default_plate="midway",
        plates=(
            PlateRow(family="midway", openings=("decora",), product_ref="PROD-LEVITON-PJ26-W",
                     size=(inch(3.13), inch(4.88)), thickness=inch(0.25),
                     material_ref="device-white"),
            PlateRow(family="midway", openings=("decora", "decora"), product_ref="PROD-LEVITON-PJ262-W",
                     size=(inch(4.94), inch(4.88)), thickness=inch(0.25),
                     material_ref="device-white"),
            PlateRow(family="midway", openings=("decora", "decora", "decora"), product_ref="PROD-LEVITON-PJ263-W",
                     size=(inch(6.75), inch(4.88)), thickness=inch(0.25),
                     material_ref="device-white"),
            PlateRow(family="midway", openings=("decora", "decora", "decora", "decora"), product_ref="PROD-LEVITON-PJ264-W",
                     size=(inch(8.56), inch(4.88)), thickness=inch(0.25),
                     material_ref="device-white"),
            PlateRow(family="standard", openings=("decora",), product_ref="PROD-LEVITON-80401-NW",
                     size=(inch(2.75), inch(4.5)), thickness=inch(0.255),
                     material_ref="device-white"),
            PlateRow(family="standard", openings=("decora", "decora"), product_ref="PROD-LEVITON-80409-NW",
                     size=(inch(4.56), inch(4.5)), thickness=inch(0.255),
                     material_ref="device-white"),
            PlateRow(family="standard", openings=("decora", "decora", "decora"), product_ref="PROD-LEVITON-80411-NW",
                     size=(inch(6.375), inch(4.5)), thickness=inch(0.255),
                     material_ref="device-white"),
            PlateRow(family="standard", openings=("decora", "decora", "decora", "decora"), product_ref="PROD-LEVITON-80412-NW",
                     size=(inch(8.19), inch(4.5)), thickness=inch(0.255),
                     material_ref="device-white"),
            PlateRow(family="claro", openings=("decora",), product_ref="PROD-LUTRON-CW-1-WH",
                     size=(inch(2.94), inch(4.69)), thickness=inch(0.3),
                     material_ref="device-white"),
            PlateRow(family="claro", openings=("decora", "decora"), product_ref="PROD-LUTRON-CW-2-WH",
                     size=(inch(4.75), inch(4.69)), thickness=inch(0.3),
                     material_ref="device-white"),
            PlateRow(family="claro", openings=("decora", "decora", "decora"), product_ref="PROD-LUTRON-CW-3-WH",
                     size=(inch(6.56), inch(4.69)), thickness=inch(0.3),
                     material_ref="device-white"),
            PlateRow(family="claro", openings=("decora", "decora", "decora", "decora"), product_ref="PROD-LUTRON-CW-4-WH",
                     size=(inch(8.37), inch(4.69)), thickness=inch(0.3),
                     material_ref="device-white"),
            PlateRow(family="standard", openings=("single",),
                     product_ref="PROD-LEVITON-80704-W", size=(inch(2.75), inch(4.5)),
                     thickness=inch(0.22), material_ref="device-white"),
            PlateRow(family="standard", openings=("single", "decora"),
                     product_ref="PROD-MULBERRY-32442", size=(inch(4.57), inch(4.5)),
                     thickness=inch(0.07), material_ref="device-white"),
        ),
        rows=(
            BoxRow(mounting="surface", gangs=1, box_product_ref="PROD-RACO-232",
                   cover_product_ref="PROD-RACO-808C",
                   box_size=(inch(4), inch(4), inch(2.125)), designation="4 x 2-1/8 square",
                   cover_rise=inch(0.5)),
            BoxRow(mounting="surface", gangs=2, box_product_ref="PROD-RACO-232",
                   cover_product_ref="PROD-RACO-809C",
                   box_size=(inch(4), inch(4), inch(2.125)), designation="4 x 2-1/8 square",
                   cover_rise=inch(0.5)),
            BoxRow(mounting="flush", gangs=1, box_product_ref="PROD-CARLON-B122A",
                   box_size=(inch(2.25), inch(3.75), inch(3.5)), box_volume_in3=22.0,
                   material_ref="box-pvc-blue"),
            BoxRow(mounting="flush", gangs=2, box_product_ref="PROD-CARLON-BH235A",
                   box_size=(inch(4), inch(3.75), inch(3.5)), box_volume_in3=35.0,
                   material_ref="box-pvc-blue"),
            BoxRow(mounting="flush", gangs=3, box_product_ref="PROD-CARLON-BH353A",
                   box_size=(inch(5.875), inch(3.75), inch(3.5)), box_volume_in3=53.0,
                   internal_clamps=True, material_ref="box-pvc-blue"),
            BoxRow(mounting="flush", gangs=4, box_product_ref="PROD-CARLON-BH464A",
                   box_size=(inch(7.75), inch(3.875), inch(3.5)), box_volume_in3=64.0,
                   internal_clamps=True, material_ref="box-pvc-blue"),
            BoxRow(mounting="flush_raceway", gangs=1, box_product_ref="PROD-RACO-232",
                   cover_product_ref="PROD-RACO-768",
                   box_size=(inch(4), inch(4), inch(2.125)), designation="4 x 2-1/8 square",
                   cover_rise=inch(0.625)),
            BoxRow(mounting="surface", gangs=1, use="luminaire", box_product_ref="PROD-RACO-192",
                   cover_product_ref="PROD-RACO-753",
                   box_size=(inch(4), inch(4), inch(1.563)), designation="4 x 1-1/2 square",
                   cover_rise=inch(0.0625)),
            BoxRow(mounting="flush", gangs=1, use="luminaire-round",
                   box_product_ref="PROD-CARLON-B520A", shape="round",
                   box_size=(inch(4), inch(4), inch(2.25)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue"),
            BoxRow(mounting="flush", gangs=1, use="recessed",
                   box_product_ref="PROD-ARLINGTON-DVFR1W",
                   box_size=(inch(4.2), inch(6.698), inch(3.875)), box_volume_in3=21.0,
                   block_profile="2x4", plate_included=True),
            # A pocket box: surface on the pocket's back (resolve/device_boxes._pocket).
            BoxRow(mounting="surface", gangs=1, use="handy", box_product_ref="PROD-RACO-674",
                   cover_product_ref="PROD-RACO-862",
                   box_size=(inch(2.125), inch(4), inch(2.125)), box_volume_in3=16.5,
                   internal_clamps=False, plate_included=True),
            BoxRow(mounting="flush", gangs=1, use="air-sealed",
                   box_product_ref="PROD-LESSCO-AIRFOIL-1G",
                   box_size=(inch(2.5), inch(4), inch(3.5)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue"),
            BoxRow(mounting="flush", gangs=1, use="air-sealed-luminaire-round",
                   box_product_ref="PROD-LESSCO-AIRFOIL-ROUND", shape="round",
                   box_size=(inch(4), inch(4), inch(2.25)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue"),
        ),
    ),
]
