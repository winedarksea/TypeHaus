# haus: editable
# Selected bathroom mirrors and lights; products/types in mirror_types.py.
# Mount elevations are BODY BOTTOMS above finished floor, not electrical box centres.
# Karlie shades face down; the junction box is 5.5 in. above its body bottom.
from typehaus import DeviceKind, ElectricalDevice, Furniture, Location, Mount, MountKind, WallAttachment, WallBacking
from typehaus.model import deg, inch

BASEMENT_MIRRORS = [
    Furniture(uid="E63FE4725D", tag="FURN-B-BATH-MIRROR", type_ref="FT-MIRROR-KOHLER-26052-BNL", room="RM-B-BATH",
            mount=Mount(kind=MountKind.WALL, elevation=inch(40)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-B-CW2", face="left", distance_from_start=inch(24),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="2455867868", tag="ED-B-BATH-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-3-BN", room="RM-B-BATH",
            circuit="CKT-LT-BACKUP", controlled_by=("ED-B-BATH-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(76.1875)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-B-CW2", face="left", distance_from_start=inch(24),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    WallBacking(uid="E4237B788F", tag="BK-B-CW2-MIRROR-LOW", wall_ref="W-B-CW2", face="left",
        start=inch(16.75), length=inch(14.5),
        elevation=inch(40), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="mirror body bottom"),
    WallBacking(uid="19EA8A2D8F", tag="BK-B-CW2-MIRROR-HANG", wall_ref="W-B-CW2", face="left",
        start=inch(16.75), length=inch(14.5),
        elevation=inch(64), height=inch(11.25), profile="2x12",
        material_ref="spf", purpose="K-26052 portrait hanging rail, about 69 in. AFF"),
    WallBacking(uid="35159AF246", tag="BK-B-CW2-MIRROR-LIGHT", wall_ref="W-B-CW2", face="left",
        start=inch(16.75), length=inch(14.5),
        elevation=inch(78), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="Karlie box at 81 11/16 in. AFF"),

]

MAIN_MIRRORS = [
    Furniture(uid="9E8720B4F1", tag="FURN-M-BATH1-MIRROR", type_ref="FT-MIRROR-KOHLER-30638-CPL", room="RM-M-BATH1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-HS1", face="left", distance_from_start=inch(54.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTM000KAAA", tag="ED-M-BATH1-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-2-CM", room="RM-M-BATH1",
            circuit="CKT-LT-MAIN", controlled_by=("ED-M-BATH1-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-HS1", face="left", distance_from_start=inch(54.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="4JFYZ9V9P7", tag="FURN-M-CLOSET-MIRROR", type_ref="FT-MIRROR-UMBRA-HUBBA-PILL", room="RM-M-CLOSET",
            mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-C2", face="left", distance_from_start=inch(18),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTM000QAAA", tag="ED-M-BATH2-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-MIRROR-DAY", room="RM-M-BATH2",
            circuit="CKT-LT-MAIN", controlled_by=("ED-M-BATH2-SW-DAY",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(80)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-W3", face="left", distance_from_start=inch(94.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="5AE57JENYW", tag="ED-M-BATH2-MIRROR-HALO", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-MIRROR-HALO-2700", room="RM-M-BATH2",
            circuit="CKT-BATH-ATTIC",
            mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-W3", face="left", distance_from_start=inch(94.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="783AC05790", tag="ED-M-BATH2-MIRROR-PLUG", kind=DeviceKind.RECEPTACLE,
            type_ref="ED-T-RECEPTACLE", room="RM-M-BATH2",
            circuit="CKT-BATH-ATTIC",
            mount=Mount(kind=MountKind.WALL, elevation=inch(64),
                        recessed_into_host_surface=True),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-W3", face="left", distance_from_start=inch(94.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    WallBacking(uid="440C21E67C", tag="BK-M-HS1-MIRROR-LOW", wall_ref="W-M-HS1", face="left",
        start=inch(48.75), length=inch(14.5),
        elevation=inch(40), height=inch(9.25), profile="2x10",
        material_ref="spf", purpose="plain arch bottom, north-face block"),
    WallBacking(uid="803899D7C4", tag="BK-M-HS1-MIRROR-HANG", wall_ref="W-M-HS1", face="left",
        start=inch(48.75), length=inch(14.5),
        elevation=inch(60), height=inch(11.25), profile="2x12",
        material_ref="spf", purpose="K-30638 rail 9 3/16 in. below arch top; north face"),
    WallBacking(uid="0E28571753", tag="BK-M-HS1-MIRROR-LIGHT", wall_ref="W-M-HS1", face="left",
        start=inch(48.75), length=inch(14.5),
        elevation=inch(80), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="Karlie junction box, north face"),

]

SECOND_MIRRORS = [
    Furniture(uid="F3A5227ADA", tag="FURN-S-BATH1-MIRROR", type_ref="FT-MIRROR-KOHLER-26050-BNL", room="RM-S-BATH1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BA-E1B", face="right", distance_from_start=inch(25.5),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000KAAA", tag="ED-S-BATH1-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-3-BN", room="RM-S-BATH1",
            circuit="CKT-LT-UPPER", controlled_by=("ED-S-BATH1-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(74.0625)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BA-E1B", face="right", distance_from_start=inch(25.5),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="71CDD3B4F5", tag="FURN-S-VANITY-MIRROR1", type_ref="FT-MIRROR-KOHLER-30638-BNL", room="RM-S-VANITY",
            mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="right", distance_from_start=inch(22.375),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000FAAA", tag="ED-S-VANITY-MIRROR1", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-2-BN", room="RM-S-VANITY",
            circuit="CKT-LT-UPPER", controlled_by=("ED-S-VANITY-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="right", distance_from_start=inch(22.375),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="3436262C8E", tag="FURN-S-VANITY-MIRROR2", type_ref="FT-MIRROR-KOHLER-30638-BNL", room="RM-S-VANITY",
            mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="right", distance_from_start=inch(52.375),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000GAAA", tag="ED-S-VANITY-MIRROR2", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-2-BN", room="RM-S-VANITY",
            circuit="CKT-LT-UPPER", controlled_by=("ED-S-VANITY-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="right", distance_from_start=inch(52.375),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000EAAA", tag="ED-S-SUITEBATH-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-2-BN", room="RM-S-SUITEBATH",
            circuit="CKT-LT-UPPER", controlled_by=("ED-S-SUITEBATH-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-SN3", face="right", distance_from_start=inch(50.5),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    WallBacking(uid="95329D8DEB", tag="BK-S-BD-N-MIRROR-HANG", wall_ref="W-S-BD-N", face="right",
        elevation=inch(60), height=inch(11.25), profile="2x12",
        material_ref="spf", purpose="two K-30638 hanging rails at about 64.8 in. AFF"),
    WallBacking(uid="958FE8500B", tag="BK-S-BD-N-MIRROR-LIGHT", wall_ref="W-S-BD-N", face="right",
        elevation=inch(80), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="Karlie junction boxes at 81.5 in. AFF"),
    WallBacking(uid="AE86C7623C", tag="BK-S-BA-E1B-MIRROR-HANG", wall_ref="W-S-BA-E1B", face="right",
        start=inch(16.75), length=inch(30.5),
        elevation=inch(60), height=inch(11.25), profile="2x12",
        material_ref="spf", purpose="K-26050 round hanging rail, below the glass head"),
    WallBacking(uid="EAF54D1E2C", tag="BK-S-BA-E1B-MIRROR-LIGHT", wall_ref="W-S-BA-E1B", face="right",
        start=inch(16.75), length=inch(30.5),
        elevation=inch(78), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="Karlie junction box at 79 9/16 in. AFF"),
    WallBacking(uid="18CE157467", tag="BK-S-SN3-MIRROR-LIGHT", wall_ref="W-S-SN3", face="right",
        start=inch(40.75), length=inch(22.5),
        elevation=inch(80), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="suite Karlie junction box at 81.5 in. AFF"),

]

ATTIC_MIRRORS = [
    Furniture(uid="D88442DB2C", tag="FURN-A-STUBATH-MIRROR", type_ref="FT-MIRROR-KOHLER-31367-BNL", room="RM-A-STUBATH",
            mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-A-HALL-S", face="right", distance_from_start=inch(44.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="3W86JZVH61", tag="ED-A-STUBATH-MIRROR", kind=DeviceKind.LIGHT,
            type_ref="ED-T-LT-KARLIE-2-BN-ATTIC", room="RM-A-STUBATH",
            circuit="CKT-LT-UPPER", controlled_by=("ED-A-STUBATH-SW",),
            mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-A-HALL-S", face="right", distance_from_start=inch(44.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    WallBacking(uid="41F8E99F9C", tag="BK-A-HALL-S-MIRROR-LOW", wall_ref="W-A-HALL-S", face="right",
        start=inch(32.75), length=inch(30.5),
        elevation=inch(48), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="plain round mirror body bottom"),
    WallBacking(uid="43529FFBED", tag="BK-A-HALL-S-MIRROR-HANG", wall_ref="W-A-HALL-S", face="right",
        start=inch(32.75), length=inch(30.5),
        elevation=inch(64), height=inch(7.25), profile="2x8",
        material_ref="spf", purpose="K-31367 mirror fastening"),

]
