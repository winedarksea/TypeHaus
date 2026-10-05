# haus: editable
# Living-room coffee-table power, recessed into the wood floor joist bay.

from typehaus import DeviceKind, ElectricalDevice, Mount, MountKind, inch, pt

MAIN_DEVICES = [
    # Under FURN-M-PUZZLE-COFFEE-TABLE, midway between the joists at y=96"/112".
    # Recessed Mount puts the body BELOW finished floor, preserving seated access.
    ElectricalDevice(
        uid="FRC001AAAA", tag="ED-M-LIVING-FLOOR-RC1", kind=DeviceKind.RECEPTACLE,
        type_ref="ED-T-FLOOR-RECEPTACLE-FLBR5420", room="RM-M-LIVING",
        position=pt(inch(327.9), inch(104)), circuit="CKT-RC-MAIN",
        mount=Mount(kind=MountKind.FLOOR, elevation=inch(0),
                    recessed_into_host_surface=True),
    ),
]
