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
    ElectricalDeviceType,
    Mount,
    MountKind,
    Service,
    ServicePort,
    deg,
    ft,
    inch,
    pt,
)

DEVICE_TYPES = (
    # `service_amps` is what the 220.82 demand estimate is compared against, and `spaces`
    # is what `electrical.panel_spaces` reconciles the circuit slots against. A 20-space
    # 100A load centre is the smallest enclosure this house could be built on, and it
    # leaves spare positions for the radon fan's future circuit and for the kitchen and
    # bathroom this template does not yet have.
    ElectricalDeviceType(tag="ED-T-PANEL", name="100A load centre, 20 spaces",
                         footprint=(inch(14), inch(4)), height=ft(2),
                         plan_symbol="panel", spaces=20, service_amps=100,
                         ports=(ServicePort(tag="service", service=Service.POWER_240,
                                            position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-SWITCH", name="Wall switch",
                         footprint=(inch(4), inch(2)), height=inch(2),
                         ports=(ServicePort(tag="power", service=Service.POWER_120,
                                            position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE", name="Receptacle, 125V duplex",
                         footprint=(inch(4), inch(2)), height=inch(2), nema="5-20R",
                         ports=(ServicePort(tag="power", service=Service.POWER_120,
                                            position=(ft(0), ft(0), ft(0))),)),
)

# --- main storey -------------------------------------------------------------------
#
# The panel stands on the west wall at the north end of RM-Main, the corner furthest from
# the front door and closest to where a service drop would land. A load centre in a living
# room is unusual but legal — NEC 240.24(D) keeps overcurrent devices out of clothes
# closets and bathrooms, and this house has neither. Give the template a utility room and
# this is the first thing that should move into it.
PANEL = [
    ElectricalDevice(uid="95YK2Q5XDP", tag="ED-PANEL", kind=DeviceKind.PANEL, type_ref="ED-T-PANEL",
                     position=pt(inch(3), ft(17)), room="RM-Main", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
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
                     position=pt(ft(6, 6), inch(2)), room="RM-Main", circuit="CKT-LIGHTS",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# NEC 210.52(A): no point along the floor line of a wall space more than 6' from a
# receptacle, which is the same as saying no two more than 12' apart with the ends within
# 6' of a break. D-101 is the only break in RM-Main's 87'-7" perimeter, leaving one wall
# space of 84'-7"; eight receptacles at about 10'-6" centres is the smallest set that
# covers it, and `electrical.receptacle_spacing` measures exactly that.
MAIN_RECEPTACLES = [
    ElectricalDevice(uid="6840M32QNF", tag="ED-Main-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(inch(2), ft(2, 6)),
                     room="RM-Main", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="BSDJA0DF9S", tag="ED-Main-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(inch(2), ft(13)),
                     room="RM-Main", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="TY97N1DXAQ", tag="ED-Main-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(3, 6), ft(19, 10)),
                     room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="EEKAB1X09G", tag="ED-Main-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(14), ft(19, 10)),
                     room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="GZB0GVK7QY", tag="ED-Main-RC5", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(23, 10), ft(19)),
                     room="RM-Main", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="KT190FCTGH", tag="ED-Main-RC6", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(23, 10), ft(8, 6)),
                     room="RM-Main", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="DJSGNVHH9E", tag="ED-Main-RC7", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(22), inch(2)),
                     room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="06D5MW2R6T", tag="ED-Main-RC8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(11, 6), inch(2)),
                     room="RM-Main", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
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
                     position=pt(ft(8, 3), ft(14, 2)), room="RM-Upper",
                     circuit="CKT-LIGHTS", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# Same 6' rule, one break (D-201), 84'-11" of wall space around an L — which needs nine
# rather than eight because the two partition legs put two corners close together.
UPPER_RECEPTACLES = [
    ElectricalDevice(uid="XZG3KBEVJY", tag="ED-Upper-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(11), ft(19, 10)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="6GBZ02ZQQF", tag="ED-Upper-RC2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(21), ft(19, 10)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="T50Z128HSD", tag="ED-Upper-RC3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(23, 10), ft(13, 6)),
                     room="RM-Upper", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="EJ75QKP365", tag="ED-Upper-RC4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(23, 10), ft(5)),
                     room="RM-Upper", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CHCT0K8BNN", tag="ED-Upper-RC5", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(20), inch(2)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="Y7S76GDZ60", tag="ED-Upper-RC6", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(10), inch(2)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="P1AB6DTNWK", tag="ED-Upper-RC7", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(1, 6), inch(2)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="57X4E8PS86", tag="ED-Upper-RC8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(inch(2), ft(6)),
                     room="RM-Upper", circuit="CKT-RECEPT", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # The landing's south partition W-206, bedroom side.
    ElectricalDevice(uid="B4G7497Z1G", tag="ED-Upper-RC9", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-RECEPTACLE", position=pt(ft(5, 6), ft(11, 10)),
                     room="RM-Upper", circuit="CKT-RECEPT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]

UPPER_DEVICES = [*UPPER_LIGHTING, *UPPER_RECEPTACLES]
