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
#             REG-M-XFER-MUD, a passive louver in W-M-STRW.
# EQ-B-ERV moves *ventilation* air only — its "supply" is fresh air, not heat.
#
# Condensate: each head/AH drains via a collected air-gap line to the mech-room sink —
# planned plumbing, no geometry yet.
#
# Instances only, explicit constructors (UI drags round-trip). Circuit assignments live in
# plan/circuits.py; `circuit=` strings here are the join keys. Uids avoid I/L/O/U
# (Crockford base32, model/ids.py).
#
# A device position is a *face* position: the point sits half the device's
# depth off the finish plane (back on the plane, plate proud of it), `rotation` turns the
# plate along the wall. Nothing in the resolver pulls a device onto its wall, so a box
# authored on the wall axis buries in the studs and one authored a few feet in floats in
# mid-air. Enforced by
# `test_catlin_contract_m3.py::test_wall_mounted_devices_resolve_against_a_wall_face`,
# except ED-M-LIVING-KGF4 (mounts on the island, not a Wall) and ED-M-PORCH-FLOOD (a
# pillar). CATLIN_EXT_2X6's inside face is 6 5/8" in from the sheathing datum, cladding
# face 6 1/2" outboard of that.
#
# Positions worth knowing (project-north frame, house sheathing SW corner at 0,0):
# - Meter: exterior face of west wall (W-M-W1), outside ED-B-PANEL at (2', 29') in the
#   basement — shortest run from the underground POWER entry at (0', 18').
# - Garage south wall W-G-S at y=40'-6 7/8", service door at x=5'-8'; both EV receptacles east
#   of it, clear of the door swing.
# - Sunken-garden porch: west wall W-SG-W1 axis x=8', inner face x=8.5', north end
#   y=-0.833'. Hot tub disconnect 7' south of that, under the deck — basement storey, so
#   Mount elevation 5' is -4' absolute.
# - PV junction box on the north gable (W-A-N2B) beside the radon riser
#   clamp cluster; at x=11' the 6:12 rake carries siding to 26'-5 3/8", so 25'-6" absolute
#   has cladding to grip.

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
    # `service_amps` is the service size as data: it's what 220.82 demand is compared
    # against. Distinct from the panel's `bus_amps` — the 225A bus behind this 200A meter is
    # what NEC 705.12 measures a backfeed against.
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
    # The ERV is EQ-T-BROAN-B210E75RT in plan/mep_erv.py — an ERV with a modeled intake and
    # discharge, on `Service.OUTDOOR_AIR`/`EXHAUST_AIR`.
    # --- The three Gree heat-pump systems (plans/TODO.md §HVAC) ----------------------
    # Every unit below carries a real Gree model number and real submittal geometry; no
    # `TODO verify datasheet` remains in this file.
    #
    # `heating_capacity_at_design_btuh` is the number `mep.heating_capacity` sizes each zone
    # against, and it is a READ VALUE on all three systems, not an interpolation — the engine
    # does no curve interpolation itself, so whatever is authored here IS the machine as far
    # as every check is concerned. System 1 reads Gree's Extended Ratings at -15F (21,000).
    # System 2 reads them too (23,687). System 3 reads AHRI/NEEP's -22F figure (7,400)
    # unadjusted, because Gree's own -22F column for it is not physically plausible — see
    # EQ-T-GREE-SAPPHIRE-9-OD, which says so in full.
    #
    # Indoor heads still carry NO heating rating, by design: a multi's heads share one
    # compressor, and three head ratings summed would size a zone against capacity that
    # compressor cannot deliver simultaneously.
    #
    # System 1 — the concealed ducted air handler in RM-S-STUDY2's ceiling bulkhead
    # (SF-S-HP1) feeding the hallway trunk to the bedrooms plus the south branch and two
    # attic boots; FLEXX Ultra R32 outdoor unit. One 24k system covers the whole upstairs.
    #
    # ** IT REPLACED EQ-T-GREE-DUC24 / EQ-T-GREE-VIREO-GEN3, AND THAT PAIRING WAS SHORT. **
    # The DUC24/VIR24 record was wrong in three ways at once, all of them found by checking
    # it back against Gree's own submittals and Extended Ratings rather than against itself:
    #
    #  * AIRFLOW. `source=` claimed 577-1030 cfm. The real ceiling for the DUC24/VIR24 pair
    #    is 736 cfm at 0.8 in. w.c. — under the 750 cfm this duct system is sized to.
    #  * CAPACITY AT DESIGN. 13,500 Btu/h was a linear interpolation between two chart
    #    points; the read value at -15 F is 14,606. Either way the zone's 15,164 Btu/h block
    #    load was ABOVE it: 89% of load, and `mep.heating_capacity` only passed because
    #    EQ-S-HP1-STRIP's 6,800 Btu/h was being credited to the zone.
    #  * AUX HEAT. The DUC24 HAS NO AUX-HEAT TERMINAL. The strip heater the shortfall was
    #    covered with could not be interlocked with the heat pump at all, so the credit the
    #    check was granting described a machine that cannot be built.
    #
    # The FLEXX Ultra answers all three — 760 cfm at 1.0 in. w.c., 21,000 Btu/h read at
    # -15 F (138% of the load, unaided), 24 VAC control with a factory heat kit — and is
    # ENERGY STAR Cold Climate certified where the Vireo is not. HSPF2 goes 9.0 -> 10.0.
    #
    # WHY THIS UNIT AND NOT A SHALLOWER ONE. Connection geometry decides where a machine can
    # live: every concealed slim duct — Gree, LG, Samsung — puts supply on one long face and
    # return on the opposite long face, so air crosses the short depth and the long dimension
    # sits ACROSS the duct axis. The FLEXX Ultra keeps that geometry; what it costs is depth,
    # 18 1/8 in against the DUC24's 11 13/16, which is what drives SF-S-HP1 from a 17 in drop
    # to 21 in (storeys/second.py). It buys back nearly an inch of the box's GRADED axis in
    # exchange — 43 1/2 in wide against 44 1/2 — because `soffit_clear_section` measures every
    # occupant across the box's shorter plan dimension, and depth is not that dimension.
    #
    # A 36k FLEXX Ultra was REJECTED: its cabinet's smallest dimension is 21 1/4 in, needing a
    # 24 in drop, landing the soffit's underside exactly on IRC R305.1's 7'-0" floor, with
    # 3.5x cooling oversizing against a 10,145 Btu/h load and 1,000 cfm into 750-cfm ducts.
    # There is no 30k in the line (24 / 36 / 48 / 60 only).
    #
    # LG's KNUJB241A/LHN248HV1 remains the one real loss on FIT — 9 21/32 in tall would have
    # sat in the original 14 in drop — but its published heating range FLOOR is -13 F, two
    # degrees short of this site's design temperature. Worth revisiting only if LG publishes
    # a lower floor.
    EquipmentType(tag="EQ-T-GREE-FLEXX-ULTRA-24-AH",
                  name="Gree FLEXX Ultra R32 concealed ducted air handler, 24k",
                  footprint=(inch(43.5), inch(21.25)), height=inch(18.125),
                  cooling_capacity_btuh=24000,
                  source="Gree FLEXX Ultra R32 air handler FXU24HP230V1R32AH, matched to EQ-T-GREE-FLEXX-ULTRA-24-OD. Cabinet 18 1/8 x 21 1/4 x 43 1/2 in (W x D x H as shipped), net weight 135.6 lb, laid horizontally for ceiling mount with the 18 1/8 in face vertical — the orientation that minimises soffit depth, so `height` is 18 1/8 in and the 43 1/2 in dimension is the plan long axis. Airflow to 760 cfm against an external static pressure of 1.0 in. w.c., which is what lets it drive the 750 cfm this duct system is sized to with margin; the DUC24 it replaced claimed 1030 cfm in prose and really topped out at 736 at 0.8 in. w.c. HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate (AHRI 215213329). 24 VAC thermostat terminals and a factory electric heat kit (4.6 / 5.5 / 9.2 kW) — the DUC24 had NEITHER, so EQ-S-HP1-STRIP could not physically be interlocked with the heat pump at all, which is the defect this retype closes. The indoor unit carries no heating rating of its own on purpose: the outdoor unit is what has to make heat at design temp, and mep.heating_capacity sizes the zone against the outdoor type.",
                  # Real face positions, on the same convention EQ-T-GREE-DUC24 established:
                  # the long dimension is x, so supply and return are on the two 43 1/2 x
                  # 18 1/8 faces — supply out the north face (+y), return in the south face
                  # (-y), both on the cabinet's own centre height. Power enters at the
                  # north-east corner where the whip lands.
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(inch(21.75), inch(10.625), inch(18.125))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), inch(10.625), inch(9.0625))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), inch(-10.625), inch(9.0625))))),
    EquipmentType(tag="EQ-T-GREE-FLEXX-ULTRA-24-OD",
                  name="Gree FLEXX Ultra R32 outdoor unit, 24k (-22F, cold climate)",
                  footprint=(inch(39), inch(14.5625)), height=inch(37.8125),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=24000,
                  heating_capacity_at_design_btuh=21000,
                  cooling_capacity_btuh=24000,
                  min_operating_temp_f=-22.0,
                  source="Gree FXU24HP230V1R32AO (FLEXX Ultra, R32). 39 x 37 13/16 x 14 9/16 in overall (W x H x D), foot pattern 29 3/4 in across the width by 15 9/16 in across the depth, net weight 187.4 lb. Electrical MCA 21 A / MOCP 25 A at 208-230 V, single phase. LOW-TEMPERATURE HEATING, read from Gree's FLEXX Ultra Extended Ratings at 70 F return — not interpolated, unlike the VIR24 record this replaced: -22 F 18,000 Btu/h at COP 1.49; -20 F 19,500 at 1.53; -15 F 21,000 at 1.57; and a flat 24,000 Btu/h from -5 F all the way to 47 F. NOTE that this document's COP column is TRUE COP (W/W), unlike the All-Match Extended Ratings whose column is Btu/h per watt. HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate certified (AHRI 215213329). min_operating_temp_f -22 F per the operating envelope. heating_capacity_at_design_btuh is the -15 F read value, so the unit covers its whole operating range unaided: at -22 F it still makes 18,000 Btu/h against a ~16,400 Btu/h load, which is what demotes EQ-S-HP1-STRIP from a design-condition necessity to true sub-lockout backup.",
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
                  heating_capacity_at_design_btuh=23687,
                  cooling_capacity_btuh=28400,
                  min_operating_temp_f=-22.0,
                  source="Gree MUL30HP230V1R32AO. OUTLINE AND FEET, from the Gree Multi R32 Installation & Service Manual S3 outline diagram p.31 (the 30k has its own sheet; the 18/24k share a smaller one): 40 5/32 x 32 33/64 x 16 13/16 in overall, foot holes 25 in apart across the width and 15 19/32 in across the depth, net weight 145.5 lb. The record read 37 x 16 in until 2026-08-28 — 37 1/8 in is the width of the cabinet TOP, which is narrower than its base, and the 3 in of missing width put the unit within an inch of the balcony rim. RATINGS, from the 30 MBH submittal (AHRI 215218915 non-ducted): SEER2 21, EER2 13.6, HSPF2 10.0, MCA 23 A / MOCP 30 A, heating range -22 F to 75 F. Datasheet chart: 30,000 Btu/h at 47F, 27,000 Btu/h at 5F, ~24,500 Btu/h at -13F, ~21,500 Btu/h at -22F. ** -15F AT-DESIGN IS A READ VALUE SINCE 2026-08-31, NOT AN INTERPOLATION: 23,687 Btu/h from the Extended Ratings, replacing a 23,500 that was linearly interpolated between the -13F and -22F chart points. ** Cooling 28,400 Btu/h per datasheet. ** THE HARDWARE IS NOT CHANGING, and that was researched rather than assumed: no Gree single-zone below -22 F exists at 9-12k at any size, and the only real -31 F multi is R-410A — MULTIU36 makes 25,910 Btu/h at -22 F on 5.57 kW where this unit makes 22,600 on 3.70 kW, i.e. 50% more power for 15% more heat, while giving up HSPF2 10.0 -> 8.6 and SEER2 21 -> 16. This system already runs to -22 F, below the -20 F hard floor. **",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # No heating rating by design: three head ratings summed would size a zone against
    # capacity the shared compressor can't deliver simultaneously. Cooling capacity is kept
    # since it's what distinguishes the 9k from the 12k on a schedule.
    EquipmentType(tag="EQ-T-GREE-HEAD-9", name="Gree Multi R32 wall-mount head, 9k",
                  footprint=(inch(32.875), inch(7.875)), height=inch(10.828125),
                  cooling_capacity_btuh=9000,
                  source="Gree GWH09ATCXB-D6DNA3C/I, the Multi R32 9k wall-mounted indoor unit, from Gree's 'Wall Mounted Indoor Unit 09KBTU R32' submittal: 32 56/64 x 10 53/64 x 7 56/64 in (W x H x D), net weight 19.8 lb. The 9k and the 12k share ONE cabinet — see EQ-T-GREE-HEAD-12 — so nothing on a wall elevation distinguishes them and the cooling rating is what does. This replaced a REPRESENTATIVE PLACEHOLDER (32 x 8 x 12, 'TODO verify datasheet') on 2026-08-31. No heating rating BY DESIGN: three head ratings summed would size a zone against capacity the shared MUL30 compressor cannot deliver simultaneously.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-HEAD-12", name="Gree Multi R32 wall-mount head, 12k",
                  footprint=(inch(32.875), inch(7.875)), height=inch(10.828125),
                  cooling_capacity_btuh=12000,
                  source="Gree GWH12ATCXB-D6DNA3A/I, the Multi R32 12k wall-mounted indoor unit, from Gree's 'Wall Mounted Indoor Unit 12KBTU R32' submittal: 32 7/8 x 10 53/64 x 7 7/8 in (W x H x D), net weight 19.8 lb — the SAME cabinet and the same weight as the 9k (EQ-T-GREE-HEAD-9), to within the 1/64 in the two sheets round to differently. That is a real fact about this line and not a copy-paste: Gree fits both capacities in one shell. This replaced a REPRESENTATIVE PLACEHOLDER (35 x 9 x 12, 'TODO verify datasheet') on 2026-08-31, and the placeholder had it 2 in wider than the 9k, which it is not.",
                  ports=()),
    # System 3 — Gree Sapphire R32, the high-efficiency unit over the stairs. True VFD
    # inverter: the soft start is why this is the one system on the backup battery circuit
    # (a hard-starting compressor is what a battery inverter cannot carry).
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9",
                  name="Gree Sapphire R32 wall-mount head, 9.1k (VFD soft start)",
                  footprint=(inch(38.1875), inch(10.125)), height=inch(13.65625),
                  cooling_capacity_btuh=9100,
                  source="Gree SAP09HP230V1R32AH, the Sapphire R32 9k wall-mounted indoor unit, from the Sapphire R32 9 MBH 230 V submittal (AHRI 214802444): 38 3/16 x 13 21/32 x 10 1/8 in (W x H x D), net weight 33.1 lb. It is a MUCH bigger head than the Multi R32 pair — 5 3/8 in wider, 2 7/8 in taller and 2 1/4 in deeper than EQ-T-GREE-HEAD-9 — which is what a SEER2 30 / HSPF2 11.2 coil costs in volume, and it matters here because this head hangs over the stair. This replaced a REPRESENTATIVE PLACEHOLDER (33 x 8 x 12, 'TODO verify datasheet') on 2026-08-31. True VFD inverter: the soft start is why this is the one system on the backup battery circuit. Heating is rated on EQ-T-GREE-SAPPHIRE-9-OD.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9-OD",
                  name="Gree Sapphire R32 outdoor unit, 9.1k (-22F)",
                  footprint=(inch(34.375), inch(14.796875)), height=inch(21.859375),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=10600,
                  heating_capacity_at_design_btuh=7400,
                  cooling_capacity_btuh=9100,
                  min_operating_temp_f=-22.0,
                  source="Gree SAP09HP230V1R32AO, from the Sapphire R32 9 MBH 230 V submittal (AHRI 214802444): 34 3/8 x 21 27/32 x 14 51/64 in (W x H x D), net weight 78.3 lb, MCA 11 A / MOCP 15 A, SEER2 30.0, HSPF2 11.2, heating range -22 F to 86 F. The outline was 31 x 23 x 13 in until 2026-08-31 — 3 3/8 in narrow and 1 13/16 in shallow. PUBLISHED HEATING, read: 10,600 Btu/h at 47 F, 11,500 at 5 F, 8,900 at 17 F. That 17 F figure is the one the old record got worst: it carried '~11,500-13,000 Btu/h at 5F' and nothing at 17 F, which read as a machine making 12,000 in the middle of its range. It makes 8,900. ** WHICH NUMBER GOVERNS AT DESIGN, AND WHY IT IS NOT GREE'S. ** Gree's own low-ambient table gives ~9,130 Btu/h at -22 F at a 70 F return, at an implied COP of 2.62. A COP of 2.62 at -22 F is not physically plausible for a single-stage residential air-source machine — the best cold-climate units published anywhere are near 1.5 there — and the 8,200 the previous record carried was that table's 90 F-return column, which is a different measurement again. AHRI/NEEP's cold-climate listing says 7,400 Btu/h at 1.32 kW, COP 1.64, at -22 F. THIS DESIGN USES NEEP. heating_capacity_at_design_btuh is 7,400 — the -22 F read value, deliberately used unadjusted at the -15 F design temperature rather than interpolated upward, because the zone is 926 Btu/h and buying margin by interpolation would be spending credibility to gain nothing. min_operating_temp_f -22 F per the operating envelope.",
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
    # System 1's electric heat kit (retyped from EQ-T-DUCT-HEATER-2KW, and it is a different
    # part doing a different job). The 2 kW inline element existed because the VIR24 made
    # 13,500 Btu/h at design against a 16,309 Btu/h block load — a shortfall
    # `mep.heating_capacity` was failing on. Two things were wrong with that answer: the
    # DUC24 has no aux-heat terminal, so nothing could stage the element with the compressor;
    # and covering a design-day deficit with resistance heat is a workaround, not a system.
    # The FLEXX Ultra covers its own load, and this kit is the factory part that stages off
    # its 24 VAC board for defrost recovery and for hours below the -22 F lockout.
    EquipmentType(tag="EQ-T-GREE-FLEXX-HEATKIT-46KW",
                  name="Gree FLEXX Ultra electric heat kit, 4.6 kW, 240V",
                  footprint=(inch(16), inch(10)), height=inch(10),
                  # ** AT-DESIGN IS ZERO, AND THAT IS THE POINT OF THE LOCKOUT. ** 15,695
                  # Btu/h is the nameplate. At this site's -15 F design temperature the kit
                  # delivers NONE of it: LM-HP1-AUX (plan/circuits.py) is an outdoor
                  # thermostat that enables the elements only below the compressor's -22 F
                  # cut-out, which is what makes the elements and the compressor
                  # non-coincident loads and keeps the house inside its 200 A service. So
                  # `mep.heating_capacity` must NOT credit it against the design-day block
                  # load — the margin it reports for System 1 is the machine's own, unaided,
                  # which is the honest reading and the whole case for the retype.
                  heating_capacity_btuh=15695, heating_capacity_at_design_btuh=0,
                  supplemental_heat=True,
                  source="Gree FLEXA2LHTR05KWD factory electric heat kit for the FLEXX Ultra air handler: 4.6 kW at 240 V (4.6 x 3,412 = 15,695 Btu/h, no cold-weather derate), MCA 29.9 A, maximum overcurrent device 35 A. It mounts INSIDE the EQ-T-GREE-FLEXX-ULTRA-24-AH cabinet on the discharge side of the coil and is staged by the air handler's own 24 VAC control, which is the whole point of the retype: the EQ-T-DUCT-HEATER-2KW it replaces was a generic inline element in the supply plenum, and the DUC24 it was drawn against had no aux-heat terminal to interlock it with. Its job also changed. It is no longer covering a design-temperature shortfall — the outdoor unit makes 21,000 Btu/h at -15 F against a 15,164 Btu/h zone load unaided — but is true backup for defrost recovery and for the hours below the -22 F compressor lockout. `supplemental_heat` like the fireplace: it counts toward its room's zone and opens none of its own.",
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
    # Exterior west wall at y=29', 7" outside the sheathing plane — the meter's back is
    # left inside the cladding it is surface-mounted on.
    #
    # Height: the elevation is the *base* of the 16" socket and the project
    # datum is the main floor, so the authored 5'-0" put the glass 8'-6" above SITE_GRADE
    # (-2'-10") — a ladder job, not a meter. 1'-6" here is grade + 4'-4" to the base and so
    # grade + 5'-0" to the register centre, mid-band of the utility's 4'-0"..6'-0" window.
    ElectricalDevice(uid="CEE001AAAA", tag="ED-M-METER", kind=DeviceKind.METER,
                     position=pt(ft(0, -10.25), ft(29, 9.125)), type_ref="ED-T-METER",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(1, 6)), room=None, rotation=deg(270)),
]

# --- the backup microgrid (notes/backup_power.md) -------------------------------------
# Four pieces, positions carry the design: EQ-B-ESS-BATT is the only thing in the RM-B-ESS
# Type X closet, in the furnace room's NE corner; EQ-B-ESS-INV sits outside it, mid-room
# against the east concrete (not a fire risk, needs to be reachable to reset);
# ED-B-BACKUP-PANEL is on the west wall on the inverter's dedicated load output;
# ED-B-BACKUP-ENCL stays in place but demoted to shed-tier relays + 24V bus only, no feed of
# its own. The DC run between the battery and the inverter is flagged on the battery below.
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
    # On the NE closet's north wall, W-B-N3. (8'-1 1/5", 34'-11") puts the 10"-deep cabinet's
    # back flat on that wall's inner face at y=35'-4" and centres it in the 2'-9 5/8" clear
    # width, north of D-B-ESS's swing.
    #
    # **This is a 300 lb wall load and the wall matters.** It is on cast concrete — an 8"
    # pour, anchored directly — which is the fixing this load wants.
    #
    # `code.R327_ess_capacity` reads `room="RM-B-ESS"` to count this as indoor storage
    # (14.3 of the 40 kWh article limit) — a future garage relocation is just this one line.
    #
    # **Flag, not a silent acceptance: the DC run is ~10' long.** EQ-B-ESS-INV is at
    # (8'-1 13/16", 24'-11 7/8") and ED-B-BACKUP-PANEL at (0'-10", 27'-0"). On an EG4 12kPV
    # that is real copper and a real voltage-drop question, and it is the one argument that
    # could send this decision back — the corner was chosen for the battery's separation
    # zone and its concrete fixing, not for the run length.
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
# Face-mounted devices on the perimeter concrete: the walls align on their EXTERIOR face, so
# the inside face is west x=0'-8", north y=35'-4", south y=0'-8" —
# `test_wall_mounted_devices_resolve_against_a_wall_face` reads exactly this.
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
    # RM-B-BATH's NEC 210.52(D) receptacle: GFCI within 3'-0" of the basin's
    # edge (1'-0" here), on the north partition — not the east wall, which is 12" cast
    # concrete behind the basin. Rides CKT-RC-BSMT rather than its own 20A circuit (the
    # panel-slot trade recorded in plans/TODO.md's panel_spaces item).
    ElectricalDevice(uid="CEE040AAAA", tag="ED-B-BATH-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 4), ft(21, 5)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-BSMT", room="RM-B-BATH", rotation=deg(180),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
]

BASEMENT_EQUIPMENT = [
    # There is one water heater, an 80-gal Rheem ProTerra hybrid HPWH
    # (plan/mep.py::EQ-T-WATER-HEATER) — its two internal power draws are not modelled as
    # two appliances.
    # The ventilator is a Broan B210E75RT, four 6" round top ports. Everything downstream of
    # it — the manifolds, the four chase risers, the outdoor side, the radials — is in
    # plan/mep_erv.py, and `pan_drain_ref` names the condensate line a cold-climate core
    # makes water into (plan/mep_drainage.py). The footprint on the element is
    # documentation; the TYPE's 24.8" x 21" is what resolves.
    #
    # Position (3'-11 1/2", 30'-6"): the case's north-east corner is 1 1/2" clear of
    # EQ-B-ESS-BATT's 36" REQUIRED separation zone (x 49 1/4"..145 1/4", y 378"..460"), which
    # `advisory.ess_clearance` grades as a rectangle, not a radius, and clear of
    # ED-B-BACKUP-ENCL's 36" NEC 110.26 working space. Every ERV branch is authored off the
    # two manifolds (plan/mep_erv.py), not off the machine, and PR-B-ERV-COND's drop at
    # (3'-11", 30'-9") is still under the case.
    Equipment(uid="CEE016AAAA", tag="EQ-B-ERV", kind=EquipmentKind.ERV,
              position=pt(ft(3, 11.5), ft(30, 6)), footprint=(inch(24.8), inch(21)),
              room="RM-B-FURNACE", type_ref="EQ-T-BROAN-B210E75RT", circuit="CKT-ERV",
              # HUNG, not floor-standing. Two reasons and the second is the binding one: a
              # Broan ships with hanging straps and this is how the unit installs, and a
              # floor-standing ERV cannot drain by gravity. Its core makes water all winter,
              # the nearest receptor is FX-B-SAUNA-FD nine feet up the basement's other end,
              # and a spigot at slab level has nowhere to fall to.
              #
              # ELEVATION 4'-6", BECAUSE THE PORTS ARE ON TOP. All four air ports on this
              # machine are 6" round on its TOP face (EQ-T-BROAN-B210E75RT,
              # plan/mep_erv_types.py). At 4'-6" the case top is at 6'-3 5/8", giving the two
              # outdoor legs and the two manifold trunks (plan/mep_erv.py) a 6'-10 7/16"
              # crossing band: 1 5/8" under the 7'-6" radial layer, 6 13/16" over this case,
              # and 6'-7 3/8" of headroom beneath — over R305.1.1's 6'-4" basement
              # projection floor. PR-B-ERV-COND (plan/mep_drainage.py) falls 0.3"/ft from the
              # pan to FX-B-SAUNA-FD.
              mount=Mount(kind=MountKind.CEILING, elevation=ft(4, 6)),
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
    # Laundry pair, in the south partition (W-M-CLN) directly behind the tower: FX-M-LAUNDRY
    # is 40" deep x 80" tall, so a surface box there is unreachable and covered by the
    # machine; recessed lets it sit flat with the plug behind it. 43" AFF splits the
    # difference between washer and dryer tops. Both boxes here are
    # `recessed_into_host_surface`, so a stale y does not merely float — it resolves inside
    # the studs; ED-M-LAUNDRY-RC1 below shares this wall for the same reason.
    # CKT-DRYER stays a 30A/14-30R even though the LG DLHC5502V heat-pump dryer only needs
    # 830W/15A minimum branch: it still ships a 4-prong cord needing 30A, and the oversize
    # lets a future conventional vented dryer go in without repulling wire.
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
    # This box stays behind its own appliance (freezer y 27'-4 7/8"..30'-1 3/4") — the
    # same constraint that decided which end of the bay the retired filler went to.
    ElectricalDevice(uid="CEE006AAAA", tag="ED-M-LIVING-KFZ1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(29, 9.25)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # NEC 440.14 disconnects for the two ground-mounted condensers, on W-M-S2's exterior
    # face, side by side east of WIN-M-LIV-S1's rough opening (x 31'-5"..33'-11") and within
    # sight of both units — 440.14 asks for sight, not reach.
    #
    # ** TWO THINGS MOVED THEM ON 2026-09-03, and both are code, not taste. ** They stood at
    # x=30'-0" and x=35'-0" at ft(5).
    #
    #   * NEC 110.26(A) working space cannot be a stairway, and ST-SG-PORCH now runs from
    #     x 28'-6" to 32'-2" straight under the old x=30' station. East of x 33'-11" the 36"
    #     working depth falls over the flight's LEVEL step-off instead.
    #   * NEC 404.8(A) caps an operating handle at 6'-7" above the standing surface. These
    #     are on a MAIN-floor wall but are operated from grade at -2'-10", so ft(5) put the
    #     handles 7'-10" up — nearly a foot past the limit, and nothing was measuring it
    #     because the mount elevation is storey-relative. 3'-6" reads 6'-4" from grade.
    #
    # Both stay clear of either condenser's own 110.26 working space, which is the pad in
    # front of them, and both are now north of the units rather than over them.
    #
    # ED-T-DISCONNECT-3R is a 3 1/4"-deep can, so its centre belongs 1 5/8" off the
    # cladding face. Same correction on ED-M-HP3-DISC below and on ED-B-SPA-DISC.
    #
    # These were on the SECOND storey until 2026-09-02, beside condensers that stood on the
    # balcony (notes/heat_pump_ground_pad.md). The units came down; the disconnects came
    # down with them, because a disconnect one storey above the machine it kills is not
    # within sight of it in any sense 440.14 means.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-HP1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(34, 3.5), ft(0, -8.875)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP1", mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)), room=None),
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-HP2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(35, 7), ft(0, -8.875)), type_ref="ED-T-DISCONNECT-3R",
                     circuit="CKT-HP2", mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)), room=None),
    # System 3 (Sapphire, backup battery circuit): its outdoor unit stands on the north
    # side beside the mudroom door, so the disconnect goes on W-M-N2's exterior face west
    # of the breezeway.
    # Offset per the can's true 3 1/4" depth (see ED-M-HP1-DISC's note on this convention).
    ElectricalDevice(uid="CEE026AAAA", tag="ED-M-HP3-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(4), ft(36, 8.875)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP3",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
    # FH-M-BATH2's thermostat: inside the room on its south wall (W-M-BDN1, interior face
    # y=13'-2 3/8"). Floor sensor is FH-M-BATH2's `stat` point.
    #
    # x=0'-11 3/4" is WEST of D-M-BATH2's opening (x 1'-6 1/2"..4'-0 1/2"), beside
    # FX-M-BATH2-SINK rather than the wall you reach as the door closes behind you.
    #
    # y=13'-3 3/8" is the value that puts the plate's back ON the wall face —
    # `test_wall_mounted_devices_resolve_against_a_wall_face` grades the resolved body, not
    # the authored point, so a value even 9/16" off reads as buried in the finish.
    ElectricalDevice(uid="CEE021AAAA", tag="ED-M-BATH2-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(m(0.298408), ft(13, 3.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH2", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # FH-M-DINING's thermostat: zone is free-standing mid-room, so control goes on the
    # nearest real wall — east wall interior face x=35'-5 3/8" (CATLIN_EXT_2X6's inside face
    # is 6 5/8" in from the 36' sheathing plane). Sits in the 5'-1" clear stretch between
    # WIN-M-LIV-E2 and WIN-M-DIN-E2, 10" clear of ED-M-LIVING-RC3 at y=16'-11".
    # FX-M-BATH2-TUB's Bask outlet. Kohler: "A qualified electrician must
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
    # ** SYSTEMS 1 AND 2 STAND ON THE GROUND, NOT ON THE BALCONY. ** Moved 2026-09-02
    # (notes/heat_pump_ground_pad.md, which carries the clearances, the line-set routes and
    # the sound reasoning). They stood on FS-SG-DECK at +10' — the watertight aluminium roof
    # of an occupied porch — on a lagged aluminium stand that cost eight through-plank
    # penetrations, sixteen sacrificial blocks, two traced condensate runs, and a standing
    # "never soffit this deck" constraint, all of it over the master bedroom's south
    # windows and reachable for replacement only by a French door or a crane.
    #
    # The pocket east of the porch is the site: bounded west by W-SG-E1 (face x=28'-6"),
    # north by the house, south by the W-RG-EAST-BALCONY apron, and open east to the yard.
    #
    # ** THEY FACE SOUTH, SIDE BY SIDE, ACROSS THE POCKET'S SOUTH HALF (2026-09-03). ** They
    # stood in a north-south row against the porch wall facing EAST, because the 2026-09-02
    # siting read the pocket as 90" of usable y and a south-facing row as wanting 99". That
    # 99" figure was right and the 90" was not: it assumed the row had to end at the house's
    # east face, x 36'-0", and east of the SE corner is open side yard out to a setback line
    # at x 58'-0". Letting HP1 stand 7" past the corner is what unlocks the layout, and what
    # it buys is the pocket's whole north strip for ST-SG-PORCH, the porch's stair to grade.
    #
    # `rotation=deg(0)` — the long axis runs in x now, so both discharge faces read SOUTH,
    # into open yard, instead of east into the pocket's own north and west faces (which
    # returned it up at WIN-M-LIV-S1 and WIN-S-STUDY2). Every clearance gains slack: HP2's
    # back goes from 6" — the published minimum — to 16 2/5" off the flight's south rail, its
    # west end keeps 6" to the porch wall, the 12" service gap between the two is now the only
    # figure at a minimum, and both compressors sit 4'-7" south of the house wall instead of
    # 6"-7" off it. Clearances and the sound reasoning: notes/heat_pump_ground_pad.md.
    #
    # ** THE PAD AND THE STANDS ARE IN params/sunken_garden.py (SL-SG-HPPAD, PT-SG-HP*,
    # CN-SG-HP*), AND THE TWO FILES CANNOT IMPORT EACH OTHER. ** The leg positions there are
    # these two centres plus each unit's published foot pattern, so a unit that moves must
    # move in both files. `mount.elevation` is the other half of the coupling: a FLOOR mount
    # measures from the storey datum, `main` is 0'-0", the pad tops out at -2'-8" and the
    # stands are 18", so the cabinets' base is at -1'-2". `test_catlin_outdoor_structures.py`
    # holds all of it together now that `mep.deck_equipment_support_coverage` — which used
    # to — sees no deck equipment at all.
    #
    # No `drain_pan` / `pan_drain_ref` on either, matching EQ-M-HP3-OD below: defrost
    # meltwater off a unit at grade drips onto its own pad and runs east onto gravel. The
    # piped, heat-traced condensate runs the balcony needed are deleted.
    Equipment(uid="CEE017AAAA", tag="EQ-M-HP1-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(34, 11.7), ft(-5, -7.25)), footprint=(inch(39), inch(14.5625)),
              rotation=deg(0), mount=Mount(kind=MountKind.FLOOR, elevation=inch(-14)),
              type_ref="EQ-T-GREE-FLEXX-ULTRA-24-OD", circuit="CKT-HP1", room=None),
    Equipment(uid="CEE018AAAA", tag="EQ-M-HP2-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(30, 8.1), ft(-5, -10.8)), footprint=(inch(40.16), inch(16.81)),
              rotation=deg(0), mount=Mount(kind=MountKind.FLOOR, elevation=inch(-14)),
              type_ref="EQ-T-GREE-MULTI-U30", circuit="CKT-HP2", room=None),
    # System 3's outdoor unit: north side beside the mudroom door, under ED-M-HP3-DISC, for
    # the short lineset run to the head over the stairs — a straight punch through W-M-N2:
    # the unit (x 10'-0"..12'-7") sits directly opposite EQ-M-HP3-STAIR (x 10'-6"..13'-3")
    # on that wall's inside face.
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
              # One 768 sf open room (kitchen/dining/living/hall, and the stair well too,
              # are all inside this claim).
              zone_rooms=("RM-M-LIVING",)),
    # --- System 3's head: stair well NW corner, on the north wall (W-M-N2), surface-mounted
    # since an 8" unit won't fit the 5 1/2" insulated cavity. The mudroom is served instead
    # by REG-M-XFER-MUD, a passive louver in the same wall (plan/mep_registers.py).
    # Position: y=35'-1 3/8" (8" body, back on W-M-N2's face); x=11'-10 1/2" (33" case runs
    # 10'-6"..13'-3", tight into the corner, square over the stair lane, 2 5/8" clear of
    # W-M-STRW); rotation 0 (back north, blowing south down the well — contrast 180 on the
    # System 2 heads, -90 on EQ-M-FIREPLACE). Hangs over open well either way (FO-M-STAIR
    # stops at y=35').
    # `room` is RM-M-LIVING, which the stair well is part of. `zone_rooms` is not — it's the
    # mudroom + mech closet; the stair volume it blows into belongs to EQ-M-HP2-LIVING's
    # 768 sf claim, not counted twice here.
    Equipment(uid="CEE030AAAA", tag="EQ-M-HP3-STAIR", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(11, 10.5), ft(35, 1.375)), footprint=(inch(33), inch(8)),
              room="RM-M-LIVING", type_ref="EQ-T-GREE-SAPPHIRE-9", rotation=deg(0),
              outdoor_ref="EQ-M-HP3-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              zone_rooms=("RM-M-MUDROOM", "RM-M-MECH")),
    # SE corner of the living room, east wall. 7" mount: WIN-M-LIV-E1's RO (sill 30")
    # crosses the cabinet band, so the 21" cabinet (tops at 28") reads as a hearth under the
    # glass instead. 48" cabinet spans y 0'-10"..4'-10", clear of ED-M-LIVING-RC4 at
    # y=5'-6 1/2". rotation -90 backs it to the wall (interior face x=35'-11 3/8").
    Equipment(uid="CEE022AAAA", tag="EQ-M-FIREPLACE", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(35, 8), ft(2, 10)), footprint=(inch(48), inch(7)),
              room="RM-M-LIVING", type_ref="EQ-T-FIREPLACE-EL", rotation=deg(-90),
              circuit="CKT-FIREPLACE",
              mount=Mount(kind=MountKind.WALL, elevation=inch(7))),
]

# --- Second storey: the NW bathroom's floor-heat control -------------------------------
SECOND_DEVICES = [
    # FH-S-BATH1's thermostat, inside the room on its south wall (W-S-BD-N1B, interior
    # face y=26'-4 11/16"), 9" west of D-S-BATH1's opening (x 7'-3"..9'-9"). Same
    # reach-as-the-door-shuts position as ED-M-BATH2-FH-STAT, and clear of the fixture
    # cluster, which all sits north of y=29'-9".
    ElectricalDevice(uid="CEE025AAAA", tag="ED-S-BATH1-FH-STAT", kind=DeviceKind.SWITCH,
                     position=pt(ft(6, 6), ft(26, 10.375)), type_ref="ED-T-FLOOR-STAT",
                     circuit="CKT-FH-BATH1", room="RM-S-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # ** RM-S-SUITEBATH AND RM-S-VANITY EACH NEED THIS RECEPTACLE FOR A GAP THE ENGINE
    # CANNOT SEE. ** Same NEC 210.52(D) gap as RM-M-BATH1 above, and the same reason: the
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
    # System 1's concealed ducted AH — inside SF-S-HP1, the wide bulkhead in RM-S-STUDY2's
    # ceiling (plan/storeys/second.py). Own branch circuit (CKT-HP1-AH) since a ducted unit's
    # blower is fed at the unit, unlike a multi's heads.
    #
    # `soffit_ref` is load-bearing: WITHOUT it a CEILING mount with no stated elevation
    # hangs off `storey.default_ceiling_height` (resolve/placeables.py), which puts this
    # unit at 9'-0", above the box it lives in.
    #
    # `rotation` is not needed: EQ-T-GREE-FLEXX-ULTRA-24-AH states (43.5, 21.25), which is
    # the cabinet as installed: 43 1/2" across x, 21 1/4" along the airflow, supply out the
    # north face into the discharge plenum and return in the south face out of the return
    # chamber. `footprint` here agrees with the type rather than fighting it.
    #
    # (20'-7", 3'-4 3/4") puts it at x 225 1/4"..268 3/4" and y 30 1/8"..51 3/8". y=30 1/8"
    # reaches DU-S-HP-RET's 25x14 stub and its 3 1/8" collar; the return chamber, REG-S-HP-RET
    # and EQ-S-ERV-MIX are all built to that face. North of the discharge, DU-S-HP-SOUTH-RISE's
    # take-off leg and the heat kit occupy the clear box between the discharge face and the
    # ERV feed's east jog at y=5'-5 1/2".
    #
    # It is still 2 5/8" inside SF-S-HP1's west cavity face and clear of the east lanes by
    # more than the 2" hanger gap; the check prints the clearances, so they are not restated.
    #
    # zone_rooms covers the whole conditioned second storey plus RM-A-STUDY/RM-A-EAST-UNFIN
    # (short attic branches) and RM-A-STUDIO/RM-A-STUBATH/RM-A-POCKET — the three rooms the
    # west loft split into, all conditioned by the one boot REG-A-HP-WEST on the suite
    # branch. Dropping any of the three from this list would report it as unheated.
    Equipment(uid="CEE032AAAA", tag="EQ-S-HP1-AH",
              kind=EquipmentKind.DUCTED_AIR_HANDLER,
              position=pt(ft(20, 7), ft(3, 4.75)), footprint=(inch(43.5), inch(21.25)),
              room="RM-S-STUDY2", type_ref="EQ-T-GREE-FLEXX-ULTRA-24-AH",
              outdoor_ref="EQ-M-HP1-OD", circuit="CKT-HP1-AH",
              mount=Mount(kind=MountKind.CEILING), soffit_ref="SF-S-HP1",
              zone_rooms=("RM-S-STUDY2", "RM-S-PLANT", "RM-S-BED1", "RM-S-BED2",
                          "RM-S-BED3", "RM-S-SUITE", "RM-S-SUITEBATH", "RM-S-VANITY",
                          "RM-S-BATH1", "RM-S-HALL", "RM-S-CLOSET", "RM-S-NCLOSET",
                          "RM-A-EAST-UNFIN", "RM-A-STUDY", "RM-A-STUDIO",
                          "RM-A-STUBATH", "RM-A-POCKET")),
    # System 1's heat kit, INSIDE the air handler's discharge plenum in SF-S-HP1.
    #
    # The FLEXX Ultra's 24 VAC board stages this kit itself, and the kit is a factory part
    # that lands in the cabinet's discharge — hence `soffit_ref` is SF-S-HP1, and the plate
    # sits at (21'-1", 4'-8 3/8"): its south edge flush on the cabinet's discharge face at
    # y=4'-3 3/8", inside DU-S-HP-SOUTH-RISE's take-off leg and 2" clear of DU-S-HP-SUP's
    # take-off the other side of the same discharge. `mep.duct_soffit_occupancy` reads that
    # leg's centreline running through the plate and reports the two as one assembly.
    #
    # `room` follows the box: RM-S-STUDY2, which is the room SF-S-HP1 hangs in and the room
    # the air handler is already filed under. It changes nothing about the credit —
    # `supplemental_heat_by_room` keys on the room and both rooms are in the same
    # EQ-S-HP1-AH zone_rooms list — and it is where the part is.
    #
    # ITS JOB CHANGED TOO, and that is the more important half. It is no longer covering a
    # design-temperature shortfall: EQ-M-HP1-OD makes 21,000 Btu/h at -15 F against a
    # 15,164 Btu/h zone load, unaided. This is defrost-recovery and sub-lockout backup.
    #
    # CKT-HP1-STRIP IS GONE. A factory kit inside the cabinet is fed from the air handler's
    # own circuit, so CKT-HP1-AH goes 15A -> 35A (the kit's MCA 29.9 A / max OCPD 35 A) and
    # the panel gets its spare 2-pole back at slot 18 (plan/circuits.py).
    Equipment(uid="CEE033AAAA", tag="EQ-S-HP1-STRIP", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(21, 1), ft(4, 8.375)), footprint=(inch(16), inch(10)),
              room="RM-S-STUDY2", type_ref="EQ-T-GREE-FLEXX-HEATKIT-46KW",
              circuit="CKT-HP1-AH", mount=Mount(kind=MountKind.CEILING),
              soffit_ref="SF-S-HP1"),
]

# --- Garage: EV receptacles on the west and south walls ----------
# ED-G-EV-1450 is on W-G-S's INTERIOR face. GARAGE_WALL_2X6's sheathing is 5/8" CDX and its
# cladding is 7/8" corrugated, and the wall also carries a 3/8" node-line offset
# (`GARAGE_Y_SOUTH`, plan/storeys/garage.py) that keeps the breezeway slot — net, W-G-S's
# interior face sits +3/8" (node) - 7/8" (wall depth) = -1/2" off the sheathing plane.
# `ED-G-EV-620` is on W-G-W, which has no node-line move, so its interior face is 7/8" off
# the sheathing plane.
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(0, 8.75), ft(56, 0.75)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE", rotation=deg(90)),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(19, 11.375), ft(41, 5.375)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE"),
]

GARAGE_EQUIPMENT = [
    # West wall — the only wall with nothing else in it. Mounted 6'-0" on an 8' wall, 15"
    # case tops at 7'-3", blows down over a bench.
    # Hard-wired, not cord-and-plug: NEC 210.8(A)(2) GFCI applies to garage *receptacles*
    # only, so CKT-GAR-HEAT carries none — a plug-in unit would need CKT-RC-GARAGE instead.
    # The case clears FX-G-HYDRANT's own y band by 12" — the hydrant is the one thing in
    # this corner someone stands over with a hose — without moving the heater off
    # FURN-G-WORKBENCH, which it is here to blow down over.
    Equipment(uid="CEE023AAAA", tag="EQ-G-HEATER", kind=EquipmentKind.SPACE_HEATER,
              position=pt(m(0.213454), m(17.858)), footprint=(inch(14), inch(9)),
              room="RM-GARAGE", type_ref="EQ-T-GARAGE-HEATER", rotation=deg(90),
              circuit="CKT-GAR-HEAT",
              mount=Mount(kind=MountKind.WALL, elevation=ft(6))),
]

# --- Attic: PV junction box beside the radon riser -----------------------------------
PV_JBOX = [
    # Offset per the can's true 3 1/4" depth (see ED-M-HP1-DISC's note on this convention).
    #
    # ** THE STATION HAS TO CLEAR BOTH THE RAKE AND A WINDOW, AND THE BAND IS NARROW. **
    # The rake wants x >= 9'-1 1/4" (the gable plane is 20'-11 3/8" + x/2, and this box
    # needs 25'-6" of cladding to grip); WIN-A-N1's rough opening (x 10'-9"..13'-3",
    # framing bumper 10'-7"..13'-5", sill +22'-0", head +25'-0") wants x <= 10'-7" or
    # x >= 13'-5". Those do not overlap at 25'-6": the ROOF UNDERSIDE (20'-1 1/2" + x/2,
    # the plane `integrity.element_above_roof` reads, a foot below the cladding plane)
    # needs x >= 10'-10" to carry a 25'-6" riser, and the window starts at 10'-9". So the
    # box sits at x=10'-2", elevation 25'-0", where the underside is 25'-4" and there is
    # 4" of clearance — wholly west of the window on the facade, which is the better
    # elevation anyway.
    #
    # Going east instead (x >= 13'-7") clears the window at 25'-6" and costs 2'-6" of
    # 1 1/2" EMT to reach a worse station: further from VR-M-RADON-VENT's riser, and out
    # over the stair void's bay.
    #
    # ** IT SITS ON W-A-N2B, NOT W-A-N2 ** — the north gable splits at x=10'-0", and
    # 10'-2" is 2" east of that. test_catlin_outdoor_structures.py names the wall it must
    # ride below; that assertion follows the box.
    ElectricalDevice(uid="CEE014AAAA", tag="ED-A-PV-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(10, 2), ft(36, 10.25)), type_ref="ED-T-PV-JB", circuit="CKT-ESS-GRID",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]
# ** THERE IS NO CN-A-PV-CLAMP, for the same reason as CN-A-NEMA-CLAMP **
# (plan/mep_electrical.py, which carries the full note): W-A-N2 wears `pbr-panel-26`, an
# exposed-fastener panel with no seam, so a seam clamp there is uninstallable. The box is
# screwed through the
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
    # Up the mechanical chase beside the radon vent to the PV junction box, at
    # (1'-6", 34'-6") — inside the enclosure, not out on the open mudroom floor.
    # ** THE RISER STOPS AT THE ATTIC DECK, AND CD-A-PV-EAST FINISHES IT. ** At 6:12 off a
    # 20'-11 3/8" eave the roof plane at x=1'-6" is 21'-8 3/8", so a riser continuing to
    # 25'-6" there would run outside the building. The chase does NOT move — moving it would
    # drag the mechanical-room penetration through every storey below, which is the same
    # reason VR-M-RADON-VENT jogs in the attic instead of relocating (mep_venting.py). A
    # ConduitRun travels flat at `start_elevation` and rises only at its LAST point, so
    # "up, then over" is two runs, not one polyline.
    ConduitRun(uid="CDT001AAAA", tag="CD-B-ATTIC-RISER", trade_size=inch(1.5),
               path=(pt(ft(2), ft(29)), pt(ft(1, 6), ft(34, 6))),
               start_elevation=ft(-4), end_elevation=ft(20, 6),
               from_ref="ED-B-PANEL", to_ref="ED-A-PV-JB"),
    # The over-and-up leg: east along the attic deck under the north rake, into the north
    # gable wall, and up it to ED-A-PV-JB at 25'-6". 6" above the deck for the flat part,
    # which is what CD-A-DATA-NE does on the same storey and for the same reason.
    #
    # It turns north at x=9'-6", 6" clear of FS-ATTIC's deck void (x 10'-0"..18'-0") west
    # edge, and finishes inside the gable wall. y=35'-10" is 4" into W-A-N2/W-A-N2B's 5 1/2"
    # stud cavity (which runs y 35'-6"..35'-11 1/2"), so the run straps to gable studs for
    # its last 1'-6" and stands up between them, directly behind the box. There is no third
    # option: FS-ATTIC's void stops at y=35'-5 3/8" and W-A-N2B's gwb face starts at
    # y=35'-5 3/8" too, so between the hole and the wall there is nothing at all. It is
    # 1 1/2" EMT in a 5 1/2" stud — a 2" bore, 36% of the depth, inside R502.8's 40% for a
    # bored hole.
    #
    # The riser follows ED-A-PV-JB west to x=10'-2" and down to 25'-0"; the box's own note
    # carries why that station.
    ConduitRun(uid="XJR4KE400J", tag="CD-A-PV-EAST", trade_size=inch(1.5),
               path=(pt(ft(1, 6), ft(34, 6)), pt(ft(9, 6), ft(34, 6)),
                     pt(ft(9, 6), ft(35, 10)), pt(ft(10, 2), ft(35, 10))),
               start_elevation=ft(20, 6), end_elevation=ft(25),
               from_ref="CD-B-ATTIC-RISER", to_ref="ED-A-PV-JB"),
    # --- the backup microgrid's three raceways ----------------------------------------
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
    # crossing W-B-N2/W-B-N3 once, 4" clear of that wall — see CONDUIT_SLEEVES below.
    ConduitRun(uid="CDT002AAAA", tag="CD-B-GARAGE", trade_size=inch(1.25),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(35)), pt(ft(16), ft(35)),
                     pt(ft(16), ft(41, 9.375))),
               start_elevation=ft(-4), end_elevation=ft(5, 10),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # Across the basement ceiling to the kitchen's east counter wall, where KGF3 (the device
    # this feeds) is.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(28, 11))),
               # -1'-6": the deck soffit is at -13 7/16" and its board at -14 1/16", so the
               # clear under it is 1 15/16" — still clear, and this is the tightest raceway
               # in the basement. Its two wall crossings go with it.
               start_elevation=ft(-1, -6), end_elevation=ft(3, 6),
               from_ref="ED-B-PANEL", to_ref="ED-M-LIVING-KGF3"),
    # South out of the basement to the hot tub disconnect under the porch. The east leg runs
    # 1' north of the y=0 sheathing line, so it crosses W-B-S1 once rather than running
    # 6'-6" inside it.
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
    # ** NEITHER RUN CROSSES THE STAIRWELL. ** Routed straight east at +9'-2" from the
    # chase at y=34'-6", they would be inside FS-S-WEST — the SECOND storey's floor, whose
    # joists run 9'-0 1/8" to 10'-0" — and FS-S-WEST's deck void is x 10'-3 3/8"..17'-8 5/8",
    # y 26'-0 3/8"..35'-5 3/8". KITCH would span **7.27 ft** of that opening and PORCH
    # **15.52 ft**, because PORCH's south leg would run down x=17'-6", which is 2 5/8"
    # INSIDE the second floor's trimmer even though it is exactly ON the main floor's —
    # eight more feet of raceway over a two-storey stairwell with nothing to strap it to.
    # Both figures are measured by `mep.run_over_void` (checks/mep/routing.py); reading
    # them by eye against FS-M-STAIR's slightly narrower opening under-counts both. A
    # ConduitRun carries no floor_ref, so nothing else grades it, and `duct_joist_bay`
    # only fires on JOIST_BAY routing.
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
    # fan's supply, one hole and two raceways, at the same exit point x=17'-6". **This costs
    # nothing extra**: 33'-6" + 15'-6" + 5'-10" south-then-east-then-south is the same
    # 54'-10" of plan run as the void-crossing alternative's 15'-6" + 39'-4", so 55.33 LF
    # developed either way, at identical cost. The long x=2'-0" leg rides FS-S-WEST, which
    # is open-web:
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
    # Out of the chase at (2'-0", 34'-6") on the attic deck at +20'-6", straight down the
    # RM-A-POCKET side of the wall line at x=2'-0" to y=22'-6", then into W-A-STU-N's sole
    # plate and up its 3 1/2" cavity to the AP at +23'-0".
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

# --- The three hardwired drops (owner) ----------------------------------------------------
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
    # beside ED-M-STUDY-RC1, the pairing a desk actually wants. 1'-0" west of it, at 32" AFF
    # — 2 1/2" over FURN-M-STUDY-DESK's top (20" deep, top at 29 1/2"), in the last course of
    # WP-M-STUDY-WAINSCOT, at hand height beside the laptop. A plate cut into a wainscot is
    # ordinary joinery.
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
    # Nothing in the engine grades run against run: `mep.run_proximity` does not exist,
    # because it would surface a long tail across 111 runs. So this clearance was measured
    # by hand and is written down here, because the next person to move this line will not
    # be told by anything.
    ConduitRun(uid="Z9TXYSYKWG", tag="CD-B-DATA-STUDY", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(inch(10), ft(31)), pt(ft(2), ft(31)), pt(ft(2), ft(19)),
                     pt(ft(16), ft(19)), pt(ft(16), ft(18, 5))),
               start_elevation=inch(-12.5), end_elevation=ft(2, 8),
               from_ref="ED-B-NET-PATCH", to_ref="ED-M-STUDY-DATA1"),
]

DATA_SLEEVES = [
    # CD-B-DATA-MEDIA's concrete crossing. `mep.sleeve_coverage` is a CODE-tier check and
    # an unsleeved crossing of a pour FAILs it. There is only one sleeve here, not two:
    # W-B-STR3 (x=10', y=30') is 2x6 bearing studs, not concrete, so its crossing is a
    # bored hole on the day, not a sleeve set before a pour — the raceway still crosses the
    # wall at that station, there is simply no pour to cast into.
    SleevePenetration(uid="V44DS76X6J", tag="SP-B-CN-CD-DATA", host_ref="W-B-CN",
                      position=pt(ft(18), ft(30)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.DATA,
                      axis="horizontal", center_elevation=ft(-1, -6)),
]

ATTIC_DATA_DEVICES = [
    # On W-A-STU-N, between RM-A-STUDIO and RM-A-STUDY — the two rooms in this attic that
    # hold people, both west of the stair void.
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
# SL-SG-DECK modelled a penetration that doesn't exist and graded UNKNOWN forever.
# ED-M-PORCH-FAN's undrawn supply is the ordinary "last leg" branch-wiring gap, not a
# penetration gap.

# --- Raceway penetrations through cast concrete ---------------------------------------
# Fifteen holes existed in the concrete and nothing in the model — `concrete_crossings`
# walked only pipe runs. Positions are resolver-computed crossing points, not hand-measured
# (`mep.sleeve_coverage` matches on them). Wall/footing crossings are horizontal, carry the
# run's elevation; deck/slab crossings are vertical.
CONDUIT_SLEEVES = [
    # CD-B-GARAGE: west to east across the basement at -4', then north under the house/
    # garage gap and up through the garage slab. The east leg runs at y=35'-0", 4" clear of
    # W-B-N3/W-B-N2's inside face (35'-4"): no crossing, no hole. W-B-STR at x=10' is framed,
    # so its crossing is bored, not cast. Only the genuine north punch at x=16'
    # (SP-B-N2-CD-GAR2) is a hole in concrete.
    SleevePenetration(uid="CNS008AAAA", tag="SP-B-N2-CD-GAR2", host_ref="W-B-N2",
                      position=pt(ft(16), ft(35, 6)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # Through the ICF *stem*, not the footing under it. The run holds -4'-0" the whole way
    # (it is pinned to the basement it leaves), and the garage foundation followed grade
    # down with the soil: FT-GF-S2 bears at -6'-8" and its top is -6'-0", two feet clear
    # below this crossing, while W-GF-S2 spans -6'-0" to -0'-8" and is what the conduit
    # actually passes through.
    #
    # `integrity.sleeve_in_opening` tests the centre against the STRUCTURE layer — the 6"
    # concrete core, not the 11" stem — and the core's south face is GARAGE_Y_SOUTH + 2 1/2"
    # of EPS. The run crosses the whole stem, so the y here is free; it sits on the core's
    # mid-depth — 3" of concrete either side — and no future move of the wall line at this
    # scale can reach it.
    SleevePenetration(uid="CNS009AAAA", tag="SP-GF-CD-GAR", host_ref="W-GF-S2",
                      position=pt(ft(16), ft(41, 2.125)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # The stub-up, 3 3/8" north of the stem's inside face, at 41'-9" — 2 3/8" of concrete
    # around the bore. `integrity.sleeve_in_opening` tests the sleeve's CENTRE, so the full
    # 2 3/8" margin is what protects it, not half the bore's clearance to the slab edge. The
    # conduit runs up the inside face of W-G-S from here to ED-G-EV-1450.
    SleevePenetration(uid="CNS010AAAA", tag="SP-G-CD-GAR", host_ref="SL-G-FLOOR",
                      position=pt(ft(16), ft(41, 9.375)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240),
    # CD-B-KITCHEN: east across the basement ceiling at -1' and up through SL-M-DECK to the
    # kitchen's east counter wall. The wall and deck sleeves are 1/2" apart in plan but in
    # different hosts, which is what the matcher keys on. W-B-STR3 (x=10', y=29') is framed
    # now, so it has no sleeve here; its partner in W-B-CN stays, since that wall is still
    # concrete.
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
    # RC1/RC2 hang on the x=18' line's west face. W-B-CS is a 2x6 stud wall with a liner,
    # west face at 17'-5 3/4"; these two sit 1" off it, the setback the whole NEC fill sets
    # its bodies back from the face it hangs on.
    ElectricalDevice(uid="NEC001AAAA", tag="ED-B-GYM-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 4.75), ft(2, 7.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC002AAAA", tag="ED-B-GYM-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(17, 4.75), ft(10, 6.5)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # RC3/RC4 are on the gym side of W-B-CE, a 6 3/4" staggered partition on the y=18'-0"
    # centreline: gym face at 17'-8 5/8", play face at 18'-3 3/8". y=17'-7.615" is the gym
    # face less the 1" body setback this file sets everywhere, and `rotation=deg(180)` turns
    # the plate south into the gym. `room=` is authored so the two rooms can never trade one
    # box between them — `electrical.receptacle_spacing` accepts any device within
    # `_NEAR_WALL_M` (0.5 m) of a room's clear face regardless of which side it's drawn on.
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

    # RM-B-WORKSHOP has zero receptacles otherwise — `electrical.receptacle_spacing`
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
    # ED-B-GYM-RC3/RC4 resolve on the gym face, not this room (see the NEC fill above); this
    # receptacle was never a duplicate of them — it is on the north wall behind the
    # television, 17' away.
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
    # RC5 is the only receptacle covering BOTH ends of the south run — D-M-BALC's east jamb
    # at 23'-10" and the far end near the SE corner, where RC4's coverage comes round the
    # east wall to meet it — and the two ends together pin it to a ~5" window, about
    # 29'-5"..29'-10". 29'-7" splits it: 5'-9" to the jamb, 5'-9 3/4" to the far point. No
    # stud line falls in that window (28'-8" and 30'-0" are the neighbours), so unlike its
    # neighbours this box is not 3/8" off a stud — it lands mid-bay, 3" east of the 29'-4"
    # bay centre.
    ElectricalDevice(uid="NEC012AAAA", tag="ED-M-LIVING-RC5", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 7), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # ED-M-LIVING-RC6 (uid NEC061AAAA) stood at (35'-4 3/8", 23'-8 3/8") on the east wall
    # at 16" and is DELETED: FURN-M-KIT-PANTRY-S2, a 96" tall cabinet, occupies y
    # 21'-2 3/8"..23'-2 3/8" and S1 23'-2 3/8"..25'-2 3/8", so that station is behind a
    # floor-to-ceiling carcass. A receptacle behind a fixed cabinet is not wall space under
    # 210.52(A) and is not reachable under any reading of it. The tombstone is here rather
    # than a silent removal because the uid is an IFC GlobalId that has shipped.
    # RM-M-PANTRY's reach-in outlet. NEC 210.52(B)(1) puts a pantry receptacle on a
    # small-appliance branch circuit, so CKT-KITCH-SA1 and not CKT-RC-MAIN. NOT GFCI: E3902
    # keys on room occupancy (STORAGE is not in the map) and on the 6' sink reach, and
    # FX-M-KITCH-SINK is 8'-1" away.
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
    # The hall band: merging RM-M-HALL into this room via BM-M-HALL lost its 210.52(A)
    # hallway exemption, and the band had zero receptacles. Positions are the four gaps
    # `electrical.receptacle_spacing` measured on the merged clear face.
    #
    # Eight outlets on the storey receptacle circuits are GFCI *devices*, not breakers
    # (code.E3902_gfci_locations): each sits within E3902.10's 6' sink reach while its
    # circuit (CKT-RC-MAIN/CKT-RC-SECOND) spans a whole storey non-GFCI, so one splashed
    # bathroom outlet can't take the floor down with it.
    #
    # This one is the hall's receptacle; ED-M-BATH2-RC1 below is RM-M-BATH2's vanity
    # outlet. x=6'-10" is on W-M-HS2 (6'-0"..8'-0"), whose NORTH face is hall. y=22'-8 3/8"
    # is that face. It clears ED-M-HALL-SW's plate (x 6'-3 3/8"..6'-5 3/8") by 2 5/8".
    ElectricalDevice(uid="NEC066AAAA", tag="ED-M-LIVING-RC8", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(6, 10), ft(22, 8.385)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # RM-M-BATH2's vanity outlet, and the room's only usable one. NEC 210.52(D) / IRC
    # E3901.6 want a receptacle within 36" of the outside edge of EACH BASIN, and ** THE
    # ENGINE HAS NO E3901 RULE AT ALL ** (see CKT-BATH-ATTIC in plan/circuits.py), so nothing
    # will report a miss here or anywhere else — two other lavatories in this house are
    # outside the 36" today, and both are written up in plans/TODO.md rather than moved
    # here, because they are not this room.
    #
    # It is on W-M-W3's finish face beside the bowl: x=7 5/8" is the face at 6 5/8" plus the
    # device's own 1" half-depth, y=15'-3" is 5 3/8" south of the basin's south edge.
    # rotation 90 turns the 4" box to run along the wall, matching ED-M-BATH2-MIRROR
    # directly above it. 44" puts it 8" above the 36" counter, which is where a backsplash
    # outlet goes.
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
    # RM-M-BATH1's only receptacle. NEC 210.52(D) requires at least one within 36" of the
    # sink's outside edge, and
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
    # y is on W-M-STOS's north face. It's inside RM-M-MUD-CLOSET, kept on purpose: NEC
    # 410.16 restricts closet luminaires, not receptacles, and RM-M-MUDROOM is
    # Occupancy.STORAGE so `electrical.receptacle_spacing` never walks it anyway. Stays GFCI
    # for its E3902.10 sink-reach location (RM-M-BATH1's lav, through W-M-STOS).
    ElectricalDevice(uid="NEC067AAAA", tag="ED-M-LIVING-RC9", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(4, 6.625), ft(26, 9.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # GFCI, for the same reason RC9 above is: RM-M-BATH1's lavatory is a 24" vanity whose
    # cabinet reaches 4'-9" further east than an 18" bowl would, so this receptacle falls
    # inside E3902.10's 6'-0" sink reach — 4'-7" to the cabinet's nearest corner, measured
    # through D-M-BATH1's open doorway rather than through a wall.
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
    # removed with D-M-STAIR (main.py WALLS) and the receptacle went with its host — there
    # is no wall on that face any more to mount it to.
    # Fills the >6' gap electrical.receptacle_spacing opened on the hall band between RC7/
    # STUDY-RC3 and the door into RM-M-STOS: N-M-W2/N-M-C2 sit 6" north of where the BATH2
    # wall move put them, stretching this door-to-door wall space past the 6' rule.
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
    # RC1 and RC3 are on the study's south/north walls (east wall nearly all door), 5'-2"/
    # 5'-10" from FX-M-LAUNDRY-SINK — inside E3902.10's 6', so both are GFCI at the device.
    # 32" is 2 1/2" over FURN-M-STUDY-DESK's top, still well under NEC 210.52(A)'s 5'-6".
    # Paired with ED-M-STUDY-DATA1 at the same height 1'-0" west.
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
    # x = 13'-8 1/2" is W-M-LS's resolved study face plus half this type's 1" depth;
    # y = 19'-4" centres it on FURN-M-STUDY-DESK, whose top is 29 1/2" — so 32" puts the box
    # 2 1/2" clear of the desk exactly as ED-M-STUDY-RC1 does, and the two outlets a seated
    # person reaches are at one height on two walls. It is 4'-0" south of REG-M-SUP4's riser
    # bay (y=20'-8"), so the box and the 3" duct in that cavity never meet.
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
    # RM-S-PLANT's five outlets are all ED-T-RECEPTACLE-WR-GFCI: WR-listed
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
    # RC1 is on the 11'-4" bay centre, the *west* jamb of D-S-DECK-W's rough opening (x
    # 12'-2"..17'-2") — the east remnant is 2" of wall — which is also what closes the wall
    # space west of the door, 6'-3 3/4" from RC2 alone (electrical.receptacle_spacing).
    # FX-S-BALC-HYD gave up this bay for it and moved to 7'-4" (plan/fixtures.py).
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
    # RM-S-BED1's west wall, SOUTH of D-S-BED1. The run from the room's SW corner to the
    # door's south jamb exceeds NEC 210.52(A)(1)'s 6 ft without a receptacle in between —
    # `electrical.receptacle_spacing` reports the gap at (22'-0", 14'-5") otherwise. y=11'-0"
    # is 2'-0" from the corner and 3'-5" from the jamb, so both halves of the run are
    # covered, and it is station 24" on W-S-BW1's grid:
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
    # RM-S-BED2's west wall, NORTH of D-S-BED2. The door's rough opening runs
    # y 21'-9 1/16" .. 24'-3 1/16" and breaks the wall line there; the space that reopens at
    # the north jamb runs 6'-2 5/8" round the NW corner to ED-S-BED2-RC1 before reaching a
    # receptacle, which is the 210.52(A)(1) 6' rule by 2 5/8" — the one FAIL the house
    # carried. x=22'-1 3/8" is W-S-BW2's east gypsum face: the wall carries 1/2" of
    # resilient channel on the HALL side only and is datumed on its studs, so this face is
    # 2 3/8" east of the 21'-11" axis (the wall is 5 1/4", not 4 1/2", and is no longer
    # symmetric about that axis);
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
    # RC2 is on the suite's east wall, not the arm's south wall — x=13'-1" there is inside
    # O-S-CLOSET's 4'-8" cased opening (x 11'-5 1/2"..16'-1 1/2"), a box in a doorway. Here it
    # also closes the 8'-5" run 210.52 measured from the opening's west jamb round to RC3.
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
    # y follows W-S-SN1's south face: the suite's north wall is the 8" staggered sound wall,
    # not the 4 3/4" INT_2X4_PARTITION.
    ElectricalDevice(uid="NEC045AAAA", tag="ED-S-SUITE-RC5", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(1, 0.75), ft(21, 11)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC046AAAA", tag="ED-S-SUITE-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(9, 3.125), ft(20, 6.375)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    # RC8: W-S-SN3 is INT_2X6_STAGGERED_PLUMBING (plan/storeys/second.py — the suite bath's
    # lav and WC actually back onto it), and this room's boundary opens a >6' gap on the
    # L-arm's south wall, W-S-SBS. None of RC1-RC7 reaches it — RC1 is 4'-3" east on the same
    # wall but stops short of the corner.
    #
    # GFCI: `code.E3902_gfci_locations` measures to a fixture's insertion CENTROID, and by
    # that reading this stretch is not within 6' of a sink — but measured to the suite bath
    # vanity's actual edge, as E3902.10 asks, the box is 4'-4" from it, not clear of the
    # circle at all.
    #
    # y is 15'-7 5/8": W-S-SBS is INT_2X4_PARTITION, its wet-wall duty having moved to SN3,
    # so its south face sits 1.000" back from the axis, and this box — and RC1 beside it —
    # follows that face.
    ElectricalDevice(uid="N0F72WZE2H", tag="ED-S-SUITE-RC8",
                     kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(11), ft(15, 7.625)),
                     type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
]
# Same treatment for the attic's lofts. RM-A-EAST-UNFIN and RM-A-POCKET are STORAGE,
# outside `_HABITABLE`, so 210.52 spacing is not evaluated for them. RM-A-STUDIO is a
# habitable bedroom and takes full 210.52 spacing; only the pocket it was split from stayed
# STORAGE. The room is already most of the way there — the east loft's ring and the study's
# devices cover its long walls — and `electrical.receptacle_spacing` names the two gaps
# that are left, both of them around the inside corner the bathroom cuts out of it at
# (9.9', 17.7'). The three devices at the end of this list are those two gaps and the bath.
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
