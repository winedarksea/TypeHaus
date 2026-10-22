"""RM-M-BATH2's vanity: SEKTION wall cabinets hung as a floating box, AXSTAD matte white
fronts (the bed desk's), under a Corian Glacier White (or HI-MACS/Staron equal) top with a bonded
bowl from the deck's fabricator and lot (owner, 2026-10-22; notes/bath2_tub_deck_finish.md).

NOT ``# haus: editable``: ``FixtureType.needs`` is a ``frozenset``. The instance is
``FX-M-BATH2-SINK`` in plan/fixtures.py. Prices live in prices.toml.
"""

from __future__ import annotations

from library.placeables import front_zone

from typehaus.model import FixtureType, Footprint2D, Product, Service, inch, pt

# IKEA parts. The 36" listing (2 AXSTAD matte white doors) was read 2026-10-22; article numbers
# are read off the listing URL and marked to confirm at order. The 12" storage cabinet's
# AXSTAD matte white front is NOT yet read: the only 12x15x30 AXSTAD listing found is matte blue.
SEKTION_WALL_36_CAB = Product(
    tag="PROD-IKEA-SEKTION-WALL-36-2AXSTAD", brand="IKEA",
    model="SEKTION 36x15x30 wall, 2 AXSTAD matte white doors",
    name='SEKTION white wall cabinet, 36 x 14 3/4 x 30", two AXSTAD matte white doors',
    url="https://www.ikea.com/us/en/p/sektion-wall-cabinet-with-2-doors-white-axstad-matte-white-s89454945/",
    source="IKEA US listing, read 2026-10-22: $338; article 894.549.45 read off the listing URL, "
           "confirm at order. Suspension rail sold separately; hinges and shelves included.",
)
SEKTION_WALL_12_CAB = Product(
    tag="PROD-IKEA-SEKTION-WALL-12-AXSTAD", brand="IKEA",
    model="SEKTION 12x15x30 wall, AXSTAD matte white door",
    name='SEKTION white wall cabinet, 12 x 14 3/4 x 30", AXSTAD matte white door',
    source="IKEA US listing family read 2026-10-22: 12x15x30 SEKTION wall cabinets with AXSTAD "
           "fronts run $132 (matte blue, article 394.635.89) to $212 (high gloss). The matte "
           "white article is NOT yet read; $132 is the matte blue price, confirm the white "
           "article and price at order. Suspension rail sold separately.",
)
SEKTION_SUSPENSION_RAIL = Product(
    tag="PROD-IKEA-SEKTION-RAIL-84", brand="IKEA", model="SEKTION suspension rail 84",
    sku="602.615.27", name='SEKTION suspension rail, galvanized, 84"',
    url="https://www.ikea.com/us/en/p/sektion-suspension-rail-galvanized-60261527/",
    source="IKEA US listing, read 2026-10-22: $20; cut to the 48\" run.",
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
BATH2_VANITY_PRODUCTS = (SEKTION_WALL_36_CAB, SEKTION_WALL_12_CAB, SEKTION_SUSPENSION_RAIL,
                         SOLID_SURFACE_LAV_BOWL)

# ** 48 x 18 IS FIXED BY THE ROOM. ** 18" holds the 33 11/16" shower aisle, the 27 1/16" to
# the tub access panel and the water closet's UPC 402.5 envelope 4 1/4" off the north end
# (the 54"/51"/48" history is in DESIGN-LOG.md). The cabinets stand 2 1/4" off W-M-W3 on a
# ledger chase (trap and supplies behind the box), so the 14 3/4" carcass plus 3/4" front
# lands at 17 3/4", under the 18" footprint.
#
# 12" storage cabinet at the SOUTH end, 36" sink cabinet at the NORTH end (2026-10-22 revision,
# which replaced the 30" sink + 18" drawer split).
#
# The bowl hole, in the type's local frame (x along the run, -x south, +y toward the wall):
# the bowl's 16 3/8 x 13 CENTRED on the vanity (x=0), i.e. on the room's centreline y=15'-2 3/8",
# which is where FX-M-BATH2-SINK's drain sits. It lies inside the 36" sink cabinet (x -12..+24),
# clear of its south side by 3 13/16", with 3" behind it for the faucet.
#
# ``height`` is OVERALL with the spout: ``_deck_height`` takes a fixed 0.14 m faucet band
# off it, and 41 1/2" - 5.512" = 35.99", the 36" counter. Known approximation: the
# ``vanity`` symbol draws a toe kick where the real box floats 5 1/2" clear.
BATH2_VANITY_48 = FixtureType(
    tag="FX-VANITY-48-SEKTION",
    name='Vanity, 48" floating SEKTION, single basin, 12" storage + 36" sink cabinet',
    footprint=(inch(48), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    basin=True,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(48), inch(18), inch(21), "lavatory front clearance"),),
    countertop_cutout=Footprint2D(points=(
        pt(inch(-8.1875), inch(-7)), pt(inch(8.1875), inch(-7)),
        pt(inch(8.1875), inch(6)), pt(inch(-8.1875), inch(6)),
    )),
    product_ref=SEKTION_WALL_36_CAB.tag,
    source="RM-M-BATH2 vanity, owner selection 2026-10-22, revised: SEKTION 36x15x30 sink cabinet "
           "with two AXSTAD matte white doors (894.549.45, to confirm) at the north end and a "
           "12x15x30 storage cabinet with an AXSTAD matte white door at the south end, both on a "
           "suspension rail (602.615.27) over a 2 1/4 in. ledger chase on W-M-W3, bottoms 5 1/2 in. "
           "AFF; both carry AXSTAD matte white shelving (door-and-shelf storage, no drawers). "
           "Corian Glacier White (or HI-MACS/Staron equal) top CT-M-BATH2-VANITY with a bonded "
           "16 3/8 x 13 in. solid-surface bowl (PROD-SS-LAV-16X13), centred on the vanity. "
           "Bath2 faucet: chrome Arvo 15840LF (PROD-DELTA-15840LF); single hole. Fallback "
           "if the SEKTION parts cannot be bought as specified: IKEA GODMORGON, about "
           "18 1/2 in. deep, wall-hung, 31 1/2 in. sink + 15 3/4 in. drawer cabinet = "
           "47 1/4 in. Rejected: US HAVBACK (21 in. deep), Swanstone one-piece tops "
           "(22 in. deep, centred bowl).",
)
