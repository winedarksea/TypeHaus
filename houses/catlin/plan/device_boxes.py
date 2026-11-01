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
#   * recessed — the fridge and freezer receptacles: an Arlington IN BOX, plug inside the wall.
# Covers and rings are not credited a volume: none of these is marked with one.

from typehaus import BoxRow, BoxStandard, Product, inch

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
# Arlington catalog page Q-3, read 2026-11-01: 21.0 in3, trim 4.200 x 6.698", 3.875" deep,
# new work (screws to the stud), duplex plate included; "plugs don't extend past the wall".
ARLINGTON_DVFR1W = Product(tag="PROD-ARLINGTON-DVFR1W", brand="Arlington", model="DVFR1W",
                           name="IN BOX recessed 1-gang box, trim and duplex plate, 21 cu. in.",
                           url="https://www.aifittings.com/media/catalog-pages/Q-3.pdf",
                           source="Geometry review C5-E2, owner 2026-11-01.")

BOX_PRODUCTS = (RACO_232, RACO_808C, RACO_809C, RACO_768, CARLON_B122A, CARLON_BH235A,
                RACO_192, RACO_753, ARLINGTON_DVFR1W)

BOX_STANDARD = [
    BoxStandard(
        uid="BXDRVSHNW8", tag="BOX-STANDARD",
        surface_drop=inch(0.75),
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
                   box_size=(inch(2.25), inch(3.75), inch(3.5)), box_volume_in3=22.0),
            BoxRow(mounting="flush", gangs=2, box_product_ref="PROD-CARLON-BH235A",
                   box_size=(inch(4), inch(3.75), inch(3.5)), box_volume_in3=35.0),
            BoxRow(mounting="flush_raceway", gangs=1, box_product_ref="PROD-RACO-232",
                   cover_product_ref="PROD-RACO-768",
                   box_size=(inch(4), inch(4), inch(2.125)), designation="4 x 2-1/8 square"),
            BoxRow(mounting="surface", gangs=1, use="luminaire", box_product_ref="PROD-RACO-192",
                   cover_product_ref="PROD-RACO-753",
                   box_size=(inch(4), inch(4), inch(1.5)), designation="4 x 1-1/2 square",
                   cover_rise=inch(0.0625)),
            BoxRow(mounting="flush", gangs=1, use="recessed",
                   box_product_ref="PROD-ARLINGTON-DVFR1W",
                   box_size=(inch(4.2), inch(6.698), inch(3.875)), box_volume_in3=21.0),
        ),
    ),
]
