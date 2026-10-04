# haus: editable
# RM-M-CLOSET, the master walk-in: every fitted piece and every device in it, in one file
# so plan/placeables.py and plan/lighting.py do not grow. Types: plan/closet_types.py.
#
# The room: clear x 8'-5 3/8"..17'-8 5/8", y 13'-2 3/8"..17'-8 5/8" (41.9 sf). Walls, with
# the closet on the named face: W-M-CLN / W-M-CLN2 north (right), W-M-BA2E2 west (left),
# W-M-BDN2 south (left), W-M-C2 east (left). D-M-BED is in the south wall at x 14'-2"..16'-10"
# and swings out into the bedroom.
#
# North wall, west to east: a 32" leg of the wire corner; FURN-M-PAX-SHOW (drawers below,
# shelves above); then FURN-M-PAX-SHOW-HANG (owner, 2026-10-03; the same drawers under one
# long rail), 1/2" off the east wall to scribe. West wall (owner, 2026-10-04): two 29 1/2"
# SuperSlide shelf-and-rod extensions continue the corner's 24 3/4" leg to the south wall.
# Both tiers share the corner's shelf elevations and 79"/39" rod lines.
# Open frames: the aisle is ~31" (~27" at the pegs), and both north frames' drawers pull
# ~18" into it.
#
# ** THE PAX FRAMES HANG ON A WALL RAIL AND ARE AUTHORED `MountKind.FLOOR`. ** The product
# is IKEA's wall-mounted frame (no floor contact, so the raised carpet carries nothing). But
# `advisory.wall_backing_present` grades a WALL mount's band at the body's BOTTOM, and a
# 93" frame fastens at its TOP; authored WALL it asks for a band at the floor.
# BK-M-CLN-PAX and -CLN2-PAX are the real rail backing, authored by hand.
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
    # The wire corner, x 8'-5 3/8"..11'-1 3/8" on this wall and y 15'-7 7/8"..17'-8 5/8" down
    # the west. The L's return is on the type's -x side, so it runs down the WEST wall. The
    # rod hangs at the body's bottom, 5/16" up to its centre: 79"/39", the retained rod lines.
    # North-leg clips in BK-M-CLN-WIRE-HI/-LO; the west leg's land in BA2E2's HIGH and GRAB.
    Furniture(uid="W46JHDBAND", tag="FURN-M-CLOSET-CORNER-HI", type_ref="FT-M-CLOSET-CORNER-WIRE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(78.6875)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(19.375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="5SDTBM2GJM", tag="FURN-M-CLOSET-CORNER-LO", type_ref="FT-M-CLOSET-CORNER-WIRE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(38.6875)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(19.375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="YF4P52RKW3", tag="FURN-M-CLOSET-PAX-SHOW", type_ref="FURN-M-PAX-SHOW",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN", face="right", distance_from_start=inch(55.0625),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    # x 14'-4 3/4"..17'-8 1/8", 1/2" off the east wall to scribe.
    Furniture(uid="X1AG5PS5Y8", tag="FURN-M-CLOSET-PAX-HANG", type_ref="FURN-M-PAX-SHOW-HANG",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-CLN2", face="right", distance_from_start=inch(31.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- west wall: two wire extensions flush with the corner tiers ----------------------
    # y 13'-2 3/8"..15'-7 7/8", 12" deep; same body bottom/top and rod offset as the L.
    # A -0.01" face-datum correction aligns with the north-hosted L exactly.
    # Supported shelf joiners and rod connectors at the seam; see notes/closet_wire.md.
    Furniture(uid="PMF55DJ74K", tag="FURN-M-CLOSET-WEST-HI", type_ref="FT-M-CLOSET-WEST-WIRE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(78.6875)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(42.875),
                  normal_gap=inch(-0.01), rotation_offset=deg(-180)))),
    Furniture(uid="NX7D3QR6WT", tag="FURN-M-CLOSET-WEST-LO", type_ref="FT-M-CLOSET-WEST-WIRE",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(38.6875)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BA2E2", face="left", distance_from_start=inch(42.875),
                  normal_gap=inch(-0.01), rotation_offset=deg(-180)))),

    # --- south wall: robe pegs -----------------------------------------------------------
    # x 10'-4 3/8"..13'-10 3/8", ~3/4" short of a 2 1/2" casing on
    # D-M-BED (leaf at 14'-2"; casing is not modelled). Rail bottom 64", pegs at ~66", so a
    # robe hem clears the floor.
    Furniture(uid="NTTF3DRZJ8", tag="FURN-M-CLOSET-PEGS", type_ref="FURN-M-CLOSET-PEGS",
              room="RM-M-CLOSET", mount=Mount(kind=MountKind.WALL, elevation=inch(64)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-BDN2", face="left", distance_from_start=inch(47.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),

    # --- lighting --------------------------------------------------------------------------
    # ** THE CANS MOVED SOUTH TO y 15'-0" FOR NEC 410.16(C)(3) (2026-10-01). ** A recessed
    # LED in a clothes closet stands 6" off the storage space. The PAX zone runs ceiling to
    # floor to the frames' face at y 15'-9 3/4"; at y 15'-8" the cans were 1 3/4" inside the
    # limit. At 15'-0" they are ~7 3/4" clear of it and ~7 1/2" clear of the south wall's
    # 12" zone above 6'. The west wire run shares the corner's
    # 24" hanging-clothes zone: CAN1 is ~6 5/8" from its edge at x 10'-5 3/8".
    # Nothing in the engine grades 410.16: re-measure after any move.
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
    # TRADFRI 30 W driver on top of the east frame, corded into ED-M-CLOSET-RC1. It names
    # the circuit so its 30 VA lands on CKT-LT-MAIN; ED-T-RECEPTACLE carries no load_va, so
    # nothing counts twice.
    ElectricalDevice(uid="FB7ZP1MC75", tag="ED-M-CLOSET-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-TRADFRI-30", circuit="CKT-LT-MAIN",
                     room="RM-M-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(93.25)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-CLN2", face="right", distance_from_start=inch(19),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # One 38" OVERSIDAN under each north frame's top, 1 1/2" behind the front edge
    # (y 15'-11 1/4"): 76" at 1.5 W/ft = 9.5 W; x1.25 = 11.9 W on the 30 W driver.
    LightRun(uid="83CZ90GFSQ", tag="LR-M-CLOSET-PAX-SHOW", type_ref="ED-T-LT-PAX-STRIP",
             path=(pt(inch(134), inch(191.25)), pt(inch(172), inch(191.25))),
             room="RM-M-CLOSET", psu_ref="ED-M-CLOSET-LT-PSU",
             controlled_by=("ED-M-CLOSET-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(91))),
    LightRun(uid="81V49T7YB8", tag="LR-M-CLOSET-PAX-HANG", type_ref="ED-T-LT-PAX-STRIP",
             path=(pt(inch(173.375), inch(191.25)), pt(inch(211.375), inch(191.25))),
             room="RM-M-CLOSET", psu_ref="ED-M-CLOSET-LT-PSU",
             controlled_by=("ED-M-CLOSET-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(91))),
]
