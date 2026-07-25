"""Raised garden — the 36" planting bed along the sunken garden's south retaining wall.

From the brief's second follow-up set: *"a 36" high garden that utilizes on the inside the
top of the sunken garden retaining wall, and on the outside concrete retaining wall
blocks."*

Section, north (sunken garden) to south (yard):

    +3'-6"   +-------+--------+-------+   <- bed top, both cheeks
             | inner |  soil  | block |
    +0'-6"   | cheek |        | wall  |   <- top of W-SG-S, the retaining wall it uses
             +-------+--------+       |
     0'-0"   -------- grade -----+    |
    -0'-6"                       +----+   <- buried SRW base course

- **Inside face**: the sunken-garden retaining wall's top. ``W-RG-INNER`` is the same 12"
  cast section on the same axis and the same two nodes as ``W-SG-S``, continued up from
  that wall's ``+0'-6"`` top — so the bed's height is measured from the wall it uses, and
  its own top lands on the ``+3'-6"`` the site's south spot elevations already record.
- **Outside face**: ``W-RG-BLOCK``, dry-stacked segmental retaining-wall block
  (``RETAINING_BLOCK_12``), with its bottom course buried per SRW practice.

The two cheeks are filed on the ``basement`` storey key with the rest of the freestanding
sunken-garden structure (absolute elevations, same as the masonry railing walls) — the
house's own main/second wall loops must contain only house walls or storey-orientation
detection traces this structure by mistake.

Not modelled: the SRW cap unit, the drainage aggregate + filter fabric behind the block,
the compacted aggregate levelling pad the buried base course beds into, and the growing
medium itself. None of them has an element kind that fits — a ``Pad``'s top is pinned to
its storey datum (here the basement's -9'), a ``Footing`` would put fictional concrete
under a dry-stacked landscape wall, and there is no fill/planting-medium kind at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import FoundationWall, Node, ft, inch, pt

from params.sunken_garden import (
    RETAINING_WALL_SPAN_X_FT,
    RETAINING_WALL_THICKNESS_IN,
    RETAINING_WALL_TOP_FT,
    SOUTH_RETAINING_WALL_AXIS_Y_FT,
    SOUTH_RETAINING_WALL_NODES,
)


@dataclass(frozen=True)
class RaisedGardenSpec:
    bed_height_in: float = 36.0  # brief: a 36" high garden, measured off the wall it uses
    bed_clear_depth_in: float = 36.0  # N-S soil width between the two cheeks
    block_thickness_in: float = 12.0  # one SRW unit deep
    block_course_height_in: float = 6.0  # SRW coursing; the wall is a whole number of these
    buried_courses: int = 1  # SRW base course sits below grade on its levelling pad


SPEC = RaisedGardenSpec()

_inner_wall_thickness_ft = RETAINING_WALL_THICKNESS_IN / 12.0
_block_thickness_ft = SPEC.block_thickness_in / 12.0

# The bed sits on the *outside* (south) of the retaining wall it uses, so every N-S station
# below steps south (-Y) from that wall's axis.
_inner_outer_face_y = SOUTH_RETAINING_WALL_AXIS_Y_FT - _inner_wall_thickness_ft / 2.0
_block_inner_face_y = _inner_outer_face_y - SPEC.bed_clear_depth_in / 12.0
_block_axis_y = _block_inner_face_y - _block_thickness_ft / 2.0

_x_west, _x_east = RETAINING_WALL_SPAN_X_FT

# Heights. The bed top is the one shared datum: the inner cheek rises the authored 36" off
# the retaining-wall top, and the block wall is built *down* from that same top — whole
# courses to grade, plus the buried base course — so the two cheeks cannot drift apart.
_bed_base = ft(RETAINING_WALL_TOP_FT)
_bed_top = _bed_base + inch(SPEC.bed_height_in)
_courses_above_grade = round(
    (SPEC.bed_height_in + RETAINING_WALL_TOP_FT * 12.0) / SPEC.block_course_height_in
)
_block_courses = _courses_above_grade + SPEC.buried_courses
_block_base = _bed_top - inch(SPEC.block_course_height_in * _block_courses)

# The block wall is a single free-standing run, so both ends are open (like the sunken
# garden's own north-edge nodes) — there is no loop to close around a planting bed.
NODES = [
    Node(uid="RGN001AAAA", tag="N-RG-SW", position=pt(ft(_x_west), ft(_block_axis_y)),
         open_end=True),
    Node(uid="RGN002AAAA", tag="N-RG-SE", position=pt(ft(_x_east), ft(_block_axis_y)),
         open_end=True),
]

WALLS = [
    # Inner cheek: the cast retaining wall's own section, continued above its +6" top. It
    # runs west→east on the same nodes as W-SG-S so it inherits that wall's winding.
    FoundationWall(uid="RGW101AAAA", tag="W-RG-INNER",
                   start_node=SOUTH_RETAINING_WALL_NODES[0],
                   end_node=SOUTH_RETAINING_WALL_NODES[1],
                   assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_bed_top, bottom_elevation=_bed_base),
    # Outer cheek: dry-stacked SRW block, base course buried.
    FoundationWall(uid="RGW102AAAA", tag="W-RG-BLOCK",
                   start_node="N-RG-SW", end_node="N-RG-SE",
                   assembly="RETAINING_BLOCK_12",
                   top_elevation=_bed_top, bottom_elevation=_block_base),
]

BASEMENT_ELEMENTS = [*NODES, *WALLS]
