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

This file was reintroduced on 2026-08-29 for the drop-in bath. An earlier
``plan/fixture_types.py`` existed and was deleted in the ``3d3973a`` dedupe when its
contents duplicated the library; nothing here duplicates anything.
"""

from __future__ import annotations

from library.placeables._zones import front_zone
from typehaus.model import FixtureType, Service, inch

# The Kohler K-5713-W1-0 Underscore, RM-M-BATH2 (plan/products.py carries brand + model).
#
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

# RM-M-BATH2's vanity (2026-08-29), replacing the FX-KITCHEN-SINK-33 that stood in for it.
#
# ** THE THING IT REPLACES WAS A DOUBLE-BOWL KITCHEN SINK. ** Not a metaphor for one: the
# instance carried ``type_ref="FX-KITCHEN-SINK-33"`` and a 27" wall mount to drag the
# library's kitchen deck down to lavatory height. It billed as a kitchen sink, drew the
# ``kitchen-sink`` symbol with TWO bowls on the bathroom plan, and gave the room no cabinet
# at all -- 33" x 22" of counter with nothing under it. The owner wants one basin and as
# much drawer and shelf as 54" can hold, so this is a vanity type rather than a sink type.
#
# 54" x 21" is set by the room, not by a catalogue: the west wall gives ** 57 1/4" ** of
# clear run between W-M-BDN1's finish face (y=13'-2 3/8") and the start of FX-M-BATH2-WC's
# 21" P2705.1 front clearance (y=17'-11 5/8"), and 54" leaves 3 1/4" of that rather than
# butting a cabinet into a code envelope. ** Measure that run off the WALLS' finish faces
# and never off `Room.clear_face` ** -- the latter is inset from the wall AXIS, which on
# this 13 7/8" exterior wall reads six inches out. 21" is the standard manufactured vanity
# depth (KraftMaid, and the 20"-23" band every mass-market line sits in); the counter
# overhangs it to 22".
#
# ``height`` is 41 1/2" and that is NOT the counter -- this file's library twin explains
# why: a fixture's height is OVERALL including the spout, and ``_deck_height`` subtracts a
# fixed 0.14 m faucet band. 41.5" - 5.512" = **35.99"**, which is the 36" comfort-height
# counter the owner chose (the same plane as the kitchen, and inside NKBA Guideline 7's
# 32"-43" band) to within a hundredth of an inch. The band is metric and the height is in
# inches, so no round inch value lands on 36.000"; 41 1/2" is the closest orderable one.
# Change this number and the counter moves -- it is not a round one by accident.
#
# ** ONE BASIN, AND THE STORAGE IS THE POINT. ** 24" four-drawer bank at the SOUTH end,
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
# y 18'-10 1/2"..21'-1 1/2". That leaves 14 1/8" of bare wall between this cabinet's north
# end and the opening -- comfortable, though the window's 3'-0" sill IS the same plane as
# the 36" counter, so a cabinet that ever runs north has no height to hide in.
#
# The front clearance is the 21" IRC P2705.1 minimum, not NKBA's recommended 30". The room
# gives 30 5/8" of aisle between this face and the tub deck's west face, so the
# recommendation IS met in fact -- but authoring 30" as a REQUIRED zone would make a
# guideline read as code in every clearance finding, which it is not.
BATH2_VANITY_54 = FixtureType(
    tag="FX-VANITY-54-SINGLE",
    name='Vanity, 54" single basin with drawer bank',
    footprint=(inch(54), inch(21)),
    height=inch(41.5),
    plan_symbol="vanity",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(54), inch(21), inch(21), "lavatory front clearance"),),
    source="RM-M-BATH2 vanity, owner selection 2026-08-29; cabinetry by owner. 54 x 21 in. "
           "carcass, 22 in. counter with a 1 in. overhang, finished counter 36 in. "
           "(comfort height, NKBA Bathroom Planning Guideline 7 allows 32-43 in.). ONE "
           "basin: a single rectangular undermount, model 20 x 15 1/2 in. overall with a "
           "17 1/4 x 13 in. cutout and a 5 1/4 in. bowl (Kohler Verticyl K-2882 class). "
           "Cabinet breakdown: 24 in. bank of four drawers at the south end (6/9/9/9 in. "
           "fronts, 19 in. boxes) + 30 in. sink base at the north end with a pair of doors "
           "and one interior shelf (SB-M-BATH2-VAN), the trap kept high and tight to the "
           "wall so the base stays usable. Six drawers plus the shelf is the storage this "
           "type exists for; a wider single-bowl unit will not fit the west wall.",
)

FIXTURE_TYPES = (KOHLER_UNDERSCORE_6036, BATH2_VANITY_54)
