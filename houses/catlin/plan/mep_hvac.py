# haus: editable
# Catlin MEP — air distribution — the ERV trunks, System 1's conditioned-air chase, equipment.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
#
# The second-floor ERV trunks run in the second floor's joist bays, split at x=18'
# (FS-S-WEST: 11.875" floor truss; FS-S-EAST: 11.875" I-joist, same depth, both 16" o.c.,
# direction "x"). Each trunk's `floor_ref` names FS-S-WEST since every trunk starts at
# x=4' — the resolver validates each segment against whichever half its midpoint falls in,
# so the crossing at x=18' still resolves. Bay centers are `8" + n*16"` from the joist-line
# math in resolve/floors.py; bay 15 (y=20'-8") and bay 17 (y=23'-4") are both clear of the
# stair FloorOpening (x:11'-18', y:25'-36') and both cross the central bearing wall at
# x=18'. The terminals on these trunks are in plan/mep_registers.py.

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
    # REG-T-ERV-EXH-WALL below is the house's only wall-oriented ERV terminal type:
    # `footprint` is a PLAN rectangle, so a ceiling grille authors (face, face) with
    # `height` as its 1" thickness and a wall grille authors (face, DEPTH) with `height` as
    # the face. Mount a ceiling type on a wall and 3" of it draws inside the studs.
    RegisterType(tag="REG-T-ERV-EXH", name="ERV stale-air extract diffuser, 6\" round",
                 footprint=(inch(7), inch(7)), height=inch(1),
                 plan_symbol="register", ventilation_terminal=True,
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    # A CEILING diffuser lies in the plane it is cut into (7x7 face, 1" deep); mounting that
    # type on a WALL tells the resolver the body reaches 7" off the wall into the room.
    # ``_body_profile`` measures a wall mount's projection as the local y extent of its
    # footprint, so REG-A-STUBATH-EXH — the house's one wall-hung extract — read as a 7"
    # protrusion, past A117.1 §307.2's 4", obstructing FX-A-STUBATH-WC's required clear
    # space. A sidewall grille is a 7" face 1" deep, which is what this type says.
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
    # The plant room's pair (notes/plant_room.md). The room is held at ~75 F / 70% RH
    # year-round, which makes its ventilation a pressure question before it is an air
    # question: natatorium practice holds such a room 0.05-0.15 in. w.g. NEGATIVE to the
    # spaces around it, so house air leaks in (harmless) and room air never leaks into a
    # stud bay (the failure this whole room is built to prevent).
    #
    # A dedicated, dampered branch off EQ-B-ERV rather than a separate machine — the house
    # already owns a proper ERV with a condensate drain and real frost control, and
    # "separate from the house ERV" is best had with an independent DAMPER, not an
    # independent unit.
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
    # REG-T-HP-RET is a 25x20 filter-back grille. 480 in2 gross at 750 cfm is 225 fpm face
    # velocity — under Manual D SS4-10's 350 fpm for a plain return grille and its 300 fpm
    # for one carrying the filter, which this one does: with the machine hung in SF-S-HP1
    # there is no filter cabinet anywhere else in the system, and the grille is the only
    # serviceable face a person can reach.
    #
    # 30 x 16 nominal, and since the 2026-09-04 reversal the INSTANCE turns it 90 degrees
    # (plan/mep_registers.py): SF-S-HP1 is 36.50" clear ACROSS x now, so the 30" runs along
    # the box in y and only the 16" crosses it. Turned, the grille sits wholly in RM-S-HALL
    # — IMC 601.5(7), no return air out of a closet — with 4 5/8" to spare.
    # A ceiling access panel under the cabinet is modelled now (FURN-S-NCLOSET-AP); the
    # filter itself still lives behind this grille and nowhere else in the model.
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

# No gas appliance in the house: all-electric (three Gree heat-pump systems + radiant
# floor), and `plan/site.py` authors no GAS UtilityLine. Air-side ports live on
# EQ-T-BROAN-B210E75RT (plan/mep_erv_types.py) and EQ-T-GREE-DUC24 (plan/electrical.py) —
# the two things that push air, neither of which burns anything.
EQUIPMENT_TYPES = (
    # ONE 80-gal hybrid HPWH. Rheem ProTerra PROPH80, EcoNet-enabled: 4.5 kW resistance
    # element, 30A/240V dedicated circuit, single power whip.
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
    # --- the backup microgrid (notes/backup_power.md) ----------------------------------
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

# --- Ventilation: ERV fresh-air / stale-air trunks ------------------------------------
#
# The ERV install is semi-rigid radial — one 75 mm run per terminal off three
# sub-manifolds, plus a real outdoor side, plus four drawn risers — and all of it lives in
# **plan/mep_erv.py**. The four lists below stay empty rather than being deleted, so
# plan/mep.py's per-storey assembly (and therefore element order in model.json) is
# untouched.
DUCTS = []

DUCTS_MAIN = []

DUCTS_BASEMENT = []

DUCTS_ATTIC = []

# --- System 1: the conditioned-air chase (plans/TODO.md §HVAC) -----------------------
# EQ-S-HP1-AH (plan/electrical.py) hangs INSIDE SF-S-HP1 at the NORTH end of the chase
# (y 30'-4 1/2"..34'-0", over RM-S-NCLOSET) and feeds ONE straight supply trunk running
# SOUTH down the second-floor hallway inside SF-S-DUCT. The return comes back up the east
# lane of SF-S-HP1 from a proper central-hall grille, and the ERV's fresh feed is wyed into
# EQ-S-ERV-MIX at the return's far (south) end. The whole system reversed on 2026-09-04
# when the machine moved out of RM-S-STUDY2's ceiling.
#
# SOFFIT routing + `soffit_ref`: naming the modeled Soffit puts these runs under
# `mep.duct_soffit_occupancy`, which derives the box's clear section from its own drop,
# framing member and lining and measures every occupant against it side by side. It also
# gives them their elevation for free: a run that names a soffit and authors no elevation
# sits on the box's clear underside. CHASE keeps its honest meaning for a framed shaft that
# is not modeled as a Soffit. The two crossings of the x=18' bearing line are legal either way.
# Hall is x 18'-2 3/4"..21'-8" clear; the trunk runs at x=19'-6".
DUCTS_HVAC_SECOND = [
    # ** THE TRUNK CARRIES THE WHOLE 750 NOW, AND THAT IS THE POINT OF THE REVERSAL. **
    # It used to leave the machine as a 500 north / 250 east split at the discharge. With
    # the machine at the north end there is one discharge and one direction: 750 cfm goes
    # south, sheds 80 + 80 + 80 + 50 + 175 + 35 along the way, and hands the last 250 to
    # DU-S-HP-SOUTH-RISE at the cap. Tapered by intent, one section by construction.
    #
    # 750 cfm through 14x8 is 965 fpm, above Manual D's 900 fpm ceiling for a trunk in a
    # finished space; 18x8 is 750 fpm. 18" and not 20" because SF-S-DUCT's 30 3/4" clear
    # has to carry the ERV mixing-box riser past the trunk as well.
    #
    # x=19'-6": the west face lands 3/8" inside the cavity and the east face keeps the full
    # 2" off the ERV riser. REG-A-HP-EAST at (19'-4", 11'-4") is still squarely over the
    # trunk (x 18'-9"..20'-3"), so its floor boot still rises straight.
    #
    # It begins ON the air handler's discharge face at (19'-6", 30'-4 1/2") inside SF-S-HP1
    # and crosses the y=27'-8" seam into SF-S-DUCT. `soffit_ref` names the hall box because
    # that is where the great majority of it runs; the check clips a run's extent to the box
    # it names, which is the same idiom DU-S-HP-SUITE uses where SF-S-SUITE abuts.
    #
    # It ends at y=9'-10", where DU-S-HP-SOUTH-RISE picks it up COLLINEARLY at the cap.
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(30, 4.5)), pt(ft(19, 6), ft(9, 10))),
            width=inch(18), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=750),
    # THE RETURN — a real one, up the east lane of SF-S-HP1. The old system had no return
    # duct worth the name: the machine breathed through RM-S-STUDY2's cased opening off a
    # 6" stub. Now REG-S-HP-RET is a central-hall grille at (20'-9", 29'-0") and this run
    # carries it north up the box's east lane, then west across the box's north end onto the
    # cabinet's return face at (19'-6", 34'-0").
    #
    # 10 (x) x 18 (depth): 180 in2 at 750 cfm is 600 fpm, a return velocity. The 10" is what
    # the box's 36.50" clear width can spare beside the 21 1/4" cabinet and a 2 3/8" hanger
    # gap; the 18" goes into the 18.25" cavity, which is why there is no `elevations` here —
    # the run derives the cavity floor for itself. ** If `mep.duct_soffit_occupancy` ever
    # objects to 18" in an 18 1/4" cavity, the fallback is 10x16 at 675 fpm. ** Let the
    # check decide; never hand-author a clear width.
    #
    # EQ-S-ERV-MIX sits at this run's START, at the south end, so the ERV's fresh air mixes
    # across the whole 6'-7" of return before the coil — and still upstream of
    # EQ-S-HP1-STRIP, which is now south of the cabinet in the discharge. The mixing box is
    # on the return and not on the trunk because `_pair_is_plumbed` excuses only
    # equipment<->duct pairs: a duct riser landing on another duct is always a clash.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(ft(21), ft(28, 3)), pt(ft(21), ft(34, 8)),
                  pt(ft(19, 6), ft(34, 8)), pt(ft(19, 6), ft(34))),
            width=inch(10), depth=inch(18), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-HP1", design_cfm=750),
    # West branch to RM-S-SUITE: tees off DU-S-HP-SUP at D-S-SUITE's centreline
    # (y=14'-1 7/8"), crosses W-S-C2B above the door through the header/top-plate cripple
    # zone, then runs west down the suite's entry arm to the grille near D-S-SUITEBATH.
    # 175 cfm feeds two terminals — REG-S-HP-SUITE (100) and REG-A-HP-WEST (75), a floor
    # boot up through FS-ATTIC directly above. 315 fpm through 10x8, quiet.
    DuctRun(uid="CSDH03AAAA", tag="DU-S-HP-SUITE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(14, 1.875)), pt(ft(12, 6), ft(14, 1.875))),
            width=inch(10), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-SUITE", design_cfm=175),
    # The two south rooms' branch: RM-S-PLANT and RM-S-STUDY2 are fed off DU-S-HP-SOUTH,
    # which reaches them from FS-ATTIC's I-joist bay at y=3'-4". The soffit stops at
    # y=2'-10" and neither room is under it; the bay is how the air crosses the x=18'
    # bearing line into the west half of the storey.
    #
    # JOIST_BAY and not CHASE because the alternative — running west along the attic floor —
    # cannot get past W-A-C1/C1B, the x=18' bearing wall RB-HOUSE sits on, which does not
    # open up. Inside the bay the duct passes UNDER that wall's bottom plate;
    # mep.duct_joist_bay reports the bearing-line crossing as a fire-blocking note
    # (R302.11), not a conflict. That note is the regression canary for this whole branch
    # and it requires the run stay filed on the `second` storey.
    #
    # 10x6/250 cfm: it also picks up RM-A-STUDY's terminal — REG-A-HP-STUDY is a straight
    # floor boot off this run, extended east to x=26'-0". 250 cfm is 75 + 75 + 100, taken
    # OUT of the trunk's authored 750 by damper, not added to it. 600 fpm at the riser,
    # 420 fpm in the east arm (175 cfm to REG-S-HP-STUDY2 and REG-A-HP-STUDY), 180 fpm in
    # the west arm (75 cfm to REG-S-HP-PLANT). 10" fits the 13 1/2" clear bay with 1 3/4"
    # to spare and 6" fits the 11 7/8" I-joist depth.
    #
    # The riser lands at x=23'-0 1/2", 3'-1 1/2" west of REG-S-HP-STUDY2 and east of the
    # room's midpoint — a short arm east to the study and the attic study, a long one west
    # to the plant room. Manual D App. A13 calls a take-off this close to a supply plenum a
    # noise defect; it is mitigated by turning vanes at the riser, a lined plenum and first
    # 5 ft, and a balancing damper, and the 18x8 trunk was chosen partly so the take-off
    # could sit further downstream than a 14x8 would have allowed.
    DuctRun(uid="NYRX7TBEGH", tag="DU-S-HP-SOUTH", system=DuctSystem.SUPPLY,
            path=(pt(ft(26), ft(3, 4)), pt(ft(6, 8), ft(3, 4))),
            width=inch(10), depth=inch(6), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", design_cfm=250),
    # THE RISER — a repeated plan point at two elevations is the vertical leg, the idiom
    # DU-S-ERV-HP-FEED's drop already uses.
    #
    # It is a separate run from DU-S-HP-SOUTH and not a fourth vertex on it, because the two
    # live in different cavities and are graded by different checks: this leg is in
    # SF-S-DUCT under `mep.duct_soffit_occupancy`, the branch is in an FS-ATTIC bay under
    # `mep.duct_joist_bay`, and a run carries one `routing` and one `soffit_ref`.
    #
    # ** IT IS A COLLINEAR REDUCER AT THE TRUNK CAP NOW. ** It used to dogleg east from the
    # discharge to x=23'-0 1/2" and that jog existed for exactly one reason: to get around
    # the machine, which stood in its way. With the machine at the north end the riser just
    # continues the trunk's own centreline at x=19'-6" from y=9'-10" to y=3'-4" and stands
    # up — 18x8 down to 10x6 at the cap, two elbows fewer, and nothing to clash with.
    # (The east-lane alternative also fits — 18 + 2 + 10 = 30 against SF-S-DUCT's 30 3/4" —
    # but a jog would overlap the trunk ALONG the box and report. Kept here as the
    # documented fallback if the cap ever has to move.)
    #
    # 99 1/8" is a 6"-deep duct on SF-S-DUCT's clear underside (the box's 14" drop, not
    # SF-S-HP1's 21"); 111 1/8" is the same duct's centreline on FS-ATTIC's bottom chord,
    # the elevation DU-S-HP-SOUTH derives for itself from the joists. Both storey-relative
    # to `second`, whose datum is 10'-0 1/8" — the same convention every PipeRun here uses.
    DuctRun(uid="27B8FKNDPB", tag="DU-S-HP-SOUTH-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(9, 10)), pt(ft(19, 6), ft(3, 4)),
                  pt(ft(19, 6), ft(3, 4))),
            elevations=(inch(99.125), inch(99.125), inch(111.125)),
            width=inch(10), depth=inch(6), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=250),
    # DU-S-ERV-HP-FEED is in plan/mep_erv.py: it comes off the attic sub-manifold, drops
    # into SF-S-DUCT, and lands on EQ-S-ERV-MIX. DU-S-PLANT-EXH is DU-M-ERV-R-PLANT there,
    # on the LEVEL-2 manifold, running in FS-S-WEST's open-web trusses and rising inside
    # W-S-C1 to a high sidewall grille — it is not System 1's, it is the ERV's stale pull
    # out of RM-S-PLANT: 25 cfm against ~20 of makeup, extract-biased on purpose, and an ERV
    # is damage limitation rather than humidity control (notes/plant_room.md).
]

# Both of the loft's terminals are straight floor boots — REG-A-HP-EAST off DU-S-HP-SUP and
# REG-A-HP-STUDY off DU-S-HP-SOUTH. DUCTS_HVAC_ATTIC is empty rather than absent, because
# "this storey has no horizontal duct" is a fact worth stating where the list would be.
DUCTS_HVAC_ATTIC = []

# The tank sits at (5'-6", 24'-0"), which frees the furnace room's NE corner for the ESS
# closet (plan/storeys/basement.py). It is not a preference: EQ-B-ESS-BATT declares a
# REQUIRED 48" x 41" separation zone all round (EQ-T-ESS-BATT, above),
# `advisory.ess_clearance` grades it with no room-or-wall exemption. With the room only 10'
# wide there is no room to buy the 48" in x — every foot west of x=3'-11" is the 36" NEC
# 110.26 working space in front of ED-B-PANEL, ED-B-BACKUP-PANEL, ED-B-BACKUP-ENCL and
# ED-B-NET-PATCH — so the 41" had to come out of y, south.
#
# (5'-6", 24'-0") is what is left once the room's other fixed points are honoured: north of
# D-B-FURN's leaf (which sweeps to y=20'-8"), west of EQ-B-ESS-INV (x=7'-0 5/16"), south of
# EQ-B-ERV (y=28'-1 5/8"), and starting at x=4'-6" so the panel wall's working space stays
# clear. It also SHORTENS the plumbing: all three runs below leave the tank heading south,
# and PR-B-CW-WH arrives straight up its own x=5'-6" line instead of doglegging.
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
