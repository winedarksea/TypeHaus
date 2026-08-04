# haus: editable
# Catlin MEP: plumbing sleeves/drains (Phase 2) + ERV trunk ducts + the System 1 heat-pump
# chase + electrical (Phase 3).
#
# Authored routing only — the user places runs/ducts/devices; the resolver validates them
# against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.
# This file is `# haus: editable` so UI moves (e.g. dragging the water heater) round-trip
# back to source; every element below is an explicit constructor, no generators.
#
# Plumbing: sleeve positions are the exact pre-pour centers the concrete crew works from —
# the resolver validates them against the fixture drain point they serve
# (`mep.sleeve_alignment`); nothing here is derived. Second-floor hall-bath drains drop
# through the framed floor into the existing INT_2X6_PLUMBING wet wall (W-S-BD-N) with no
# sleeve needed — only a cast concrete deck needs a pre-positioned penetration.
#
# Ventilation: the second-floor ERV trunks run in the FS-SECOND joist bays (11.875" I-joist, 16" o.c.,
# direction "x"). Bay centers are `8" + n*16"` from the joist-line math in
# resolve/floors.py; bay 15 (y=20'-8") and bay 17 (y=23'-4") are both clear of the stair
# FloorOpening (x:11'-18', y:25'-36') and both cross the central bearing wall at x=18'.

from typehaus import (
    ClearancePolicy,
    ClearanceZone,
    Connector,
    ConnectorKind,
    DeviceKind,
    DuctRouting,
    DuctRun,
    DuctSystem,
    ElectricalDevice,
    ElectricalDeviceType,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Footprint2D,
    Mount,
    MountKind,
    PipeAccessory,
    PipeAccessoryKind,
    PipeRun,
    PipeSystem,
    Register,
    RegisterType,
    Service,
    ServicePort,
    SleevePenetration,
    Sump,
    SumpPump,
    VentRun,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# Two families of air terminal now, and the difference matters on the plan set:
#
# REG-T-ERV-SUP / REG-T-ERV-EXH are *ventilation* terminals (ventilation_terminal=True) —
# small, continuous-flow diffusers on EQ-B-ERV's balanced trunks, sized for the ~197 cfm
# whole-house rate. They replace REG-T-SUPPLY/REG-T-RETURN, which were drawn and named like
# old-fashioned furnace grilles (plans/TODO.md §HVAC: "currently styled more like old
# fashioned grilles, not true ERV inputs/outputs"). The old tags are gone rather than kept
# as aliases: two names for one terminal is how a schedule ends up printing both.
#
# REG-T-HP-SUP / REG-T-HP-RET are the *conditioned-air* terminals on System 1's ducted
# chase (plan/electrical.py EQ-S-HP1-AH) — a heating CFM, so they are the bigger section.
REGISTER_TYPES = (
    RegisterType(tag="REG-T-ERV-SUP", name="ERV fresh-air supply diffuser, 6\" round",
                 footprint=(inch(7), inch(7)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-ERV-EXH", name="ERV stale-air extract diffuser, 6\" round",
                 footprint=(inch(7), inch(7)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    # The sauna's own pair, small and dampered. A sauna is run in sessions, not
    # continuously: during a session you want the room sealed and stratified, and after one
    # you want it turned over hard. Both terminals are 4"x4" with an adjustable, closable
    # damper at the face (plans/TODO.md §HVAC) so the room can be shut off the trunk and
    # opened wide, which a fixed 6" round diffuser cannot do.
    RegisterType(tag="REG-T-ERV-SAUNA-SUP",
                 name="Sauna fresh-air supply, 4x4, small adjustable/closable damper",
                 footprint=(inch(4), inch(4)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 source="plans/TODO.md §HVAC: sauna terminals small, adjustable/closable damper",
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-ERV-SAUNA-EXH",
                 name="Sauna stale-air extract, 4x4, small adjustable/closable damper",
                 footprint=(inch(4), inch(4)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 source="plans/TODO.md §HVAC: sauna terminals small, adjustable/closable damper",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-HP-SUP", name="Heat-pump supply register, 12x6",
                 footprint=(inch(12), inch(6)), height=inch(1),
                 plan_symbol="register",
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-HP-RET", name="Heat-pump return grille, 20x14",
                 footprint=(inch(20), inch(14)), height=inch(1),
                 plan_symbol="register",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
)

# No gas appliance in the house: the gas furnace that used to stand at (4', 29'-4") is gone
# (all-electric — three Gree heat-pump systems + radiant floor), and `plan/site.py` never authored a GAS
# UtilityLine to feed one. The air-side ports it used to carry now live on EQ-T-ERV and
# EQ-T-GREE-SLIM24 (plan/electrical.py) — the two things left that push air, neither of
# which burns anything.
EQUIPMENT_TYPES = (
    # The 120V Rheem heat-pump water heater (plans/electrical_notes.md lines 25-26): stays
    # on the backup subsystem, so no gas and no 240V boost — the 240V tank is EQ-B-WH2
    # (plan/electrical.py). Compressor ~500W; the type is electric-only.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Heat pump water heater, Rheem 120V", footprint=(inch(24), inch(24)), height=ft(5),
                  plan_symbol="water-heater",
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))))),
    # --- the backup microgrid (2026-08-02, notes/backup_power.md) ----------------------
    #
    # EG4 12kPV. The name is the PV input, not the output: 12,000 W of array in, 8,000 W of
    # AC out continuous, which is the number the autonomy calc checks the backup loads
    # against and the number the CKT-ESS-GRID breaker is sized on. Surge is the datasheet's
    # 16 kW / 0.5 s step (12 kW/1 s, 10 kW/1 min below it); the 0.5 s figure is the one a
    # compressor start actually asks for.
    #
    # UL 9540 belongs to the *battery*, not here — the listing R327.2 wants is on the energy
    # storage system, and marking an inverter with it would make the check pass on the
    # strength of the wrong product.
    EquipmentType(tag="EQ-T-EG4-12KPV", name="EG4 12kPV hybrid inverter",
                  footprint=(inch(27), inch(12)), height=inch(35),
                  inverter_kw_continuous=8.0, inverter_kw_surge=16.0, pv_input_kw=12.0,
                  ports=(ServicePort(tag="grid", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="load", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),),
                  source="EG4 12kPV spec sheet, read 2026-08-02: 8,000 W continuous AC output (120/240V split phase), 12,000 W PV input over 2 MPPTs at 600 VDC max, 16 kW/0.5 s surge, UL 1741 + UL 9540 listed."),
    # EG4 PowerPro WallMount Indoor, 14.3 kWh. One unit to start; the R327.5 aggregate check
    # is what a second one would have to answer to (40 kWh indoors — two of these is 28.6,
    # three is 42.9 and fails, which is the real ceiling on this closet).
    #
    # ``ul_9540_listed=True`` is a declaration about this product, and `code.R327_ess_listing`
    # reports exactly what is declared here — it never infers a listing from the name.
    #
    # The 3'-0" REQUIRED clearance is the owner's separation rule (plans/TODO.md: "Keep a 3'
    # clearance from other devices"), not a code working space, which is why
    # `advisory.ess_clearance` grades it and no CODE check does. Authored as a band all the
    # way around: the concern is a neighbouring device in any direction, not access to a
    # front face.
    EquipmentType(tag="EQ-T-ESS-BATT", name="EG4 PowerPro WallMount Indoor, 14.3 kWh",
                  footprint=(inch(24), inch(10)), height=inch(43),
                  storage_kwh=14.3, ul_9540_listed=True,
                  clearances=(ClearanceZone(
                      footprint=Footprint2D(points=(
                          pt(inch(-48), inch(-41)), pt(inch(48), inch(-41)),
                          pt(inch(48), inch(41)), pt(inch(-48), inch(41)))),
                      purpose="3'-0\" separation from other devices",
                      policy=ClearancePolicy.REQUIRED,
                      source="owner rule, plans/TODO.md backup-power block"),),
                  ports=(ServicePort(tag="dc", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),),
                  source="EG4 PowerPro WallMount Indoor 14.3 kWh (LFP), UL 9540 listed. Capacity is nameplate; the autonomy calc applies its own depth of discharge (takeoff/backup_calc.py)."),
)

ELECTRICAL_DEVICE_TYPES = (
    # ``bus_amps=225`` is what `code.NEC_705_12_interconnection` computes the 120% rule
    # against (2026-08-02). It is the busbar rating, deliberately not the 200A service:
    # NEC 705.12(B)(3)(2) sizes the allowable backfeed on the bus, and this panel is a 225A
    # bus on a 200A main precisely so there is 70A of source headroom.
    ElectricalDeviceType(tag="ED-T-PANEL", name="225A electrical panel (200A service)", footprint=(inch(20), inch(4)), height=ft(3),
                          plan_symbol="panel", spaces=54, bus_amps=225,
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # The backup subpanel on the EG4's dedicated load output (2026-08-02). 12 spaces for the
    # 7 the two tiers use — the spare six are the room a second always-on circuit needs, and
    # a 12-space enclosure costs nothing over an 8. No ``bus_amps``: nothing backfeeds this
    # bus today, and stating a rating the 705.12 check would then grade against a service
    # main it does not have would be worse than saying nothing (see the note in
    # checks/mep/power_sources.py about the missing feeder element).
    ElectricalDeviceType(tag="ED-T-BACKUP-PANEL",
                          name="12-space backup subpanel (EG4 load output)",
                          footprint=(inch(14), inch(4)), height=ft(1, 8),
                          plan_symbol="panel", spaces=12,
                          ports=(ServicePort(tag="feed", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # ED-T-LIGHT is gone. It was a generic "Ceiling light" with no lamp, no lumens and no
    # listing, standing one per room; every light in the house is now a real product from
    # plan/lighting_types.py carrying a schedule mark, and a fixture a schedule cannot
    # print a row for has no place in a lighting plan.
    ElectricalDeviceType(tag="ED-T-SWITCH", name="Wall switch", footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE", name="Receptacle", footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    # NEMA 3R weatherproof exterior junction box with a gasketed blank cover plate.
    ElectricalDeviceType(tag="ED-T-JBOX", name="NEMA 3R weatherproof junction box",
                          footprint=(inch(6), inch(6)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Kitchen outlets. ED-T-RECEPTACLE above stays a plain 120V duplex — its port list is
    # pinned by a contract test — so the counter devices name their own types instead.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-GFCI", name="GFCI receptacle",
                          footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-240", name="240V appliance receptacle, NEMA 14-50",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # The kettle outlet the brief asks for: a 5-20R and a 6-20R in one two-gang box, so a
    # 120V and a 240V appliance can share the spot. Two ports, one device.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-620",
                          name="NEMA 5-20R/6-20R duplex kettle outlet",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power-120", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),
                                 ServicePort(tag="power-240", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))))),
)

SLEEVES = [
    # BATH1's WC is wall-hung on an in-wall carrier (FX-TOILET-WH): the bowl bolts to a
    # steel carrier frame inside W-M-BAE's 2x6 stud bay and the 3" waste drops inside the
    # wall, so the pre-pour sleeve sits on that wall's centerline at the fixture's authored
    # drain_position — under the carrier, not under the bowl.
    SleevePenetration(uid="CMP901AAAA", tag="SP-M-WC1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(22, 7)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH1-WC"),
    # Re-pointed 2026-07-29 (plans/TODO.md): the BATH2 WC moved to the wet wall and its
    # routed drain (PR-B-WC2-DRAIN) now drops at the fixture's own flange, so the sleeve
    # finally sits where the pipe actually is instead of at the old (3', 18') position.
    SleevePenetration(uid="CMP902AAAA", tag="SP-M-WC2", host_ref="SL-M-DECK",
                      position=pt(m(0.686504), m(6.14439)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH2-WC"),
    SleevePenetration(uid="CMP907AAAA", tag="SP-M-BATH2-SH", host_ref="SL-M-DECK",
                      position=pt(ft(1, 9), ft(17, 3)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-SH"),
    SleevePenetration(uid="CMP908AAAA", tag="SP-M-BATH2-TUB", host_ref="SL-M-DECK",
                      position=pt(ft(7, 4), ft(19, 4.8)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-TUB"),
    SleevePenetration(uid="CMP909AAAA", tag="SP-M-BATH2-SINK", host_ref="SL-M-DECK",
                      position=pt(ft(1), ft(16, 6)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-SINK"),
    # Projection of FX-M-BATH1-LAV onto the W-M-BAE structure-layer centerline (x=6, from
    # storeys/main.py node coordinates N-M-BA1/N-M-BA2), at the lavatory's own y (nudged
    # +6" with it on 2026-07-29 for the BATH2 wall move).
    SleevePenetration(uid="CMP903AAAA", tag="SP-M-LAV1", host_ref="SL-M-DECK",
                      position=pt(ft(6), m(7.00891)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-M-BATH1-LAV"),
    # Projection of FX-M-LAUNDRY onto the W-M-BA2E centerline (x=8'). The wall tag in this
    # comment used to read "W-M-BA2E2", which spans y 13'-4"..18'-0" and so contains neither
    # this sleeve nor the fixture — a stale tag, corrected 2026-07-31 here and on the
    # fixture's own `wall_ref` (plan/fixtures.py). The position is unchanged: x=8' is the wet
    # wall's centreline and y=20' sits inside the stacked pair's band, so the standpipe and
    # the supply box land behind the machine rather than beside it. It survived the 8" move
    # north of 2026-08-03 without moving — the band is 18'-0 5/8"..21'-4 5/8" now and y=20'
    # is still well inside it, as are SP-M-CW-WASH (20'-7.2") and SP-M-HW-WASH (21'-2.4").
    SleevePenetration(uid="CMP904AAAA", tag="SP-M-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY"),
    # The laundry tub's waste, straight down under its basin the way every other main-storey
    # fixture drops through this 9" cast deck. 2" rather than the 1 1/2" one sink would take,
    # because the branch below it is the tub's trap arm to the laundry stack and 2" is what
    # buys the 60" Table 1002.2 allows for the 45" it runs. Authored at exactly the fixture's
    # `drain_position`, which is what makes `mep.sleeve_alignment` read 0.00".
    SleevePenetration(uid="ZW630NFAAS", tag="SP-M-LSINK", host_ref="SL-M-DECK",
                      position=pt(ft(11, 9), ft(18, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY-SINK"),
    # The kitchen sink's waste through the 9" deck. Authored at exactly FX-M-KITCH-SINK's
    # `drain_position`, which is what makes `mep.sleeve_alignment` read 0.00". Moved to the
    # north wall 2026-07-30 with the sink, then re-centred the same day with the sink/
    # dishwasher flip — see plan/fixtures.py.
    SleevePenetration(uid="BFQH6F04VQ", tag="SP-M-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(28, 7), ft(35)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-KITCH-SINK"),
]

# Supply risers through the 9" concrete deck — every hot/cold branch that leaves the
# basement ceiling for a main- or second-storey wet wall crosses SL-M-DECK, and a PEX
# riser through cast concrete is a cast-in sleeve exactly like a waste drop
# (`mep.sleeve_coverage` holds every crossing to one). Positions sit on (or tight to) the
# wet wall each riser feeds, spaced >= 5" from every neighbouring penetration so the
# 4"-tolerance sleeve matcher can never confuse two.
SUPPLY_SLEEVES = [
    SleevePenetration(uid="CMPS01AAAA", tag="SP-M-CW-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(23, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS02AAAA", tag="SP-M-HW-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(24)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS03AAAA", tag="SP-M-CW-BATH2", host_ref="SL-M-DECK",
                      position=pt(ft(2, 3), ft(17, 2.4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS04AAAA", tag="SP-M-HW-BATH2", host_ref="SL-M-DECK",
                      position=pt(ft(2, 3), ft(16, 9.6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS05AAAA", tag="SP-M-CW-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS06AAAA", tag="SP-M-HW-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(21, 2.4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    # Moved to the north wall 2026-07-30 with the sink, then re-centred with the sink/
    # dishwasher flip: same offset magnitude from the sink centre, but the along-wall
    # component now points *east* (toward the dishwasher's new spot) instead of west.
    SleevePenetration(uid="CMPS07AAAA", tag="SP-M-CW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 0.6), ft(34, 1.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS08AAAA", tag="SP-M-HW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 6.6), ft(33, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS09AAAA", tag="SP-M-CW-SBATH", host_ref="SL-M-DECK",
                      position=pt(ft(5, 7.2), ft(26, 4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    # x=6'-2.4" -> 6'-4" (2026-08-02) with PR-B-HW-SBATH's riser below: RM-M-MUD-CLOSET's
    # east return now tees into N-M-BA1 and its corner pack took the old station — see the
    # note on that PipeRun.
    SleevePenetration(uid="CMPS10AAAA", tag="SP-M-HW-SBATH", host_ref="SL-M-DECK",
                      position=pt(ft(6, 4), ft(26, 4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS11AAAA", tag="SP-M-CW-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(13, 7.2), ft(16, 10.8)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS12AAAA", tag="SP-M-HW-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(14, 2.4), ft(16, 10.8)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    # The two south-face wall hydrants' shared riser (2026-08-01). One crossing, not two:
    # both hydrants are fed from the second-floor joist space, so a single 3/4" branch
    # leaves the basement here and splits up there. y=13'-4" is W-M-BDN1's line — the
    # main-storey partition the riser stands inside — and it is over open basement ceiling
    # at x=6' (W-B-SA-N, the sauna's north partition, starts at x=8'-10"), so the
    # penetration lands in the deck rather than on top of a wall below it. Nothing else
    # crosses within 3' of it.
    SleevePenetration(uid="CMPS16AAAA", tag="SP-M-CW-HYD", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(13, 4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
]

# Second-storey waste stacks. The upstairs bathrooms drain down through framed walls and
# floors — no sleeve needed there — but each stack still has to pass the one concrete
# plate in its way, the SL-M-DECK deck, on the way to the basement-ceiling collector.
STACK_SLEEVES = [
    SleevePenetration(uid="CMPS13AAAA", tag="SP-M-S-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(5), ft(26, 4)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-S-BATH1-WC"),
    SleevePenetration(uid="CMPS14AAAA", tag="SP-M-S-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(13), ft(16, 10.8)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-S-SUITEBATH-WC"),
    # The heat-pump condensate drop from the main-storey wall heads (master bedroom +
    # living room, both on the south wall by the centre line) down to the collected
    # air-gap line at the basement ceiling (plans/TODO.md §condensate).
    SleevePenetration(uid="CMPS15AAAA", tag="SP-M-COND", host_ref="SL-M-DECK",
                      position=pt(ft(17, 6), ft(1)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.DRAIN),
]

# Slab-on-grade stub-ups. A fixture standing on grade has no wall drain stack — its trap
# arm runs *under* the slab — so the penetration is set before the pour exactly like the
# deck sleeves above. Each fixture authors this same point as its `drain_position` (or, where
# there is no override, as its own position), which is what makes the alignment check exact.
#
# Four of them now (2026-07-30). The basement went from one slab fixture to four in one
# decision: a bathroom at the foot of the stair, and the sauna's shower end resolved into a
# curbed pan plus a floor drain.
SLAB_STUBS = [
    # Was SP-B-UTILITY, FX-1's stub at (7', 19'-6"), until 2026-07-30. Same cast-in, moved
    # and upsized to 3" for the bathroom's water closet: the utility sink it used to serve is
    # gone and the fixture that replaced it is a WC, which needs a 3" closet bend rather than
    # a 1 1/2" trap arm. The uid rides along because it is the same penetration in the same
    # pour schedule, not a new one.
    SleevePenetration(uid="CBP901AAAA", tag="SP-B-BATH-WC", host_ref="SL-B-FLOOR",
                      position=pt(ft(11, 8), ft(20)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-B-BATH-WC"),
    SleevePenetration(uid="CBP904AAAA", tag="SP-B-BATH-LAV", host_ref="SL-B-FLOOR",
                      position=pt(ft(17), ft(20)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-B-BATH-LAV"),
    # The sauna's two. The pan's is under the centre of the 36" x 36" curbed shower; the floor
    # drain's is the drain body itself, which is why its position and the fixture's are the
    # same point with no `drain_position` override on either.
    SleevePenetration(uid="CBP905AAAA", tag="SP-B-SAUNA-SH", host_ref="SL-B-FLOOR",
                      position=pt(ft(15, 8.5), ft(12, 0.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-SH"),
    SleevePenetration(uid="CBP906AAAA", tag="SP-B-SAUNA-FD", host_ref="SL-B-FLOOR",
                      position=pt(ft(13, 6), ft(12, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-FD"),
    # Where the ceiling collector turns down to become the under-slab building drain
    # (2026-07-30; 4" since the 2026-07-31 building-drain upsize). A 4" waste through cast
    # concrete is a cast-in exactly like the fixture stubs; `mep.sleeve_coverage` holds the
    # crossing to it.
    SleevePenetration(uid="CBP902AAAA", tag="SP-B-SLAB-MAIN", host_ref="SL-B-FLOOR",
                      position=pt(ft(3), ft(15, 6)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6)),
    # The bathroom branch's two under-footing crossings on its way to the main (IRC P2604,
    # the same relieving-arch treatment PR-G-HYDRANT-CW gets under the garage footing).
    # `mep.footing_clearance` requires both: at each one the pipe's crown sits below the
    # footing's -9'-8" bearing plane, so it is a crossing *through* the footing, not a pipe
    # standing clear of its 45° influence line.
    #
    # This one was SP-B-CW-UTIL-DR (FX-1's 1 1/2" arm) until 2026-07-30. The crossing point is
    # unchanged — the new bathroom branch runs the same corridor down the mechanical room, so
    # the hole stays where the concrete crew already had it — but it carries the 3" bathroom
    # branch now. Invert at the crossing is -9'-11 1/8" project, so the centre is -9'-9 5/8" —
    # 1 5/8" below FT-B-CW3's -9'-8" bearing plane, which is what makes this an under-footing
    # crossing rather than a pipe standing inside the footing's 45 degree influence line.
    SleevePenetration(uid="CBP903AAAA", tag="SP-B-CW-BATH-DR", host_ref="FT-B-CW3",
                      position=pt(ft(7), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-9.8)),
    # Under FT-B-STR, where the branch leaves the bathroom westward into the mechanical room.
    # The stair shaft is boxed in cast concrete on three sides, so every service this room
    # gets has to cross one of them: the drain crosses here, below the footing, and the vent
    # and the two supplies cross the wall above (WALL_SLEEVES).
    SleevePenetration(uid="CBP907AAAA", tag="SP-B-STR-BATH-DR", host_ref="FT-B-STR2",
                      position=pt(ft(10), ft(20)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-9.675)),
]

# Horizontal sleeves through the basement's cast concrete walls. The whole ceiling-level
# distribution — collector, branches, supply trunks, hydrant line — has to get past the
# y=18' centre cross walls and out the perimeter, and every one of those crossings is a
# cast-in-place hole the concrete crew sets before the pour (`mep.sleeve_coverage`).
# center_elevation is project-frame absolute (the walls span -9'..0'); positions along
# y=18' keep >= 5" between neighbours so the 4"-tolerance matcher stays unambiguous.
WALL_SLEEVES = [
    # W-B-CW (y=18', x 0..6'-9"), west centre wall — the mechanical wall of the house.
    # Split at N-B-ESS-S on 2026-08-02 for the ESS closet: the three sleeves east of
    # x=6'-9" (BATH1-CW at 7'-4.8", WASH-CW at 8'-0", SAUNA-VENT at 9'-0") now host on
    # W-B-CW3, the stub that forms the closet's south wall. Same concrete, same positions,
    # same runs through them — only the segment they name changed.
    SleevePenetration(uid="CBPW01AAAA", tag="SP-B-CW-WC2", host_ref="W-B-CW",
                      position=pt(m(0.686504), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-1.37)),
    SleevePenetration(uid="CBPW02AAAA", tag="SP-B-CW-SBATH-CW", host_ref="W-B-CW",
                      position=pt(ft(4), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    SleevePenetration(uid="CBPW03AAAA", tag="SP-B-CW-SBATH-DR", host_ref="W-B-CW",
                      position=pt(ft(4, 6.4), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-1.748)),
    SleevePenetration(uid="CBPW04AAAA", tag="SP-B-CW-HYD", host_ref="W-B-CW",
                      position=pt(ft(5), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
    SleevePenetration(uid="CBPW05AAAA", tag="SP-B-CW-WH", host_ref="W-B-CW",
                      position=pt(ft(5, 6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    # The collector's own crossing. centre = invert at y=18' (-1'-9.0" project) + half of
    # 4" — re-solved with the 2026-07-31 building-drain upsize.
    SleevePenetration(uid="CBPW06AAAA", tag="SP-B-CW-MAIN", host_ref="W-B-CW",
                      position=pt(ft(6), ft(18)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=ft(-1.587)),
    SleevePenetration(uid="CBPW07AAAA", tag="SP-B-CW-HW", host_ref="W-B-CW",
                      position=pt(ft(6, 6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.96)),
    # (SP-B-CW-COND stood at (7', 18') until 2026-07-30, for the condensate collector's run up
    # to FX-1's basin. PR-B-COND no longer crosses this wall at all — it now terminates over
    # the sauna's floor drain, which is south of y=18' — so the hole is retired rather than
    # left cast for a route nothing takes, the same call the SUITE drain sleeve got below.)
    # The sauna group's vent crossing, on its way north to the shared radon/vent chase. x=9'
    # is the one free slot on this wall: the supply and drain sleeves either side of it run
    # 2'-3" to 8' at 5"+ pitch, and 9' leaves 12" to the nearest of them and 6" to W-B-STR's
    # west face. Elevation is the run's own interpolated centreline where it passes through.
    SleevePenetration(uid="CBPW24AAAA", tag="SP-B-CW-SAUNA-VENT", host_ref="W-B-CW3",
                      position=pt(ft(9), ft(18)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      purpose=Service.VENT, center_elevation=ft(-1.276)),
    SleevePenetration(uid="CBPW09AAAA", tag="SP-B-CW-BATH1-CW", host_ref="W-B-CW3",
                      position=pt(ft(7, 4.8), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    SleevePenetration(uid="CBPW10AAAA", tag="SP-B-CW-WASH-CW", host_ref="W-B-CW3",
                      position=pt(ft(8), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    # (There is no SUITE drain sleeve here. The ensuite stack drops at x=13' — east of this
    # wall's x 1'..10' extent — and its collector runs south of y=18' to the main, so it
    # never crosses W-B-CW. A sleeve was authored at (9', 18') for a route the run does not
    # take; `mep.sleeve_coverage` had it as the one unclaimed drain sleeve on this wall, and
    # a hole cast for nothing is the same defect as a missing one.)
    # W-B-STR (x=10', y 18'-6"..35'), the stair shaft's west wall — the stair-foot bathroom's
    # only way out to the mechanical room's trunks (2026-07-30). Three crossings at the
    # basement ceiling, spread 6"–18" apart along y so the 4"-tolerance sleeve matcher can
    # tell them apart, and all of them land inside the room's 18'-6"..21'-6" depth:
    #   vent  at y=21'-0", highest of the three (its riser stands 9" further north, inside
    #          the partition itself, and the leg turns west just south of it)
    #   cold   at y=20'-3"
    #   hot    at y=19'-9"
    # The fourth service, the drain, goes *under* the footing instead — SP-B-STR-BATH-DR.
    SleevePenetration(uid="CBPW23AAAA", tag="SP-B-STR-BATH-VENT", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(21)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.VENT, center_elevation=ft(-1.25)),
    SleevePenetration(uid="CBPW25AAAA", tag="SP-B-STR-BATH-CW", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(20, 3)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.9)),
    SleevePenetration(uid="CBPW26AAAA", tag="SP-B-STR-BATH-HW", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(19, 9)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-1)),
    # The laundry tub's branch west to PR-B-MAIN-DRAIN (2026-07-31). Its own crossing at
    # y=18'-9", a foot south of the stair-bathroom group above and 3" clear of W-B-CW2's
    # north face, which is why the tub's waste drops at 18'-9" rather than under its own
    # centre — see plan/fixtures.py. PR-B-LSINK-DRAIN's invert at x=10' is -1'-1 3/4"
    # project, interpolated along its 1.32"/ft fall; the sleeve is cast at the pipe's
    # centerline, 1" (half a diameter) above that, which is what `mep.sewer_exit_invert`
    # matches to within 1/2".
    SleevePenetration(uid="HTE6ZE86KX", tag="SP-B-STR-LSINK-DR", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(18, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.0594)),
    # W-B-CE (y=18', x 18..36) — the kitchen lines' way east. x-columns moved 2026-07-30 with
    # the sink to the north wall and again the same day with the sink/dishwasher flip (see
    # plan/placeables.py's kitchen header); y=18' is W-B-CE's own line and is unaffected.
    SleevePenetration(uid="CBPW12AAAA", tag="SP-B-CE-KITCH-DR", host_ref="W-B-CE",
                      position=pt(ft(28, 7), ft(18)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.17)),
    SleevePenetration(uid="CBPW13AAAA", tag="SP-B-CE-KITCH-CW", host_ref="W-B-CE",
                      position=pt(ft(29, 0.6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    SleevePenetration(uid="CBPW14AAAA", tag="SP-B-CE-KITCH-HW", host_ref="W-B-CE",
                      position=pt(ft(29, 6.6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.97)),
    # W-B-CS2 (x=18', y 13'-10"..18') — the kitchen drain's crossing of the centre line,
    # up at the ceiling well above D-B-GYM's 6'-8" head.
    SleevePenetration(uid="CBPW15AAAA", tag="SP-B-CS2-KITCH", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16, 6)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.56)),
    SleevePenetration(uid="CBPW21AAAA", tag="SP-B-CS2-CW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    SleevePenetration(uid="CBPW22AAAA", tag="SP-B-CS2-HW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(15, 6)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.97)),
    # W-B-CS (x=18', y 0..13'-10") — the condensate collector's two crossings.
    # Re-levelled 2026-07-30 with PR-B-COND's new termination: same hole, same plan position,
    # 3/8" lower than the crossing it was cast for.
    SleevePenetration(uid="CBPW16AAAA", tag="SP-B-CS-COND", host_ref="W-B-CS",
                      position=pt(ft(18), ft(9)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      center_elevation=ft(-1.567)),
    SleevePenetration(uid="CBPW17AAAA", tag="SP-B-CS-COND2", host_ref="W-B-CS",
                      position=pt(ft(18), ft(1, 5.3)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      center_elevation=ft(-0.987)),
    # Perimeter exits.
    # The building drain leaves *under* FT-B-S1, not through W-B-S1 (2026-07-30): with the
    # sewer connection below the slab there is no wall left at that depth — the walls stop at
    # -9'-0", the slab top — so the exit is an under-footing protection sleeve set at the
    # footing centerline, y=0. center_elevation is the pipe centreline where it crosses:
    # PR-B-MAIN-DRAIN's invert there is -10'-6 1/4", so with the 4" building drain
    # (2026-07-31 upsize) the sleeve centre is invert + 2" = -10'-4 1/4" = ft(-10.356).
    # `mep.footing_clearance` is what requires this sleeve (IRC P2604) and matches the run to
    # it; `mep.sewer_exit_invert` holds the invert to the number cast in.
    SleevePenetration(uid="CBPW18AAAA", tag="SP-B-SEWER-EXIT", host_ref="FT-B-S1",
                      position=pt(ft(3), ft(0)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=ft(-10.356)),
    SleevePenetration(uid="CBPW19AAAA", tag="SP-B-S1-HYD", host_ref="W-B-S1",
                      position=pt(ft(5), ft(0, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
    SleevePenetration(uid="CBPW20AAAA", tag="SP-B-N3-HYD", host_ref="W-B-N3",
                      position=pt(ft(5), ft(35, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
]

# The hydrant line's garage-foundation protection (IRC P2604): the buried run passes
# under FT-GF-S-DR at its 6' bury (22" below the footing's 4'-2" bearing plane) inside a
# protection sleeve, and its rise at the hydrant encroaches on FT-GF-W's 45° influence
# line, protected at the marked point. `mep.footing_clearance` requires both.
#
# There was a third sleeve here, SP-G-HYDRANT-PED, the block-out through the 4" topping
# pedestal the barrel used to pass on its way up. The pedestal was retired 2026-08-03
# (params/foundations.py) and its block-out went with it: the barrel now rises through
# SP-G-HYDRANT in SL-G-FLOOR and nothing else.
GARAGE_SLEEVES = [
    SleevePenetration(uid="CGPW01AAAA", tag="SP-GF-S-HYD", host_ref="FT-GF-S-DR",
                      position=pt(ft(5), ft(41)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
    SleevePenetration(uid="CGPW02AAAA", tag="SP-GF-W-HYD", host_ref="FT-GF-W",
                      position=pt(ft(0, 9.6), ft(61, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
]

# Basement-ceiling collector: picks up both WC sleeves, heads to the south-wall sewer
# exit. Starts at SP-M-WC1's new carrier-outlet point on the x=4' wall line (the wall-hung
# WC drops its waste inside W-M-BAE, → SLEEVES). Axis-aligned so the authored length is
# exact (4'-7" + 1' + 18' = 23'-7"); inverts give a comfortable 8"/23'-7" ≈ 0.34"/ft
# slope, well above the 1/8"/ft minimum a 4" line needs (it was sized 3" until the
# 2026-07-31 building-drain upsize), and SP-M-WC2 still ties in at the (3', 18') corner
# fitting.
# Routed 3D drains (2026-07-29 plumbing pass). Every run now carries an invert at every
# vertex (`elevations`), vertical drops are repeated plan points, and the collector rides
# y=16'-6" — a foot clear of the y=18' concrete cross walls it used to be drawn *inside*
# of — crossing them perpendicular through the WALL_SLEEVES above. The first leg falls hard
# (≈2"/ft) so the 46' kitchen branch can hold its own 1/4"/ft and still tie in from above.
#
# The sewer goes out UNDER the slab (2026-07-30, owner's call: the municipal connection is
# buried below the slab, as Minnesota does to keep it under frost). That changes where the
# building drain leaves and it is worth writing down why the geometry has only one answer:
#
#   * the foundation walls stop at -9'-0", which is the *top* of the slab, so there is no
#     wall left to pass through below it — the old exit at -2'-3" through W-B-S1 was 2'-3"
#     under grade, above MN's 42" frost line, which is the thing the owner's note rules out;
#   * the footings sit -9'-8" to -9'-0", so the drain leaves *beneath* FT-B-S1 inside a
#     protection sleeve — IRC P2604, the same relieving-arch treatment PR-G-HYDRANT-CW
#     already gets under the garage footing.
#
# So the collector stays hung at the basement ceiling where it belongs (that is where the
# upper-floor stacks arrive), and at its downstream end it drops through the slab at
# (3', 15'-6") — SP-B-SLAB-MAIN — and runs under the slab to the exit. That drop is also
# what makes every slab fixture in the basement possible: see PR-B-BATH-DRAIN and
# PR-B-SAUNA-DRAIN below. (Until 2026-07-30 there was exactly one such fixture, FX-1.)
DRAINS = [
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), ft(22, 7)), pt(ft(6), ft(22, 7)), pt(ft(6), ft(16, 6)),
                  pt(ft(3), ft(16, 6)), pt(ft(3), ft(15, 6)), pt(ft(3), ft(15, 6)),
                  pt(ft(3), ft(-1))),
            diameter=inch(4), material="pvc",
            # …ceiling collector… | 1' more at the ceiling | drop through the slab |
            # under-slab to the exit. The drop is at y=15'-6", not at the collector's own
            # y=16'-6" turn: 5'-6" down under the slab the pipe sits 10 5/8" below FT-B-CW's
            # bearing plane, so it needs at least that much lateral clearance from the
            # footing's 45° influence line and 16'-6" gave only 8". y=15'-6" gives 20".
            # -1.1 and -1.55 are basement-relative: -10'-1 1/5" and -10'-6 3/5" project, so
            # the 16'-6" under-slab leg falls 5.4" (0.33"/ft — a 4" line only needs
            # 0.125"/ft) and its 4" crown clears the slab underside by 5.7". Sized 4"
            # (2026-07-31): the rolled-up basement load is 42 DFU, past the 35 a 3"
            # horizontal branch carries (Table 703.2); inverts stayed put, only the crown
            # rose.
            elevations=(ft(9), ft(8), ft(7), ft(6, 11.2), ft(6, 10.9), ft(-1.1),
                        ft(-1.55)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC", "FX-M-KITCH-SINK",
                    "FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    # Re-routed 2026-07-30 with the sink's move to the north wall, then re-routed again the
    # same day with the sink/dishwasher flip: straight down the deck sleeve's own column (no
    # jog — a jog at y=35' would run right along W-B-N1's inner concrete face) to the same
    # W-B-CE/W-B-CS2 crossings (SP-B-CE-KITCH-DR, SP-B-CS2-KITCH) and west to the main stack
    # tie-in — that route is fixed by the basement framing, not by where in the kitchen the
    # sink sits. Elevations re-solved to land on both sleeves' cast centerlines exactly, at
    # >= 0.25"/ft on every segment.
    PipeRun(uid="S0Y00EZNNG", tag="PR-B-KITCH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(28, 7), ft(35)), pt(ft(28, 7), ft(35)),
                  pt(ft(28, 7), ft(16, 6)), pt(ft(6), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 2.9), ft(7, 8.44), ft(6, 11.57)),
            serves=("FX-M-KITCH-SINK",)),
    # BATH2's WC, at its re-pointed flange on the wet wall (→ SP-M-WC2).
    PipeRun(uid="CBPD01AAAA", tag="PR-B-WC2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(m(0.686504), m(6.14439)), pt(m(0.686504), m(6.14439)),
                  pt(m(0.686504), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9), ft(8), ft(7, 2), ft(7)),
            serves=("FX-M-BATH2-WC",)),
    PipeRun(uid="CBPD02AAAA", tag="PR-B-LAV1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(6), m(7.00891)), pt(ft(6), m(7.00891)), pt(ft(6), ft(22, 7))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(8, 0.2)),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPD03AAAA", tag="PR-B-TUB2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(7, 4), ft(19, 4.8)), pt(ft(7, 4), ft(19, 4.8)),
                  pt(ft(6), ft(19, 4.8))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 7.2)),
            serves=("FX-M-BATH2-TUB",)),
    PipeRun(uid="CBPD04AAAA", tag="PR-B-SH2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1, 9), ft(17, 3)), pt(ft(1, 9), ft(17, 3)),
                  pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 1.2)),
            serves=("FX-M-BATH2-SH",)),
    PipeRun(uid="CBPD05AAAA", tag="PR-B-SINK2-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(1), ft(16, 6)), pt(ft(1), ft(16, 6)), pt(ft(3), ft(16, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 0.6)),
            serves=("FX-M-BATH2-SINK",)),
    PipeRun(uid="CBPD06AAAA", tag="PR-B-WASH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(8), ft(20)), pt(ft(8), ft(20)), pt(ft(6), ft(20))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 8.4)),
            serves=("FX-M-LAUNDRY",)),
    # The laundry tub (2026-07-31). Down its own cast sleeve under the basin, then 5'-9" west
    # along the basement ceiling to PR-B-MAIN-DRAIN's x=6' collector — the same two-move shape
    # as PR-B-SINK2-DRAIN and PR-B-WASH-DRAIN above, because the 9" concrete deck leaves no
    # other way off this floor.
    #
    # It is the tub's trap arm as well as its branch, and that is what sizes it: the vent is
    # PR-M-WC-VENT's leg standing in W-M-BA2E at x=8', which this run passes 3'-9" from, and
    # Table 1002.2 allows 60" on 2" against 42" on 1 1/2". Falls 7.6" over the 5'-9" horizontal
    # (1.32"/ft, well over the 1/4"/ft floor) and arrives at 7'-5", about 6" above the
    # collector's interpolated invert at this y — a branch tees into the top of a horizontal
    # drain, not into its side.
    PipeRun(uid="ZK49S63X8X", tag="PR-B-LSINK-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 9), ft(18, 9)), pt(ft(11, 9), ft(18, 9)),
                  pt(ft(6), ft(18, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(9), ft(8, 0.6), ft(7, 5)),
            serves=("FX-M-LAUNDRY-SINK",)),
    # --- the two basement slab-fixture branches (2026-07-30) ---------------------------
    #
    # Every fixture on these two runs stands *on* the basement floor, so none of them can
    # reach the ceiling collector 6'-6" overhead: each drops through its cast stub and runs
    # under the slab to PR-B-MAIN-DRAIN's under-slab leg at x=3'. That leg exists because the
    # sewer goes out under the slab (the 2026-07-30 decision above); before it there was no
    # gravity drain anywhere on this floor, which is why the basement had one fixture.
    #
    # Inverts are basement-relative, so -0.7 reads as 8 2/5" below the finish floor. Both runs
    # fall a uniform 0.3"/ft — above the 1/4"/ft `mep.drain_slope` minimum for <= 3" with
    # enough margin that no segment lands on the threshold — and both stay deep enough that
    # their crowns keep the 1" of bedding `mep.under_slab_burial` wants below the slab's
    # -9'-3 1/2" underside, while arriving at the main between its invert and its crown so the
    # tie is a wye into the upper half of the pipe rather than a bottom entry.
    #
    # A note on what these runs are NOT on: neither fixture group appears in
    # PR-B-MAIN-DRAIN's `serves`. That follows the convention FX-1 set — a slab branch
    # carries its own fixtures and the main lists the stacks it collects — and since
    # 2026-07-31 the convention is load-safe: `mep.pipe_sizing` rolls every drain's load
    # up through the routed geometry (resolve/mep.py::accumulated_serves), so these 8 DFU
    # land on the main whether or not they are re-listed. That rollup is what showed the
    # building drain carrying 42 DFU against the 35 a 3" line takes, and why it is 4" now.
    #
    # The bathroom branch. Its route is the one FX-1's used, extended east into the new room:
    # 3" out of the WC's closet bend at (11'-8", 20'), west under FT-B-STR's bearing plane in
    # a protection sleeve (SP-B-STR-BATH-DR), across the mechanical room, under FT-B-CW in the
    # second sleeve (SP-B-CW-BATH-DR — FX-1's old crossing, upsized in place), then west to the
    # main at (3', 15'-6"). Going west rather than straight south is deliberate: south would
    # cross under W-B-CW2, which has no footing in params/foundations.py to hang a protection
    # sleeve on, and a crossing that depends on a missing footing is not a crossing that has
    # been detailed.
    PipeRun(uid="CBPD07AAAA", tag="PR-B-BATH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(11, 8), ft(20)), pt(ft(11, 8), ft(20)), pt(ft(7), ft(20)),
                  pt(ft(7), ft(15, 6)), pt(ft(3), ft(15, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(0), ft(-0.758), ft(-0.875), ft(-0.988), ft(-1.088)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # The lavatory's own 1 1/2" arm, west along the room to the WC's branch — the same
    # relationship PR-B-LAV1-DRAIN has to the main-floor collector. It arrives at -7 5/8",
    # inside the 3" branch's upper half at that point (invert -8 5/8", crown -5 5/8").
    PipeRun(uid="CBPD09AAAA", tag="PR-B-BATH-LAV-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(17), ft(20)), pt(ft(17), ft(20)), pt(ft(11, 8), ft(20))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 6), ft(-0.52), ft(-0.653)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna group: the curbed pan's 2" drop at (15'-8 1/2", 12'-0 3/16"), south to the
    # wet floor's own line, west through the floor drain at (13'-6", 12'-9"), then straight
    # west under the workshop to the main. One 2" branch carries both — 4 DFU against the 6 a
    # 2" horizontal branch takes — and passes under no footing on the way: W-B-SA-W is a
    # framed partition on the slab, and the run stops 1'-8" short of FT-B-W2 while sitting only
    # 5" below its bearing plane, so it stays outside the 45° influence line.
    PipeRun(uid="CBPD08AAAA", tag="PR-B-SAUNA-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(15, 8.5), ft(12, 0.1875)), pt(ft(15, 8.5), ft(12, 0.1875)),
                  pt(ft(15, 8.5), ft(12, 9)), pt(ft(13, 6), ft(12, 9)),
                  pt(ft(3), ft(12, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0, 2), ft(-0.715), ft(-0.733), ft(-0.788), ft(-1.051)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
    # The floor drain's own way through the slab, and the whole of it: a floor drain has no
    # trap arm above the floor to draw — the body *is* the penetration — so this run is one
    # vertical drop from the strainer at finish floor onto the branch above. It is authored
    # separately rather than as a vertex on the branch because a mid-run vertex crosses no
    # slab, and `mep.sleeve_coverage` correctly reads a cast stub that no run passes through
    # as either a stale sleeve or a mis-routed run.
    PipeRun(uid="CBPD10AAAA", tag="PR-B-SAUNA-FD-DROP", system=PipeSystem.DRAIN,
            path=(pt(ft(13, 6), ft(12, 9)), pt(ft(13, 6), ft(12, 9))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0), ft(-0.788)),
            serves=("FX-B-SAUNA-FD",)),
]

# Second-storey waste stacks, filed on ``main`` (datum 0' = the deck they drop through)
# so the elevations read as heights on the storey the pipe is actually visible from:
# +9'-9" is the second floor's underside, the negative inverts are the basement ceiling.
SECOND_DRAINS = [
    PipeRun(uid="CMPD07AAAA", tag="PR-M-S-BATH1-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(5), ft(26, 4)), pt(ft(5), ft(26, 4)),
                  pt(ft(4, 6.4), ft(17, 4.8)), pt(ft(3), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.5), ft(-1.9), ft(-2)),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    PipeRun(uid="CMPD08AAAA", tag="PR-M-S-SUITE-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(13), ft(16, 10.8)), pt(ft(13), ft(16, 10.8)),
                  pt(ft(6, 2.4), ft(16, 8.4)), pt(ft(6), ft(16, 6))),
            diameter=inch(3), material="pvc",
            elevations=(ft(9, 9), ft(-1.5), ft(-1.917), ft(-1.983)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

# Heat-pump condensate (plans/TODO.md §condensate): a collected 3/4" air-gap line at the
# basement ceiling, falling continuously to terminate over a receptor — never tied into the
# sanitary system. PR-M-COND-HEADS drops the two main-storey
# wall heads (master bed + living room, both by the centre line on the south wall)
# through SP-M-COND and hands off to the basement collector, which also picks up the gym
# head. EQ-S-HP1-AH's line down the second-floor chase is still undrawn — the chase route
# to this collector is a follow-up, recorded rather than guessed.
CONDENSATE_MAIN = [
    PipeRun(uid="CMPC02AAAA", tag="PR-M-COND-HEADS", system=PipeSystem.DRAIN,
            path=(pt(ft(17, 6), ft(1)), pt(ft(17, 6), ft(1)), pt(ft(27), ft(9))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(2, 6), ft(-1), ft(-1.342))),
]

# --- RM-M-LAUNDRY: the two air gaps (2026-07-31) --------------------------------------
#
# Both of this room's indirect wastes are air-gapped, and neither of them is a fitting the
# model has a name for, so they are drawn as the pipe they are and explained here.
#
# The washer's is the ordinary one: a 2" standpipe rising in W-M-BA2E's stud bay behind the
# machine, its top at 36" — inside the 18"..42"-above-the-trap band, and above the machine's
# own tub so it cannot back-siphon. The discharge hose is *dropped into* that standpipe, not
# sealed to it, and that open annulus is the air gap. A backup therefore spills out of the
# box at 36" rather than into the machine. Below the deck the trap and the branch are already
# drawn as PR-B-WASH-DRAIN; this run is the leg above the deck that was missing.
#
# The dryer's is the new one, and it is the reason this room needs no duct. A ventless
# heat-pump dryer condenses its moisture instead of blowing it outdoors; the pump lifts that
# condensate out of the machine and it has to land somewhere that is not the sanitary system.
# It lands over the laundry tub — 3'-0", which is 2" clear of the tub's 34" flood rim, twice
# the 1" a 3/4" line needs. A tub is what an air gap wants (trapped, sees water in normal
# use), the same reading that put PR-B-COND over FX-B-SAUNA-FD rather than over a lavatory
# when FX-1 was retired.
#
# The condensate line stays on this floor: PR-B-COND is a basement collector terminating over
# the sauna floor drain and there is no reason to drop 9' and cross the house when the
# receptor is 2' away. `mep.drain_slope` grades it as the DRAIN it is filed as and holds every
# segment to IRC P3005.3's 1/4"/ft, which a 22" run at 12" of fall per leg clears many times
# over. Neither run declares `serves`: a standpipe's fixture units are counted on the branch
# below it, and condensate is not a drainage fixture at all.
LAUNDRY_MAIN = [
    PipeRun(uid="P8A9ADNE6N", tag="PR-M-WASH-STANDPIPE", system=PipeSystem.DRAIN,
            path=(pt(ft(8), ft(20)), pt(ft(8), ft(20))),
            diameter=inch(2), material="pvc",
            elevations=(ft(3), ft(0)),
            wall_refs=("W-M-BA2E",)),
    # Both ends ride their fixtures: +8" in y on 2026-08-03 with the stack and the tub, when
    # W-M-CLN moved to y=18'-0". The run's shape, length and fall are unchanged — it leaves
    # the dryer's east face and turns south over the tub exactly as before.
    PipeRun(uid="5NYN0SKYSV", tag="PR-M-DRYER-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(10, 8), ft(19, 8.635)), pt(ft(11, 9), ft(19, 8.635)),
                  pt(ft(11, 9), ft(18, 11.135))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(5), ft(4), ft(3))),
]

# Re-terminated 2026-07-30, when FX-1 was retired: the collector used to run north across
# W-B-CW and air-gap over that sink's basin, and it now stops short of that wall and
# terminates over FX-B-SAUNA-FD instead — the sauna wet floor's drain (owner's call). A
# condensate air gap wants a trapped receptor that sees water in normal use, which a shower
# floor's drain is and a finished bathroom's lavatory is not.
#
# The route west across the sauna ceiling is the one this run already took (SP-B-CS-COND, the
# cast crossing of the centre wall at (18', 9'), is unchanged in plan and re-levelled to the
# new interpolated centreline); it runs above the sauna's hung drop ceiling. What is new is
# the last leg: north to y=12'-9" and then straight down in a boxed chase against W-B-SA-N,
# which is why the floor drain sits 12" off that wall rather than mid-floor — a 3/4" drop in
# the open middle of a tiled wet room is not a detail anyone would build. The air gap is 9"
# above the finish floor.
#
# 0.3"/ft of fall across all three horizontal legs — more than a condensate line needs, but
# `mep.drain_slope` grades this run as what it is filed as, a DRAIN, and holds every segment to
# IRC P3005.3's 1/4"/ft. It drains toward the receptor over its whole length either way.
CONDENSATE = [
    PipeRun(uid="CBPC01AAAA", tag="PR-B-COND", system=PipeSystem.DRAIN,
            path=(pt(ft(27), ft(9)), pt(ft(18), ft(9)), pt(ft(13, 6), ft(9)),
                  pt(ft(13, 6), ft(12, 9)), pt(ft(13, 6), ft(12, 9))),
            diameter=inch(0.75), material="pvc",
            elevations=(ft(7, 7.9), ft(7, 5.2), ft(7, 3.85), ft(7, 2.725),
                        ft(0, 9))),
]

# --- Vent branches: wet wall -> shared chase ----------------------------------------
# None of the water-closet wet walls continues to the storey above (W-M-BAE and W-M-BA2E
# die at the main-floor top plate; W-S-BD-N dies under the cathedral attic), so no vent can
# simply rise inside them. They don't have to: VR-M-RADON-VENT below is already a shared
# radon/plumbing chase running the full height of the house at (1', 34'-6") — moved to the
# NW corner 2026-07-28, inside RM-M-MECH's framed closet and RM-S-BATH1's NW notch (was
# (3', 33'), floating in open mudroom floor space) — and a vent may run horizontally once
# it is above every served fixture's flood-level rim. These are the runs that get it
# there — authored, because the engine never routes pipe on its own, and validated by
# `mep.vent_reachability` (must touch the wet wall, must land on the chase).
#
# Both runs sit inside the floor system over their storey's 9' top plate, drilled through
# the I-joist webs, and fall ~1/8"/ft back toward the fixtures so condensate returns to the
# drainage system rather than pooling in the horizontal leg.
VENT_BRANCHES_MAIN = [
    # Bath2 takeoff on W-M-BA2E (x=8') -> across the hall -> bath1 takeoff on W-M-BAE
    # (x=6') -> north through the storage-room ceiling -> chase. 2" for two water closets.
    PipeRun(uid="CMP906AAAA", tag="PR-M-WC-VENT", system=PipeSystem.VENT,
            path=(pt(ft(2, 3.6), ft(17, 3.6)), pt(ft(8), ft(18)), pt(ft(8), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5.5),
            # FX-M-BATH1-LAV joined on 2026-07-30, when FX-LAV-COMPACT finally declared
            # Service.VENT. No new pipe: this run's x=6' leg is W-M-BAE's own stud bay and it
            # passes 1'-0" north of the lavatory's drain point at (6', 23'), so the trap arm
            # ties into the leg already drawn there — well inside Table 1002.2's 42" for 1.5".
            # FX-M-LAUNDRY-SINK joined on 2026-07-31, on the same terms: this run's x=8' leg is
            # W-M-BA2E's own stud bay and PR-B-LSINK-DRAIN arrives against that wall 3" south
            # of the leg's start, so the tub wet-vents off the laundry stack with no new pipe.
            # The trap arm is the 45" that branch runs below the deck, inside Table 1002.2's
            # 60" for 2". The washer itself needs no entry — an Appliance declares no
            # Service.VENT — but its standpipe (PR-M-WASH-STANDPIPE) is the physical riser
            # this tee sits beside.
            serves=("FX-M-BATH2-WC", "FX-M-BATH1-WC", "FX-M-BATH2-SH",
                    "FX-M-BATH2-TUB", "FX-M-BATH1-LAV", "FX-M-LAUNDRY-SINK")),
    # Kitchen sink. Re-routed 2026-07-30 with the sink's move to the north wall: W-M-N1
    # *does* continue to the storey above at this x (W-S-N1 stacks on it, into RM-S-BED3's
    # wall), so `mep.vent_reachability` is still satisfied by the wet-wall path. x=32'-8" is
    # the riser's bay — clear of WIN-M-KITCH's RO (29'-5".."31'-8"), WIN-M-KITCH-N's RO
    # (33'-5".."34'-7") and, one storey up, WIN-S-HALL-N's RO (26'-9".."29'-3" since the
    # 2026-07-30 facade pass stacked it on WIN-M-KITCH's column) — rather than
    # x=30'-7" under the sink itself, which sits inside two stacked window ROs. From there it
    # turns west in the same FS-SECOND joist bay as before, y=24'-8" (bays are 8"+n*16"; this
    # one passes south of FO-S-STAIR, which starts at y=25'-2 3/8", and north of both trunk
    # ducts at 20'-8" and 23'-4"), then north to the shared radon/vent chase at (1', 34'-6").
    # It rises 6" over its length so condensate drains back to the fixture.
    PipeRun(uid="ZTQRPPRATP", tag="PR-M-KITCH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(32, 8), ft(35, 9)), pt(ft(32, 8), ft(24, 8)),
                  pt(ft(1), ft(24, 8)), pt(ft(1), ft(34, 6))),
            diameter=inch(1.5), start_elevation=ft(9, 3), end_elevation=ft(9, 9),
            serves=("FX-M-KITCH-SINK",)),
]

VENT_BRANCHES_SECOND = [
    # Hall-bath takeoff on W-S-BD-N (y=26'-4") -> west to the chase line -> north to the
    # chase.
    PipeRun(uid="CSP901AAAA", tag="PR-S-BATH1-VENT", system=PipeSystem.VENT,
            path=(pt(ft(9, 8.4), ft(31)), pt(ft(5), ft(26, 4)), pt(ft(1), ft(26, 4)),
                  pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 4),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # The suite bath's own vent: takeoff on its west wet wall W-S-DC2 (x=9'-7 1/2"), north
    # through the landing and the hall bath, then west along y=34'-6" to the shared
    # radon/plumbing chase. It runs up the x=9'-7 1/2" line rather than joining the hall
    # bath's run at x=1' so the two branches never share a leg.
    #
    # The chase here is VR-M-RADON-VENT's, at (1', 34'-6") — now the *same* shaft as the
    # 2'x2' mechanical chase in the hall bath's NW corner (W-S-CH-W/CH-S, moved there
    # 2026-07-28 from the NE corner specifically so it could carry this riser; storeys/
    # second.py).
    PipeRun(uid="CSP902AAAA", tag="PR-S-SUITEBATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(13, 10), ft(16)), pt(ft(9, 7.5), ft(20)),
                  pt(ft(9, 7.5), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

# --- Ventilation: ERV fresh-air / stale-air trunks in the FS-SECOND joist bays -------
# These are ventilation trunks, not heating ducts — EQ-B-ERV (plan/electrical.py) is what
# they connect to, and nothing on the air side carries heat. Sized for the ASHRAE 62.2 whole-
# house rate rather than a furnace CFM: 0.03 x 5,115 ft2 conditioned + 7.5 x (5 bedrooms + 1)
# = 198 cfm required, 210 cfm on the machine (2026-08-01, see EQ-T-ERV), which at 10"x6"
# (0.42 ft2) is ~505 fpm — quiet enough to run continuously, where the 12"x8"/14"x8" furnace
# trunks they replace were roughly four times oversized.
#
# The balanced pair is modeled as the ERV's SUPPLY and RETURN trunks; dedicated stale
# pulls (the hall bath's shower takeoff) use DuctSystem.EXHAUST. Distribution now reaches all
# four storeys: trunks ride joist bays where a floor system exists (FS-SECOND under the
# second storey, FS-SECOND over the main storey's ceiling, FS-ATTIC under the attic) and
# drop to CHASE routing in the basement, whose ceiling is the SL-M-DECK concrete.
DUCTS = [
    # DU-M-ERV-SUP is gone (2026-07-29, with the terminal reduction). Every terminal it fed
    # was either dropped or flipped to stale pickup: the second storey now takes its fresh
    # air off System 1's chase — REG-S-HP-BED1/2/3 on DU-S-HP-SUP, the suite on
    # DU-S-HP-SUITE — and gives stale air back on DU-M-ERV-RET, which is why that trunk
    # below is untouched and carries seven pickups. A supply trunk with no terminal on it
    # is not a spare, it is a duct nobody would ever build, so it is deleted rather than
    # shortened to a stub. (plan/electrical.py and plans/electrical_notes.md were updated
    # to the per-storey topology on 2026-07-30; the main storey's own pair is
    # DU-M1-ERV-SUP/RET below.)
    DuctRun(uid="CMD902AAAA", tag="DU-M-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(23, 4)), pt(ft(32), ft(23, 4))), width=inch(10), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    # Hall bath shower exhaust: a dedicated stale pull in the FS-ATTIC joist bay centred at
    # y=32'-8" (8" + 24*16"), right over FX-S-BATH1-SH at (5', 33'). It crosses the
    # SL-D-SHOWER cut plane (x=5', plan/views.py) inside the shower's reach, which is what
    # makes the detail's `shower_hrv_duct` component draw the takeoff.
    DuctRun(uid="CSDV01AAAA", tag="DU-S-BATH1-EXH", system=DuctSystem.EXHAUST,
           path=(pt(ft(3), ft(32, 8)), pt(ft(17), ft(32, 8))), width=inch(6), depth=inch(4),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
]

# Main-storey distribution rides the FS-SECOND joist bays overhead (the main ceiling is
# that floor's underside) in its own pair of bays — 12'-8" (8"+9*16") and 15'-4"
# (8"+11*16") — south of both second-storey trunks and clear of FO-S-STAIR.
DUCTS_MAIN = [
    DuctRun(uid="CMDV01AAAA", tag="DU-M1-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(4), ft(12, 8)), pt(ft(32), ft(12, 8))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    DuctRun(uid="CMDV02AAAA", tag="DU-M1-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(15, 4)), pt(ft(32), ft(15, 4))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
]

# Basement trunks leave EQ-B-ERV in the furnace room and run exposed-in-chase under the
# SL-M-DECK concrete — no joist bays to ride, so CHASE routing and no floor_ref.
DUCTS_BASEMENT = [
    DuctRun(uid="CBDV01AAAA", tag="DU-B-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(18)), pt(ft(27), ft(18)), pt(ft(27), ft(9))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
    DuctRun(uid="CBDV02AAAA", tag="DU-B-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(8)), pt(ft(16), ft(8))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
    # The stair-foot bathroom's branch off that trunk (2026-07-30). 6" x 4" for one 50 cfm
    # terminal, taken off at y=20' and run east into the room — which means a cast opening
    # through W-B-STR2's 12" concrete at the ceiling, on the same line as the room's three
    # service sleeves and set before the pour with them. Ducts carry no SleevePenetration in
    # this model (the trunk it tees off already crosses W-B-CW the same way), so the opening
    # lives in this comment and on the concrete crew's drawing rather than as an element.
    DuctRun(uid="CBDV03AAAA", tag="DU-B-ERV-BATH", system=DuctSystem.EXHAUST,
           path=(pt(ft(5), ft(20)), pt(ft(11, 8), ft(20))),
           width=inch(6), depth=inch(4), routing=DuctRouting.CHASE),
    # The sauna's own fresh-air branch (2026-07-29). 4"x4" — a sauna wants a trickle it can
    # shut, not a room's worth of air — taken off the supply trunk where it turns east at
    # (5', 18') and run south down the workshop side of W-B-SA-W to the heater line, then
    # east into the room above EQ-B-SAUNA-HTR. It ends over the heater on purpose: fresh air
    # dropped onto the stones is what drives the convection loop down to REG-B-EXH2 at the
    # floor, which is the only way a sealed hot room turns over at all.
    DuctRun(uid="CBDV04AAAA", tag="DU-B-SAUNA-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(5), ft(18)), pt(ft(5), ft(8, 9)), pt(ft(9, 9.8125), ft(8, 9))),
           width=inch(4), depth=inch(4), routing=DuctRouting.CHASE),
]

# Attic distribution rides the FS-ATTIC joist bays. The attic went the same way the second
# storey did, one step further (2026-07-30): DU-A-ERV-SUP is gone entirely. Its one
# terminal, REG-A-SUP1, was made redundant by REG-A-HP-WEST — a floor boot off System 1's
# DU-S-HP-SUITE branch directly below (REGISTERS_ATTIC below) — and a fresh trunk with no
# terminal on it is a duct nobody would build, so it is deleted rather than stubbed, exactly
# as DU-M-ERV-SUP was. The attic's air pattern is now the storey pattern everywhere:
# conditioned/fresh air in off System 1, stale air out through the one ERV extract.
#
# The surviving return starts at x=2', beside the maintenance shaft at (1', 34'-6") where
# VR-M-RADON-VENT's radon/plumbing riser comes up through every storey (RADON_SUMP /
# VENT_RISERS below) — the ERV branch rides that same shaft up from the basement — and runs
# 4'-0" east to its terminal in the bay centred at 31'-4" (8"+23*16"); DU-S-BATH1-EXH's bay
# at 32'-8" stays free. Nothing here goes near FO-A-STAIR (y 5'-9 5/8"..8'-9 5/8").
#
# The attic loses no required coverage: RM-A-STUDY is fed by REG-A-HP-STUDY off System 1's
# own attic branch, and RM-A-WEST by REG-A-HP-WEST off the suite branch.
DUCTS_ATTIC = [
    DuctRun(uid="CADV02AAAA", tag="DU-A-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(2), ft(31, 4)), pt(ft(6), ft(31, 4))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
]

# --- System 1: the conditioned-air chase (plans/TODO.md §HVAC) -----------------------
# EQ-S-HP1-AH (plan/electrical.py) hangs INSIDE the dropped soffit box at its south end
# (y 6'..9'-7", over RM-S-STUDY2's north strip — see the placement note there) and feeds
# ONE straight supply trunk north along the second-floor hallway inside that soffit
# (SOFFITS in plan/storeys/second.py), with a short return-plenum stub at its rear — the
# return grille sits right at the unit, with the ERV's fresh feed wyed in behind it
# (DU-S-ERV-HP-FEED below). CHASE
# routing and no `floor_ref`: this duct is not in a joist bay, it is in a framed box below
# the ceiling, so the joist-bay geometry checks correctly do not apply to it — and its two
# crossings of the centre bearing line at x=18' are legal for the same reason.
#
# The hall is x 18'-2 3/4" .. 21'-8" clear, so the two ducts sit side by side at x=19'-4"
# (supply) and x=20'-8" (return) with the soffit spanning the full hall width.
#
# `design_cfm` is authored intent, not a solved airflow — this is a straight-run duct meant
# to operate at low flow, which is the whole reason one 24k unit covers the upstairs. The
# 14x8 trunk at 750 cfm is ~965 fpm; the return keeps the same section over its short stub
# (the two coexist side by side only at SF-S-DUCT's south end now).
DUCTS_HVAC_SECOND = [
    # Starts at y=9'-7" — EQ-S-HP1-AH's discharge face — since 2026-07-30: the unit lives
    # INSIDE the soffit box at its south end (y 6'..9'-7", see plan/electrical.py), so the
    # trunk is everything north of the case.
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(9, 7)), pt(ft(19, 4), ft(33))),
            width=inch(14), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=750),
    # The return is a plenum stub, not a trunk (2026-07-30): REG-S-HP-RET sits right at
    # EQ-S-HP1-AH's rear corner, and this 6" of duct is the box section carrying grille
    # air to the unit's bottom-return opening. The rooms do NOT return to the AH: their
    # only extract is the ERV's stale pickups (REGISTERS below), and the hall — fed back
    # by every door undercut — is the single place the AH breathes from. That is the
    # loose coupling the mixing design wants: the ERV's balance is set by its own
    # terminals, the AH just recirculates the hall plus whatever DU-S-ERV-HP-FEED
    # injects behind its grille.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(ft(20, 8), ft(9, 8)), pt(ft(20, 8), ft(9, 2))),
            width=inch(14), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=750),
    # The west branch to RM-S-SUITE, rerouted 2026-07-30. It tees off DU-S-HP-SUP at the
    # centreline of D-S-SUITE (y=14'-1 7/8") and goes straight through W-S-C2B *above the
    # door* — through the cripple zone between the door's header and the top plate, which
    # an 8"-deep duct riding the 14" soffit drop (z ~7'-10"..8'-6" against a ~7'-4" header
    # top and a 9'-0" plate) clears — then west down the suite's entry arm (y 12'-5" ..
    # 15'-11", RM-S-SUITE's own floor area) to the grille. 6'-10" of 10x8 replaces the old
    # 10'-10" detour at y=20'-4" that crossed RM-S-SUITEBATH; the arm was always the short
    # straight route, it just took SF-S-SUITE moving over it (plan/storeys/second.py). It
    # stops about D-S-SUITEBATH — the soffit ends there too, and the grille in the box's
    # west end face throws the rest of the way down the arm and into the suite.
    #
    # 250 cfm now, not 150: the run feeds two terminals — REG-S-HP-SUITE at its west end
    # and REG-A-HP-WEST, a floor boot up through FS-ATTIC into RM-A-WEST directly above
    # the run. 250 cfm through 10x8 is ~450 fpm, still quiet enough for a bedroom ceiling.
    DuctRun(uid="CSDH03AAAA", tag="DU-S-HP-SUITE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(14, 1.875)), pt(ft(12, 6), ft(14, 1.875))),
            width=inch(10), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=250),
    # The ERV -> System 1 fresh-air feed (2026-07-30): the one place fresh air enters the
    # heat-pump loop. It taps DU-M1-ERV-SUP where that trunk crosses under the hall
    # (y=12'-8", FS-SECOND joist bay), rises into SF-S-DUCT's box — the lane DU-S-HP-RET
    # vacated when it became a stub — and runs south at x=20'-8" to inject just behind
    # REG-S-HP-RET through a 45-degree wye into the return plenum. The wye (a mixing box in
    # effect) rather than hard-ducting ERV to AH is deliberate: the two machines run on
    # independent schedules, so each must breathe without the other — the AH pulls hall air
    # when the ERV is off, and the ERV supplies past a stopped blower without backpressure.
    # 6" is the biggest round the joist-bay tap takes, and at ~100 cfm (the storey's share
    # of the whole-house rate) it runs ~510 fpm. The vertical from the FS-SECOND bay up
    # into the soffit is not drawn (DuctRun carries no elevation) — same status as
    # EQ-S-HP1-AH's condensate drop, recorded in plans/TODO.md.
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            path=(pt(ft(20, 8), ft(12, 8)), pt(ft(20, 8), ft(10))),
            width=inch(6), depth=inch(6), routing=DuctRouting.CHASE, design_cfm=100),
]

# Terminals off the chase. Each bedroom grille sits just inside the bedroom at the hallway
# wall (interior face x=22'-2 3/4"), fed by a short boot through that wall out of the
# soffit — the boot is a detail, not a run, so it carries no DuctRun of its own; the
# grille's `duct_ref` names the trunk it comes off. All of them are ceiling grilles in the
# soffit face at 8'-0" (9'-0" ceiling less the 12" drop).
#
# RM-S-SUITE is in EQ-S-HP1-AH's zone_rooms and has its terminal: REG-S-HP-SUITE, off the
# DU-S-HP-SUITE branch above. Since the 2026-07-30 reroute the branch enters over D-S-SUITE
# and runs down the suite's entry arm to about the bathroom door, and the grille sits at
# the branch's west terminus (12'-6", 14'-1 7/8") in SF-S-SUITE's west end face, throwing
# the rest of the way down the arm and into the suite's main volume where the arm opens
# out at x=9'-7 1/2".
#
# The suite's ERV supply (REG-S-SUP6) is gone rather than kept alongside: this branch is
# what makes it redundant.
REGISTERS_HVAC_SECOND = [
    Register(uid="CSRH01AAAA", tag="REG-S-HP-BED1", kind=DuctSystem.SUPPLY, room="RM-S-BED1",
             position=pt(ft(22, 6), ft(13, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH02AAAA", tag="REG-S-HP-BED2", kind=DuctSystem.SUPPLY, room="RM-S-BED2",
             position=pt(ft(22, 6), ft(22, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH03AAAA", tag="REG-S-HP-BED3", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
             position=pt(ft(22, 6), ft(31, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # "Near the stairs": in the hall band west of the centre line, just south of the stair
    # well's south edge (the well is x 11'..18', y 25'..36').
    Register(uid="CSRH04AAAA", tag="REG-S-HP-STAIR", kind=DuctSystem.SUPPLY, room="RM-S-HALL",
             position=pt(ft(17, 6), ft(24)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The suite's supply, in SF-S-SUITE's soffit face at the branch's west terminus,
    # throwing west out of the entry arm. 7'-10" because SF-S-SUITE drops 14" off the
    # 9'-0" ceiling.
    Register(uid="CSRH06AAAA", tag="REG-S-HP-SUITE", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
             position=pt(ft(12, 6), ft(14, 1.875)), duct_ref="DU-S-HP-SUITE",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 10))),
    # The one return, at the hall's south end right AT EQ-S-HP1-AH (2026-07-30): the
    # unit's rear face is y=9'-7" and the grille centres 1" north of it in the soffit
    # face, feeding the unit's bottom-return through DU-S-HP-RET's 6" plenum stub. Behind
    # this grille is where DU-S-ERV-HP-FEED's wye injects the ERV's fresh air (see
    # DUCTS_HVAC_SECOND): fresh mixes into the return plenum, not into a hard-coupled duct,
    # so either machine runs alone. 7'-10" — the soffit face, same plane as the hall cans.
    Register(uid="CSRH05AAAA", tag="REG-S-HP-RET", kind=DuctSystem.RETURN, room="RM-S-HALL",
             position=pt(ft(20, 8), ft(9, 8)), duct_ref="DU-S-HP-RET",
             type_ref="REG-T-HP-RET",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 10))),
]

# One attic branch left (2026-07-30): RM-A-STUDY's, which genuinely needs a horizontal
# run — the room starts at x=22'-4", east of anything the trunk passes under, so its air
# has to travel. CHASE routing — it rides the attic floor/knee space, not a joist bay.
# DU-A-HP-EAST is gone: its grille moved to directly over the hall soffit and became a
# straight boot off the trunk (REG-A-HP-EAST below), the same pattern as REG-A-HP-WEST —
# a 6'-8" horizontal run whose only job was reaching a grille that could sit anywhere in
# a 456 sf open room was length for its own sake.
DUCTS_HVAC_ATTIC = [
    DuctRun(uid="CADH01AAAA", tag="DU-A-HP-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(3)), pt(ft(26), ft(3))),
            width=inch(8), depth=inch(6), routing=DuctRouting.CHASE, design_cfm=100),
]

REGISTERS_HVAC_ATTIC = [
    Register(uid="CARH01AAAA", tag="REG-A-HP-STUDY", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDY", position=pt(ft(26), ft(3)), duct_ref="DU-A-HP-STUDY",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # Directly above the hall soffit (2026-07-30): the trunk runs at x=19'-4" below, so
    # the boot rises straight through FS-ATTIC into the floor grille — no attic duct run
    # at all. y=10' keeps the grille a foot inside RM-A-EAST's south wall (y=9') and
    # clear of FO-A-STAIR's walkway (the opening ends at y=8'-9 5/8").
    Register(uid="CARH02AAAA", tag="REG-A-HP-EAST", kind=DuctSystem.SUPPLY,
             room="RM-A-EAST", position=pt(ft(19, 4), ft(10)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # RM-A-WEST's supply (2026-07-30): a floor boot straight up off DU-S-HP-SUITE through
    # FS-ATTIC — the branch runs at y=14'-1 7/8" directly below, so the boot is one bay's
    # rise, landing just west of the centre bearing wall roughly over D-S-SUITE. This is
    # what retired REG-A-SUP1 and its DU-A-ERV-SUP trunk: the west attic room now gets
    # conditioned air off System 1 like RM-A-STUDY/RM-A-EAST do, and gives stale air back
    # at REG-A-RET1 (REGISTERS_ATTIC), so the ERV's attic side is extract-only, the same
    # pattern as the second storey.
    Register(uid="CARH03AAAA", tag="REG-A-HP-WEST", kind=DuctSystem.SUPPLY,
             room="RM-A-WEST", position=pt(ft(16, 6), ft(14, 1.875)),
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# CONDENSATE — planned plumbing item, no geometry this pass. Each of the four indoor units
# (EQ-S-HP1-AH and the three heads) makes condensate in cooling; the two wall heads on
# interior walls and the ducted unit gravity-drain into a collected air-gap drain line that
# terminates over the mechanical-room sink, which is what keeps a trapped condensate line
# out of the sanitary system. Nothing is modeled here yet: the line needs the plumbing pass
# that gives the mechanical-room sink its own drain (plans/TODO.md).

# Every register here drops into a boot in the FS-SECOND joist bay, so the grille face lands
# flush with the finished floor and the type's 1" height is the frame below it, not a kerb
# standing on it. Saying so keeps a register out of a neighbour's clear floor space without
# exempting registers as a class — a surface-mounted one would still report.
#
# The second storey went supply-less on the ERV on 2026-07-29. The three bedrooms' boots
# are still here and still in the same holes — same uids, so the IFC GlobalIds survive a
# rename that would otherwise churn every downstream reference — but they are stale-air
# pickups now, on DU-M-ERV-RET rather than the deleted DU-M-ERV-SUP. The bedrooms' fresh
# air comes from REG-S-HP-BED1/2/3 off DU-S-HP-SUP (REGISTERS_HVAC_SECOND above), and the
# suite's from REG-S-HP-SUITE off DU-S-HP-SUITE, so extracting here rather than supplying
# is what makes the storey's air actually move: in at the hall soffit, out at the far wall
# of each room.
#
# Two terminals were dropped outright rather than converted:
#   REG-S-SUP1 (RM-S-PLANT) — the plant room is getting its own dedicated mini-HRV, whose
#     humidity load has nothing to do with the whole-house rate; it is not drawn yet, so
#     mep.ventilation_distribution honestly reports RM-S-PLANT as unserved until it is.
#   REG-S-SUP2 (RM-S-STUDY2) — dropped by the user's 2026-07-29 call; the study takes its
#     air from the hall it opens onto. Also honestly reported.
# And two more for redundancy: REG-S-SUP6 (RM-S-SUITE, replaced by REG-S-HP-SUITE) and
# REG-S-SUP7/REG-S-RET1 (the hall, which is the plenum between them, not a served room).
REGISTERS = [
    # One per bedroom now that the east bedrooms are equal 9'-0" bays: BED1 y 9'-18',
    # BED2 y 18'-27', BED3 y 27'-36'. RM-S-BED2 had no terminal at all before the
    # re-spacing (plans/TODO.md). All three sit at x=29', against the east wall and
    # diagonally opposite the hall-side supply grille, so the room crossventilates.
    Register(uid="CMR903AAAA", tag="REG-S-RET-BED1", kind=DuctSystem.RETURN, room="RM-S-BED1",
            position=pt(ft(29), ft(13, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-RET-BED2", kind=DuctSystem.RETURN, room="RM-S-BED2",
            position=pt(ft(29), ft(22, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR904AAAA", tag="REG-S-RET-BED3", kind=DuctSystem.RETURN, room="RM-S-BED3",
            position=pt(ft(29), ft(31, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # The suite's extract is back at (9', 20') (2026-07-30, its original spot). It chased
    # the supply grille twice: when REG-S-HP-SUITE first landed at (8'-6", 20'-4") this
    # moved south to (9', 12') to break the ceiling-supply-over-floor-extract short
    # circuit; then the branch reroute put the supply at (12'-6", 14'-1 7/8") and (9', 12')
    # became the short circuit — ~4' away in plan. (9', 20') is 7'+ from the new supply,
    # on the same trunk, east of FURN-S-SUITE-BED (x 2'-6"..7'-6") and clear of its foot
    # zone.
    Register(uid="CMR906AAAA", tag="REG-S-RET2", kind=DuctSystem.RETURN, room="RM-S-SUITE",
            position=pt(ft(9), ft(20)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# --- Distribution registers, all four storeys (ASHRAE 62.2 coverage) ----------------
# Stale air out of every wet room, fresh air into the living/sleeping rooms the ERV still
# supplies directly, all matched to rooms explicitly via room= (mep.ventilation_distribution).
# RM-S-NCLOSET and the other storage rooms get nothing. On the second storey the ERV is now
# extract-only (see REGISTERS above): what is left here is the two wet-room boots off the
# FS-SECOND return trunk plus the hall bath's ceiling grille on the EXHAUST run in the
# FS-ATTIC bay over the shower.
#
# The wet-room pickups are EXHAUST, not RETURN, and each states the airflow it is balanced
# to (2026-08-01, code.R303_3_local_exhaust). Two things were wrong before: a bathroom's air
# is pulled and thrown away, never recirculated — which is what DuctSystem.EXHAUST means and
# what RM-B-BATH and RM-S-BATH1 already said — and no terminal in the house stated a cfm, so
# R303.3 could not tell a 20 cfm grille from a decorative one. 20 cfm each is ASHRAE 62.2's
# *continuous* local-exhaust rate, which is the rate that applies here: this is an ERV that
# runs all the time, not a fan on a timer, and the 50 cfm figure is the intermittent
# alternative for a fan someone has to remember to switch on.
#
# Five wet rooms at 20 cfm is 100 cfm of the machine's 210, which is what the balanced supply
# side has to make up and does.
REGISTERS_SECOND = [
    Register(uid="CSRV03AAAA", tag="REG-S-EXH3", kind=DuctSystem.EXHAUST, room="RM-S-SUITEBATH",
            position=pt(ft(14), ft(19)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV04AAAA", tag="REG-S-EXH4", kind=DuctSystem.EXHAUST, room="RM-S-VANITY",
            position=pt(ft(3), ft(24, 4)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV05AAAA", tag="REG-S-EXH1", kind=DuctSystem.EXHAUST, room="RM-S-BATH1",
            position=pt(ft(5), ft(32, 8)), duct_ref="DU-S-BATH1-EXH", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Main-storey terminals are ceiling grilles fed from the DUCTS_MAIN bays overhead. The
# kitchen is open plan inside RM-M-LIVING (no Occupancy.KITCHEN), so its stale pickup is
# placed by position — (33', 33'), over the counter run — and still carries the LIVING room=.
REGISTERS_MAIN = [
    Register(uid="CMRV01AAAA", tag="REG-M-SUP1", kind=DuctSystem.SUPPLY, room="RM-M-LIVING",
            position=pt(ft(27), ft(12)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # REG-M-SUP2, the living room's second outlet at (30', 26'), is gone (2026-07-29). One
    # ERV outlet is what an open-plan room at the whole-house rate wants; the pair was
    # sized as if this were a heating trunk.
    Register(uid="CMRV03AAAA", tag="REG-M-SUP3", kind=DuctSystem.SUPPLY, room="RM-M-BED",
            position=pt(ft(9), ft(6)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV04AAAA", tag="REG-M-SUP4", kind=DuctSystem.SUPPLY, room="RM-M-STUDY",
            position=pt(ft(15, 8), ft(20)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The two baths are EXHAUST at 20 cfm each, like the second storey's — see the note over
    # REGISTERS_SECOND for why the whole wet-room set changed direction on 2026-08-01.
    Register(uid="CMRV05AAAA", tag="REG-M-EXH1", kind=DuctSystem.EXHAUST, room="RM-M-BATH1",
            position=pt(m(0.354668), m(7.86145)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV06AAAA", tag="REG-M-EXH2", kind=DuctSystem.EXHAUST, room="RM-M-BATH2",
            position=pt(ft(4), ft(18)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV07AAAA", tag="REG-M-RET3", kind=DuctSystem.RETURN, room="RM-M-LAUNDRY",
            position=pt(ft(10, 6), ft(20)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV08AAAA", tag="REG-M-RET5", kind=DuctSystem.RETURN, room="RM-M-LIVING",
            position=pt(ft(33), ft(33)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-M-MUDROOM is stale-pickup only, no fresh-air outlet — the user reversed the earlier
    # call on 2026-07-29, and this comment used to argue the opposite ("fresh-air intake
    # only... positive pressure against the door"). A mudroom is the room that smells: wet
    # coats, boots, the dog, and whatever comes in off the drive through the door beside it.
    # Pressurising it pushes that everywhere else in the house. Extracting from it makes the
    # mudroom the low-pressure end of the main storey, so the boundary air moves toward the
    # boots instead of away from them, and the ERV recovers the heat on the way out.
    #
    # Same grille, same hole, same uid — only the direction changed. Centred in the hallway
    # strip between the two closets, clear of both, in line with the window/bench.
    Register(uid="CMRV09AAAA", tag="REG-M-RET-MUD", kind=DuctSystem.RETURN, room="RM-M-MUDROOM",
            position=pt(m(1.23013), m(9.56867)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Basement terminals hang from the SL-M-DECK underside off the CHASE trunks — except the
# sauna's stale pickup, which is the one wall-mounted terminal in the house (see below).
REGISTERS_BASEMENT = [
    Register(uid="CBRV01AAAA", tag="REG-B-SUP1", kind=DuctSystem.SUPPLY, room="RM-B-GYM",
            position=pt(ft(27), ft(9)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # REG-B-SUP2 is back (2026-08-01), in its old hole at (27', 27') and on its old uid so
    # the IFC GlobalId is the one it had. It was dropped on 2026-07-29 on the argument that
    # the media room shares the basement's open volume with the gym and takes its air through
    # the opening between them — true as far as air goes, and beside the point for this room:
    # RM-B-PLAY-N is 324 sf of habitable MEDIA space with no glazing at all, so it is legal
    # only under R303.1 Exception 1, and the exception's second half is outdoor air supplied
    # to *the room*. An adjacent room's grille does not satisfy it, and neither does an
    # opening between them.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(27), ft(27)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-ERV-SUP",
            design_cfm=30,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    #
    # REG-B-RET1 moved off the middle of the floor (it was at (5', 8')) and onto the
    # workbench line at (4'-6", 4'-6") — the pickup is there for light fume handling
    # (plans/TODO.md: "an ERV intake in the workshop (this one over a bench for light fume
    # handling)"), which only works if it is over the bench and not over the aisle. Solder,
    # a can of finish, a bit of glue: this is a bench hood's worth of pull, not a spray
    # booth's, and it is deliberately on the RETURN trunk rather than a dedicated exhaust.
    # NOTE the bench itself is not modeled yet — no Furniture in RM-B-WORKSHOP — so the
    # position is taken from ED-B-WORKSHOP-PANEL1 (plan/lighting.py), the flat panel
    # authored explicitly as the light "over a bench" in the west bay — offset 18" south of
    # the panel so the two are not the same ceiling point. When the workbench is placed,
    # this register moves with it.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(4, 6), ft(4, 6)), duct_ref="DU-B-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The sauna's stale pickup came off the ceiling on 2026-07-29 and went to the wall, 4"
    # above the finished floor on the south concrete face (y=1'-0") directly below
    # FURN-B-SAUNA-BENCH-S, whose 18" top clears it completely. This is the whole point of a
    # sauna's extract: the room stratifies hard, the löyly you want to keep is at bench
    # height and above, and the air you want gone is the cold, stale, spent layer sitting on
    # the floor. A ceiling grille at 8' pulls the good air straight out. Paired with
    # REG-B-SUP3 over the heater, it makes the convection loop the room needs — down the
    # far wall, across the floor, out under the bench — and both ends are dampered
    # (REG-T-ERV-SAUNA-*) so the loop can be shut during a session and opened after one.
    # EXHAUST at 20 cfm since 2026-08-01 (code.R303_3_local_exhaust). The room is
    # Occupancy.BATHROOM and R303.3 reaches it: it has a 14x24 window whose openable half is
    # 1.2 sf, short of the section's 1.5 sf, so the mechanical path is the one that carries
    # it. The direction was always what this grille did — spent air out of a sealed hot room
    # is not air to recirculate — and the loop the comment above describes is unchanged.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            position=pt(ft(11, 5.5), ft(1)), duct_ref="DU-B-ERV-RET",
            type_ref="REG-T-ERV-SAUNA-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4))),
    # Fresh air in high, over the stones. EQ-B-SAUNA-HTR is at (9'-9 13/16", 8'-9") on the
    # west liner (plan/electrical.py); this sits directly above it at 7'-0", below the 8'
    # ceiling so the boot can turn out of DU-B-SAUNA-SUP without fighting the drop ceiling
    # the condensate line already runs above.
    Register(uid="CBRV06AAAA", tag="REG-B-SUP3", kind=DuctSystem.SUPPLY, room="RM-B-SAUNA",
            position=pt(ft(9, 9.8125), ft(8, 9)), duct_ref="DU-B-SAUNA-SUP",
            type_ref="REG-T-ERV-SAUNA-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
    # RM-B-BATH (2026-07-30). Filed as EXHAUST rather than RETURN, like RM-S-BATH1's terminal
    # and unlike the basement's other two stale pickups: a bathroom's air is pulled and not
    # recirculated. It sits over the water closet at the room's west end, the far corner from
    # the door, so the room's makeup air crosses it on the way through.
    Register(uid="CBRV05AAAA", tag="REG-B-EXH1", kind=DuctSystem.EXHAUST, room="RM-B-BATH",
            position=pt(ft(11, 8), ft(20)), duct_ref="DU-B-ERV-BATH",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
]

# One attic ERV terminal now (2026-07-30): the extract. Four became a balanced pair on
# 2026-07-29 (REG-A-SUP2/SUP3 gone, the pair moved to the NW corner beside the maintenance
# shaft at (1', 34'-6") where the radon/plumbing riser rises through every storey), and then
# the supply half went too — REG-A-SUP1 was retired by REG-A-HP-WEST, the floor boot off
# System 1's DU-S-HP-SUITE branch (REGISTERS_HVAC_ATTIC above), which conditions RM-A-WEST
# instead of just ventilating it. What is left is the stale pickup on a 4'-0" branch off the
# shaft: fresh in off System 1, stale out here, the same in-at-the-supply / out-at-the-ERV
# pattern as every other storey. The attic is one cathedral volume across the knee walls, so
# one extract still turns the floor over.
REGISTERS_ATTIC = [
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-WEST",
            position=pt(ft(6), ft(31, 4)), duct_ref="DU-A-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(m(1.88684), m(10.0015)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH-HP"),
]

# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(1, 2), ft(29)), type_ref="ED-T-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), rotation=deg(90)),
]

# One light + switch per habitable room, one code-minimum receptacle per bedroom (bare
# minimum, not NEC 210.52 spacing). Switch sits 1' toward -x of the light, except where the
# room's door is known, in which case the switch sits beside the door on the latch side —
# which is where a switch actually goes. Receptacle 1' toward +x. Uids avoid the letters
# I/L/O/U (Crockford base32, → model/ids.py). These were formerly generated from a
# `_HABITABLE_ROOMS` table; expanded to explicit constructors so the file is
# `# haus: editable` and UI edits round-trip.
#
# `electrical.room_lighting` matches devices to rooms by tag suffix, so a device serving
# RM-<x> must be tagged ED-<x>-*.
#
# Each `-LT` fixture below was one generic ED-T-LIGHT until the lighting plan went in. They
# were re-typed in place rather than deleted and re-added, so every uid — and therefore
# every derived IFC GlobalId — survived. Each now names a real product, states the switch
# that controls it, and is positioned as one corner of the grid the rest of which lives in
# plan/lighting.py. The switches were left where they were.
BASEMENT_DEVICES = [
    # RM-B-GYM (x 18'-36', y 0-18'): switch just inside D-B-PLAY, the door at (24', 18').
    ElectricalDevice(uid="CED010K1AA", tag="ED-B-GYM-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(9)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-BACKUP",
                     room="RM-B-GYM", controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    ElectricalDevice(uid="CED010K2AA", tag="ED-B-GYM-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(23, 6.5), ft(17, 5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-BACKUP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

MAIN_DEVICES = [
    ElectricalDevice(uid="CED001K1AA", tag="ED-M-LIVING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-LIVING", controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED001K2AA", tag="ED-M-LIVING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(12)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED002K1AA", tag="ED-M-BED-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-BED", controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED002K2AA", tag="ED-M-BED-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12, 6), ft(13, 0.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED002K3AA", tag="ED-M-BED-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED003K1AA", tag="ED-M-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(15, 8), ft(19, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-STUDY", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED003K2AA", tag="ED-M-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(21, 5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(270)),
    # --- kitchen outlets (RM-M-LIVING is open plan, so these keep the LIVING suffix) ---
    # Circuits are still deferred (decision 1): these are symbols and mounting heights, not
    # a panel schedule. Counter outlets sit at 42" — 6" of backsplash over the 36" counter,
    # under the 54" wall cabinets. The refrigerator's future battery-backup circuit is not
    # modeled; KRF1 is an ordinary duplex until that circuit is designed.
    #
    # Repositioned 2026-07-30 with the range/sink wall swap, then again the same day with the
    # sink/dishwasher flip and the range/N3 flip. KET1 stayed on FURN-M-KIT-E1's open counter;
    # KGF1 moved off the sink (now under it) onto the dishwasher's new spot instead. KGF2
    # stayed put — it was never over an appliance. KGF3 followed the range's cooking zone
    # north with N3.
    ElectricalDevice(uid="VDGMBY3YW7", tag="ED-M-LIVING-KET1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(25, 6), ft(35, 3.375)), type_ref="ED-T-RECEPTACLE-620", circuit="CKT-KETTLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="N9317V3K8Y", tag="ED-M-LIVING-KGF1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(31, 1), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="J34E2ZM4GG", tag="ED-M-LIVING-KGF2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(32), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="EJYZJRDFG0", tag="ED-M-LIVING-KGF3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4.375), ft(28, 11.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # The island receptacle (2026-08-02). FURN-M-KIT-ISLAND (CASE-ISLAND-60, 5'x3',
    # x 25'-0"..30'-0", y 26'-5 3/8"..29'-5 3/8", 36" counter) had none. 2023 NEC
    # 210.52(C)(2) no longer *requires* an island countertop receptacle — but where none
    # serves the countertop it requires provisions for adding one, and 210.52(C)(3) now
    # confines a receptacle that SERVES the countertop to on/above/in the counter surface
    # (the old below-counter side-mount allowance is gone, precisely because of cords
    # draped over an edge people sit at). So this one goes on the island's EAST END face —
    # never the south face, where the seating overhang is and the stools tuck under — at
    # 32", just below the 36" top with no overhang above it on that end, wired as the
    # 210.52(C)(2) provision and a usable point for stand-mixer-class appliances. GFCI at
    # the device per 210.8(A)(6) (all kitchen 125V receptacles), on CKT-KITCH-SA2, the
    # counter-east small-appliance circuit the east end of the kitchen already runs on
    # (20A, dual-function GFCI+AFCI breaker). rotation 90 backs it west into the carcass.
    ElectricalDevice(uid="CEDKGF4AAA", tag="ED-M-LIVING-KGF4", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(30, 1), ft(27, 11.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA2",
                     rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(32))),
    # Behind the range at 6": the whip drops to the floor box, not to a counter height. Moved
    # north with APPL-M-RANGE when it swapped with N3; x is still the wall-face constant
    # (35'-4") and y is the range's new along-wall position.
    ElectricalDevice(uid="S8DH5FRQQA", tag="ED-M-LIVING-KRG1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(35, 3.375), ft(31, 8.375)), type_ref="ED-T-RECEPTACLE-240", circuit="CKT-RANGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(6)), rotation=deg(270)),
    # On the centre bearing wall's east face, behind APPL-M-FRIDGE, at 48" — above the
    # coil deck, so the plug is reachable without pulling the whole cabinet out.
    ElectricalDevice(uid="D9EBW2FJTX", tag="ED-M-LIVING-KRF1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(31, 5.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # Inside the sink base, 18" up: the dishwasher's cord and the disposer share the box.
    # Followed APPL-M-DW to its new spot when it flipped with the sink; x is the dishwasher's
    # along-wall position and y is the wall-face constant (35'-4").
    ElectricalDevice(uid="WK41TSMA97", tag="ED-M-LIVING-KDW1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(31, 1), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-DISHWASHER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
]

# Re-snapped to the survey-aligned partitions (storeys/second.py): each light sits in its
# room's new centre, each switch beside that room's door on the room side, and each -RC1 on
# the first of the wall positions `electrical.receptacle_spacing` measures (the rest of the
# 210.52 fill is in plan/electrical.py). None of these carry `room=`, so a device left on a
# stale coordinate is matched to its room by tag suffix and still reports PASS — which is
# exactly how they came to be stranded inside partitions.
SECOND_DEVICES = [
    ElectricalDevice(uid="CED004K1AA", tag="ED-S-PLANT-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-UPPER",
                     room="RM-S-PLANT", controlled_by=("ED-S-PLANT-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    # Beside D-S-PLANT, the door through the centre bearing wall at y=4'-5 1/2".
    ElectricalDevice(uid="CED004K2AA", tag="ED-S-PLANT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(6, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(270)),
    ElectricalDevice(uid="CED005K1AA", tag="ED-S-STUDY2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED005K2AA", tag="ED-S-STUDY2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(19), ft(8, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED006K1AA", tag="ED-S-BED1-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(11, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED1", controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED006K2AA", tag="ED-S-BED1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(13, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED006K3AA", tag="ED-S-BED1-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25, 11), ft(17, 8.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED007K1AA", tag="ED-S-BED2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(20, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED2", controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED007K2AA", tag="ED-S-BED2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(22, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED007K3AA", tag="ED-S-BED2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25, 10), ft(26, 8.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED008K1AA", tag="ED-S-BED3-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(29, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED3", controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED008K2AA", tag="ED-S-BED3-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(30, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED008K3AA", tag="ED-S-BED3-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 4.375), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(0)),
    ElectricalDevice(uid="CED009K1AA", tag="ED-S-SUITE-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(11)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITE", controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # In the suite's east arm, beside D-S-SUITE (the hall door through the bearing wall).
    ElectricalDevice(uid="CED009K2AA", tag="ED-S-SUITE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(16, 7), ft(12, 8.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED009K3AA", tag="ED-S-SUITE-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 3), ft(15, 6.625)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # --- rooms the survey added: suite bath, vanity alcove, landing, north closet -------
    # None is a habitable occupancy, so `electrical.room_lighting` does not require these;
    # they are here because a windowless bath, an interior alcove, the stair arrival and a
    # closet all need a switched light to be usable.
    ElectricalDevice(uid="CED013K1AA", tag="ED-S-SUITEBATH-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(11, 6), ft(18)), type_ref="ED-T-LT-CAN4-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITEBATH", controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED013K2AA", tag="ED-S-SUITEBATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12, 9), ft(16, 3.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED014K1AA", tag="ED-S-VANITY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(3), ft(23, 6)), type_ref="ED-T-LT-CAN4-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-VANITY", controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED014K2AA", tag="ED-S-VANITY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(5), ft(25, 11.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED015K1AA", tag="ED-S-LANDING-LT", kind=DeviceKind.LIGHT,
                     position=pt(m(2.44371), m(7.41198)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-HALL", controlled_by=("ED-S-LANDING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On W-S-SN3's north face beside ED-S-STAIR-SW (plan/lighting.py): W-S-BD-N2, which
    # used to carry this switch, came out with O-S-STAIRTOP on 2026-07-28.
    ElectricalDevice(uid="CED015K2AA", tag="ED-S-LANDING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(11, 6), ft(22, 7.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED016K1AA", tag="ED-S-NCLOSET-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(33)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-NCLOSET", controlled_by=("ED-S-NCLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED016K2AA", tag="ED-S-NCLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 5.5), ft(30, 6.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# Attic habitable rooms, both east of the ridge. The cathedral ceiling follows the 4:12 roof
# off a 5' knee wall, so at x=27' the roof plane is 5' + 9'/3 = 8' — the same 8' the rest of
# the house's ceiling boxes sit at, which is why these lights need no special elevation.
ATTIC_DEVICES = [
    # RM-A-EAST (x 18'-36', y 8'-8"-36'): switch inside D-A-HALVES, the door at (18', 32').
    ElectricalDevice(uid="CED011K1AA", tag="ED-A-EAST-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(15)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-EAST", controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED011K2AA", tag="ED-A-EAST-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(32, 5.5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # RM-A-STUDY (x 18'-36', y 0-8'-8"): switch inside D-A-STUDY, the door at (19', 8'-8").
    ElectricalDevice(uid="CED012K1AA", tag="ED-A-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-STUDY", controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED012K2AA", tag="ED-A-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 8.375), ft(8, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room, riding RM-M-MECH's framed shaft
# closet up through the NW notch moved into RM-S-BATH1 (2026-07-28 — was at (3',33'),
# floating in open mudroom floor space with no enclosure; storeys/main.py, storeys/
# second.py). Its passive radon vent and the plumbing vent share one mechanical chase up
# to 23'-10" — under the 4:12 rake, which is at 25'-5.7" over the chase's x=1' — turn 90°
# out through the north gable siding, then 90° back up, clamped to the standing seam with
# S-5!-style clamps. The termination is derived (12" above the true roof surface at the
# riser — the deck plane plus CATLIN_ROOF's above-structure skin, resolve/
# vent_termination.py), not authored: an authored absolute cannot follow a rake, which is
# how it drifted to 33', 2' above its own ridge. Elevations are project-frame.
RADON_SUMP = [
    Sump(uid="CMSP01AAAA", tag="SM-B-RADON", position=pt(ft(1), ft(34, 6)),
         diameter=inch(18), depth=inch(24), host_ref="SL-B-FLOOR",
         sealed_cover=True, radon_vent=True, vent_ref="VR-M-RADON-VENT",
         # CKT-SUMP has existed on the panel schedule all along; the pit it feeds only
         # implied a pump. Saying it here is what puts an IfcPump/SUMPPUMP in the export,
         # joins it to the stormwater system, and gives the discharge somewhere to be
         # checked — the foundation schedule used to infer "DRAINING TO SUMP" from the mere
         # existence of this pit while every drain tile on the project said "daylight".
         pump=SumpPump(model="1/3 hp cast-iron submersible", horsepower=0.33,
                       discharge="daylight", circuit_ref="CKT-SUMP")),
]

VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(1), ft(34, 6)), start_elevation=ft(-8.5),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), ft(2, 6)),
            wall_ref="W-A-N2", attachment="standing_seam_clamp"),
]

# S-5! standing-seam clamps fixing the exterior riser to the north gable siding. The riser
# spans 23'-10" to its derived termination, and the gable siding at x=1' stops at the
# 25'-5.7" rake, so all three clamps sit on the pipe *and* on cladding they can actually
# grip. The riser rides W-A-N2, the west half of the north gable wall (x=0..18); W-A-N1
# is the east half.
# These hold a *pipe*, so the part is an S-5! CanDuit ring on an S-5! seam clamp, not the
# bare clamp — the same assembly the roof leaders use (LEADER_CLAMPS below). The ring is
# selected on outer diameter, and 3" PVC DWV is 3.5" OD, which is the #11 (3.4-3.7") size;
# the 4" leaders take #13. Authoring the bare "S-5!" here billed brackets and no rings.
VENT_CLAMPS = [
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 4), size="S-5! CanDuit #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 10), size="S-5! CanDuit #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(25, 4), size="S-5! CanDuit #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
]

# --- Outdoor NEMA 3R weatherproof junction box on the north gable siding -------------
# Gasketed blank cover plate; mounted to the standing seam with an S-5!-style clamp. It
# serves the exterior vent riser's work zone, so it belongs beside the CN-M-VENT-CLAMP
# cluster (24'-4" / 24'-10" / 25'-4" at x=1') — not 19' below it at eye level on the main
# storey. Filed on the attic storey with the gable wall it now rides: at x=4' the 4:12
# rake carries the siding to ~26'-5.7", so a box at 25'-6" has cladding to grip. It stands
# 3' east of the riser bundle (2026-07-28: riser moved from x=3' to x=1', box follows to
# stay 3' clear of the pipes and their clamps).
# Both heights below are the same 25'-6": a Mount elevation is storey-relative (attic datum
# 20') while a Connector elevation is project-frame absolute.
NEMA_BOX = [
    ElectricalDevice(uid="CEJ901AAAA", tag="ED-A-NEMA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(4), ft(36, 8)), type_ref="ED-T-JBOX",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
NEMA_CLAMP = [
    # The clamp is the box's own fastener, so it shares the box's point exactly — it followed
    # ED-A-NEMA-JB from y=37'-0" to the cladding face on 2026-08-03 (the box had been hanging
    # 4" clear of the siding it is supposed to be clamped to).
    Connector(uid="CMNC01AAAA", tag="CN-A-NEMA-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(4), ft(36, 8)), elevation=ft(25, 6), size="S-5!",
              connects=("ED-A-NEMA-JB", "W-A-N2")),
]

# --- Downspout securement: S-5! CanDuit clamps on the standing-seam siding ------------
# The two roof leaders (params/roof_trim.py, TR-RF-LEADER-W/E) run ~24' from the gutter
# outlet down the north end of the west and east faces. They are steadied — NOT supported —
# by the same hardware the radon riser uses: an S-5! non-penetrating standing-seam clamp
# with an S-5! CanDuit pipe clamp on its M8 shaft, exactly as CN-M-VENT-CLAMP1..3 above.
# https://3482954.fs1.hubspotusercontent-na1.net/hubfs/3482954/Resources/Product%20Documents/Utility/CanDuit%20Pipe%20Clamp/WEB-Hybrid-Sales-Tech-CanDuit-Pipe-Clamp-Cut-Sheet.pdf
# CanDuit comes in 14 sizes; a 4" round leader (4.0" OD) takes the **#13** ring, whose
# 4.00-4.37" adjustability range is the only one that closes on it. The reference note is
# explicit that these keep the leader against the wall and are not its primary support.
#
# The ring number is the part number: it is what `size` bills through `library/hardware.py`
# (S5_CANDUIT_PIPE_CLAMP), which in turn declares `requires_role`, so the seam clamp each
# ring mounts on is billed with it. Authoring a bare "S-5!" here would order the brackets
# and none of the rings.
#
# Four per leader at roughly 6' o.c. (5' / 11' / 17' / 23'), each on the wall that actually
# has cladding at that elevation: main to 10', second to 20', the attic knee wall above. In
# plan they sit on the leader's own centre line — 8.77" outboard of the sheathing datum,
# which is the trough's mid-width (params/roof_trim.py::_TROUGH_MID_IN) and also just about
# where a strapped 4" round leader's centre lands off 5.02" of wall stack.
# (Literal offsets, not arithmetic: the editable-plan dialect forbids binary operators.)
_LEADER_X_W = inch(-8.77)
_LEADER_X_E = ft(36, 8.77)
_LEADER_Y = ft(35, 6)

LEADER_CLAMPS = [
    Connector(uid="CMLC01AAAA", tag="CN-A-LEADER-W1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(5), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-M-W1B")),
    Connector(uid="CMLC02AAAA", tag="CN-A-LEADER-W2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(11), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC03AAAA", tag="CN-A-LEADER-W3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(17), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC04AAAA", tag="CN-A-LEADER-W4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(23), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-A-W1")),
    Connector(uid="CMLC05AAAA", tag="CN-A-LEADER-E1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(5), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-M-E2")),
    Connector(uid="CMLC06AAAA", tag="CN-A-LEADER-E2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(11), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
    Connector(uid="CMLC07AAAA", tag="CN-A-LEADER-E3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(17), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
    Connector(uid="CMLC08AAAA", tag="CN-A-LEADER-E4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(23), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-A-E2")),
]

# --- Water supply: the house entry out to the garage hydrant ------------------------
#
# The project's first PipeSystem.WATER_COLD run — everything authored before this is DRAIN
# or VENT. It starts at the house's water entry (5', 0'), where site.py's WATER UtilityLine
# terminates, and runs north under the basement slab and then out under grade to the garage,
# surfacing through SP-G-HYDRANT (params/foundations.py) at the hydrant.
#
# Elevations are the burial depth, not a ceiling height: the run leaves the entry at the
# service's own 6' depth and stays there. That is what keeps the hydrant's shutoff — which
# sits at the *end* of this run — at the 72" bury the code wants, well below the 42" frost
# depth the footings are set to. It is deliberately NOT routed up into the garage and back
# down: a supply line that rises above frost anywhere along its length freezes there.
#
# Filed on ``main`` rather than ``basement`` even though it runs under both: PipeRun
# elevations resolve as ``storey datum + authored``, and main's datum is 0'-0" = grade. On
# the basement's -9' datum the same authored -6' would resolve to -15' absolute, and the
# authored number would stop meaning "six feet down".
#
# The interior shutoff is ED/EQ-free by design: it is the hydrant's own valve at the
# buried end plus the isolation valve immediately downstream of the slab penetration, both
# of which mep.hydrant_freeze_depth asserts against this run's geometry.
# Re-routed 2026-07-29: the buried leg now runs at x=5' the whole way north (it used to
# hug the garage's west footing 8" off its edge for 24', inside the 45° influence line)
# and turns west only at y=61', crossing *under* FT-GF-S-DR through SP-GF-S-HYD and rising
# through SP-G-HYDRANT / the pedestal block-out at the fixture. The three basement wall
# crossings (S1 / CW / N3) are cast horizontal sleeves at the -6' bury; between them the
# line runs exposed across the heated basement at the same elevation, which is what keeps
# every buried vertex at the full 72" the fixture is specified for
# (`mep.hydrant_freeze_depth` walks all of them; the terminal rise is the hydrant's own
# self-draining barrel and is exempt).
WATER_SUPPLY = [
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(0)), pt(ft(5), ft(61)), pt(ft(1, 6), ft(61)),
                  pt(ft(1, 6), ft(62)), pt(ft(1, 6), ft(62))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(-6), ft(-6), ft(-6), ft(-6), ft(0, 4.8)),
            serves=("FX-G-HYDRANT",)),
]

# --- Domestic hot/cold distribution (2026-07-29 plumbing pass) -----------------------
#
# PEX home-run-lite: a 1" cold trunk tees off the water service where it crosses the
# house (the hydrant line above IS the service; the tee at (5', 1') rises to the
# basement ceiling), and a 1" hot trunk leaves EQ-B-WH. Both run the ceiling band just
# south of the y=18' wall (cold at y=16'-2.4", hot at y=15'-10.8" — 3.6" apart, under the
# routed drains' y=16'-6" line), cross the concrete through their own WALL_SLEEVES, and
# rise to each wet-wall group through the SUPPLY_SLEEVES cast in the deck. `serves` on a
# trunk is the union of everything downstream, so `mep.pipe_sizing` sums the real WSFU.
# Filed on ``basement`` (datum -9'): ceiling runs read as 8'-ish heights.
#
# The cold trunk went from 1" to 1 1/4" on 2026-07-30, and it is worth saying why rather than
# just how: the stair-foot bathroom and the sauna shower added 4 WSFU of cold, taking the trunk
# from 30 to 34 against the 32 a 1" branch carries in Table 610.4's 46–60 psi / <100' column.
# Nothing else about the distribution changed — the hot trunk is still 1" at 21.5 WSFU — and
# the one cast crossing the trunk makes on its way east (SP-B-CS2-CW) grew with it.
SUPPLY = [
    PipeRun(uid="CBPW30AAAA", tag="PR-B-CW-TRUNK", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(1)), pt(ft(5), ft(1)), pt(ft(5), ft(16)),
                  pt(ft(8), ft(16)), pt(ft(29, 0.6), ft(16)),
                  pt(ft(29, 0.6), ft(34, 1.2)), pt(ft(29, 0.6), ft(34, 1.2))),
            diameter=inch(1.25), material="copper", finish="lacquered",
            elevations=(ft(3), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(8, 1.2), ft(12, 6)),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV", "FX-M-BATH2-WC",
                    "FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK",
                    "FX-M-LAUNDRY", "FX-M-KITCH-SINK",
                    "FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2",
                    "FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The two south-face wall hydrants (2026-08-01), 2.5 WSFU cold each.
                    # 34 -> 39 on a 1 1/4" trunk that carries 64 in Table 610.4's 46-60 psi
                    # column, so the tee costs nothing in size.
                    "FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="CBPW31AAAA", tag="PR-B-HW-TRUNK", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015)),
                  pt(ft(6, 6), ft(19, 2.4)), pt(ft(6, 6), ft(15, 6))),
            diameter=inch(1), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(4), ft(8), ft(8), ft(8)),
            serves=("FX-M-BATH1-LAV", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK", "FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK",
                    "FX-M-KITCH-SINK",
                    "FX-B-BATH-LAV", "FX-B-SAUNA-SH",
                    "FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH",
                    # The dishwasher was taking hot water from a branch that never declared
                    # it (2026-08-01). Undeclared, its 1.5 WSFU was missing from the trunk's
                    # load *and* `mep.water_hammer_arrestor` had no supply to ask about, so
                    # the quick-closing valve on it went ungraded rather than failing.
                    "APPL-M-DW")),
    # Cold feed to the water heater itself (equipment, not a fixture — no fixture units).
    PipeRun(uid="CBPW32AAAA", tag="PR-B-CW-WH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(5, 6), ft(16, 9.6)), pt(ft(5, 6), ft(19, 2.4)),
                  pt(m(1.88684), m(10.0015)), pt(m(1.88684), m(10.0015))),
            diameter=inch(1), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(4))),
    # Main-storey groups.
    PipeRun(uid="CBPW33AAAA", tag="PR-B-CW-BATH1", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(7, 4.8), ft(16, 9.6)),
                  pt(ft(7, 4.8), ft(19, 2.4)), pt(ft(6), ft(23, 7.2)),
                  pt(ft(6), ft(23, 7.2)), pt(ft(6), ft(23, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(12, 6)),
            wall_refs=(None, None, None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    PipeRun(uid="CBPW34AAAA", tag="PR-B-HW-BATH1", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(24))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12, 6)),
            wall_refs=(None, None, "W-M-BAE"),
            serves=("FX-M-BATH1-LAV",)),
    PipeRun(uid="CBPW35AAAA", tag="PR-B-CW-BATH2", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(2, 3), ft(16)),
                  pt(ft(2, 3), ft(17, 2.4)), pt(ft(2, 3), ft(17, 2.4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(12)),
            serves=("FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB",
                    "FX-M-BATH2-SINK")),
    PipeRun(uid="CBPW36AAAA", tag="PR-B-HW-BATH2", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(2, 3), ft(15, 6)),
                  pt(ft(2, 3), ft(16, 9.6)), pt(ft(2, 3), ft(16, 9.6))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12)),
            serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-BATH2-SINK")),
    # The laundry pair rises inside W-M-BA2E, so each riser is split at the deck top
    # (ft(9) basement-relative = 0'-0" project) like the BATH1 pair above: the lower leg is
    # the sleeved concrete crossing and hosts no wall, the leg above it is in the stud
    # cavity and names it. `mep.wet_wall_occupancy` checks the declared segment's z-range
    # against the wall's own extent, so a single riser spanning both would read as escaping
    # the wall it is actually inside.
    PipeRun(uid="CBPW37AAAA", tag="PR-B-CW-WASH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(8), ft(20, 7.2)),
                  pt(ft(8), ft(20, 7.2)), pt(ft(8), ft(20, 7.2))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW38AAAA", tag="PR-B-HW-WASH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(8), ft(21, 2.4)),
                  pt(ft(8), ft(21, 2.4)), pt(ft(8), ft(21, 2.4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(12)),
            wall_refs=(None, None, "W-M-BA2E"),
            serves=("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK")),
    PipeRun(uid="CBPW39AAAA", tag="PR-B-HW-KITCH", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(29, 6.6), ft(15, 6)),
                  pt(ft(29, 6.6), ft(33, 7.2)), pt(ft(29, 6.6), ft(33, 7.2))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(8), ft(12, 6)),
            serves=("FX-M-KITCH-SINK", "APPL-M-DW")),
    # Second-storey groups: risers straight up through the deck to the wet walls above.
    # These two climb two storeys of wall to reach the hall bath, so each riser is split at
    # both storey lines — deck top ft(9) and the second floor ft(19) (basement-relative;
    # 0'-0" and 10'-0" project) — and names the wall it is inside on each leg. The
    # main-storey leg passes through a storage-room 2x4 partition (3.5" cavity, ample for
    # 3/4" PEX); only the second-storey leg is in a staggered wet wall.
    PipeRun(uid="CBPW40AAAA", tag="PR-B-CW-SBATH", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(16)), pt(ft(4), ft(16, 9.6)), pt(ft(4), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4)),
                  pt(ft(5, 7.2), ft(26, 4)), pt(ft(5, 7.2), ft(26, 4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(9), ft(19),
                        ft(21, 6)),
            wall_refs=(None, None, None, None, "W-M-STOS", "W-S-BD-N"),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # Riser moved 2.4" -> 4" east of N-M-BA1 (2026-08-02, RM-M-MUD-CLOSET): W-M-MUDC-E now
    # tees into that node from the north, and the junction trims W-M-STOS2's stud cavity
    # back to the partition's east face at x=6'-2 3/8" — the old x=6'-2.4" left half the
    # pipe in the corner pack. 6'-4" is the first clean bay past the tee, still 6 1/2"
    # west of D-M-MUD's jamb pack here and 8" west of D-S-BATH1's on the leg above.
    # SP-M-HW-SBATH (the SL-M-DECK sleeve this riser crosses) moved with it.
    PipeRun(uid="CBPW41AAAA", tag="PR-B-HW-SBATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4)), pt(ft(6, 4), ft(26, 4)),
                  pt(ft(6, 4), ft(26, 4))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(9), ft(19), ft(21, 6)),
            wall_refs=(None, None, "W-M-STOS2", "W-S-BD-N1B"),
            serves=("FX-S-BATH1-LAV", "FX-S-BATH1-SH", "FX-S-VANITY-LAV1",
                    "FX-S-VANITY-LAV2")),
    PipeRun(uid="CBPW42AAAA", tag="PR-B-CW-SUITE", system=PipeSystem.WATER_COLD,
            path=(pt(ft(8), ft(16)), pt(ft(13, 7.2), ft(16, 10.8)),
                  pt(ft(13, 7.2), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(21, 6)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
    PipeRun(uid="CBPW43AAAA", tag="PR-B-HW-SUITE", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(14, 2.4), ft(16, 10.8)),
                  pt(ft(14, 2.4), ft(16, 10.8))),
            diameter=inch(0.75), material="copper", insulation='1" fiberglass sleeve, ASJ jacket (R-3.5)',
            elevations=(ft(8), ft(8), ft(21, 6)),
            serves=("FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH")),
    # The stair-foot bathroom, fed from the water-heater corner down the mechanical room's
    # ceiling — the same pair of runs that fed FX-1 until 2026-07-30 (same uids), turned east
    # through W-B-STR's two new sleeves instead of dropping to a sink at x=7'. Each crosses at
    # its own y so the sleeves stay distinguishable (cold 20'-3", hot 19'-9"), then runs east
    # to x=16' and north to the partition line, where both drop inside W-B-BA-N's cavity to the
    # fixtures. Cold carries the WC and the lavatory (3.25 WSFU), hot the lavatory alone.
    PipeRun(uid="CBPW44AAAA", tag="PR-B-CW-BATH", system=PipeSystem.WATER_COLD,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7), ft(26)), pt(ft(7), ft(20, 3)),
                  pt(ft(16), ft(20, 3)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2), ft(8, 1.2),
                        ft(2, 6)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeRun(uid="CBPW45AAAA", tag="PR-B-HW-BATH", system=PipeSystem.WATER_HOT,
            path=(pt(m(1.88684), m(10.0015)), pt(ft(7, 3.6), ft(26)),
                  pt(ft(7, 3.6), ft(19, 9)), pt(ft(16), ft(19, 9)),
                  pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(8), ft(8), ft(2, 6)),
            serves=("FX-B-BATH-LAV",)),
    # The sauna shower's mixer, the first supply this room has ever had. Both legs tee off the
    # trunks where they already run — cold off PR-B-CW-TRUNK's y=16' leg, hot off the end of
    # PR-B-HW-TRUNK at (6'-6", 15'-6") — come down the aisle at x=17'-4", pass through
    # W-B-SA-N's stud bay (a framed partition needs no cast sleeve, unlike every service the
    # bathroom gets) and drop to the valve at 4'-6" inside W-B-CS's liner build-up, 4" apart on
    # either side of the pan's centreline. x=17'-4" keeps both of them 2" clear of W-B-CS2's
    # concrete face at 17'-6" on the way past. No supply runs to FX-B-SAUNA-FD: a floor drain
    # has none, which is why FX-FLOOR-DRAIN declares neither WATER_COLD nor WATER_HOT.
    PipeRun(uid="CBPW46AAAA", tag="PR-B-CW-SAUNA", system=PipeSystem.WATER_COLD,
            path=(pt(ft(17, 4), ft(16)), pt(ft(17, 4), ft(12, 2)),
                  pt(ft(17, 4), ft(12, 2))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
    PipeRun(uid="CBPW47AAAA", tag="PR-B-HW-SAUNA", system=PipeSystem.WATER_HOT,
            path=(pt(ft(6, 6), ft(15, 6)), pt(ft(17, 4), ft(15, 6)),
                  pt(ft(17, 4), ft(11, 10)), pt(ft(17, 4), ft(11, 10))),
            diameter=inch(0.5), material="copper", finish="lacquered",
            elevations=(ft(8), ft(8), ft(8), ft(4, 6)),
            serves=("FX-B-SAUNA-SH",)),
]

# --- The two south-face wall hydrants (2026-08-01) -----------------------------------
#
# One branch, two hydrants, and the route is decided by a wall that is not there.
#
# A frost-free *wall* hydrant is fed from inside: its seat sits in the stud cavity and the
# pipe reaching it has to arrive inside that cavity. On this house a supply cannot arrive
# from below. The main-storey exterior wall's stud bay is at y 0.5"..6" off the sheathing
# plane, and directly under it stands W-B-S1, 12" of cast concrete spanning y 0"..12" — a
# riser through SL-M-DECK into that cavity would come up through the top of a bearing wall.
# The same is true of W-M-C1 over W-B-CS on the centre line.
#
# So both hydrants are fed from *above*, out of the second floor's joist space, which is
# framed (FS-SECOND, 11 7/8" I-joists) and reaches every exterior wall in the house. One
# riser leaves the basement, and up there it splits: one leg drops down inside W-M-S1 to the
# porch hydrant, the other rises into W-S-S1 to the balcony hydrant. Neither leg is ever
# outboard of the wall's 4" of continuous exterior insulation, which is what makes a pipe in
# this exterior cavity a warm pipe rather than a burst one.
#
# The riser stands in W-M-BDN1, a main-storey 2x4 partition (3.5" cavity — ample for 3/4"
# PEX, the same clearance PR-B-CW-SBATH's W-M-STOS leg has) whose line at y=13'-4" is over
# open basement ceiling at x=6', so its deck crossing (SP-M-CW-HYD) lands in the slab and
# not on a wall below.
HYDRANT_BRANCH_BASEMENT = [
    # Two runs for one branch, because the material changes at the deck. The ceiling leg is
    # hung in the open under cast concrete, so it is lacquered copper like everything else
    # down here; from the slab up it is inside a wall and a joist bay, where nobody sees it
    # and PEX's tolerance for a hard freeze is worth more than a finish.
    PipeRun(uid="X4M2QP7B0K", tag="PR-B-CW-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(16)), pt(ft(6), ft(13, 4))),
            diameter=inch(0.75), material="copper", finish="lacquered",
            elevations=(ft(8, 1.2), ft(8, 1.2)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    PipeRun(uid="Z5NB8QMK2H", tag="PR-B-CW-HYD-RISER", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13, 4)), pt(ft(6), ft(13, 4)), pt(ft(6), ft(13, 4)),
                  pt(ft(6), ft(13, 4))),
            diameter=inch(0.75), material="pex",
            # Basement-relative: 8'-1.2" is the ceiling trunk band, 9'-0" is the top of the
            # 9" deck (0'-0" project), 18'-0" is the top plate of W-M-BDN1 (9'-0" project —
            # main-storey partitions stop there, 9'-0" being the ceiling height), and
            # 18'-3" is 9'-3" project, inside the second floor's joist space, whose 11 7/8"
            # joists hang 9'-0 1/8" to 10'-0". The split at the plate is what
            # `mep.wet_wall_occupancy` grades: a declared in-wall segment has to stay inside
            # the wall's own z-extent, and a riser drawn straight from the deck to the joist
            # bay escapes it by 3".
            elevations=(ft(8, 1.2), ft(9), ft(18), ft(18, 3)),
            wall_refs=(None, "W-M-BDN1", None),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# The joist-space distribution and the two legs off it. Filed on ``main`` (datum 0'-0")
# because these are the main storey's ceiling, and a main-relative elevation of 9'-3" reads
# as the height it is; on ``second`` the same plane would have to be authored as -0'-9".
#
# The east–west leg at y=0'-9" runs *along* a joist bay rather than across one. The leg that
# gets there from the riser crosses joists at x=6' and is drilled through their webs — 3/4"
# PEX in an 11 7/8" I-joist web, which is inside every manufacturer's hole chart and is why
# the branch is PEX here rather than the copper it becomes downstairs.
HYDRANT_BRANCH_MAIN = [
    PipeRun(uid="R9TC5VZ1WQ", tag="PR-M-CW-HYD-DIST", system=PipeSystem.WATER_COLD,
            path=(pt(ft(6), ft(13, 4)), pt(ft(6), ft(0, 9)), pt(ft(16, 8), ft(0, 9))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(9, 3)),
            serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
    # Porch leg: south into the wall's own plane (y=3 1/4", the 2x6 cavity's centre line),
    # then straight down inside W-M-S1 to the hydrant's seat at 2'-0".
    PipeRun(uid="B6HD0NKX3M", tag="PR-M-CW-PORCH-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 9)), pt(ft(12), ft(0, 3.25)), pt(ft(12), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(2)),
            wall_refs=(None, "W-M-S1"),
            serves=("FX-M-PORCH-HYD",)),
    # Balcony leg: the same jog into the wall plane, then up. Split at 10'-0" because the
    # second floor is between: below that line the pipe is crossing the deck and hosted by
    # nothing, above it it is inside W-S-S1's cavity (which starts at 10'-0"), and
    # `mep.wet_wall_occupancy` grades a declared segment against the wall's own z-extent.
    PipeRun(uid="V2FJ8LRY6P", tag="PR-M-CW-BALC-HYD", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 9)), pt(ft(16, 8), ft(0, 3.25)),
                  pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), ft(0, 3.25))),
            diameter=inch(0.75), material="pex",
            elevations=(ft(9, 3), ft(9, 3), ft(10), ft(12)),
            wall_refs=(None, None, "W-S-S1"),
            serves=("FX-S-BALC-HYD",)),
    # The barrel. This short copper leg is the hydrant's own metal tube plus the sleeve over
    # it, modelled as a run so that the insulation has somewhere to be billed and so that
    # `mep.exterior_hydrant_protection` has something to grade. It is the one place in the
    # house where a supply pipe is *in* the envelope rather than behind it: 10" of metal
    # from the seat in the stud cavity, out through 1/2" sheathing, 2" polyiso, 2" EPS and
    # the rainscreen, to the escutcheon on the cladding face at y = -5". PEX stops at the
    # seat — continuing in copper inboard would extend the bridge into the room.
    PipeRun(uid="T8WQ3E5AZC", tag="PR-M-CW-PORCH-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(12), ft(0, 3.25)), pt(ft(12), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-M-PORCH-HYD",)),
]

# The balcony hydrant's barrel, filed on ``second`` (datum 10'-0") with the wall it pierces.
HYDRANT_BRANCH_SECOND = [
    PipeRun(uid="G7YB4XN2SD", tag="PR-S-CW-BALC-HYD-CU", system=PipeSystem.WATER_COLD,
            path=(pt(ft(16, 8), ft(0, 3.25)), pt(ft(16, 8), inch(-5))),
            diameter=inch(0.75), material="copper",
            insulation='1/2" closed-cell elastomeric sleeve, foil-faced, over the barrel',
            elevations=(ft(2), ft(2)),
            serves=("FX-S-BALC-HYD",)),
]

# --- In-line supply devices (2026-08-01) ---------------------------------------------
#
# Everything below used to be prose. `notes/garage_hydrant.md` recorded the hydrant's
# shutoff and vacuum breaker in a sentence, `mep.hydrant_freeze_depth` emitted an UNKNOWN
# saying the model had no element for either, and the backflow preventer, the arrestors,
# the main shutoff and the RO provision lived only in `plans/TODO.md`. `PipeAccessory` is
# the element that makes them real; these are the fifteen the house actually has.
#
# An accessory with no `elevation` takes its host run's invert at the nearest vertex, which
# is what a valve on a pipe is at. Only the ones that sit somewhere other than on the pipe's
# own line — a stub rising to a cabinet, a breaker at a handle height — author one.
SUPPLY_DEVICES_BASEMENT = [
    # P2903.9.1. The service enters buried at -6'-0" and stays there all the way to the
    # garage (PR-G-HYDRANT-CW *is* the service); the house tees off it at (5', 1') and rises
    # to the basement ceiling, and this valve is on that riser at 4'-0" above the basement
    # floor — head height in the mechanical room, reachable with one hand and no ladder,
    # which is what "accessible" means and is not true of anything buried.
    #
    # The garage hydrant is upstream of it, on the service itself. That is deliberate rather
    # than an oversight: the hydrant's own seat is 6' down and is its shutoff, and bringing
    # the yard line up to a valve inside the house and back down would put a high point
    # above frost in the middle of it — the exact failure `mep.hydrant_freeze_depth` exists
    # to catch.
    PipeAccessory(uid="N5PK9WQ2TB", tag="PA-B-MAIN-SHUTOFF",
                  kind=PipeAccessoryKind.MAIN_SHUTOFF, pipe_ref="PR-B-CW-TRUNK",
                  position=pt(ft(5), ft(1)), elevation=ft(4), accessible=True,
                  room="RM-B-FURNACE",
                  model='1 1/4" full-port bronze ball valve, lever handle',
                  serves=("PR-B-CW-TRUNK",)),
    # P2902, the owner's request (plans/TODO.md §Plumbing): backflow protection on the
    # basement fixture connections. Two rather than one, because the two basement groups tee
    # off different trunks in different rooms and no single point is upstream of both. These
    # fixtures sit 9' below grade with the building drain leaving under the slab, which is
    # the condition that makes a siphon back into the supply worth a device rather than
    # trusting each fixture's own air gap.
    PipeAccessory(uid="H2VD7MCX4L", tag="PA-B-BFP-BATH",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-B-CW-BATH",
                  position=pt(ft(7), ft(26)), room="RM-B-FURNACE", accessible=True,
                  model='1/2" dual-check backflow preventer, testable',
                  serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    PipeAccessory(uid="Q8RJ1ZFN6V", tag="PA-B-BFP-SAUNA",
                  kind=PipeAccessoryKind.BACKFLOW_PREVENTER, pipe_ref="PR-B-CW-SAUNA",
                  position=pt(ft(17, 4), ft(16)), room="RM-B-SAUNA", accessible=True,
                  model='1/2" dual-check backflow preventer, testable',
                  serves=("FX-B-SAUNA-SH",)),
    # P2903.5. The washer slams two solenoids shut, so it takes two arrestors — one on each
    # supply. An arrestor on the cold alone leaves the hot line to hammer, which is the
    # failure this pair exists to prevent and the reason the check grades per system rather
    # than per appliance. Both sit at the machine's own riser, within the 6' of the quick-
    # closing valve the manufacturers specify.
    PipeAccessory(uid="F3ZC6TWL9N", tag="PA-M-WASH-WHA-CW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-CW-WASH",
                  position=pt(ft(8), ft(20, 7.2)), room="RM-M-LAUNDRY",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("FX-M-LAUNDRY",)),
    PipeAccessory(uid="K7XB2VDR5H", tag="PA-M-WASH-WHA-HW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-HW-WASH",
                  position=pt(ft(8), ft(21, 2.4)), room="RM-M-LAUNDRY",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("FX-M-LAUNDRY",)),
    # The dishwasher's fill solenoid is the other quick-closing valve in the house. It takes
    # hot water only, so it takes one arrestor, on the kitchen hot branch at the sink base.
    PipeAccessory(uid="W4NL8QSJ0M", tag="PA-M-DW-WHA-HW",
                  kind=PipeAccessoryKind.WATER_HAMMER_ARRESTOR, pipe_ref="PR-B-HW-KITCH",
                  position=pt(ft(29, 6.6), ft(33, 7.2)), room="RM-M-LIVING",
                  model="Sioux Chief MiniRester 660-G class, size A",
                  serves=("APPL-M-DW",)),
    # The branch isolation for both wall hydrants, at the tee where their shared riser
    # leaves the cold trunk. Not a code item — the hydrants' own seats are their shutoffs
    # and neither is winterised — but a hose bib is the thing most likely to need a valve
    # turned off in a hurry, and this is the last point where one valve reaches both.
    PipeAccessory(uid="Y6MT3HKB1F", tag="PA-B-HYD-ISO", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-CW-HYD", position=pt(ft(6), ft(16)), accessible=True,
                  room="RM-B-GYM", model='3/4" quarter-turn ball valve',
                  serves=("FX-M-PORCH-HYD", "FX-S-BALC-HYD")),
]

# The garage yard hydrant's two devices, on the service run they belong to (which is filed
# on ``main``, → WATER_SUPPLY above). The seat is the hydrant's own buried valve at -6'-0" —
# it takes the run's elevation, which is exactly the 72" bury `mep.hydrant_freeze_depth`
# grades — and the vacuum breaker screws onto the outlet at the handle, 2'-6" up.
SUPPLY_DEVICES_GARAGE = [
    PipeAccessory(uid="C9GW5PXV2R", tag="PA-G-HYD-SEAT", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-G-HYDRANT-CW", position=pt(ft(1, 6), ft(62)),
                  room="RM-GARAGE", model="hydrant's own compression seat, 6' bury",
                  serves=("FX-G-HYDRANT",)),
    PipeAccessory(uid="J1DS4RQZ8X", tag="PA-G-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-G-HYDRANT-CW",
                  position=pt(ft(1, 6), ft(62)), elevation=ft(2, 6), room="RM-GARAGE",
                  model="screw-on hose-bib vacuum breaker, ASSE 1011",
                  serves=("FX-G-HYDRANT",)),
]

# The porch hydrant's three, and the RO provision. All on ``main``.
SUPPLY_DEVICES_MAIN = [
    PipeAccessory(uid="A5VK7BND3T", tag="PA-M-PORCH-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-PORCH-HYD",
                  position=pt(ft(12), ft(0, 3.25)), room="RM-M-BED",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-M-PORCH-HYD",)),
    PipeAccessory(uid="E2QH9LCW6Y", tag="PA-M-PORCH-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-M-CW-PORCH-HYD-CU",
                  position=pt(ft(12), inch(-5)),
                  model="integral anti-siphon vacuum breaker, ASSE 1052",
                  serves=("FX-M-PORCH-HYD",)),
    # The penetration itself. This is the element that says "this hydrant is protected by
    # the envelope rather than by bury depth", which is what exempts it from
    # `mep.hydrant_freeze_depth` and hands it to `mep.exterior_hydrant_protection`. Its
    # `install_parts` are the three loose items the TODO asked for by name: nobody stocks
    # them as a hydrant, and they are properties of this hole in this wall.
    PipeAccessory(uid="U3FP6ZMG8B", tag="PA-M-PORCH-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-M-CW-PORCH-HYD-CU",
                  position=pt(ft(12), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-M-PORCH-HYD",)),
    # P2903 has nothing to say about this one: it is a capped 1/4" tee off the kitchen cold
    # riser, left for a reverse-osmosis unit nobody has bought yet. No fixture and no
    # fixture units, because a capped stub draws no water — what it buys is that the wall
    # does not have to be opened the day one is.
    PipeAccessory(uid="L8CY2WRT4K", tag="PA-M-RO-STUB", kind=PipeAccessoryKind.RO_STUB,
                  pipe_ref="PR-B-CW-TRUNK", position=pt(ft(29, 0.6), ft(34, 1.2)),
                  elevation=ft(2, 6), room="RM-M-LIVING", accessible=True,
                  model='1/4" compression stop on a capped tee, in the sink base'),
]

# The balcony hydrant's three, on ``second``.
SUPPLY_DEVICES_SECOND = [
    PipeAccessory(uid="S6BN1JXV7Q", tag="PA-S-BALC-HYD-SEAT",
                  kind=PipeAccessoryKind.SHUTOFF, pipe_ref="PR-M-CW-BALC-HYD",
                  position=pt(ft(16, 8), ft(0, 3.25)), room="RM-S-PLANT",
                  model="hydrant's own compression seat, inboard end of the barrel",
                  serves=("FX-S-BALC-HYD",)),
    PipeAccessory(uid="P0GZ5DKF9W", tag="PA-S-BALC-HYD-VB",
                  kind=PipeAccessoryKind.VACUUM_BREAKER, pipe_ref="PR-S-CW-BALC-HYD-CU",
                  position=pt(ft(16, 8), inch(-5)),
                  model="integral anti-siphon vacuum breaker, ASSE 1052",
                  serves=("FX-S-BALC-HYD",)),
    PipeAccessory(uid="M4TQ8HRC1Z", tag="PA-S-BALC-HYD-SEAL",
                  kind=PipeAccessoryKind.PENETRATION_SEAL, pipe_ref="PR-S-CW-BALC-HYD-CU",
                  position=pt(ft(16, 8), ft(0)),
                  model="gasketed escutcheon over a foamed barrel penetration",
                  install_parts=("silicone gasket, hydrant escutcheon",
                                 "plastic mounting bracket, non-conductive",
                                 'closed-cell spray foam, 1/4" annulus around the barrel'),
                  serves=("FX-S-BALC-HYD",)),
]

MAIN_ELEMENTS = [*SLEEVES, *SUPPLY_SLEEVES, *STACK_SLEEVES, *SECOND_DRAINS, *CONDENSATE_MAIN,
                 *LAUNDRY_MAIN,
                 *VENT_BRANCHES_MAIN, *MAIN_DEVICES, *WATER_SUPPLY, *GARAGE_SLEEVES,
                 *HYDRANT_BRANCH_MAIN, *SUPPLY_DEVICES_MAIN, *SUPPLY_DEVICES_GARAGE,
                 *DUCTS_MAIN, *REGISTERS_MAIN]
# The basement's two plumbing vents. Both are offset vents to VR-M-RADON-VENT's shared
# radon/plumbing chase at (1', 34'-6"), because neither room has a wet wall that continues to
# the storey above: every wall around the stair-foot bathroom except its own north partition
# is 12" cast concrete stopping at the main-floor deck, and the sauna's are a 2x4 partition,
# the centre concrete wall and the foundation. `mep.vent_reachability` grades the authored
# path — nothing here is inferred, so an unvented fixture would still fail loudly.
#
# Both share the same vertical band: the tee sits low, the riser goes up inside the room's own
# stud cavity, and the horizontal leg tops out at 8'-1" basement-relative rather than 8'-3",
# because the "basement ceiling" here is 9" of cast concrete and a run at the deck's underside
# would be cast into it (which `mep.sleeve_coverage` caught the first time it was tried). Each
# rises a few inches over its length to the chase so condensate drains back to the fixtures.
#
# Neither shares a leg with the other — the bathroom's runs north at x=7', the sauna's at
# x=9' — the same rule PR-S-SUITEBATH-VENT follows against the hall bath's branch.
VENT_BRANCHES_BASEMENT = [
    # RM-B-BATH. Was PR-B-UTIL-VENT, FX-1's vent, until 2026-07-30: same uid, same corridor
    # north at x=7' to the chase, new fixtures at the near end. The riser now stands in a real
    # stud cavity for the first time — W-B-BA-N, the bathroom's INT_2X6_STAGGERED_PLUMBING
    # north partition — instead of boxed onto a concrete face, which is what that wall's
    # assembly was chosen for. It crosses W-B-STR's concrete through SP-B-STR-BATH-VENT.
    #
    # The riser stands on the partition's line at (16', 21'-9 3/8"); the leg west runs 9"
    # south of it at y=21'-0", so its crossing of W-B-STR2 stays clear of the node the
    # partition tees into. Trap arms measured to that leg: 1'-0" from the water closet's
    # flange and 1'-5" from the lavatory's trap, against Table 1002.2's 6'-0" for 3" and
    # 3'-6" for 1 1/2".
    PipeRun(uid="CBPV01AAAA", tag="PR-B-BATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21)), pt(ft(7), ft(21)), pt(ft(7), ft(34, 6)),
                  pt(ft(1), ft(34, 6))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 6), ft(7, 8), ft(7, 9), ft(7, 10), ft(8, 0.5), ft(8, 1)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # RM-B-SAUNA's shower group. 2" for 4 DFU, rising at (17'-4", 13'-0") — inside W-B-CS's
    # 3 1/2" liner build-up, in the pan's own east wall, 6" south of the north liner and clear
    # of the mixer's two supply drops at 11'-10" and 12'-2". That is both fixtures' declared
    # wet wall (plan/fixtures.py) and the one basement wet wall that carries a framed wall on
    # the storey above, so the vent has a true stack path as well as this drawn one.
    #
    # Trap arms as the check measures them: 14" from the pan's drain and 23" from the floor
    # drain, against Table 1002.2's 5'-0" for a 2" arm. Above the sauna's hung ceiling the run leaves
    # the build-up north over W-B-SA-N, crosses the aisle west, and passes W-B-CW through
    # SP-B-CW-SAUNA-VENT at x=9'.
    PipeRun(uid="CBPV02AAAA", tag="PR-B-SAUNA-VENT", system=PipeSystem.VENT,
            path=(pt(ft(17, 4), ft(13)), pt(ft(17, 4), ft(13)),
                  pt(ft(17, 4), ft(14, 8)), pt(ft(9), ft(14, 8)),
                  pt(ft(9), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0, 6), ft(7, 4), ft(7, 6), ft(7, 8), ft(8, 0.5), ft(8, 1)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
]

BASEMENT_ELEMENTS = [*DRAINS, *CONDENSATE, *SUPPLY, *HYDRANT_BRANCH_BASEMENT,
                     *SUPPLY_DEVICES_BASEMENT, *WALL_SLEEVES, *SLAB_STUBS,
                     *VENT_BRANCHES_BASEMENT,
                     *EQUIPMENT, *PANEL, *BASEMENT_DEVICES,
                     *RADON_SUMP, *VENT_RISERS, *VENT_CLAMPS, *DUCTS_BASEMENT,
                     *REGISTERS_BASEMENT]
SECOND_ELEMENTS = [*DUCTS, *DUCTS_HVAC_SECOND, *REGISTERS, *REGISTERS_SECOND,
                   *REGISTERS_HVAC_SECOND, *VENT_BRANCHES_SECOND, *SECOND_DEVICES,
                   *HYDRANT_BRANCH_SECOND, *SUPPLY_DEVICES_SECOND]
ATTIC_ELEMENTS = [*NEMA_BOX, *NEMA_CLAMP, *LEADER_CLAMPS,
                  *ATTIC_DEVICES, *DUCTS_ATTIC, *DUCTS_HVAC_ATTIC,
                  *REGISTERS_ATTIC, *REGISTERS_HVAC_ATTIC]
