"""System 3's ground pad and stand, in the slot between the house and the garage.

`EQ-M-HP3-OD` (Gree Sapphire R32 9k) has stood at grade on the north side since it was
authored, on the same terms as the two units that came down off the balcony on 2026-09-02
(`notes/heat_pump_ground_pad.md`) — no drain pan, no piped condensate, defrost meltwater
onto its own ground. **It had no ground to stand on.** No pad, no stand, and no
``mount.elevation``, so a `FLOOR` mount put its base on the `main` datum at 0'-0", 2'-10"
in the air over bare soil. This module gives it what `SL-SG-HPPAD` gives the other two, at
the same pad top and the same stand height, so all three cabinets' bases are one number.

Not in `params/sunken_garden.py`, which owns the pocket south of the house; this pad is in
the 4'-0 1/2" slot north of it, between the house cladding face (y 36'-7 1/4") and the
garage's (y 40'-7 3/4"), east of the breezeway and west of the front walk.

``Slab``/``Post``/``Connector`` are not UI-movable kinds, so a params home is legal and no
``# haus: editable`` marker is wanted. The cabinet itself is authored in
`plan/electrical.py`, which this module cannot import and which cannot import this one —
the centre below is the same literal, written twice on purpose, and
`test_catlin_outdoor_structures.py` is what holds the two together.
"""

from __future__ import annotations

from typehaus import Connector, ConnectorKind, Post, Slab, ft, inch, pt

# --- the cabinet this serves, restated ------------------------------------------------
# EQ-T-GREE-SAPPHIRE-9-OD: 34 3/8" wide x 14 51/64" deep, 78.3 lb. The element carried a
# 31 x 13 placeholder footprint until 2026-09-04 — the outline the TYPE record shed on
# 2026-08-31 — and the type's footprint is what geometry reads (resolve/placeables.py
# ``_local_footprint`` prefers the type), so the plan drew 34 3/8" while every comment in
# the house said 31".
_CAB_W_IN = 34.375
_CAB_D_IN = 14.796875
#: House north cladding face. y=36'-0" is the sheathing line (``face("sheathing-ext")`` on
#: W-M-N2) and the rainscreen/girt/board-batten stack outboard of it is
#: ``params/roof_trim.py::_WALL_OUTBOARD_IN``, 7 1/4".
_CLADDING_Y_IN = 36 * 12 + 7.25
#: Garage south cladding face, ``params/breezeway.py::_GARAGE_CLADDING_Y``. The slot
#: between the two faces is 48 1/2".
_GARAGE_CLADDING_Y_IN = 40 * 12 + 7.75
#: 8" of back clearance — **and it is under Gree's published minimum. The figures WERE
#: sourced on 2026-09-09**, retiring this line's old claim that no clearance diagram could
#: be fetched: greecomfort.com's own "GREE MINI-SPLIT SYSTEMS CHEAT SHEET" (08262020),
#: under CLEARANCES, states *"2' clearance from the top, 2' right side, 1' left side,
#: 6 1/2' discharge (air outlet), and 1' incoming (air inlet) air side"*. Measured against
#: this siting, in the 48 1/2" slot:
#:
#:   air inlet (S, to house cladding)     8"        vs 12"   — 4" short
#:   discharge (N, to garage cladding)   25 11/16"  vs 78"   — 52 5/16" short
#:   west side (to GL-BW-WALL-E)         -5/16"     vs 12"   — the cabinet and the
#:                                                             breezeway's east glazing
#:                                                             INTERPENETRATE by 5/16"
#:
#: **No orientation fits.** The unit's largest face is 34 3/8"; the slot is 48 1/2". Across
#: the airflow axis that leaves at most 33 11/16" against the 90" (12+78) Gree wants; turned
#: 90 degrees the discharge could run east to open yard, but the two sides then share
#: 14 1/8" against 36" (12+24). The slot cannot hold this cabinet to its own manufacturer's
#: numbers at any position or rotation, and moving it east does not change a single y
#: dimension above. Nothing in the engine grades an Equipment against a clearance envelope,
#: which is why this stood at 0 FAIL. Re-siting the unit out of the slot is the fix; that is
#: an owner decision, not a params edit.
#:
#: ** WHERE THAT LEAVES THE 2026-09-09 POSITION: AN OWNER-ACCEPTED INTERIM. ** The 2'-4"
#: move was made to free the breezeway's glazing, not to fix the airflow, and the owner
#: accepted the y-axis shortfall as a deferred issue rather than re-site the unit now. As
#: moved, measured (not asserted) — x 12'-4"..15'-2 3/8", y 37'-3 1/4"..38'-6 3/64":
#:
#:   MET      west side, to GL-BW-WALL-E     12 11/16"  vs 12"  (was -5/16", a collision)
#:   MET      east side, service              open yard vs 24"  (front walk is flat, not
#:                                                               an obstruction)
#:   MET      top                             open      vs 24"  (the breezeway roof now
#:                                                               sheds at x 11'-3", 13"
#:                                                               west of the cabinet; it
#:                                                               used to shed onto its lid)
#:   NOT MET  air inlet (S, to house cladding)  8"      vs 12"  — 4" short
#:   NOT MET  discharge (N, to garage cladding) 25 11/16" vs 78" — 52 5/16" short
#:
#: **The x axis is now right and the y axis cannot be.** Moving east changed no y dimension
#: and never could: the slot is 48 1/2" and this cabinet is 14 51/64" deep, so front+back
#: can never exceed 33 11/16" against the 90" (12+78) Gree asks. Turning it 90 degrees
#: would open the discharge east to the yard but leave the two sides sharing 14 1/8"
#: against 36". **The fix is re-siting system 3's outdoor unit out of the slot**, which
#: drags the W-M-N2 lineset punch, ED-M-HP3-DISC and CKT-HP3 with it.
#:
#: ** NOTHING WILL REMIND ANYONE. ** No check in this engine grades an Equipment against a
#: clearance envelope — that is why the 5/16" interpenetration with the glazing stood at
#: 0 FAIL until it was measured by hand. `haus check` is green on this cabinet and will
#: stay green however badly it is boxed in. This comment is the only record.
_BACK_CLEAR_IN = 8.0
#: West face at x 12'-4". ** IT MOVED 2'-4" EAST ON 2026-09-09 AND THE MOVE IS THE
#: BREEZEWAY'S. ** It stood at x 10'-0", which was 6" clear of D-M-ENTRY's near jamb and
#: clear of that door's landing — but x 10'-0" is also where the breezeway's east glazing
#: line stood, and cabinet and glass INTERPENETRATED by 5/16" (z -1'-2"..+0'-7 7/8" against
#: the panel's -0'-7 1/4"..+7'-4 3/4"), at 0 FAIL. Widening the deck to cover
#: `D-G-SERVICE`'s R311.3 landing put that glass at x 11'-3 5/16", so the cabinet had to go.
#:
#: 2'-4" is chosen, not rounded: it is the smallest whole-inch move that clears the new
#: glass face by Gree's 12" lesser-side minimum. West face 12'-4" less glass face
#: 11'-3 5/16" = **12 11/16" clear**. The east face lands at 15'-2 3/8" and the pad at
#: 15'-5", which is why the front walk's west edge moved to 15'-9" (plan/site.py).
#:
#: The lineset still punches W-M-N2 straight: `EQ-M-HP3-STAIR` inside spans x 10'-7 3/4"..
#: 13'-4 3/4" and the cabinet now spans 12'-4"..15'-2 3/8", so 12 3/4" of station is shared
#: and the punch sits in it, behind the cabinet's west end. That overlap is the binding
#: constraint on any further eastward move — past x 13'-4 3/4" the punch stops being
#: straight and the run has to turn inside the wall.
_CAB_X0_IN = 148.0

#: The cabinet centre, in inches from the project origin. **This pair is also written in
#: plan/electrical.py** as ``pt(ft(11, 5.1875), ft(37, 10.6484375))`` and the two files
#: cannot import each other.
_CX_IN = _CAB_X0_IN + _CAB_W_IN / 2.0                      # 137 3/16"
_CY_IN = _CLADDING_Y_IN + _BACK_CLEAR_IN + _CAB_D_IN / 2.0  # 454 41/64"

# --- the pad ---------------------------------------------------------------------------
# x 9'-9"..13'-1", y 36'-10 1/4"..38'-11" — 6.9 sf, 0.08 cy at 4". Same assembly, same
# top and the same reasoning as the pocket pads: 4" unreinforced on 4" of open-graded
# stone, no XPS, no vapour retarder, no frost footing under 78 lb of cabinet.
#
# The south edge stops 3" short of the house cladding, the convention SL-SG-HPPAD set: a
# pad that never touches the house has no isolation joint to detail, and the gap drops the
# wall's runoff into gravel rather than against a lip. The north edge is NOT the same
# convention against the garage — it stops 20 3/4" short of it, because the pad is sized to
# the stand rather than to the slot, and that 20 3/4" is the walking route through.
#: Moved 2'-4" east with the cabinet: x 12'-1"..15'-5". It keeps its 3"/2 5/8" margins on
#: the cabinet ends, and its east edge now stops 4" short of the front walk's new west edge
#: at x 15'-9" — the same "never touch, no joint to detail" convention its south edge uses
#: against the house cladding.
_PAD_X0_IN, _PAD_X1_IN = 145.0, 185.0
_PAD_Y0_IN, _PAD_Y1_IN = 442.25, 467.0
#: Two inches proud of the -2'-10" site grade, the same top as both pocket pads, so all
#: three cabinets' bases resolve to one number.
_PAD_TOP = ft(-2, -8)

HP3_PAD = Slab(
    uid="MHP3PADAAA", tag="SL-M-HP3PAD", assembly="HP_PAD_ON_GRADE",
    outline=(pt(inch(_PAD_X0_IN), inch(_PAD_Y0_IN)), pt(inch(_PAD_X1_IN), inch(_PAD_Y0_IN)),
             pt(inch(_PAD_X1_IN), inch(_PAD_Y1_IN)), pt(inch(_PAD_X0_IN), inch(_PAD_Y1_IN))),
    thickness=inch(4.0), top_elevation=_PAD_TOP)

# --- the stand -------------------------------------------------------------------------
# ** THE LEGS ARE NOT THE FEET HERE, AND THAT IS THE ONE DEPARTURE FROM SL-SG-HPPAD. **
# The pocket stands put a leg directly under each published foot hole, because Gree gives a
# foot pattern for the FXU24 (29 3/4 x 15 9/16) and the MUL30 (25 x 15 19/32) in their
# submittals. **No mounting-hole drawing for the SAP09 chassis could be sourced** — the
# installation manual's outline sheet is not in any mirror that answers — so putting a leg
# on an invented pitch would be asserting a dimension nobody read.
#
# So this stand is specified the way it is actually bought: two rails running the DEPTH way
# under the cabinet's ends, and the cabinet's own feet bolt to the rails wherever its pitch
# puts them. The four legs are the rails' ends, not the cabinet's feet:
#
#   rails   in y at x = centre +/- 13", i.e. 4 3/16" inboard of each cabinet end
#   legs    at y = centre +/- 8 3/4", a 17 1/2" rail that takes any foot pitch up to ~17"
#
# 17 1/2" is chosen against the two patterns that ARE published: both are ~15 9/16" across
# the depth, an inch WIDER than the FXU24's own casing, so a rail that only spanned this
# cabinet's 14 51/64" could miss its feet outboard on both sides. Whatever the SAP09's
# pitch turns out to be, it lands on the rail.
_RAIL_HALF_LEN_IN = 8.75
_RAIL_HALF_PITCH_IN = 13.0
_HP3_STAND_AT = (
    (1, _CX_IN - _RAIL_HALF_PITCH_IN, _CY_IN - _RAIL_HALF_LEN_IN),
    (2, _CX_IN - _RAIL_HALF_PITCH_IN, _CY_IN + _RAIL_HALF_LEN_IN),
    (3, _CX_IN + _RAIL_HALF_PITCH_IN, _CY_IN - _RAIL_HALF_LEN_IN),
    (4, _CX_IN + _RAIL_HALF_PITCH_IN, _CY_IN + _RAIL_HALF_LEN_IN),
)
#: 18", the pocket stands' height, for the pocket stands' reason: at grade the cold-climate
#: guidance (18"-24") applies as written and 18" puts the coil bottom about 20" above grade,
#: past both the drift and Gree's own 2"-above-the-snow-line rule.
_HP3_STAND_HEIGHT_IN = 18.0

# ``supported_by`` naming the pad is what stands these up FROM its top rather than hanging
# them below the storey datum — ``_resolve_post`` (resolve/envelope.py) bears a post on any
# tag in ``solid_top``, and a Slab is in that map.
HP3_STAND_LEGS = [
    Post(uid=f"MHP3L{_i}AAAA", tag=f"PT-M-HP3-L{_i}",
         position=pt(inch(_x), inch(_y)), size="2.0x2.0",
         height=inch(_HP3_STAND_HEIGHT_IN),
         supported_by="SL-M-HP3PAD", assembly="EQUIP_STAND_ALUM")
    for _i, _x, _y in _HP3_STAND_AT
]
# One wedge anchor per leg at the pad top, ``SS316-WEDGE-38x3`` — 316 rather than
# galvanised for the pocket stands' reason: an aluminium leg on a pad at grade sits in the
# splash and the road salt all winter. ``EQUIPMENT_ANCHOR`` because the part is selected by
# the joint, not by the section above it.
HP3_STAND_ANCHORS = [
    Connector(uid=f"MHP3C{_i}AAAA", tag=f"CN-M-HP3-A{_i}",
              kind=ConnectorKind.EQUIPMENT_ANCHOR, position=pt(inch(_x), inch(_y)),
              elevation=_PAD_TOP, size="SS316-WEDGE-38x3",
              connects=(f"PT-M-HP3-L{_i}", "SL-M-HP3PAD"))
    for _i, _x, _y in _HP3_STAND_AT
]

MAIN_ELEMENTS = [HP3_PAD, *HP3_STAND_LEGS, *HP3_STAND_ANCHORS]
