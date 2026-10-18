"""Fitted sauna seating; dimensions are inches from the current finished liner faces."""

from typehaus.model import FurnitureCut, FurnitureType, inch, pt
from typehaus.model.placeable_symbols._sauna_recliner import (
    MATTRESS_FLAT_LENGTH_IN,
    MATTRESS_THICKNESS_IN,
    REFERENCE_DEPTH_IN,
    REFERENCE_WIDTH_IN,
    profile_height_in,
)

UPPER_WEST_X_IN = 123.25
UPPER_EAST_X_IN = 151.25
UPPER_SOUTH_Y_IN = 38.1875
BENCH_NORTH_Y_IN = 116.1875
LOWER_EAST_X_IN = 171.25
READING_SOUTH_Y_IN = 10.0
READING_NORTH_Y_IN = 38.0
READING_EAST_X_IN = 181.75
STEP_EAST_X_IN = 185.25
STEP_SOUTH_Y_IN = 70.1875
STEP_NORTH_Y_IN = 80.1875
UPPER_HEIGHT_IN = 42.0
LOWER_HEIGHT_IN = 24.0
STEP_HEIGHT_IN = 12.0
LIGHT_RAIL_HEIGHT_IN = 16.0

UPPER_POSITION = pt(inch((UPPER_WEST_X_IN + UPPER_EAST_X_IN) / 2),
                    inch((UPPER_SOUTH_Y_IN + BENCH_NORTH_Y_IN) / 2))
LOWER_POSITION = pt(inch((UPPER_EAST_X_IN + LOWER_EAST_X_IN) / 2),
                    inch((READING_NORTH_Y_IN + BENCH_NORTH_Y_IN) / 2))
READING_POSITION = pt(inch((UPPER_WEST_X_IN + READING_EAST_X_IN) / 2),
                      inch((READING_SOUTH_Y_IN + READING_NORTH_Y_IN) / 2))
STEP_POSITION = pt(inch((LOWER_EAST_X_IN + STEP_EAST_X_IN) / 2),
                   inch((STEP_SOUTH_Y_IN + STEP_NORTH_Y_IN) / 2))
WEST_LIGHT_PATH = (pt(inch(LOWER_EAST_X_IN), inch(BENCH_NORTH_Y_IN)),
                   pt(inch(LOWER_EAST_X_IN), inch(READING_NORTH_Y_IN)))
READING_LIGHT_PATH = (pt(inch(LOWER_EAST_X_IN), inch(READING_NORTH_Y_IN)),
                      pt(inch(READING_EAST_X_IN), inch(READING_NORTH_Y_IN)),
                      pt(inch(READING_EAST_X_IN), inch(READING_SOUTH_Y_IN)))

_JOINERY = ("Unfinished owner basswood slats on a bought Douglas fir frame, eased edges, "
            "open frame. Removable deck sections "
            "for cleaning and service; support framing must leave the floor drain, "
            "condensate air gaps and west exhaust unobstructed. notes/sauna_seating.md.")

UPPER_BENCH = FurnitureType(
    tag="FT-CATLIN-SAUNA-UPPER-78", name='Sauna lying bench, 78 x 28, 42" top',
    footprint=(inch(BENCH_NORTH_Y_IN - UPPER_SOUTH_Y_IN),
               inch(UPPER_EAST_X_IN - UPPER_WEST_X_IN)),
    height=inch(UPPER_HEIGHT_IN), plan_symbol="sauna-open-bench",
    source=_JOINERY + ' Full 78 x 28" lying surface; no inward-projecting backrest.',
)
LOWER_PLATFORM = FurnitureType(
    tag="FT-CATLIN-SAUNA-LOWER-78", name='Sauna foot platform, 78 3/16 x 20, 24" top',
    footprint=(inch(BENCH_NORTH_Y_IN - READING_NORTH_Y_IN),
               inch(LOWER_EAST_X_IN - UPPER_EAST_X_IN)),
    height=inch(LOWER_HEIGHT_IN), plan_symbol="sauna-open-bench", source=_JOINERY,
)
READING_PLATFORM = FurnitureType(
    tag="FT-CATLIN-SAUNA-READING-58", name='Sauna reading platform, 58 1/2 x 28, 24" top',
    footprint=(inch(READING_EAST_X_IN - UPPER_WEST_X_IN),
               inch(READING_NORTH_Y_IN - READING_SOUTH_Y_IN)),
    height=inch(LOWER_HEIGHT_IN), plan_symbol="sauna-open-bench", source=_JOINERY,
)
ACCESS_STEP = FurnitureType(
    tag="FT-CATLIN-SAUNA-STEP", name='Sauna access step, 14 x 10, 12" top',
    footprint=(inch(STEP_EAST_X_IN - LOWER_EAST_X_IN),
               inch(STEP_NORTH_Y_IN - STEP_SOUTH_Y_IN)),
    height=inch(STEP_HEIGHT_IN), plan_symbol="sauna-open-bench",
    source=_JOINERY + " Secure against sliding and tipping; 12/24/42 inch access sequence.",
)
READING_RECLINER = FurnitureType(
    tag="FT-CATLIN-SAUNA-RECLINER", name="Armless wooden bench-top reading recliner",
    footprint=(inch(REFERENCE_WIDTH_IN), inch(REFERENCE_DEPTH_IN)),
    height=inch(profile_height_in()), plan_symbol="sauna-recliner",
    source=("Removable self-supporting wood frame, rounded slats, positive 105/110/112 "
            "degree back locks; drawn at 110 degrees. No wall/window attachment. "
            "36 inch back, 22 inch seat, 22 inch leg support. Full-size mock-up with "
            "the mattress and a one-hour reading trial required before fabrication. "
            "notes/sauna_seating.md."),
)
READING_MATTRESS = FurnitureType(
    tag="FT-CATLIN-SAUNA-MATTRESS", name='Custom linen/wool shikibuton, 26 x 80 x 4" flat',
    footprint=(inch(REFERENCE_WIDTH_IN), inch(REFERENCE_DEPTH_IN)),
    height=inch(profile_height_in(mattress=True)), plan_symbol="sauna-recliner-mattress",
    source=(f"Custom {REFERENCE_WIDTH_IN:g} x {MATTRESS_FLAT_LENGTH_IN:g} x "
            f"{MATTRESS_THICKNESS_IN:g} inch flat mattress, linen fabric and wool filling. "
            "Flexible 36/22/22 inch sections, washable linen cover, natural-fiber ties; "
            "adjustable matching lumbar/neck cushions included. Height is the bent "
            "assembly envelope, not thickness. Hot-sauna qualification of the complete "
            "assembly REQUIRED before purchase/fabrication; supplier unselected. "
            "Lift and air after wet use. notes/sauna_seating.md."),
)
# The benches' cut lists (2026-10-16). Slats are owner stock, so they reach `haus millwork`:
# 1" x 3 1/2" basswood at 1/2" gaps, running the bench's long way. Bearers are bought Douglas
# fir 2x4s across it at <= 24" o.c. (2026-10-18; notes/sauna_seating.md), so they stay off
# the mill order. The step's 10" takes three 3" slats. Legs, stretchers, the recliner and the
# heater fence are not designed yet: an allowance in notes/wood_supply.md, not a cut.
_SLAT = "basswood-bench-5q"
_BEARER = "df-sauna-frame"


def _deck_cuts(slats: int, slat_width_in: float, long_in: float, short_in: float,
               bearers: int) -> tuple[FurnitureCut, ...]:
    return (FurnitureCut(part="sauna bench slat", count=slats, thickness=inch(1),
                         width=inch(slat_width_in), length=inch(long_in), material_ref=_SLAT),
            FurnitureCut(part="sauna bench bearer", count=bearers, thickness=inch(1.5),
                         width=inch(3.5), length=inch(short_in), material_ref=_BEARER))


UPPER_BENCH = UPPER_BENCH.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(7, 3.5, 78, 28, 5)))
LOWER_PLATFORM = LOWER_PLATFORM.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(5, 3.5, 78.1875, 20, 5)))
READING_PLATFORM = READING_PLATFORM.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(7, 3.5, 58.5, 28, 4)))
ACCESS_STEP = ACCESS_STEP.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(3, 3.0, 14, 10, 2)))

SAUNA_FURNITURE_TYPES = (UPPER_BENCH, LOWER_PLATFORM, READING_PLATFORM, ACCESS_STEP,
                        READING_RECLINER, READING_MATTRESS)
