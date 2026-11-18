"""FS-BW-FLOOR's west edge: the board ends past the westmost joist (owner, 2026-11-18).

The joist field starts 3 3/4" east of the deck's west edge (clear of PT-BW-CW/-CNW), so the
board ends overhung the westmost joist by 3". A 2-ply 2x8 nailed to that joist's west face,
top flush with the framing, fills the strip in three pieces cut 1/8" off the column faces (the
middle piece clears BM-BW-SCSILL's LUS28Z flanges). Both rims run 3 3/4" west onto the ply
ends, end nailed as at a joist, so the corners carry the board ends too. The two end pieces
take a third ply (owner, 2026-11-18), so W-BW-SCREEN's plate stubs past the columns bear 2 1/4"
of their 3 1/2", centre over bearing (`notes/north_entry_structure.md` §2a).
"""

from typehaus import JoistReinforcement, ft, inch, pt

from params.north_entry_frame import (
    COLUMN_HALF_FT,
    FIELD_WEST_X_FT,
    FRAME_Y0_FT,
    FRAME_Y1_FT,
    GARAGE_SEAT_Y_FT,
    JOIST_MEMBER_WIDTH_IN,
    LANDING_WEST_FT,
    PIER_LINE_Y_FT,
)

_CLEAR_FT = 0.125 / 12
_RIM_HALF_FT = 0.75 / 12
#: The rims' run past the westmost joist axis, to the deck's west edge.
WEST_RIM_EXTENSION = inch((FIELD_WEST_X_FT - LANDING_WEST_FT) * 12)
_PLY_X_FT = FIELD_WEST_X_FT - JOIST_MEMBER_WIDTH_IN / 12
_SOURCE = ("west deck edge strip, KDAT 2x8 plies on the westmost joist's west face; IRC "
           "R602.3(1) built-up face nailing, 10d (304 S10ACN) 3 at each end and 2 rows at 16 in "
           "o.c. per ply; notes/north_entry_structure.md section 2a")


def _plies(y0_ft, y1_ft, added=2):
    return JoistReinforcement(
        at=pt(ft(_PLY_X_FT), ft((y0_ft + y1_ft) / 2)), plies=added + 1, blocking=False,
        extent=(ft(y0_ft), ft(y1_ft)), source=_SOURCE)


WEST_EDGE_PLIES = (
    _plies(FRAME_Y0_FT + _RIM_HALF_FT, PIER_LINE_Y_FT - COLUMN_HALF_FT - _CLEAR_FT, added=3),
    _plies(PIER_LINE_Y_FT + COLUMN_HALF_FT + _CLEAR_FT,
           GARAGE_SEAT_Y_FT - COLUMN_HALF_FT - _CLEAR_FT),
    _plies(GARAGE_SEAT_Y_FT + COLUMN_HALF_FT + _CLEAR_FT, FRAME_Y1_FT - _RIM_HALF_FT, added=3),
)
