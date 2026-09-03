"""Breezeway — the enclosed 8' x 4' x 4' polycarbonate shelter between house and garage.

One freestanding structure spanning the 4'-0 1/2" slot between the house's north entry
(``D-M-ENTRY``, centred on x = 4'-0") and the garage's service door (``D-G-SERVICE``,
centred on x = 5'-0"). It touches neither building: four 6x6 ground-contact posts on
isolated piers and frost-depth pads carry the whole thing, and the glazing is *snug* to the
house and garage cladding without lapping into either one's flashing.

**"8 x 4 x 4" is the brief, and this module means it literally.** The glazed
enclosure is 8'-0" tall x 4'-0" N-S x 4'-0" E-W. The three dimensions are measured on the
*enclosure*: the foundations below the floor-beam soffit are excluded (they are ground work,
not room), and so is the ~1" wedge bulge that crowns the roof for drainage.

That reading falls straight out of the sheet:

* A standing sheet is a 4'x8' sheet stood on end and **uncut**: 4'-0" wide N-S, exactly
  8'-0" tall, from the floor-beam soffit (-7 1/4") to the roof sheet's underside
  (+7'-4 3/4"). Nothing of the framing shows below it and nothing of the elevation is open
  above it.
* The E-W extent is 4'-0" glazing line to glazing line, centred on x = 8'-0" — the shared
  centre of the house entry and the garage service door, which are concentric — so the
  glazing runs x = 6'-0" to 10'-0".
* The roof is **one** 4'-0" x 4'-0" sheet: half of an 8'x4', cut once.

The bill is therefore three sheets for the enclosure itself, and only one cut among them:
two 8'x4' sheets standing whole, one 8'x4' halved for the roof. Three sheets is the whole
bill: the gap under the deck is left open rather than skirted.

The two sheets meet, so one ``profile="H"`` channel per side receives both — the wall sheet
in its lower slot, the roof sheet in its upper — replacing the eave U and the wall F-head.

**What that costs, stated rather than left implicit:**

* The roof does not oversail the glazing line as a drip edge; it dies *in* the shared
  channel, so the sill U-channel's weep holes are the assembly's only drainage path.
* **Headroom is now honest rather than generous.** Clear under the rafters is ~7'-3 1/4",
  but the roof beams run N-S at x = 6'-2 3/4" / 9'-9 1/4" and their soffit is at +6'-3 1/2" —
  *below* a 6'-8" door head. Those two beams sit on the glazing lines at the very edges of
  the walk-line, which runs door to door (N-S) up the middle of the 4'-0" width, so a person
  passes between them and not under them. Anyone reaching for the west or east glazing ducks.
  This is a deliberate consequence of measuring the 8' on the sheet.
* The garage-eave clearance: the garage's south fascia underside is at +9'-11.4" and this
  roof tops out around +7'-5 1/2", so ~2'-6" of air.

Framing directions (the brief's "opposite rotation"):

    FLOOR PLAN (main, z = 0'-0")           ROOF PLAN (z = +6'-10 3/4")
     garage stem                            garage cladding
     |===================|  N-S floor       |===================|  N-S roof beams
     |-------------------|  beams on        |-------------------|  on the post tops
     |-------------------|  the post        |-------------------|  E-W rafters
     |===================|  lines           |===================|  crown at x = 8'-0"
     house      E-W joists @ 16"            house    (wedges on every rafter)
                deck boards N-S

**Grade and the frost pads.** The breezeway's *foundations* are pinned to the soil — the
pads bear at 42" below grade, so the piers carry that full depth — and nothing above
``_FLOOR_BEAM_TOP`` follows grade at all, because this is a bridge between two doors and
both thresholds are at 0'-0". Two consequences:

* **The 1'-10 3/4" that opened up under the deck stays open.** The deck is a bridge
  between two doors, nothing under it is enclosed space, and everything down there —
  ground-contact posts on isolated piers, PT beams and joists — is detailed to be exposed
  and to dry. The enclosure is the 8'-0" of sheet above the deck; below it is open air.
* **No guard is required, and none is authored.** The walking surface is 2'-6" above grade,
  right at IRC R312.1's trigger, and ``structural.deck_guard`` grades it a PASS at exactly
  30". The question the number raises is answered by the enclosure rather than by the
  number: all four sides are closed — 8'-0" of glazing east and west, a door at each end —
  so there is no open edge to fall from. A guard on a glazed vestibule would be a rail
  inside a wall.

Three places this deviates from the brief or from the plan it was built to, each on purpose:

1. **Joists are on edge, not laid flat.** The brief guessed "flat wide side on beam". A
   flat-laid 2x cannot make the 7'-0" joist span — DCA6 Table 3A tabulates a 2x8 on edge at
   10'-7" and has no row at all for one on its side — so they stand up like any deck joist.
2. **Joists hang flush in the beams rather than sitting on them.** Stacking would double
   the framing depth to 14 1/2" and put the beam soffit in a trench, since the deck surface
   has to meet the house threshold at 0'-0". Flush framing keeps the whole assembly 7 1/4"
   deep, which is why the beams carry an explicit ``top_elevation``: that is the authored
   declaration ``structural.member_interference`` reads to tell this joint from the
   elevation bug it otherwise looks exactly like.
3. **The wedges carry the E-W crown, and nothing else. There is no N-S fall in this roof.**
   The 1" house-to-garage slope this module used to carry was never a roof question: it was
   *walkway* drainage, and the walkway is a composite deck. A composite plank drains through
   the gaps between boards, so that is where it drains (see ``PORCH_DECK_COMPOSITE`` and
   ``FLOOR``'s subfloor below), and the roof is left doing the one job a roof does —
   shedding east and west off a crown. The wedges are real framing now (``WEDGES``), not a drawing.

The 22" step at the garage door is resolved elsewhere, not here: ``D-G-SERVICE``
now carries the same negative ``sill_height`` ``D-G-OVERHEAD`` always did, so it opens off
the garage slab at 0'-0" like this deck does, and ``params/foundations.py`` gaps the ICF stem
to a grade beam under it the same way it does under the vehicle door. The deck's +1" walking
surface is 1" above that threshold, inside R311.3.1's 1 1/2".
"""

from __future__ import annotations

from typehaus import (
    Beam,
    Connector,
    ConnectorKind,
    DeckLayer,
    FloorSystem,
    GlazingPanel,
    GlazingTrim,
    JoistSpec,
    Node,
    Pad,
    Post,
    TrimKind,
    Wedge,
    ft,
    inch,
    pt,
)

from params.foundations import SITE_GRADE
from plan.storeys.garage import GARAGE_Y_SOUTH

# ============================================================================
# Plan geometry — every number here is derived, never repeated.
# ============================================================================
# North face of the house's outsulated wall: the y=36' sheathing plane plus the whole
# catlin-truss stack — 1 1/2" band A foam, the 1 1/2" inner girt, 1" of band C foam, the
# 1/2" vent gap, the 1 1/2" outer girt and 1 1/4" of PBR panel (plan/assemblies.py
# CATLIN_EXT_2X6, and params/roof_trim.py::_WALL_OUTBOARD_IN, which is the same number).
# This is what the breezeway's south end butts. When this stack's thickness changes, the
# garage moves with it (plan/storeys/garage.py) so the slot below does not lose its reveal.
_HOUSE_CLADDING_Y = 36.0 + 7.25 / 12.0  # 36.6042'

# South face of the garage's ICF stem: the wall line itself. The 11" section is aligned so
# its exterior EPS face lands on the node line, coplanar with the SHEATHING face of the wood
# wall above (params/foundations.py), so the stem is no longer the proud face here — the
# cladding is, 7/8" south of it. It keeps its own name because the deck still butts *this*
# plane, tucked under that 7/8" of overhang.
_GARAGE_STEM_Y = GARAGE_Y_SOUTH.feet  # 40.71875'
# South face of the garage's wood wall above the stem: the corrugated panel straight on the
# sheathing plane. That is the obstruction now, at deck level and at roof level both, so it
# is what sets the clear gap. 0.875" is GARAGE_WALL_2X6's 7/8" corrugated exposed-fastener
# panel; the wall's `alignment` puts whichever sheathing it carries on the node line, so a
# cladding-thickness change here has to move with a matching edit to the garage's wall
# lines to keep _CLEAR_GAP_FT and the reveal below correct.
_GARAGE_CLADDING_Y = GARAGE_Y_SOUTH.feet - 0.875 / 12.0  # 40.6458'

_CLEAR_GAP_FT = _GARAGE_CLADDING_Y - _HOUSE_CLADDING_Y  # 4.04167' = 4'-0 1/2"
_PANEL_FT = 4.0  # one 4'x8' sheet, UNCUT in the N-S direction

#: The reveal the glazing is held off the garage cladding by, so the sheet has somewhere to
#: go and the north F-channel has a thickness. **It is free, and it is DERIVED**: the slot
#: is 1/2" wider than the sheet, so what an uncut sheet does not fill is the reveal. Nothing
#: authors it, which is the point — it is a leftover, and if it ever goes to zero the sheet
#: stops being glazeable and this line goes negative rather than lying about it.
#:
#: If the slot ever closes, spend it by moving the garage's two wall lines rather than
#: ripping the sheet — a 24'x24' garage on open ground 40' from any setback does not care
#: where it stands to the half inch. See plan/storeys/garage.py::GARAGE_Y_SOUTH.
_REVEAL_FT = _CLEAR_GAP_FT - _PANEL_FT  # 0.04167' = 1/2"

# N-S: the FRAME line — the deck edge, the beam ends, the rafter stations. Snug to the
# house cladding and the garage cladding, since the most-proud face at each end is what the
# structure has to clear. This is where the posts used to stand as well; see below.
_POST_HALF_FT = 5.5 / 24.0  # half a dressed 6x6
_FRAME_Y0 = _HOUSE_CLADDING_Y + _POST_HALF_FT  # 36.8333'
_FRAME_Y1 = _GARAGE_CLADDING_Y - _POST_HALF_FT  # 40.4167'

# ---------------------------------------------------------------------------
# **The posts do NOT stand on the frame line. The foundations would not fit.**
#
# A pier pad under the frame line lands inside the building it is beside. Both ends, and
# neither was visible to any rule in the engine — `structural.member_interference` excludes
# slab/footing/pad solids on purpose (a beam legitimately bears into concrete) and a
# FoundationWall contributes no framed members, so concrete against concrete was ungraded.
# With 2'-0" pads on the frame line the numbers were:
#
#   PD-BW-1/2 -> W-B-N*  house basement wall   6 1/16" of plan overlap, the pad's full 12"
#                                              of thickness inside the wall's own band
#   PD-BW-3/4 -> W-GF-S* garage ICF stem       8 3/8" of plan overlap, likewise
#   PR-BW-3/4 -> W-GF-S* garage ICF stem       1 5/8" over 4'-0" of shared height
#
# `structural.concrete_interference` grades it now, and this is the fix it asked for:
# **shrink the pads to their real load and move the posts inboard**, letting the two floor
# beams and the two roof beams cantilever the remainder out to the frame line. Nothing above
# the beams moves — the enclosure, the deck, the sheets and the rafters are all measured off
# the frame line, and the frame line is untouched.
#
# The band a pad may live in is measured at PAD DEPTH, not at grade:
#   * house side — the basement wall's outboard XPS face, y = 36' sheathing plane +
#     CATLIN_BASEMENT_8's 4.05" of damp-proof + 2x 2" XPS (plan/assemblies.py). The
#     protection panel outboard of it stops 6" below grade, ~3' above these pads, so it is
#     not what a pad has to clear.
#   * garage side — the ICF stem's outboard EPS face, which is the node line itself
#     (`_GARAGE_STEM_Y`). Its coil-gap/coil-ext layers stop at -3'-0", also above the pads.
_HOUSE_FOUNDATION_Y = 36.0 + 4.05 / 12.0  # 36.3375'
_PAD_BAND_FT = _GARAGE_STEM_Y - _HOUSE_FOUNDATION_Y  # 4.38125' = 4'-4 9/16"

# **The pads were enormously oversized.** `structural.deck_footing_size` graded the 2'-0"
# square pads at 4.00 ft2 against an IRC R507.3.1 requirement of 1.00 ft2 — and that 1.00 is
# already the 12" minimum side, not the load: 3.2 ft2 tributary at 50 psf on 1500 psf soil
# needs 0.11 ft2. 1'-4" is the size chosen: 1.78 ft2, comfortably over both the load and the
# 12" minimum, and 2" of ledge all round the 12" round pier it carries.
_PAD_SIDE_FT = 16.0 / 12.0
_PAD_HALF_FT = _PAD_SIDE_FT / 2.0
_FORM_CLEAR_FT = 2.0 / 12.0  # working room between a pad edge and the wall it stands beside

# The widest post spacing the band will take, and then the round number just inside it.
# Wider is better — every inch of spacing is an inch off the cantilevers — so this is at the
# practical maximum rather than picked for looks.
_POST_SPACING_MAX_FT = _PAD_BAND_FT - 2.0 * (_PAD_HALF_FT + _FORM_CLEAR_FT)  # 2.7146'
_POST_SPACING_FT = 2.0 + 8.0 / 12.0  # 2'-8"
_POST_MID_Y = (_HOUSE_FOUNDATION_Y + _GARAGE_STEM_Y) / 2.0  # 38.5281', the band's centre
_POST_Y0 = _POST_MID_Y - _POST_SPACING_FT / 2.0  # 37.1948'
_POST_Y1 = _POST_MID_Y + _POST_SPACING_FT / 2.0  # 39.8615'
# The beams cantilever the rest: 0.3615' (4 11/32") at the house end and 0.5552' (6 21/32")
# at the garage, against IRC R507.5.2's ceiling of a quarter of the 2.6667' actual beam span
# = 0.6667'. Both clear; the north one uses 83% of its allowance.
#
# The two are UNEQUAL, and centring the posts on the frame line instead would even them at
# 0.4583" each — but the band is not centred on the frame line. Its centre sits 3 1/2" south
# of the frame's, so an evenly-cantilevered pair leaves only 1 1/8" of forming clearance at
# the garage end. The band is the binding constraint, so the band is what this is centred on.

# The glazing runs from the house cladding north and stops one panel later — so the reveal
# lands at the garage end rather than at the house, where the door is. The sheet's N-S
# dimension is the sheet's own 4'-0" and nothing else; the slot is what has to be wide
# enough for it.
_GLAZING_Y0 = _HOUSE_CLADDING_Y
_GLAZING_Y1 = _GLAZING_Y0 + _PANEL_FT

# E-W: exactly 4'-0", centred midway between the two doors it shelters. `D-M-ENTRY` and
# `D-G-SERVICE` are now CONCENTRIC at x = 8'-0", so this midpoint is simply their shared
# centre. This centre must track both doors — nothing else in the plan enforces that but
# `test_breezeway_stays_centred_between_the_two_doors_it_shelters`, after the enclosure once
# stood 3'-6" off its own door with nothing catching the drift until
# `code.R311_3_exterior_landing` reported it.
_GLAZING_CENTER_X = 8.0
_GLAZING_X0 = _GLAZING_CENTER_X - _PANEL_FT / 2.0  # 6.0'
_GLAZING_X1 = _GLAZING_CENTER_X + _PANEL_FT / 2.0  # 10.0'
# The posts stand *inside* the glazing lines with the sheets on their outer faces, so the
# 4'-0" is the glazed dimension and not a post-centre dimension.
_POST_X0 = _GLAZING_X0 + _POST_HALF_FT  # 6.2292' — west post centre
_POST_X1 = _GLAZING_X1 - _POST_HALF_FT  # 9.7708' — east post centre
# The roof glazing runs to the same E/W lines as the standing sheets, so the two meet in one
# channel — see the module docstring for the drainage consequence.
_ROOF_X0, _ROOF_X1 = _GLAZING_X0, _GLAZING_X1

_POST_XY = [(_POST_X0, _POST_Y0), (_POST_X1, _POST_Y0),
            (_POST_X0, _POST_Y1), (_POST_X1, _POST_Y1)]
# Where the frame lands: beam ends, rafter stations, deck corners.
_FRAME_XY = [(_POST_X0, _FRAME_Y0), (_POST_X1, _FRAME_Y0),
             (_POST_X0, _FRAME_Y1), (_POST_X1, _FRAME_Y1)]

# Where SL-D-BREEZEWAY cuts (plan/views.py). Published rather than re-typed there because
# the station is chosen, not rounded to: the *south frame line* crosses the whole stack —
# the pad, the pier, both floor beams, the first joist, both roof beams, the first rafter
# and its two wedges, the deck, both standing sheets and the roof sheet.
#
# It no longer crosses the 6x6 POST, and it cannot: the posts moved 4 11/32" inboard so
# their pads would fit between the two buildings (see the post-line block above), while the
# joists and rafters stayed on the frame line where the sheets need bearing. No plane
# crosses both any more. This one is still the right one — the pier and pad it does cross
# are the ones under the post 4" away, and the post's section is on the framing plan.
DETAIL_CUT_Y_FT = _FRAME_Y0

# ============================================================================
# Vertical stack (project-frame absolute; +Z up, 0'-0" is the main-floor datum).
# ============================================================================
# Frost depth is measured from soil. The pads are the only part of this structure pinned to
# the ground rather than to the two doors it joins: they follow grade, while _FLOOR_BEAM_TOP
# and everything derived from it below stay exactly where the two door thresholds are.
_GRADE_FT = SITE_GRADE.feet
_FROST_FT = 42.0 / 12.0  # MN profile frost depth *below grade*; the pads bear at or below it
_PAD_THICKNESS_FT = 1.0
_PAD_BOTTOM = _GRADE_FT - _FROST_FT       # -6'-0"
_PAD_TOP = _PAD_BOTTOM + _PAD_THICKNESS_FT  # -5'-0"

_JOIST = "2x8"
_JOIST_DEPTH_FT = 7.25 / 12.0
_BEAM = "2-2x8"  # same depth as the joists, so they hang flush
_DECK_THICKNESS_IN = 1.0
_RAFTER_DEPTH_FT = 5.5 / 12.0

# The floor does **not** follow grade: the breezeway is a bridge between two doors, and both
# thresholds are at 0'-0". Since grade dropped 2'-6" the deck stands proud of the soil rather
# than sitting on it — see the "open under the deck" note in the docstring.
_FLOOR_BEAM_TOP = 0.0  # the main datum: joist tops and beam top are one plane
_PIER_TOP = _FLOOR_BEAM_TOP - _JOIST_DEPTH_FT  # -7 1/4", the floor-beam soffit
_DECK_SURFACE = _DECK_THICKNESS_IN / 12.0  # +1", the walking surface

# The whole stack is derived *top-down from the standing sheet*, which is the one dimension
# the brief fixes: an uncut 4'x8' sheet stood on end, foot on the floor-beam soffit.
_WALL_SHEET_FT = 8.0  # _PIER_TOP (-7 1/4") to the roof sheet's underside — uncut
_GLAZING_THICKNESS_IN = 0.63
# The roof sheet's own underside — +7'-4 3/4". The standing sheets stop here, which is what
# lets one channel capture both.
_ROOF_GLAZING_UNDER = _PIER_TOP + _WALL_SHEET_FT  # 7.3958' = +7'-4 3/4"

# Drainage wedges on every rafter: 0 at each eave rising to the crown at x = 8'-0". One
# 1" rise over a 2'-0" half-span (~1:24) — shallow, but the roof is now a single bent sheet
# rather than two flat ones meeting at a crown bar, and 1" over 2'-0" is well inside 16mm
# multiwall's cold-bend radius. The glazing plane is authored at the *mean* wedge height,
# a GlazingPanel being a flat sheet — which puts its flat underside 1/2" below the crown.
_WEDGE_RISE_IN = 1.0
_WEDGE_RUN_FT = 2.0  # the half-span, crown to eave; a wedge is one rip per half
_ROOF_GLAZING_TOP = _ROOF_GLAZING_UNDER + _GLAZING_THICKNESS_IN / 12.0
_RAFTER_TOP = _ROOF_GLAZING_UNDER - (_WEDGE_RISE_IN / 2.0) / 12.0  # 7.3542'
_ROOF_BEAM_TOP = _RAFTER_TOP - _RAFTER_DEPTH_FT  # 6.8958' = +6'-10 3/4"
_POST_TOP = _ROOF_BEAM_TOP - _JOIST_DEPTH_FT  # 6.2917' = +6'-3 1/2", the roof-beam soffit
# Clear under the rafters is ~7'-3 1/4"; under the two N-S roof beams it is +6'-3 1/2", below
# a 6'-8" door head. They run at x = 6'-2 3/4"/9'-9 1/4", at the walk-line edges — see the
# module docstring. The garage's south fascia underside is at +9'-11.4", so clearance is
# ~2'-6" and not a binding constraint.

# ============================================================================
# Foundations: pad -> concrete pier -> 6x6 post.
# ============================================================================
# The pads and the 6x6 posts keep the uids the retired params/foundations.py stub gave
# them, so their IFC GlobalIds (uuid5 over the uid) survive this rewrite.
PADS = [
    Pad(uid=f"CP{i}00AAAAA", tag=f"PD-BW-{i}",
        outline=(pt(ft(x - _PAD_HALF_FT), ft(y - _PAD_HALF_FT)),
                 pt(ft(x + _PAD_HALF_FT), ft(y - _PAD_HALF_FT)),
                 pt(ft(x + _PAD_HALF_FT), ft(y + _PAD_HALF_FT)),
                 pt(ft(x - _PAD_HALF_FT), ft(y + _PAD_HALF_FT))),
        thickness=ft(_PAD_THICKNESS_FT), bottom_elevation=ft(_PAD_BOTTOM))
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

# 12" round concrete piers carry the wood clear of the ground, pad top up to the floor-beam
# soffit. The 6x6 above is ground-contact rated anyway (the brief), but a post standing in
# soil rots from the end grain first whatever its treatment.
#
# **All four piers now top out on one plane.** The two garage-end ones used to stop a course
# lower, at the ICF stem top, because a 12" round is 6 1/2" fatter than the 5 1/2" post it
# carries and spilled 3 1/4" past the post's north face into W-G-S's bottom plate at -0'-8"
# (structural.member_interference). Moving the posts inboard off the frame line put the pier
# faces 4 5/16" clear of the stem line, so the special case has nothing left to dodge —
# `member_interference` and `concrete_interference` are both what prove that, not this
# comment.
_PIER_TOPS = [_PIER_TOP] * 4

# ** THE CAGE IS THE MINIMUM ACI PERMITS, AND IT IS NOT OPTIONAL. ** Same section as
# PT-SG-COL, so the same arithmetic and the same answer (params/sunken_garden.py has it in
# full): A_g = 113.10 in2, §10.6.1.1's 1% floor is 1.131 in2, (4) #5 = 1.24 in2 (rho 1.096%)
# clears it by 9.6% and is §10.7.3.1(b)'s own four-bar minimum for a circular tie. #3 ties
# (§25.7.2.1, verticals #10 or smaller) at §25.7.2.2's maximum — the least of 16db = 10.0",
# 48dt = 18.0", h = 12.0".
#
# **These piers are COLUMNS, not pedestals, which is the whole reason the bars are here.**
# h/d is 4.7 (56 3/4" over 12"), past ACI §2.3's 3.0, and §14.1.5 does not permit a plain
# concrete column at ANY stress. Before this the four stood unreinforced and ungraded:
# `engineering/pier_basis.cast_piers` indexed footings from `Footing.under` and these bear
# on `Pad`s, so they fell out silently — no record, not even an INCOMPLETE.
#
# The 1% floor is a creep, shrinkage and accidental-moment rule, indifferent to load, which
# is fortunate: this pier's axial DEMAND cannot be computed. It carries BM-BW-RW/RE, and the
# breezeway roof is neither a Roof nor a FloorSystem (see the ROOF FRAME block below), so
# there is no plan area to divide among the posts. `haus engineering --item
# deck_post/PR-BW-1` grades the six detailing states and reports the axial one INCOMPLETE
# rather than publishing a d/c against a demand it knows is short.
# Oracle: notes/breezeway_piers.md. Do not thin it to "save concrete".
_PIER_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'

PIERS = [
    Post(uid=f"BWPR{i}AAAAA", tag=f"PR-BW-{i}", position=pt(ft(x), ft(y)),
         size="12 round", height=ft(_PIER_TOPS[i - 1] - _PAD_TOP),
         assembly="PIER_CONCRETE_12", vertical_reinforcement=_PIER_CAGE,
         supported_by=f"PD-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

POSTS = [
    Post(uid=f"CP{i}50AAAAA", tag=f"PT-BW-{i}", position=pt(ft(x), ft(y)),
         size="6x6", height=ft(_POST_TOP - _PIER_TOPS[i - 1]),
         assembly="POST_KDAT", supported_by=f"PR-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

# ============================================================================
# Deck: two N-S floor beams bolted to the post faces, E-W joists flush between them.
# ============================================================================
_BEAM_NODES = [
    ("BWN01AAAAA", "N-BW-FSW", _POST_X0, _FRAME_Y0),
    ("BWN02AAAAA", "N-BW-FSE", _POST_X1, _FRAME_Y0),
    ("BWN03AAAAA", "N-BW-FNW", _POST_X0, _FRAME_Y1),
    ("BWN04AAAAA", "N-BW-FNE", _POST_X1, _FRAME_Y1),
]
# The roof beams sit on the same two plan lines but on their own nodes: one node cannot
# carry two elevations, and the joint-detection pass reads node identity.
_ROOF_NODES = [
    ("BWN11AAAAA", "N-BW-RSW", _POST_X0, _FRAME_Y0),
    ("BWN12AAAAA", "N-BW-RSE", _POST_X1, _FRAME_Y0),
    ("BWN13AAAAA", "N-BW-RNW", _POST_X0, _FRAME_Y1),
    ("BWN14AAAAA", "N-BW-RNE", _POST_X1, _FRAME_Y1),
]
# Rafter ends run out to the roof envelope, which is now the post *outer face* — 2 3/4" past
# each post centre — so the rafter, the sheet and the H channel all die on one plane.
_RAFTER_Y = [_FRAME_Y0, (_FRAME_Y0 + _FRAME_Y1) / 2.0, _FRAME_Y1]
_RAFTER_NODES = [
    (f"BWN2{i}{side}AAAA", f"N-BW-R{i}{side}", x, y)
    for i, y in enumerate(_RAFTER_Y, start=1)
    for side, x in (("W", _ROOF_X0), ("E", _ROOF_X1))
]

NODES = [Node(uid=uid, tag=tag, position=pt(ft(x), ft(y)))
         for uid, tag, x, y in (*_BEAM_NODES, *_ROOF_NODES, *_RAFTER_NODES)]

# ``top_elevation`` is load-bearing information, not decoration: it pins the beam flush in
# the joist band (see the module docstring), and it is what stops the resolver's
# post-shortening rule from dragging these posts — which carry the roof, not just this
# beam — down by a joist depth.
FLOOR_BEAMS = [
    Beam(uid="BWBM01AAAA", tag="BM-BW-FW", start_node="N-BW-FSW", end_node="N-BW-FNW",
         size=_BEAM, top_elevation=ft(_FLOOR_BEAM_TOP), assembly="BEAM_KDAT",
         bearing_refs=("PT-BW-1", "PT-BW-3")),
    Beam(uid="BWBM02AAAA", tag="BM-BW-FE", start_node="N-BW-FSE", end_node="N-BW-FNE",
         size=_BEAM, top_elevation=ft(_FLOOR_BEAM_TOP), assembly="BEAM_KDAT",
         bearing_refs=("PT-BW-2", "PT-BW-4")),
]

_DECK_OUTLINE = (pt(ft(_POST_X0), ft(_FRAME_Y0)), pt(ft(_POST_X1), ft(_FRAME_Y0)),
                 pt(ft(_POST_X1), ft(_FRAME_Y1)), pt(ft(_POST_X0), ft(_FRAME_Y1)))

# The composite plank is this floor system's own SUBFLOOR, and the sheet is authored.
#
# ** IT WAS A SLAB UNTIL 2026-09-03, AND THE REASON IT COULD NOT BE A SUBFLOOR IS FIXED. **
# A plank over joists is a floor system's `subfloor` everywhere else in this house (the
# garden's two decks and the balcony), which bills by the square foot in [sheet_goods]
# instead of by the cubic yard out of a table named [concrete]. This one could not be,
# because `resolve/floors.py` drew a subfloor bearing-line to bearing-line by the OUTLINE'S
# perpendicular extent — so a floor system's sheet was exactly its joist field, and this
# plank oversails the rim to land on the house cladding and the garage stem, which is what a
# deck board does and what these two doors open onto. Two ways to say it and both failed:
# keep the outline at the frame box and the sheet stops short of each threshold
# (`code.R311_3_exterior_landing` FAILs both doors); stretch the outline to the two faces and
# the joist solver lays a joist on that line, straight through the posts.
#
# `FloorSystem.subfloor_outline` is the third way and it is one field: an authored sheet
# polygon that replaces the derived corners and touches nothing else — not the joist solver,
# not `deck_voids`, not the elevations. The oversail is 2 3/4" on the glazing lines and
# 2 3/4"/3 5/8" at the two buildings, all inside the 8" `bearing_plan_tolerance_in` that
# `structural.subfloor_oversail` bounds it against.
#
# Laid door to door (N-S) across the joists, on breather tape at every joist top so the two
# never trap water against each other, and GAPPED 3/16" between boards — the gaps are the
# drainage, which is why this deck is dead flat and carries no fall (see PORCH_DECK_COMPOSITE
# in plan/assemblies.py, and the module docstring's deviation 3).
_DECK_SHEET = (pt(ft(_GLAZING_X0), ft(_HOUSE_CLADDING_Y)),
               pt(ft(_GLAZING_X1), ft(_HOUSE_CLADDING_Y)),
               pt(ft(_GLAZING_X1), ft(_GARAGE_STEM_Y)),
               pt(ft(_GLAZING_X0), ft(_GARAGE_STEM_Y)))

# ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
# 40-psf floor table — see checks/structural/deck.py.
FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    joists=JoistSpec(member=_JOIST, spacing=inch(16), direction="x",
                     bearing_refs=("BM-BW-FW", "BM-BW-FE")),
    outline=_DECK_OUTLINE,
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(_DECK_THICKNESS_IN)),
    subfloor_outline=_DECK_SHEET,
    service="deck",
    source="breezeway deck — KDAT 2x8 joists hung flush E-W between the two floor beams",
)

# ============================================================================
# Roof frame: two N-S beams on the post tops, three E-W rafters over them.
# ============================================================================
ROOF_BEAMS = [
    Beam(uid="BWBM03AAAA", tag="BM-BW-RW", start_node="N-BW-RSW", end_node="N-BW-RNW",
         size=_BEAM, top_elevation=ft(_ROOF_BEAM_TOP), assembly="BEAM_KDAT",
         bearing_refs=("PT-BW-1", "PT-BW-3")),
    Beam(uid="BWBM04AAAA", tag="BM-BW-RE", start_node="N-BW-RSE", end_node="N-BW-RNE",
         size=_BEAM, top_elevation=ft(_ROOF_BEAM_TOP), assembly="BEAM_KDAT",
         bearing_refs=("PT-BW-2", "PT-BW-4")),
]

# Three 2x6 rafters at ~1'-9" o.c. across the 3'-7" between the beams, seated on top of
# them. A Roof element cannot be used here: resolve/roof_geometry.py only accepts Wall
# bearing refs, and a FloorSystem is pinned to its storey elevation — an absolute-elevation
# Beam is the idiom for framing that belongs to no storey datum (cf. BM-SG-RAIL-R/F).
RAFTERS = [
    Beam(uid=f"BWRF0{i}AAAA", tag=f"BM-BW-R{i}", start_node=f"N-BW-R{i}W",
         end_node=f"N-BW-R{i}E", size="2x6", top_elevation=ft(_RAFTER_TOP),
         assembly="BEAM_KDAT", bearing_refs=("BM-BW-RW", "BM-BW-RE"))
    for i in range(1, len(_RAFTER_Y) + 1)
]

# A back-to-back pair of tapered rips on every rafter: 1" proud at the crown (x = 8'-0"),
# feathered to nothing at each eave 2'-0" away. Six pieces, ripped from 2x4 KDAT laid flat,
# so each one shows its 3 1/2" face in plan — which is why the member carries an explicit
# plan width (a taper's own vertical extent cannot say which way it was laid).
#
# These used to be a drawing and a derivation input and nothing else: `_RAFTER_TOP` was set
# half a wedge below the glazing, and `emit/draw/detail_components` drew a triangle from a
# constant. Nothing was ordered or cut. `_RAFTER_TOP` still derives exactly as it did, so
# **no elevation moves** — the six pieces are simply real now.
WEDGES = [
    Wedge(uid=f"BWWG{side}{i}AAAA", tag=f"WG-BW-R{i}{side}",
          position=pt(ft(_GLAZING_CENTER_X), ft(y)), base_elevation=ft(_RAFTER_TOP),
          run=ft(_WEDGE_RUN_FT), rise=inch(_WEDGE_RISE_IN),
          axis="x", direction=direction, member="2x4:kdat", assembly="BEAM_KDAT",
          bears_on=(f"BM-BW-R{i}",))
    for i, y in enumerate(_RAFTER_Y, start=1)
    for side, direction in (("W", -1), ("E", 1))
]

# ============================================================================
# Glazing: three 4'x8' sheets, two standing uncut and one halved across the roof.
# ============================================================================
# One sheet, 4'-0" x 4'-0" — half of an 8'x4', the only cut in the bill. Flutes run E-W,
# down-slope from the crown at x = 4'-6" to each eave, so the open (draining) flute ends land
# at x = 2'-6" and 6'-6". The sheet bends over the crown rather than butting a second sheet
# there, which is what retired the crown glazing bar: no joint, nothing to seal.
ROOF_GLAZING = [
    GlazingPanel(
        uid="BWGP01AAAA", tag="GL-BW-ROOF",
        outline=(pt(ft(_ROOF_X0), ft(_GLAZING_Y0)), pt(ft(_ROOF_X1), ft(_GLAZING_Y0)),
                 pt(ft(_ROOF_X1), ft(_GLAZING_Y1)), pt(ft(_ROOF_X0), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), top_elevation=ft(_ROOF_GLAZING_TOP),
        plane="horizontal", assembly="BREEZEWAY_ROOF_GLAZING"),
]

# The two side walls. Vertical glazing is where a bird strike happens, so both carry the
# patterned solar/bird-safety film the brief names; the film is a surface treatment, not a
# layer, so it is recorded on the panel rather than in the assembly.
_BIRD_FILM = "SOLYX BSF-DB35 solar bird-safety film"
WALL_GLAZING = [
    GlazingPanel(
        uid="BWGP03AAAA", tag="GL-BW-WALL-W",
        outline=(pt(ft(_GLAZING_X0), ft(_GLAZING_Y0)), pt(ft(_GLAZING_X0), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), plane="vertical",
        base_elevation=ft(_PIER_TOP), top_elevation=ft(_ROOF_GLAZING_UNDER),
        assembly="BREEZEWAY_GLAZED_WALL", film=_BIRD_FILM),
    GlazingPanel(
        uid="BWGP04AAAA", tag="GL-BW-WALL-E",
        outline=(pt(ft(_GLAZING_X1), ft(_GLAZING_Y0)), pt(ft(_GLAZING_X1), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), plane="vertical",
        base_elevation=ft(_PIER_TOP), top_elevation=ft(_ROOF_GLAZING_UNDER),
        assembly="BREEZEWAY_GLAZED_WALL", film=_BIRD_FILM),
]

# ============================================================================
# Glazing trim: every cut edge of every sheet is capped. Billed by the lineal foot.
# ============================================================================
_CHANNEL_DEPTH = inch(1.5)   # how far the extrusion laps the sheet face
_CHANNEL_THICK = inch(1.0)   # its section across the sheet
_ROOF_EAVE_TOP = _RAFTER_TOP + _GLAZING_THICKNESS_IN / 12.0  # wedge is 0 at the eave
# The north F-channel spans from the roof panel's edge back to the garage cladding, so its
# run sits on the midline of that reach rather than on the panel edge — 1/2", the reveal the
# uncut panel leaves at this end.
_FCH_N_Y = (_GLAZING_Y1 + _GARAGE_CLADDING_Y) / 2.0

# The shared H channel — the piece that carries both the roof eave and the wall head. An H
# receives a sheet in each of its two slots, which is exactly the joint here since the
# standing sheet's head and the roof sheet's edge land on the same line: the wall sheet
# enters from below, the roof sheet from the side, and the web between them is the only
# thing crossing the joint.
#
# "H" is already in GlazingTrim's documented profile vocabulary and was unused; this is the
# joint it is the word for.
_H_LAP = inch(1.5)   # how far each slot grips the sheet in it
_H_WEB = inch(0.5)   # the web between the two slots
_H_DEPTH = _H_LAP + _H_WEB + _H_LAP

ROOF_TRIM = [
    GlazingTrim(uid="BWGT01AAAA", tag="TR-BW-HCH-W", kind=TrimKind.GLAZING_CHANNEL,
                profile="H", weep_holes=False, glazing_ref="GL-BW-ROOF",
                path=(pt(ft(_ROOF_X0), ft(_GLAZING_Y0)), pt(ft(_ROOF_X0), ft(_GLAZING_Y1))),
                top_elevation=ft(_ROOF_GLAZING_UNDER) + _H_LAP + _H_WEB,
                depth=_H_DEPTH, thickness=inch(2.0), material="aluminum-extrusion"),
    GlazingTrim(uid="BWGT02AAAA", tag="TR-BW-HCH-E", kind=TrimKind.GLAZING_CHANNEL,
                profile="H", weep_holes=False, glazing_ref="GL-BW-ROOF",
                path=(pt(ft(_ROOF_X1), ft(_GLAZING_Y0)), pt(ft(_ROOF_X1), ft(_GLAZING_Y1))),
                top_elevation=ft(_ROOF_GLAZING_UNDER) + _H_LAP + _H_WEB,
                depth=_H_DEPTH, thickness=inch(2.0), material="aluminum-extrusion"),
    # No TR-BW-BAR-CROWN: the roof is one sheet bent over the crown, so there is no joint
    # there to cap. A glazing bar with nothing between its slots is a strip of flashing.
    # North and south roof edges run parallel to the flutes and butt the cladding: an
    # F-channel receiver, with a bent leg covering back to the wall. Both legs are short
    # now that the garage cladding is the proud face at that end — the north one covers the
    # 1/2" reveal the uncut panel leaves, nothing more.
    GlazingTrim(uid="BWGT04AAAA", tag="TR-BW-FCH-S", kind=TrimKind.GLAZING_CHANNEL,
                profile="F", path=(pt(ft(_ROOF_X0), ft(_GLAZING_Y0)),
                                   pt(ft(_ROOF_X1), ft(_GLAZING_Y0))),
                top_elevation=ft(_ROOF_EAVE_TOP), depth=_CHANNEL_DEPTH,
                thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
    GlazingTrim(uid="BWGT05AAAA", tag="TR-BW-FCH-N", kind=TrimKind.GLAZING_CHANNEL,
                profile="F", path=(pt(ft(_ROOF_X0), ft(_FCH_N_Y)),
                                   pt(ft(_ROOF_X1), ft(_FCH_N_Y))),
                top_elevation=ft(_ROOF_EAVE_TOP), depth=_CHANNEL_DEPTH,
                thickness=ft(_GARAGE_CLADDING_Y - _GLAZING_Y1), material="aluminum-extrusion"),
]

# Each standing sheet is captured on all four edges: a weeping U-channel sill on the deck,
# an F-channel head under the roof beam, and an F-channel jamb against each building's
# cladding. The jambs run vertically, so their length is their ``depth``.
_WALL_PANEL_HEIGHT = ft(_ROOF_GLAZING_UNDER - _PIER_TOP)
WALL_TRIM = []
for _i, (_tag, _x, _ref) in enumerate(
        (("W", _GLAZING_X0, "GL-BW-WALL-W"), ("E", _GLAZING_X1, "GL-BW-WALL-E")), start=1):
    _run = (pt(ft(_x), ft(_GLAZING_Y0)), pt(ft(_x), ft(_GLAZING_Y1)))
    WALL_TRIM += [
        # The sill is at the deck surface, which the sheet passes rather than starts at —
        # it runs 8 1/4" further down to the floor-beam soffit, covering the beam band and
        # the deck edge.
        GlazingTrim(uid=f"BWGT1{_i}AAAA", tag=f"TR-BW-SILL-{_tag}",
                    kind=TrimKind.GLAZING_CHANNEL, profile="U", weep_holes=True,
                    glazing_ref=_ref, path=_run,
                    top_elevation=ft(_DECK_SURFACE) + _CHANNEL_DEPTH, depth=_CHANNEL_DEPTH,
                    thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
        # No TR-BW-HEAD-*: the shared H channel above is this sheet's head. The sill's
        # weep holes are now the whole drainage path for the assembly, since the roof's
        # eave U went with the head.
    ]
    for _side, _y in (("S", _GLAZING_Y0), ("N", _GLAZING_Y1)):
        _half = _GLAZING_THICKNESS_IN / 24.0
        WALL_TRIM.append(GlazingTrim(
            uid=f"BWGJ{_side}{_i}AAAA", tag=f"TR-BW-JAMB-{_tag}{_side}",
            kind=TrimKind.GLAZING_CHANNEL, profile="F", glazing_ref=_ref,
            vertical=True,
            path=(pt(ft(_x - _half), ft(_y)), pt(ft(_x + _half), ft(_y))),
            # A jamb runs the sheet's full height, so its top must track the sheet's top
            # (_ROOF_GLAZING_UNDER), not _POST_TOP.
            top_elevation=ft(_ROOF_GLAZING_UNDER), depth=_WALL_PANEL_HEIGHT,
            thickness=_CHANNEL_THICK, material="aluminum-extrusion"))

# ============================================================================
# Hardware.
# ============================================================================
# ABU66SS stainless standoff bases hold the 6x6 clear of the pier top so end grain never
# sits in standing water; KBS1Z straps tie each roof beam down to the post it seats on,
# which is the only uplift restraint a freestanding pinned frame has.
CONNECTORS = [
    Connector(uid=f"BWCB{i}AAAAA", tag=f"CN-BW-BASE-{i}", kind=ConnectorKind.POST_BASE,
              position=pt(ft(x), ft(y)), elevation=ft(_PIER_TOP), size="ABU66SS",
              connects=(f"PT-BW-{i}", f"PR-BW-{i}"))
    for i, (x, y) in enumerate(_POST_XY, start=1)
] + [
    Connector(uid=f"BWCK{i}AAAAA", tag=f"CN-BW-KBS-{i}", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(x), ft(y)), elevation=ft(_POST_TOP), size="KBS1Z",
              connects=(f"PT-BW-{i}", "BM-BW-RW" if x == _POST_X0 else "BM-BW-RE"))
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

MAIN_ELEMENTS = [*NODES, *PADS, *PIERS, *POSTS, *FLOOR_BEAMS, FLOOR,
                 *ROOF_BEAMS, *RAFTERS, *WEDGES, *ROOF_GLAZING, *WALL_GLAZING,
                 *ROOF_TRIM, *WALL_TRIM, *CONNECTORS]
