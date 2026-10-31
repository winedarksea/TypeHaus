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
    pt,
)
from typehaus.model import Location, WallAttachment

LIVING_LIGHTING = [
    # RM-M-LIVING's shadow-gap coves: one run down each side in the 5/8" reveal where the
    # ceiling board stops short of the wall it washes (DRYWALL-STANDARD's Z bead, #103; the
    # resolver centres each on its reveal), at the 9' ceiling plane — the tape on the bead,
    # fixed to the board rather than to the framing.
    # ** E4 RGB+CCT SINCE 2026-10-31, SPLIT AT THE SLAT PARTITION (y=13'-0"). ** The W/E tags
    # keep the lounge halves, LR-M-DINING-W/E take the dining halves: one controller per
    # zone, so the two ends scene apart. 12 mm tape in the 15.9 mm reveal leaves ~2 mm a side.
    LightRun(uid="QRM0001AAA", tag="LR-M-LIVING-W", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(18, 3.5625), ft(1)), pt(ft(18, 3.5625), ft(13))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW-COVE",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    LightRun(uid="QRM0002AAA", tag="LR-M-LIVING-E", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(35, 5.1875), ft(1)), pt(ft(35, 5.1875), ft(13))),
             room="RM-M-LIVING", psu_ref="ED-M-LIVING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW-COVE",), emission_side="right",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    LightRun(uid="BJTQTK477J", tag="LR-M-DINING-W", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(18, 3.5625), ft(13)), pt(ft(18, 3.5625), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-DINING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW-COVE",),
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    LightRun(uid="H7WQ6SD52G", tag="LR-M-DINING-E", type_ref="ED-T-LT-STRIP24-RGBCCT",
             path=(pt(ft(35, 5.1875), ft(13)), pt(ft(35, 5.1875), ft(21, 6))),
             room="RM-M-LIVING", psu_ref="ED-M-DINING-LT-PSU",
             controlled_by=("ED-M-LIVING-SW-COVE",), emission_side="right",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # Non-dimming HLG drivers, each feeding its zone's GL-C-001P (which dims and mixes), at
    # the old OMNIDRIVE's spot by the kitchen soffit's service hatch. Lounge: 24' x 5 W/ft =
    # 120 W, x1.25 = 150 W, the HLG-150's whole nameplate, so the 240. Dining: 17' = 85 W,
    # x1.25 = 106 W on the 150. The cove relay cuts both drivers' 120 V.
    ElectricalDevice(uid="QTM0001AAA", tag="ED-M-LIVING-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(19), ft(22, 6)), type_ref="ED-T-LT-PSU-240-HLG",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING)),
    ElectricalDevice(uid="KADE9WHCBJ", tag="ED-M-LIVING-LT-CTRL", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(19), ft(23, 3)), type_ref="ED-T-LT-CTRL-5IN1",
                     room="RM-M-LIVING", mount=Mount(kind=MountKind.CEILING)),
    ElectricalDevice(uid="AMDV43NTPM", tag="ED-M-DINING-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(20, 3), ft(22, 6)), type_ref="ED-T-LT-PSU-150-HLG",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING)),
    ElectricalDevice(uid="WEY30PQ1C8", tag="ED-M-DINING-LT-CTRL", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(20, 3), ft(23, 3)), type_ref="ED-T-LT-CTRL-5IN1",
                     room="RM-M-LIVING", mount=Mount(kind=MountKind.CEILING)),
    # The lounge, laid out off the furniture (2026-10-31): ED-M-LIVING-LT (plan/mep_electrical)
    # over the coffee table on the fire axis y=7'-4"; CAN2 a gimbal 27" off the fireplace wall
    # aimed at the mantel; CAN3/CAN4 gimbals 33" off the south glazing, washing the curtains;
    # CAN5/CAN6 their mirror about the fire axis. Nothing over the sofa or armchairs, every can
    # in a joist mid-bay clear of the ERV returns at y=10'-0"/12'-8".
    # Four D215S groups so scenes can mix them (2026-10-31): A accents CAN2-4 on -SW-ACCENT,
    # B downlights LT/CAN5/CAN6 on -SW, C day CAND1/2 on -SW-DAY, D coves on -SW-COVE.
    ElectricalDevice(uid="QTM0002AAA", tag="ED-M-LIVING-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(33, 2), ft(7, 4)), type_ref="ED-T-LT-CAN4-PREM-GIMBAL",
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
    ElectricalDevice(uid="55ZCN0PWCS", tag="ED-M-LIVING-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(25, 6), ft(11, 4)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QKY6VSH030", tag="ED-M-LIVING-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 2), ft(11, 4)), type_ref="ED-T-LT-CAN4-PREM",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The day layer: mark A1, 5000 K, over the puzzle table (x 26'-4"..28'-4", y 5'-6"..9'-2"),
    # one joist bay either side of ED-M-LIVING-LT, so the cool light lands on the work. CAND1
    # is 2 1/2" north of 6'-0": the y=5'-4" joist is sistered twice, so its bay is 70 1/4"..78 3/4".
    ElectricalDevice(uid="QTM0019AAA", tag="ED-M-LIVING-CAND1", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 4), ft(6, 2.5)), type_ref="ED-T-LT-CAN4-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM001AAAA", tag="ED-M-LIVING-CAND2", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 4), ft(8, 8)), type_ref="ED-T-LT-CAN4-5000",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-LIVING-SW-DAY",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The lounge station: a 4-gang of D215S relays on W-M-C1's east face, COVE, ACCENT,
    # ED-M-LIVING-SW (plan/mep_electrical.py, at 12'-0") and DAY. No dimmers: the cans run
    # full or off, and the coves dim at their controllers.
    ElectricalDevice(uid="DS30ANGPH9", tag="ED-M-LIVING-SW-COVE", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(136),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QT8E5TH823", tag="ED-M-LIVING-SW-ACCENT", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(140),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTM001DAAA", tag="ED-M-LIVING-SW-DAY", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(148),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The dining fixture, centred on FURN-M-DINING at y=18'. A 3'-6" assembly off a 9' ceiling puts
    # the shade bottom at 5'-6" — about 3' over a 30" table, which is the height that lights
    # the table without blocking the person across it.
    ElectricalDevice(uid="QTM0005AAA", tag="ED-M-DINING-PEND", kind=DeviceKind.LIGHT,
                     position=pt(inch(317.375), ft(18)), type_ref="ED-T-LT-PENDANT",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     controlled_by=("ED-M-DINING-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(3, 6))),
    # A D215S relay since 2026-10-31, so scenes reach the chandelier; it still dims by its own
    # remote (the accepted integrated exception). CHECK ITEM: the fixture must come back at
    # its last state on power-up, or a relay "on" leaves it dark.
    ElectricalDevice(uid="QTM0006AAA", tag="ED-M-DINING-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-MAIN", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C2", face="right", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # The kitchen end of the same room, on the backup circuit with the basement
    # (electrical_notes.md line 24).
    #
    # Two rows (2026-10-31), each in a FS-S-EAST mid-bay and on one x pitch of 3'-0" off the
    # sink centre: CAN1-CAN3 at y=34'-0", between the uppers' face (34'-2 1/2") and the
    # counter edge (33'-5 3/8"), CAN2 on the sink; CAN5-CAN8 at y=27'-4" over the peninsula
    # worktop, ahead of both the cook in the aisle and the stools. CAN5 is the row's west end
    # and lights the pantry and fridge faces 2'-10" off them. CAN3 stays west of
    # PR-M-KITCH-VENT at x=32'-7".
    # Task cans (A4, 25 deg) since 2026-10-31 at the sink (CAN2), the peninsula (CAN4/6/7/8)
    # and the range front (CAN9); CAN10 is an A over the pantry aisle. Two legs:
    # perimeter on ED-M-KITCH-SW, peninsula on ED-M-KITCH-SW-PEN.
    ElectricalDevice(uid="7WE319EHB5", tag="ED-M-KITCH-CAN5", kind=DeviceKind.LIGHT,
                     position=pt(ft(23, 4), ft(27, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="Z256WYTAN6", tag="ED-M-KITCH-CAN6", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 4), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="T5YZRQ2P6K", tag="ED-M-KITCH-CAN7", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 4), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QXW0T5DB2J", tag="ED-M-KITCH-CAN8", kind=DeviceKind.LIGHT,
                     position=pt(ft(32, 4), ft(27, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM0009AAA", tag="ED-M-KITCH-CAN1", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 4), ft(34)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000AAAA", tag="ED-M-KITCH-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(29, 4), ft(34)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # CAN4 is over the peninsula carousel's landing in front of the microwave, between the
    # upper's face and the east counter edge.
    ElectricalDevice(uid="QTM000BAAA", tag="ED-M-KITCH-CAN3", kind=DeviceKind.LIGHT,
                     position=pt(ft(32, 4), ft(34)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="QTM000CAAA", tag="ED-M-KITCH-CAN4", kind=DeviceKind.LIGHT,
                     position=pt(ft(33, 10), ft(28, 8)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW-PEN",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The range front, 1 1/4" inside APPL-M-RANGE's face (32'-11 3/4"), 8 3/4" ahead of the
    # hood, its 25 deg beam clear of the hood onto the front burners. x=33'-1" and not the
    # planned 32'-10": PR-M-KITCH-VENT runs north-south in the bay at x=32'-7".
    ElectricalDevice(uid="HP0FGG8J2G", tag="ED-M-KITCH-CAN9", kind=DeviceKind.LIGHT,
                     position=pt(ft(33, 1), ft(31, 4)), type_ref="ED-T-LT-CAN4-TASK",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     controlled_by=("ED-M-KITCH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The pantry aisle, 17" off the PANTRY-S1/S2 fronts (33'-5 1/2"), north of the stools.
    ElectricalDevice(uid="KPZAFJ3357", tag="ED-M-KITCH-CAN10", kind=DeviceKind.LIGHT,
                     position=pt(ft(32), ft(23, 4)), type_ref="ED-T-LT-CAN4",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
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
    # A 3-gang since 2026-10-31: the lounge scene keypad, then the perimeter and peninsula
    # relays, in the 7 1/2" bay between D-M-STUDY's north king (y=260.24") and the end pack
    # (267.75"). A real 3-gang (~5.7") fits it; the modelled 1-gang boxes sit at a 2 5/16"
    # pitch, centred on y=22'-0", 5/16" clear of each stud. At 44", not 46": the keypad's box
    # is back to back with ED-M-STUDY-SW's (48") in the same cavity, and 44" puts them apart.
    #
    # ED-M-LIVING-RC7 was moved north on this wall to clear D-M-STUDY's jamb pack; its
    # spacing position remains governed by the NEC 210.52 run in electrical.py.
    # A ZEN32 on the house's Z-Wave stick; its relay is unwired (every load has its own D215S).
    ElectricalDevice(uid="65D56B3E59", tag="ED-M-LIVING-KEYPAD", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-ZOOZ-ZEN32",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(45.6875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="QTM000DAAA", tag="ED-M-KITCH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(48),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="9DC7AGX2V8", tag="ED-M-KITCH-SW-PEN", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="right", distance_from_start=inch(50.3125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),

    # --- kitchen under-cabinet task light -----------------------------------------------
    # Ceiling cans alone over a counter you stand in front of light your own shadow onto
    # the work surface. Tape follows the real undersides: west W36, east W30, diagonal
    # corner and W12, at the cabinet's front edge.
    # ** IKEA MITTLED (U1) SINCE 2026-10-31, AND IT STAYS. ** ~208 lm/ft is ~30% under the
    # ~300 lm/ft rule, but the A/A4 cans over every counter run carry the rest and the owner
    # prefers it; 2700 K against the cans' 3000 K is one step. Mark U is the revert.
    LightRun(uid="63DMV159RN", tag="LR-M-KIT-N-WE1", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(297.375), ft(34, 3.375)), pt(inch(333.375), ft(34, 3.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(53))),
    LightRun(uid="0ZE5GQV7CQ", tag="LR-M-KIT-N-WE2", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(369.49), ft(34, 3.375)), pt(inch(399.49), ft(34, 3.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(53))),
    # Corner tape follows the diagonal front, inset one inch onto its real underside.
    LightRun(uid="5SGJTPFRSQ", tag="LR-M-KIT-N-WE3", type_ref="ED-T-LT-MITTLED",
             path=(pt(inch(400.375), inch(411.375)), pt(inch(411.375), inch(400.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(73))),
    LightRun(uid="D1YNDEW7NK", tag="LR-M-KIT-E-WN1", type_ref="ED-T-LT-MITTLED",
             path=(pt(ft(34, 3.375), inch(387.375)), pt(ft(34, 3.375), inch(399.375))),
             room="RM-M-LIVING", psu_ref="ED-M-KITCH-LT-PSU",
             controlled_by=("ED-M-KITCH-SW-UC",),
             mount=Mount(kind=MountKind.WALL, elevation=inch(73))),
    # 93.56" at 2.8 W/ft = 21.8 W; x1.25 = 27.3 W on one TRADFRI 30 W, the closet's idiom
    # (plan/closet.py): on the shelf inside FURN-M-KIT-WE5, corded into -UC-RC beside it, which
    # ED-M-KITCH-SW-UC switches. The TRADFRI's 30 VA lands on CKT-LT-BACKUP; the outlet has none.
    ElectricalDevice(uid="7VSVT7B8ZS", tag="ED-M-KITCH-LT-PSU", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-LT-PSU-TRADFRI-30",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(74)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(60),
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
                     type_ref="ED-T-LEV-MATTER",
                     circuit="CKT-LT-BACKUP", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-PAN-E", face="right", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
