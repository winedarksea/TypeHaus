"""Raised garden — the SRW apron wrapping the sunken garden on three sides.

From the brief's follow-up (2026-07-25): *"W-RG-BLOCK should form a U around the sunken
garden up to the N-S plane of the balcony railing on the arched concrete. It's 3' wider
than the sunken garden wall … it starts at the same height as the top of the sunken garden
wall, and goes down 3' from there (that puts it mostly below grade, which is fine for now),
with this change meaning W-RG-INNER can likely be deleted (W-SG-* replace it effectively)."*

**This is not the 36" planter it used to be.** Until that change the module built a bed:
two parallel cheeks — a cast inner one continuing ``W-SG-S`` up above its top, and an SRW
block outer one — holding 36" of soil between them, standing 3'-6" proud of grade. What it
builds now is a *retaining apron*: one SRW run wrapping the sunken garden's west, south and
east sides, topping out level with the retaining wall and running 3' down. The soil it
retains is the yard, not a planting bed.

**The apron is fully above grade since 2026-08-18, and this is what the house was lifted
for.** Its base sits at -2'-6": the house came out of the ground by moving grade down to
the apron's own footing line, so all three 6"-course feet of it stand proud of the soil
instead of two and a half of them being buried. Which also reverses what it retains. It
used to hold the yard back off the sunken garden; the yard is now *below* its base, and
what it holds is the 3'-0" raised terrace between it and the sunken-garden walls — the same
3 feet, retained from the other side.

** THE BASE COURSE HAS NEGATIVE EMBEDMENT, AND THIS PARAGRAPH USED TO DENY IT. ** It read
"-2'-6" is now finished grade", which was true for exactly three days. Grade went to
**-2'-10"** on 2026-08-21 with the basement-ceiling overhaul (`plan/site.py`,
`params/foundations.py::SITE_GRADE`) and **the apron did not follow it down** — nothing ties
`BASE` here to `SITE_GRADE`, and nothing checks the two against each other. So the base
course of a dry-stacked SRW retaining 3'-0" of fill stands **4" clear of finished grade**,
with its 6" levelling pad (``undercut``, below) two-thirds exposed.

That is a real defect, not a drafting slip. A segmental retaining wall is a *flexible*
system and is correctly designed here to ride 42" of frost without a frost footing — but it
depends absolutely on base-course embedment to resist sliding, and on a buried levelling pad
to resist erosion and frost lensing at the toe. `unbalanced_fill` below still states 3'-0",
so the model believes this wall retains three feet and knows nothing holds its toe.

**It is deliberately not fixed here**, because the fix is an owner's choice between two
different jobs and the cheaper one is not a change to this module at all: either raise
finished grade against the outboard face by 10"-12" over a ~4' bench (new `SpotElevation`s
in the editable `plan/site.py`, ~$700-1,500, and free if the real survey reshapes this yard
anyway), or drop the apron 4" and add a 6" course (~245 sf of face re-set, $7,350-14,700 at
this house's own `prices.toml` `RETAINING_BLOCK_12` rate). See `plans/pattern_language_review.md`.

Section, at a side leg, west (yard) to east (sunken garden):

    +0'-6"   +----+          +----+   <- apron top = W-SG-* top, both sides level
             |    | terrace  |    |
             | SRW|##########| SG |   <- the 3'-0" of fill the apron now retains, inboard
             |    |          |wall|
    -2'-6"   +----+          |    |   <- apron base, and its levelling pad below it
             . . . -- grade -. . . .   <- -2'-10" since 2026-08-21: FOUR INCHES LOWER
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
  re-derived — two derivations silently diverge the next time a dimension moves. It was
  ``PORCH_FRONT_AXIS_Y_FT`` until 2026-08-29, when that one constant split into two: the
  porch's beam plane stayed on -9.5' and the balcony's moved 12" south. The apron closes
  against the balcony RAILING, so it follows the balcony; both legs shorten 12".
- **The U's north corners close back to the balcony.** ``W-RG-WEST-BALCONY`` and
  ``W-RG-EAST-BALCONY`` are 3' SRW runs on that same plane. Their block faces meet the
  balcony's side railing faces, closing the two open ends.
- **``W-RG-INNER`` is gone.** Its job was to be the bed's inner cheek; ``W-SG-W2``/``E2``/
  ``S`` are the apron's inner face now, so a second wall on the same axis as ``W-SG-S``
  would be a duplicate. ``W-RG-BLOCK`` keeps uid ``RGW102AAAA`` on the south leg so it
  retains its IFC GlobalId (uuid5 over the uid) across the rewrite — the same deliberate
  uid preservation ``sunken_garden.py`` already practises.

The apron is filed on the ``basement`` storey key with the rest of the freestanding
sunken-garden structure (absolute elevations, same as the masonry railing walls) — the
house's own main/second wall loops must contain only house walls or storey-orientation
detection traces this structure by mistake.

**The levelling pad is modelled now** (2026-08-15), as a ``FootingBedding`` hosted on each
wall rather than on a footing — ``host_ref`` accepts either since this change, because the
excavation and the order of stone are the same whether concrete or a base course sits on
it. A ``Pad`` still does not fit (its top is pinned to the basement's -9' datum) and a
``Footing`` would put fictional concrete under a dry-stacked landscape wall.

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
    drop_ft: float = 3.0
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
    # Short returns close the U against the balcony side railings. Their far ends remain
    # open because they terminate at the balcony wall face rather than another RG wall axis.
    Node(uid="RGN005AAAA", tag="N-RG-WEST-BALCONY",
         position=pt(ft(X_WEST + 3.0), ft(Y_NORTH)), open_end=True),
    Node(uid="RGN006AAAA", tag="N-RG-EAST-BALCONY",
         position=pt(ft(X_EAST - 3.0), ft(Y_NORTH)), open_end=True),
]

# ``unbalanced_fill`` is authored rather than derived, and has to be. The engine derives
# unbalanced fill as the depth of soil standing against a wall *below grade*, which for
# these five legs is now zero — their base is grade. That is a true statement about the
# outboard (yard) side and a false one about the wall: the 3'-0" of terrace between the
# apron and the sunken-garden walls bears on the apron's inboard face over its whole height,
# and a dry-stacked SRW run needs exactly that fill (plus its batter and its drainage stone)
# to stand at all. Nothing in the model can infer a retained height on the high side of a
# freestanding wall, so it is stated: 3'-0", the apron's full run.
_APRON = dict(assembly="RETAINING_BLOCK_12", top_elevation=TOP, bottom_elevation=BASE,
              unbalanced_fill=ft(3))

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
# own underside (-2'-6", which is finished grade since 2026-08-18), so the excavation runs
# to -3'-0" — 6" below grade, which is what a levelling pad is.
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
