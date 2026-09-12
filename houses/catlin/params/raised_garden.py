"""Raised garden — the SRW apron wrapping the sunken garden on three sides.

From the brief's follow-up (2026-07-25): *"W-RG-BLOCK should form a U around the sunken
garden up to the N-S plane of the balcony railing on the arched concrete. It's 3' wider
than the sunken garden wall … it starts at the same height as the top of the sunken garden
wall, and goes down 3' from there (that puts it mostly below grade, which is fine for now),
with this change meaning W-RG-INNER can likely be deleted (W-SG-* replace it effectively)."*

**It is a *retaining apron***: one SRW run wrapping the sunken garden's west, south and
east sides, topping out level with the retaining wall and running 3' down. The soil it
retains is the yard, not a planting bed.

**What the apron holds is the raised terrace between it and the sunken-garden walls.** It
tops out level with those walls and runs down from there; its base and its 6" levelling pad
sit in the yard outboard of it.

** THE BASE COURSE EMBEDMENT WAS NEGATIVE, AND IT IS NOW 8". REDUCED, NOT CLOSED. **
`drop_ft` was 3'-0" and the top was +0'-6", putting the base at -2'-6" against a **-2'-10"**
grade plane: the base course of a dry-stacked SRW retaining three feet of fill stood **4"
clear of finished ground**, with its levelling pad two-thirds exposed. Nothing tied `BASE`
to the ground and nothing checked the two against each other, so it went to 0 FAIL for two
revisions.

Two things changed on 2026-09-10 and the defect is arithmetic now rather than invisible:

* The yard is **modelled**. `plan/site.py` authors three south-yard stations at -3'-4" and
  `resolve/site_earth.local_grade_elevation_m` reads them, so this apron springs from a
  ground elevation somebody wrote down instead of from an assumed global plane.
* The **drop is 4'-0"**, eight whole 6" courses. Off a top that is now the porch datum at
  0'-0", that lands the base at **-4'-0"** against a yard at **-3'-4"**: the base course is
  buried **8"**, against the ~6" the guidance wants on a 3-foot wall.

**What the wall retains did not change, and it is worth being clear why.** The terrace
still stands 3'-4" above the yard — the apron top came down 2" with the court walls and the
yard is where it always was — so `unbalanced_fill` below is 3'-4" and not the 4'-0" drop.
The extra 8" buys embedment, not retained height. Stating it as the drop would put the run
on IRC R404.1.1's 48" threshold exactly and send five landscape walls into an R404.4
cantilever analysis they have no footing for; see the note beside `_APRON`.

**What is still open.** 8" of embedment is the number the arithmetic gives, not a number
anyone has designed to. Sliding, overturning and the global stability of a tiered apron
beside a 10-foot cut are still ungraded here, exactly as
`notes/sunken_garden_court_free_body.md` §9 says. **This is a defect reduced from "the toe
is in the air" to "the toe is buried 8" and nobody has checked the wall".** Do not read the
fix as a design.

Section, at a side leg, west (yard) to east (sunken garden):

    0'-0"    +----+          +----+   <- apron top = W-SG-* top = the porch datum, level
             |    | terrace  |    |
             | SRW|##########| SG |   <- 3'-4" of terrace over the yard: what it retains
             |    |          |wall|
             |    |          |    |
    -3'-4"   . . .|. . yard . |. . .   <- authored, three stations in plan/site.py
             |    |          |    |
    -4'-0"   +----+          |    |   <- apron base, 8" buried, levelling pad below it
        (yard)                     |

Plan — a U whose north corners return three feet to the balcony railing:

    y = -9.5'    +--+---- . . . . . . . . . . . . . . . ----+--+   <- balcony returns
                 |  |   (balcony closes the two north corners) |  |
                 |  |    +-------------------------------+     |  |
                 |  |    |        sunken garden          |     |  |
                 |  |    +-------------------------------+     |  |
    y = -33.33'  +--+---------------------------------------------+  <- south leg
               x=4.0                                            x=32.0

- **"3' wider" is measured from the sunken-garden walls' outer faces, not their axes.** That
  is the reading that reproduces the old south leg exactly (its axis was already at
  -33.33333 = -29.83333 - 3.0 - 0.5) and the one that clears the 84"-wide SG strip footings:
  measuring 3' from the axis instead would put the legs *inside* ``FT-SG-W2``/``FT-SG-E2``,
  which span x = [4.5, 11.5] and [24.5, 31.5]. The legs' inner faces land at 4.5 / 31.5 —
  tangent to those footings, no overlap.
- **North limit** is ``BALCONY_FRONT_AXIS_Y_FT`` (-10.5'), the plane ``RL-SG-BALCONY``
  sits on. Consumed from ``params/sunken_garden.py``'s exported contract rather than
  re-derived — two derivations silently diverge the next time a dimension moves. The apron
  closes against the balcony RAILING, so it follows the balcony, not the porch's beam plane
  (``PORCH_FRONT_AXIS_Y_FT``, -9.5').
- **The U's north corners close back to the court walls.** ``W-RG-WEST-BALCONY`` and
  ``W-RG-EAST-BALCONY`` are 3'-6" SRW runs on that same plane, and their inboard ends butt
  the OUTER faces of ``W-SG-W1``/``W-SG-E1`` (x 7'-6" / 28'-6"). They were 2'-9" until
  2026-09-12, leaving a 9" notch at each corner where the terrace fill met the yard behind
  nothing; closing it takes ``TR-SG-LEADER-SE``'s slot with it — see the NODES comment.
- **``W-RG-INNER`` is gone.** Its job was to be the bed's inner cheek; ``W-SG-W2``/``E2``/
  ``S`` are the apron's inner face now, so a second wall on the same axis as ``W-SG-S``
  would be a duplicate. ``W-RG-BLOCK`` keeps uid ``RGW102AAAA`` on the south leg so it
  retains its IFC GlobalId (uuid5 over the uid) across the rewrite — the same deliberate
  uid preservation ``sunken_garden.py`` already practises.

The apron is filed on the ``basement`` storey key with the rest of the freestanding
sunken-garden structure (absolute elevations, same as the masonry railing walls) — the
house's own main/second wall loops must contain only house walls or storey-orientation
detection traces this structure by mistake.

**The levelling pad is modelled** as a ``FootingBedding`` hosted on each wall rather than on
a footing — ``host_ref`` accepts either, because the excavation and the order of stone are
the same whether concrete or a base course sits on it. A ``Pad`` still does not fit (its top
is pinned to the basement's -9' datum) and a ``Footing`` would put fictional concrete under
a dry-stacked landscape wall.

Not modelled: the SRW cap unit, and the drainage aggregate + filter fabric behind the
block. The growing medium is not on this list because there is no longer a bed to fill.

Known and accepted: the west leg (x ∈ [3.5, 4.5]) runs over the x = 3 sewer and beside the
x = 5 water line for its whole length. Both are 5-6' below grade against a wall bottom that
now sits *at* grade, so there is no physical conflict — and no check exists for utility
clearance to catch one if a future change brought them together.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import FootingBedding, FoundationWall, Node, ft, inch, pt

from params.sunken_garden import (
    BALCONY_FRONT_AXIS_Y_FT,
    RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN,
    RETAINING_WALL_SPAN_X_FT,
    RETAINING_WALL_THICKNESS_IN,
    RETAINING_WALL_TOP_FT,
    SOUTH_RETAINING_WALL_AXIS_Y_FT,
)


@dataclass(frozen=True)
class RaisedGardenSpec:
    """The apron's own numbers. Everything else is read off the sunken garden."""

    # How far outboard of the sunken-garden walls' *outer faces* the apron stands. The
    # brief's "3' wider than the sunken garden wall" — see the module note on why this is
    # measured from the face and not the axis.
    clear_offset_ft: float = 3.0
    # How far the apron runs down from the sunken-garden wall top it starts level with.
    #
    # ** 4'-0", EIGHT WHOLE 6" COURSES, AND IT IS SET BY THE YARD. ** It was 3'-0" while
    # the yard was an assumed flat plane at the -2'-10" global datum and the apron top was
    # +0'-6". Both ends moved: the top is the porch datum at 0'-0" now (one form height
    # across all five court walls), and the yard is authored at -3'-4" by three stations in
    # `plan/site.py`. A 3'-0" drop off the new top lands the base at -3'-0", which is 4"
    # ABOVE the ground — the same negative embedment as before, arrived at the other way.
    #
    # 4'-0" buries the base course 8". 3'-10" would bury it 6", the figure the guidance
    # actually wants, and it is not taken: an SRW is laid in whole courses and 3'-10" is
    # 7.67 of them. The extra 2" is the cheapest inch of embedment on this job.
    drop_ft: float = 4.0
    block_thickness_in: float = 12.0  # one SRW unit deep
    block_course_height_in: float = 6.0  # SRW coursing
    # The compacted levelling pad the base course beds into: 6" of stone, running 6" past
    # each block face. Both are the ordinary SRW numbers for a wall this short — the pad is
    # wider than the block so the base course can be shifted into line without ending up
    # bearing on the pad's own edge, and it is bearing prep, not drainage, so it carries no
    # tile. It does carry the geotextile: unwrapped stone in this clay silts shut, the same
    # reasoning DRW-SG-MAIN is fabric-wrapped for.
    base_pad_depth_in: float = 6.0
    base_pad_overhang_in: float = 6.0


SPEC = RaisedGardenSpec()

_block_thickness_ft = SPEC.block_thickness_in / 12.0
_sg_half_thickness_ft = RETAINING_WALL_THICKNESS_IN / 24.0
# Outboard of a sunken-garden wall's outer face by the clear offset, then half the block's
# own thickness again to reach the apron's axis.
_step_out_ft = _sg_half_thickness_ft + SPEC.clear_offset_ft + _block_thickness_ft / 2.0

_sg_x_west, _sg_x_east = RETAINING_WALL_SPAN_X_FT
X_WEST = _sg_x_west - _step_out_ft                       # 4.0
X_EAST = _sg_x_east + _step_out_ft                       # 32.0
Y_SOUTH = SOUTH_RETAINING_WALL_AXIS_Y_FT - _step_out_ft  # -33.33333
Y_NORTH = BALCONY_FRONT_AXIS_Y_FT                        # -10.5

# ** THE RETURNS RUN ALL THE WAY TO THE CONCRETE NOW (owner, 2026-09-12). ** Both ends land
# on the sunken-garden wall's OUTER face — x 7'-6" and 28'-6" — so the terrace fill is
# retained corner to corner and the block butts cast concrete with no notch between them.
# Derived off the court wall rather than typed: the faces move with
# `RETAINING_WALL_SPAN_X_FT` and `RETAINING_WALL_THICKNESS_IN`, which are the two numbers
# that can put them anywhere else.
#
# They stopped 6" short of the balcony deck edge (x 6'-9" / 29'-3") until this date, for
# TR-SG-LEADER-SE's slot, which left a 9" gap at each north corner where the fill met the
# yard behind nothing. Closing it is 9" of block per return and it costs the leader its
# slot — see the NODES comment and `params/sunken_garden.py` beside the leader.
X_WEST_BALCONY = _sg_x_west - _sg_half_thickness_ft      # 7.5
X_EAST_BALCONY = _sg_x_east + _sg_half_thickness_ft      # 28.5

# Level with the sunken-garden wall top, 3' down. The drop is a whole number of 6" courses
# by construction, which is what lets the run be dry-stacked without a cut course.
TOP = ft(RETAINING_WALL_TOP_FT)
BASE = TOP - inch(SPEC.drop_ft * 12.0)

NODES = [
    # The south corners and the two balcony junctions are closed corners. A node with exactly
    # one *non*-open-end wall edge raises integrity.wall_loop_open as a hard ERROR
    # (resolve/topology.py), so only the ends at the balcony wall faces remain open.
    Node(uid="RGN001AAAA", tag="N-RG-SW", position=pt(ft(X_WEST), ft(Y_SOUTH)),
         open_end=False),
    Node(uid="RGN002AAAA", tag="N-RG-SE", position=pt(ft(X_EAST), ft(Y_SOUTH)),
         open_end=False),
    Node(uid="RGN003AAAA", tag="N-RG-NW", position=pt(ft(X_WEST), ft(Y_NORTH)),
         open_end=False),
    Node(uid="RGN004AAAA", tag="N-RG-NE", position=pt(ft(X_EAST), ft(Y_NORTH)),
         open_end=False),
    # Short returns close the U against the sunken-garden walls. Their far ends stay OPEN
    # because they terminate on a concrete wall face rather than on another RG wall axis.
    #
    # ** 3'-6", TO THE CONCRETE, SINCE 2026-09-12 — THE 9" NOTCH IS CLOSED. ** Each return
    # was 2'-9" and stopped 6" short of the balcony deck edge, which left a 9" gap between
    # its end and the court wall's outer face (x 7'-6" / 28'-6") where the terrace fill met
    # the yard with nothing retaining it. The gap was refused twice on the leader's account
    # and it was still a hole in a retaining wall; the owner closed it. 3'-6" is 3 1/2 SRW
    # units, so it is still one cut block per course on each return, and the cut is the same
    # trade it always was against a ripped finish board on the deck.
    #
    # ** WHAT IT COSTS: TR-SG-LEADER-SE LOSES ITS SLOT, AND THE OUTLET IS A DETAIL NOW. **
    # The leader's 3" pipe resolves at x 28'-10 7/8"..29'-1 1/8" on this same y, so the east
    # return now runs UNDER it. Nothing collides — the wall tops out at 0'-0" and the pipe's
    # outlet is at +0'-6", six inches above it, and `haus check` grades neither against the
    # other — but a 200 sf deck discharging onto the crest of a dry-stacked segmental wall
    # is the SRW failure mode, water into the joints and into the drainage stone that is the
    # only thing holding the run up. **So the outlet takes a cast elbow and a 1'-0" shoe
    # carrying it south clear of the cap, onto the terrace bed at y -11'-3".** That is 3"
    # past the block's south face, it lands on the same washed stone the leader has
    # discharged onto since the soakaway gave the balcony back, and it is the whole of the
    # change: the pipe, its straps and its bore are where they were. The elbow is not
    # modelled — `Downspout` is a vertical run with one outlet elevation — so it lives here
    # and in `notes/heat_pump_ground_pad.md`, and it is the one piece of this corner a
    # drawing has to carry rather than the model.
    Node(uid="RGN005AAAA", tag="N-RG-WEST-BALCONY",
         position=pt(ft(X_WEST_BALCONY), ft(Y_NORTH)), open_end=True),
    Node(uid="RGN006AAAA", tag="N-RG-EAST-BALCONY",
         position=pt(ft(X_EAST_BALCONY), ft(Y_NORTH)), open_end=True),
]

# ``unbalanced_fill`` is authored rather than derived, and has to be. The engine derives
# unbalanced fill as the depth of soil standing against a wall *below grade*, which on the
# outboard (yard) side is only the 8" the base course is buried by. That is a true
# statement about the yard and a false one about the wall: the raised terrace between the
# apron and the sunken-garden walls bears on the apron's INBOARD face, and a dry-stacked
# SRW run needs exactly that fill (plus its batter and its drainage stone) to stand at all.
# Nothing in the model can infer a retained height on the high side of a freestanding wall,
# so it is stated.
#
# ** IT IS THE DIFFERENTIAL, NOT THE WALL'S RUN, AND CONFLATING THE TWO IS A REAL TRAP. **
# The number is the height the terrace stands above the yard: the apron tops out with the
# court walls at 0'-0", the yard is authored at -3'-4", so 3'-4" of fill on the inboard
# face is unopposed by anything on the outboard one. Below -3'-4" both faces stand in the
# same undisturbed ground and it balances.
#
# It happened to equal ``drop_ft`` while ``drop_ft`` was 3'-0" and the base course stood 4"
# clear of the yard, because zero outboard soil makes the two the same. They are not the
# same any more and writing ``ft(SPEC.drop_ft)`` here would state 4'-0" — which is IRC
# R404.1.1's 48" threshold hit exactly, sending five landscape walls into an R404.4
# engineered analysis (a cantilever concrete stem on a strip footing) that a segmental
# gravity wall has no footing for and is the wrong model of anyway. The extra 8" of drop
# buys EMBEDMENT. It does not retain anything.
#
# So it tracks the exposure, which is where that 3'-4" is computed and pinned.
_APRON = dict(assembly="RETAINING_BLOCK_12", top_elevation=TOP, bottom_elevation=BASE,
              unbalanced_fill=inch(RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN))

WALLS = [
    # The south leg keeps W-RG-BLOCK's tag *and* its uid: the tag is what the energy and
    # grading exemptions match on by "W-RG-" prefix, and the uid is what its IFC GlobalId is
    # derived from. It is 28' now rather than 20' — it runs corner to corner of the U.
    FoundationWall(uid="RGW102AAAA", tag="W-RG-BLOCK",
                   start_node="N-RG-SW", end_node="N-RG-SE", **_APRON),
    # The two legs north to the arch wall's plane. New walls, new uids.
    FoundationWall(uid="RGW103AAAA", tag="W-RG-WEST",
                   start_node="N-RG-NW", end_node="N-RG-SW", **_APRON),
    FoundationWall(uid="RGW104AAAA", tag="W-RG-EAST",
                   start_node="N-RG-SE", end_node="N-RG-NE", **_APRON),
    FoundationWall(uid="RGW105AAAA", tag="W-RG-WEST-BALCONY",
                   start_node="N-RG-NW", end_node="N-RG-WEST-BALCONY", **_APRON),
    FoundationWall(uid="RGW106AAAA", tag="W-RG-EAST-BALCONY",
                   start_node="N-RG-EAST-BALCONY", end_node="N-RG-NE", **_APRON),
]

# The levelling pad under every leg. Hosted on the wall, not on a footing: there is no
# footing, and inventing one would order concrete nobody pours. The bed's top is the wall's
# own underside — **-4'-0" since 2026-09-10**, 8" below the authored -3'-4" yard — so the
# excavation runs to -4'-6", which is a buried levelling pad and no longer the two-thirds
# exposed one the module note used to have to confess to.
#
# The bands butt at the shared corner nodes rather than overlapping — ``rect_between`` is
# not extended past an axis end, the same convention ``_resolve_footing`` follows — so the
# stone at each corner is billed once. The trade-off is the other way: each 90° corner
# leaves a 2' x 2' notch of its own footprint unbilled, about 0.15 cu yd across the three
# of them. Under a landscape wall that is inside the compaction allowance.
BEDDINGS = [
    FootingBedding(
        uid=f"RGB{i:03d}AAAA",
        tag=f"FB-{w.tag[2:]}",
        host_ref=w.tag,
        undercut=inch(SPEC.base_pad_depth_in),
        width=inch(SPEC.block_thickness_in + 2 * SPEC.base_pad_overhang_in),
        aggregate="MnDOT Class 5 aggregate base",
        geotextile=True,
        drain_tile=False,
    )
    for i, w in enumerate(WALLS, start=1)
]

BASEMENT_ELEMENTS = [*NODES, *WALLS, *BEDDINGS]
