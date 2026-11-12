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
# x=18'. The terminals on these trunks are in plan/mep_registers_*.py.

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
    Mount,
    MountKind,
    PortCertainty,
    Service,
    ServicePort,
    SleevePenetration,
    Slab,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import ModelRepresentation, m

# The air terminals' TYPES moved to plan/air_terminal_types.py on 2026-10-31 (one white
# family at submittal sizes: 100 mm disc valves on the ERV, aluminium grilles on System 1),
# with the plant-room extract and the study sidewall that lived here. Instances stay in
# plan/mep_registers_*.py. Spec and sources: notes/air_distribution_products.md.



# No gas appliance in the house: all-electric (three Gree heat-pump systems + radiant
# floor), and `plan/site.py` authors no GAS UtilityLine. Air-side ports live on
# EQ-T-BROAN-B210E75RT (plan/mep_erv_types.py) and EQ-T-GREE-DUC24 (plan/electrical.py) —
# the two things that push air, neither of which burns anything.
EQUIPMENT_TYPES = (
    # ONE 80-gal HPWH: the Rheem ProTerra Plug-in with HydroBoost, PROPH80 T0 RH120-M (owner,
    # 2026-10-31). 120 V, 395 W average, NO ELEMENT: the 240 V ProTerra falls back to its
    # 4.5 kW element on a compressor, airflow, condensate or sensor fault in any mode, so no
    # automation could promise "compressor only" on battery. This one's wiring diagram lists
    # no element (Use & Care, component codes). Its alarm table still says "heating source
    # defaults to elements", which reads as carried over from the 240 V manual: confirm with
    # Rheem. The cost is recovery: 12 GPH and no element boost; FHR 84 gal is the HydroBoost
    # mixing valve at a 132 F tank. CKT-WH, 1-pole, surplus tier. See
    # `code.MN_4714_0608_water_heater_relief` for the TPR.
    #
    # GEOMETRY: Rheem RH-PIHP-SC-SO Rev. 7 (03/25) p.2, PROPH80 T0 RH120-MSO, letters in the
    # comments below; notes/water_service.md §1. Plug-in: SIDE connections on the factory
    # HydroBoost riser at the product's front-right, no top nipples.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Water heater, Rheem ProTerra Plug-in HydroBoost 80 gal heat pump, 120 V",
                  product_ref="PROD-RHEEM-PROPH80",
                  # Height = A 74 3/16", the tank top with its filter grille. H 91" is the
                  # ducted inlet elbow (plan/mep_hpwh_air.py); the filter wants 6" over the top.
                  footprint=(inch(24.25), inch(24.25)), height=inch(74.1875),
                  # Tank (B 24 1/4"): a 16-gon, flats on the axes. The lobe at front-right is
                  # the riser cover, 40-75 deg right of front at r 15" (SCALED); it stops at
                  # G 54 5/16" but is drawn full height.
                  footprint_shape=Footprint2D(points=(
                      pt(inch(12.125), inch(2.412)), pt(inch(10.279), inch(6.868)),
                      pt(inch(6.868), inch(10.279)), pt(inch(2.412), inch(12.125)),
                      pt(inch(-2.412), inch(12.125)), pt(inch(-6.868), inch(10.279)),
                      pt(inch(-10.279), inch(6.868)), pt(inch(-12.125), inch(2.412)),
                      pt(inch(-12.125), inch(-2.412)), pt(inch(-10.279), inch(-6.868)),
                      pt(inch(-6.868), inch(-10.279)), pt(inch(-2.412), inch(-12.125)),
                      pt(inch(2.412), inch(-12.125)), pt(inch(6.868), inch(-10.279)),
                      pt(inch(7.824), inch(-9.324)), pt(inch(9.642), inch(-11.491)),
                      pt(inch(12.287), inch(-8.604)), pt(inch(14.489), inch(-3.882)),
                      pt(inch(11.813), inch(-3.165)), pt(inch(12.125), inch(-2.412)))),
                  plan_symbol="water-heater",
                  model_representation=ModelRepresentation(symbol="rheem-proterra-plugin-80"),
                  source="Rheem spec sheet RH-PIHP-SC-NO-SO-SS Rev. 1 (04/26), PROPH80 T0 RH120-M: 80 gal (72 rated), 15 A minimum breaker, 395 W average, UEF 3.46, 4,200 Btu/h compressor, FHR 84 gal at a 132 F tank, 12 GPH recovery (60 F rise), 74 3/16 x 24 1/4 in, 244 lb; modes Heat Pump and Vacation/Away only; factory cord to a standard outlet. ENERGY STAR (PD 3555363): 12.0 A maximum, 120 V. Port geometry: RH-PIHP-SC-SO Rev. 7 (03/25) p.2 and Use & Care p.11; heights published, plan positions scaled (+-1in).",
                  # Product frame: -y front, +x right, z off the floor. Heights published (E, K,
                  # C); every x/y SCALED off p.2's plan and elevation (+-1"), and the T&P height
                  # too. 3/4" NPT, MIP fittings. `power` is the factory cord, a face only.
                  # Clearances 0" rear/sides, 6" top, 2" T&P release. Both connections
                  # ducted: "any size room", no added ventilation (AP22654 p.9).
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD,
                                     position=(inch(10.7), inch(-11.9), inch(5.0625)),
                                     connection_size=inch(0.75), direction=(0.669, -0.743, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT cold inlet at the HydroBoost riser foot (factory valve cluster), ~42 deg right of front, r ~16in. Height K = 5 1/16in published; x/y scaled off RH-PIHP-SC-SO Rev. 7 p.2."),
                         ServicePort(tag="hot", service=Service.WATER_HOT,
                                     position=(inch(14.1), inch(-5.1), inch(42.375)),
                                     connection_size=inch(0.75), direction=(0.940, -0.342, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT hot outlet, top fitting of the HydroBoost riser, ~70 deg right of front, r ~15in. Height E = 42 3/8in published; x/y scaled off RH-PIHP-SC-SO Rev. 7 p.2."),
                         ServicePort(tag="condensate", service=Service.DRAIN,
                                     position=(inch(-7.5), inch(-11), inch(59)),
                                     connection_size=inch(0.75), direction=(0.0, -1.0, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="3/4in NPT female primary condensate, front-left shoulder. Height C = 59in published; x/y scaled off the drawing."),
                         ServicePort(tag="relief", service=Service.DRAIN,
                                     position=(inch(-5.3), inch(-14.5), inch(46)),
                                     connection_size=inch(0.75), direction=(-0.342, -0.940, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="Factory T&P valve outlet, front-left, ~20 deg left of front, r ~15.4in. Position AND height scaled off RH-PIHP-SC-SO Rev. 7 p.2 (not published); confirm on the delivered unit."),
                         ServicePort(tag="air-out", service=Service.TRANSFER_AIR,
                                     position=(inch(11.4), inch(-4.15), inch(65.5)),
                                     connection_size=inch(8), direction=(0.940, -0.342, 0.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="Outlet adapter: scaled (+/-1.5in) from the side grille above the HydroBoost riser; field verify."),
                         ServicePort(tag="air-in", service=Service.TRANSFER_AIR,
                                     position=(inch(0), inch(0), inch(74.1875)),
                                     connection_size=inch(8), direction=(0.0, 0.0, 1.0),
                                     certainty=PortCertainty.EXACT,
                                     notes="Top inlet: the filter grille under Rheem's inlet adapter and SP20890 elbow (H 91in to its top, AP22654 p.17). Plan centre assumed."),
                         ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))))),
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
    # EQ-S-HP1-AH's supply box (2026-11-11), filed MIXING_BOX: the passive-box kind.
    EquipmentType(tag="EQ-T-HP1-SUP-BOX",
                  name="System 1 supply box, 22 1/2 x 14 x 23 in, shop-fabricated",
                  footprint=(inch(22.5), inch(14)), height=inch(23), plan_symbol="erv",
                  source="Shop-fabricated galvanized plenum, 22 1/2 x 14 x 23 in, on the attic deck at EQ-S-HP1-AH's discharge: the cabinet's 11 5/8 x 16 3/4 in opening (4 1/4 in up on its platform) enters its east face through the unit's 3 in canvas connector, and DU-S-HP-SUP-DROP (12x12) leaves through its floor down FS-ATTIC's y 336-352 bay onto the 18x8 trunk. It is the transition between the two sections. Gree's IOM asks for a solid sheet-metal bottom for the first 6 in after the unit; that reads as the downflow-over-combustible-floor case, but the drop here starts at the inlet wall, so confirm with Gree before fabrication. Mastic-sealed, 26 ga, set on the deck.",
                  ports=(ServicePort(tag="inlet", service=Service.SUPPLY_AIR,
                                     position=(inch(11.25), ft(0), inch(13.3125))),
                         ServicePort(tag="drop", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), ft(0))))),
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
# EQ-S-HP1-AH lies on the attic deck over the north hall (EQUIPMENT_HVAC_ATTIC below, since
# 2026-11-11: SF-S-HP1's 36 1/2" clear width could not hold Gree's 24" front service space in
# any orientation). Its west discharge feeds EQ-A-HP1-SUP-BOX, which drops DU-S-HP-SUP through
# FS-ATTIC's y 336-352 bay into SF-S-DUCT; the trunk runs SOUTH down the hallway. The hall
# return rises from REG-S-HP-RET through the y 352-368 bay to EQ-S-ERV-MIX at the unit's east
# end, where the ERV feed and RM-S-SUITE's and RM-S-BED3's returns also land.
#
# SOFFIT routing + `soffit_ref` puts the trunk under `mep.duct_soffit_occupancy`. Hall is
# x 18'-2 3/4"..21'-8" clear; the trunk runs at x=19'-6".
DUCTS_HVAC_SECOND = [
    # 750 cfm through 18x8 is 750 fpm (14x8 was 965, over Manual D's 900 for a trunk in a
    # finished space). It sheds 3 x 80 (plan/mep_hvac_branches.py) + 50 + 175 + 35 and hands
    # the last 250 to DU-S-HP-SOUTH-RISE collinearly at the cap (y=9'-10").
    #
    # Its north cap is at y=29'-2", 6" past DU-S-HP-SUP-DROP's top take-off and north of
    # DU-S-HP-BED3's collar (y=27'-6"). REG-A-HP-EAST at (19'-4", 11'-4") is still squarely
    # over it. 100 1/8" storey is SF-S-DUCT's cavity floor.
    DuctRun(uid="CSDH01AAAA", tag="DU-S-HP-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), inch(350)), pt(ft(19, 6), ft(9, 10))),
            elevations=(inch(100.125), inch(100.125)),
            width=inch(18), depth=inch(8), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=750, material="galvanized"),
    # THE DROP from EQ-A-HP1-SUP-BOX's floor through FS-ATTIC's y 336-352 bay (FO-A-HP1-SUP)
    # onto the trunk's top. 12x12 and not the trunk's 18x8: the same 144 in2 (750 fpm), and a
    # 12" riser passes between joists 16" apart where an 18" one cuts one.
    DuctRun(uid="F5569DXC7B", tag="DU-S-HP-SUP-DROP", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), inch(344)), pt(ft(19, 6), inch(344))),
            elevations=(inch(121), inch(102)),
            width=inch(12), depth=inch(12), routing=DuctRouting.CHASE,
            design_cfm=750, material="galvanized"),
    # THE HALL RETURN: REG-S-HP-RET's boot rises through SF-S-DUCT's open top into FS-ATTIC's
    # y 352-368 bay, runs east along it (12 wide x 10 deep in 13 11/16" clear; 490 cfm is
    # 588 fpm) and turns up through the deck into EQ-S-ERV-MIX. The bay runs in x, so
    # nothing is bored.
    DuctRun(uid="CSDH02AAAA", tag="DU-S-HP-RET", system=DuctSystem.RETURN,
            path=(pt(inch(239), inch(360)), pt(inch(304.5), inch(360)),
                  pt(inch(304.5), inch(360))),
            elevations=(inch(114.125), inch(114.125), inch(121)),
            width=inch(12), depth=inch(10), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-ATTIC", design_cfm=490, material="galvanized"),
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
    # 99 1/8" is a 6"-deep duct on SF-S-DUCT's clear underside (the box's 14" drop);
    # 111 1/8" is the same duct's centreline on FS-ATTIC's bottom chord,
    # the elevation DU-S-HP-SOUTH derives for itself from the joists. Both storey-relative
    # to `second`, whose datum is 10'-0" — the same convention every PipeRun here uses.
    DuctRun(uid="27B8FKNDPB", tag="DU-S-HP-SOUTH-RISE", system=DuctSystem.SUPPLY,
            path=(pt(ft(19, 6), ft(9, 10)), pt(ft(19, 6), ft(3, 3)),
                  pt(ft(19, 6), ft(3, 3))),
            elevations=(inch(99.125), inch(99.125), inch(111.125)),
            width=inch(10), depth=inch(6), routing=DuctRouting.SOFFIT,
            soffit_ref="SF-S-DUCT", design_cfm=250, material="galvanized"),
    # DU-S-ERV-HP-FEED is in plan/mep_erv_l3.py: it comes off the attic sub-manifold and
    # ends in EQ-S-ERV-MIX on the attic deck; it never enters SF-S-DUCT. DU-S-PLANT-EXH is DU-M-ERV-R-PLANT there,
    # on the LEVEL-2 manifold, running in FS-S-WEST's open-web trusses and rising inside
    # W-S-C1 to a high sidewall grille — it is not System 1's, it is the ERV's stale pull
    # out of RM-S-PLANT: 25 cfm against ~20 of makeup, extract-biased on purpose, and an ERV
    # is damage limitation rather than humidity control (notes/plant_room.md).
]

# THE AIR HANDLER IN THE ATTIC (2026-11-11). Horizontal-left on the deck of RM-A-EAST-UNFIN
# (conditioned, under the hot roof), over the north hall. It stands on SL-A-HP1-PLATFORM, 4 1/4"
# up, which is what gives the primary condensate port room for Gree's trap above the deck
# (PR-A-COND-HP1, plan/mep_condensate.py). The emergency pan (2" deep, 3" oversize,
# tasks.toml) sits on the platform under the cabinet and is not modelled: its rails lift every
# connection about 1" more on site. A float switch in it opens the cooling call (IMC 307.2.3
# item 3; owner, 2026-11-11: the attic is conditioned, but an overflow still wets the
# second-storey ceiling, so the code and Gree's IOM both apply). Rotation 0
# puts the discharge west, the return east and the service front SOUTH, where Gree's 24" zone
# (x 20'-10 1/2"..24'-6", y 25'-4 9/16"..27'-4 9/16") is open deck at the end of the walk
# from D-A-STUDY: ~20' at
# 6'-9" headroom or more, inside IMC 306.3's 50' passageway. The supply opening's rear-biased
# centre (y=28'-8") is the drop bay's centre. Tags keep their `-S-` for continuity. The
# refrigerant lines are not modelled (notes/flexx_ultra_geometry.md).
EQUIPMENT_HVAC_ATTIC = [
    Equipment(uid="CEE032AAAA", tag="EQ-S-HP1-AH",
              kind=EquipmentKind.DUCTED_AIR_HANDLER,
              position=pt(inch(272.25), inch(339.1875)), footprint=(inch(43.5), inch(21.25)),
              room="RM-A-EAST-UNFIN", type_ref="EQ-T-GREE-FLEXX-ULTRA-24-AH",
              outdoor_ref="EQ-M-HP1-OD", circuit="CKT-HP1-AH",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(4.25)),
              zone_rooms=("RM-S-STUDY2", "RM-S-PLANT", "RM-S-BED1", "RM-S-BED2",
                          "RM-S-BED3", "RM-S-SUITE", "RM-S-SUITEBATH", "RM-S-VANITY",
                          "RM-S-BATH1", "RM-S-HALL", "RM-S-CLOSET", "RM-S-NCLOSET",
                          "RM-A-EAST-UNFIN", "RM-A-STUDY", "RM-A-STUDIO",
                          "RM-A-STUBATH", "RM-A-POCKET")),
    # The FLEXA2LHTR05KWD kit slides into the cabinet's discharge end and is drawn there.
    # `blower_interlock_ref` is what makes the overlap intended: the unit's own 24 VAC board
    # stages it with the blower. Fed from CKT-HP1-AH (35 A).
    Equipment(uid="CEE033AAAA", tag="EQ-S-HP1-STRIP", kind=EquipmentKind.SPACE_HEATER,
              position=pt(inch(256.5), inch(339.1875)), footprint=(inch(16), inch(10)),
              rotation=deg(90), room="RM-A-EAST-UNFIN",
              type_ref="EQ-T-GREE-FLEXX-HEATKIT-46KW", circuit="CKT-HP1-AH",
              blower_interlock_ref="EQ-S-HP1-AH",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(4.25))),
    # The cabinet's platform: 3" past the case each way, for the pan.
    Slab(uid="BX4WEB62X5", tag="SL-A-HP1-PLATFORM", kind="deck",
         outline=(pt(inch(247.5), inch(325.5625)), pt(inch(297), inch(325.5625)),
                  pt(inch(297), inch(352.8125)), pt(inch(247.5), inch(352.8125))),
         thickness=inch(4.25), assembly="AH_PLATFORM_PLY", top_elevation=inch(245)),
    Equipment(uid="HP2Y52SMWG", tag="EQ-A-HP1-SUP-BOX", kind=EquipmentKind.MIXING_BOX,
              position=pt(inch(236.25), inch(344)), footprint=(inch(22.5), inch(14)),
              room="RM-A-EAST-UNFIN", type_ref="EQ-T-HP1-SUP-BOX",
              mount=Mount(kind=MountKind.FLOOR)),
]

# The cabinet's two air connections: each is the unit's 3" canvas connector (DuctStandard
# PortKit) and a 1" collar into its shop box (the return box stands 4" off the cabinet). Sections are the openings: supply 11 5/8 across x
# 16 3/4 high (submittal p.4); return 20 x 16, INFERRED from the 16x20x1 internal filter
# (IOM §2.5). Measure the delivered cabinet before either box is made. REG-A-HP-EAST and
# REG-A-HP-STUDY are straight floor boots off the second-storey trunks.
DUCTS_HVAC_ATTIC = [
    DuctRun(uid="Q3DEES5ZH3", tag="DU-A-HP1-SUP-NECK", system=DuctSystem.SUPPLY,
            path=(pt(inch(250.5), inch(344)), pt(inch(246.5), inch(344))),
            elevations=(inch(14.0625), inch(14.0625)),
            width=inch(11.625), depth=inch(16.75), routing=DuctRouting.EXPOSED,
            design_cfm=750, material="galvanized"),
    DuctRun(uid="XNJFPY0B2F", tag="DU-A-HP1-RET-NECK", system=DuctSystem.RETURN,
            path=(pt(inch(299), inch(339.1875)), pt(inch(294), inch(339.1875))),
            elevations=(inch(14.0625), inch(14.0625)),
            width=inch(20), depth=inch(16), routing=DuctRouting.EXPOSED,
            design_cfm=750, material="galvanized"),
]

# ** OPEN IN RM-B-WORKSHOP's NE CORNER SINCE 2026-11-09 (owner). ** Back on W-B-CW2 (Rheem
# 0" rear), riser lobe 14" off W-B-HALL-W. Both air connections are ducted through
# W-B-HALL-W's one 12 1/2" bay north of D-B-SHOP into the stair hall (plan/mep_hpwh_air.py),
# so the chill and the shop dust both stay out of the workshop's air and the filter.
#
# ** ROTATED -40 deg: EXHAUST SOUTH-EAST, ON THE BAY'S LINE. ** The exhaust is front + 70
# deg, so the side port, the top elbow's outlet and the turn onto the bay line up in plan:
# each duct runs straight to one bend square to W-B-HALL-W. The display faces south-west
# over the 30x30 working space on the open floor; the T&P and condensate face it, west of
# the ducts. World ports (notes/water_service.md §1): hot (145.0", 188.4", 42 3/8"), cold
# (138.0", 185.4", 5 1/16"), T&P (124.1", 193.7", ~46"), condensate (124.7", 197.8", 59"),
# air-out (143.6", 190.9", 65 1/2"), air-in (top centre, 74 3/16").
EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(inch(137.5), inch(201.375)), rotation=deg(-40),
             footprint=(inch(24.25), inch(24.25)), room="RM-B-WORKSHOP", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH",
             relief_discharge_ref="PR-B-WH-TPR"),
]
