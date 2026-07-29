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
        "Encodes a declared subset: R305 ceiling height, R310 emergency escape openings, "
        "R311.7 stairways, R311.6 hallway width, egress door width, and R401.3 lot "
        "drainage away from the foundation. Does NOT cover "
        "structural, mechanical, electrical, plumbing, or energy chapters. "
        "This profile covers a declared subset of the code; results are never 'code compliant'."
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
