# haus: editable
# Catlin lighting — the SECOND storey.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    LightRun,
    Mount,
    MountKind,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment, m

# --- Second storey --------------------------------------------------------------------
SECOND_LIGHTING = [
    # Two straight shadow-gap legs in SF-S-DUCT's underside (owner, 2026-11-09): no U, no
    # south crossing, no north return. The board stops 5/8" short of each wall (DRYWALL-
    # STANDARD, #103); the bead is the board's depth, so nothing rises into the 2x2 rungs, and
    # the resolver derives the beads off these paths (the north bulkhead's Z bead is gone).
    # West leg (-GAP, ED-S-HALL-LT-PSU): x=18'-6" from y=9'-7" to 22'-4", where W-S-C2C (the
    # suite bath) ends at the stair opening: 12.75 ft. East leg (-GAP2, -PSU2): x=21'-6" from
    # y=9'-7" to the north bulkhead at 27'-6", beside the closet: 17.9 ft.
    # Tunable white (E6) since 2026-10-31: the controller holds a low 2700 K night preset that
    # HA recalls after dark while the plain 3-ways (2026-11-03) leave both drivers' 120 V on.
    LightRun(uid="QRS0001AAA", tag="LR-S-HALL-GAP", type_ref="ED-T-LT-STRIP24-TUNABLE",
             path=(pt(ft(18, 6), ft(9, 7)), pt(ft(18, 6), ft(22, 4))),
             room="RM-S-HALL", psu_ref="ED-S-HALL-LT-PSU", controller_ref="ED-S-HALL-LT-CTRL",
             controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
             soffit_ref="SF-S-DUCT", soffit_edge_offset=inch(0.3125),
             emission_side="left",
             mount=Mount(kind=MountKind.CEILING, elevation=inch(94.5))),
    LightRun(uid="6V6YZABYSN", tag="LR-S-HALL-GAP2", type_ref="ED-T-LT-STRIP24-TUNABLE",
             path=(pt(ft(21, 6), ft(27, 6)), pt(ft(21, 6), ft(9, 7))),
             room="RM-S-HALL", psu_ref="ED-S-HALL-LT-PSU2", controller_ref="ED-S-HALL-LT-CTRL2",
             controlled_by=("ED-S-HALL-SW", "ED-S-HALL-SW2"),
             soffit_ref="SF-S-DUCT", soffit_edge_offset=inch(0.3125),
             emission_side="left",
             mount=Mount(kind=MountKind.CEILING, elevation=inch(94.5))),
    # Both Class 2 HLG-100 (96 W) drivers and their GL-C-001P controllers are in RM-S-NCLOSET,
    # on the east wall (W-S-BW4's closet face), reachable from the closet floor. 12.75 ft / 17.9 ft at 3 W/ft x1.25 is 48 / 67 W. Each 24 V pair is
    # fed at its leg's NORTH end. East: straight out through the bulkhead, ~3 ft. West: 18 AWG
    # Class 2 through SF-S-DUCT along the east wall to y=22'-4", ~12 ft each way; at
    # 38 W (1.6 A) the pair drops ~0.3 V (1.3% of 24 V), then the tape's own run. The lead is
    # derived since 2026-11-17 (resolve/led_leads.py, decision #137) for its length, gauge and
    # drop; pull it before the board goes up, clear of DU-S-HP-SUITE-RET-LANE (x 251-257", up
    # at the ceiling board) in SF-S-DUCT.
    ElectricalDevice(uid="QTS0001AAA", tag="ED-S-HALL-LT-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-UPPER", room="RM-S-NCLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(66)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW4", face="left", distance_from_start=inch(16),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="RTFGRQ9WBV", tag="ED-S-HALL-LT-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-S-HALL-LT-PSU", room="RM-S-NCLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(66)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW4", face="left", distance_from_start=inch(32),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="PZY7PB1XX0", tag="ED-S-HALL-LT-PSU2", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-96-WE",
                     circuit="CKT-LT-UPPER", room="RM-S-NCLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(52)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW4", face="left", distance_from_start=inch(16),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="MW0FDQBB4F", tag="ED-S-HALL-LT-CTRL2", kind=DeviceKind.LED_CONTROLLER,
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-S-HALL-LT-PSU2", room="RM-S-NCLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(52)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW4", face="left", distance_from_start=inch(32),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The balcony at D-S-BALCONY (owner, 2026-11-09), mirroring the porch's pair on W-M-S2 in
    # the 18" between the door's east jamb and WIN-S-STUDY1: a WR GFCI with in-use cover (NEC
    # 210.52(E)(3), `code.NEC_210_52_E3_balcony_receptacles`), 18" above the deck, on
    # CKT-RC-SECOND (20 A AFCI, GFCI at the device); and one exterior sconce on a plain paddle
    # inside Study 2 at the door, CKT-LT-UPPER with the load it switches. No room= on either
    # outdoor fitting: the exterior classifiers place them geometrically.
    ElectricalDevice(uid="VA4Z7YCQDQ", tag="ED-S-BALCONY-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-S2", face="right", distance_from_start=inch(79),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="9MMKJPKNEW", tag="ED-S-BALCONY-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-EXT", circuit="CKT-LT-UPPER",
                     controlled_by=("ED-S-STUDY2-SW-BALCONY",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-S2", face="right", distance_from_start=inch(80),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="YJJ1BVX3AZ", tag="ED-S-STUDY2-SW-BALCONY", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-S2", face="left", distance_from_start=inch(79),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # No hall cans since 2026-10-31: the three that recessed into SF-S-DUCT sat inside
    # DU-S-HP-SUP. The LR-S-HALL-GAP shadow-gap cove lights the hall on these switches.
    # Both x's follow the hall face of W-S-BW1/BW2, plain half-board partitions since
    # 2026-10-23 (plan/storeys/second.py). Authored x is the face LESS 1" (box back on the
    # face, 2" box): 21'-8 1/8" - 1" = 21'-7 1/8".
    ElectricalDevice(uid="QTS0005AAA", tag="ED-S-HALL-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW1", face="left", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTS0006AAA", tag="ED-S-HALL-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW2", face="left", distance_from_start=inch(106),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-S-SUITE: the linear wall lamp over the bed is the feature light. The cans
    # (2026-10-31): ED-S-SUITE-LT over the desk ahead of its user, CAN2 on the bed's axis
    # between the dresser and the bed foot, CAN3 in the east aisle beside the bed's foot
    # half, CAN4 in the arm past the walk-in on ED-S-CLOSET-CAN1's x. None over the mattress.
    # y tracks W-S-SN1's south face (same station as ED-S-SUITE-RC5), the 8" staggered
    # sound wall.
    ElectricalDevice(uid="QTS0007AAA", tag="ED-S-SUITE-LAMP", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-WALL-LINEAR",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE", controlled_by=("ED-S-SUITE-LAMP-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SN1", face="right", distance_from_start=inch(59.875),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The lamp's own switch at the bed (2026-10-31), 46" AFF over the bed's east corner on
    # W-S-SN2: x=7'-7 1/2", west of the suite-face stud at 7'-10 1/2" and ~4" clear of
    # PR-M-WC-VENT rising in that wall at x=8'-2 1/2".
    ElectricalDevice(uid="BBVJNKQP5R", tag="ED-S-SUITE-LAMP-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", plate="reggio-sungold",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SN2", face="right", distance_from_start=inch(21),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS0008AAA", tag="ED-S-SUITE-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(14)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0009AAA", tag="ED-S-SUITE-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(8, 8.75), ft(16, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000AAAA", tag="ED-S-SUITE-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 9.5), ft(14)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITE",
                     controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # Centred on the shelf run, its trim 6" outside the 16" shelf's storage space (NEC 410.16).
    ElectricalDevice(uid="QTS000BAAA", tag="ED-S-CLOSET-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(13, 9.5), ft(11, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-CLOSET",
                     controlled_by=("ED-S-CLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000CAAA", tag="ED-S-CLOSET-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-UPPER", room="RM-S-CLOSET",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-DC1", face="right", distance_from_start=inch(35),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-S-SUITEBATH: the tub's can, on its long centreline 2.6" south of its middle, in
    # the same clear FS-ATTIC bay as ED-S-SUITEBATH-LT (plan/mep_electrical.py). It was
    # under PR-A-STUBATH-SH-DRAIN's trap at y 20'-6". Nothing grades this; re-measure after
    # a move. The mirror bar is on the north wall over FX-S-SUITEBATH-LAV.
    ElectricalDevice(uid="QTS000DAAA", tag="ED-S-SUITEBATH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(16, 5.625), ft(19, 4)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-SUITEBATH",
                     controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # No lit niche (owner, 2026-10-12): LR-S-NICHE and ED-S-NICHE-PSU are gone. A hole in a
    # one-piece insert has nothing to lap to (FX-TUBSHOWER-60-DIVERTED; superseded note
    # notes/superseded/shower_niche.md). Mark E1 stays in the catalog as a named revert.


    # RM-S-BATH1: a general can, a wet can over the shower clear of the stack vent at
    # y=34'-3". The mirror is a plain Kohler K-26050 round under a 3-light Karlie on the
    # east wall, on the lavatory's centre line (plan/mirrors.py).
    ElectricalDevice(uid="QTS000HAAA", tag="ED-S-BATH1-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(m(1.22226), ft(30)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000JAAA", tag="ED-S-BATH1-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 5.75), ft(33, 9)), type_ref="ED-T-LT-CAN4-WET",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     controlled_by=("ED-S-BATH1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # GFCI at 54" AFF, switch at 46": 8" between device centers. Both are at y=354",
    # 6" beyond the stopped door tip; the mirror's south edge is y=359.5".
    ElectricalDevice(uid="QTS000MAAA", tag="ED-S-BATH1-RC-MIRROR",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-GUIDE",
                     circuit="CKT-BATH-RC", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BA-E1B", face="right", distance_from_start=inch(46),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000NAAA", tag="ED-S-BATH1-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-UPPER", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BA-E1B", face="right", distance_from_start=inch(46),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The hall bath's lit niche and its PSU are gone too (2026-10-12), same reason.

    # Both switches sit at x=17'-6 3/4", the humid liner on W-S-C1's plant-room face — a
    # switch authored to the bare wall face resolves inside the panel.
    # RM-S-PLANT: two suspended tubes over the plants at the south windows, on a D315S relay
    # so HA runs a photoperiod rather than whenever somebody remembers. The fan-light
    # (ED-S-PLANT-LT, re-typed) moves the humid air a plant room makes.
    ElectricalDevice(uid="QTS000PAAA", tag="ED-S-PLANT-TUBE1", kind=DeviceKind.LIGHT,
                     position=pt(m(1.62004), m(0.594343)), type_ref="ED-T-LT-GROW-BAR",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(2, 3))),
    ElectricalDevice(uid="QTS000QAAA", tag="ED-S-PLANT-TUBE2", kind=DeviceKind.LIGHT,
                     position=pt(m(3.7205), m(0.609677)), type_ref="ED-T-LT-GROW-BAR",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     controlled_by=("ED-S-PLANT-SW-TIMER",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(2, 3))),
    # South/latch side of D-S-PLANT: the 4" device fits between the junction's end stud
    # (north face y=9.415") and the door's south king (south face y=14").
    ElectricalDevice(uid="QTS000RAAA", tag="ED-S-PLANT-SW-TIMER", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-UPPER", room="RM-S-PLANT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-C1", face="left", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-S-STUDY2: the notes' study sconces — down spots on the *side* walls, set back
    # from the south window wall, so the desk is lit without a lit head in the glass after
    # dark. Two stair sconces step up the north wall beside ST-S2A's flight to the attic.
    ElectricalDevice(uid="QTS000SAAA", tag="ED-S-STUDY2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(31), ft(3)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # CAN3/CAN4 (2026-10-31) over FURN-S-STUDY-TABLE, the room's desk, 12" either side of
    # its centre in FS-ATTIC's 1'-4"..2'-8" bay: one ahead of each seat.
    ElectricalDevice(uid="HXYCRA72DT", tag="ED-S-STUDY2-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 10), ft(2)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="T6R81NEGCB", tag="ED-S-STUDY2-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 10), ft(2)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS000TAAA", tag="ED-S-STUDY2-SPOT1", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6)),
                     location=Location(attachment=WallAttachment(wall_ref="W-S-S2", face="left", distance_from_start=m(2.03137), normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTS000VAAA", tag="ED-S-STUDY2-SPOT2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-SPOT",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-S2", face="left", distance_from_start=inch(142.625),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # x=29'-0", z=7'-6": ST-S2A climbs westward at 7 1/2" per 10" of run, so a station too
    # far west buries the fixture in its own flight — at x=25'-0" the tread top is 95 1/2"
    # storey-relative against a 10'-0" floor-to-floor storey, leaving no band for an 8"
    # fixture. At x=29'-0" the tread top is 59 1/2" storey-relative, so ft(7,6) sits 30 1/2"
    # above the tread with the fixture topping out at 98" -- clear of the deck over, the
    # same relationship SC2 keeps at x=32' (45 1/2" over a 32 1/2" tread).
    #
    # ** NO CHECK CAUGHT THIS. ** `code.R303_7_stairway_illumination` counts luminaires
    # serving the flight (nine for ST-S2A, so it never depended on SC1),
    # `electrical.room_lighting` counts by room, and the fc advisory is planar. Nothing in
    # the engine compares a wall-mount elevation against the stair it lights.
    ElectricalDevice(uid="QTS000WAAA", tag="ED-S-STUDY2-STAIR-SC1", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", serves_stair="ST-S2A",
                     controlled_by=("ED-S-STUDY2-STAIR-SW", "ED-A-STUDY-STAIR-SW"),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS2", face="right", distance_from_start=inch(85),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTS000XAAA", tag="ED-S-STUDY2-STAIR-SC2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2", serves_stair="ST-S2A",
                     controlled_by=("ED-S-STUDY2-STAIR-SW", "ED-A-STUDY-STAIR-SW"),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS2", face="right", distance_from_start=inch(121),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # ST-S2A's foot end of the stair sconces' 3-way (ED-A-STUDY-STAIR-SW is the head end), on
    # W-S-E1 beside the bottom step, south of WIN-S-STUDY3: NEC 210.70(A)(2)(3) wants the
    # stair's lighting controlled at each floor level; ED-S-STUDY2-SW is 15 ft away at the door.
    ElectricalDevice(uid="0V2B6HV409", tag="ED-S-STUDY2-STAIR-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3", circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-E1", face="left", distance_from_start=inch(21),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-S-BED1/2/3, one template laid off the furniture (2026-10-31): ED-S-BED*-LT in front
    # of the PAX fronts, CAN2 over the open floor beside or past the bed foot, CAN3 over the
    # desk ahead of its user, and CAN4 a reading can 21" off the headboard wall on its own
    # switch leg (no bedside lamp in these rooms). BED2's centred queen gets a pair, CAN4 and
    # CAN5, 2' either side of its centre; BED1's twin and BED3's full stand against a wall
    # and take one, on the open side. Joist mid-bays throughout; no duct runs over these rooms.
    ElectricalDevice(uid="QTS0010AAA", tag="ED-S-BED1-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(30), ft(14)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0011AAA", tag="ED-S-BED1-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 4), ft(15, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0012AAA", tag="ED-S-BED1-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(33, 8.5), ft(12, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED1",
                     controlled_by=("ED-S-BED1-SW-READ",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0013AAA", tag="ED-S-BED2-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(28, 8), ft(20, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0014AAA", tag="ED-S-BED2-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 10.5), ft(25, 7.75)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0015AAA", tag="ED-S-BED2-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(30, 8), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW-READ",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="XSN6WX8VW4", tag="ED-S-BED2-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(34, 8), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED2",
                     controlled_by=("ED-S-BED2-SW-READ",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0016AAA", tag="ED-S-BED3-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 5), ft(32, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0017AAA", tag="ED-S-BED3-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(23, 1.5), ft(32, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTS0018AAA", tag="ED-S-BED3-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(33, 8.5), ft(31, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-UPPER", room="RM-S-BED3",
                     controlled_by=("ED-S-BED3-SW-READ",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # The landing end of RM-S-HALL + the stairwell chandelier, hung over the ST-M2S
    # opening so it reads from both the stair and the landing. Both name RM-S-HALL —
    # landing, well and east hall are one room since the centre line opened under
    # BM-S-HALL.
    #
    # There is no can over the landing itself: that point is inside FO-A-HALL, open to the
    # roof, with no host surface for a recessed can. The chandelier below is the fixture
    # for it instead — a double-height pendant hanging over the well — and the landing's own
    # switch (ED-S-LANDING-SW) runs it.
    #
    # ** THE CANOPY IS ON THE RAFTERS AND THE CASCADE HANGS 11'-8" FROM IT (2026-09-23). **
    # At x=13'-11 7/8" the 6:12 underside is 27'-3" (project), 17'-2" over this floor.
    # `elevation` is the LOWEST GLOBE: 5'-6" over the landing floor, 8 1/2" above the
    # R311.7.2 volume over the upper flight's nearest going (6'-8" over its nosing), which
    # the 23" cascade overhangs in plan. The type's 6' is the cascade band, so the top globe
    # is at 11'-6" — above the attic floor, seen from the attic hall too — and the 5'-8"
    # above it is cable (→ resolve/suspension.py). 11'-8" overall of the 13'-0" it ships.
    # ** THE 23" CANOPY NEEDS A LEVEL SEAT ON 6:12: ** flat, it stands 5 3/4" off the rake
    # at its low edge. The listing claims a sloped-ceiling mount; if it is a swivel hook
    # only, block a level plinth between the rafters.
    ElectricalDevice(uid="QTS001AAAA", tag="ED-S-STAIR-CHAND", kind=DeviceKind.LIGHT,
                     position=pt(m(4.26405), m(9.3355)), type_ref="ED-T-LT-CHANDELIER",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL", serves_stair="ST-M2S",
                     controlled_by=("ED-M-STAIR-SW2", "ED-S-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(5, 6))),
    # On W-S-SN3's north face at y=22'-6 1/4", the wall you walk straight at off the
    # flight — a two-gang box with ED-S-LANDING-SW. x=12' is inside the well's west lane
    # (x 10'-3 1/4"..13'-9 3/4"), where ST-M2S turns left, and is where you arrive. A plain
    # switch, not a dimmer: the chandelier dims by its own remote (mark L).
    ElectricalDevice(uid="QTS001BAAA", tag="ED-S-STAIR-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-UPPER", room="RM-S-HALL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SN3", face="left", distance_from_start=inch(28.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
