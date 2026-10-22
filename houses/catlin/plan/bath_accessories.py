# haus: editable
# Mount.elevation is above FINISHED floor; WallBacking.elevation is above wall framing base.
# Bare hardware; tests reserve an 8.11 x 6 x 5.5 in. loaded envelope and 33.44 in. pivot top.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment, deg, inch, pt


_HOLDER_BASE = inch(25.33)
_PAD_BASE = inch(23.25)

BASEMENT_BATH_ACCESSORIES = [
    Furniture(uid="TPBBATH001", tag="FURN-B-BATH-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-B-BATH", mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-B-STR3B", face="left", distance_from_start=inch(38.5625),
                  rotation_offset=deg(-180)))),
]

MAIN_BATH_ACCESSORIES = [
    Furniture(uid="TPMBATH101", tag="FURN-M-BATH1-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-M-BATH1", mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W2", face="left", distance_from_start=inch(18.865),
                  rotation_offset=deg(-180)))),
    Furniture(uid="TPMBATH201", tag="FURN-M-BATH2-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-M-BATH2", mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W3", face="left", distance_from_start=inch(41.385),
                  rotation_offset=deg(-180)))),
]

SECOND_BATH_ACCESSORIES = [
    Furniture(uid="TPSBATH101", tag="FURN-S-BATH1-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-CH-S", face="left", distance_from_start=inch(6),
                  rotation_offset=deg(-180)))),
    # Explicit point, checked against the west side of the vanity. A host ref records
    # support, not a transform; moving the vanity requires moving holder and pad together.
    Furniture(uid="TPSBATH201", tag="FURN-S-SUITEBATH-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-S-SUITEBATH", host_fixture_ref="FX-S-SUITEBATH-LAV",
              position=pt(inch(148.83), inch(248.25)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE)),
    Furniture(uid="TPSBATH202", tag="FURN-S-SUITEBATH-TP-PAD", type_ref="FT-TP-CABINET-BACKING-12",
              room="RM-S-SUITEBATH", host_fixture_ref="FX-S-SUITEBATH-LAV",
              position=pt(inch(151.625), inch(250.25)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=_PAD_BASE,
                          recessed_into_host_surface=True)),
]

ATTIC_BATH_ACCESSORIES = [
    Furniture(uid="TPABATH001", tag="FURN-A-STUBATH-TP", type_ref="FT-MOEN-ALIGN-TP",
              room="RM-A-STUBATH", host_fixture_ref="FX-A-STUBATH-LAV",
              position=pt(inch(150.955), inch(253)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=_HOLDER_BASE)),
    Furniture(uid="TPABATH002", tag="FURN-A-STUBATH-TP-PAD", type_ref="FT-TP-CABINET-BACKING-12",
              room="RM-A-STUBATH", host_fixture_ref="FX-A-STUBATH-LAV",
              position=pt(inch(153.75), inch(253.625)), rotation=deg(-90),
              mount=Mount(kind=MountKind.WALL, elevation=_PAD_BASE,
                          recessed_into_host_surface=True)),
]
