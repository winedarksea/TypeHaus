"""MN Residential code profile (#8/#10/#32) — versioned by edition (→ 12 §checks/code).

Profile rigor (#32): declares edition, effective date, amendment history vs. IRC base,
and a coverage statement; every rule carries a citation; results are tri-state; output
wording never says "code compliant".
"""

from __future__ import annotations

from typehaus.checks.registry import JurisdictionProfile

MN_2024 = JurisdictionProfile(
    name="mn-2024",
    edition="Minnesota Residential Code 2020 (MN Rules 1309)",
    effective_date="2020-03-31",
    irc_base="2018 IRC + MN amendments",
    coverage_statement=(
        "Encodes a declared subset: R305 ceiling height, R310 emergency escape openings, "
        "R311.7 stairways, R311.6 hallway width, and egress door width. Does NOT cover "
        "structural, mechanical, electrical, plumbing, or energy chapters. "
        "This profile covers a declared subset of the code; results are never 'code compliant'."
    ),
)

PROFILES: dict[str, JurisdictionProfile] = {"mn-2024": MN_2024}


def get_profile(name: str) -> JurisdictionProfile:
    return PROFILES.get(name, MN_2024)
