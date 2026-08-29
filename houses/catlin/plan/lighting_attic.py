# haus: editable
# Catlin lighting — the ATTIC storey, split out of plan/lighting.py on 2026-08-29.
#
# The file was 1,158 lines against AGENTS.md's 500 and the guest studio added to it. Split by
# STOREY rather than by device kind, which is how a reader looks for a fitting and how
# plan/manifest.py already consumes these lists — it takes one `*_LIGHTING` tuple per storey,
# so moving one out is a manifest import change and nothing else.
#
# ** AN EDITABLE FILE CANNOT `from plan import ...` ** — the dialect forbids it — so this module
# imports only from `typehaus` and the manifest composes. Same reason plan/mep.py is an
# aggregator and is not editable.
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
from typehaus.model import m

ATTIC_LIGHTING = [
    # Was RM-A-DEN's: a 43 ft2 nook with no wall on the way in to put a switch on, so the
    # fixture carries its own (notes: "spotlight sconce with switch on sconce"). No
    # `controlled_by`, deliberately — `integral_switch` on the type exempts it from
    # `electrical.lighting_controls`. Back at x=14'-0" (2026-07-31) after WIN-A-S-JUL-W's
    # width settled at 18": the original position clears the window jamb by 1'-11".
    #
    # ** REASSIGNED TO THE WEST LOFT 2026-08-27 ** when the Den was deleted and its space
    # folded into the west loft. Position, type, mount, elevation and circuit are all
    # unchanged — the wall it hangs on (the south gable at x=14'-0") did not move, only the
    # room claim around it did. The integral switch is kept: see the type's note.
    # Re-pointed again on 2026-08-29 when that loft became RM-A-STUDIO — same wall, same
    # 600 lm, and those lumens are now counted toward R303.1 Exception 1 (see below).
    ElectricalDevice(uid="QTA0001AAA", tag="ED-A-STUDIO-SCONCE", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(0, 8.625)), type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),

    ElectricalDevice(uid="QTA0002AAA", tag="ED-A-EAST-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0003AAA", tag="ED-A-EAST-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0004AAA", tag="ED-A-EAST-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(28)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),

    # RM-A-STUDY: the second of the notes' two studies. Its spot sconce goes on the knee
    # wall, which is only 5' tall — hence a 4' mount, not the 6' used downstairs. The
    # stair sconce lights ST-S2A's landing at the top of the flight.
    ElectricalDevice(uid="QTA0005AAA", tag="ED-A-STUDY-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(3)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY",
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTA0006AAA", tag="ED-A-STUDY-SPOT", kind=DeviceKind.LIGHT,
                     position=pt(ft(35, 3.375), ft(2, 3)), type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(-90),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
    ElectricalDevice(uid="QTA0007AAA", tag="ED-A-STUDY-STAIR-SC", kind=DeviceKind.LIGHT,
                     position=pt(m(8.32505), m(0.222461)), type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", rotation=deg(180),
                     controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),

    # ** EVERY TAG IN THIS BLOCK WAS RENAMED ED-A-WEST-* -> ED-A-STUDIO-* ON 2026-08-29 **
    # (and ED-A-DEN-SCONCE with them), uids untouched, and two of the four cans left the studio
    # altogether. This is not tidying: `electrical.room_lighting` matches devices to a room by
    # NAME — `ED-{room.tag[3:]}-*` — so a room renamed RM-A-STUDIO has no lights at all until
    # its fittings are renamed with it, and a fitting that ends up in the bath or the pocket
    # must carry THAT room's prefix or it counts toward the wrong one. The three prefixes
    # ED-A-STUDIO-, ED-A-STUBATH- and ED-A-POCKET- are disjoint, which is also why the bath is
    # tagged RM-A-STUBATH rather than RM-A-STUDIO-BATH (see storeys/attic_studio.py).
    #
    # ** THE LUMEN COUNT IS R303.1 EXCEPTION 1, AND IT IS THE REASON FOR THE ADDED CANS. **
    # The studio's glazing is 21.33 sf against 0.08 x 356.6 = 28.52 sf, and openable is 10.67
    # against 14.26 — both short, and NO GLAZING IS ADDED because the south gable's
    # six-opening mirror about x=18' is not negotiable (houses/catlin/CLAUDE.md). So the room
    # takes Exception 1, and four of `_exception_1`'s gates matter here:
    #   * a luminaire must be ASSIGNED to the room — `room=` is the whole match, position is
    #     never read;
    #   * every one must state `lumens` on its LuminaireType or the verdict is UNKNOWN rather
    #     than PASS (ED-T-LT-CAN4 = 900, ED-T-LT-SPOT-SW = 600);
    #   * ** a LightRun COUNTS FOR NOTHING ** — `_room_lumens` excludes cove and tape runs by
    #     its own docstring. Point luminaires only;
    #   * 6 fc delivered, computed as lumens x 0.60 x 0.80 / area_sf — i.e. LUMENS >= 12.5 x
    #     the room's square feet, which at 356.6 sf is 4,457 lm.
    # Two inherited cans plus the sconce is 2,400 lm = 2.9 fc and FAILS. Five cans plus the
    # sconce is 5,100 lm = 6.9 fc, which passes by 15%. SIX cans plus the sconce is 6,000 lm =
    # 8.08 fc, and that is what is specified: it survives the room growing 30%, which is what a
    # margin measured against a RESOLVED area ought to do. 80 VA on CKT-LT-UPPER.
    ElectricalDevice(uid="QTA0008AAA", tag="ED-A-STUDIO-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(10)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    # ** MOVED (9'-0", 20'-0") -> (7'-0", 20'-0"). ** Its old station is 4 1/8" west of
    # W-A-STU-W's face — a 5" housing half-buried in a wall.
    ElectricalDevice(uid="QTA000BAAA", tag="ED-A-STUDIO-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(7), ft(20)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    # The four added cans: two more down the ridge side at 9'-8" where the roof is high, two
    # out at 8'-0" toward the knee wall — the same two-band rhythm the room already had.
    ElectricalDevice(uid="QP7K1NEC12", tag="ED-A-STUDIO-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(3)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="KR49G4VP4A", tag="ED-A-STUDIO-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(14), ft(16)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="6M2C9K60B8", tag="ED-A-STUDIO-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(7), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="7QXE07XJ69", tag="ED-A-STUDIO-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(7), ft(13)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO",
                     controlled_by=("ED-A-STUDIO-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    # On W-A-C1B's west face at 6'-0", position unchanged: the two centre-wall segments are
    # collinear, but the wall south of y=5'-7" faces RM-A-STUDY and the studio does not start
    # until that line. A station 5" further south is a switch in the wrong room.
    ElectricalDevice(uid="QTA000CAAA", tag="ED-A-STUDIO-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(6)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDIO", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # ** THIS CAN BECAME THE BATH'S LIGHT AND WAS RETYPED WET-LISTED. ** Its station was inside
    # the bath box, so it moved with the room rather than against it — and a recessed can over
    # a 36" shower pan is a damp/wet location, which is what ED-T-LT-CAN4-WET is for. Same
    # 900 lm, so the studio's own count is unaffected: this fitting is not part of the 6,000.
    ElectricalDevice(uid="QTA0009AAA", tag="ED-A-STUBATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 9), ft(19, 6)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-A-STUBATH",
                     controlled_by=("ED-A-STUBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9),
                                 recessed_into_host_surface=True)),
    # On W-A-BATH-S's north face, east of D-A-STUBATH's leaf (which parks x 11'-3 5/8" to
    # 13'-9 5/8") — the wall you reach for on the way in. It was first put on W-A-STU-W beside
    # the lavatory, and `test_wall_mounted_devices_resolve_against_a_wall_face` reported it
    # floating 1.6" off that face; the door wall is both the better station and the one whose
    # finish face the house's standard 1" box offset lands on cleanly.
    ElectricalDevice(uid="DD20R7F44T", tag="ED-A-STUBATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(14, 3), ft(17, 7.375)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-STUBATH",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
    # ** AND THIS ONE BECAME THE POCKET'S. ** Its station (14'-0", 30'-0") is inside FO-A-HALL
    # — open to the roof, with no ceiling to recess into. (5'-0", 30'-0") puts it over the
    # storage pocket, which wants one anyway: IRC M1305.1.3 asks for a light at the ERV
    # appliance, and a STORAGE room is graded for none.
    ElectricalDevice(uid="QTA000AAAA", tag="ED-A-POCKET-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-A-POCKET",
                     controlled_by=("ED-A-POCKET-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="G5RDBXPZVD", tag="ED-A-POCKET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(22, 0.625)), type_ref="ED-T-SWITCH",
                     circuit="CKT-LT-UPPER", room="RM-A-POCKET", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46))),
]
