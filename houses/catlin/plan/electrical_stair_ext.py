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
    # The head of ST-S2A, on the south face of W-A-SN: 18" is x=19'-6", west of the flight.
    ElectricalDevice(uid="PNBZMKXZCC", tag="ED-A-STAIR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GUIDE", circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-SN", face="right", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# No room=: an exterior placeable names none (the wet-location checks rely on it).
EXTERIOR_MAIN = [
    # Front: north face of W-M-N2 on the entry bridge side of D-M-ENTRY, 18" up.
    ElectricalDevice(uid="1XK99YN2KR", tag="ED-M-FRONT-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N2", face="right", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Rear: south face of W-M-S2 between D-M-BALC and WIN-M-LIV-S2, x=24'-7".
    ElectricalDevice(uid="7QVNCGSY39", tag="ED-M-REAR-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S2", face="right", distance_from_start=inch(79),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]
