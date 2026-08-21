"""Breezeway — the enclosed 8' x 4' x 4' polycarbonate shelter between house and garage.

One freestanding structure spanning the 4'-0 1/2" slot between the house's north entry
(``D-M-ENTRY``, centred on x = 4'-0") and the garage's service door (``D-G-SERVICE``,
centred on x = 5'-0"). It touches neither building: four 6x6 ground-contact posts on
isolated piers and frost-depth pads carry the whole thing, and the glazing is *snug* to the
house and garage cladding without lapping into either one's flashing.

**"8 x 4 x 4" is the brief, and this module means it literally (2026-07-27).** The glazed
enclosure is 8'-0" tall x 4'-0" N-S x 4'-0" E-W. The three dimensions are measured on the
*enclosure*: the foundations below the floor-beam soffit are excluded (they are ground work,
not room), and so is the ~1" wedge bulge that crowns the roof for drainage.

That reading falls straight out of the sheet:

* A standing sheet is a 4'x8' sheet stood on end and **uncut**: 4'-0" wide N-S, exactly
  8'-0" tall, from the floor-beam soffit (-7 1/4") to the roof sheet's underside
  (+7'-4 3/4"). Nothing of the framing shows below it and nothing of the elevation is open
  above it.
* The E-W extent is 4'-0" glazing line to glazing line, centred on x = 4'-6" — midway
  between the house entry (x = 4'-0") and the garage service door (x = 5'-0") — so the
  glazing runs x = 2'-6" to 6'-6". It used to be 7'-5 1/2", which was a corridor rather than
  a vestibule and cost a third more of everything.
* The roof is **one** 4'-0" x 4'-0" sheet: half of an 8'x4', cut once.

The bill is therefore three sheets for the enclosure itself, and only one cut among them:
two 8'x4' sheets standing whole, one 8'x4' halved for the roof. (The "10' stock" era — when
the standing sheet ran 9'-10 3/4" — is retired; it existed only because the enclosure was
8'-0" clear *above the decking* rather than 8'-0" of sheet.) Three sheets is the whole bill:
the gap the 2026-08-18 lift opened under the deck is left open rather than skirted.

The two sheets meet, so one ``profile="H"`` channel per side receives both — the wall sheet
in its lower slot, the roof sheet in its upper — replacing the eave U and the wall F-head
that used to stand 3 1/4" apart in plan with 14 1/2" of open elevation between them.

**What that costs, stated rather than left implicit:**

* The roof does not oversail the glazing line as a drip edge; it dies *in* the shared
  channel, so the sill U-channel's weep holes are the assembly's only drainage path.
* **Headroom is now honest rather than generous.** Clear under the rafters is ~7'-3 1/4",
  but the roof beams run N-S at x = 2'-8 3/4" / 6'-3 1/4" and their soffit is at +6'-3 1/2" —
  *below* a 6'-8" door head. Those two beams sit on the glazing lines at the very edges of
  the walk-line, which runs door to door (N-S) up the middle of the 4'-0" width, so a person
  passes between them and not under them. Anyone reaching for the west or east glazing ducks.
  This is a deliberate consequence of measuring the 8' on the sheet.
* The garage-eave clearance note is now trivial rather than tight: the garage's south fascia
  underside is at +9'-11.4" and this roof tops out around +7'-5 1/2", so ~2'-6" of air
  instead of the old 7 1/4".

Framing directions (the brief's "opposite rotation"):

    FLOOR PLAN (main, z = 0'-0")           ROOF PLAN (z = +6'-10 3/4")
     garage stem                            garage cladding
     |===================|  N-S floor       |===================|  N-S roof beams
     |-------------------|  beams on        |-------------------|  on the post tops
     |-------------------|  the post        |-------------------|  E-W rafters
     |===================|  lines           |===================|  crown at x = 4'-6"
     house      E-W joists @ 16"            house    (wedges on every rafter)
                deck boards N-S

**What the 2026-08-18 lift did to it.** Grade dropped 2'-6" to bring the house out of the
ground. The breezeway's *foundations* went with the soil — the pads still bear at 42" below
grade, so the piers grew 2'-6" — and nothing above ``_FLOOR_BEAM_TOP`` moved at all, because
this is a bridge between two doors and both thresholds are still at 0'-0". Two consequences:

* **The 1'-10 3/4" that opened up under the deck stays open.** A half-sheet skirt in the
  same multiwall stood there briefly and is retired (2026-08-21): the deck is a bridge
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
3. **The 1" fall toward the garage lives in the wedges, not in shorter garage-side posts.**
   A ``Beam`` is a prism, so a sloped N-S roof beam cannot be expressed; sinking the north
   posts 1" would just leave the beam floating over them. The wedges that crown the roof
   E-W are already a sloping element on every rafter, so they carry the N-S fall too — one
   sloping part instead of a slope the structure cannot hold.

The 22" step at the garage door is resolved as of 2026-08-01, and not here: ``D-G-SERVICE``
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
    FloorSystem,
    GlazingPanel,
    GlazingTrim,
    JoistSpec,
    Node,
    Pad,
    Post,
    Slab,
    TrimKind,
    ft,
    inch,
    pt,
)

from params.foundations import SITE_GRADE
from plan.storeys.garage import GARAGE_STEM_REVEAL, GARAGE_Y_SOUTH

# ============================================================================
# Plan geometry — every number here is derived, never repeated.
# ============================================================================
# North face of the house's outsulated wall: the y=36' sheathing plane plus .02" WRB,
# 2" polyiso, 2" EPS, 1/2" furring and 1/2" standing seam (plan/assemblies.py
# CATLIN_EXT_2X6). This is what the breezeway's south end butts.
_HOUSE_CLADDING_Y = 36.0 + (0.02 + 2.0 + 2.0 + 0.5 + 0.5) / 12.0  # 36.4183'

# South face of the garage's ICF stem: the wall line itself. The 11" section is aligned so
# its exterior EPS face lands on the node line, coplanar with the zip-R of the wood wall
# above (params/foundations.py), so the stem is no longer the proud face here — the
# cladding is, 7/8" south of it. It keeps its own name because the deck still butts *this*
# plane, tucked under that 7/8" of overhang.
_GARAGE_STEM_Y = GARAGE_Y_SOUTH.feet  # 40.53125'
# South face of the garage's wood wall above the stem: rainscreen + standing seam over the
# zip-R plane. That is the obstruction now, at deck level and at roof level both, so it is
# what sets the clear gap.
_GARAGE_CLADDING_Y = GARAGE_Y_SOUTH.feet - (0.375 + 0.5) / 12.0  # 40.4583'

_CLEAR_GAP_FT = _GARAGE_CLADDING_Y - _HOUSE_CLADDING_Y  # 4.0400' = 4'-0 1/2"
_PANEL_FT = 4.0  # one 4'x8' sheet, uncut

# N-S: post outer faces snug to the house cladding and the garage cladding — the
# most-proud face at each end is what a post has to clear.
_POST_HALF_FT = 5.5 / 24.0  # half a dressed 6x6
_POST_Y0 = _HOUSE_CLADDING_Y + _POST_HALF_FT  # 36.6475'
_POST_Y1 = _GARAGE_CLADDING_Y - _POST_HALF_FT  # 40.2292'

# The glazing runs a full uncut 4'-0" from the house cladding north, leaving its 1/2"
# reveal at the garage cladding rather than at the house, where the door is.
_GLAZING_Y0 = _HOUSE_CLADDING_Y
_GLAZING_Y1 = _HOUSE_CLADDING_Y + _PANEL_FT

# E-W: exactly 4'-0", centred midway between the two doors it shelters. That centre moved
# from x = 4'-6" to x = 7'-3" on 2026-08-01, and the reason is a coordination miss rather
# than a design change: this module was written on 2026-07-27 against a house entry at
# x = 4'-0" and a service door at x = 5'-0", and the 2026-07-28 mudroom conversion pushed
# D-M-ENTRY east to x = 8'-0" without the shelter following. It has been standing 3'-6" west
# of the door it exists for ever since — the deck did not touch the entry's landing patch at
# all, which is what code.R311_3_exterior_landing eventually reported.
#
# The two doors are 1'-6" apart in x (entry 8'-0", service 6'-6"), so their outer jambs span
# 4'-6" and a 4'-0" enclosure cannot cover both to the last inch: each door's outer 3" of
# leaf oversails the deck edge at one corner. The brief's literal 8x4x4 — three sheets, one
# cut — is what this module is built to keep, so the 3" is accepted rather than paid for with
# a wider (and two-cut) enclosure. Both doors clear R311.3's 36"-deep landing patch at 92%
# coverage, and the walk line door-to-door is unaffected: it runs up the middle, where the
# deck is full width.
_GLAZING_CENTER_X = 7.25
_GLAZING_X0 = _GLAZING_CENTER_X - _PANEL_FT / 2.0  # 2.5'
_GLAZING_X1 = _GLAZING_CENTER_X + _PANEL_FT / 2.0  # 6.5'
# The posts stand *inside* the glazing lines with the sheets on their outer faces, so the
# 4'-0" is the glazed dimension and not a post-centre dimension. (It used to run the other
# way — glazing derived from an 8'-0" post spread — which is why the enclosure was 7'-5 1/2".)
_POST_X0 = _GLAZING_X0 + _POST_HALF_FT  # 2.7292' — west post centre
_POST_X1 = _GLAZING_X1 - _POST_HALF_FT  # 6.2708' — east post centre
# The roof glazing runs to the same E/W lines as the standing sheets, so the two meet in one
# channel. It used to oversail them by 3 1/4" as a drip edge; retiring that is the cost of
# the shared channel (see the module docstring), and the sill U-channel's weep holes are now
# the only drainage path.
_ROOF_X0, _ROOF_X1 = _GLAZING_X0, _GLAZING_X1

_POST_XY = [(_POST_X0, _POST_Y0), (_POST_X1, _POST_Y0),
            (_POST_X0, _POST_Y1), (_POST_X1, _POST_Y1)]

# Where SL-D-BREEZEWAY cuts (plan/views.py). Published rather than re-typed there because
# the whole point of the station is that it lands on the *south frame line*: pad, pier, post,
# both floor beams, the first joist, both roof beams, the first rafter, the deck, both
# standing sheets and the roof sheets are all crossed by one plane at this y. Any other
# station misses the foundation or misses the frame.
DETAIL_CUT_Y_FT = _POST_Y0

# ============================================================================
# Vertical stack (project-frame absolute; +Z up, 0'-0" is the main-floor datum).
# ============================================================================
# Frost depth is measured from soil, and the soil is 2'-6" below the main floor. The pads
# are the only part of this structure pinned to the ground rather than to the two doors it
# joins: when grade dropped on 2026-08-18 they went down with it and the piers grew 2'-6",
# while _FLOOR_BEAM_TOP and everything derived from it below stayed exactly where it was.
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

# Drainage wedges on every rafter: 0 at each eave rising to the crown at x = 4'-6". One
# 1" rise over a 2'-0" half-span (~1:24) — shallow, but the roof is now a single bent sheet
# rather than two flat ones meeting at a crown bar, and 1" over 2'-0" is well inside 16mm
# multiwall's cold-bend radius. The glazing plane is authored at the *mean* wedge height,
# a GlazingPanel being a flat sheet.
_WEDGE_RISE_IN = 1.0
_ROOF_GLAZING_TOP = _ROOF_GLAZING_UNDER + _GLAZING_THICKNESS_IN / 12.0
_RAFTER_TOP = _ROOF_GLAZING_UNDER - (_WEDGE_RISE_IN / 2.0) / 12.0  # 7.3542'
_ROOF_BEAM_TOP = _RAFTER_TOP - _RAFTER_DEPTH_FT  # 6.8958' = +6'-10 3/4"
_POST_TOP = _ROOF_BEAM_TOP - _JOIST_DEPTH_FT  # 6.2917' = +6'-3 1/2", the roof-beam soffit
# Clear under the rafters is ~7'-3 1/4"; under the two N-S roof beams it is +6'-3 1/2", below
# a 6'-8" door head. They run at x = 2'-8 3/4"/6'-3 1/4", at the walk-line edges — see the
# module docstring. The garage's south fascia underside is at +9'-11.4", so the old 7 1/4"
# eave clearance is now ~2'-6" and no longer a constraint worth checking.

# ============================================================================
# Foundations: pad -> concrete pier -> 6x6 post.
# ============================================================================
# The pads and the 6x6 posts keep the uids the retired params/foundations.py stub gave
# them, so their IFC GlobalIds (uuid5 over the uid) survive this rewrite.
PADS = [
    Pad(uid=f"CP{i}00AAAAA", tag=f"PD-BW-{i}",
        outline=(pt(ft(x - 1), ft(y - 1)), pt(ft(x + 1), ft(y - 1)),
                 pt(ft(x + 1), ft(y + 1)), pt(ft(x - 1), ft(y + 1))),
        thickness=ft(_PAD_THICKNESS_FT), bottom_elevation=ft(_PAD_BOTTOM))
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

# 12" round concrete piers carry the wood clear of the ground, pad top up to the floor-beam
# soffit. The 6x6 above is ground-contact rated anyway (the brief), but a post standing in
# soil rots from the end grain first whatever its treatment.
#
# The two garage-end piers stop one course lower, at the ICF stem top, and their posts run
# down to meet them. A 12" round is 6 1/2" fatter than the 5 1/2" post it carries, so it
# spills 3 1/4" past the post's north face — which was harmless while the garage's wood wall
# started 1'-10" *above* the datum, and stopped being harmless on 2026-08-18 when grade
# dropped and the whole garage went down with it: W-G-S's bottom plate now sits at -0'-8",
# three quarters of an inch under the -0'-7 1/4" floor-beam soffit these piers top out at,
# and concrete and plate wanted the same band (structural.member_interference). The post is
# exactly as wide as the cladding is proud of the stem, so it passes where the pier cannot.
# Nothing in plan moves: the enclosure, the deck and the uncut sheets are all measured off
# the post lines, and the post lines are untouched.
_GARAGE_STEM_TOP = _GRADE_FT + GARAGE_STEM_REVEAL.feet  # -0'-8"
_PIER_TOPS = [_PIER_TOP, _PIER_TOP,
              min(_PIER_TOP, _GARAGE_STEM_TOP), min(_PIER_TOP, _GARAGE_STEM_TOP)]

PIERS = [
    Post(uid=f"BWPR{i}AAAAA", tag=f"PR-BW-{i}", position=pt(ft(x), ft(y)),
         size="12 round", height=ft(_PIER_TOPS[i - 1] - _PAD_TOP), supported_by=f"PD-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

POSTS = [
    Post(uid=f"CP{i}50AAAAA", tag=f"PT-BW-{i}", position=pt(ft(x), ft(y)),
         size="6x6", height=ft(_POST_TOP - _PIER_TOPS[i - 1]), supported_by=f"PR-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

# ============================================================================
# Deck: two N-S floor beams bolted to the post faces, E-W joists flush between them.
# ============================================================================
_BEAM_NODES = [
    ("BWN01AAAAA", "N-BW-FSW", _POST_X0, _POST_Y0),
    ("BWN02AAAAA", "N-BW-FSE", _POST_X1, _POST_Y0),
    ("BWN03AAAAA", "N-BW-FNW", _POST_X0, _POST_Y1),
    ("BWN04AAAAA", "N-BW-FNE", _POST_X1, _POST_Y1),
]
# The roof beams sit on the same two plan lines but on their own nodes: one node cannot
# carry two elevations, and the joint-detection pass reads node identity.
_ROOF_NODES = [
    ("BWN11AAAAA", "N-BW-RSW", _POST_X0, _POST_Y0),
    ("BWN12AAAAA", "N-BW-RSE", _POST_X1, _POST_Y0),
    ("BWN13AAAAA", "N-BW-RNW", _POST_X0, _POST_Y1),
    ("BWN14AAAAA", "N-BW-RNE", _POST_X1, _POST_Y1),
]
# Rafter ends run out to the roof envelope, which is now the post *outer face* — 2 3/4" past
# each post centre — so the rafter, the sheet and the H channel all die on one plane.
_RAFTER_Y = [_POST_Y0, (_POST_Y0 + _POST_Y1) / 2.0, _POST_Y1]
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
         size=_BEAM, top_elevation=ft(_FLOOR_BEAM_TOP),
         bearing_refs=("PT-BW-1", "PT-BW-3")),
    Beam(uid="BWBM02AAAA", tag="BM-BW-FE", start_node="N-BW-FSE", end_node="N-BW-FNE",
         size=_BEAM, top_elevation=ft(_FLOOR_BEAM_TOP),
         bearing_refs=("PT-BW-2", "PT-BW-4")),
]

_DECK_OUTLINE = (pt(ft(_POST_X0), ft(_POST_Y0)), pt(ft(_POST_X1), ft(_POST_Y0)),
                 pt(ft(_POST_X1), ft(_POST_Y1)), pt(ft(_POST_X0), ft(_POST_Y1)))

# ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
# 40-psf floor table — see checks/structural/deck.py.
FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    joists=JoistSpec(member=_JOIST, spacing=inch(16), direction="x",
                     bearing_refs=("BM-BW-FW", "BM-BW-FE")),
    outline=_DECK_OUTLINE,
    service="deck",
    source="breezeway deck — KDAT 2x8 joists hung flush E-W between the two floor beams",
)

# Composite decking, laid door to door (N-S) across the joists, on breather tape at every
# joist top so the two never trap water against each other. It reaches out to the post
# faces on all four sides at the house end, and past them at the garage end: the deck
# runs on to the stem face, tucking 7/8" under the cladding that oversails it.
DECK = Slab(
    uid="BWSL01AAAA", tag="SL-BW-DECK",
    outline=(pt(ft(_GLAZING_X0), ft(_HOUSE_CLADDING_Y)),
             pt(ft(_GLAZING_X1), ft(_HOUSE_CLADDING_Y)),
             pt(ft(_GLAZING_X1), ft(_GARAGE_STEM_Y)),
             pt(ft(_GLAZING_X0), ft(_GARAGE_STEM_Y))),
    thickness=inch(_DECK_THICKNESS_IN), assembly="PORCH_DECK_COMPOSITE",
    datum="walking_surface",
)

# ============================================================================
# Roof frame: two N-S beams on the post tops, three E-W rafters over them.
# ============================================================================
ROOF_BEAMS = [
    Beam(uid="BWBM03AAAA", tag="BM-BW-RW", start_node="N-BW-RSW", end_node="N-BW-RNW",
         size=_BEAM, top_elevation=ft(_ROOF_BEAM_TOP),
         bearing_refs=("PT-BW-1", "PT-BW-3")),
    Beam(uid="BWBM04AAAA", tag="BM-BW-RE", start_node="N-BW-RSE", end_node="N-BW-RNE",
         size=_BEAM, top_elevation=ft(_ROOF_BEAM_TOP),
         bearing_refs=("PT-BW-2", "PT-BW-4")),
]

# Three 2x6 rafters at ~1'-9" o.c. across the 3'-7" between the beams, seated on top of
# them. A Roof element cannot be used here: resolve/roof_geometry.py only accepts Wall
# bearing refs, and a FloorSystem is pinned to its storey elevation — an absolute-elevation
# Beam is the idiom for framing that belongs to no storey datum (cf. BM-SG-GIRT-R/F).
RAFTERS = [
    Beam(uid=f"BWRF0{i}AAAA", tag=f"BM-BW-R{i}", start_node=f"N-BW-R{i}W",
         end_node=f"N-BW-R{i}E", size="2x6", top_elevation=ft(_RAFTER_TOP),
         bearing_refs=("BM-BW-RW", "BM-BW-RE"))
    for i in range(1, len(_RAFTER_Y) + 1)
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
# run sits on the midline of that reach rather than on the panel edge. That reach is now
# just the 1/2" reveal the uncut panel leaves at this end; it used to be 6 1/8", because the
# cladding stood that far behind a proud stem.
_FCH_N_Y = (_GLAZING_Y1 + _GARAGE_CLADDING_Y) / 2.0

# The shared H channel — the piece the roof eave U and the wall head used to be. An H
# receives a sheet in each of its two slots, which is exactly the joint here now that the
# standing sheet's head and the roof sheet's edge land on the same line: the wall sheet
# enters from below, the roof sheet from the side, and the web between them is the only
# thing crossing the joint. Before, those were two unrelated extrusions 3 1/4" apart in plan
# and 13.4" apart vertically, with 14 1/2" of open elevation between the sheets they held.
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
        # The sill is at the deck surface, which the sheet now passes rather than starts
        # at — it runs 8 1/4" further down to the floor-beam soffit, covering the beam band
        # and the deck edge that used to show below it.
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
            # A jamb runs the sheet's full height, so its top moved up with the sheet's:
            # leaving it at _POST_TOP while _WALL_PANEL_HEIGHT grew pushed its foot 1'-9 3/4"
            # below the sheet, into the pier.
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

MAIN_ELEMENTS = [*NODES, *PADS, *PIERS, *POSTS, *FLOOR_BEAMS, FLOOR, DECK,
                 *ROOF_BEAMS, *RAFTERS, *ROOF_GLAZING, *WALL_GLAZING,
                 *ROOF_TRIM, *WALL_TRIM, *CONNECTORS]
