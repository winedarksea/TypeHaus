# haus: editable
# Mount elevations are above the room's finished floor, to the bottom of bare hardware.
# Cabinet positions are explicit, with regression checks against their named vanity.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment, deg, inch, pt

BASEMENT_TOWEL_ACCESSORIES = [
    Furniture(
        uid="TWBBHAND01",
        tag="FURN-B-BATH-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-B-BATH",
        mount=Mount(kind=MountKind.WALL, elevation=inch(47.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-B-STR2",
                face="left",
                distance_from_start=inch(19.375),
                rotation_offset=deg(-180),
            )
        ),
    ),
    # Dry side of the sauna wall, just north of its outward-opening door. Inside, the
    # shower, heater and benches leave no useful dry bar location or hanging drop.
    Furniture(
        uid="TWBBATH001",
        tag="FURN-B-SAUNA-BATH-TOWEL",
        type_ref="FT-MOEN-ALIGN-BATH-TOWEL",
        room="RM-B-GYM",
        mount=Mount(kind=MountKind.WALL, elevation=inch(53.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-B-CS",
                face="left",
                distance_from_start=inch(31.5),
                rotation_offset=deg(-180),
            )
        ),
    ),
]

MAIN_TOWEL_ACCESSORIES = [
    # Alongside the basin, clear of the WC access panel and the basin's left edge.
    Furniture(
        uid="TWMBHAND01",
        tag="FURN-M-BATH1-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-M-BATH1",
        mount=Mount(kind=MountKind.WALL, elevation=inch(47.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-M-HS1",
                face="left",
                distance_from_start=inch(39),
                rotation_offset=deg(-180),
            )
        ),
    ),
    Furniture(
        uid="TWMBHAND02",
        tag="FURN-M-BATH2-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL-CH",
        room="RM-M-BATH2",
        host_fixture_ref="FX-M-BATH2-SINK",
        position=pt(inch(18.25), inch(207.915)),
        rotation=deg(180),
        mount=Mount(kind=MountKind.WALL, elevation=inch(29.33)),
    ),
    Furniture(
        uid="TWMBPAD001",
        tag="FURN-M-BATH2-HAND-TOWEL-PAD",
        type_ref="FT-TOWEL-CABINET-BACKING-12",
        room="RM-M-BATH2",
        host_fixture_ref="FX-M-BATH2-SINK",
        position=pt(inch(17.5), inch(205.25)),
        mount=Mount(kind=MountKind.WALL, elevation=inch(28.5), recessed_into_host_surface=True),
    ),
    # The gap between vanity and window is too short for an 18 in. bar plus its posts.
    Furniture(
        uid="TWMBHOOK01",
        tag="FURN-M-BATH2-BATH-TOWEL",
        type_ref="FT-MOEN-ALIGN-TOWEL-HOOK-CH",
        room="RM-M-BATH2",
        mount=Mount(kind=MountKind.WALL, elevation=inch(63.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-M-W3",
                face="left",
                distance_from_start=inch(52.5),
                rotation_offset=deg(-180),
            )
        ),
    ),
    # A matched pair centred along the tub. The south post is on the continuous BA2E2 face.
    Furniture(
        uid="VT1XT3DST9", tag="FURN-M-BATH2-TUB-TOWEL-S", type_ref="FT-MOEN-ALIGN-BATH-TOWEL-CH",
        room="RM-M-BATH2", mount=Mount(kind=MountKind.WALL, elevation=inch(53.33)),
        location=Location(attachment=WallAttachment(
            wall_ref="W-M-BA2E", face="right", distance_from_start=inch(49.385),
            rotation_offset=deg(0))),
    ),
    Furniture(
        uid="RDPJANWDRK", tag="FURN-M-BATH2-TUB-TOWEL-N", type_ref="FT-MOEN-ALIGN-BATH-TOWEL-CH",
        room="RM-M-BATH2", mount=Mount(kind=MountKind.WALL, elevation=inch(53.33)),
        location=Location(attachment=WallAttachment(
            wall_ref="W-M-BA2E", face="right", distance_from_start=inch(21.385),
            rotation_offset=deg(0))),
    ),
]

SECOND_TOWEL_ACCESSORIES = [
    # Opposite the two sinks, within reach across the narrow vanity alcove. Side walls
    # carry a window and a cased opening; these bars preserve both operations.
    Furniture(
        uid="TWSVHAND01",
        tag="FURN-S-VANITY-HAND-TOWEL1",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-S-VANITY",
        mount=Mount(kind=MountKind.WALL, elevation=inch(47.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-S-SN1",
                face="left",
                distance_from_start=inch(22.375),
                rotation_offset=deg(-180),
            )
        ),
    ),
    Furniture(
        uid="TWSVHAND02",
        tag="FURN-S-VANITY-HAND-TOWEL2",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-S-VANITY",
        mount=Mount(kind=MountKind.WALL, elevation=inch(47.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-S-SN1",
                face="left",
                distance_from_start=inch(52.375),
                rotation_offset=deg(-180),
            )
        ),
    ),
    # South side of the vanity, beyond the entry leaf's swing, below the counter.
    Furniture(
        uid="TWSBHAND01",
        tag="FURN-S-BATH1-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-S-BATH1",
        host_fixture_ref="FX-S-BATH1-LAV",
        position=pt(inch(106.125), inch(354.835)),
        mount=Mount(kind=MountKind.WALL, elevation=inch(29.33)),
    ),
    Furniture(
        uid="TWSBPAD001",
        tag="FURN-S-BATH1-HAND-TOWEL-PAD",
        type_ref="FT-TOWEL-CABINET-BACKING-12",
        room="RM-S-BATH1",
        host_fixture_ref="FX-S-BATH1-LAV",
        position=pt(inch(106.125), inch(357.625)),
        mount=Mount(kind=MountKind.WALL, elevation=inch(28.5), recessed_into_host_surface=True),
    ),
    # No bar-sized gap remains between the linen cabinet and the west window casing.
    Furniture(
        uid="TWSBHOOK01",
        tag="FURN-S-BATH1-BATH-TOWEL",
        type_ref="FT-MOEN-ALIGN-TOWEL-HOOK",
        room="RM-S-BATH1",
        mount=Mount(kind=MountKind.WALL, elevation=inch(63.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-S-W1",
                face="left",
                distance_from_start=inch(39.875),
                rotation_offset=deg(-180),
            )
        ),
    ),
    # North end of the west vanity side, separated horizontally and vertically from TP.
    Furniture(
        uid="TWSSHAND01",
        tag="FURN-S-SUITEBATH-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-S-SUITEBATH",
        host_fixture_ref="FX-S-SUITEBATH-LAV",
        position=pt(inch(148.835), inch(258.5)),
        rotation=deg(-90),
        mount=Mount(kind=MountKind.WALL, elevation=inch(31.83)),
    ),
    Furniture(
        uid="TWSSPAD001",
        tag="FURN-S-SUITEBATH-HAND-TOWEL-PAD",
        type_ref="FT-TOWEL-CABINET-BACKING-12",
        room="RM-S-SUITEBATH",
        host_fixture_ref="FX-S-SUITEBATH-LAV",
        position=pt(inch(151.625), inch(257.625)),
        rotation=deg(-90),
        mount=Mount(kind=MountKind.WALL, elevation=inch(31), recessed_into_host_surface=True),
    ),
    # North of the existing robe pegs; a separate towel has its full hanging drop.
    Furniture(
        uid="TWSSBATH01",
        tag="FURN-S-SUITEBATH-BATH-TOWEL",
        type_ref="FT-MOEN-ALIGN-BATH-TOWEL",
        room="RM-S-SUITEBATH",
        mount=Mount(kind=MountKind.WALL, elevation=inch(53.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-S-DC2",
                face="right",
                distance_from_start=inch(52),
                rotation_offset=deg(0),
            )
        ),
    ),
]

ATTIC_TOWEL_ACCESSORIES = [
    Furniture(
        uid="TWABHAND01",
        tag="FURN-A-STUBATH-HAND-TOWEL",
        type_ref="FT-MOEN-ALIGN-HAND-TOWEL",
        room="RM-A-STUBATH",
        mount=Mount(kind=MountKind.WALL, elevation=inch(47.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-A-HALL-S",
                face="right",
                distance_from_start=inch(22),
                rotation_offset=deg(0),
            )
        ),
    ),
    # 51 in. AFF clears the west roof rake and reuses BK-A-BATH-S behind both posts.
    Furniture(
        uid="TWABBATH01",
        tag="FURN-A-STUBATH-BATH-TOWEL",
        type_ref="FT-MOEN-ALIGN-BATH-TOWEL",
        room="RM-A-STUBATH",
        mount=Mount(kind=MountKind.WALL, elevation=inch(50.33)),
        location=Location(
            attachment=WallAttachment(
                wall_ref="W-A-BATH-S",
                face="left",
                distance_from_start=inch(23.5),
                rotation_offset=deg(-180),
            )
        ),
    ),
]
