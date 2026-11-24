# haus: editable
# Catlin lighting — RM-M-LIVING: lounge, dining and kitchen.
#
# Split out of plan/lighting.py on 2026-10-31 (1,741 lines against AGENTS.md's 500),
# by zone, and composed in plan/manifest.py like plan/lighting_attic.py: an editable
# file cannot `from plan import ...`. Uids and tags moved unchanged.
# plan/manifest.py spreads LIVING_LIGHTING ahead of lighting_main.MAIN_LIGHTING on `main`.
#
# Conventions (rotation, mounts, controlled_by, 24V PSUs, uids): plan/lighting_basement.py.
# Scenes (the engine models none): notes/smart_home.md, "Lighting scenes".

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    LightRun,
    Mount,
    MountKind,
    deg,
    ft,
    inch,
    mm,
    pt,
)
from typehaus.model import Location, WallAttachment

LIVING_LIGHTING = [
    # RM-M-LIVING's shadow-gap coves: one run down each side in the 5/8" reveal where the
    # ceiling board stops short of the wall it washes (DRYWALL-STANDARD's Z bead, #103; the
    # resolver centres each on its reveal), at the board face — 8'-11", the 9' plane less
    # CR-LIVING-CEIL-RC's channel — the tape on the bead, fixed to the board, not the framing.
    # ** E4 RGB+CCT SINCE 2026-10-31, SPLIT AT THE SLAT PARTITION (y=13'-0"). ** The W/E tags
    # keep the lounge halves, LR-M-DINING-W/E take the dining halves: one controller per
    # zone, so the two ends scene apart. 12 mm tape in the 15.9 mm reveal leaves ~2 mm a side.
    LightRun(uid="QRM0001AAA", tag="LR-M-LIVING-W", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(18, 3.5625), ft(1)), pt(ft(18, 3.5625), ft(13))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU", controller_ref="ED-M-LIVING-LT-CTRL",
             controlled_by=("ED-M-LIVING-SW-COVE",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 11))),
    LightRun(uid="QRM0002AAA", tag="LR-M-LIVING-E", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(35, 5.1875), ft(1)), pt(ft(35, 5.1875), ft(13))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU-E", controller_ref="ED-M-LIVING-LT-CTRL-E",
             controlled_by=("ED-M-LIVING-SW-COVE",), emission_side="right",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 11))),
    LightRun(uid="BJTQTK477J", tag="LR-M-DINING-W", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(18, 3.5625), ft(13)), pt(ft(18, 3.5625), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-DINING-LT-PSU", controller_ref="ED-M-DINING-LT-CTRL",
             controlled_by=("ED-M-LIVING-SW-COVE",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 11))),
    LightRun(uid="H7WQ6SD52G", tag="LR-M-DINING-E", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(35, 5.1875), ft(13)), pt(ft(35, 5.1875), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-DINING-LT-PSU-E", controller_ref="ED-M-DINING-LT-CTRL-E",
             controlled_by=("ED-M-LIVING-SW-COVE",), emission_side="right",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 11))),
    # ** ONE CLASS 2 DRIVER PER COVE HALF (owner, 2026-10-31). ** The tape carries no
    # listing, so the listed part is the supply, and each segment gets a <=100 VA Class 2
    # HLG-100H-24A (non-dimming) with its own GL-C-001P beside it, which dims and mixes; HA
    # groups each zone's pair. All channels on (20 W/m, 2026-11-07): lounge halves 12' x 6.1
    # W/ft = 73 W, x1.25 = 92 W; dining 8.5' = 52 W, x1.25 = 65 W; all on 96 W.
    # ** A VISIBLE BANK ON THE STUDY CEILING (owner, 2026-11-17). ** It was hidden above the
    # living ceiling behind a hatch nobody modelled (electrical.led_gear_access). Now four
    # drivers on edge at 4" pitch, long axis N-S, under the study board's east half against
    # the x=18' wall the west coves sit behind; each controller in line at its driver's DC
    # end. West-cove pairs nearest the wall. Leads are derived (resolve/led_leads.py): the
    # east coves' ~30' takes 14 AWG. The cove paddle (a hard-off, left on) cuts all four 120 V.
    ElectricalDevice(uid="QTM0001AAA", tag="ED-M-LIVING-LT-PSU", kind=DeviceKind.LED_DRIVER,
                     position=pt(inch(212.5), inch(243)), rotation=deg(90),
                     type_ref="ED-T-LT-PSU-96-WE", circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4))),
    ElectricalDevice(uid="KADE9WHCBJ", tag="ED-M-LIVING-LT-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     position=pt(inch(212.5), inch(253.25)), rotation=deg(90),
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-M-LIVING-LT-PSU", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=mm(37))),
    ElectricalDevice(uid="AMDV43NTPM", tag="ED-M-DINING-LT-PSU", kind=DeviceKind.LED_DRIVER,
                     position=pt(inch(208.5), inch(243)), rotation=deg(90),
                     type_ref="ED-T-LT-PSU-96-WE", circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4))),
    ElectricalDevice(uid="WEY30PQ1C8", tag="ED-M-DINING-LT-CTRL", kind=DeviceKind.LED_CONTROLLER,
                     position=pt(inch(208.5), inch(253.25)), rotation=deg(90),
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-M-DINING-LT-PSU", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=mm(37))),
    ElectricalDevice(uid="BT4Y3QPQYX", tag="ED-M-LIVING-LT-PSU-E", kind=DeviceKind.LED_DRIVER,
                     position=pt(inch(204.5), inch(243)), rotation=deg(90),
                     type_ref="ED-T-LT-PSU-96-WE", circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4))),
    ElectricalDevice(uid="A4G60525S8", tag="ED-M-LIVING-LT-CTRL-E", kind=DeviceKind.LED_CONTROLLER,
                     position=pt(inch(204.5), inch(253.25)), rotation=deg(90),
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-M-LIVING-LT-PSU-E", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=mm(37))),
    ElectricalDevice(uid="M9S69APGYK", tag="ED-M-DINING-LT-PSU-E", kind=DeviceKind.LED_DRIVER,
                     position=pt(inch(200.5), inch(243)), rotation=deg(90),
                     type_ref="ED-T-LT-PSU-96-WE", circuit="CKT-LT-MAIN", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(4))),
    ElectricalDevice(uid="4KSC9M1MHX", tag="ED-M-DINING-LT-CTRL-E", kind=DeviceKind.LED_CONTROLLER,
                     position=pt(inch(200.5), inch(253.25)), rotation=deg(90),
                     type_ref="ED-T-LT-CTRL-5IN1", psu_ref="ED-M-DINING-LT-PSU-E", room="RM-M-STUDY-CLOSET",
                     mount=Mount(kind=MountKind.CEILING, drop=mm(37))),
    # The lounge: one 3'-8" lattice, x 25'-6" / 29'-2" / 32'-10", rows y=3'-4" and 11'-4" (joist
    # mid-bays, clear of the ERV returns at y=10'-0"/12'-8"), symmetric about the fire axis
    # y=7'-4". South row CAN3/CAN4/CAN7: gimbals 33" off the glazing, washing the curtains.
    # CAN2: the fire-axis gimbal, 31" off the fireplace wall, aimed at the mantel. North row
    # CAND1-3: the day cans. No can over the movable furniture; the lamps read there.
    # Scene groups: A accents CAN2/3/4/7 on -SW-ACCENT, C day CAND1-3 on -SW-DAY, both D315S
    # relays; B retired 2026-11-24 (CAN5/6, ED-M-LIVING-LT); D coves via their Zigbee controllers.
    ElectricalDevice(uid="QTM0002AAA", tag="ED-M-LIVING-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(32, 10), ft(7, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-ACCENT",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0003AAA", tag="ED-M-LIVING-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 6), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-ACCENT",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0004AAA", tag="ED-M-LIVING-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 2), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-ACCENT",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="FQZ5724DVP", tag="ED-M-LIVING-CAN7", kind=DeviceKind.LIGHT,
                     position=pt(ft(32, 10), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-ACCENT",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The day layer: mark A1, 5000 K, the north row on the lattice (y=11'-4", the farthest from
    # the south and east glazing). The puzzle table's day light is LAMP-M-LIV-PUZZLE.
    ElectricalDevice(uid="QTM0019AAA", tag="ED-M-LIVING-CAND1", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 6), ft(11, 4)), type_ref="ED-T-LT-CAN4-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM001AAAA", tag="ED-M-LIVING-CAND2", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 2), ft(11, 4)), type_ref="ED-T-LT-CAN4-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="K96ZBJ7FQR", tag="ED-M-LIVING-CAND3", kind=DeviceKind.LIGHT,
                     position=pt(ft(32, 10), ft(11, 4)), type_ref="ED-T-LT-CAN4-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The lounge station, a 3-gang on W-M-C1's east face: COVE (a plain hard-off left on), then
    # D315S relays ACCENT and DAY. No dimmers: the cans run full or off, and the coves dim at
    # their controllers.
    ElectricalDevice(uid="DS30ANGPH9", tag="ED-M-LIVING-SW-COVE", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(134.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QT8E5TH823", tag="ED-M-LIVING-SW-ACCENT", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(138.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTM001DAAA", tag="ED-M-LIVING-SW-DAY", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(142.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The dining fixture, centred on FURN-M-DINING at y=18'. A 3'-6" assembly off a 9' ceiling puts
    # the shade bottom at 5'-6" — about 3' over a 30" table, which is the height that lights
    # the table without blocking the person across it.
    ElectricalDevice(uid="QTM0005AAA", tag="ED-M-DINING-PEND", kind=DeviceKind.LIGHT,
                     position=pt(inch(317.375), ft(18)), type_ref="ED-T-LT-PENDANT",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-DINING-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(3, 6))),
    # A plain paddle since 2026-11-03; the chandelier dims by its own remote (the accepted
    # integrated exception).
    ElectricalDevice(uid="QTM0006AAA", tag="ED-M-DINING-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C2", face="right", distance_from_start=inch(34.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The kitchen end of the same room. The cans left the backup tier on 2026-11-02 for
    # CKT-LT-MAIN; only the under-cabinet tape below rides it (notes/backup_power.md §5).
    #
    # One x pitch of 3'-0" (22'-10", 25'-10", 28'-10", 31'-10"), every can in a FS-S-EAST mid-bay
    # (y 24'-8", 27'-4", 30'-0", 32'-8"). North counter row CAN1-CAN3 at y=32'-8", 7 5/8" ahead
    # of the counter front and 18 1/2" off the uppers' faces; CAN3 is 10" west of PR-M-KITCH-VENT
    # (x=32'-8"). Peninsula row CAN5-CAN8 at y=27'-4" over the worktop; CAN5 is the aisle end, 2'-2"
    # off the fridge/pantry faces. CAN9/CAN10 are the range and pantry-column cans, >=18" off
    # every tall face. No can over the microwave landing (CAN4, retired 2026-11-24): CAN8, CAN9
    # and the hood LED cover it.
    # Task cans (A4, 25 deg) at the sink (CAN2) and peninsula (CAN6/7/8) and the range (CAN9); CAN10
    # is an A over the pantry aisle. Two legs: perimeter on ED-M-KITCH-SW, peninsula on -SW-PEN.
    ElectricalDevice(uid="7WE319EHB5", tag="ED-M-KITCH-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(22, 10), ft(27, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="Z256WYTAN6", tag="ED-M-KITCH-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 10), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="T5YZRQ2P6K", tag="ED-M-KITCH-CAN7", kind=DeviceKind.LIGHT,
                     position=pt(ft(28, 10), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QXW0T5DB2J", tag="ED-M-KITCH-CAN8", kind=DeviceKind.LIGHT,
                     position=pt(ft(31, 10), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0009AAA", tag="ED-M-KITCH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 10), ft(32, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000AAAA", tag="ED-M-KITCH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(28, 10), ft(32, 8)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000BAAA", tag="ED-M-KITCH-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(31, 10), ft(32, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The range can: 13 3/4" west of APPL-M-RANGE's face (32'-11 3/4"), off the body, midway between
    # the rows; the hood LED lights the cooktop (the vent pipe at x=32'-8" blocks a can behind it).
    ElectricalDevice(uid="HP0FGG8J2G", tag="ED-M-KITCH-CAN9", kind=DeviceKind.LIGHT,
                     position=pt(ft(31, 10), ft(30)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The pantry aisle, 21 5/8" off the PANTRY-S1/S2 fronts (33'-5 1/2"), centred on their seam.
    ElectricalDevice(uid="KPZAFJ3357", tag="ED-M-KITCH-CAN10", kind=DeviceKind.LIGHT,
                     position=pt(ft(31, 10), ft(24, 8)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # ** MOVED OFF W-M-C5 (2026-09-06): THE KITCHEN'S MAIN SWITCH WAS BEHIND A CABINET. **
    # W-M-C5 (y 25'-10"..33'-1") is all behind PANTRYC and the fridge/freezer columns.
    #
    # W-M-C3's east face instead, in the 11" of free wall between D-M-STUDY's jamb pack
    # (which reaches y=256.97", measured off the resolved `framing_bumper`, not the 30"
    # leaf) and N-M-C2 at y=268": the wall you pass walking into the kitchen through the
    # BM-M-HALL beam line. ED-M-KITCH-SW-UC stays at the pantry corner for the counter tape.
    #
    # A 3-gang since 2026-10-31: the lounge scene keypad, the perimeter paddle and the
    # peninsula D315S relay, in the 7 1/2" bay between D-M-STUDY's north king (y=260.24") and the end pack
    # (267.75"). A real 3-gang (~5.7") fits it; the modelled 1-gang boxes sit at a 2 5/16"
    # pitch, centred on y=22'-0", 5/16" clear of each stud. At 44", not 46": the keypad's box
    # is back to back with ED-M-STUDY-SW's (48") in the same cavity, and 44" puts them apart.
    #
    # ED-M-LIVING-RC7 was moved north on this wall to clear D-M-STUDY's jamb pack; its
    # spacing position remains governed by the NEC 210.52 run in electrical.py.
    # A ZEN32 on the house's Z-Wave stick; its relay is unwired (scenes reach the D315S groups).
    ElectricalDevice(uid="65D56B3E59", tag="ED-M-LIVING-KEYPAD", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-ZOOZ-ZEN32",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(45.6875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTM000DAAA", tag="ED-M-KITCH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(48),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="9DC7AGX2V8", tag="ED-M-KITCH-SW-PEN", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(50.3125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- kitchen under-cabinet task light -----------------------------------------------
    # Ceiling cans alone over a counter you stand in front of light your own shadow onto
    # the work surface. Tape follows the real undersides: west W36, east W30, diagonal
    # corner and W12, at the cabinet's front edge.
    # ** IKEA MITTLED (U1) SINCE 2026-10-31, AND IT STAYS. ** The US modules give ~235 lm/ft
    # on these runs, under the ~300 lm/ft rule, but the A/A4 cans over every counter run carry
    # the rest and the owner prefers it; 2700 K against the cans' 3000 K is one step. Mark U
    # is the revert.
    LightRun(uid="63DMV159RN", tag="LR-M-KIT-N-WE1", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(297.375), ft(34, 3.375)), pt(inch(333.375), ft(34, 3.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             aperture="down", mount=Mount(kind=MountKind.WALL, elevation=inch(53))),
    LightRun(uid="0ZE5GQV7CQ", tag="LR-M-KIT-N-WE2", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(369.49), ft(34, 3.375)), pt(inch(399.49), ft(34, 3.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             aperture="down", mount=Mount(kind=MountKind.WALL, elevation=inch(53))),
    # Corner tape follows the diagonal front, inset one inch onto its real underside:
    # 15.56" drawn, one 15" MITTLED module bought.
    LightRun(uid="5SGJTPFRSQ", tag="LR-M-KIT-N-WE3", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(400.375), inch(411.375)), pt(inch(411.375), inch(400.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU2",
             controlled_by=("ED-M-KITCH-SW-UC",),
             aperture="down", mount=Mount(kind=MountKind.WALL, elevation=inch(73))),
    LightRun(uid="D1YNDEW7NK", tag="LR-M-KIT-E-WN1", type_ref="ED-T-LT-MITTLED",
             path=(pt(ft(34, 3.375), inch(387.375)), pt(ft(34, 3.375), inch(399.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU2",
             controlled_by=("ED-M-KITCH-SW-UC",),
             aperture="down", mount=Mount(kind=MountKind.WALL, elevation=inch(73))),
    # Six US modules draw 25.2 W, over one TRADFRI 30 W's 125% rule (31.5 W), so two drivers
    # split them by place (owner, 2026-11-08): -PSU takes WE1 (24+12) and WE2 (18+12), 17.6 W
    # = 22 W at 125%; -PSU2 the corner WE3 (15) and the east WN1 (12), 7.6 W = 9.5 W. The
    # closet's idiom (plan/closet.py): both lie on a shelf at 72" inside FURN-M-KIT-WE5 (d
    # 32.5"-62.5"; each 11 1/4" long, d 34.4"-45.6" and 50.4"-61.6"), under the 76" -UC-RC box
    # (74"-78") they cord into, which ED-M-KITCH-SW-UC switches. Each TRADFRI's 30 VA lands on
    # CKT-LT-BACKUP; the outlet has none.
    ElectricalDevice(uid="7VSVT7B8ZS", tag="ED-M-KITCH-LT-PSU", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-TRADFRI-30",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(56),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="120VZACVB0", tag="ED-M-KITCH-LT-PSU2", kind=DeviceKind.LED_DRIVER,
                     type_ref="ED-T-LT-PSU-TRADFRI-30",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(40),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # GFCI at the device: every kitchen 125 V receptacle wants it, and the circuit has none.
    # 76" keeps the box in the band between the cabinet rail backings (58 1/4"..81 1/2").
    ElectricalDevice(uid="D0QND637F1", tag="ED-M-KITCH-UC-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-15",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-UC",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(76)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(50),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Single gang on the pantry east return (the pantry's own sensor moved inside,
    # 2026-10-27), at 46 inches above the north base counter and below its uppers.
    # Keep the box out of the corner pack.
    ElectricalDevice(uid="EX3ZQQPM9K", tag="ED-M-KITCH-SW-UC", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="right", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
