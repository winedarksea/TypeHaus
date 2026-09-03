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
#: when ``Post.vertical_reinforcement`` arrived and this module stopped
#: reporting a bare INCOMPLETE and started grading a reinforced column; to "3" when
#: ``_detailing_only`` arrived and a pier whose axial demand the model cannot state stopped
#: publishing a d/c against an under-count and started publishing the six detailing limits
#: with the axial one named as missing; to "4" when ``_moment_column`` arrived and a column
#: that IS a deck's lateral system started being graded in BENDING at its base.
BASIS_VERSION = "4"
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
        "§14.1.2 excludes cast-in-place piles and piers EMBEDDED IN GROUND from that "
        "chapter, and a reviewer may reach for it here. The exclusion is for a shaft "
        "laterally supported by soil over its WHOLE height; every pier graded in this "
        "module stands free above grade for part of its own, so it is a column and is "
        "graded as one. Check that against the section before citing the exclusion.",
    )

    if is_pedestal and cage is None:
        return _plain_pedestal(pier, area, ratio, shape, demand, common)
    if cage is None:
        return _unreinforced_column(pier, area, ratio, shape, demand, minimum_steel, common)
    if pier.lateral_system and cage is not None and not pier.unmodelled_load:
        return _moment_column(pier, area, ratio, shape, demand, minimum_steel, cage, common)
    if pier.unmodelled_load:
        # The demand is an under-count and this module knows by how little it can say.
        # Grading the six LOAD-INDEPENDENT detailing limits is real work and is published;
        # the axial comparison is not, and is left out rather than printed against a number
        # the model cannot make. See ``_detailing_only``.
        return _detailing_only(pier, area, ratio, shape, minimum_steel, cage, common)
    return _reinforced_column(pier, area, ratio, shape, demand, minimum_steel, cage, common)


def _capacity(area_in2: float, steel_in2: float) -> float:
    """``phi * alpha * Po`` — ACI 318-19 §22.4.2.1 with Eq. 22.4.2.2."""
    squash = 0.85 * PRESUMPTIVE_FC_PSI * (area_in2 - steel_in2) + REINFORCEMENT_FY_PSI * steel_in2
    return PHI_COMPRESSION_TIED * TIED_AXIAL_CAP * squash


def _detailing_states(pier: _Pier, area: float, minimum_steel: float,
                      cage: _Cage) -> tuple[LimitState, ...]:
    """The six limit states that DO NOT read the load — every one of ACI's detailing rules.

    Separated because they are exactly what stays gradeable when the demand is unknown. A
    1% steel floor, a four-bar minimum, a tie size and a tie pitch are properties of the
    section and the cage; none of them moves when a load the model cannot see is added.
    """
    _slender, magnifier, eccentricity, embedded = _slenderness(pier)
    steel = cage.area_in2
    # §25.7.2.2 — the least of 16 longitudinal diameters, 48 tie diameters, and the column's
    # own least dimension.
    tie_limit = min(16.0 * cage.bar_diameter_in, 48.0 * cage.tie_diameter_in, pier.diameter_in)
    required_tie = (_TIE_BAR_FOR_SMALL_LONGITUDINAL
                    if cage.bar <= _LARGEST_LONGITUDINAL_TAKING_A_NUMBER_3_TIE else 4)
    return (
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



# --- flexure, for a column that is somebody's lateral system ------------------------------

#: ACI 318-19 Table 22.2.2.4.3 — the equivalent rectangular stress block depth factor.
#: 0.85 to 4,000 psi, then 0.05 off per 1,000 psi, floored at 0.65.
def _beta_1(fc_psi: float) -> float:
    return min(0.85, max(0.65, 0.85 - 0.05 * (fc_psi - 4000.0) / 1000.0))


#: ACI 318-19 §20.2.2.2 — the modulus of elasticity of non-prestressed bars.
STEEL_MODULUS_PSI = 29_000_000.0
#: ACI 318-19 §22.2.2.1 — the concrete strain at the extreme compression fibre at nominal.
CONCRETE_ULTIMATE_STRAIN = 0.003
#: ACI 318-19 Table 21.2.2 — phi runs 0.65 (compression-controlled) to 0.90
#: (tension-controlled) between the compression-controlled strain limit and
#: ``epsilon_ty + 0.003``. For Grade 60, ``epsilon_ty`` is 60/29,000 = 0.00207.
PHI_TENSION_CONTROLLED = 0.90

#: ACI 318-19 §6.2.5 / §6.6.4.4.4 — the effective length factor for a column FIXED at its
#: base and free at its top. Theoretically 2.0; §R6.2.5's Table R6.2.5 recommends 2.1 for
#: the real, non-ideal fixity a doweled lap into a wall provides, and 2.1 is what is used.
CANTILEVER_EFFECTIVE_LENGTH_FACTOR = 2.1


def _segment(radius_in: float, depth_in: float) -> tuple[float, float]:
    """A circular segment of height ``depth_in`` measured down from the top of the circle.

    Returns ``(area in2, centroid above the circle's centre in inches)``. This is the
    compression block on a round column: ACI's stress block is rectangular in DEPTH, not in
    plan, so on a circle it cuts a segment rather than a rectangle, and using ``b*a`` with
    any single width is the classic way to get a round column's Mn wrong.
    """
    if depth_in <= 0.0:
        return (0.0, 0.0)
    if depth_in >= 2.0 * radius_in:
        return (math.pi * radius_in ** 2, 0.0)
    offset = radius_in - depth_in                       # chord's distance above the centre
    half_chord2 = max(radius_in ** 2 - offset ** 2, 0.0)
    area = radius_in ** 2 * math.acos(offset / radius_in) - offset * math.sqrt(half_chord2)
    if area <= 0.0:
        return (0.0, 0.0)
    centroid = (2.0 / 3.0) * half_chord2 ** 1.5 / area
    return (area, centroid)


def _bar_offsets(pier: _Pier, cage: _Cage, cover_in: float) -> tuple[float, ...]:
    """Each bar's distance ABOVE the section centre, along the bending axis.

    The cage is laid out evenly around a bar circle whose radius is the column radius less
    the cover, the tie and half a bar. The layout is then ROTATED so that no bar sits on the
    extreme compression or tension fibre — for four bars that puts them at +/-45 degrees,
    which is the WEAK orientation of a four-bar cage and about 8% below the strong one. It
    is taken deliberately: a round column is built in a round tube and nothing on site
    orients the cage to the wind.
    """
    radius = pier.diameter_in / 2.0 - cover_in - cage.tie_diameter_in - cage.bar_diameter_in / 2.0
    radius = max(radius, 0.0)
    step = 2.0 * math.pi / cage.count
    start = step / 2.0
    return tuple(radius * math.cos(start + index * step) for index in range(cage.count))


def _phi(strain: float) -> float:
    """ACI 318-19 Table 21.2.2, the transition on the extreme tension bar's strain."""
    yield_strain = REINFORCEMENT_FY_PSI / STEEL_MODULUS_PSI
    if strain <= yield_strain:
        return PHI_COMPRESSION_TIED
    if strain >= yield_strain + 0.003:
        return PHI_TENSION_CONTROLLED
    span = PHI_TENSION_CONTROLLED - PHI_COMPRESSION_TIED
    return PHI_COMPRESSION_TIED + span * (strain - yield_strain) / 0.003


def _pm_point(pier: _Pier, cage: _Cage, cover_in: float,
              axial_lb: float) -> tuple[float, float, float]:
    """``(phi*Mn in lb-ft, phi, the neutral-axis depth c in inches)`` at a given ``Pu``.

    Straight strain compatibility on the round section: bisect the neutral-axis depth until
    ``phi*Pn`` equals the factored axial load, then report ``phi*Mn`` at that same ``c``.
    That is the point on the P-M interaction diagram the column is actually being asked to
    reach, rather than the pure-flexure intercept — which on a column carrying any axial
    load at all is the conservative answer by a wide margin, since axial compression
    *increases* a lightly loaded column's moment capacity up to the balance point.
    """
    radius = pier.diameter_in / 2.0
    beta = _beta_1(PRESUMPTIVE_FC_PSI)
    offsets = _bar_offsets(pier, cage, cover_in)
    bar_area = _BAR[cage.bar][0]

    def state(c: float) -> tuple[float, float, float]:
        area, centroid = _segment(radius, min(beta * c, 2.0 * radius))
        force = 0.85 * PRESUMPTIVE_FC_PSI * area
        moment = force * centroid
        worst_tension = 0.0
        for offset in offsets:
            depth = radius - offset                      # from the extreme compression fibre
            strain = CONCRETE_ULTIMATE_STRAIN * (c - depth) / c
            stress = max(-REINFORCEMENT_FY_PSI,
                         min(REINFORCEMENT_FY_PSI, STEEL_MODULUS_PSI * strain))
            # A bar inside the stress block displaces concrete that is already counted.
            if depth <= beta * c:
                stress -= 0.85 * PRESUMPTIVE_FC_PSI
            force += stress * bar_area
            moment += stress * bar_area * offset
            worst_tension = min(worst_tension, strain)
        return (force, moment, -worst_tension)

    low, high = 0.05 * pier.diameter_in, 4.0 * pier.diameter_in
    for _ in range(80):
        mid = 0.5 * (low + high)
        force, _moment, tension = state(mid)
        if _phi(tension) * force < axial_lb:
            low = mid
        else:
            high = mid
    c = 0.5 * (low + high)
    _force, moment, tension = state(c)
    phi = _phi(tension)
    return (phi * moment / 12.0, phi, c)


def _sway_magnifier(pier: _Pier, axial_lb: float) -> tuple[float, float]:
    """``(k*lu/r, delta)`` for a cantilever column, ACI 318-19 §6.6.4.

    ``k`` is ``CANTILEVER_EFFECTIVE_LENGTH_FACTOR``, not ``_slenderness``'s 1.0, and the
    difference is the whole point of this record: ``_slenderness`` designs a LEANING column
    that sheds its P-delta to a braced bay, and this column has no braced bay to shed it to.
    The threshold it is measured against is §6.2.5's SWAY limit of 22, not the non-sway 34.
    """
    radius_of_gyration = pier.diameter_in / 4.0
    slenderness = CANTILEVER_EFFECTIVE_LENGTH_FACTOR * pier.height_in / radius_of_gyration
    modulus = 57_000.0 * math.sqrt(PRESUMPTIVE_FC_PSI)
    inertia = math.pi * pier.diameter_in ** 4 / 64.0
    sustained = (1.2 * pier.dead_lb / pier.factored_lb) if pier.factored_lb else 0.0
    stiffness = 0.4 * modulus * inertia / (1.0 + sustained)
    effective = CANTILEVER_EFFECTIVE_LENGTH_FACTOR * pier.height_in
    critical = math.pi ** 2 * stiffness / effective ** 2
    magnifier = max(1.0 / (1.0 - axial_lb / (0.75 * critical)), 1.0) if critical > 0 else 1.0
    return (slenderness, magnifier)


def _class_b_lap_in(cage: _Cage) -> float:
    """ACI 318-19 §25.4.2.4 development, §25.5.2.1 class B splice, for a #6 or smaller bar.

    ``ld = (fy psi_t psi_e psi_s / (25 lambda sqrt(f'c))) db`` with every factor 1.0 —
    bottom-cast (psi_t 1.0), UNCOATED (psi_e 1.0), and see below, normalweight (lambda 1.0).
    A class B lap is 1.3 ld, and every bar at a column base is spliced at the same section,
    which is what makes it class B rather than class A.

    **psi_e is 1.0 even though these bars are galvanized**, and that is not an oversight:
    ACI 318-19's coating factor is written for EPOXY, and §25.4.2.5's zinc-coated (galvanized)
    reinforcement row carries psi_e = 1.0. Zinc does not debond the way epoxy does.
    """
    length = (REINFORCEMENT_FY_PSI / (25.0 * math.sqrt(PRESUMPTIVE_FC_PSI))) \
        * cage.bar_diameter_in
    return 1.3 * length


def _moment_column(pier: _Pier, area: float, ratio: float, shape: str, demand: float,
                   minimum_steel: float, cage: _Cage,
                   common: tuple[str, ...]) -> EngineeringRecord:
    """A cast column that IS its deck's lateral system: graded in BENDING as well as axially.

    Every other record in this module grades a leaning column — one whose storey shear goes
    somewhere else, so the section only ever sees axial load and ACI's minimum eccentricity.
    This one has nowhere to send it. ``pier_basis._base_moments`` derives what arrives at the
    base (wind on the deck at the Fig. 29.3-1 Case A/B ceiling, and the R301.5 guard load
    taken wholly on one column), and the section is checked against the P-M interaction
    point at its own factored axial load rather than against the axial cap alone.

    The six detailing limits are unchanged and still published: a bending column is subject
    to every one of them and to more besides.

    **Oracle.** ``houses/catlin/notes/balcony_moment_columns.md``, hand-worked in a separate
    pass; ``tests/test_pier_calcs.py`` reproduces it.
    """
    steel = cage.area_in2
    capacity = _capacity(area, steel)
    cover_in = _authored_cover_in(pier.vertical_reinforcement)
    phi_mn, phi, neutral_axis = _pm_point(pier, cage, cover_in, demand)
    slenderness, magnifier = _sway_magnifier(pier, demand)
    governing = max(pier.wind_base_moment_lb_ft, pier.guard_base_moment_lb_ft)
    lap = _class_b_lap_in(cage)

    states = (
        LimitState("axial, tied column", demand, capacity, "lb",
                   f"ACI 318-19 §22.4.2.1 Pn,max = {TIED_AXIAL_CAP:.2f} Po, phi "
                   f"{PHI_COMPRESSION_TIED:.2f} (Table 21.2.2) — f'c "
                   f"{PRESUMPTIVE_FC_PSI:,.0f} psi, fy {REINFORCEMENT_FY_PSI:,.0f} psi"),
        LimitState("bending at base, wind", pier.wind_base_moment_lb_ft, phi_mn, "lb-ft",
                   f"ACI 318-19 §22.4 P-M interaction at Pu {demand:,.0f} lb, phi "
                   f"{phi:.2f}, c {neutral_axis:.2f}\" — ASCE 7-16 §29.3 storey shear at "
                   f"0.6W (§2.4.1)"),
        LimitState("bending at base, guard", pier.guard_base_moment_lb_ft, phi_mn, "lb-ft",
                   "IRC R301.5 — a 200 lb concentrated load in any direction at the top of "
                   "the guard, taken wholly on this column rather than shared"),
        LimitState("magnified moment (sway)", governing * magnifier, phi_mn, "lb-ft",
                   f"ACI 318-19 §6.6.4.5.2 delta {magnifier:.3f} at k "
                   f"{CANTILEVER_EFFECTIVE_LENGTH_FACTOR:.1f}, k*lu/r {slenderness:.0f} "
                   f"against §6.2.5's SWAY limit of {SWAY_SLENDERNESS_LIMIT:.0f}"),
        LimitState("dowel lap, class B", lap, pier.height_in, "in",
                   "ACI 318-19 §25.4.2.4 development x §25.5.2.1's 1.3 for a class B "
                   "splice with every bar spliced at one section; graded against the "
                   "column's own height, which is the only bound this model holds on how "
                   "much lap can physically exist. The AUTHORED lap is in the assembly's "
                   "source and on the drawing"),
        *_detailing_states(pier, area, minimum_steel, cage),
    )
    over = any(not state.ok for state in states)
    which = "the guard load" if pier.guard_base_moment_lb_ft >= pier.wind_base_moment_lb_ft \
        else "wind"
    notes = common + (
        f"CAGE: {pier.vertical_reinforcement} — As {steel:.2f} in2, rho "
        f"{100.0 * steel / area:.3f}%, against the {minimum_steel:.3f} in2 that "
        f"{COLUMN_MIN_REINFORCEMENT_RATIO:.2f} Ag requires. This is the MINIMUM cage the Code "
        f"permits, not a chosen margin.",
        f"LATERAL: {pier.moment_basis}.",
        f"BENDING GOVERNS, and {which} governs the bending: {governing:,.0f} lb-ft against "
        f"phi*Mn {phi_mn:,.0f} lb-ft at this column's own axial load, d/c "
        f"{governing / phi_mn:.2f} before magnification and "
        f"{governing * magnifier / phi_mn:.2f} after. The AXIAL comparison — "
        f"{demand:,.0f} lb against {capacity:,.0f} lb, d/c {demand / capacity:.3f} — is not "
        f"what sizes this column and never was.",
        f"SLENDERNESS: k*lu/r = {slenderness:.0f} at k "
        f"{CANTILEVER_EFFECTIVE_LENGTH_FACTOR:.1f}, past §6.2.5's sway limit of "
        f"{SWAY_SLENDERNESS_LIMIT:.0f}, so the moment is magnified above. The magnifier is "
        f"{magnifier:.3f} — near unity, because the axial load is about "
        f"{100.0 * demand / capacity:.0f}% of capacity and P-delta needs P to bite.",
        f"DOWELS: a class B lap of {lap:.0f}\" on #{cage.bar} bars, cast with the wall pour "
        f"below and lapped into the column's own cage. psi_e is 1.0 for GALVANIZED bar "
        f"(ACI 318-19 §25.4.2.5); it is epoxy coating that takes 1.2-1.5, and reading the "
        f"epoxy row for a galvanized bar would lengthen every lap in this house by half.",
        f"f'c IS THE PRESUMPTIVE {PRESUMPTIVE_FC_PSI:,.0f} psi, not the mix the assembly "
        f"specifies. This model carries no strength on an Assembly, so every concrete calc "
        f"in this engine reads one presumptive value. Where a house specifies more — the "
        f"catlin garden columns are a 5,000 psi class F3+C2 mix for durability — the "
        f"capacity above is understated, which is the safe direction. It is named here so "
        f"nobody reconciles this record against the drawing and concludes one of them is "
        f"wrong.",
        "SCREENING: the base is taken as FIXED, which the doweled lap into the wall top is "
        "detailed to deliver and which no calculation here proves; shear in the column is "
        "not graded (the section is enormous relative to a few hundred pounds, but 'enormous' "
        "is a judgement); and torsion, the wall-top joint's own capacity and the foundation's "
        "rotational stiffness are all outside it. A stamped design is what closes those.",
    )
    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} tied COLUMN (h/d "
                 f"{ratio:.1f}) FIXED at its base and carrying its deck's whole lateral "
                 f"system — {pier.vertical_reinforcement}, at d/c "
                 f"{governing * magnifier / phi_mn:.2f} in bending on {which}"),
        inputs=_inputs(pier, area, steel, cage) + (
            Quantity("wind_base_moment", pier.wind_base_moment_lb_ft, "lb-ft", 1.0),
            Quantity("guard_base_moment", pier.guard_base_moment_lb_ft, "lb-ft", 1.0),
            Quantity("phi_Mn", phi_mn, "lb-ft", 1.0),
            Quantity("cover", cover_in, "in", 0.125),
        ),
        limit_states=states, notes=notes, element_tags=(pier.tag,))


#: ACI 318-19 §20.5.1.3(a) — cast against and permanently in contact with ground is 3"; a
#: column exposed to weather takes 1-1/2". Used only when the house authors no cover.
DEFAULT_COVER_IN = 1.5


def _authored_cover_in(spec: str | None) -> float:
    """The cover the house wrote into ``Post.vertical_reinforcement``, or the Code minimum.

    The field is free text for a drawing, so this reads a ``2" cover`` fragment out of it
    the same way ``parse_cage`` reads the four numbers that carry meaning. Cover changes the
    bar circle and therefore the lever arm, so a house that specifies 2" for durability
    should be graded on 2" and not quietly credited with 1-1/2"'s longer arm.
    """
    if not spec:
        return DEFAULT_COVER_IN
    found = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:\"|in\b|inch)\s*cover", spec,
                      re.IGNORECASE)
    return float(found.group(1)) if found else DEFAULT_COVER_IN


def _detailing_only(pier: _Pier, area: float, ratio: float, shape: str, minimum_steel: float,
                    cage: _Cage, common: tuple[str, ...]) -> EngineeringRecord:
    """A cage graded in full against a demand that is knowably incomplete.

    ``_Pier.unmodelled_load`` names beams bearing on this pier whose load is not an area
    anywhere in the model, so ``tributary_ft2`` is an under-count of unknown size. The six
    detailing states above are load-independent and are published; the §22.4.2 axial
    comparison is **omitted, not estimated**. A d/c printed against a demand known to be
    short is worse than no d/c at all — a reader takes a number at face value and has no way
    to see what is missing from it, where an INCOMPLETE with a named cause is actionable.

    The remedy is upstream and is not this module's: give the load a modelled area to divide
    (a ``Roof`` or a ``FloorSystem`` over the beams), or have the engineer state the axial
    demand. Either way the record becomes ``_reinforced_column``'s with nothing here changed.
    """
    steel = cage.area_in2
    states = _detailing_states(pier, area, minimum_steel, cage)
    over = any(not state.ok for state in states)
    beams = ", ".join(pier.unmodelled_load)
    reason = (f"the axial DEMAND on {pier.tag}. It carries {beams}, which no "
              f"FloorSystem and no Roof names — so there is no tributary AREA for that load "
              f"and the {pier.tributary_ft2:.1f} ft2 this pier does account for is an "
              f"under-count of unknown size. The cage is graded in full above; the section "
              f"is not, and is not guessed at")
    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.INCOMPLETE,
        summary=(f"{pier.tag}: a {pier.diameter_in:.0f}\" {shape} tied COLUMN (h/d "
                 f"{ratio:.1f}) with {pier.vertical_reinforcement} — rho "
                 f"{100.0 * steel / area:.2f}% against ACI 318-19 §10.6.1.1's 1% floor, and "
                 f"six detailing limits met; the AXIAL state is not computed"),
        inputs=_inputs(pier, area, steel, cage), limit_states=states, missing=(reason,),
        notes=common + (
            f"CAGE: {pier.vertical_reinforcement} — As {steel:.2f} in2, rho "
            f"{100.0 * steel / area:.3f}%, against the {minimum_steel:.3f} in2 that "
            f"{COLUMN_MIN_REINFORCEMENT_RATIO:.2f} Ag requires. This is the MINIMUM cage the "
            f"Code permits, not a chosen margin.",
            f"UNMODELLED: {beams}. This is a shelter roof carried on beams and rafters with "
            f"no Roof or FloorSystem over it, so it has no plan area to shoelace. It is a "
            f"small load — the enclosure is 4'-0\" x 4'-0\" of 16mm multiwall on three 2x6 "
            f"rafters — and 'small' is a judgement, not a calculation, which is exactly why "
            f"this record declines to turn it into one.",
            "SCREENING: the detailing limits above are complete and the section is not "
            "graded at all. A stamped design states the demand and closes it.",
        ), element_tags=(pier.tag,))


def _reinforced_column(pier: _Pier, area: float, ratio: float, shape: str, demand: float,
                       minimum_steel: float, cage: _Cage,
                       common: tuple[str, ...]) -> EngineeringRecord:
    """The cage is stated: grade it, and grade the four detailing limits around it."""
    steel = cage.area_in2
    capacity = _capacity(area, steel)
    slenderness, magnifier, _eccentricity, _embedded = _slenderness(pier)

    states = (
        LimitState("axial, tied column", demand, capacity, "lb",
                   f"ACI 318-19 §22.4.2.1 Pn,max = {TIED_AXIAL_CAP:.2f} Po, phi "
                   f"{PHI_COMPRESSION_TIED:.2f} (Table 21.2.2) — f'c "
                   f"{PRESUMPTIVE_FC_PSI:,.0f} psi, fy {REINFORCEMENT_FY_PSI:,.0f} psi"),
        *_detailing_states(pier, area, minimum_steel, cage),
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
