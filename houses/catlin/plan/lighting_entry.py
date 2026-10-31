# haus: editable
# Catlin lighting — the MAIN storey's mudroom, closets, north entry, hall and stair head.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    Mount,
    MountKind,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

ENTRY_LIGHTING = [
    # RM-M-CLOSET's cans, switch, mirror and PAX strips are in plan/closet.py.
    # Centred east-west in RM-M-MUD-CLOSET; y keeps the trim 6" outside the 16" shelf's
    # storage space (NEC 410.16) and inside the one joist bay that allows it.
    ElectricalDevice(uid="QTM000XAAA", tag="ED-M-STORAGE-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(3, 2.125), ft(28, 10.75)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-MUD-CLOSET",
                     controlled_by=("ED-M-STORAGE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # room=RM-M-MECH, the shaft closet off the mudroom's north end. Its ceiling is risers,
    # trunk and the ERV chase header; the one bay a 6" housing clears is over
    # EQ-M-ERV-MAN-EXH, so the can lights that plenum's dampers from 3" above it.
    ElectricalDevice(uid="QTM000YAAA", tag="ED-M-STORAGE-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 1), ft(35, 0.375)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-MECH",
                     controlled_by=("ED-M-STORAGE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Keep the 3-gang bank on W-M-MUDC-E's east (mudroom) face after the door moves.
    # The first 16" stud bay holds the bank at 4" pitch, clear of the corner pack.
    # W-M-MECH-E would put it behind the open D-M-ENTRY leaf.
    ElectricalDevice(uid="QTM000ZAAA", tag="ED-M-STORAGE-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-MUDC-E", face="left", distance_from_start=inch(13),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # ** THE NORTH ENTRY'S OWN LIGHT, AND UNTIL 2026-09-11 IT DID NOT EXIST. **
    # `code.R303_8_exterior_stairway_illumination` wants a luminaire at ST-BW-ENTRY's top
    # landing, and it PASSED for as long as the landing reached x=11'-6": ED-M-PANTRY-LT, a
    # wall light INSIDE the pantry at (18'-5", 33'-4 3/8"), sat 3'-10" from the tiers in
    # plan and the rule's 4'-0" ring has no opinion about the wall between them. Narrowing
    # the landing to the service door's jamb (x=9'-7") moved the tiers 1'-11" west and the
    # pantry light fell out of the ring — which is the first honest reading that rule has
    # given this stair. So: a mark R sconce (the garage-door pair's type) on the house's north
    # face beside D-M-ENTRY, under the canopy, lighting the landing, the door and the top of
    # the tiers at once.
    #
    # x=11'-4" is W-M-N2's bay centre between the studs at 10'-8" and 12'-0" — east of the
    # tee at N-M-N2 where W-M-STRW's bearing stack lands, and 1'-10" east of the door's RO.
    # y is the fixture's CENTRE: the cladding face is 36'-7 1/4" (params/north_entry_frame.py
    # ::HOUSE_CLADDING_Y_FT) and the 5" body owes it half its depth, so 36'-9 3/4". 6'-4" is
    # storey-relative on `main` (datum = top of joists), so the 9" housing runs 6'-4"..7'-1"
    # beside a 6'-8" door head; the canopy's truss chords are at +7'-4" at the headers and
    # rise toward the ridge, so nothing is overhead within 1'-0".
    ElectricalDevice(uid="NGK4BKKT48", tag="ED-M-ENTRY-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-EXT",
                     circuit="CKT-LT-MAIN", controlled_by=("ED-M-ENTRY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 4)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N2", face="right", distance_from_start=inch(80),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Its switch, inside the dwelling (R303.8.1 — the garage's ED-G-EXT-SW is in the wrong
    # building for this one). D-M-ENTRY fills W-M-N3 to within 6" and 3 5/8" of its ends, so there is
    # no north-wall station beside the door; use the north gang on W-M-MUDC-E
    # (see ED-M-STORAGE-SW), the one nearest the front door. A Matter relay since 2026-10-31,
    # so HA can light the landing at dusk and on arrival.
    ElectricalDevice(uid="1XT4G5S2XX", tag="ED-M-ENTRY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-MUDC-E", face="left", distance_from_start=inch(5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # ** THE MUDROOM ITSELF HAD NO LIGHT AT ALL UNTIL 2026-09-15. ** It is the front door,
    # and both devices standing in it switched lights somewhere else: ED-M-STORAGE-SW the
    # two closet cans, ED-M-ENTRY-SW the exterior sconce above. Nothing reported it —
    # `electrical.room_lighting` walks habitable rooms and this one is Occupancy.STORAGE,
    # so a windowlit vestibule with a 32" door at the far end read as fine.
    #
    # ** ONLY HALF THIS CEILING IS USABLE, AND IT IS NOT THE HALF THE BENCH IS UNDER. **
    # The ceiling is FS-S-WEST — 11 7/8" open-web floor trusses at 16" o.c. running in x,
    # 5/8" gypsum under them. The room is an L. Its WEST BAND (x 6 5/8"..72", between the
    # two closets, where the window and FURN-M-MUD-BENCH are) is where all THIRTEEN
    # DU-M-ERV-R-* radials fan out of the manifolds in RM-M-MECH — every JOIST_BAY duct on
    # FS-S-WEST is in this band. The old 5"-tall 3" can (mark C, retired) did not go there. The EAST
    # STRIP (x 74"..116 1/8", the walk from D-M-ENTRY to D-M-MUD) carries no ERV radial at
    # all: only CD-M-DATA-KITCH at 9'-2 1/4" and PR-M-S-BATH1-LAV-DRAIN's leg at
    # 9'-6 11/16"..9'-9 3/4", both above a 5" housing hung off a 106 1/4" ceiling.
    #
    # The two walk cans at x=8'-0", D-M-ENTRY's and D-M-MUD's RO centreline, each in a
    # truss mid-bay: y=28'-8", and y=33'-10" between the 32'-11"/33'-2" chords and the
    # 34'-6" override.
    ElectricalDevice(uid="1QB0DSS28T", tag="ED-M-MUDROOM-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(8), ft(28, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     controlled_by=("ED-M-MUDROOM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CZBCJDJJ6G", tag="ED-M-MUDROOM-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(8), ft(33, 10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     controlled_by=("ED-M-MUDROOM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # A third can centres over the 36" bench (x=15 1/8", y=31'-4"), a task light for
    # boots on and off; the bench is the one seat in this house a can stands over on
    # purpose. It joins the mudroom dimmer, in a bay clear of the ERV radials.
    ElectricalDevice(uid="MUDCAN00001", tag="ED-M-MUDROOM-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(inch(15.125), ft(31, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     controlled_by=("ED-M-MUDROOM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The bench's wall light remains as layered light beside the new can. The can's ceiling
    # location needs duct coordination (above), and the sconce avoids putting all bench light
    # on the top of a bowed head. This is mark H, the up/down already bought 15 times in this
    # house — no new type, no new prices.toml row. Centred y=31'-4" on the bench and WIN-M-MUD,
    # which the bench centreline fixes; at 6'-8" it clears the window's 5'-6" head by 8"
    # and the 106 1/4" ceiling by 20". x=8 11/16" is the face convention: W-M-W1's paint
    # plane is 6.635" and the 4"-deep body is centred on its own position.
    ElectricalDevice(uid="FPDTQVFPTK", tag="ED-M-MUDROOM-SCONCE", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM", controlled_by=("ED-M-MUDROOM-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 8)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-W1", face="left", distance_from_start=inch(24),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # ** A DIMMER, AND IT IS NOT ON THE NORTH WALL. ** D-M-ENTRY fills W-M-N3 to within 6"
    # and 3 5/8" of its ends, so this is the middle gang of the 3-gang plate on W-M-MUDC-E (see
    # ED-M-STORAGE-SW): closet cans, house light, porch light.
    #
    # ED-T-SWITCH-DIM carries no load_va, so the dimmer is free electrically; what it buys
    # is arriving at 11pm into something other than a bright white box. All three fixtures
    # above are dimmable=True. The whole addition is 30 VA (2 x 9 + 12) on CKT-LT-MAIN.
    ElectricalDevice(uid="0ZZNRE9AV0", tag="ED-M-MUDROOM-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-OCC-PIR",
                     circuit="CKT-LT-MAIN", room="RM-M-MUDROOM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-MUDC-E", face="left", distance_from_start=inch(9),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-M-HALL: three cans down the run on a 3-way pair, with ED-M-STAIR-CAN1 below as the
    # fourth: one row at y=24'-8" (the mid-bay nearest the hall's centre line), 2'-8" apart,
    # 2'-0" off each end.
    ElectricalDevice(uid="QTM0010AAA", tag="ED-M-HALL-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(8, 3), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0011AAA", tag="ED-M-HALL-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(10, 11), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0012AAA", tag="ED-M-HALL-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(16, 3), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-HALL-SW", "ED-M-HALL-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # West end of the run, on W-M-BAE's hall face just south of D-M-BATH1 (door spans
    # y 23'-4"..25'-4", the only piece of wall a plate fits on). Moved here 2026-07-31 from
    # x=4'-5", which was 1'-7" inside RM-M-BATH1 (wall at x=6'-0") — `integrity.
    # placeable_room_mismatch` had been reporting it. rotation 90 faces east into the hall.
    # y +1" on 2026-08-29 for the same reason as ED-M-BATH1-MIRROR above: W-M-HS2 retyped to
    # the 6 3/4" wet wall with W-M-HS1, so the hall's south face came 1" north and the plate's
    # bottom 3/8" was left standing in it. At 22'-10" the plate runs y 22'-8"..23'-0" and is
    # still 4" clear of D-M-BATH1's opening at 23'-4" — that door is what bounds it north.
    ElectricalDevice(uid="QTM0013AAA", tag="ED-M-HALL-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BAE", face="left", distance_from_start=inch(44),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTM0014AAA", tag="ED-M-HALL-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-HS4", face="left", distance_from_start=inch(50),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # The stair head. The can stood under FO-S-STAIR's open well with no ceiling to recess
    # into; since 2026-10-31 it is the hall row's third can, at the foot of ST-M2S, on its
    # own backup-circuit switch. The switch is also one end of the basement railing run's
    # 3-way.
    ElectricalDevice(uid="QTM0015AAA", tag="ED-M-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 7), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-STAIR-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0016AAA", tag="ED-M-STAIR-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER-COMPANION",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-STRW", face="left", distance_from_start=inch(96),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]
