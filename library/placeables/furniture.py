"""Starter furniture catalog — sizes from ``plans/furniture_size_reference.md``.

Every type names a ``plan_symbol``, so it draws as a real plan glyph and masses as a boxy
multi-colour object without needing an imported product file. Dimensions are the reference's
*average* size, authored with ``ft(feet, inches)`` so the source reads as the drawing does.

The four original tags (``FURN-SOFA-84``, ``FURN-QUEEN-BED``, ``FURN-DINING-6``,
``FURN-DESK-48``) are kept stable — any already-placed instance still resolves.
"""

from __future__ import annotations

from typehaus.model import (Footprint2D, FurnitureType, ft, inch, m, pt)
from typehaus.model.placeable_symbols.furniture import sectional_points

from library.placeables._zones import front_zone, side_zone, surround_zone

REFERENCE = "plans/furniture_size_reference.md (US residential averages)"

# --- Living room ------------------------------------------------------------------------

STANDARD_SOFA = FurnitureType(
    tag="FURN-SOFA-84", name="Standard sofa", footprint=(ft(7), ft(2, 11)), height=ft(2, 10),
    plan_symbol="sofa", source=REFERENCE,
    clearances=(front_zone(ft(7), ft(2, 11), ft(2, 6), "walk path in front of seating"),),
)
LOVESEAT = FurnitureType(
    tag="FURN-LOVESEAT-60", name="Loveseat", footprint=(ft(5), ft(2, 11)), height=ft(2, 10),
    plan_symbol="loveseat", source=REFERENCE,
    clearances=(front_zone(ft(5), ft(2, 11), ft(2, 6), "walk path in front of seating"),),
)
# The first catalog use of ``footprint_shape``: a sectional is not a rectangle, and its L is
# generated from the same function the glyph draws, so outline and symbol cannot disagree.
_SECTIONAL_SIZE = (ft(9, 2), ft(7, 1))
SECTIONAL = FurnitureType(
    tag="FURN-SECTIONAL-L", name="L-shaped sectional", footprint=_SECTIONAL_SIZE,
    height=ft(2, 10), plan_symbol="sectional", source=REFERENCE,
    footprint_shape=Footprint2D(points=tuple(
        pt(m(x), m(y)) for x, y in sectional_points(_SECTIONAL_SIZE[0].meters,
                                                    _SECTIONAL_SIZE[1].meters))),
)
ARMCHAIR = FurnitureType(
    tag="FURN-ARMCHAIR-35", name="Armchair", footprint=(ft(2, 11), ft(2, 11)),
    height=ft(2, 11), plan_symbol="armchair", source=REFERENCE,
)
ROCKING_CHAIR = FurnitureType(
    tag="FURN-ROCKING-CHAIR-30", name="Rocking chair", footprint=(ft(2, 6), ft(3)),
    height=ft(3, 2), plan_symbol="armchair", source=REFERENCE,
)
COFFEE_TABLE = FurnitureType(
    tag="FURN-COFFEE-48", name="Coffee table", footprint=(ft(4), ft(2)), height=ft(1, 6),
    plan_symbol="coffee-table", source=REFERENCE,
)
END_TABLE = FurnitureType(
    tag="FURN-END-22", name="End table", footprint=(ft(1, 10), ft(1, 10)), height=ft(2),
    plan_symbol="end-table", source=REFERENCE,
)
MEDIA_CONSOLE = FurnitureType(
    tag="FURN-MEDIA-60", name="Media console", footprint=(ft(5), ft(1, 6)), height=ft(2),
    plan_symbol="media-console", storage=True, source=REFERENCE,
)
# TV sizes are quoted W x H x D; the footprint is W x D and the stated H is the height.
TV_65 = FurnitureType(
    tag="FURN-TV-65", name='65" television', footprint=(inch(56.5), inch(14.5)),
    height=inch(33.9), plan_symbol="tv", source=REFERENCE,
)
TV_98 = FurnitureType(
    tag="FURN-TV-98", name='98" television', footprint=(inch(85.3), inch(16.5)),
    height=inch(50.1), plan_symbol="tv", source=REFERENCE,
)

# --- Bedroom ----------------------------------------------------------------------------

# ``height`` is the true overall height of the object, not a mattress-top planning envelope:
# the headboard has to mass correctly, and the IFC prism and the 3D box read the same number.
_BED_HEIGHT = ft(3, 4)


def _bed_clearances(width, depth):
    """Compact side access both sides plus foot access — how a bed is actually used."""
    return (side_zone(width, depth, ft(1, 6), "bed side access", sign=1),
            side_zone(width, depth, ft(1, 6), "bed side access", sign=-1),
            front_zone(width, depth, ft(1, 6), "bed foot access"))


QUEEN_BED = FurnitureType(
    tag="FURN-QUEEN-BED", name="Queen bed", footprint=(ft(5, 4), ft(7)), height=_BED_HEIGHT,
    plan_symbol="bed", source=REFERENCE, clearances=_bed_clearances(ft(5, 4), ft(7)),
)
KING_BED = FurnitureType(
    tag="FURN-BED-KING", name="King bed", footprint=(ft(6, 8), ft(7)), height=_BED_HEIGHT,
    plan_symbol="bed", source=REFERENCE, clearances=_bed_clearances(ft(6, 8), ft(7)),
)
FULL_BED = FurnitureType(
    tag="FURN-BED-FULL", name="Full bed", footprint=(ft(4, 9), ft(6, 7)), height=_BED_HEIGHT,
    plan_symbol="bed", source=REFERENCE, clearances=_bed_clearances(ft(4, 9), ft(6, 7)),
)
TWIN_BED = FurnitureType(
    tag="FURN-BED-TWIN", name="Twin bed", footprint=(ft(3, 6), ft(6, 7)), height=_BED_HEIGHT,
    plan_symbol="bed", source=REFERENCE, clearances=_bed_clearances(ft(3, 6), ft(6, 7)),
)
DRESSER = FurnitureType(
    tag="FURN-DRESSER-60", name="Dresser", footprint=(ft(5), ft(1, 8)), height=ft(3),
    plan_symbol="dresser", storage=True, source=REFERENCE,
    clearances=(front_zone(ft(5), ft(1, 8), ft(2), "drawer swing"),),
)
CHEST = FurnitureType(
    tag="FURN-CHEST-34", name="Chest of drawers", footprint=(ft(2, 10), ft(1, 7)),
    height=ft(4, 2), plan_symbol="chest", storage=True, source=REFERENCE,
    clearances=(front_zone(ft(2, 10), ft(1, 7), ft(1, 10), "drawer swing"),),
)
# A free-standing wardrobe — the closet a bedroom without a closet gets. 48" x 24" x 78" is
# the standard two-door armoire: 24" deep is what a hanger needs front-to-back, and 78" is
# the tallest a case can be and still pass under an 80" door head on its way into the room.
#
# No clearance zone, unlike DRESSER and CHEST: those swing drawers, and this is specified
# with sliding/bypass doors precisely because the rooms it serves have no 24" of floor to
# spare in front of it. A hinged-door wardrobe would want ``front_zone(..., ft(2), ...)``
# and should be a separate type rather than a silent change to this one.
WARDROBE_48 = FurnitureType(
    tag="FURN-WARDROBE-48", name="Wardrobe (sliding door)", footprint=(ft(4), ft(2)),
    height=ft(6, 6), plan_symbol="tall-cabinet-double", storage=True, source=REFERENCE,
)
NIGHTSTAND = FurnitureType(
    tag="FURN-NIGHTSTAND-24", name="Nightstand", footprint=(ft(2), ft(1, 4)), height=ft(2, 2),
    plan_symbol="nightstand", storage=True, source=REFERENCE,
)

# --- Dining -----------------------------------------------------------------------------

# The chair-use zone exists to be stood in by these — naming them makes a table and the chairs
# tucked at it one furniture group, so the correct arrangement stops reporting as a conflict
# while a sofa parked in the same zone still does (→ resolve/placeable_groups).
DINING_CHAIR_TAG = "FURN-DINING-CHAIR"

SIX_SEAT_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-6", name="Six-seat dining table", footprint=(ft(6), ft(3)), height=ft(2, 6),
    plan_symbol="dining-table", source=REFERENCE,
    clearances=(surround_zone(ft(6), ft(3), ft(3), "chair-use zone",
                              occupant_types=(DINING_CHAIR_TAG,)),),
)
# The next size up, and the one a room with circulation on all four sides can carry: 8' gives
# three 30" settings a side, 42" of depth gives a serving spine down the middle. It is an
# eight-*place* table — the two ends are settings too — but a plan is free to leave the end
# chairs out, and an open-plan dining zone usually should: an end chair pulled out is what
# blocks the aisle past the table.
EIGHT_SEAT_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-8", name="Eight-seat dining table", footprint=(ft(8), ft(3, 6)),
    height=ft(2, 6), plan_symbol="dining-table", source=REFERENCE,
    clearances=(surround_zone(ft(8), ft(3, 6), ft(3), "chair-use zone",
                              occupant_types=(DINING_CHAIR_TAG,)),),
)
ROUND_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-ROUND-48", name="Round four-seat dining table", footprint=(ft(4), ft(4)),
    height=ft(2, 6), plan_symbol="round-table", source=REFERENCE,
    clearances=(surround_zone(ft(4), ft(4), ft(3), "chair-use zone",
                              occupant_types=(DINING_CHAIR_TAG,)),),
)
# A compact square table for two: the 3' footprint is large enough for a chess board and
# everyday work, while keeping the same apron-and-leg 2D/3D family as the dining tables.
TWO_PERSON_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-2-36", name="Two-person dining table", footprint=(ft(3), ft(3)),
    height=ft(2, 6), plan_symbol="dining-table", source=REFERENCE,
    clearances=(surround_zone(ft(3), ft(3), ft(3), "chair-use zone",
                              occupant_types=(DINING_CHAIR_TAG,)),),
)
# No pull-out zone of its own: a dining chair lives inside the table's chair-use zone by
# definition, and giving it a second one only reports the set conflicting with itself.
DINING_CHAIR = FurnitureType(
    tag=DINING_CHAIR_TAG, name="Dining chair", footprint=(ft(1, 8), ft(1, 10)),
    height=ft(3, 2), plan_symbol="dining-chair", source=REFERENCE,
)

# --- Home office ------------------------------------------------------------------------

OFFICE_CHAIR_TAG = "FURN-OFFICE-CHAIR"

WRITING_DESK = FurnitureType(
    tag="FURN-DESK-48", name="Writing desk", footprint=(ft(4), ft(2)), height=ft(2, 6),
    plan_symbol="desk", source=REFERENCE,
    clearances=(front_zone(ft(4), ft(2), ft(3), "desk chair pull-out",
                           occupant_types=(OFFICE_CHAIR_TAG, "FURN-DESK-CHAIR")),),
)
OFFICE_CHAIR = FurnitureType(
    tag=OFFICE_CHAIR_TAG, name="Office chair", footprint=(ft(2, 2), ft(2, 2)),
    height=ft(3, 2), plan_symbol="office-chair", source=REFERENCE,
)
DESK_CHAIR = FurnitureType(
    tag="FURN-DESK-CHAIR", name="Desk chair", footprint=(ft(1, 8), ft(1, 10)),
    height=ft(3, 2), plan_symbol="dining-chair", source=REFERENCE,
)
BOOKCASE = FurnitureType(
    tag="FURN-BOOKCASE-32", name="Bookcase", footprint=(ft(2, 8), ft(1)), height=ft(6),
    plan_symbol="bookcase", storage=True, source=REFERENCE,
)

# --- Sauna --------------------------------------------------------------------------------
#
# Not "furniture" the way a sofa is — sauna benches are site-built joinery, scribed to the
# room and made from the same low-conductivity stock as the wall liner (basswood/aspen, see
# the ``sauna-tg`` material). They are catalogued here anyway because they are placed,
# counted and dragged like every other free-standing object, and because the two dimensions
# that matter are the same two a catalog carries: the run and the depth.
#
# Heights are the Law of Löyly, not an ergonomic average: the upper bench at 36" is the one
# that has to sit level with the top of the heater stones, and the foot bench at 18" is the
# step to it. The ``sauna-bench-tiered`` symbol derives the lower tier at half the declared
# height, so those two numbers stay locked together at any size.
#
# No ``clearances``: a walk-path zone in front of a bench is meaningless in a room this
# small, where the opposite bench and the heater are *supposed* to be within arm's reach.
SAUNA_BENCH_TIERED_102 = FurnitureType(
    tag="FURN-SAUNA-BENCH-2T-102", name="Two-tier sauna bench, 8'-6\"",
    footprint=(ft(8, 6), ft(3, 6)), height=ft(3), plan_symbol="sauna-bench-tiered",
    source="Law of Löyly two-tier bench: upper 36\", lower 18\" (notes/sauna_shower_basement_detail.md)",
)
SAUNA_BENCH_54 = FurnitureType(
    tag="FURN-SAUNA-BENCH-54", name='Sauna foot bench, 4\'-6"',
    footprint=(ft(4, 6), ft(1, 8)), height=ft(1, 6), plan_symbol="sauna-bench",
    source="Law of Löyly lower bench, 18\" (notes/sauna_shower_basement_detail.md)",
)

# A workbench and a shoe-changing bench are generic furniture, not house-specific joinery:
# both were authored in catlin's own catalog only because nothing shared existed. (The
# mudroom *closets* stay house-local — their footprints are fitted to specific walls.)
WORKBENCH_60 = FurnitureType(
    tag="FURN-G-WORKBENCH",
    name="Garage workbench, 60 x 30 x 34 in",
    footprint=(inch(60), inch(30)),
    height=inch(34),
    plan_symbol="desk",
    source="Standard garage workbench, 60 x 30 x 34 in",
)
# `sauna-bench` is reused as the plan symbol: a platform against the +y wall is exactly this
# bench's shape at rotation 90. 18" seat height matches the sauna foot bench.
MUDROOM_BENCH_36 = FurnitureType(
    tag="FURN-M-MUD-BENCH",
    name="Mudroom bench, 36 x 18 in",
    footprint=(ft(3), ft(1, 6)),
    height=ft(1, 6),
    plan_symbol="sauna-bench",
    storage=False,
    source="Shoe-changing bench, 36 x 18 in",
)

STARTER_FURNITURE_TYPES = (
    STANDARD_SOFA, LOVESEAT, SECTIONAL, ARMCHAIR, ROCKING_CHAIR, COFFEE_TABLE, END_TABLE,
    MEDIA_CONSOLE,
    TV_65, TV_98,
    QUEEN_BED, KING_BED, FULL_BED, TWIN_BED, DRESSER, CHEST, WARDROBE_48, NIGHTSTAND,
    SIX_SEAT_DINING_TABLE, EIGHT_SEAT_DINING_TABLE, ROUND_DINING_TABLE,
    TWO_PERSON_DINING_TABLE, DINING_CHAIR,
    WRITING_DESK, OFFICE_CHAIR, DESK_CHAIR, BOOKCASE,
    SAUNA_BENCH_TIERED_102, SAUNA_BENCH_54,
    WORKBENCH_60, MUDROOM_BENCH_36,
)
