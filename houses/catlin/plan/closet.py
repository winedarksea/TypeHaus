# haus: editable
# RM-M-CLOSET, the master walk-in: every fitted piece and every device in it, in one file
# so plan/placeables.py and plan/lighting.py do not grow. Types: plan/closet_types.py.
#
# The room: clear x 8'-5 3/8"..17'-8 5/8", y 13'-2 3/8"..17'-8 5/8" (41.9 sf). Walls, with
# the closet on the named face: W-M-CLN / W-M-CLN2 north (right), W-M-BA2E2 west (left),
# W-M-BDN2 south (left), W-M-C2 east (left). D-M-BED is in the south wall at x 14'-2"..16'-10"
# and swings out into the bedroom.
#
# North wall, west to east (owner, 2026-10-01): a 32" custom bay of two rods (80"/40") with
# a valance and a shoe deck on the PAX lines; FURN-M-PAX-SHOW (drawers below, shelves
# above); then two 19 5/8" frames (owner, 2026-10-02): FURN-M-PAX-DRESS (dress rail, ~60"
# clear, three shelves above) and FURN-M-PAX-DOUBLE (rails on the bay's 79"/39" lines, a
# shelf on top), 5/8" off the east wall to scribe. Open frames: the aisle is ~31", and the
# central drawers pull ~18" into it.
#
# ** THE PAX FRAMES HANG ON A WALL RAIL AND ARE AUTHORED `MountKind.FLOOR`. ** The product
# is IKEA's wall-mounted frame (no floor contact, so the raised carpet carries nothing). But
# `advisory.wall_backing_present` grades a WALL mount's band at the body's BOTTOM, and a
# 93" frame fastens at its TOP; authored WALL it asks for a band at the floor. BK-M-CLN-PAX
# is the real rail backing, authored by hand. The plinth deck does sit on the floor.
#
# Distances are station-to-centre from each wall's start node: W-M-CLN from x 8'-2",
# W-M-CLN2 from x 13'-5", W-M-BA2E2 south from y 18'-0", W-M-BDN2 east from x 8'-2",
# W-M-C2 north from y 13'-0".

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    Furniture,
    LightRun,
    Location,
    Mount,
    MountKind,
    WallAttachment,
)
from typehaus.model import deg, ft, inch, pt

MAIN_CLOSET = [
    # --- north wall ---------------------------------------------------------------------
    # Custom bay centre x 9'-9 3/8" (101 3/8"..133 3/8"). Both boards are 22 7/8" deep, the
    # PAX depth, so the front reads as one line; the valance tops out at the frames' 93 1/8".
    Furniture(uid="8YDGGBNZHY", tag="FURN-M-CLOSET-VALANCE", type_ref="FT-M-CLOSET-VALANCE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(90.125)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(19.375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="SA4RFVMGE4", tag="FURN-M-CLOSET-PLINTH", type_ref="FT-M-CLOSET-PLINTH",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(19.375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # Rods run east off the west wall, 12" off the north face (hanger centre), into the
    # central frame's side panel. Their bases sit in BA2E2's existing wet-wall courses
    # (BK-M-BA2E2-HIGH 72"..79 1/4", -GRAB 32"..39 1/4"), so they need no new band.
    Furniture(uid="XX4XJN6N0V", tag="FURN-M-CLOSET-ROD-HI", type_ref="FT-M-CLOSET-ROD-32",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(79)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(15.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="5M8RT8XXWJ", tag="FURN-M-CLOSET-ROD-LO", type_ref="FT-M-CLOSET-ROD-32",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(39)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(15.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="YF4P52RKW3", tag="FURN-M-CLOSET-PAX-SHOW", type_ref="FURN-M-PAX-SHOW",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(55.0625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # x 14'-4 3/4"..16'-0 3/8" and 16'-0 3/8"..17'-8".
    Furniture(uid="X1AG5PS5Y8", tag="FURN-M-CLOSET-PAX-DRESS", type_ref="FURN-M-PAX-DRESS",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN2", face="right", distance_from_start=inch(21.5625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="88MG1P0R11", tag="FURN-M-CLOSET-PAX-DOUBLE", type_ref="FURN-M-PAX-DOUBLE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN2", face="right", distance_from_start=inch(41.1875),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- west wall: SEKTION drawers, south-justified (owner, 2026-10-01) -----------------
    # Two 24" units form one 48" run. The north unit is under the west bay's 39" rod: the
    # rod's first 15 1/2" from the wall is directly over the 36" counter and cannot take
    # hanging clothes; only its remaining length beyond the cabinet face stays usable.
    Furniture(uid="RBXDWNQ5MB", tag="FURN-M-CLOSET-SEKTION-N", type_ref="FURN-M-SEKTION-24-DRAWER",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(21.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="3MCJXB7KKA", tag="FURN-M-CLOSET-SEKTION-S", type_ref="FURN-M-SEKTION-24-DRAWER",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(45.625),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # --- south wall: robe pegs, between the SEKTION run and the switch -------------------
    # x 9'-9"..13'-3"; rail bottom 64", pegs at ~66", so a robe hem clears the floor.
    Furniture(uid="NTTF3DRZJ8", tag="FURN-M-CLOSET-PEGS", type_ref="FT-M-PEG-RAIL-42",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(64)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BDN2", face="left", distance_from_start=inch(43),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # --- lighting --------------------------------------------------------------------------
    # ** THE CANS MOVED SOUTH TO y 15'-0" FOR NEC 410.16(C)(3) (2026-10-01). ** A recessed
    # LED in a clothes closet stands 6" off the storage space. The PAX zone runs ceiling to
    # floor to the frames' face at y 15'-9 3/4"; at y 15'-8" the cans were 1 3/4" inside the
    # limit. At 15'-0" they are ~7 3/4" clear of it and ~7 1/2" clear of the south wall's
    # 12" zone above 6'. Nothing in the engine grades 410.16: re-measure after any move.
    # 1,300 lm over 41.9 sf at CU 0.60 x LLF 0.80 = 14.9 fc on the aisle, plus the PAX strips
    # inside the frames. x stays on 11'/15', one can per side of the central frame.
    ElectricalDevice(uid="QTM000VAAA", tag="ED-M-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(11), ft(15)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="1N2XSTDANE", tag="ED-M-CLOSET-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(15), ft(15)), type_ref="ED-T-LT-CAN3",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** MOVED OFF THE WEST WALL (2026-10-01): ** at y 16'-10" it stood behind the west
    # bay's hanging clothes. Now on the south wall at x 13'-9", latch side of D-M-BED, 46".
    ElectricalDevice(uid="QTM000WAAA", tag="ED-M-CLOSET-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN2", face="left", distance_from_start=inch(67),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The lit mirror: east wall, centred y 14'-6" between the south corner and the PAX face,
    # bottom 14", top 74". Hardwired on CKT-LT-MAIN; its own touch switch, so no controlled_by.
    ElectricalDevice(uid="4JFYZ9V9P7", tag="ED-M-CLOSET-MIRROR", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-MIRROR-CLOSET",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(14)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C2", face="left", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The PAX strips' outlet: north wall just above the frames, x 14'-6", SWITCHED by the
    # closet switch, so one switch lights the room. The OVERSIDAN door sensor does nothing on
    # an open frame. On CKT-LT-MAIN: the driver is a lighting load.
    ElectricalDevice(uid="1VBBCZK5TY", tag="ED-M-CLOSET-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-LT-MAIN", room="RM-M-CLOSET",
                     controlled_by=("ED-M-CLOSET-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(96)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-CLN2", face="right", distance_from_start=inch(13),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # TRADFRI 30 W driver on top of the dress frame, corded into ED-M-CLOSET-RC1. It names
    # the circuit so its 30 VA lands on CKT-LT-MAIN; ED-T-RECEPTACLE carries no load_va, so
    # nothing counts twice.
    ElectricalDevice(uid="FB7ZP1MC75", tag="ED-M-CLOSET-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-TRADFRI-30", circuit="CKT-LT-MAIN",
                     room="RM-M-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(93.25)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-CLN2", face="right", distance_from_start=inch(19),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # One OVERSIDAN per frame under its top panel, 1 1/2" behind the front edge
    # (y 15'-11 1/4"): 38" + 18" + 18" = 74" at 1.5 W/ft is 9.3 W; x1.25 = 11.6 W on a 30 W
    # driver, three of its nine sources.
    LightRun(uid="83CZ90GFSQ", tag="LR-M-CLOSET-PAX-SHOW", type_ref="ED-T-LT-PAX-STRIP",
             path=(pt(inch(134), inch(191.25)), pt(inch(172), inch(191.25))),
             room="RM-M-CLOSET", psu_ref="ED-M-CLOSET-LT-PSU",
             controlled_by=("ED-M-CLOSET-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(91))),
    LightRun(uid="81V49T7YB8", tag="LR-M-CLOSET-PAX-DRESS", type_ref="ED-T-LT-PAX-STRIP",
             path=(pt(inch(173.5625), inch(191.25)), pt(inch(191.5625), inch(191.25))),
             room="RM-M-CLOSET", psu_ref="ED-M-CLOSET-LT-PSU",
             controlled_by=("ED-M-CLOSET-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(91))),
    LightRun(uid="27DAVE1XP0", tag="LR-M-CLOSET-PAX-DOUBLE", type_ref="ED-T-LT-PAX-STRIP",
             path=(pt(inch(193.1875), inch(191.25)), pt(inch(211.1875), inch(191.25))),
             room="RM-M-CLOSET", psu_ref="ED-M-CLOSET-LT-PSU",
             controlled_by=("ED-M-CLOSET-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(91))),
]
