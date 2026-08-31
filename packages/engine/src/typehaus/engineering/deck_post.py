"""A round cast-concrete column carrying a deck — ``deck_post/<Post tag>``.

IRC R507.4 publishes maximum heights for **sawn lumber** deck posts, 4x4 and 6x6. There is
no row for a 12" or 20" round cast column and there never will be, which is why these are
engineered items rather than a gap in the table.

**What this module grades is the CAGE, not the section.** The catlin columns run at about a
twenty-fifth of their axial capacity, and no plausible edit to the concrete changes that.
What decides whether a cast column is legal at all is ACI 318-19 §14.1.5 — a plain concrete
COLUMN is not permitted at any stress — and after that a short list of detailing limits that
are functions of the gross area and the bar sizes rather than of the load: §10.6.1.1's 1%
floor and 8% ceiling, §10.7.3.1's four-bar minimum within circular ties, and §25.7.2's tie
size and spacing. Those are the comparisons below, and on these two piers every one of them
binds harder than the axial check does.

A column whose ``Post.vertical_reinforcement`` is unset is still **INCOMPLETE naming that
field** — #32's rule, and the reason the field was added. A *pedestal* (h/d <= 3) is a
different member: §14.1.3(d) permits it to be plain, so it is graded on §14.5.4 instead.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md`` §4, hand-worked in a separate pass;
``tests/test_pier_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.retaining_basis import (
    _BAR,
    PRESUMPTIVE_FC_PSI,
    REINFORCEMENT_FY_PSI,
)

KIND = "deck_post"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint. Bumped to "2"
#: on 2026-08-30, when ``Post.vertical_reinforcement`` arrived and this module stopped
#: reporting a bare INCOMPLETE and started grading a reinforced column.
BASIS_VERSION = "2"
BASIS = "IRC R507.4 (no row); ACI 318-19 Ch. 10, 22.4, 25.7 (reinforced) / 14.5 (plain)"

#: ACI 318-19 §2.3 defines a PEDESTAL as a member with a ratio of height to least lateral
#: dimension not exceeding 3; §14.3.3.1 states the same as a design limit. Plain concrete
#: pedestals are permitted (§14.1.3(d)); **plain concrete COLUMNS are not** — §14.1.5, "plain
#: concrete shall not be permitted for columns and pile caps", and R14.1.5 gives the reason:
#: a column lacks the ductility it should have, and a random crack in an unreinforced one
#: endangers its structural integrity. (§22.2.1 in ACI 318-11, whose closing sentence carries
#: the same prohibition.) So the ratio is not trivia — it decides which chapter applies.
PEDESTAL_HEIGHT_RATIO = 3.0

#: ACI 318-19 §10.6.1.1: "area of longitudinal reinforcement shall be at least 0.01Ag but
#: shall not exceed 0.08Ag" (§10.9.1 in 318-11). The floor is NOT a strength requirement —
#: it covers creep, shrinkage and the accidental moment no analysis names — which is why a
#: column at d/c 0.04 does not get to carry less than it.
COLUMN_MIN_REINFORCEMENT_RATIO = 0.01
COLUMN_MAX_REINFORCEMENT_RATIO = 0.08

#: ACI 318-19 §10.7.3.1(b): the minimum number of longitudinal bars is "four within
#: rectangular or circular ties". Six is §10.7.3.1(c)'s SPIRAL case and three is (a)'s
#: triangular-tie case; the three get confused constantly, and neither catlin pier is
#: spirally reinforced.
MIN_BARS_IN_CIRCULAR_TIES = 4

#: ACI 318-19 Table 22.4.2.1: ``alpha`` = 0.80 for a tied column, 0.85 for a spiral one, on
#: ``Pn,max = alpha * Po``. **It is not a safety factor, it is an eccentricity.** R22.4.2
#: records that these caps replaced the explicit minimum-eccentricity design ACI 318-71
#: carried, and that they correspond to e = 0.10h (tied) and 0.05h (spiral) — which is what
#: ``_slenderness`` below spends.
TIED_AXIAL_CAP = 0.80
TIED_EMBEDDED_ECCENTRICITY_RATIO = 0.10

#: ACI 318-19 Table 21.2.2, compression-controlled with ties (0.75 with spirals).
PHI_COMPRESSION_TIED = 0.65

#: ACI 318-19 §6.2.5. Slenderness may be neglected in a NON-SWAY frame below
#: ``34 + 12(M1/M2)``, capped at 40; 34 is that expression's conservative floor and is what
#: is used here, which sidesteps the sign convention on M1/M2 entirely. The SWAY limit is 22,
#: and it is the one that would apply if the leaning-column assumption below failed.
NONSWAY_SLENDERNESS_FLOOR = 34.0
SWAY_SLENDERNESS_LIMIT = 22.0

#: ACI 318-19 §25.7.2.1 — ties are #3 for longitudinal bars #10 and smaller, #4 above that.
_TIE_BAR_FOR_SMALL_LONGITUDINAL = 3
_LARGEST_LONGITUDINAL_TAKING_A_NUMBER_3_TIE = 10


@dataclass(frozen=True)
class _Cage:
    """A parsed column cage: ``(4) #5 vertical, #3 ties @ 10" o.c.``"""

    count: int
    bar: int
    tie_bar: int
    tie_spacing_in: float

    @property
    def area_in2(self) -> float:
        return self.count * _BAR[self.bar][0]

    @property
    def bar_diameter_in(self) -> float:
        return _BAR[self.bar][1]

    @property
    def tie_diameter_in(self) -> float:
        return _BAR[self.tie_bar][1]


def parse_cage(spec: str | None) -> _Cage | None:
    """``'(4) #5 vertical, #3 ties @ 10" o.c.'`` -> ``_Cage(4, 5, 3, 10.0)``.

    Deliberately strict about the four things that carry meaning — bar count, bar size, tie
    size and tie spacing — and indifferent to everything around them, because the field is
    free text a house authors for a drawing. **A string this cannot read is reported as NO
    steel**, the conservative reading and the same contract
    ``retaining_basis.parse_reinforcement`` keeps for a wall.

    The wall's spec is a SPACING and this one is a COUNT, which is not an inconsistency: ACI
    bounds a column's steel by ``0.01Ag`` and its bar count by four, and neither question can
    be asked of a spacing.
    """
    if not spec:
        return None
    text = spec.strip()
    # Longitudinal: "(4) #5", "4-#5", "4 #5". The tie group is excluded by requiring the
    # count to precede the bar, which "#3 ties" never does.
    longitudinal = re.search(r"\(?\s*(\d+)\s*\)?\s*[-x]?\s*#\s*(\d+)", text)
    ties = re.search(r"#\s*(\d+)\s*(?:ties?|hoops?|stirrups?)\D*?@\s*([0-9]+(?:\.[0-9]+)?)",
                     text, re.IGNORECASE)
    if longitudinal is None or ties is None:
        return None
    count, bar = int(longitudinal.group(1)), int(longitudinal.group(2))
    tie_bar, spacing_in = int(ties.group(1)), float(ties.group(2))
    if bar not in _BAR or tie_bar not in _BAR or count <= 0 or spacing_in <= 0.0:
        return None
    return _Cage(count=count, bar=bar, tie_bar=tie_bar, tie_spacing_in=spacing_in)


def _slenderness(pier: _Pier) -> tuple[float, float, float, float]:
    """``(k*lu/r, delta_ns, magnified e_min, the e the axial cap already embeds)`` in inches.

    ``k`` = 1.0, because these are **leaning columns**: ``structural.lateral_racking`` reports
    both catlin piers as carrying no knee brace, with every pound of storey shear handed to
    the braced bays. A leaning column is designed non-sway for its own load and sheds its
    P-delta to the bays that brace it — and that hand-off is a diaphragm claim the racking
    check already reports as UNKNOWN, which is where it belongs. **If that claim fails these
    are cantilevers, k is 2.0, and the governing threshold is 22 rather than 34.**
    """
    radius_of_gyration = pier.diameter_in / 4.0          # d/4 for a circular section
    slenderness = pier.height_in / radius_of_gyration    # k = 1.0
    # ACI 318-19 §6.6.4.4.4(a) EI = 0.4 Ec Ig / (1 + beta_dns), §6.6.4.5.2 delta_ns.
    modulus = 57_000.0 * math.sqrt(PRESUMPTIVE_FC_PSI)
    inertia = math.pi * pier.diameter_in ** 4 / 64.0
    sustained = (1.2 * pier.dead_lb / pier.factored_lb) if pier.factored_lb else 0.0
    stiffness = 0.4 * modulus * inertia / (1.0 + sustained)
    critical = math.pi ** 2 * stiffness / pier.height_in ** 2
    magnifier = max(1.0 / (1.0 - pier.factored_lb / (0.75 * critical)), 1.0)
    # §6.6.4.5.4's minimum moment, as the eccentricity it is: M2,min = Pu (0.6 + 0.03h).
    minimum_eccentricity = 0.6 + 0.03 * pier.diameter_in
    return (slenderness, magnifier, minimum_eccentricity * magnifier,
            TIED_EMBEDDED_ECCENTRICITY_RATIO * pier.diameter_in)


@keys(KIND)
def enumerate_posts(ctx: EngineeringContext) -> list[str]:
    return [pier.tag for pier in cast_piers(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(pier) for pier in cast_piers(ctx)]


def _one(pier: _Pier) -> EngineeringRecord:
    area = pier.gross_area_in2
    ratio = pier.height_in / pier.diameter_in if pier.diameter_in else float("inf")
    is_pedestal = ratio <= PEDESTAL_HEIGHT_RATIO
    cage = parse_cage(pier.vertical_reinforcement)
    demand = pier.factored_lb
    minimum_steel = COLUMN_MIN_REINFORCEMENT_RATIO * area
    shape = "round" if pier.round_section else "square"

    common = (
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
    )

    if is_pedestal and cage is None:
        return _plain_pedestal(pier, area, ratio, shape, demand, common)
    if cage is None:
        return _unreinforced_column(pier, area, ratio, shape, demand, minimum_steel, common)
    return _reinforced_column(pier, area, ratio, shape, demand, minimum_steel, cage, common)


def _capacity(area_in2: float, steel_in2: float) -> float:
    """``phi * alpha * Po`` — ACI 318-19 §22.4.2.1 with Eq. 22.4.2.2."""
    squash = 0.85 * PRESUMPTIVE_FC_PSI * (area_in2 - steel_in2) + REINFORCEMENT_FY_PSI * steel_in2
    return PHI_COMPRESSION_TIED * TIED_AXIAL_CAP * squash


def _reinforced_column(pier: _Pier, area: float, ratio: float, shape: str, demand: float,
                       minimum_steel: float, cage: _Cage,
                       common: tuple[str, ...]) -> EngineeringRecord:
    """The cage is stated: grade it, and grade the four detailing limits around it."""
    steel = cage.area_in2
    capacity = _capacity(area, steel)
    slenderness, magnifier, eccentricity, embedded = _slenderness(pier)
    # §25.7.2.2 — the least of 16 longitudinal diameters, 48 tie diameters, and the column's
    # own least dimension.
    tie_limit = min(16.0 * cage.bar_diameter_in, 48.0 * cage.tie_diameter_in, pier.diameter_in)
    required_tie = (_TIE_BAR_FOR_SMALL_LONGITUDINAL
                    if cage.bar <= _LARGEST_LONGITUDINAL_TAKING_A_NUMBER_3_TIE else 4)

    states = (
        LimitState("axial, tied column", demand, capacity, "lb",
                   f"ACI 318-19 §22.4.2.1 Pn,max = {TIED_AXIAL_CAP:.2f} Po, phi "
                   f"{PHI_COMPRESSION_TIED:.2f} (Table 21.2.2) — f'c "
                   f"{PRESUMPTIVE_FC_PSI:,.0f} psi, fy {REINFORCEMENT_FY_PSI:,.0f} psi"),
        LimitState("longitudinal steel", minimum_steel, steel, "in2",
                   f"ACI 318-19 §10.6.1.1 minimum {COLUMN_MIN_REINFORCEMENT_RATIO:.2f} Ag"),
        LimitState("steel ratio ceiling", steel, COLUMN_MAX_REINFORCEMENT_RATIO * area, "in2",
                   f"ACI 318-19 §10.6.1.1 maximum {COLUMN_MAX_REINFORCEMENT_RATIO:.2f} Ag"),
        LimitState("bar count", float(MIN_BARS_IN_CIRCULAR_TIES), float(cage.count), "bars",
                   "ACI 318-19 §10.7.3.1(b), four within rectangular or circular ties"),
        LimitState("tie size", float(required_tie), float(cage.tie_bar), "bar no.",
                   "ACI 318-19 §25.7.2.1 — #3 for longitudinal bars #10 and smaller"),
        LimitState("tie spacing", cage.tie_spacing_in, tie_limit, "in",
                   f"ACI 318-19 §25.7.2.2, least of 16db ({16.0 * cage.bar_diameter_in:.1f}\"), "
                   f"48dt ({48.0 * cage.tie_diameter_in:.1f}\"), h ({pier.diameter_in:.1f}\")"),
        LimitState("minimum eccentricity", eccentricity, embedded, "in",
                   f"ACI 318-19 §6.6.4.5.4 e_min magnified by §6.6.4.5.2 delta_ns "
                   f"{magnifier:.3f}, against the {TIED_EMBEDDED_ECCENTRICITY_RATIO:.2f}h "
                   f"R22.4.2 says the {TIED_AXIAL_CAP:.2f} cap already carries"),
    )
    over = any(not state.ok for state in states)
    notes = common + (
        f"CAGE: {pier.vertical_reinforcement} — As {steel:.2f} in2, rho "
        f"{100.0 * steel / area:.3f}%, against the {minimum_steel:.3f} in2 that "
        f"{COLUMN_MIN_REINFORCEMENT_RATIO:.2f} Ag requires. This is the MINIMUM cage the Code "
        f"permits, not a chosen margin.",
        f"Demand {demand:,.0f} lb factored (1.2D + 1.6L) against {capacity:,.0f} lb: d/c "
        f"{demand / capacity:.3f}. **The section is not what governs here** — every detailing "
        f"limit above binds harder than this comparison does, and the 1% steel floor is not a "
        f"strength requirement but a creep, shrinkage and accidental-moment one.",
        f"SLENDERNESS: k*lu/r = {slenderness:.1f} against §6.2.5's non-sway floor of "
        f"{NONSWAY_SLENDERNESS_FLOOR:.0f} — "
        + ("NOT neglectable, so delta_ns is computed above"
           if slenderness > NONSWAY_SLENDERNESS_FLOOR else "neglectable outright")
        + f". k is 1.0 on the LEANING-COLUMN assumption: `structural.lateral_racking` gives "
          f"this post's storey shear to the braced bays on a diaphragm claim it reports as "
          f"UNKNOWN. If that claim fails, k is 2.0 and the threshold is "
          f"{SWAY_SLENDERNESS_LIMIT:.0f}.",
        "SCREENING: no bending from the beams' eccentric landing beyond the Code minimum "
        "above, no wind or seismic moment in the shaft, and no development, splice or cover "
        "detail. A stamped design is what turns this into a finished column.",
    )
    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} tied COLUMN (h/d "
                 f"{ratio:.1f}) with {pier.vertical_reinforcement} — rho "
                 f"{100.0 * steel / area:.2f}% against ACI 318-19 §10.6.1.1's 1% floor, at "
                 f"d/c {demand / capacity:.2f} on the §22.4.2 axial cap"),
        inputs=_inputs(pier, area, steel, cage), limit_states=states, notes=notes,
        element_tags=(pier.tag,))


def _unreinforced_column(pier: _Pier, area: float, ratio: float, shape: str, demand: float,
                         minimum_steel: float, common: tuple[str, ...]) -> EngineeringRecord:
    """No cage on a member ACI will not let be plain. #32's rule: say so, never guess."""
    plain = _plain_capacity(pier, area)
    states = (
        LimitState("axial, gross section", demand, plain, "lb",
                   f"ACI 318-19 §14.5.4 at 0.45 f'c, phi 0.60 — reported to show the section "
                   f"is not what is missing; f'c {PRESUMPTIVE_FC_PSI:,.0f} psi"),
    )
    reason = (f"the vertical reinforcement in {pier.tag} — ACI 318-19 §14.1.5 does not permit "
              f"a plain concrete COLUMN at any stress. Author `Post.vertical_reinforcement`, "
              f"e.g. '(4) #5 vertical, #3 ties @ 10\" o.c.'; at least {minimum_steel:.2f} in2 "
              f"(1% of gross) over at least {MIN_BARS_IN_CIRCULAR_TIES} bars, sized by the "
              f"engineer")
    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} cast COLUMN (h/d "
                 f"{ratio:.1f}, past a pedestal's {PEDESTAL_HEIGHT_RATIO:.0f}) carrying "
                 f"{demand:,.0f} lb — the plain section is at d/c {demand / plain:.2f} and "
                 f"the reinforcement is unstated"),
        inputs=_inputs(pier, area, 0.0, None), limit_states=states, missing=(reason,),
        notes=common + (
            f"A column of this size takes at least {minimum_steel:.2f} in2 of longitudinal "
            f"steel (ACI 318-19 §10.6.1.1, 0.01Ag, and not more than 0.08Ag), plus ties.",
            "The plain-section number above is reported so nobody reads this INCOMPLETE as "
            "'the column might be too small'. It is not; it has no bars.",
        ), element_tags=(pier.tag,))


def _plain_pedestal(pier: _Pier, area: float, ratio: float, shape: str, demand: float,
                    common: tuple[str, ...]) -> EngineeringRecord:
    """h/d <= 3, so §14.1.3(d) permits plain concrete and §14.5.4 is the capacity."""
    plain = _plain_capacity(pier, area)
    states = (
        LimitState("axial, gross section", demand, plain, "lb",
                   f"ACI 318-19 §14.5.4 at 0.45 f'c, phi 0.60 — f'c "
                   f"{PRESUMPTIVE_FC_PSI:,.0f} psi"),
    )
    over = any(not state.ok for state in states)
    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} PEDESTAL (h/d {ratio:.1f}) "
                 f"at d/c {demand / plain:.2f} on the plain section, which ACI 318-19 "
                 f"§14.1.3(d) permits at this proportion"),
        inputs=_inputs(pier, area, 0.0, None), limit_states=states,
        notes=common + ("SCREENING: axial only, no moment and no lateral case.",),
        element_tags=(pier.tag,))


def _plain_capacity(pier: _Pier, area: float) -> float:
    """ACI 318-19 §14.5.4 (§22.6.5.2 in 318-11), the expression ``retaining_system`` uses on
    the court's strut and with the same phi."""
    slenderness = max(1.0 - (pier.height_in / (32.0 * pier.diameter_in)) ** 2, 0.0)
    return 0.60 * 0.45 * PRESUMPTIVE_FC_PSI * area * slenderness


def _inputs(pier: _Pier, area: float, steel: float, cage: _Cage | None) -> tuple[Quantity, ...]:
    base = (
        Quantity("column_diameter", pier.diameter_in, "in", 0.5),
        Quantity("column_height", pier.height_in, "in", 0.01),
        Quantity("gross_area", area, "in2", 0.1),
        Quantity("tributary_area", pier.tributary_ft2, "ft2", 0.01),
        Quantity("carried_dead", pier.carried_dead_lb, "lb", 1.0),
        Quantity("dead_load", pier.dead_lb, "lb", 1.0),
        Quantity("live_load", pier.live_lb, "lb", 1.0),
        Quantity("fc", PRESUMPTIVE_FC_PSI, "psi", 1.0),
    )
    if cage is None:
        return base
    return base + (
        Quantity("longitudinal_steel", steel, "in2", 0.01),
        Quantity("bar_count", float(cage.count), "bars", None),
        Quantity("bar_number", float(cage.bar), "bar no.", None),
        Quantity("tie_number", float(cage.tie_bar), "bar no.", None),
        Quantity("tie_spacing", cage.tie_spacing_in, "in", 0.25),
        Quantity("fy", REINFORCEMENT_FY_PSI, "psi", 1.0),
    )
