"""Sheltered east screen cuts, supplemental supports and the timber's end nailing, inches.

Supplemental solids are coordination geometry; their mass is charged once through MDO.
Connection acceptance is evaluated by entry_screen_finish_checks, never implied by a solid.
"""

from dataclasses import dataclass
from math import ceil, floor

PANEL_THICKNESS_IN = 0.750
FINISH_BOTTOM_IN = 2.0
FINISH_TOP_IN = 47.5
PREVIOUS_PANEL_RUNS_IN = ((0.125, 7.875), (13.625, 40.5625),
                          (40.6875, 67.625), (73.375, 79.25))
# Wall length: south node to W-G-S's cladding face (E2-101); was 79.375 to its node line, and
# 78.5 until the south end moved 1/2" north, clear of D-M-ENTRY's casing (2026-11-18).
SCREEN_LENGTH_IN = 78.000
# The MDO stops at the north chord post: the end pack north of it, its tie block and the two
# HL33 garage ties stay exposed and oiled like the timber (owner, 2026-11-14).
PANEL_RUNS_IN = ((0.125, 7.375), (13.125, 37.250), (43.000, 67.125))
# The retired north panel's tie relief; only the previous-finish baseline still reads it.
TIE_RELIEF_START_IN = 76.625
TIE_RELIEF_BOTTOM_IN = 22.125
TIE_RELIEF_TOP_IN = 25.875
NAILER_STATIONS_IN = (6.625, 13.875, 36.500, 43.750, 66.375)
NAILER_BOTTOM_IN = 0.56
NAILER_TOP_IN = 45.0
TIMBER_STATION_IN = 40.125
# The 6x6 chords' west face: 72" + the garage's 7/16" ZIP, flush with W-G-W's studs (it was
# 72.625 behind the 5/8" CDX until 2026-11-18). params/north_entry_frame.py holds the line.
STUD_WEST_IN = 72.4375
STUD_EAST_IN = STUD_WEST_IN + 3.5
# One solid 6x6 under the band's centre post, on both its faces and the chord posts'.
TIMBER_WEST_IN = STUD_WEST_IN
TIMBER_WIDTH_IN = 5.5
TIMBER_EAST_IN = TIMBER_WEST_IN + TIMBER_WIDTH_IN
WOOD_DENSITY_KG_M3 = 600.0
SAW_KERF_IN = 0.125
STOCK_LENGTH_IN = 96.0


@dataclass(frozen=True)
class ScreenSupport:
    tag: str
    profile: str
    west_in: float
    east_in: float
    station_start_in: float
    station_end_in: float
    bottom_in: float = NAILER_BOTTOM_IN
    top_in: float = NAILER_TOP_IN

    @property
    def volume_in3(self):
        return ((self.east_in - self.west_in) * (self.station_end_in - self.station_start_in)
                * (self.top_in - self.bottom_in))


# Preserve the retained nailers' identities; -3 and -5 are deliberately retired.
NAILER_IDENTITIES = (1, 2, 6, 7, 4)
SUPPORTS = tuple(
    ScreenSupport(f"TR-BW-MDO-NAILER-{identity}", "2x4", STUD_WEST_IN, STUD_EAST_IN,
                  station - 0.75, station + 0.75)
    for identity, station in zip(NAILER_IDENTITIES, NAILER_STATIONS_IN, strict=True)
) + (
    ScreenSupport("TR-BW-MDO-TIMBER", "6x6", TIMBER_WEST_IN, TIMBER_EAST_IN,
                  TIMBER_STATION_IN - TIMBER_WIDTH_IN / 2,
                  TIMBER_STATION_IN + TIMBER_WIDTH_IN / 2),
)

# The timber is framed into the wall like a stud (owner, 2026-11-14): nailed through each
# plate into its end grain on the flat, before the wall stands and the band goes on. Screws
# into its ends are outside ER-192 (side grain only), and no angle fits the 1/8in gaps.
END_NAIL_PART = "S10ACN"  # 0.148 x 3in 304 SS ring shank (library/hardware/nails.py)
END_NAIL_DIAMETER_IN = 0.148
END_NAIL_LENGTH_IN = 3.0
END_NAILS_PER_END = 4
PLATE_THICKNESS_IN = 1.5
SOUTHERN_PINE_G = 0.55
# AWC, "Changes to the 2015 NDS": C_eg 0.67 for D < 1/4in installed in end grain (NDS 12.5.2).
END_GRAIN_FACTOR = 0.67
WET_SERVICE_LATERAL = 0.70  # NDS Table 11.3.3, dowel-type fasteners, MC > 19%
# Assumed floor: no bending yield strength was read for the S10ACN. The 100 ksi the engine
# carries for a common steel nail reads 135 lb where this reads 105.
END_NAIL_FYB_PSI = 60_000.0
END_CONNECTION_OPEN = (
    "Read the S10ACN's bending yield strength from Simpson; the end-nail rows are graded at "
    "an assumed 60 ksi floor.",
    "Confirm C_eg against NDS 2018 12.5.2 in print; it was read from AWC's summary of the "
    "2015 changes.",
)

# Conservative procurement/dead-load allowances, not additional solid-derived weight.
PAINT_RESERVE_LB = 2.0
END_NAIL_MASS_ALLOWANCE_LB = 0.02
HARDWARE_QUANTITIES = {END_NAIL_PART: 2 * END_NAILS_PER_END}
HARDWARE_AND_PAINT_RESERVE_LB = (
    PAINT_RESERVE_LB + HARDWARE_QUANTITIES[END_NAIL_PART] * END_NAIL_MASS_ALLOWANCE_LB
)


def panel_net_area_in2(runs):
    # A run reaching past the tie block was relieved round it, open-ended to its own end.
    return sum(b - a for a, b in runs) * (FINISH_TOP_IN - FINISH_BOTTOM_IN) - max(
        0.0, runs[-1][1] - TIE_RELIEF_START_IN
    ) * (TIE_RELIEF_TOP_IN - TIE_RELIEF_BOTTOM_IN)


GROSS_PANEL_AREA_IN2 = sum(b - a for a, b in PANEL_RUNS_IN) * (FINISH_TOP_IN - FINISH_BOTTOM_IN)
NET_PANEL_AREA_IN2 = panel_net_area_in2(PANEL_RUNS_IN)
LB_PER_IN3 = 0.0254**3 * WOOD_DENSITY_KG_M3 * 2.2046226218
SUPPORT_WEIGHT_LB = sum(s.volume_in3 for s in SUPPORTS) * LB_PER_IN3
PREVIOUS_SUPPORT_WEIGHT_LB = 5 * 1.5 * 3.5 * (NAILER_TOP_IN - NAILER_BOTTOM_IN) * LB_PER_IN3
PREVIOUS_HARDWARE_AND_PAINT_RESERVE_LB = 2.0
ACCESSORY_AREAL_DENSITY_KG_M2 = (
    (SUPPORT_WEIGHT_LB + HARDWARE_AND_PAINT_RESERVE_LB)
    / 2.2046226218 / (NET_PANEL_AREA_IN2 * 0.0254**2)
)
PURCHASING = tuple(
    {"profile": profile, "cut_length_in": NAILER_TOP_IN - NAILER_BOTTOM_IN,
     "cuts": sum(s.profile == profile for s in SUPPORTS),
     "stock_length_in": STOCK_LENGTH_IN,
     "cuts_per_board": floor(STOCK_LENGTH_IN / (NAILER_TOP_IN - NAILER_BOTTOM_IN + SAW_KERF_IN)),
     "boards": ceil(sum(s.profile == profile for s in SUPPORTS) / floor(
         STOCK_LENGTH_IN / (NAILER_TOP_IN - NAILER_BOTTOM_IN + SAW_KERF_IN)))}
    for profile in ("2x4", "6x6")
)

# Local member screening of the solid 6x6 and its end nails.
GUARD_CONCENTRATED_LB = 200.0
GUARD_INFILL_PSF = 50.0
GUARD_INFILL_AREA_FT2 = 1.0
LOCAL_DEFLECTION_LIMIT_IN = 0.25  # project coordination limit, not a statutory guard limit
WIND_TRIBUTARY_WIDTH_IN = 32.0
# NDS Supplement Table 4D, SP No.2 timbers, wet row (no further C_M but Fc-perp's).
SOUTHERN_PINE_TIMBER_FB_PSI = 850.0
SOUTHERN_PINE_TIMBER_E_PSI = 1.2e6
SOUTHERN_PINE_TIMBER_FV_PSI = 165.0
SOUTHERN_PINE_TIMBER_FC_PERP_PSI = 375.0
WOOD_FC_PERP_WET_FACTOR = 0.67
