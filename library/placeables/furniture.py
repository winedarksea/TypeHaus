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
    """Side access both sides plus foot access — how a bed is actually used."""
    return (side_zone(width, depth, ft(2), "bed side access", sign=1),
            side_zone(width, depth, ft(2), "bed side access", sign=-1),
            front_zone(width, depth, ft(2, 6), "bed foot access"))


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
NIGHTSTAND = FurnitureType(
    tag="FURN-NIGHTSTAND-24", name="Nightstand", footprint=(ft(2), ft(1, 4)), height=ft(2, 2),
    plan_symbol="nightstand", storage=True, source=REFERENCE,
)

# --- Dining -----------------------------------------------------------------------------

SIX_SEAT_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-6", name="Six-seat dining table", footprint=(ft(6), ft(3)), height=ft(2, 6),
    plan_symbol="dining-table", source=REFERENCE,
    clearances=(surround_zone(ft(6), ft(3), ft(3), "chair-use zone"),),
)
ROUND_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-ROUND-48", name="Round four-seat dining table", footprint=(ft(4), ft(4)),
    height=ft(2, 6), plan_symbol="round-table", source=REFERENCE,
    clearances=(surround_zone(ft(4), ft(4), ft(3), "chair-use zone"),),
)
# No pull-out zone of its own: a dining chair lives inside the table's chair-use zone by
# definition, and giving it a second one only reports the set conflicting with itself.
DINING_CHAIR = FurnitureType(
    tag="FURN-DINING-CHAIR", name="Dining chair", footprint=(ft(1, 8), ft(1, 10)),
    height=ft(3, 2), plan_symbol="dining-chair", source=REFERENCE,
)

# --- Home office ------------------------------------------------------------------------

WRITING_DESK = FurnitureType(
    tag="FURN-DESK-48", name="Writing desk", footprint=(ft(4), ft(2)), height=ft(2, 6),
    plan_symbol="desk", source=REFERENCE,
    clearances=(front_zone(ft(4), ft(2), ft(3), "desk chair pull-out"),),
)
OFFICE_CHAIR = FurnitureType(
    tag="FURN-OFFICE-CHAIR", name="Office chair", footprint=(ft(2, 2), ft(2, 2)),
    height=ft(3, 2), plan_symbol="office-chair", source=REFERENCE,
)
BOOKCASE = FurnitureType(
    tag="FURN-BOOKCASE-32", name="Bookcase", footprint=(ft(2, 8), ft(1)), height=ft(6),
    plan_symbol="bookcase", storage=True, source=REFERENCE,
)

STARTER_FURNITURE_TYPES = (
    STANDARD_SOFA, LOVESEAT, SECTIONAL, ARMCHAIR, COFFEE_TABLE, END_TABLE, MEDIA_CONSOLE,
    TV_65, TV_98,
    QUEEN_BED, KING_BED, FULL_BED, TWIN_BED, DRESSER, CHEST, NIGHTSTAND,
    SIX_SEAT_DINING_TABLE, ROUND_DINING_TABLE, DINING_CHAIR,
    WRITING_DESK, OFFICE_CHAIR, BOOKCASE,
)
