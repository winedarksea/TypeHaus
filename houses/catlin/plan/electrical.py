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
    ConduitRun,
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
from typehaus.model import m

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
    # The PV array's wall box: same NEMA 3R shell as ED-T-JBOX but on the 2-pole backfeed
    # circuit, so its port is 240V (circuit_refs reconciles poles against ports).
    ElectricalDeviceType(tag="ED-T-PV-JB", name="PV junction box, NEMA 3R",
                          footprint=(inch(6), inch(6)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
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
                     position=pt(m(0.571135), m(9.43475)), type_ref="ED-T-BACKUP-ENCL", circuit="CKT-BACKUP-FEED",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room="RM-B-FURNACE"),
]

# --- Basement: backup outlets, sauna, spa (sunken garden files on this storey) --------
BASEMENT_DEVICES = [
    # HA server + router (backup). Beside the panel in the furnace room.
    ElectricalDevice(uid="CEE003AAAA", tag="ED-B-UTIL-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(3), ft(28)), type_ref="ED-T-RECEPTACLE", circuit="CKT-HA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Sump pump (backup; ~1000W start). GFCI lives at the breaker, not the outlet.
    ElectricalDevice(uid="CEE004AAAA", tag="ED-B-SUMP-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4, 6), ft(33)), type_ref="ED-T-RECEPTACLE", circuit="CKT-SUMP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Sauna heater connection, NE corner of RM-B-SAUNA, low like the heater terminals.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(15), ft(7)), type_ref="ED-T-SAUNA-JB", circuit="CKT-SAUNA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # Hot tub in the sunken garden: disconnect on the west porch wall, 7' from its north
    # end, under the porch deck (see header). NEC 680.22 convenience receptacle beside it.
    ElectricalDevice(uid="CEE010AAAA", tag="ED-B-SPA-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(8, 6), ft(-7.833)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-SPA",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="CEE011AAAA", tag="ED-B-SPA-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(8, 6), ft(-5.5)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]

BASEMENT_EQUIPMENT = [
    # 240V tank beside the HPWH (EQ-B-WH at ~(5'-11", 33')) in the furnace room.
    Equipment(uid="CEE015AAAA", tag="EQ-B-WH2", kind=EquipmentKind.WATER_HEATER,
              position=pt(m(2.54347), m(9.89175)), footprint=(inch(24), inch(24)),
              room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER-240", circuit="CKT-WH-240"),
    Equipment(uid="CEE016AAAA", tag="EQ-B-ERV", kind=EquipmentKind.ERV,
              position=pt(m(2.09754), m(8.88149)), footprint=(inch(24), inch(24)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV", circuit="CKT-ERV"),
]

# --- Main storey: dryer, freezer, minisplit condensers + disconnects ------------------
MAIN_DEVICES = [
    # Dryer behind the laundry pair (FX-M-LAUNDRY at (10'-6", 20')).
    ElectricalDevice(uid="CEE007AAAA", tag="ED-M-LAUNDRY-DR1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(9, 6), ft(20)), type_ref="ED-T-RECEPTACLE-1430", circuit="CKT-DRYER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36))),
    # Freezer beside the fridge (KRF1 at (18'-4", 31'-5")) on the centre wall's east face;
    # fridge + freezer + PoE WiFi share the backup kitchen circuit.
    ElectricalDevice(uid="CEE006AAAA", tag="ED-M-LIVING-KFZ1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4), ft(29, 10)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Minisplit 1 (large, upstairs zone): disconnect on the north wall exterior face,
    # condenser on the ground in the house/garage gap, east of the breezeway.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-MINI1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(26), ft(36.4)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-MINI-1",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # Minisplit 2 (small, deep-cold, basement zone; backup): condenser on the porch deck
    # over the sunken garden, disconnect on the south wall exterior face behind it.
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-MINI2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(24), ft(-0.5)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-MINI-2",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]

MAIN_EQUIPMENT = [
    Equipment(uid="CEE017AAAA", tag="EQ-M-MINI1", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(26), ft(37, 6)), footprint=(inch(38), inch(16)),
              type_ref="EQ-T-MINISPLIT-LG", circuit="CKT-MINI-1"),
    Equipment(uid="CEE018AAAA", tag="EQ-M-MINI2", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(24), ft(-4)), footprint=(inch(30), inch(12)),
              type_ref="EQ-T-MINISPLIT-SM", circuit="CKT-MINI-2"),
]

# --- Garage: both EV receptacles on the south wall, east of the service door ----------
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(16), ft(41, 6)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(20), ft(41, 6)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# --- Attic: PV junction box beside the radon riser (ED-A-NEMA-JB at (6', 37')) --------
PV_JBOX = [
    ElectricalDevice(uid="CEE014AAAA", tag="ED-A-PV-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9), ft(37)), type_ref="ED-T-PV-JB", circuit="CKT-PV",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
PV_JBOX_CLAMP = [
    Connector(uid="CEE019AAAA", tag="CN-A-PV-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(9), ft(37)), elevation=ft(25, 6), size="S-5!",
              connects=("ED-A-PV-JB", "W-A-N2")),
]

# --- Conduit trunks (electrical_notes.md line 3: make it easy to run new lines) -------
# Four EMT trunks from ED-B-PANEL, elevations project-frame absolute (they cross
# storeys). Each run travels its plan polyline flat at start_elevation and rises
# vertically at its last point to end_elevation; the takeoff bills the developed length.
CONDUIT_TRUNKS = [
    # Up the (3', 33') mechanical chase beside the radon vent to the PV junction box.
    ConduitRun(uid="CDT001AAAA", tag="CD-B-ATTIC-RISER", trade_size=inch(1.5),
               path=(pt(ft(2), ft(29)), pt(ft(3), ft(33))),
               start_elevation=ft(-4), end_elevation=ft(25, 6),
               from_ref="ED-B-PANEL", to_ref="ED-A-PV-JB"),
    # North under the 4'-ish house/garage gap to the EV receptacles on W-G-S.
    ConduitRun(uid="CDT002AAAA", tag="CD-B-GARAGE", trade_size=inch(1.25),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(36)), pt(ft(16), ft(36)),
                     pt(ft(16), ft(41, 6))),
               start_elevation=ft(-4), end_elevation=ft(5, 10),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # Across the basement ceiling to the kitchen's east counter wall.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(32))),
               start_elevation=ft(-1), end_elevation=ft(3, 6),
               from_ref="ED-B-PANEL", to_ref="ED-M-LIVING-KGF3"),
    # South out of the basement to the hot tub disconnect under the porch.
    ConduitRun(uid="CDT004AAAA", tag="CD-B-SPA", trade_size=inch(1),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(0)), pt(ft(8, 6), ft(0)),
                     pt(ft(8, 6), ft(-7.833))),
               start_elevation=ft(-4), end_elevation=ft(-4),
               from_ref="ED-B-PANEL", to_ref="ED-B-SPA-DISC"),
]

# --- NEC 210.52 fill (generated positions, hand-authored constructors) ---------------
# electrical.receptacle_spacing walks each habitable room clear-face ring; these
# receptacles close every wall-space gap the 6-foot rule found. Positions sit on the
# room boundary and are draggable like any other device.
NEC_FILL_BASEMENT = [
    ElectricalDevice(uid="NEC001AAAA", tag="ED-B-GYM-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.00), ft(2.62)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC002AAAA", tag="ED-B-GYM-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.00), ft(10.54)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC003AAAA", tag="ED-B-GYM-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(20.58), ft(18.00)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC004AAAA", tag="ED-B-GYM-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33.29), ft(18.00)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC005AAAA", tag="ED-B-GYM-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(36.00), ft(11.46)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC006AAAA", tag="ED-B-GYM-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(36.00), ft(2.21)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC007AAAA", tag="ED-B-GYM-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(28.96), ft(0.00)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
NEC_FILL_MAIN = [
    ElectricalDevice(uid="NEC008AAAA", tag="ED-M-LIVING-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(4.47)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC009AAAA", tag="ED-M-LIVING-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(15.87)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC010AAAA", tag="ED-M-LIVING-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(16.93)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC011AAAA", tag="ED-M-LIVING-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(5.53)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC012AAAA", tag="ED-M-LIVING-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30.03), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC061AAAA", tag="ED-M-LIVING-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(23.70)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC013AAAA", tag="ED-M-BED-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(8.52), ft(13.28)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC014AAAA", tag="ED-M-BED-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(10.75)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC015AAAA", tag="ED-M-BED-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(1.13)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC016AAAA", tag="ED-M-BED-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9.40), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC017AAAA", tag="ED-M-BED-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.05), ft(0.33)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC018AAAA", tag="ED-M-BED-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.05), ft(9.96)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC019AAAA", tag="ED-M-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(18.96)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC020AAAA", tag="ED-M-STUDY-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13.39), ft(18.79)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
NEC_FILL_SECOND = [
    ElectricalDevice(uid="NEC021AAAA", tag="ED-S-PLANT-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(8.01), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC022AAAA", tag="ED-S-PLANT-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.05), ft(2.08)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC023AAAA", tag="ED-S-PLANT-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(3.50), ft(8.61)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC024AAAA", tag="ED-S-PLANT-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13.48), ft(8.61)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC025AAAA", tag="ED-S-PLANT-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(3.10)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC026AAAA", tag="ED-S-STUDY2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(3.83)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC027AAAA", tag="ED-S-STUDY2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(27.49), ft(8.61)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC028AAAA", tag="ED-S-STUDY2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(5.08)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC029AAAA", tag="ED-S-STUDY2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(28.99), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC030AAAA", tag="ED-S-BED1-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.72), ft(18.27)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC031AAAA", tag="ED-S-BED1-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30.98), ft(19.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC032AAAA", tag="ED-S-BED1-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(14.98)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC033AAAA", tag="ED-S-BED1-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(28.94), ft(12.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC034AAAA", tag="ED-S-BED2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.74), ft(27.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC035AAAA", tag="ED-S-BED2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(32.68), ft(27.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC036AAAA", tag="ED-S-BED2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(21.28)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC037AAAA", tag="ED-S-BED2-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(27.24), ft(20.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC038AAAA", tag="ED-S-BED3-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.74), ft(35.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC039AAAA", tag="ED-S-BED3-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(32.68), ft(35.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC040AAAA", tag="ED-S-BED3-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(29.28)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC041AAAA", tag="ED-S-BED3-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(27.24), ft(28.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC042AAAA", tag="ED-S-SUITE-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(11.12), ft(24.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC043AAAA", tag="ED-S-SUITE-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(21.91)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC044AAAA", tag="ED-S-SUITE-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(16.60), ft(13.39)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC045AAAA", tag="ED-S-SUITE-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4.53), ft(13.39)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC046AAAA", tag="ED-S-SUITE-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.05), ft(17.83)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC047AAAA", tag="ED-S-SUITE-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.53), ft(26.28)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
NEC_FILL_ATTIC = [
    ElectricalDevice(uid="NEC048AAAA", tag="ED-A-EAST-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(13.16)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC049AAAA", tag="ED-A-EAST-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(23.94)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC050AAAA", tag="ED-A-EAST-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19.40), ft(35.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC051AAAA", tag="ED-A-EAST-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29.98), ft(35.95)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC052AAAA", tag="ED-A-EAST-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(31.32)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC053AAAA", tag="ED-A-EAST-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(20.74)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC054AAAA", tag="ED-A-EAST-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(10.15)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC055AAAA", tag="ED-A-EAST-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.79), ft(8.72)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC056AAAA", tag="ED-A-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.54), ft(8.61)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC057AAAA", tag="ED-A-STUDY-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(7.94)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC058AAAA", tag="ED-A-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33.75), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC059AAAA", tag="ED-A-STUDY-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(23.67), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC060AAAA", tag="ED-A-STUDY-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(4.52)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]

BASEMENT_ELEMENTS = [*BACKUP_ENCLOSURE, *BASEMENT_DEVICES, *BASEMENT_EQUIPMENT,
                     *CONDUIT_TRUNKS, *NEC_FILL_BASEMENT]
MAIN_ELEMENTS = [*SERVICE_DEVICES, *MAIN_DEVICES, *MAIN_EQUIPMENT, *NEC_FILL_MAIN]
GARAGE_ELEMENTS = [*GARAGE_DEVICES]
SECOND_ELEMENTS = [*NEC_FILL_SECOND]
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP, *NEC_FILL_ATTIC]
