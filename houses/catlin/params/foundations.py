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
    BarSpec,
    CrushedStoneSpec,
    DrainTile,
    Drywell,
    Footing,
    FootingBedding,
    FoundationWall,
    Length,
    Node,
    ReinforcementSpec,
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
    GARAGE_X_EAST,
    GARAGE_X_WEST,
    GARAGE_STEM_REVEAL,
    GARAGE_Y_NORTH,
    GARAGE_Y_SOUTH,
    OVERHEAD_DOOR_OFFSET,
    OVERHEAD_DOOR_WIDTH,
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

# The four south strips take FOOTING_EXPOSED_20 (the EXPOSED mix, F3), the rest FOOTING_20;
# all are plain strips on the bedding, with no foam under them (owner: creep). They are the
# strips the sunken garden runs along: the garden floor is at -9'-1 7/16" and they bottom
# out at -9'-9 7/16", **8" of frost cover** against MN Rules 1303.1600's 42" for Ramsey
# County — measured, as IRC R403.1.4.1 says to, from the lowest adjacent grade, which beside
# them is the garden floor and not the -2'-10" site plane six and a half feet overhead.
#
# ``structural.frost_depth`` derives a local grade per footing; the answer to what it finds
# here is IRC R403.3 — the horizontal wings under the garden slab
# (``params/sunken_garden.FROST_WINGS``, SL-SG-FROST-W/E/N) over the drained stone bedding.
# Deepening the strips is not an available alternative: FT-B-S2/S3's
# south toe is what carries SG_VENEER_BEAM_14's isolation board at -8"..-10" (that is what
# `_SOUTH_TOE_TRIM` below is for), so re-centring the strips and re-founding the brick wall
# are one change and not this one. It used to be the veneer PLINTH that leaned on that toe;
# the plinth is gone and the constraint is not.
# W-B-S1B joined on 2026-09-05 and left the same day with the sauna shrink. FT-B-S1 is one
# unsplit strip again, and it is back inside the court's 42" frost reach — which is what the
# `SL-SG-FROST-W` wings under the garden slab are for. See the header
# note on `structural.frost_depth` above.
_FROST_FORMED = {"W-B-S1", "W-B-S2", "W-B-S3", "W-B-S4"}
# ** THIS SET IS EMPTY, AND `_SOUTH_TOE_TRIM` IS SUPERSEDED (2026-09-05, second pass). **
# W-B-S2/S3 took a 2" trim, putting their south face on -8" — flush against
# SG_VENEER_BEAM_14's isolation board, which is what that trim was bought for. S1/S4 then
# took 6" for a different reason (below), and the "jog between the two trims is a footing
# step" this comment used to end on was exactly the mistake: a jog leaves TWO south faces on
# one line, and the closure board that has to run past both can only be flush with one.
#
# The 32" of FT-SG-W1's north end that faces FT-B-S2 (and the mirror at E1/S3) had **-1 13/16"
# of clearance** — a solid concrete lap, at the same elevation since the porch footings rose
# to the court plane, with the 2" board unable to enter it. All four south strips take the
# 6" trim now, one face at -4" across the whole south line, and the board runs its full 84".
#
# What the 2" bought is not lost. The beam's board still separates the veneer pour from the
# house pour; it now does it across 4" of bedding stone rather than flush against the strip,
# which is a longer path through a worse insulator IN SERIES with the same 2" of XPS — so
# the break is if anything better, and the beam bears nothing on that toe (it spans between
# the side walls, see notes/sunken_garden_veneer_beam.md). What the 2" WAS load-bearing for
# — the beam's concrete north face reaching -10" so W-B-BRICK gets its cavity — is a fact
# about the BEAM and does not move with this strip at all.
_TOE_TRIMMED: set[str] = set()
# ** S1 AND S4 WERE TRIMMED BY 6" ON 2026-09-05; S2 AND S3 JOINED THEM THE SAME DAY. **
# The rationale block above is kept because its reasoning about the BEAM is still right; its
# conclusion about these two is not, and this is why.
#
# The sunken garden's side walls run north to the house across a 2" XPS board since this
# date (params/sunken_garden._y_wall_end), ending on -6 3/16". FT-SG-W1/E1 are hosted
# (``Footing.under``) so they come with the wall — and an untrimmed 20" strip on the wall
# axis puts a house strip's south face on -10", which would leave the two footings lapping
# by nearly 4" of solid concrete. Nothing grades that: ``concrete_interference`` sees
# isolated pours only.
#
# **S2/S3 were left out of this on the first pass and should not have been.** The garden
# footing is 84" wide and only its outer 52" faces S1/S4; the inner 32" faces S2/S3, which
# sat at -8" and lapped it by 1 13/16". Which strip a given inch of the closure faces is an
# accident of where W-B-S1 stops (x = 8'-10"), and no thermal detail should turn on that.
#
# 6", not the beam's 2", because the board has to be a board at footing level as well as at
# stem level: -4" leaves the full 2" between the strips, so TB-SG-W1/E1 and the stem
# boards above them are one continuous plane instead of a nominal one buried in a pour.
#
# It is free structurally, and in the same direction the 2" trim already argued for: these
# two carry an 8" wall standing at y = 0..8", so a strip centred on y = 0 threw a 10" toe
# south under a load whose centre is at +4". At -4"..+16" the toes are 4" and 8" — the
# eccentricity halves and changes sign, and all 20" of bearing is still under the wall.
#
# Two things fall out of it that were wrong before and are not any more. FT-B-S1's south
# 2" used to lap SG_VENEER_BEAM_14's `xps-break` at -10"..-8" over the 10" the beam
# oversails it (x 8'-0"..8'-10"); at -4" it does not, and FT-B-S4 — which now reaches west
# to 27'-2" and would have picked up the identical lap — never gets it.
_GARDEN_END_TOE_TRIM = inch(6)
_GARDEN_END_TRIMMED = {"W-B-S1", "W-B-S2", "W-B-S3", "W-B-S4"}

# ** SUPERSEDED — KEPT FOR ITS REASONING, WHICH IS STILL WHY THE TRIM GOES NORTH AND NOT
# SOUTH. `_TOE_TRIMMED` IS EMPTY, SO THIS CONSTANT IS NOW UNUSED. **
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


def _toe_offset(tag: str) -> Length | None:
    """How far this strip's centre sits north of the line ``center_on`` picks.

    Only the garden-end four take one, and they are the four that stay on the node line —
    see the two blocks above, and ``_center_on`` below.
    """
    if tag in _GARDEN_END_TRIMMED:
        return _GARDEN_END_TOE_TRIM
    if tag in _TOE_TRIMMED:
        return _SOUTH_TOE_TRIM
    return None


# --- what the strip is centred on -------------------------------------------------
#
# ``center_on="wall"`` centres the strip on the midline of the wall's RESOLVED layer band
# rather than on the raw node line. Every concrete wall here aligns on
# ``face("concrete-ext")``, so its pour runs entirely INBOARD of that line and a strip
# centred on it threw all of its toe outboard. Measured on the resolved model before this
# change: an 8" segment (the N/W runs) had **10" of toe outside the pour and 2" inside**,
# and on the 12" segments (W-B-E1/E2) the wall's inboard face stood **2" PAST the footing
# altogether** — the wall was not all on its own footing.
#
# ** THE BAND IS NOT THE CONCRETE, AND THAT IS THE WHOLE CAVEAT. ** ``band_axis`` is handed
# EVERY layer's polygon, so the datum is the midline of the entire stack — the 4" of
# exterior XPS and its coating included, not the pour's midline. Measured: the new datum
# sits 1 29/32" inboard of the node line on the 8" walls and 3 29/32" on the 12" ones,
# which is 2 3/32" outboard of the concrete's own midline in both cases. So the toes go
# 10"/2" -> 8 3/32"/3 29/32" on an 8" wall and 10"/-2" -> 6 3/32"/1 29/32" on a 12" one:
# the eccentricity halves and every wall lands on its footing, but it is NOT symmetric and
# cannot be made so from here. Closing the last 2 3/32" means centring on the STRUCTURE
# layer, which is an engine change and not this one.
#
# TWO GROUPS STAY ON THE NODE LINE, and neither is an oversight.
#
# 1. **The four garden-end strips.** Their south face is pinned at -4" by the closure joint
#    against FT-SG-W1/E1 (see ``_GARDEN_END_TOE_TRIM`` above, and
#    ``test_catlin_contract_m3.test_the_veneer_beam_isolates_the_house_footing``). With the
#    face pinned and the width fixed at 20" the strip occupies -4"..+16" **whatever** datum
#    its offset is measured from, so re-centring them buys no geometry whatever — it only
#    re-expresses the same strip against a worse datum. Worse, because their band centres
#    do not agree with each other: measured, +1 29/32" on S1/S4 (BASEMENT_8),
#    +1 3/4" on S2 (SAUNA_LINER_ON_GARDEN_CURB, whose band includes the sauna's shiplap
#    liner) and -1/32" on S3 (GARDEN_CURB_6). One trim constant could no longer put
#    three different walls on one face, and S2's footing would move the next time an
#    interior sauna finish changed thickness.
# 2. **The four framed walls** — W-B-CS, W-B-STR, W-B-STR3, W-B-STR3B. A stud wall is
#    already centred on its own node line (each one's stud layer is within 1/4" of it), so
#    there is nothing to correct, and its band is dominated by finishes, so correcting
#    anyway makes it worse. W-B-CS is the case that shows it: its shiplap liner and
#    foil-polyiso would pull the strip **1 7/16" off the studs it carries**.
_FRAMED_WALLS = {"W-B-CS", "W-B-STR", "W-B-STR3", "W-B-STR3B"}


# ** W-B-CS3 (framed, y 10'-0"..13'-10") HAS NO FOOTING OF ITS OWN, AND NEEDS NONE. **
# D-B-GYM's header carries its run to two jamb packs (king + jack, resolved at y
# 124 7/16"..127 7/16" and 163 7/16"..166 7/16"), so the neighbouring strips run past each
# pack by T = 8": the 45° spread through the footing depth, and R403.1.1's maximum
# projection. They end at y 135 7/16" and 155 7/16"; the 20" under the opening stays slab.
# Both walls START at the gap (W-B-CS at y=10'-0", W-B-CS2 at 13'-10").
# `structural.bearing_wall_footing` FAILs if the door or its packs move off these.
_START_EXTENSION = {"W-B-CS": inch(15.4375), "W-B-CS2": inch(10.5625)}


def _center_on(tag: str) -> str:
    """``"wall"`` for the pours; ``"axis"`` where the node line is already the right line."""
    if tag in _GARDEN_END_TRIMMED or tag in _FRAMED_WALLS:
        return "axis"
    return "wall"


HOUSE_FOOTINGS = [
    Footing(uid=f"CF{i:03d}AAAAA", tag=f"FT-{t[2:]}", under=t,
            width=inch(20), depth=inch(8),
            center_on=_center_on(t), offset=_toe_offset(t),
            start_extension=_START_EXTENSION.get(t),
            assembly="FOOTING_EXPOSED_20" if t in _FROST_FORMED else "FOOTING_20")
    for i, t in _HOUSE_WALL_TAGS
]

# Bearing prep below every house footing: 7" undercut, geotextile, drain tile, compacted
# washed stone — a drained bearing surface that also breaks footing-to-wet-clay thermal
# contact. 4" perimeter foam matches BASEMENT_12's exterior XPS.
# One bedding per footing, sharing the footing's own permanent index for the same reason.
#
# ** THE TILE FALLS TO SM-B-RADON, NOT TO DAYLIGHT (corrected 2026-09-05). ** It said
# `discharge="daylight"` for as long as it existed, and that was never true on this lot:
# the bedding's underside is -124 7/16", which is 7'-6 1/2" BELOW the -2'-10" site grade.
# There is no point on this property the perimeter tile can gravity-daylight to. It passed
# silently because `discharge` is free text and `checks/mep/drainage.py` short-circuits the
# literal "daylight" as always-valid — it names nothing, so there is nothing to resolve.
#
# SM-B-RADON is the only collector below this invert: a sealed pit whose bottom is
# -136 15/16", 12 1/2" below the tile, on CKT-SUMP with a 1/3 hp submersible that lifts to
# daylight. Re-checked when this load was added: a 1/3 hp cast-iron submersible moves
# ~40 gpm at the ~12' of head this lift needs, against a 36'x36' footprint's perimeter
# infiltration, and it draws well under the 20 A CKT-SUMP already carries for it. The pump
# was always the thing doing this work; the model just said otherwise.
#
# The sunken garden's own FT-SG-* beds are NOT changed: their tile lets go into the court's
# own soakaway course below them, by gravity with no pump in the path.
HOUSE_FOOTING_BEDDING = [
    FootingBedding(uid=f"CFB{i:03d}AAAA", tag=f"FB-{t[2:]}", host_ref=f"FT-{t[2:]}",
                   undercut=inch(7), perimeter_insulation=inch(4),
                   drain_tile_spec=DrainTile(diameter=inch(4), sock=True,
                                             discharge="SM-B-RADON"))
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
# A car can't climb a 22" ICF stem, so the north stem GAPS at the overhead door: the flanking
# segments keep the full reveal and nothing is poured between them. W-G-N above is untouched
# (splitting it would break the ridge closure it carries) — the door reaches down via a
# negative sill_height in plan/storeys/garage.py, and its header carries the roof to the
# jamb packs on the two 4'-0" stem piers.
#
# ** NO GRADE BEAM SINCE 2026-09-23 (owner). ** W-GF-N-DR (uid CGF105) and FT-GF-N-DR
# (CGF205) are retired: nothing bears on the opening, the slab runs out to the door line
# (SL-G-FLOOR's tab below), and the K8 joint — 1" XPS + PU sealant — separates it from the
# driveway. The garage is unconditioned, so frost reaches under the slab anyway; the
# threshold floats with it rather than sitting on a frost wall. The gap nodes are open ends.
# The service door's stem gap is CLOSED since 2026-09-11 (see W-GF-S-DR below); these two
# are the arithmetic that produced its fossil split stations, 2'-3" and 5'-9" off N-GF-SW —
# the 2026-09-07..11 door offset less/plus the 3" margin the hydrant crossing asked for.
_FOSSIL_SERVICE_OFFSET = ft(2, 6)
_SERVICE_GAP_MARGIN = ft(0, 3)

GARAGE_STEM_NODES = [
    Node(uid="CGF001AAAA", tag="N-GF-SW", position=pt(GARAGE_X_WEST, GARAGE_Y_SOUTH)),
    Node(uid="CGF002AAAA", tag="N-GF-SE", position=pt(GARAGE_X_EAST, GARAGE_Y_SOUTH)),
    Node(uid="CGF003AAAA", tag="N-GF-NE", position=pt(GARAGE_X_EAST, GARAGE_Y_NORTH)),
    Node(uid="CGF004AAAA", tag="N-GF-NW", position=pt(GARAGE_X_WEST, GARAGE_Y_NORTH)),
    # Overhead-door gap in the NORTH stem. D-G-OVERHEAD hangs off N-G-NE and W-G-N runs
    # east->west, so OVERHEAD_DOOR_OFFSET is measured back from x=30': the jambs land at
    # x=26' and x=10'. Flush with the opening, no margin — the ±3" `_SERVICE_GAP_MARGIN`
    # below is the service door's rule, forced by a buried water line, and nothing crosses
    # here. CGF005 is the uid the retired east gap's south node carried. `open_end`: the
    # stem stops here and nothing spans the door (see the grade-beam note above).
    Node(uid="CGF005AAAA", tag="N-GF-N-DRW",
         position=pt(GARAGE_X_EAST - OVERHEAD_DOOR_OFFSET - OVERHEAD_DOOR_WIDTH,
                     GARAGE_Y_NORTH), open_end=True),
    # ** THE SOUTH STEM'S DOOR SPLIT IS A FOSSIL TOO, SINCE 2026-09-11, AND IT IS PINNED. **
    # From 2026-08-01 this was the service door's stem gap, 3" wider than the opening each
    # side because the hydrant line (PR-G-HYDRANT-CW) crossed buried at the door's west jamb
    # and a flush gap would have put the crossing on a footing joint. The door moved into the
    # SW corner (SERVICE_DOOR_OFFSET 2'-6" -> 0'-7") and the gap did NOT follow: its sill has
    # been +1'-0" over the stem top since the north-entry landing, so nothing ever needed the
    # stem out of the way, and W-GF-S-DR below is plain `_STEM` now. The two nodes stay where
    # the gap left them (x 8'-3" and 11'-9") on the S-BRICK precedent — moving them would
    # re-cut FT-GF-S-DR out from under `SP-GF-S-HYD` at x=11'-0" (plan/mep_sleeves.py), and
    # the crossing is what this footing's identity exists for.
    Node(uid="CGF007AAAA", tag="N-GF-S-DRW",
         position=pt(GARAGE_X_WEST + _FOSSIL_SERVICE_OFFSET - _SERVICE_GAP_MARGIN,
                     GARAGE_Y_SOUTH)),
    Node(uid="CGF008AAAA", tag="N-GF-S-DRE",
         position=pt(GARAGE_X_WEST + _FOSSIL_SERVICE_OFFSET + SERVICE_DOOR_WIDTH
                     + _SERVICE_GAP_MARGIN, GARAGE_Y_SOUTH)),
    # ** THE SOUTH SPLIT IS A LEGACY FOSSIL AND IS KEPT DELIBERATELY. ** It exists only
    # because the SE brick-ledge wainscot return once needed 4'-0" of widened, ledged stem
    # under it; both halves have been plain `_STEM` since 2026-09-02, and the wainscot
    # itself is gone since 2026-09-03, so the split is now purely cosmetic. Merging
    # W-GF-S2/S3 back into one wall would delete a real footing and churn every golden that
    # names it, for no geometric change at all. Not worth it — but do not invent a new
    # reason for the split either: there isn't one.
    Node(uid="CGF009AAAA", tag="N-GF-S-BRICK",
         position=pt(GARAGE_X_WEST + ft(20), GARAGE_Y_SOUTH)),
    # ** ITS NORTH TWIN IS NO LONGER A FOSSIL. ** (20', GARAGE_Y_NORTH) is exactly the new
    # overhead door's east jamb, so the node the deleted wainscot left behind is retagged in
    # place — same uid, same coordinate, a reason at last. Do not merge W-GF-N2 away.
    Node(uid="CGF010AAAA", tag="N-GF-N-DRE",
         position=pt(GARAGE_X_EAST - OVERHEAD_DOOR_OFFSET, GARAGE_Y_NORTH), open_end=True),
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

# ** THE GARAGE STEM RETAINS NOTHING, AND SAYING SO IS THE MODEL CATCHING UP (2026-09-15). **
# `_unbalanced_fill_ft`'s derived answer is grade down to the bottom of the wall, which its
# own docstring calls a conservative proxy and says depends on two things the model does not
# carry: the finished grade at each face, and whether a slab braces the inside. Both are
# knowable here and both say zero.
#
# Measured: grade is -2'-10", the stem runs -6'-4" to -1'-0", and SL-G-FLOOR's TOP is
# -2'-10" — exactly grade. So the fill stands at the same level on both faces and there is
# no differential to retain; the proxy's 3'-6" is the depth from grade to the stem bottom,
# counted as though the garage side were open to that depth. It is not: it is filled to
# grade, with the top few inches foam and slab rather than soil (which is the owner's own
# description of it, 2026-09-14).
#
# Worth authoring whatever happens to the footings. It is the difference between a wall the
# register reports as retaining 3'-6" and one that retains nothing, and it is the
# prerequisite for any claim under 2024 IRC R403.5, which reaches NONRETAINING
# cast-in-place foundations only.
_NO_RETAINED_FILL = ft(0)

# The ICF core's steel: #4 @ 16" each way, one layer at the core — the form's own web module,
# three times IRC R404.1.2(8) footnote d's #4 @ 48" for a 6" stay-in-place wall. No dowels:
# the stems stand on crushed stone (decision #75 D10; notes/basement_wall_horizontal_steel.md §3).
# Cover 1 1/2", not the mix's 3": the core is FORMED against the EPS, never cast against earth,
# so ACI 318-19 Table 20.5.1.3.1's formed-face row (#5 and smaller, ground) governs — and 3"
# each side of a centred mat does not fit in 6".
_ICF_STEM_STEEL = ReinforcementSpec(
    bars=(BarSpec(role="vertical", bar=4, spacing=inch(16)),
          BarSpec(role="horizontal", bar=4, spacing=inch(16))),
    cover=inch(1.5),
    source="IRC Table R404.1.2(8) footnote d floor (#4 @ 48\"), authored at the ICF's 16\" module",
)

# `interior_room`: the stem is an open U since the grade beam went, and an open chain has no
# winding to recover (resolve/orientation.py falls back to +1, which builds every layer
# inside out). Naming the garage puts layer 0 — the gypsum band — on its side of each wall.
_STEM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN, top_elevation=_STEM_TOP,
             bottom_elevation=ft(_GRADE_FT - _FROST),
             unbalanced_fill=_NO_RETAINED_FILL, reinforcement=_ICF_STEM_STEEL,
             interior_room="RM-GARAGE")

GARAGE_STEM_WALLS = [
    # South stem, split four ways: two fossil splits (N-GF-S-DRW/-DRE, N-GF-S-BRICK) and no
    # gap. W-GF-S1 keeps the original uid as the remnant of the single wall.
    FoundationWall(uid="CGF101AAAA", tag="W-GF-S1", start_node="N-GF-SW",
                   end_node="N-GF-S-DRW", **_STEM),
    # ** `_STEM`, NOT `_GRADE_BEAM`, SINCE 2026-09-11. ** This was the service door's grade
    # beam, dropped to grade so the door could open off the slab — a premise that died when
    # the door's sill rose to the north-entry landing (+1'-0" over the stem top). With the
    # door in the SW corner (RO 6'-7"..9'-7") the landing carriers BM-BW-FC/-FE pass over
    # this stem's top at -1'-0" with 3 3/4" to their soffit. The tag, uid and footing
    # FT-GF-S-DR are kept because the water-service sleeve names that footing.
    FoundationWall(uid="CGF107AAAA", tag="W-GF-S-DR", start_node="N-GF-S-DRW",
                   end_node="N-GF-S-DRE", **_STEM),
    # W-GF-S2 keeps its uid on the remnant (SERVICE_DOOR side); W-GF-S3 is the corner
    # piece. See the legacy-split note on N-GF-S-BRICK above.
    FoundationWall(uid="CGF108AAAA", tag="W-GF-S2", start_node="N-GF-S-DRE",
                   end_node="N-GF-S-BRICK", **_STEM),
    FoundationWall(uid="CGF109AAAA", tag="W-GF-S3", start_node="N-GF-S-BRICK",
                   end_node="N-GF-SE", **_STEM),
    # The east stem is one unbroken run again now that the door is off it; W-GF-E1's uid
    # carries the merged wall (W-GF-E2/CGF106 retired).
    FoundationWall(uid="CGF102AAAA", tag="W-GF-E", start_node="N-GF-SE",
                   end_node="N-GF-NE", **_STEM),
    # North stem: two 4'-0" piers either side of the overhead door, nothing between them.
    # W-GF-N2 keeps CGF110 (its east end is unmoved) and W-GF-N keeps CGF103 on the west
    # remnant. The grade beam W-GF-N-DR (CGF105) is retired 2026-09-23 — never reuse it.
    FoundationWall(uid="CGF110AAAA", tag="W-GF-N2", start_node="N-GF-NE",
                   end_node="N-GF-N-DRE", **_STEM),
    FoundationWall(uid="CGF103AAAA", tag="W-GF-N", start_node="N-GF-N-DRW",
                   end_node="N-GF-NW", **_STEM),
    FoundationWall(uid="CGF104AAAA", tag="W-GF-W", start_node="N-GF-NW",
                   end_node="N-GF-SW", **_STEM),
]

# Not a comprehension any more: the north wall splits into three, and a fresh uid per item
# would reassign CGF203/204AAAA (footings that didn't conceptually change) to the new door
# pieces. Original uids are kept and re-used across the 2026-09-07 rotation — CGF206
# (FT-GF-E2) is the one that retired with the east gap.
#
# `center_on="wall"`: the stem runs 0"..11" inboard of the raw node line, so a 20" strip
# centred on the node line (the default) would leave 10" of toe under nothing. Centred on
# the resolved section instead, the toe is a symmetric 4 1/2" each side.
# ** STONE, NOT CONCRETE, SINCE 2026-09-15 (owner). ** The section is unchanged — 20" x 8",
# centred on the wall, bearing at -7'-0" — and so are the nine tags, uids and `under` refs.
# What changed is what it is made of. The scoreboard below is the argument; Table R403.4 is
# the sizing, and this section clears it with room: a one-storey conventional light-frame
# load (1,100 plf) wants D = 4" at every soil bearing value in the table and W = 13"/15"/17"
# for an 8"/10"/12" wall. 8" deep and 20" wide are both above the widest of those, which
# matters because Table R403.4's wall-width columns START at 8" and this stem is 6" — there
# is no column to read, so the widest published W is taken rather than an interpolation
# invented below the table's own range.
_GARAGE_FOOTING = dict(width=inch(20), depth=inch(8), center_on="wall",
                       assembly="FOOTING_STONE_20", material="crushed_stone",
                       stone=CrushedStoneSpec())

# ** ASKED 2026-09-11, REFUSED TWICE, AND DONE ON 2026-09-15. ALL FIVE REASONS ARE GONE. **
#
# The proposal was to build these nine on consolidated crushed stone instead of concrete,
# citing 2024 IRC R403.5. It was refused twice, and the second refusal rested on a single
# claim: that the section was really R403.4.1 under R403.4, *Footings for precast concrete
# foundations*, and so had nothing to say about a wall poured in place. **That claim was
# wrong, and both sections exist.** They do different jobs:
#
#   * **R403.5 "Crushed Stone Footings for Cast-in-Place Concrete Foundations"** is the
#     SCOPE: stone footings per R403.4.1 are permitted for NONRETAINING cast-in-place
#     foundations complying with R404.1.3, in Seismic Design Categories A, B and C.
#   * **R403.4.1** is the specification R403.5 points AT — angular, ASTM C33, 1/2" max and
#     1/16" min, free of organic/clayey/silty soils, vibratory-plate consolidated in lifts
#     not greater than 8". It sits under the precast article because that is where it was
#     first needed, not because that is the only place it is used.
#
# And the sizing is **Table R403.4**, not Table R403.5 — an easy and consequential swap,
# because Table R403.5 is a FOUNDATION WALL table (stem width, height, horizontal bar, braced
# wall line spacing) and has no footing dimension in it at all.
#
# The scoreboard, which is why this took three passes:
#
#   1. GONE, and it was the last one standing. "There is nothing to dowel into" rested on the
#      section being precast-scoped. R403.5 is written for a cast-in-place wall, which is
#      what GARAGE_ICF_6 is. What the original reason was RIGHT about is that the dowels
#      need something: under R403.5 they get the ICF's own base and the stone carries
#      bearing, which is the trade the section makes and the reason it is limited to walls
#      that retain nothing.
#   2. GONE, and by this file. `unbalanced_fill=ft(0)` is authored on `_STEM` and
#      the since-retired `_GRADE_BEAM` (see `_NO_RETAINED_FILL` above): grade is -2'-10", the stem runs
#      -6'-4"..-1'-0", and SL-G-FLOOR's top is -2'-10" — exactly grade — so these stems
#      retain nothing and the 3'-6" this reason rested on was the derived proxy, not the
#      building. That authored zero is now also what makes the R403.5 claim TESTABLE:
#      `code.R403_5_crushed_stone_footings` refuses the section on any wall that retains, and
#      reports UNKNOWN rather than passing on a wall that never states it.
#   3. GONE by not deleting anything. This is a RETYPE: same nine elements, same tags, same
#      uids, same `under`, same `bottom_elevation`, same -7'-0" bearing plane. SP-GF-S-HYD
#      still names them and every argument in `mep_supply.py`, `electrical.py` and
#      `north_entry_frame.py` keeps its referent.
#   4. GONE. `FootingBedding` is not what was used — `Footing.material` is a discriminator on
#      the footing itself, so a stone footing is still a Footing and stays in all six
#      `isinstance(el, Footing)` consumers instead of vanishing from them.
#   5. GONE. `FOOTING_STONE_20` is its own assembly; `FOOTING_20` is untouched under every
#      FT-B-* strip in the house.
#
# ** THE SIZE CLEARS TABLE R403.4 WITH ROOM, AND THE 6" STEM IS THE ONE SUBTLETY. ** The row
# is conventional light-frame, one storey, 1,100 plf: minimum depth D = 4" at EVERY soil
# bearing value the table publishes, and minimum width W = 13"/15"/17" for an 8"/10"/12"
# wall. This section is 20" x 8". But the table's wall-width columns START at 8" and the ICF
# core is 6", so there is no column to read — footnote a permits interpolating DEPTH between
# wall widths and says nothing about extrapolating WIDTH below the table. The check therefore
# holds a sub-8" wall to the WIDEST published W, 17", rather than inventing a narrower one.
# 20" passes that, so the question never becomes load-bearing here.
#
# ** MINNESOTA IS ON THE 2018 IRC IN THIS ENGINE, AND THAT IS HANDLED RATHER THAN IGNORED. **
# `MN_2020`'s `irc_base` is "2018 IRC + MN amendments", which contains no R403.5 at all. MN
# adopts the 2024 edition in 2027 and this house is built after it, so the check RUNS and the
# profile carries a `permit_exclusions` entry saying in as many words that it is ahead of the
# edition on the checklist. The alternative — retype nine footings and let no rule anywhere
# ask whether it was allowed — is the silent-at-0-FAIL failure this repo exists to catch.
#
# ** WHAT IS STILL TRUE AND IS NOT A CODE QUESTION. ** R403.1.4's 12" minimum depth and
# R403.1.4.1's frost depth still govern and are unaffected: these bases sit at -7'-0" against
# a -2'-10" grade, 50" down against `frost_depth_in=42`, and `structural.frost_depth` passes
# on depth alone. The figures also require the footing top at least 4" below undisturbed
# ground, which -6'-4" clears by more than three feet.
#
# ** THE COST MOVED, AND NOT ONLY DOWN. ** 3.95 cy of concrete left the bill and 3.95 cy of
# stone arrived: `prices.toml` carries both halves with their MnDOT 2025 sourcing. The stone
# is cheaper per yard but it is a FILTER aggregate rather than a bedding stone (1/2" top size
# against #57's 1"), it is under half a tandem and must ride with the beddings' 71.2 cy #57
# order to avoid a per-order delivery charge larger than the stone, and R403.5's
# vibratory-plate consolidation is a trade operation with its own machine and its own
# inspection hold — it is NOT the excavator's spread-and-level, and it carries its own
# labour line for that reason.
#
# The original five, kept verbatim below because they are what the answer is made of:

#
# 1. **There is nothing to dowel into.** `GARAGE_ICF_6` is a cast-in-place ICF wall with
#    vertical bars at 16" o.c. (`_ICF_STEM_STEEL`), and those bars lap dowels cast into the
#    footing. The IRC does list "crushed stone footings" among the supports a foundation
#    wall may bear on, but the design for one lives in R403.4, *Footings for precast
#    concrete foundations* — it is written for a precast panel set on compacted stone, not
#    for a wall poured in place with reinforcement running out of its base. (Neither section
#    is encoded in this engine; `checks/code/mn_residential` carries R403.1.4 and R403.1.6
#    only, so nothing here would have refused the change.)
# 2. **These stems retain fill.** `structural.foundation_unbalanced_fill` reports 3'-6" of
#    unbalanced fill (GM, 45 psf/ft) on all nine. The footing is the base restraint for that
#    push as well as the bearing: the 20" strip under an 11" section (6" core + 2 x 2 1/2"
#    EPS) is a symmetric 4 1/2" toe each side, and the dowels are what stop the base sliding.
#    Stone gives friction and no keyway.
# 3. **The bearing plane is a datum three other files were designed against.**
#    `plan/mep_supply.py` routes PR-G-HYDRANT-CW under FT-GF-S-DR's -7'-0" plane and keeps
#    an east leg out of FT-GF-S1/-S-DR's influence cone; `mep.footing_clearance` PASSES only
#    because SP-GF-S-HYD names twelve footings, these nine among them; `plan/electrical.py`
#    holds a run two feet clear of FT-GF-S2 at -6'-8"; and `params/north_entry_frame.py`
#    sets its piers to stay outside FT-GF-S1/-S3's 45 degree line from a -6'-4" underside.
#    Delete the footings and every one of those arguments loses its referent and the sleeve
#    becomes a sleeve through nothing.
# 4. **The cited precedent does not transfer.** `raised_garden.py`'s
#    `FootingBedding(aggregate="MnDOT Class 5 aggregate base")` hosts on a FoundationWall
#    because that wall is a DRY-STACKED SRW — a wall type that by design has no concrete
#    under it. An ICF stem is the other case the element's own docstring separates.
# 5. **`FOOTING_20` is shared with the house**, so this could not be a retype in any event:
#    every FT-B-* strip is on it too.
#
# Frost is not the obstacle and should not be offered as one. These bases sit at -7'-0"
# against a -2'-10" grade, 50" down against `frost_depth_in=42`, and `structural.frost_depth`
# passes on depth alone. A well-drained NFS section CAN be counted toward frost depth
# (`FootingBedding.non_frost_susceptible` + `drain_tile`, ASCE 32 via IRC R403.1.4.1) — but
# that is a route to a SHALLOWER footing, not to no footing, and nothing here wants to come up.
#
# ** WHAT THE REQUEST IS ACTUALLY POINTING AT, AND IT IS REAL. ** These eight are the only
# footings in this house with NO `FootingBedding` under them. `HOUSE_FOOTING_BEDDING` above
# beds every FT-B-* on 7" of stone; `sunken_garden.py` beds every FT-SG-*; `raised_garden.py`
# beds all five W-RG-*. `FOOTING_20`'s own `source` string even says the strip is "poured
# against the bedding prep" — and for these eight there is none. Left open rather than
# authored here for one honest reason: a bed's drain tile needs a collector below it, and the
# garage has none. The house's falls to SM-B-RADON and the court's to its soakaway course; there is
# no sump in the garage and no gravity outlet below -7'-0" on this lot. An undrained bed is a
# defensible thing to specify (the raised garden's are `drain_tile=False`) but it is an
# excavation and a stone order nobody has costed, and it is a decision, not a correction.
#
# ** ⚠ THAT PREMISE IS FALSE, AND IT HAS BEEN SINCE THE COURT WAS DUG (noted 2026-09-14). **
# "No gravity outlet below -7'-0" on this lot" is the load-bearing sentence above, and
# the court's soakaway stone runs down to **-14'-7 7/16"** — over seven feet below the level
# this paragraph says nothing gets under. The same claim appears above for the house tile;
# `drainage.network_fallback` and the sump's own overflow to FB-SG-ARCH now say otherwise, and
# the gravity path from the house side to the court's soakaway needs no pump at all.
#
# ** THE DECISION IS STILL OPEN AND THIS IS NOT AN INSTRUCTION TO AUTHOR IT. ** Whether the
# garage wants beds is a cost and a scope question — eight footings, an excavation and a
# stone order — and it is deliberately out of scope here. What is recorded is that the
# reason currently given for NOT doing it is not a fact about the lot. Revisit it on the
# merits: the run from the garage to the court is long, crosses the drive and would want its
# own fall, and none of that has been looked at. The false premise is what had to go.

GARAGE_FOOTINGS = [
    Footing(uid="CGF201AAAA", tag="FT-GF-S1", under="W-GF-S1", **_GARAGE_FOOTING),
    Footing(uid="CGF207AAAA", tag="FT-GF-S-DR", under="W-GF-S-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF208AAAA", tag="FT-GF-S2", under="W-GF-S2", **_GARAGE_FOOTING),
    Footing(uid="CGF209AAAA", tag="FT-GF-S3", under="W-GF-S3", **_GARAGE_FOOTING),
    Footing(uid="CGF202AAAA", tag="FT-GF-E", under="W-GF-E", **_GARAGE_FOOTING),
    Footing(uid="CGF210AAAA", tag="FT-GF-N2", under="W-GF-N2", **_GARAGE_FOOTING),
    Footing(uid="CGF203AAAA", tag="FT-GF-N", under="W-GF-N", **_GARAGE_FOOTING),
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
_slab_x_w = GARAGE_X_WEST + _SLAB_INSET
_slab_x_e = GARAGE_X_EAST - _SLAB_INSET
# The overhead door's tab: with no grade beam under the door the slab runs out between the
# two stem piers to the node line (the stems' outer EPS face), the usual 1/2" off each pier
# end. The driveway's K8 joint starts there (params/driveway.py).
_door_x_e = GARAGE_X_EAST - OVERHEAD_DOOR_OFFSET - _SLAB_GAP
_door_x_w = GARAGE_X_EAST - OVERHEAD_DOOR_OFFSET - OVERHEAD_DOOR_WIDTH + _SLAB_GAP
# ** THE HOUSE SLAB-EDGE BREAK, STATED (free body §11j-§11k, basis 8). ** SL-B-FLOOR's south and
# north edges carry the court's thermal-break thrust to the far footing line, so the board's
# grade is a graded input: FOAMULAR 1000 (100 psi) holds the sheet's 1/3 sustained-load rule
# at 0.885; FOAMULAR 400 read 2.21. 1000 is not made in 1" — 1.5" is its thinnest (the
# bearing rows read depth x length, never thickness). SL-B-FLOOR spells these kwargs out
# (basement.py is editable and cannot import params/); `test_catlin_contract_m3` pins the pair.
SLAB_EDGE_BREAK = dict(
    material_ref="xps", thickness=inch(1.5), psi=100.0, modulus_psi=3700.0,
    sustained_load_fraction=0.3333,  # the sheet's 1/3; a literal so basement.py can match it
    source="Owens Corning FOAMULAR NGX 1000, ASTM C578 Type V: 100 psi min (ASTM D1621), "
           "minimum compressive modulus 3,700 psi published (PDS 07 21 13.13.OCC); dead load "
           "<= 1/3 of rating; 1.5\" min thickness (Pub. 58307-Q, 06-2025)")
# The garage's edge carries no court thrust: it stays the 1" 40 psi board its underslab
# layer already orders (a wheel load).
GARAGE_SLAB_EDGE_BREAK = dict(
    material_ref="xps", thickness=inch(1), psi=40.0, modulus_psi=1800.0,
    sustained_load_fraction=0.3333,
    source="Owens Corning FOAMULAR 400, ASTM C578 Type VI: 40 psi min (ASTM D1621), minimum "
           "compressive modulus 1,800 psi published; sustained load <= 1/3 of rating "
           "(PDS 07 21 13.13.OCC)")

GARAGE_SLAB = Slab(
    kind="pour",
    uid="CGS501AAAA", tag="SL-G-FLOOR",
    outline=(pt(_slab_x_w, _slab_y_s), pt(_slab_x_e, _slab_y_s),
             pt(_slab_x_e, _slab_y_n), pt(_door_x_e, _slab_y_n),
             pt(_door_x_e, GARAGE_Y_NORTH), pt(_door_x_w, GARAGE_Y_NORTH),
             pt(_door_x_w, _slab_y_n), pt(_slab_x_w, _slab_y_n)),
    thickness=inch(3.5), assembly="GARAGE_SLAB_ON_GRADE", top_elevation=SITE_GRADE,
    perimeter_thermal_break=SlabThermalBreak(**GARAGE_SLAB_EDGE_BREAK),
)

# --- garage service-door landing ---------------------------------------------------
#
# The shared composite landing is authored with its actual bridge frame in breezeway.py.
# Retired unsupported concrete landing CGS510AAAA / SL-G-STEP-0. The composite
# FS-BW-GARAGE continuation now bears on the foundation-to-foundation bridge.
GARAGE_STEPS = []

# --- garage hydrant: supply sleeve, gravel pit -------------------------------------
#
# FX-G-HYDRANT stands free near the SW corner, 1'-0" east of ST-G-SERVICE's flight. The
# sleeve and drywell below it are not UI-movable, so they live here rather than in editable
# plan/fixtures.py.
#
# ``_FROST`` above is the *footing* frost depth (42"); the hydrant's 72" bury is a separate
# number — its own shutoff-valve depth, consistent with but not the same as frost.
#
# Freestanding, not wall-mounted: at this bury the shutoff sits 22" and the weep stone 34"
# below the garage footings' -7'-0" bearing plane, so the 45° influence line keeps the stone
# 34" off every footing edge. Against FT-GF-W that is x >= 10'-10 1/2"; against the south
# strip (north face 44'-6 1/4") it is y >= 48'-1". No wall position clears both.
#
# ** (11'-0", 48'-6") SINCE 2026-09-16. ** It stood at y=62'-0" in the NW corner and the
# service jogged east in the yard to reach it. Moved south beside the service stair, on the
# line the house entry now uses (SP-B-N3-HYD at x=11'-0"), the buried run is one straight
# 13'-0" leg crossing FT-GF-S-DR perpendicular inside SP-GF-S-HYD. The stone clears the
# south strip by 38 3/4" and FT-GF-W by 35 1/2".
#
# Consequence: a post standing 4'-1" off the west stem face beside the stair foot. Don't
# move it onto a wall.
HYDRANT_X_FT = 11.0         # the FT-GF-W-clear station, and the service line
HYDRANT_Y_FT = 48.5         # beside ST-G-SERVICE's foot; FT-GF-S binds
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
# stone's edge stands 35 1/2" off FT-GF-W (no slack) and 38 3/4" off the south strip.
GARAGE_HYDRANT_DRYWELL = Drywell(
    uid="CGP603AAAA", tag="DRW-G-HYDRANT",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    diameter=inch(18), depth=inch(18),
    top_elevation=ft(_GRADE_FT - (HYDRANT_BURY_FT - 0.5)),
    geotextile=True, inlet_refs=("FX-G-HYDRANT",),
    # ** ITS FALLBACK IS THE GROUND ABOVE IT, AND THAT IS THE HONEST ANSWER (2026-09-14). **
    # `drainage.network_fallback` asks every soakaway where the water goes when the soil
    # stops taking it, because a below-grade court with one outfall has no answer. This one
    # does, and it is allowed to be unglamorous: 2.6 cu ft of stone taking ONE frost-free
    # hydrant's weep — a few quarts of clean potable water per use, and nothing else. When
    # it is full the next weep stands in the hydrant's barrel and then surcharges up its own
    # 18" shaft to the yard.
    #
    # Saying "daylight" here is therefore a statement about this soakaway's DUTY, not a
    # discovery that there is daylight at -6'-0" on this lot (there is not, and
    # `foundations.py`'s garage reasoning turns on exactly that). It would be the wrong
    # answer for anything carrying foundation or roof water; it is the right one for a weep
    # hole, and the distinction is the reason it is written out rather than left blank.
    overflow_ref="daylight",
    overflow_invert=ft(_GRADE_FT),
)

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *HOUSE_FOOTING_BEDDING, *VENEER_PLINTH,
                     *VENEER_PLINTH_BEDDING, *GARAGE_STEM_NODES,
                     *GARAGE_STEM_WALLS, *GARAGE_FOOTINGS, GARAGE_HYDRANT_DRYWELL]
GARAGE_ELEMENTS = [GARAGE_SLAB, *GARAGE_STEPS, GARAGE_HYDRANT_SLEEVE]
