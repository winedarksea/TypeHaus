"""Generated foundation support: house footings, garage ICF stem + slab.

- House: strip footings (20" x 8") under every basement concrete wall.
- Garage: freestanding ICF stem (6" core) from frost depth to 22" above grade,
  wood walls bear on top (the ``garage`` storey elevation), footing under.
- House footings additionally get a bedding-prep record (undercut, geotextile, drain
  tile, compacted washed-stone bed, perimeter foam) — see ``HOUSE_FOOTING_BEDDING``.

The breezeway's pads/piers/posts belong to the whole structure in ``params/breezeway.py``.
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
# (FFE = 0'-0"), so "raising the house out of the ground" is authored the way a drawing set
# states it: the floor stays at 0'-0" and grade goes down. Everything pinned to soil rather
# than to the house — the garage that is driven into at grade, its stem reveal, the
# breezeway's frost pads, the hydrant's bury — derives from here.
#
# Grade, the garage, the breezeway pads and the hydrant's bury are all pinned to soil; the
# basement floor is not — it is authored separately and can move without grade moving,
# which is the whole reason this constant is authored as a distance from the datum rather
# than derived from the basement.
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
# 15, 16, 18 and 19 are retired. W-B-CW, W-B-CE, W-B-STR2 and W-B-CW3 became framed
# partitions in the basement-ceiling overhaul — a stud wall on the slab needs no 20"x8"
# strip, no bedding and no drain tile, and those four runs of tile had nothing to collect.
# FT-B-STR stays: W-B-STR is still a bearing wall, framed or not.
_HOUSE_WALL_TAGS = (
    (1, "W-B-S1"), (2, "W-B-S2"), (3, "W-B-S3"), (4, "W-B-E1"), (5, "W-B-E2"),
    (6, "W-B-N1"), (7, "W-B-N2"), (8, "W-B-N3"), (9, "W-B-W1"), (10, "W-B-W2"),
    (11, "W-B-CS"), (12, "W-B-CS2"), (13, "W-B-CN"), (14, "W-B-CN2"),
    (17, "W-B-STR"),
    # 20/21 are the halves the ESS-closet relocation split off: W-B-N4 is the west 6'-0" of
    # the old W-B-N3 and W-B-STR3 the south 9'-2 5/8" of the old W-B-STR. Each keeps its own
    # strip because each is still a wall on the same footing line — the split is where a
    # partition tees in, not where the pour stops.
    (20, "W-B-N4"), (21, "W-B-STR3"),
    # 22 is the east 8'-0" of the old W-B-S3, split off at the excavation edge (x=28'-0")
    # so each half could author the backfill it actually retains.
    (22, "W-B-S4"),
    # 23 was W-B-S1B, the west 3'-10" of the old W-B-S1 split off when the sauna rotated
    # onto the garden wall (2026-09-05). The same day's shrink pulled the sauna east to the
    # excavation edge, W-B-S1 is one unsplit segment again, and the index is **retired, not
    # reused** — a footing index is authored permanently, so 24 stays where it is.
    # 24 is the 3'-8 5/8" of the old W-B-STR3 between the rotated bathroom's north
    # partition and N-B-BA-W. It is a BEARING wall — FS-M-MECH and FS-M-STAIR both name it
    # — so unlike W-B-STR2 beside it (which carries nothing and stands on the slab) it
    # keeps the strip its parent had.
    (24, "W-B-STR3B"),
)

# The three south strips are formed in an insulated footing form, the rest are poured
# against the bedding as before. They are the strips the sunken garden runs along: the
# garden floor is at -9'-1 7/16" and they bottom out at -9'-9 7/16", **8" of frost cover**
# against MN Rules 1303.1600's 42" for Ramsey County — measured, as IRC R403.1.4.1 says to,
# from the lowest adjacent grade, which beside them is the garden floor and not the -2'-10"
# site plane six and a half feet overhead.
#
# ``structural.frost_depth`` derives a local grade per footing; the answer to what it finds
# here is IRC R403.3 — the horizontal wings under the garden slab
# (``params/sunken_garden.FROST_WINGS``) plus this form, which keeps the concrete off the
# soil on both faces. Deepening the strips is not an available alternative: FT-B-S2/S3's
# south toe is what carries SG_VENEER_BEAM_14's isolation board at -8"..-10" (that is what
# `_SOUTH_TOE_TRIM` below is for), so re-centring the strips and re-founding the brick wall
# are one change and not this one. It used to be the veneer PLINTH that leaned on that toe;
# the plinth is gone and the constraint is not.
# W-B-S1B joined on 2026-09-05 and left the same day with the sauna shrink. FT-B-S1 is one
# unsplit strip again, and it is back inside the court's 42" frost reach — which is what the
# insulated form and the `SL-SG-FROST-W` wings under the garden slab are for. See the header
# note on `structural.frost_depth` above.
_FROST_FORMED = {"W-B-S1", "W-B-S2", "W-B-S3", "W-B-S4"}
# The two the veneer stands over — see `_SOUTH_TOE_TRIM`. S1 and S4 are deliberately NOT in
# it: they carry full 8" basement walls with soil against them, the beam does not reach
# them, and a 2" jog at each end of the run is a footing step, which is an ordinary thing
# to build and cheaper than moving two footings that had no reason to move.
_TOE_TRIMMED = {"W-B-S2", "W-B-S3"}

# ** THE FOUR GARDEN-FACE STRIPS ARE SHIFTED 2" OFF THE WALL AXIS, AND IT COSTS NOTHING. **
# `offset` moves the strip square to its wall without changing its width, so all 20" of
# bearing is still there — it is the same footing, sitting 2" further under the house.
#
# It buys the 2" that W-SG-BRKBM's XPS isolation board needs at -8"..-10" (the beam's
# concrete north face has to reach -10" or W-B-BRICK cannot have a 6" cavity). And it is
# free structurally, in fact better: these four carry a 7 1/4" curb and three storeys of
# framed wall standing at y = 0..+9 1/2", so a strip centred on y = 0 threw 10" of toe south
# under a load that was never over it. Moving 2" toward the load reduces the eccentricity it
# was already carrying.
#
# The sign is the resolver's own left-hand normal off `start_node -> end_node`, NOT a
# compass direction — `test_catlin_contract_m3` pins the resulting face at y = -8".
_SOUTH_TOE_TRIM = inch(2)
HOUSE_FOOTINGS = [
    Footing(uid=f"CF{i:03d}AAAAA", tag=f"FT-{t[2:]}", under=t,
            width=inch(20), depth=inch(8),
            offset=_SOUTH_TOE_TRIM if t in _TOE_TRIMMED else None,
            assembly="FOOTING_FPSF_20" if t in _FROST_FORMED else "CATLIN_FOOTING_20")
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

# --- the veneer plinth, RETIRED 2026-09-05 -----------------------------------------
# FT-B-BRICK (10"x5" on FT-B-S2/S3's toe) and FB-B-BRICK (its 2" bed) are GONE, not
# commented out: W-B-BRICK now bears on W-SG-BRKBM, a grade beam spanning between the
# court's two side walls (params/sunken_garden.py), and a wall that spans has no footing.
#
# Why they went. The plinth was cast ON the house footing's own toe, and the break between
# the two was `FootingBedding.cast_foam_in_aggregate` — a bool with no thickness, no
# material and no R-value, which emits no solid and bills nothing. The 2" `undercut` it dug
# billed as 0.1 cy of washed crushed stone, so what the BOM actually ordered under 129 SF of
# brick standing in open air was ~R-0.4 where R-10 was intended. The uids CFV301AAAA /
# CFV351AAAA are retired with them and must not be reused.
#
# `VENEER_PLINTH` and `VENEER_PLINTH_BEDDING` are still imported by name in
# plan/manifest.py's element list; both are now empty, which keeps that list honest about
# what this file used to publish rather than silently dropping a name.
VENEER_PLINTH: list[Footing] = []
VENEER_PLINTH_BEDDING: list[FootingBedding] = []

# --- garage ICF stem (basement storey; absolute elevations) -----------------------
#
# Every elevation in this block is measured from ``SITE_GRADE``, not from the project datum.
# The garage is driven into at grade and stays there; when grade moves, the whole garage
# foundation moves with it, while the house it stands beside does not move at all.
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
    # ** THESE TWO SPLITS ARE LEGACY AND ARE KEPT DELIBERATELY. ** They exist only because
    # the SE/NE brick-ledge wainscot returns once needed 4'-0" of widened, ledged stem under
    # them; both halves have been plain `_STEM` since 2026-09-02, and the wainscot itself is
    # gone since 2026-09-03, so the split is now purely cosmetic. Merging W-GF-S2/S3 and
    # W-GF-N/N2 back into one wall apiece would delete two real footings and churn every
    # golden that names them, for no geometric change at all. Not worth it — but do not
    # invent a new reason for the split either: there isn't one.
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
_GRADE_BEAM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN,
                   top_elevation=_GRADE_BEAM_TOP,
                   bottom_elevation=ft(_GRADE_FT - _FROST))

GARAGE_STEM_WALLS = [
    # South stem, split three ways at the service door — the east wall's pattern exactly.
    # W-GF-S1 keeps the original uid as the remnant of the single wall;
    # the grade beam and the far segment are new.
    FoundationWall(uid="CGF101AAAA", tag="W-GF-S1", start_node="N-GF-SW",
                   end_node="N-GF-S-DRW", **_STEM),
    FoundationWall(uid="CGF107AAAA", tag="W-GF-S-DR", start_node="N-GF-S-DRW",
                   end_node="N-GF-S-DRE", **_GRADE_BEAM),
    # W-GF-S2 keeps its uid on the remnant (SERVICE_DOOR side); W-GF-S3 is the corner
    # piece. See the legacy-split note on N-GF-S-BRICK above.
    FoundationWall(uid="CGF108AAAA", tag="W-GF-S2", start_node="N-GF-S-DRE",
                   end_node="N-GF-S-BRICK", **_STEM),
    FoundationWall(uid="CGF109AAAA", tag="W-GF-S3", start_node="N-GF-S-BRICK",
                   end_node="N-GF-SE", **_STEM),
    FoundationWall(uid="CGF102AAAA", tag="W-GF-E1", start_node="N-GF-SE",
                   end_node="N-GF-E-DRS", **_STEM),
    FoundationWall(uid="CGF105AAAA", tag="W-GF-E-DR", start_node="N-GF-E-DRS",
                   end_node="N-GF-E-DRN", **_GRADE_BEAM),
    FoundationWall(uid="CGF106AAAA", tag="W-GF-E2", start_node="N-GF-E-DRN",
                   end_node="N-GF-NE", **_STEM),
    # W-GF-N split the same way: W-GF-N keeps its uid on the remnant (west side);
    # W-GF-N2 is the corner piece.
    FoundationWall(uid="CGF103AAAA", tag="W-GF-N", start_node="N-GF-N-BRICK",
                   end_node="N-GF-NW", **_STEM),
    FoundationWall(uid="CGF110AAAA", tag="W-GF-N2", start_node="N-GF-NE",
                   end_node="N-GF-N-BRICK", **_STEM),
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
_GARAGE_FOOTING = dict(width=inch(20), depth=inch(8), center_on="wall",
                       assembly="CATLIN_FOOTING_20")

GARAGE_FOOTINGS = [
    Footing(uid="CGF201AAAA", tag="FT-GF-S1", under="W-GF-S1", **_GARAGE_FOOTING),
    Footing(uid="CGF207AAAA", tag="FT-GF-S-DR", under="W-GF-S-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF208AAAA", tag="FT-GF-S2", under="W-GF-S2", **_GARAGE_FOOTING),
    Footing(uid="CGF209AAAA", tag="FT-GF-S3", under="W-GF-S3", **_GARAGE_FOOTING),
    Footing(uid="CGF202AAAA", tag="FT-GF-E1", under="W-GF-E1", **_GARAGE_FOOTING),
    Footing(uid="CGF205AAAA", tag="FT-GF-E-DR", under="W-GF-E-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF206AAAA", tag="FT-GF-E2", under="W-GF-E2", **_GARAGE_FOOTING),
    Footing(uid="CGF203AAAA", tag="FT-GF-N", under="W-GF-N", **_GARAGE_FOOTING),
    Footing(uid="CGF210AAAA", tag="FT-GF-N2", under="W-GF-N2", **_GARAGE_FOOTING),
    Footing(uid="CGF204AAAA", tag="FT-GF-W", under="W-GF-W", **_GARAGE_FOOTING),
]

# Filed on "garage", where it belongs, with an absolute ``top_elevation``: the garage storey
# datum is the ICF stem top, but this slab pours at grade, and ``Slab.top_elevation`` is how
# a slab says so without being re-filed onto whichever storey happens to sit at its
# elevation. (It lived on "main" before this override existed, when "main" was at 0'-0".)
# Inset from the wall lines = the 11" stem section + the
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
# is a house rule — see houses/catlin/CLAUDE.md). The garage slab is at grade, -2'-10", so
# there are five risers between the two, inside the garage.
#
# Four of those risers are `ST-G-SERVICE`, a `Stair` (in plan/storeys/garage.py — a
# UI-movable element has to live in an editable file), using `Stair.floor_opening=None`
# with `base_elevation`/`top_elevation` to state the rise directly for a step-down within
# one storey. `structural.stair_riser_uniformity` and `code.R311_7_8_handrail` both grade it.
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
         thickness=inch(6), top_elevation=ft(0), assembly="CATLIN_GARAGE_STEP_6"),
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
# The hydrant is freestanding, not wall-mounted: nowhere on a wall clears the footings'
# 45° bearing-influence line at this bury depth. The clear zone is x >= 4'-10 1/2",
# y <= 59'-7 7/8", floor not wall — no wall
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
# salt-slush wet line was retired by owner decision. Replaced by spec, not
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
# Re-sized from 2'x4' deep (12.6 cu ft, bottom -9'-0", overlapped FT-GF-W by 4"
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
