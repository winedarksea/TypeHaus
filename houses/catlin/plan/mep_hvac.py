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
    # A WALL-ORIENTED SUPPLY TYPE STOOD HERE FOR ONE DAY AND IS GONE (2026-08-30).
    # REG-M-SUP4 spent 2026-08-29 on W-M-LS at 5'-0" and needed its own type for it; the
    # owner then put it back in RM-M-STUDY's ceiling over ED-M-STUDY-SPOT and paired it with
    # a LOW extract, so `REG-T-ERV-SUP-WALL` had no user left and was deleted with its
    # prices.toml row. **The finding it was minted for outlived it and is stated on
    # REG-T-ERV-EXH-WALL below**, which is now the house's only wall-oriented ERV terminal
    # type: `footprint` is a PLAN rectangle, so a ceiling grille authors (face, face) with
    # `height` as its 1" thickness and a wall grille authors (face, DEPTH) with `height` as
    # the face. Mount a ceiling type on a wall and 3" of it draws inside the studs.
    RegisterType(tag="REG-T-ERV-EXH", name="ERV stale-air extract diffuser, 6\" round",
                 footprint=(inch(7), inch(7)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    # The house's ONE wall-oriented ERV terminal type, and the note above is why it is the
    # only one: a CEILING diffuser lies in the plane it is cut into, so its type is a 7x7
    # face 1" deep, and mounting that type on a WALL tells the resolver the body reaches 7"
    # off the wall into the room. ``_body_profile`` measures a wall mount's projection as
    # the local y extent of its footprint, so REG-A-STUBATH-EXH — the house's one wall-hung
    # extract — read as a 7" protrusion, past A117.1 §307.2's 4", and stood as an
    # obstruction inside FX-A-STUBATH-WC's required clear space. It surfaced the day
    # ``active_code_profile`` was set (plan/manifest.py) and the water-closet envelope
    # stopped being dropped; before that the zone did not resolve and nothing could collide
    # with it. A sidewall grille is a 7" face 1" deep, which is what this says.
    RegisterType(tag="REG-T-ERV-EXH-WALL",
                 name="ERV stale-air extract diffuser, 6\" round, sidewall",
                 footprint=(inch(7), inch(1)), height=inch(7),
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
    # ** REG-T-HP-RET GREW TO A 25x20 FILTER-BACK GRILLE ON 2026-08-30. ** It was 20x14 —
    # 280 in2 gross, and 750 cfm through it is 386 fpm face velocity. Manual D SS4-10 wants
    # 350 fpm at a plain return grille and 300 at one carrying the filter, which is what this
    # one is: with the machine hung in SF-S-HP1 there is no filter cabinet anywhere else in
    # the system, and the grille is the only serviceable face a person can reach. 480 in2
    # gross is 225 fpm, comfortably under both.
    #
    # 30" in x and 16" in y, not a square-ish 25x20, because the return chamber it opens into
    # is the 19" of SF-S-HP1 south of the cabinet: width is the free dimension there and
    # depth is not. It still leaves 21 3/8" of the box's 72 3/4" clear width either side.
    # (Nothing in the model records a filter or an access panel anywhere — see plans/TODO.md.)
    RegisterType(tag="REG-T-HP-RET", name="Heat-pump return grille, 30x16, filter-back",
                 footprint=(inch(30), inch(16)), height=inch(1),
                 plan_symbol="register",
                 source="Filter-back return grille, 30 x 16 nominal (480 in2 gross), hinged face, MERV 13 1\" filter behind it. Sized to Manual D SS4-10's 300 fpm figure for a filter grille at System 1's 750 cfm, which is 225 fpm here; the 20x14 it replaced was 386 fpm and carried no filter.",
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
# UtilityLine to feed one. The air-side ports it used to carry now live on
# EQ-T-BROAN-B210E75RT (plan/mep_erv_types.py) and EQ-T-GREE-DUC24 (plan/electrical.py) —
# the two things left that push air, neither of which burns anything.
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
# ================= THE RECTANGULAR ERV IS GONE (2026-08-25) =========================
#
# Nine sheet-metal ERV trunks used to live in the four lists below — 10x6 and 8x6 trunk and
# branch with tees cut into them, sized to ASHRAE 62.2 rather than to furnace CFM and, at
# ~505 fpm, perfectly quiet. What was wrong with them was not the sizing: it was that they
# were a *furnace*-shaped system for a ventilator, and that half the machine they served did
# not exist. The install is semi-rigid radial now — one 75 mm run per terminal off three
# sub-manifolds, plus a real outdoor side, plus four drawn risers — and all of it lives in
# **plan/mep_erv.py**.
#
# The four lists stay as empty lists rather than being deleted, so plan/mep.py's per-storey
# assembly (and therefore element order in model.json) is untouched by the move.
#
# Deleted, for the record: DU-M-ERV-RET, DU-M1-ERV-SUP, DU-M1-ERV-RET, DU-B-ERV-SUP,
# DU-B-ERV-RET, DU-B-ERV-BATH, DU-B-SAUNA-SUP, DU-S-BATH1-EXH, DU-A-ERV-RET. Also
# DU-S-PLANT-EXH, which the plan's port budget moved onto the attic sub-manifold.
DUCTS = []

DUCTS_MAIN = []

DUCTS_BASEMENT = []

DUCTS_ATTIC = []

# --- System 1: the conditioned-air chase (plans/TODO.md §HVAC) -----------------------
# EQ-S-HP1-AH (plan/electrical.py) hangs INSIDE the dropped soffit box at its south end
# (y 6'..9'-7", over RM-S-STUDY2) and feeds ONE straight supply trunk north along the
# second-floor hallway inside that soffit, with a short return-plenum stub at its rear
# (ERV fresh feed wyed in behind it — DU-S-ERV-HP-FEED below).
#
# SOFFIT routing + `soffit_ref="SF-S-DUCT"` since 2026-08-25, replacing CHASE. CHASE was
# never a description of where these run — it was the flag that turned the joist-bay check
# off, and nothing checked anything in its place, which is why every clearance in this file
# used to be hand arithmetic in a comment. Naming the modeled Soffit puts them under
# `mep.duct_soffit_occupancy`, which derives the box's clear section from its own drop,
# framing member and lining and measures both trunks, the air handler and the strip heater
# against it side by side. It also gives them their elevation for free: a run that names a
# soffit and authors no elevation sits on the box's clear underside. CHASE keeps its honest
# meaning for a framed shaft that is not modeled as a Soffit. The two crossings of the
# x=18' bearing line are legal either way.
# Hall is x 18'-2 3/4"..21'-8" clear: supply at x=19'-4", return at x=20'-8", side by side.
# `design_cfm` is authored intent for a low-flow straight run (why one 24k unit covers the
# upstairs): 14x8 @ 750 cfm is ~965 fpm.
DUCTS_HVAC_SECOND = [
    # ** 14x8 -> 18x8, AND IT STARTS IN SF-S-HP1 NOW (2026-08-30). ** 750 cfm through 14x8 is
    # 965 fpm, above Manual D's 900 fpm ceiling for a trunk in a finished space — a number
    # this file's own `design_cfm` comment asserted was "low-flow" and never divided out.
    # 18x8 is 750 fpm. 18" and not 20" because the hall box's 30 3/4" clear has to carry the
    # ERV mixing-box feed past the trunk as well: 18 + 2 hanger gap + 6 = 26, and the feed's
    # own drop is fixed at x=20'-8", which 20x8 does not clear.
    #
    # x moved 19'-4" -> 19'-6" with the widening — the west face lands 3/8" inside the
    # cavity and the east face keeps the full 2" off the ERV feed. REG-A-HP-EAST at
    # (19'-4", 11'-4") is still squarely over the trunk (x 18'-9"..20'-3"), so its floor boot
    # still rises straight.
    #
    # It begins at (19'-6", 5'-3"), the north face of the air handler's supply plenum inside
    # SF-S-HP1, and crosses the y=7'-6" seam into SF-S-DUCT. `soffit_ref` names the hall box
    # because that is where 27 of its 29 feet run; the check clips a run's extent to the box
    # it names, which is the same idiom DU-S-HP-SUITE uses where SF-S-SUITE abuts. The 2'-3"
    # inside SF-S-HP1 is therefore not graded there — it is the plenum's own neck, and it
    # runs in the west third of that box, well clear of ST-S2A's flight at x>=22'-5 3/8".
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(5, 3)), pt(ft(19, 6), ft(33))),
            width=inch(18), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=750),
    # The return-plenum stub, rebuilt in SF-S-HP1 on 2026-08-30 and now carrying the return
    # the right way round. It used to run (20'-8", 9'-8") -> (20'-8", 9'-2") in the hall box:
    # REG-S-HP-RET sat 1" NORTH of the air handler's case, which is the same face the supply
    # leaves from. A return grille at the discharge end is a short circuit drawn as a plenum.
    #
    # The machine's return is its south face, so the grille and this stub are south of it:
    # 25x14 from REG-S-HP-RET's filter-back grille at (20'-7", 1'-9") north to (20'-7", 2'-3"),
    # where the case's collar and flex connector pick it up 3 1/8" further on. 750 cfm through
    # 25x14 is 309 fpm — a return velocity, not a supply one; the old 14x8 stub was 965.
    #
    # Rooms still do NOT return to the AH — the only extract is the ERV's stale pickups, and
    # the hall (fed by door undercuts) through D-S-STUDY2's 2'-6" cased opening is the AH's
    # breathing source. That loose coupling is unchanged by the move; the path is one cased
    # opening longer. ERV balance is still set by its own terminals, and the AH recirculates
    # whatever DU-S-ERV-HP-FEED injects through EQ-S-ERV-MIX at the far side of this chamber.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(ft(20, 7), ft(1, 9)), pt(ft(20, 7), ft(2, 3))),
            width=inch(25), depth=inch(14), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-HP1", design_cfm=750),
    # West branch to RM-S-SUITE, rerouted 2026-07-30: tees off DU-S-HP-SUP at D-S-SUITE's
    # centreline (y=14'-1 7/8"), crosses W-S-C2B above the door through the header/top-plate
    # cripple zone, then runs west down the suite's entry arm to the grille near
    # D-S-SUITEBATH. 6'-10" of 10x8 replaces the old 10'-10" detour across RM-S-SUITEBATH.
    # (This used to carry "an 8"-deep duct on the 14" soffit drop clears it". It does, but
    # that is now `mep.duct_soffit_occupancy`'s answer against SF-S-SUITE's derived cavity,
    # not a number in a comment that nothing re-runs when the FramingSpec changes.)
    # 250 cfm (not 150): feeds two terminals — REG-S-HP-SUITE and REG-A-HP-WEST, a floor
    # boot up through FS-ATTIC directly above. ~450 fpm through 10x8, still quiet.
    DuctRun(uid="CSDH03AAAA", tag="DU-S-HP-SUITE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(14, 1.875)), pt(ft(12, 6), ft(14, 1.875))),
            width=inch(10), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-SUITE", design_cfm=250),
    # The two south rooms' branch (2026-08-16). RM-S-PLANT and RM-S-STUDY2 were the only
    # conditioned rooms on this storey with no drawn terminal, which was always the odd
    # reading: EQ-S-HP1-AH hangs in RM-S-STUDY2's own ceiling.
    #
    # ** ITS RISER IS DRAWN AS OF 2026-08-30, AND THE BRANCH IS NO LONGER AN ORPHAN. ** From
    # 2026-08-16 to 2026-08-30 this run reached (19'-4", 3'-4") in an FS-ATTIC joist bay and
    # DU-S-HP-SUP ended at (19'-4", 9'-7") in SF-S-DUCT, and NOTHING JOINED THEM. The engine
    # cannot catch that — no check validates that a DuctRun endpoint reaches equipment or
    # another run, and `Register.duct_ref` is an unvalidated string — so it stood open in
    # plans/TODO.md instead. The reason it stood open was the packing problem in the hall
    # box, and the packing problem was an artifact of a placeholder air handler that did not
    # exist (plan/electrical.py::EQ-T-GREE-DUC24). With the machine in SF-S-HP1 the riser has
    # a lane and a determinable lower end, and DU-S-HP-SOUTH-RISE below is it.
    #
    # The run KEEPS its path, its bay and its bearing crossing. JOIST_BAY and not CHASE
    # because the alternative — running west along the attic floor — cannot get past
    # W-A-C1/C1B, the x=18' bearing wall RB-HOUSE sits on, which does not open up. Inside the
    # bay the duct passes UNDER that wall's bottom plate; mep.duct_joist_bay reports the
    # bearing-line crossing as a fire-blocking note (R302.11), not a conflict. That note is
    # the regression canary for this whole branch and it requires the run stay filed on the
    # `second` storey.
    #
    # ** 8x6/150 -> 10x6/250, AND EXTENDED EAST TO x=26'-0". ** It picks up RM-A-STUDY's
    # terminal now: DU-A-HP-STUDY is deleted and REG-A-HP-STUDY is a straight floor boot off
    # this run, the same pattern as the retired DU-A-HP-EAST -> REG-A-HP-EAST. That branch was
    # orphaned too (it started at (19'-4", 3'-0") at -8 7/8", inside this bay, connected to
    # nothing), it straddled the joist at y=32" and overlapped THIS duct by 4" — two 8" ducts
    # do not fit one 13 1/2" clear bay, and it escaped mep.duct_joist_bay only by being
    # authored CHASE — and it ran 6'-8" of bare duct across RM-A-STUDY's finished floor to get
    # to a floor register, along a bay it never needed to leave. Deleting it kills all four
    # faults at once; re-baying it would have fixed two and still needed a second riser.
    #
    # 250 cfm is 75 + 75 + 100, taken OUT of the trunk's authored 750 by damper, not added to
    # it: 750 is the air the machine moves, and these three registers redistribute it. 600 fpm
    # at the riser, 420 fpm in the east arm (175 cfm to REG-S-HP-STUDY2 and REG-A-HP-STUDY),
    # 180 fpm in the west arm (75 cfm to REG-S-HP-PLANT). 10" fits the 13 1/2" clear bay with
    # 1 3/4" to spare and 6" fits the 11 7/8" I-joist depth.
    #
    # The riser lands at x=23'-0 1/2", which is 3'-1 1/2" west of REG-S-HP-STUDY2 and east of
    # the room's midpoint — a short arm east to the study and the attic study, a long one west
    # to the plant room. Manual D App. A13 calls a take-off this close to a supply plenum a
    # noise defect; it is mitigated by turning vanes at the riser, a lined plenum and first
    # 5 ft, and a balancing damper, and the 18x8 trunk was chosen partly so the take-off could
    # sit further downstream than a 14x8 would have allowed.
    DuctRun(uid="NYRX7TBEGH", tag="DU-S-HP-SOUTH", system=DuctSystem.SUPPLY,
            path=(pt(ft(26), ft(3, 4)), pt(ft(6, 8), ft(3, 4))),
            width=inch(10), depth=inch(6), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", design_cfm=250),
    # THE RISER — the vertical plans/TODO.md held open, and the last of System 1's three.
    # A repeated plan point at two elevations IS the vertical leg, the idiom
    # DU-S-ERV-HP-FEED's drop already uses; all `DuctRun` ever lacked was somewhere to put
    # the second number, and it has had that since 2026-08-25.
    #
    # It is a separate run from DU-S-HP-SOUTH and not a fourth vertex on it, because the two
    # live in different cavities and are graded by different checks: this leg is in SF-S-HP1
    # under `mep.duct_soffit_occupancy`, the branch is in an FS-ATTIC bay under
    # `mep.duct_joist_bay`, and a run carries one `routing` and one `soffit_ref`.
    #
    # x=23'-0 1/2" is the box's middle lane: 2 1/4" east of the air handler's case and 2 1/2"
    # west of EQ-S-ERV-MIX, both more than the 2" hanger gap. It leaves the supply plenum at
    # y=5'-1" — the plenum is fabricated out to x=23'-5 1/2" to catch this take-off, which is
    # what a plenum is for — runs south past the machine, and stands up at y=3'-4", the
    # FS-ATTIC bay centreline (8" + 2 x 16"), 15" of rise from the soffit cavity into the bay.
    # Every foot of it is south of y=5'-9", so none of it is under ST-S2A.
    #
    # 96 1/8" is a 6"-deep duct on SF-S-HP1's clear underside; 111 1/8" is the same duct's
    # centreline on FS-ATTIC's bottom chord, the elevation DU-S-HP-SOUTH derives for itself
    # from the joists. Both storey-relative to `second`, whose datum is 10'-0 1/8" — the same
    # convention every PipeRun on this storey uses, and the reason those two numbers are not
    # the -8 7/8" the attic-filed runs carry for the same bay.
    DuctRun(uid="27B8FKNDPB", tag="DU-S-HP-SOUTH-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(23, 0.5), ft(5, 1)), pt(ft(23, 0.5), ft(3, 4)),
                  pt(ft(23, 0.5), ft(3, 4))),
            elevations=(inch(96.125), inch(96.125), inch(111.125)),
            width=inch(10), depth=inch(6), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-HP1", design_cfm=250),
    # DU-S-ERV-HP-FEED moved to plan/mep_erv.py (2026-08-25). It kept its tag and its uid
    # and nothing else: it used to tap DU-M1-ERV-SUP at y=12'-8" — a trunk that no longer
    # exists — and its rise into the soffit was undrawn because `DuctRun` had no elevation
    # field. It now comes off the attic sub-manifold, drops into SF-S-DUCT, and lands on the
    # new EQ-S-ERV-MIX mixing box instead of wyeing into the return plenum by comment.
    # DU-S-PLANT-EXH moved to plan/mep_erv.py as DU-A-ERV-R-PLANT (2026-08-25), and moved
    # again on 2026-08-29 to DU-M-ERV-R-PLANT on the LEVEL-2 manifold, running in FS-S-WEST's
    # open-web trusses and rising inside W-S-C1 to a high sidewall grille. Same uid throughout.
    # The second move was not about air at all: the attic route ran the length of the new guest
    # studio's knee wall. It was never System 1's — it is the ERV's stale pull out of
    # RM-S-PLANT. The reasoning that survives the move is in the new run's
    # comment and in notes/plant_room.md: 25 cfm against ~20 of makeup, extract-biased on
    # purpose, and an ERV is damage limitation rather than humidity control.
]

# NO ATTIC BRANCH IS LEFT (2026-08-30). Both of the loft's terminals are straight floor
# boots now — REG-A-HP-EAST off DU-S-HP-SUP and REG-A-HP-STUDY off DU-S-HP-SOUTH — and
# DUCTS_HVAC_ATTIC is empty rather than absent, because "this storey has no horizontal duct"
# is a fact worth stating where the list used to be.
#
# DU-A-HP-STUDY (uid CADH01AAAA) was the last one and it was wrong in four ways at once. It
# started at (19'-4", 3'-0") at -8 7/8" inside the same FS-ATTIC bay DU-S-HP-SOUTH rides and
# **was joined to nothing** — the branch tree it belonged to had no riser at all. Its 8"
# width at y=3'-0" spanned 32"..40", straddling the joist at y=32" and overlapping
# DU-S-HP-SOUTH by 4"; two 8" ducts do not fit one 13 1/2" clear bay, and it escaped
# `mep.duct_joist_bay` only because it was authored `routing=CHASE`, which turns the joist
# check off. Then it rose to +3" and ran 6'-8" east ON RM-A-STUDY's finished floor to a floor
# register — surfacing from the floor, running on top of it and dropping back into it — along
# a bay it never needed to leave, since FS-ATTIC's I-joists span x.
#
# DU-A-HP-EAST went the same way on 2026-07-30 and for the same reason: 6'-8" of run just to
# reach a grille that could sit anywhere in an open room. Re-baying this one would have fixed
# the straddle and the finished floor and left the orphan and a second riser to draw.
DUCTS_HVAC_ATTIC = []

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
