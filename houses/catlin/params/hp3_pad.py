"""System 3 ground pad/stand, house north face west of the extruded-gable connector.

The open-yard position retires the interim house/garage slot, whose inlet and discharge
clearances never fitted. The cabinet is authored independently in plan/electrical.py:
editable plan modules cannot import params, so resolved-geometry tests hold them together.
See notes/hp3_north_relocation.md for the coordinated service and refrigerant routing.
"""

from __future__ import annotations

from typehaus import Connector, ConnectorKind, Post, Slab, ft, inch, pt

# SAP09HP230V1R32AO cabinet dimensions, Gree Sapphire R32 service manual p. 3.
_CAB_W_IN = 34.375
_CAB_D_IN = 14.796875
_CLADDING_Y_IN = 36 * 12 + 7.25
# Service manual p. 44: rear/left 300 mm, right/top 500 mm, discharge 2000 mm.
# Round up rear to 12" and reserve 24" sides/top, 80" north discharge; the manufacturer
# FAQ's larger 24" right/top values therefore also fit. Sources read 2026-09-10:
# https://www.greecomfort.com/assets/our-products/sapphire-r32/documents/sapphire-r32-service-manual-a.pdf
# https://www.greecomfort.com/faqs/
_BACK_CLEAR_IN = 12.0
_CAB_X0_IN = 0.0
_CX_IN = _CAB_X0_IN + _CAB_W_IN / 2.0
_CY_IN = _CLADDING_Y_IN + _BACK_CLEAR_IN + _CAB_D_IN / 2.0

# Same 40 x 24 3/4" pad, 4" thick over free-draining stone, translated with its stand.
# The 3" west overrun past the house corner remains inside the west yard; defrost drains
# north to gravel, away from the east entry. The slab does not touch either building.
_PAD_X0_IN, _PAD_X1_IN = -3.0, 37.0
_PAD_Y0_IN, _PAD_Y1_IN = 446.25, 471.0
_PAD_TOP = ft(-2, -8)

HP3_PAD = Slab(
    uid="MHP3PADAAA", tag="SL-M-HP3PAD", assembly="HP_PAD_ON_GRADE",
    outline=(pt(inch(_PAD_X0_IN), inch(_PAD_Y0_IN)), pt(inch(_PAD_X1_IN), inch(_PAD_Y0_IN)),
             pt(inch(_PAD_X1_IN), inch(_PAD_Y1_IN)), pt(inch(_PAD_X0_IN), inch(_PAD_Y1_IN))),
    thickness=inch(4.0), top_elevation=_PAD_TOP)

# Two depthwise adjustable rails at 26" centres accept the manufacturer's foot pattern;
# legs are rail ends, not an assertion that the feet lie directly over those legs.
_RAIL_HALF_LEN_IN = 8.75
_RAIL_HALF_PITCH_IN = 13.0
_HP3_STAND_AT = (
    (1, _CX_IN - _RAIL_HALF_PITCH_IN, _CY_IN - _RAIL_HALF_LEN_IN),
    (2, _CX_IN - _RAIL_HALF_PITCH_IN, _CY_IN + _RAIL_HALF_LEN_IN),
    (3, _CX_IN + _RAIL_HALF_PITCH_IN, _CY_IN - _RAIL_HALF_LEN_IN),
    (4, _CX_IN + _RAIL_HALF_PITCH_IN, _CY_IN + _RAIL_HALF_LEN_IN),
)
# As on the other two stands, cabinet base is 20" above nominal site grade. Keep snow
# cleared below the coil; stand height does not guarantee clearance above drifting snow.
_HP3_STAND_HEIGHT_IN = 18.0
HP3_STAND_LEGS = [
    Post(uid=f"MHP3L{_i}AAAA", tag=f"PT-M-HP3-L{_i}",
         position=pt(inch(_x), inch(_y)), size="2.0x2.0",
         height=inch(_HP3_STAND_HEIGHT_IN),
         supported_by="SL-M-HP3PAD", assembly="EQUIP_STAND_ALUM")
    for _i, _x, _y in _HP3_STAND_AT
]
# 316 stainless anchors resist splash/road salt at the aluminium stand feet.
HP3_STAND_ANCHORS = [
    Connector(uid=f"MHP3C{_i}AAAA", tag=f"CN-M-HP3-A{_i}",
              kind=ConnectorKind.EQUIPMENT_ANCHOR, position=pt(inch(_x), inch(_y)),
              elevation=_PAD_TOP, size="SS316-WEDGE-38x3",
              connects=(f"PT-M-HP3-L{_i}", "SL-M-HP3PAD"))
    for _i, _x, _y in _HP3_STAND_AT
]

MAIN_ELEMENTS = [HP3_PAD, *HP3_STAND_LEGS, *HP3_STAND_ANCHORS]
