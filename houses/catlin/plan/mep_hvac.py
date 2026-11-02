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
    PortCertainty,
    Service,
    ServicePort,
    SleevePenetration,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# The air terminals' TYPES moved to plan/air_terminal_types.py on 2026-10-31 (one white
# family at submittal sizes: 100 mm disc valves on the ERV, aluminium grilles on System 1),
# with the plant-room extract and the study sidewall that lived here. Instances stay in
# plan/mep_registers.py. Spec and sources: notes/air_distribution_products.md.



# No gas appliance in the house: all-electric (three Gree heat-pump systems + radiant
# floor), and `plan/site.py` authors no GAS UtilityLine. Air-side ports live on
# EQ-T-BROAN-B210E75RT (plan/mep_erv_types.py) and EQ-T-GREE-DUC24 (plan/electrical.py) —
# the two things that push air, neither of which burns anything.
EQUIPMENT_TYPES = (
    # ONE 80-gal hybrid HPWH. Rheem ProTerra PROPH80, EcoNet-enabled: 4.5 kW resistance
    # element, 30A/240V dedicated circuit, single power whip.
    #
    # Compressor-only draw ("Heat Pump"/"Energy Saver" mode) is ~360-500W per the datasheet.
    # ESPHome's esphome-econet component forces Heat-Pump-Only mode ON BATTERY, Hybrid
    # otherwise — a ** BACKUP RESERVE ** behaviour that belongs with CKT-WH-240's
    # `backup_tier=SHED`, not a load-management credit: an unlisted software governor is not
    # a PCS (2026 NEC 130.2) and nothing in the 220.82 calculation reads it. The
    # breaker/panel/NEC 220.82 sizing goes against the nameplate 4.5 kW. See
    # `code.MN_4714_0608_water_heater_relief` for the TPR.
    #
    # Fallback if reverted to a 120V-only plug-in HPWH (~450W, no 240V circuit): swap
    # `type_ref` on EQ-B-WH to a 120V-only EquipmentType, retag `circuit` to a 1-pole 120V
    # circuit at ~450 VA. Nothing else needs to move.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Water heater, Rheem ProTerra 80gal hybrid heat pump (EcoNet)",
                  product_ref="PROD-RHEEM-PROPH80",
                  # Body = 24 1/4" tank (B); height 76 13/16" = K, the top nipples. NOT 91": that
                  # is H, the unit with an 8" duct elbow, and this house does not duct it.
                  footprint=(inch(24.25), inch(24.25)), height=inch(76.8125),
                  # Round tank: a 16-gon, flats on the axes, so a pipe may pass the corners.
                  footprint_shape=Footprint2D(points=(
                      pt(inch(12.125), inch(2.412)), pt(inch(10.279), inch(6.868)),
                      pt(inch(6.868), inch(10.279)), pt(inch(2.412), inch(12.125)),
                      pt(inch(-2.412), inch(12.125)), pt(inch(-6.868), inch(10.279)),
                      pt(inch(-10.279), inch(6.868)), pt(inch(-12.125), inch(2.412)),
                      pt(inch(-12.125), inch(-2.412)), pt(inch(-10.279), inch(-6.868)),
                      pt(inch(-6.868), inch(-10.279)), pt(inch(-2.412), inch(-12.125)),
                      pt(inch(2.412), inch(-12.125)), pt(inch(6.868), inch(-10.279)),
                      pt(inch(10.279), inch(-6.868)), pt(inch(12.125), inch(-2.412)))),
                  plan_symbol="water-heater",
                  source="Rheem PROPH80 T2 RH400-30 / ProTerra XE80T10HS45U0 class: 80 gal, 4.5 kW resistance element, 30A/240V dedicated circuit, ~360-500W compressor draw in Heat Pump Only mode. HA via ESPHome esphome-econet on the RS-485 (RJ11) EcoNet port; the Wi-Fi module is never registered. Mode control on the ProTerra to be tested (notes/smart_home.md).",
                  # Ports off Rheem's RH400-30 sheet and HP-400-SO (letters A-L). Product frame:
                  # -y front, +x right. Nipples at K 76 13/16" (tank top A 74 3/16"); hot 4 1/8"
                  # left/1 1/2" back, cold 4 1/8" right/1 1/2" front, x/y SCALED (+-0.3").
                  # Published: condensate C 59", T&P E 42 3/8". `power` is a face only.
                  # Clearances 0" rear/sides, 6" top; exhaust 6" off a wall when not ducted;
                  # 2" off the T&P side for its release.
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD,
                                     position=(inch(4.125), inch(-1.5), inch(76.8125)),
                                     connection_size=inch(0.75), direction=(0.0, 0.0, 1.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT cold inlet, top nipple (right of axis). Height K published; x/y scaled off the Rheem top-view drawing."),
                         ServicePort(tag="hot", service=Service.WATER_HOT,
                                     position=(inch(-4.125), inch(1.5), inch(76.8125)),
                                     connection_size=inch(0.75), direction=(0.0, 0.0, 1.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT hot outlet, top nipple (left of axis). Height K published; x/y scaled off the Rheem top-view drawing."),
                         ServicePort(tag="condensate", service=Service.DRAIN,
                                     position=(inch(-7.5), inch(-11), inch(59)),
                                     connection_size=inch(0.75), direction=(0.0, -1.0, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT female primary condensate, front-left shoulder. Height C = 59in published; x/y scaled off the drawing."),
                         ServicePort(tag="relief", service=Service.DRAIN,
                                     position=(inch(-14.125), ft(0), inch(42.375)),
                                     connection_size=inch(0.75), direction=(-1.0, 0.0, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="Factory T&P valve, product-left side. Height E = 42 3/8in published; 2in off the 24 1/4in body is where the valve outlet is drawn."),
                         ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0)))),
                  clearances=(
                      ClearanceZone(
                          footprint=Footprint2D(points=(
                              pt(inch(12.125), inch(-6)), pt(inch(18.125), inch(-6)),
                              pt(inch(18.125), inch(12)), pt(inch(12.125), inch(12)))),
                          purpose="air exhaust 6in off any wall or hard surface when not ducted",
                          policy=ClearancePolicy.RECOMMENDED,
                          source="Rheem RH400-30 spec sheet, non-ducted note"),)),
    # --- the backup microgrid (notes/backup_power.md) ----------------------------------
    #
    # EG4 12kPV: name is the PV input, not the output. 12,000 W array in, 8,000 W AC out
    # continuous — the number the autonomy calc and CKT-ESS-GRID breaker use. Surge is the
    # datasheet's 16 kW/0.5 s (12 kW/1 s, 10 kW/1 min) — 0.5 s is what a compressor start asks.
    # UL 9540 belongs to the battery, not here — marking the inverter would pass R327.2's
    # check on the strength of the wrong product.
    # Idle/efficiency: the sheet's "<55 W standby" and 94% MAX — meter at commissioning.
    EquipmentType(tag="EQ-T-EG4-12KPV", name="EG4 12kPV hybrid inverter",
                  product_ref="PROD-EG4-12KPV",
                  footprint=(inch(27), inch(12)), height=inch(35),
                  inverter_kw_continuous=8.0, inverter_kw_surge=16.0, pv_input_kw=12.0,
                  inverter_idle_w=55.0, inverter_efficiency=0.94,
                  ports=(ServicePort(tag="grid", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="load", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),),
                  source="EG4 12kPV spec sheet v1.0.9 (eg4electronics.com, read 2026-10-31): 8,000 W continuous AC output (120/240V split phase), 12,000 W PV input over 2 MPPTs at 600 VDC max, 16 kW/0.5 s surge, idle consumption (standby) <55 W, battery-to-grid max efficiency 94%, UL 1741 SA/SB."),
    # EG4 WallMount Indoor, 14.3 kWh; `advisory.ess_capacity`'s 40 kWh (2021 R328.5) caps a
    # third. `ul_9540_listed` is declared, never inferred. The owner's 3'-0" zone is still
    # drawn off the old 24x10 body, so the 18.1" cabinet gets 39" at its sides.
    # Any later pack: on EG4's UL 9540 list for the 12kPV (or a 3rd-ed. DC ESS listing the
    # AHJ accepts in writing), closed-loop CAN, own BMS contactor, a UL 9540A report.
    EquipmentType(tag="EQ-T-ESS-BATT", name="EG4 WallMount Indoor 280Ah, 14.3 kWh",
                  product_ref="PROD-EG4-POWERPRO-WM",
                  footprint=(inch(18.125), inch(9.625)), height=inch(36.375),
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
                  source="EG4 WallMount Indoor 280Ah product page (read 2026-10-31): 14.3 kWh LFP, 36.4 x 18.1 x 9.6 in (H x W x D), 282 lb, UL 1973 + UL 9540A; UL 9540 as a system with the 12kPV/18kPV/FlexBOSS21; closed-loop RS485 comms. Capacity is nameplate; the autonomy calc applies its own depth of discharge (takeoff/backup_calc.py)."),
)

# --- Ventilation: ERV fresh-air / stale-air trunks ------------------------------------
#
# The ERV install is home-run radial — one 4" galvanized run per terminal off five
# plenums, plus a real outdoor side, plus four drawn vertical runs — and all of it lives in
# **plan/mep_erv_l1.py** and its per-cavity siblings (l2, l3, outdoor, risers). The four lists below stay empty rather than being deleted, so
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
    # south, sheds 3 x 80 (plan/mep_hvac_branches.py) + 50 + 175 + 35 along the way, and hands
    # the last 250 to DU-S-HP-SOUTH-RISE at the cap. Tapered by intent, one section by build.
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
    # it names. (DU-S-HP-SUITE used the same idiom where SF-S-SUITE abutted; that box was
    # retired 2026-09-13 and the branch is EXPOSED now, so this trunk is the only user left.)
    #
    # It ends at y=9'-10", where DU-S-HP-SOUTH-RISE picks it up COLLINEARLY at the cap.
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(30, 4.5)), pt(ft(19, 6), ft(9, 10))),
            width=inch(18), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=750, material="galvanized"),
    # THE RETURN — a real one, up the east lane of SF-S-HP1. The old system had no return
    # duct worth the name: the machine breathed through RM-S-STUDY2's cased opening off a
    # 6" stub.
    #
    # ** IT STARTS INSIDE THE PLENUM, NOT AT A GRILLE. ** REG-S-HP-RET opens into
    # EQ-S-ERV-MIX's underside and the ERV's fresh feed drops into the same box; this run is
    # what leaves it. It begins at (21'-0", 29'-7"), inside the plenum's y 27'-11"..30'-4",
    # runs north up the east lane past the cabinet, then west across the box's north end onto
    # the cabinet's return face at (19'-6", 34'-0"). `_pair_is_plumbed` excuses the
    # plenum<->duct overlap at the start — `mep.duct_connectivity` earns that, it is not a
    # tolerance.
    #
    # 10 (x) x 18 (depth): 180 in2 at 750 cfm is 600 fpm, a return velocity. The 10" is what
    # the box's 36.50" clear width can spare beside the 21 1/4" cabinet and a 2 3/8" hanger
    # gap; the 18" goes into the 20.25" cavity, which is why there is no `elevations` here —
    # the run derives the cavity floor for itself. ** If `mep.duct_soffit_occupancy` ever
    # objects to 18" in the cavity, the fallback is 10x16 at 675 fpm. ** Let the check
    # decide; never hand-author a clear width.
    #
    # THE CAVITY WAS 18.25" until 2026-09-18, when the box went to a 23" drop to make room
    # for the air handler's emergency drain pan. This run derives the floor, so it simply
    # moved down with it — but the 2" the pan takes is the machine's AND this duct's: set on
    # the pan, the cabinet reads 2 + 18 1/8 = 20 1/8 and this return 2 + 18 = 20, both
    # inside 20.25. That is what the deepening was sized to, and it is why 18" survived.
    #
    # It carries the full 750: 650 of room air off the grille plus the ERV's 100, mixed in
    # the plenum behind it. Everything here is upstream of the coil and therefore upstream of
    # EQ-S-HP1-STRIP, which sits SOUTH of the cabinet in the discharge.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(ft(21), ft(29, 7)), pt(ft(21), ft(34, 8)),
                  pt(ft(19, 6), ft(34, 8)), pt(ft(19, 6), ft(34))),
            width=inch(10), depth=inch(18), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-HP1", design_cfm=750, material="galvanized"),
    # West branch to RM-S-SUITE: tees off DU-S-HP-SUP at y=14'-8 7/8", 7" north of
    # D-S-SUITE's centreline, and crosses W-S-C2B above the door in the CLEAR bay between
    # its header cripples (2026-10-31: on the door centre the 10x8 ran through the middle
    # cripple, which `mep.terminal_neck_fit` found), ending at the loft boot 28" west. REG-S-HP-SUITE is a high sidewall
    # grille on W-S-C2B's suite face; REG-A-HP-WEST is the floor boot at the duct end in
    # RM-A-STUDIO. 175 cfm feeds both: 100 to the suite and 75 to the loft.
    # 315 fpm through 10x8, quiet.
    #
    # ** EXPOSED SINCE 2026-09-13, AND THE ELEVATION IS AUTHORED BECAUSE OF IT. ** SF-S-SUITE
    # boxed this branch out of the entry arm and is retired; RM-S-SUITE declares its ceiling
    # open instead. Dropping `soffit_ref` also drops the cavity that DERIVED this run's z —
    # `_derived_base_z` would fall back to the storey datum and lay a supply duct on the
    # floor — so the centreline is authored at the height the box had already given it:
    # 100 1/8" storey-relative, which is DU-S-HP-SUP's own centreline inside SF-S-DUCT.
    # ** THAT IS THE CEILING ON IT, NOT A PREFERENCE. ** A branch cannot tee above the trunk
    # it comes off, so 216 1/8"..224 1/8" absolute is where this duct can be, exposed or not.
    # Underside 8'-0 1/8" over the arm floor, against the 6'-8" headroom line the declaration
    # does not retire.
    DuctRun(uid="CSDH03AAAA", tag="DU-S-HP-SUITE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 4), ft(14, 8.875)), pt(ft(17), ft(14, 8.875))),
            width=inch(10), depth=inch(8), routing=DuctRouting.EXPOSED,
            start_elevation=inch(100.125), end_elevation=inch(100.125), design_cfm=175, material="galvanized"),
    # The plant room and attic study share FS-ATTIC's y=3'-3" I-joist bay.
    # RM-S-STUDY2 takes 75 cfm from the soffit leg below before it rises; this
    # bay run carries the remaining 175 cfm west across the x=18' bearing line.
    #
    # JOIST_BAY and not CHASE because the alternative — running west along the attic floor —
    # cannot get past W-A-C1/C1B, the x=18' bearing wall RB-HOUSE sits on, which does not
    # open up. Inside the bay the duct passes UNDER that wall's bottom plate;
    # mep.duct_joist_bay reports the bearing-line crossing as a fire-blocking note
    # (R302.11), not a conflict. That note is the regression canary for this whole branch
    # and it requires the run stay filed on the `second` storey.
    #
    # 10x6/175 cfm: REG-A-HP-STUDY is a straight floor boot at x=18'-10".
    # The riser still receives 250 cfm (75 + 75 + 100); after the 75 cfm sidewall
    # take-off, 175 rises into this bay. 420 fpm before the attic boot, then 180 fpm
    # to REG-S-HP-PLANT. The section remains 10x6 to match the riser and fits the
    # 13 1/2" clear bay and 11 7/8" I-joist depth.
    #
    # The riser lands at x=19'-6"; the entire bay run now travels west from there.
    # Manual D App. A13 calls a take-off this close to a supply plenum a noise defect; it is
    # mitigated by turning vanes at the riser, a lined plenum and first 5 ft, and a balancing
    # damper, and the 18x8 trunk was chosen partly so the take-off could sit further
    # downstream than a 14x8 would have allowed.
    #
    # Rise only west of the x=18' bearing line; final elevation follows the terminal's
    # resolved ceiling face and inlet. The boot begins at x=15'-2", grille at 14'-8".
    # The attic study still takes 100 cfm from this branch before its 75 cfm plant tail.
    DuctRun(uid="NYRX7TBEGH", tag="DU-S-HP-SOUTH", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(3, 3)), pt(ft(17, 6), ft(3, 3)),
                  pt(ft(15, 2), ft(3, 3))),
            width=inch(10), depth=inch(6), routing=DuctRouting.JOIST_BAY,
            end_terminal_ref="REG-S-HP-PLANT",
            floor_ref="FS-ATTIC", design_cfm=175, material="galvanized"),
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
    # ** WHY IT TRAVELS SOUTH BELOW THE JOISTS INSTEAD OF RISING AT THE CAP. ** The obvious
    # saving is to stand this branch up at the trunk cap and let the attic side do the
    # north-south travel — which would also let SF-S-DUCT stop at y=9'-10" and give
    # RM-S-STUDY2 back the 7 ft of 14"-deep box that lowers its ceiling to 7'-10". It does not
    # work, and the reason is the hole chart, not the duct size:
    #
    #  * FS-ATTIC's joists run in **x** (11 7/8" I-joist, 16" o.c.), so ANY north-south run in
    #    that floor crosses them. DU-S-HP-SOUTH avoids this by living in ONE bay for its whole
    #    length; a riser at the cap would have to cross ~5 joists to reach that bay.
    #  * Those crossings would land at x=19'-6" — 15 1/4" from the face of W-S-C1, the x=18'
    #    bearing wall the east span starts on. That is inside every published no-hole zone;
    #    the chart's permissive band is mid-span, out at x~27'.
    #  * And "a small enough duct" does not buy it back. 250 cfm wants ~51 in2 to stay under
    #    Manual D's 700 fpm branch ceiling, i.e. 8" round — a hole this depth of I-joist only
    #    allows near mid-span. The largest hole the chart would entertain 15" off a bearing is
    #    about 6 1/2" round: 33 in2, 1,090 fpm, half again over the ceiling and audible in a
    #    bedroom hallway.
    #
    # So the soffit leg is not laziness — it is the only way to travel 6'-6" in y under a
    # floor whose joists run in x. The 7 ft of box in the study is what that costs.
    #
    # 99 1/8" is a 6"-deep duct on SF-S-DUCT's clear underside (the box's 14" drop, not
    # SF-S-HP1's 21"); 111 1/8" is the same duct's centreline on FS-ATTIC's bottom chord,
    # the elevation DU-S-HP-SOUTH derives for itself from the joists. Both storey-relative
    # to `second`, whose datum is 10'-0" — the same convention every PipeRun here uses.
    DuctRun(uid="27B8FKNDPB", tag="DU-S-HP-SOUTH-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(9, 10)), pt(ft(19, 6), ft(3, 3)),
                  pt(ft(19, 6), ft(3, 3))),
            elevations=(inch(99.125), inch(99.125), inch(111.125)),
            width=inch(10), depth=inch(6), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=250, material="galvanized"),
    # DU-S-ERV-HP-FEED is in plan/mep_erv_l3.py: it comes off the attic sub-manifold and
    # drops straight onto EQ-S-ERV-MIX in SF-S-HP1; it never enters SF-S-DUCT. DU-S-PLANT-EXH is DU-M-ERV-R-PLANT there,
    # on the LEVEL-2 manifold, running in FS-S-WEST's open-web trusses and rising inside
    # W-S-C1 to a high sidewall grille — it is not System 1's, it is the ERV's stale pull
    # out of RM-S-PLANT: 25 cfm against ~20 of makeup, extract-biased on purpose, and an ERV
    # is damage limitation rather than humidity control (notes/plant_room.md).
]

# Both of the loft's terminals are straight floor boots — REG-A-HP-EAST off DU-S-HP-SUP and
# REG-A-HP-STUDY off DU-S-HP-SOUTH. DUCTS_HVAC_ATTIC is empty rather than absent, because
# "this storey has no horizontal duct" is a fact worth stating where the list would be.
DUCTS_HVAC_ATTIC = []

# The tank sits against W-B-STR3 at (8'-9", 29'-5"), flush to its resolved east interior face,
# in the slot between the hung ERV case (west), W-B-ESS-S (north) and D-B-CLOSET's swing
# (south, y <= 339"). Clear of EQ-B-ESS-BATT's 36" zone, the dry-fire lane and the 36"
# NEC 110.26 working spaces along the west wall.
#
# ** ROTATED -90 SO THE AIR EXHAUST FACES THE ROOM (owner, 2026-10-29). ** Product right
# (exhaust) is SOUTH: its 6" zone (x 99..117", y 334 7/8..340 7/8") is open floor, with only
# D-B-CLOSET's leaf in it while it stands open (PR-B-ERV-COND left it on 2026-10-29).
# Back is EAST on the wall (0" allowed). Left (T&P, 42 3/8") is NORTH, 4 1/2" body-to-wall: 1"
# south from 29'-6" buys that; the leaf's swing (y <= 339") would allow 1 7/8" more.
# PR-B-ERV-COND runs through that gap at 52", 9" over the valve (plan/mep_drainage.py).
# Front (display, condensate) is WEST, beside the ERV case: the display is read through
# EcoNet, the lower panels from under the case (it hangs at 54"; it moved 3/16" west to open
# the slot to 24.28"). mep_supply.py, mep_supply_devices.py and mep_drainage.py quote the rotated ports.
EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(ft(8, 9), ft(29, 5)), rotation=deg(-90),
             footprint=(inch(24.25), inch(24.25)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH-240",
             relief_discharge_ref="PR-B-WH-TPR"),
]
