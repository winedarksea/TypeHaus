# haus: editable
# Smart-home instances: doorbell, cameras, opener, EVSE, thermostat, alarm relays, leak valve.
# Every device runs locally in Home Assistant with no vendor cloud after setup
# (notes/smart_home.md). Types and products: plan/smart_home_types.py.
#
# Data endpoints are home runs off ED-B-NET-PATCH (PoE), or ride an AP's raceway as a second
# Cat 6A and continue in a short extension (two Cat 6A fit a 3/4" EMT). Exterior devices
# carry no room=, so the classifiers place them geometrically.

from typehaus import (
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
from typehaus.model import Location, WallAttachment

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
    ConduitRun(uid="REEA36N7AS", tag="CD-M-DATA-DOORBELL", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(ft(6), inch(411.5)), pt(ft(6), ft(35, 1)), pt(ft(10), ft(35, 1)),
                     pt(ft(10), ft(35, 1)), pt(ft(10), ft(35, 9)), pt(ft(10, 3.5), ft(35, 9))),
               start_elevation=inch(110.5), end_elevation=ft(3, 9),
               elevations=(inch(110.5), inch(110.5), inch(110.5), ft(3, 9), ft(3, 9), ft(3, 9)),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-DOORBELL"),
    # Under the balcony joists in the bay south of the screen's front track, so the IR does
    # not flare off the mesh. Base = soffit (105.75") less the body.
    ElectricalDevice(uid="VD453HW3G7", tag="ED-M-CAM-PORCH", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(17, 6), ft(-9, -2.5)), type_ref="ED-T-CAM-TURRET",
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(101.625))),
    # A second Cat 6A in CD-M-DATA-PORCH, then this extension: up into the balcony joists
    # beside the AP and south through them (bored at mid-depth) so nothing crosses under
    # the screen track, then down to the camera.
    ConduitRun(uid="ASN1XG0FEK", tag="CD-M-DATA-CAM-PORCH", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(ft(17, 6), ft(-4.833)), pt(ft(17, 6), ft(-5)), pt(ft(17, 6), ft(-5)),
                     pt(ft(17, 6), ft(-9, -2.5)), pt(ft(17, 6), ft(-9, -2.5))),
               start_elevation=ft(8, 10.25), end_elevation=inch(105.75),
               elevations=(ft(8, 10.25), ft(8, 10.25), ft(9, 3.5), ft(9, 3.5), inch(105.75)),
               from_ref="ED-M-PORCH-AP", to_ref="ED-M-CAM-PORCH"),
    # Canopy camera: a second Cat 6A in CD-M-DATA-KITCH, then north in FS-S-EAST's webs, east
    # in the last bay, under PR-M-KITCH-LOCAL-VENT's top leg (1/2" clear) and down W-M-N1's
    # bay east of WIN-M-KITCH and its vent riser; out between girts at 5'-9" and across to
    # the camera under BM-BW-RE's soffit. Exterior leg is EMT from a sealed LB.
    ConduitRun(uid="JWWQ53ZA3Z", tag="CD-M-DATA-CAM-CANOPY", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(ft(19), ft(29)), pt(ft(19), ft(35, 3.5)), pt(ft(31, 7.25), ft(35, 3.5)),
                     pt(ft(31, 7.25), ft(35, 9.75)), pt(ft(31, 7.25), ft(35, 9.75)),
                     pt(ft(31, 7.25), ft(36, 9)), pt(ft(30, 4.5), ft(36, 9)),
                     pt(ft(30, 4.5), ft(37, 11.75)), pt(ft(30, 4.5), ft(37, 11.75)),
                     pt(ft(30, 2), ft(37, 11.75))),
               start_elevation=ft(9, 2.25), end_elevation=ft(6, 2),
               elevations=(ft(9, 2.25), ft(9, 2.25), ft(9, 2.25), ft(9, 0.75), ft(5, 9),
                           ft(5, 9), ft(5, 9), ft(5, 9), ft(6, 2), ft(6, 2)),
               # LB at 5, outside the cladding where the leg leaves the wall.
               pull_points=(5,),
               from_ref="ED-M-KITCH-AP", to_ref="ED-BW-CAM-CANOPY"),
]

# --- entry: the canopy column camera ---------------------------------------------------------
# Under BM-BW-RE's soffit (+6'-4"), just north of PT-BW-RE's cap. Faces north (180 deg): the
# lens spans west through north to east, the drive and the street.
ENTRY_ELEMENTS = [
    ElectricalDevice(uid="N9MVN2Z9HK", tag="ED-BW-CAM-CANOPY", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(30), ft(37, 11.75)), rotation=deg(180),
                     type_ref="ED-T-CAM-WIDE",
                     mount=Mount(kind=MountKind.CEILING, elevation=inch(71.75))),
]

# --- second: HP1 thermostat and the plant-room leak shutoff ----------------------------------
SECOND_ELEMENTS = [
    # System 1's zone stat, on the hall face of W-S-BW2 between D-S-BED1 and D-S-BED2, at
    # the floor stats' 54" centre. 24 VAC from EQ-S-HP1-AH; no branch circuit.
    ElectricalDevice(uid="Y9HHGXHGB6", tag="ED-S-HP-STAT", kind=DeviceKind.SWITCH, type_ref="ED-T-HP-STAT",
                     room="RM-S-HALL", mount=Mount(kind=MountKind.WALL, elevation=inch(52)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW2", face="left", distance_from_start=inch(42),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # On the lever ball valve at PA-S-PLANT-WATER-STUB's outlet: carried by the valve, not the
    # wall (FLOOR kind at its height, so no backing is owed). Its probe on the floor closes the
    # valve with HA down; 12 V adapter in ED-S-PLANT-RC2, 1'-9" west.
    Appliance(uid="18N1177G8A", tag="APPL-S-PLANT-VALVE", type_ref="APPL-ZOOZ-ZAC36", room="RM-S-PLANT",
              position=pt(ft(7, 9), ft(0, 10.75)),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(15))),
]

# --- garage: opener, its ceiling receptacle, the EVSE ----------------------------------------
GARAGE_ELEMENTS = [
    # Head 11' back from W-G-N on the door's centreline, hung on straps from the 10'-1" ceiling
    # (3'-1" over the 7' door) at the rail's line; the rail runs to the header. The ratgdo32
    # wires to the opener's Security+ 2.0 terminals. Mount heights here read off the slab.
    Appliance(uid="CC8K8WDGSR", tag="APPL-G-GDO", type_ref="APPL-LIFTMASTER-8550W", room="RM-GARAGE",
              position=pt(ft(18), ft(56, 6)),
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 4)),
              install_parts=("ratgdo32 ESPHome opener controller (Security+ 2.0)",)),
    # The opener's own outlet, on the spare CKT-RC-GARAGE (GFCI at the breaker).
    ElectricalDevice(uid="8F8ER9WZ7X", tag="ED-G-GDO-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19, 6), ft(56, 6)), type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-RC-GARAGE", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 11.25))),
    # Beside ED-G-EV-1450, plugged into it; OCPP to HA, never online.
    Appliance(uid="KF9QATERC5", tag="APPL-G-EVSE", type_ref="APPL-GRIZZLE-SMART-40", room="RM-GARAGE",
              mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-G-S", face="left", distance_from_start=inch(186),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
]
