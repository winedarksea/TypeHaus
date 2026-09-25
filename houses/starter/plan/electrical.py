# haus: editable
# The starter's electrical package — the smallest one a house can actually be wired from.
#
# Three product types, one panel, and a light + switch + NEC 210.52 receptacles in each of
# the two habitable rooms. The panel schedule itself is `plan/circuits.py`; devices join to
# it by naming a circuit tag, and `electrical.circuit_refs` reconciles the two directions.
#
# Why this exists at all: `plan/mep.py` has to carry ED-RADON-FAN-JB, because MN Rules
# 1303.2402 subpart 6 requires a box for the future radon fan in every new Minnesota
# dwelling. Both `electrical.room_lighting` and `electrical.receptacle_spacing` gate on
# "does this plan model electrical at all", so that one mandatory box flipped them from
# "not modeled" to "modeled and incomplete", and the template shipped with four advisory
# FAILs. The honest answer is to model the rest, not to loosen the checks.
#
# `electrical.room_lighting` matches a device to a room by tag: RM-Main's devices are
# ED-Main-*, RM-Upper's are ED-Upper-*. The landing (RM-Upper-Hall) is a HALLWAY and
# therefore not a habitable room, so it is graded by neither check and carries no device
# here — a real house would light it, and the tag to use would be ED-Upper-Hall-*.
#
# A device position is a *face* position, the same convention `houses/catlin` uses: the
# point sits about half the device's depth off the finish plane, so a receptacle authored
# on the wall axis would bury itself in the studs. The finish faces resolve at 0.053' in
# from each node line, i.e. x/y = 0.053' on the south and west, 19.947' on the north and
# 23.947' on the east; every wall device below sits an inch or so off the face it serves.

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

# --- main storey -------------------------------------------------------------------
#
# The panel stands on the west wall at the north end of RM-Main, the corner furthest from
# the front door and closest to where a service drop would land. A load centre in a living
# room is unusual but legal — NEC 240.24(D) keeps overcurrent devices out of clothes
# closets and bathrooms, and this house has neither. Give the template a utility room and
# this is the first thing that should move into it.
PANEL = [
    ElectricalDevice(uid="95YK2Q5XDP", tag="ED-PANEL", kind=DeviceKind.PANEL, type_ref="ED-T-PANEL",
                     room="RM-Main", mount=Mount(kind=MountKind.WALL, elevation=ft(5)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-104", face="left", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# One ceiling fixture at the room's centre and one switch inside the front door. The
# fixture names its switch in `controlled_by`, which is what `electrical.lighting_controls`
# reconciles — a light that names nothing is a light nobody can turn off. Neither fixture
# carries a `type_ref`: a product with real photometrics is a house's decision, and an
# invented one would print a schedule row that is not true. That is also why
# `electrical.wet_location` and `advisory.dark_sky_lighting` stay UNKNOWN here; they grade
# luminaire *types*, and this template declares none.
MAIN_LIGHTING = [
    ElectricalDevice(uid="BQ16ZQHZPB", tag="ED-Main-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(12), ft(10)), room="RM-Main",
                     circuit="CKT-LIGHTS", controlled_by=("ED-Main-SW1",),
                     mount=Mount(kind=MountKind.CEILING)),
    # South wall, east of D-101's rough opening (x 3'..6') — inside the door, on the
    # latch side.
    ElectricalDevice(uid="VWVMA7CSJH", tag="ED-Main-SW1", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH",
                     room="RM-Main", circuit="CKT-LIGHTS",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-101", face="left", distance_from_start=inch(78),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

# NEC 210.52(A): no point along the floor line of a wall space more than 6' from a
# receptacle, which is the same as saying no two more than 12' apart with the ends within
# 6' of a break. D-101 is the only break in RM-Main's 87'-7" perimeter, leaving one wall
# space of 84'-7"; eight receptacles at about 10'-6" centres is the smallest set that
# covers it, and `electrical.receptacle_spacing` measures exactly that.
MAIN_RECEPTACLES = [
    ElectricalDevice(uid="6840M32QNF", tag="ED-Main-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-104", face="left", distance_from_start=inch(210),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="BSDJA0DF9S", tag="ED-Main-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-104", face="left", distance_from_start=inch(84),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="TY97N1DXAQ", tag="ED-Main-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-103", face="left", distance_from_start=inch(246),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="EEKAB1X09G", tag="ED-Main-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-103", face="left", distance_from_start=inch(120),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="GZB0GVK7QY", tag="ED-Main-RC5", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-102", face="left", distance_from_start=inch(228),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="KT190FCTGH", tag="ED-Main-RC6", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-102", face="left", distance_from_start=inch(102),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="DJSGNVHH9E", tag="ED-Main-RC7", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-101", face="left", distance_from_start=inch(264),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="06D5MW2R6T", tag="ED-Main-RC8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-101", face="left", distance_from_start=inch(138),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

MAIN_DEVICES = [*PANEL, *MAIN_LIGHTING, *MAIN_RECEPTACLES]

# --- upper storey ------------------------------------------------------------------
UPPER_LIGHTING = [
    # RM-Upper is an L — 24' x 12' with a 16' x 8' arm north of the landing — so the
    # fixture sits at the L's centroid rather than at the middle of a bounding box.
    ElectricalDevice(uid="K9F1ZPTPNR", tag="ED-Upper-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13), ft(9)), room="RM-Upper",
                     circuit="CKT-LIGHTS", controlled_by=("ED-Upper-SW1",),
                     mount=Mount(kind=MountKind.CEILING)),
    # Bedroom side of the landing partition W-205, south of D-201 (which runs y
    # 14'-8"..17'-4").
    ElectricalDevice(uid="MT08T1Q659", tag="ED-Upper-SW1", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH",
                     room="RM-Upper",
                     circuit="CKT-LIGHTS", mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-205", face="left", distance_from_start=inch(70),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# Same 6' rule, one break (D-201), 84'-11" of wall space around an L — which needs nine
# rather than eight because the two partition legs put two corners close together.
UPPER_RECEPTACLES = [
    ElectricalDevice(uid="XZG3KBEVJY", tag="ED-Upper-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-203", face="left", distance_from_start=inch(156),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="6GBZ02ZQQF", tag="ED-Upper-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-203", face="left", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="T50Z128HSD", tag="ED-Upper-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-202", face="left", distance_from_start=inch(162),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="EJ75QKP365", tag="ED-Upper-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-202", face="left", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CHCT0K8BNN", tag="ED-Upper-RC5", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-201", face="left", distance_from_start=inch(240),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="Y7S76GDZ60", tag="ED-Upper-RC6", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-201", face="left", distance_from_start=inch(120),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="P1AB6DTNWK", tag="ED-Upper-RC7", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-201", face="left", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="57X4E8PS86", tag="ED-Upper-RC8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-204B", face="left", distance_from_start=inch(72),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The landing's south partition W-206, bedroom side.
    ElectricalDevice(uid="B4G7497Z1G", tag="ED-Upper-RC9", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-206", face="left", distance_from_start=inch(30),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

UPPER_DEVICES = [*UPPER_LIGHTING, *UPPER_RECEPTACLES]
