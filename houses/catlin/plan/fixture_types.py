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

from library.placeables import front_zone
from plan.bath2_vanity_types import BATH2_VANITY_48
from plan.fixture_types_wc import WC_AND_SHOWER_TYPES
from plan.kitchen_sink_types import KITCHEN_SINK_32_SINGLE
from typehaus.model import FixturePart, FixtureType, Mount, MountKind, Service, ServicePort, PortCertainty, inch, m

# The Kohler K-1130-W1-0 Underscore, RM-M-BATH2 (plan/products.py carries brand + model).
# A DROP-IN, not FX-TUB-60's alcove box: it drops through a framed deck onto a 1"-2" mortar
# bed and the rim carries no load. So the footprint is the RIM; the room is occupied by the
# deck box SL-M-TUBDK / W-M-TUBDK-W / -S in plan/storeys/main.py.
#
# ``Service.POWER_120`` is the Bask heated surface, cord-and-plug on a dedicated 120 V 15 A
# Class A GFCI circuit (CKT-BATH2-TUB). Actual draw is 65 W.
KOHLER_UNDERSCORE_6032 = FixtureType(
    tag="FX-KOHLER-UNDERSCORE-6032",
    name="Underscore drop-in bath with Bask heated surface",
    footprint=(inch(60), inch(32)),
    height=inch(21),
    plan_symbol="kohler-underscore-6032",
    basin=False,
    product_ref="PROD-KOHLER-1130-W1-0",
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT,
                     Service.POWER_120}),
    source="Kohler specification sheet K-1130-W1, US-CA 10-14-2026, read 2026-10-22: "
           "60 x 32 x 21 in., basin top 55 1/8 x 27 1/8, bottom 42 x 23 1/2, water depth "
           "17 1/8 in., 81 gal, 81 lb, minimum floor load 59 lb/ft2, cutout 59 1/2 x 31 1/2, "
           "1 1/2 in. end drain 12 9/16 in. from the end (K-7272 Clearflo, PROD-KOHLER-7272). "
           "Bask: 120 V / 0.5 A / 65 W; 20 x 15 in. minimum access panel at the heater end.",
)

# The trim shares the tub's services; its host relation permits the spout over the rim.
MOEN_ALIGN_ROMAN = FixtureType(
    tag="FX-MOEN-ALIGN-ROMAN",
    name="Align T393 three-hole Roman tub filler, chrome",
    footprint=(inch(15.9375), inch(9.03125)),
    height=inch(6.40625),
    plan_symbol="roman-tub-filler",
    basin=False,
    product_ref="PROD-MOEN-T393",
    source="Moen t393sp.pdf Rev. 1/18, read 2026-10-22: 10 in. handle centres, "
           "7 29/32 in. overall reach, outlet centre 7 1/4 in. from hole, "
           "3 23/32 in. outlet underside, 6 13/32 in. overall height. "
           "Outward closed levers reach 2 31/32 in. from each handle centre; "
           "2 1/4 in. spout and 1 15/16 in. handle bases. "
           "https://assets.moen.com/shared/docs/product-specifications/t393sp.pdf",
)

# RM-M-BATH2's vanity is the floating SEKTION in plan/bath2_vanity_types.py (2026-10-22).

# A real washing bowl replaces the 9 7/8"-projection Vero hand-rinse basin.
# The drawing gives 145 mm china height; the shared symbol adds its 0.14 m faucet band.
DCODE_WALL_BASIN = FixtureType(
    tag="FX-DURAVIT-DCODE-070545", name="D-Code wall-mounted basin, 15 3/8 x 8 1/2 in. bowl",
    footprint=(inch(17.75), inch(13.375)), height=m(0.285),
    plan_symbol="lavatory-wall-hung", basin=True,
    mount=Mount(kind=MountKind.WALL, elevation=m(0.7186)),
    product_ref="PROD-DURAVIT-07054500002",
    parts=(FixturePart(role="faucet", product_ref="PROD-DURAVIT-B21010001U10"),
           FixturePart(role="trap", product_ref="PROD-DEARBORN-707BN-1")),
    ports=(
        ServicePort(tag="DCODE-DRAIN", service=Service.DRAIN,
                    position=(inch(1.125), inch(9.9475), inch(20) - m(0.7186)),
                    certainty=PortCertainty.EXACT),
        ServicePort(tag="DCODE-HOT", service=Service.WATER_HOT,
                    position=(inch(4.125), inch(6.5625), inch(24) - m(0.7186)),
                    certainty=PortCertainty.EXACT),
        ServicePort(tag="DCODE-COLD", service=Service.WATER_COLD,
                    position=(inch(-5.375), inch(6.5625), inch(24) - m(0.7186)),
                    certainty=PortCertainty.EXACT),
    ),
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(inch(17.75), inch(13.375), inch(30),
                           "lavatory front clearance"),),
    source='Duravit US D-Code 07054500002, read 2026-10-21: white, wall-mounted, '
           '17 3/4 x 13 3/8 x 5 3/4 in. china; interior 15 3/8 x 8 1/2 in.; '
           'one central faucet hole, overflow, glazed underside, cUPC listed. '
           '34 in. rim above finished floor. Drawing 1266560: fixing holes 240 mm apart, '
           '55 mm below rim. See notes/main_bath1_basin_spec.md for support and fittings. '
           'https://pro.duravit.us/pro/html/default/402880943a1b6e1b013a1bd282eb0051.us-en.html'
           '?ncat=washbasins&nser=7120&product=94764',
)

FIXTURE_TYPES = (KOHLER_UNDERSCORE_6032, MOEN_ALIGN_ROMAN, BATH2_VANITY_48, DCODE_WALL_BASIN,
                 KITCHEN_SINK_32_SINGLE,
                 *WC_AND_SHOWER_TYPES)
