"""Rooftop PV array — parametric module (plans/electrical_notes.md lines 31-33).

One row of 440 W modules each side of the house gable ridge (RF-HOUSE: ridge N-S at
x=18', 4:12, 36' footprint), landscape orientation (69.4" edge along the ridge), max fit:
floor(36' / 5.783') = 6 modules per row, centred, 12 x 440 W = 5,280 W installed. Mounted
on S-5! PVKIT standing-seam kits (no penetrations), four per module; the DC/AC run leaves
the roof at ED-A-PV-JB beside the radon-vent riser (plan/electrical.py) and lands on the
EG4 12kPV's MPPTs (EQ-B-ESS-INV, plan/electrical.py) — the array does not backfeed on
its own any more; the inverter's grid port does, on CKT-ESS-GRID (plan/circuits.py).

Generated — max fit is computed, so this cannot live in a ``# haus: editable`` module
(the dialect forbids loops); ``SolarPanel`` is not a UI-movable kind, so a params home is
legal. The resolver (resolve/solar.py) owns the tilt math; clamp elevations here follow
the resolved deck plane (RF-HOUSE eave_z 25.84' at the footprint edge, ridge 31.98',
4:12), good to an inch — the clamps are count-and-marker hardware, not located geometry.
"""

from __future__ import annotations

import math

from typehaus import Connector, ConnectorKind, SolarPanel, ft, inch, pt

ROOF_TAG = "RF-HOUSE"
RIDGE_X_FT = 18.0
FOOTPRINT_FT = 36.0
PANEL_W_IN = 69.4  # along-ridge edge (landscape)
PANEL_L_IN = 44.6  # down-slope edge, in the panel plane
PANEL_T_IN = 1.2
PANEL_WATTS = 440.0
PRODUCT = "Aptos 440 W module, 69.4 x 44.6 x 1.2 in"

# --- module electrical identity (2026-08-02) ---------------------------------------
# Aptos 440 W: Voc 39.03 V, Vmp 33.48 V, temperature coefficients -0.30%/degC on Pmax,
# -0.25%/degC on Voc, +0.046%/degC on Isc (owner-supplied datasheet figures).
PANEL_VOC = 39.03
VOC_TEMP_COEFF_PER_C = -0.0025
# Site design low. -30 degC is the cold-side design temperature used for the array's
# voltage correction — colder than the ASHRAE extreme annual mean minimum for the Twin
# Cities, deliberately, because a string is sized on the coldest sunny morning and not on
# an average of minima. NOT the heating design temperature: this number sizes conductors
# and the 690.12 grouping, not a heat load.
DESIGN_LOW_C = -30.0
STC_C = 25.0
# 39.03 x (1 + (-0.0025)(-30 - 25)) = 44.40 V. The number every voltage rule must use:
# rated Voc understates a January morning by 5.4 V per module, which is the difference
# between a two-module group at 78.1 V (legal) and one at 88.8 V (not).
PANEL_VOC_COLD = PANEL_VOC * (1.0 + VOC_TEMP_COEFF_PER_C * (DESIGN_LOW_C - STC_C))

# One string per roof side, six modules each, landing on the EG4 12kPV's two MPPTs
# (EQ-B-ESS-INV, plan/electrical.py). 6 x 44.40 = 266.4 V cold per string, well inside the
# inverter's 600 VDC ceiling.
#
# RSD on every module, and that is a computed outcome rather than a preference: two
# adjacent Aptos modules sum to 88.8 V cold against NEC 690.12(B)(2)'s 80 V limit, so
# "every other module" — the option plans/TODO.md hoped for — does not clear it here. One
# transmitter per module is what `code.NEC_690_12_rapid_shutdown` accepts, and if a future
# module with a lower Voc changes that arithmetic the check will say so.
PANEL_RSD = True
RIDGE_CLEARANCE_FT = 1.0  # plan gap between the ridge line and the modules' top edge
CLAMPS_PER_PANEL = 4
PLANE_Z_AT_X0_FT = 25.84  # resolved RF-HOUSE deck plane at the footprint edge (eave_z)
PITCH = 4.0 / 12.0

_w_ft = PANEL_W_IN / 12.0
_count = math.floor(FOOTPRINT_FT / _w_ft)  # 6
_row_start_ft = (FOOTPRINT_FT - _count * _w_ft) / 2.0
# Plan projection of the down-slope edge (44.6" at 4:12).
_plan_l_ft = (PANEL_L_IN / 12.0) / math.sqrt(1.0 + PITCH * PITCH)


def _plane_z_ft(x: float) -> float:
    return PLANE_Z_AT_X0_FT + (RIDGE_X_FT - abs(x - RIDGE_X_FT)) * PITCH


def _build():
    panels = []
    clamps = []
    for side, sign in (("W", -1.0), ("E", 1.0)):
        origin_x = RIDGE_X_FT + sign * RIDGE_CLEARANCE_FT
        for index in range(_count):
            n = index + 1
            origin_y = _row_start_ft + index * _w_ft
            tag = f"SP-A-PV-{side}{n}"
            panels.append(SolarPanel(
                uid=f"SPV{side}{n}AAAA", tag=tag, roof_ref=ROOF_TAG,
                origin=pt(ft(origin_x), ft(origin_y)),
                width=inch(PANEL_W_IN), length=inch(PANEL_L_IN),
                thickness=inch(PANEL_T_IN), watts=PANEL_WATTS, product=PRODUCT,
                string=f"STR-{side}", voc=PANEL_VOC, voc_cold=PANEL_VOC_COLD,
                rsd=PANEL_RSD,
            ))
            # Four PVKIT clamps per module, inset 6" from each corner in plan.
            near_x = origin_x + sign * 0.5
            far_x = origin_x + sign * (_plan_l_ft - 0.5)
            for letter, (cx, cy) in zip("ABCD", (
                    (near_x, origin_y + 0.5), (near_x, origin_y + _w_ft - 0.5),
                    (far_x, origin_y + 0.5), (far_x, origin_y + _w_ft - 0.5))):
                clamps.append(Connector(
                    uid=f"SPC{side}{n}{letter}AAA", tag=f"CN-A-PV-{side}{n}{letter}",
                    kind=ConnectorKind.STANDING_SEAM_CLAMP,
                    position=pt(ft(cx), ft(cy)), elevation=ft(_plane_z_ft(cx)),
                    size="S-5-PVKIT", connects=(tag, ROOF_TAG)))
    return panels, clamps


_PANELS, _CLAMPS = _build()

TOTAL_WATTS = sum(panel.watts for panel in _PANELS)  # 5,280 W
ATTIC_ELEMENTS = [*_PANELS, *_CLAMPS]
