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

- a DRIP EDGE whose flange lies ON the top deck, under the field underlayment, and whose
  turn-down hangs at the trough's mid-width, so the roof's runoff is thrown into the middle
  of the gutter instead of down the wall behind it ("drip edge nailed to roof furring and
  empties into gutter");
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
- roof stack above the deck (perpendicular): zip 0.5" + deck vapour barrier 0.04" -> foam
  3" + 3" -> top deck 0.625" (top-deck surface at 7.165") -> underlayment 0.06" -> vent mat
  0.25" -> metal 0.5"; the 4:12 slope factor turns those perpendicular offsets into the
  vertical ones an authored elevation is measured in;
- the wall cladding's head lands at the roofing's own underside (MatingFaces with a
  continuous skin), 7.475" perpendicular above the deck plane.

**The batten cavity is gone; a 1/4" vent mat replaced it** (2026-08-20). The roof was a
vented batten roof and the drip edge's ceiling used to be the batten cavity's underside —
the chain existed partly to avoid damming that slot. The metal now clips through a thin
ventilated mat to a top deck screwed straight through the foam, and the ceiling is the top
deck's own surface instead: the drip flashing lies ON that deck and the underlayment laps
OVER it, so nothing *else* in the chain may reach that plane — a second thing under the
underlayment is what lifts it off the deck it has to bond to. Same chain, a different plane.
"""

from __future__ import annotations

import math

from typehaus import Downspout, Flashing, Gutter, TrimKind, ft, inch, pt

_HOUSE_FT = 36.0
# Wall layers outboard of the sheathing-ext datum -> the cladding outer face, which is
# exactly the roof footprint edge (the zero-overhang roof laps the cladding).
#
# **The one constant the cladding face is measured by**, and deliberately spelled as the
# stack it is: 1 1/2" band A foam + 1 1/2" inner girt + 1" band C foam + 1/2" vent gap +
# 1 1/2" outer girt + 1 1/4" PBR panel (plan/assemblies.py CATLIN_EXT_2X6). The catlin
# truss moved it out one full inch on 2026-08-26, and the exposed-fastener panel that
# replaced the snap-lock seam the same day moved it a further 3/4" — a ribbed panel stands
# off by its rib height, where a snap-lock pan stands off by its pan. Every param in this
# house that measures off the cladding moved with it.
#
# The values it has had, kept beside it so the revert is a line and not a re-derivation:
#   6.5"  — the girts under 1/2" snap-lock seam (2026-08-26, earlier the same day)
#   5.5"  — the Swinburne truss (2026-08-23): 1.5 foam + 3.5 outrigger band + 0.5 seam
#   5.02" — the CI boards before it: 0.02 WRB + 2" polyiso + 2" EPS + 0.5 furring + 0.5 seam
_WALL_OUTBOARD_IN = 1.5 + 1.5 + 1.0 + 0.5 + 1.5 + 1.25  # 7.25"
_EAVE_X_W = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_X_E = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)

_PLATE_TOP = ft(25)  # attic elevation 20' + 5' knee walls
_DECK_RISE_IN = 11.875 - 5.5 * (4.0 / 12.0)  # I-joist depth - 2x6 seat drop = 10.0417"
_EAVE_DECK = _PLATE_TOP + inch(_DECK_RISE_IN)  # deck plane at the eave edge (eave_z_m)

# The roof stack is offset perpendicular to the slope; an authored elevation is vertical.
_SLOPE_FACTOR = math.hypot(1.0, 4.0 / 12.0)  # 4:12 -> 1.0541
# The top deck's upper surface: the drip flashing lies on it and the underlayment laps over
# the flashing, so nothing in the chain may stand above this plane or the underlayment
# cannot bond to the deck it is sealing.
_DRIP_CEILING_IN = 7.165 * _SLOPE_FACTOR     # 7.55" — top-deck surface, vertical
_CLADDING_HEAD_IN = 7.475 * _SLOPE_FACTOR    # 7.88" — roofing underside == wall panel heads

# The derived corner trim (resolve/roof_trim.py::_corner_trim_members): a formed angle 1.25"
# deep in plan, hung outboard of the footprint edge, with a leg down over the wall panel
# heads. Its sheet's *inner* face and its lower edge are the two faces everything below
# registers against.
#
# **Both numbers are transcriptions of the resolver's, and both were wrong.** The leg was
# read as 2" — it went to 4" when the rake trim had to double as a barge board — so every
# piece hung below it sat 2" high, and the trough's rim ended up above the trim's lower edge
# instead of a lap under it. And the trim was read as a solid 1.25" billet, when
# ``trim_bands.formed_edge_bands`` makes it sheet metal: the face is one shell thick at the
# *outboard* side of that 1.25", which left the whole 0.42" of it for the gutter's back sheet
# to be drawn inside of. Two pieces of metal, one place.
_TRIM_FACE_IN = 1.25
_TRIM_LEG_IN = 4.0                           # resolve/roof_trim.py::_CORNER_TRIM_LEG_M
#: The formed face's own thickness — ``trim_bands``' shell rule, which at a 4" leg is only
#: ever bounded by the plan depth.
_TRIM_SHEET_IN = min(0.5, _TRIM_FACE_IN / 3.0)          # 0.42"
_TRIM_BOTTOM_IN = _CLADDING_HEAD_IN - _TRIM_LEG_IN      # 3.88" above the deck plane

#: The coil the whole chain is ordered in (2026-08-01). The derived corner trim above it is
#: already `RF-HOUSE.edge_trim_material` — the house's one exterior dark — and the gutter hangs
#: directly under it on the eaves, 6" of it, so leaving the trough in mill aluminium put a pale
#: grey band along the two edges where the dark outline is supposed to be continuous: the rakes
#: read black and the eaves read weak grey. The leader takes the same coil, as a gutter's leader
#: does. Ordinary stock — every gutter manufacturer's colour card carries the roof coil's darks.
_CHAIN_MATERIAL = "metal-dark-exterior"

#: The overlap every joint in the chain takes. Half an inch is also the thickness the
#: boxes-only IR draws sheet metal at (resolve/trim_bands.py::GUTTER_SHELL_M), so a lap of
#: one nominal shell is the smallest one that still reads as a lap in the model.
_LAP_IN = 0.5

# --- Box gutter ---------------------------------------------------------------------------
# 6" of trough, hung with its back sheet tucked a lap *behind* the corner trim's outer face,
# so the trim's lower leg sheds onto the back sheet rather than past it into the gap. The rim
# rides a lap above the trim's bottom edge — high enough to make that lap, low enough to
# stay clear of the top deck (the rim must stay under _DRIP_CEILING_IN, or the gutter lifts
# the underlayment off the deck it has to bond to).
_GUTTER_THICK_IN = 6.0                       # channel width, out from the back sheet's face
_GUTTER_DEPTH = inch(5)                      # channel height
#: Inner face of the back sheet. A lap *behind* the trim's face means behind the face's own
#: sheet, not behind the plan depth that sheet hangs at the end of.
_GUTTER_BACK_IN = _TRIM_FACE_IN - _TRIM_SHEET_IN - _LAP_IN   # 0.33"
_GUTTER_RIM_IN = _TRIM_BOTTOM_IN + _LAP_IN                   # 4.38" above the deck plane

#: Mid-width of the trough — where a drip wants to land, being the furthest it can be from
#: both the back sheet and the front lip. The shell closes a half-shell at each side.
_TROUGH_MID_IN = _GUTTER_BACK_IN + _LAP_IN + (_GUTTER_THICK_IN - 2.0 * _LAP_IN) / 2.0

# --- Drip edge ----------------------------------------------------------------------------
# A bent angle (resolve/trim_bands.py::drip_edge_bands): a flat leg lying **on the top deck**
# and running out over the trough, with a turn-down at its outboard end.
#
# It used to be derived upward from the gutter's rim — a lap above it — which put a drip edge
# in mid-air 0.7" clear of the roof it drains, its inboard end a whole inch *outboard* of the
# deck's own edge. That is backwards. A drip edge is a roof-plane piece: it is nailed to the
# deck, the field underlayment is lapped over its flange, and only then does its turn-down
# reach down into the trough. So the flange lands on ``_DRIP_CEILING_IN`` and everything else
# follows from where the deck is, not from where the gutter ended up.
#: How far the flange runs back onto the deck from the roof edge — ordinary drip-edge stock.
_DRIP_DECK_BEARING_IN = 1.5
_DRIP_INNER_IN = -_DRIP_DECK_BEARING_IN
_DRIP_THICK_IN = _TROUGH_MID_IN + _LAP_IN / 2.0 - _DRIP_INNER_IN
#: The flange's *underside* is the deck surface; the drawn shell is a lap thick, so the top
#: face — the one the underlayment bonds over — stands exactly one nominal sheet above it.
_DRIP_TOP_IN = _DRIP_CEILING_IN + _LAP_IN
#: Deep enough to reach a lap below the trough's rim from a flange that now starts three
#: inches higher up, and still stop well above the floor.
_DRIP_DEPTH = inch(5.5)


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
        thickness=inch(_DRIP_THICK_IN), material=_CHAIN_MATERIAL,
        host_ref="RF-HOUSE", back_side=back_side)
    gutter = Gutter(
        uid=f"RTGT0{index}AAAA", tag=f"TR-RF-GUTTER-{side}", kind=TrimKind.GUTTER,
        path=_run(out(_GUTTER_BACK_IN + _GUTTER_THICK_IN / 2.0)),
        top_elevation=_above_deck(_GUTTER_RIM_IN), depth=_GUTTER_DEPTH,
        thickness=inch(_GUTTER_THICK_IN), material=_CHAIN_MATERIAL, host_ref="RF-HOUSE",
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
        material=_CHAIN_MATERIAL, gutter_ref=f"TR-RF-GUTTER-{side}",
        # Four clamps at roughly 6' o.c. down the ~24' run (plan/mep.py::LEADER_CLAMPS).
        clamp_refs=tuple(f"CN-A-LEADER-{side}{n}" for n in (1, 2, 3, 4)))


ATTIC_ELEMENTS = [
    *_eave_water("W", 1, _EAVE_X_W, -1.0), *_eave_water("E", 2, _EAVE_X_E, 1.0),
    _leader("W", 1, _EAVE_X_W, -1.0), _leader("E", 2, _EAVE_X_E, 1.0),
]
