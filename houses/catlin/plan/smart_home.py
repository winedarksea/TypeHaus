# haus: editable
# Smart-home instances: doorbell, cameras, opener, EVSE, thermostat, alarm relays.
# Every device runs locally in Home Assistant with no vendor cloud after setup
# (notes/smart_home.md). Types and products: plan/smart_home_types.py.
#
# Data endpoints are home runs off ED-B-NET-PATCH (PoE), or ride an AP's raceway as a second
# Cat 6A and continue in a short extension (two Cat 6A fit a 3/4" EMT). Exterior devices
# carry no room=, so the classifiers place them geometrically.

from typehaus import (
    Alarm,
    AlarmKind,
    Appliance,
    ConduitRun,
    DeviceKind,
    ElectricalDevice,
    Mount,
    MountKind,
    Service,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, RacewayCable, WallAttachment

# --- basement: the interconnect relays beside the backup enclosure ---------------------------
# Under ED-B-BACKUP-ENCL on W-B-W1, on the alarms' own circuit (Kidde wants every
# interconnected unit on one branch). Their dry contacts land on two isolated inputs in the
# enclosure; HA observes, the alarms stand alone.
BASEMENT_ELEMENTS = [
    ElectricalDevice(uid="GG0D6W1KJY", tag="ED-B-ALARM-RELAY-SMOKE", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-ALARM-RELAY-SMOKE", circuit="CKT-LT-BACKUP",
                     room="RM-B-FURNACE", mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-W1", face="left", distance_from_start=inch(37),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="TM59ZRME3D", tag="ED-B-ALARM-RELAY-CO", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-ALARM-RELAY-CO", circuit="CKT-LT-BACKUP",
                     room="RM-B-FURNACE", mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-W1", face="left", distance_from_start=inch(45),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Leak sensors (notes/leak_detectors.md): SONOFF SNZB-05P on the floor at each risk point,
    # Zigbee to ZHA, battery (no circuit). HA notifies; nothing depends on them. `position`
    # is the floor point (an Alarm has no wall host or elevation).
    Alarm(uid="4MRMB39TRR", tag="AL-B-WH-LEAK", kind=AlarmKind.LEAK, room="RM-B-WORKSHOP",
          position=pt(inch(147), inch(186))),
    Alarm(uid="F5CW2JYT7F", tag="AL-B-HDR-LEAK", kind=AlarmKind.LEAK, room="RM-B-WORKSHOP",
          position=pt(inch(161), inch(205))),
    Alarm(uid="XEPT78K46Z", tag="AL-B-UTIL-LEAK", kind=AlarmKind.LEAK, room="RM-B-FURNACE",
          position=pt(inch(96.5), inch(248))),
    Alarm(uid="PBBVF80R33", tag="AL-B-SUMP-LEAK", kind=AlarmKind.LEAK, room="RM-B-FURNACE",
          position=pt(inch(26.5), inch(391))),
    Alarm(uid="TQGGAKSHH4", tag="AL-B-MAIN-LEAK", kind=AlarmKind.LEAK, room="RM-B-STAIR",
          position=pt(inch(136), inch(414))),
    Alarm(uid="PKG7EJRSDK", tag="AL-B-BATH-LEAK", kind=AlarmKind.LEAK, room="RM-B-BATH",
          position=pt(inch(127), inch(243.1))),
]

# --- main: doorbell and the porch camera -----------------------------------------------------
MAIN_ELEMENTS = [
    # Latch side of D-M-ENTRY, x=10'-3 1/2" in W-M-N2's first bay, between the strike blocks.
    ElectricalDevice(uid="ZRZEAYW6SG", tag="ED-M-DOORBELL", kind=DeviceKind.DATA_OUTLET,
                     type_ref="ED-T-DOORBELL-POE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(45.5)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N2", face="right", distance_from_start=inch(92.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The doorbell's raceway. W-M-N2 has no way in from below (it stands on the basement
    # wall's concrete, its band is FO-M-STAIR's trimmer) or from above (FO-S-STAIR's trimmer
    # truss), so: a second Cat 6A in CD-M-DATA-KITCH-TRUNK to its pull box in RM-M-MECH's ceiling,
    # then north and east in FS-S-WEST's last truss bay, down W-M-STRW's cavity, and north
    # through the corner into W-M-N2's first bay at the doorbell.
    ConduitRun(uid="REEA36N7AS", tag="CD-M-DATA-DOORBELL", cables=(RacewayCable(count=1, outside_diameter=inch(0.287), cable_type="CMR", role="indoor Cat 6A: doorbell", source="trueCABLE Cat6A Riser U/UTP 23AWG CMR spec sheet rev 3: OD 7.30 mm"),),
               trade_size=inch(0.75), service=Service.DATA,
               # 2026-11-06: lifted to 111" so it crosses the 413.75" truss inside its R1 chase.
               path=(pt(ft(6), inch(411.5)), pt(ft(6), ft(35, 1.5)), pt(ft(10), ft(35, 1.5)),
                     pt(ft(10), ft(35, 1.5)), pt(ft(10), ft(35, 9)), pt(ft(10, 3.5), ft(35, 9))),
               start_elevation=inch(110.5), end_elevation=ft(3, 9),
               elevations=(inch(110.5), inch(111), inch(111), ft(3, 9), ft(3, 9), ft(3, 9)),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-DOORBELL"),
    # Under the balcony joists in the bay south of the screen's front track, so the IR does
    # not flare off the mesh. Base = soffit (105.75") less the 4 15/16" body.
    ElectricalDevice(uid="VD453HW3G7", tag="ED-M-CAM-PORCH", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(17, 6), ft(-9, -2.5)), type_ref="ED-T-CAM-PANTILT",
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(100.8125))),
    # A second Cat 6A in CD-M-DATA-PORCH, then this extension: up into the balcony joists
    # beside the AP and south through them (bored at mid-depth) so nothing crosses under
    # the screen track, then down to the camera.
    ConduitRun(uid="ASN1XG0FEK", tag="CD-M-DATA-CAM-PORCH", cables=(RacewayCable(count=1, outside_diameter=inch(0.26), cable_type="CMP", wet_location=True, role="outdoor Cat 6A: backyard camera", source="Prysmian GenSPEED 10 UTP Indoor/Outdoor Plenum Cat 6A 7141007, REV 09/25: OD 0.260 in, CMP, Wet Location rated per UL 83, SUN RES"),),
               trade_size=inch(0.75), service=Service.DATA,
               path=(pt(ft(17, 6), ft(-4.833)), pt(ft(17, 6), ft(-5)), pt(ft(17, 6), ft(-5)),
                     pt(ft(17, 6), ft(-9, -2.5)), pt(ft(17, 6), ft(-9, -2.5))),
               start_elevation=ft(8, 10.25), end_elevation=inch(105.75),
               elevations=(ft(8, 10.25), ft(8, 10.25), ft(9, 3.5), ft(9, 3.5), inch(105.75)),
               from_ref="ED-M-PORCH-AP", to_ref="ED-M-CAM-PORCH"),
    # Canopy camera: a second Cat 6A in CD-M-DATA-KITCH, then north in FS-S-EAST's webs, east
    # in the last bay, under PR-M-KITCH-LOCAL-VENT's top leg (1/2" clear) and down W-M-N1's
    # bay east of WIN-M-KITCH and its vent riser; out between girts at 5'-9" and across to
    # the camera under BM-BW-RE's soffit. Exterior leg is EMT from a sealed LB.
    ConduitRun(uid="JWWQ53ZA3Z", tag="CD-M-DATA-CAM-CANOPY", cables=(RacewayCable(count=1, outside_diameter=inch(0.26), cable_type="CMP", wet_location=True, role="outdoor Cat 6A: canopy camera", source="Prysmian GenSPEED 10 UTP Indoor/Outdoor Plenum Cat 6A 7141007, REV 09/25: OD 0.260 in, CMP, Wet Location rated per UL 83, SUN RES"),),
               trade_size=inch(0.75), service=Service.DATA,
               path=(pt(ft(19), ft(29)), pt(ft(19), ft(35, 3.5)), pt(ft(31, 7.25), ft(35, 3.5)),
                     pt(ft(31, 7.25), ft(35, 9.75)), pt(ft(31, 7.25), ft(35, 9.75)),
                     pt(ft(31, 7.25), ft(36, 9)), pt(ft(30, 1.125), ft(36, 9)),
                     pt(ft(30, 1.125), ft(37, 11.75)), pt(ft(30, 1.125), ft(37, 11.75)),
                     pt(ft(29, 10.625), ft(37, 11.75))),
               start_elevation=ft(9, 2.25), end_elevation=ft(6, 2),
               elevations=(ft(9, 2.25), ft(9, 2.25), ft(9, 2.25), ft(9, 0.75), ft(5, 9),
                           ft(5, 9), ft(5, 9), ft(5, 9), ft(6, 2), ft(6, 2)),
               # LB at 5, outside the cladding where the leg leaves the wall.
               pull_points=(5,),
               from_ref="ED-M-KITCH-AP", to_ref="ED-BW-CAM-CANOPY"),
    # Leak sensors (notes/leak_detectors.md): SONOFF SNZB-05P on the floor at each risk point,
    # Zigbee to ZHA, battery (no circuit). HA notifies; nothing depends on them. `position`
    # is the floor point (an Alarm has no wall host or elevation).
    Alarm(uid="WJ9EBM7Q87", tag="AL-M-LAUNDRY-LEAK", kind=AlarmKind.LEAK, room="RM-M-LAUNDRY",
          position=pt(inch(127.7), inch(237))),
    Alarm(uid="BDTVWPTR52", tag="AL-M-KITCH-LEAK", kind=AlarmKind.LEAK, room="RM-M-LIVING",
          position=pt(inch(352), inch(410))),
    Alarm(uid="YM5VGSJ383", tag="AL-M-BATH1-LEAK", kind=AlarmKind.LEAK, room="RM-M-BATH1",
          position=pt(inch(42.6), inch(274.9))),
    Alarm(uid="SA96J50WJP", tag="AL-M-BATH2-LEAK", kind=AlarmKind.LEAK, room="RM-M-BATH2",
          position=pt(inch(27.5), inch(176.2))),
]

# --- entry: the canopy column camera ---------------------------------------------------------
# Under BM-BW-RE's soffit (+6'-4"), just north of PT-BW-RE's cap, on the header's centreline
# (x=29'-8 5/8" since it moved 3 3/8" inboard, 2026-10-31; the conduit's last legs with it). Faces north (180 deg): the
# lens spans west through north to east, the drive and the street.
ENTRY_ELEMENTS = [
    ElectricalDevice(uid="N9MVN2Z9HK", tag="ED-BW-CAM-CANOPY", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(29, 8.625), ft(37, 11.75)), rotation=deg(180),
                     type_ref="ED-T-CAM-WIDE",
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(71.75))),
]

# --- second: HP1 thermostat -----------------------------------------------------------------
SECOND_ELEMENTS = [
    # System 1's zone stat, on the hall face of W-S-BW2 between D-S-BED1 and D-S-BED2, at
    # the floor stats' 54" centre. 24 VAC from EQ-S-HP1-AH; no branch circuit.
    ElectricalDevice(uid="Y9HHGXHGB6", tag="ED-S-HP-STAT", kind=DeviceKind.SWITCH, type_ref="ED-T-HP-STAT",
                     room="RM-S-HALL", mount=Mount(kind=MountKind.WALL, elevation=inch(52)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW2", face="left", distance_from_start=inch(42),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Leak sensors (notes/leak_detectors.md): SONOFF SNZB-05P on the floor at each risk point,
    # Zigbee to ZHA, battery (no circuit). HA notifies; nothing depends on them. `position`
    # is the floor point (an Alarm has no wall host or elevation).
    Alarm(uid="PZY0BF7HRZ", tag="AL-S-BATH1-LEAK", kind=AlarmKind.LEAK, room="RM-S-BATH1",
          position=pt(inch(91.9), inch(356.5))),
    Alarm(uid="580NGDANV5", tag="AL-S-VANITY-LEAK", kind=AlarmKind.LEAK, room="RM-S-VANITY",
          position=pt(inch(10.4), inch(295.2))),
    Alarm(uid="4BE63CZDY4", tag="AL-S-SUITEBATH-LEAK", kind=AlarmKind.LEAK, room="RM-S-SUITEBATH",
          position=pt(inch(147.5), inch(240.5))),
    Alarm(uid="GBAGDPRYSN", tag="AL-S-PLANT-LEAK", kind=AlarmKind.LEAK, room="RM-S-PLANT",
          position=pt(inch(166), inch(28))),
]

# --- garage: opener, its ceiling receptacle, the EVSE ----------------------------------------
GARAGE_ELEMENTS = [
    # LiftMaster 87504-267 (8550W is discontinued). Head 11' back from W-G-N on the door's
    # centreline, hung on straps from the 10'-1" ceiling (3'-1" over the 7' door; it needs 2"
    # above the door's high point) at the rail's line; the rail runs to the header. The ratgdo32
    # wires to the opener's Security+ 2.0 terminals. Mount heights here read off the slab.
    Appliance(uid="CC8K8WDGSR", tag="APPL-G-GDO", type_ref="APPL-LIFTMASTER-87504-267", room="RM-GARAGE",
              position=pt(ft(18), ft(56, 6)),
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 4)),
              install_parts=("ratgdo32 ESPHome opener controller (Security+ 2.0)",)),
    # The opener's own outlet, on the garage lights' CKT-LT-GARAGE (2026-11-14): 210.11(C)(4)'s
    # circuit may have no outlet but the bay receptacles. 210.8(A)(2) still wants GFCI, with
    # a reset in reach, so it rides the load side of ED-G-GDO-GFCI beside ED-G-SW.
    ElectricalDevice(uid="8F8ER9WZ7X", tag="ED-G-GDO-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19, 6), ft(56, 6)), type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-LT-GARAGE", room="RM-GARAGE", gfci_ref="ED-G-GDO-GFCI",
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 11.25))),
    # Hardwired from ED-G-EV-1450's box (no plug, 2026-10-30); OCPP to HA, never online.
    Appliance(uid="KF9QATERC5", tag="APPL-G-EVSE", type_ref="APPL-GRIZZLE-SMART-40", room="RM-GARAGE",
              mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-G-S", face="left", distance_from_start=inch(186),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
]
