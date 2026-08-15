"""MN Residential code profile (#8/#10/#32) — versioned by edition (→ 12 §checks/code).

Profile rigor (#32): declares edition, effective date, amendment history vs. IRC base,
and a coverage statement; every rule carries a citation; results are tri-state; output
wording never says "code compliant".

The profile also *owns* its permit checklist and its climate table. Both used to live
elsewhere — the checklist hand-written in ``checks/permit.py``, the envelope table under a
Minnesota-specific name in ``checks/code/mn_energy.py`` — which made adding a jurisdiction a
code change across three modules instead of a new profile here.
"""

from __future__ import annotations

from typehaus.checks.code.mn_energy import MN_ZONE_6
from typehaus.checks.jurisdiction import JurisdictionProfile, PermitItemSpec

MN_2024 = JurisdictionProfile(
    name="mn-2024",
    edition="Minnesota Residential Code 2020 (MN Rules 1309)",
    effective_date="2020-03-31",
    irc_base="2018 IRC + MN amendments",
    coverage_statement=(
        "Encodes a declared subset. "
        "Habitability, egress and circulation: R305 ceiling height, R310 emergency escape "
        "openings (sleeping rooms and basements), R311.2 egress door width and height, "
        "R311.3 landings at exterior doors, R311.6 hallway width, R311.7 stairways. "
        "Fall protection: R312.1 guards at stair wells and raised walking surfaces, "
        "R312.1.3 guard opening limits, R311.7.8 stair handrails, and R312.2 window fall "
        "protection. Glazing: R308.4 safety glazing in hazardous locations. "
        "Fire safety: R302.5/R302.6 garage-to-dwelling separation (gypsum thickness, doors "
        "into sleeping rooms, ducts into garages) and R302.13 floor-assembly protection; "
        "R314/R315 smoke and CO alarms per storey and per sleeping area. "
        "Light and ventilation: R303.1 glazing and openable area, R303.3 local exhaust, "
        "N1103.6 whole-house ventilation rate. "
        "Site: R401.3 lot drainage away from the foundation, local setbacks. "
        "Energy: the N1102.1.2 prescriptive envelope and the N1102.4.1.2 air-leakage "
        "target. "
        "Attic: R807.1 access and R806.2 ventilation net free area. "
        "Structural: frost depth and I-joist span tables only — no engineered analysis, no "
        "lateral system, no connection design. "
        "Plumbing: rough-in geometry and MN ch. 4714 sizing tables (sleeving, drain slope, "
        "wall occupancy, under-slab and footing clearance, sewer invert, DFU/WSFU sizing, "
        "trap-arm length) — no gas, no fixture venting beyond trap arms, no testing. "
        "Electrical: E3902 GFCI receptacle locations and E3902.16 AFCI branch-circuit "
        "coverage only — no conductor sizing, box fill, or load calculation, none of which "
        "is claimed as a code result. "
        "Energy storage: R327.2 UL 9540 listing, R327.5 per-unit and aggregate energy "
        "ratings, and R327.7 smoke and heat detection at the system. R327.3 installation "
        "per the manufacturer's instructions and R327.6 protection from impact are NOT "
        "covered — neither has anything in the model to grade. Source-side NEC: 705.12 "
        "busbar interconnection and 690.12 PV rapid shutdown; no other article of the NEC "
        "is claimed. "
        "Explicitly NOT covered, and not merely unimplemented: fireblocking and "
        "draftstopping (R302.11-.12), crawl spaces (R408), chimneys and solid-fuel "
        "appliances (R1001-R1004), and notching and boring limits (R502.8/R602.6). "
        "Also covered: R310.2.3 window wells, M1502 dryer exhaust, and P2801.6/P2804.6.1 "
        "water-heater relief discharge and pan. "
        "Added 2026-08-15: R302.7 under-stair protection, R303.7/R303.8 interior and "
        "exterior stairway illumination (presence and switching only — illuminance is a "
        "photometric result this model cannot compute), R403.1.6 sill-plate anchorage "
        "(the schedule rule, not a bolt count), R405.1 foundation drainage, R406.1 "
        "dampproofing, and MN Rules 1303.2400-.2402 passive radon control — the state's "
        "own rule, with no IRC parent, covering the collection point, the sealed sump "
        "cover, the exhaust's separation from openings into conditioned space, and the "
        "power source for a future fan. Not covered within that radon rule, because the "
        "model carries no field to grade them: the soil-gas membrane laps, the 10 ft of "
        "perforated pipe under it, the vent labelling, the 24-inch fan clearance, and the "
        "R-4 insulation on pipe in unconditioned space. Not covered: "
        "assembly fire-resistance ratings beyond gypsum grade and thickness. "
        "Every permit item names the checks that answer it; this profile covers a declared "
        "subset of the code; results are never 'code compliant'."
    ),
    frost_depth_in=42.0,
    # IRC Table R401.4.1 presumptive value for sandy/silty clay, the conservative default
    # where no soils report exists. A real geotechnical report supersedes it.
    soil_bearing_psf=1500.0,
    # Twin Cities glacial till backfill reads as GM/ML (silty gravel to inorganic silt) on
    # the Hennepin County soil survey — IRC Table R405.1's 45 psf/ft equivalent-fluid group,
    # the middle of the three columns. Like soil_bearing_psf above this is the presumptive
    # value where no soils report exists, and a real geotechnical report supersedes it.
    soil_class="GM",
    climate=MN_ZONE_6,
    permit_items=(
        PermitItemSpec("Ceiling height / habitable attic", ("code.R305_ceiling_height",),
                       ("IRC R305",)),
        # R310.1 is two requirements, and only the room-level one was encoded: a basement
        # with habitable space needs its own escape opening whether or not anyone sleeps in
        # it. The storey-level rule joins this line rather than opening a new one — a plan
        # reviewer asks "can you get out" once.
        PermitItemSpec("Emergency escape and rescue openings",
                       ("code.R310_egress", "code.R310_1_storey_egress",
                        "code.R310_2_3_window_well"), ("IRC R310",), blocking=False),
        # R311.2 fixes both dimensions of the required egress door; one permit line, two
        # checks — a plan reviewer measures the door once.
        PermitItemSpec("Egress door clear width and height",
                       ("code.R311_door_width", "code.R311_2_door_height"),
                       ("IRC R311.2",)),
        PermitItemSpec("Landings at exterior doors", ("code.R311_3_exterior_landing",),
                       ("IRC R311.3", "IRC R311.3.1"), blocking=False),
        # Claimed by the coverage statement since it was written, implemented by nothing:
        # the meta-tests catch a checklist item with no check and a check on no item, but
        # not a prose claim with neither.
        PermitItemSpec("Hallway width", ("code.R311_6_hallway_width",), ("IRC R311.6",),
                       blocking=False),
        PermitItemSpec("Stair geometry and headroom",
                       ("code.R311_7_stair_geometry", "code.R311_7_2_stair_headroom",
                        "code.R311_7_1_stair_width", "code.R311_7_6_landing_depth",
                        "structural.stair_riser_uniformity"),
                       ("IRC R311.7", "IRC R311.7.5.1")),
        PermitItemSpec("Guards at stair-well openings", ("code.R312_1_guard",),
                       ("IRC R312.1",)),
        # The stair-well rule above and structural.deck_guard covered two shapes of the same
        # requirement; every other raised edge went unmeasured.
        PermitItemSpec("Guards at raised walking surfaces", ("code.R312_1_guard_height",),
                       ("IRC R312.1.1", "IRC R312.1.2"), blocking=False),
        PermitItemSpec("Window fall protection", ("code.R312_2_window_fall_protection",),
                       ("IRC R312.2",), blocking=False),
        # Railing grew a handrail role, so this leaves permit_exclusions and joins the
        # checklist in the same change — a check may not be both.
        PermitItemSpec("Stair handrails", ("code.R311_7_8_handrail",),
                       ("IRC R311.7.8",), blocking=False),
        PermitItemSpec("Guard opening limit", ("code.R312_1_3_guard_opening_limit",),
                       ("IRC R312.1.3",), blocking=False),
        PermitItemSpec("Safety glazing", ("code.R308_4_safety_glazing",),
                       ("IRC R308.4",), blocking=False),
        PermitItemSpec("Garage / dwelling separation",
                       ("code.R302_5_garage_separation",),
                       ("IRC R302.5.1", "IRC R302.5.2", "IRC R302.6"), blocking=False),
        PermitItemSpec("Floor assembly protection", ("code.R302_13_floor_protection",),
                       ("IRC R302.13",), blocking=False),
        PermitItemSpec("Under-stair protection", ("code.R302_7_under_stair_protection",),
                       ("IRC R302.7",)),
        # Two rules, one permit line: a reviewer asks "is the stair lit, and can you switch
        # it from both ends" once, and the interior/exterior split is the code's own way of
        # saying where the fixture goes, not a second question.
        PermitItemSpec("Stairway illumination",
                       ("code.R303_7_stairway_illumination",
                        "code.R303_8_exterior_stairway_illumination"),
                       ("IRC R303.7", "IRC R303.8")),
        PermitItemSpec("Habitable light and ventilation",
                       ("code.R303_1_light_and_ventilation",), ("IRC R303.1",),
                       blocking=False),
        PermitItemSpec("Bathroom and kitchen exhaust", ("code.R303_3_local_exhaust",),
                       ("IRC R303.3", "IRC M1507"), blocking=False),
        PermitItemSpec("Whole-house ventilation rate",
                       ("code.N1103_6_whole_house_ventilation",),
                       ("IRC N1103.6", "ASHRAE 62.2"), blocking=False),
        PermitItemSpec("Attic access", ("code.R807_1_attic_access",), ("IRC R807.1",),
                       blocking=False),
        PermitItemSpec("Attic ventilation", ("code.R806_2_attic_ventilation",),
                       ("IRC R806.2",), blocking=False),
        PermitItemSpec("GFCI receptacle locations", ("code.E3902_gfci_locations",),
                       ("IRC E3902",), blocking=False),
        PermitItemSpec("AFCI branch circuits", ("code.E3902_16_afci",),
                       ("IRC E3902.16",), blocking=False),
        # The energy storage system. R327 is the 2018 IRC's article number for it; the 2021
        # edition renumbered the same material to R328, and this profile's base is 2018.
        PermitItemSpec("Energy storage system",
                       ("code.R327_ess_listing", "code.R327_ess_capacity",
                        "code.R327_ess_detection"),
                       ("IRC R327.2", "IRC R327.5", "IRC R327.7"), blocking=False),
        # The two source-side NEC rules. Separate item from the ESS: an inspector signs off
        # on a backfeed breaker and a roof shutdown at a different moment than on a battery.
        PermitItemSpec("PV interconnection and rapid shutdown",
                       ("code.NEC_705_12_interconnection",
                        "code.NEC_690_12_rapid_shutdown"),
                       ("NEC 705.12(B)(3)(2)", "NEC 690.12(B)(2)"), blocking=False),
        PermitItemSpec("Dryer exhaust", ("code.M1502_dryer_exhaust",), ("IRC M1502",),
                       blocking=False),
        PermitItemSpec("Water-heater relief and pan", ("code.P2804_water_heater_relief",),
                       ("IRC P2801.6", "IRC P2804.6.1"), blocking=False),
        PermitItemSpec("Smoke / CO alarm placement",
                       ("code.R314_R315_alarms", "code.R315_garage_alarms"),
                       ("IRC R314", "IRC R315")),
        # R314.3's actual requirement — an alarm on *each* storey, basements included — had
        # no rule: the existing check only visits storeys that have a bedroom on them, so a
        # basement with zero alarms passed the gate. Non-blocking until the house carries the
        # alarms the rule asks for.
        PermitItemSpec("Alarms on every storey",
                       ("code.R314_alarm_every_storey", "code.R315_co_every_sleeping_area"),
                       ("IRC R314.3", "IRC R314.4", "IRC R315.3"), blocking=False),
        # R401.3 was two registered checks no checklist item referenced — precisely the
        # drift the coverage test now prevents. Lot drainage is a permit-plan requirement,
        # and the coverage statement above has always claimed it.
        PermitItemSpec("Lot drainage away from the foundation",
                       ("code.R401_3_grading", "code.R401_3_impervious"), ("IRC R401.3",)),
        PermitItemSpec("Site setbacks", ("code.site_setback",), ("local zoning",)),
        PermitItemSpec("Energy prescriptive envelope", ("code.energy_prescriptive",),
                       ("IRC N1102.1.2",)),
        PermitItemSpec("Envelope air-leakage target", ("code.N1102_4_air_leakage",),
                       ("IRC N1102.4.1.2", "MN Rules 1322")),
        PermitItemSpec("Foundation frost depth", ("structural.frost_depth",), ("IRC R403.1.4",)),
        PermitItemSpec("Sill-plate anchorage", ("code.R403_1_6_foundation_anchorage",),
                       ("IRC R403.1.6",)),
        # Drainage and dampproofing are one sheet's worth of review — "how does water get
        # away from this concrete" — but two independent findings, because a wall can have
        # tile and no membrane or the reverse.
        PermitItemSpec("Foundation drainage and dampproofing",
                       ("code.R405_1_foundation_drainage", "code.R406_1_dampproofing"),
                       ("IRC R405.1", "IRC R406.1")),
        # Minnesota's own rule, with no IRC parent: every new residential structure in the
        # state gets a passive soil-gas system, and it is drawn on the foundation and
        # plumbing sheets rather than described in a note.
        PermitItemSpec("Passive radon control system", ("code.MN_1303_2402_radon",),
                       ("MN Rules 1303.2400-.2402",)),
        PermitItemSpec("I-joist span table", ("structural.ijoist_span",),
                       ("manufacturer span table",)),
        PermitItemSpec("Plumbing sleeve alignment", ("mep.sleeve_alignment",), ()),
        PermitItemSpec("Plumbing drain slope", ("mep.drain_slope",), ("IRC P3005.3",)),
        # Every one of these plumbing checks answers a line a plan reviewer actually asks
        # about, so they go on the checklist rather than into the exclusion list — the
        # pour-day sleeve schedule most of all, since it is the one item that cannot be
        # corrected after the fact.
        PermitItemSpec("Cast-in sleeve coverage", ("mep.sleeve_coverage",), ()),
        # Grouped: both answer "is the pipe in this wall, and can the wall still do its job".
        PermitItemSpec("Plumbing in framed walls",
                       ("mep.wet_wall_occupancy", "structural.wet_wall_bearing"), ()),
        # Grouped as one line for the same reason: pipe against concrete below grade.
        # `under_slab_burial` contributes nothing on a house with no under-slab drainage,
        # which is why it is not a line of its own — an item with no findings at all grades
        # UNKNOWN, and "this house routes its basement main at the ceiling" is not an
        # unevaluated permit question.
        PermitItemSpec("Pipe below and beside concrete",
                       ("mep.under_slab_burial", "mep.footing_clearance"),
                       ("IRC P2604",)),
        PermitItemSpec("Building sewer invert at the exit sleeve",
                       ("mep.sewer_exit_invert",), ()),
        PermitItemSpec("Drain and supply pipe sizing", ("mep.pipe_sizing",),
                       ("MN Plumbing Code (ch. 4714) Tables 702.1, 703.2, 610.3, 610.4",)),
        PermitItemSpec("Trap-arm length", ("mep.trap_arm_length",),
                       ("MN Plumbing Code (ch. 4714) Table 1002.2",)),
        # Grouped as one line because a reviewer asks them as one question — "how is the
        # potable supply controlled and protected" — and because two of the three are
        # contingent on what the house contains: a plan with no hose connection produces no
        # backflow findings and one with no washer no arrestor findings, and either alone
        # would grade an item UNKNOWN for the honest reason that the house has nothing to
        # evaluate.
        PermitItemSpec("Water supply protection and shutoff",
                       ("mep.main_shutoff", "mep.backflow_prevention",
                        "mep.water_hammer_arrestor"),
                       ("IRC P2902", "IRC P2903.5", "IRC P2903.9.1")),
        PermitItemSpec("Hot-water pipe insulation", ("mep.hot_water_insulation",),
                       ("IRC N1103.4.2",)),
    ),
    permit_exclusions=(
        ("mep.hydrant_freeze_depth",
         "a fixture-durability rule (a yard hydrant's own freeze protection), not a "
         "permit-plan review item; it stays in the full check report"),
    ),
)

PROFILES: dict[str, JurisdictionProfile] = {"mn-2024": MN_2024}

# The jurisdiction used when neither a flag nor preferences.toml names one.
DEFAULT_PROFILE_NAME = "mn-2024"


class UnknownProfile(KeyError):
    """A profile name no jurisdiction in this build defines."""


def get_profile(name: str) -> JurisdictionProfile:
    """Look up a profile by name, refusing names this build does not define.

    This was ``PROFILES.get(name, MN_2024)``: ``--profile wi-2024`` silently evaluated a
    Wisconsin house against Minnesota's code, and nothing in the output said so.
    """
    try:
        return PROFILES[name]
    except KeyError:
        known = ", ".join(sorted(PROFILES))
        raise UnknownProfile(
            f"unknown jurisdiction profile {name!r}; this build defines: {known}"
        ) from None
