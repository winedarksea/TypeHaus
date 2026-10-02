# haus: editable
# BED1-3's wardrobes (owner, 2026-10-02): IKEA PAX, as the master closet (plan/closet.py).
# Types: plan/bedroom_wardrobe_types.py.
#
# ** THE FRAMES HANG ON A WALL RAIL AND ARE AUTHORED `MountKind.FLOOR` at 1/4". ** Same
# reason as plan/closet.py: `advisory.wall_backing_present` grades a WALL mount at the body's
# bottom. The rail backing is authored by hand in plan/backing.py (BK-S-BW1/BW2/BD2-PAX).
#
# BED1 and BED2 are identical: a PAX/GRIMO corner set in the SW corner, frame on the west
# wall (BW1/BW2, channel on the hall face, so the rail screws into studs), corner unit along
# the south wall (SS2 in BED1: channel on the BED1 face, so its tip anchor is into the
# channel only; BD1 in BED2: plain face). Then a doorless 19 5/8" six-shelf frame north of
# the L, up to D-S-BED1/2's south jamb (its casing omitted; the side panel is scribed).
# Stations from the wall start: BW1 from y 9'-0", BW2 from y 17'-8", BD2 from x 21'-11".
#
# BED3: two 39 3/8" frames on the south wall (BD2, channel on the BED2 side) from 5/8" off
# the east wall, behind an AULI/MEHAMN pair at x 28'-10"..35'-4 3/4", face y 29'-0 3/8".
# The mirror is the west half. The frames may swap ends; the pair does not care.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import deg, inch

BEDROOM_WARDROBES = [
    # --- BED1 ---------------------------------------------------------------------------
    # The L: y 9'-2 7/8"..12'-10 1/4" on the west wall, x 22'-1 3/8"..25'-8 3/4" on the south.
    Furniture(uid="CSB704AAAA", tag="FURN-S-BED1-WARD", type_ref="FURN-S-PAX-CORNER",
              room="RM-S-BED1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BW1", face="right", distance_from_start=inch(24.5625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # y 12'-10 1/4"..14'-5 7/8".
    Furniture(uid="7TV2ME4AA0", tag="FURN-S-BED1-PAX-SHELF", type_ref="FURN-S-PAX-SHELF-20",
              room="RM-S-BED1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BW1", face="right", distance_from_start=inch(56.0625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- BED2 ---------------------------------------------------------------------------
    # The L: y 17'-10 3/8"..21'-5 3/4"; the shelf frame y 21'-5 3/4"..23'-1 3/8".
    Furniture(uid="CSB705AAAA", tag="FURN-S-BED2-WARD", type_ref="FURN-S-PAX-CORNER",
              room="RM-S-BED2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BW2", face="right", distance_from_start=inch(24.0625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="MTZ7Q1RB7W", tag="FURN-S-BED2-PAX-SHELF", type_ref="FURN-S-PAX-SHELF-20",
              room="RM-S-BED2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BW2", face="right", distance_from_start=inch(55.5625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- BED3 ---------------------------------------------------------------------------
    # Two rods at the east (corner) end, x 32'-1 3/8"..35'-4 3/4"; shelves x 28'-10"..32'-1 3/8".
    Furniture(uid="252P8H5E8X", tag="FURN-S-BED3-PAX-HANG", type_ref="FURN-S-PAX-DOUBLE-40",
              room="RM-S-BED3", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD2", face="left", distance_from_start=inch(142.0625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="6V7KD9WV65", tag="FURN-S-BED3-PAX-SHELF", type_ref="FURN-S-PAX-SHELF-40",
              room="RM-S-BED3", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD2", face="left", distance_from_start=inch(102.6875),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The sliding pair on the frames' fronts; 1/4" up so its top meets theirs at 93 1/8".
    Furniture(uid="CSB706AAAA", tag="FURN-S-BED3-WARD", type_ref="FURN-S-PAX-SLIDE-79",
              room="RM-S-BED3", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD2", face="left", distance_from_start=inch(122.375),
                  normal_gap=inch(22.875), rotation_offset=deg(-180)))),
]
