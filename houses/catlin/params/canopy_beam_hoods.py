"""Matching canopy-only covers; shop fastening and movement release remain in the note."""

from params.north_entry_frame import (
    HEADER_SOUTH_Y_FT,
    HEADER_TAIL_SOUTH_Y_FT,
    HEADER_TOP_FT,
    LANDING_WEST_FT,
    ROOF_COLUMN_EAST_X_FT,
)
from typehaus import Annotation, Flashing, FormedFlashingSection, TrimKind, ft, inch, pt

VENTILATION_GAP_IN = 0.5
HOOD_WIDTH_IN = 5.5 + 2 * VENTILATION_GAP_IN
CROWN_SLOPE = 0.25 / 12
TRUSS_HALF_WIDTH_IN = 0.75
TRUSS_CLEARANCE_IN = 1.0
SHEET_THICKNESS_IN = 0.032
HOOD_SOUTH_Y_FT = HEADER_TAIL_SOUTH_Y_FT - VENTILATION_GAP_IN / 12
HOOD_NORTH_Y_FT = (
    HEADER_SOUTH_Y_FT - (TRUSS_HALF_WIDTH_IN + TRUSS_CLEARANCE_IN + SHEET_THICKNESS_IN) / 12
)
HOOD_CROWN_FT = HEADER_TOP_FT + (VENTILATION_GAP_IN + HOOD_WIDTH_IN / 2 * CROWN_SLOPE) / 12

HOODS = [
    Flashing(
        uid=uid,
        tag=f"TR-BW-HOOD-{side}",
        kind=TrimKind.BEAM_CAP,
        host_ref=f"BM-BW-R{side}",
        material="metal-dark-exterior",
        path=(pt(ft(x), ft(HOOD_SOUTH_Y_FT)), pt(ft(x), ft(HOOD_NORTH_Y_FT))),
        top_elevation=ft(HOOD_CROWN_FT),
        depth=inch(1.25),
        thickness=inch(HOOD_WIDTH_IN),
        section=FormedFlashingSection(
            profile="ventilated_hood",
            roof_ref="RF-BW-CANOPY",
            slope=CROWN_SLOPE,
            air_gap=inch(VENTILATION_GAP_IN),
            upstand=inch(1),
            sheet_thickness=inch(SHEET_THICKNESS_IN),
        ),
    )
    for side, x, uid in (
        ("W", LANDING_WEST_FT, "5P8RW4EB4M"),
        ("E", ROOF_COLUMN_EAST_X_FT, "DA1JYY56XG"),
    )
]

NOTES = [
    Annotation(
        uid="G98N9J0W2S",
        tag="AN-BW-BEAM-HOODS",
        position=pt(ft(18), ft(37)),
        text=(
            "CANOPY TAIL HOODS TR-BW-HOOD-W/E: matching 8-7/8in beam tails from post centres. "
            "Brake-formed crowned metal, minimum 1/2in clear of glulam top, sides and south end; "
            "discontinuous nonabsorptive spacers and sheltered side tabs fixed ONLY to glulam, "
            "no top penetrations. Downturned sides, outward hems, ventilated south return and "
            "OPEN bottom. North hood upstand stops 1in south of truss face; separate canopy-roof "
            "apron laps 7/8in over it with 1/2in separation, roof leg 1in under membrane/roofing. "
            "Keep all truss bearings and ties clear. Metal/coating, isolated side fasteners and "
            "spacers must suit actual treatment and nearby ZMAX; preserve field-cut treatment. "
            "No house attachment, contact or sealant bridge. Nominal hood-to-house gap 1-1/4in; "
            "confirm actual finishes, fabrication tolerances and required relative movement BEFORE "
            "fabrication. Shop tab layout, wind securement and roof-rake lap need approval; "
            "see notes/canopy_beam_tail_hoods.md. Geometry is not a construction release."
        ),
    )
]

ELEMENTS = [*HOODS, *NOTES]
