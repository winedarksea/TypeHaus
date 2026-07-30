# haus: editable
# Catlin electrical service upgrade (plans/electrical_notes.md): 200A service with a
# separate meter, 225A panel (type in plan/mep.py), 240V appliance circuits, two EV
# receptacles in the garage, the smart-relay backup subsystem's DIN enclosure, hot tub +
# heat-pump disconnects, and the PV junction box beside the radon-vent riser.
#
# All-electric house: no gas service, no furnace. Heat is the three Gree heat-pump systems
# below plus the electric radiant floor zones (FloorHeat in plan/storeys/):
#   System 1  EQ-M-HP1-OD (Vireo GEN3) -> EQ-S-HP1-AH, the concealed ducted air handler in
#             RM-S-STUDY2 feeding the dropped hallway chase (plan/mep.py) — upstairs + the
#             two attic branches.
#   System 2  EQ-M-HP2-OD (Multi Ultra 3-port, -22F) -> three wall heads: EQ-B-HP2-GYM,
#             EQ-M-HP2-BED, EQ-M-HP2-LIVING.
#   System 3  EQ-M-HP3-OD (Sapphire R32, VFD soft start, backup battery circuit) ->
#             EQ-M-HP3-STAIR, recessed into W-M-STRW to reach the mudroom too.
# EQ-B-ERV is still the only thing that moves *ventilation* air — its "supply" is fresh
# air, not heat.
#
# Condensate: each head/air handler drains to a collected air-gap drain line into the
# mechanical-room sink — a planned plumbing item, no geometry yet (see plan/mep.py).
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
    # The 14-50 is the managed EVSE outlet: an Emporia Vue with dynamic load management
    # (whole-panel CT sensing) throttles the charger so the EV group never pushes the
    # service over its ceiling. The EMS arrangement itself is LM-EV in plan/circuits.py
    # (NEC 625.42); load_va here stays the unmanaged continuous rating so the panel
    # schedule still shows the connected load the conductors are sized for.
    ElectricalDeviceType(tag="ED-T-EV-1450",
                          name="EV receptacle, NEMA 14-50R (Emporia Vue managed EVSE)",
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
    # "Supply" is fresh air, not heat: the ERV trunks in plan/mep.py connect to these two
    # ports — a SUPPLY/RETURN pair on the main and basement storeys (DU-M1-, DU-B-ERV-
    # SUP/RET), stale-air-only trunks on the second storey and attic (DU-M-ERV-RET,
    # DU-A-ERV-RET), whose rooms take fresh air off the heat-pump chase (DU-S-HP-SUP /
    # DU-S-HP-SUITE) instead, and DU-S-ERV-HP-FEED, the 6" fresh feed that wyes into the
    # chase's return plenum behind REG-S-HP-RET so System 1 recirculates ERV-fresh air
    # without the two machines being hard-coupled. (The outdoor-side intake and exhaust are the ERV's other pair of
    # collars; `Service` has no OUTDOOR_AIR/EXHAUST_AIR member to name them with, so they
    # stay unmodeled rather than mislabeled as house-side ports.)
    # ventilation_cfm is the continuous balanced rate the trunks in plan/mep.py are sized
    # for: ASHRAE 62.2 at 0.03 x 5,078 ft2 + 7.5 x (5 bedrooms + 1) = ~197 cfm. The
    # sensible recovery effectiveness is what the block load's ventilation term turns on —
    # at 197 cfm and an 85 F design ΔT, every 0.05 of SRE is ~2,000 Btu/h — so it is the
    # one number here that most needs the datasheet.
    EquipmentType(tag="EQ-T-ERV", name="ERV, 240V", footprint=(inch(24), inch(24)), height=inch(30),
                  plan_symbol="erv",
                  ventilation_cfm=197,  # TODO verify datasheet
                  sensible_recovery_effectiveness=0.75,  # TODO verify datasheet
                  source="Airflow is the computed ASHRAE 62.2 whole-house rate; SRE 0.75 is a REPRESENTATIVE PLACEHOLDER for a good residential ERV core. TODO verify datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(24))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(24))))),
    # --- The three Gree heat-pump systems (plans/TODO.md §HVAC) ----------------------
    #
    # EVERY CAPACITY BELOW IS A REPRESENTATIVE FIGURE FOR ITS PRODUCT CLASS, NOT A
    # DATASHEET READING. Each carries `# TODO verify datasheet` and its `source` says so.
    # The at-design column is the *authored derate* at the site's -15 F heating design
    # temperature (plan/site.py): the model does no performance-curve interpolation, so a
    # wrong number here is a wrong number in mep.heating_capacity — check them before
    # anything is ordered.
    #
    # System 1 — Gree Slim concealed ducted indoor unit in RM-S-STUDY2, feeding the
    # dropped hallway chase north to the bedrooms and the two attic branches; Vireo GEN3
    # outdoor unit. A straight-run duct at low flow, which is why one 24k head covers the
    # whole upstairs.
    EquipmentType(tag="EQ-T-GREE-SLIM24",
                  name="Gree Slim concealed ducted air handler, 24k",
                  footprint=(inch(43), inch(21)), height=inch(11),
                  cooling_capacity_btuh=24000,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — 2-ton concealed-ducted class. The indoor unit carries no heating rating here on purpose: the outdoor unit is what has to make heat at design temp, and mep.heating_capacity sizes the zone against EQ-T-GREE-VIREO-GEN3. TODO verify datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(11))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(11))))),
    EquipmentType(tag="EQ-T-GREE-VIREO-GEN3",
                  name="Gree Vireo GEN3 outdoor unit, 24k",
                  footprint=(inch(38), inch(16)), height=inch(32),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=27000,  # TODO verify datasheet
                  heating_capacity_at_design_btuh=16500,  # TODO verify datasheet
                  cooling_capacity_btuh=24000,  # TODO verify datasheet
                  min_operating_temp_f=-4.0,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — 2-ton cold-climate inverter class (~27,000 Btu/h at 47F, ~16,500 Btu/h at -15F, rated to -4F). The Vireo is NOT the -22F unit; the Multi Ultra below is. TODO verify datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # System 2 — Gree Multi Ultra, one 3-port outdoor unit driving three wall-mount heads
    # (basement gym, main-floor suite bedroom, living room). Rated to -22 F, which is what
    # makes it the unit carrying the three coldest-exposure rooms.
    EquipmentType(tag="EQ-T-GREE-MULTI-U30",
                  name="Gree Multi Ultra 3-port outdoor unit, 30k (-22F)",
                  footprint=(inch(37), inch(16)), height=inch(34),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=32000,  # TODO verify datasheet
                  heating_capacity_at_design_btuh=22000,  # TODO verify datasheet
                  cooling_capacity_btuh=30000,  # TODO verify datasheet
                  min_operating_temp_f=-22.0,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — 2.5-ton 3-port multi class (~32,000 Btu/h at 47F, ~22,000 Btu/h at -15F, rated to -22F). TODO verify datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # The heads themselves: no heating rating, by design. A multi's three heads share one
    # compressor, so three head ratings summed would size the zone against a capacity the
    # outdoor unit cannot deliver simultaneously. Their nominal cooling capacity is kept
    # because it is what distinguishes the 9k from the 12k on a schedule.
    EquipmentType(tag="EQ-T-GREE-HEAD-9", name="Gree wall-mount head, 9k",
                  footprint=(inch(32), inch(8)), height=inch(12),
                  cooling_capacity_btuh=9000,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — 9k wall-mount head on EQ-T-GREE-MULTI-U30. TODO verify datasheet.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-HEAD-12", name="Gree wall-mount head, 12k",
                  footprint=(inch(35), inch(9)), height=inch(12),
                  cooling_capacity_btuh=12000,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — 12k wall-mount head on EQ-T-GREE-MULTI-U30. TODO verify datasheet.",
                  ports=()),
    # System 3 — Gree Sapphire R32, the high-efficiency unit over the stairs. True VFD
    # inverter: the soft start is why this is the one system on the backup battery circuit
    # (a hard-starting compressor is what a battery inverter cannot carry).
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9",
                  name="Gree Sapphire R32 wall-mount head, 9.1k (VFD soft start)",
                  footprint=(inch(33), inch(8)), height=inch(12),
                  cooling_capacity_btuh=9100,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — Sapphire-class 9,100 Btu/h head with a true VFD inverter (soft start, hence the backup-battery circuit). Heating is rated on EQ-T-GREE-SAPPHIRE-9-OD. TODO verify datasheet.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9-OD",
                  name="Gree Sapphire R32 outdoor unit, 9.1k (-22F)",
                  footprint=(inch(31), inch(13)), height=inch(23),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=12000,  # TODO verify datasheet
                  heating_capacity_at_design_btuh=8000,  # TODO verify datasheet
                  cooling_capacity_btuh=9100,  # TODO verify datasheet
                  min_operating_temp_f=-22.0,  # TODO verify datasheet
                  source="REPRESENTATIVE PLACEHOLDER — Sapphire-class 9.1k outdoor unit (~12,000 Btu/h at 47F, ~8,000 Btu/h at -15F, rated to -22F). TODO verify datasheet.",
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
    # Garage infrared heater lamp — same 1,500 W / 120V / 20A arithmetic as the fireplace.
    # It is hard-wired equipment rather than a fan-forced unit; RM-GARAGE stays
    # `conditioned=False` and therefore out of the 3 VA/ft2 general-lighting area.
    EquipmentType(tag="EQ-T-GARAGE-HEATER", name="Garage infrared heater lamp, 1.5 kW, 120V",
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
    # RM-B-BATH's required receptacle (2026-07-30, NEC 210.52(D)): GFCI, on the wall adjacent
    # to the basin and within 3'-0" of its outside edge — 1'-0" here, on the north partition
    # just west of the lavatory (which occupies y 19'-0"..21'-0" against the east wall). It
    # cannot go on the east wall itself: that is 12" cast concrete with the basin against it.
    # On CKT-RC-BSMT with the basement's other receptacles rather than its own 20A circuit,
    # which is the trade this house already made for the panel it has (see plans/TODO.md's
    # open panel_spaces item — nothing here adds a slot).
    ElectricalDevice(uid="CEE040AAAA", tag="ED-B-BATH-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 4), ft(21, 4)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-BSMT", room="RM-B-BATH", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
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
    # System 2's basement head: high on the east face of the centre bearing wall at x=18',
    # near the gym ceiling (plans/TODO.md §HVAC), backs west (rotation 90) so it throws east
    # across the open gym. Its zone is the whole conditioned basement — the sauna's own
    # EQ-B-SAUNA-HTR is a sauna heater, not space heat, and the basement is one open volume
    # off the stair.
    Equipment(uid="CEE031AAAA", tag="EQ-B-HP2-GYM", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(18, 6), ft(9)), footprint=(inch(32), inch(8)),
              room="RM-B-GYM", type_ref="EQ-T-GREE-HEAD-9", rotation=deg(90),
              outdoor_ref="EQ-M-HP2-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6)),
              zone_rooms=("RM-B-GYM", "RM-B-PLAY-N", "RM-B-STAIR", "RM-B-WORKSHOP",
                          "RM-B-SAUNA", "RM-B-FURNACE", "RM-B-BATH")),
    Equipment(uid="CEE020AAAA", tag="EQ-B-SAUNA-HTR", kind=EquipmentKind.SAUNA_HEATER,
              position=pt(ft(9, 9.8125), ft(8, 9)), footprint=(inch(18), inch(16)),
              room="RM-B-SAUNA", type_ref="EQ-T-SAUNA-HEATER", rotation=deg(90),
              circuit="CKT-SAUNA"),
]

# --- Main storey: dryer, freezer, heat-pump condensers/heads + disconnects ------------
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
    # System 3 (Sapphire, backup battery circuit): its outdoor unit stands on the north
    # side beside the mudroom door, so the disconnect goes on W-M-N2's exterior face west
    # of the breezeway — clear of ED-M-HP1-DISC's condenser gap.
    ElectricalDevice(uid="CEE026AAAA", tag="ED-M-HP3-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(4), ft(36.4)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP3",
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
    # --- Outdoor units. `zone_rooms` is empty on all three: a condenser's zone is the
    # union of its indoor units' rooms, and each head/air handler below names its condenser
    # with `outdoor_ref`. Refrigerant linesets are deliberately not modeled — the pairing
    # IS the record (plans/TODO.md), and there is no wall penetration riding on it yet.
    # System 3's outdoor unit, north side beside the mudroom door and under
    # ED-M-HP3-DISC — the short lineset run to the head over the stairs is why it is here
    # and not out with the other two.
    Equipment(uid="CEE027AAAA", tag="EQ-M-HP3-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(m(2.50437), m(11.4357)), footprint=(inch(31), inch(13)),
              type_ref="EQ-T-GREE-SAPPHIRE-9-OD", circuit="CKT-HP3", room=None),
    # --- System 2's main-floor heads. Both hang high on the south wall either side of the
    # centre wall at x=18' (plans/TODO.md §HVAC), backs south (rotation 180), blowing north
    # into the length of the room. Power comes from the outdoor unit on a multi, so neither
    # head carries a `circuit` — CKT-HP2 feeds EQ-M-HP2-OD and the interconnects run from
    # there.
    Equipment(uid="CEE028AAAA", tag="EQ-M-HP2-BED", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(16), ft(0, 6)), footprint=(inch(35), inch(9)),
              room="RM-M-BED", type_ref="EQ-T-GREE-HEAD-12", rotation=deg(180),
              outdoor_ref="EQ-M-HP2-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6)),
              # The west half of the main floor: the suite bedroom and everything off it.
              zone_rooms=("RM-M-BED", "RM-M-BATH1", "RM-M-BATH2", "RM-M-CLOSET",
                          "RM-M-LAUNDRY", "RM-M-STUDY")),
    Equipment(uid="CEE029AAAA", tag="EQ-M-HP2-LIVING", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(20), ft(0, 6)), footprint=(inch(35), inch(9)),
              room="RM-M-LIVING", type_ref="EQ-T-GREE-HEAD-12", rotation=deg(180),
              outdoor_ref="EQ-M-HP2-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6)),
              # One 768 sf open room (kitchen/dining/living/hall, and since 2026-07-30 the
              # stair well too, are all inside this claim).
              zone_rooms=("RM-M-LIVING",)),
    # --- System 3's head: over the stair head, partly recessed into W-M-STRW (the bearing
    # wall at x=10' between the stair and the mudroom) so one unit reaches both spaces —
    # the cutout in that wall is the whole point of the position. Backs west (rotation 90)
    # against the wall, high enough to clear the stair opening below it.
    #
    # `room` followed RM-M-STAIR into RM-M-LIVING on 2026-07-30 — the stair well is part of
    # that room now (see main.py's ROOMS), and the head still hangs in the same place over
    # it. `zone_rooms` did not: it is the mudroom and the mech closet. What this head is
    # *sized* for is the entry side of the wall it is recessed in, and the stair volume it
    # also blows into belongs to EQ-M-HP2-LIVING's 768 sf claim rather than being counted a
    # second time here.
    Equipment(uid="CEE030AAAA", tag="EQ-M-HP3-STAIR", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(10, 6), ft(30)), footprint=(inch(33), inch(8)),
              room="RM-M-LIVING", type_ref="EQ-T-GREE-SAPPHIRE-9", rotation=deg(90),
              outdoor_ref="EQ-M-HP3-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7),
                          recessed_into_host_surface=True),
              zone_rooms=("RM-M-MUDROOM", "RM-M-MECH")),
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
    # NEC 440.14 disconnects for the two condensers on the upper balcony. They sit on
    # the second-storey south wall behind the units, within sight from the balcony door
    # while staying clear of D-S-DECK-E's 5' French-door opening at x=18'-10"..23'-10".
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-HP1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(11), ft(0, 6)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP1", mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-HP2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(15), ft(0, 6)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP2", mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # FH-S-BATH1's thermostat, inside the room on its south wall (W-S-BD-N1B, interior
    # face y=26'-4 11/16"), 9" west of D-S-BATH1's opening (x 7'-3"..9'-9"). Same
    # reach-as-the-door-shuts position as ED-M-BATH2-FH-STAT, and clear of the fixture
    # cluster, which all sits north of y=29'-9".
    ElectricalDevice(uid="CEE025AAAA", tag="ED-S-BATH1-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 6), ft(26, 5)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH1", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

SECOND_EQUIPMENT = [
    # The Vireo (System 1, the concealed ducted upstairs unit) and the Multi Ultra
    # (System 2) share the upper balcony, not the main-level porch. The balcony's walking
    # surface is the second-storey datum (10'); keeping these in SECOND_ELEMENTS gives the
    # 3D model that elevation rather than drawing them at grade. Both sit west of the
    # French-door opening, with their 16" deep cabinets aligned east-west across the deck.
    Equipment(uid="CEE017AAAA", tag="EQ-M-HP1-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(m(2.98655), m(-0.527314)), footprint=(inch(38), inch(16)),
              type_ref="EQ-T-GREE-VIREO-GEN3", circuit="CKT-HP1", room=None),
    Equipment(uid="CEE018AAAA", tag="EQ-M-HP2-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(m(4.19103), m(-0.538707)), footprint=(inch(37), inch(16)),
              type_ref="EQ-T-GREE-MULTI-U30", circuit="CKT-HP2", room=None),
    # System 1's concealed ducted air handler, INSIDE SF-S-DUCT's dropped box at the south
    # end of the full hallway trunk (2026-07-30). It cannot go in the floor structure: the
    # case is 21" wide x 11" deep and an 11 7/8" I-joist bay at 16" o.c. offers ~14 1/2"
    # clear — and the old spot at (21', 7') with the 43" side running east reached
    # x=22'-8 1/2", 18" inside FO-A-STAIR's framed opening (x starts 21'-2"), i.e. hanging
    # in the attic stairwell. The soffit box is the one cavity that actually holds it:
    # 14" drop x 30 3/4" clear takes the 11" x 21" case with room for the lining. Long
    # side now runs along the hall (footprint 21" x 43", y 6'-0"..9'-7"), west of the
    # stair opening by 5 1/2"; discharge faces north into DU-S-HP-SUP at y=9'-7",
    # bottom-return at the rear through REG-S-HP-RET's plenum stub (plan/mep.py). Ceiling
    # mount: it hangs at the ceiling plane, the case dropping into the box below it.
    # This is the one indoor unit with its own branch circuit (CKT-HP1-AH): a ducted
    # unit's blower is fed at the unit, not from the condenser the way a multi's heads
    # are.
    #
    # zone_rooms is the whole conditioned second storey plus the three attic rooms served:
    # RM-A-STUDY and RM-A-EAST off the two short attic branches, RM-A-WEST off the suite
    # branch's REG-A-HP-WEST floor boot (2026-07-30). RM-A-DEN is deliberately NOT in it —
    # nothing serves it, and mep.heating_capacity reports it as unclaimed rather than
    # pretending this unit carries it (plans/TODO.md).
    Equipment(uid="CEE032AAAA", tag="EQ-S-HP1-AH",
              kind=EquipmentKind.DUCTED_AIR_HANDLER,
              position=pt(ft(19, 10), ft(7, 9.5)), footprint=(inch(21), inch(43)),
              room="RM-S-STUDY2", type_ref="EQ-T-GREE-SLIM24",
              outdoor_ref="EQ-M-HP1-OD", circuit="CKT-HP1-AH",
              mount=Mount(kind=MountKind.CEILING),
              zone_rooms=("RM-S-STUDY2", "RM-S-PLANT", "RM-S-BED1", "RM-S-BED2",
                          "RM-S-BED3", "RM-S-SUITE", "RM-S-SUITEBATH", "RM-S-VANITY",
                          "RM-S-BATH1", "RM-S-HALL", "RM-S-CLOSET", "RM-S-NCLOSET",
                          "RM-A-EAST", "RM-A-STUDY", "RM-A-WEST")),
]

# --- Garage: both EV receptacles on the south wall, east of the service door ----------
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(m(0.256331), m(17.0886)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE"),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(m(6.08013), m(12.6631)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE"),
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
              position=pt(m(0.227899), m(14.595)), footprint=(inch(14), inch(9)),
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
    # Across the basement ceiling to the kitchen's east counter wall — still the east wall
    # after the 2026-07-30 range/sink swap, since KGF3 (the device this feeds) stayed the
    # east-wall device; its position along that wall moved twice since, with the cooking run
    # and then with the range/N3 flip.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(28, 11))),
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
                     # On the east wall's BESTA run; keep the plan position for spacing, but
                     # raise it into the backsplash zone above the 29 3/4" cabinet line.
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36))),
    ElectricalDevice(uid="NEC011AAAA", tag="ED-M-LIVING-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(5.53)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     # Same east-wall BESTA condition as RC3: 36" puts the box above the
                     # countertop while preserving the receptacle's wall-space location.
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36))),
    ElectricalDevice(uid="NEC012AAAA", tag="ED-M-LIVING-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30.03), ft(0.05)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC061AAAA", tag="ED-M-LIVING-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35.95), ft(23.70)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # Fills the >6' gap electrical.receptacle_spacing flags on the centre bearing wall
    # between RC2 (y=15.87) and the wall's south end, on the LIVING face.
    ElectricalDevice(uid="NEC064AAAA", tag="ED-M-LIVING-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18.05), ft(21.10)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # The old hall band, 2026-07-28. Opening the centre line under BM-M-HALL merged
    # RM-M-HALL into this room, and a hallway's walls are exempt from 210.52(A) only while
    # they *are* a hallway — as habitable-room wall space the same 6'/12' rule reaches them,
    # and the band had no receptacles at all. Positions are the four gaps
    # `electrical.receptacle_spacing` measured on the merged clear face, each 0.05' off its
    # wall like the fills above.
    # y flipped to W-M-HS1's south (living) face (2026-07-28): W-M-BAE's 2' east shift
    # extended W-M-HS1 to x=6', and the north face at this x is now inside RM-M-BATH1.
    ElectricalDevice(uid="NEC066AAAA", tag="ED-M-LIVING-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(5.40), ft(21.56)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # y flipped to W-M-STOS's north (mudroom) face (2026-07-28): W-M-BAE's 2' east shift
    # extended W-M-STOS's south face — where this device sat — into RM-M-BATH1.
    ElectricalDevice(uid="NEC067AAAA", tag="ED-M-LIVING-RC9", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4.55), ft(26.43)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC068AAAA", tag="ED-M-LIVING-RC10", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9.50), ft(26.23)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # On the 10 3/16" pier at W-M-STRS's east end, between D-M-STAIR and the well partition
    # the wall dies into — the only wall left on that face, and a useful one to have at the
    # head of the stairs.
    ElectricalDevice(uid="NEC069AAAA", tag="ED-M-LIVING-RC11", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13.85), ft(25.73)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # Fills the >6' gap electrical.receptacle_spacing opened on the hall band between RC7/
    # STUDY-RC3 and the door into RM-M-STOS (2026-07-29): N-M-W2/N-M-C2 pushed 6" north
    # for the BATH2 wall move, stretching this door-to-door wall space past the 6' rule.
    # Positioned centred in that space (the door itself brackets the run at 13'-9" east).
    ElectricalDevice(uid="NEC070AAAA", tag="ED-M-LIVING-RC12", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(16, 1.2), ft(22, 2.6)), type_ref="ED-T-RECEPTACLE",
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
    # Fills the >6' gap electrical.receptacle_spacing flags on the centre bearing wall,
    # on the STUDY face opposite ED-M-LIVING-RC7.
    ElectricalDevice(uid="NEC065AAAA", tag="ED-M-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17.95), ft(21.10)), type_ref="ED-T-RECEPTACLE",
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
                     position=pt(m(0.0519211), m(1.41351)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), room="RM-S-PLANT"),
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
SECOND_ELEMENTS = [*SECOND_DEVICES, *SECOND_EQUIPMENT, *NEC_FILL_SECOND]
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP, *NEC_FILL_ATTIC]
