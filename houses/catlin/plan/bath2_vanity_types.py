"""RM-M-BATH2's vanity: two 15"-deep SEKTION wall frames hung as a floating box, AXSTAD
matte white fronts (the bed desk's), under a Corian Glacier White (or HI-MACS/Staron equal) top with a bonded
bowl from the deck's fabricator and lot (owner, 2026-10-22; notes/bath2_tub_deck_finish.md).

NOT ``# haus: editable``: ``FixtureType.needs`` is a ``frozenset``. The instance is
``FX-M-BATH2-SINK`` in plan/fixtures.py. Prices live in prices.toml.
"""

from __future__ import annotations

from library.placeables import front_zone

from typehaus.model import FixtureType, Footprint2D, Product, Service, inch, pt

# Every IKEA part below was read on IKEA US on 2026-10-22. SEKTION base frames are 24" deep,
# which the room cannot take; the 15" wall frames on the suspension rail can.
SEKTION_WALL_30_15_30 = Product(
    tag="PROD-IKEA-SEKTION-WALL-30-15-30", brand="IKEA", model="SEKTION 30x15x30 wall",
    sku="702.654.69", name='SEKTION white wall cabinet frame, 30 x 14 3/4 x 30"',
    url="https://www.ikea.com/us/en/p/sektion-wall-cabinet-white-70265469/",
    source="IKEA US listing, read 2026-10-22: $78; suspension rail and hinges sold separately.",
)
SEKTION_WALL_18_15_30 = Product(
    tag="PROD-IKEA-SEKTION-WALL-18-15-30", brand="IKEA", model="SEKTION 18x15x30 wall",
    sku="802.654.64", name='SEKTION white wall cabinet frame, 18 x 14 3/4 x 30"',
    url="https://www.ikea.com/us/en/p/sektion-wall-cabinet-white-80265464/",
    source="IKEA US listing, read 2026-10-22: $58; suspension rail and hinges sold separately.",
)
SEKTION_SUSPENSION_RAIL = Product(
    tag="PROD-IKEA-SEKTION-RAIL-84", brand="IKEA", model="SEKTION suspension rail 84",
    sku="602.615.27", name='SEKTION suspension rail, galvanized, 84"',
    url="https://www.ikea.com/us/en/p/sektion-suspension-rail-galvanized-60261527/",
    source="IKEA US listing, read 2026-10-22: $20; cut to the 48\" run.",
)
MAXIMERA_DRAWER_18_15 = Product(
    tag="PROD-IKEA-MAXIMERA-MEDIUM-18-15", brand="IKEA", model="MAXIMERA medium 18x15",
    sku="202.656.74", name='MAXIMERA medium drawer, white, 18 x 14 3/4"',
    url="https://www.ikea.com/us/en/p/maximera-drawer-medium-white-20265674/",
    source=("IKEA US listing, read 2026-10-22: $34; the 15\"-deep drawer IKEA sells for "
            "the wall frame (its 18x15x40 glass-door cabinet ships the low one, 502.656.58). "
            "No cut-down drawer is specified."),
)
AXSTAD_DOOR_15_30 = Product(
    tag="PROD-IKEA-AXSTAD-MATTE-15-30", brand="IKEA", model="AXSTAD matte white 15x30",
    sku="304.260.49", name='AXSTAD matte white door, 15 x 30"',
    url="https://www.ikea.com/us/en/p/axstad-door-matt-white-30426049/",
    source="IKEA US listing, read 2026-10-22: $86; UTRUSTA 110 deg hinges sold separately.",
)
AXSTAD_DRAWER_FRONT_18_10 = Product(
    tag="PROD-IKEA-AXSTAD-MATTE-18-10", brand="IKEA", model="AXSTAD matte white 18x10",
    sku="204.260.64", name='AXSTAD matte white drawer front, 18 x 10"',
    url="https://www.ikea.com/us/en/p/axstad-drawer-front-matte-white-20426064/",
    source="IKEA US listing, read 2026-10-22: $50; availability not shown, confirm at order.",
)
SOLID_SURFACE_LAV_BOWL = Product(
    tag="PROD-SS-LAV-16X13", brand="Generic", model="solid-surface undermount lavatory, 16 3/8 x 13 x 5",
    name="Solid-surface undermount lavatory bowl, 16 3/8 x 13 x 5 in., integral front overflow, seam-bonded to the top",
    source=("Basic generic shape (owner, 2026-10-22): any maker's solid-surface bowl in this envelope. "
            "Drawn to the Corian 810P sheet, Jan 2026 revision: 16 3/8 x 13 x 5 in. bowl "
            "(415 x 329 x 127 mm), integral front overflow; the Nov 2018 sheet reads "
            "16 1/2 x 13 1/8 x 5 1/2. Fits the 17 1/4 x 13 in. envelope the Caxton held. "
            "Bonded by the deck's fabricator in the same white lot. "
            "https://www.tools.corian.com/IMG/pdf/corian_lav_810p_new.pdf"),
)
BATH2_VANITY_PRODUCTS = (SEKTION_WALL_30_15_30, SEKTION_WALL_18_15_30, SEKTION_SUSPENSION_RAIL,
                         MAXIMERA_DRAWER_18_15, AXSTAD_DOOR_15_30, AXSTAD_DRAWER_FRONT_18_10,
                         SOLID_SURFACE_LAV_BOWL)

# ** 48 x 18 IS FIXED BY THE ROOM. ** 18" holds the 33 11/16" shower aisle, the 27 1/16" to
# the tub access panel and the water closet's UPC 402.5 envelope 4 1/4" off the north end
# (the 54"/51"/48" history is in DESIGN-LOG.md). The frames stand 2 1/4" off W-M-W3 on a
# ledger chase (trap and supplies behind the box), so the 14 3/4" frame plus 3/4" front
# lands at 17 3/4", under the 18" footprint.
#
# 30" sink frame with two 15x30 doors at the SOUTH end (basin where the aisle is widest),
# 18" frame with three 10" drawers at the north. Frame bottoms at 5 1/2" AFF, so the
# heated tile runs under the box and the 12 mm top finishes at 36".
#
# The bowl hole, in the type's local frame (x along the run, +y toward the wall): the bowl's
# 16 3/8 x 13 over the 30" sink frame, centred 9" south of the cabinet centre (y=14'-5 3/8",
# where the basin and FX-M-BATH2-SINK's drain have stood since 2026-09-09), with 3" behind
# it for the faucet.
#
# ``height`` is OVERALL with the spout: ``_deck_height`` takes a fixed 0.14 m faucet band
# off it, and 41 1/2" - 5.512" = 35.99", the 36" counter. Known approximation: the
# ``vanity`` symbol draws a toe kick where the real box floats 5 1/2" clear.
BATH2_VANITY_48 = FixtureType(
    tag="FX-VANITY-48-SEKTION",
    name='Vanity, 48" floating SEKTION, single basin with drawer bank',
    footprint=(inch(48), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    basin=True,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(48), inch(18), inch(21), "lavatory front clearance"),),
    countertop_cutout=Footprint2D(points=(
        pt(inch(-17.1875), inch(-7)), pt(inch(-0.8125), inch(-7)),
        pt(inch(-0.8125), inch(6)), pt(inch(-17.1875), inch(6)),
    )),
    product_ref=SEKTION_WALL_30_15_30.tag,
    source="RM-M-BATH2 vanity, owner selection 2026-10-22: SEKTION 30x15x30 (702.654.69) "
           "and 18x15x30 (802.654.64) wall frames on a suspension rail (602.615.27) over a "
           "2 1/4 in. ledger chase on W-M-W3, bottoms 5 1/2 in. AFF; two AXSTAD matte white "
           "15x30 doors (304.260.49) on the sink frame, three AXSTAD 18x10 fronts "
           "(204.260.64) on MAXIMERA medium 18x15 drawers (202.656.74). Corian Glacier "
           "White (or HI-MACS/Staron equal) top CT-M-BATH2-VANITY with a bonded 16 3/8 x 13 in. "
           "solid-surface bowl (PROD-SS-LAV-16X13). "
           "Bath2 faucet: chrome Arvo 15840LF (PROD-DELTA-15840LF); single hole. Fallback "
           "if the SEKTION parts cannot be bought as specified: IKEA GODMORGON, about "
           "18 1/2 in. deep, wall-hung, 31 1/2 in. sink + 15 3/4 in. drawer cabinet = "
           "47 1/4 in. Rejected: US HAVBACK (21 in. deep), Swanstone one-piece tops "
           "(22 in. deep, centred bowl).",
)
