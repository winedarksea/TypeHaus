"""The basement's ceiling — the main floor's structure, all wood.

Five joist fields on one flat bearing seat. West of x=18' the TJI 230 bays (``FS-M-WEST``,
``FS-M-MECH``, ``FS-M-STAIR``); east of it ``FS-M-EAST`` (TJI 230, y 0'-13') and ``FS-M-NE``
(11 7/8" open-web floor trusses at 16" o.c., y 13'-36', decision #112). Every member is
11 7/8", so the seat, the subfloor and the basement ceiling are one plane each, house-wide.
``FS-M-NE`` replaced ``SL-M-DECK``, the BuildDeck EPS/concrete band; its basis is in
``DESIGN-LOG.md`` ("Main deck goes wood"), and ``DECK_EPS_INT`` stays a named revert.

::

      +3/4" + plank   Cotton Oak LVP on the subfloor, whole main floor
      +3/4"           3/4" plywood subfloor   <- every main-floor wall plate stands here
      0'-0"           STOREY DATUM (top of joists)
                      11 7/8" TJI 230 @ 16" / open-web truss @ 16"
     -11 7/8"         joist soffit (5/8" gypsum hangs here, basement ceiling)
                      1 1/2" PT mudsill (concrete walls) or 2x6 double top plate (x=18')
     -13 3/8"
                      1/16" EPDM gasket, compressed (on concrete)
     -13 7/16"        BEARING SEAT

**The datum is the top of joists, not the walking surface.** The subfloor rides above it and
the walls stand on the subfloor (``resolve/plate_seat.py``, decision #110).

**Why a params module and not ``plan/storeys/main.py``.** The depth and the seat want to be
one constant each: ``BEARING_SEAT`` is read by the basement walls (as literals, since
editable files cannot import) and by the wall-base detail. FloorSystems are not UI-movable.

**Why five FloorSystems and not one.** ``FloorSystem.outline`` scopes only the
*perpendicular* extent; span boundaries come from the bearing refs' axis midpoints
(``resolve/floors.py``), so each field names only the lines it actually bears on.
**Bearing refs are a bearing statement**: duplicates on one grid line are a degenerate span
and dropped. ``integrity.floor_bearing_grid`` catches the trap that the x=18' framed walls
carry ``alignment=face("stud-ext", offset=inch(-2.75))``, a hand-written HALF of the stud;
an offset that stopped matching would slide their axis off x=18'.
"""

from typehaus.geometry import rect
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus import (
    DeckLayer,
    FloorSystem,
    JoistReinforcement,
    JoistSpec,
    Layer,
    LayerFunction,
    Strongback,
    ft,
    inch,
    pt,
)

from params.flooring import LVP_THICKNESS_IN
from params.second_deck import _DEPTH as _JOIST_DEPTH
from params.second_deck import (_JOIST, _JOIST_BEARING, _SUBFLOOR, _TRUSS, _TRUSS_BEARING,
                                _WEB_OPENING, _WEB_PANEL_OFFSET, _WEB_PANEL_PITCH,
                                TJI_230_FLOOR_SPAN, TRIFORCE_OJ418S_FLOOR_SPAN)

_JOIST_OC = inch(16)

# The basement's ceiling — 5/8" gypsum board, room side (and only layer).
_CEILING_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),)

# The storey datum is the TOP OF JOISTS; the finished floor of every bay is _SUBFLOOR above
# it. ``plan/manifest.py`` takes the main storey's elevation from MAIN_DATUM.
MAIN_DATUM = ft(0)
MAIN_FINISHED_FLOOR = inch(MAIN_DATUM.inches + _SUBFLOOR.inches)

# The plank's total installed depth, from the one selection the house material reads, so stair
# arrivals and the rendered walking plane stay coordinated.
_LVP = inch(LVP_THICKNESS_IN)
MAIN_FINISHED_FLOOR_LVP = inch(MAIN_FINISHED_FLOOR.inches + _LVP.inches)

# --- the bearing seat ---------------------------------------------------------------
#
# One flat plane all the way round the basement. Every basement ``FoundationWall`` and the
# x=18' framed walls top out here, and the flat-laid PT plate the joists bear on over
# concrete is returned here (``resolve/construction_sills.py``). The gasket is the number
# ``FramingSpec.sill_gasket`` states on EXT_2X6.
_SILL_GASKET_COMPRESSED = inch(0.0625)   # EPDM sill seal, compressed thickness
_MUDSILL = inch(1.5)                     # 2x PT sill plate, laid flat
BEARING_SEAT = inch(-(_SILL_GASKET_COMPRESSED.inches + _MUDSILL.inches
                      + _JOIST_DEPTH.inches))

# The basement's own two planes, derived from the seat. The pour is exactly 8'-0", which is
# what takes the 8" segments to ``#5 @ 41" o.c.`` on IRC Table R404.1.2(8)'s 8' row.
# ``plan/storeys/basement.py`` repeats both as literals; ``integrity.basement_bearing_seat``
# stops them drifting.
BASEMENT_WALL_HEIGHT = ft(8)
BASEMENT_DATUM = inch(BEARING_SEAT.inches - BASEMENT_WALL_HEIGHT.inches)

# The basement's FINISHED ceiling, off its own datum: joist soffit less the 5/8" board,
# 8'-0 15/16". ``Storey.default_ceiling_height`` reads this; soffits, ceiling placeables and
# lights hang from it.
BASEMENT_CEILING_HEIGHT = inch(-(_JOIST_DEPTH.inches + _CEILING_GWB[0].thickness.inches)
                               - BASEMENT_DATUM.inches)

# The TJI/truss seam east of x=18'. Same depth both sides, so no movement joint and no
# ceiling step (``RM-B-GYM`` is one flat ceiling); only the member changes.
_SEAM_Y = ft(13)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


_rect = rect


# --- the west half, in three bays -------------------------------------------------
#
# Each system names every wall its joists actually land on — duplicates on one grid line
# are a degenerate span and ``resolve/floors.py`` drops them — and the x=10' line north of
# ``_MECH_Y`` is declared as bearing. ``W-B-STR3`` is 2x6 bearing studs (see its note in
# plan/storeys/basement.py): what these joists need from it is 1 1/2" of structure either
# side of the NODE axis, which the studs give at 2 7/8" / 2 5/8".
#
# ``_MECH_Y`` is the N-B-BA-W / N-B-BA-E node line: the southernmost y at which x=10' is a
# bearing wall for its whole remaining run (W-B-STR3 to y=31', then W-B-STR to y=36' —
# one continuous wall, two tags). South of it x=10' is W-B-STR2, a non-bearing steel-stud
# stub, so the south bay keeps the full 18'-0" span.
#
# Joist depth does NOT follow the shorter spans. It is set by the deck match — the seat and
# the datum are one plane each, house-wide — so the 10' and 8' bays simply carry reserve.
_MECH_Y = ft(21, 9.375)
_STR_X = ft(10)

# The transition is a DOUBLE JOIST, and it has to be authored as one. Two abutting floor
# systems each lay a member on their own outline edge (``resolve/floors.py`` always emits at
# perp0 and perp1), so an edge shared to the inch puts two joists in the same place —
# ``structural.member_interference``, correctly. It is also not what anyone builds: a bay
# whose span changes from 18'-0" to 10'-0" gets a joist on each side of the line, nailed
# together. So the south system stops one joist WIDTH short and the pair sits face to face,
# which is exactly the one flange width this subtracts. Do not "tidy" the two edges back
# onto one number.
_TRANSITION_DOUBLE = inch(cross_section(_JOIST).flange_width_m / M_PER_IN)  # one flange
_MECH_Y_S = inch(_MECH_Y.inches - _TRANSITION_DOUBLE.inches)

# --- RM-M-BATH2's drop-in bath: the answer to plans/TODO.md's 60 psf item ---------
#
# The Kohler K-1130-W1 holds 81 gal (K-5713-W1's 72 until 2026-10-22). Filled, with a 200 lb
# occupant, that is 957 lb over its 13.33 ft2 plan area -- ~72 psf, against the 40 psf an IRC residential floor is
# designed to (R301.5 Table, adopted unamended by MN Rules 1309.0301; there is no bathtub
# provision or concentrated-load footnote anywhere in it). Boise Cascade's Tech Note IJ-12
# is the one manufacturer document on point and states the test plainly: "If a whirlpool
# filled with water or any other object weighs more than the 40 psf uniform load placed
# over its footprint, the floor joists or beams should be designed for the heavier load."
# By that test this bath qualifies, so it is answered here rather than argued with.
#
# ** THE ARITHMETIC SAYS BLOCKING, NOT A BEAM, AND ORIENTATION IS WHY. ** The bath is
# authored at rotation 90, so its 60" length runs NORTH-SOUTH and these joists run
# EAST-WEST: the load crosses four joist lines (y=208", 224", 240", 256") instead of
# bearing its length on two or three. Each line picks up ~72 psf over a 16" strip for the
# bath's 32" width -- 96 plf over 2.67 ft, or 256 lb -- where the parallel
# orientation would have put ~428 lb on one line. Against the 960 lb of live load the code
# already assigns each 24 ft2 tributary strip, the filled bath with a bather generates
# ~49% of the code live-load moment. It does not break the design assumption; it fits
# inside it. The floor is not overloaded, and no beam, post or squash block is warranted
# (a squash block would do nothing anyway -- it transfers bearing at a support, and this
# load is at midspan).
#
# What IS worth buying, while the basement ceiling is still open, is load SHARING. Two
# reinforcements, each blocking to the joist line on both sides, fill every bay the bath
# sits in (y 192"..256") with full-depth blocking on the bath's own centre line. Blocking
# is what makes four joists deflect together instead of the loaded one dishing between its
# neighbours -- which is the actual risk here, since the governing number was never
# strength. It is also what carries W-M-TUBDK-S, the deck's south knee wall, which runs
# PARALLEL to the joists at y=196" and lands in a bay rather than on a line.
#
# ``plies=1`` is blocking with no sister (``resolve/floors.py`` runs ``range(plies - 1)``);
# ``plies=2`` is one sister ply plus blocking. The y=240" entry carries the sister, which
# is the belt-and-braces an engineer would most likely add for a few hundred dollars of
# I-joist and is cheap only while the basement ceiling is open.
#
# ** TWO ENTRIES, NON-ADJACENT LINES, AND THE SISTER RIDES ONE OF THEM -- ALL THREE ARE
# FORCED BY THE RESOLVER, NOT CHOSEN. ** Each entry blocks to the joist line on BOTH sides,
# so lines 16" apart would double-block the bay between them and
# ``structural.member_interference`` FAILs on the duplicate. 208" and 240" are 32" apart
# and their four blocks tile 192"..256" exactly once. The sister then cannot be a third
# entry anywhere inside that range for the same reason -- a free-standing ply lands in a
# bay something else already blocks -- so it is authored ON the 240" line, where
# ``_reinforcement_members`` computes the blocks off the finished CLUSTER face and steps
# them clear of the ply by construction. It also happens to put the ply at y=242 1/2",
# which is 9 3/4" clear of PR-B-TUB2-DRAIN's drop at (7'-4", 19'-4 4/5"); on the 224" line
# it would have landed within a couple of inches of it.
#
# ** THE "97% OF ITS TABLE LIMIT" IN THE OLD TODO ENTRY WAS OVER-PRECISE, AND THAT IS
# WORTH KNOWING BEFORE ANYONE SPENDS MONEY ON IT. ** ``_IJOIST_SPAN_FT`` in
# ``checks/structural/checks.py`` is a simplified advisory table with ONE row per depth
# and no dead-load column, no joist series and no deflection criterion -- its docstring
# says "Simplified allowable joist spans (ft) at 16" o.c., residential floor (40 psf
# live)". 18'-6" is not a Weyerhaeuser lookup, so "18'-0" of an 18'-6" limit" is not the
# 97%-of-capacity reading it looks like. The real number wants ForteWEB with the actual
# series and the actual dead load, and the one input most likely to move it is the deck
# box's own weight: a 1 1/2" mortar bed plus platform and tile is roughly 450-500 lb of
# PERMANENT load over ~23 ft2, which is the part that creeps for thirty years while the
# 601 lb of water is there a few hours a week.
# (2026-11-01: the series is named, TJI 230, and every TJI floor now grades against
# TJ-4000's own row, ``TJI_230_FLOOR_SPAN``: 19'-10" at L/480, 40 live / 20 dead.)
#
# ** THE THIRD ENTRY IS THE WASHTOWER, AND IT IS BLOCKING ONLY — NO SISTER. ** FX-M-LAUNDRY
# stands at (115.83", 236.64"), so its 27"x32 3/4" footprint covers y 220"..253" and its
# nearest joist line is the SAME y=240" the bath already sisters — and a sister ply runs the
# WHOLE joist (``resolve/floors.py`` ``_reinforcement_members``), so the doubled line is
# already under the machine end to end. Nothing to add there.
#
# What the machine does not have is blocking at its OWN station: the bath's blocks all sit
# at x=74.56", 40" west. The WashTower is ~450 lb (340 dry + a drum of water) on 6.1 ft2,
# spread over 2-3 lines at 150-225 lb each — LIGHTER per line than the bath's 256 lb, on a
# line that is already doubled, so this is not a strength entry and no ply is warranted.
# It is the SPIN CYCLE: a ~20 Hz dynamic point load at essentially midspan of an 18'-0" bay,
# and blocking is what makes the neighbouring lines take it instead of one line drumming.
# Cheap only while the basement ceiling is open.
#
# ** IT MUST STAY LAST IN THIS TUPLE. ** ``laid`` is built in iteration order and every
# entry's blocks are cut against the cluster laid SO FAR. Ahead of the y=240" bath entry
# this one would cut its blocks against a bare joist and the bath's ply would then be laid
# straight through them — ``structural.member_interference``, two FAILs. ``plies=1`` asks
# for no ply of its own and tops up nothing; it rides the bath entry's finished cluster.
# one flange wide at x=115.83", clear of the bath's blocks at x=74.56". The station
# follows the machine: it moved 1 3/4" east on 2026-09-09 and this constant went with it.
_TUB_DECK_X = inch(74.56)          # the blocks' axis: 3.9" west of FX-M-BATH2-TUB's centre (78.49"),
                                   # clear of the end drain's drop at x=78.49", y=215.18"
_LAUNDRY_X = inch(115.83)          # FX-M-LAUNDRY's centre, and its own blocks' station
# ** W-M-CLN2 HAS NOTHING UNDER IT SINCE 2026-09-07. ** W-B-CW2B was the only basement wall
# beneath that run, and the basement hall's extension to the sauna wall deleted it (see
# storeys/basement.py). The partition is 9'-0" of INT_2X4_STAGGERED_GWB — double board both
# faces, the heaviest non-bearing wall type in the house — running x 13'-4"..18'-0" at
# y=216", which is ALONG FS-M-WEST's joists (``direction="x"``) and mid-bay between the
# 208" and 224" lines. That is the load case this house already answers with
# ``JoistReinforcement``, so it answers this one the same way: solid blocking in the bays,
# no sister ply. A partition parallel to the joists does not need a doubled line under it;
# it needs the neighbouring lines tied so the one bay does not carry it alone.
#
# ** y=217", NOT 216". ** ``at`` snaps to the NEAREST joist line and 216" is exactly
# equidistant from 208" and 224" — a coin toss decided inside the resolver. 217" is a
# deliberate 1" north, which snaps to 224" and blocks the 208"..240" bays; the wall's own
# 216" line sits inside the southern of those two.
#
# Two stations at 2'-3" o.c., inside the 4'-0" this house treats as the spacing for blocking
# under a parallel partition, with the x=18'-0" bearing line closing the east end and W-M-CLN
# (which still stacks, on W-B-CW2) closing the west.
_CLN2_X_W = inch(174)              # 1'-2" east of W-M-CLN2's west end at 13'-4"
_CLN2_X_E = inch(201)              # 1'-3" west of the x=18'-0" bearing line
# ** WALL-TOP BLOCKING (Minn. R. 1309.0404, Table R404.1(1) fn. f; basis note §4). ** Where a
# TJI field runs PARALLEL to a backfilled foundation wall, full-depth blocking in the first
# three joist spaces at <= 72" o.c., each station tied to the sill by five A35Z
# (``plan/wall_top_ties.py``) and within 8" of a MASA (derived: the nearest anchor moves to
# it). Two lines per station block four spaces, as on W-B-N1. ``code.MN_1309_0404_wall_top``
# grades it; W-B-N2 has no station because FO-M-STAIR fills those spaces.
def _wall_top_blocks(wall, xs, lines):
    return tuple(
        JoistReinforcement(at=pt(x, y), plies=1, blocking=True,
                           source=f"{wall} top restraint (Minn. R. 1309.0404, Table R404.1(1) "
                                  "fn. f): full-depth blocking in the first three joist "
                                  "spaces, 72\" o.c. max; subfloor nailed to it 8d @ 3\"")
        for x in xs for y in lines)


_S_WALL_LINES = (inch(16), inch(48))
_N_WALL_LINES = (inch(421), inch(389))  # FS-M-MECH's lines 421.4" / 389.4"

_WEST_FLOOR_REINFORCEMENT = (
    JoistReinforcement(at=pt(_TUB_DECK_X, inch(208)), plies=1, blocking=True,
                       source="RM-M-BATH2 drop-in bath: full-depth blocking in the "
                              "192\"..224\" bays under the bath and under W-M-TUBDK-S"),
    JoistReinforcement(at=pt(_TUB_DECK_X, inch(240)), plies=2, blocking=True,
                       source="RM-M-BATH2 drop-in bath: one sister ply plus full-depth "
                              "blocking in the 224\"..256\" bays, completing the spread"),
    JoistReinforcement(at=pt(_LAUNDRY_X, inch(240)), plies=1, blocking=True,
                       source="FX-M-LAUNDRY WashTower: full-depth blocking in the "
                              "224\"..256\" bays at the machine's own station, for spin-"
                              "cycle vibration — the y=240\" line is sistered already"),
    JoistReinforcement(at=pt(_CLN2_X_W, inch(217)), plies=1, blocking=True,
                       source="W-M-CLN2's west third: full-depth blocking in the "
                              "208\"..240\" bays under a 9'-0\" double-gwb partition that "
                              "runs ALONG the joists mid-bay and, since W-B-CW2B was "
                              "deleted on 2026-09-07, stacks on nothing. Authored intent, "
                              "not a check response: no rule in this engine grades an "
                              "unsupported partition"),
    JoistReinforcement(at=pt(_CLN2_X_E, inch(217)), plies=1, blocking=True,
                       source="W-M-CLN2's east third: the second of the pair above, "
                              "2'-3\" along, with the x=18'-0\" bearing line closing the "
                              "run 1'-3\" further east"),
    *_wall_top_blocks("W-B-S1", (inch(36), inch(84)), _S_WALL_LINES),
)

# South bay: full 18'-0" span, wall to centre line, y 0'-0" to the bathroom node line.
WEST_FLOOR = FloorSystem(
    uid="CMFS01AAAA", tag="FS-M-WEST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     # x=0': W-B-W2 carries y 0..18', W-B-W1 the rest. x=18': W-B-CS
                     # carries y 0..10'-0" since the sauna rotated (2026-09-05), W-B-CS3
                     # to 13'-10", W-B-CS2 to 18', W-B-CN2 to the node line.
                     # All five are true bearing; the three on x=18' resolve to one
                     # boundary (integrity.floor_bearing_grid holds them there).
                     bearing_refs=("W-B-W2", "W-B-W1", "W-B-CS", "W-B-CS3", "W-B-CS2",
                                   "W-B-CN2"),
                     # The x=18' plate is shared with FS-M-NE's trusses north of y=13'.
                     end_bearing=(("W-B-CS2", _JOIST_BEARING), ("W-B-CN2", _JOIST_BEARING)),
                     sill_tie="A35Z"),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    published_span=TJI_230_FLOOR_SPAN,
    reinforcements=_WEST_FLOOR_REINFORCEMENT,
    # The basement's ceiling: 5/8" gypsum end to end (houses/catlin/preferences.toml).
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _MECH_Y_S),
    source="catlin main floor, west half south of the bathroom node line — 11 7/8\" "
           "TJI 230 joists at 16\" o.c. spanning 18'-0\" east-west from the west wall to the "
           "x=18' bearing line",
)

# Mechanical-room bay: 10'-0" west wall to the x=10' line.
MECH_FLOOR = FloorSystem(
    uid="CMFS03AAAA", tag="FS-M-MECH",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-W1", "W-B-STR3B", "W-B-STR3", "W-B-STR"),
                     sill_tie="A35Z"),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    published_span=TJI_230_FLOOR_SPAN,
    ceiling_below=_CEILING_GWB,
    outline=_rect(_ZERO, _MECH_Y, _STR_X, _HOUSE),
    # The two ERV risers' own holes, added 2026-09-15 — the FIRST openings this deck has ever
    # declared, though four risers have been passing through its joist field all along.
    # FO-M-ERV-OA is the intake, which moved into this closet out of the NW chase that day;
    # FO-M-ERV-EA is the discharge, which stayed in the chase but re-stationed. Each cuts one
    # joist. The vents, the radon riser and the conduits through this deck are still undrawn —
    # see the openings' own notes in plan/storeys/main.py.
    openings=("FO-M-ERV-OA",),
    # W-B-N3 at x=8', W-B-N4 at x=5'-10", its east end: the FO-M-ERV-OA chase (x 6"..48 1/2")
    # and DU-ERV-RISER-SUP's 6" run west through the third space (x 17"..68") leave no other
    # spot. The station also serves W-B-N3's west end.
    reinforcements=(*_wall_top_blocks("W-B-N3", (inch(96),), _N_WALL_LINES),
                    *_wall_top_blocks("W-B-N4", (inch(70),), _N_WALL_LINES)),
    source="catlin main floor, over the furnace room — same joists as FS-M-WEST, spanning "
           "10'-0\" east-west from the west wall to the x=10' bearing line",
)

# Stair bay: 8'-0" from the x=10' line to the centre line, carrying FO-M-STAIR. Its west
# edge is a bearing edge, which is why W-B-STR3 has to stay a declared bearing ref —
# ``structural.floor_opening_header`` reads FO-M-STAIR's own refs and would otherwise size
# that edge a 9'-0" engineered header. That edge sits on the framed wall's plywood face at
# x=10'-3 1/4" rather than the pour's at 10'-6"; the refs did not change, because
# ``_opening_edge_has_declared_bearing`` reads the named walls' full layer footprints and
# this one reaches exactly that face.
STAIR_FLOOR = FloorSystem(
    uid="CMFS04AAAA", tag="FS-M-STAIR",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-STR3B", "W-B-STR3", "W-B-STR", "W-B-CN"),
                     end_bearing=(("W-B-CN", _JOIST_BEARING),)),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    published_span=TJI_230_FLOOR_SPAN,
    ceiling_below=_CEILING_GWB,
    outline=_rect(_STR_X, _MECH_Y, _CENTRE_X, _HOUSE),
    openings=("FO-M-STAIR",),
    source="catlin main floor, over the stair shaft — same joists as FS-M-WEST, spanning "
           "8'-0\" east-west from the x=10' bearing line to the x=18' bearing line",
)

# The east half's I-joist bay: the gym's ceiling, south of the truss seam.
#
# ** THE SEAM IS A DOUBLE MEMBER, AND IT HAS TO BE AUTHORED AS ONE ** (the ``_MECH_Y_S`` reasoning
# above): both fields lay a member on their own outline edge, so this one stops short by half
# of each member's width and the TJI and the truss's chord sit face to face.
_SEAM_GAP = inch((cross_section(_JOIST).flange_width_m + cross_section(_TRUSS).width_m)
                 / 2 / M_PER_IN)
_SEAM_Y_S = inch(_SEAM_Y.inches - _SEAM_GAP.inches)
EAST_FLOOR = FloorSystem(
    uid="CMFS02AAAA", tag="FS-M-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     # South of y=13'-10", so its west bearing is the framed pair W-B-CS
                     # (y 0..10'-0") and W-B-CS3 (10'-0"..13'-10").
                     bearing_refs=("W-B-CS", "W-B-CS3", "W-B-E1"),
                     sill_tie="A35Z"),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    published_span=TJI_230_FLOOR_SPAN,
    ceiling_below=_CEILING_GWB,
    outline=_rect(_CENTRE_X, _ZERO, _HOUSE, _SEAM_Y_S),
    # ** D-B-PATIO'S HEADER IS IN THIS BAND (2026-10-31). ** W-B-S3-FR bears this deck's
    # y=0 edge line but runs PARALLEL to the joists, so the 63 5/16" opening under it is
    # carried by a flush 2-ply 1 3/4" x 11 7/8" Microllam LVL beside the edge joist, seated
    # on the two 4-stud jamb packs. NOT a bearing ref: resolve/floors.py would cut every
    # joist at that line. Graded as `band_header/D-B-PATIO` (notes/patio_band_header.md).
    reinforcements=(JoistReinforcement(
        at=pt(inch(256), inch(3.25)), plies=3, member="1.75x11.875 LVL", blocking=False,
        extent=(inch(218.34375), inch(293.65625)),
        source="flush band header over D-B-PATIO (Door.header_in_band) — 2-ply Microllam "
               "LVL 2.0E, Weyerhaeuser TJ-9000 (July 2026)"),
        *_wall_top_blocks("W-B-S4", (inch(350), inch(398)), _S_WALL_LINES)),
    # RM-M-LIVING's fireplace piers pass through this deck in the pockets between joists
    # 005/006; the joists run continuous and the subfloor cut is DERIVED
    # (`resolve/through_deck.py`, decision #78).
    source="catlin main floor, east half south of y=13' — same joists as FS-M-WEST, "
           "spanning 18'-0\" from the x=18' bearing line to W-B-E1",
)

# --- the east half north of y=13': open-web floor trusses (decision #112) ---------------
#
# ** 16" O.C., THE PUBLISHED ROW, STIFFENED FOR BOUNCE (owner, 2026-11-02). ** TRIFORCE's
# OJ418S row (40 psf live / 25 psf dead, L/480, 16" o.c.) reaches 18'-0"; the trusses are
# 17'-11", so the field is a prescriptive read like the TJI fields, and the order asks
# L/720 live. The kitchen, dining and the lounge's north end stand here; what the owner
# wants is no bounce, which is the strongbacks and the doubled peninsula truss, not 60 psf.
# Same 11 7/8" depth as every other field, so nothing above or below this deck moved.
#
# The webs are ``FS-S-WEST``'s Warren layout (24" pitch, 13" clear, 12" offset): the
# fabricator builds both decks to one drawing, and ``mep.open_web_panel`` reads it. The
# kitchen drain, the ERV radials and the data conduits cross through the webs.
#
# ** THE x=18' PLATE IS SPLIT 3 1/2" / 2" ** exactly as on the second floor: ``W-B-CS2``/
# ``-CN2``/``-CN`` are 2x6 framed walls whose double top plate is the seat, the trusses take
# 3 1/2" (open-web minimum 3") and the TJIs west of it 2" (minimum 1 3/4").
# ``integrity.floor_end_bearing`` grades the pair.
#
# ** LINES. ** 16" from the seam, 156".."396"; the two north lines move (412 -> 408,
# 428 -> 420) so the three bays at W-B-N1 stay 12" — the N1 blocking, the CN-WT-N1 ties,
# the kitchen drain and risers and ``W-M-PAN-S`` (1" off 396) all keep their bays, and the
# north sink run's base cabinets get trusses at 408 and 420. 19 trusses.
#
# ** POINT LOADS FOR THE FABRICATOR. ** The peninsula's cabinet boxes (y 319.4"..343.4")
# carry the cantilevered quartz and its stool users: the 332" line under them is doubled
# (the sister lands at 328.5"), and 316" is 3.4" off their back edge. ``APPL-M-FRIDGE``/
# ``-FREEZER`` stand against the x=18' bearing wall (~175 lb a truss within 2'-3" of the
# seat), so they get no sister; they and the partitions this field carries (below) still go
# on the truss drawing. ``notes/main_floor_truss_basis.md`` lists them.
_TRUSS_OC = inch(16)
_TRUSS_LINE_MOVES = ((inch(412), inch(408)), (inch(428), inch(420)))
_PENINSULA_TRUSS = JoistReinforcement(
    at=pt(ft(27), inch(331.4)), plies=2, blocking=False,
    source="peninsula cabinet boxes (y 319.4\"..343.4\"): stone, brackets and three stool "
           "users bear through them mid-span; double the truss under the box centre "
           "(notes/main_floor_truss_basis.md)")
# ** STRONGBACKS (TRIFORCE pp. 20-22, Detail 5 Option #1). ** Two 2x6 on edge on the bottom
# chords, each hard against a face of the 27' web: A in the 26' opening, B in the 28' one,
# both within 6" of mid-span. Cut in a bay where a run crosses at their height ("can be cut
# between two joists for ducts or pipes").
_STRONGBACK_SOURCE = ("TRIFORCE Specifier Guide pp. 20-22, Detail 5 Option #1: 2x6 on edge, "
                      "attached to the diagonal web and chord, for a stiffer floor")
# Cut bays: the CW trunk, PR-B-HW-KITCH, CD-B-DATA-MEDIA (a bore would sit ~1.2" off the
# bottom edge, short of R502.8.1's 2") and the kitchen drain.
_STRONGBACK_OMIT = (inch(180), inch(196), inch(292), inch(414))
_STRONGBACKS = (
    Strongback(at=inch(317.75), omit_bays=_STRONGBACK_OMIT, source=_STRONGBACK_SOURCE),
    Strongback(at=inch(330.25), omit_bays=_STRONGBACK_OMIT, source=_STRONGBACK_SOURCE),
)

# ** ANCHORAGE TO THE CONCRETE (Minn. R. 1309.0404, notes/main_floor_truss_basis.md §4). **
# Minnesota's R404.1 amendment wants floor joists "connected to the sill plate at the top of
# wall with an approved connector", and where the framing runs PARALLEL to a foundation wall,
# full-depth blocking in the first three joist spaces at its Table R404.1(1) spacing (72" for
# an 8' wall in GM soil). So: ``sill_tie`` puts one A35Z on every truss end seated on the
# W-B-E1/E2 sill (533 lb a truss at 16" o.c. against 538 lb), the x=18' plate ends stay
# toe-nailed, and W-B-N1, the one foundation wall this field runs parallel to, takes
# blocking in the four bays y 32'..36' at x 21'/27'/33' — 72" o.c., 36" off each end wall,
# five A35Z a station (``plan/wall_top_ties.py``). Each line blocks the bay either side.
_N_WALL_BLOCK_X = (ft(21), ft(27), ft(33))
_N_WALL_BLOCKING = tuple(
    JoistReinforcement(at=pt(x, y), plies=1, blocking=True,
                       source="W-B-N1 top restraint (Minn. R. 1309.0404, Table R404.1(1)): "
                              "full-depth blocking in the bays next to a parallel foundation "
                              "wall, 72\" o.c.; subfloor nailed to it 8d @ 3\"")
    for x in _N_WALL_BLOCK_X for y in (ft(35), ft(33)))

NE_FLOOR = FloorSystem(
    uid="Q3ZJD83QVD", tag="FS-M-NE",
    joists=JoistSpec(member=_TRUSS, spacing=_TRUSS_OC, direction="x",
                     # x=18': W-B-CS2 (13'-10"..18'), W-B-CN2 (to the bath node line),
                     # W-B-CN (to 36'); x=36': W-B-E1 (to 18'), W-B-E2. The 10" of the seam
                     # bay south of 13'-10" lands on W-B-CS3, which FS-M-EAST also names.
                     bearing_refs=("W-B-CS3", "W-B-CS2", "W-B-CN2", "W-B-CN", "W-B-E1",
                                   "W-B-E2"),
                     web_panel_pitch=_WEB_PANEL_PITCH,
                     web_opening_width=_WEB_OPENING,
                     web_panel_offset=_WEB_PANEL_OFFSET,
                     end_bearing=(("W-B-CS3", _TRUSS_BEARING), ("W-B-CS2", _TRUSS_BEARING),
                                  ("W-B-CN2", _TRUSS_BEARING), ("W-B-CN", _TRUSS_BEARING)),
                     line_overrides=_TRUSS_LINE_MOVES,
                     sill_tie="A35Z"),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
    reinforcements=(*_N_WALL_BLOCKING, _PENINSULA_TRUSS),
    strongbacks=_STRONGBACKS,
    published_span=TRIFORCE_OJ418S_FLOOR_SPAN,
    ceiling_below=_CEILING_GWB,
    outline=_rect(_CENTRE_X, _SEAM_Y, _HOUSE, _HOUSE),
    source="catlin main floor, east half north of y=13' — 11 7/8\" open-web floor trusses "
           "at 16\" o.c. (TRIFORCE OJ418S row, 40/25 psf at L/480; L/720 live on the order), "
           "a doubled truss under the peninsula and two 2x6 strongbacks against bounce, "
           "spanning 18'-0\" from the x=18' bearing line to W-B-E1/W-B-E2 (decision #112, "
           "replacing SL-M-DECK)",
)

MAIN_ELEMENTS = [WEST_FLOOR, MECH_FLOOR, STAIR_FLOOR, EAST_FLOOR, NE_FLOOR]
