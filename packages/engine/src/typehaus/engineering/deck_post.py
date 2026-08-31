"""A round cast-concrete column carrying a deck — ``deck_post/<Post tag>``.

IRC R507.4 publishes maximum heights for **sawn lumber** deck posts, 4x4 and 6x6. There is
no row for a 12" or 20" round cast column and there never will be, which is why these are
engineered items rather than a gap in the table.

**And the answer this module reaches is INCOMPLETE, on purpose.** The concrete is not close
to working hard — the catlin columns run at about a twentieth of their section's capacity —
but ACI 318 does not let a column be plain concrete at all, and ``Post`` carries **no field
in which a house could state the reinforcement**. So the record computes and publishes the
demand, publishes the section's capacity, publishes the minimum longitudinal steel a column
of this size takes, and then names the one thing it does not have. Guessing that a sonotube
"probably has bars in it" is the assumption a calculation cannot survive; #32's rule is that
a check which cannot evaluate says so.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md``, hand-worked in a separate pass.
"""

from __future__ import annotations

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.retaining_basis import PRESUMPTIVE_FC_PSI

KIND = "deck_post"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "IRC R507.4 (no row); ACI 318 structural plain / reinforced concrete"

#: ACI 318-19 §2.3 defines a PEDESTAL as a member with a ratio of height to least lateral
#: dimension not exceeding 3; §14.3.3.1 states the same as a design limit ("ratio of
#: unsupported height to average least lateral dimension shall not exceed 3"). Plain concrete
#: pedestals are permitted (§14.1.3(d)); **plain concrete COLUMNS are not** — §14.1.5, "plain
#: concrete shall not be permitted for columns and pile caps", and R14.1.5 gives the reason:
#: a column lacks the ductility it should have, and a random crack in an unreinforced one
#: endangers its structural integrity. (§22.2.1 in ACI 318-11, whose closing sentence carries
#: the same prohibition.)
#:
#: So the ratio is not trivia — it is the whole question of which clause applies, and both
#: catlin piers are well past it at 10.7 and 6.4.
PEDESTAL_HEIGHT_RATIO = 3.0

#: ACI 318 minimum longitudinal reinforcement for a column, as a fraction of the gross area.
#: ACI 318-19 §10.6.1.1: "area of longitudinal reinforcement shall be at least 0.01Ag but
#: shall not exceed 0.08Ag" (§10.9.1 in 318-11).
COLUMN_MIN_REINFORCEMENT_RATIO = 0.01


@keys(KIND)
def enumerate_posts(ctx: EngineeringContext) -> list[str]:
    return [pier.tag for pier in cast_piers(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(pier) for pier in cast_piers(ctx)]


def _one(pier: _Pier) -> EngineeringRecord:
    tags = (pier.tag,)
    area = pier.gross_area_in2
    ratio = pier.height_in / pier.diameter_in if pier.diameter_in else float("inf")
    is_pedestal = ratio <= PEDESTAL_HEIGHT_RATIO

    # ACI 318 §14.5.4 (§22.6.5.2 in 318-11), the same expression `retaining_system` uses on
    # the court's strut and with the same phi. Reported for BOTH branches: for a pedestal it
    # is the governing capacity, and for a column it is the number that says the section is
    # nowhere near the reason this record is incomplete.
    slenderness = max(1.0 - (pier.height_in / (32.0 * pier.diameter_in)) ** 2, 0.0)
    plain_capacity = 0.60 * 0.45 * PRESUMPTIVE_FC_PSI * area * slenderness
    demand = pier.factored_lb
    minimum_steel = COLUMN_MIN_REINFORCEMENT_RATIO * area

    states = (
        LimitState("axial, gross section", demand, plain_capacity, "lb",
                   f"ACI 318 §14.5.4 at 0.45 f'c, phi 0.60 — f'c {PRESUMPTIVE_FC_PSI:,.0f} "
                   f"psi, slenderness factor {slenderness:.2f}"),
    )
    inputs = (
        Quantity("column_diameter", pier.diameter_in, "in", 0.5),
        Quantity("column_height", pier.height_in, "in", 0.01),
        Quantity("gross_area", area, "in2", 0.1),
        Quantity("tributary_area", pier.tributary_ft2, "ft2", 0.01),
        Quantity("carried_dead", pier.carried_dead_lb, "lb", 1.0),
        Quantity("dead_load", pier.dead_lb, "lb", 1.0),
        Quantity("live_load", pier.live_lb, "lb", 1.0),
        Quantity("fc", PRESUMPTIVE_FC_PSI, "psi", 1.0),
    )
    shape = "round" if pier.round_section else "square"
    notes = (
        f"IRC R507.4 tabulates maximum heights for SAWN LUMBER deck posts (4x4, 6x6). A "
        f"{pier.diameter_in:.0f}\" {shape} cast concrete column has no row in it, which is "
        f"why this is an engineered item and not a gap in the table.",
        f"Height / least lateral dimension = {ratio:.1f}. ACI 318-19 §2.3 / §14.3.3.1 call a "
        f"member a PEDESTAL at {PEDESTAL_HEIGHT_RATIO:.0f} or less and §14.1.3(d) permits it "
        f"to be plain concrete; past that it is a COLUMN, and §14.1.5 does not permit a plain "
        f"one at any stress.",
        "§14.1.2 excludes cast-in-place piles and piers EMBEDDED IN GROUND from that chapter, "
        "and a reviewer may reach for it here. It does not reach: the bell is embedded and "
        "the shaft above it stands free in an open court for its whole height.",
        f"Demand {demand:,.0f} lb factored (1.2D + 1.6L) against {plain_capacity:,.0f} lb "
        f"on the gross section: d/c {demand / plain_capacity:.3f} if the section alone "
        f"could be relied on. **The concrete is not the problem here.**",
        f"A column of this size takes at least {minimum_steel:.2f} in2 of longitudinal steel "
        f"(ACI 318-19 §10.6.1.1, 0.01Ag, and not more than 0.08Ag), plus ties. Sizing it is "
        f"the engineer's, and this engine has nowhere to record the answer.",
        "SCREENING: axial only. No moment from the beams' eccentricity, no lateral load on "
        "the shaft, no slenderness amplification beyond the plain-concrete bracket above, "
        "and no fire or durability case.",
    )

    if is_pedestal:
        over = any(not state.ok for state in states)
        return EngineeringRecord(
            item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS,
            status=Status.OVER if over else Status.OK,
            summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} PEDESTAL "
                     f"(h/d {ratio:.1f}) at d/c {demand / plain_capacity:.2f} on the plain "
                     f"section, which ACI 318 permits at this proportion"),
            inputs=inputs, limit_states=states, notes=notes, element_tags=tags)

    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} cast COLUMN (h/d "
                 f"{ratio:.1f}, past a pedestal's {PEDESTAL_HEIGHT_RATIO:.0f}) carrying "
                 f"{demand:,.0f} lb — the section is at d/c "
                 f"{demand / plain_capacity:.2f} and the reinforcement is unstated"),
        inputs=inputs, limit_states=states,
        missing=(f"the vertical reinforcement in {pier.tag} — ACI 318-19 §14.1.5 does not "
                 f"permit a plain concrete COLUMN at any stress, and `Post` carries no field in "
                 f"which a house could state one. At least "
                 f"{minimum_steel:.2f} in2 (1% of gross) plus ties, sized by the engineer",),
        notes=notes, element_tags=tags)
