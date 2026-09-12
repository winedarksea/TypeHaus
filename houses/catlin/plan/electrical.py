# haus: editable
# Catlin electrical service upgrade (plans/electrical_notes.md): 200A service, separate
# meter, 225A panel (plan/mep.py), 240V appliance circuits, two garage EV receptacles, the
# backup subsystem's DIN enclosure, hot tub + heat-pump disconnects, PV junction box.
#
# All-electric: no gas, no furnace. Three Gree heat-pump systems plus electric radiant
# floor zones (FloorHeat in plan/storeys/):
#   System 1  EQ-M-HP1-OD (FLEXX Ultra, NORTH pad) -> EQ-S-HP1-AH, concealed ducted AH in
#             SF-S-HP1 over RM-S-NCLOSET, feeding the dropped hallway chase SOUTHWARD —
#             upstairs + two attic branches.
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
# pillar). EXT_2X6's inside face is 6 5/8" in from the sheathing datum, cladding
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
#
# ** THE GROUNDING ELECTRODE SYSTEM IS NOT MODELLED, AND THIS COMMENT IS ALL THERE IS. **
# No element kind can hold one: grep the engine for `grounding electrode`, `ground rod` or
# `ufer` and there are no hits, so there is nothing to author and nothing to grade. The
# intent, recorded here so it reaches the electrician rather than being rediscovered on
# site:
#
# - A CONCRETE-ENCASED ELECTRODE (NEC 250.52(A)(3), the "Ufer") is the primary. This house
#   pours continuous footings with galvanized bar throughout, which is exactly the
#   condition the article is written for: 20 ft or more of 1/2" or larger bar in the
#   bottom of a footing in direct contact with earth. It is close to free at pour time and
#   cannot be retrofitted afterwards at any price. ** It must be tied and stubbed BEFORE
#   the footing pour ** — this is the one item on this list with a hard deadline.
# - SUPPLEMENTAL RODS where the encased electrode alone is not accepted. 250.53(A)(2)
#   wants a second rod unless the first is shown to be 25 ohms or less, and a rod pair is
#   cheaper than the resistance test.
# - The bonding jumper lands at ED-B-PANEL at (10", 29'), which is the same enclosure
#   CKT-SPD protects. That is not a coincidence and it matters: an SPD clamps to ground,
#   so its let-through voltage is only as good as the electrode behind it. A surge device
#   on a poor ground is decoration.
# - ** DO NOT bond the PV/lightning path to a rebar run carrying a cathodic anode. **
#   plans/notes.md flagged this and it is real — an anode tied to a grounded system
#   discharges into the earth instead of into the steel it is meant to protect. The
#   columns declined anodes in favour of galvanized bar at 2" cover, so today there is no
#   conflict; re-read this line if anodes are ever added (plans/TODO.md tracks that
#   decision for the sunken-garden walls).

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
                          plan_symbol="junction-box",
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
    # The same radio on a wall bracket, and it exists because ``footprint`` is a PLAN
    # rectangle: the ceiling type's 8x8 is the disc seen from below, and hung on a wall that
    # reads as 8" of DEPTH, so ED-A-STUDIO-AP buried 3" of itself in W-A-STU-N's studs at
    # 0 FAIL. Turned on edge the disc is 8" across the wall and 2" off it, which is what
    # these numbers are; ``height`` is the 8" diameter now that the diameter stands up.
    ElectricalDeviceType(tag="ED-T-AP-WALL",
                          name="Wireless access point, wall, PoE 802.3af",
                          poe_watts=15.0,
                          footprint=(inch(8), inch(2)), height=inch(8),
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
    # RM-B-SAUNA's heated zone measures 555 cf off the resolved liner faces (8'-3 15/16" x
    # 8'-10 11/16" x 7'-6").
    #
    # ** THE 9 kW WAS UNDERSIZED, AND IT WAS THE "600 cf" CLAIM THAT WAS WRONG (2026-09-06).
    # ** The comment this replaces held 9 kW on the argument that the trade rule
    # (~1 kW / 45-50 cf, wanting 11.1-12.3 kW here) could be taken at its low end because the
    # room is basswood over foil-polyiso on all six surfaces, and that "the notes' heater is
    # rated 9 kW to 600 cf". No manufacturer researched publishes a 9 kW to 600 cf: every
    # one of their own tables puts 9 kW at 283-494 cf, and HUUM voids its warranty outright
    # if the room is dimensioned wrong. The glass partition in
    # notes/sauna_shower_basement_detail.md adds notional volume on top of the 555. The
    # comment even names the wall it is standing on — "600 cf is the wall this room is now
    # 45 cf from" — and the wall was in the wrong place.
    #
    # 10.5 kW, and it is a cascade rather than a swap. CKT-SAUNA moves 50 A -> 60 A and
    # 9000 -> 10500 VA (circuits.py), and the two sauna detail notes' sheet lines move with
    # it, because "240 V, 50 A, 10.5 kW max" was never arithmetic that closed: NEC 424.3(B)
    # makes this a continuous load at 125%, so 10500/240 = 43.75 A x 1.25 = 54.7 A and 50 A
    # will not carry it. (The 50 A WAS right for 9 kW — 37.5 x 1.25 = 46.9 A. It is the kW
    # that was wrong, not the sizing.)
    #
    # ** THE BODY IS 45" TALL AND FLOOR-STANDING, WHICH IS THE OTHER HALF OF THE CORRECTION.
    # ** The authored 18" x 16" x 30" was a placeholder box, and 30" is a height no heater in
    # this class has: they want 22-28" of width including listed clearance to combustibles
    # and 35-47" of CLEAR SPACE ABOVE. There is no heater niche in this model and none is
    # wanted — the placeholder was the heater itself — so this is a straight body-size
    # correction. The Cilindro's own numbers: 3.94" clearance all round, 37.4" of headroom
    # above, 78" minimum ceiling. RM-B-SAUNA is 7'-6" (90") clear, so the headroom closes.
    EquipmentType(tag="EQ-T-SAUNA-HEATER", name="Electric sauna heater, 10.5 kW",
                  footprint=(inch(16), inch(15)), height=inch(45),
                  plan_symbol="sauna-heater",
                  product_ref="PROD-HARVIA-PC110E",
                  source="Harvia Cilindro PC110E, 10.5 kW at 240 V 1-phase, 43.75 A nominal, rated 141-636 cf, ETL listed, 16 x 15 x 45 in., 264 lb of stone. The Xenio CX170 control (PROD-HARVIA-CX170) is MANDATORY and mounts outside the hot room - there is no built-in-control variant of this heater.",
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
                  # AHRI 215213329 rates the MATCHED PAIR, so the same two numbers sit on
                  # the air handler and on EQ-T-GREE-FLEXX-ULTRA-24-OD below. Both are read
                  # off this type's own source note; neither is derived from the other.
                  hspf2=10.0,
                  seer2=18.0,
                  source="Gree FLEXX Ultra R32 air handler FXU24HP230V1R32AH, matched to EQ-T-GREE-FLEXX-ULTRA-24-OD. Cabinet 18 1/8 x 21 1/4 x 43 1/2 in (W x D x H as shipped), net weight 135.6 lb, laid horizontally for ceiling mount with the 18 1/8 in face vertical — the orientation that minimises soffit depth, so `height` is 18 1/8 in and the 43 1/2 in dimension is the plan long axis. Airflow to 760 cfm against an external static pressure of 1.0 in. w.c., which is what lets it drive the 750 cfm this duct system is sized to with margin; the DUC24 it replaced claimed 1030 cfm in prose and really topped out at 736 at 0.8 in. w.c. HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate (AHRI 215213329). 24 VAC thermostat terminals and a factory electric heat kit (4.6 / 5.5 / 9.2 kW) — the DUC24 had NEITHER, so EQ-S-HP1-STRIP could not physically be interlocked with the heat pump at all, which is the defect this retype closes. The indoor unit carries no heating rating of its own on purpose: the outdoor unit is what has to make heat at design temp, and mep.heating_capacity sizes the zone against the outdoor type.",
                  # Real face positions. Air crosses the cabinet the LONG way — in one
                  # 18 1/8 x 21 1/4 end and out the other — which is what the source note's
                  # "43 1/2 in H as shipped, laid horizontally" describes and what the coil
                  # and blower actually do. The ports were previously authored on the
                  # 43 1/2 x 18 1/8 faces, i.e. air crossing the 21 1/4" dimension, which
                  # contradicted the type's own note. Nothing in the engine checks port
                  # positions; this is documentation integrity, and leaving it made the plan
                  # self-contradictory under EQ-S-HP1-AH's rotation=deg(90).
                  # Local -x is supply, +x is return, both on the cabinet's centre height;
                  # power enters at the return-end top corner where the whip lands.
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(inch(21.75), inch(10.625), inch(18.125))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(inch(-21.75), ft(0), inch(9.0625))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(inch(21.75), ft(0), inch(9.0625))))),
    EquipmentType(tag="EQ-T-GREE-FLEXX-ULTRA-24-OD",
                  name="Gree FLEXX Ultra R32 outdoor unit, 24k (-22F, cold climate)",
                  footprint=(inch(39), inch(14.5625)), height=inch(37.8125),
                  plan_symbol="heat-pump-outdoor",
                  heating_capacity_btuh=24000,
                  heating_capacity_at_design_btuh=21000,
                  cooling_capacity_btuh=24000,
                  min_operating_temp_f=-22.0,
                  hspf2=10.0,
                  seer2=18.0,
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
                  # AHRI 215218915 (non-ducted). The three heads carry NO efficiency of
                  # their own for the same reason they carry no heating rating: the rating
                  # is the system's, and printing it three more times would read as four
                  # rated machines where there is one.
                  hspf2=10.0,
                  seer2=21.0,
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
                  # AHRI 214802444, the matched pair — same numbers on the outdoor unit.
                  hspf2=11.2,
                  seer2=30.0,
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
                  hspf2=11.2,
                  seer2=30.0,
                  source="Gree SAP09HP230V1R32AO, from the Sapphire R32 9 MBH 230 V submittal (AHRI 214802444): 34 3/8 x 21 27/32 x 14 51/64 in (W x H x D), net weight 78.3 lb, MCA 11 A / MOCP 15 A, SEER2 30.0, HSPF2 11.2, heating range -22 F to 86 F. The outline was 31 x 23 x 13 in until 2026-08-31 — 3 3/8 in narrow and 1 13/16 in shallow. PUBLISHED HEATING, read: 10,600 Btu/h at 47 F, 11,500 at 5 F, 8,900 at 17 F. That 17 F figure is the one the old record got worst: it carried '~11,500-13,000 Btu/h at 5F' and nothing at 17 F, which read as a machine making 12,000 in the middle of its range. It makes 8,900. ** WHICH NUMBER GOVERNS AT DESIGN, AND WHY IT IS NOT GREE'S. ** Gree's own low-ambient table gives ~9,130 Btu/h at -22 F at a 70 F return, at an implied COP of 2.62. A COP of 2.62 at -22 F is not physically plausible for a single-stage residential air-source machine — the best cold-climate units published anywhere are near 1.5 there — and the 8,200 the previous record carried was that table's 90 F-return column, which is a different measurement again. AHRI/NEEP's cold-climate listing says 7,400 Btu/h at 1.32 kW, COP 1.64, at -22 F. THIS DESIGN USES NEEP. heating_capacity_at_design_btuh is 7,400 — the -22 F read value, deliberately used unadjusted at the -15 F design temperature rather than interpolated upward, because the zone is 926 Btu/h and buying margin by interpolation would be spending credibility to gain nothing. min_operating_temp_f -22 F per the operating envelope.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # 1,500W/120V = 12.5A; x1.25 continuous = 15.6A needs a 20A breaker (not 15A). Hard-wired
    # Equipment, not a receptacle. Rated 5,118 Btu/h (1,500W x 3.412, no cold-weather derate).
    # `supplemental_heat` so it never opens its own HVAC zone — counts toward RM-M-LIVING's
    # zone (takeoff/hvac.py supplemental_heat_by_room).
    #
    # ** A REAL PRODUCT SINCE 2026-09-06: the Amantii BI-30-XTRASLIM (BI-X190030-1). ** It was
    # a generic 48" x 7" big-box cabinet; it is now the ~30" unit the owner asked for, and the
    # footprint authored here is the ROUGH OPENING (29" x 4 1/2" x 20 3/8" high), because the
    # rough opening is the hole cut in the W-M-FIRE-* brick and is therefore the thing that can
    # interfere with something. The body is 29 1/8 x 19 7/8 x 4" and the face only 3/8" wider
    # than the body.
    #
    # ** EVERY UNIT ON THE MARKET THAT IS 26-32" WIDE AND <= 6" DEEP AND HARDWIREABLE IS AN
    # AMANTII. ** That is the whole population, not a preference. Swept and ruled out: all
    # Modern Flames (nearest shallow unit 44"), Dimplex (the Multi-Fire SL Slim 36" is the
    # closest miss; the 30" Ignite Aspire is 18" DEEP), SimpliFire, Napoleon (Cineview 30 is
    # 7 3/4"), Flamerite, the 230 V British makers, and the Amazon-tier 30" units — which have
    # no hardwire procedure and no UL 2021 "fixed and location dedicated" listing.
    # ** FIELD-CONVERTING A CORD-CONNECTED APPLIANCE VOIDS ITS LISTING **, so that tier is out
    # on principle and not on price. Touchstone's Sideline 28 (80028, ~$359) is disqualified in
    # writing: manual rev 251114 p.17 says "the 80028 Sideline 28\" Electric Fireplace cannot be
    # hardwired"; the p.12 "Plug-in or Hardwire" drawing is boilerplate shared across models and
    # the model-named sentence governs.
    #
    # ** WHY THIS ONE AND NOT THE TRD-30-XTRASLIM. ** It is TRIMLESS, so the brick runs to the
    # glass edge — the entire point of a masonry surround — and it is the only unit in the
    # field with a published mantel rule. The TRD has 57% more glass but lands a 31 1/4" steel
    # flange on the brick face and demands a 10" floor clearance plus a PERMANENT AIR-INTAKE
    # SLOT CUT INTO THE MASONRY.
    #
    # ** 240 V WAS CONSIDERED AND BUYS NOTHING. ** No 26-32" unit at <= 6" depth exists in
    # 208/240 V at all: the 30"-class 240 V units are 11 5/8"-18" deep and the shallow 240 V
    # units start at 42". And 240 V is WATTAGE ONLY — Dimplex's XLF50 is the same SKU at
    # 1500 W/5118 Btu (120 V) and 2500 W/8530 Btu (240 V), SimpliFire ships one firebox with an
    # internal voltage selector, and Modern Flames' USA and 230 V manuals list identical
    # `LED 12V` and `12 VDC stepper motor` rows. The extra ~1,000-1,300 W would be resistance
    # heat at roughly 3x the heat pump's cost per Btu in a room the heat pump already serves.
    # Staying at 120 V also leaves the ServicePort POWER_120, CKT-FIREPLACE at poles=1 and
    # plan/circuits.py's whole 1,500 W / 12.5 A / 20 A justification untouched.
    #
    # ** NO ClearanceZone, AND THAT IS EARNED, NOT SKIPPED. ** A ClearanceZone is a PLAN
    # rectangle. Every clearance this unit publishes is VERTICAL — "mantel 4 inches from the
    # trim", combustible facing allowed, no floor clearance and no air slot — so any plan zone
    # authored here would be inventing a requirement the manufacturer does not state. The
    # mantel clearance is held instead by the elevation: SB-M-FIRE-MANTEL's underside at 64"
    # against the opening top at 44 3/8" is 19 5/8", about 5x the published 4". (It was
    # 11 5/8" and about 3x until 2026-09-11, when the owner reversed the sill back to 24" AFF
    # — see EQ-M-FIREPLACE below. The margin grew; nothing about this paragraph turns on it.)
    #
    # ** FOUR THINGS TO CONFIRM IN WRITING FROM AMANTII BEFORE FRAMING: ** (1) the mantel
    # PROJECTION the 4" is quoted at — unpublished industry-wide; ask specifically whether 4"
    # holds for a solid walnut shelf projecting 7-8". (2) Bottom, side and back combustible
    # clearances, which the manual simply omits. (3) That the left-side L/N/G junction block
    # stays serviceable through the glass opening once the unit is bricked in. (4) ** That the
    # unit ships with the 2022 CSA manual revision ** — the older manual under the same model
    # number says 1465 W / 5000 Btu and has NO mantel and NO hardwire section at all, i.e. an
    # inspector would find no permission to hardwire it. Note the Panorama warranty excludes
    # tray, front and back glass; and beware HVACDirect, which labels the APPLIANCE dimensions
    # "Framing Dimensions" (framing to those is too small) and sells a "BI-30-XTRASLIM-LUMINA"
    # at 110 lb that Amantii does not list — the manual weight is 50.7 lb.
    #
    # ** ON LOOKS, HONESTLY: no reliable evidence distinguishes any of these at 9-10 ft. **
    # Every "most realistic flame" page in this category is a retailer or an affiliate and none
    # addresses viewing distance. What IS verifiable is that neither Amantii publishes
    # anti-glare or low-iron glass — both are plain clear tempered and BOTH WILL MIRROR THE TWO
    # WINDOWS FLANKING THEM. Here glare is solved by the brick reveal and the mantel's shadow,
    # not by model choice. (The one glossy-LCD shallow unit with a verified owner glare
    # complaint, Modern Flames' HelioVision, starts at 52" and never reaches this decision.)
    EquipmentType(tag="EQ-T-FIREPLACE-EL",
                  name="Amantii BI-30-XTRASLIM electric fireplace, 1.5 kW built-in",
                  footprint=(inch(29), inch(4.5)), height=inch(20.375),
                  heating_capacity_btuh=5118, heating_capacity_at_design_btuh=5118,
                  supplemental_heat=True,
                  source="Amantii BI-30-XTRASLIM (BI-X190030-1), Panorama built-in series, from the 2022 CSA-revision installation manual: rough opening 29 x 20 3/8 x 4 1/2 in, appliance 29 1/8 x 19 7/8 x 4 in, trimless face 3/8 in wider than the body, viewing glass 25 1/4 x 11 7/8 in (300 sq in), 50.7 lb. Electrical 120 V, 1500 W, 5118 Btu/h, 12.5 A, dedicated 15 A circuit preferred (this house gives it a 20 A — see plan/circuits.py); HARDWIREABLE via an L/N/G block on the left side. Clearances: mantel 4 in from the trim, combustible facing allowed, no floor clearance and no air-intake slot. $1,499-1,539. Chosen because it is the only trimless unit in the 26-32 in x <= 6 in deep hardwireable field, which is entirely Amantii; the alternative TRD-30-XTRASLIM lands a 31 1/4 in steel flange on the brick and wants a permanent air slot cut into it. Replaced a generic 48 x 7 in 1.5 kW big-box insert on 2026-09-06",
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
    # On the sauna's SOUTH liner immediately WEST of EQ-B-SAUNA-HTR, low like the heater
    # terminals. It followed the heater onto the garden wall when the room rotated on
    # 2026-09-05, into the south-east corner when the room shrank, and 2'-0" further east
    # (x 15'-5 3/4"..15'-11 3/4") when the heater turned onto the east liner: it butts the
    # heater's west face, which is what "immediately west" has meant throughout.
    #
    # ** IT STAYS LOW AND IT STAYS OUT OF THE BENCH. ** 18" is the box's BASE, exactly
    # FURN-B-SAUNA-BENCH-SW's top, so the bench stops 7 15/16" short of it rather than
    # running under it. Raising the box over the bench would buy that back and is the wrong
    # trade in a room that stratifies: a junction box belongs in the coolest air there is.
    ElectricalDevice(uid="CEE005AAAA", tag="ED-B-SAUNA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(inch(188.75), inch(12.5)), type_ref="ED-T-SAUNA-JB",
                     circuit="CKT-SAUNA", rotation=deg(0),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
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
    # RM-B-BATH's NEC 210.52(D) receptacle: GFCI within 3'-0" of the basin's edge (1'-9"
    # here), on W-B-STR2's bath face at x=10'-3 3/8" — beside the vanity across the room's
    # short dimension, with no wall between plate and basin. Rides CKT-RC-BSMT rather than
    # its own 20A circuit (the panel-slot trade recorded in plans/TODO.md's panel_spaces
    # item).
    ElectricalDevice(uid="CEE040AAAA", tag="ED-B-BATH-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(124.375), ft(19, 3)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-BSMT", room="RM-B-BATH", rotation=deg(90),
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
    # Sauna heater: back to the SOUTH liner at x 8'-6"..10'-0", 2" off the face, diagonally
    # opposite the shower pan in the room's north-east corner and 2'-1" west of
    # WIN-B-SAUNA's west jamb. It moved onto the garden wall with the room on 2026-09-05.
    # EQ-B-HP2-GYM (System 2's basement head). ** MOVED TO THE GYM'S SOUTH WALL BY A UI DRAG
    # AND KEPT THERE (2026-09-05). ** The comment here said "high on the centre bearing
    # wall's east face at x=18', backs west, throws east across the gym" and had been wrong
    # since the drag: it is on W-B-S3-FR, the framed walkout, at x=26'-5", backing SOUTH and
    # throwing north across the room. That is the better wall — a 32 7/8" cabinet on the
    # centre line sat between D-B-GYM and D-B-SAUNA, and the long throw is now across the
    # room's 18' depth rather than its width. y=10 9/16" puts its back on the wall's gwb
    # face at 6 5/8"; `rotation=deg(0)` aims the discharge at -y, which is into the wall, so
    # the louvre throws off the coil face at +y. zone_rooms is the whole conditioned
    # basement (one open volume off the stair) — EQ-B-SAUNA-HTR heats the sauna, not space.
    #
    # ** THE HEAD WAS 5 1/2" INTO THE CEILING AND THAT WAS NOT THE DRAG'S DOING. ** The mount
    # was authored at 7'-6" AFF and this is a 10 53/64" cabinet, so its top stood at 100 13/16"
    # in a room whose ceiling `code.R305_ceiling_height` measures at 7'-11 3/8" (95 3/8").
    # It read as "high on the wall" and was through the deck; the same numbers held on the
    # centre wall it came off, so this is a pre-existing error the move surfaced rather than
    # caused. 6'-6" puts the top at 88 13/16" with 6 9/16" of clear above it, which is the
    # air Gree's Multi R32 wall-mount installation wants over the cabinet.
    Equipment(uid="CEE031AAAA", tag="EQ-B-HP2-GYM", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(m(7.83384), m(0.278247)), footprint=(inch(32), inch(8)),
              room="RM-B-GYM", type_ref="EQ-T-GREE-HEAD-9", rotation=deg(0),
              outdoor_ref="EQ-M-HP2-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
              zone_rooms=("RM-B-GYM", "RM-B-PLAY-N", "RM-B-STAIR", "RM-B-WORKSHOP",
                          "RM-B-SAUNA", "RM-B-FURNACE", "RM-B-BATH")),
    # ** ON THE EAST LINER SINCE 2026-09-05 (round three), AND IT TURNED TO GET THERE. **
    # It stood on the SOUTH liner at x 14'-5 3/4"..15'-11 3/4" from the shrink until the
    # south bench grew: with the heater in the middle of that wall the bench could be 2'-6"
    # and no longer. Against the east liner instead — `rotation=deg(270)` turns the 18"
    # face to the wall and the 16" depth into the room, since local -y is a placeable's
    # front — it takes x 15'-11 3/4"..17'-3 3/4" by y 0'-11 1/2"..2'-5 1/2" and hands the
    # whole middle of the south liner back. The bench went 2'-6" -> 4'-0" on it
    # (plan/placeables.py).
    #
    # 2" off the east liner and 2" off the south, the same stand-off it always carried.
    # **It is deliberately NOT pushed north against D-B-SAUNA's jamb**, which would free
    # another foot and a half of bench: that puts a 30" stove at the doorway you walk past
    # in the dark, and nothing in this engine grades clearance to a sauna heater —
    # `EquipmentType` carries no `clearances` at all.
    #
    # Clear of everything, and every one of these gaps is hand-held: 1'-1 15/16" to the
    # south bench's east end, 8 1/4" north to D-B-SAUNA's leaf (y 3'-1 11/16"..5'-1 11/16"),
    # and 4'-3 11/16" to FX-B-SAUNA-SH's pan.
    Equipment(uid="CEE020AAAA", tag="EQ-B-SAUNA-HTR", kind=EquipmentKind.SAUNA_HEATER,
              position=pt(inch(199.75), inch(20.5)), footprint=(inch(18), inch(16)),
              room="RM-B-SAUNA", type_ref="EQ-T-SAUNA-HEATER", rotation=deg(270),
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
                     position=pt(m(3.33058), m(5.53486)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-LAUNDRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(43),
                                 recessed_into_host_surface=True), room="RM-M-LAUNDRY"),
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
    #   * NEC 110.26(A) working space cannot be a stairway, and ST-SG-PORCH ran straight
    #     under the old x=30' station while the flight was in the pocket's north strip.
    #   * NEC 404.8(A) caps an operating handle at 6'-7" above the standing surface. These
    #     are on a MAIN-floor wall but are operated from grade at -2'-10", so ft(5) put the
    #     handles 7'-10" up — nearly a foot past the limit, and nothing was measuring it
    #     because the mount elevation is storey-relative. 3'-6" reads 6'-4" from grade.
    #
    # ** AND THEY LEFT THE HOUSE ALTOGETHER ON 2026-09-04. ** They went to W-SG-E1's EAST
    # face, at (28'-7 5/8", -3'-6") and (28'-7 5/8", -4'-6"), 1 5/8" off the concrete for
    # the can's 3 1/4" depth and turned `deg(90)` so the depth runs in x against an east face
    # (the ED-M-LIVING-KFZ1 convention). HP1's can then followed its unit to the north face
    # later the same day (see its own block below); ED-M-HP2-DISC is the one that stayed,
    # and everything argued here is now argued for it alone.
    #
    # **The row is what evicted them, and 110.26(A)(3) is why there was no appeal.** With the
    # condensers tucked against the house from x 29'-0" to 36'-7" — the owner's call on
    # 2026-09-04, buying a quieter east side yard at the price of a louder living room —
    # W-M-S2's exterior face is cabinet from the porch wall to past the corner, and the 6"
    # left at x 28'-6"..29'-0" is not the 30" 110.26(A)(2) wants. Height does not rescue it:
    # (A)(3) measures the clear space **from the grade up**, so a 3'-4" cabinet standing 6"
    # off the wall consumes the whole working space however high the handle is hung.
    #
    # ** THE 42" BETWEEN THE CABINETS AND THE FLIGHT IS THE ONLY PLACE LEFT, AND IT FITS. **
    # W-SG-E1's east face is clear from HP2's south face at y -2'-6" to ST-SG-PORCH's north
    # side at -6'-0". Two 12" cans at -3'-6" and -4'-6" are 24" of equipment; the 30" space
    # they share spans y -3'-0"..-5'-6", which leaves 6" to the cabinets and 6" to the stair,
    # over 36" of depth (x 28'-6"..31'-6") with nothing in it. Within sight of both units,
    # 1'-9" away — 440.14 asks for sight, and here it is nearly reach as well.
    #
    # ** THE MOUNT DROPS TO -0'-8", AND ACCESS IS FINE. ** This wall tops out at 0'-0", so
    # there is no 3'-6" to hang from; -0'-8" puts the handles 2'-2" above grade, against
    # 404.8(A)'s 6'-7" ceiling and well inside it. Readily accessible standing on the pocket
    # grade beside the units, which is the access 440.14 turns on, and reachable a second way
    # over the porch guard from the deck 8" above them (owner, 2026-09-04) — a convenience,
    # not the compliance path.
    #
    # What the low mount does cost is exposure: these 3R cans now sit in the splash and the
    # plough line where the W-M-S2 position had them at 6'-4" and dry. Specify them
    # stainless-hinged and gasketed, and take the knockouts on the BOTTOM so nothing drains
    # into the enclosure.
    #
    # ED-T-DISCONNECT-3R is a 3 1/4"-deep can, so its centre belongs 1 5/8" off the
    # cladding face. Same correction on ED-M-HP3-DISC below and on ED-B-SPA-DISC.
    #
    # These were on the SECOND storey until 2026-09-02, beside condensers that stood on the
    # balcony (notes/heat_pump_ground_pad.md). The units came down; the disconnects came
    # down with them, because a disconnect one storey above the machine it kills is not
    # within sight of it in any sense 440.14 means.
    # ** ED-M-HP1-DISC LEFT THIS WALL WITH ITS UNIT (2026-09-04, later the same day). **
    # Everything above is now HP2's story alone; only ED-M-HP2-DISC stays on W-SG-E1.
    # HP1's can goes to the house's NORTH face beside its own cabinet, at (32'-5",
    # 36'-8 7/8") — 1 5/8" off the cladding for the can's 3 1/4" depth, and with NO
    # `rotation`, because a north face wants the depth in y where the pocket's east face
    # wanted it in x.
    # elevation 3'-6" reads 6'-4" above the -2'-10" grade it is operated from — inside NEC
    # 404.8(A)'s 6'-7" — and it is dry, at standing height, not in the plough line.
    #
    # ** IT MOVED 32'-0" -> 32'-5" ON 2026-09-07 BECAUSE ITS CABINET LANDED ON IT. ** The
    # old station sat in the clear band 30'-7 1/2"..33'-3" between WIN-M-KITCH's framing
    # bumper and the next opening's; EQ-M-HP1-OD now occupies x 33'-0"..36'-3" — hard against
    # the house's NE corner — so the can went WEST of the machine instead of east, into the
    # 14" band between the garage's east gutter line (31'-10") and the cabinet. A 6 1/2" can
    # centred at 32'-5" spans 32'-1 3/4"..32'-8 1/4": 3 3/4" clear each side, and clear of
    # both WIN-M-KITCH's RO (28'-2 1/2"..30'-5 1/2") and WIN-M-KITCH-N's (33'-5"..34'-7").
    #
    # ** IT IS A 6 1/2" CAN IN A 14" SLOT AND IT HAS NO NEC 110.26 WORKING SPACE TO SPEAK
    # OF. ** Nothing in this engine grades that. It is the accepted cost of centring the
    # garage on the house ridge, recorded here rather than papered over, and it is a hard
    # bound: the cabinet cannot move west (the gutter) or east (the corner), so this can has
    # nowhere better on this face. If the working space is wanted back, the answer is to
    # move EQ-M-HP1-OD off the north face entirely, not to shuffle this box.
    ElectricalDevice(uid="CEE012AAAA", tag="ED-M-HP1-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(32, 5), ft(36, 8.875)),
                     type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP1", room=None,
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
    ElectricalDevice(uid="CEE013AAAA", tag="ED-M-HP2-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(28, 7.625), ft(-4, -6)), rotation=deg(90),
                     type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP2", room=None,
                     mount=Mount(kind=MountKind.WALL, elevation=ft(0, -8))),
    # HP3's west-yard position puts this disconnect beside the cabinet, with a 30" clear
    # working band x=3'-1"..5'-7" between its pad and the connector screen. The 3'-6"
    # main-relative mount is 6'-4" above grade. CKT-HP3 remains on the backup supply.
    ElectricalDevice(uid="CEE026AAAA", tag="ED-M-HP3-DISC", kind=DeviceKind.DISCONNECT,
                     position=pt(ft(4, 4), ft(36, 8.875)), type_ref="ED-T-DISCONNECT-3R", circuit="CKT-HP3",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6))),
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
    # nearest real wall — east wall interior face x=35'-5 3/8" (EXT_2X6's inside face
    # is 6 5/8" in from the 36' sheathing plane). ** WIN-M-DIN-E2 IS GONE, AND THE STRETCH IT
    # NAMED WITH IT. ** It was retired 2026-08-24 with the old WIN-M-LIV-E2 and replaced by
    # WIN-M-EAST-MID at y=18'-8" (plan/storeys/main.py), so the "5'-1" clear stretch between
    # WIN-M-LIV-E2 and WIN-M-DIN-E2" this comment used to describe has not existed for two
    # weeks. The real clear stretch is now y 14'-5 1/2"..17'-6 1/2", 3'-1" of it.
    #
    # ** MOVED 17'-9" -> 16'-0" (2026-09-06). ** At y=17'-9" it stood 2 1/2" INSIDE
    # WIN-M-EAST-MID's rough opening (y 17'-6 1/2"..19'-10 1/2"), at 48" between that
    # window's 32" sill and 80" head — a device specified in a hole. y=16'-0" centres it in
    # the pier the corrected sentence above names: 16 1/2" of clear wall to WIN-M-LIV-E2's
    # RO end (y=14'-5 1/2") and 16 1/2" to WIN-M-EAST-MID's RO start (y=17'-6 1/2"), the
    # 37" pier taken dead centre. Clear of ED-M-LIVING-RC3 (y=16'-11 1/8") by 11" in plan
    # and 12" in elevation, and 48" clears the BESTA run's 29 3/4" tops the whole way.
    # ** NOTHING IN `haus check` ASKED FOR THIS AND NOTHING WILL VERIFY IT: ** no rule
    # grades a wall device against an opening, which is why the defect survived two weeks
    # of clean reports. Re-measure by hand if either east window moves.
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
                     position=pt(ft(35, 4.375), ft(16)), type_ref="ED-T-FLOOR-STAT",
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
    # ** THEY FACE SOUTH, SIDE BY SIDE, ALONG THE HOUSE (2026-09-04). ** They stood in a
    # north-south row against the porch wall facing EAST until 2026-09-03, then for one day
    # in an east-west row across the pocket's SOUTH half. Both earlier layouts are dead for
    # the same reason: ST-SG-PORCH springs from W-SG-E1's top, that top is walkable only
    # between its two 12" round columns (y -9'-9"..-3'-0"), and a row anywhere in the
    # pocket's south half stands inside exactly that window.
    #
    # So the row and the flight swapped halves. `rotation=deg(0)` is unchanged and still
    # right — the long axis runs in x, both discharge faces read SOUTH into open yard rather
    # than east into the pocket's own faces (which returned it up at WIN-M-LIV-S1 and
    # WIN-S-STUDY2) — and the whole change is the two centres.
    #
    # ** WHAT THE SWAP COSTS AND WHAT IT BUYS. ** It buys the flight: 3'-8" of clear yard
    # between HP2's discharge face and the stair's north rail, against a published 24", and
    # HP1's 40" zone is east of the flight entirely. It buys the line sets, which now run
    # 1'-6" north into the band penetration instead of 5' west along a pad. It costs the
    # backs: both cabinets sit at 6" off the cladding — HP2's published minimum, HP1's is 4"
    # — directly under WIN-M-LIV-S1, which is the objection that ruled a row here out on
    # 2026-09-02 and is now simply taken. It is a sound judgement, not a code one, and
    # notes/heat_pump_ground_pad.md argues it rather than burying it.
    #
    # ** THE ROW IS TUCKED AS FAR WEST AS IT GOES (owner, 2026-09-04). ** It sat at x 31'-0"
    # for part of that day, which left a 30" band of house wall for the disconnects and put
    # HP1's east end 2'-10" past the SE corner. The owner traded it: tucking the row behind
    # the corner shadows the whole east side yard with the house's own mass, at the price of
    # a noisier living room, and that is the elevation people stand on. **It cannot tuck all
    # the way** — 40 5/32" + 12" + 39" is 7'-7 1/6" and the porch wall to the corner is
    # 7'-6" — so HP1 still oversails by 7 1/6", with 19'-5" to the setback beyond it.
    #
    # Two figures are now at their minimum and neither cabinet moves in x alone: the 12"
    # service gap between them, and HP2's 6" to W-SG-E1. The eight stand legs in
    # params/sunken_garden.py are derived from these centres and move with them.
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
    # ** SYSTEM 1'S UNIT LEFT THE POCKET ON 2026-09-04 AND STANDS ON THE NORTH FACE. **
    # It follows its air handler, which moved to SF-S-HP1 over RM-S-NCLOSET at the north end
    # of the second storey; the whole argument is in `params/hp1_north_pad.py`, which carries
    # SL-M-HP1PAD, PT-M-HP1-L1..4 and CN-M-HP1-A1..4. The centre here and the centre there
    # are the same literal, written twice on purpose — the two files cannot import each
    # other — and `test_catlin_outdoor_structures.py` holds them together.
    #
    # `rotation=deg(180)` faces the discharge NORTH, away from the wall. All four clearances
    # are better than the south row's: back (S) 6" against the published 4"; discharge (N)
    # 40" into open front yard; far end (W) 14" to the garage's east gutter face.
    #
    # ** IT WENT 6'-6" EAST ON 2026-09-07 (x 28'-1 1/2" -> 34'-7 1/2"). ** The garage moved
    # 6'-0" east onto the house ridge and its own ridge turned, so the edge west of this
    # cabinet stopped being a rake at x=25'-4" and became an EAVE with a gutter, face at
    # 31'-10". 6'-6" is the smallest move that gives the 14" far-end clear back; the whole
    # argument, including why it oversails the NE corner by 3" rather than giving up 3" of
    # airflow clearance, is in params/hp1_north_pad.py, which moved with it.
    #
    # ** THE SERVICE SIDE IS GONE AS A NUMBER: 23 3/4" -> the open yard past the corner. **
    # The cabinet's east face is at the house's NE corner, so the service side is unbounded
    # by anything but the sky. `ED-M-HP1-DISC` moved to the WEST side, into the 14" band
    # between the gutter line and the cabinet (its own note below). That is the honest cost
    # of the garage move on this face.
    #
    # `mount.elevation` is UNCHANGED at -14": the pad tops out at the same -2'-8" under the
    # same 18" stand, so all three cabinets keep one base plane at -1'-2".
    Equipment(uid="CEE017AAAA", tag="EQ-M-HP1-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(34, 7.5), ft(37, 8.53125)), footprint=(inch(39), inch(14.5625)),
              rotation=deg(180), mount=Mount(kind=MountKind.FLOOR, elevation=inch(-14)),
              type_ref="EQ-T-GREE-FLEXX-ULTRA-24-OD", circuit="CKT-HP1", room=None),
    Equipment(uid="CEE018AAAA", tag="EQ-M-HP2-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(30, 8.08), ft(-1, -9.655)), footprint=(inch(40.16), inch(16.81)),
              rotation=deg(0), mount=Mount(kind=MountKind.FLOOR, elevation=inch(-14)),
              type_ref="EQ-T-GREE-MULTI-U30", circuit="CKT-HP2", room=None),
    # HP3 is west of the connector roof/screen, discharging NORTH into open yard.
    # Rear clearance is 12" to north cladding; cabinet x=0..2'-10 3/8". Pad and 18" stand
    # are in params/hp3_pad.py. Their shared base remains -1'-2" (20" above site grade).
    # The former straight lineset punch is replaced by a high-level wall-supported dogleg
    # above the entry, then a drop west of the screen; notes/hp3_north_relocation.md gives
    # its route. Refrigerant geometry is not an engine element; outdoor_ref preserves the
    # connection to the indoor head. Defrost drains to the west-yard gravel, off the walk.
    Equipment(uid="CEE027AAAA", tag="EQ-M-HP3-OD", kind=EquipmentKind.HEAT_PUMP,
              position=pt(ft(1, 5.1875), ft(38, 2.6484375)),
              footprint=(inch(34.375), inch(14.796875)), rotation=deg(180),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(-14)),
              type_ref="EQ-T-GREE-SAPPHIRE-9-OD", circuit="CKT-HP3", room=None),
    # --- System 2's main-floor heads: high on the south wall either side of the centre wall
    # at x=18', backs south, blowing north. Neither carries `circuit` — power comes off the
    # multi's outdoor unit (CKT-HP2 feeds EQ-M-HP2-OD, interconnects run from there).
    #
    # ** y MOVED 0'-6" -> 0'-11 1/8" ON 2026-09-06, AND IT IS A CORRECTION. ** W-M-S2's
    # interior face is y=6 5/8" (EXT_2X6 aligned on the 0'-0" sheathing plane), and a
    # 9" body centred at y=6" spans y 1 1/2"..10 1/2" — ** 5 1/8" of both heads was drawn
    # inside the studs. ** 6 5/8" + 4 1/2" puts each case's BACK on the finish face, which is
    # where a surface-mounted head hangs. Nothing grades this: the wall-face test in
    # `test_catlin_contract_m3.py` walks ElectricalDevices only, so Equipment floats or buries
    # in silence. Same class of error as the fireplace's own 35'-11 3/8" erratum below, found
    # and fixed in the same pass.
    Equipment(uid="CEE028AAAA", tag="EQ-M-HP2-BED", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(16), ft(0, 11.125)), footprint=(inch(35), inch(9)),
              room="RM-M-BED", type_ref="EQ-T-GREE-HEAD-12", rotation=deg(180),
              outdoor_ref="EQ-M-HP2-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6)),
              # The west half of the main floor: the suite bedroom and everything off it.
              zone_rooms=("RM-M-BED", "RM-M-BATH1", "RM-M-BATH2", "RM-M-CLOSET",
                          "RM-M-LAUNDRY", "RM-M-STUDY")),
    Equipment(uid="CEE029AAAA", tag="EQ-M-HP2-LIVING", kind=EquipmentKind.INDOOR_HEAD,
              position=pt(ft(20), ft(0, 11.125)), footprint=(inch(35), inch(9)),
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
              position=pt(m(3.66415), m(10.6761)), footprint=(inch(33), inch(8)),
              room="RM-M-LIVING", type_ref="EQ-T-GREE-SAPPHIRE-9", rotation=deg(0),
              outdoor_ref="EQ-M-HP3-OD",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              zone_rooms=("RM-M-MUDROOM", "RM-M-MECH")),
    # --- the fire, moved out of the SE corner 2026-09-06 --------------------------------
    #
    # ** IT WAS TOO LOW, NOTHING FACED IT, AND IT COULD NOT BE RAISED WHERE IT STOOD. **
    # (READ THE ELEVATION PARAGRAPH BELOW BEFORE THIS ONE: the owner reversed the height half
    # of this argument on 2026-09-11 and the sill is back at 24" AFF. The MOVE, which is what
    # this paragraph is really about, stands.) In the
    # SE corner the 7" mount existed precisely to duck under WIN-M-LIV-E1's rough opening,
    # which sits directly over it — so the flame sat a foot below the seated eye and there was
    # no lifting it in place. `plans/pattern_language_review.md` C9/C10 asked for it at seated
    # eye level, reading as fire at 11 feet, with a dark surround and the seats turned onto it.
    #
    # It now sits in the pier between WIN-M-LIV-E1 and WIN-M-LIV-E2, centred on y=8'-8", in a
    # 45 1/2" white-facebrick surround stopping at a walnut mantel — W-M-FIRE-* in
    # plan/storeys/main.py carries the pier arithmetic and the whole elevation ladder, and
    # SB-M-FIRE-MANTEL in plan/millwork.py is the shelf. The BESTA run was re-laid about it
    # (all eight kept) and the seating turned onto it (plan/placeables.py).
    #
    # ** POSITION. ** x=35'-1 7/8" stands the 4 1/2"-deep body's FACE 1/4" PROUD of the brick
    # at x=34'-11 5/8", with its back at 35'-4 1/8" — 5/8" through the wythe's back face and
    # into the 1 7/8" of framing behind it, which is where a 4 1/2" appliance in a 3 5/8"
    # wythe has to go. ** The 1/4" is a real dimension, not a drafting fudge. ** The
    # XtraSlim is TRIMLESS and its face is published 3/8" wider than the body: there is a
    # thin face flange that laps whatever the finish is, so on brick the glass plane sits
    # proud of the brick plane by about the flange, not flush with it. Flush was authored
    # first and it was wrong twice over — wrong about the product, and it put two coplanar
    # faces in the viewer, which z-fights and reads as a torn hole in the surround.
    # y=8'-8" is the pier centre.
    #
    # ** HOW IT ACTUALLY SITS IN THE WYTHE, measured off the resolved bodies. ** The jambs are
    # 8" of brick each side — ONE WHOLE BRICK AND ONE HEAD JOINT (7 5/8" + 3/8"), ZERO CUT
    # CLOSERS. The masonry opening is 29 1/2" and 45 1/2" less 29 1/2" is 16", exactly two
    # modules. W-M-FIRE-JAMB-S/-N are authored at that 8" (plan/storeys/main.py).
    #
    # ** ERRATUM (2026-09-06). ** This paragraph used to say "8 1/4" of brick as a jamb… a fat
    # head joint or a lightly cut closer, every course". That measured to the APPLIANCE's 29",
    # not to the masonry opening, and it contradicted the whole reason the panel is 45 1/2" —
    # `plan/storeys/main.py`'s derivation of 29 1/2" + 8" + 8", whose entire point is that no
    # closer is cut anywhere on this panel. Nothing was ever wrong but the sentence.
    #
    # The opening's HEAD is a cut course and that one IS unavoidable: 44 5/8" AFF is 16.7
    # courses of 2 2/3", so the brick is CUT along the head. That is normal for a trimless
    # unit — the brick is being cut to the opening anyway, there being no flange to hide a
    # joint under — and it is why the lintel here is a steel angle rather than a rowlock.
    # Below the opening the coursing is exact: 24" AFF is 9 courses off the floor line.
    #
    # ** THE DATUM, ESTABLISHED RATHER THAN ASSUMED (2026-09-11). ** `Mount.elevation` is
    # measured from the ROOM'S FINISHED FLOOR, not the subfloor. `resolve/placeables.py`'s
    # `_floor_elevation` returns `room_finished_floor_elevation(...)` and hands it to
    # `resolved_mount_elevation` as `floor_m`, which adds the mount to it. RM-M-LIVING's
    # finished floor is +15/16", so an authored 24" resolves to 24 15/16" absolute — which is
    # exactly W-M-FIRE-PLINTH's top, the brick sill, to the thousandth. That agreement is the
    # check on the claim, and the resolved model confirms it: `canvas_objects` carries this
    # unit at z=0.8366125 m = 32 15/16" absolute at the old authored 32". ** THE COMMENT ON
    # FURN-M-FIRE-MANTEL IN plan/placeables.py STILL SAYS THE DATUM IS THE FRAMING FLOOR AND
    # IT IS NOW WRONG ** — that was true when it was written and stopped being true when the
    # finished-floor plane landed; the mantel, authored 64 15/16" against that reading, now
    # resolves to 65 7/8" absolute and floats 15/16" OFF the top of W-M-FIRE-HEAD. Reported,
    # not fixed here: that file is not this change's to edit.
    #
    # ** THE SILL IS BACK AT 24" AFF, AND THIS PARAGRAPH USED TO ARGUE THE OPPOSITE. ** It read:
    # "`elevation` is the BASE of the opening at 32" — the east row's own sill line, so one
    # datum serves four openings — which puts the opening top at 52 3/8" and the flame centre
    # at 42 3/16" against a seated eye of ~46-48". That is a 14" RISE on the old unit's 28"
    # top." Every number in it was right. The owner has seen it built to that height and
    # REVERSED IT on 2026-09-11: 32" reads as a picture hung on a wall rather than as a
    # hearth, and 32" of blank plinth under a 20 5/8" hole makes the 45 1/2" panel top-heavy.
    # What the reversal costs is stated plainly: the opening top drops to 44 3/8" AFF and the
    # flame centre to 34 3/16", which is ~12" BELOW a seated eye rather than ~5" below it, and
    # the shared sill line with WIN-M-LIV-E1/-E2 at 32" is given up — the fire no longer
    # datums with the east window row. ** THAT IS A PREFERENCE DECISION OVERRULING A DESIGN
    # ARGUMENT, NOT A CORRECTION OF ONE, ** and nothing in `haus check` grades it either way
    # (`checks/code/mn_residential/profile.py` disclaims IRC R1001-R1004). Do not "restore"
    # 32" off the strength of the quoted sentences without asking the owner.
    #
    # The MOVE out of the SE corner stands on its own and is untouched by the reversal: there
    # the 7" mount was ducking WIN-M-LIV-E1's rough opening directly above it, so 28" was a
    # ceiling and not a choice. Here 24" is a choice, and 32" remains available.
    #
    # rotation -90 backs it to the wall and opens it west into the room.
    #
    # ** `recessed_into_host_surface=True` IS THE HONEST FLAG AND IT MATTERS. ** The body is
    # let INTO the W-M-FIRE-* brick, not stood in front of it, so its 4 1/2" of depth is a cavity
    # behind the face rather than a protrusion into the room — which is what
    # `resolve/placeable_clear_floor_obstruction` needs to know. Without it the model reads a
    # 29" x 4 1/2" box lapping 105 sq in of the wythe, i.e. two solids in the same air, and
    # nothing in `haus check` catches that on its own.
    #
    # ** ERRATUM, AND IT PREDATES THIS CHANGE: the east wall's interior face is 35'-5 3/8",
    # NOT 35'-11 3/8". ** The comment this replaces claimed the latter — the gwb had been
    # subtracted from the wrong side — and `electrical.py`'s own FH-M-DINING note,
    # plan/placeables.py and plan/millwork.py all say 35'-5 3/8". The consequence was live: the
    # old unit at x=35'-8" with a 7" body had its BACK at 35'-11 1/2", so ** the fireplace has
    # been buried 6 1/8" inside the studs for as long as that comment has existed. **
    Equipment(uid="CEE022AAAA", tag="EQ-M-FIREPLACE", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(35, 1.875), ft(8, 8)), footprint=(inch(29), inch(4.5)),
              room="RM-M-LIVING", type_ref="EQ-T-FIREPLACE-EL", rotation=deg(-90),
              circuit="CKT-FIREPLACE",
              mount=Mount(kind=MountKind.WALL, elevation=inch(24),
                          recessed_into_host_surface=True)),
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
    # ** RM-S-SUITEBATH AND RM-S-VANITY EACH GET THIS RECEPTACLE FOR NEC 210.52(D). ** Both
    # were authored when nothing in the engine encoded E3901.6, so the note here used to
    # say the gap was one "the engine cannot see". ** THAT IS NO LONGER TRUE (checked
    # 2026-09-06): ** checks/mep/electrical_receptacles.py implements the rule and
    # code.E3901_6_bathroom_receptacle now PASSES both bowls of RM-S-VANITY off
    # ED-S-VANITY-RC1 below, and every other lavatory in the house besides. The outlets
    # stay for the reason they were always right; only the claim that nothing grades them
    # is retired.
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
    # System 1's concealed ducted AH — inside SF-S-HP1, the box that IS the ceiling of
    # RM-S-NCLOSET and the north end of RM-S-HALL (plan/storeys/second.py). It moved here
    # from RM-S-STUDY2 on 2026-09-04. Own branch circuit (CKT-HP1-AH) since a ducted unit's
    # blower is fed at the unit, unlike a multi's heads.
    #
    # `soffit_ref` is load-bearing: WITHOUT it a CEILING mount with no stated elevation
    # hangs off `storey.default_ceiling_height` (resolve/placeables.py), which puts this
    # unit at 9'-0", above the box it lives in.
    #
    # ** rotation=deg(90), NOT a hand-swapped `footprint`. ** The type states (43.5, 21.25);
    # `_transformed_polygon` rotates the catalogued case, so the 43 1/2" runs ALONG the box
    # (y) where there is 7'-9", and only the 21 1/4" case depth competes for the box's
    # 36.50" clear width. Hand-swapping the footprint would have left the type and the
    # instance disagreeing about which dimension is which.
    #
    # ** x = 19'-6" IS FORCED, NOT PREFERRED. ** Three constraints intersect at one 1 3/8"
    # band: DU-S-HP-SUITE's tee bounds the cabinet centre to [229, 235], SF-S-DUCT's cavity
    # to [233.625, 246.375], and the discharge face to within 1 5/8" of the cabinet centre.
    # The intersection is [233.625, 235] and 19'-6" = 234 sits in it.
    #
    # (19'-6", 32'-2 1/4") puts the case at y 30'-4 1/2"..34'-0" and x 18'-11 3/8"..20'-0 5/8".
    # y=30'-4 1/2" is DU-S-HP-SUP's start (supply, running SOUTH now); y=34'-0" is
    # DU-S-HP-RET's end. The lanes across the box are 1 7/8 | cabinet 21 1/4 | 2 3/8 |
    # return 10 | 1 against 36.50" clear; the check prints them, so they are not restated.
    #
    # zone_rooms covers the whole conditioned second storey plus RM-A-STUDY/RM-A-EAST-UNFIN
    # (short attic branches) and RM-A-STUDIO/RM-A-STUBATH/RM-A-POCKET — the three rooms the
    # west loft split into, all conditioned by the one boot REG-A-HP-WEST on the suite
    # branch. Dropping any of the three from this list would report it as unheated.
    Equipment(uid="CEE032AAAA", tag="EQ-S-HP1-AH",
              kind=EquipmentKind.DUCTED_AIR_HANDLER,
              position=pt(ft(19, 6), inch(386.25)), footprint=(inch(43.5), inch(21.25)),
              rotation=deg(90),
              room="RM-S-NCLOSET", type_ref="EQ-T-GREE-FLEXX-ULTRA-24-AH",
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
    # that lands in the cabinet's discharge — hence `soffit_ref` is SF-S-HP1. With the
    # machine turned and the trunk running SOUTH, the discharge is the cabinet's SOUTH face
    # at y=30'-4 1/2", so the plate sits at (19'-6", 29'-11 1/2"): its north edge flush on
    # that face, on the trunk's own centreline, upstream of DU-S-HP-SUP's start.
    # Across the box it is 16" against 36.50" clear with the 10" return beside it —
    # 16 + 2 + 10 = 28.00, 8 1/2" spare — so it is nowhere near the graded pair.
    # It is also DOWNSTREAM of EQ-S-ERV-MIX, which is on the return at the box's south end:
    # fresh air mixes across the whole 6'-7" return before the coil, then gets heated.
    #
    # `room` follows the box: RM-S-HALL, the room the discharge end of SF-S-HP1 hangs in
    # (the cabinet itself is filed under RM-S-NCLOSET at the north end). It changes nothing
    # about the credit — `supplemental_heat_by_room` keys on the room and both rooms are in
    # the same EQ-S-HP1-AH zone_rooms list — and it is where the part is.
    #
    # ITS JOB CHANGED TOO, and that is the more important half. It is no longer covering a
    # design-temperature shortfall: EQ-M-HP1-OD makes 21,000 Btu/h at -15 F against a
    # 15,164 Btu/h zone load, unaided. This is defrost-recovery and sub-lockout backup.
    #
    # CKT-HP1-STRIP IS GONE. A factory kit inside the cabinet is fed from the air handler's
    # own circuit, so CKT-HP1-AH goes 15A -> 35A (the kit's MCA 29.9 A / max OCPD 35 A) and
    # the panel gets its spare 2-pole back at slot 18 (plan/circuits.py).
    Equipment(uid="CEE033AAAA", tag="EQ-S-HP1-STRIP", kind=EquipmentKind.SPACE_HEATER,
              position=pt(ft(19, 6), ft(29, 11.5)), footprint=(inch(16), inch(10)),
              room="RM-S-HALL", type_ref="EQ-T-GREE-FLEXX-HEATKIT-46KW",
              circuit="CKT-HP1-AH", mount=Mount(kind=MountKind.CEILING),
              soffit_ref="SF-S-HP1"),
]

# --- Garage: EV receptacles on the west and south walls ----------
# ED-G-EV-1450 is on W-G-S's INTERIOR face. GARAGE_WALL_2X6's sheathing is 5/8" CDX and its
# cladding is 7/8" corrugated, and the wall also carries a 3/8" node-line offset
# (`GARAGE_Y_SOUTH`, plan/storeys/garage.py) that keeps the breezeway slot — net, W-G-S's
# interior face sits +3/8" (node) - 7/8" (wall depth) = -1/2" off the sheathing plane.
# `ED-G-EV-620` is on W-G-W, which has no node-line move, so its interior face is 7/8" off
# the sheathing plane. Both west-wall devices here and `EQ-G-HEATER` below travelled the
# garage's 6'-0" east move on 2026-09-07 — they sit ON that wall. `ED-G-EV-1450` did not:
# it is a station on the SOUTH wall's interior face, still well inside its new x 6'..30'
# run, and holding it still keeps `CD-B-GARAGE` and its three sleeves untouched.
GARAGE_DEVICES = [
    ElectricalDevice(uid="CEE008AAAA", tag="ED-G-EV-620", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(6, 8.75), ft(58, 6.75)), type_ref="ED-T-EV-620", circuit="CKT-EV-620",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), room="RM-GARAGE", rotation=deg(90)),
    ElectricalDevice(uid="CEE009AAAA", tag="ED-G-EV-1450", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(19, 11.375), ft(43, 11.375)), type_ref="ED-T-EV-1450", circuit="CKT-EV-1450",
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
              position=pt(m(2.042254), m(18.62)), footprint=(inch(14), inch(9)),
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
    # x >= 13'-5". ** THE 2026-09-06 MOVE WEST CLOSED THE EASTWARD BAND AGAIN. ** The
    # 2026-09-03 move east had opened 10'-10"..11'-11" between the roof underside's
    # x >= 10'-10" (20'-1 1/2" + x/2, the plane `integrity.element_above_roof` reads, a foot
    # below the cladding) and the old bumper at 11'-11"; the window has since come back a
    # bay west and that band is inside the glass. None of it matters, because the box was
    # LEFT at x=10'-2" through both moves: elevation 25'-0" where the underside is 25'-4",
    # 4" of clearance, and 5" west of the bumper — wholly west of the window on the facade,
    # which is the better elevation anyway. It is a tighter 5" than it was, and it is the
    # number to re-check if this window is ever asked to move again.
    #
    # Going east instead (x >= 14'-11") clears the window at 25'-6" and costs 2'-6" of
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
    # ** ONE FEEDER, TWO RUNS SINCE 2026-09-09, AND THE SPLIT IS THE POINT. ** The whole
    # thing used to sit at -4'-0" — the burial depth it wants in the house/garage gap —
    # which inside the house is five feet off the slab: 6'-1" of it crossed RM-B-STAIR at
    # head height and `mep.run_in_finished_volume` called it at 36.1". A `ConduitRun` changes
    # elevation only at its LAST vertex, so a run that has to be high indoors and low
    # outdoors cannot be one run. CD-B-GARAGE is now the indoor leg, held at the basement
    # ceiling and turning DOWN at the wall it leaves through; CD-B-GAP-EV below is the
    # buried leg. Both name the same panel and the same receptacle, because that is what
    # they are — the conduit schedule and the BOM read one feeder in two rows.
    #
    # THE INDOOR LEG'S TWO NUMBERS. -1'-1 3/4" is 1.9" under RM-B-STAIR's -1'-0 1/2"
    # ceiling, inside the 3" the check allows, and it is chosen against the two runs this
    # leg crosses rather than against the ceiling: PR-B-CW-TRUNK's x=5'-0" leg at -1'-2.8"
    # (1 1/16" on centre) and CD-B-DATA-STUDY's x=2'-0" leg at -1'-0.5" (1 1/4"), which is
    # how two raceways rack together. y moved 35'-0" -> 35'-3" for the same reason:
    # PR-B-KITCH-DRAIN owns y=35'-0" from x=4'-6" to x=18'-0" and its crown is above this
    # band, so the old lane is not free at ceiling height. 35'-3" puts the conduit's face
    # 3/8" off W-B-N2's inside face (35'-4"), which is where it is strapped.
    ConduitRun(uid="CDT002AAAA", tag="CD-B-GARAGE", trade_size=inch(1.25),
               path=(pt(ft(2), ft(29)), pt(ft(2), ft(35, 3)), pt(ft(16), ft(35, 3)),
                     pt(ft(16), ft(35, 5)), pt(ft(16), ft(35, 5))),
               start_elevation=ft(-1, -1.75), end_elevation=ft(-4),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # The buried leg: out through SP-B-N2-CD-GAR2 at -4'-0", north under the house/garage
    # gap, and up through the garage slab to ED-G-EV-1450. Same station the whole feeder
    # always used — none of its three sleeves moved.
    ConduitRun(uid="5PEMG38MHJ", tag="CD-B-GAP-EV", trade_size=inch(1.25),
               path=(pt(ft(16), ft(35, 5)), pt(ft(16), ft(44, 3.375))),
               start_elevation=ft(-4), end_elevation=ft(5, 10),
               from_ref="ED-B-PANEL", to_ref="ED-G-EV-1450"),
    # Across the basement ceiling to the kitchen's east counter wall, where KGF3 (the device
    # this feeds) is.
    ConduitRun(uid="CDT003AAAA", tag="CD-B-KITCHEN", trade_size=inch(0.75),
               path=(pt(ft(2), ft(29)), pt(ft(35), ft(29)), pt(ft(35), ft(28, 11))),
               # ** -1'-4", RAISED 2" ON 2026-09-09, AND THE OLD PROSE WAS THE TELL. ** This
               # block claimed 1 15/16" of clear under the deck board while the run was
               # authored at -1'-6", where the real gap is 3 9/16" and the raceway hangs 4.3"
               # into RM-B-PLAY-N below — `mep.run_in_finished_volume` FAILed on it. At -1'-4"
               # the conduit's top is 1 9/16" under the board at -14 1/16": strapped tight to
               # the deck framing with room for the ceiling, which is what was always meant.
               # This is the tightest raceway in the basement. Its two wall crossings go with
               # it. Do not put it back — a 16'-6" bulkhead to box a 3/4" pipe is not the fix.
               start_elevation=ft(-1, -4), end_elevation=ft(3, 6),
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
    # Media room: east along the basement ceiling at -1'-4", through the stair shaft's west
    # wall and the centre wall, then north to the jack behind the television. Held at y=30'
    # so its two sleeves stay a clear foot from CD-B-KITCHEN's at y=29' — the sleeve matcher
    # pairs a run to a hole by proximity, and two holes 6" apart in the same wall confuse it.
    #
    # -1'-4" for the same reason CD-B-KITCHEN is (2026-09-09): at -1'-6" it hung 4.3" into
    # RM-B-PLAY-N, whose finished ceiling IS the deck board at -14 1/16". Both raceways
    # cross that room, and both had to come up the same 2".
    ConduitRun(uid="D606MFGTEG", tag="CD-B-DATA-MEDIA", trade_size=inch(0.75), service=Service.DATA,
               path=(pt(inch(10), ft(31)), pt(ft(2), ft(30)), pt(ft(27, 9), ft(30)),
                     pt(ft(27, 9), ft(35, 3))),
               start_elevation=ft(-1, -4), end_elevation=ft(-6, -10),
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
                     position=pt(ft(6, 6), ft(22, 0.625)), type_ref="ED-T-AP-WALL",
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
    # CD-B-GARAGE / CD-B-GAP-EV: the indoor leg runs west to east at the basement ceiling
    # on y=35'-3", 1" clear of W-B-N3/W-B-N2's inside face (35'-4"), and turns down at
    # x=16' where it meets that wall; the buried leg goes on north under the house/garage
    # gap and up through the garage slab. The 2026-09-09 split moved no sleeve: the turn
    # lands on the same x=16' station the punch always used. W-B-STR at x=10' is framed, so
    # its crossing is bored, not cast. Only the genuine north punch at x=16'
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
                      position=pt(ft(16), ft(43, 8.125)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2), purpose=Service.POWER_240,
                      axis="horizontal", center_elevation=ft(-4)),
    # The stub-up, 3 3/8" north of the stem's inside face, at 41'-9" — 2 3/8" of concrete
    # around the bore. `integrity.sleeve_in_opening` tests the sleeve's CENTRE, so the full
    # 2 3/8" margin is what protects it, not half the bore's clearance to the slab edge. The
    # conduit runs up the inside face of W-G-S from here to ED-G-EV-1450.
    SleevePenetration(uid="CNS010AAAA", tag="SP-G-CD-GAR", host_ref="SL-G-FLOOR",
                      position=pt(ft(16), ft(44, 3.375)), pipe_diameter=inch(1.25),
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
    # Host is W-B-S1 again since the sauna shrink undid the 2026-09-05 pour split: x=8'-6"
    # is back in the one south segment. Same hole, same station.
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
    # ** RC1/RC2 HUNG ON THE WRONG SIDE OF THE x=18' LINE UNTIL 2026-09-05. ** They were
    # authored at x=17'-4 3/4", 1" WEST of W-B-CS's west face — which is inside the sauna,
    # not the gym: a 120V convenience receptacle in a 190 F room. `receptacle_spacing`
    # accepts any device within 0.5 m of a room's clear face regardless of which side it is
    # drawn on, so nothing said so. All three now sit 1" EAST of the line's gym face
    # (18'-3 3/8" on the framed segments), which is the setback this whole file uses, with
    # the plate turned east into the room.
    #
    # Three, not two, because the line is broken by two doors now: D-B-SAUNA at y 2'-10"..
    # 4'-10" and D-B-GYM at y 9'-11"..12'-7". NEC 210.52(A)(2) measures wall space between
    # doorways, so each of the three stretches needs its own — south of the sauna door,
    # between the two, and north of D-B-GYM. RC8 sits on the 15" of W-B-CS3 left north of
    # that door; the wall past it is W-B-CS2's 12" pour, which is the last place to want a
    # cast-in box.
    ElectricalDevice(uid="NEC001AAAA", tag="ED-B-GYM-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(220.375), ft(1, 4)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="NEC002AAAA", tag="ED-B-GYM-RC2", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(220.375), ft(5, 6)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
    ElectricalDevice(uid="WSTK6T5E4K", tag="ED-B-GYM-RC8", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(220.375), m(3.07239)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-GYM",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(90)),
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

    # ** THE HALL, AND NOTHING IN THIS ENGINE ASKED FOR IT (2026-09-07). ** The basement
    # hall runs 15'-6" from the stair foot to the sauna wall now, which is NEC 210.52(H)
    # territory — a hallway 10 ft or more in length takes at least one receptacle. Like the
    # workshop benches above, `electrical.receptacle_spacing` walks
    # {BEDROOM, LIVING, KITCHEN, DINING, OFFICE} and STAIR is outside it, so no check will
    # ever call this gap. It is authored because the code says so, not because the model
    # noticed.
    #
    # On W-B-HALL-W's hall face (east face at 14'-2 1/16") 1" proud of it — the face
    # convention at the top of this file — at y=16'-0", roughly the hall's midpoint and
    # clear of both doors: D-B-SHOP's north jamb is at 13'-9 7/16" and D-B-GYM is opposite,
    # on the other side. `rotation=deg(90)` turns the plate east into the hall. Elevation
    # 16", the house's standard. CKT-RC-BSMT is already `gfci=True, afci=True`
    # (plan/circuits.py), which is what E3902.11 wants of an unfinished-basement outlet.
    ElectricalDevice(uid="KYE6QTF5VS", tag="ED-B-HALL-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(171.0725), ft(16)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-BSMT", room="RM-B-STAIR", rotation=deg(90),
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
    # E3901.6 want a receptacle within 36" of the outside edge of EACH BASIN. ** THE ENGINE
    # NOW HAS THAT RULE ** — code.E3901_6_bathroom_receptacle, in
    # checks/mep/electrical_receptacles.py — and every lavatory in this house passes it,
    # including the two that were written up in plans/TODO.md as outside the 36" and have
    # since been served. The paragraph that stood here saying no such rule existed predates
    # the check.
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
    # ------------------------------------------------------------------------------------
    # THE TWO WASHLET OUTLETS (2026-09-06) — one stud bay, both baths.
    # ------------------------------------------------------------------------------------
    # `[allowances] plumbing-bidet-seats` buys two TOTO WASHLET S5 seats for the two
    # main-floor showpieces and had bought them for a fortnight with no receptacle anywhere
    # near either bowl. The requirement is written in three places (fixture_types_wc.py's
    # FX-TOTO-CARLYLE-II source, prices.toml, notes/interior_selections.md): a GFCI outlet
    # 6-12" AFF at each toilet, on its own 20 A circuit, NOT ganged. See plan/circuits.py.
    #
    # ** BOTH LIVE IN ONE STUD BAY OF W-M-HS1 — x 8 1/8" to 15", the wall's west bay — and
    # that bay is the only place either of them could go. ** W-M-HS1 is the wet wall between
    # the two baths and carries BOTH bowls: FX-M-BATH1-WC hangs on its north face, on the
    # DuoFit carrier, and FX-M-BATH2-WC's tank stands against its south face. The resolved
    # framing leaves exactly one clear bay beside them: stud-000 at x=7.39" against
    # carrier-0-stud-0 at x=15.78", 6 7/8" of clear cavity, full 5 1/2" deep (both are 2x6 —
    # the staggered run does not start until x=40"). Everything east of it is spoken for —
    # the 19 3/4" carrier bay, then 1 1/2" of clear before FX-M-BATH1-LAV's cabinet at
    # x=41 1/2" on the north face and the tub deck on the south.
    #
    # It is provably free of MEP: no pipe run, conduit, duct, sleeve or pipe accessory has a
    # vertex anywhere in x 4"..22", y 258"..278" on this storey. Confirm that again before
    # putting anything else in it — a wet wall's west end is exactly where a plumber would
    # reach for a spare bay.
    #
    # ** THE TWO BOXES ARE BACK TO BACK AND THAT IS DELIBERATE. ** A 4" device in a 6 7/8"
    # bay can only be roughly centred, so two of them cannot both be offset; they are on
    # OPPOSITE FACES of a 5 1/2" cavity with about 1 1/2" of air between the box backs, and
    # the wall either side of the bay is bathroom-to-bathroom, so nothing is being shorted
    # acoustically that the room next door does not already hear. Do not "fix" this by
    # sliding one east into the carrier bay: that bay is purpose-framed around an 880 lb
    # point load and a header, and there is no cavity in it to put a box in.
    #
    # 8" AFF is the base (Mount.elevation is the BASE, and the type is 2" tall), so the body
    # sits 8"..10" — inside the 6-12" band with room either side, and matching
    # ED-M-BATH2-TUB-RC's height. y is the wall's own finish face plus the device's 1"
    # half-depth, the same arithmetic as ED-M-BATH2-RC1 above; rotation 0 runs the 4" box
    # along an east-west wall.
    #
    # ** CORD REACH IS WHAT MAKES THIS WORK AND NOTHING GRADES IT. ** A WASHLET's cord exits
    # the seat's rear-left (viewed facing the fixture, i.e. the west side of both of these
    # bowls) on about 4 ft of lead. From the SP's west china edge at x=18.91" the run is
    # ~7"; from the Carlyle II's at x=20.875" it is ~9". Move either bowl east and re-measure
    # rather than assuming — no check in this engine compares a device to the fixture it
    # feeds, and an out-of-reach outlet builds and checks clean.
    ElectricalDevice(uid="FZ7A2MC93E", tag="ED-M-BATH1-WC-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(11.5), inch(272.385)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-WASHLET-BATH1", room="RM-M-BATH1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(8))),
    ElectricalDevice(uid="90BE5BHPAX", tag="ED-M-BATH2-WC-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(11.5), inch(263.615)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-WASHLET-BATH2", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(8))),
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
                     position=pt(inch(76.385), m(7.91434)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), room="RM-M-LIVING", rotation=deg(90)),
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
                     position=pt(inch(211.115), ft(10, 9)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(270)),
    ElectricalDevice(uid="NEC015AAAA", tag="ED-M-BED-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(inch(211.115), ft(1, 1.5)), type_ref="ED-T-RECEPTACLE",
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
    # x = 13'-9 1/2" is W-M-LS's resolved study face plus half this type's 1" depth — W-M-LS
    # moved +1" east 2026-09-09 (funding part of the BATH2 jog realignment), and this offset
    # moved the same 1" to stay on the wall's new face;
    # y = 19'-4" centres it on FURN-M-STUDY-DESK, whose top is 29 1/2" — so 32" puts the box
    # 2 1/2" clear of the desk exactly as ED-M-STUDY-RC1 does, and the two outlets a seated
    # person reaches are at one height on two walls. It is 4'-0" south of REG-M-SUP4's riser
    # bay (y=20'-8"), so the box and the 3" duct in that cavity never meet.
    ElectricalDevice(uid="NEC020AAAA", tag="ED-M-STUDY-RC2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(inch(165.375), ft(19, 4)), type_ref="ED-T-RECEPTACLE-GFCI",
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
    # RC1 is on the 11'-4" bay centre, 6'-3 3/4" from RC2 (electrical.receptacle_spacing).
    # It was placed there as the *west* jamb of D-S-DECK-W's rough opening (x 12'-2"..17'-2"),
    # which closed the wall space west of that door. The door is gone (2026-09-03) and
    # WIN-S-PLANT4 stands in its place, so this is now an ordinary station on a continuous
    # wall: a window sill 2'-8" up breaks no wall space, and 210.52(A) is satisfied by RC1/RC2
    # on their own spacing. The bay is still the right one — it stays.
    # FX-S-BALC-HYD gave up this bay for it and moved to 7'-4" (plan/fixtures.py).
    ElectricalDevice(uid="NEC021AAAA", tag="ED-S-PLANT-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(11, 4), ft(0, 8.75)), type_ref="ED-T-RECEPTACLE-WR-GFCI",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # RC2 is the outlet nearest FX-S-BALC-HYD (1'-5 3/4" in plan) and it is deliberately NOT
    # the power for the room's drip-irrigation timer: the hydrant's thread is outdoors, so a
    # cord from here would cross W-S-S1's Class I liner and 4" of continuous exterior foam
    # for a device that ships as a battery unit. Nothing is authored on the balcony either.
    # See notes/plant_room.md, open item 2.
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
                     position=pt(ft(33, 2.875), inch(111.875)), type_ref="ED-T-RECEPTACLE",
                     circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="NEC032AAAA", tag="ED-S-BED1-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 7.375), inch(111.875)), type_ref="ED-T-RECEPTACLE",
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
    # Slid 26'-9 7/8" -> 29'-2" east along the same south wall, 2026-09-06.
    # FURN-S-BED3-WARD moved onto this wall (x 293.5..341.5) to clear the north wall for
    # WIN-S-HALL-N's move west to 24'-0", and at 321 7/8" the box ended up BEHIND the case. Nothing would have
    # caught it: `_fixed_cabinet_intervals` in checks/mep/electrical.py only breaks wall
    # space for a placeable with `work_surface is False`, and FURN-WARDROBE-48 leaves it
    # None, so electrical.receptacle_spacing passes either way and the room just quietly
    # loses a usable outlet. 29'-2" (350") is 8 1/2" clear of the case's east end.
    ElectricalDevice(uid="NEC040AAAA", tag="ED-S-BED3-RC4", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 2), ft(26, 11.375)), type_ref="ED-T-RECEPTACLE",
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
                     position=pt(ft(1, 0.75), inch(263.625)), type_ref="ED-T-RECEPTACLE-GFCI",
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
