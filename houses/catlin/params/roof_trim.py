"""House-roof eave water management — the box gutter and its lap chain (Tier 2, WP roof-eave).

The RF-HOUSE eave edges (ridge runs N-S, so the eaves are the WEST and EAST footprint
edges) get the water-management pieces the derived roof-edge trim does NOT provide.

**RF-HOUSE has no fascia at all**, and that is the fact every offset here is measured from.
Its standing-seam siding and standing-seam roofing are one continuous skin over a flush
zero-overhang edge, so ``resolve/roof_trim.py`` takes the ``continuous_skin_cladding`` path:
no fascia boards, no soffit, no drip-edge cladding band — just a **corner trim** angle,
1.25" thick, hung outboard of the footprint edge, its top flush with the roofing and a 2"
leg lapping down over the head of the wall panels. That angle is the derived counterpart of
the reference's "stainless steel flashing behind gutter over wall furring": it already caps
the wall cladding's head from outboard, so authoring a counter-flashing here would put two
pieces of metal in one place. What it does *not* do is get the water into a trough, and
that is the job left for this module.

The chain, in which **every higher piece sheds onto the next lower one** so water can never
get behind the siding:

    roofing → corner trim (derived) → drip edge → box gutter → downspout

- a DRIP EDGE whose flat leg rests on the gutter's rim under the corner trim's lower leg,
  and whose turn-down hangs at the trough's mid-width, so the roof's runoff is thrown into
  the middle of the gutter instead of down the wall behind it ("drip edge nailed to roof
  furring and empties into gutter");
- a 6" BOX GUTTER hung **tight to the wall plane** — its back sheet tucked *behind* the
  corner trim's outer face rather than standing off in mid-air, which is what closes the
  open slot that used to run the length of the eave;
- a DOWNSPOUT per eave, because the gutters slope to one, plus the S-5! securement clamps
  (plan/mep.py) that steady it.

Every joint takes the same nominal ``_LAP_IN`` of overlap, and each piece's elevation is
derived from the one above it rather than authored, so the chain cannot be broken by
changing one number in isolation.

The reference mounts the gutter the same way: `gutter_back_x = x_fur1 + furring_wall - 0.2`
puts the back sheet essentially *on* the cladding plane, with the roofing running out past
it so the water has to fall inside.

RF-HOUSE has zero authored overhang, so no soffit exists or is needed. Garage gutter/
drip stay deferred with the garage/truss roof work.

Not `# haus: editable`: trim runs are not UI-movable elements (only params-generated
geometry lives here), so the editable-writeback rule does not apply.

Geometry facts this module derives from (see plan/storeys/attic.py + plan/assemblies.py):
- sheathing-ext datum plane at x = 0 / 36'; wall stack outboard of it =
  wrb 0.02" + polyiso 2" + eps 2" + furring 0.5" + cladding 0.5" = 5.02" (cladding face
  == roof footprint edge, where eave_z_m is defined) — and the footprint runs to that same
  face in **y** as well, which is how far the eave runs have to reach to close the corner;
- knee-wall plate top at 25'; deck plane (eave_z_m) rides the I-joist rise above it:
  11.875" - 5.5" x 4/12 seat drop (2x6 knee walls) = 10.0417";
- roof stack above the deck (perpendicular): deck 0.75" + membrane 0.25" -> foam 6" ->
  roof membrane 0.25" (furring underside at 7.25") -> batten 0.75" -> metal 0.5"; the 4:12
  slope factor turns those perpendicular offsets into the vertical ones an authored
  elevation is measured in;
- the wall cladding's head lands at the roofing's own underside (MatingFaces with a
  continuous skin), 8.0" perpendicular above the deck plane.
"""

from __future__ import annotations

import math

from typehaus import Downspout, Flashing, Gutter, TrimKind, ft, inch, pt

_HOUSE_FT = 36.0
# Wall layers outboard of the sheathing-ext datum -> the cladding outer face, which is
# exactly the roof footprint edge (the zero-overhang roof laps the cladding).
_WALL_OUTBOARD_IN = 0.02 + 2.0 + 2.0 + 0.5 + 0.5  # 5.02"
_EAVE_X_W = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_X_E = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)

_PLATE_TOP = ft(25)  # attic elevation 20' + 5' knee walls
_DECK_RISE_IN = 11.875 - 5.5 * (4.0 / 12.0)  # I-joist depth - 2x6 seat drop = 10.0417"
_EAVE_DECK = _PLATE_TOP + inch(_DECK_RISE_IN)  # deck plane at the eave edge (eave_z_m)

# The roof stack is offset perpendicular to the slope; an authored elevation is vertical.
_SLOPE_FACTOR = math.hypot(1.0, 4.0 / 12.0)  # 4:12 -> 1.0541
_VENT_SLOT_IN = 7.25 * _SLOPE_FACTOR         # 7.64" — roof furring underside, vertical
_CLADDING_HEAD_IN = 8.0 * _SLOPE_FACTOR      # 8.43" — roofing underside == wall panel heads

# The derived corner trim (resolve/roof_trim.py::_corner_trim_members): 1.25" thick, hung
# outboard of the footprint edge, with a 2" leg down over the wall panel heads. Its outer
# face and its lower edge are the two faces everything below registers against.
_TRIM_FACE_IN = 1.25
_TRIM_BOTTOM_IN = _CLADDING_HEAD_IN - 2.0    # 6.43" above the deck plane

#: The overlap every joint in the chain takes. Half an inch is also the thickness the
#: boxes-only IR draws sheet metal at (resolve/trim_bands.py::GUTTER_SHELL_M), so a lap of
#: one nominal shell is the smallest one that still reads as a lap in the model.
_LAP_IN = 0.5

# --- Box gutter ---------------------------------------------------------------------------
# 6" of trough, hung with its back sheet tucked a lap *behind* the corner trim's outer face,
# so the trim's lower leg sheds onto the back sheet rather than past it into the gap. The rim
# rides a lap above the trim's bottom edge — high enough to make that lap, low enough to
# leave the eave end of the roof's vent channel open (the rim must stay under _VENT_SLOT_IN,
# or the gutter dams the channel it is supposed to sit below).
_GUTTER_THICK_IN = 6.0                       # channel width, out from the back sheet's face
_GUTTER_DEPTH = inch(5)                      # channel height
_GUTTER_BACK_IN = _TRIM_FACE_IN - _LAP_IN    # 0.75" — inner face of the back sheet
_GUTTER_RIM_IN = _TRIM_BOTTOM_IN + _LAP_IN   # 6.93" above the deck plane

#: Mid-width of the trough — where a drip wants to land, being the furthest it can be from
#: both the back sheet and the front lip. The shell closes a half-shell at each side.
_TROUGH_MID_IN = _GUTTER_BACK_IN + _LAP_IN + (_GUTTER_THICK_IN - 2.0 * _LAP_IN) / 2.0

# --- Drip edge ----------------------------------------------------------------------------
# A bent angle (resolve/trim_bands.py::drip_edge_bands): a flat leg spanning from the gutter's
# back sheet out over the trough, and a turn-down at its outboard end. It runs from the back
# sheet's inner face to a half-shell past the trough's mid-width, which puts the turn-down
# centred on the middle of the channel. Its top is a lap above the gutter rim, so the corner
# trim laps over the drip and the drip laps over the gutter — three pieces, two clean laps.
_DRIP_INNER_IN = _GUTTER_BACK_IN
_DRIP_THICK_IN = _TROUGH_MID_IN + _LAP_IN / 2.0 - _DRIP_INNER_IN
_DRIP_TOP_IN = _GUTTER_RIM_IN + _LAP_IN
_DRIP_DEPTH = inch(3)                        # turn-down ends well inside the trough


def _above_deck(vertical_in: float):
    """An absolute elevation from a vertical offset above the deck plane at the eave."""
    return _EAVE_DECK + inch(vertical_in)


# The eaves run the full roof footprint, which reaches the *cladding* face at both gable
# ends — not the sheathing datum. Stopping at ft(0)/ft(36) left 5.02" of open roof stack
# at each rake corner with no gutter under it, which is the hole the 3D view showed.
_EAVE_Y0 = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_Y1 = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)


def _run(x):
    return (pt(x, _EAVE_Y0), pt(x, _EAVE_Y1))


def _eave_water(side: str, index: int, eave_x, outward: float):
    """One eave edge's drip edge and box gutter; ``outward`` is -1 west / +1 east.

    Both runs go south→north (+y), whose left-hand normal (resolve/geometry.py::normal,
    90 deg CCW) points west (-x). The house is east of the west eave and west of the east
    eave, so the building is on the *right* of the west run and on the *left* of the east
    run — which is what tells the gutter which sheet is its back, and the drip edge which
    end its turn-down hangs off. Get it wrong on the drip and it points back at the wall.
    """
    back_side = "right" if outward < 0 else "left"

    def out(inches_val: float):
        offset = inch(inches_val)
        return eave_x + offset if outward > 0 else eave_x - offset

    drip = Flashing(
        uid=f"RTFF0{index}AAAA", tag=f"TR-RF-DRIP-{side}", kind=TrimKind.DRIP_FLASHING,
        path=_run(out(_DRIP_INNER_IN + _DRIP_THICK_IN / 2.0)),
        top_elevation=_above_deck(_DRIP_TOP_IN), depth=_DRIP_DEPTH,
        thickness=inch(_DRIP_THICK_IN), material="aluminum",
        host_ref="RF-HOUSE", back_side=back_side)
    gutter = Gutter(
        uid=f"RTGT0{index}AAAA", tag=f"TR-RF-GUTTER-{side}", kind=TrimKind.GUTTER,
        path=_run(out(_GUTTER_BACK_IN + _GUTTER_THICK_IN / 2.0)),
        top_elevation=_above_deck(_GUTTER_RIM_IN), depth=_GUTTER_DEPTH,
        thickness=inch(_GUTTER_THICK_IN), material="aluminum", host_ref="RF-HOUSE",
        slope=f'1/16 in/ft to the north-end {side} downspout',
        downspout_ref=f"TR-RF-LEADER-{side}",
        back_side=back_side)
    return [drip, gutter]


# --- Downspouts ---------------------------------------------------------------------------
# One 4" round leader per eave. Each eave sheds half the roof: 18' of run x 36' = 648 sq ft.
# Minneapolis' short-duration design intensity is around 8 in/hr, and at that rate a 3"
# leader is good for roughly 425 sq ft — not enough — while a 4" round still clears 648. So
# 4", not the more usual 3".
#
# Both go to the NORTH end, discharging into the 4' gap toward the garage rather than onto
# the freestanding sunken-garden structure 5" off the south face. Each hangs on the trough's
# centre line, so it takes the outlet straight down out of the gutter floor, and runs to a
# splash block a foot above grade (main storey elevation 0). The S-5! CanDuit clamps that
# hold it to the standing-seam siding are in plan/mep.py; per the reference they steady the
# leader and are explicitly not its primary support.
_LEADER_DIA_IN = 4.0
_LEADER_Y = ft(_HOUSE_FT) - inch(6.0)
_LEADER_BOTTOM = ft(1)


def _leader(side: str, index: int, eave_x, outward: float):
    offset = inch(_TROUGH_MID_IN)
    return Downspout(
        uid=f"RTDS0{index}AAAA", tag=f"TR-RF-LEADER-{side}",
        position=pt(eave_x + offset if outward > 0 else eave_x - offset, _LEADER_Y),
        top_elevation=_above_deck(_GUTTER_RIM_IN) - _GUTTER_DEPTH,
        bottom_elevation=_LEADER_BOTTOM, diameter=inch(_LEADER_DIA_IN),
        material="aluminum", gutter_ref=f"TR-RF-GUTTER-{side}",
        # Four clamps at roughly 6' o.c. down the ~24' run (plan/mep.py::LEADER_CLAMPS).
        clamp_refs=tuple(f"CN-A-LEADER-{side}{n}" for n in (1, 2, 3, 4)))


ATTIC_ELEMENTS = [
    *_eave_water("W", 1, _EAVE_X_W, -1.0), *_eave_water("E", 2, _EAVE_X_E, 1.0),
    _leader("W", 1, _EAVE_X_W, -1.0), _leader("E", 2, _EAVE_X_E, 1.0),
]
