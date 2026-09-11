"""The inspections Minnesota requires, in the order Minn. R. 1300.0210 states them.

Data, beside the profile's permit checklist, for the same reason the checklist is data: a
second jurisdiction is a second list here, not an ``if profile == ...`` in the scheduler.

Three things this list deliberately is not.

**It is not a schedule.** ``after`` is a partial order and ``gates`` names trades. When any
of it happens is authored in ``houses/<name>/inspections.toml``; nothing here is a date.

**It carries no phone numbers.** Who to call is house-owned (``[authorities]``), exactly as
prices are — Saint Paul's number does not belong in an engine shipped to Duluth.

**Who inspects electrical is a house fact, not a profile fact.** Minnesota licenses
electrical through the Department of Labor and Industry, and Minn. Stat. 326B.36 subd. 1
and 6 let a municipality run its own electrical, plumbing and mechanical inspections — Saint
Paul does all three, through DSI, on its own numbers. So the electrical lines carry
``authority = "electrical"`` to say they resolve to a *different authority row*, and the
label says nothing about who staffs it: ``[authorities]`` in ``houses/<name>/inspections.toml``
is where that is answered. The earlier "(State inspector)" labels here were wrong for the
one city this repo's reference house is in.
"""

from __future__ import annotations

from typehaus.checks.jurisdiction import InspectionSpec

#: Minn. R. 1300.0210 subp. 3-9, in the order the rule states them, plus the two Minnesota
#: additions (radon rough-in under MN Rules 1303.2400, the blower-door report under MN
#: Rules 1322 / N1102.4.1.2) at the point in the build where they actually happen.
MN_INSPECTIONS: tuple[InspectionSpec, ...] = (
    InspectionSpec(
        id="erosion", label="Erosion and sediment control",
        authority="building", gates=("earth",),
        check_ids=("code.R401_3_impervious",),
        on_site=("permit card posted",
                 "inspection record card posted and kept on site (subp. 3)",
                 "silt fence installed along the downhill edge",
                 "rock construction entrance"),
        milestone="foundation",
        code_refs=("MN Rules 1300.0210", "NPDES construction permit"),
    ),
    InspectionSpec(
        id="footing", label="Footing — forms and reinforcement, before the pour",
        authority="building", after=("erosion",),
        check_ids=("structural.frost_depth", "structural.concrete_cover_meets_minimum",
                   "structural.concrete_mix_matches_exposure",
                   "integrity.reinforcement_spec_agrees"),
        on_site=("approved plan set", "footing forms set and braced",
                 "reinforcement tied and chaired", "bottom of footing below frost"),
        milestone="foundation",
        code_refs=("IRC R403.1", "IRC R403.1.4"),
    ),
    InspectionSpec(
        id="foundation_wall", label="Foundation wall — forms, steel and anchorage",
        authority="building", after=("footing",),
        check_ids=("structural.foundation_unbalanced_fill",
                   "code.R403_1_6_foundation_anchorage",
                   "structural.concrete_cover_meets_minimum"),
        on_site=("wall forms set", "vertical and horizontal steel placed",
                 "anchor bolt layout marked to the sill plan"),
        milestone="foundation",
        code_refs=("IRC R404", "IRC R403.1.6"),
    ),
    InspectionSpec(
        # The one line that has to pass before anything gets buried, which is why it gates
        # both the earth trade (backfill) and framing (the walls it would brace).
        id="foundation_backfill", label="Damproofing, drainage and backfill",
        authority="building", after=("foundation_wall",), gates=("earth", "framing"),
        check_ids=("code.R405_1_foundation_drainage", "code.R406_1_dampproofing",
                   "drainage.discharge_consistency", "code.R401_3_grading"),
        on_site=("damproofing applied and cured", "drain tile bedded in washed rock",
                 "filter fabric over the rock"),
        milestone="foundation",
        code_refs=("IRC R405.1", "IRC R406.1"),
    ),
    InspectionSpec(
        id="underground_plumbing", label="Under-slab plumbing, under test",
        authority="plumbing", after=("foundation_wall",),
        check_ids=("mep.under_slab_burial", "mep.footing_clearance", "mep.drain_slope",
                   "mep.sleeve_coverage", "mep.sleeve_alignment", "mep.sewer_exit_invert"),
        on_site=("system under 10 ft head or 5 psi air", "gauge reading holding",
                 "trench open at every joint"),
        milestone="foundation",
        code_refs=("MN Rules 4714.0712", "IRC P2503"),
    ),
    InspectionSpec(
        # An OWNER hold, not an AHJ line. Minn. R. 1300.0210 names no radon rough-in:
        # the passive system is mandatory under 1303.2400-.2403 and is verified inside the
        # under-slab and final inspections, and Saint Paul issues a separate radon plumbing
        # permit. Everything under this slab is invisible the day after the pour, so the
        # hold is real — it is just the owner's, and giving it a phone number would be a lie.
        id="radon_rough", label="Passive radon system rough-in (owner's hold)",
        authority="owner", after=("underground_plumbing",),
        check_ids=("code.MN_1303_2402_radon",),
        on_site=("gas-permeable layer in place", "riser labelled at every storey",
                 "sump cover sealed and gasketed", "junction box in the attic for a fan"),
        milestone="foundation",
        code_refs=("MN Rules 1303.2400-.2402",),
    ),
    InspectionSpec(
        id="slab", label="Slab — vapour retarder, insulation and in-floor tube",
        authority="building", after=("underground_plumbing", "radon_rough"),
        gates=("floors",),
        check_ids=("integrity.slab_thickness", "code.energy_prescriptive"),
        on_site=("vapour retarder lapped and sealed", "under-slab insulation placed",
                 "in-floor tube pressurised and marked"),
        milestone="foundation",
        code_refs=("IRC R506", "IRC N1102.1.2"),
    ),
    InspectionSpec(
        id="braced_wall", label="Braced wall lines and lateral bracing",
        authority="building", after=("foundation_backfill",),
        check_ids=("structural.braced_wall_line_spacing", "structural.braced_wall_panels",
                   "structural.lateral_racking"),
        on_site=("braced wall plan on site", "hold-downs installed and torqued"),
        milestone="weathertight",
        code_refs=("IRC R602.10",),
    ),
    InspectionSpec(
        id="rough_plumbing", label="Rough plumbing, under test",
        authority="plumbing", after=("braced_wall",),
        check_ids=("mep.drain_slope", "mep.drain_offset_geometry", "mep.trap_arm_length",
                   "mep.vent_reachability", "mep.vent_termination_height",
                   "mep.wet_wall_occupancy", "structural.wet_wall_bearing",
                   "mep.pipe_sizing", "mep.fixture_drain_reach"),
        on_site=("DWV under test", "water piping under test", "no insulation in the walls"),
        milestone="rough_ins",
        code_refs=("IRC P2503", "MN Rules 4714"),
    ),
    InspectionSpec(
        id="rough_mechanical", label="Rough mechanical — duct, equipment and venting",
        authority="mechanical", after=("braced_wall",),
        check_ids=("mep.duct_connectivity", "mep.duct_joist_bay_occupancy",
                   "mep.duct_soffit_occupancy", "mep.ventilation_distribution",
                   "code.N1103_6_whole_house_ventilation", "code.M1502_dryer_exhaust",
                   "mep.erv_outdoor_terminals"),
        on_site=("duct runs complete and supported", "equipment set and level",
                 "combustion and exhaust terminations set"),
        milestone="rough_ins",
        code_refs=("IRC M1601", "MN Rules 1322 R403.5"),
    ),
    InspectionSpec(
        id="rough_electrical", label="Rough electrical",
        authority="electrical", after=("braced_wall",),
        check_ids=("electrical.receptacle_spacing", "code.E3902_gfci_locations",
                   "code.E3902_16_afci", "code.E3901_6_bathroom_receptacle",
                   "electrical.room_lighting", "electrical.circuit_refs",
                   "electrical.panel_spaces", "electrical.wet_location"),
        on_site=("electrical permit filed with the authority named in [authorities]",
                 "boxes set and secured", "cable stapled and protected at plates"),
        milestone="rough_ins",
        code_refs=("MN Rules 1315", "2026 NEC"),
    ),
    InspectionSpec(
        id="framing", label="Framing — after all three rough-ins",
        authority="building",
        after=("rough_plumbing", "rough_mechanical", "rough_electrical"),
        gates=("walls",),
        check_ids=("structural.ijoist_span", "structural.rafter_span",
                   "structural.header_prescriptive", "structural.ridge_beam_depth",
                   "structural.member_interference", "structural.floor_opening_header",
                   "structural.uplift_path_coverage", "code.R302_5_garage_separation",
                   "code.R302_13_floor_protection"),
        on_site=("sealed truss drawings on site", "hangers and straps installed",
                 "fireblocking in place"),
        milestone="rough_ins",
        code_refs=("IRC R502", "IRC R802", "IRC R602"),
    ),
    InspectionSpec(
        # 1300.0210 subp. 6.F calls this the ENERGY-EFFICIENCY inspection, and the rule
        # names no "insulation" inspection at all. The name matters: it is the sheet the
        # certificate under 1322.0401 is checked against, not a look at the batts.
        id="energy", label="Energy efficiency — insulation, air barrier and certificate",
        authority="building", after=("framing",),
        check_ids=("code.energy_prescriptive", "building_science.condensation",
                   "code.R316_4", "code.R806_5_unvented_roof",
                   "code.R806_2_attic_ventilation"),
        on_site=("air sealing complete at every penetration",
                 "insulation certificate posted", "baffles at the eaves"),
        milestone="insulated",
        code_refs=("MN Rules 1300.0210 subp. 6.F", "IRC N1102.1.2", "IRC N1102.4"),
    ),
    InspectionSpec(
        id="blower_door", label="Blower-door test report (third party)",
        authority="report", after=("energy",),
        check_ids=("code.N1102_4_air_leakage",),
        on_site=("test report filed with the AHJ", "ACH50 at or below the target"),
        milestone="insulated",
        code_refs=("IRC N1102.4.1.2", "MN Rules 1322"),
    ),
    InspectionSpec(
        id="drywall", label="Gypsum board — fastening, before taping",
        authority="building", after=("energy",),
        check_ids=("code.R302_7_under_stair_protection", "code.R302_13_floor_protection",
                   "code.R316_4"),
        on_site=("board hung and fastened", "rated assemblies complete and continuous"),
        milestone="insulated",
        code_refs=("IRC R702.3",),
    ),
    InspectionSpec(
        # Minn. R. 1300.0210 subp. 6.H: fire-resistance-rated construction and the
        # penetrations through it. On a house of this kind that is the garage separation,
        # which is why the applicability probe is a garage and not a rated corridor.
        id="fire_penetrations",
        label="Fire-resistance-rated construction and penetrations",
        authority="building", after=("framing",), applies_when="garage_separation",
        # Fireblocking is explicitly outside this profile's coverage statement, so it is
        # an on-site tick below and not a check id that would silently never run.
        check_ids=("code.R302_5_garage_separation", "code.R302_13_floor_protection"),
        on_site=("separation complete and continuous to the underside of the roof deck",
                 "every penetration through the separation firestopped",
                 "self-closing door set and latching"),
        milestone="rough_ins",
        code_refs=("MN Rules 1300.0210 subp. 6.H", "IRC R302.5", "IRC R302.11"),
    ),
    InspectionSpec(
        id="lath", label="Lath and weather barrier (stucco)",
        authority="building", after=("framing",), applies_when="stucco",
        on_site=("two layers of weather-resistive barrier", "lath fastened and lapped",
                 "casing and weep screed set"),
        milestone="weathertight",
        code_refs=("IRC R703.7",),
    ),
    InspectionSpec(
        id="fireplace", label="Fireplace and chimney",
        authority="building", after=("framing",), applies_when="fireplace",
        on_site=("hearth extension formed", "clearances to combustibles verified"),
        milestone="rough_ins",
        code_refs=("IRC R1001", "IRC R1003"),
    ),
    InspectionSpec(
        id="gas_test", label="Fuel-gas piping test",
        authority="mechanical", after=("rough_mechanical",), applies_when="gas",
        on_site=("piping under test", "gauge holding"),
        milestone="rough_ins",
        code_refs=("IRC G2417",),
    ),
    InspectionSpec(
        id="final_plumbing", label="Final plumbing",
        authority="plumbing", after=("drywall",),
        check_ids=("mep.backflow_prevention", "mep.main_shutoff",
                   "code.P2804_water_heater_relief", "mep.hot_water_insulation",
                   "mep.water_hammer_arrestor", "mep.exterior_hydrant_protection"),
        on_site=("every fixture set and trapped",
                 "water heater relief piped to within 6\" of the floor"),
        milestone="final",
        code_refs=("IRC P2503.5",),
    ),
    InspectionSpec(
        id="final_mechanical", label="Final mechanical",
        authority="mechanical", after=("drywall",),
        check_ids=("mep.heating_capacity", "mep.cooling_capacity",
                   "code.R303_3_local_exhaust", "mep.humid_room_pressure"),
        on_site=("equipment started and balanced", "ventilation controls labelled"),
        milestone="final",
        code_refs=("IRC M1305",),
    ),
    InspectionSpec(
        id="final_electrical", label="Final electrical",
        authority="electrical", after=("drywall",),
        check_ids=("electrical.service_load", "electrical.lighting_controls",
                   "code.R327_ess_listing", "code.R327_ess_capacity",
                   "code.R327_ess_detection", "code.NEC_705_12_interconnection",
                   "code.NEC_690_12_rapid_shutdown"),
        on_site=("panel directory complete", "devices trimmed and tested"),
        milestone="final",
        code_refs=("MN Rules 1315", "2026 NEC"),
    ),
    InspectionSpec(
        id="building_final", label="Building final — certificate of occupancy",
        authority="building",
        after=("blower_door", "final_plumbing", "final_mechanical", "final_electrical"),
        check_ids=("code.R310_egress", "code.R311_7_stair_geometry",
                   "code.R311_7_8_handrail", "code.R312_1_guard",
                   "code.R312_1_3_guard_opening_limit", "code.R314_R315_alarms",
                   "code.R314_alarm_every_storey", "code.R315_co_every_sleeping_area",
                   "code.R305_ceiling_height", "code.R308_4_safety_glazing",
                   "code.R303_7_stairway_illumination",
                   "code.R303_8_exterior_stairway_illumination",
                   "code.R311_3_exterior_landing", "code.site_setback"),
        on_site=("address numbers posted", "alarms installed and sounding",
                 "final grade away from the foundation", "as-built survey filed",
                 "energy certificate posted on the electrical panel, naming the general "
                 "contractor (MN Rules 1322.0401)"),
        milestone="final",
        code_refs=("IRC R110", "MN Rules 1322.0401"),
    ),
)
