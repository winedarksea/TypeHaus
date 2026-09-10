"""Catlin plumbing-fixture catalog — the named products, where the owner has chosen one.

NOT ``# haus: editable``: like ``appliance_types``/``lighting_types`` these are catalog type
definitions rather than placed instances, and ``FixtureType.needs`` is a ``frozenset``,
which the editable dialect forbids. The movable instances that reference these tags live in
``plan/fixtures.py``, which is editable, so UI drags still round-trip.

``library/placeables/fixtures.py`` stays what it is: a planning-allowance catalog whose own
header says "final fixture selection by owner." This file is that selection, and it rides
beside the allowances rather than replacing them — the lavatory, the water closets and the
shower are all still correctly generic. Tags are disjoint (``FX-KOHLER-*`` against the
library's ``FX-TUB-*``/``FX-SHOWER-*``), which ``integrity.duplicate_catalog_tag`` proves.
Nothing here duplicates the library.
"""

from __future__ import annotations

from library.placeables._zones import front_zone
from plan.fixture_types_wc import WC_AND_SHOWER_TYPES
from typehaus.model import FixtureType, Service, inch

# The Kohler K-5713-W1-0 Underscore, RM-M-BATH2 (plan/products.py carries brand + model).
# ** THIS IS A DROP-IN, AND THAT IS THE WHOLE REASON IT IS NOT FX-TUB-60. ** The library's
# allowance is a three-sided *alcove* tub — a 60x30 box whose own skirt is the finished
# face. This bath has no skirt. It drops through a hole in a framed deck and sits on a
# 1"-2" mortar bed on the subfloor, and Kohler is explicit that the rim carries no load
# (max 1/8" spacers under it). So the footprint below is the RIM, the thing that laps the
# deck — not the space the fixture occupies in the room, which is the deck box
# SL-M-TUBDK / W-M-TUBDK-W / -S in plan/storeys/main.py.
#
# 59 11/16" is the spec drawing's dimension; the marketing name rounds it to 59 3/4".
# ``height`` is the bath's own 21", so a `Mount.elevation` of 0 puts its bottom on the
# subfloor where the mortar bed actually holds it — the rim then lands at 21", and the
# deck's finished top is set 1" higher (the bed) in the SL-M-TUBDK elevation arithmetic.
#
# ``Service.POWER_120`` is the Bask heated surface and is NOT decoration: it is what makes
# the fixture schedule and `mep` see an electrical requirement on a *bathtub*. The service
# is a dedicated 120 V 15 A Class A GFCI circuit (CKT-BATH2-TUB) whose receptacle must sit
# behind the bath and within 24" of the power supply — the bath is cord-and-plug, factory
# wired, so there is no hardwired junction box to locate. Actual draw is 65 W.
KOHLER_UNDERSCORE_6036 = FixtureType(
    tag="FX-KOHLER-UNDERSCORE-6036",
    name="Underscore drop-in bath with Bask heated surface",
    footprint=(inch(59.6875), inch(35.75)),
    height=inch(21),
    plan_symbol="tub",
    product_ref="PROD-KOHLER-5713-W1-0",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT,
                     Service.POWER_120}),
    source="Kohler specification sheet K-5713-W1_spec_US-CA rev. 2-28-2024, read "
           "2026-08-29: 59 11/16 x 35 3/4 x 21 in. overall, basin top 55 9/16 x 28 3/8, "
           "water depth 16 5/16 in., 72.017 gal, 91 lb empty, minimum floor load "
           "49.3 lb/ft2, centre 1 1/2 in. drain (K-7272 Clearflo, PROD-KOHLER-7272). "
           "Bask heated surface: 120 V / 1.1 A / 65 W, dedicated 120 V 15 A Class A GFCI "
           "circuit required, outlet behind the bath within 24 in. of the power supply.",
)

# RM-M-BATH2's vanity, replacing a borrowed FX-KITCHEN-SINK-33 that billed as a kitchen
# sink, drew a two-bowl symbol on the bathroom plan, and gave the room no cabinet at all.
# The owner wants one basin and as much drawer and shelf as the wall can hold, so this is a
# vanity type rather than a sink type.
#
# ** 54" WAS WRONG, AND IT WAS WRONG AGAINST THE WRONG CODE (revised 2026-09-06). ** The
# original sizing measured the run to the start of FX-M-BATH2-WC's **21" IRC P2705.1** front
# clearance at y=17'-11 5/8" and reported 3 1/4" of slack. But this file's own header says
# why IRC P2705.1 has no force in Minnesota -- Minn. R. 1309.0010 subp. 3.D deletes IRC
# chapters 25-33 -- and the envelope actually drawn and actually enforced is **UPC 402.5's
# 24"**, which is three inches nearer. Against that, 54" cleared by ** 0.24" **, and the
# instant the water closet became a real product rather than a 28"-deep allowance the cabinet
# stood inside a code envelope. TOTO's one-piece skirted bowls run 28 1/2" (Nexus) to 30"
# (Carlyle II); there is no real toilet the 54" survives.
#
# It went to 51" x 21" on 2026-09-06, clearing the Carlyle II's envelope by 1 3/4" instead
# of a quarter inch, and then to ** 48" x 18" on 2026-09-09 ** for the aisle rather than for
# the envelope: 48" is on the stock width ladder where 51" never was, 18" is the house's own
# -SHALLOW depth (the boxed big-box combos measure 18.6"-18.75"), and the pair leaves
# 4 1/4" to the water closet's envelope. The three inches of length come out of the drawer
# bank; the 30" sink base is untouched. ** Measure that run off the WALLS' finish faces
# and never off `Room.clear_face` ** -- the latter is inset from the wall AXIS, which on
# this 13 7/8" exterior wall reads six inches out. The counter overhangs the carcass to 19".
#
# ``height`` is 41 1/2" and that is NOT the counter -- this file's library twin explains
# why: a fixture's height is OVERALL including the spout, and ``_deck_height`` subtracts a
# fixed 0.14 m faucet band. 41.5" - 5.512" = **35.99"**, which is the 36" comfort-height
# counter the owner chose (the same plane as the kitchen, and inside NKBA Guideline 7's
# 32"-43" band) to within a hundredth of an inch. The band is metric and the height is in
# inches, so no round inch value lands on 36.000"; 41 1/2" is the closest orderable one.
# Change this number and the counter moves -- it is not a round one by accident.
#
# ** ONE BASIN, AND THE STORAGE IS THE POINT. ** 21" four-drawer bank at the SOUTH end,
# 30" sink base at the NORTH end with the basin over it, so the counter runs unbroken from
# the drawer bank to the basin rim rather than being cut in half by a second bowl. The
# basin centreline lands at y=16'-3 5/8" -- 39" off W-M-BDN1's face, comfortably past
# NKBA G5's recommended 20" to a sidewall. The sink base's interior shelf is authored as
# SB-M-BATH2-VAN in plan/millwork.py, because a shelf the owner will stand things on is
# worth billing; the drawer boxes are not modelled (the engine has no drawer vocabulary)
# and live in the cabinet breakdown below and in prices.toml.
#
# WIN-M-BATH2 is not in the way, and the margin is bigger than a first read of the storey
# file suggests: its comment quotes "y 19'-8"" for a ``from_node`` offset that is the
# opening's NEAR EDGE, and W-M-W3 is authored north-to-south, so the 27" unit actually runs
# y 18'-10 1/2"..21'-1 1/2". Since the 2026-09-09 shuffle this cabinet ends at y=17'-2 3/8"
# and the gap is 20 1/8", though the window's 3'-0" sill IS the same plane as the 36"
# counter, so a cabinet that ever runs north has no height to hide in.
#
# The front clearance is the 21" IRC P2705.1 minimum, not NKBA's recommended 30", and the
# room now beats the recommendation across the whole cabinet: 33 11/16" of aisle to the
# shower for the south 36" of the run and 27 1/16" to the tub deck's access panel for the
# north 12". The BASIN sits in the wide half deliberately (see the type's `source`). Authoring 30" as a
# REQUIRED zone would make a guideline read as code in every clearance finding, which it
# is not -- but the numbers above are what the owner asked the room to hold.
BATH2_VANITY_48 = FixtureType(
    tag="FX-VANITY-48-SHALLOW",
    name='Vanity, 48" single basin with drawer bank',
    footprint=(inch(48), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(48), inch(18), inch(21), "lavatory front clearance"),),
    source="RM-M-BATH2 vanity, owner selection 2026-08-29, narrowed 54 in. to 51 in. on "
           "2026-09-06 when the water closet became a real product, and 51 x 21 in. to "
           "48 x 18 in. on 2026-09-09 to open the room's approach. 48 x 18 in. carcass, "
           "22 in. counter with a 1 in. overhang, finished counter 36 in. (comfort height, "
           "NKBA Bathroom Planning Guideline 7 allows 32-43 in.). ONE basin: a single "
           "rectangular undermount, 20 x 15 1/2 in. overall with a 17 1/4 x 13 in. cutout "
           "and a 5 1/4 in. bowl -- Kohler Caxton K-20000-0 (PROD-KOHLER-K-20000), chosen "
           "over the Verticyl K-2882 this first named, whose vertical sides and tight "
           "corner radii are exactly what stops a cloth reaching the corner in one pass. "
           "Cabinet breakdown: 30 in. sink base at the SOUTH end with a pair of doors "
           "and 18 in. bank of three drawers at the north end (6/6/6 in. fronts, 16 in. "
           "boxes). The ends were swapped on 2026-09-09: the tub deck stands 26 in. off "
           "this face at the room's north end and the shower stands 41 in. off it at the "
           "south, so the basin belongs south and the drawers take the pinch. "
           "One interior shelf (SB-M-BATH2-VAN), the trap kept high and tight to the "
           "wall so the base stays usable. QUARTZ with an undermount rather than the "
           "integral solid-surface top the four small vanities take: this and the hall "
           "hall-bath unit are the two busiest decks and the two that are fabricated "
           "rather than bought boxed."
)

# ---------------------------------------------------------------------------
# THE OTHER FIVE BATHROOMS' VANITIES (2026-08-30)
# ---------------------------------------------------------------------------
#
# ** EVERY OTHER BATHROOM IN THIS HOUSE HAD A BASIN AND NO CABINET. ** The library's
# ``FX-LAV-24`` and ``FX-LAV-COMPACT`` are bare bowls -- a 24"x20" and an 18"x14" footprint
# with no carcass, no doors and nowhere to put anything. Six instances of them stood in five
# bathrooms. These five types replace them with real cabinets, sized to the run each room
# actually has rather than to a catalogue.
#
# ** THE TAG SUFFIX IS THE DEPTH, AND IT IS LOAD-BEARING. ** ``-SINGLE`` is 21" deep, the
# cabinet-line standard (Menards Quality One, KraftMaid, Diamond NOW are all 21" nominal
# with a 22" top). ``-SHALLOW`` is 18" deep and is NOT a premium product: the cheap big-box
# combos -- the ones that arrive boxed with the top and bowl already on them -- measure
# 18.6"-18.75" deep, so 18" is what is on the pallet. Three of these rooms cannot take 21"
# and lose nothing by it. (RM-M-BATH2's ``FX-VANITY-48-SHALLOW`` above joined them on
# 2026-09-09, from 51" x 21".)
#
# ** WIDTHS ARE THE CHEAP STOCK LADDER: 24 / 30 / 36 / 48 / 60. ** Those five are stocked
# by every big-box and every builder cabinet line, assembled, no lead time. 18", 42", 54"
# and 66" are the one-SKU-or-special-order band, and 21"/27"/33" exist only in semi-custom
# 3"-increment lines. Widening a room's vanity past its stock size costs more than the
# storage is worth, so where a wall gave an awkward number the width was rounded DOWN to
# the ladder rather than made to fit.
#
# ** THE 21" FRONT ZONE IS A DESIGN CONVENTION HERE, NOT A MINNESOTA CODE MINIMUM. **
# Say it that way, because the obvious cite is wrong twice over. Minnesota does not use the
# IRC's plumbing chapters at all -- Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33
# and 1309.0307 sends fixtures to Minn. R. ch. 4714, which adopts the 2018 UPC -- so IRC
# P2705.1's 21" has no force here. And UPC 402.5, which does, says "the clear space in front
# of any water closet or BIDET shall be not less than 24 inches": it never mentions a
# lavatory. (An earlier draft of this comment cited a UPC 402.5 "Exception 1" giving
# lavatories 21" in dwelling units. That exception appears only in Washington's UPC insert
# pages -- it is a Washington amendment, not base UPC, and it does not apply in Minnesota.
# See plan/fixtures.py's RM-M-BATH1 header, which works the same chain the other way.)
#
# So under Minnesota's plumbing code a lavatory has NO front-clearance requirement, and 21"
# is what this house chooses to hold anyway -- it is IRC's number, it is the floor NKBA's
# Guideline 4 builds its recommended 30" on, and a vanity you cannot stand in front of is a
# bad vanity whether or not an inspector says so. The WATER CLOSETS are a different matter:
# theirs IS 24" and it is enforced, because the house sets `active_code_profile="MN/IRC"`
# and `_water_closet_required_clearance` encodes 24". Every placement below was checked by
# hand against those 24"/15" envelopes as well as against its own 21".
#
# ** THE ZONES RESOLVE AS *RECOMMENDED*, WHICH IS NOT WHAT A READER EXPECTS. **
# ``front_zone`` builds a zone at the default policy, and that default is RECOMMENDED, so an
# encroachment here reports WARN/UNKNOWN rather than FAIL. That is why these were also
# checked by hand against the walls' own layer polygons. Note that the water-closet zones in
# this house are inert entirely (they carry a ``code_profile`` and the house sets no
# ``active_code_profile``), so NOTHING in the engine is enforcing the 15"/24" bands the
# placements below were designed around -- they are held by arithmetic and by the tests in
# ``test_catlin_bathroom_vanities.py``, not by a check.
#
# ** STORAGE IS DOORS PLUS A SHELF, NOT DRAWERS, AND THAT IS A COST DECISION. ** At equal
# width a drawer base runs about 1.5x a door base (Home Decorators Cabinetry, 21" wide:
# sink base VSB2121L $551.61 against drawer base VBD2121 $818.48 -- +$267 on one cabinet).
# Under a sink the top drawer is a false front anyway, because the trap is in the way, so
# the premium buys even less there than it does in a kitchen. Each of these carries a
# full-depth adjustable interior shelf instead (the ``SB-*-VAN`` banks in plan/millwork.py,
# cut from the owner's own oak), which roughly doubles usable volume for the price of a
# board. Only the 48" hall-bath unit gets a drawer bank, because it is the one wall wide
# enough to hold a 30" sink base AND an 18" bank without giving up the sink base.

# RM-M-BATH1, the small main bath: 62" x 42" between finish faces, with a wall-hung water
# closet already eating the west half of the north wall. 24" is what is left between that
# bowl's 15" side band (x=41.41") and the east wall's face (x=68.62") -- 27.21", so a 24"
# cabinet fits with 3.2" to spare and a 30" one does not. 18" deep is forced: at 21" the
# 21" front zone would reach y=316.39" against a south wall face at 313.63".
VANITY_24_SHALLOW = FixtureType(
    tag="FX-VANITY-24-SHALLOW",
    name='Vanity, 24" single basin, shallow',
    footprint=(inch(24), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    product_ref="PROD-SWAN-CONTOUR",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(24), inch(18), inch(21), "lavatory front clearance"),),
    source='Small-bath vanity, owner selection 2026-08-30. 24" x 18" carcass, 25" x 19" '
           'one-piece SOLID-SURFACE top with an integral coved bowl, finished counter 36" '
           '(comfort height; NKBA Bathroom Planning Guideline 7 allows 32"-43"). One sink '
           'base, two doors, one full-depth adjustable shelf (SB-M-BATH1-VAN). This is the '
           'big-box combo tier -- Glacier Bay GB24P2 class, 25" x 18.6", cabinet and top '
           'boxed together for roughly the price of the top alone -- which is why 18" is '
           'the cheap depth here and not a compromise. Replaces an 18" x 14" wall-hung '
           'basin that had no cabinet at all.',
)

# RM-S-VANITY, the double-vanity alcove off the second-storey landing, and RM-S-SUITEBATH's
# west half. 30" is the stock size that fits both. Shallow because the alcove is only 40.62"
# deep: at 18" the front zone stops at y=273.62" against a north face at y=272.0", and at
# 21" it would overrun by 1.38".
VANITY_30_SHALLOW = FixtureType(
    tag="FX-VANITY-30-SHALLOW",
    name='Vanity, 30" single basin, shallow',
    footprint=(inch(30), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    product_ref="PROD-SWAN-CONTOUR",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(30), inch(18), inch(21), "lavatory front clearance"),),
    source='Vanity, owner selection 2026-08-30. 30" x 18" carcass, 31" x 19" '
           'one-piece SOLID-SURFACE top with an integral coved bowl, finished counter 36". One '
           'sink base, two doors, one full-depth adjustable shelf. TWO of these stand side '
           'by side in RM-S-VANITY under one 61" double top -- which is how a 60" double '
           'vanity is actually built and bought, and it keeps two drains, two traps and '
           'two lavatories in the fixture schedule rather than collapsing them into one.',
)

# RM-S-SUITEBATH's south wall. 31.76" between the water closet's 15" side band (x=149.81")
# and the tub-shower's west face (x=181.57"), so 30" is the largest stock width that fits.
# The room is 71" deep, so this one keeps the standard 21".
VANITY_30_SINGLE = FixtureType(
    tag="FX-VANITY-30-SINGLE",
    name='Vanity, 30" single basin',
    footprint=(inch(30), inch(21)),
    height=inch(41.5),
    plan_symbol="vanity",
    product_ref="PROD-SWAN-CONTOUR",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(30), inch(21), inch(21), "lavatory front clearance"),),
    source='Primary-suite bath vanity, owner selection 2026-08-30. 30" x 21" carcass '
           '(Menards Quality One VDB3021 / KraftMaid vanity sink base class), 31" x 22" '
           'one-piece SOLID-SURFACE top with an integral coved bowl, finished counter 36". One '
           'sink base, two doors, one full-depth adjustable shelf (SB-S-SUITEBATH-VAN).',
)

# RM-B-BATH (basement, 86.62" x 39.61") and RM-A-STUBATH (attic guest bath). Both have far
# more wall than 36" -- the constraint in each is elsewhere. In the basement it is
# D-B-BATH's swing: the door's arc reaches the east wall, and a 21"-deep cabinet is caught
# by it at every position on that wall while an 18"-deep one clears from the north face on.
# In the attic the vanity is held east of the west-wall receptacle and west of the shower.
VANITY_36_SHALLOW = FixtureType(
    tag="FX-VANITY-36-SHALLOW",
    name='Vanity, 36" single basin, shallow',
    footprint=(inch(36), inch(18)),
    height=inch(41.5),
    plan_symbol="vanity",
    product_ref="PROD-SWAN-CONTOUR",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(36), inch(18), inch(21), "lavatory front clearance"),),
    source='Vanity, owner selection 2026-08-30. 36" x 18" carcass, 37" x 19" '
           'one-piece SOLID-SURFACE top with an integral coved bowl, finished counter 36". One '
           'sink base, two doors, one full-depth adjustable shelf. 36" is the widest of '
           'the three volume stock sizes (24/30/36) and the last one before the price step '
           'up to 48". Used twice: RM-B-BATH and RM-A-STUBATH.',
)

# RM-S-BATH1, the second-storey hall bath. The east wall gives 46.5" of usable run -- bounded
# north by D-S-BATH1's swing arc and south by FURN-S-BATH1-SHELF, the shower's return panel.
# 48" fits that, but only just and only as a real arc rather than its bounding box: pushed as
# far north as the swing allows the cabinet runs y 345.75"..393.75", scribing to the shelf
# with 0.75" to spare. It is the only vanity in the house wide enough to carry a drawer bank
# without giving up a full-size sink base, so it is the only one that gets one.
VANITY_48_SINGLE = FixtureType(
    tag="FX-VANITY-48-SINGLE",
    name='Vanity, 48" single basin with drawer bank',
    footprint=(inch(48), inch(21)),
    height=inch(41.5),
    plan_symbol="vanity",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(48), inch(21), inch(21), "lavatory front clearance"),),
    source='Hall-bath vanity, owner selection 2026-08-30, top revised 2026-09-06. 48" x '
           '21" carcass, 49" x 22" QUARTZ top with a Kohler Caxton K-20000-0 undermount '
           '(PROD-KOHLER-K-20000) -- this and the 51" are the two busiest decks and the '
           'only two that are fabricated rather than bought boxed. Finished counter 36". '
           'Cabinet breakdown: 30" sink base at the SOUTH end with two doors and one '
           'full-depth adjustable shelf (SB-S-BATH1-VAN), plus an 18" three-drawer bank at '
           'the NORTH end. The drawer bank is the ~1.5x-per-inch cabinet in the house and '
           'is bought here only because 48" leaves room for it beside a full sink base; '
           'every other bathroom takes doors and a shelf instead.',
)

# ---------------------------------------------------------------------------
# THE TOPS CHANGED, AND IT IS THE BEST CLEANABILITY-PER-DOLLAR MOVE IN THE HOUSE (2026-09-06)
# ---------------------------------------------------------------------------
#
# The integral-versus-undermount split above was right on the cleanability axis and is kept:
# a coved integral bowl has no caulk joint, no clip reveal and no silicone ring to mildew.
# ** WHAT WAS WRONG WAS THE MATERIAL. ** Cultured marble is a ~0.020" clear gelcoat over
# filled polyester -- hot hair tools scorch it permanently, it yellows in sun, and a refinish
# lays down a THINNER gelcoat than the original. Compression-moulded solid surface (Swan
# Contour, PROD-SWAN-CONTOUR) is the same integral coved bowl at the same price band in a
# HOMOGENEOUS material: a scratch or a scorch sands back to new instead of cutting through a
# skin, and its matte finish reads better against white oak and hides water spots.
#
# The 48" and 51" keep quartz with a Kohler Caxton K-20000-0 undermount (PROD-KOHLER-K-20000,
# chosen over the Verticyl K-2882 first specified: Verticyl's selling point is vertical sides
# and tight corner radii, which is exactly what stops a cloth reaching the corner in one
# pass). Those two are the busiest decks and the 51" is fabricated regardless, so they carry
# no ``product_ref`` -- a fabricated top is not a purchased SKU.
#
# ** ORDER EVERY TOP DRILLED SINGLE-HOLE, IN WRITING. ** All eight lavatory faucets are
# single-hole (Delta Arvo 15840LF-SP): one deck penetration instead of three, in the splash
# zone, cheaper in brushed nickel. Stock tops are drilled single-hole or 4" centerset at the
# factory and 8" widespread is a special-order drilling -- and FIELD-drilling a cast top
# chips it and voids its warranty. Swan Contour ships single-hole with 4"/8" knockouts you
# simply never break out; plugging holes with a deck plate afterwards defeats the whole point.

FIXTURE_TYPES = (KOHLER_UNDERSCORE_6036, BATH2_VANITY_48,
                 VANITY_24_SHALLOW, VANITY_30_SHALLOW, VANITY_30_SINGLE,
                 VANITY_36_SHALLOW, VANITY_48_SINGLE,
                 *WC_AND_SHOWER_TYPES)

