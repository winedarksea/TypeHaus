"""Generated foundation support: house footings, garage ICF stem + slab.

- House: strip footings (20" x 8") under every basement concrete wall.
- Garage: freestanding ICF stem (6" core) from frost depth to 22" above grade,
  wood walls bear on top (the ``garage`` storey elevation), footing under.
- House footings additionally get a bedding-prep record (undercut, geotextile, drain
  tile, compacted washed-stone bed, perimeter foam) — see ``HOUSE_FOOTING_BEDDING``.

The breezeway's pads/piers/posts used to live here as a roofless stub; they now belong to
the whole structure in ``params/breezeway.py``.
"""

from __future__ import annotations

from typehaus import (
    DrainTile,
    Drywell,
    Footing,
    FootingBedding,
    FoundationWall,
    Node,
    Service,
    Slab,
    SlabThermalBreak,
    SleevePenetration,
    face,
    ft,
    inch,
    pt,
)

# The ICF form's own dimensions, from the assembly that declares them. The stem's
# alignment and the slab's inset are both measured off the section, so neither is
# repeated here.
from plan.assemblies import GARAGE_ICF_CORE, GARAGE_ICF_EPS

# One source of truth for where the garage stands: the wall lines the wood walls above are
# authored on. The stem must sit under them and the slab inside them, so both derive from
# there rather than repeating the literal.
from plan.storeys.garage import (
    GARAGE_STEM_REVEAL,
    GARAGE_Y_NORTH,
    GARAGE_Y_SOUTH,
    OVERHEAD_DOOR_OFFSET,
    OVERHEAD_DOOR_WIDTH,
    SERVICE_DOOR_OFFSET,
    SERVICE_DOOR_WIDTH,
)

# --- the site datum ---------------------------------------------------------------
#
# Finished grade, in the project frame. The vertical datum of this model is the main floor
# (FFE = 0'-0"), so "raising the house 2'-10" out of the ground" is authored the way a
# drawing set states it: the floor stays at 0'-0" and grade goes down. Everything pinned to
# soil rather than to the house — the garage that is still driven into at grade, its stem
# reveal, the breezeway's frost pads, the hydrant's bury — derives from here.
#
# 2'-6" on 2026-08-18, then 2'-10" on 2026-08-21: the mixed I-joist / EPS-formed deck over
# the basement is deeper than the 9" cast slab it replaced, so the house rose 4" and the
# basement floor stayed where it was rather than surrendering the headroom.
#
# **It did NOT move again on 2026-08-23.** The flat-bearing-seat rework deepened that deck
# to 14 3/8" and took the basement slab UP 2 9/16" to meet it. The house does not rise; the
# basement floor does. Grade, the garage, the breezeway pads and the hydrant's bury are all
# pinned to soil and none of them moved — which is the whole reason this constant is
# authored as a distance from the datum rather than derived from the basement.
#
# ``plan/site.py`` is ``# haus: editable`` and may hold only literals, so it repeats this
# number as ``Site.grade``. ``plan/manifest.py`` asserts the two agree; do not edit one
# without the other.
SITE_GRADE = ft(-2, -10)

# --- house strip footings --------------------------------------------------------
#
# **The index is authored, not counted.** Each uid is ``CF{index:03d}AAAAA``, and the index
# used to come from ``enumerate()`` over a bare tag list — so removing a tag renumbered
# every footing after it and changed their IFC GlobalIds, against decision #16. Writing the
# pairs out makes the number what it always meant to be: this footing's permanent name.
# Add a footing with the next unused index; retire one by deleting its row and never
# reusing the number.
#
# 15, 16, 18 and 19 are retired (2026-08-21). W-B-CW, W-B-CE, W-B-STR2 and W-B-CW3 became
# framed partitions in the basement-ceiling overhaul — a stud wall on the slab needs no
# 20"x8" strip, no bedding and no drain tile, and those four runs of tile had nothing to
# collect. FT-B-STR stays: W-B-STR is still a bearing wall, framed or not.
_HOUSE_WALL_TAGS = (
    (1, "W-B-S1"), (2, "W-B-S2"), (3, "W-B-S3"), (4, "W-B-E1"), (5, "W-B-E2"),
    (6, "W-B-N1"), (7, "W-B-N2"), (8, "W-B-N3"), (9, "W-B-W1"), (10, "W-B-W2"),
    (11, "W-B-CS"), (12, "W-B-CS2"), (13, "W-B-CN"), (14, "W-B-CN2"),
    (17, "W-B-STR"),
    # 20/21 are the halves the 2026-08-23 ESS-closet relocation split off: W-B-N4 is the
    # west 6'-0" of the old W-B-N3 and W-B-STR3 the south 9'-2 5/8" of the old W-B-STR.
    # Each keeps its own strip because each is still a wall on the same footing line — the
    # split is where a partition tees in, not where the pour stops.
    (20, "W-B-N4"), (21, "W-B-STR3"),
    # 22 is the east 8'-0" of the old W-B-S3, split off at the excavation edge (x=28'-0")
    # on 2026-08-28 so each half could author the backfill it actually retains.
    (22, "W-B-S4"),
)

# The three south strips are formed in an insulated footing form, the rest are poured
# against the bedding as before. They are the strips the sunken garden runs along: the
# garden floor is at -9'-1 7/16" and they bottom out at -9'-9 7/16" — both rose 2 9/16" on
# 2026-08-23 with the basement slab, so the cover between them is unchanged at **8" of frost
# cover** against MN Rules 1303.1600's 42" for Ramsey County — measured, as IRC R403.1.4.1
# says to, from the lowest adjacent grade, which beside them is the garden floor and not the
# -2'-10" site plane six and a half feet overhead.
#
# Nothing said so until 2026-08-22: ``structural.frost_depth`` compared every footing to one
# global scalar and passed all 35. It derives a local grade per footing now, and the answer
# to what it found is IRC R403.3 — the horizontal wings under the garden slab
# (``params/sunken_garden.FROST_WINGS``) plus this form, which keeps the concrete off the
# soil on both faces. Deepening the strips is the alternative and it is not available:
# FT-B-BRICK's derivation leans on FT-B-S2/S3's 10" south toe being there to bear on, so
# re-centring the strips and re-footing the brick wall are one change and not this one.
#
# ``Footing`` had no assembly field at all before that date — no material, no reinforcement —
# so every footing in every house priced and scheduled as plain cast concrete out of a
# hardcoded category row, and this detail was not expressible.
_FROST_FORMED = {"W-B-S1", "W-B-S2", "W-B-S3", "W-B-S4"}

HOUSE_FOOTINGS = [
    Footing(uid=f"CF{i:03d}AAAAA", tag=f"FT-{t[2:]}", under=t,
            width=inch(20), depth=inch(8),
            assembly="FOOTING_FPSF_20" if t in _FROST_FORMED else None)
    for i, t in _HOUSE_WALL_TAGS
]

# Bearing prep below every house footing: 7" undercut, geotextile, drain tile, compacted
# washed stone — a drained bearing surface that also breaks footing-to-wet-clay thermal
# contact. 4" perimeter foam matches CATLIN_BASEMENT_12's exterior XPS.
# One bedding per footing, sharing the footing's own permanent index for the same reason.
HOUSE_FOOTING_BEDDING = [
    FootingBedding(uid=f"CFB{i:03d}AAAA", tag=f"FB-{t[2:]}", host_ref=f"FT-{t[2:]}",
                   undercut=inch(7), perimeter_insulation=inch(4),
                   drain_tile_spec=DrainTile(diameter=inch(4), sock=True,
                                             discharge="daylight"))
    for i, t in _HOUSE_WALL_TAGS
]

# --- glazed-brick veneer plinth (W-B-BRICK) ---------------------------------------
# Deliberately NOT appended to _HOUSE_WALL_TAGS: that loop pours a 20"x8" strip monolithic
# with the house footing, which is the thermal bridge this detail exists to avoid. Instead
# it's a shallow plinth cast ON the house footing's projecting toe (FT-B-S2/S3's toe runs
# 10" south of the brick face), separated by a 2" XPS bed (FB-B-BRICK) rather than a
# ``Dowel`` block — ``Dowel.axis`` can't describe a horizontal bed, so the veneer's own
# masonry ties do that job instead (plans/TODO.md).
#
# 10"x5": 10" wide clears the brick's outer face (-9.175") with ~0.4" to spare and stays
# inside the house footing's -10" edge; 5" deep over the 2" bed tops out at -8'-5",
# D-B-PATIO's raised threshold — the highest it can go without crossing the door. Full
# derivation on W-B-BRICK in plan/storeys/basement.py.
#
# Stops at x=28' on the sunken garden's east wall axis, where FT-SG-E1 already breaks
# thermally from the house footing — no third break needed, no collision (FT-SG-E1 sits
# 1'-5" below this plinth).
# On the same insulated form as the strips it bears on (2026-08-22): its bottom is at
# -9'-2", which is 2" **above** the garden floor beside it, so of the four footings the
# sunken garden reaches this is the one with negative frost cover. The R403.3 wings under
# the garden slab are what answer it; the form is what keeps this pour from being a
# 10"-wide thermal bridge sitting in the open at the bottom of the court.
VENEER_PLINTH = [
    Footing(uid="CFV301AAAA", tag="FT-B-BRICK", under="W-B-BRICK",
            width=inch(10), depth=inch(5), assembly="FOOTING_FPSF_20"),
]

# Same ``cast_foam_in_aggregate`` record the sunken garden's house-adjacent footings carry
# (2" 40psi XPS), used here as a bed rather than a block. No drain tile: sits a foot above
# the house footing's own tile with nothing to collect.
VENEER_PLINTH_BEDDING = [
    FootingBedding(uid="CFV351AAAA", tag="FB-B-BRICK", host_ref="FT-B-BRICK",
                   undercut=inch(2), geotextile=False, drain_tile=False,
                   cast_foam_in_aggregate=True),
]

# --- garage ICF stem (basement storey; absolute elevations) -----------------------
#
# Every elevation in this block is measured from ``SITE_GRADE``, not from the project datum.
# The garage is driven into at grade and stays there; when grade moved 2'-6" down — and
# again 4" on 2026-08-21 — the whole garage foundation went with it, while the house it
# stands beside did not move at all.
_GRADE_FT = SITE_GRADE.feet
_FROST = 42.0 / 12.0  # frost depth below grade
# Exposed above grade, and the garage storey datum besides — ``GARAGE_STEM_REVEAL`` is the
# *reveal*, a height above soil, authored next to the wall lines it belongs with
# (plan/storeys/garage.py); grade is what it is a reveal above.
_STEM_TOP = ft(_GRADE_FT + GARAGE_STEM_REVEAL.feet)
# A car can't climb a 22" ICF stem, so the east stem gaps at the overhead door: the flanking
# segments keep the full reveal, and the segment behind the door becomes a grade beam flush
# with the slab (grade), no curb across the opening. W-G-E above is untouched (splitting it
# would break the ridge closure it carries) — the door reaches down via a negative
# sill_height in plan/storeys/garage.py instead.
_GRADE_BEAM_TOP = SITE_GRADE
# How much wider than the opening the service door's stem gap is formed — see N-GF-S-DRW.
_SERVICE_GAP_MARGIN = ft(0, 3)

GARAGE_STEM_NODES = [
    Node(uid="CGF001AAAA", tag="N-GF-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGF002AAAA", tag="N-GF-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGF003AAAA", tag="N-GF-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGF004AAAA", tag="N-GF-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
    Node(uid="CGF005AAAA", tag="N-GF-E-DRS", position=pt(ft(24), GARAGE_Y_SOUTH + OVERHEAD_DOOR_OFFSET)),
    Node(uid="CGF006AAAA", tag="N-GF-E-DRN",
         position=pt(ft(24), GARAGE_Y_SOUTH + OVERHEAD_DOOR_OFFSET + OVERHEAD_DOOR_WIDTH)),
    # Service door gap in the south stem (2026-08-01). Unlike the overhead door's gap, this
    # one gets 3" margin each side: the hydrant line (PR-G-HYDRANT-CW) crosses buried at
    # x=5'-0", exactly the door's west jamb, so a flush gap would land the crossing on the
    # joint between two footings and trip mep.footing_clearance in both. The wider block-out
    # puts it unambiguously inside the grade beam.
    Node(uid="CGF007AAAA", tag="N-GF-S-DRW",
         position=pt(SERVICE_DOOR_OFFSET - _SERVICE_GAP_MARGIN, GARAGE_Y_SOUTH)),
    Node(uid="CGF008AAAA", tag="N-GF-S-DRE",
         position=pt(SERVICE_DOOR_OFFSET + SERVICE_DOOR_WIDTH + _SERVICE_GAP_MARGIN,
                     GARAGE_Y_SOUTH)),
    # The SE/NE brick-ledge corner returns (garage.py's W-G-BRICK-SRET/NRET, 2026-08-26)
    # need 4'-0" of widened, brick-ledged stem under them too, same as the east piers. These
    # split the last 4'-0" off the corner end of W-GF-S2/W-GF-N.
    Node(uid="CGF009AAAA", tag="N-GF-S-BRICK", position=pt(ft(20), GARAGE_Y_SOUTH)),
    Node(uid="CGF010AAAA", tag="N-GF-N-BRICK", position=pt(ft(20), GARAGE_Y_NORTH)),
]

# Aligns the stem's exterior EPS face to the 24'x24' node line, which is also the wood
# walls' zip-R plane (`alignment=face("zip-r-ext")` above) — coplanar, so only the 7/8"
# rainscreen + cladding projects past and drips clear. Left unaligned it stood 5 5/8" proud
# of the cladding, a shelf for rain to pool on (plans/TODO.md).
#
# Uses `face("concrete-ext")`, not `face("eps-ext")`: the fuzzy prefix matcher in
# resolve/topology.py would match "eps-ext" to the *eps-int* layer first. Concrete face is
# unambiguous and already the basement walls' datum; offsetting the axis outward by one EPS
# thickness lands the exterior foam face on the node line.
_ALIGN = face("concrete-ext", offset=GARAGE_ICF_EPS)

_STEM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN, top_elevation=_STEM_TOP,
             bottom_elevation=ft(_GRADE_FT - _FROST))
# The two east segments flanking the overhead door carry the brick wainscot
# (plan/storeys/garage.py's W-G-BRICK-S/N), so their stem is the brick-ledge form: the same
# wall above the shelf, widened below it to bear a full 3 5/8" wythe. A sibling dict rather
# than a mutation of _STEM, which every other segment shares.
#
# These walls are NOT conceptually new — they exist today only because the stem drops to a
# grade beam under the door, and they already happen to be exactly the 4'-0" piers the
# wainscot wants. Only the assembly string changes; the uids stay.
_STEM_BRICKLEDGE = dict(assembly="GARAGE_ICF_6_BRICKLEDGE", alignment=_ALIGN,
                        top_elevation=_STEM_TOP,
                        bottom_elevation=ft(_GRADE_FT - _FROST))
_GRADE_BEAM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN,
                   top_elevation=_GRADE_BEAM_TOP,
                   bottom_elevation=ft(_GRADE_FT - _FROST))

GARAGE_STEM_WALLS = [
    # South stem, split three ways at the service door on 2026-08-01 — the east wall's
    # pattern exactly. W-GF-S1 keeps the original uid as the remnant of the single wall;
    # the grade beam and the far segment are new.
    FoundationWall(uid="CGF101AAAA", tag="W-GF-S1", start_node="N-GF-SW",
                   end_node="N-GF-S-DRW", **_STEM),
    FoundationWall(uid="CGF107AAAA", tag="W-GF-S-DR", start_node="N-GF-S-DRW",
                   end_node="N-GF-S-DRE", **_GRADE_BEAM),
    # W-GF-S2 split again (2026-08-26): its corner-adjacent 4'-0" now carries the SE brick
    # return, so it needs the brick-ledge stem too. W-GF-S2 keeps its uid on the remnant
    # (SERVICE_DOOR side); W-GF-S3 is the new corner piece.
    FoundationWall(uid="CGF108AAAA", tag="W-GF-S2", start_node="N-GF-S-DRE",
                   end_node="N-GF-S-BRICK", **_STEM),
    FoundationWall(uid="CGF109AAAA", tag="W-GF-S3", start_node="N-GF-S-BRICK",
                   end_node="N-GF-SE", **_STEM_BRICKLEDGE),
    FoundationWall(uid="CGF102AAAA", tag="W-GF-E1", start_node="N-GF-SE",
                   end_node="N-GF-E-DRS", **_STEM_BRICKLEDGE),
    FoundationWall(uid="CGF105AAAA", tag="W-GF-E-DR", start_node="N-GF-E-DRS",
                   end_node="N-GF-E-DRN", **_GRADE_BEAM),
    FoundationWall(uid="CGF106AAAA", tag="W-GF-E2", start_node="N-GF-E-DRN",
                   end_node="N-GF-NE", **_STEM_BRICKLEDGE),
    # W-GF-N split (2026-08-26) the same way, for the NE brick return: W-GF-N keeps its uid
    # on the remnant (west side); W-GF-N2 is the new corner piece.
    FoundationWall(uid="CGF103AAAA", tag="W-GF-N", start_node="N-GF-N-BRICK",
                   end_node="N-GF-NW", **_STEM),
    FoundationWall(uid="CGF110AAAA", tag="W-GF-N2", start_node="N-GF-NE",
                   end_node="N-GF-N-BRICK", **_STEM_BRICKLEDGE),
    FoundationWall(uid="CGF104AAAA", tag="W-GF-W", start_node="N-GF-NW",
                   end_node="N-GF-SW", **_STEM),
]

# Not a comprehension any more: the east wall split into three, and a fresh uid per item
# would reassign CGF203/204AAAA (footings that didn't conceptually change) to the new door
# pieces. Original uids are kept; only the grade beam and far door-split piece are new.
#
# `center_on="wall"`: the stem runs 0"..11" inboard of the raw node line, so a 20" strip
# centred on the node line (the default) would leave 10" of toe under nothing. Centred on
# the resolved section instead, the toe is a symmetric 4 1/2" each side.
_GARAGE_FOOTING = dict(width=inch(20), depth=inch(8), center_on="wall")
# FT-GF-E1/E2 (and, since the SE/NE brick returns, FT-GF-S3/N2) are wider because their
# stems are (GARAGE_ICF_6_BRICKLEDGE, above). Two facts worth stating rather than
# rediscovering:
#
# 1. `center_on="wall"` takes `band_axis` over EVERY resolved layer polygon
#    (resolve/envelope.py), and the ledge band is now one of them — so these two footings
#    re-centre on the stepped section (276 3/8" .. 292 5/8", 16 1/4" wide once the gwb band
#    is counted) and sit 2" east of their un-ledged neighbours: FT-GF-E-DR centres on
#    x = 282 1/2", these two on 284 1/2". That is the correct behaviour — the footing wants
#    to be under the ledge — but nothing downstream may be dimensioned off their edges.
# 2. It also drops the toe. At the shared 20" a symmetric toe under an 11" section is
#    4 1/2"; under the stepped section it would be ~1 7/8". 24" gives 3 7/8" outboard of
#    the ledge (272 1/2" .. 296 1/2") and 4 1/2" inboard, back in the same range.
_GARAGE_FOOTING_BRICKLEDGE = dict(width=inch(24), depth=inch(8), center_on="wall")

GARAGE_FOOTINGS = [
    Footing(uid="CGF201AAAA", tag="FT-GF-S1", under="W-GF-S1", **_GARAGE_FOOTING),
    Footing(uid="CGF207AAAA", tag="FT-GF-S-DR", under="W-GF-S-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF208AAAA", tag="FT-GF-S2", under="W-GF-S2", **_GARAGE_FOOTING),
    Footing(uid="CGF209AAAA", tag="FT-GF-S3", under="W-GF-S3", **_GARAGE_FOOTING_BRICKLEDGE),
    Footing(uid="CGF202AAAA", tag="FT-GF-E1", under="W-GF-E1",
            **_GARAGE_FOOTING_BRICKLEDGE),
    Footing(uid="CGF205AAAA", tag="FT-GF-E-DR", under="W-GF-E-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF206AAAA", tag="FT-GF-E2", under="W-GF-E2",
            **_GARAGE_FOOTING_BRICKLEDGE),
    Footing(uid="CGF203AAAA", tag="FT-GF-N", under="W-GF-N", **_GARAGE_FOOTING),
    Footing(uid="CGF210AAAA", tag="FT-GF-N2", under="W-GF-N2", **_GARAGE_FOOTING_BRICKLEDGE),
    Footing(uid="CGF204AAAA", tag="FT-GF-W", under="W-GF-W", **_GARAGE_FOOTING),
]

# Filed on "garage", where it belongs, with an absolute ``top_elevation``: the garage storey
# datum is the ICF stem top, but this slab pours at grade, and ``Slab.top_elevation`` is how
# a slab says so without being re-filed onto whichever storey happens to sit at its
# elevation. (It lived on "main" until 2026-08-18 precisely because that override did not
# exist and "main" was at 0'-0".) Inset from the wall lines = the 11" stem section + the
# usual 1/2" gap to the stem's interior face, keeping the pour inside the stem.
_SLAB_GAP = inch(0.5)
_SLAB_INSET = GARAGE_ICF_CORE + GARAGE_ICF_EPS + GARAGE_ICF_EPS + _SLAB_GAP
_slab_y_s = GARAGE_Y_SOUTH + _SLAB_INSET
_slab_y_n = GARAGE_Y_NORTH - _SLAB_INSET
GARAGE_SLAB = Slab(
    uid="CGS501AAAA", tag="SL-G-FLOOR",
    outline=(pt(_SLAB_INSET, _slab_y_s), pt(ft(24) - _SLAB_INSET, _slab_y_s),
             pt(ft(24) - _SLAB_INSET, _slab_y_n), pt(_SLAB_INSET, _slab_y_n)),
    thickness=inch(3.5), assembly="GARAGE_SLAB_ON_GRADE", top_elevation=SITE_GRADE,
    perimeter_thermal_break=SlabThermalBreak(material_ref="xps", thickness=inch(1)),
)

# --- garage service-door landing ---------------------------------------------------
#
# D-G-SERVICE's threshold is at 0'-0", level with the breezeway deck outside it (that pairing
# is a house rule — see houses/catlin/CLAUDE.md). The garage slab is at grade, -2'-10". So
# from 2026-08-18 there are five risers between the two, inside the garage.
#
# **This used to be five concrete `Slab`s, SL-G-STEP-0..4, and four of them are now a
# `Stair`** (ST-G-SERVICE, in plan/storeys/garage.py — a UI-movable element has to live in an
# editable file). The comment that stood here explained why a `Stair` was impossible —
# "`Stair` takes its rise from a pair of storey elevations through a FloorOpening in the
# storey above, and this run is a step-down *within* one storey with no floor to open" — and
# it was true until 2026-08-22, when `Stair.floor_opening` became optional and
# `base_elevation`/`top_elevation` were added for exactly this case. It also claimed
# "`structural.stair_riser_uniformity` grades the result", which was **not** true: that check
# and `code.R311_7_8_handrail` both iterate `model.stairs`, so a five-riser flight with no
# handrail drew no finding of any kind. Both grade it now, which is the point of the change.
#
# What stays here is the **landing**: a 3'-0" x 3'-0" pad at the threshold, poured with the
# slab, R311.7.6's "a landing at least as deep as the stair is wide". A landing is a floor,
# not a flight; it has no business being generated by a stair resolver.
#
# It lands in the south-west corner, on the door's own 5'-0"..8'-0" band. The 16' overhead
# door is in the *east* wall between y=45' and y=61', so the drive path never crosses this;
# the flight below the landing stops at y=47'-2 3/8", clear of it.
_STEP_X0 = SERVICE_DOOR_OFFSET
_STEP_X1 = SERVICE_DOOR_OFFSET + SERVICE_DOOR_WIDTH
_STEP_LANDING_FT = 3.0         # R311.7.6: a landing at least as deep as the run is wide

GARAGE_STEPS = [
    Slab(uid="CGS510AAAA", tag="SL-G-STEP-0",
         outline=(pt(_STEP_X0, GARAGE_Y_SOUTH), pt(_STEP_X1, GARAGE_Y_SOUTH),
                  pt(_STEP_X1, GARAGE_Y_SOUTH + ft(_STEP_LANDING_FT)),
                  pt(_STEP_X0, GARAGE_Y_SOUTH + ft(_STEP_LANDING_FT))),
         thickness=inch(6), top_elevation=ft(0)),
]

# --- garage hydrant: supply sleeve, gravel pit -------------------------------------
#
# FX-G-HYDRANT stands on the west wall near the NW corner. The sleeve and drywell below it
# are not UI-movable, so they live here rather than in editable plan/fixtures.py.
#
# ``_FROST`` above is the *footing* frost depth (42"); the hydrant's 72" bury is a separate
# number — its own shutoff-valve depth, 2'-6" below the ICF stem bottom, consistent but not
# the same thing.
#
# Position (2026-08-15): the hydrant is freestanding, not wall-mounted, because nowhere on
# a wall clears the footings' 45° bearing-influence line at this bury depth. The old NW
# corner spot (1'-6", 62') had the weep-stone pocket overlapping FT-GF-W outright — only
# passing footing_clearance because of a sleeve that bore concrete the pipe never touched
# (deleted). The clear zone is x >= 4'-10 1/2", y <= 59'-7 7/8", floor not wall — no wall
# position works here, so it stands free like a yard hydrant should (Y34 barrel, unlike the
# two wall hydrants in plan/fixtures.py).
#
# x=5'-0" sits on the existing supply line (PR-G-HYDRANT-CW runs north at x=5'-0" through
# three sleeves), keeping the run straight instead of jogging. y=59'-6" clears FT-GF-N by
# 35 7/8" (34" required) and stays inside the overhead door's 45'..61' band.
#
# Consequence: the hydrant sits 5' out into the parking area, not against the wall — every
# compliant position here is in the room. Mitigate with a bollard/wheel stop if needed;
# don't move it back to the wall.
HYDRANT_X_FT = 5.0          # on the service line — the run reaches it without a jog
HYDRANT_Y_FT = 59.5         # north bay, clear of FT-GF-N's influence line
HYDRANT_BURY_FT = 6.0       # shutoff depth below grade — the code number for this fixture

# A 4" topping pedestal (SL-G-HYDRANT-PED) that lifted the slab penetration above the
# salt-slush wet line was retired 2026-08-03 by owner decision. Replaced by spec, not
# geometry — a flexible chloride-tolerant sealant at the penetration instead (see
# notes/garage_hydrant.md). Bury, sleeve, and drywell below grade are unchanged.

# Filed on "garage" with SL-G-FLOOR, the slab it passes through — the sleeve resolver looks
# its host up by tag across the whole plan, so the storey only labels the resolved sleeve,
# and labelling it with the structure it belongs to is the honest answer. purpose=WATER_COLD,
# not the DRAIN default: carries supply down only.
GARAGE_HYDRANT_SLEEVE = SleevePenetration(
    uid="CGP602AAAA", tag="SP-G-HYDRANT", host_ref="SL-G-FLOOR",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    pipe_diameter=inch(0.75), sleeve_diameter=inch(2),
    serves_fixture="FX-G-HYDRANT", purpose=Service.WATER_COLD,
)

# The gravel bed FX-G-HYDRANT's own weep drains into: a Woodford Y34-style frost-free
# hydrant self-drains through a weep hole at its buried shutoff, into stone packed around
# the valve. Not a catch basin for wash-down water, no floor-drain reading (see
# notes/garage_hydrant.md) — solely the hydrant's own weep. Modeled as a FootingBedding only
# because that was the closest thing available; the stand-in was billing its excavation
# perimeter as (nonexistent) perimeter drain tile in the sitework take-off.
#
# Sits directly on the hydrant's own stack (HYDRANT_X_FT/Y_FT) — the pocket, being the
# deepest excavation in the assembly, is what the 45° influence line grades hardest, so it
# (not the pipe) sets how far out the fixture stands. See HYDRANT_X_FT above.
#
# Re-sized 2026-08-15 from 2'x4' deep (12.6 cu ft, bottom -9'-0", overlapped FT-GF-W by 4"
# in plan — nothing was grading it, since `mep.footing_clearance` only walks pipe runs) down
# to 1'-6"x1'-6" deep, top -5'-6", ~2.6 cu ft. Bottom -7'-0" is 34" below bearing; the
# stone's edge stands 35 1/2" off FT-GF-W and 35 7/8" off FT-GF-N — no slack left in either.
GARAGE_HYDRANT_DRYWELL = Drywell(
    uid="CGP603AAAA", tag="DRW-G-HYDRANT",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    diameter=inch(18), depth=inch(18),
    top_elevation=ft(_GRADE_FT - (HYDRANT_BURY_FT - 0.5)),
    geotextile=True, inlet_refs=("FX-G-HYDRANT",),
)

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *HOUSE_FOOTING_BEDDING, *VENEER_PLINTH,
                     *VENEER_PLINTH_BEDDING, *GARAGE_STEM_NODES,
                     *GARAGE_STEM_WALLS, *GARAGE_FOOTINGS, GARAGE_HYDRANT_DRYWELL]
GARAGE_ELEMENTS = [GARAGE_SLAB, *GARAGE_STEPS, GARAGE_HYDRANT_SLEEVE]
