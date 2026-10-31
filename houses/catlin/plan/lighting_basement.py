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
# The cans, coves and sconces are on CKT-LT-BACKUP (electrical_notes.md line 24: basement
# and kitchen light survive an outage). The work light is not: the mark Q1 T8 strips in the
# workshop, gym and furnace room are on CKT-LT-BSMT, each on its own switch (NEC 210.7).
# Q1 is surface (`drop` = its 2.5" height) or chain-hung (a larger `drop`).
BASEMENT_LIGHTING = [
    # RM-B-GYM: ED-B-GYM-LT (plan/mep_electrical.py) is a lampless N3 fan on its own wall
    # control, so the gym's light is this 4-can grid in FS-M-EAST's mid-bays, y 6'-0"/11'-4",
    # plus the four strips below. The north row stays south of SL-M-DECK's band at
    # y=13'-0" (solid deck, nothing to recess into) and off joist 009 at y=12'-0".
    ElectricalDevice(uid="QTB0001AAA", tag="ED-B-GYM-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0002AAA", tag="ED-B-GYM-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0003AAA", tag="ED-B-GYM-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(11, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0004AAA", tag="ED-B-GYM-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(11, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Four Q1 strips, two E-W rows of two about the room's centre, 59" and 64" off the fan's
    # centre and 33" clear of its 52" blade circle: no strobe through the blades. The north
    # row is under SL-M-DECK's ceiling, 1 9/16" below FS-M-EAST's, hence the deeper drop.
    ElectricalDevice(uid="GBATRH18K6", tag="ED-B-GYM-STRIP1", kind=DeviceKind.LIGHT,
                     position=pt(inch(267.5), ft(4)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="WSP6C8GG0P", tag="ED-B-GYM-STRIP2", kind=DeviceKind.LIGHT,
                     position=pt(inch(371.5), ft(4)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    ElectricalDevice(uid="VTTBTEZP59", tag="ED-B-GYM-STRIP3", kind=DeviceKind.LIGHT,
                     position=pt(inch(267.5), ft(14, 4)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4.0625))),
    ElectricalDevice(uid="Z054XAGTKG", tag="ED-B-GYM-STRIP4", kind=DeviceKind.LIGHT,
                     position=pt(inch(371.5), ft(14, 4)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     controlled_by=("ED-B-GYM-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4.0625))),
    # Their toggle, 6 1/2" west of ED-B-GYM-SW (the cans', CKT-LT-BACKUP) inside D-B-PLAY, in
    # the bay across stud-007 (64").
    ElectricalDevice(uid="1NAESZJ528", tag="ED-B-GYM-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CE", face="right", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-B-WORKSHOP: six Q1 strips (2026-10-31; was two mark D 2x4 panels, the documented
    # revert). Bench row: three end to end at x=2'-8" over FURN-B-WORKSHOP-BENCH-N/-S
    # (x 0'-8"..3'-2", y 3'-6"..13'-6"), 6" behind the bench front so the light lands ahead of
    # your head, and 4 1/2" east of DU-B-ERV-R-BENCH (x=2'-0", 6'-10 1/2" AFF) so the duct
    # does not shadow the top. Fill: two at x=6'-6" down the west bay. North strip: one E-W at
    # y=14'-1", x 9'-3"..13'-3", 2" east of PR-B-SAUNA-VENT's riser line. All surface on the
    # FS-M-WEST gypsum, above the radials hung 8-15" lower. LT1/LT6 keep PANEL1/PANEL2's uids.
    ElectricalDevice(uid="QTB0005AAA", tag="ED-B-WORKSHOP-LT1", kind=DeviceKind.LIGHT,
                     position=pt(inch(32), inch(54)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="9YNQEQAQF1", tag="ED-B-WORKSHOP-LT2", kind=DeviceKind.LIGHT,
                     position=pt(inch(32), inch(102)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="W4AN3C35D4", tag="ED-B-WORKSHOP-LT3", kind=DeviceKind.LIGHT,
                     position=pt(inch(32), inch(150)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="64P02WRNRK", tag="ED-B-WORKSHOP-LT4", kind=DeviceKind.LIGHT,
                     position=pt(inch(78), inch(54)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="4TA5AQX50C", tag="ED-B-WORKSHOP-LT5", kind=DeviceKind.LIGHT,
                     position=pt(inch(78), inch(102)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5)), rotation=deg(90)),
    ElectricalDevice(uid="QTB0006AAA", tag="ED-B-WORKSHOP-LT6", kind=DeviceKind.LIGHT,
                     position=pt(inch(135), inch(169)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     controlled_by=("ED-B-WORKSHOP-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(2.5))),
    # Two toggles in a 2-gang on W-B-HALL-W's workshop face, inside D-B-SHOP: room (LT4-6)
    # nearest the door, bench row (LT1-3) 4" north. The door's latch jamb has 5 5/8" of wall,
    # so the gang is on the hinge side; at 90 degrees the leaf is clear of it. Distance is
    # off the wall's north end.
    ElectricalDevice(uid="QTB0007AAA", tag="ED-B-WORKSHOP-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-HALL-W", face="right", distance_from_start=inch(41),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="3WSW0XSFYZ", tag="ED-B-WORKSHOP-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-HALL-W", face="right", distance_from_start=inch(37),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The under-stair storage (new 2026-09-05). ED-T-LT-SPOT-SW is the
    # house's integral-switch down-spot — the same article ED-A-STUDIO-SCONCE uses — which
    # is the right fixture for a low space you reach into rather than stand in: NEC 210.70
    # wants a lighting outlet with a switch you can reach, and `integral_switch=True` is
    # what exempts it from `electrical.lighting_controls` (lighting_types.py says so on the
    # type). `room` is RM-B-STAIR since the closet stopped being a `Room` of its own the
    # same day (storeys/basement.py ROOMS) — the fixture did not move an inch.
    #
    # On W-B-STR3's Type X face (x=10'-3 1/4") 2" proud of it, 22" along, 3" north of where
    # it was so it clears D-B-CLOSET's derived RO (2026-10-29), at 4'-6" AFF. The elevation is set by the RAKE, not by habit: the flight
    # overhead is 6'-1 5/8" up at this y, and a 9" fixture at 54" tops out 10 5/8" under it.
    ElectricalDevice(uid="JYMY6WGGP3", tag="ED-B-CLOSET-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SPOT-SW",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(54)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3", face="left", distance_from_start=inch(22),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),


    # ** RM-B-SAUNA IS LIT FROM UNDER THE BENCHES SINCE 2026-09-13; NOTHING ELECTRICAL IS
    # LEFT IN THE HOT ROOM. ** ED-B-SAUNA-LT (mark V, a $1,500-2,250 Cariitti fibre kit) was
    # cut for cost; mark V stays in the catalog as the named revert and ** uid AEYMMW1KDG IS
    # RETIRED, never to be reused ** (the SGS503AAAA precedent). Why, in full:
    # DESIGN-LOG.md, "Basement".
    #
    # Open-frame rails at 16" AFF keep the 90 C tape low, independent of the new
    # 24" platform tops. WEST is the long foot deck; SOUTH follows only the reading
    # platform's exposed north/east edges. Neither path spans unsupported open floor.
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
    # ** THE PSU SIZE IS THE BINDING CONSTRAINT. ** 9'-8 11/16" at 3 W/ft x1.25 is 36.5 W,
    # 61% of the PSU-60. A PSU sums into the backup tier at its RATING (plan/lighting_types.py),
    # so a PSU-200 here would flip `cycle_48h.sustains_always_on` (test_backup_calc.py).
    #
    # On the workshop face of W-B-SA-N (y=10'-3 13/16"), not in the sauna: x=10'-0" keeps the
    # 8" box clear of W-B-SA-W's corner and the sauna's north service strip; 48" AFF keeps the
    # driver accessible and ventilated. Its 8x6x3 footprint projects 6" on a wall, not the
    # part's real 3": do not measure a clearance off it. One 24V Class 2 pair crosses
    # W-B-SA-N's foil-faced polyiso through a gasketed grommet, sealed both faces.
    ElectricalDevice(uid="392P1PBQF7", tag="ED-B-SAUNA-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-BACKUP", room="RM-B-WORKSHOP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-SA-N", face="left", distance_from_start=inch(2),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The control is OUTSIDE the hot room — a wall switch is rated to 40 C ambient and a
    # sauna is not, which is why an integral-switch J1 could never stand inside. On W-B-CS's
    # GYM face, 4 3/8" north of D-B-SAUNA's north jamb, so it is the switch you reach on the
    # way in; `room` is RM-B-GYM because the device is in the gym.
    # ** ED-T-SWITCH-DIM SINCE 2026-09-13, TO KEEP THE DIMMING MARK V ALREADY HAD. ** Pair it
    # with the OMNIDRIVE X as a reverse-phase ELV control (now the D2ELV-1BW Matter dimmer),
    # NEVER the DVCL-153P the cans use — that mis-pairing is the commonest cause of tape flicker.
    ElectricalDevice(uid="MDVC5HGQZ8", tag="ED-B-SAUNA-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER-ELV",
                     circuit="CKT-LT-BACKUP", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CS", face="left", distance_from_start=inch(54),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-FURNACE: two cans, not 2x4 panels — the ceiling is full of supply, drain and ERV
    # runs, and each panel sat ~3" off a pipe. Re-typed in place (uids kept). Each station is
    # a gap the 6" housing clears (electrical.ceiling_can_framing): CAN1 over the aisle
    # between the utility sink and the water heater, CAN2 south of the inverter.
    ElectricalDevice(uid="QTB0008AAA", tag="ED-B-FURNACE-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(8, 3), ft(24)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTB0009AAA", tag="ED-B-FURNACE-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(3, 3), ft(32)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # y=23'-0" is mid-room on the east wall face (W-B-STR3, framed 2x6), x=9'-5" to 9'-8 1/8"
    # — 1" proud of the face — which is where you reach it walking in from D-B-FURN.
    ElectricalDevice(uid="QTB000AAAA", tag="ED-B-FURNACE-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BACKUP", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3B", face="right", distance_from_start=inch(30),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Two Q1 strips N-S at x=3'-8" for NEC 110.26(D): STRIP1 over the working space of
    # ED-B-PANEL-2 / -BACKUP-PANEL, STRIP2 over ED-B-PANEL, the patch box, the backup
    # enclosure and EQ-B-ESS-INV's front. Each stands in a gap between the E-W radials
    # (y 27'-0", 28'-0", 30'-2") and hangs 6" on chains, under PR-B-SAUNA-VENT (y=33'-4")
    # and CD-B-PLAY-SPARE: bottom 7'-7" AFF, over the 6'-6" working-space headroom and the
    # dry-fire lane's 6'-0". Own toggle, ganged 4" past ED-B-FURNACE-SW in the same stud bay:
    # the cans stay on backup, the strips do not.
    ElectricalDevice(uid="5FCBDBTYK0", tag="ED-B-FURNACE-STRIP1", kind=DeviceKind.LIGHT,
                     position=pt(inch(44), inch(296)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(6)), rotation=deg(90)),
    ElectricalDevice(uid="5TN9818FDS", tag="ED-B-FURNACE-STRIP2", kind=DeviceKind.LIGHT,
                     position=pt(inch(44), inch(392)), type_ref="ED-T-LT-STRIP-T8",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     controlled_by=("ED-B-FURNACE-SW2",),
                     mount=Mount(kind=MountKind.CEILING, drop=inch(6)), rotation=deg(90)),
    ElectricalDevice(uid="8SD6TT8XXZ", tag="ED-B-FURNACE-SW2", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BSMT", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-STR3B", face="right", distance_from_start=inch(34),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-B-ESS: one keyless lampholder on the Type X lid (NEC 210.70(C), equipment needing
    # service), centred in the closet, south of EQ-B-ESS-BATT. On CKT-LT-BACKUP with the
    # closet's alarms: the battery is serviced in an outage. Switch inside, on the wall south
    # of the door: outside, the box would stand in the dry-fire lane.
    ElectricalDevice(uid="38Y8Y71C9D", tag="ED-B-ESS-LT", kind=DeviceKind.LIGHT,
                     position=pt(inch(96), inch(398)), type_ref="ED-T-LT-KEYLESS",
                     circuit="CKT-LT-BACKUP", room="RM-B-ESS",
                     controlled_by=("ED-B-ESS-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(87.3125))),
    ElectricalDevice(uid="ZKRPWY85MT", tag="ED-B-ESS-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BACKUP", room="RM-B-ESS",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-ESS-W", face="left", distance_from_start=inch(50),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),

    # RM-B-PLAY-N is the theatre. Up/down sconces are the traditional answer (notes) and the
    # dimmer is the whole point: bright enough to cross the room, dark enough to watch
    # something.
    #
    # ** THE FOUR CANS ARE GONE (2026-09-06, owner's call), BECAUSE THIS CEILING CANNOT
    # TAKE ONE. ** ED-B-PLAY-N-CAN1..4 (uids QTB000DAAA, QTB000EAAA, QTB0010AAA, QTB0011AAA)
    # all stood inside SL-M-DECK: 4 3/8" of cast cap over a 10" EPS stay-in-place form, on
    # 1/2" steel furring, under the 5/8" gypsum IRC R316.4 requires as the thermal barrier
    # over that foam. The whole 18' x 18' room is on it. There is no cavity — plan/mep.py's
    # duct routing has said so for weeks ("NO cavity at all, so every foot of that run is
    # surface-mounted") — and the only way to recess anything is to cut the one layer that
    # is there to stop a fire reaching the foam. The right fitting count for a ceiling like
    # that is zero.
    #
    # ** SIX SCONCES, NOT TWO, AND THE ARITHMETIC IS THE REASON. ** This windowless room is
    # habitable only under R303.1 Exception 1's 6 fc average, and
    # code.R303_1_light_and_ventilation counts POINT luminaires only — LightRuns are
    # deliberately excluded from `_room_lumens` ("a cove can only add light, which makes the
    # number conservative"), so the cove below is worth exactly 0 fc to the check no matter
    # how long it is. The floor is 6 fc x 324 sf / (CU 0.60 x LLF 0.80) = 4,050 lm.
    # Two sconces alone is 1,400 lm / 2.1 fc and FAILS. Six ED-T-LT-SCONCE-UD at 700 lm is
    # 4,200 lm / 6.2 fc and passes. ** THAT IS 0.2 fc OF MARGIN AND IT IS THE WHOLE MARGIN: **
    # drop one sconce, or swap the type for anything dimmer, and this room is a FAIL. An
    # eighth-sconce scheme was offered and 6 was the call.
    #
    # Three a side on the two side walls at the room's quarter points, y = 22'-6", 27'-0",
    # 31'-6" — SCONCE1/2 keep their uids and move onto the outer east stations, so the
    # schedule reads as one six-piece run rather than a pair plus four. Nothing is on either
    # side wall to foul at 6'-6": the bookcases are on the south wall, the 98" screen and
    # the sectional are in the middle third.
    ElectricalDevice(uid="QTB000BAAA", tag="ED-B-PLAY-N-SCONCE1", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-E2", face="left", distance_from_start=inch(54),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="QTB000CAAA", tag="ED-B-PLAY-N-SCONCE2", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-E2", face="left", distance_from_start=inch(162),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="7VRS9XJKG7", tag="ED-B-PLAY-N-SCONCE3", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
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
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(8.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="4XZRS7P3VR", tag="ED-B-PLAY-N-SCONCE5", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(62.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="JBZ1PYPYF0", tag="ED-B-PLAY-N-SCONCE6", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N", controlled_by=("ED-B-PLAY-N-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="right", distance_from_start=inch(116.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # ** THE AMBIENT COVE WAS DESIGNED, PRICED AND WITHDRAWN (2026-09-06) FOR THE BATTERY. **
    # Two surface COB channels up the side walls at 7'-4" (2 x 15'-6" at 3 W/ft, 93 W, a
    # PSU-200) would sum at the driver's rating on CKT-LT-BACKUP and flip
    # `cycle_48h.sustains_always_on` (test_backup_calc.py). If it is wanted, it goes on
    # CKT-LT-BSMT (non-backup, since 2026-10-31) with its own switch.
    ElectricalDevice(uid="QTB000FAAA", tag="ED-B-PLAY-N-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LUT-DIVA",
                     circuit="CKT-LT-BACKUP", room="RM-B-PLAY-N",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN2", face="right", distance_from_start=inch(24),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # RM-B-STAIR: the railing light the notes ask for. A 24V tape at 34" on the stair's
    # west wall, under the handrail — it lights the treads without a fixture in anyone's
    # eyeline coming up. 3-way with the main-storey stair switch, because a stair light
    # that can only be switched from the bottom is a stair light nobody uses.
    #
    # ** A KNOWN LIMIT, MADE VISIBLE BY THE 2026-09-05 CLOSET AND NOT CAUSED BY IT. **
    # `LightRun` carries ONE `Mount` elevation for its whole path, and 34" is measured off
    # the SLAB, not off the raking nosing line — so this tape does not climb with the flight
    # it lights. From y=25'-8" to y=31'-0" it lies under the arriving flight, which is the
    # under-stair storage; north of that it is under the landing deck. Nothing
    # grades a light run's room, so no check says this. Fixing it needs a raked run, which
    # the schema does not have (see `serves_stair` on Railing for the same problem solved
    # for guards).
    LightRun(uid="QRB0001AAA", tag="LR-B-STAIR-RAIL", type_ref="ED-T-LT-STRIP24",
             path=(pt(ft(10, 4.375), ft(25, 8)), pt(ft(10, 4.375), ft(34, 10))),
             room="RM-B-STAIR", psu_ref="ED-B-STAIR-LT-PSU",
             controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
             mount=Mount(kind=MountKind.WALL, elevation=inch(34))),
    # The AC/DC supply in a ceiling box, at the head of the run it feeds (notes: "Box in
    # ceiling for AC/DC power supply"). 9'-5" of tape at 3 W/ft is 28 W; x1.25 = 35 W, so
    # the 60 W supply is the catalog size above it. **It moved to the lower landing's
    # ceiling on 2026-09-05**: (11', 26') is inside the under-stair storage, and a stair
    # light's supply does not belong behind the stored goods.
    ElectricalDevice(uid="QTB000GAAA", tag="ED-B-STAIR-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(15, 6), ft(33)), type_ref="ED-T-LT-PSU-60",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.CEILING)),
    # The 3-way at the stair foot. It hung on W-B-STR3's east face at (10'-4 3/8", 26'-6")
    # until 2026-09-05, which the under-stair closet then enclosed — so it moved across the
    # well onto **W-B-WELL's east face** (x=14'-0 7/8") at the same height, level with the
    # bathroom's north wall. That is the hall side, which is where you reach for it.
    # y=25'-10" and not 25'-6": at the bathroom's north wall line the box straddles
    # W-B-BA-E's own end — that wall's gypsum runs to x=14'-2", four inches past this
    # face — and reads as 0.8" buried. Four inches north is clear of it and still the first
    # thing your hand finds at the stair foot.
    ElectricalDevice(uid="QTB000HAAA", tag="ED-B-STAIR-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-WELL", face="right", distance_from_start=inch(4),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The can lights the HALL — the slot between W-B-BA-E and W-B-CN2 — centred in it and
    # level with D-B-BATH's leaf. The slot was 3'-2 5/8" and the can sat at x=15'-9";
    # sliding W-B-BA-E 1 5/16" west onto the well partition's line (2026-09-05) made it
    # **3'-4", x 14'-2"..17'-6"** (since 2026-10-30), whose centre is x=15'-10". x=14' would still
    # put the can inside W-B-BA-E's studs. It no longer runs "south to O-B-HALL": since
    # 2026-09-07 the slot runs to the sauna wall and this is the first of four cans on it.
    ElectricalDevice(uid="QTB000JAAA", tag="ED-B-STAIR-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(23, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** THREE MORE CANS DOWN THE EXTENDED HALL (2026-09-07). ** The hall is 15'-6" of
    # windowless circulation now and CAN1 alone lit its north quarter. Same type, same
    # circuit, same two-way pair, on the same x=190" centre line — the new wall's east face
    # lands at 170.0725" and W-B-CN2's west face at 210", so the centre did not move when
    # the slot grew. (South of y=13'-10" the east side is W-B-CS3's face at 212.615" and the
    # true centre is 191 5/16"; holding 190" keeps the ladder straight, which is worth more
    # than 1 5/16" on a 3" aperture.) On CKT-LT-BACKUP the three cost 19.5 VA (6.5 W PAR20).
    #
    # ** THE MIDDLE ONE IS AT 15'-0", NOT THE 15'-6" A 4'-0" LADDER WANTS. ** PR-B-HW-SAUNA
    # crosses the hall east-west at y=15'-6", 2 9/16" below the finished ceiling, and a
    # recessed can wants that plane for its trim. 15'-0" is 6" clear of the pipe and leaves
    # 4'-0"/4'-6"/3'-6" spacings, which nobody standing in a 3'-4" hall can read.
    #
    # Recessing is legitimate here: SL-M-DECK is the x 18'-36' half, so this hall's ceiling
    # is FS-M-WEST's joist bays and there is depth for the 6" housing.
    ElectricalDevice(uid="J2YZPDZ9MP", tag="ED-B-STAIR-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(19, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="780QDKJASC", tag="ED-B-STAIR-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(15)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="K96T60Y9RX", tag="ED-B-STAIR-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(inch(190), ft(11, 6)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-STAIR",
                     controlled_by=("ED-B-STAIR-SW", "ED-M-STAIR-SW"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),

    # RM-B-BATH (2026-07-30; rotated 2026-09-05). On CKT-LT-BACKUP, deliberately, so this
    # room and the stair foot stay lit together on backup power. The can is the vanity light,
    # on the room's centre line 17 1/2" off the mirror wall: the only joist bay in the 18-24"
    # band (the doubled joists at 20'-0"/21'-4" hold the rest); switch on the latch-jamb side
    # (door swings out, so it isn't behind the leaf).
    ElectricalDevice(uid="QTB000KAAA", tag="ED-B-BATH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(12), ft(19, 7.75)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH",
                     controlled_by=("ED-B-BATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # x follows W-B-BA-E: the wall slid 1 5/16" west on 2026-09-05 and the switch went with
    # it, back onto the new finish face at 13'-7 5/16". Left where it was it stood 1 5/16"
    # inside the studs — `integrity.wall_mount_on_face` caught it,
    # and no `haus check` rule does.
    ElectricalDevice(uid="QTB000LAAA", tag="ED-B-BATH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BACKUP", room="RM-B-BATH",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-BA-E", face="right", distance_from_start=inch(16),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
