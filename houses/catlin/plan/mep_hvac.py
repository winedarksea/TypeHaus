# haus: editable
# Catlin MEP — air distribution — the ERV trunks, System 1's conditioned-air chase, equipment.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# The second-floor ERV trunks run in the second floor's joist bays — since 2026-08-21 that
# deck is split at x=18' (FS-S-WEST: 11.875" floor truss; FS-S-EAST: 11.875" I-joist, same
# depth, both 16" o.c., direction "x"), and each trunk's `floor_ref` names FS-S-WEST since
# every trunk starts at x=4' — the resolver validates each segment against whichever half
# its midpoint falls in, so the crossing at x=18' still resolves. Bay centers are
# `8" + n*16"` from the joist-line math in resolve/floors.py; bay 15 (y=20'-8") and bay 17
# (y=23'-4") are both clear of the stair FloorOpening (x:11'-18', y:25'-36') and both cross
# the central bearing wall at x=18'. The terminals on these trunks are in
# plan/mep_registers.py.

from typehaus import (
    ClearancePolicy,
    ClearanceZone,
    DuctRouting,
    DuctRun,
    DuctSystem,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Footprint2D,
    RegisterType,
    Service,
    ServicePort,
    SleevePenetration,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# Two terminal families: REG-T-ERV-SUP/EXH are ventilation terminals (small, continuous-
# flow, ~197 cfm whole-house rate) replacing the old furnace-styled REG-T-SUPPLY/RETURN
# (plans/TODO.md §HVAC) — old tags dropped, not aliased, so a schedule can't print both.
# REG-T-HP-SUP/RET are the bigger conditioned-air terminals on System 1's ducted chase.
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
    # The plant room's pair (2026-08-18, notes/plant_room.md). The room is held at ~75 F /
    # 70% RH year-round, which makes its ventilation a pressure question before it is an air
    # question: natatorium practice holds such a room 0.05-0.15 in. w.g. NEGATIVE to the
    # spaces around it, so house air leaks in (harmless) and room air never leaks into a
    # stud bay (the failure this whole room is built to prevent).
    #
    # A dedicated, dampered branch off EQ-B-ERV rather than a separate machine — the house
    # already owns a proper ERV in a mechanical room with a condensate drain and real frost
    # control, and "separate from the house ERV" is best had with an independent DAMPER, not
    # an independent unit. (The alternative considered and rejected was a through-wall
    # ERV: the class of unit available here is single-core and alternates supply and exhaust
    # on 75-second half-cycles, i.e. it cyclically pressurises the room, and the one on the
    # table is out of spec below -4 F against a -15 F design temperature.)
    #
    # RH-driven, not schedule-driven: no terminal and no ERV self-regulates humidity, and
    # the setpoint resets from 70% down to ~55% as outdoor air falls to -15 F.
    RegisterType(tag="REG-T-ERV-PLANT-EXH",
                 name="Plant-room stale-air extract, 6x4, motorised RH-controlled damper",
                 footprint=(inch(6), inch(4)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 source="notes/plant_room.md — dedicated dampered extract off EQ-B-ERV; holds RM-S-PLANT neutral-to-slightly-negative and is the room's only moisture removal path",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    # System 1's terminal in the plant room needs to be shuttable, which the plain
    # REG-T-HP-SUP is not. Two reasons, both fatal without it: DU-S-HP-SOUTH ties the room's
    # air to the whole-house air handler and every other room on the branch, so an open
    # damper carries the plant room's moisture house-wide; and a supply-only terminal in a
    # closed room pressurises it. Motorised so the RH controller owns it, interlocked with
    # REG-S-ERV-PLANT-EXH.
    RegisterType(tag="REG-T-HP-SUP-DAMPERED",
                 name="Heat-pump supply register, 12x6, motorised isolation damper",
                 footprint=(inch(12), inch(6)), height=inch(1),
                 plan_symbol="register",
                 source="notes/plant_room.md — REG-T-HP-SUP with a motorised zone damper so System 1 can be isolated from a 70% RH room",
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
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
    # Third family: a passive transfer louver — no duct/fan/system, just a hole with a
    # grille, moving air on pressure difference alone. `ports=()` is deliberate: nothing to
    # connect it to. (`needs` still defaults to SUPPLY_AIR — unused by a register, and the
    # dialect can't spell an empty frozenset, so it's left rather than worked around.)
    # 12" face fits a 14 1/2" clear 2x6 bay without cutting a stud (10x8 free opening);
    # wider needs a header. `footprint`/`height` are swapped vs. the ceiling diffusers above
    # because this one mounts in a wall, not a ceiling — swap them back and it resolves flat.
    RegisterType(tag="REG-T-TRANSFER-1210",
                 name="Passive transfer louver, 12x10 face (10x8 free opening)",
                 footprint=(inch(12), inch(1)), height=inch(10),
                 plan_symbol="register",
                 source="Passive door/wall transfer grille, single 2x6 bay — no duct, no damper",
                 ports=()),
)

# No gas appliance in the house: the gas furnace that used to stand at (4', 29'-4") is gone
# (all-electric — three Gree heat-pump systems + radiant floor), and `plan/site.py` never authored a GAS
# UtilityLine to feed one. The air-side ports it used to carry now live on EQ-T-ERV and
# EQ-T-GREE-SLIM24 (plan/electrical.py) — the two things left that push air, neither of
# which burns anything.
EQUIPMENT_TYPES = (
    # ONE 80-gal hybrid HPWH (2026-08-15), replacing the earlier two-tank 120V-compressor/
    # 240V-element split. Rheem ProTerra PROPH80, EcoNet-enabled: 4.5 kW resistance element,
    # 30A/240V dedicated circuit, single power whip.
    #
    # Compressor-only draw ("Heat Pump"/"Energy Saver" mode) is ~360-500W per the datasheet;
    # `LM-WH` (plan/circuits.py) carries 500 VA as its `max_simultaneous_va` ceiling.
    # ESPHome's esphome-econet component forces Heat-Pump-Only mode on battery/near-peak,
    # Hybrid otherwise — a demand-response behavior on the normal circuit (lives on
    # `LoadManagement`, not a second `Equipment`); the breaker/panel/NEC 220.82 sizing still
    # goes against the nameplate 4.5 kW. See `code.P2804_water_heater_relief` for the TPR.
    #
    # Fallback if reverted to a 120V-only plug-in HPWH (~450W, no 240V circuit): swap
    # `type_ref` on EQ-B-WH to a 120V-only EquipmentType, retag `circuit` to a 1-pole 120V
    # circuit at ~450 VA, and delete `LM-WH`. Nothing else needs to move.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Water heater, Rheem ProTerra 80gal hybrid heat pump (EcoNet)",
                  product_ref="PROD-RHEEM-PROPH80",
                  footprint=(inch(24), inch(24)), height=ft(5, 8),
                  plan_symbol="water-heater",
                  source="Rheem PROPH80 T2 RH400-30 / ProTerra XE80T10HS45U0 class: 80 gal, 4.5 kW resistance element, 30A/240V dedicated circuit, ~360-500W compressor draw in Heat Pump Only mode, EcoNet wifi module.",
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))))),
    # --- the backup microgrid (2026-08-02, notes/backup_power.md) ----------------------
    #
    # EG4 12kPV: name is the PV input, not the output. 12,000 W array in, 8,000 W AC out
    # continuous — the number the autonomy calc and CKT-ESS-GRID breaker use. Surge is the
    # datasheet's 16 kW/0.5 s (12 kW/1 s, 10 kW/1 min) — 0.5 s is what a compressor start asks.
    # UL 9540 belongs to the battery, not here — marking the inverter would pass R327.2's
    # check on the strength of the wrong product.
    EquipmentType(tag="EQ-T-EG4-12KPV", name="EG4 12kPV hybrid inverter",
                  product_ref="PROD-EG4-12KPV",
                  footprint=(inch(27), inch(12)), height=inch(35),
                  inverter_kw_continuous=8.0, inverter_kw_surge=16.0, pv_input_kw=12.0,
                  ports=(ServicePort(tag="grid", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="load", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),),
                  source="EG4 12kPV spec sheet, read 2026-08-02: 8,000 W continuous AC output (120/240V split phase), 12,000 W PV input over 2 MPPTs at 600 VDC max, 16 kW/0.5 s surge, UL 1741 + UL 9540 listed."),
    # EG4 PowerPro WallMount Indoor, 14.3 kWh. One unit to start; R327.5's 40 kWh indoor
    # aggregate ceiling is what a second (28.6 kWh) or third (42.9, fails) would answer to.
    # `ul_9540_listed=True` is a declaration `code.R327_ess_listing` reports as-is — it never
    # infers a listing from the name. The 3'-0" REQUIRED clearance is the owner's separation
    # rule (plans/TODO.md), not a code working space — `advisory.ess_clearance` grades it,
    # no CODE check does — authored as a band all around since it's about any neighbouring
    # device, not front-face access.
    EquipmentType(tag="EQ-T-ESS-BATT", name="EG4 PowerPro WallMount Indoor, 14.3 kWh",
                  product_ref="PROD-EG4-POWERPRO-WM",
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

# --- Ventilation: ERV fresh-air / stale-air trunks in the second-floor joist bays ----
# Ventilation trunks (EQ-B-ERV), not heating ducts. Sized to ASHRAE 62.2, not furnace CFM:
# 0.03 x 5,115 ft2 + 7.5 x 6 = 198 cfm required, 210 cfm on the machine (2026-08-01) — at
# 10"x6" that's ~505 fpm, quiet enough to run continuously (vs. the ~4x oversized 12"x8"/
# 14"x8" furnace trunks they replaced). Balanced pair = ERV SUPPLY/RETURN; dedicated stale
# pulls (hall-bath shower) use EXHAUST. Reaches all four storeys via joist-bay routing
# (FS-S-WEST/FS-S-EAST, FS-ATTIC) dropping to CHASE routing in the basement under SL-M-DECK.
DUCTS = [
    # DU-M-ERV-SUP is gone (2026-07-29): the second storey now takes fresh air off System 1's
    # chase (REG-S-HP-BED1/2/3 on DU-S-HP-SUP, suite on DU-S-HP-SUITE) and returns stale air
    # via DU-M-ERV-RET below (now carrying seven pickups). A supply trunk with no terminal
    # is deleted, not stubbed. Main storey's own pair is DU-M1-ERV-SUP/RET below.
    DuctRun(uid="CMD902AAAA", tag="DU-M-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(23, 4)), pt(ft(32), ft(23, 4))), width=inch(10), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST"),
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
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST"),
    DuctRun(uid="CMDV02AAAA", tag="DU-M1-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(15, 4)), pt(ft(32), ft(15, 4))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST"),
]

# Basement trunks leave EQ-B-ERV in the furnace room and run exposed-in-chase under the
# main floor. CHASE routing, no floor_ref, and that is now a *choice* rather than the only
# option it was: until 2026-08-21 the whole ceiling was SL-M-DECK's 9" pour with no joist
# bays to ride at all. Two thirds of it is FS-M-WEST/FS-M-EAST joists now, and the west
# half's bays run east-west — the same direction the trunk's long leg does at y=18'. Moving
# these into the bays (routing=JOIST_BAY, floor_ref="FS-M-WEST") would buy back the 6" of
# headroom the chases cost along that run. Left as chase because the runs also cross the
# x=18' bearing line and the concrete band, so they cannot be bays end to end, and splitting
# a trunk into bay and chase segments is a routing pass of its own — recorded in
# plans/TODO.md rather than half-done here.
DUCTS_BASEMENT = [
    DuctRun(uid="CBDV01AAAA", tag="DU-B-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(18)), pt(ft(27), ft(18)), pt(ft(27), ft(9))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
    DuctRun(uid="CBDV02AAAA", tag="DU-B-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(8)), pt(ft(16), ft(8))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
    # Stair-foot bathroom branch (2026-07-30): 6"x4" for one 50 cfm terminal, teed off at
    # y=20' and crossing W-B-STR2. That crossing used to be a cast opening in 12" concrete,
    # set with the room's three service sleeves before the pour; W-B-STR2 is a steel-stud
    # partition since 2026-08-21, so it is a boxed-out stud bay the framer cuts, and the
    # three sleeves beside it are gone (plan/mep_sleeves.py).
    DuctRun(uid="CBDV03AAAA", tag="DU-B-ERV-BATH", system=DuctSystem.EXHAUST,
           path=(pt(ft(5), ft(20)), pt(ft(11, 8), ft(20))),
           width=inch(6), depth=inch(4), routing=DuctRouting.CHASE),
    # Sauna's fresh-air branch (2026-07-29): 4"x4", a trickle it can shut rather than a
    # room's worth of air. Taps the supply trunk at (5', 18'), runs south along W-B-SA-W to
    # the heater line, ending over EQ-B-SAUNA-HTR on purpose — fresh air dropped onto the
    # stones drives the convection loop down to REG-B-EXH2, the only way the sealed room
    # turns over.
    DuctRun(uid="CBDV04AAAA", tag="DU-B-SAUNA-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(5), ft(18)), pt(ft(5), ft(8, 9)), pt(ft(9, 9.8125), ft(8, 9))),
           width=inch(4), depth=inch(4), routing=DuctRouting.CHASE),
]

# Attic distribution rides the FS-ATTIC joist bays. DU-A-ERV-SUP is gone (2026-07-30, same
# reasoning as DU-M-ERV-SUP): its terminal REG-A-SUP1 was made redundant by REG-A-HP-WEST,
# a floor boot off System 1's DU-S-HP-SUITE branch directly below. Attic air pattern is now
# uniform: conditioned/fresh air in off System 1, stale air out through the one ERV extract.
# Surviving return starts at x=2' by the maintenance shaft (1', 34'-6", same shaft the ERV
# branch rides up from the basement) and runs to its terminal at bay-centre 31'-4"
# (8"+23*16"); DU-S-BATH1-EXH's bay at 32'-8" stays free. Nothing here nears FO-A-STAIR.
# Coverage held: RM-A-STUDY via REG-A-HP-STUDY, RM-A-WEST via REG-A-HP-WEST off the suite branch.
DUCTS_ATTIC = [
    DuctRun(uid="CADV02AAAA", tag="DU-A-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(2), ft(31, 4)), pt(ft(6), ft(31, 4))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
]

# --- System 1: the conditioned-air chase (plans/TODO.md §HVAC) -----------------------
# EQ-S-HP1-AH (plan/electrical.py) hangs INSIDE the dropped soffit box at its south end
# (y 6'..9'-7", over RM-S-STUDY2) and feeds ONE straight supply trunk north along the
# second-floor hallway inside that soffit, with a short return-plenum stub at its rear
# (ERV fresh feed wyed in behind it — DU-S-ERV-HP-FEED below). CHASE routing, no
# `floor_ref`: it's in a framed box, not a joist bay, so joist-bay geometry checks
# correctly don't apply, and its two crossings of the x=18' bearing line are legal.
# Hall is x 18'-2 3/4"..21'-8" clear: supply at x=19'-4", return at x=20'-8", side by side.
# `design_cfm` is authored intent for a low-flow straight run (why one 24k unit covers the
# upstairs): 14x8 @ 750 cfm is ~965 fpm.
DUCTS_HVAC_SECOND = [
    # Starts at y=9'-7" — EQ-S-HP1-AH's discharge face — since 2026-07-30: the unit lives
    # INSIDE the soffit box at its south end (y 6'..9'-7", see plan/electrical.py), so the
    # trunk is everything north of the case.
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(9, 7)), pt(ft(19, 4), ft(33))),
            width=inch(14), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=750),
    # Plenum stub, not a trunk (2026-07-30): REG-S-HP-RET sits at the unit's rear corner;
    # this 6" carries grille air to the bottom-return opening. Rooms do NOT return to the
    # AH — only extract is the ERV's stale pickups; the hall (fed by door undercuts) is the
    # AH's sole breathing source. Deliberate loose coupling: ERV balance is set by its own
    # terminals, AH just recirculates the hall plus whatever DU-S-ERV-HP-FEED injects.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(ft(20, 8), ft(9, 8)), pt(ft(20, 8), ft(9, 2))),
            width=inch(14), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=750),
    # West branch to RM-S-SUITE, rerouted 2026-07-30: tees off DU-S-HP-SUP at D-S-SUITE's
    # centreline (y=14'-1 7/8"), crosses W-S-C2B above the door through the header/top-plate
    # cripple zone (an 8"-deep duct on the 14" soffit drop clears it), then runs west down
    # the suite's entry arm to the grille near D-S-SUITEBATH. 6'-10" of 10x8 replaces the
    # old 10'-10" detour across RM-S-SUITEBATH.
    # 250 cfm (not 150): feeds two terminals — REG-S-HP-SUITE and REG-A-HP-WEST, a floor
    # boot up through FS-ATTIC directly above. ~450 fpm through 10x8, still quiet.
    DuctRun(uid="CSDH03AAAA", tag="DU-S-HP-SUITE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(14, 1.875)), pt(ft(12, 6), ft(14, 1.875))),
            width=inch(10), depth=inch(8), routing=DuctRouting.CHASE, design_cfm=250),
    # The two south rooms' branch (2026-08-16). RM-S-PLANT and RM-S-STUDY2 were the only
    # conditioned rooms on this storey with no drawn terminal, which was always the odd
    # reading: EQ-S-HP1-AH hangs in RM-S-STUDY2's own ceiling soffit.
    #
    # Nothing can leave the trunk southward inside SF-S-DUCT: the air handler's 21"x43" case
    # fills the box from y=6'-0" to y=9'-7", leaving ~5" either side of it — no lane for a
    # branch. So this one comes off the top instead, riding the FS-ATTIC joist bay centred at
    # y=3'-4" (8" + 2*16"), a floor cavity that runs unbroken east-west over BOTH rooms. It
    # feeds off the same riser out of the trunk head at x=19'-4" that DU-A-HP-STUDY leaves
    # from, dropping into the bay 4" north of that branch's centreline instead of continuing
    # up onto the attic deck. The riser itself stays undrawn (DuctRun carries no elevation),
    # exactly as DU-S-ERV-HP-FEED's rise and EQ-S-HP1-AH's condensate drop are — plans/TODO.md.
    #
    # JOIST_BAY and not CHASE because the alternative — running west along the attic floor —
    # cannot get past W-A-C1/C1B, the x=18' bearing wall RB-HOUSE sits on, which does not open
    # up. Inside the bay the duct passes UNDER that wall's bottom plate; mep.duct_joist_bay
    # reports the bearing-line crossing as a fire-blocking note (R302.11), not a conflict.
    # 8x6 fits the 11 7/8" I-joist depth with the 14 1/2" clear bay to spare.
    #
    # 150 cfm is 75 per terminal, taken OUT of the trunk's authored 750 by damper, not added
    # to it: 750 is the air EQ-S-HP1-AH moves, and two more registers redistribute it rather
    # than increase it. ~450 fpm through 8x6, in line with the rest of System 1.
    #
    # Both ends stop ON a terminal — east at REG-S-HP-STUDY2 (22'-8"), west at REG-S-HP-PLANT
    # (6'-8") — like DU-S-HP-SUITE and DU-A-HP-STUDY. The riser at x=19'-4" lands 3'-4" in
    # from the east end, so the tee throws a short arm to the study and a long one to the
    # plant room; there is no duct east of the study's boot to balance that, and none needed.
    DuctRun(uid="NYRX7TBEGH", tag="DU-S-HP-SOUTH", system=DuctSystem.SUPPLY,
            path=(pt(ft(22, 8), ft(3, 4)), pt(ft(6, 8), ft(3, 4))),
            width=inch(8), depth=inch(6), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", design_cfm=150),
    # ERV -> System 1 fresh-air feed (2026-07-30), the one place fresh air enters the
    # heat-pump loop. Taps DU-M1-ERV-SUP at y=12'-8" (FS-SECOND bay), rises into the lane
    # DU-S-HP-RET vacated, runs south at x=20'-8" to inject behind REG-S-HP-RET via a
    # 45-degree wye. Wye (not hard-ducted) is deliberate: the ERV and AH run on independent
    # schedules and each must breathe without the other. 6" is the biggest round the
    # joist-bay tap takes; ~100 cfm (storey's share of whole-house rate) runs ~510 fpm.
    # Vertical rise into the soffit is undrawn (DuctRun has no elevation) — same status as
    # EQ-S-HP1-AH's condensate drop, per plans/TODO.md.
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            path=(pt(ft(20, 8), ft(12, 8)), pt(ft(20, 8), ft(10))),
            width=inch(6), depth=inch(6), routing=DuctRouting.CHASE, design_cfm=100),
    # The plant room's dedicated extract (2026-08-18). Rides the FS-ATTIC joist bay centred
    # at y=4'-8" (8" + 3*16") — the next bay north of DU-S-HP-SOUTH's at 3'-4", so the
    # room's supply and its extract are in different bays and different halves of the room.
    # (Not the 6'-0" bay: FS-ATTIC carries trimmers at 5'-7" and 5'-9 5/8" there, and a 6"
    # duct centred at 6'-0" straddles one — mep.duct_joist_bay.)
    # Runs east from the terminal to x=19'-4", the same riser lane out of the trunk head
    # that DU-S-HP-SOUTH and DU-A-HP-STUDY leave from, and drops through SF-S-DUCT to
    # EQ-B-ERV's stale side. The vertical leg is undrawn — DuctRun carries no elevation —
    # exactly as DU-S-ERV-HP-FEED's rise and EQ-S-HP1-AH's condensate drop are (plans/TODO.md).
    #
    # 25 cfm against ~20 of makeup: extract-biased on purpose, which is what "slightly
    # negative" means in air rather than in inches of water. 6x4 fits the 11 7/8" I-joist bay
    # with room to spare and runs ~150 fpm, quiet enough for a room somebody sits in.
    #
    # An ERV is damage limitation, not humidity control. Even an 84%-latent core loses ~16%
    # of the moisture in every air change; at this flow against -15 F outdoor air the
    # unrecovered loss is on the order of 1.5-2 gal/day, so a humidifier is required
    # regardless — see notes/plant_room.md, and plans/TODO.md for the unmodelled item.
    DuctRun(uid="RVGWJXKPZ7", tag="DU-S-PLANT-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(14), ft(4, 8)), pt(ft(19, 4), ft(4, 8))),
            width=inch(6), depth=inch(4), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", design_cfm=25),
]

# One attic branch left (2026-07-30): RM-A-STUDY's, which genuinely needs a horizontal run
# since the room starts at x=22'-4", east of anything the trunk passes under. CHASE routing
# — rides the attic floor/knee space, not a joist bay. DU-A-HP-EAST is gone: its grille
# became a straight boot off the trunk (REG-A-HP-EAST), same pattern as REG-A-HP-WEST —
# a 6'-8" run just to reach a grille that could sit anywhere in the open room.
DUCTS_HVAC_ATTIC = [
    DuctRun(uid="CADH01AAAA", tag="DU-A-HP-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(3)), pt(ft(26), ft(3))),
            width=inch(8), depth=inch(6), routing=DuctRouting.CHASE, design_cfm=100),
]

# The tank moved from (6'-2 1/4", 32'-9 7/8") to (5'-6", 24'-0") on 2026-08-23, to free the
# furnace room's NE corner for the ESS closet (plan/storeys/basement.py). It is not a
# preference: EQ-B-ESS-BATT declares a REQUIRED 48" x 41" separation zone all round
# (EQ-T-ESS-BATT, above), `advisory.ess_clearance` grades it with no room-or-wall exemption,
# and the old tank stood squarely inside the zone a battery in that corner would project.
# With the room only 10' wide there is no room to buy the 48" in x — every foot west of
# x=3'-11" is the 36" NEC 110.26 working space in front of ED-B-PANEL, ED-B-BACKUP-PANEL,
# ED-B-BACKUP-ENCL and ED-B-NET-PATCH — so the 41" had to come out of y, which means south.
#
# (5'-6", 24'-0") is what is left once the room's other fixed points are honoured: north of
# D-B-FURN's leaf (which sweeps to y=20'-8"), west of EQ-B-ESS-INV (x=7'-0 5/16"), south of
# EQ-B-ERV (y=28'-1 5/8"), and starting at x=4'-6" so the panel wall's working space stays
# clear. It also SHORTENS the plumbing: all three runs below leave the tank heading south,
# and PR-B-CW-WH now arrives straight up its own x=5'-6" line instead of doglegging.
#
# **Four literals, one position.** This coordinate is repeated verbatim as a path endpoint in
# PR-B-HW-TRUNK, PR-B-CW-WH and PR-B-HW-BATH1 (plan/mep_supply.py) and is the datum for
# PR-B-WH-TPR (plan/mep_drainage.py). Move the tank without moving all four and the hot
# trunk, the cold feed and the bath-1 branch silently disconnect — nothing in the resolver
# pulls a pipe onto its equipment. `test_water_heater_connections.py` asserts the three
# endpoints coincide with EQ-B-WH.position in the RESOLVED model, so the trap is now caught
# in CI rather than by eye.
EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(ft(5, 6), ft(24)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH-240",
             relief_discharge_ref="PR-B-WH-TPR"),
]
