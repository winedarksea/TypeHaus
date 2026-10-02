"""System 1's north-face pad and stand, west of PT-BW-PE under the open-ended canopy.

Owner decision, 2026-10-02: assume Gree accepts this open-ended canopy configuration.
The north-facing cabinet moved 7'-10" west to x 25'-2"..28'-5", retaining its 6" rear
gap and leaving 12" to the 14" pier's west face. The garage's northward shift provides
57 15/16" from the discharge to its south cladding. This is an accepted design assumption,
not a manufacturer approval obtained by the model; plans/hp1-canopy-siting-study.md
records the obstruction-table distinction.

The pad falls north into a 3" gravel strip formed out of SL-WK-C. Beyond that strip,
39 3/4" of paved entry walk remains. The cabinet overlaps WIN-M-KITCH's west edge by
2 1/2" in plan, with 18 3/16" between cabinet top and sill. A pure west translation leaves
the rear 1 3/8" beyond the canopy's south roof edge; its stand height and pad top remain
the same as the other two units.

The cabinet follows the north-end air handler in RM-S-NCLOSET. It left the shared south
pad on 2026-09-04, stood east of the garage from 2026-09-07, and now occupies this bay.
The electrical authoring file cannot import this params module: its matching literal
centre, this pad's drainage outline in plan/site.py, and the stand are held together by
test_catlin_outdoor_structures.py. Three units, three pads, three params modules.
"""

from __future__ import annotations

from typehaus import Connector, ConnectorKind, Post, Slab, ft, inch, pt

# --- the cabinet this serves, restated ------------------------------------------------
# EQ-T-GREE-FLEXX-ULTRA-24-OD: 39" wide x 14 9/16" deep, 187.4 lb, foot pattern
# 29 3/4" x 15 9/16" from the submittal (the same pattern params/sunken_garden.py used
# while this unit stood down there).
_CAB_W_IN = 39.0
_CAB_D_IN = 14.5625
_FOOT_W_IN = 29.75
_FOOT_D_IN = 15.5625
#: House north cladding face. y=36'-0" is the sheathing line (``face("sheathing-ext")`` on
#: W-M-N2) and the rainscreen/girt/board-batten stack outboard of it is
#: ``params/roof_trim.py::_WALL_OUTBOARD_IN``, 7 1/4".
_CLADDING_Y_IN = 36 * 12 + 7.25
#: ** 6", NOT THE PUBLISHED 4". ** Gree's back clearance for this chassis is 4"; the
#: `hp3_pad` idiom is "published plus two" where the ground has the room, and here it has.
#: The two extra inches are not comfort, they are what makes the pad buildable: at 4" the
#: pad's south edge lands 3/4" off the cladding instead of the 3" convention SL-SG-HPPAD
#: set, and forcing the 3" back would hang the 2" leg half an inch off the slab and fail
#: ``pad.contains(ring)``. At 6" the pocket's own arithmetic reproduces exactly.
_BACK_CLEAR_IN = 6.0

#: The cabinet centre, in inches from the project origin. **This pair is also written in
#: plan/electrical.py** as ``pt(ft(26, 9.5), ft(37, 8.53125))`` and the two files cannot
#: import each other. The Y mirrors the centre the unit had in the pocket
#: (``ft(-1, -8.53125)`` about the same cladding offset), which is not a coincidence: it is
#: the same cabinet at the same back clearance off the same 7 1/4" cladding stack.
#:
#: Pier west face 29'-5", less 12" service space and half the 39" cabinet.
_CX_IN = 26 * 12 + 9.5                                      # 26'-9 1/2"
_CY_IN = _CLADDING_Y_IN + _BACK_CLEAR_IN + _CAB_D_IN / 2.0  # 37'-8 17/32"

# --- the pad ---------------------------------------------------------------------------
# x 24'-11 1/4"..28'-7 3/4", y 36'-10"..39'-4" — 9.27 sf, 0.114 cy at 4". Same assembly,
# same top and the same reasoning as the other two: 4" unreinforced on 4" of open-graded
# stone, no XPS, no vapour retarder, no frost footing under 187 lb of cabinet.
#
# The south edge stops 2 3/4" short of the house cladding — SL-SG-HPPAD's convention, and
# the number that falls out of a 6" back clearance rather than a number chosen: a pad that
# never touches the house has no isolation joint to detail, and the gap drops the wall's
# runoff into gravel rather than against a lip. The east and west edges run 2 3/4" past the
# cabinet, the same rule that sets the pocket pad's east edge. The north edge runs 12 3/16"
# past the cabinet, which is the standing room in front of the service side.
#: Derived off the centre rather than restated, so the pad follows the cabinet: the east
#: and west edges run 2 3/4" past it, which is the pocket pad's own rule.
_PAD_X0_IN, _PAD_X1_IN = _CX_IN - (_CAB_W_IN / 2.0 + 2.75), _CX_IN + (_CAB_W_IN / 2.0 + 2.75)
_PAD_Y0_IN, _PAD_Y1_IN = 36 * 12 + 10.0, 39 * 12 + 4.0
#: Two inches proud of the -2'-10" site grade, the same top as both other pads, so all
#: three cabinets' bases resolve to one number.
_PAD_TOP = ft(-2, -8)

HP1_PAD = Slab(
    kind="pour",
    uid="MHP1PADAAA", tag="SL-M-HP1PAD", assembly="HP_PAD_ON_GRADE",
    outline=(pt(inch(_PAD_X0_IN), inch(_PAD_Y0_IN)), pt(inch(_PAD_X1_IN), inch(_PAD_Y0_IN)),
             pt(inch(_PAD_X1_IN), inch(_PAD_Y1_IN)), pt(inch(_PAD_X0_IN), inch(_PAD_Y1_IN))),
    thickness=inch(4.0), top_elevation=_PAD_TOP)

# --- the stand -------------------------------------------------------------------------
# ** ON A PAD THE LEGS ARE THE FEET. ** This unit's foot pattern IS published, so it takes
# `sunken_garden.py`'s form and not `hp3_pad.py`'s: a leg directly under each of the four
# hole centres, no rail spanning two grids, no cantilever. `hp3_pad` runs rails only
# because no mounting-hole drawing for the SAP09 chassis could be sourced.
#
# `rotation=deg(180)` on the cabinet turns it end for end about its own centre, so the foot
# pattern maps onto itself and these four positions are unchanged by it. The long axis is
# in x either way, so the WIDTH pitch is in x and the DEPTH pitch in y.
#
# The 15 9/16" foot pattern is WIDER than the 14 9/16" casing across the depth, so the legs
# stand half an inch proud of both faces — which is why the pad's south edge is a derived
# number rather than "the cabinet line plus a bit".
_HP1_STAND_AT = (
    (1, _CX_IN - _FOOT_W_IN / 2.0, _CY_IN - _FOOT_D_IN / 2.0),
    (2, _CX_IN - _FOOT_W_IN / 2.0, _CY_IN + _FOOT_D_IN / 2.0),
    (3, _CX_IN + _FOOT_W_IN / 2.0, _CY_IN - _FOOT_D_IN / 2.0),
    (4, _CX_IN + _FOOT_W_IN / 2.0, _CY_IN + _FOOT_D_IN / 2.0),
)
#: 18", the other two stands' height, for the other two stands' reason: at grade the
#: cold-climate guidance (18"-24") applies as written and 18" puts the coil bottom about
#: 20" above grade, past both the drift and Gree's own 2"-above-the-snow-line rule.
#: On a NORTH face that height earns a second keep: this is the shaded side all winter.
_HP1_STAND_HEIGHT_IN = 18.0

# ``supported_by`` naming the pad is what stands these up FROM its top rather than hanging
# them below the storey datum — ``_resolve_post`` (resolve/envelope.py) bears a post on any
# tag in ``solid_top``, and a Slab is in that map.
HP1_STAND_LEGS = [
    Post(uid=f"MHP1L{_i}AAAA", tag=f"PT-M-HP1-L{_i}",
         position=pt(inch(_x), inch(_y)), size="2.0x2.0",
         height=inch(_HP1_STAND_HEIGHT_IN),
         supported_by="SL-M-HP1PAD", assembly="EQUIP_STAND_ALUM")
    for _i, _x, _y in _HP1_STAND_AT
]
# One wedge anchor per leg at the pad top, ``SS316-WEDGE-38x3`` — 316 rather than
# galvanised for the other stands' reason: an aluminium leg on a pad at grade sits in the
# splash and the road salt all winter. ``EQUIPMENT_ANCHOR`` because the part is selected by
# the joint, not by the section above it.
HP1_STAND_ANCHORS = [
    Connector(uid=f"MHP1C{_i}AAAA", tag=f"CN-M-HP1-A{_i}",
              kind=ConnectorKind.EQUIPMENT_ANCHOR, position=pt(inch(_x), inch(_y)),
              elevation=_PAD_TOP, size="SS316-WEDGE-38x3",
              connects=(f"PT-M-HP1-L{_i}", "SL-M-HP1PAD"))
    for _i, _x, _y in _HP1_STAND_AT
]

MAIN_ELEMENTS = [HP1_PAD, *HP1_STAND_LEGS, *HP1_STAND_ANCHORS]
