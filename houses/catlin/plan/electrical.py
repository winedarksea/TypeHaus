# haus: editable
# Catlin electrical service upgrade (plans/electrical_notes.md): 200A service with a
# separate meter, 225A panel (type in plan/mep.py), 240V appliance circuits, two EV
# receptacles in the garage, the smart-relay backup subsystem's DIN enclosure, hot tub +
# minisplit disconnects, and the PV junction box beside the radon-vent riser.
#
# Instances only, explicit constructors (`# haus: editable` — UI drags round-trip).
# Circuit assignments live in plan/circuits.py (non-editable); the `circuit=` strings
# here are the join keys. Uids avoid I/L/O/U (Crockford base32, → model/ids.py).
#
# Positions worth knowing (project-north frame, house sheathing SW corner at 0,0):
# - Meter: exterior face of the west wall (W-M-W1), directly outside ED-B-PANEL at
#   (2', 29') in the basement below — shortest service-entrance run from the underground
#   POWER UtilityLine entry at (0', 18').
# - Garage south wall W-G-S runs y=41' with the service door at x=5'-8'; both EV
#   receptacles sit east of it, clear of the door swing.
# - Sunken-garden porch: west wall W-SG-W1 axis at x=8', inner face x=8.5', north end at
#   y=-0.833'. The hot tub disconnect goes 7' south of that north end, under the porch
#   deck (0') and above the garden floor (-9') — basement storey, so Mount elevation 5'
#   puts it at -4' absolute.
# - PV junction box rides the north gable (W-A-N2) beside the radon riser's clamp
#   cluster; at x=9' the 4:12 rake carries siding to 28', so a box at 25'-6" absolute
#   (attic Mount 5'-6" over the 20' datum) has cladding to grip.

from typehaus import (
    Connector,
    ConnectorKind,
    DeviceKind,
    ElectricalDevice,
    ElectricalDeviceType,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Mount,
    MountKind,
    Service,
    ServicePort,
    ft,
    inch,
    pt,
)

DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-METER", name="200A meter socket (meter separate from panel)",
                          footprint=(inch(12), inch(6)), height=inch(16),
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-DISCONNECT-3R", name="NEMA 3R disconnect, 240V",
                          footprint=(inch(8), inch(4)), height=inch(12),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # EV receptacles (plans/electrical_notes.md lines 5-7). load_va is the continuous EV
    # load at 80% of the breaker: 6-20 -> 240x16, 14-50 -> 240x40.
    ElectricalDeviceType(tag="ED-T-EV-620", name="EV receptacle, NEMA 6-20R",
                          nema="6-20R", load_va=3840,
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-EV-1450", name="EV receptacle, NEMA 14-50R",
                          nema="14-50R", load_va=9600,
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-1430", name="Dryer receptacle, NEMA 14-30R",
                          nema="14-30R", load_va=5000,
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # The backup subsystem's physical presence: one DIN-rail enclosure beside the panel
    # (Shelly Pro 4PM relays, 24V PSUs, DIN UPS). The component list is derived by the
    # backup takeoff from the backup-flagged circuits; only the enclosure is modeled.
    ElectricalDeviceType(tag="ED-T-BACKUP-ENCL",
                          name="Backup control enclosure (DIN rail: relays, 24V PSU, UPS)",
                          footprint=(inch(16), inch(6)), height=inch(20),
                          plan_symbol="panel",
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Sauna heaters are hard-wired: a 240V junction box at the heater corner, not a
    # receptacle. 30A/2p circuit -> 7200 VA connected.
    ElectricalDeviceType(tag="ED-T-SAUNA-JB", name="Sauna heater junction box, 240V",
                          load_va=7200,
                          footprint=(inch(6), inch(6)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
)

EQUIPMENT_TYPES = (
    # The 240V resistance tank alongside the 120V Rheem HPWH (EQ-T-WATER-HEATER,
    # plan/mep.py) — notes line 4 wants one of each.
    EquipmentType(tag="EQ-T-WATER-HEATER-240", name="Electric water heater, 240V",
                  footprint=(inch(24), inch(24)), height=ft(5),
                  plan_symbol="water-heater",
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))))),
    EquipmentType(tag="EQ-T-ERV", name="ERV, 240V", footprint=(inch(24), inch(24)), height=inch(30),
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Minisplit outdoor condensers: the larger unit serves the upstairs hallway head, the
    # smaller deep-cold unit serves the basement (and is the one on backup).
    EquipmentType(tag="EQ-T-MINISPLIT-LG", name="Minisplit condenser (large, upstairs zone)",
                  footprint=(inch(38), inch(16)), height=inch(32),
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    EquipmentType(tag="EQ-T-MINISPLIT-SM", name="Minisplit condenser (small, deep-cold, basement zone)",
                  footprint=(inch(30), inch(12)), height=inch(22),
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
)

# --- Service entrance + backup enclosure ---------------------------------------------
SERVICE_DEVICES = [
    # Exterior west wall at y=29', 6" outside the sheathing plane, 5' up.
    ElectricalDevice(uid="CEE001AAAA", tag="ED-M-METER", kind=DeviceKind.METER,
                     position=pt(ft(-0.5), ft(29)), type_ref="ED-T-METER",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]

BACKUP_ENCLOSURE = [
    ElectricalDevice(uid="CEE002AAAA", tag="ED-B-BACKUP-ENCL", kind=DeviceKind.PANEL,
                     position=pt(ft(2), ft(31)), type_ref="ED-T-BACKUP-ENCL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]

# --- Basement: backup outlets, sauna, spa (sunken garden files on this storey) --------
BASEMENT_DEVICES = [
    # HA server + router (backup). Beside the panel in the furnace room.
    ElectricalDevice(uid="CEE003AAAA", tag="ED-B-UTIL-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(3), ft(28)), type_ref="ED-T-RECEPTACLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Sump pump (backup; ~1000W start). GFCI lives at the breaker, not the outlet.
    ElectricalDevice(uid="CEE004AAAA", tag="ED-B-SUMP-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4, 6), ft(33)), type_ref="ED-T-RECEPTACLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Sauna heater connection, NE corner of RM-B-SAUNA, low like the heater terminals.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(15), ft(7)), type_ref="ED-T-SAUNA-JB",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # Hot tub in the sunken garden: disconnect on the west porch wall, 7' from its north
    # end, under the porch deck (see header). NEC 680.22 convenience receptacle beside it.
    ElectricalDevice(uid="CEE010AAAA", tag="ED-B-SPA-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(8, 6), ft(-7.833)), type_ref="ED-T-DISCONNECT-3R",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="CEE011AAAA", tag="ED-B-SPA-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(8, 6), ft(-5.5)), type_ref="ED-T-RECEPTACLE-GFCI",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]

BASEMENT_EQUIPMENT = [
    # 240V tank beside the HPWH (EQ-B-WH at ~(5'-11", 33')) in the furnace room.
    Equipment(uid="CEE015AAAA", tag="EQ-B-WH2", kind=EquipmentKind.WATER_HEATER,
              position=pt(ft(8), ft(33)), footprint=(inch(24), inch(24)),
              room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER-240"),
    Equipment(uid="CEE016AAAA", tag="EQ-B-ERV", kind=EquipmentKind.ERV,
              position=pt(ft(7), ft(29)), footprint=(inch(24), inch(24)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV"),
]

# --- Main storey: dryer, freezer, minisplit condensers + disconnects ------------------
MAIN_DEVICES = [
    # Dryer behind the laundry pair (FX-M-LAUNDRY at (10'-6", 20')).
    ElectricalDevice(uid="CEE007AAAA", tag="ED-M-LAUNDRY-DR1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(9, 6), ft(20)), type_ref="ED-T-RECEPTACLE-1430",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36))),
    # Freezer beside the fridge (KRF1 at (18'-4", 31'-5")) on the centre wall's east face;
    # fridge + freezer + PoE WiFi share the backup kitchen circuit.
    ElectricalDevice(uid="CEE006AAAA", tag="ED-M-LIVING-KFZ1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4), ft(29, 10)), type_ref="ED-T-RECEPTACLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Minisplit 1 (large, upstairs zone): disconnect on the north wall exterior face,
    # condenser on the ground in the house/garage gap, east of the breezeway.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-MINI1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(26), ft(36.4)), type_ref="ED-T-DISCONNECT-3R",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # Minisplit 2 (small, deep-cold, basement zone; backup): condenser on the porch deck
    # over the sunken garden, disconnect on the south wall exterior face behind it.
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-MINI2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(24), ft(-0.5)), type_ref="ED-T-DISCONNECT-3R",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]

MAIN_EQUIPMENT = [
    Equipment(uid="CEE017AAAA", tag="EQ-M-MINI1", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(26), ft(37, 6)), footprint=(inch(38), inch(16)),
              type_ref="EQ-T-MINISPLIT-LG"),
    Equipment(uid="CEE018AAAA", tag="EQ-M-MINI2", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(24), ft(-4)), footprint=(inch(30), inch(12)),
              type_ref="EQ-T-MINISPLIT-SM"),
]

# --- Garage: both EV receptacles on the south wall, east of the service door ----------
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(16), ft(41, 6)), type_ref="ED-T-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(20), ft(41, 6)), type_ref="ED-T-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# --- Attic: PV junction box beside the radon riser (ED-A-NEMA-JB at (6', 37')) --------
PV_JBOX = [
    ElectricalDevice(uid="CEE014AAAA", tag="ED-A-PV-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9), ft(37)), type_ref="ED-T-JBOX",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
PV_JBOX_CLAMP = [
    Connector(uid="CEE019AAAA", tag="CN-A-PV-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(9), ft(37)), elevation=ft(25, 6), size="S-5!",
              connects=("ED-A-PV-JB", "W-A-N2")),
]

BASEMENT_ELEMENTS = [*BACKUP_ENCLOSURE, *BASEMENT_DEVICES, *BASEMENT_EQUIPMENT]
MAIN_ELEMENTS = [*SERVICE_DEVICES, *MAIN_DEVICES, *MAIN_EQUIPMENT]
GARAGE_ELEMENTS = [*GARAGE_DEVICES]
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP]
