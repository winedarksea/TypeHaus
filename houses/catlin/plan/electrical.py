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
# face 6 1/2" outboard of that (5" until the 2026-08-23 Swinburne truss, 5 1/2" until
# the 2026-08-26 catlin truss laid four flat girt layers where the outrigger band was).
#
# Positions worth knowing (project-north frame, house sheathing SW corner at 0,0):
# - Meter: exterior face of west wall (W-M-W1), outside ED-B-PANEL at (2', 29') in the
#   basement — shortest run from the underground POWER entry at (0', 18').
# - Garage south wall W-G-S at y=40'-6 7/8", service door at x=5'-8'; both EV receptacles east
#   of it, clear of the door swing.
# - Sunken-garden porch: west wall W-SG-W1 axis x=8', inner face x=8.5', north end
#   y=-0.833'. Hot tub disconnect 7' south of that, under the deck — basement storey, so
#   Mount elevation 5' is -4' absolute.
# - PV junction box on the north gable (W-A-N2B since 2026-08-29) beside the radon riser
#   clamp cluster; at x=11' the 6:12 rake carries siding to 26'-5 3/8", so 25'-6" absolute
#   has cladding to grip. It was at x=9' under a 4:12 rake reaching 28'.

from typehaus import (
    ConduitRun,
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
                          # A meter socket is a plain galvanised can with a glass register,
                          # not the yellow slab the electrical-domain fallback colour draws
                          # (same reason ED-T-DISCONNECT-3R names a symbol) — `plan_symbol`
                          # gives it both the steel grey and the round dial.
                          plan_symbol="meter",
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # A 60A NEMA 3R safety switch is a small hooded grey can with a lever on its right side,
    # not the yellow slab the domain fallback colour draws — `plan_symbol` gives it both the
    # handle and the steel grey. Sized off the product (6-1/2" x 3-1/4" x 9-1/2"), about a
    # fifth under the placeholder it replaced.
    ElectricalDeviceType(tag="ED-T-DISCONNECT-3R", name="NEMA 3R disconnect, 240V",
                          footprint=(inch(6.5), inch(3.25)), height=inch(9.5),
                          plan_symbol="disconnect",
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
    # A wall jack. The catalog had an enclosure and two access points and no way to say
    # "a cable ends here at a plate", so a hardwired drop could not be modelled at all —
    # which is why RM-M-STUDY and RM-B-PLAY-N had none. Receptacle-sized because it is a
    # single-gang plate in the same box family, and NO ``poe_watts``: a jack is passive, and
    # a number here would land in the PoE budget as load that does not exist.
    ElectricalDeviceType(tag="ED-T-DATA-JACK",
                          name="Data outlet, single-gang RJ45 (Cat 6A)",
                          footprint=(inch(2.75), inch(2)), height=inch(4.5),
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
    # EQ-T-ERV is gone (2026-08-25), replaced by EQ-T-BROAN-B210E75RT in plan/mep_erv.py.
    # It was `24x24x30, 210 cfm, SRE 0.75` with two `# TODO verify datasheet` markers, and
    # its note ended: "outdoor-side intake/exhaust stay unmodeled since `Service` has no
    # OUTDOOR_AIR/EXHAUST_AIR member." `Service` has both now, so the machine has four
    # ports, and an ERV with an intake and a discharge is finally a modeled ERV.
    # --- The three Gree heat-pump systems (plans/TODO.md §HVAC) ----------------------
    # Outdoor units carry real Gree datasheet capacities (model # in each `source`), not
    # placeholders. `heating_capacity_at_design_btuh` linearly interpolates the datasheet
    # chart points bracketing the site's -15F design temp (plan/site.py) — the model does no
    # curve interpolation itself, so this field is the authored derate mep.heating_capacity
    # sizes each zone against. Indoor heads keep `# TODO verify datasheet` on purpose: they
    # carry no heating rating by design (a multi's heads share one compressor).
    #
    # System 1 — the concealed ducted air handler in RM-S-STUDY2's ceiling bulkhead
    # (SF-S-HP1) feeding the hallway trunk to the bedrooms plus the south branch and two
    # attic boots; Vireo R32 outdoor unit. One 24k system covers the whole upstairs.
    #
    # ** IT REPLACED EQ-T-GREE-SLIM24 ON 2026-08-30, AND THE PLACEHOLDER WAS LOAD-BEARING. **
    # That type was an explicit "REPRESENTATIVE PLACEHOLDER … TODO verify datasheet": 43 x
    # 21 x 11, 750 cfm on the trunk, no model number, no ESP, and all three ports at
    # (0, 0, 11") so no connection face was modelled at all. 43 3/8" wide is Gree's
    # DISCONTINUED low-static DUCT24HP230V1AD, which tops out at 589 cfm at 0.04" w.c. — it
    # cannot deliver the 750 cfm every duct in this house is sized to. The placeholder was
    # therefore not merely unverified; it invalidated the airflow, and its 21" case is what
    # made a 30 3/4" hall box look like it could hold a machine and a branch lane at once.
    #
    # WHY THIS UNIT AND NOT A SHALLOWER ONE. Connection geometry decides where a machine can
    # live: every concealed slim duct — Gree, LG, Samsung — puts supply on one long face and
    # return on the opposite long face, so air crosses the short depth and the long dimension
    # sits ACROSS the duct axis. Only a multi-position AHU connects on its ends, and the two
    # end-connected Gree AHUs (GMV-ND24A/B-T(U), FLEXX ECO R32) are both out on climate — the
    # first needs a GMV VRF outdoor unit whose floor is about -4 F, the second's heating range
    # stops at 5 F, against a -15 F design day. LG's KNUJB241A/LHN248HV1 is by far the best
    # FIT — 9 21/32" tall would have sat in the existing 14" drop — and is the one real loss
    # here: its matched KUSXA241A publishes 21,600 Btu/h at -13 F, but its published heating
    # range FLOOR is -13 F, two degrees short of this site's design temperature. Worth
    # revisiting only if LG publishes a lower floor.
    EquipmentType(tag="EQ-T-GREE-DUC24",
                  name="Gree concealed ducted air handler, 24k, R32",
                  footprint=(inch(44.47), inch(29.69)), height=inch(11.81),
                  cooling_capacity_btuh=24000,
                  source="Gree DUC24HP230V1R32AH concealed-duct air handler (R32). Cabinet 44 31/64 x 29 11/16 x 11 13/16 in, net weight 92.6 lb, airflow 577-1030 cfm over eight fan-speed notches, external static pressure 0.8 in. w.c. maximum. Paired with EQ-T-GREE-VIREO-GEN3 (VIR24HP230V1R32AO) outdoor: ~14,200 Btu/h at -13 F, minimum operating temperature -22 F, so the system's envelope brackets the site's -15 F design day. The indoor unit carries no heating rating of its own on purpose — the outdoor unit is what has to make heat at design temp, and mep.heating_capacity sizes the zone against the outdoor type. THIS REPLACED EQ-T-GREE-SLIM24, a REPRESENTATIVE PLACEHOLDER whose 43 in width matched only the discontinued low-static DUCT24HP230V1AD (589 cfm at 0.04 in. w.c.), which cannot move the 750 cfm this duct system is sized to.",
                  # Real face positions, replacing three ports stacked at (0, 0, 11"). The
                  # long dimension is x, so supply and return are on the two 44 1/2 x 11 13/16
                  # faces: supply out the north face (+y), return in the south face (-y), both
                  # on the cabinet's own centre height. Power enters at the north-east corner
                  # where the whip lands. This is what makes "supply north / return south, in
                  # line" a modelled fact rather than a sentence in a comment.
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(inch(22.235), inch(14.845), inch(11.81))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), inch(14.845), inch(5.905))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), inch(-14.845), inch(5.905))))),
    EquipmentType(tag="EQ-T-GREE-VIREO-GEN3",
                  name="Gree Vireo R32 outdoor unit, 24k",
                  footprint=(inch(37.72), inch(15.83)), height=inch(26.0),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=27000,
                  heating_capacity_at_design_btuh=13500,
                  cooling_capacity_btuh=22000,
                  min_operating_temp_f=-22.0,
                  source="Gree VIR24HP230V1R32AO (R32 refrigerant). OUTLINE AND FEET, from the Gree Vireo R32 Service Manual §3 outline diagram p.19 (the sheet is headed with this exact part number, shared with VIR18HP230V1R32AO): 37 23/32 x 25 63/64 x 15 53/64 in overall, foot holes 22 7/16 in apart across the width and 14 39/64 in across the depth, net weight 92.6 lb. This is the Vireo *R32* line and NOT the Vireo GEN3 (R410A), which is a different cabinet with a different foot pattern and a slot running the other way — the record read GEN3 and 38 x 16 x 32 in until 2026-08-28, and the height was wrong by 6 in. Datasheet chart: 27,000 Btu/h at 47F (the 47F rating holds despite the smaller at-design number below because this outdoor unit is paired with the EQ-T-GREE-DUC24 slim-duct air handler, not a wall head), ~16,100-16,500 Btu/h at 5F, ~14,200 Btu/h at -13F, ~12,000 Btu/h at -22F. -15F at-design (13,500 Btu/h) is linearly interpolated between the -13F and -22F chart points and additionally derated for slim-duct static-pressure loss. Cooling is the conservative end of the published 22,000-24,000 Btu/h range. min_operating_temp_f -22F per datasheet operating envelope.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # System 2 — Gree Multi Ultra, one 3-port outdoor unit driving three wall-mount heads
    # (basement gym, main-floor suite bedroom, living room). Rated to -22 F, which is what
    # makes it the unit carrying the three coldest-exposure rooms.
    EquipmentType(tag="EQ-T-GREE-MULTI-U30",
                  name="Gree Multi R32 3-port outdoor unit, 30k (-22F)",
                  footprint=(inch(40.16), inch(16.81)), height=inch(32.52),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=30000,
                  heating_capacity_at_design_btuh=23500,
                  cooling_capacity_btuh=28400,
                  min_operating_temp_f=-22.0,
                  source="Gree MUL30HP230V1R32AO. OUTLINE AND FEET, from the Gree Multi R32 Installation & Service Manual §3 outline diagram p.31 (the 30k has its own sheet; the 18/24k share a smaller one): 40 5/32 x 32 33/64 x 16 13/16 in overall, foot holes 25 in apart across the width and 15 19/32 in across the depth, net weight 145.5 lb. The record read 37 x 16 in until 2026-08-28 — 37 1/8 in is the width of the cabinet TOP, which is narrower than its base, and the 3 in of missing width put the unit within an inch of the balcony rim. Datasheet chart: 30,000 Btu/h at 47F, 27,000 Btu/h at 5F, ~24,500 Btu/h at -13F, ~21,500 Btu/h at -22F. -15F at-design (23,500 Btu/h) is linearly interpolated between the -13F and -22F chart points. Cooling 28,400 Btu/h and min_operating_temp_f -22F per datasheet.",
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
    # Exterior west wall at y=29', 7" outside the sheathing plane. Moved out 1/2"
    # on 2026-08-23 with the Swinburne truss (cladding face 5.02" -> 5.5" proud) and a
    # further 1" on 2026-08-26 with the catlin truss (5.5" -> 6.5"); each time the meter's
    # back was left inside the cladding it is surface-mounted on.
    #
    # Height (2026-08-27): the elevation is the *base* of the 16" socket and the project
    # datum is the main floor, so the authored 5'-0" put the glass 8'-6" above SITE_GRADE
    # (-2'-10") — a ladder job, not a meter. 1'-6" here is grade + 4'-4" to the base and so
    # grade + 5'-0" to the register centre, mid-band of the utility's 4'-0"..6'-0" window.
    ElectricalDevice(uid="CEE001AAAA", tag="ED-M-METER", kind=DeviceKind.METER,
                     position=pt(ft(0, -10.25), ft(29, 9.125)), type_ref="ED-T-METER",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(1, 6)), room=None, rotation=deg(270)),
]

# --- the backup microgrid (2026-08-02, notes/backup_power.md) ------------------------
# Four pieces, positions carry the design: EQ-B-ESS-BATT is the only thing in the RM-B-ESS
# Type X closet, which moved to the furnace room's NE corner on 2026-08-23;
# EQ-B-ESS-INV sits outside it, mid-room against the east concrete (not a fire risk, needs
# to be reachable to reset); ED-B-BACKUP-PANEL is on the west wall on the inverter's
# dedicated load output; ED-B-BACKUP-ENCL stays in place but demoted to shed-tier relays +
# 24V bus only, no feed of its own. Only the battery moved with the closet — which is why
# the DC run between it and the inverter grew, and why that is flagged on the battery below
# rather than quietly absorbed.
BACKUP_ENCLOSURE = [
    # circuit= is gone with CKT-BACKUP-FEED (plan/circuits.py): this enclosure's gear lives
    # downstream of the inverter's load output now, and naming a grid-side branch circuit on
    # it said the opposite.
    ElectricalDevice(uid="CEE002AAAA", tag="ED-B-BACKUP-ENCL", kind=DeviceKind.PANEL,
                     position=pt(inch(11), ft(32, 6)), type_ref="ED-T-BACKUP-ENCL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room="RM-B-FURNACE", rotation=deg(90)),
    # The subpanel the two backup tiers are homed to (plan/circuits.py). On the west wall
    # 2'-0" south of ED-B-PANEL, so the inverter's grid conductors and its load conductors
    # run to two enclosures a person can stand between.
    ElectricalDevice(uid="CEE060AAAA", tag="ED-B-BACKUP-PANEL", kind=DeviceKind.PANEL,
                     position=pt(inch(10), ft(27)), type_ref="ED-T-BACKUP-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room="RM-B-FURNACE", rotation=deg(90)),
]

ESS_EQUIPMENT = [
    # On the NE closet's north wall, W-B-N3 (2026-08-23; was the SE closet, 2026-08-02).
    # (8'-1 1/5", 34'-11") puts the 10"-deep cabinet's back flat on that wall's inner face at
    # y=35'-4" and centres it in the 2'-9 5/8" clear width, north of D-B-ESS's swing.
    #
    # **This is a 300 lb wall load and the wall matters.** It hung on 12" concrete when it
    # was first authored, the 2026-08-21 overhaul reframed that stub as steel studs, and the
    # note here said the load then wanted blocking or a backing plate. The move puts it back
    # on cast concrete — an 8" pour, anchored directly. That is a better fixing than either
    # of the two before it and it is the quiet win in this relocation.
    #
    # `code.R327_ess_capacity` reads `room="RM-B-ESS"` to count this as indoor storage
    # (14.3 of the 40 kWh article limit) — a future garage relocation is just this one line.
    #
    # **Flag, not a silent acceptance: the DC run got about 10' longer.** EQ-B-ESS-INV is at
    # (8'-1 13/16", 24'-11 7/8") and ED-B-BACKUP-PANEL at (0'-10", 27'-0"), both of which
    # stayed put; the battery went from ~4'-9" to ~10'-0" of conductor from the inverter. On
    # an EG4 12kPV that is real copper and a real voltage-drop question, and it is the one
    # argument that could send this decision back — the corner was chosen for the battery's
    # separation zone and its concrete fixing, not for the run length.
    Equipment(uid="CEQ020AAAA", tag="EQ-B-ESS-BATT", kind=EquipmentKind.BATTERY,
              position=pt(ft(8, 1.2), ft(34, 11)), footprint=(inch(24), inch(10)),
              type_ref="EQ-T-ESS-BATT",
              room="RM-B-ESS", circuit="CKT-ESS-GRID",
              mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # The inverter, outside the closet on the furnace room's west wall. Not on a branch
    # circuit: its grid port IS CKT-ESS-GRID, which is a source, and its load output feeds
    # ED-B-BACKUP-PANEL.
    Equipment(uid="CEQ021AAAA", tag="EQ-B-ESS-INV", kind=EquipmentKind.INVERTER,
              position=pt(m(1.35596), m(10.6076)), footprint=(inch(27), inch(12)),
              type_ref="EQ-T-EG4-12KPV",
              room="RM-B-FURNACE", circuit="CKT-ESS-GRID",
              mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]

# --- Basement: backup outlets, sauna, spa (sunken garden files on this storey) --------
# Face-mounted devices on the perimeter concrete moved 4" with the 2026-08-21 12" -> 8"
# thinning (see storeys/basement.py): the walls align on their EXTERIOR face, so the inside
# face is what moved — west from x=1'-0" to 0'-8", north from y=35'-0" to 35'-4", south from
# y=1'-0" to 0'-8". Every position here that used to sit 1"-3" off one of those faces was
# shifted by the same 4", which is what `test_wall_mounted_devices_resolve_against_a_wall_face`
# reads.
BASEMENT_DEVICES = [
    # HA server + router (backup). Beside the panel in the furnace room.
    ElectricalDevice(uid="CEE003AAAA", tag="ED-B-UTIL-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(9), ft(28)), type_ref="ED-T-RECEPTACLE", circuit="CKT-HA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # Sump pump (backup; ~1000W start). GFCI lives at the breaker, not the outlet.
    ElectricalDevice(uid="CEE004AAAA", tag="ED-B-SUMP-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4, 6), ft(35, 3)), type_ref="ED-T-RECEPTACLE", circuit="CKT-SUMP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # On the sauna's west liner wall immediately south of EQ-B-SAUNA-HTR (footprint y
    # 8'-0"..9'-6"), low like the heater terminals. Old (15', 7') position was off-wall and
    # is now inside FURN-B-SAUNA-BENCH-E.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(9, 4.875), ft(7, 9)), type_ref="ED-T-SAUNA-JB", circuit="CKT-SAUNA",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18)), rotation=deg(90)),
    # Hot tub in the sunken garden: disconnect on the west porch wall, 7' from its north
    # end, under the porch deck (see header). NEC 680.22 convenience receptacle beside it.
    # x is 1 5/8" off W-SG-W1's east face (x=8'-6"), not 2": the can is 3 1/4" deep, and the
    # 2" standoff the four DISCONNECT-3R boxes were authored with dates from when the type
    # carried a placeholder 4" depth. Its back now sits on the concrete.
    ElectricalDevice(uid="CEE010AAAA", tag="ED-B-SPA-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(8, 7.625), ft(-7, -10)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-SPA",
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
    # The ventilator, retyped to the real machine on 2026-08-25 — a Broan B210E75RT, four
    # 6" round top ports, in place of a placeholder that carried two `# TODO verify
    # datasheet` markers. Same uid, same position, same room, same circuit: the unit did not
    # move, it stopped being generic. Everything downstream of it — the manifolds, the four
    # chase risers, the outdoor side that did not exist, the radials — is in plan/mep_erv.py,
    # and `pan_drain_ref` names the condensate line a cold-climate core makes water into
    # (plan/mep_drainage.py). The footprint on the element is documentation; the TYPE's
    # 24.8" x 21" is what resolves.
    #
    # **Moved 12 5/8" south 2026-08-27, to (3'-11 1/2", 30'-6").** The Broan's real case is
    # 24.8" x 21" where the placeholder's was 24" x 24", and at the drag-authored
    # (3'-11 7/16", 31'-6 5/8") its north-east corner stood 35.5" from EQ-B-ESS-BATT — half
    # an inch inside the battery's 36" REQUIRED separation zone (x 49 1/4"..145 1/4",
    # y 378"..460"), which `advisory.ess_clearance` grades as a rectangle, not a radius. The
    # y=30'-6" line puts the case's north edge at 376 1/2", 1 1/2" clear of it, and buys a
    # second thing for free: at the old y the case overlapped ED-B-BACKUP-ENCL's 36" NEC
    # 110.26 working space, and it no longer does. Nothing downstream moves — every ERV
    # branch is authored off the two manifolds (plan/mep_erv.py), not off the machine, and
    # PR-B-ERV-COND's drop at (3'-11", 30'-9") is still under the case.
    Equipment(uid="CEE016AAAA", tag="EQ-B-ERV", kind=EquipmentKind.ERV,
              position=pt(ft(3, 11.5), ft(30, 6)), footprint=(inch(24.8), inch(21)),
              room="RM-B-FURNACE", type_ref="EQ-T-BROAN-B210E75RT", circuit="CKT-ERV",
              # HUNG, not floor-standing (2026-08-25). Two reasons and the second is the
              # binding one: a Broan ships with hanging straps and this is how the unit
              # installs, and a floor-standing ERV cannot drain by gravity. Its core makes
              # water all winter, the nearest receptor is FX-B-SAUNA-FD nine feet up the
              # basement's other end, and a spigot at slab level has nowhere to fall to. At
              # a 6'-0" base the 21.6" case tops out at 7'-9 5/8", three inches under the
              # basement's 8'-0 15/16" clear.
              mount=Mount(kind=MountKind.CEILING, elevation=ft(6)),
              pan_drain_ref="PR-B-ERV-COND"),
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
    # 2026-08-29: y +1 5/8" (18'-0 3/8" -> 18'-2") with W-M-CLN's laundry face when that
    # wall was retyped to INT_2X4_STAGGERED_DOUBLE_GWB (storeys/main.py). Both boxes here
    # are `recessed_into_host_surface`, so a stale y does not merely float — it resolves
    # inside the studs. ED-M-LAUNDRY-RC1 below moved the same 1 5/8" for the same reason.
    # CKT-DRYER stays a 30A/14-30R even though the LG DLHC5502V heat-pump dryer only needs
    # 830W/15A minimum branch: it still ships a 4-prong cord needing 30A, and the oversize
    # lets a future conventional vented dryer go in without repulling wire.
    # 2026-08-30: y -5/8" (18'-2" -> 18'-1 3/8") with the follow-up retype to the
    # single-gwb INT_2X4_STAGGERED_GWB (1 1/4" thinner) — the same reasoning in reverse,
    # by half the distance. ED-M-LAUNDRY-RC1 below moved the same 5/8" the same way.
    ElectricalDevice(uid="CEE007AAAA", tag="ED-M-LAUNDRY-DR1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(9, 6), ft(18, 1.375)), type_ref="ED-T-RECEPTACLE-1430",
                     circuit="CKT-DRYER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43),
                                 recessed_into_host_surface=True)),
    # CKT-LAUNDRY (circuits.py slot 36, 20A) was scheduled but the outlet never drawn — this
    # is it: washer half of the stack, 8" east of the dryer box, same 43" band. NEC 210.52(F),
    # the room's only 120V outlet.
    ElectricalDevice(uid="QBSRR1MWVB", tag="ED-M-LAUNDRY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10, 2), ft(18, 2.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-LAUNDRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43),
                                 recessed_into_host_surface=True)),
    # Freezer beside the fridge (KRF1 at (18'-4 3/8", 31'-4 5/8")) on the centre wall's east
    # face; fridge + freezer + PoE WiFi share the backup kitchen circuit.
    # y 29'-10" -> 29'-5 1/4" -> 29'-9 1/4" (both 2026-08-24). It went south when the pantry
    # room's partition took the north end of the run, then came back north with the whole
    # cold run when W-M-PAN-S moved 4" (storeys/main.py). This box stays behind its own
    # appliance (freezer now y 27'-4 7/8"..30'-1 3/4") — the same constraint that decided
    # which end of the old 72" bay the retired filler went to.
    ElectricalDevice(uid="CEE006AAAA", tag="ED-M-LIVING-KFZ1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(29, 9.25)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # System 3 (Sapphire, backup battery circuit): its outdoor unit stands on the north
    # side beside the mudroom door, so the disconnect goes on W-M-N2's exterior face west
    # of the breezeway — clear of ED-M-HP1-DISC's condenser gap.
    # Moved out 1/2" on 2026-08-23 with the Swinburne truss's cladding face, 3/8" back in
    # on 2026-08-25 with the can's true 3 1/4" depth (see ED-M-HP1-DISC), and out 1" again
    # on 2026-08-26 with the catlin truss (5.5" -> 6.5" proud).
    ElectricalDevice(uid="CEE026AAAA", tag="ED-M-HP3-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(4), ft(36, 8.875)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP3",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # FH-M-BATH2's thermostat: inside the room on its south wall (W-M-BDN1, interior face
    # y=13'-2 3/8"). Floor sensor is FH-M-BATH2's `stat` point.
    #
    # x moved from 4'-9" to 0'-11 3/4" — WEST of D-M-BATH2's opening (x 1'-6 1/2"..4'-0 1/2")
    # rather than 8" east of it, so it is no longer the wall you reach as the door closes
    # behind you but the return beside FX-M-BATH2-SINK. That x is kept as authored.
    #
    # y snapped back to 13'-3 3/8" (2026-08-29). The drag that set the x left y at 13'-2 15/16",
    # which is 9/16" INSIDE W-M-BDN1's finish — `test_wall_mounted_devices_resolve_against_a_
    # wall_face` grades the resolved body, not the authored point, and it caught this. 13'-3 3/8"
    # is the value that puts the plate's back ON the face, and it is what the y was before
    # the drag; only the x was ever meant to move.
    ElectricalDevice(uid="CEE021AAAA", tag="ED-M-BATH2-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(m(0.298408), ft(13, 3.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH2", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # FH-M-DINING's thermostat: zone is free-standing mid-room, so control goes on the
    # nearest real wall — east wall interior face x=35'-5 3/8" (corrected 2026-08-03 from
    # 35'-11 3/8", which sat in the studs; CATLIN_EXT_2X6's inside face is 6 5/8" in from the
    # 36' sheathing plane). Sits in the 5'-1" clear stretch between WIN-M-LIV-E2 and
    # WIN-M-DIN-E2, 10" clear of ED-M-LIVING-RC3 at y=16'-11".
    # FX-M-BATH2-TUB's Bask outlet (2026-08-29). Kohler: "A qualified electrician must
    # install a GFCI-protected, 120 V, 15 A, grounded outlet. Locate the outlet BEHIND THE
    # BATH and WITHIN 24 in. of the power supply." The bath ships cord-and-plug with its
    # supply factory-wired to a board on the shell, so this is the whole electrical scope —
    # there is no hardwired junction box to place, and CKT-BATH2-TUB is the dedicated
    # circuit the spec sheet requires.
    #
    # Inside SL-M-TUBDK's deck box, on W-M-TUBDK-W's bay face (x=4'-8 1/2") at y=16'-8.9",
    # facing east, 8" up off the subfloor — above any water that ever finds the box.
    #
    # x=4'-9 1/2" puts the box's BACK on that face, not its centre — ED-T-RECEPTACLE-GFCI
    # is a 4" x 2" body and half of it authored at the face resolves inside the studs
    # (`test_wall_mounted_devices_resolve_against_a_wall_face`, which is how this was
    # caught). The 4" reads along y here because the type has no way to say the box is hung
    # with its long axis vertical, which is how it is actually mounted; the foot bay is
    # 4 1/16" and would not take a horizontal one.
    #
    # ** y IS IN THE FOOT BAY, SOUTH OF THE BATH, AND THAT IS THE POINT. ** The obvious spot
    # is further north, on the same face beside the shell — and it does not work: the bath
    # sits 3/16" off that face, so a receptacle there would have the acrylic hard against
    # its cover and nowhere for a plug to project. South of the bath's foot (16'-10 15/16")
    # the bay is 4 1/16" x 36" of open box, and the cord plugs in facing EAST down the 36",
    # not north into the 4" — which is why this wall and not the south knee wall.
    # FURN-M-BATH2-TUBDK-AP is directly outside it in the same wall (plan/placeables.py);
    # the existing FURN-M-BATH2-TUB-AP in W-M-BA2E's laundry face reaches the trap, not this.
    #
    # ** THE 24" IS THE ONE DIMENSION HERE THAT IS NOT VERIFIED. ** Kohler publishes neither
    # the cord length nor where on the shell the power supply sits, and this bath is 5'-0"
    # long: this outlet is within 24" of a board at the foot and is not within 24" of one at
    # the head. Measure it against the delivered bath before the knee wall is
    # closed. Moving the box is a 15-minute job while the bay is open and a demolition
    # afterwards.
    #
    # RECEPTACLE, not RECEPTACLE_GFCI: the protection is at the breaker (CKT-BATH2-TUB's
    # `gfci=True`), which is what the house does everywhere and is the only thing that works
    # here — a GFCI device sealed inside a knee-wall box cannot be tested or reset.
    ElectricalDevice(uid="CEE041AAAA", tag="ED-M-BATH2-TUB-RC", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(4, 9.5), ft(16, 8.9)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-BATH2-TUB", room="RM-M-BATH2", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(8))),
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
    # not reach). Both on the wall's exterior face (y=-7 1/2"), corrected 2026-08-03 from
    # y=+6" which put a 3R disconnect on the interior side of the wall from its condenser,
    # and moved out a further 1/2" on 2026-08-23 when the Swinburne truss took the cladding
    # face from 5.02" to 5.5" proud of the sheathing plane, and 1" more on 2026-08-26 when
    # the catlin truss took it to 6.5". Pulled 3/8" back in on 2026-08-25:
    # ED-T-DISCONNECT-3R is a 3 1/4"-deep can, so its centre belongs 1 5/8" off the cladding
    # face, and the 2" these were authored with dates from the type's old placeholder 4"
    # depth. Same correction on ED-M-HP3-DISC and ED-B-SPA-DISC.
    #
    # **Both slid east/west 2026-08-27 to stand beside the units they kill**, which is what
    # NEC 440.14 asks of them and what neither did before: HP1's box was 24" west of
    # EQ-M-HP1-OD (x 96"..112") and HP2's was 88" *east* of EQ-M-HP2-OD (x 202"..218"),
    # around a corner from it. They now sit 7 1/4" off HP1-OD's west edge and on HP2-OD's
    # east edge respectively. y stays at -8 7/8": that is the 3 1/4" case's back edge exactly
    # on W-S-S1/W-S-S2's cladding face at y=-7 1/4", and the drag that moved the x had left
    # both boxes floating 3/8" proud of it (`test_wall_mounted_devices_resolve_against_a_wall_face`).
    # ED-M-HP2-DISC straddles the W-S-S1/W-S-S2 break at x=18'-0" — collinear walls with the
    # W-S-C1 tee's framing behind the joint, so the backing is there.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-HP1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(7, 1.5), ft(0, -8.875)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP1", mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room=None),
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-HP2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(18, 0.25), ft(0, -8.875)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP2", mount=Mount(kind=MountKind.WALL, elevation=ft(5)), room=None),
    # FH-S-BATH1's thermostat, inside the room on its south wall (W-S-BD-N1B, interior
    # face y=26'-4 11/16"), 9" west of D-S-BATH1's opening (x 7'-3"..9'-9"). Same
    # reach-as-the-door-shuts position as ED-M-BATH2-FH-STAT, and clear of the fixture
    # cluster, which all sits north of y=29'-9".
    ElectricalDevice(uid="CEE025AAAA", tag="ED-S-BATH1-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 6), ft(26, 10.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH1", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # ** RM-S-SUITEBATH AND RM-S-VANITY BOTH HAD NO RECEPTACLE AT ALL UNTIL 2026-08-30. **
    # Same NEC 210.52(D) gap as RM-M-BATH1 above, and the same reason it went unnoticed: the
    # engine encodes E3902's GFCI-location rule but nothing encodes E3901.6 / 210.52(D)'s
    # "one within 36 in. of each sink", so a bathroom with zero outlets draws no finding.
    #
    # SUITEBATH sits on W-S-SN3 immediately WEST of the 30" vanity rather than beside its
    # mirror: the mirror is 24" wide on a 30" cabinet, which leaves 3 1/2" and 2 1/2" of wall
    # at the two ends and a device plate needs 4". About 12" to the basin's nearest edge. It
    # is west of the water closet's 15" side band in plan, which does not matter -- at 44" AFF
    # it is nowhere near that envelope's clear FLOOR space, and `_clearance_conflicts` tests
    # bodies that stand in the zone, not things hung above it.
    ElectricalDevice(uid="ZQBJ03VGYD", tag="ED-S-SUITEBATH-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(148), inch(263.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND", room="RM-S-SUITEBATH", rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44))),
    # ** ONE OUTLET SERVES BOTH BOWLS IN THE ALCOVE, AND THAT IS DELIBERATE. ** 210.52(D)
    # asks for one within 36" of EACH sink, not one per sink. At x=5'-4 1/2", east of
    # ED-S-VANITY-SW and past MIRROR2's end, it is 8.9" from the east bowl's edge and 33.2"
    # from the west bowl's -- inside 36" for both, with 2.8" to spare on the far one. ** That
    # margin is the thing to re-check if either cabinet moves **: the 60" run is already at
    # the code minimum for bowl spacing, so there is no slack to absorb a shift. A second
    # receptacle between the mirrors is the fallback, and it does not fit today (the gap
    # there is 3" and a plate needs 4").
    ElectricalDevice(uid="J9JPM7DWDS", tag="ED-S-VANITY-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(64.5), inch(313.625)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND", room="RM-S-VANITY", rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44))),
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
    #
    # BOTH STAND 12" CLEAR OF THE PLANK (2026-08-28), on the aluminium frames authored as
    # PT-SG-HPA1..4 / PT-SG-HPB1..4 in params/sunken_garden.py, bolted down through the deck
    # into blocking. Three facts about that, none of which is visible from this file:
    #
    #  * The stand is REQUIRED, not a nicety. Gree's service manual §8.6 says to fix the foot
    #    holes with bolts onto a support rated to four times unit weight, and IRC M1401.4
    #    makes a manufacturer instruction mandatory. A condenser at +10' on an open deck also
    #    overturns and slides long before its own weight holds it.
    #  * The stand's legs DO NOT sit under the cabinets' own feet. They are placed to land in
    #    joist bays clear of the three balcony beams, because the anchors must reach
    #    sacrificial blocking rather than a beam or a joist — see `_HP_STAND_AT`.
    #  * 12" is the owner's number against a guide's 18"-24". It still clears the 42" guard
    #    once the cabinet is on it (12 + 32/34 = 44"/46"), which is what the airflow needed.
    #
    # ``mount.elevation`` is the whole height change: `resolved_mount_elevation` returns
    # floor + elevation for a FLOOR mount. THE TWO NUMBERS ARE COUPLED — this and
    # `_HP_STAND_HEIGHT_IN` in params/sunken_garden.py describe one dimension in two modules
    # that cannot import each other. `mep.deck_equipment_support` is what holds them
    # together; do not change one without the other.
    #
    # ** 13 1/2", NOT 12", AND THE 1 1/2" IS THE PLANK. ** A FLOOR mount measures from the
    # storey datum, and on `second` that datum is FS-SG-DECK's JOIST TOPS at 10'-0". The
    # stand does not stand there — it stands on the aluminium plank laid over them, 1 1/2"
    # higher, which is also where its base plate is bedded and where the lag crosses the
    # waterproof plane. Authoring 12" here put both cabinets 1 1/2" below the tops of their
    # own legs. This is the same trap the porch beam hangers fell into at `_porch_top`.
    #
    # `drain_pan`/`pan_drain_ref`: a cold-climate heat pump in heating mode sheds defrost
    # meltwater all winter, and this one does it over an occupied porch. Left to run onto the
    # deck it sheets 8'-8" of bare aluminium to the drip edge and refreezes on the way, on a
    # surface two doors open onto, then ices the box gutter and plugs the 3" leader.
    Equipment(uid="CEE017AAAA", tag="EQ-M-HP1-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(9, 2), ft(-2, -6)), footprint=(inch(37.72), inch(15.83)),
              rotation=deg(90), mount=Mount(kind=MountKind.FLOOR, elevation=inch(13.5)),
              drain_pan=True, pan_drain_ref="PR-S-HP1-COND",
              type_ref="EQ-T-GREE-VIREO-GEN3", circuit="CKT-HP1", room=None),
    Equipment(uid="CEE018AAAA", tag="EQ-M-HP2-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(17, 6), ft(-2, -6)), footprint=(inch(40.16), inch(16.81)),
              rotation=deg(90), mount=Mount(kind=MountKind.FLOOR, elevation=inch(13.5)),
              drain_pan=True, pan_drain_ref="PR-S-HP2-COND",
              type_ref="EQ-T-GREE-MULTI-U30", circuit="CKT-HP2", room=None),
    # System 1's concealed ducted AH — inside SF-S-HP1, the wide bulkhead in RM-S-STUDY2's
    # ceiling (plan/storeys/second.py). Own branch circuit (CKT-HP1-AH) since a ducted unit's
    # blower is fed at the unit, unlike a multi's heads.
    #
    # ** IT CAME OUT OF SF-S-DUCT ON 2026-08-30, WITH THE PLACEHOLDER THAT FIT THERE. ** The
    # unit lived at the hall box's south end from 2026-07-30, and every layout decision on
    # this storey was built around a 21"-wide case leaving ~4 7/8" either side of a 30 3/4"
    # cavity. That case was EQ-T-GREE-SLIM24, a REPRESENTATIVE PLACEHOLDER (see the type
    # above): the real machine is 44 1/2 x 29 11/16 and no 35" box holds it. The 4 7/8"
    # slivers were never a lane for a branch either, which is exactly why DU-S-HP-SOUTH had
    # no riser and plans/TODO.md stayed open — the packing problem was an artifact of a
    # placeholder, not a fact about the house.
    #
    # `soffit_ref` is the 2026-08-25 correction and still load-bearing: WITHOUT it a CEILING
    # mount with no stated elevation hangs off `storey.default_ceiling_height`
    # (resolve/placeables.py), which put this unit at 9'-0", above the box it lives in.
    #
    # `rotation` is GONE with the placeholder. It existed because `EquipmentType.footprint`
    # wins over the element's and the old type stated (43, 21) — the long dimension the wrong
    # way round for a case that runs across the hall. EQ-T-GREE-DUC24 states (44.47, 29.69),
    # which is the cabinet as installed: 44 1/2" across x, 29 11/16" along the airflow, supply
    # out the north face into the trunk and return in the south face out of the return
    # chamber. Nothing to rotate, and `footprint` here now agrees with the type rather than
    # fighting it.
    #
    # (20'-7", 3'-9") puts the case at x 224 3/4"..269 1/4" and y 30 1/8"..59 7/8": 2 5/8"
    # inside SF-S-HP1's west cavity face, clear of both lanes that pass it by more than the
    # 2" hanger gap, and — the part that is geometry rather than tidiness — with its north
    # face 9 3/4" south of ST-S2A's lowest stringer face, so the supply plenum, the branch
    # take-off and the ERV's east jog all sit south of the stair rather than under it. The
    # check prints the clearances; do not restate them here.
    #
    # zone_rooms covers the whole conditioned second storey plus RM-A-STUDY/RM-A-EAST-UNFIN (short
    # attic branches) and RM-A-WEST-UNFIN (suite branch's REG-A-HP-WEST boot, 2026-07-30).
    # RM-A-DEN used to be excluded here — nothing served it — but the room was deleted
    # 2026-08-27 and its 43 sf is inside what is now RM-A-STUDIO, which this zone names.
    #
    # THE WEST LOFT BECAME THREE ROOMS ON 2026-08-29 and all three are named here, because
    # the one boot (REG-A-HP-WEST, still on the suite branch) is what conditions the whole
    # of the old room's footprint. The studio is the room that wanted it; the bath and the
    # storage pocket are on the same air, through the same branch, and dropping either from
    # this list would report them as unheated rather than as what they are.
    # The old gap in the zone closed by itself; the TODO entry it pointed at is moot.
    Equipment(uid="CEE032AAAA", tag="EQ-S-HP1-AH",
              kind=EquipmentKind.DUCTED_AIR_HANDLER,
              position=pt(ft(20, 7), ft(3, 9)), footprint=(inch(44.47), inch(29.69)),
              room="RM-S-STUDY2", type_ref="EQ-T-GREE-DUC24",
              outdoor_ref="EQ-M-HP1-OD", circuit="CKT-HP1-AH",
              mount=Mount(kind=MountKind.CEILING), soffit_ref="SF-S-HP1",
              zone_rooms=("RM-S-STUDY2", "RM-S-PLANT", "RM-S-BED1", "RM-S-BED2",
                          "RM-S-BED3", "RM-S-SUITE", "RM-S-SUITEBATH", "RM-S-VANITY",
                          "RM-S-BATH1", "RM-S-HALL", "RM-S-CLOSET", "RM-S-NCLOSET",
                          "RM-A-EAST-UNFIN", "RM-A-STUDY", "RM-A-STUDIO",
                          "RM-A-STUDIO-BATH", "RM-A-POCKET")),
    # The duct heater above, downstream of the coil in the supply trunk — inside SF-S-DUCT,
    # 17" north of the y=8'-9 5/8" seam SF-S-HP1 hands the trunk over on, so it heats every
    # branch the trunk feeds rather than one room's boot.
    #
    # ** RE-CENTRED ON THE DUCT IT HEATS, 2026-08-30. ** It sat at x=19'-10" against a trunk
    # centred on 19'-4" — six inches off the duct it is plumbed into, an existing defect that
    # nothing had reported, because `mep.duct_soffit_occupancy` reads a duct running THROUGH
    # a machine as plumbed to it and stops there. x=19'-6" is the 18x8 trunk's new centreline.
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
              position=pt(ft(19, 6), ft(10, 3)), footprint=(inch(16), inch(10)),
              room="RM-S-HALL", type_ref="EQ-T-DUCT-HEATER-2KW",
              circuit="CKT-HP1-STRIP", mount=Mount(kind=MountKind.CEILING),
              # Same 2026-08-25 correction as the air handler above: without `soffit_ref`
              # this hung at the 9'-0" storey ceiling instead of inside the box it is
              # plumbed into. Its 16"x10" plate is measured against SF-S-DUCT's derived
              # cavity by `mep.duct_soffit_occupancy`, and DU-S-HP-SUP's centreline runs
              # through it, which is what tells the check the two are one assembly rather
              # than two things fighting for the same lane.
              soffit_ref="SF-S-DUCT"),
]

# --- Garage: both EV receptacles on the south wall, east of the service door ----------
# ED-G-EV-1450 is on W-G-S's INTERIOR face, so it followed the wall 1" north on 2026-08-26
# when the catlin truss pushed the house's cladding out and the whole 24'x24' garage moved
# with it (plan/storeys/garage.py::GARAGE_Y_SOUTH). Same move as ED-G-SW and ED-G-EXT-SW in
# plan/lighting.py, and the same 1/2" move all three made on 2026-08-23.
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(0, 9.625), ft(56, 0.75)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE", rotation=deg(90)),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(19, 11.375), ft(41, 5.875)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE"),
]

GARAGE_EQUIPMENT = [
    # West wall — the only wall with nothing else in it. Mounted 6'-0" on an 8' wall, 15"
    # case tops at 7'-3", blows down over a bench.
    # Hard-wired, not cord-and-plug: NEC 210.8(A)(2) GFCI applies to garage *receptacles*
    # only, so CKT-GAR-HEAT carries none — a plug-in unit would need CKT-RC-GARAGE instead.
    # Nudged 12" south of the 2026-08-21 NW-corner position (y was 18.1628): at that y the
    # case straddled FX-G-HYDRANT's own y band, and the hydrant is the one thing in this
    # corner someone stands over with a hose. 12" takes the two bands apart without moving
    # the heater off FURN-G-WORKBENCH, which it is here to blow down over.
    Equipment(uid="CEE023AAAA", tag="EQ-G-HEATER", kind=EquipmentKind.SPACE_HEATER,
              position=pt(m(0.213454), m(17.858)), footprint=(inch(14), inch(9)),
              room="RM-GARAGE", type_ref="EQ-T-GARAGE-HEATER", rotation=deg(90),
              circuit="CKT-GAR-HEAT",
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
]

# --- Attic: PV junction box beside the radon riser -----------------------------------
PV_JBOX = [
    # Moved out 1/2" on 2026-08-23 with the Swinburne truss's cladding face, 3/8" back in
    # on 2026-08-25 with the can's true 3 1/4" depth (see ED-M-HP1-DISC), and out 1" again
    # on 2026-08-26 with the catlin truss (5.5" -> 6.5" proud).
    #
    # ** MOVED x 9'-0" -> 11'-0" ON 2026-08-29, and it had to. ** The gable's rake follows
    # the roof, and at 6:12 off a 20'-11 3/8" eave the plane stands at 25'-5 3/8" at x=9'-0"
    # — 1/2" BELOW this box's own 25'-6", i.e. the enclosure was on the roofing rather than
    # the siding. At x=11'-0" the plane is 26'-5 3/8" and the box hangs with 11" of cladding
    # over it. It follows VR-M-RADON-VENT's riser east on the same pass (mep_venting.py) and
    # is still beside it: the riser jogs to x 9'-7 1/2", so the box is 1'-4 1/2" east of it.
    #
    # ** IT SITS ON W-A-N2B NOW, NOT W-A-N2 ** — the north gable split at x=10'-0" on
    # 2026-08-29 and 11'-0" is east of that. test_catlin_outdoor_structures.py names the
    # wall it must ride below; that assertion follows the box.
    # ** MOVED AGAIN, 11'-0" -> 10'-2", ON 2026-08-30: x=11'-0" IS INSIDE A WINDOW. **
    # The 2026-08-29 move solved the rake and walked into WIN-A-N1, whose rough opening is
    # x 10'-9"..13'-3" (framing bumper 10'-7"..13'-5"), sill +22'-0", head +25'-0". At x=11'-0"
    # this box hangs on the facade 3" inside that window's west jamb with its centre 6" over
    # the head, and CD-A-PV-EAST's riser clipped the opening's top corner for 3" reaching it.
    # `mep.run_through_opening` found the conduit; the box was found by looking at why.
    #
    # Both constraints are satisfiable at once and the band is narrow. The rake wants
    # x >= 9'-1 1/4" (the gable plane is 20'-11 3/8" + x/2, and this box needs 25'-6"); the
    # window wants x <= 10'-7" or x >= 13'-5". Those do not overlap at 25'-6": the ROOF
    # UNDERSIDE (20'-1 1/2" + x/2, which is the plane `integrity.element_above_roof` reads,
    # and is a foot below the cladding plane the 2026-08-29 note reasoned from) needs
    # x >= 10'-10" to carry a 25'-6" riser, and the window starts at 10'-9". **So the box
    # drops to 25'-0" as well as moving to 10'-2"**, where the underside is 25'-4" and there
    # is 4" of clearance. On the facade it is then wholly west of the window rather than
    # perched over its corner, which is the better elevation anyway.
    #
    # Going east instead (x >= 13'-7") clears the window at the original 25'-6" and costs
    # 2'-6" of 1 1/2" EMT to reach a worse station: further from VR-M-RADON-VENT's riser,
    # and out over the stair void's bay.
    #
    # Still on W-A-N2B, which spans x 18'-0"->10'-0" — 10'-2" is 2" east of that split, so
    # test_catlin_outdoor_structures.py's wall assertion is unchanged.
    ElectricalDevice(uid="CEE014AAAA", tag="ED-A-PV-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(10, 2), ft(36, 10.25)), type_ref="ED-T-PV-JB", circuit="CKT-ESS-GRID",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]
# ** CN-A-PV-CLAMP is GONE (2026-08-26), for the same reason as CN-A-NEMA-CLAMP **
# (plan/mep_electrical.py, which carries the full note). It was a plain S-5! seam clamp on
# W-A-N2, and W-A-N2 wears `pbr-panel-26` now — an exposed-fastener panel with no seam. At
# x=9' the rake is well above the box's 25'-6", so this was wall and not roof, and a seam
# clamp there is not merely unnecessary but uninstallable. The box is screwed through the
# panel into the girt with the same gasketed T09150HWAM the panel is hung on, and those are
# inside the field-grid screw count.
#
# NOT to be confused with the 48 S-5-PVKIT clamps in params/solar.py: those are on the
# mechanically seamed ROOF, which is untouched, and they stay exactly as they are.
PV_JBOX_CLAMP = []

# --- Conduit trunks (electrical_notes.md line 3: make it easy to run new lines) -------
# Four EMT trunks from ED-B-PANEL, elevations project-frame absolute (they cross
# storeys). Each run travels its plan polyline flat at start_elevation and rises
# vertically at its last point to end_elevation; the takeoff bills the developed length.
CONDUIT_TRUNKS = [
    # Up the mechanical chase beside the radon vent to the PV junction box. Corrected
    # 2026-08-02 to (1'-6", 34'-6") — the old (3', 33') sat 4" south of W-M-MECH-S, out in
    # the open mudroom floor with no enclosure.
    # ** THE RISER STOPS AT THE ATTIC DECK SINCE 2026-08-29, AND CD-A-PV-EAST FINISHES IT. **
    # It used to run all the way to 25'-6" at x=1'-6". That worked under the old 4:12 roof off
    # 5'-0" knee walls, where the plane at x=1'-6" stood at 25'-6" exactly; at 6:12 off a
    # 20'-11 3/8" eave the plane there is 21'-8 3/8", so the last 3'-10" of this run was
    # simply outside the building. The chase does NOT move — moving it would drag the
    # mechanical-room penetration through every storey below, which is the same reason
    # VR-M-RADON-VENT jogs in the attic instead of relocating (mep_venting.py). A ConduitRun
    # travels flat at `start_elevation` and rises only at its LAST point, so "up, then over"
    # is two runs, not one polyline.
    ConduitRun(uid="CDT001AAAA", tag="CD-B-ATTIC-RISER", trade_size=inch(1.5),
               path=(pt(ft(2), ft(29)), pt(ft(1, 6), ft(34, 6))),
               start_elevation=ft(-4), end_elevation=ft(20, 6),
               from_ref="ED-B-PANEL", to_ref="ED-A-PV-JB"),
    # The over-and-up leg: east along the attic deck under the north rake, into the north
    # gable wall, and up it to ED-A-PV-JB at 25'-6". 6" above the deck for the flat part,
    # which is what CD-A-DATA-NE does on the same storey and for the same reason.
    #
    # ** THE LAST FOOT WAS OVER FO-A-HALL (fixed 2026-08-30). ** It ran straight east at
    # y=34'-6" to x=11'-0" and stood up there — and FS-ATTIC's deck void is x 10'-0"..18'-0",
    # so the last 12" of the flat leg AND the whole 5'-0" riser were in a 13'-deep open shaft
    # with no deck under either. This is the same defect CD-A-DATA-NE was rerouted for on
    # 2026-08-29, one bay west and missed at the time; `mep.run_over_void` is what found it.
    #
    # It turns north at x=9'-6", 6" clear of the void's west edge, and finishes inside the
    # gable wall. y=35'-10" is 4" into W-A-N2/W-A-N2B's 5 1/2" stud cavity (which runs
    # y 35'-6"..35'-11 1/2"), so the run straps to gable studs for its last 1'-6" and stands
    # up between them, directly behind the box. There is no third option: FS-ATTIC's void
    # stops at y=35'-5 3/8" and W-A-N2B's gwb face starts at y=35'-5 3/8" too, so between the
    # hole and the wall there is nothing at all. It is 1 1/2" EMT in a 5 1/2" stud — a 2"
    # bore, 36% of the depth, inside R502.8's 40% for a bored hole. **+1.33 LF.**
    #
    # ** THE RISER WAS 3" INSIDE WIN-A-N1 (fixed 2026-08-30). ** It follows ED-A-PV-JB west
    # to x=10'-2" and down to 25'-0"; the box's own note carries why that station. **-1'-0".**
    ConduitRun(uid="XJR4KE400J", tag="CD-A-PV-EAST", trade_size=inch(1.5),
               path=(pt(ft(1, 6), ft(34, 6)), pt(ft(9, 6), ft(34, 6)),
                     pt(ft(9, 6), ft(35, 10)), pt(ft(10, 2), ft(35, 10))),
               start_elevation=ft(20, 6), end_elevation=ft(25),
               from_ref="CD-B-ATTIC-RISER", to_ref="ED-A-PV-JB"),
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
    # crossings; pulled 1' south it punched the wall once. Since the 2026-08-21 thinning it
    # runs 4" clear of that wall instead of grazing its face — see CONDUIT_SLEEVES below,
    # where two sleeves went away because of it.
    ConduitRun(uid="CDT002AAAA", tag="CD-B-GARAGE", trade_size=inch(1.25),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(35)), pt(ft(16), ft(35)),
                     pt(ft(16), ft(41, 9.375))),
               start_elevation=ft(-4), end_elevation=ft(5, 10),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # Across the basement ceiling to the kitchen's east counter wall — still the east wall
    # after the 2026-07-30 range/sink swap, since KGF3 (the device this feeds) stayed the
    # east-wall device; its position along that wall moved twice since, with the cooking run
    # and then with the range/N3 flip.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(28, 11))),
               # -1'-6", not the -1'-0" it held until 2026-08-21: the basement ceiling
               # dropped when the 9" deck became the EPS deck with 5/8" gypsum under it, and
               # a raceway at -1'-0" was then lying *inside* the pour (mep.sleeve_coverage
               # caught it as an unsleeved crossing at 26'-6"). The 2026-08-23 seat rework
               # took the deck soffit down another 1 9/16" to -13 7/16" and its board to
               # -14 1/16", so the clear under it is 1 15/16" — still clear, and this is the
               # tightest raceway in the basement. Its two wall crossings go with it.
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
                     position=pt(inch(10), ft(31)), type_ref="ED-T-NET-ENCLOSURE",
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
    # ** BOTH RUNS CROSSED THE STAIRWELL, AND BOTH ARE OFF IT NOW (2026-08-30). **
    # They left the chase at y=34'-6" and went straight east at +9'-2". At that height they
    # are inside FS-S-WEST — the SECOND storey's floor, whose joists run 9'-0 1/8" to 10'-0"
    # — and FS-S-WEST's deck void is x 10'-3 3/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8".
    # KITCH spanned **7.27 ft** of that opening and PORCH **15.52 ft**, because PORCH's south
    # leg then ran down x=17'-6", which is 2 5/8" INSIDE the second floor's trimmer even
    # though it is exactly ON the main floor's — eight more feet of raceway over a two-storey
    # stairwell with nothing to strap it to. Both figures are measured by `mep.run_over_void`
    # (checks/mep/routing.py), which is the check this pair is the reason for; reading them
    # by eye against FS-M-STAIR's slightly narrower opening under-counts both. Nothing graded
    # it before: a ConduitRun carries no floor_ref, so it draws wherever it is authored, and
    # `duct_joist_bay` only fires on JOIST_BAY routing.
    #
    # KITCH goes NORTH instead, into the first joist bay inboard of the north wall at
    # y=35'-6" — 6" clear of the void's north edge, strapping to the rim and the joist ends
    # the whole way. x 2'-0"..19'-0" of that wall carries one opening, D-M-ENTRY, whose head
    # is at 6'-8"; at +9'-2" this run is above the plate line entirely, in the floor
    # structure, so no header is in its way. **+2 LF.** (19', 29') is unchanged: it still
    # sits east of the FO-M-STAIR well and between the kitchen, the stair and RM-M-STUDY —
    # one radio covering all three, which is what put it there rather than over the counter.
    ConduitRun(uid="CDT010AAAA", tag="CD-M-DATA-KITCH", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(2), ft(35, 6)), pt(ft(19), ft(35, 6)),
                     pt(ft(19), ft(29))),
               start_elevation=ft(9, 2), end_elevation=ft(9, 2),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-KITCH-AP"),
    # PORCH goes SOUTH first and turns east at y=1'-0", well below the void, then out under
    # the balcony deck to the porch soffit — still sharing SP-SG-PORCH-ELEC with the ceiling
    # fan's supply, one hole and two raceways, because the exit point at x=17'-6" never
    # moved — only the y at which the run reaches it did, from a line inside the stairwell to
    # one twenty-five feet south of it. **The reroute is free**: 15'-6" + 39'-4" east-then-south is the same 54'-10" of
    # plan run as 33'-6" + 15'-6" + 5'-10" south-then-east-then-south, so 55.33 LF developed
    # either way, at identical cost. The long x=2'-0" leg rides FS-S-WEST, which is open-web:
    # 3/4" EMT passes between the 8 7/8" chords without a hole in anything
    # (resolve/framing/profiles.py).
    ConduitRun(uid="CDT011AAAA", tag="CD-M-DATA-PORCH", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(2), ft(1)), pt(ft(17, 6), ft(1)),
                     pt(ft(17, 6), ft(-4.833))),
               start_elevation=ft(9, 2), end_elevation=ft(8, 8),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-PORCH-AP"),
]

ATTIC_DATA_TRUNKS = [
    # Into the north gable wall and east along it to the NE corner, then up to the access
    # point.
    #
    # ** THE 2026-08-29 DETOUR IS RETIRED (2026-08-30). ** That pass found the run spanning
    # 8'-0" of FO-A-HALL on the open deck and sent it 66 feet the long way round — south down
    # x=2'-0" to y=20'-8", east across the studio, and back north up the east loft. The
    # premise it rested on was "FO-A-HALL's north edge IS W-A-N2's inside gwb face, so the
    # strip between the void and the wall is wall, not deck." Both halves are true and the
    # conclusion does not follow: a conduit does not need DECK, it needs FRAMING TO STRAP TO,
    # and a stud cavity is framing. DU-ERV-EA has run that same band all along.
    #
    # So it turns north and finishes inside the gable. y=35'-7" is 1" into the 5 1/2" stud
    # cavity (y 35'-6"..35'-11 1/2" on W-A-N2 / W-A-N2B / W-A-N1, which is one continuous
    # line of studs across all three), so `mep.run_over_void` passes it on the wall
    # exemption rather than on a technicality — the studs are the support. Thermally it is
    # the right side too: CATLIN_EXT_2X6 puts air and vapour control on the exterior foam
    # with mineral wool inboard, so a raceway in the cavity is on the warm side of both.
    # **57.08 -> 29.58 LF, ratio 2.26 -> 1.19, four 90s down to three (270 deg of bend
    # against NEC's 360 deg limit per pull, where the old route was AT the limit).**
    #
    # It turns north at x=6'-0" rather than x=2'-0", and that is the whole reason DU-ERV-EA
    # does not have to move. The exhaust trunk climbs the 6:12 rake from +244" at x=1'-11"
    # to +258" at x=8'-0", so west of x=4'-4" its 6" envelope is at this conduit's own
    # +20'-6"; from x=6'-0" east it is 3 3/4" clear and climbing, and by x=10'-0" it is at
    # +276" and 2'-6" overhead. Entering the band four feet further east costs nothing —
    # 29.58 LF either way, because the leg lost on the deck is the leg gained in the wall —
    # and it leaves a 6" insulated duct strapped to the gable where it belongs instead of
    # hanging it 10" off the wall over the void. It also keeps 1 5/8" from CD-A-PV-EAST,
    # which shares this cavity at y=35'-10" for its last 1'-6".
    # ** REROUTED 2026-08-30 WITH THE AP IT FEEDS — OFF THE GABLE, DOWN THE POCKET. **
    # The gable route this replaced was itself a reroute, and it traded one defect for
    # another: it left the FO-A-HALL detour behind and then ran 21'-0" through the north
    # gable's stud cavity, climbing 20'-6" -> 24'-0", which put it inside WIN-A-N2's rough
    # opening (x 22'-9"..25'-3", sill +22'-0", head +25'-0") at +23'-3". Nothing caught it,
    # for the same reason nothing caught DU-ERV-EA in the same band: no check in the engine
    # grades a run against an opening.
    #
    # It now goes south instead of east. Out of the chase at (2'-0", 34'-6") on the attic
    # deck at +20'-6", straight down the RM-A-POCKET side of the wall line at x=2'-0" to
    # y=22'-6", then into W-A-STU-N's sole plate and up its 3 1/2" cavity to the AP at
    # +23'-0". **29.58 -> 20.0 LF, 3 elbows -> 1.**
    #
    # The x=2'-0" lane is clear of both FS-ATTIC deck voids (x 21'-2"..35'-5 3/8" / y 5'-9 5/8"
    # ..8'-9 5/8", and x 10'-0"..18'-0" / y 22'-6 3/8"..35'-5 3/8"), and it parallels
    # DU-A-ERV-R-ATTIC and -STUBATH, which take x=1'-0" at +20'-4" — 1'-0" of plan separation
    # and 2" of elevation. A 3/4" EMT in a 2x4 stud is a 1" bore, 29% of depth, inside R602.6
    # either way, and the cavity is mineral wool with no other service in it.
    ConduitRun(uid="CDT012AAAA", tag="CD-A-DATA-NE", trade_size=inch(0.75),
               service=Service.DATA,
               path=(pt(ft(2), ft(34, 6)), pt(ft(2), ft(22, 6)),
                     pt(ft(6, 6), ft(22, 6))),
               start_elevation=ft(20, 6), end_elevation=ft(23),
               from_ref="ED-B-NET-PATCH", to_ref="ED-A-STUDIO-AP"),
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

# --- The three hardwired drops (owner, 2026-08-22) ---------------------------------------
#
# The owner's brief: "run through joists and down; all come together at a switch and router
# in the mechanical room, powered by backup power." That IS the topology already here —
# ED-B-NET-PATCH stands in RM-B-FURNACE on CKT-HA, which is homed to ED-B-BACKUP-PANEL at
# BackupTier.ALWAYS_ON — so nothing new is needed at the head end. These are three more home
# runs off it.
#
# ** WHY NOT THE SPA CONDUIT. ** The brief said the workshop drop could "likely share the spa
# conduit", and the route is right — CD-B-SPA runs 1" EMT south down x=2'-0" at -4'-0", a
# foot clear of the workshop's west wall. The PIPE is not shareable: NEC 800.133(A)(1)(c) and
# 725.136 forbid communications and Class 2 circuits sharing a raceway with power conductors,
# and the model already encodes it — ``ConduitRun.service`` is one value, never a set. So
# CD-B-DATA-SHOP runs PARALLEL, 6" east of it, in its own pipe. The E-603 sheet's own note
# draws the same line: shared *penetrations* are permitted, shared raceways are not, which is
# the precedent CD-M-DATA-PORCH already sets by sharing SP-SG-PORCH-ELEC with a supply.
#
# No ``circuit=`` on any of the three: a passive jack names no circuit, which is the
# documented pattern (takeoff/data.py) and what keeps the PoE budget honest.
BASEMENT_DATA_DEVICES = [
    # At the workbenches on the west wall, between ED-B-WORKSHOP-RC1 (y=6') and RC2 (y=11'),
    # at the same 42" the receptacles use — 8" above a 34" bench top.
    ElectricalDevice(uid="C75K1P71SX", tag="ED-B-WORKSHOP-DATA1", kind=DeviceKind.DATA_OUTLET,
                     position=pt(inch(9), ft(8, 6)), type_ref="ED-T-DATA-JACK",
                     room="RM-B-WORKSHOP", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    # Behind the television on the media room's north wall, 1'-0" east of ED-B-PLAY-N-RC1 so
    # the two plates do not share a box location. Both sit inside the panel's 85.3" width
    # (x 23'-2" to 30'-3"), so neither is visible with the TV hung.
    ElectricalDevice(uid="N99QMTQDK6", tag="ED-B-PLAY-N-DATA1", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(27, 9), ft(35, 3)), type_ref="ED-T-DATA-JACK",
                     room="RM-B-PLAY-N", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(30))),
]

MAIN_DATA_DEVICES_STUDY = [
    # RM-M-STUDY's east wall is nearly all door, so the south wall is where anything goes —
    # beside ED-M-STUDY-RC1, the pairing a desk actually wants. 1'-0" west of it.
    #
    # 2026-08-29, the call-booth fit-out: the desk that pairing was always for now exists
    # (FURN-M-STUDY-DESK, 20" deep, top at 29 1/2"), so the jack came UP from 16" to 32" —
    # 2 1/2" over the top, in the last course of WP-M-STUDY-WAINSCOT, at hand height beside
    # the laptop. A plate cut into a wainscot is ordinary joinery. And y moved 1 5/8" north
    # with W-M-CLN2's face when that wall was retyped to INT_2X4_STAGGERED_DOUBLE_GWB: a
    # device position is a FACE position (top of this file), so a retype that moves a face
    # buries every device on it. 2026-08-30: y -5/8" (18'-5" -> 18'-4 3/8") south again with
    # the follow-up retype to the single-gwb INT_2X4_STAGGERED_GWB.
    ElectricalDevice(uid="V51Z24K1AA", tag="ED-M-STUDY-DATA1", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(16), ft(18, 4.375)), type_ref="ED-T-DATA-JACK",
                     room="RM-M-STUDY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(32))),
]

BASEMENT_DATA_TRUNKS = [
    # Workshop: south down x=2'-6" at -4'-0", six inches east of CD-B-SPA and parallel to it
    # the whole way, then west to the jack and down the wall to 42" over the slab. Stays
    # inside the basement box — no crossing, no sleeve.
    ConduitRun(uid="F2D3CT89ZV", tag="CD-B-DATA-SHOP", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(inch(10), ft(31)), pt(ft(2, 6), ft(31)), pt(ft(2, 6), ft(8, 6)),
                     pt(inch(9), ft(8, 6))),
               start_elevation=ft(-4), end_elevation=ft(-5, -10),
               from_ref="ED-B-NET-PATCH", to_ref="ED-B-WORKSHOP-DATA1"),
    # Media room: east along the basement ceiling at -1'-6", through the stair shaft's west
    # wall and the centre wall, then north to the jack behind the television. Held at y=30'
    # so its two sleeves stay a clear foot from CD-B-KITCHEN's at y=29' — the sleeve matcher
    # pairs a run to a hole by proximity, and two holes 6" apart in the same wall confuse it.
    ConduitRun(uid="D606MFGTEG", tag="CD-B-DATA-MEDIA", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(inch(10), ft(31)), pt(ft(2), ft(30)), pt(ft(27, 9), ft(30)),
                     pt(ft(27, 9), ft(35, 3))),
               start_elevation=ft(-1, -6), end_elevation=ft(-6, -10),
               from_ref="ED-B-NET-PATCH", to_ref="ED-B-PLAY-N-DATA1"),
    # Study: south and east strapped to the basement ceiling at -1'-0 1/2", then up the
    # study's south wall to the jack.
    #
    # ** IT RAN AT -4'-0" UNTIL 2026-08-30, AND THAT IS 5'-1 7/16" ABOVE THE BASEMENT SLAB. **
    # Not in a ceiling and not in a floor — in open room air at head height, for the whole
    # 27'-9" of its plan run: 21'-2" across RM-B-FURNACE, 6'-0" across RM-B-BATH a foot from
    # FX-B-BATH-WC, and its east leg at y=19'-0" passed 1'-0" in front of D-B-FURN's opening,
    # square across the width of the leaf at forehead height. The basement mechanical room
    # tolerates exposed conduit; a bathroom and a doorway do not.
    #
    # The comment this replaces described a route the model never had — "up the x=2'-0" riser
    # to the main floor structure, then east through the FS-M-WEST joist bays. Drilled bays."
    # A `ConduitRun` is flat at `start_elevation` and rises only at its LAST vertex
    # (model/mep.py), so there was no riser at x=2'-0" and nothing ever entered FS-M-WEST.
    # This is the largest comment-versus-model gap I found in the data cabling, and no check
    # could have caught it: `mep.run_over_void` grades deck voids, not room volume, and a
    # ConduitRun carries no `floor_ref` to grade against a floor in the first place.
    #
    # ** -1'-0 1/2" IS SWEPT, NOT PICKED. ** The basement ceiling is the busiest plane in the
    # house and the obvious answers are all occupied: CD-B-DATA-MEDIA's -1'-6" line puts this
    # run 3/8" INTO PR-B-SAUNA-VENT where that vent crosses (9'-0", 19'-0"), and -1'-4" puts
    # it 7/8" into PR-B-HW-TRUNK. Sweeping the whole -3'-4"..-0'-11" band against every other
    # run in the model, interpolating each neighbour's elevation at the actual crossing, the
    # only lane that is both clear AND above D-B-FURN's head is the one tight to the joists.
    #
    # -1'-0 1/2" puts the raceway's top at -1'-0 1/8", a quarter inch under FS-M-WEST's joist
    # bottoms at -0'-11 7/8" — strapped to the underside, which is what the trade does — with
    # 1 1/4" to PR-B-CW-TRUNK, the nearest service. It is 1'-4 15/16" over D-B-FURN's head.
    #
    # Nothing in the engine grades run against run: `mep.run_proximity` was scoped in the
    # 2026-08-30 plan and deliberately not built, because it surfaces a long tail across 111
    # runs. So this clearance was measured by hand and is written down here, because the next
    # person to move this line will not be told by anything.
    ConduitRun(uid="Z9TXYSYKWG", tag="CD-B-DATA-STUDY", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(inch(10), ft(31)), pt(ft(2), ft(31)), pt(ft(2), ft(19)),
                     pt(ft(16), ft(19)), pt(ft(16), ft(18, 5))),
               start_elevation=inch(-12.5), end_elevation=ft(2, 8),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-STUDY-DATA1"),
]

DATA_SLEEVES = [
    # CD-B-DATA-MEDIA's concrete crossing. `mep.sleeve_coverage` is a CODE-tier check and
    # an unsleeved crossing of a pour FAILs it.
    # SP-B-STR-CD-DATA (W-B-STR3, x=10', y=30') was here until 2026-08-24 and is gone for
    # the same reason the eighteen listed at mep_sleeves.py went on 2026-08-21: W-B-STR3
    # is 2x6 bearing studs now, not 12" of concrete, and a framed wall takes a bored hole
    # on the day rather than a sleeve set before a pour. The raceway still crosses the wall
    # at the same station; there is simply no pour to cast into.
    SleevePenetration(uid="V44DS76X6J", tag="SP-B-CN-CD-DATA", host_ref="W-B-CN",
                      position=pt(ft(18), ft(30)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.DATA,
                      axis="horizontal", center_elevation=ft(-1, -6)),
]

ATTIC_DATA_DEVICES = [
    # High on the north gable in RM-A-EAST-UNFIN. Mount elevation is storey-relative (attic
    # datum 20'), so 4' here is 24' absolute.
    #
    # ** MOVED x 33'-0" -> 27'-0" ON 2026-08-29. ** It was in the NE corner, "under the 4:12
    # rake, which at x=33' carries the roof to 26'". At 6:12 off a plate the north gable's
    # inside face at x=33' stands 1'-7 1/2" above the deck and a 4'-0" mount is three feet of
    # fresh air. The rule is `x_mount <= 2 x (head + 2")` read backwards: a 4'-0" device needs
    # 8'-8" of run from the eave, so anywhere in x 8'-8"..27'-4" holds it. 27'-0" is the
    # easternmost bay that does, which keeps the AP where its coverage was wanted — over the
    # east loft — rather than dragging it to the ridge. CD-A-DATA-NE's last two vertices
    # follow it.
    # ** MOVED OFF THE NORTH GABLE ONTO W-A-STU-N ON 2026-08-30, AND RETAGGED WITH IT. **
    # The gable station was chosen to cover RM-A-EAST-UNFIN, which is unfinished storage; the
    # two rooms in this attic that hold people are RM-A-STUDIO and RM-A-STUDY, and both are
    # west of the stair void. The radio now sits between them instead of over the boxes.
    #
    # The move also empties the gable band. CD-A-DATA-NE had to climb that band to reach
    # x=27'-0" and passed through WIN-A-N2's rough opening at +23'-3" doing it — the same
    # 2'-6" of glass DU-ERV-EA was crossing, in the same band, for the same reason. Both are
    # out of it now.
    #
    # x=6'-6" AT A 3'-0" MOUNT is set by the rake and was measured against
    # `integrity.element_above_roof`, not derived: the ROOF UNDERSIDE here is 20'-1 1/2" + x/2,
    # so a 4'-0" mount needs x >= 7'-9" — and x 7'-0"..9'-0" is D-A-POCKET's rough opening,
    # x 9'-4 3/4"..9'-10 1/4" W-A-STU-W's tee studs. **There is no 4'-0" station on this wall.**
    # 3'-0" at x=6'-6" leaves 4 1/2" under the rake and clears the door by 6". (Do not use the
    # wall-top formula at attic_studio.py:241 here — a `ToRoof` top is not the rake underside
    # and the two differ by about a foot.) y=22'-0 5/8" is 1" off the gwb face on the STUDIO
    # side, the station ED-A-POCKET-SW already uses.
    ElectricalDevice(uid="CND004AAAA", tag="ED-A-STUDIO-AP", kind=DeviceKind.DATA_OUTLET,
                     position=pt(ft(6, 6), ft(22, 0.625)), type_ref="ED-T-AP-CEILING",
                     room="RM-A-STUDIO", wall_ref="W-A-STU-N",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3))),
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
    # SP-B-N3-CD-GAR and SP-B-N2-CD-GAR were here until 2026-08-21 and are gone with the
    # 12" -> 8" thinning, which is the one place that change deleted work rather than
    # shrinking it. The east leg runs at y=35'-0", which was *exactly* the 12" wall's inside
    # face, so the resolver read the run as inside W-B-N3 (x 0'-10') and W-B-N2 (x 10'-18')
    # and the two grazing crossings needed sleeves. At 8" the inside face is 35'-4" and the
    # raceway is 4" clear of both walls: no crossing, no hole. Only the genuine north punch
    # at x=16' (SP-B-N2-CD-GAR2) and the stair wall at x=10' remain.
    # SP-B-STR-CD-GAR (W-B-STR, x=10', y=35') went on 2026-08-24 with the pour: that wall
    # is framed now, so its crossing is bored, not cast. Only the genuine north punch at
    # x=16' is still a hole in concrete.
    SleevePenetration(uid="CNS008AAAA", tag="SP-B-N2-CD-GAR2", host_ref="W-B-N2",
                      position=pt(ft(16), ft(35, 6)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # Through the ICF *stem*, not the footing under it. The run holds -4'-0" the whole way
    # (it is pinned to the basement it leaves, which did not move), and when grade dropped
    # 2'-6" on 2026-08-18 the garage foundation went down with the soil: FT-GF-S2 now bears
    # at -6'-8" and its top is -6'-0", two feet clear below this crossing, while W-GF-S2
    # spans -6'-0" to -0'-8" and is what the conduit actually passes through.
    #
    # ** 40'-10 7/8" -> 41'-2 1/8" ON 2026-08-31, AND ONTO THE CORE'S MIDDLE. **
    # `integrity.sleeve_in_opening` tests the centre against the STRUCTURE layer — the 6"
    # concrete core, not the 11" stem — and the core's south face is GARAGE_Y_SOUTH + 2 1/2"
    # of EPS. The old station sat 1/8" inside that face, so the 3/8" the garage moved north
    # with the corrugated cladding put it 1/4" OUTSIDE and the check failed, correctly. The
    # run crosses the whole stem, so the y here was always free; it is on the core's
    # mid-depth now — 3" of concrete either side — and no future move of the wall line at
    # this scale can reach it.
    SleevePenetration(uid="CNS009AAAA", tag="SP-GF-CD-GAR", host_ref="W-GF-S2",
                      position=pt(ft(16), ft(41, 2.125)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # The stub-up, 3 3/8" north of the stem's inside face. It stood at 41'-6" until
    # 2026-08-23 and that was 1/8" inside SL-G-FLOOR's south edge — passing only because
    # `integrity.sleeve_in_opening` tests the sleeve's CENTRE, with half the 2" bore hanging
    # over the slab edge. Moving the garage 1/2" north pushed the centre out too and it
    # failed, correctly. It is not back at the edge: 41'-9" leaves 2 3/8" of concrete around
    # the bore. The conduit runs up the inside face of W-G-S from here to ED-G-EV-1450.
    SleevePenetration(uid="CNS010AAAA", tag="SP-G-CD-GAR", host_ref="SL-G-FLOOR",
                      position=pt(ft(16), ft(41, 9.375)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240),
    # CD-B-KITCHEN: east across the basement ceiling at -1' and up through SL-M-DECK to the
    # kitchen's east counter wall. The wall and deck sleeves are 1/2" apart in plan but in
    # different hosts, which is what the matcher keys on.
    # SP-B-STR-CD-KITCH (W-B-STR3, x=10', y=29', -1'-6") also went on 2026-08-24 with the
    # pour. Its partner in W-B-CN stays: that wall is still concrete.
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
    # RC1/RC2 hang on the x=18' line's west face and moved 3 1/4" east on 2026-08-28, from
    # 17'-1 1/2" to 17'-4 3/4". The wall moved, not the design: W-B-CS went from 12" of
    # concrete with the liner on it to a 2x6 stud wall with the same liner, so its west face
    # went 17'-2 1/2" -> 17'-5 3/4" and these two were left floating 3.2" off it. They keep
    # the same 1" the whole NEC fill sets its bodies back from the face it hangs on.
    ElectricalDevice(uid="NEC001AAAA", tag="ED-B-GYM-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 4.75), ft(2, 7.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC002AAAA", tag="ED-B-GYM-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 4.75), ft(10, 6.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # ** RC3/RC4 CROSSED W-B-CE ON 2026-08-30, FROM y 18'-4.385" TO 17'-7.615". **
    # They were on the PLAY-ROOM side of the wall the whole time. W-B-CE is 6 3/4" of
    # staggered partition on the y = 18'-0" centreline, so its gym face is at 17'-8 5/8"
    # and its play face at 18'-3 3/8": bodies at 18'-4.385" stood 1" north of the play
    # face, in RM-B-PLAY-N, while counting toward RM-B-GYM's 210.52(A) spacing — because
    # `electrical.receptacle_spacing` accepts any device within `_NEAR_WALL_M` (0.5 m) of a
    # room's clear face, and neither carried a `room=` for anything to contradict.
    # 17'-7.615" is the gym face less the 1" body setback this file sets everywhere, and
    # `rotation=deg(180)` turns the plate south into the gym. `room=` is authored now so
    # the two rooms can never trade one box between them again.
    ElectricalDevice(uid="NEC003AAAA", tag="ED-B-GYM-RC3", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(20, 7), ft(17, 7.615)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-GYM", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC004AAAA", tag="ED-B-GYM-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(33, 3.5), ft(17, 7.615)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-GYM", rotation=deg(180),
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
                     position=pt(ft(28, 11.5), inch(9)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),

    # RM-B-WORKSHOP had ZERO receptacles until 2026-08-22 — `electrical.receptacle_spacing`
    # walks {BEDROOM, LIVING, KITCHEN, DINING, OFFICE} and a UTILITY room is outside it, so
    # nothing ever asked. These are the two over the new benches
    # (FURN-B-WORKSHOP-BENCH-N/S, plan/placeables.py), one apiece, at their centres.
    #
    # x = 9": the face convention at the top of this file — half the 2" body off the west
    # wall's 0'-8" finish plane — with `rotation=deg(90)` turning the plate along the wall.
    # Elevation 42" is the house's counter idiom, 8" above a 34" bench top.
    #
    # CKT-RC-BSMT, which is already `gfci=True, afci=True` (plan/circuits.py), so E3902.11's
    # unfinished-basement GFCI requirement is satisfied with no new circuit. That matters:
    # ED-B-PANEL has no spare 2-pole left, and a bench outlet is not worth a service change.
    ElectricalDevice(uid="17M93C11P3", tag="ED-B-WORKSHOP-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(9), ft(6)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-WORKSHOP", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="Z8RBX115XH", tag="ED-B-WORKSHOP-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(9), ft(11)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-WORKSHOP", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),

    # RM-B-PLAY-N had no receptacle of its own either, and a wall-hung 98" panel needs one
    # behind it. Directly under FURN-B-PLAY-TV at x=26'-9", on the north wall's 35'-4" face
    # (1" south of it — half the 2" body, the face convention above), plate turned south into
    # the room. Elevation 30" puts it behind the panel's lower edge rather than below it.
    #
    # ED-B-GYM-RC3/RC4 used to resolve inside THIS room while serving the gym's spacing;
    # they crossed to the gym face on 2026-08-30 (see the NEC fill above). This receptacle
    # was never a duplicate of them — it is on the north wall behind the television, 17'
    # away — which is why nothing here had to move with them.
    ElectricalDevice(uid="GQCPVT59F6", tag="ED-B-PLAY-N-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(26, 9), ft(35, 3)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-PLAY-N", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(30))),
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
    # x 30'-0 3/8" -> 29'-7" (2026-08-24). D-M-BALC moved 6" west to stand under D-S-DECK-E,
    # putting its east jamb at 23'-10", and 30'-0 3/8" was then 6'-2" from it
    # (electrical.receptacle_spacing). RC5 is the only receptacle covering BOTH ends of the
    # south run — that jamb and the far end near the SE corner, where RC4's coverage comes
    # round the east wall to meet it — and the two ends together pin it to a ~5" window,
    # about 29'-5"..29'-10". 29'-7" splits it: 5'-9" to the jamb, 5'-9 3/4" to the far
    # point. No stud line falls in that window (28'-8" and 30'-0" are the neighbours), so
    # unlike its neighbours this box is not 3/8" off a stud — it lands mid-bay, 3" east of
    # the 29'-4" bay centre. 29'-4" itself was tried and left the far point 6'-1" out.
    ElectricalDevice(uid="NEC012AAAA", tag="ED-M-LIVING-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 7), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # ED-M-LIVING-RC6 (uid NEC061AAAA) stood at (35'-4 3/8", 23'-8 3/8") on the east wall
    # at 16" and is DELETED 2026-08-24: FURN-M-KIT-PANTRY-S2, a 96" tall cabinet, now
    # occupies y 21'-2 3/8"..23'-2 3/8" and S1 23'-2 3/8"..25'-2 3/8", so that station is
    # behind a floor-to-ceiling carcass. A receptacle behind a fixed cabinet is not wall
    # space under 210.52(A) and is not reachable under any reading of it. The tombstone is
    # here rather than a silent removal because the uid is an IFC GlobalId that has shipped.
    # RM-M-PANTRY's reach-in outlet (2026-08-24). NEC 210.52(B)(1) puts a pantry receptacle
    # on a small-appliance branch circuit, so CKT-KITCH-SA1 and not CKT-RC-MAIN. NOT GFCI:
    # E3902 keys on room occupancy (STORAGE is not in the map) and on the 6' sink reach, and
    # FX-M-KITCH-SINK is 8'-1" away (2026-08-26: was 7'-4" before the sink moved +9" east).
    #
    # The NORTH wall at 48" — over the second shelf, which is what "reach-in height" means.
    # Not the south wall (3 1/2"/4 1/8" of jamb pack is all there is), not the west (KRF1
    # and KFZ1 already sit in that band on the far face of the same 2x6), not the east
    # (4 3/4" of 2x4 with the door pack in it).
    ElectricalDevice(uid="ZC14VSGCST", tag="ED-M-PANTRY-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(21, 3), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-KITCH-SA1", room="RM-M-PANTRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
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
    #
    # ** THIS OUTLET WAS DOING TWO JOBS AND ON 2026-08-29 IT BECAME TWO OUTLETS. **
    # Until then it sat at (5'-4 3/4", 22'-0 5/8") — physically INSIDE RM-M-BATH2, on
    # W-M-HS1's south face, close enough to FX-M-BATH2-SINK to be that room's vanity outlet,
    # while `electrical.receptacle_spacing` still counted it for RM-M-LIVING because the hall
    # band is part of that room and the box was within the wall's own thickness of its ring.
    # One device, one wall, two rooms' worth of duty.
    #
    # SL-M-TUBDK's deck box ended that: at x=5'-4 3/4" the box now stands sealed behind the
    # bath, between the plywood and the mineral wool, on a face that no longer faces a room.
    # It could go west to the piece of W-M-HS1 still open in the bathroom, or east to the
    # hall — and only the second keeps RM-M-LIVING's 6' rule, which FAILed the moment it
    # went west. It cannot do both any more, so it does one and ED-M-BATH2-RC1 below does
    # the other.
    #
    # This one takes the hall. x=6'-10" is on W-M-HS2 (6'-0"..8'-0"), whose NORTH face is
    # hall — W-M-HS1's north face is inside RM-M-BATH1 at the old x, which is what drove the
    # 2026-07-28 flip to the south face in the first place. y=22'-8 3/8" is that face after
    # its retype. It clears ED-M-HALL-SW's plate (x 6'-3 3/8"..6'-5 3/8") by 2 5/8".
    ElectricalDevice(uid="NEC066AAAA", tag="ED-M-LIVING-RC8", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(6, 10), ft(22, 8.385)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # RM-M-BATH2's vanity outlet, and the room's only usable one. ** IT MOVED TO THE VANITY
    # ON 2026-08-29, OFF W-M-HS1's SOUTH FACE BY THE WATER CLOSET, AND THE REASON IS A CODE
    # RULE THIS ENGINE DOES NOT ENCODE. ** NEC 210.52(D) / IRC E3901.6 want a receptacle
    # within 36" of the outside edge of EACH BASIN. At its old station (1'-1", 21'-11 5/8")
    # it stood 58" from the basin of the new 54" vanity — it was described as the vanity
    # outlet and had stopped being one. It is now on W-M-W3's finish face beside the bowl:
    # x=7 5/8" is the face at 6 5/8" plus the device's own 1" half-depth, y=15'-3" is 5 3/8"
    # south of the basin's south edge. rotation 90 turns the 4" box to run along the wall,
    # matching ED-M-BATH2-MIRROR directly above it.
    #
    # ** 44" PUTS IT 8" ABOVE THE 36" COUNTER **, which is where a backsplash outlet goes;
    # the old 16" was a baseboard height and would now be behind a cabinet. ** THE ENGINE
    # HAS NO E3901 RULE AT ALL ** (see CKT-BATH-ATTIC in plan/circuits.py), so nothing
    # reported this and nothing will report the next one — two other lavatories in this
    # house are outside the 36" today, and both are written up in plans/TODO.md rather than
    # moved here, because they are not this room.
    #
    # ** ED-M-BATH2-TUB-RC IS NOT AN ANSWER TO 210.52(D) AND MUST NEVER BE READ AS ONE. **
    # It measures 32" from this basin's east edge, so a naive check would call the rule
    # satisfied — but it is sealed inside SL-M-TUBDK's deck box behind FURN-M-BATH2-TUBDK-AP,
    # serving the bath's Bask heater, and nobody plugs a razor into it.
    #
    # GFCI at the DEVICE, not the breaker, which is the exception this house makes in exactly
    # this location: CKT-RC-MAIN spans the whole storey, and this is a bathroom outlet under
    # E3902.1 outright. The same reasoning as the other seven storey-circuit GFCI devices in
    # the note above — one splashed bathroom outlet must not take the floor down with it.
    # Contrast ED-M-BATH2-TUB-RC, which is breaker-protected because it is sealed inside the
    # deck box and could never be reset.
    ElectricalDevice(uid="N7TTYA9RV6", tag="ED-M-BATH2-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(7.635), ft(15, 3)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN", room="RM-M-BATH2", rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44))),
    # ** RM-M-BATH1 HAD NO RECEPTACLE AT ALL UNTIL 2026-08-30. ** Not one too far away --
    # none. NEC 210.52(D) requires at least one within 36" of the sink's outside edge, and
    # (D)(2) requires it on a wall or partition ADJACENT to the sink, on the countertop, or
    # on the cabinet itself. An outlet in the next room does not satisfy it however close it
    # measures, which is why the two entries in plans/TODO.md that quoted 42.9" and 37.2" to
    # receptacles in RM-S-SUITE were understating the problem rather than describing it.
    #
    # W-M-BAE, in the 8 5/8" of wall between the room's north-east corner (y=22'-7 3/8") and
    # D-M-BATH1's opening (y 23'-4"..25'-4"). That strip is the only piece of wall in this
    # 62" x 44" room that is not the water closet, the vanity, the mirror over it or the
    # door: 1 1/8" east of the cabinet's end and about 4" from the basin's nearest edge.
    # 44" AFF is the house's vanity-outlet height and is well inside (D)(2)'s "not more than
    # 12 in. below the countertop" (the counter is 36").
    #
    # GFCI at the DEVICE on the storey circuit, which is this house's settled treatment for
    # a bathroom outlet -- see ED-M-BATH2-RC1 above for why the breaker is the wrong place.
    ElectricalDevice(uid="4KMFZPRJPX", tag="ED-M-BATH1-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(67.625), inch(275.75)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN", room="RM-M-BATH1", rotation=deg(-90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(44))),
    # y flipped to W-M-STOS's north face (2026-07-28) when W-M-BAE's shift pushed the south
    # face into RM-M-BATH1. Inside RM-M-MUD-CLOSET since 2026-08-02, kept on purpose: NEC
    # 410.16 restricts closet luminaires, not receptacles, and RM-M-MUDROOM is
    # Occupancy.STORAGE so `electrical.receptacle_spacing` never walks it anyway. Stays GFCI
    # for its unmoved E3902.10 sink-reach location (RM-M-BATH1's lav, through W-M-STOS).
    ElectricalDevice(uid="NEC067AAAA", tag="ED-M-LIVING-RC9", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(4, 6.625), ft(26, 9.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # ** GFCI SINCE 2026-08-30, FOR EXACTLY THE REASON RC9 ABOVE ALREADY IS. ** RM-M-BATH1's
    # lavatory became a 24" vanity that day and its cabinet reaches 4'-9" further east than
    # the 18" bowl did, so this receptacle fell inside E3902.10's 6'-0" sink reach — 4'-7"
    # to the cabinet's nearest corner, measured through D-M-BATH1's open doorway rather than
    # through a wall. `code.E3902_gfci_locations` FAILed it and is correct.
    #
    # A note for whoever reads that finding next: the check measures from the fixture's
    # CENTROID (it reported 5.8'), but NEC 210.8 and E3902.10 both measure from the sink's
    # OUTSIDE EDGE, which here is 4.6'. The check understates every distance by half a
    # fixture, so it under-reports rather than over-reports — this one is real either way.
    ElectricalDevice(uid="NEC068AAAA", tag="ED-M-LIVING-RC10", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(m(1.9388), m(7.91434)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), room="RM-M-LIVING", rotation=deg(0)),
    # ED-M-LIVING-RC11 stood on the 10 3/16" pier at W-M-STRS's east end. That wall was
    # removed with D-M-STAIR (2026-08-24, main.py WALLS) and the receptacle went with its
    # host — there is no wall on that face any more to mount it to.
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
    # south/north walls (east wall nearly all door), 5'-2"/5'-10" from FX-M-LAUNDRY-SINK —
    # inside E3902.10's 6', so both are GFCI at the device.
    #
    # 2026-08-29, the call-booth fit-out: +1 5/8" north (W-M-CLN2 retyped to
    # INT_2X4_STAGGERED_DOUBLE_GWB, and a device position is a face position), and up from
    # 16" to 32" — 2 1/2" over FURN-M-STUDY-DESK's top, still well under NEC 210.52(A)'s
    # 5'-6". Paired with ED-M-STUDY-DATA1 at the same height 1'-0" west. 2026-08-30: y -5/8"
    # (18'-5" -> 18'-4 3/8") south again, same follow-up retype to INT_2X4_STAGGERED_GWB.
    #
    # ** ED-M-STUDY-RC2 WAS DELETED HERE AND CAME BACK THE SAME DAY. READ WHY. ** It sat at
    # 16" on the west wall. The first booth layout ran FURN-M-STUDY-BENCH down that whole
    # wall, and `_fixed_cabinet_intervals` breaks a counterless fixed cabinet OUT of the
    # receptacle ring — so the west wall stopped being wall space, the RC1 -> RC3 span
    # walked 11.46' against 12', and the outlet was redundant. Then the owner turned the
    # booth 90 degrees, the bench went to the north wall, and the west wall became 3'-8" of
    # bare wall again: `electrical.receptacle_spacing` FAILed at (13.4', 20.7') within one
    # build. It is restored below, on its original uid so the IFC GlobalId survives the
    # round trip, at the desk's height rather than its old 16".
    #
    # ** THE MARGIN ON THE RC1 -> RC3 SPAN IS STILL ONLY 6 1/2", ** and this outlet does not
    # widen it — it covers a different wall space. Anything that lengthens this room's ring
    # or pushes RC1 and RC3 apart flips that to a FAIL. Re-read the finding, do not assume.
    #
    # ** AND THE THING THIS PAIR TEACHES: a fixed built-in is load-bearing on an ELECTRICAL
    # check. ** Moving furniture in this house can delete or create a code finding with no
    # device touched at all. `haus check` after a placeable move, every time.
    ElectricalDevice(uid="NEC019AAAA", tag="ED-M-STUDY-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(17), ft(18, 4.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(32))),
    # Fills the >6' gap electrical.receptacle_spacing flags on the centre bearing wall,
    # on the STUDY face opposite ED-M-LIVING-RC7.
    # Restored 2026-08-29 (see above). x = 13'-8 1/2" is W-M-LS's resolved study face at
    # 13'-8" plus half this type's 1" depth; y = 19'-4" centres it on FURN-M-STUDY-DESK,
    # whose top is 29 1/2" — so 32" puts the box 2 1/2" clear of the desk exactly as
    # ED-M-STUDY-RC1 does, and the two outlets a seated person reaches are at one height on
    # two walls. It is 4'-0" south of REG-M-SUP4's riser bay (y=20'-8"), so the box and the
    # 3" duct in that cavity never meet. 2026-08-30: x -5/8" with the follow-up retype of
    # W-M-LS to the single-gwb INT_2X4_STAGGERED_GWB — the study face gave back 5/8".
    ElectricalDevice(uid="NEC020AAAA", tag="ED-M-STUDY-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(164.375), ft(19, 4)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(32)), rotation=deg(90)),
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
    # opening (x 11'-2"..16'-2"). 17'-0" centred the 1'-10" of wall left, under the 2'-0"
    # 210.52(A)(2) counts as wall space — kept anyway since the south wall is where the
    # plant gear plugs in.
    #
    # 17.0' -> 11'-4" (2026-08-24): D-S-DECK-W slid 1'-0" inward, so its rough opening is
    # x 12'-2"..17'-2" and the east remnant is 2" of wall. RC1 crosses to the *west* jamb
    # instead, on the 11'-4" bay centre — and that is also what closes the wall space west
    # of the door, which the inward move had stretched to 6'-3 3/4" from RC2 alone
    # (electrical.receptacle_spacing). FX-S-BALC-HYD gave up this bay for it and moved to
    # 7'-4" (plan/fixtures.py).
    ElectricalDevice(uid="NEC021AAAA", tag="ED-S-PLANT-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(11, 4), ft(0, 8.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC022AAAA", tag="ED-S-PLANT-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(5, 10.25), ft(0, 8.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC023AAAA", tag="ED-S-PLANT-RC3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(0, 8.75), ft(3, 6.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
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
    # RM-S-BED1's west wall, SOUTH of D-S-BED1 (2026-08-30). Moving that door 6" north onto
    # its stud line stretched the run from the room's SW corner to the door's south jamb past
    # NEC 210.52(A)(1)'s 6 ft — `electrical.receptacle_spacing` reported the gap at (22'-0",
    # 14'-5") the moment the door moved. y=11'-0" is 2'-0" from the corner and 3'-5" from the
    # jamb, so both halves of the run are covered, and it is station 24" on W-S-BW1's grid:
    # a bay centre, clear of the module studs at 16" and 32" and of the corner pack.
    # x is the east gypsum face plus 1", the same offset ED-S-BED2-RC5 uses on this wall —
    # the box is 2" deep and its back goes on the face.
    ElectricalDevice(uid="1M621JFX16", tag="ED-S-BED1-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 2.375), ft(11)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
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
    # RM-S-BED2's west wall, NORTH of D-S-BED2 (2026-08-24). The door's rough opening runs
    # y 21'-9 1/16" .. 24'-3 1/16" and breaks the wall line there; the space that reopens at
    # the north jamb ran 6'-2 5/8" round the NW corner to ED-S-BED2-RC1 before reaching a
    # receptacle, which is the 210.52(A)(1) 6' rule by 2 5/8" — the one FAIL the house
    # carried. x=22'-1 3/8" is W-S-BW2's east gypsum face — unchanged by the 2026-08-30
    # INT_2X4_RC retype, which added 1/2" of resilient channel to the HALL side only and
    # re-datumed the wall on its studs, so this face is still 2 3/8" east of the 21'-11" axis
    # (the wall is 5 1/4" now, not 4 1/2", and it is no longer symmetric about that axis);
    # y=25'-6" leaves 1'-2 15/16" of wall to the RO and 1'-2" to the corner, so the box lands
    # in a stud bay and not in a corner pack. x is the face PLUS 1" — the box is 2" deep and
    # its back goes on the face, which is the same offset ED-S-BED2-RC2 uses on the east
    # wall (test_wall_mounted_devices_resolve_against_a_wall_face grades the resolved body,
    # and authoring the face itself buries half the box in the gypsum).
    ElectricalDevice(uid="QBXTAARME9", tag="ED-S-BED2-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 2.375), ft(25, 6)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
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
    # y follows W-S-SN1's south face, which moved 1 5/8" into the room on 2026-08-21 when
    # the suite's north wall went from the 4 3/4" INT_2X4_PARTITION to the 8" staggered
    # sound wall. Authored y was 22'-0 5/8" against the old face.
    ElectricalDevice(uid="NEC045AAAA", tag="ED-S-SUITE-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(1, 0.75), ft(21, 11)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC046AAAA", tag="ED-S-SUITE-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 3.125), ft(20, 6.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # RC8 (2026-08-30): W-S-SN3's retype to INT_2X6_STAGGERED_PLUMBING (plan/storeys/
    # second.py — the suite bath's lav and WC actually back onto it) moved this room's
    # boundary enough to open a >6' gap on the L-arm's south wall, W-S-SBS. None of RC1-RC7
    # reaches it — RC1 is 4'-3" east on the same wall but stops short of the corner where the
    # GFCI since 2026-08-30. It was authored plain, on the reading that this stretch is not
    # within 6' of a sink — which was what `code.E3902_gfci_locations` said at the time,
    # because that rule measured to a fixture's insertion CENTROID. Measured to the suite
    # bath vanity's actual edge, as E3902.10 asks, the box is 4'-4" from it, not clear of
    # the circle at all.
    #
    # y is 15'-7 5/8", not the 15'-6 5/8" first authored: W-S-SBS went the OTHER way in the
    # same pass (INT_2X6_STAGGERED_PLUMBING -> INT_2X4_PARTITION, its wet-wall duty having
    # moved to SN3), so its south face pulled back 1.000" and this box — and RC1 beside it —
    # had to follow or hang in the room.
    ElectricalDevice(uid="N0F72WZE2H", tag="ED-S-SUITE-RC8",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(11), ft(15, 7.625)),
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
# Same treatment for the attic's lofts. RM-A-EAST-UNFIN and RM-A-POCKET are STORAGE,
# outside `_HABITABLE`, so 210.52 spacing is not evaluated for them. (RM-A-DEN stood in
# this sentence until 2026-08-27; it was STORAGE too, and it became part of the west loft.)
#
# ** THE WEST LOFT LEFT THAT SENTENCE ON 2026-08-29. ** RM-A-STUDIO is a habitable bedroom
# now and takes full 210.52 spacing; only the pocket it was split from stayed STORAGE. The
# room was already most of the way there — the east loft's ring and the study's devices
# cover its long walls — and `electrical.receptacle_spacing` named the two gaps that were
# left, both of them around the inside corner the new bathroom cut out of it at (9.9',
# 17.7'). The three devices at the end of this list are those two gaps and the bath.
ATTIC_ELEMENTS = [*PV_JBOX, *PV_JBOX_CLAMP, *ATTIC_DATA_DEVICES, *ATTIC_DATA_TRUNKS]
BASEMENT_ELEMENTS = [*BACKUP_ENCLOSURE, *ESS_EQUIPMENT, *BASEMENT_DEVICES,
                     *BASEMENT_EQUIPMENT, *CONDUIT_TRUNKS, *DATA_HEAD_END, *DATA_TRUNKS,
                     *BASEMENT_DATA_DEVICES, *BASEMENT_DATA_TRUNKS, *DATA_SLEEVES,
                     *NEC_FILL_BASEMENT]
MAIN_ELEMENTS = [*SERVICE_DEVICES, *MAIN_DEVICES, *MAIN_EQUIPMENT, *MAIN_DATA_DEVICES,
                 *MAIN_DATA_DEVICES_STUDY,
                 *MAIN_DATA_TRUNKS, *CONDUIT_SLEEVES, *NEC_FILL_MAIN]
GARAGE_ELEMENTS = [*GARAGE_DEVICES, *GARAGE_EQUIPMENT]
SECOND_ELEMENTS = [*SECOND_DEVICES, *SECOND_EQUIPMENT, *NEC_FILL_SECOND]
