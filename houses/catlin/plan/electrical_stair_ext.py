# haus: editable
# Stair-landing guide-light duplexes (T6525-W, 12" above the deck) and the two exterior
# in-use receptacles. Owner decisions 2026-10-27, notes/workshop_receptacles.md.
#
# Elevations are storey-relative: landing deck top + 12". ST-B2M's decks sit at 51 1/16"
# (east, lower landing) and 58 3/8" (west, upper landing) over the basement slab; ST-M2S's
# level landing is 61 1/4" over the main floor.

from typehaus import DeviceKind, ElectricalDevice, Mount, MountKind, deg, inch
from typehaus.model import Location, WallAttachment

STAIR_BASEMENT = [
    # W-B-N2 runs east to west from x=18'-0": 28" is x=15'-8 1/2", the lower (east) landing.
    ElectricalDevice(uid="EWK9TNBGRH", tag="ED-B-STAIR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GUIDE", circuit="CKT-RC-BSMT", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(63)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-N2", face="left", distance_from_start=inch(28),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # 71" is x=12'-1", the upper (west) landing, whose deck is 7 5/16" higher.
    ElectricalDevice(uid="AVTBXKVZWX", tag="ED-B-STAIR-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GUIDE", circuit="CKT-RC-BSMT", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(70.4)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-N2", face="left", distance_from_start=inch(71),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Tread night lights (2026-10-31): a mark K sconce on each face of W-B-WELL, 14-15" over
    # the fourth tread of each flight (lower 28.9", upper 80.4" AFF). Own Matter relay 6 1/2"
    # north of ED-B-STAIR-SW, in the bay past the partition's head stud, on CKT-LT-BSMT; HA runs them dusk to dawn on the stair's motion, so the
    # 3-way cans stay the "on" light.
    ElectricalDevice(uid="WQM6PM2543", tag="ED-B-STAIR-NIGHT1", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-STAIR", circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-NIGHT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-WELL", face="right", distance_from_start=inch(40),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="BVVKMV2S3T", tag="ED-B-STAIR-NIGHT2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-STAIR", circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-NIGHT-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-WELL", face="left", distance_from_start=inch(41),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="YBYP0465RJ", tag="ED-B-STAIR-NIGHT-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER", circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-WELL", face="right", distance_from_start=inch(10.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

STAIR_MAIN = [
    # ST-M2S's level landing, east of EQ-M-HP3-STAIR (x 10'-7"..13'-5"); 42" is x=14'-6".
    ElectricalDevice(uid="9BNPRT11G5", tag="ED-M-STAIR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GUIDE", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(73.2)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N2", face="left", distance_from_start=inch(42),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

STAIR_ATTIC = [
    # Standard duplex on the study wall beside the attic stair; retained at 12" AFF.
    ElectricalDevice(uid="PNBZMKXZCC", tag="ED-A-STAIR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-15", circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C1", face="right", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

# No room=: an exterior placeable names none (the wet-location checks rely on it).
EXTERIOR_MAIN = [
    # Front: north face of W-M-N2 on the entry bridge side of D-M-ENTRY, 18" up.
    ElectricalDevice(uid="1XK99YN2KR", tag="ED-M-FRONT-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N2", face="right", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Rear: south face of W-M-S2 between D-M-BALC and WIN-M-LIV-S2, x=24'-7".
    ElectricalDevice(uid="7QVNCGSY39", tag="ED-M-REAR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S2", face="right", distance_from_start=inch(79),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
