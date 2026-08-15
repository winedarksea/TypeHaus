# haus: editable
# Catlin MEP — air distribution — the ERV trunks, System 1's conditioned-air chase, equipment.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# The second-floor ERV trunks run in the FS-SECOND joist bays (11.875" I-joist, 16" o.c.,
# direction "x"). Bay centers are `8" + n*16"` from the joist-line math in resolve/floors.py; bay
# 15 (y=20'-8") and bay 17 (y=23'-4") are both clear of the stair FloorOpening (x:11'-18',
# y:25'-36') and both cross the central bearing wall at x=18'. The terminals on these trunks are
# in plan/mep_registers.py.

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
    # ONE 80-gallon hybrid heat-pump water heater (2026-08-15, replacing the two-tank
    # 120V-compressor/240V-element split this house carried since plans/electrical_notes.md
    # was first drafted — see the corrected note below). Rheem ProTerra PROPH80, EcoNet-
    # enabled: 4.5 kW resistance element, 30A/240V dedicated circuit, single power whip —
    # a real product, not two products standing in for one.
    #
    # The compressor's own steady-state draw in the mode EcoNet calls "Heat Pump" /
    # "Energy Saver" — no resistance backup — is ~360-500W per the datasheet and vendor
    # documentation; `LM-WH` (plan/circuits.py) carries that as its 500 VA
    # `max_simultaneous_va` ceiling, the conservative round number. Home automation
    # (ESPHome's `esphome-econet` component bridging the unit's EcoNet API to Home
    # Assistant) forces Heat-Pump-Only mode whenever the house is on battery (grid down)
    # or near the 200A service peak, and drops back to Hybrid mode otherwise. The nameplate
    # 4.5 kW is what the breaker, the panel schedule and the NEC 220.82 estimate are sized
    # against — the automation is a demand-response behavior layered on top of a normal
    # circuit, not a second circuit, so it lives on `LoadManagement`, not on a second
    # `Equipment`. See `code.P2804_water_heater_relief` for the TPR discharge this needs.
    #
    # Reverting to the original two-implementation note this replaced (single 120V
    # "plug-in" HPWH, no 240V circuit at all, ~450W max, entirely on backup): swap
    # `type_ref` on EQ-B-WH to a small 120V-only EquipmentType (power_120 port, no
    # resistance element), retag its `circuit` to a 1-pole 120V circuit at ~450 VA, and
    # delete `LM-WH` — the mode-switching automation has nothing left to switch. Nothing
    # else in the plan (piping, position, room, TPR discharge) needs to move.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Water heater, Rheem ProTerra 80gal hybrid heat pump (EcoNet)",
                  footprint=(inch(24), inch(24)), height=ft(5, 8),
                  plan_symbol="water-heater",
                  source="Rheem PROPH80 T2 RH400-30 / ProTerra XE80T10HS45U0 class: 80 gal, 4.5 kW resistance element, 30A/240V dedicated circuit, ~360-500W compressor draw in Heat Pump Only mode, EcoNet wifi module.",
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))))),
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

EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(m(1.88684), m(10.0015)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH-240",
             relief_discharge_ref="PR-B-WH-TPR"),
]
