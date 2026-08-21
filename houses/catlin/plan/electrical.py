# haus: editable
# Catlin electrical service upgrade (plans/electrical_notes.md): 200A service, separate
# meter, 225A panel (plan/mep.py), 240V appliance circuits, two garage EV receptacles, the
# backup subsystem's DIN enclosure, hot tub + heat-pump disconnects, PV junction box.
#
# All-electric: no gas, no furnace. Three Gree heat-pump systems plus electric radiant
# floor zones (FloorHeat in plan/storeys/):
#   System 1  EQ-M-HP1-OD (Vireo GEN3) -> EQ-S-HP1-AH, concealed ducted AH in RM-S-STUDY2
#             feeding the dropped hallway chase — upstairs + two attic branches.
#   System 2  EQ-M-HP2-OD (Multi Ultra 3-port, -22F) -> EQ-B-HP2-GYM, EQ-M-HP2-BED,
#             EQ-M-HP2-LIVING.
#   System 3  EQ-M-HP3-OD (Sapphire R32, VFD soft start, backup battery circuit) ->
#             EQ-M-HP3-STAIR, stair well NW corner on W-M-N2. Mudroom reached via
#             REG-M-XFER-MUD, a passive louver in W-M-STRW (moved off that wall 2026-08-15).
# EQ-B-ERV moves *ventilation* air only — its "supply" is fresh air, not heat.
#
# Condensate: each head/AH drains via a collected air-gap line to the mech-room sink —
# planned plumbing, no geometry yet.
#
# Instances only, explicit constructors (UI drags round-trip). Circuit assignments live in
# plan/circuits.py; `circuit=` strings here are the join keys. Uids avoid I/L/O/U
# (Crockford base32, model/ids.py).
#
# A device position is a *face* position (2026-08-03): the point sits half the device's
# depth off the finish plane (back on the plane, plate proud of it), `rotation` turns the
# plate along the wall. Nothing in the resolver pulls a device onto its wall, so a box
# authored on the wall axis buries in the studs and one authored a few feet in floats in
# mid-air — both were widespread until this convention. Enforced by
# `test_catlin_contract_m3.py::test_wall_mounted_devices_resolve_against_a_wall_face`,
# except ED-M-LIVING-KGF4 (mounts on the island, not a Wall) and ED-M-PORCH-FLOOD (a
# pillar). CATLIN_EXT_2X6's inside face is 6 5/8" in from the sheathing datum, cladding
# face 5" outboard of that.
#
# Positions worth knowing (project-north frame, house sheathing SW corner at 0,0):
# - Meter: exterior face of west wall (W-M-W1), outside ED-B-PANEL at (2', 29') in the
#   basement — shortest run from the underground POWER entry at (0', 18').
# - Garage south wall W-G-S at y=41', service door at x=5'-8'; both EV receptacles east
#   of it, clear of the door swing.
# - Sunken-garden porch: west wall W-SG-W1 axis x=8', inner face x=8.5', north end
#   y=-0.833'. Hot tub disconnect 7' south of that, under the deck — basement storey, so
#   Mount elevation 5' is -4' absolute.
# - PV junction box on the north gable (W-A-N2) beside the radon riser clamp cluster; at
#   x=9' the 4:12 rake carries siding to 28', so 25'-6" absolute has cladding to grip.

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
    SleevePenetration,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

DEVICE_TYPES = (
    # `service_amps` (2026-08-15) is the service size as data, not just in the product name:
    # it's what 220.82 demand is compared against (was a hardcoded 200 in
    # takeoff/electrical.py before). Distinct from the panel's `bus_amps` — the 225A bus
    # behind this 200A meter is what NEC 705.12 measures a backfeed against.
    ElectricalDeviceType(tag="ED-T-METER", name="200A meter socket (meter separate from panel)",
                          service_amps=200,
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
    # The managed EVSE outlet: an Emporia Vue (whole-panel CT sensing, NEC 625.42) throttles
    # it so the EV group never pushes the service over its ceiling — that EMS is LM-EV in
    # plan/circuits.py. load_va stays the unmanaged continuous rating so the schedule shows
    # what the conductors are sized for.
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
    # Radiant-floor thermostat: line-voltage control for the mat's cold lead. `DeviceKind`
    # has no THERMOSTAT member (would fall through the IFC map to IfcBuildingElementProxy);
    # SWITCH maps to IfcSwitchingDevice, which is what this really is.
    # No `load_va`: one type serves three zones of different sizes, so a single figure would
    # be wrong. VA is authored per-zone on the circuit in plan/circuits.py instead, which is
    # what `takeoff.electrical._connected_va` prefers anyway.
    ElectricalDeviceType(tag="ED-T-FLOOR-STAT", name="Radiant floor thermostat, 120V",
                          footprint=(inch(4), inch(2)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    # --- structured cabling (plans/electrical_notes.md: "WiFi (energy efficient, POE") ----
    # All three are DeviceKind.DATA_OUTLET (plan-symbol axis only); `ifc_entity`/
    # `ifc_predefined_type` carry what each one *is*, so they reach Revit as Communication
    # Devices rather than proxies — future PoE cameras are just another entry here.
    # The enclosure (router + PoE switch + patch field, on CKT-HA) is the only one of the
    # three fed from a branch circuit; the APs draw power over their data cables (poe_watts,
    # no `circuit`), so the panel schedule can't see them — E-603 totals them instead.
    ElectricalDeviceType(tag="ED-T-NET-ENCLOSURE",
                          name="Structured media enclosure, 28in (router + PoE switch + patch)",
                          footprint=(inch(15), inch(4)), height=inch(28),
                          ifc_entity="IfcCommunicationsAppliance",
                          ifc_predefined_type="NETWORKHUB",
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),
                                 ServicePort(tag="data", service=Service.DATA,
                                             position=(ft(0), ft(0), ft(0))),)),
    # 15 W is the 802.3af class-4 ceiling a Wi-Fi 6/6E ceiling AP draws under load; the
    # allowance already carried in plan/circuits.py said the same number before there was
    # anywhere to put it.
    ElectricalDeviceType(tag="ED-T-AP-CEILING",
                          name="Wireless access point, ceiling, PoE 802.3af",
                          poe_watts=15.0,
                          footprint=(inch(8), inch(8)), height=inch(2),
                          ifc_entity="IfcCommunicationsAppliance",
                          ifc_predefined_type="NETWORKAPPLIANCE",
                          ports=(ServicePort(tag="data", service=Service.DATA,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-AP-OUTDOOR",
                          name="Wireless access point, outdoor wet-rated, PoE 802.3af",
                          poe_watts=15.0,
                          footprint=(inch(9), inch(9)), height=inch(3),
                          ifc_entity="IfcCommunicationsAppliance",
                          ifc_predefined_type="NETWORKAPPLIANCE",
                          ports=(ServicePort(tag="data", service=Service.DATA,
                                             position=(ft(0), ft(0), ft(0))),)),
)

EQUIPMENT_TYPES = (
    # RM-B-SAUNA's heated zone is ~513 cf; trade rule ~1kW/45-50cf wants 9-10.5 kW, matching
    # the detail notes' "240V, 50A GFCI breaker ... max 10.5 kW".
    EquipmentType(tag="EQ-T-SAUNA-HEATER", name="Electric sauna heater, 9 kW",
                  footprint=(inch(18), inch(16)), height=inch(30),
                  plan_symbol="sauna-heater",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Only air-moving equipment in the house (no furnace/air handler), so the SUPPLY_AIR/
    # RETURN_AIR ports live here. "Supply" is fresh air, not heat: plan/mep.py's ERV trunks
    # connect to these two ports across all four storeys (see mep.py for the branch layout);
    # outdoor-side intake/exhaust stay unmodeled since `Service` has no OUTDOOR_AIR/
    # EXHAUST_AIR member.
    # ventilation_cfm is the ASHRAE 62.2 continuous balanced rate the trunks are sized for
    # (0.03 x conditioned ft2 + 7.5 x (bedrooms+1)). Bumped 197 -> 210 (2026-08-01) when
    # conditioned area drift (5,078 -> 5,115 ft2) put code.N1103_6 one cfm short; 210 rounds
    # up with headroom for the next ~400 ft2 of growth. Still quiet: ~505 fpm through the
    # 10x6 trunk.
    # sensible_recovery_effectiveness drives the block load's ventilation term (0.05 SRE ~=
    # 2,000 Btu/h at this rate and 85F design ΔT) — the number most needing the datasheet.
    EquipmentType(tag="EQ-T-ERV", name="ERV, 240V", footprint=(inch(24), inch(24)), height=inch(30),
                  plan_symbol="erv",
                  ventilation_cfm=210,  # TODO verify datasheet
                  sensible_recovery_effectiveness=0.75,  # TODO verify datasheet
                  source="Airflow is the computed ASHRAE 62.2 whole-house rate; SRE 0.75 is a REPRESENTATIVE PLACEHOLDER for a good residential ERV core. TODO verify datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(24))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(24))))),
    # --- The three Gree heat-pump systems (plans/TODO.md §HVAC) ----------------------
    # Outdoor units carry real Gree datasheet capacities (model # in each `source`), not
    # placeholders. `heating_capacity_at_design_btuh` linearly interpolates the datasheet
    # chart points bracketing the site's -15F design temp (plan/site.py) — the model does no
    # curve interpolation itself, so this field is the authored derate mep.heating_capacity
    # sizes each zone against. Indoor heads keep `# TODO verify datasheet` on purpose: they
    # carry no heating rating by design (a multi's heads share one compressor).
    #
    # System 1 — Gree Slim concealed ducted unit in RM-S-STUDY2 feeding the dropped hallway
    # chase to bedrooms + two attic branches; Vireo GEN3 outdoor unit. One 24k head covers
    # the whole upstairs via a straight low-flow duct run.
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
                  heating_capacity_btuh=27000,
                  heating_capacity_at_design_btuh=13500,
                  cooling_capacity_btuh=22000,
                  min_operating_temp_f=-22.0,
                  source="Gree VIR24HP230V1R32AO (R32 refrigerant). Datasheet chart: 27,000 Btu/h at 47F (the 47F rating holds despite the smaller at-design number below because this outdoor unit is paired with the EQ-T-GREE-SLIM24 slim-duct air handler, not a wall head), ~16,100-16,500 Btu/h at 5F, ~14,200 Btu/h at -13F, ~12,000 Btu/h at -22F. -15F at-design (13,500 Btu/h) is linearly interpolated between the -13F and -22F chart points and additionally derated for slim-duct static-pressure loss. Cooling is the conservative end of the published 22,000-24,000 Btu/h range. min_operating_temp_f -22F per datasheet operating envelope.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # System 2 — Gree Multi Ultra, one 3-port outdoor unit driving three wall-mount heads
    # (basement gym, main-floor suite bedroom, living room). Rated to -22 F, which is what
    # makes it the unit carrying the three coldest-exposure rooms.
    EquipmentType(tag="EQ-T-GREE-MULTI-U30",
                  name="Gree Multi Ultra 3-port outdoor unit, 30k (-22F)",
                  footprint=(inch(37), inch(16)), height=inch(34),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=30000,
                  heating_capacity_at_design_btuh=23500,
                  cooling_capacity_btuh=28400,
                  min_operating_temp_f=-22.0,
                  source="Gree MUL30HP230V1R32AO. Datasheet chart: 30,000 Btu/h at 47F, 27,000 Btu/h at 5F, ~24,500 Btu/h at -13F, ~21,500 Btu/h at -22F. -15F at-design (23,500 Btu/h) is linearly interpolated between the -13F and -22F chart points. Cooling 28,400 Btu/h and min_operating_temp_f -22F per datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # No heating rating by design: three head ratings summed would size a zone against
    # capacity the shared compressor can't deliver simultaneously. Cooling capacity is kept
    # since it's what distinguishes the 9k from the 12k on a schedule.
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
                  heating_capacity_btuh=10600,
                  heating_capacity_at_design_btuh=9300,
                  cooling_capacity_btuh=9100,
                  min_operating_temp_f=-22.0,
                  source="Gree SAP09HP230V1R32AO. Datasheet chart: 10,600 Btu/h at 47F, ~11,500-13,000 Btu/h at 5F, ~10,000 Btu/h at -13F, ~8,200 Btu/h at -22F. -15F at-design (9,300 Btu/h) is linearly interpolated between the -13F and -22F chart points. Cooling 9,100 Btu/h and min_operating_temp_f -22F per datasheet.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # 1,500W/120V = 12.5A; x1.25 continuous = 15.6A needs a 20A breaker (not 15A). Hard-wired
    # Equipment, not a receptacle. Rated 5,100 Btu/h (1,500W x 3.412, no cold-weather derate).
    # `supplemental_heat` so it never opens its own HVAC zone — counts toward RM-M-LIVING's
    # zone (takeoff/hvac.py supplemental_heat_by_room).
    EquipmentType(tag="EQ-T-FIREPLACE-EL", name="Electric fireplace, 1.5 kW linear wall-mount",
                  footprint=(inch(48), inch(7)), height=inch(21),
                  heating_capacity_btuh=5100, heating_capacity_at_design_btuh=5100,
                  supplemental_heat=True,
                  ports=(ServicePort(tag="power", service=Service.POWER_120,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Supplemental duct heater in System 1's supply plenum (2026-08-15): EQ-T-GREE-VIREO-GEN3's
    # zone had a 16,309 Btu/h block load at -15F design against 13,500 Btu/h at-design output
    # + FH-S-BATH1's mat, a -1,069 Btu/h shortfall `mep.heating_capacity` was failing on. This
    # is the standard fix — resistance heat downstream of the coil for the few design hours
    # the compressor can't reach the load. 2kW x 3.412 = 6,800 Btu/h, no cold-weather derate.
    # `supplemental_heat` like the fireplace: counts toward its room's zone, opens none of
    # its own.
    EquipmentType(tag="EQ-T-DUCT-HEATER-2KW",
                  name="Inline duct heater, 2 kW, 240V (supply plenum)",
                  footprint=(inch(16), inch(10)), height=inch(10),
                  heating_capacity_btuh=6800, heating_capacity_at_design_btuh=6800,
                  supplemental_heat=True,
                  source="Generic 2 kW / 240 V single-stage open-coil duct heater with integral airflow and high-limit interlock, mounted in the supply plenum downstream of the air handler and enabled only on a second-stage call. Sized to cover the zone design-temperature shortfall with margin, not to carry the house.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
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
                     position=pt(ft(0, -8), ft(29, 9.125)), type_ref="ED-T-METER",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room=None, rotation=deg(270)),
]

# --- the backup microgrid (2026-08-02, notes/backup_power.md) ------------------------
# Four pieces, positions carry the design: EQ-B-ESS-BATT is the only thing in the RM-B-ESS
# Type X closet; EQ-B-ESS-INV sits outside it on the furnace room's west wall (not a fire
# risk, needs to be reachable to reset); ED-B-BACKUP-PANEL is beside the inverter on its
# dedicated load output; ED-B-BACKUP-ENCL stays in place but demoted to shed-tier relays +
# 24V bus only, no feed of its own.
BACKUP_ENCLOSURE = [
    # circuit= is gone with CKT-BACKUP-FEED (plan/circuits.py): this enclosure's gear lives
    # downstream of the inverter's load output now, and naming a grid-side branch circuit on
    # it said the opposite.
    ElectricalDevice(uid="CEE002AAAA", tag="ED-B-BACKUP-ENCL", kind=DeviceKind.PANEL,
                     position=pt(ft(1, 3), ft(32, 6)), type_ref="ED-T-BACKUP-ENCL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room="RM-B-FURNACE", rotation=deg(90)),
    # The subpanel the two backup tiers are homed to (plan/circuits.py). On the west wall
    # 2'-0" south of ED-B-PANEL, so the inverter's grid conductors and its load conductors
    # run to two enclosures a person can stand between.
    ElectricalDevice(uid="CEE060AAAA", tag="ED-B-BACKUP-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(1, 2), ft(27)), type_ref="ED-T-BACKUP-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room="RM-B-FURNACE", rotation=deg(90)),
]

ESS_EQUIPMENT = [
    # On the ESS closet's east face — 12" concrete (W-B-STR2), the one wall rated for 300 lb.
    # (8'-4", 20'-3") clears both framed partitions and the door swing.
    # `code.R327_ess_capacity` reads `room="RM-B-ESS"` to count this as indoor storage
    # (14.3 of the 40 kWh article limit) — a future garage relocation is just this one line.
    Equipment(uid="CEQ020AAAA", tag="EQ-B-ESS-BATT", kind=EquipmentKind.BATTERY,
              position=pt(ft(8, 4), ft(20, 3)), footprint=(inch(24), inch(10)),
              type_ref="EQ-T-ESS-BATT",
              room="RM-B-ESS", circuit="CKT-ESS-GRID",
              mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # The inverter, outside the closet on the furnace room's west wall. Not on a branch
    # circuit: its grid port IS CKT-ESS-GRID, which is a source, and its load output feeds
    # ED-B-BACKUP-PANEL.
    Equipment(uid="CEQ021AAAA", tag="EQ-B-ESS-INV", kind=EquipmentKind.INVERTER,
              position=pt(m(2.48448), m(7.61735)), footprint=(inch(27), inch(12)),
              type_ref="EQ-T-EG4-12KPV",
              room="RM-B-FURNACE", circuit="CKT-ESS-GRID",
              mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]

# --- Basement: backup outlets, sauna, spa (sunken garden files on this storey) --------
BASEMENT_DEVICES = [
    # HA server + router (backup). Beside the panel in the furnace room.
    ElectricalDevice(uid="CEE003AAAA", tag="ED-B-UTIL-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(1, 1), ft(28)), type_ref="ED-T-RECEPTACLE", circuit="CKT-HA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # Sump pump (backup; ~1000W start). GFCI lives at the breaker, not the outlet.
    ElectricalDevice(uid="CEE004AAAA", tag="ED-B-SUMP-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4, 6), ft(34, 11)), type_ref="ED-T-RECEPTACLE", circuit="CKT-SUMP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # On the sauna's west liner wall immediately south of EQ-B-SAUNA-HTR (footprint y
    # 8'-0"..9'-6"), low like the heater terminals. Old (15', 7') position was off-wall and
    # is now inside FURN-B-SAUNA-BENCH-E.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9, 4.875), ft(7, 9)), type_ref="ED-T-SAUNA-JB", circuit="CKT-SAUNA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)), rotation=deg(90)),
    # Hot tub in the sunken garden: disconnect on the west porch wall, 7' from its north
    # end, under the porch deck (see header). NEC 680.22 convenience receptacle beside it.
    ElectricalDevice(uid="CEE010AAAA", tag="ED-B-SPA-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(8, 8), ft(-7, -10)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-SPA",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), rotation=deg(90)),
    ElectricalDevice(uid="CEE011AAAA", tag="ED-B-SPA-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(8, 7), ft(-5, -6)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4)), rotation=deg(90)),
    # RM-B-BATH's NEC 210.52(D) receptacle (2026-07-30): GFCI within 3'-0" of the basin's
    # edge (1'-0" here), on the north partition — not the east wall, which is 12" cast
    # concrete behind the basin. Rides CKT-RC-BSMT rather than its own 20A circuit (the
    # panel-slot trade recorded in plans/TODO.md's panel_spaces item).
    ElectricalDevice(uid="CEE040AAAA", tag="ED-B-BATH-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 4), ft(21, 5)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-BSMT", room="RM-B-BATH", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
]

BASEMENT_EQUIPMENT = [
    # EQ-B-WH2 (the second "240V element" tank) was retired 2026-08-15: there's one water
    # heater, an 80-gal Rheem ProTerra hybrid HPWH (plan/mep.py::EQ-T-WATER-HEATER) — the
    # two-tank split was a modelling artifact of describing one product's two internal power
    # draws as two appliances.
    Equipment(uid="CEE016AAAA", tag="EQ-B-ERV", kind=EquipmentKind.ERV,
              position=pt(m(2.09754), m(8.88149)), footprint=(inch(24), inch(24)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV", circuit="CKT-ERV"),
    # Sauna heater: NW corner of the *heated* zone (south 8'-6" of RM-B-SAUNA — the north 4'
    # is the shower per notes/sauna_shower_basement_detail.md), back to the west liner face,
    # diagonally opposite the bench for 3'-2 11/16" of clear floor.
    # EQ-B-HP2-GYM (System 2's basement head): high on the centre bearing wall's east face at
    # x=18', backs west, throws east across the gym. zone_rooms is the whole conditioned
    # basement (one open volume off the stair) — EQ-B-SAUNA-HTR heats the sauna, not space.
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
    # Laundry pair, moved to W-M-CLN (2026-07-31, with the stacked unit) then north 8"
    # (2026-08-03, y 17'-4 5/8" -> 18'-0 5/8") — boxes in this partition go where it goes
    # (plan/storeys/main.py NODES). Recessed in the south partition directly behind the
    # tower: FX-M-LAUNDRY is 40" deep x 80" tall, so a surface box there is unreachable and
    # covered by the machine; recessed lets it sit flat with the plug behind it. 43" AFF
    # splits the difference between washer and dryer tops.
    # CKT-DRYER stays a 30A/14-30R even though the LG DLHC5502V heat-pump dryer only needs
    # 830W/15A minimum branch: it still ships a 4-prong cord needing 30A, and the oversize
    # lets a future conventional vented dryer go in without repulling wire.
    ElectricalDevice(uid="CEE007AAAA", tag="ED-M-LAUNDRY-DR1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(9, 6), ft(18, 0.375)), type_ref="ED-T-RECEPTACLE-1430",
                     circuit="CKT-DRYER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43),
                                 recessed_into_host_surface=True)),
    # CKT-LAUNDRY (circuits.py slot 36, 20A) was scheduled but the outlet never drawn — this
    # is it: washer half of the stack, 8" east of the dryer box, same 43" band. NEC 210.52(F),
    # the room's only 120V outlet.
    ElectricalDevice(uid="QBSRR1MWVB", tag="ED-M-LAUNDRY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10, 2), ft(18, 1.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-LAUNDRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43),
                                 recessed_into_host_surface=True)),
    # Freezer beside the fridge (KRF1 at (18'-4", 31'-5")) on the centre wall's east face;
    # fridge + freezer + PoE WiFi share the backup kitchen circuit.
    ElectricalDevice(uid="CEE006AAAA", tag="ED-M-LIVING-KFZ1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(29, 10)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # System 3 (Sapphire, backup battery circuit): its outdoor unit stands on the north
    # side beside the mudroom door, so the disconnect goes on W-M-N2's exterior face west
    # of the breezeway — clear of ED-M-HP1-DISC's condenser gap.
    ElectricalDevice(uid="CEE026AAAA", tag="ED-M-HP3-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(4), ft(36, 7)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP3",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # FH-M-BATH2's thermostat: inside the room on its south wall (W-M-BDN1, interior face
    # y=13'-0 11/16"), 8" east of D-M-BATH2's opening (x 1'-6 1/2"..4'-0 1/2") — the wall
    # you reach as the door closes behind you. Floor sensor is FH-M-BATH2's `stat` point.
    ElectricalDevice(uid="CEE021AAAA", tag="ED-M-BATH2-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(4, 9), ft(13, 3.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH2", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # FH-M-DINING's thermostat: zone is free-standing mid-room, so control goes on the
    # nearest real wall — east wall interior face x=35'-5 3/8" (corrected 2026-08-03 from
    # 35'-11 3/8", which sat in the studs; CATLIN_EXT_2X6's inside face is 6 5/8" in from the
    # 36' sheathing plane). Sits in the 5'-1" clear stretch between WIN-M-LIV-E2 and
    # WIN-M-DIN-E2, 10" clear of ED-M-LIVING-RC3 at y=16'-11".
    ElectricalDevice(uid="CEE024AAAA", tag="ED-M-DINING-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(35, 4.375), ft(17, 9)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-DINING", room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(270)),
]

MAIN_EQUIPMENT = [
    # --- Outdoor units. `zone_rooms` is empty on all three — a condenser's zone is the union
    # of its indoor units' rooms, named via each head's `outdoor_ref`. Refrigerant linesets
    # are deliberately not modeled (the outdoor_ref pairing IS the record, plans/TODO.md).
    # System 3's outdoor unit: north side beside the mudroom door, under ED-M-HP3-DISC, for
    # the short lineset run to the head over the stairs. Since 2026-08-15 it's a straight
    # punch through W-M-N2 — the unit (x 10'-0"..12'-7") sits directly opposite
    # EQ-M-HP3-STAIR (x 10'-6"..13'-3") on that wall's inside face.
    Equipment(uid="CEE027AAAA", tag="EQ-M-HP3-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(m(3.44566), m(11.3941)), footprint=(inch(31), inch(13)),
              type_ref="EQ-T-GREE-SAPPHIRE-9-OD", circuit="CKT-HP3", room=None),
    # --- System 2's main-floor heads: high on the south wall either side of the centre wall
    # at x=18', backs south, blowing north. Neither carries `circuit` — power comes off the
    # multi's outdoor unit (CKT-HP2 feeds EQ-M-HP2-OD, interconnects run from there).
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
    # --- System 3's head: stair well NW corner, on the north wall (W-M-N2).
    # Moved off W-M-STRW 2026-08-15 (plans/TODO.md): it used to hang on the west wall,
    # partly recessed into that wall's appearance-grade plywood stair face (the one hole
    # deliberately allowed there) and blowing across the flight instead of down the well.
    # Now surface-mounted on W-M-N2; the mudroom is served instead by REG-M-XFER-MUD, a
    # passive louver in the same wall (plan/mep_registers.py).
    # Position: y=35'-1 3/8" (8" body, back on W-M-N2's face, surface-mounted since an 8"
    # unit won't fit the 5 1/2" insulated cavity); x=11'-10 1/2" (33" case runs
    # 10'-6"..13'-3", tight into the corner, square over the stair lane, 2 5/8" clear of
    # W-M-STRW); rotation 0 (back north, blowing south down the well — contrast 180 on the
    # System 2 heads, -90 on EQ-M-FIREPLACE). Hangs over open well either way (FO-M-STAIR
    # stops at y=35'), same as the old position.
    # `room` followed RM-M-STAIR into RM-M-LIVING (2026-07-30, stair well is part of that
    # room now). `zone_rooms` did not — it's the mudroom + mech closet; the stair volume it
    # blows into belongs to EQ-M-HP2-LIVING's 768 sf claim, not counted twice here.
    Equipment(uid="CEE030AAAA", tag="EQ-M-HP3-STAIR", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(11, 10.5), ft(35, 1.375)), footprint=(inch(33), inch(8)),
              room="RM-M-LIVING", type_ref="EQ-T-GREE-SAPPHIRE-9", rotation=deg(0),
              outdoor_ref="EQ-M-HP3-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              zone_rooms=("RM-M-MUDROOM", "RM-M-MECH")),
    # SE corner of the living room, east wall. Dropped 36" -> 7" mount (2026-07-30) when
    # WIN-M-LIV-E1 restacked to y=4'-0": its RO (sill 30") now crosses the cabinet band, so
    # the 21" cabinet (tops at 28") reads as a hearth under the glass instead. 48" cabinet
    # spans y 0'-10"..4'-10", clear of ED-M-LIVING-RC4 at y=5'-6 1/2". rotation -90 backs it
    # to the wall (interior face x=35'-11 3/8").
    Equipment(uid="CEE022AAAA", tag="EQ-M-FIREPLACE", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(35, 8), ft(2, 10)), footprint=(inch(48), inch(7)),
              room="RM-M-LIVING", type_ref="EQ-T-FIREPLACE-EL", rotation=deg(-90),
              circuit="CKT-FIREPLACE",
              mount=Mount(kind=MountKind.WALL, elevation=inch(7))),
]

# --- Second storey: the NW bathroom's floor-heat control -------------------------------
SECOND_DEVICES = [
    # NEC 440.14 disconnects for the two balcony condensers, second-storey south wall within
    # sight of their units. Moved 2026-07-31 off D-S-DECK-W's rough opening onto clear wall
    # with 110.26 working space clear of any condenser: HP1's box between the plant windows,
    # HP2's east of D-S-DECK-E (its unit sits 7' away in plain sight — 440.14 needs sight,
    # not reach). Both on the wall's exterior face (y=-7"), corrected 2026-08-03 from y=+6"
    # which put a 3R disconnect on the interior side of the wall from its condenser.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-HP1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(6), ft(0, -7)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP1", mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-HP2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(25, 6.5), ft(0, -7)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP2", mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # FH-S-BATH1's thermostat, inside the room on its south wall (W-S-BD-N1B, interior
    # face y=26'-4 11/16"), 9" west of D-S-BATH1's opening (x 7'-3"..9'-9"). Same
    # reach-as-the-door-shuts position as ED-M-BATH2-FH-STAT, and clear of the fixture
    # cluster, which all sits north of y=29'-9".
    ElectricalDevice(uid="CEE025AAAA", tag="ED-S-BATH1-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 6), ft(26, 8.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH1", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

SECOND_EQUIPMENT = [
    # Vireo (System 1) and Multi Ultra (System 2) condensers share the upper balcony, not the
    # main-level porch — kept in SECOND_ELEMENTS so the 3D model uses the balcony's 10'
    # datum, not grade.
    # Both turned 90 deg and re-stationed 2026-07-31 for D-S-DECK-W: broadside they filled
    # the whole balcony frontage and the new door RO (x 11'-2"..16'-2") landed on both.
    # End-on (16" of x each) lets two doors and two condensers share the 21' deck: HP1 at
    # x 8'-0"..9'-4" (below WIN-S-PLANT2's sill, so no glass conflict), HP2 in the 2'-8" gap
    # between the French doors at x 16'-10"..18'-2", clear of both leaf sweeps. Both keep
    # 1'-0" standoff from the wall for the linesets.
    Equipment(uid="CEE017AAAA", tag="EQ-M-HP1-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(8, 8), ft(-2, -7)), footprint=(inch(38), inch(16)),
              rotation=deg(90),
              type_ref="EQ-T-GREE-VIREO-GEN3", circuit="CKT-HP1", room=None),
    Equipment(uid="CEE018AAAA", tag="EQ-M-HP2-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(17, 6), ft(-2, -6.5)), footprint=(inch(37), inch(16)),
              rotation=deg(90),
              type_ref="EQ-T-GREE-MULTI-U30", circuit="CKT-HP2", room=None),
    # System 1's concealed ducted AH, inside SF-S-DUCT's dropped box at the south end of the
    # hallway trunk (2026-07-30). Can't sit in the floor structure — 21"x11" case vs. ~14 1/2"
    # clear in an 11 7/8" I-joist bay — and the old (21', 7') spot hung 18" into FO-A-STAIR's
    # framed opening. The soffit box (14" drop x 30 3/4" clear) is the one cavity that holds
    # it; footprint 21"x43" runs the hall, discharge north into DU-S-HP-SUP, return through
    # REG-S-HP-RET's plenum stub. Own branch circuit (CKT-HP1-AH) since a ducted unit's
    # blower is fed at the unit, unlike a multi's heads.
    # zone_rooms covers the whole conditioned second storey plus RM-A-STUDY/RM-A-EAST (short
    # attic branches) and RM-A-WEST (suite branch's REG-A-HP-WEST boot, 2026-07-30).
    # RM-A-DEN is deliberately excluded — nothing serves it (plans/TODO.md).
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
    # The duct heater above, in the supply plenum immediately north of the air handler's
    # discharge — inside SF-S-DUCT's soffit box, 8" past the y=9'-7" line DU-S-HP-SUP leaves
    # from, so it heats every branch the trunk feeds rather than one room's boot.
    #
    # `room` is RM-S-HALL, not RM-S-STUDY2 where the air handler is filed: the study's clear
    # face stops at y=8'-11", the trunk soffit runs the hall, and this sits in the trunk.
    # (`integrity.placeable_room_mismatch` said so at the first attempt.) It changes nothing
    # about the credit — `supplemental_heat_by_room` keys on the room, and RM-S-HALL is in
    # the same EQ-S-HP1-AH zone_rooms list as RM-S-STUDY2 — and it is where the part is.
    #
    # It takes CKT-SPARE-240, the 2-pole the panel has been holding since 2026-07-25 for
    # "future 240V" — this is that load, and the breaker comes down 30A -> 15A with it
    # (2,000 W / 240 V = 8.3 A, x125% continuous = 10.4 A). The panel therefore gains no
    # slot and loses its last spare pair; see plans/TODO.md.
    Equipment(uid="CEE033AAAA", tag="EQ-S-HP1-STRIP", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(19, 10), ft(10, 3)), footprint=(inch(16), inch(10)),
              room="RM-S-HALL", type_ref="EQ-T-DUCT-HEATER-2KW",
              circuit="CKT-HP1-STRIP", mount=Mount(kind=MountKind.CEILING)),
]

# --- Garage: both EV receptacles on the south wall, east of the service door ----------
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(0, 9.625), ft(56, 0.75)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE", rotation=deg(90)),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(19, 11.375), ft(41, 4)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE"),
]

GARAGE_EQUIPMENT = [
    # West wall — the only wall with nothing else in it. Mounted 6'-0" on an 8' wall, 15"
    # case tops at 7'-3", blows down over a bench.
    # Hard-wired, not cord-and-plug: NEC 210.8(A)(2) GFCI applies to garage *receptacles*
    # only, so CKT-GAR-HEAT carries none — a plug-in unit would need CKT-RC-GARAGE instead.
    Equipment(uid="CEE023AAAA", tag="EQ-G-HEATER", kind=EquipmentKind.SPACE_HEATER,
              position=pt(m(0.227899), m(14.595)), footprint=(inch(14), inch(9)),
              room="RM-GARAGE", type_ref="EQ-T-GARAGE-HEATER", rotation=deg(90),
              circuit="CKT-GAR-HEAT",
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
]

# --- Attic: PV junction box beside the radon riser (ED-A-NEMA-JB at (6', 37')) --------
PV_JBOX = [
    ElectricalDevice(uid="CEE014AAAA", tag="ED-A-PV-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9), ft(36, 8)), type_ref="ED-T-PV-JB", circuit="CKT-ESS-GRID",
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
    # Up the mechanical chase beside the radon vent to the PV junction box. Corrected
    # 2026-08-02 to (1'-6", 34'-6") — the old (3', 33') sat 4" south of W-M-MECH-S, out in
    # the open mudroom floor with no enclosure.
    ConduitRun(uid="CDT001AAAA", tag="CD-B-ATTIC-RISER", trade_size=inch(1.5),
               path=(pt(ft(2), ft(29)), pt(ft(1, 6), ft(34, 6))),
               start_elevation=ft(-4), end_elevation=ft(25, 6),
               from_ref="ED-B-PANEL", to_ref="ED-A-PV-JB"),
    # --- the backup microgrid's three raceways (2026-08-02) --------------------------
    #
    # The PV string conductors no longer terminate at the panel: they land on the
    # inverter's MPPTs, and only the inverter's AC grid port reaches ED-B-PANEL. So the
    # attic riser above feeds ED-A-PV-JB as before, and this run takes it the rest of the
    # way down the same chase to EQ-B-ESS-INV.
    ConduitRun(uid="CDT005AAAA", tag="CD-B-PV-INV", trade_size=inch(1),
               path=(pt(ft(1, 6), ft(34, 6)), pt(ft(2), ft(24, 6))),
               start_elevation=ft(-4), end_elevation=ft(-4),
               from_ref="ED-A-PV-JB", to_ref="EQ-B-ESS-INV"),
    # Grid port up to the service panel's CKT-ESS-GRID breaker: 4'-6" of wall, but it is
    # the run that carries the backfeed and it is billed like any other.
    ConduitRun(uid="CDT006AAAA", tag="CD-B-INV-PANEL", trade_size=inch(1),
               path=(pt(ft(2), ft(24, 6)), pt(ft(2), ft(29))),
               start_elevation=ft(-4), end_elevation=ft(-4),
               from_ref="EQ-B-ESS-INV", to_ref="ED-B-PANEL"),
    # Load output down to the backup subpanel — the conductors that stay live when the
    # grid does not.
    ConduitRun(uid="CDT007AAAA", tag="CD-B-INV-BACKUP", trade_size=inch(1),
               path=(pt(ft(2), ft(24, 6)), pt(ft(2), ft(27))),
               start_elevation=ft(-4), end_elevation=ft(-4),
               from_ref="EQ-B-ESS-INV", to_ref="ED-B-BACKUP-PANEL"),
    # North under the house/garage gap to the EV receptacles on W-G-S. East leg runs y=35',
    # not y=36' (2026-08-02): the old line ran 14' inside W-B-N2/W-B-N3 as three wall
    # crossings; pulled 1' south it punches the wall once.
    ConduitRun(uid="CDT002AAAA", tag="CD-B-GARAGE", trade_size=inch(1.25),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(35)), pt(ft(16), ft(35)),
                     pt(ft(16), ft(41, 6))),
               start_elevation=ft(-4), end_elevation=ft(5, 10),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # Across the basement ceiling to the kitchen's east counter wall — still the east wall
    # after the 2026-07-30 range/sink swap, since KGF3 (the device this feeds) stayed the
    # east-wall device; its position along that wall moved twice since, with the cooking run
    # and then with the range/N3 flip.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(28, 11))),
               # -1'-6", not the -1'-0" it held until 2026-08-21: the basement ceiling
               # dropped when the 9" deck became the 12 5/8" EPS deck with 5/8" gypsum
               # under it, and a raceway at -1'-0" was then lying *inside* the pour
               # (mep.sleeve_coverage caught it as an unsleeved crossing at 26'-6").
               # 4 3/4" clear under the -1'-1 1/4" soffit. Its two wall crossings go with it.
               start_elevation=ft(-1, -6), end_elevation=ft(3, 6),
               from_ref="ED-B-PANEL", to_ref="ED-M-LIVING-KGF3"),
    # South out of the basement to the hot tub disconnect under the porch. Same 2026-08-02
    # correction as CD-B-GARAGE above: the east leg was on the y=0 sheathing line, i.e.
    # inside W-B-S1 for 6'-6". Pulled 1' north it crosses that wall once.
    ConduitRun(uid="CDT004AAAA", tag="CD-B-SPA", trade_size=inch(1),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(1)), pt(ft(8, 6), ft(1)),
                     pt(ft(8, 6), ft(-7.833))),
               start_elevation=ft(-4), end_elevation=ft(-4),
               from_ref="ED-B-PANEL", to_ref="ED-B-SPA-DISC"),
]

# --- Structured cabling: the head end, three access points, and the spine trunk ---------
# Rides the existing full-height radon/plumbing chase at (1', 34'-6") in its own raceways
# (NEC 800.133/725 forbids comms sharing a raceway with power). Four risers 6" apart on the
# y=34'-6" line (>=5" so mep.sleeve_coverage's matcher doesn't confuse sleeves through
# SL-M-DECK): x=1'-0" radon/vent, x=1'-6" CD-B-ATTIC-RISER (PV DC), x=2'-0"
# CD-B-DATA-CHASE, x=2'-6" CD-B-SPARE-CHASE (capped, pull string).
# Star topology, not daisy chain: every run is a home run from ED-B-NET-PATCH, which is
# what `electrical.data_reachability`'s from_ref/to_ref graph walk needs to mean anything.
DATA_HEAD_END = [
    # Router, PoE switch and patch field in the basement mechanical room, 2' north of
    # ED-B-PANEL (29') and clear of the ERV duct crossing at 31'-4". It is the only
    # low-voltage device on a branch circuit: CKT-HA, with the HA server it sits beside.
    ElectricalDevice(uid="CND001AAAA", tag="ED-B-NET-PATCH", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(1, 2), ft(31)), type_ref="ED-T-NET-ENCLOSURE",
                     circuit="CKT-HA", room="RM-B-FURNACE",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), rotation=deg(90)),
]

DATA_TRUNKS = [
    # The spine riser: basement mechanical room to the attic floor, 6" east of the
    # radon/vent bundle. Every upstairs pull goes through this one pipe.
    ConduitRun(uid="CDT008AAAA", tag="CD-B-DATA-CHASE", trade_size=inch(1.25),
               service=Service.DATA,
               path=(pt(ft(2), ft(31)), pt(ft(2), ft(34, 6))),
               start_elevation=ft(-4), end_elevation=ft(20, 6),
               from_ref="ED-B-NET-PATCH"),
    # The capped spare, another 6" east. No service and no conductors — a pull string and
    # 2" of room, which is the whole of what electrical_notes.md line 3 ("conduit, make it
    # easy to run new lines") asks for. It is where the PoE cameras go.
    ConduitRun(uid="CDT009AAAA", tag="CD-B-SPARE-CHASE", trade_size=inch(2),
               service=None,
               path=(pt(ft(2), ft(31)), pt(ft(2, 6), ft(34, 6))),
               start_elevation=ft(-4), end_elevation=ft(20, 6),
               from_ref="ED-B-NET-PATCH"),
]

MAIN_DATA_TRUNKS = [
    # Out of the chase at the main ceiling plane and east across the FS-SECOND joist bay to
    # the open kitchen/living ceiling. (19', 29') sits east of the FO-M-STAIR well
    # (x 10'-6"..17'-6") and between the kitchen, the stair and RM-M-STUDY — one radio
    # covering all three, which is what put it here rather than over the counter.
    ConduitRun(uid="CDT010AAAA", tag="CD-M-DATA-KITCH", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(19), ft(34, 6)), pt(ft(19), ft(29))),
               start_elevation=ft(9, 2), end_elevation=ft(9, 2),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-KITCH-AP"),
    # South through the same joist bay and out under the balcony deck to the porch soffit,
    # sharing SP-SG-PORCH-ELEC with the ceiling fan's supply — one hole, two raceways.
    ConduitRun(uid="CDT011AAAA", tag="CD-M-DATA-PORCH", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(17, 6), ft(34, 6)),
                     pt(ft(17, 6), ft(-4.833))),
               start_elevation=ft(9, 2), end_elevation=ft(8, 8),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-PORCH-AP"),
]

ATTIC_DATA_TRUNKS = [
    # Along the attic floor to the NE corner, then up the gable to the access point.
    ConduitRun(uid="CDT012AAAA", tag="CD-A-DATA-NE", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(33), ft(34, 6)), pt(ft(33), ft(35, 5))),
               start_elevation=ft(20, 6), end_elevation=ft(24),
               from_ref="ED-B-NET-PATCH", to_ref="ED-A-EAST-AP"),
]

MAIN_DATA_DEVICES = [
    ElectricalDevice(uid="CND002AAAA", tag="ED-M-KITCH-AP", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(19), ft(29)), type_ref="ED-T-AP-CEILING",
                     room="RM-M-LIVING",
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # No `room=`, deliberately — the same reason ED-M-PORCH-FAN carries none, so the wet/
    # exterior classifiers place it geometrically instead of believing a label. 1' west of
    # the fan, in the same soffit bay and through the same deck penetration.
    ElectricalDevice(uid="CND003AAAA", tag="ED-M-PORCH-AP", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(17), ft(-4.833)), type_ref="ED-T-AP-OUTDOOR",
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(8, 6))),
]

ATTIC_DATA_DEVICES = [
    # High on the north gable in the NE corner of RM-A-EAST. Mount elevation is
    # storey-relative (attic datum 20'), so 4' here is 24' absolute — under the 4:12 rake,
    # which at x=33' carries the roof to 26'.
    ElectricalDevice(uid="CND004AAAA", tag="ED-A-EAST-AP", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(33), ft(35, 1.375)), type_ref="ED-T-AP-CEILING",
                     room="RM-A-EAST", wall_ref="W-A-N1",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]

# No porch deck penetration, deliberately: everything on the porch (elev <=9'-2") is
# *under* the balcony deck (SL-SG-DECK at 10'-0"..10'-1 1/2"), not through it — raceways
# exit via the framed south wall (drilled hole) into the soffit. A sleeve tried on
# SL-SG-DECK (2026-08-02) modelled a penetration that doesn't exist and graded UNKNOWN
# forever. ED-M-PORCH-FAN's undrawn supply is the ordinary "last leg" branch-wiring gap,
# not a penetration gap.

# --- Raceway penetrations through cast concrete (2026-08-02) ---------------------------
# Fifteen holes existed in the concrete and nothing in the model — `concrete_crossings`
# walked only pipe runs. Positions are resolver-computed crossing points, not hand-measured
# (`mep.sleeve_coverage` matches on them). Wall/footing crossings are horizontal, carry the
# run's elevation; deck/slab crossings are vertical.
CONDUIT_SLEEVES = [
    # CD-B-GARAGE: west to east across the basement at -4', then north under the house/
    # garage gap and up through the garage slab.
    SleevePenetration(uid="CNS005AAAA", tag="SP-B-N3-CD-GAR", host_ref="W-B-N3",
                      position=pt(ft(6), ft(35)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    SleevePenetration(uid="CNS006AAAA", tag="SP-B-STR-CD-GAR", host_ref="W-B-STR",
                      position=pt(ft(10), ft(35)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    SleevePenetration(uid="CNS007AAAA", tag="SP-B-N2-CD-GAR", host_ref="W-B-N2",
                      position=pt(ft(13), ft(35)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    SleevePenetration(uid="CNS008AAAA", tag="SP-B-N2-CD-GAR2", host_ref="W-B-N2",
                      position=pt(ft(16), ft(35, 6)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # Through the ICF *stem*, not the footing under it. The run holds -4'-0" the whole way
    # (it is pinned to the basement it leaves, which did not move), and when grade dropped
    # 2'-6" on 2026-08-18 the garage foundation went down with the soil: FT-GF-S2 now bears
    # at -6'-8" and its top is -6'-0", two feet clear below this crossing, while W-GF-S2
    # spans -6'-0" to -0'-8" and is what the conduit actually passes through.
    SleevePenetration(uid="CNS009AAAA", tag="SP-GF-CD-GAR", host_ref="W-GF-S2",
                      position=pt(ft(16), ft(40, 10)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    SleevePenetration(uid="CNS010AAAA", tag="SP-G-CD-GAR", host_ref="SL-G-FLOOR",
                      position=pt(ft(16), ft(41, 6)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240),
    # CD-B-KITCHEN: east across the basement ceiling at -1' and up through SL-M-DECK to the
    # kitchen's east counter wall. The wall and deck sleeves are 1/2" apart in plan but in
    # different hosts, which is what the matcher keys on.
    SleevePenetration(uid="CNS011AAAA", tag="SP-B-STR-CD-KITCH", host_ref="W-B-STR",
                      position=pt(ft(10), ft(29)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.POWER_120,
                      axis="horizontal", center_elevation=ft(-1)),
    SleevePenetration(uid="CNS012AAAA", tag="SP-B-CN-CD-KITCH", host_ref="W-B-CN",
                      position=pt(ft(18), ft(29)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.POWER_120,
                      axis="horizontal", center_elevation=ft(-1, -6)),
    SleevePenetration(uid="CNS013AAAA", tag="SP-B-E2-CD-KITCH", host_ref="W-B-E2",
                      position=pt(ft(35), ft(28, 11.5)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.POWER_120,
                      axis="horizontal", center_elevation=ft(-1, -6)),
    SleevePenetration(uid="CNS014AAAA", tag="SP-M-CD-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(35), ft(28, 11)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.POWER_120),
    SleevePenetration(uid="CNS015AAAA", tag="SP-B-S1-CD-SPA", host_ref="W-B-S1",
                      position=pt(ft(8, 6), ft(0, 6)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(1.75), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    SleevePenetration(uid="CNS016AAAA", tag="SP-SG-W1-CD-SPA", host_ref="W-SG-W1",
                      position=pt(ft(8, 6), ft(-4.3332)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(1.75), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
]

# --- NEC 210.52 fill (generated positions, hand-authored constructors) ---------------
# electrical.receptacle_spacing walks each habitable room clear-face ring; these
# receptacles close every wall-space gap the 6-foot rule found. Positions sit on the
# room boundary and are draggable like any other device.
NEC_FILL_BASEMENT = [
    ElectricalDevice(uid="NEC001AAAA", tag="ED-B-GYM-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 1.5), ft(2, 7.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC002AAAA", tag="ED-B-GYM-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 1.5), ft(10, 6.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC003AAAA", tag="ED-B-GYM-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(20, 7), ft(18, 4.385)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC004AAAA", tag="ED-B-GYM-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 3.5), ft(18, 4.385)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC005AAAA", tag="ED-B-GYM-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(34, 11), ft(11, 5.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC006AAAA", tag="ED-B-GYM-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(34, 11), ft(2, 2.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC007AAAA", tag="ED-B-GYM-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(28, 11.5), ft(1, 1)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
NEC_FILL_MAIN = [
    ElectricalDevice(uid="NEC008AAAA", tag="ED-M-LIVING-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(4, 5.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC009AAAA", tag="ED-M-LIVING-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(15, 10.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC010AAAA", tag="ED-M-LIVING-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(16, 11.125)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     # On the east wall's BESTA run; keep the plan position for spacing, but
                     # raise it into the backsplash zone above the 29 3/4" cabinet line.
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36)), rotation=deg(270)),
    ElectricalDevice(uid="NEC011AAAA", tag="ED-M-LIVING-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(5, 6.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     # Same east-wall BESTA condition as RC3: 36" puts the box above the
                     # countertop while preserving the receptacle's wall-space location.
                     mount=Mount(kind=MountKind.WALL, elevation=inch(36)), rotation=deg(270)),
    ElectricalDevice(uid="NEC012AAAA", tag="ED-M-LIVING-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30, 0.375), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC061AAAA", tag="ED-M-LIVING-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(23, 8.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # Fills the >6' gap electrical.receptacle_spacing flags on the centre bearing wall
    # between RC2 (y=15.87) and the wall's south end, on the LIVING face.
    ElectricalDevice(uid="NEC064AAAA", tag="ED-M-LIVING-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(21, 1.25)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    # The old hall band (2026-07-28): merging RM-M-HALL into this room via BM-M-HALL lost
    # its 210.52(A) hallway exemption, and the band had zero receptacles. Positions are the
    # four gaps `electrical.receptacle_spacing` measured on the merged clear face.
    #
    # Eight outlets on the storey receptacle circuits are GFCI *devices*, not breakers
    # (2026-08-01, code.E3902_gfci_locations): each sits within E3902.10's 6' sink reach
    # while its circuit (CKT-RC-MAIN/CKT-RC-SECOND) spans a whole storey non-GFCI, so one
    # splashed bathroom outlet can't take the floor down with it.
    #
    # y flipped to W-M-HS1's south face (2026-07-28): W-M-BAE's 2' east shift put the north
    # face inside RM-M-BATH1 at this x.
    ElectricalDevice(uid="NEC066AAAA", tag="ED-M-LIVING-RC8", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(5, 4.75), ft(22, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # y flipped to W-M-STOS's north face (2026-07-28) when W-M-BAE's shift pushed the south
    # face into RM-M-BATH1. Inside RM-M-MUD-CLOSET since 2026-08-02, kept on purpose: NEC
    # 410.16 restricts closet luminaires, not receptacles, and RM-M-MUDROOM is
    # Occupancy.STORAGE so `electrical.receptacle_spacing` never walks it anyway. Stays GFCI
    # for its unmoved E3902.10 sink-reach location (RM-M-BATH1's lav, through W-M-STOS).
    ElectricalDevice(uid="NEC067AAAA", tag="ED-M-LIVING-RC9", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(4, 6.625), ft(26, 7.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC068AAAA", tag="ED-M-LIVING-RC10", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9, 6), ft(26, 0.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # On the 10 3/16" pier at W-M-STRS's east end, between D-M-STAIR and the well partition
    # the wall dies into — the only wall left on that face, and a useful one to have at the
    # head of the stairs.
    ElectricalDevice(uid="NEC069AAAA", tag="ED-M-LIVING-RC11", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(13, 10.25), ft(25, 6.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # Fills the >6' gap electrical.receptacle_spacing opened on the hall band between RC7/
    # STUDY-RC3 and the door into RM-M-STOS (2026-07-29): N-M-W2/N-M-C2 pushed 6" north
    # for the BATH2 wall move, stretching this door-to-door wall space past the 6' rule.
    # Positioned centred in that space (the door itself brackets the run at 13'-9" east).
    ElectricalDevice(uid="NEC070AAAA", tag="ED-M-LIVING-RC12", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(16, 1.25), ft(22, 7.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC013AAAA", tag="ED-M-BED-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(8, 6.25), ft(12, 8.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC014AAAA", tag="ED-M-BED-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 7.625), ft(10, 9)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC015AAAA", tag="ED-M-BED-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 7.625), ft(1, 1.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC016AAAA", tag="ED-M-BED-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9, 4.75), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC017AAAA", tag="ED-M-BED-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0, 7.625), ft(0, 10)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC018AAAA", tag="ED-M-BED-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0, 7.625), ft(9, 11.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    # 2026-08-03: RC1 sat in D-M-STUDY's rough opening; moved with RC3 onto the study's
    # south/north walls (RM-M-STUDY is 4'-8"x4'-2", east wall nearly all door), 5'-2"/5'-10"
    # from FX-M-LAUNDRY-SINK — inside E3902.10's 6', so both are GFCI at the device.
    ElectricalDevice(uid="NEC019AAAA", tag="ED-M-STUDY-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17), ft(18, 3.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC020AAAA", tag="ED-M-STUDY-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(13, 7.375), ft(18, 9.5)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    # Fills the >6' gap electrical.receptacle_spacing flags on the centre bearing wall,
    # on the STUDY face opposite ED-M-LIVING-RC7.
    ElectricalDevice(uid="NEC065AAAA", tag="ED-M-STUDY-RC3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17), ft(22, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
# NEC 210.52(A) fill for the second storey, re-snapped after the partitions moved onto the
# survey (storeys/second.py). Positions are the *resolved room boundaries*, walked with the
# same arc-length maths `electrical.receptacle_spacing` uses, 1 1/2" inside each finished
# face: none of these devices carries `room=`, so a stale coordinate more than 19 5/8"
# (`_NEAR_WALL_M`) off simply stops counting toward the room and nothing reports it.
NEC_FILL_SECOND = [
    # RM-S-PLANT's five outlets are all ED-T-RECEPTACLE-WR-GFCI (2026-08-18): WR-listed
    # bodies, GFCI at the device, in-use covers, non-metallic gasketed boxes. NEC 2023 makes
    # the room a damp location throughout and a wet one wherever it is misted or hosed, and
    # everything that plugs in here — pumps, heat mats, the humidifier — stays plugged in,
    # which is what makes an in-use cover the right one rather than a flip lid.
    #
    # All five moved off the old finished face at the same time: the liner is 1 1/4" thicker
    # than the painted gypsum it replaced, so the south and west faces came in to y/x 7 9/32"
    # and the north partitions' faces went out to y 8'-9 9/32". Each device sits ~1 1/2"
    # inside its new face, the same station `electrical.receptacle_spacing` measures, and
    # `test_wall_mounted_devices_resolve_against_a_wall_face` is what caught them buried.
    #
    # GFCI at the DEVICE and not at CKT-RC-SECOND's breaker, per the convention in
    # plan/circuits.py, and that is also what keeps the plants alive: the grow tubes are on
    # CKT-LT-UPPER, a separate, non-GFCI lighting circuit, so a nuisance trip from a pump
    # cannot take the photoperiod down with it — and grow-light drivers' own leakage current
    # is exactly why the lighting side must not sit behind a 5 mA trip either.
    # Moved x=15.89' -> 17.0' (2026-07-31): the old station was inside D-S-DECK-W's rough
    # opening (x 11'-2"..16'-2"). 17'-0" centres the 1'-10" of wall left, under the 2'-0"
    # 210.52(A)(2) counts as wall space — kept anyway since the south wall is where the
    # plant gear plugs in.
    ElectricalDevice(uid="NEC021AAAA", tag="ED-S-PLANT-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17), ft(0, 8.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC022AAAA", tag="ED-S-PLANT-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(5, 10.25), ft(0, 8.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC023AAAA", tag="ED-S-PLANT-RC3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(0, 8.75), ft(4, 7.625)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), room="RM-S-PLANT", rotation=deg(90)),
    ElectricalDevice(uid="NEC024AAAA", tag="ED-S-PLANT-RC4", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(5, 11.125), ft(8, 7.375)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC025AAAA", tag="ED-S-PLANT-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 11.625), ft(8, 7.375)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC026AAAA", tag="ED-S-STUDY2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(0, 9.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC027AAAA", tag="ED-S-STUDY2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(7, 9.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC028AAAA", tag="ED-S-STUDY2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26, 1.5), ft(8, 8.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC029AAAA", tag="ED-S-STUDY2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 1.125), ft(8, 8.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC062AAAA", tag="ED-S-STUDY2-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 2), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC063AAAA", tag="ED-S-STUDY2-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(27, 4.5), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC030AAAA", tag="ED-S-BED1-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(17, 2.125)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC031AAAA", tag="ED-S-BED1-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 2.875), ft(9, 3.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC032AAAA", tag="ED-S-BED1-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 7.375), ft(9, 3.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC034AAAA", tag="ED-S-BED2-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(26, 3.125)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC035AAAA", tag="ED-S-BED2-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 3.875), ft(17, 11.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC036AAAA", tag="ED-S-BED2-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 8.375), ft(17, 11.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC038AAAA", tag="ED-S-BED3-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(32, 4), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC039AAAA", tag="ED-S-BED3-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(28, 8.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC040AAAA", tag="ED-S-BED3-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26, 9.875), ft(26, 11.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # Moved 2026-07-31: RC2 was authored at x=13'-1" on the arm's south wall, which is inside
    # O-S-CLOSET's 4'-8" cased opening (x 11'-5 1/2"..16'-1 1/2") — a box in a doorway. On the
    # suite's east wall instead, where it also closes the 8'-5" run 210.52 measured from the
    # opening's west jamb round to RC3.
    ElectricalDevice(uid="NEC042AAAA", tag="ED-S-SUITE-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(9, 4.125), ft(11)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # The 2'-2" of wall between D-S-SUITE's east jamb and O-S-CLOSET's east jamb. Short, but
    # 210.52(A)(2) counts any unbroken run of 2'-0" or more as wall space, and this one had
    # nothing on it.
    ElectricalDevice(uid="NEC047AAAA", tag="ED-S-SUITE-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 2.375), ft(12, 8.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC043AAAA", tag="ED-S-SUITE-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(6, 5), ft(9, 3.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC044AAAA", tag="ED-S-SUITE-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(0, 7.625), ft(12, 11.875)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC045AAAA", tag="ED-S-SUITE-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(1, 0.75), ft(22, 0.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC046AAAA", tag="ED-S-SUITE-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 3.125), ft(20, 6.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
]
# Same treatment for the attic's two habitable rooms. RM-A-WEST (media) and RM-A-DEN
# (storage) are outside `_HABITABLE`, so 210.52 spacing is not evaluated for them.
NEC_FILL_ATTIC = [
    ElectricalDevice(uid="NEC048AAAA", tag="ED-A-EAST-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(13, 8.25)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC049AAAA", tag="ED-A-EAST-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(24, 0.875)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC050AAAA", tag="ED-A-EAST-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(19, 5.375), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC051AAAA", tag="ED-A-EAST-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 11.25), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC052AAAA", tag="ED-A-EAST-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(31, 3.25)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC053AAAA", tag="ED-A-EAST-RC6", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(20, 9.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC054AAAA", tag="ED-A-EAST-RC7", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(10, 3.75)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC055AAAA", tag="ED-A-EAST-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26, 6.375), ft(9, 3.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # RC1/RC2 moved 2026-07-31: both used to sit over the FO-A-STAIR well (1 3/4"/6 5/8" of
    # deck, a 9' drop to reach). RC1 -> south wall between RC4/RC3; RC2 -> east wall south of
    # the well, closing the 7'-10" run from RC3 round the corner.
    ElectricalDevice(uid="NEC056AAAA", tag="ED-A-STUDY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC057AAAA", tag="ED-A-STUDY-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4.375), ft(2)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC058AAAA", tag="ED-A-STUDY-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 10.75), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC059AAAA", tag="ED-A-STUDY-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(23, 10.5), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC060AAAA", tag="ED-A-STUDY-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(4, 6.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
]

BASEMENT_ELEMENTS = [*BACKUP_ENCLOSURE, *ESS_EQUIPMENT, *BASEMENT_DEVICES,
                     *BASEMENT_EQUIPMENT, *CONDUIT_TRUNKS, *DATA_HEAD_END, *DATA_TRUNKS,
                     *NEC_FILL_BASEMENT]
MAIN_ELEMENTS = [*SERVICE_DEVICES, *MAIN_DEVICES, *MAIN_EQUIPMENT, *MAIN_DATA_DEVICES,
                 *MAIN_DATA_TRUNKS, *CONDUIT_SLEEVES, *NEC_FILL_MAIN]
GARAGE_ELEMENTS = [*GARAGE_DEVICES, *GARAGE_EQUIPMENT]
SECOND_ELEMENTS = [*SECOND_DEVICES, *SECOND_EQUIPMENT, *NEC_FILL_SECOND]
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP, *ATTIC_DATA_DEVICES, *ATTIC_DATA_TRUNKS,
                  *NEC_FILL_ATTIC]
