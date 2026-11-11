"""Garage/canopy corner clamps follow their shared Image II seam register.

The southeast canopy corner has ColorGard and intentionally omits separate Minis.
These are authored wind-mitigation quantities, not an engineered uplift schedule.
"""

import math

from plan.storeys.garage import (
    GARAGE_X_EAST,
    GARAGE_X_WEST,
    GARAGE_Y_NORTH,
    GARAGE_Y_SOUTH,
    ROOFS,
)

from params.north_entry_frame import TRUSS_DATUM_Y_FT
from typehaus import Connector, ConnectorKind, inch, pt

PANEL_PITCH_IN = 16.0
EAVE_OVERHANG_IN = ROOFS[0].overhang.inches
EAVE_CLAMP_SETBACK_IN = 4.0
GARAGE_SOUTH_CLADDING_OFFSET_IN = 0.875
CANOPY_SOUTH_RAKE_OFFSET_IN = 1.375
WEST_CLAMP_X_IN = GARAGE_X_WEST.inches - EAVE_OVERHANG_IN + EAVE_CLAMP_SETBACK_IN
EAST_CLAMP_X_IN = GARAGE_X_EAST.inches + EAVE_OVERHANG_IN - EAVE_CLAMP_SETBACK_IN
NORTH_RAKE_IN = GARAGE_Y_NORTH.inches + EAVE_OVERHANG_IN
SOUTH_RAKE_IN = TRUSS_DATUM_Y_FT * 12 - CANOPY_SOUTH_RAKE_OFFSET_IN
SEAM_DATUM_IN = (GARAGE_Y_SOUTH.inches - GARAGE_SOUTH_CLADDING_OFFSET_IN
                 + NORTH_RAKE_IN) / 2
FIRST_SOUTH_SEAM_IN = SEAM_DATUM_IN + math.ceil(
    (SOUTH_RAKE_IN - SEAM_DATUM_IN) / PANEL_PITCH_IN) * PANEL_PITCH_IN
FIRST_NORTH_SEAM_IN = SEAM_DATUM_IN + math.floor(
    (NORTH_RAKE_IN - SEAM_DATUM_IN) / PANEL_PITCH_IN) * PANEL_PITCH_IN

_CORNER_CLAMPS = (
    ("SW", WEST_CLAMP_X_IN, FIRST_SOUTH_SEAM_IN, 1, "RF-BW-CANOPY",
     ("M2BE9KCQQ7", "PPM5H4K6EK", "QAZ18JEVTF")),
    ("NE", EAST_CLAMP_X_IN, FIRST_NORTH_SEAM_IN, -1, "RF-GARAGE",
     ("QNY7KXYE7F", "S67JTBKR21", "5WVHPSXHFD")),
    ("NW", WEST_CLAMP_X_IN, FIRST_NORTH_SEAM_IN, -1, "RF-GARAGE",
     ("8REEX7CC35", "4YB7X5WM5X", "CM84J5D2KA")),
)
GARAGE_ROOF_WIND_CLAMPS = [
    Connector(uid=uid, tag=f"CN-G-WIND-RF{corner}-{index}",
              kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(inch(x), inch(first + direction * (index - 1) * PANEL_PITCH_IN)),
              connects=(roof,), size="S-5-N Mini")
    for corner, x, first, direction, roof, uids in _CORNER_CLAMPS
    for index, uid in enumerate(uids, 1)
]
