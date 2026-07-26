# haus: editable
# Catlin electrical service upgrade (plans/electrical_notes.md): 200A service with a
# separate meter, 225A panel (type in plan/mep.py), 240V appliance circuits, two EV
# receptacles in the garage, the smart-relay backup subsystem's DIN enclosure, hot tub +
# minisplit disconnects, and the PV junction box beside the radon-vent riser.
#
# All-electric house: no gas service, no furnace. Heat is the two minisplits below plus the
# electric radiant floor zones (FloorHeat in plan/storeys/), and EQ-B-ERV is the only thing
# that moves air — its "supply" is fresh air, not heat.
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
    deg,
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
    # receptacle. 50A/2p circuit feeding the 9 kW EQ-B-SAUNA-HTR -> 9000 VA connected.
    ElectricalDeviceType(tag="ED-T-SAUNA-JB", name="Sauna heater junction box, 240V",
                          load_va=9000,
                          footprint=(inch(6), inch(6)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Radiant-floor thermostat: the line-voltage control the mat's cold lead lands in, with
    # its floor sensor run back into the slab. `DeviceKind` has no THERMOSTAT member, and a
    # new one would fall through the IFC map to IfcBuildingElementProxy; SWITCH is a real
    # line-voltage control device in a single-gang box and maps to IfcSwitchingDevice, which
    # is what this is.
    #
    # No `load_va`: one type serves three zones of three different areas, so a figure here
    # would be wrong for at least two of them. The mat is the load, not the control, and
    # each zone's VA is authored on its circuit in plan/circuits.py — which is what
    # `takeoff.electrical._connected_va` prefers anyway.
    ElectricalDeviceType(tag="ED-T-FLOOR-STAT", name="Radiant floor thermostat, 120V",
                          footprint=(inch(4), inch(2)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
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
    # Electric sauna heater. RM-B-SAUNA's heated zone is 8'-0 11/16" x 8'-6" x 7'-6" ~= 513
    # cubic feet, and the trade rule is ~1 kW per 45-50 cf, so this room wants 9-10.5 kW —
    # which is the "240V, 50A GFCI breaker ... max 10.5 kW" the detail notes call for.
    # Floor-standing, 18" x 16" x 30", stones on top (see the ``sauna-heater`` symbol).
    EquipmentType(tag="EQ-T-SAUNA-HEATER", name="Electric sauna heater, 9 kW",
                  footprint=(inch(18), inch(16)), height=inch(30),
                  plan_symbol="sauna-heater",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # The only air-moving equipment in the house — there is no furnace and no air handler,
    # so the SUPPLY_AIR/RETURN_AIR ports that used to hang off EQ-T-FURNACE belong here.
    # "Supply" is fresh air, not heat: the DU-M-ERV-SUP/RET trunks in plan/mep.py connect
    # to these two ports. (The outdoor-side intake and exhaust are the ERV's other pair of
    # collars; `Service` has no OUTDOOR_AIR/EXHAUST_AIR member to name them with, so they
    # stay unmodeled rather than mislabeled as house-side ports.)
    EquipmentType(tag="EQ-T-ERV", name="ERV, 240V", footprint=(inch(24), inch(24)), height=inch(30),
                  plan_symbol="erv",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(24))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(24))))),
    # Minisplit outdoor condensers: the larger unit serves the upstairs hallway head, the
    # smaller deep-cold unit serves the basement (and is the one on backup).
    EquipmentType(tag="EQ-T-MINISPLIT-LG", name="Minisplit condenser (large, upstairs zone)",
                  footprint=(inch(38), inch(16)), height=inch(32),
                  heating_capacity_btuh=30000, heating_capacity_at_design_btuh=21000,
                  source="REPRESENTATIVE PLACEHOLDER — typical 2.5-ton hyper-heat class (~30,000 Btu/h rated at 47F, ~21,000 Btu/h at -13F). Overwrite with the selected model's datasheet numbers.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    EquipmentType(tag="EQ-T-MINISPLIT-SM", name="Minisplit condenser (small, deep-cold, basement zone)",
                  footprint=(inch(30), inch(12)), height=inch(22),
                  heating_capacity_btuh=12000, heating_capacity_at_design_btuh=8700,
                  source="REPRESENTATIVE PLACEHOLDER — typical 1-ton deep-cold hyper-heat class (~12,000 Btu/h rated at 47F, ~8,700 Btu/h at -13F). Overwrite with the selected model's datasheet numbers.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Wall-mount linear electric fireplace, 1,500 W max on 120V — 12.5A, which is why the
    # circuit is 20A and not 15A: 12.5 x 1.25 (continuous) = 15.6A needs the 16A a 20A
    # breaker allows. 48" x 7" cabinet, 21" tall, hard-wired (hence Equipment: the circuit
    # hook lives on the placeable, so there is no receptacle behind the glass).
    EquipmentType(tag="EQ-T-FIREPLACE-EL", name="Electric fireplace, 1.5 kW linear wall-mount",
                  footprint=(inch(48), inch(7)), height=inch(21),
                  ports=(ServicePort(tag="power", service=Service.POWER_120,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Garage unit heater — same 1,500 W / 120V / 20A arithmetic as the fireplace. A small
    # fan-forced box for taking the chill off the bench, not for heating 571 ft2 of
    # unconditioned garage; RM-GARAGE stays `conditioned=False` and therefore out of the
    # 3 VA/ft2 general-lighting area, heater or no heater.
    EquipmentType(tag="EQ-T-GARAGE-HEATER", name="Garage unit heater, 1.5 kW fan-forced, 120V",
                  footprint=(inch(14), inch(9)), height=inch(15),
                  ports=(ServicePort(tag="power", service=Service.POWER_120,
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
    # Sauna heater connection: on the sauna's west liner wall immediately south of
    # EQ-B-SAUNA-HTR (its footprint is y 8'-0"..9'-6"), low like the heater terminals. It
    # used to sit at (15', 7'), which was neither on a wall nor in the "NE corner" its
    # comment claimed — and is now inside FURN-B-SAUNA-BENCH-E.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9, 3), ft(7, 9)), type_ref="ED-T-SAUNA-JB", circuit="CKT-SAUNA",
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
    # Sauna heater, NW corner of the sauna's *heated* zone — the south 8'-6" of RM-B-SAUNA,
    # since notes/sauna_shower_basement_detail.md reserves the north 4' for the shower. Back
    # to the west liner face (x=9'-1 13/16", so rotation 90 = back west), north face on the
    # 9'-6" partition line: it is the first thing past the door and diagonally opposite the
    # bench, which is what keeps 3'-2 11/16" of clear floor between hot metal and bare shins.
    Equipment(uid="CEE020AAAA", tag="EQ-B-SAUNA-HTR", kind=EquipmentKind.SAUNA_HEATER,
              position=pt(ft(9, 9.8125), ft(8, 9)), footprint=(inch(18), inch(16)),
              room="RM-B-SAUNA", type_ref="EQ-T-SAUNA-HEATER", rotation=deg(90),
              circuit="CKT-SAUNA"),
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
    # FH-M-BATH2's thermostat: inside the room on its south wall (W-M-BDN1, interior face
    # y=13'-4 11/16"), 8" east of D-M-BATH2's opening (x 1'-6 1/2"..4'-0 1/2") — the wall
    # you reach as the door closes behind you. Floor sensor is FH-M-BATH2's `stat` point.
    ElectricalDevice(uid="CEE021AAAA", tag="ED-M-BATH2-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(4, 9), ft(13, 5)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH2", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # FH-M-DINING's thermostat. The zone is free-standing in the middle of a 642 ft2 room,
    # so its control goes on the nearest real wall: W-M-E1's interior face at x=35'-11 3/8",
    # in the 2'-5" of clear wall between WIN-M-DIN-E1's rough opening (y 13'-9"..16'-0") and
    # WIN-M-DIN-E2's (y 18'-4 3/4"..20'-8"). ED-M-LIVING-RC3 sits at y=16'-11", so 17'-9"
    # keeps 10" between the two boxes. The sensor lead runs the 5' back to the zone edge.
    ElectricalDevice(uid="CEE024AAAA", tag="ED-M-DINING-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(35, 11), ft(17, 9)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-DINING", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

MAIN_EQUIPMENT = [
    Equipment(uid="CEE017AAAA", tag="EQ-M-MINI1", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(26), ft(37, 6)), footprint=(inch(38), inch(16)),
              type_ref="EQ-T-MINISPLIT-LG", circuit="CKT-MINI-1"),
    Equipment(uid="CEE018AAAA", tag="EQ-M-MINI2", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(24), ft(-4)), footprint=(inch(30), inch(12)),
              type_ref="EQ-T-MINISPLIT-SM", circuit="CKT-MINI-2"),
    # Electric fireplace, SE corner of the living room. It hangs on the *east* wall rather
    # than the south one because that is where the corner has wall left: W-M-S2 gives only
    # 2'-1" between WIN-M-LIV-S1's rough opening and the corner, while W-M-E1 runs clear
    # from the corner up to WIN-M-LIV-E1's sill line at y=5'-9". The 48" cabinet takes
    # y 0'-10"..4'-10" — 9 1/2" off the corner, 7 1/2" short of ED-M-LIVING-RC4 at
    # y=5'-6 1/2". rotation -90 puts its back east against the wall (interior face
    # x=35'-11 3/8"; the 7" cabinet centres at 35'-8"). Mounted at 36" so the glass sits
    # above FURN-M-MEDIA's 30" top on the wall around the corner.
    Equipment(uid="CEE022AAAA", tag="EQ-M-FIREPLACE", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(35, 8), ft(2, 10)), footprint=(inch(48), inch(7)),
              room="RM-M-LIVING", type_ref="EQ-T-FIREPLACE-EL", rotation=deg(-90),
              circuit="CKT-FIREPLACE",
              mount=Mount(kind=MountKind.WALL, elevation=inch(36))),
]

# --- Second storey: the NW bathroom's floor-heat control -------------------------------
SECOND_DEVICES = [
    # FH-S-ENSUITE's thermostat, inside the room on its south wall (W-S-BD-N1B, interior
    # face y=26'-4 11/16"), 9" west of D-S-ENSUITE's opening (x 7'-3"..9'-9"). Same
    # reach-as-the-door-shuts position as ED-M-BATH2-FH-STAT, and clear of the fixture
    # cluster, which all sits north of y=29'-9".
    ElectricalDevice(uid="CEE025AAAA", tag="ED-S-ENSUITE-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 6), ft(26, 5)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-ENSUITE", room="RM-S-ENSUITE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
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

GARAGE_EQUIPMENT = [
    # Bench heater on the west wall — the only one of the four with nothing in it:
    # D-G-OVERHEAD takes 16' of the east wall, D-G-SERVICE the south, WIN-G-N1/N2 the
    # north. Interior face x=0'-0 5/8", so the 9"-deep box centres at x=0'-5"; rotation 90
    # puts its back west. Mounted at 6'-0" on an 8'-0" wall, so its 15" case tops out at
    # 7'-3" and it blows down over a bench instead of at someone's head.
    #
    # Hard-wired, not a cord-and-plug unit: NEC 210.8(A)(2) puts GFCI on *receptacles* in a
    # garage, and CKT-GAR-HEAT therefore carries no GFCI. Plugging this into the wall
    # instead would drag it onto CKT-RC-GARAGE's GFCI protection and off its own circuit.
    Equipment(uid="CEE023AAAA", tag="EQ-G-HEATER", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(0, 5), ft(48)), footprint=(inch(14), inch(9)),
              room="RM-GARAGE", type_ref="EQ-T-GARAGE-HEATER", rotation=deg(90),
              circuit="CKT-GAR-HEAT",
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
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
# NEC 210.52(A) fill for the second storey, re-snapped after the partitions moved onto the
# survey (storeys/second.py). Positions are the *resolved room boundaries*, walked with the
# same arc-length maths `electrical.receptacle_spacing` uses, 1 1/2" inside each finished
# face: none of these devices carries `room=`, so a stale coordinate more than 19 5/8"
# (`_NEAR_WALL_M`) off simply stops counting toward the room and nothing reports it.
NEC_FILL_SECOND = [
    ElectricalDevice(uid="NEC021AAAA", tag="ED-S-PLANT-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(15.89), ft(0.12)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC022AAAA", tag="ED-S-PLANT-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(5.85), ft(0.15)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC023AAAA", tag="ED-S-PLANT-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.18), ft(4.54)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC024AAAA", tag="ED-S-PLANT-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(5.93), ft(8.85)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC025AAAA", tag="ED-S-PLANT-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(15.97), ft(8.88)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC026AAAA", tag="ED-S-STUDY2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.17), ft(0.79)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC027AAAA", tag="ED-S-STUDY2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.17), ft(7.78)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC028AAAA", tag="ED-S-STUDY2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.13), ft(8.83)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC029AAAA", tag="ED-S-STUDY2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.09), ft(8.89)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC062AAAA", tag="ED-S-STUDY2-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.83), ft(0.64)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC063AAAA", tag="ED-S-STUDY2-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(27.37), ft(0.18)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC030AAAA", tag="ED-S-BED1-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.84), ft(17.18)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC031AAAA", tag="ED-S-BED1-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33.24), ft(9.14)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC032AAAA", tag="ED-S-BED1-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.61), ft(9.12)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC034AAAA", tag="ED-S-BED2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.84), ft(26.26)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC035AAAA", tag="ED-S-BED2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33.32), ft(18.14)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC036AAAA", tag="ED-S-BED2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.7), ft(18.12)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC038AAAA", tag="ED-S-BED3-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(32.33), ft(35.85)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC039AAAA", tag="ED-S-BED3-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.83), ft(28.72)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC040AAAA", tag="ED-S-BED3-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.82), ft(27.16)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC042AAAA", tag="ED-S-SUITE-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13.08), ft(12.53)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC043AAAA", tag="ED-S-SUITE-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(6.42), ft(9.16)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC044AAAA", tag="ED-S-SUITE-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0.18), ft(12.99)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC045AAAA", tag="ED-S-SUITE-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(1.06), ft(22.2)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC046AAAA", tag="ED-S-SUITE-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9.57), ft(20.53)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
# Same treatment for the attic's two habitable rooms. RM-A-WEST (media) and RM-A-DEN
# (storage) are outside `_HABITABLE`, so 210.52 spacing is not evaluated for them.
NEC_FILL_ATTIC = [
    ElectricalDevice(uid="NEC048AAAA", tag="ED-A-EAST-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.14), ft(13.69)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC049AAAA", tag="ED-A-EAST-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.18), ft(24.07)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC050AAAA", tag="ED-A-EAST-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19.45), ft(35.84)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC051AAAA", tag="ED-A-EAST-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29.94), ft(35.83)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC052AAAA", tag="ED-A-EAST-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.86), ft(31.27)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC053AAAA", tag="ED-A-EAST-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.83), ft(20.8)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC054AAAA", tag="ED-A-EAST-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.87), ft(10.31)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC055AAAA", tag="ED-A-EAST-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.53), ft(9.18)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC056AAAA", tag="ED-A-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26.37), ft(8.82)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC057AAAA", tag="ED-A-STUDY-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.83), ft(8.28)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC058AAAA", tag="ED-A-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33.9), ft(0.12)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC059AAAA", tag="ED-A-STUDY-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(23.87), ft(0.15)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC060AAAA", tag="ED-A-STUDY-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.18), ft(4.53)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]

BASEMENT_ELEMENTS = [*BACKUP_ENCLOSURE, *BASEMENT_DEVICES, *BASEMENT_EQUIPMENT,
                     *CONDUIT_TRUNKS, *NEC_FILL_BASEMENT]
MAIN_ELEMENTS = [*SERVICE_DEVICES, *MAIN_DEVICES, *MAIN_EQUIPMENT, *NEC_FILL_MAIN]
GARAGE_ELEMENTS = [*GARAGE_DEVICES, *GARAGE_EQUIPMENT]
SECOND_ELEMENTS = [*SECOND_DEVICES, *NEC_FILL_SECOND]
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP, *NEC_FILL_ATTIC]
