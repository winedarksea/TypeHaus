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
        "Encodes a declared subset. Habitability and egress: R305 ceiling height, R310 "
        "emergency escape openings, R311.7 stairways, R311.6 hallway width, egress door "
        "width. Site: R401.3 lot drainage away from the foundation, local setbacks. "
        "Energy: the N1102.1.2 prescriptive envelope only. Structural: frost depth and "
        "I-joist span tables only — no engineered analysis, no lateral system, no "
        "connection design. Plumbing: rough-in geometry and MN ch. 4714 sizing tables "
        "(sleeving, drain slope, wall occupancy, under-slab and footing clearance, sewer "
        "invert, DFU/WSFU sizing, trap-arm length) — no gas, no fixture venting beyond "
        "trap arms, no testing. Does NOT cover mechanical or electrical chapters at all. "
        "Every permit item names the checks that answer it; this profile covers a declared "
        "subset of the code; results are never 'code compliant'."
    ),
    frost_depth_in=42.0,
    # IRC Table R401.4.1 presumptive value for sandy/silty clay, the conservative default
    # where no soils report exists. A real geotechnical report supersedes it.
    soil_bearing_psf=1500.0,
    climate=MN_ZONE_6,
    permit_items=(
        PermitItemSpec("Ceiling height / habitable attic", ("code.R305_ceiling_height",),
                       ("IRC R305",)),
        PermitItemSpec("Sleeping-room emergency escape", ("code.R310_egress",), ("IRC R310",)),
        PermitItemSpec("Egress door clear width", ("code.R311_door_width",), ("IRC R311.2",)),
        PermitItemSpec("Stair geometry and headroom",
                       ("code.R311_7_stair_geometry", "code.R311_7_2_stair_headroom",
                        "code.R311_7_1_stair_width", "code.R311_7_6_landing_depth"),
                       ("IRC R311.7",)),
        PermitItemSpec("Guards at stair-well openings", ("code.R312_1_guard",),
                       ("IRC R312.1",)),
        PermitItemSpec("Smoke / CO alarm placement",
                       ("code.R314_R315_alarms", "code.R315_garage_alarms"),
                       ("IRC R314", "IRC R315")),
        # R401.3 was two registered checks no checklist item referenced — precisely the
        # drift the coverage test now prevents. Lot drainage is a permit-plan requirement,
        # and the coverage statement above has always claimed it.
        PermitItemSpec("Lot drainage away from the foundation",
                       ("code.R401_3_grading", "code.R401_3_impervious"), ("IRC R401.3",)),
        PermitItemSpec("Site setbacks", ("code.site_setback",), ("local zoning",)),
        PermitItemSpec("Energy prescriptive envelope", ("code.energy_prescriptive",),
                       ("IRC N1102.1.2",)),
        PermitItemSpec("Foundation frost depth", ("structural.frost_depth",), ("IRC R403.1.4",)),
        PermitItemSpec("I-joist span table", ("structural.ijoist_span",),
                       ("manufacturer span table",)),
        PermitItemSpec("Plumbing sleeve alignment", ("mep.sleeve_alignment",), ()),
        PermitItemSpec("Plumbing drain slope", ("mep.drain_slope",), ("IRC P3005.3",)),
        # The plumbing pass (2026-07-29) landed eight more CODE-tier checks. Every one of
        # them answers a line a plan reviewer actually asks about, so they go on the
        # checklist rather than into the exclusion list — the pour-day sleeve schedule most
        # of all, since it is the one item that cannot be corrected after the fact.
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
    ),
    permit_exclusions=(
        ("mep.hydrant_freeze_depth",
         "a fixture-durability rule (a yard hydrant's own freeze protection), not a "
         "permit-plan review item; it stays in the full check report"),
        ("code.R311_7_8_handrail",
         "no handrail is modeled yet — Railing elements are guards with no handrail "
         "role/graspability semantics, so the check reports UNKNOWN by design in the "
         "full check report; it joins the checklist when the schema grows a handrail "
         "role (plans/TODO.md)"),
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
