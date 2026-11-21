# haus: editable
# Device boxes, declared once (decision #93): the engine derives each wall device's box from
# the face it lands on (resolve/device_boxes.py) and bills box plus cover/ring each.
#   * surface — bare basement concrete: RACO 232 4" square x 2 1/8" (30.3 in3, Table
#     314.16(A)) under a 1/2" raised industrial cover, fed by NM in a derived 3/4" EMT sleeve
#     from overhead (notes/basement_surface_wiring.md).
#   * flush — a framed cavity: a deep nonmetallic new-work box, which the owner prefers
#     because it is easier to make up.
#   * flush_raceway — a flush box an authored raceway or a floor-heat lead reaches: the steel
#     4" square (RACO 235, the 232 with a TS side bracket) with a 1-device ring, which clears
#     Schluter's 35 mm thermostat minimum.
#   * luminaire, surface — a wall light on concrete: RACO 192 4" square x 1 1/2" under a flat
#     RACO 753, so a 4 1/2" square sconce backplate covers it (geometry review C6-E10, owner
#     2026-11-01). The box sides stay in view: field-paint them to the wall.
#   * luminaire-round — the WAC Sprig sconces (marks J, J1): a 4" round box, what the plate is
#     slotted for and what the 4 3/8" canopy covers with 3/16" to spare all round.
#   * recessed — the fridge and freezer receptacles: an Arlington IN BOX, plug inside the wall.
#     Its new-work screws want wood (Q-3), and both boxes sit mid-bay, so each gets a flat
#     2x4 block behind it, stud to stud, derived from the row (geometry review M3-107).
#   * ceiling (decision #140) — a ceiling fixture or hardwired alarm head: a 4" octagon,
#     2 1/8" deep, on a 16-24" bar hanger (the Kidde plates screw to a 4" octagon); a fan
#     takes the RACO 929 fan-rated brace box; through RM-S-PLANT's membrane, the air-sealed
#     rows. A ceiling receptacle takes the general flush row.
#   * fan, surface — the porch fan under FS-SG-BALCONY's bare joists: a Bell PRCF57550BZ
#     weatherproof fan box screwed under the joist over it (notes/porch_fan_box.md).
#   * mounts (decision #149, notes/box_supports.md) — every row names its `support`: nail-on
#     boxes are seated against a stud face; ceiling bars span joist to joist; a `box_use=
#     "bracket"` device holds its station on a RACO 601 + Arlington SL18 SliderBar.
# Covers and rings are not credited a volume: none of these is marked with one.
# The blue nonmetallic boxes name box-pvc-blue; steel rows stay galvanized (material_ref None).

from typehaus import BoxRow, BoxStandard, BoxSupport, PlateRow, Product, inch

_SOURCE = "Owner decision 2026-10-28, notes/basement_surface_wiring.md."

RACO_232 = Product(tag="PROD-RACO-232", brand="RACO", model="232",
                   name="4 in. square box, 2-1/8 in. deep, welded, 1/2 and 3/4 in. KOs",
                   url="https://www.hubbell.com/raco/en/Products/232", source=_SOURCE)
# The flush_raceway box (decision #149): the plain 232 has no bracket, so its TS-bracket twin.
# RACO-235 sheet: 4" square x 2-1/8", 30.3 in3, TS side-mount bracket with gauging tabs and
# nailing spurs, 7.01" overall.
RACO_235 = Product(tag="PROD-RACO-235", brand="RACO", model="235",
                   name="4 in. square box, 2-1/8 in. deep, welded, TS side-mount bracket",
                   url="https://hubbellcdn.com/specsheet/RACO-8235-SPEC-EN.pdf",
                   source="Hubbell RACO-235/8235 spec sheet; notes/box_supports.md.")
# The bracket alternative (decision #149): where a box must stay mid-bay (centred over a
# mirror, a symmetric pair, clear of a cabinet end), an Arlington SliderBar SL18 across the
# bay ("Works with Studs 12" to 18" on-center", instruction sheet; "Can mount a steel box via
# the pilot holes on the bar", catalog page) carries a RACO 601: 3 x 2 x 3-1/2 gangable
# switch box, 18.0 cu in, NMSC L clamps (spec sheet). Arlington's own SLB101 (17.0 cu in)
# is too small for a through-fed 12 AWG device. Bar section unpublished; drawn representative.
ARLINGTON_SL18 = Product(tag="PROD-ARLINGTON-SL18", brand="Arlington", model="SL18",
                         name="SLIDERBAR adjustable box mounting bar, studs 12-18 in. o.c.",
                         url="https://www.aifittings.com/media/instruction-sheets/SL18.pdf",
                         source="Arlington SL18 instruction sheet, spec sheet and catalog page; notes/box_supports.md.")
RACO_601 = Product(tag="PROD-RACO-601", brand="RACO", model="601",
                   name="3 x 2 in. gangable switch box, 3-1/2 in. deep, NMSC clamps, 18.0 cu. in.",
                   url="https://hubbellcdn.com/specsheet/RACO-601-SPEC-EN.pdf",
                   source="Hubbell RACO-601 spec sheet; notes/box_supports.md.")
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

# RM-S-SUITE's plates, Sun Gold to match its Chevron supply (owner, 2026-11-19). Sizes are
# assumed standard (unpublished); a standard plate needs the Lever Edge strap's tab removed.
_REGGIO_SOURCE = "Reggio steel switch plate; Sun Gold is a listed finish (floorregisters-n-vents.com/reggio-steel-switch-plate). Size and thickness unconfirmed, assumed standard."
PLATE_REGGIO_2SPB_SG = Product(tag="PROD-REGGIO-2SPB-SG", brand="Reggio Register Co.",
    model="2SPB", name="Steel Single Decora wall plate, 1-gang, Sun Gold",
    url="https://www.reggioregister.com/products/2spb", source=_REGGIO_SOURCE)
PLATE_REGGIO_6SPB_SG = Product(tag="PROD-REGGIO-6SPB-SG", brand="Reggio Register Co.",
    model="6SPB", name="Steel Double Decora wall plate, 2-gang, Sun Gold",
    url="https://www.reggioregister.com/products/6spb", source=_REGGIO_SOURCE)

PLATE_REGGIO_1SPB_SG = Product(tag="PROD-REGGIO-1SPB-SG", brand="Reggio Register Co.",
    model="1SPB", name="Steel Single Toggle wall plate, 1-gang, Sun Gold",
    url="https://www.reggioregister.com/products/1spb", source=_REGGIO_SOURCE)

# Heavy-duty toggles' plates (owner, 2026-11-20). Hubbell SS1/SS2 sheets publish no size: SS1
# 2.87 x 4.5 is the distributor figure, SS2 assumed one gang pitch wider. Thickness is Kyle's
# published 5/32" for all three. Kyle SPSJS-T: toggle/Decora/toggle, 6 3/8 x 4 1/2, 430 SS.
_SS_SOURCE = "Heavy-duty toggles, owner 2026-11-20 (notes/workshop_receptacles.md)."
PLATE_HUBBELL_SS1 = Product(tag="PROD-HUBBELL-SS1", brand="Hubbell", model="SS1",
    name="Toggle wall plate, 1-gang, 302/304 stainless, brushed",
    url="https://hubbellcdn.com/specsheet/WIRING_SS1_spec.pdf", source=_SS_SOURCE)
PLATE_HUBBELL_SS2 = Product(tag="PROD-HUBBELL-SS2", brand="Hubbell", model="SS2",
    name="Toggle wall plate, 2-gang, 302/304 stainless, brushed",
    url="https://hubbellcdn.com/specsheet/WIRING_SS2_spec.pdf", source=_SS_SOURCE)
PLATE_KYLE_SPSJS_T = Product(tag="PROD-KYLE-SPSJS-T", brand="Kyle Switch Plates", model="SPSJS-T",
    name="3-gang wall plate, toggle/Decora/toggle, 430 stainless, satin",
    url="https://www.kyleswitchplates.com/toggle-decora-toggle-triple-wall-switch-plate-cover-stainless-steel/",
    source=_SS_SOURCE)

# Ceiling boxes (decision #140), retail listings read 2026-11-20; ESTIMATE until submittal.
_CEILING_SOURCE = "Ceiling boxes, decision #140 (2026-11-20)."
# Appleton FFS561LDNBH (Gexpro/Platt listings): 4" octagon, 2-1/8" deep, 21.5 in3, 16-24" bar
# hanger, fixture 70 lb, fan 35 lb. Its 35 lb fan listing is not relied on: fans take the 929.
APPLETON_FFS561LDNBH = Product(tag="PROD-APPLETON-FFS561LDNBH", brand="Appleton",
    model="FFS561LDNBH", name="4 in. octagon ceiling box, 2-1/8 in. deep, 21.5 cu. in., NM clamps, 16-24 in. bar hanger",
    url="https://www.gexpro.com/p/568232/appleton/2-1-8-deep-4-octagon-ceiling-box-with-hanger/687855001408/ffs561ldnbh",
    source=_CEILING_SOURCE)
# RACO 929 spec sheet (via search, RACO-929-SPEC-EN): 2-1/8" deep, 22.5 in3, fan 70 lb at 16 and
# 24" spans, fixture 210 lb at 16" (90 at 24"), brace slides 16-24". Drawn as a 4" round.
RACO_929 = Product(tag="PROD-RACO-929", brand="RACO", model="929",
    name="KWIK-BRACE fan support with 2-1/8 in. deep box, 22.5 cu. in., fan rated 70 lb",
    url="https://hubbellcdn.com/specsheet/RACO-929-SPEC-EN.pdf", source=_CEILING_SOURCE)
# Arlington FBR415F (aifittings.com, read 2026-11-20): vapor box, gasketed flange and KOs,
# 18.3 in3, 2.723" tall, fan 110 lb / fixture 150 lb at 16" o.c. (UL). The plant fan's box.
ARLINGTON_FBR415F = Product(tag="PROD-ARLINGTON-FBR415F", brand="Arlington", model="FBR415F",
    name="Non-metallic vapor fan/fixture box, gasketed flange, adjustable steel bracket, 18.3 cu. in.",
    url="https://www.aifittings.com/catalog/fan-fixture-boxes/non-metallic-vapor-box-with-adjustable-steel-bracket/FBR415F",
    source=_CEILING_SOURCE)

# The garden flood's junction box (`remote_box`, owner 2026-11-20): Bell 5361-0, 4" round,
# 1-1/2" deep, five 1/2" hubs, die-cast; 16 in3 is a retailer figure (Zoro), not read off a
# Hubbell sheet. Bell 5374-0 4" round blank cover, gasket and screws included.
BELL_5361_0 = Product(tag="PROD-BELL-5361-0", brand="Bell (Hubbell)", model="5361-0",
    name="Weatherproof round box, 4 in., 1-1/2 in. deep, five 1/2 in. outlets, 16 cu. in., gray",
    url="https://www.gexpro.com/p/51023/hubbell-raco-wp-round-box-4-depth-1-1-2-5-1-2-hubs-050169536100-5361-0",
    source="Gexpro listing (4 in. dia., 1-1/2 in. deep, (5) 1/2 in. outlets); 16 cu. in. per Zoro. CONFIRM the marked volume at order.")
BELL_5374_0 = Product(tag="PROD-BELL-5374-0", brand="Bell (Hubbell)", model="5374-0",
    name="4 in. round weatherproof blank cover, gasket and screws, gray",
    url="https://www.hubbell.com/bell/en/c/5374-0/p/2140990", source="Hubbell product page")

# The porch fan's box (owner, 2026-11-20): FS-SG-BALCONY is bare joists, so the box hangs
# from the joist over the fan. Bell spec sheets BELL-PRCF57550BZ-SPEC-EN (REV 8/2026) and
# PRCF57550BZ (2019): polycarbonate, NEMA 3R, UL listed, 1.5" deep, 4.28" wide, 7.5" with its
# galvanized bracket, cubic capacity 16 (unit unprinted: in3), fan 70 lb, fixture 150 lb, mounts
# parallel, perpendicular or 45 deg to a joist, five 3/4" threaded hubs (no clamps), rain collar.
BELL_PRCF57550BZ = Product(tag="PROD-BELL-PRCF57550BZ", brand="Bell (Hubbell)", model="PRCF57550BZ",
    name="Outdoor Comforts weatherproof ceiling fan/luminaire box, 16 cu. in., fan 70 lb, bronze",
    url="https://hubbellcdn.com/specsheet/BELL-PRCF57550BZ-SPEC-EN.pdf",
    source="Hubbell spec sheets BELL-PRCF57550BZ-SPEC-EN and PRCF57550BZ; retail at Menards and Lowe's. notes/porch_fan_box.md.")

# Box mounts (decision #149, notes/box_supports.md). Ear and bar sections the datasheets do not
# dimension are drawn representative; ranges are the listed ones, on the basis each states.
# A Carlon nail-on box: captive nails through molded ears on one side, nailed to the stud
# face, the front left 1/2" proud of the stud for the board (ear size unpublished).
NAIL_ON = BoxSupport(kind="stud_side", section=(inch(1), inch(0.125)), offset=inch(0.5))
# RACO 235: the 232's box with a TS side bracket, 7" overall, flush to the stud face.
TS_BRACKET = BoxSupport(kind="stud_side", section=(inch(1.5), inch(0.0625)),
                        offset=inch(0.625), length=inch(7))
# Appleton NBH: a telescoping flat bar, 16-24" o.c., the box hung under it.
APPLETON_BAR = BoxSupport(kind="joist_span", span=(inch(16), inch(24)), span_basis="centres",
                          section=(inch(0.5), inch(0.0625)), offset=inch(2.125))
# RACO 929: two telescoping rectangular channels, "fits 16-24 in. o.c.", flanged ends.
RACO_BRACE = BoxSupport(kind="joist_span", span=(inch(16), inch(24)), span_basis="centres",
                        section=(inch(0.875), inch(0.75)), offset=inch(2.5))
# Arlington FBR415F: an adjustable plated-steel bracket "for joists or rafters 16-24 in. on
# centers", toothed end tabs, two #12 screws each end.
ARLINGTON_BRACKET = BoxSupport(kind="joist_span", span=(inch(16), inch(24)),
                               span_basis="centres", section=(inch(0.75), inch(0.0625)),
                               offset=inch(2.723))
# Screwed under the member over the point: the Bell fan box's 7.5" bracket, the 5361's lugs.
BELL_FAN_BRACKET = BoxSupport(kind="member_under", section=(inch(1.25), inch(0.0625)),
                              length=inch(7.5))
# Arlington SL18: a slotted channel stud face to stud face, the box screwed to its face.
SLIDERBAR = BoxSupport(kind="stud_span", span=(inch(12), inch(18)), span_basis="centres",
                       section=(inch(2.375), inch(0.0625)), offset=inch(3.5),
                       product_ref="PROD-ARLINGTON-SL18")
BELL_LUGS = BoxSupport(kind="member_under", section=(inch(0.75), inch(0.125)),
                       length=inch(5))
BOX_PRODUCTS = (BELL_PRCF57550BZ, BELL_5361_0, BELL_5374_0, APPLETON_FFS561LDNBH, RACO_929, ARLINGTON_FBR415F,
                PLATE_REGGIO_1SPB_SG, PLATE_REGGIO_2SPB_SG, PLATE_REGGIO_6SPB_SG,
                PLATE_HUBBELL_SS1, PLATE_HUBBELL_SS2, PLATE_KYLE_SPSJS_T,
                PLATE_PJ26_W, PLATE_PJ262_W, PLATE_PJ263_W, PLATE_PJ264_W, PLATE_80401_NW, PLATE_80409_NW, PLATE_80411_NW, PLATE_80412_NW, PLATE_CW_1_WH, PLATE_CW_2_WH, PLATE_CW_3_WH, PLATE_CW_4_WH, PLATE_80704_W, PLATE_MULBERRY_32442,
                RACO_232, RACO_235, ARLINGTON_SL18, RACO_601, CARLON_BH353A, CARLON_BH464A, RACO_808C, RACO_809C, RACO_768, CARLON_B122A, CARLON_BH235A,
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
            PlateRow(family="reggio-sungold", openings=("decora",),
                     product_ref="PROD-REGGIO-2SPB-SG", size=(inch(2.75), inch(4.5)),
                     thickness=inch(0.06), material_ref="reggio-sun-gold"),
            PlateRow(family="reggio-sungold", openings=("decora", "decora"),
                     product_ref="PROD-REGGIO-6SPB-SG", size=(inch(4.56), inch(4.5)),
                     thickness=inch(0.06), material_ref="reggio-sun-gold"),
            PlateRow(family="reggio-sungold", openings=("toggle",),
                     product_ref="PROD-REGGIO-1SPB-SG", size=(inch(2.75), inch(4.5)),
                     thickness=inch(0.06), material_ref="reggio-sun-gold"),
            PlateRow(family="stainless", openings=("toggle",), product_ref="PROD-HUBBELL-SS1",
                     size=(inch(2.87), inch(4.5)), thickness=inch(0.156),
                     material_ref="plate-stainless"),
            PlateRow(family="stainless", openings=("toggle", "toggle"),
                     product_ref="PROD-HUBBELL-SS2", size=(inch(4.68), inch(4.5)),
                     thickness=inch(0.156), material_ref="plate-stainless"),
            PlateRow(family="stainless", openings=("toggle", "decora", "toggle"),
                     product_ref="PROD-KYLE-SPSJS-T", size=(inch(6.375), inch(4.5)),
                     thickness=inch(0.156), material_ref="plate-stainless"),
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
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
            BoxRow(mounting="flush", gangs=2, box_product_ref="PROD-CARLON-BH235A",
                   box_size=(inch(4), inch(3.75), inch(3.5)), box_volume_in3=35.0,
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
            BoxRow(mounting="flush", gangs=3, box_product_ref="PROD-CARLON-BH353A",
                   box_size=(inch(5.875), inch(3.75), inch(3.5)), box_volume_in3=53.0,
                   internal_clamps=True, material_ref="box-pvc-blue",
                   support=NAIL_ON),
            BoxRow(mounting="flush", gangs=4, box_product_ref="PROD-CARLON-BH464A",
                   box_size=(inch(7.75), inch(3.875), inch(3.5)), box_volume_in3=64.0,
                   internal_clamps=True, material_ref="box-pvc-blue",
                   support=NAIL_ON),
            BoxRow(mounting="flush_raceway", gangs=1, box_product_ref="PROD-RACO-235",
                   cover_product_ref="PROD-RACO-768",
                   box_size=(inch(4), inch(4), inch(2.125)), designation="4 x 2-1/8 square",
                   cover_rise=inch(0.625),
                   support=TS_BRACKET),
            BoxRow(mounting="surface", gangs=1, use="luminaire", box_product_ref="PROD-RACO-192",
                   cover_product_ref="PROD-RACO-753",
                   box_size=(inch(4), inch(4), inch(1.563)), designation="4 x 1-1/2 square",
                   cover_rise=inch(0.0625)),
            BoxRow(mounting="flush", gangs=1, use="luminaire-round",
                   box_product_ref="PROD-CARLON-B520A", shape="round",
                   box_size=(inch(4), inch(4), inch(2.25)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
            # A box that must hold its station mid-bay: on a stud-to-stud bar (device box_use).
            BoxRow(mounting="flush", gangs=1, use="bracket", box_product_ref="PROD-RACO-601",
                   box_size=(inch(2), inch(3), inch(3.5)), designation="3 x 2 x 3-1/2 device",
                   internal_clamps=True, support=SLIDERBAR),
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
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
            # Ceiling boxes (decision #140).
            BoxRow(mounting="flush", gangs=1, use="ceiling",
                   box_product_ref="PROD-APPLETON-FFS561LDNBH", shape="octagon",
                   box_size=(inch(4), inch(4), inch(2.125)),
                   designation="4 x 2-1/8 round/octagonal", rated_load_lb=70.0,
                   support=APPLETON_BAR),
            BoxRow(mounting="flush", gangs=1, use="fan", box_product_ref="PROD-RACO-929",
                   shape="round", box_size=(inch(4), inch(4), inch(2.125)),
                   box_volume_in3=22.5, fan_rated=True, rated_load_lb=210.0,
                   support=RACO_BRACE),
            BoxRow(mounting="flush", gangs=1, use="air-sealed-fan",
                   box_product_ref="PROD-ARLINGTON-FBR415F", shape="round",
                   box_size=(inch(4), inch(4), inch(2.723)), box_volume_in3=18.3,
                   fan_rated=True, rated_load_lb=150.0, material_ref="box-pvc-blue",
                   support=ARLINGTON_BRACKET),
            BoxRow(mounting="flush", gangs=1, use="air-sealed-ceiling",
                   box_product_ref="PROD-LESSCO-AIRFOIL-ROUND", shape="round",
                   box_size=(inch(4), inch(4), inch(2.25)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
            # A bare concrete ceiling (none today): the wall light's drawn box and flat cover.
            BoxRow(mounting="surface", gangs=1, use="ceiling", box_product_ref="PROD-RACO-192",
                   cover_product_ref="PROD-RACO-753",
                   box_size=(inch(4), inch(4), inch(1.563)), designation="4 x 1-1/2 square",
                   cover_rise=inch(0.0625)),
            # A self-mounting wet fitting's junction box (`remote_box`), on the framing beside it.
            BoxRow(mounting="surface", gangs=1, use="weatherproof",
                   box_product_ref="PROD-BELL-5361-0", cover_product_ref="PROD-BELL-5374-0",
                   shape="round", box_size=(inch(4), inch(4), inch(1.5)), box_volume_in3=16.0,
                   cover_rise=inch(0.25),
                   support=BELL_LUGS),
            # A fan under a bare deck: hung from the joist over it, the canopy covers it.
            BoxRow(mounting="surface", gangs=1, use="fan",
                   box_product_ref="PROD-BELL-PRCF57550BZ", shape="round",
                   box_size=(inch(4.28), inch(4.28), inch(1.5)), box_volume_in3=16.0,
                   internal_clamps=False, fan_rated=True, rated_load_lb=150.0,
                   material_ref="box-pvc-bronze",
                   support=BELL_FAN_BRACKET),
            BoxRow(mounting="flush", gangs=1, use="air-sealed-luminaire-round",
                   box_product_ref="PROD-LESSCO-AIRFOIL-ROUND", shape="round",
                   box_size=(inch(4), inch(4), inch(2.25)), box_volume_in3=20.0,
                   material_ref="box-pvc-blue",
                   support=NAIL_ON),
        ),
    ),
]
