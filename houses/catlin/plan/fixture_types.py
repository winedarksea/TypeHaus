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

FIXTURE_TYPES = (KOHLER_UNDERSCORE_6036,)
