"""Breezeway — the enclosed 4'x8' polycarbonate shelter between house and garage.

One freestanding structure spanning the 4'-0 1/2" slot between the house's north entry
(``D-M-ENTRY``, centred on x = 4'-0") and the garage's service door (``D-G-SERVICE``,
centred on x = 5'-0"). It touches neither building: four 6x6 ground-contact posts on
isolated piers and frost-depth pads carry the whole thing, and the glazing is *snug* to the
house and garage cladding without lapping into either one's flashing.

Sheet economy is the design. Three 4'x8' sheets of 16mm multiwall polycarbonate:

* two stand vertically as the east and west walls — 4'-0" long (door to door) x 8'-0" tall,
  one whole sheet each, no cut;
* the third is halved into two 4'x4' pieces that make the 4'x8' roof, split at the crown.

Everything else follows from that. The roof envelope is 8'-0" E-W (x = 0'-6" to 8'-6",
centred on x = 4'-6", between the two doors) and 4'-0" N-S. The posts stand 7'-0" apart
E-W, so the roof projects 3 1/4" past the glazing on each side as a drip edge. The 8'-0"
clear is measured from the *walking surface* — the top of the decking, not the joist datum
under it — because that is what a person stands on and what the sheet has to cover; the
sunken garden's guard height is derived the same way, and for the same reason.

Framing directions (the brief's "opposite rotation"):

    FLOOR PLAN (main, z = 0'-0")           ROOF PLAN (z = +8'-8 1/4")
     garage stem                            garage cladding
     |===================|  N-S floor       |===================|  N-S roof beams
     |-------------------|  beams on        |-------------------|  on the post tops
     |-------------------|  the post        |-------------------|  E-W rafters
     |===================|  lines           |===================|  crown at x = 4'-6"
     house      E-W joists @ 16"            house    (wedges on every rafter)
                deck boards N-S

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

The 22" step at the garage door is a known, deferred mismatch: ``D-G-SERVICE`` sits on the
``garage`` storey (the ICF stem top, 1'-10") while this deck and the house entry are both at
0'-0". Recorded in plans/TODO.md, not resolved here.
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

from plan.storeys.garage import GARAGE_Y_SOUTH

# ============================================================================
# Plan geometry — every number here is derived, never repeated.
# ============================================================================
# North face of the house's outsulated wall: the y=36' sheathing plane plus .02" WRB,
# 2" polyiso, 2" EPS, 1/2" furring and 1/2" standing seam (plan/assemblies.py
# CATLIN_EXT_2X6). This is what the breezeway's south end butts.
_HOUSE_CLADDING_Y = 36.0 + (0.02 + 2.0 + 2.0 + 0.5 + 0.5) / 12.0  # 36.4183'

# South face of the garage's ICF stem: the wall line less half the 13" ICF section
# (8" core + 2.5" EPS each side, GARAGE_ICF_8). The stem — not the cladding 5 5/8"
# behind it — is the obstruction at deck level, so it is what sets the clear gap.
_GARAGE_STEM_Y = GARAGE_Y_SOUTH.feet - (8.0 + 2.5 + 2.5) / 24.0  # 40.4583'
# South face of the garage's wood wall above the stem, for the roof's north reach.
_GARAGE_CLADDING_Y = GARAGE_Y_SOUTH.feet - (0.375 + 0.5) / 12.0  # 40.9271'

_CLEAR_GAP_FT = _GARAGE_STEM_Y - _HOUSE_CLADDING_Y  # 4.0400' = 4'-0 1/2"
_PANEL_FT = 4.0  # one 4'x8' sheet, uncut

# E-W: the roof/panel envelope is centred between the two doors (house entry x=4',
# garage service door x=5'), 8'-0" wide.
_ROOF_X0, _ROOF_X1 = 0.5, 8.5
_POST_X0, _POST_X1 = 1.0, 8.0  # 7'-0" apart; roof oversails 6" past each post centre

# N-S: post outer faces snug to the house cladding and the garage stem.
_POST_HALF_FT = 5.5 / 24.0  # half a dressed 6x6
_POST_Y0 = _HOUSE_CLADDING_Y + _POST_HALF_FT  # 36.6475'
_POST_Y1 = _GARAGE_STEM_Y - _POST_HALF_FT  # 40.2292'

# The glazing runs a full uncut 4'-0" from the house cladding north, leaving its 1/2"
# reveal at the garage stem rather than at the house, where the door is.
_GLAZING_Y0 = _HOUSE_CLADDING_Y
_GLAZING_Y1 = _HOUSE_CLADDING_Y + _PANEL_FT
_GLAZING_X0 = _POST_X0 - _POST_HALF_FT  # west post outer face
_GLAZING_X1 = _POST_X1 + _POST_HALF_FT  # east post outer face

_POST_XY = [(_POST_X0, _POST_Y0), (_POST_X1, _POST_Y0),
            (_POST_X0, _POST_Y1), (_POST_X1, _POST_Y1)]

# ============================================================================
# Vertical stack (project-frame absolute; +Z up, 0'-0" is the main-floor datum).
# ============================================================================
_FROST_FT = 42.0 / 12.0  # MN profile frost depth; the pads bear at or below this
_PAD_THICKNESS_FT = 1.0
_PAD_TOP = -_FROST_FT + _PAD_THICKNESS_FT  # -2.5'

_JOIST = "2x8"
_JOIST_DEPTH_FT = 7.25 / 12.0
_BEAM = "2-2x8"  # same depth as the joists, so they hang flush
_DECK_THICKNESS_IN = 1.0
_RAFTER_DEPTH_FT = 5.5 / 12.0

_FLOOR_BEAM_TOP = 0.0  # the main datum: joist tops and beam top are one plane
_PIER_TOP = _FLOOR_BEAM_TOP - _JOIST_DEPTH_FT  # -7 1/4", the floor-beam soffit
_DECK_SURFACE = _DECK_THICKNESS_IN / 12.0  # +1", the walking surface

# 8'-0" of clear headroom above the walking surface puts the roof-beam soffit — and so the
# post tops the beams seat on — at +8'-1".
_CLEAR_HEIGHT_FT = 8.0
_POST_TOP = _DECK_SURFACE + _CLEAR_HEIGHT_FT  # 8.0833' = +8'-1"
_ROOF_BEAM_TOP = _POST_TOP + _JOIST_DEPTH_FT  # 8.6875' = +8'-8 1/4"
_RAFTER_TOP = _ROOF_BEAM_TOP + _RAFTER_DEPTH_FT  # 9.1458' = +9'-1 3/4"

# Drainage wedges on every rafter: 0 at each eave rising to the crown at x = 4'-6", ~1:12.
# The glazing rides on them, so its plane is authored at the *mean* wedge height — a
# GlazingPanel is a flat sheet and the crown is only 3 1/2" over a 4'-0" half-span.
_WEDGE_RISE_IN = 3.5
_GLAZING_THICKNESS_IN = 0.63
_ROOF_GLAZING_TOP = (_RAFTER_TOP + (_WEDGE_RISE_IN / 2.0 + _GLAZING_THICKNESS_IN) / 12.0)
# Verified against the resolved model, not estimated: the garage's south eave hangs its PVC
# fascia underside at +9'-11.4" and its gutter at +9'-11.9", both over this footprint. The
# breezeway crown tops out at +9'-4.1", so the roof tucks under with ~7 1/4" to spare.

# ============================================================================
# Foundations: pad -> concrete pier -> 6x6 post.
# ============================================================================
# The pads and the 6x6 posts keep the uids the retired params/foundations.py stub gave
# them, so their IFC GlobalIds (uuid5 over the uid) survive this rewrite.
PADS = [
    Pad(uid=f"CP{i}00AAAAA", tag=f"PD-BW-{i}",
        outline=(pt(ft(x - 1), ft(y - 1)), pt(ft(x + 1), ft(y - 1)),
                 pt(ft(x + 1), ft(y + 1)), pt(ft(x - 1), ft(y + 1))),
        thickness=ft(_PAD_THICKNESS_FT), bottom_elevation=ft(-_FROST_FT))
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

# 12" round concrete piers carry the wood clear of the ground, pad top up to the floor-beam
# soffit. The 6x6 above is ground-contact rated anyway (the brief), but a post standing in
# soil rots from the end grain first whatever its treatment.
PIERS = [
    Post(uid=f"BWPR{i}AAAAA", tag=f"PR-BW-{i}", position=pt(ft(x), ft(y)),
         size="12 round", height=ft(_PIER_TOP - _PAD_TOP), supported_by=f"PD-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

POSTS = [
    Post(uid=f"CP{i}50AAAAA", tag=f"PT-BW-{i}", position=pt(ft(x), ft(y)),
         size="6x6", height=ft(_POST_TOP - _PIER_TOP), supported_by=f"PR-BW-{i}")
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
# Rafter ends run out to the roof envelope, 6" past each post line.
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
# faces on all four sides, which is also the house cladding and the garage stem.
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
# Glazing: three 4'x8' sheets, two standing and one halved across the roof.
# ============================================================================
# Flutes run E-W, down-slope from the crown to each eave, so the open (draining) flute ends
# land at x = 0'-6" and 8'-6" and the sealed high ends meet under the crown bar.
ROOF_GLAZING = [
    GlazingPanel(
        uid="BWGP01AAAA", tag="GL-BW-ROOF-W",
        outline=(pt(ft(_ROOF_X0), ft(_GLAZING_Y0)), pt(ft(4.5), ft(_GLAZING_Y0)),
                 pt(ft(4.5), ft(_GLAZING_Y1)), pt(ft(_ROOF_X0), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), top_elevation=ft(_ROOF_GLAZING_TOP),
        plane="horizontal", assembly="BREEZEWAY_ROOF_POLY"),
    GlazingPanel(
        uid="BWGP02AAAA", tag="GL-BW-ROOF-E",
        outline=(pt(ft(4.5), ft(_GLAZING_Y0)), pt(ft(_ROOF_X1), ft(_GLAZING_Y0)),
                 pt(ft(_ROOF_X1), ft(_GLAZING_Y1)), pt(ft(4.5), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), top_elevation=ft(_ROOF_GLAZING_TOP),
        plane="horizontal", assembly="BREEZEWAY_ROOF_POLY"),
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
        base_elevation=ft(_DECK_SURFACE), top_elevation=ft(_POST_TOP),
        assembly="BREEZEWAY_GLAZED_WALL", film=_BIRD_FILM),
    GlazingPanel(
        uid="BWGP04AAAA", tag="GL-BW-WALL-E",
        outline=(pt(ft(_GLAZING_X1), ft(_GLAZING_Y0)), pt(ft(_GLAZING_X1), ft(_GLAZING_Y1))),
        thickness=inch(_GLAZING_THICKNESS_IN), plane="vertical",
        base_elevation=ft(_DECK_SURFACE), top_elevation=ft(_POST_TOP),
        assembly="BREEZEWAY_GLAZED_WALL", film=_BIRD_FILM),
]

# ============================================================================
# Glazing trim: every cut edge of every sheet is capped. Billed by the lineal foot.
# ============================================================================
_CHANNEL_DEPTH = inch(1.5)   # how far the extrusion laps the sheet face
_CHANNEL_THICK = inch(1.0)   # its section across the sheet
_ROOF_EAVE_TOP = _RAFTER_TOP + _GLAZING_THICKNESS_IN / 12.0  # wedge is 0 at the eave
_ROOF_CROWN_TOP = (_RAFTER_TOP + (_WEDGE_RISE_IN + _GLAZING_THICKNESS_IN) / 12.0)
# The north F-channel spans from the roof panel's edge back to the garage cladding 6 1/8"
# behind it (the stem below is that much proud of the wall above), so its run sits on the
# midline of that reach rather than on the panel edge.
_FCH_N_Y = (_GLAZING_Y1 + _GARAGE_CLADDING_Y) / 2.0

ROOF_TRIM = [
    # Low (open) flute ends at both eaves: a vented U-channel drilled with weep holes, or
    # the flutes hold the water they are meant to shed and grow algae in it.
    GlazingTrim(uid="BWGT01AAAA", tag="TR-BW-UCH-W", kind=TrimKind.GLAZING_CHANNEL,
                profile="U", weep_holes=True, glazing_ref="GL-BW-ROOF-W",
                path=(pt(ft(_ROOF_X0), ft(_GLAZING_Y0)), pt(ft(_ROOF_X0), ft(_GLAZING_Y1))),
                top_elevation=ft(_ROOF_EAVE_TOP), depth=_CHANNEL_DEPTH,
                thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
    GlazingTrim(uid="BWGT02AAAA", tag="TR-BW-UCH-E", kind=TrimKind.GLAZING_CHANNEL,
                profile="U", weep_holes=True, glazing_ref="GL-BW-ROOF-E",
                path=(pt(ft(_ROOF_X1), ft(_GLAZING_Y0)), pt(ft(_ROOF_X1), ft(_GLAZING_Y1))),
                top_elevation=ft(_ROOF_EAVE_TOP), depth=_CHANNEL_DEPTH,
                thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
    # The crown: both sheets' high flute ends meet here over the wedge apexes, sealed with
    # solid (not vented) tape under a concealed-fastener aluminium glazing bar.
    GlazingTrim(uid="BWGT03AAAA", tag="TR-BW-BAR-CROWN", kind=TrimKind.GLAZING_BAR,
                profile="bar", sealed_tape=True,
                path=(pt(ft(4.5), ft(_GLAZING_Y0)), pt(ft(4.5), ft(_GLAZING_Y1))),
                top_elevation=ft(_ROOF_CROWN_TOP + 0.5 / 12.0), depth=inch(2.0),
                thickness=inch(2.5), material="aluminum-extrusion"),
    # North and south roof edges run parallel to the flutes and butt the cladding: an
    # F-channel receiver, with a bent leg covering back to the wall. The north leg is the
    # long one — the garage's wood wall stands 5 5/8" behind its stem.
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
_WALL_PANEL_HEIGHT = ft(_POST_TOP - _DECK_SURFACE)
WALL_TRIM = []
for _i, (_tag, _x, _ref) in enumerate(
        (("W", _GLAZING_X0, "GL-BW-WALL-W"), ("E", _GLAZING_X1, "GL-BW-WALL-E")), start=1):
    _run = (pt(ft(_x), ft(_GLAZING_Y0)), pt(ft(_x), ft(_GLAZING_Y1)))
    WALL_TRIM += [
        GlazingTrim(uid=f"BWGT1{_i}AAAA", tag=f"TR-BW-SILL-{_tag}",
                    kind=TrimKind.GLAZING_CHANNEL, profile="U", weep_holes=True,
                    glazing_ref=_ref, path=_run,
                    top_elevation=ft(_DECK_SURFACE) + _CHANNEL_DEPTH, depth=_CHANNEL_DEPTH,
                    thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
        GlazingTrim(uid=f"BWGT2{_i}AAAA", tag=f"TR-BW-HEAD-{_tag}",
                    kind=TrimKind.GLAZING_CHANNEL, profile="F", glazing_ref=_ref,
                    path=_run, top_elevation=ft(_POST_TOP), depth=_CHANNEL_DEPTH,
                    thickness=_CHANNEL_THICK, material="aluminum-extrusion"),
    ]
    for _side, _y in (("S", _GLAZING_Y0), ("N", _GLAZING_Y1)):
        _half = _GLAZING_THICKNESS_IN / 24.0
        WALL_TRIM.append(GlazingTrim(
            uid=f"BWGJ{_side}{_i}AAAA", tag=f"TR-BW-JAMB-{_tag}{_side}",
            kind=TrimKind.GLAZING_CHANNEL, profile="F", glazing_ref=_ref,
            vertical=True,
            path=(pt(ft(_x - _half), ft(_y)), pt(ft(_x + _half), ft(_y))),
            top_elevation=ft(_POST_TOP), depth=_WALL_PANEL_HEIGHT,
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
