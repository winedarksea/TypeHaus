"""System 1's ground pad and stand, on the north face east of the garage.

`EQ-M-HP1-OD` (Gree FLEXX Ultra R32 24k) stood on the shared south pad `SL-SG-HPPAD`
beside `EQ-M-HP2-OD` until 2026-09-04, in a row 6" off the house under `WIN-M-LIV-S1`,
oversailing the pocket's SE corner by 7 1/6". It crossed to the north face with the air
handler, and this module is the ground it stands on. Same pad top, same 18" stand and the
same anchor as both other units, so all three cabinets' bases resolve to one number.

** WHY THE NORTH FACE AT ALL. ** The move is not about the condenser; it is about where
`SF-S-HP1` sits. The air handler came out of `RM-S-STUDY2`'s ceiling and went into
`RM-S-NCLOSET`'s, at the north end of the storey, and a ~31 ft lineset up the north wall is
the short way to reach it. What the south pocket gets back is a unit: one cabinet under
`WIN-M-LIV-S1` instead of two, no oversail, and 8.96 sf of pour where there was 19.6.

** WHAT IT COSTS, PLAINLY: A CONDENSER UNDER THE KITCHEN SINK WINDOW. ** `WIN-M-KITCH` is
centred x 29'-4", RO 28'-2 1/2"..30'-5 1/2", and the cabinet is 39" wide. There is no
window-free band 39" wide anywhere on this wall — the widest is 34 1/2" west of the
opening — so a north-face siting laps a window whatever is done. It laps this one. The
discharge faces AWAY from the wall (`rotation=deg(180)`, north), and the sill clears the
cabinet top by 18 3/16".

** THE 40" DISCHARGE IS LEGAL ONLY BECAUSE THE CABINET STANDS EAST OF THE GARAGE. ** The
garage occupies x 6'..30' with its roof to 31'-4" and its gutter face to 31'-10"; this
cabinet is at x 33'-0"..36'-3", past its plan extent, discharging north into open front
yard. The 48 1/2" slot between the house and the garage — where `SL-M-HP3PAD` sits — could
never have given a 24k unit its discharge, and that, not the pad, is the load-bearing
siting reason. It is also the sentence that moved this cabinet 6'-6" east on 2026-09-07:
the garage moved under it, and the siting reason moved with the garage.

** IT LAPS `WIN-M-KITCH-N` NOW, NOT `WIN-M-KITCH`, AND ONE OF THEM IS UNAVOIDABLE. ** The
window-free band between the two ROs is 35 1/2" against a 39" cabinet, so a north-face
siting laps a window wherever it goes — it always did. The new lap is 10" of a 14" RO
against the 18 1/2" it took out of `WIN-M-KITCH`, so the trade is slightly better, and the
sink window is clear.

Not in `params/hp3_pad.py`, which owns the slot pad, and not in `params/sunken_garden.py`,
which owns the pocket: three units, three pads, three modules.

``Slab``/``Post``/``Connector`` are not UI-movable kinds, so a params home is legal and no
``# haus: editable`` marker is wanted. The cabinet itself is authored in
`plan/electrical.py`, which this module cannot import and which cannot import this one —
the centre below is the same literal, written twice on purpose, and
`test_catlin_outdoor_structures.py` is what holds the two together.
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
#: plan/electrical.py** as ``pt(ft(34, 7.5), ft(37, 8.53125))`` and the two files cannot
#: import each other. The Y mirrors the centre the unit had in the pocket
#: (``ft(-1, -8.53125)`` about the same cladding offset), which is not a coincidence: it is
#: the same cabinet at the same back clearance off the same 7 1/4" cladding stack.
#:
#: ** X WENT 28'-1 1/2" -> 34'-7 1/2" ON 2026-09-07, AND IT IS THE SMALLEST MOVE THAT KEEPS
#: THE CLEARANCE. ** The garage moved 6'-0" east onto the house ridge and its roof turned, so
#: what stands west of this cabinet is no longer a rake at x=25'-4" but an EAVE at x=31'-4"
#: carrying a gutter whose outer face is at 31'-10". The far-end clear was 14"; 33'-0" is the
#: west face that gives 14" back, and 33'-0" + 19 1/2" is this centre.
#:
#: ** IT OVERSAILS THE HOUSE'S NE CORNER BY 3", AND THAT IS THE TRADE THAT WAS TAKEN. **
#: The cabinet runs x 33'-0"..36'-3" against a north wall that ends at 36'-0", so its last
#: 3" have open air behind them instead of cladding — the 6" back clearance holds over 36 of
#: 39 inches. The alternative was to sit flush at 32'-9"..36'-0" and give the far end 11"
#: instead of 14", which trades a published-unknown airflow clearance for a mounting
#: cosmetic. Airflow won. There is no third option: 31'-10" to 36'-0" is 50" and the cabinet
#: plus its clearance is 53".
_CX_IN = 34 * 12 + 7.5                                      # 34'-7 1/2"
_CY_IN = _CLADDING_Y_IN + _BACK_CLEAR_IN + _CAB_D_IN / 2.0  # 37'-8 17/32"

# --- the pad ---------------------------------------------------------------------------
# x 32'-9 1/4"..36'-5 3/4", y 36'-10"..39'-4" — 9.27 sf, 0.114 cy at 4". Same assembly,
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
