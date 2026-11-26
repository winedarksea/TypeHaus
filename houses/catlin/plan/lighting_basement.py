# haus: editable
# Catlin lighting — the BASEMENT storey.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
#
# `# haus: editable` is REQUIRED: ElectricalDevice is UI-movable, and the loader raises
# `loader.uneditable_movable_element` for one authored elsewhere. Type catalog is the
# non-editable plan/lighting_types.py (uses frozenset, forbidden here).
#
# The sixteen generic ED-T-LIGHT fixtures once one-per-room in plan/mep.py were re-typed
# in place (uid/IFC GlobalId preserved) rather than deleted; everything below is what got
# *added* around them. ED-T-LIGHT itself is retired.
#
# Conventions used throughout:
# - Rotation names the wall a fixture backs onto: deg(0) north, deg(90) west,
#   deg(180) south, deg(-90) east (local +y is the object's back).
# - `Mount(CEILING, recessed_into_host_surface=True)` with no elevation puts a can's base
#   on the ceiling plane, housing in the joist bay above. Attic cans state an elevation
#   (1 1/2" + x/2, x = distance from the nearer eave) because that ceiling is a 6:12
#   cathedral off a rafter plate. Those fittings live in plan/lighting_attic.py.
# - `Mount(CEILING, drop=<type height>)` lands a pendant's canopy on the ceiling; shade
#   bottom = ceiling minus the type's full assembly height.
# - A strip's x,y is its centre; `rotation=deg(90)` runs it N-S. Strips and cans sit in
#   joist/truss mid-bays (#140); chain-hung strips (`drop` > 2.5") clear surface EMT.
# - `controlled_by` names switch(es) on the *load*. Two tags is a 3-way pair. A fixture
#   whose type carries `integral_switch` names none, by design.
# - 24V runs carry no `circuit`: their PSU does, sized at 1.25x connected tape watts and
#   checked by `electrical.light_run_psu`.
#
# Uids are QT/QR + storey letter + serial (Crockford base32, no I/L/O/U → model/ids.py).

from .sauna_types import LIGHT_RAIL_HEIGHT_IN, READING_LIGHT_PATH, WEST_LIGHT_PATH

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

# --- Basement -------------------------------------------------------------------------
# Every light here is on CKT-LT-BSMT since 2026-11-24; the stair's only outage light is
# ED-M-STAIR-NIGHT-LT on CKT-LT-BACKUP (plan/lighting_entry.py, notes/backup_power.md §5).
# Q1 is surface (`drop` = its 2.5" height) or chain-hung (a larger `drop`).
BASEMENT_LIGHTING = [
    # RM-B-GYM: ED-B-GYM-LT (plan/mep_electrical.py) is a lampless N3 fan on its own wall
    # control, so the gym's light is this 4-can grid in FS-M-EAST's mid-bays, y 6'-0"/11'-4",
    # plus the six strips below. The north row stays south of FS-M-NE's trusses at
    # y=13'-0" and off joist 009 at y=12'-0".
    ElectricalDevice(uid="QTB0001AAA", tag="ED-B-GYM-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0002AAA", tag="ED-B-GYM-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0003AAA", tag="ED-B-GYM-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(11, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0004AAA", tag="ED-B-GYM-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(11, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Six Q1 strips, two E-W rows of three about the room's centre (x=26'-7", y=9'-2 1/4"),
    # each row's ceiling box in a joist/truss bay (#140): 63 1/2" and 68" off the fan's centre,
    # clear of its 52" blade circle: no strobe through the blades. Outer pair at x=22'-3 1/2"
    # and 30'-11 1/2", middle at x=26'-7.8". Both rows hang 2.5": the ceiling is one plane
    # since decision #112.
    ElectricalDevice(uid="GBATRH18K6", tag="ED-B-GYM-STRIP1", kind=DeviceKind.LIGHT,
                     position=pt(inch(267.5), inch(44.5)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="WSP6C8GG0P", tag="ED-B-GYM-STRIP2", kind=DeviceKind.LIGHT,
                     position=pt(inch(371.5), inch(44.5)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="VTTBTEZP59", tag="ED-B-GYM-STRIP3", kind=DeviceKind.LIGHT,
                     position=pt(inch(267.5), inch(176)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="Z054XAGTKG", tag="ED-B-GYM-STRIP4", kind=DeviceKind.LIGHT,
                     position=pt(inch(371.5), inch(176)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="KT8H307096", tag="ED-B-GYM-STRIP5", kind=DeviceKind.LIGHT,
                     position=pt(inch(319.8), inch(44.5)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="1E7D8ESFT3", tag="ED-B-GYM-STRIP6", kind=DeviceKind.LIGHT,
                     position=pt(inch(319.8), inch(176)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    # Their toggle, 6 1/2" west of ED-B-GYM-SW (the cans', also CKT-LT-BSMT) inside D-B-PLAY, in
    # the bay across stud-007 (64").
    ElectricalDevice(uid="1NAESZJ528", tag="ED-B-GYM-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER", circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CE", face="right", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-B-WORKSHOP: six Q1 strips on one 3-way pair (2026-11-24: one kind and switch group).
    # Bench row LT1/LT2 N-S at x=2'-8" over FURN-B-WORKSHOP-BENCH-N/-S, 6" behind the bench
    # front, south ends clear of the y=3'-4" SAUNA-EXH duct. Aisle: LT4/LT5 N-S at x=6'-6"
    # (joist mid-bays), LT6 E-W at y=4'-8" (N-S there crosses that duct). Surface on the
    # gypsum, above the radials hung 8-15" lower. LT7 E-W south of the water heater, lighting
    # its approach and the HW header (NEC 210.70(C)), chain-hung 8" under DU-B-ERV-R-SAUNA-SUP.
    ElectricalDevice(uid="QTB0005AAA", tag="ED-B-WORKSHOP-LT1", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 8), ft(6)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="9YNQEQAQF1", tag="ED-B-WORKSHOP-LT2", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 8), ft(10)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="64P02WRNRK", tag="ED-B-WORKSHOP-LT4", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6), ft(8, 8)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="4TA5AQX50C", tag="ED-B-WORKSHOP-LT5", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6), ft(12, 8)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="QTB0006AAA", tag="ED-B-WORKSHOP-LT6", kind=DeviceKind.LIGHT,
                     position=pt(ft(6, 6), ft(4, 8)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="E6HC520FMQ", tag="ED-B-WORKSHOP-LT7", kind=DeviceKind.LIGHT,
                     position=pt(ft(11, 6), ft(12, 8)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW", "ED-B-WORKSHOP-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(8))),
    # A 1-gang on W-B-HALL-W's workshop face, inside D-B-SHOP. The door's latch jamb has
    # 5 5/8" of wall, so it is on the hinge side; at 90 degrees the leaf is clear of it.
    # Distance is off the wall's north end.
    ElectricalDevice(uid="QTB0007AAA", tag="ED-B-WORKSHOP-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-HBL-SW3",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-HALL-W", face="right", distance_from_start=inch(41),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # Its 3-way partner at D-B-FURN, the room's second entry (NEC 210.70(C)(1)), on W-B-CW's
    # workshop face at x=2'-0" (latch side; the leaf hangs on the east jamb), the bay east of
    # ED-B-FURNACE-SW3's so the two boxes do not meet back to back. Runs cross over 61".
    ElectricalDevice(uid="GTXS39HE9Z", tag="ED-B-WORKSHOP-SW3", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-HBL-SW3",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CW", face="right", distance_from_start=inch(30.25),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The under-stair storage (RM-B-STAIR's volume behind D-B-CLOSET): two Q3 lampholders,
    # one per bay (2026-11-15), on ED-B-CLOSET-SW at the door and on the load side of the
    # blank-face GFCI beside it (each lampholder's receptacle is a basement outlet). WEST: on
    # W-B-STR3, 18" along, 54" AFF; the upper flight is ~68" up here. EAST: on W-B-CN under the
    # lower landing (joists 43" AFF, ledger 41"), 33" AFF, lighting that landing and the void
    # under the lower flight; reached by crouching north under the upper landing (50").
    ElectricalDevice(uid="JYMY6WGGP3", tag="ED-B-CLOSET-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-PULLCHAIN",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-CLOSET-SW",), gfci_ref="ED-B-CLOSET-GFCI",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3", face="left", distance_from_start=inch(18),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="ZHF5VAJD6P", tag="ED-B-CLOSET-LT2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-PULLCHAIN",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-CLOSET-SW",), gfci_ref="ED-B-CLOSET-GFCI",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(33)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="left", distance_from_start=inch(131),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # In the furnace room, on W-B-STR3 north of D-B-CLOSET (the 6 3/4" south of it is too
    # narrow): the switch, then the GFCI that protects both lampholders' receptacles.
    ElectricalDevice(uid="VTEDWAW1V7", tag="ED-B-CLOSET-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3", face="right", distance_from_start=inch(9.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="X2K9AK59ZE", tag="ED-B-CLOSET-GFCI", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-DF",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3", face="right", distance_from_start=inch(6.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),


    # ** RM-B-SAUNA IS LIT FROM UNDER THE BENCHES SINCE 2026-09-13; NOTHING ELECTRICAL IS
    # LEFT IN THE HOT ROOM. ** ED-B-SAUNA-LT (mark V, a $1,500-2,250 Cariitti fibre kit) was
    # cut for cost; mark V stays in the catalog as the named revert and ** uid AEYMMW1KDG IS
    # RETIRED, never to be reused ** (the SGS503AAAA precedent). Why, in full:
    # DESIGN-LOG.md, "Basement".
    #
    # Open-frame rails at 16" AFF keep the 90 C tape low, under the 24" lower deck's one
    # exposed (east) edge, split at the recliner's head (2026-11-25): WEST north of it,
    # SOUTH beside the recliner. Neither path spans unsupported open floor.
    LightRun(uid="CH9EBHV9B6", tag="LR-B-SAUNA-WEST", type_ref="ED-T-LT-STRIP24-SAUNA",
             path=WEST_LIGHT_PATH,
             room="RM-B-SAUNA", psu_ref="ED-B-SAUNA-LT-PSU",
             controlled_by=("ED-B-SAUNA-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(LIGHT_RAIL_HEIGHT_IN))),
    LightRun(uid="0Y2Z97Y7TY", tag="LR-B-SAUNA-SOUTH", type_ref="ED-T-LT-STRIP24-SAUNA",
             path=READING_LIGHT_PATH,
             room="RM-B-SAUNA", psu_ref="ED-B-SAUNA-LT-PSU",
             controlled_by=("ED-B-SAUNA-SW",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(LIGHT_RAIL_HEIGHT_IN))),
    # No `circuit=` on either run: a 24V run carries none, its PSU does.
    #
    # The PSU: 6'-8 9/16" at 3 W/ft x1.25 is 25.2 W, 42% of the PSU-60 (2026-11-25).
    #
    # On the workshop face of W-B-SA-W (y=7'-1", 2026-11-25; it was on W-B-SA-N, which faces
    # the bath now), not in the sauna; 48" AFF keeps the driver accessible and ventilated.
    # It draws at the -J box's published 7.40 x 3.74 x 1.59 in, flat on the wall. One 24V
    # Class 2 pair crosses W-B-SA-W's foil-faced polyiso through a gasketed grommet.
    ElectricalDevice(uid="392P1PBQF7", tag="ED-B-SAUNA-LT-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-SA-W", face="left", distance_from_start=inch(85),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The control is OUTSIDE the hot room — a wall switch is rated to 40 C ambient and a
    # sauna is not, which is why an integral-switch J1 could never stand inside. On W-B-CS's
    # GYM face, north of D-B-SAUNA's latch jamb, so it is the switch you reach on the way in;
    # `room` is RM-B-GYM because the device is in the gym.
    # ** A DIMMER, TO KEEP THE DIMMING MARK V HAD: ED-T-LUT-DIVA-ELV (DVELV-300P, on Diode
    # LED's OMNIDRIVE X list), a reverse-phase ELV control. NEVER a TRIAC DVCL-153P (the theatre's):
    # that mis-pairing is the commonest cause of tape flicker. **
    ElectricalDevice(uid="MDVC5HGQZ8", tag="ED-B-SAUNA-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LUT-DIVA-ELV",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CS", face="left", distance_from_start=inch(9.375),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-FURNACE: three Q1 strips on one 3-way pair, one kind, circuit and switch group
    # (2026-11-24). Off backup: in an outage, a flashlight or a lamp on ED-B-UTIL-RC1.
    # STRIP1/2 N-S at x=1'-7.25" in front of ED-B-PANEL-2, -BACKUP-PANEL, -PANEL and the
    # backup enclosure (NEC 110.26(D)), chain-hung 9" under CD-B-DATA-STUDY and the EMT
    # (bottom 7'-4" AFF). STRIP3 E-W in the south pocket beside the utility sink, lighting it
    # and the ERV (210.70(C)); its box in the only 16" bay there (y 18'-8"..20'-0"), hung 15"
    # under PR-M-S-BATH1-DRAIN and PR-B-MAIN-DRAIN (bottom 6'-10" AFF).
    ElectricalDevice(uid="5FCBDBTYK0", tag="ED-B-FURNACE-STRIP1", kind=DeviceKind.LIGHT,
                     position=pt(ft(1, 7.25), ft(26, 5.5)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW2", "ED-B-FURNACE-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(9)), rotation=deg(90)),
    ElectricalDevice(uid="5TN9818FDS", tag="ED-B-FURNACE-STRIP2", kind=DeviceKind.LIGHT,
                     position=pt(ft(1, 7.25), ft(30, 5.5)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW2", "ED-B-FURNACE-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(9)), rotation=deg(90)),
    ElectricalDevice(uid="80YS3B0N3S", tag="ED-B-FURNACE-STRIP3", kind=DeviceKind.LIGHT,
                     position=pt(ft(5, 7), ft(19, 4)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW2", "ED-B-FURNACE-SW3"),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(15))),
    # SW2 mid-room on W-B-STR3B's face (y=23'-0"); SW3 at D-B-FURN (210.70(C)(1): a control
    # at each entry), on W-B-CW's furnace face at x=1'-0", latch side, under the 61"+ runs.
    ElectricalDevice(uid="8SD6TT8XXZ", tag="ED-B-FURNACE-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3B", face="right", distance_from_start=inch(30),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="JJ2EMNAQQ0", tag="ED-B-FURNACE-SW3", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CW", face="left", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-ESS: one keyless lampholder on the Type X lid (NEC 210.70(C), equipment needing
    # service), centred in the closet, south of EQ-B-ESS-BATT. Off backup since 2026-11-24
    # (a flashlight in an outage); the closet's alarms stay on it. Switch inside, on the wall
    # south of the door: outside, the box would stand in the dry-fire lane.
    ElectricalDevice(uid="38Y8Y71C9D", tag="ED-B-ESS-LT", kind=DeviceKind.LIGHT,
                     position=pt(inch(96), inch(398)), type_ref="ED-T-LT-KEYLESS",
                     circuit="CKT-LT-BSMT", room="RM-B-ESS",
                     controlled_by=("ED-B-ESS-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(87.3125))),
    ElectricalDevice(uid="ZKRPWY85MT", tag="ED-B-ESS-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-ESS",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-ESS-W", face="left", distance_from_start=inch(50),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-PLAY-N is the theatre. Up/down sconces are the traditional answer (notes) and the
    # dimmer is the whole point: bright enough to cross the room, dark enough to watch
    # something.
    #
    # ** THE FOUR CANS ARE GONE (2026-09-06, owner's call), AND THE CEILING TAKES NO BOX.
    # ** ED-B-PLAY-N-CAN1..4 (uids QTB000DAAA, QTB000EAAA, QTB0010AAA, QTB0011AAA) are retired.
    # Since decision #112 the ceiling is 5/8" gypsum on resilient channel under FS-M-NE's
    # trusses (CR-PLAY-CEIL-RC, notes/theater_ceiling_acoustics.md): a recessed can or box
    # is a rigid bridge through the decoupling and a hole in the sound-rated board. The
    # right fitting count for that ceiling is zero.
    #
    # ** SIX SCONCES, NOT TWO, AND THE ARITHMETIC IS THE REASON. ** This windowless room is
    # habitable only under R303.1 Exception 1's 6 fc average, and
    # code.R303_1_light_and_ventilation counts POINT luminaires only — LightRuns are
    # deliberately excluded from `_room_lumens` ("a cove can only add light, which makes the
    # number conservative"), so the cove below is worth exactly 0 fc to the check no matter
    # how long it is. The check reads 282 sf, so the floor is 6 fc x 282 / (CU 0.60 x LLF
    # 0.80) = 3,525 lm. Six ED-T-LT-SCONCE-UD at 680 lm is 4,080 lm / 7.0 fc and passes.
    # ** ONE SCONCE IS THE WHOLE MARGIN: ** five is 3,400 lm / 5.8 fc and FAILS, as does any
    # dimmer type. An eighth-sconce scheme was offered and 6 was the call.
    #
    # Three a side on the two side walls at the room's quarter points, y = 22'-6", 27'-0",
    # 31'-6" — SCONCE1/2 keep their uids and move onto the outer east stations, so the
    # schedule reads as one six-piece run rather than a pair plus four. Nothing is on either
    # side wall to foul at 6'-6": the bookcases are on the south wall, the 98" screen and
    # the sectional are in the middle third.
    ElectricalDevice(uid="QTB000BAAA", tag="ED-B-PLAY-N-SCONCE1", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-E2", face="left", distance_from_start=inch(54),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTB000CAAA", tag="ED-B-PLAY-N-SCONCE2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-E2", face="left", distance_from_start=inch(162),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="7VRS9XJKG7", tag="ED-B-PLAY-N-SCONCE3", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-E2", face="left", distance_from_start=inch(108),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # West wall. ** THE TWO DEVICE LINES ARE NOT MIRRORED, AND THAT IS CORRECT: ** the east
    # side is W-B-E2, a 16.17" foundation wall, and the west is W-B-CN/CN2 at 12", so a
    # station mirrored about x=27'-0" would stand 6" off the west face. x=18'-8" puts a
    # 4"-deep body's back ON that face (216" axis + 6" half-thickness + 2"), which is what
    # `integrity.wall_mount_on_face` grades — the resolved body,
    # never the authored point. The two banks line up in ELEVATION and in y, which is what
    # reads in the room.
    ElectricalDevice(uid="NYEVZE2RN5", tag="ED-B-PLAY-N-SCONCE4", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(8.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="4XZRS7P3VR", tag="ED-B-PLAY-N-SCONCE5", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD", box_use="bracket",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(62.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="JBZ1PYPYF0", tag="ED-B-PLAY-N-SCONCE6", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD", box_use="bracket",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(116.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The court flood's switch inside D-B-SUNKEN (owner, 2026-11-09): a wire-free RF companion
    # of ED-M-PORCH-FLOOD-SW's D315S, no circuit and no box, on the east bay between the pair's
    # east king and stud-000 (x=24'-10 1/2"), 48" AFF.
    ElectricalDevice(uid="S66994CVB0", tag="ED-B-SUNKEN-SW-FLOOD", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-RF-COMPANION", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-S3-FR", face="left", distance_from_start=inch(82.5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # ** THE AMBIENT COVE WAS DESIGNED, PRICED AND WITHDRAWN (2026-09-06) FOR THE BATTERY. **
    # Two surface COB channels up the side walls at 7'-4" (2 x 15'-6" at 3 W/ft, 93 W, a
    # PSU-200) would have summed at its rating on CKT-LT-BACKUP. The room is on CKT-LT-BSMT
    # since 2026-11-02, so that objection is gone; a revival takes its own switch.
    #
    # The theater dimmer is inside D-B-PLAY (2026-11-09): first framed bay west of the pair's
    # west king (x=23'-11 13/16"), x=23'-8 3/8" on the theater face's stud row.
    ElectricalDevice(uid="QTB000FAAA", tag="ED-B-PLAY-N-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LUT-DIVA",
                     circuit="CKT-LT-BSMT", room="RM-B-PLAY-N",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CE", face="left", distance_from_start=inch(68.4),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-STAIR's landing lights (owner, 2026-11-25): two recessed cans over the two
    # half-landings, one per lane, on CKT-LT-BSMT (not backup; ED-M-STAIR-NIGHT-LT is the
    # outage light) and the stair's 3-way pair. They recess into ST-M2S's landing underside
    # (painted gypsum at +51.89" abs), which a ceiling mount over FO-M-STAIR's open well hangs
    # from (resolve/placeables.py). y=33'-11 1/2" is the mid-bay between that landing's joists
    # at 399.1"/415.1"; x=190" is the hall cans' line, x=145 1/2" the west lane's centre. The
    # railing tape LR-B-STAIR-RAIL and its supply ED-B-STAIR-LT-PSU are retired.
    ElectricalDevice(uid="9KFSBVZDPD", tag="ED-B-STAIR-LAND-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(inch(145.5), inch(407.5)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR", serves_stair="ST-B2M",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="BSSN4HYTM5", tag="ED-B-STAIR-LAND-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), inch(407.5)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR", serves_stair="ST-B2M",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The 3-way at the stair foot. It hung on W-B-STR3's east face at (10'-4 3/8", 26'-6")
    # until 2026-09-05, which the under-stair closet then enclosed — so it moved across the
    # well onto **W-B-WELL-HEAD's east face** (x=14'-2 1/4") at the same height, level with the
    # bathroom's north wall. That is the hall side, which is where you reach for it.
    # y=25'-9 3/4", 3 3/4" north of W-B-BA-E's end; that face is flush with this one since
    # 2026-11-16, so the offset is no longer forced, and it is still the first thing your
    # hand finds at the stair foot. The box nails beside the stub's own end stud (2026-11-20).
    ElectricalDevice(uid="QTB000HAAA", tag="ED-B-STAIR-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-WELL-HEAD", face="right", distance_from_start=inch(3.75),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The can lights the HALL — the slot between W-B-BA-E and W-B-CN2 — centred in it and
    # level with D-B-BATH's leaf. The slot was 3'-2 5/8" and the can sat at x=15'-9";
    # sliding W-B-BA-E 1 5/16" west onto the well partition's line (2026-09-05) made it
    # **3'-4", x 14'-2"..17'-6"** (since 2026-10-30), whose centre is x=15'-10". x=14' would still
    # put the can inside W-B-BA-E's studs. It no longer runs "south to O-B-HALL": since
    # 2026-09-07 the slot runs to the sauna wall and this is the first of four cans on it.
    ElectricalDevice(uid="QTB000JAAA", tag="ED-B-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(23, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** THREE MORE CANS DOWN THE EXTENDED HALL (2026-09-07). ** The hall is 15'-6" of
    # windowless circulation now and CAN1 alone lit its north quarter. Same type, same
    # circuit, same two-way pair, on the same x=190" centre line — the new wall's east face
    # lands at 170.0725" and W-B-CN2's west face at 210", so the centre did not move when
    # the slot grew. (South of y=13'-10" the east side is W-B-CS3's face at 212.615" and the
    # true centre is 191 5/16"; holding 190" keeps the ladder straight, which is worth more
    # than 1 5/16" on a 3" aperture.) The three are 19.5 VA (6.5 W PAR20), on CKT-LT-BSMT.
    #
    # ** THE MIDDLE ONE IS AT 15'-0", NOT THE 15'-6" A 4'-0" LADDER WANTS. ** PR-B-HW-SAUNA
    # crosses the hall east-west at y=15'-6", 2 9/16" below the finished ceiling, and a
    # recessed can wants that plane for its trim. 15'-0" is 6" clear of the pipe and leaves
    # 4'-0"/4'-6"/3'-6" spacings, which nobody standing in a 3'-4" hall can read.
    #
    # Recessing is legitimate here: this hall's ceiling is FS-M-WEST's joist bays, with depth
    # for the 6" housing.
    ElectricalDevice(uid="J2YZPDZ9MP", tag="ED-B-STAIR-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(19, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="780QDKJASC", tag="ED-B-STAIR-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="K96T60Y9RX", tag="ED-B-STAIR-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(11, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BSMT", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-BATH (2026-07-30; rotated 2026-09-05). On CKT-LT-BSMT with the stair foot since
    # 2026-11-02 (off backup: notes/backup_power.md §5). No recessed light since 2026-11-19
    # (owner): ED-B-BATH-CAN1 is retired and the Karlie over the mirror (ED-B-BATH-MIRROR,
    # plan/mirrors.py) lights the room. Switch on the latch-jamb side (door swings out, so
    # it isn't behind the leaf).
    # Hosted on W-B-BA-E's bath face (x=13'-7 3/4" since the 2026-11-16 1" alignment), so it
    # follows the wall.
    ElectricalDevice(uid="QTB000LAAA", tag="ED-B-BATH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-BATH",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-BA-E", face="right", distance_from_start=inch(14.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
