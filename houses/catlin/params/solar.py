"""Rooftop PV array — parametric module.

One unbroken row of bifacial 410 W modules each side of the house gable ridge (RF-HOUSE: ridge
N-S at x=18', 6:12, 36' footprint), PORTRAIT (44.6" edge along the ridge, 67.7" down-slope),
as close to the ridge as IRC R324.6.2 allows: the module HULL in plan is 18" from the ridge
(array 24.4% of the plan roof, under 33%). The 36" pathway of R324.6.1 is the north rake end
of each plane (north is the street side); there is no interior gap. Max fit along the ridge:
9 portrait modules per row (a landscape row fits 6). 18 x 410 W = 7,380 W, on S-5! PVKIT
standing-seam kits (no penetrations), four per module on its two across-seam edges. The
DC/AC run leaves the roof at ED-A-PV-JB beside the radon-vent riser (plan/electrical.py)
and lands on the EG4 12kPV's MPPTs (EQ-B-ESS-INV).

Generated — max fit is computed, so this cannot live in a ``# haus: editable`` module
(the dialect forbids loops); ``SolarPanel`` is not a UI-movable kind, so a params home is
legal. The resolver (resolve/solar.py) owns the tilt math; clamp elevations here follow
the assembly-derived seam crowns. Clamp columns follow the shared 16 inch stations.
"""

from __future__ import annotations

import math

from params.cladding import HOUSE_NS_OUTBOARD_IN
from params.roof_panel import (
    ABOVE_DECK,
    EAVE_DECK_IN,
    PITCH,
    clamp_columns_inches,
    seam_top_inches,
)

from typehaus import Connector, ConnectorKind, SolarPanel, ft, inch, pt
from typehaus.quantities import M_PER_IN

ROOF_TAG = "RF-HOUSE"
RIDGE_X_FT = 18.0
FOOTPRINT_FT = 36.0
# Aptos DNA-108-BF10-410W, bifacial, same 67.7 x 44.6 x 1.3 in frame as the 440 W
# monofacial it replaces. Aptos datasheet USSSP201-781 (06/2025), STC front face: Pmax 410 W,
# Voc 37.67 V, Isc 13.11 A, Vmp 33.08 V, Imp 12.39 A; Pmax -0.32 %/degC, Voc -0.24 %/degC,
# Isc +0.03 %/degC; rear-side gain rows 5 % 431 W / 15 % 472 W / 25 % 513 W; 5,400 Pa.
PANEL_ALONG_IN = 44.6  # along-ridge edge (portrait)
PANEL_DEPTH_IN = 67.7  # down-slope edge, in the panel plane
PANEL_T_IN = 1.3
PANEL_WATTS = 410.0
PRODUCT = "Aptos DNA-108-BF10-410W (datasheet 06/2025), 67.7 x 44.6 x 1.3 in"

# --- module electrical identity -----------------------------------------------------
PANEL_VOC = 37.67
VOC_TEMP_COEFF_PER_C = -0.0024
# Site design low. -30 degC is the cold-side design temperature used for the array's
# voltage correction — colder than the ASHRAE extreme annual mean minimum for the Twin
# Cities, deliberately, because a string is sized on the coldest sunny morning and not on
# an average of minima. NOT the heating design temperature: this number sizes conductors
# and the 690.12 grouping, not a heat load.
DESIGN_LOW_C = -30.0
STC_C = 25.0
# 37.67 x (1 + (-0.0024)(-30 - 25)) = 42.64 V. The number every voltage rule must use.
PANEL_VOC_COLD = PANEL_VOC * (1.0 + VOC_TEMP_COEFF_PER_C * (DESIGN_LOW_C - STC_C))

# One string per roof side, nine modules each, one string per MPPT on the 12kPV (2 MPPTs,
# 120-500 V operating, 600 V max, 25 A usable and 31 A short-circuit per MPPT; spec sheet
# v1.0.9). 9 x 42.64 = 383.8 V cold; Vmp 9 x 33.08 x (1 - 0.0032 x 45 K) = 255 V at a 70 degC
# cell; Imp 12.39 A (15.5 A at +25 % rear gain), Isc 13.11 A x 1.25 rear x 1.25 NEC = 20.5 A.
# Two strings never share an MPPT: 2 x 15.5 A > 25 A. 7.38 kW STC is under 12 kW usable.
#
# RSD on every module: two adjacent modules sum to 85.3 V cold against NEC 690.12(B)(2)'s
# 80 V limit, so "every other module" does not clear it. One SunSpec receiver per module (the
# inverter carries the transmitter) is what `code.NEC_690_12_rapid_shutdown` accepts.
PANEL_RSD = True
CLAMPS_PER_PANEL = 4

# --- layout -----------------------------------------------------------------------------
# R324.6.2: 18" ridge setback each side below 33 % coverage, measured in plan to the module
# HULL. The standoff leans the module's top face toward the ridge by (skin + standoff +
# thickness) x sin(pitch), so the authored origin sits that far further out.
RIDGE_HULL_SETBACK_IN = 18.0
STANDOFF_IN = 3.0  # SolarPanel.standoff default (clamp height off the roof skin)
_SKIN_IN = sum(layer.thickness.meters for layer in ABOVE_DECK) / M_PER_IN
_LEAN_IN = (_SKIN_IN + STANDOFF_IN + PANEL_T_IN) * PITCH / math.hypot(1.0, PITCH)
RIDGE_CLEARANCE_IN = RIDGE_HULL_SETBACK_IN + _LEAN_IN + 0.02  # origin-to-ridge, plan
# The roof edge is the cladding face, HOUSE_NS_OUTBOARD_IN outboard of the 36' line.
ROOF_SOUTH_IN = -HOUSE_NS_OUTBOARD_IN
ROOF_NORTH_IN = FOOTPRINT_FT * 12 + HOUSE_NS_OUTBOARD_IN
# S-5! PVKIT 2.0 manual s1.4.3: 1/4" minimum between module columns (thermal cycling).
MODULE_GAP_IN = 0.25
# Gable-edge keep-out south of the array; the north end is the R324.6.1 pathway (36",
# street side). 4" clears the rake hem and trim fasteners; the whole rake is wind edge zone
# regardless (a = 0.1 x 37' = 3.7 ft), so this is workmanship, not a wind setback.
RAKE_MARGIN_SOUTH_IN = 4.0
PATHWAY_MIN_IN = 36.5  # 36" + 1/2" build tolerance
_COUNT = math.floor((ROOF_NORTH_IN - PATHWAY_MIN_IN - ROOF_SOUTH_IN - RAKE_MARGIN_SOUTH_IN
                     + MODULE_GAP_IN) / (PANEL_ALONG_IN + MODULE_GAP_IN))  # 9
_ROW_START_IN = ROOF_SOUTH_IN + RAKE_MARGIN_SOUTH_IN
# Plan projection of the down-slope edge (67.7" at 6:12).
_plan_l_ft = (PANEL_DEPTH_IN / 12.0) / math.sqrt(1.0 + PITCH * PITCH)
PLANE_Z_AT_X0_FT = EAVE_DECK_IN / 12


def _build():
    panels = []
    clamps = []
    for side, sign in (("W", -1.0), ("E", 1.0)):
        origin_x = RIDGE_X_FT + sign * RIDGE_CLEARANCE_IN / 12.0
        for index in range(_COUNT):
            n = index + 1
            start_in = _ROW_START_IN + index * (PANEL_ALONG_IN + MODULE_GAP_IN)
            origin_y = start_in / 12.0
            tag = f"SP-A-PV-{side}{n}"
            panels.append(SolarPanel(
                uid=f"SPV{side}{n}AAAA", tag=tag, roof_ref=ROOF_TAG,
                origin=pt(ft(origin_x), ft(origin_y)),
                width=inch(PANEL_ALONG_IN), length=inch(PANEL_DEPTH_IN),
                thickness=inch(PANEL_T_IN), watts=PANEL_WATTS, product=PRODUCT,
                string=f"STR-{side}", voc=PANEL_VOC, voc_cold=PANEL_VOC_COLD,
                rsd=PANEL_RSD,
            ))
            # Both clamp columns sit on seams at least six inches inside the module ends;
            # the portrait module's 44.6" edge always spans two or more 16" seam stations.
            column_a, column_b = (value / 12 for value in
                                  clamp_columns_inches(start_in, PANEL_ALONG_IN))
            near_x = origin_x + sign * 0.5
            far_x = origin_x + sign * (_plan_l_ft - 0.5)
            for letter, (cx, cy) in zip("ABCD", (
                    (near_x, column_a), (near_x, column_b),
                    (far_x, column_a), (far_x, column_b))):
                clamps.append(Connector(
                    uid=f"SPC{side}{n}{letter}AAA", tag=f"CN-A-PV-{side}{n}{letter}",
                    kind=ConnectorKind.STANDING_SEAM_CLAMP,
                    position=pt(ft(cx), ft(cy)), elevation=inch(seam_top_inches(cx * 12)),
                    size="S-5-PVKIT", connects=(tag, ROOF_TAG)))
    return panels, clamps


_PANELS, _CLAMPS = _build()

TOTAL_WATTS = sum(panel.watts for panel in _PANELS)  # 7,380 W
ATTIC_ELEMENTS = [*_PANELS, *_CLAMPS]
