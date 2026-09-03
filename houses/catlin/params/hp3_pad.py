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
#: 8" of back clearance. Gree publishes no clearance diagram for this chassis that could be
#: fetched (every PDF mirror 403s — the same wall `notes/heat_pump_ground_pad.md` hit for
#: the FXU24/MUL30 stacking allowance), so this is not a read minimum: it is HP2's published
#: 6" plus two, taken because the slot has the room and because the pad's own south edge
#: then clears the legs by 2 5/8" instead of a scant half inch. What it costs is the
#: discharge, which still reads 25 11/16" to the garage cladding — see the note.
_BACK_CLEAR_IN = 8.0
#: West face on the round foot at x 10'-0", which is 6" clear of D-M-ENTRY's near jamb at
#: x 9'-6" and leaves the entry door's R311.3 landing (x 6'-6"..9'-6") untouched. The
#: cabinet still straddles the lineset punch through W-M-N2 opposite EQ-M-HP3-STAIR.
_CAB_X0_IN = 120.0

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
_PAD_X0_IN, _PAD_X1_IN = 117.0, 157.0
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
