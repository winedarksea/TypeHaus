"""Fitted sauna seating; dimensions are inches from the current finished liner faces."""

from typehaus.model import FurnitureCut, FurnitureType, inch, pt
from typehaus.model.placeable_symbols._sauna_recliner import (
    MATTRESS_FLAT_LENGTH_IN,
    MATTRESS_THICKNESS_IN,
    REFERENCE_DEPTH_IN,
    REFERENCE_WIDTH_IN,
    profile_height_in,
)

# Re-laid 2026-11-25 when the sauna gave its north 2' to the bath: clear box x 121 5/8"..
# 210", y 9 1/4"..90 3/4". Two full-length decks against the west wall, the aisle east of
# them with the step, the floor drain and the heater.
UPPER_WEST_X_IN = 123.25
UPPER_EAST_X_IN = 151.25
LOWER_EAST_X_IN = 179.25
BENCH_SOUTH_Y_IN = 10.0
BENCH_NORTH_Y_IN = 90.5625
# The recliner on the lower deck's south end, back north, feet to the window.
RECLINER_NORTH_Y_IN = 67.5
STEP_EAST_X_IN = 193.25
STEP_SOUTH_Y_IN = 68.0
STEP_NORTH_Y_IN = 78.0
UPPER_HEIGHT_IN = 42.0
LOWER_HEIGHT_IN = 24.0
STEP_HEIGHT_IN = 12.0
LIGHT_RAIL_HEIGHT_IN = 16.0

UPPER_POSITION = pt(inch((UPPER_WEST_X_IN + UPPER_EAST_X_IN) / 2),
                    inch((BENCH_SOUTH_Y_IN + BENCH_NORTH_Y_IN) / 2))
LOWER_POSITION = pt(inch((UPPER_EAST_X_IN + LOWER_EAST_X_IN) / 2),
                    inch((BENCH_SOUTH_Y_IN + BENCH_NORTH_Y_IN) / 2))
RECLINER_POSITION = pt(inch((UPPER_EAST_X_IN + LOWER_EAST_X_IN) / 2),
                       inch((BENCH_SOUTH_Y_IN + RECLINER_NORTH_Y_IN) / 2))
STEP_POSITION = pt(inch((LOWER_EAST_X_IN + STEP_EAST_X_IN) / 2),
                   inch((STEP_SOUTH_Y_IN + STEP_NORTH_Y_IN) / 2))
# The lower deck's one exposed edge, split at the recliner's head: two runs, one switch.
WEST_LIGHT_PATH = (pt(inch(LOWER_EAST_X_IN), inch(BENCH_NORTH_Y_IN)),
                   pt(inch(LOWER_EAST_X_IN), inch(RECLINER_NORTH_Y_IN)))
READING_LIGHT_PATH = (pt(inch(LOWER_EAST_X_IN), inch(RECLINER_NORTH_Y_IN)),
                      pt(inch(LOWER_EAST_X_IN), inch(BENCH_SOUTH_Y_IN)))

# work_surface=False: fixed casework, so the locust base stops at the benches (review I3-001).
_JOINERY = ("Unfinished owner basswood slats on a bought Douglas fir frame, eased edges, "
            "open frame. Removable deck sections "
            "for cleaning and service; support framing must leave the floor drain, "
            "condensate air gaps and west exhaust unobstructed. notes/sauna_seating.md.")

UPPER_BENCH = FurnitureType(
    tag="FT-CATLIN-SAUNA-UPPER-81", name='Sauna lying bench, 80 9/16 x 28, 42" top',
    footprint=(inch(BENCH_NORTH_Y_IN - BENCH_SOUTH_Y_IN),
               inch(UPPER_EAST_X_IN - UPPER_WEST_X_IN)),
    height=inch(UPPER_HEIGHT_IN), plan_symbol="sauna-open-bench", work_surface=False,
    source=_JOINERY + ' Full 80 9/16 x 28" lying surface; no inward-projecting backrest.',
)
LOWER_PLATFORM = FurnitureType(
    tag="FT-CATLIN-SAUNA-LOWER-81", name='Sauna lower deck, 80 9/16 x 28, 24" top',
    footprint=(inch(BENCH_NORTH_Y_IN - BENCH_SOUTH_Y_IN),
               inch(LOWER_EAST_X_IN - UPPER_EAST_X_IN)),
    height=inch(LOWER_HEIGHT_IN), plan_symbol="sauna-open-bench", work_surface=False,
    source=_JOINERY + " Carries the reading recliner at its south end.",
)
# Catalog-only since 2026-11-25: the recliner moved onto the lower deck.
READING_PLATFORM = FurnitureType(
    tag="FT-CATLIN-SAUNA-READING-58", name='Sauna reading platform, 58 1/2 x 28, 24" top',
    footprint=(inch(58.5), inch(28)),
    height=inch(LOWER_HEIGHT_IN), plan_symbol="sauna-open-bench", work_surface=False,
    source=_JOINERY,
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
# 3/4" x 3 1/2" basswood (4/4, the liner's stock, since 2026-10-20) at 1/2" gaps, running the
# bench's long way. Bearers are bought Douglas fir 2x4s across it at <= 16" o.c.
# (notes/sauna_seating.md), so they stay off
# the mill order. The step's 10" takes three 3" slats. Legs, stretchers, the recliner and the
# heater fence are not designed yet: an allowance in notes/wood_supply.md, not a cut.
_SLAT = "basswood-bench-4q"
_BEARER = "df-sauna-frame"


def _deck_cuts(slats: int, slat_width_in: float, long_in: float, short_in: float,
               bearers: int) -> tuple[FurnitureCut, ...]:
    return (FurnitureCut(part="sauna bench slat", count=slats, thickness=inch(0.75),
                         width=inch(slat_width_in), length=inch(long_in), material_ref=_SLAT),
            FurnitureCut(part="sauna bench bearer", count=bearers, thickness=inch(1.5),
                         width=inch(3.5), length=inch(short_in), material_ref=_BEARER))


# The two decks: 7 slats (27 1/2" with six 1/2" gaps) by 80 9/16", 7 bearers at 13 7/16".
UPPER_BENCH = UPPER_BENCH.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(7, 3.5, 80.5625, 28, 7)))
LOWER_PLATFORM = LOWER_PLATFORM.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(7, 3.5, 80.5625, 28, 7)))
READING_PLATFORM = READING_PLATFORM.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(7, 3.5, 58.5, 28, 5)))
ACCESS_STEP = ACCESS_STEP.model_copy(update=dict(
    wood_material_ref=_SLAT, cut_list=_deck_cuts(3, 3.0, 14, 10, 2)))

SAUNA_FURNITURE_TYPES = (UPPER_BENCH, LOWER_PLATFORM, READING_PLATFORM, ACCESS_STEP,
                        READING_RECLINER, READING_MATTRESS)
