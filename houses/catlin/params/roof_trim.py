"""House-roof eave water management — the box gutter and its lap chain (Tier 2, WP roof-eave).

The RF-HOUSE eave edges (ridge runs N-S, so the eaves are the WEST and EAST footprint
edges) get the water-management pieces the derived roof-edge trim does NOT provide.

**RF-HOUSE has no fascia at all**, and that is the fact every offset here is measured from.
Its standing-seam siding and standing-seam roofing are one continuous skin over a flush
zero-overhang edge, so ``resolve/roof_trim.py`` takes the ``continuous_skin_cladding`` path:
no fascia boards, no soffit, no edge band. ``RF-HOUSE.eave_trim.drip_edge`` then derives
ONE formed drip edge per edge (``resolve/roof_drip_edge.py``): a flange on the deck at the
6:12 pitch, a nose over the deck edge, a face on the old corner trim's plane (1.25" out,
its sheet 0.42" thick) with a 4" leg down over the wall panel heads, and a kick into the
trough. It is derived because it has to rake: an authored ``Flashing`` has one elevation.

The chain, in which **every higher piece sheds onto the next lower one** so water can never
get behind the siding:

    roofing → formed drip edge (derived) → box gutter → downspout

- a 6" BOX GUTTER hung **tight to the wall plane** — its back sheet tucked *behind* the drip
  edge's face rather than standing off in mid-air, which is what closes the open slot that
  used to run the length of the eave; the drip's kick lands inside the trough;
- a DOWNSPOUT per eave, because the gutters slope to one, plus the S-5! securement clamps
  (plan/mep.py) that steady it.

Every joint takes the same nominal ``_LAP_IN`` of overlap, and each piece's elevation is
derived from the one above it rather than authored, so the chain cannot be broken by
changing one number in isolation.

The reference mounts the gutter the same way: `gutter_back_x = x_fur1 + furring_wall - 0.2`
puts the back sheet essentially *on* the cladding plane, with the roofing running out past
it so the water has to fall inside.

RF-HOUSE has zero authored overhang, so no soffit exists or is needed. The garage's drip
edge and K-gutter derive from its own ``EaveTrim`` (plan/storeys/garage.py).

Not `# haus: editable`: trim runs are not UI-movable elements (only params-generated
geometry lives here), so the editable-writeback rule does not apply.

Geometry facts this module derives from (see plan/storeys/attic.py + plan/assemblies.py):
- sheathing-ext datum plane at x = 0 / 36'; wall stack outboard of it =
  ccSPF 4" + vent gap 0.5" + outer girt 1.5" + PBR 1.25" = 7.25" (``_WALL_OUTBOARD_IN``;
  cladding face == roof footprint edge, where eave_z_m is defined) — and the footprint runs
  to that same face in **y** as well, which is how far the eave runs have to reach to close
  the corner;
- RAFTER-PLATE top at 20'-2 1/4" (attic datum 20'-0" + 3/4" subfloor + 1 1/2" of 2x6 laid
  flat, no knee wall — see plan/assemblies.py's RAFTER_PLATE); deck plane (eave_z_m)
  rides the I-joist rise above it: 11.875" - 5.5" x 6/12 seat drop = 9.125", so eave_z is
  20'-11 3/8";
- roof stack above the deck (perpendicular): 5/8" CDX plywood (deck surface at 0.625") ->
  0.04" adhered butyl membrane -> metal 0.5". That is the whole of it. The 6:12 slope factor
  turns those perpendicular offsets into the vertical ones an authored elevation is
  measured in;
- the wall cladding's head lands at the roofing's own underside (MatingFaces with a
  continuous skin), 0.665" perpendicular above the deck plane.

The roof is 5/8" plywood straight on the I-joists with a fully-adhered butyl membrane on it
and the panel clipped to that (plan/assemblies.py ROOF, flash-and-batt in the bay
under IRC R806.5 item 5.1.3).

**The chain hangs from the deck top, 0.625" above the deck plane.** The drip edge's flange
lies ON the structural deck and the membrane laps OVER it. One consequence worth stating,
because it looks wrong at a glance and is not: the drip edge's foot and the gutter's rim are
BELOW the deck plane (``_TRIM_BOTTOM_IN`` is negative). The face's 4" leg laps DOWN over
the wall panel heads, and with only 0.67" of roof stack above the deck there is nowhere else
for 4" of leg to go.
"""

from __future__ import annotations

import math

from typehaus import DischargeExtension, Downspout, Flashing, Gutter, TrimKind, ft, inch, pt

_HOUSE_FT = 36.0
# Wall layers outboard of the sheathing-ext datum -> the cladding outer face, which is
# exactly the roof footprint edge (the zero-overhang roof laps the cladding).
#
# **The one constant the cladding face is measured by**, and deliberately spelled as the
# stack it is: 4" ccSPF (around the three-ply standoff blocks) + 1/2" vent gap +
# 1 1/2" outer girt + 1 1/4" PBR panel (plan/assemblies.py EXT_2X6; one girt tier since
# 2026-09-01). A ribbed panel
# stands off by its rib height, where a snap-lock pan stands off by its pan. Every param in
# this house that measures off the cladding moves with it.
#
# The values it has had, kept beside it so the revert is a line and not a re-derivation:
#   6.5"  — the girts under 1/2" snap-lock seam
#   5.5"  — the Swinburne truss: 1.5 foam + 3.5 outrigger band + 0.5 seam
#   5.02" — the CI boards before it: 0.02 WRB + 2" polyiso + 2" EPS + 0.5 furring + 0.5 seam
_WALL_OUTBOARD_IN = 4.0 + 0.5 + 1.5 + 1.25  # 7.25"
_EAVE_X_W = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_X_E = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)

# ** 20'-2 1/4", NOT 25'-0". ** The eave is a 2x6 laid FLAT on the attic deck
# (RAFTER_PLATE, no knee wall), so the plate top is the attic datum plus 3/4" of
# subfloor plus 1 1/2" of plate. Everything in this module hangs off it.
_PLATE_TOP = ft(20, 2.25)
_DECK_RISE_IN = 11.875 - 5.5 * (6.0 / 12.0)  # I-joist depth - 2x6 seat drop = 9.125"
_EAVE_DECK = _PLATE_TOP + inch(_DECK_RISE_IN)  # deck plane at the eave edge (eave_z_m)

# The roof stack is offset perpendicular to the slope; an authored elevation is vertical.
_SLOPE_FACTOR = math.hypot(1.0, 6.0 / 12.0)  # 6:12 -> 1.1180
#: The values this has had, kept beside it so the revert is a line and not a
#: re-derivation: 7.475 under the screwed nailbase over 6" of polyiso, 4.25 under the vented
#: batten roof before it.
_CLADDING_HEAD_IN = 0.665 * _SLOPE_FACTOR    # 0.74" — roofing underside == wall panel heads

# The derived drip edge's FACE (resolve/roof_drip_edge.py, on the plane the corner trim it
# replaced stood on): 1.25" out from the footprint edge, one sheet thick at the outboard side
# of that, with a 4" leg down over the wall panel heads. Its sheet's *inner* face and its
# foot are the two faces everything below registers against.
#
# **Both numbers are transcriptions of the resolver's.** Reading the leg as 2" once hung
# every piece below it 2" high, and reading the face as a solid 1.25" billet drew the
# gutter's back sheet inside it. Two pieces of metal, one place.
_TRIM_FACE_IN = 1.25                         # resolve/roof_trim.py::_CORNER_TRIM_THICKNESS_M
_TRIM_LEG_IN = 4.0                           # resolve/roof_trim.py::_CORNER_TRIM_LEG_M
#: The formed face's own thickness — ``trim_bands``' shell rule, bounded by the plan depth.
_TRIM_SHEET_IN = min(0.5, _TRIM_FACE_IN / 3.0)          # 0.42"
#: NEGATIVE, and correctly so: a 4" leg hung from a roofing underside only 0.74" above the
#: deck reaches 3.26" BELOW it, lapping down over the wall panel heads.
_TRIM_BOTTOM_IN = _CLADDING_HEAD_IN - _TRIM_LEG_IN      # -3.26"

#: The coil the whole chain is ordered in — `RF-HOUSE.edge_trim_material`, the house's one
#: exterior dark, which the derived drip edge is already in. A mill-aluminium trough under it
#: put a pale band along the eaves where the dark outline is supposed to be continuous. The
#: leader takes the same coil, as a gutter's leader does.
_CHAIN_MATERIAL = "metal-dark-exterior"

#: The overlap every joint in the chain takes. Half an inch is also the thickness the IR
#: draws sheet metal at (resolve/trim_bands.py::GUTTER_SHELL_M), so a lap of one nominal
#: shell is the smallest one that still reads as a lap in the model.
_LAP_IN = 0.5

# --- Box gutter ---------------------------------------------------------------------------
# 6" of trough, hung with its back sheet tucked a lap *behind* the drip edge's face, so the
# face and its kick shed into the trough rather than past it into the gap. The rim rides a
# lap above the face's foot — high enough to make that lap, low enough to stay clear of the
# deck top (or the gutter lifts the underlayment off the deck it has to bond to).
_GUTTER_THICK_IN = 6.0                       # channel width, out from the back sheet's face
_GUTTER_DEPTH = inch(5)                      # channel height
#: Inner face of the back sheet. A lap *behind* the face means behind the face's own sheet,
#: not behind the plan depth that sheet hangs at the end of.
_GUTTER_BACK_IN = _TRIM_FACE_IN - _TRIM_SHEET_IN - _LAP_IN   # 0.33"
_GUTTER_RIM_IN = _TRIM_BOTTOM_IN + _LAP_IN                   # -2.76"

#: Mid-width of the trough, where the leader takes its outlet. The shell closes a half-shell
#: at each side.
_TROUGH_MID_IN = _GUTTER_BACK_IN + _LAP_IN + (_GUTTER_THICK_IN - 2.0 * _LAP_IN) / 2.0


def _above_deck(vertical_in: float):
    """An absolute elevation from a vertical offset above the deck plane at the eave."""
    return _EAVE_DECK + inch(vertical_in)


# The eaves run the full roof footprint, which reaches the *cladding* face at both gable
# ends — not the sheathing datum. Stopping at ft(0)/ft(36) left 7.25" of open roof stack
# at each rake corner with no gutter under it, which is the hole the 3D view showed.
_EAVE_Y0 = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_Y1 = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)


def _run(x):
    return (pt(x, _EAVE_Y0), pt(x, _EAVE_Y1))


def _eave_water(side: str, index: int, eave_x, outward: float):
    """One eave edge's box gutter; ``outward`` is -1 west / +1 east.

    Both runs go south→north (+y), whose left-hand normal (resolve/geometry.py::normal,
    90 deg CCW) points west (-x). The house is east of the west eave and west of the east
    eave, so the building is on the *right* of the west run and on the *left* of the east
    run — which is what tells the gutter which sheet is its back.
    """
    back_side = "right" if outward < 0 else "left"

    def out(inches_val: float):
        offset = inch(inches_val)
        return eave_x + offset if outward > 0 else eave_x - offset

    return Gutter(
        uid=f"RTGT0{index}AAAA", tag=f"TR-RF-GUTTER-{side}", kind=TrimKind.GUTTER,
        path=_run(out(_GUTTER_BACK_IN + _GUTTER_THICK_IN / 2.0)),
        top_elevation=_above_deck(_GUTTER_RIM_IN), depth=_GUTTER_DEPTH,
        thickness=inch(_GUTTER_THICK_IN), material=_CHAIN_MATERIAL, host_ref="RF-HOUSE",
        slope=f'1/16 in/ft to the north-end {side} downspout',
        downspout_ref=f"TR-RF-LEADER-{side}",
        back_side=back_side)


# --- Downspouts ---------------------------------------------------------------------------
# One 4" round leader per eave. Each eave sheds half the roof: 18' of run x 36' = 648 sq ft.
# Minneapolis' short-duration design intensity is around 8 in/hr, and at that rate a 3"
# leader is good for roughly 425 sq ft — not enough — while a 4" round still clears 648. So
# 4", not the more usual 3".
#
# Both go to the NORTH end, discharging into the 4' gap toward the garage rather than onto
# the freestanding sunken-garden structure 5" off the south face. Each hangs on the trough's
# centre line, so it takes the outlet straight down out of the gutter floor. Each runs to its
# buried extension's riser and on to its own rain garden, mirrored about x=18'-0"
# (`_discharge`). The S-5! CanDuit clamps that
# hold it to the standing-seam siding are in plan/mep.py; per the reference they steady the
# leader and are explicitly not its primary support.
_LEADER_DIA_IN = 4.0
_LEADER_Y = ft(_HOUSE_FT) - inch(6.0)
# The riser from +1'-0" down to the extension's inlet bills with the extension.
_LEADER_BOTTOM = ft(1)


def _leader(side: str, index: int, eave_x, outward: float):
    offset = inch(_TROUGH_MID_IN)
    x = eave_x + offset if outward > 0 else eave_x - offset
    return Downspout(
        uid=f"RTDS0{index}AAAA", tag=f"TR-RF-LEADER-{side}",
        position=pt(x, _LEADER_Y),
        top_elevation=_above_deck(_GUTTER_RIM_IN) - _GUTTER_DEPTH,
        bottom_elevation=_LEADER_BOTTOM,
        diameter=inch(_LEADER_DIA_IN),
        material=_CHAIN_MATERIAL, gutter_ref=f"TR-RF-GUTTER-{side}",
        # Four clamps at roughly 6' o.c. down the ~24' run (plan/mep.py::LEADER_CLAMPS).
        clamp_refs=tuple(f"CN-A-LEADER-{side}{n}" for n in (1, 2, 3, 4)),
        **_discharge(side, x))


# 4" solid PVC buried north to a pop-up emitter in the side's basin
# (params/landscape_gardens.py), the east run the west's mirror about x=18'-0". The WEST run
# passes west of SL-M-HP3PAD in open yard; the EAST one passes under walks D and C, so its
# inlet drops 8" to put the pipe's crown under their Class 5 base (-3'-7"). Both outlets
# stand within 2" of the basin floor (-4'-1"). notes/rain_garden_sizing.md §6.
# The WEST line also carries SM-B-RADON's pumped water: PR-B-SUMP-DISCH wyes into its riser
# at -1'-10" (plan/mep_drainage.py), so that basin takes groundwater too.
_INVERTS = {"W": (ft(-3, -4), ft(-3, -11)), "E": (ft(-4), ft(-4, -2))}


def _discharge(side: str, leader_x) -> dict:
    def mx(x_ft: float):
        return ft(x_ft) if side == "W" else ft(_HOUSE_FT - x_ft)

    inlet, outlet = _INVERTS[side]
    return dict(
        discharge_ref=f"RG-{side}-BASIN",
        extension=DischargeExtension(
            path=(pt(leader_x, _LEADER_Y), pt(mx(-1.5), ft(36, 2)),
                  pt(mx(-1.5), ft(46, 6)), pt(mx(-3.5), ft(49))),
            diameter=inch(4), material="pvc-sdr35",
            inlet_invert=inlet, outlet_invert=outlet))


# FORTIFIED Roof §4.5's drip at every eave AND rake is the derived drip edge on all four
# RF-HOUSE edges (checks/structural/fortified_roof.py grades its flange on the deck).
ATTIC_ELEMENTS = [
    _eave_water("W", 1, _EAVE_X_W, -1.0), _eave_water("E", 2, _EAVE_X_E, 1.0),
    _leader("W", 1, _EAVE_X_W, -1.0), _leader("E", 2, _EAVE_X_E, 1.0),
]


# --- the four wall corners, where board & batten meets PBR ---------------------------------
#
# ** THE ENGINE MODELS NO WALL-TO-WALL CORNER TRIM AT ALL. ** ``corner_trim`` in
# ``takeoff/edge_trim.py`` is exclusively the ROOF-edge piece, the one this module's
# docstring describes, derived by ``resolve/roof_trim.py`` from the ROOF's cladding — it
# never consults a wall material. So the PBR-to-board-&-batten corner did not error and did
# not pick the wrong metal: it simply billed nothing. That gap is closed here.
#
# ** WHY THIS IS IN ``params/`` AND NOT AN EDITABLE PLAN FILE. ** Every offset below is
# measured off ``_WALL_OUTBOARD_IN``, the one constant the cladding face is measured by, and
# the whole hazard this house already carries is that four *other* consumers of that face
# hand-transcribe it (breezeway, sunken garden, the exterior devices, and this module's own
# eave lines). The editable dialect forbids arithmetic, so authoring these in ``plan/`` would
# mean transcribing 7 1/4" a fifth time. Derived here they move with the face; the cost is
# that they are read-only in the UI, which is right for a piece that has no position of its
# own — it is wherever the corner is.
#
# The SOLID needs no special case and gets none: a ``Flashing`` resolves as a vertical band
# of height ``depth`` swept along its plan path, which for these is 8" of developed coil
# swept the full height of the corner. The TAKE-OFF did need one — ``_EdgeRun.path`` is a
# PLAN polyline and ``edge_trim_takeoff`` measured every run along it, so billed that way
# these four came to 2.7 LF between them instead of 89.5. ``Flashing.vertical`` swaps which
# axis is the run and which is the cross-section, mirroring ``GlazingTrim.vertical``, which
# has carried exactly this fix for a jamb channel since it existed.
_CORNER_LEG_IN = 4.0
#: 21'-3" — the attic wall's top at every corner. All four land on the EAVE line and none on
#: a gable rake (the ridge runs north-south), so the four runs are the same length.
_CORNER_TOP = inch(255.0)
#: Down to the resolved wall base, -1'-1 7/16" — the bottom of the cladding, not the datum.
_CORNER_RUN = inch(255.0 + 13.4375)


def _wall_corner(name: str, index: int, x, y, x_sign: float, y_sign: float):
    """One formed outside corner: a 4" leg onto each face, meeting at the cladding corner.

    8" of developed coil, one bend either side — the cheapest piece in either manufacturer's
    wall-trim kit, and the same 4" leg the derived roof corner uses (``_TRIM_LEG_IN``).
    Black (``metal-dark-exterior``) since 2026-09-23, to match the window trim; it was the
    board & batten's own coil before.
    """
    return Flashing(
        # `haus fmt` never visits `params/*.py`, so `uid=""` here would stay empty and
        # collide every GlobalId — the uids are authored on the same structured pattern the
        # eave chain above uses, and `integrity.duplicate_uid` is a hard load-time ERROR if
        # one of them is ever reused.
        uid=f"RTWC0{index}AAAA", tag=f"TR-H-CORNER-{name}",
        kind=TrimKind.WALL_CORNER, vertical=True,
        path=(pt(inch(x.inches + x_sign * _CORNER_LEG_IN), y),
              pt(x, y),
              pt(x, inch(y.inches + y_sign * _CORNER_LEG_IN))),
        top_elevation=_CORNER_TOP, depth=_CORNER_RUN, thickness=inch(_TRIM_FACE_IN),
        material="metal-dark-exterior")


#: Filed on ``main`` rather than ``attic``: the run starts below the main datum and the
#: storey is a container, not a height.
MAIN_ELEMENTS = [
    _wall_corner("SW", 1, _EAVE_X_W, _EAVE_Y0, 1.0, 1.0),
    _wall_corner("SE", 2, _EAVE_X_E, _EAVE_Y0, -1.0, 1.0),
    _wall_corner("NE", 3, _EAVE_X_E, _EAVE_Y1, -1.0, -1.0),
    _wall_corner("NW", 4, _EAVE_X_W, _EAVE_Y1, 1.0, -1.0),
]
