"""Sheltered east screen cuts, supplemental supports and candidate connections, inches.

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
PANEL_RUNS_IN = ((0.125, 7.875), (13.625, 37.750), (43.500, 67.625), (73.375, 79.250))
TIE_RELIEF_START_IN = 76.625
TIE_RELIEF_BOTTOM_IN = 22.125
TIE_RELIEF_TOP_IN = 25.875
NAILER_STATIONS_IN = (7.125, 14.375, 37.000, 44.250, 66.875, 74.125)
NAILER_BOTTOM_IN = 0.56
NAILER_TOP_IN = 45.0
TIMBER_STATION_IN = 40.625
TIMBER_WEST_IN = 73.625
TIMBER_PLY_THICKNESS_IN = 1.5
TIMBER_WIDTH_IN = 5.5
TIMBER_PLY_COUNT = 3
TIMBER_EAST_IN = TIMBER_WEST_IN + TIMBER_PLY_COUNT * TIMBER_PLY_THICKNESS_IN
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


# Preserve the identities of the four retained nailers; -3 is deliberately retired.
NAILER_IDENTITIES = (1, 2, 6, 7, 4, 5)
SUPPORTS = tuple(
    ScreenSupport(f"TR-BW-MDO-NAILER-{identity}", "2x4", 73.625, 77.125,
                  station - 0.75, station + 0.75)
    for identity, station in zip(NAILER_IDENTITIES, NAILER_STATIONS_IN, strict=True)
) + tuple(
    ScreenSupport(f"TR-BW-MDO-TIMBER-PLY-{ply + 1}", "2x6",
                  TIMBER_WEST_IN + ply * TIMBER_PLY_THICKNESS_IN,
                  TIMBER_WEST_IN + (ply + 1) * TIMBER_PLY_THICKNESS_IN,
                  TIMBER_STATION_IN - TIMBER_WIDTH_IN / 2,
                  TIMBER_STATION_IN + TIMBER_WIDTH_IN / 2)
    for ply in range(TIMBER_PLY_COUNT)
)

# Side-grain screws between adjacent plies, assembled west-to-east. Stagger the two
# interfaces vertically to avoid intersecting shanks inside the centre ply.
PLY_SCREW_PART = "SDWS22300DB"
PLY_SCREW_LENGTH_IN = 3.0
PLY_SCREW_THREAD_IN = 1.5
PLY_SCREW_HEAD_DIAMETER_IN = 0.760
PLY_SCREW_HEAD_PROJECTION_IN = 0.125
PLY_SCREW_OFFSETS_IN = ((6.0, 14.0, 30.0, 38.0), (7.0, 15.0, 29.0, 37.0))
PLY_SCREWS = tuple(
    (TIMBER_WEST_IN + (interface + 2) * TIMBER_PLY_THICKNESS_IN,
     TIMBER_STATION_IN, NAILER_BOTTOM_IN + offset)
    for interface, offsets in enumerate(PLY_SCREW_OFFSETS_IN) for offset in offsets
)

END_ANGLE_PART = "A35Z"
END_SCREW_PART = "SD9112"
END_ANGLES_PER_END = 2
END_SCREWS_PER_ANGLE = 12  # candidate bent configuration: six per member, ESR-3096 Table 5
END_ANGLE_LEG_IN = 1.4375
END_ANGLE_HEIGHT_IN = 4.5
END_ANGLE_STEEL_IN = 0.0478
# These remain explicit prerequisites until a bent configuration and its holes are
# coordinated with the intact plywood, the plate and the adjacent edge nailer.
END_CONNECTION_MISSING = (
    "Select and verify the bent A35Z stud-to-plate configuration and installed load directions; "
    "F1/F2 695/845 lb from the unbent upper-band detail do not establish this connection.",
    "Verify all SD9112 hole locations, side-grain penetration, wood edge/end distances and "
    "plate contact at both ends without cutting west shear plywood or existing plates.",
    "Resolve A35Z bent-tab interference with the two new edge nailers; the 1/8in gaps "
    "are narrower than a 1-7/16in angle leg. Candidate hardware envelopes are not installation approval.",
)

# Conservative procurement/dead-load allowances, not additional solid-derived weight.
PAINT_RESERVE_LB = 2.0
ANGLE_MASS_ALLOWANCE_LB = 0.35
CONNECTOR_SCREW_MASS_ALLOWANCE_LB = 0.02
TIMBER_SCREW_MASS_ALLOWANCE_LB = 0.03
HARDWARE_QUANTITIES = {
    PLY_SCREW_PART: len(PLY_SCREWS),
    END_ANGLE_PART: 2 * END_ANGLES_PER_END,
    END_SCREW_PART: 2 * END_ANGLES_PER_END * END_SCREWS_PER_ANGLE,
}
HARDWARE_AND_PAINT_RESERVE_LB = (
    PAINT_RESERVE_LB + HARDWARE_QUANTITIES[END_ANGLE_PART] * ANGLE_MASS_ALLOWANCE_LB
    + HARDWARE_QUANTITIES[END_SCREW_PART] * CONNECTOR_SCREW_MASS_ALLOWANCE_LB
    + HARDWARE_QUANTITIES[PLY_SCREW_PART] * TIMBER_SCREW_MASS_ALLOWANCE_LB
)


def panel_net_area_in2(runs):
    return sum(b - a for a, b in runs) * (FINISH_TOP_IN - FINISH_BOTTOM_IN) - (
        PANEL_RUNS_IN[-1][1] - TIE_RELIEF_START_IN
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
    for profile in ("2x4", "2x6")
)

# Local member screening uses a SINGLE loaded ply; no composite inertia or assumed
# equal ply sharing. End load transfer and attachment still require verified details.
GUARD_CONCENTRATED_LB = 200.0
GUARD_INFILL_PSF = 50.0
GUARD_INFILL_AREA_FT2 = 1.0
LOCAL_DEFLECTION_LIMIT_IN = 0.25  # project coordination limit, not a statutory guard limit
WIND_TRIBUTARY_WIDTH_IN = 32.0
SOUTHERN_PINE_2X6_FB_PSI = 1000.0
SOUTHERN_PINE_2X6_E_PSI = 1.4e6
SOUTHERN_PINE_FV_PSI = 175.0
SOUTHERN_PINE_FC_PERP_PSI = 565.0
WOOD_E_WET_FACTOR = 0.90
WOOD_FV_WET_FACTOR = 0.97
WOOD_FC_PERP_WET_FACTOR = 0.67
SCREW_WET_FACTOR = 0.70
PLY_SCREW_WITHDRAWAL_LB_IN = 164.0
PLY_SCREW_WITHDRAWAL_MAX_LB = 245.0
PLY_SCREW_MIN_EDGE_IN = 1.4375
PLY_SCREW_MIN_END_IN = 6.0
PLY_SCREW_MIN_SPACING_IN = 8.0
