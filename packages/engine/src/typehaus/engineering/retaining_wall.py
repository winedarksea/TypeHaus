"""Cantilever retaining wall — sliding, overturning, bearing and eccentricity.

`retaining_wall/<FoundationWall tag>`. The item `structural.foundation_unbalanced_fill` and
`structural.frost_depth` both delegate to, which is the argument for the whole register: one
engineer's design over the sunken-garden walls answers two checks across three walls and the
footings under them, with one stamp and one fingerprint.

**Oracle.** `houses/catlin/notes/sunken_garden_retaining_screening.md` §4 is an independently
hand-worked screening of exactly these three walls, written in a separate pass from this
module, and `tests/test_retaining_wall_calc.py` reproduces all twelve of its numbers — three
load cases × four limit states. A calculation that only agrees with itself is not verified.

**This is a screening, not a design, and the record says so.** Every geotechnical input is a
presumptive code-table value (`soil.py`); no drainage or hydrostatic case is run, no seismic
increment is applied, no reinforcement is sized, and no global-stability or settlement
question is opened. What it does do is answer the question IRC R404.4 actually asks — does
the base reach a safety factor of 1.5 against sliding and overturning — and answer it in
numbers a reviewer can disagree with term by term.

Conventions, so that a reader comparing rows compares like with like:

* moments are taken about the **toe**, per lineal foot of wall;
* a safety factor is carried as ``required / achieved`` so that, like every strength ratio
  beside it, **> 1 is over**;
* **passive resistance on the toe is neglected** unless the model can establish the toe's
  embedment. It is the standard conservative treatment and it barely matters here — on the
  catlin walls the toe is buried 6 1/2" and contributes under 1% of the resistance.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.soil import (
    CONCRETE_UNIT_WEIGHT_PCF,
    SOIL_UNIT_WEIGHT_BAND_PCF,
    PresumptiveSoil,
    aggregate_bed,
    presumptive,
)
from typehaus.model.enums import LayerFunction

KIND = "retaining_wall"

#: Bumped whenever the arithmetic below changes. It rides in the fingerprint, so a seal goes
#: stale when the *calculation* changes and not only when the model does.
BASIS_VERSION = "1"
BASIS = "IRC R404.4; IBC 1610.1 / 1806.2 presumptive values"

#: IRC R404.4's own requirement, and the only number here that is not a lookup.
REQUIRED_FS = 1.5

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class _Geometry:
    """One wall's stem and footing, in feet, per lineal foot of wall."""

    tag: str
    stem_thickness_ft: float
    stem_height_ft: float
    footing_width_ft: float
    footing_depth_ft: float
    toe_ft: float
    heel_ft: float
    retained_height_ft: float
    #: Depth of soil in front of the toe, where the model establishes one. Neglected (0.0)
    #: otherwise — see the module docstring.
    toe_embedment_ft: float = 0.0


@dataclass(frozen=True)
class _Case:
    """One load case's results — a lateral pressure and a soil unit weight."""

    label: str
    efp_psf_per_ft: float
    soil_pcf: float
    thrust_plf: float
    weight_plf: float
    resistance_plf: float
    resisting_moment: float
    overturning_moment: float
    bearing_psf: float
    eccentricity_ft: float

    @property
    def fs_sliding(self) -> float:
        return self.resistance_plf / self.thrust_plf if self.thrust_plf else float("inf")

    @property
    def fs_overturning(self) -> float:
        return (self.resisting_moment / self.overturning_moment
                if self.overturning_moment else float("inf"))


def analyse(geometry: _Geometry, soil: PresumptiveSoil, *, at_rest: bool = False,
            soil_pcf: float = SOIL_UNIT_WEIGHT_BAND_PCF[0],
            base: PresumptiveSoil | None = None) -> _Case:
    """One load case, per lineal foot, moments about the toe.

    ``soil`` is the **retained** material — it sets the pressure on the stem. ``base`` is
    what the footing actually **bears on**, and it sets the friction, the passive term and
    the allowable bearing. They are usually the same and here they are not: these footings
    sit on 42" of replacement stone, and sliding happens at that interface, not against the
    silty gravel behind the wall. Defaults to ``soil`` so a wall bearing on its own subgrade
    needs no second argument.

    Kept a free function taking plain numbers so the oracle test can drive it straight from
    the hand calc's own table without building a model.
    """
    base = base or soil
    efp = soil.at_rest_efp_psf_per_ft if at_rest else soil.active_efp_psf_per_ft
    height = geometry.retained_height_ft

    # Triangular active (or at-rest) thrust, resultant at H/3 above the base.
    thrust = 0.5 * efp * height * height
    overturning = thrust * height / 3.0

    # Dead load only. IBC Table 1806.2 footnote a applies the friction coefficient to the
    # dead load, and nothing here is anything else.
    stem = geometry.stem_thickness_ft * geometry.stem_height_ft * CONCRETE_UNIT_WEIGHT_PCF
    footing = (geometry.footing_width_ft * geometry.footing_depth_ft
               * CONCRETE_UNIT_WEIGHT_PCF)
    # The column of soil standing on the heel — the term the heel exists for, and the one a
    # footing centred on its stem throws away half of.
    on_heel = geometry.heel_ft * geometry.stem_height_ft * soil_pcf
    weight = stem + footing + on_heel

    passive = 0.5 * base.lateral_bearing_psf_per_ft * geometry.toe_embedment_ft ** 2
    resistance = base.friction_coefficient * weight + passive

    resisting = (footing * geometry.footing_width_ft / 2.0
                 + stem * (geometry.toe_ft + geometry.stem_thickness_ft / 2.0)
                 + on_heel * (geometry.footing_width_ft - geometry.heel_ft / 2.0))

    # Resultant location, eccentricity from the footing's centre, and the trapezoidal
    # bearing pressure at the toe.
    arm = (resisting - overturning) / weight if weight else 0.0
    eccentricity = geometry.footing_width_ft / 2.0 - arm
    bearing = (weight / geometry.footing_width_ft
               * (1.0 + 6.0 * eccentricity / geometry.footing_width_ft))

    return _Case(
        label=("at-rest" if at_rest else "active") + f" {efp:.0f} psf/ft, soil {soil_pcf:.0f} pcf",
        efp_psf_per_ft=efp, soil_pcf=soil_pcf,
        thrust_plf=thrust, weight_plf=weight, resistance_plf=resistance,
        resisting_moment=resisting, overturning_moment=overturning,
        bearing_psf=bearing, eccentricity_ft=eccentricity,
    )


def _limit_states(case: _Case, geometry: _Geometry, soil: PresumptiveSoil,
                  base: PresumptiveSoil | None = None) -> tuple[LimitState, ...]:
    """The four comparisons, all in the demand/capacity convention (> 1 is over)."""
    base = base or soil
    return (
        LimitState("sliding", REQUIRED_FS, case.fs_sliding, "", "IRC R404.4",
                   is_safety_factor=True),
        LimitState("overturning", REQUIRED_FS, case.fs_overturning, "", "IRC R404.4",
                   is_safety_factor=True),
        LimitState("bearing", case.bearing_psf, base.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {base.ibc_class}"),
        # Outside the middle third the heel lifts and the trapezoid above stops describing
        # the real pressure distribution, so this is a validity check on the row above it as
        # much as a limit state of its own.
        LimitState("eccentricity", abs(case.eccentricity_ft),
                   geometry.footing_width_ft / 6.0, "ft", "kern of the base (B/6)"),
    )


def _retaining_walls(ctx: EngineeringContext) -> list:
    """Free retaining walls — the ones IRC R404.4 sends to an engineered design.

    Scoped to ``lateral_support == "unsupported"``: a wall braced top and bottom is a
    basement wall and the prescriptive table answers it. This deliberately does *not*
    re-implement `foundation_unbalanced_fill`'s other handoff branches (an off-table
    thickness, a DR cell); those walls still reach the register through the check that
    delegates them, and get a NO_CALC record until someone widens this module's scope.
    """
    from typehaus.model.structure import FoundationWall

    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall)
            and getattr(w, "lateral_support", None) == "unsupported"]


@keys(KIND)
def enumerate_walls(ctx: EngineeringContext) -> list[str]:
    return [wall.tag for wall in _retaining_walls(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    records: list[EngineeringRecord] = []
    for wall in _retaining_walls(ctx):
        records.append(_one(ctx, wall))
    return records


def _one(ctx: EngineeringContext, wall) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    tag = wall.tag
    missing: list[str] = []

    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")

    geometry, geometry_missing = _geometry(ctx, wall)
    missing.extend(geometry_missing)

    if soil is None or geometry is None:
        return EngineeringRecord(
            item_id=item_id(KIND, tag), kind=KIND, key=tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{tag}: the R404.4 screening could not run",
            missing=tuple(missing), element_tags=(tag,),
        )

    # Both ends of the soil-unit-weight band. It is the one input with no code table behind
    # it (soil.py), so the calculation refuses to pick a number: where the two ends agree
    # the verdict is robust across the whole plausible range and is reported; where they
    # straddle the requirement, the answer genuinely turns on the missing datum and the
    # record says so instead of choosing.
    base = _base_interface(ctx, wall) or soil
    low, high = SOIL_UNIT_WEIGHT_BAND_PCF
    lower = analyse(geometry, soil, soil_pcf=low, base=base)
    upper = analyse(geometry, soil, soil_pcf=high, base=base)
    states_low = _limit_states(lower, geometry, soil, base)
    states_high = _limit_states(upper, geometry, soil, base)
    over_low = any(not state.ok for state in states_low)
    over_high = any(not state.ok for state in states_high)

    inputs = (
        Quantity("retained_height", geometry.retained_height_ft, "ft", 0.01),
        Quantity("stem_thickness", geometry.stem_thickness_ft, "ft", 0.01),
        Quantity("stem_height", geometry.stem_height_ft, "ft", 0.01),
        Quantity("footing_width", geometry.footing_width_ft, "ft", 0.01),
        Quantity("footing_depth", geometry.footing_depth_ft, "ft", 0.01),
        Quantity("toe", geometry.toe_ft, "ft", 0.01),
        Quantity("heel", geometry.heel_ft, "ft", 0.01),
        Quantity("toe_embedment", geometry.toe_embedment_ft, "ft", 0.01),
        Quantity("active_efp", soil.active_efp_psf_per_ft, "psf/ft", 1.0),
        Quantity("friction_coefficient", base.friction_coefficient, "", 0.01),
        Quantity("allowable_bearing", base.allowable_bearing_psf, "psf", 1.0),
        Quantity("concrete_unit_weight", CONCRETE_UNIT_WEIGHT_PCF, "pcf", 1.0),
    )
    notes = (
        "SCREENING on presumptive code values, not a design: "
        f"{soil.citation}. No geotechnical report is on file for this site.",
        f"Retained soil: {soil.soil_class}. Base bears on: {base.soil_class} "
        f"(friction {base.friction_coefficient:.2f}, allowable "
        f"{base.allowable_bearing_psf:,.0f} psf).",
        "No hydrostatic case — every number presumes the drainage behind the wall works "
        "perfectly. A saturated backfill roughly doubles the thrust.",
        "No seismic increment, no reinforcement design, no global-stability or settlement "
        "check. Passive resistance on the toe is neglected unless an embedment is derived.",
        f"Soil unit weight is a band, not a value ({low:.0f}-{high:.0f} pcf): no code table "
        f"publishes one. Both ends are run; sliding moves by "
        f"{abs(upper.fs_sliding - lower.fs_sliding):.2f} across it.",
    )

    if over_low != over_high:
        return EngineeringRecord(
            item_id=item_id(KIND, tag), kind=KIND, key=tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=(f"{tag}: the verdict turns on the soil unit weight — it checks at "
                     f"{high:.0f} pcf and does not at {low:.0f} pcf"),
            inputs=inputs, limit_states=states_low,
            missing=("a measured soil unit weight (no code table publishes one, and this "
                     "wall's answer depends on it)",),
            notes=notes, element_tags=(tag,),
        )

    # Report the conservative end. Both ends agree on the verdict, so this is the honest
    # margin rather than the flattering one.
    governing = max(states_low, key=lambda state: state.ratio)
    return EngineeringRecord(
        item_id=item_id(KIND, tag), kind=KIND, key=tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over_low else Status.OK,
        summary=(f"{tag}: {geometry.stem_thickness_ft * 12:.0f}\" cantilever retaining "
                 f"{geometry.retained_height_ft:.2f}' on a "
                 f"{geometry.footing_width_ft:.1f}' base "
                 f"({geometry.toe_ft:.1f}' toe / {geometry.heel_ft:.1f}' heel); "
                 f"{governing.name} governs at FS "
                 f"{1.0 / governing.ratio * REQUIRED_FS:.2f}"
                 if governing.is_safety_factor else
                 f"{tag}: {governing.name} governs"),
        inputs=inputs, limit_states=states_low, notes=notes, element_tags=(tag,),
    )


def _base_interface(ctx: EngineeringContext, wall) -> PresumptiveSoil | None:  # type: ignore[no-untyped-def]
    """What the footing under this wall actually bears on.

    Sliding happens at the base, so the friction coefficient describes the interface there —
    not the backfill behind the stem. Where a ``FootingBedding`` replaces the subgrade with a
    compacted washed-stone section, that stone is the bearing material and IBC Table 1806.2's
    gravel row is the right one.

    The gradation claim is not inferred from the ``aggregate`` free-text string, which would
    be reading a soil classification out of a substring — the same guess ``FootingBedding``'s
    own docstring refuses. It is taken from ``non_frost_susceptible``, which is an authored
    ASTM D422 claim (<6% passing the #200 sieve) about that very stone, and a bed that makes
    it is by that claim a clean open-graded gravel. A bedding that does not declare it falls
    back to the site's own class, which is the conservative direction.
    """
    from typehaus.model.structure import Footing, FootingBedding

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.under == wall.tag), None)
    hosts = {wall.tag} | ({footing.tag} if footing is not None else set())
    for bedding in ctx.plan.all_elements():
        if (isinstance(bedding, FootingBedding) and bedding.host_ref in hosts
                and getattr(bedding, "non_frost_susceptible", None) is True):
            return aggregate_bed()
    return None


def _geometry(ctx: EngineeringContext, wall) -> tuple[_Geometry | None, list[str]]:  # type: ignore[no-untyped-def]
    """The stem and footing dimensions, or the names of what the model does not carry."""
    from typehaus.model.structure import Footing

    tag = wall.tag
    missing: list[str] = []

    thickness_in = _structure_thickness_in(ctx, wall.assembly)
    if thickness_in is None:
        missing.append(f"a concrete STRUCTURE layer on assembly {wall.assembly}")

    if wall.top_elevation is None or wall.bottom_elevation is None:
        missing.append(f"top_elevation/bottom_elevation on {tag}")
        wall_height = None
    else:
        wall_height = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M_PER_FT

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.under == tag), None)
    if footing is None:
        missing.append(f"a Footing under {tag}")

    if wall.unbalanced_fill is None:
        # Deliberately not derived from Site.grade here. The check's proxy measures to a
        # single global grade plane, and a wall with a terrace against it — which is exactly
        # the condition that sends a wall to R404.4 — is what a plane cannot describe. A
        # retaining-wall design against an understated height is worse than none.
        missing.append(f"an authored unbalanced_fill on {tag} (the grade-plane proxy is not "
                       f"a safe input for a retaining-wall design)")

    if missing:
        return None, missing

    width_ft = footing.width.meters / _M_PER_FT
    depth_ft = footing.depth.meters / _M_PER_FT
    # The stem is what stands *above* the footing. ``FoundationWall.bottom_elevation`` is the
    # underside of the footing, not the top of the slab it bears on, so the wall's own height
    # already includes the footing depth — subtracting it here is what keeps the stem's dead
    # weight, and the column of soil standing on the heel beside it, from being counted a
    # foot too tall.
    stem_ft = wall_height - depth_ft
    thickness_ft = thickness_in / 12.0
    # ``center_on="axis"`` is a footing centred on the stem: toe and heel are equal, and
    # half the width sits on the side that does nothing for sliding.
    side = (width_ft - thickness_ft) / 2.0
    return _Geometry(
        tag=tag,
        stem_thickness_ft=thickness_ft,
        stem_height_ft=stem_ft,
        footing_width_ft=width_ft,
        footing_depth_ft=depth_ft,
        toe_ft=side,
        heel_ft=side,
        retained_height_ft=wall.unbalanced_fill.meters / _M_PER_FT,
    ), []


def _structure_thickness_in(ctx: EngineeringContext, assembly_tag: str) -> float | None:
    """The concrete STRUCTURE layer's nominal thickness. The foam over it retains nothing."""
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == assembly_tag), None)
    if assembly is None:
        return None
    for layer in assembly.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return round(layer.thickness.inches * 2.0) / 2.0
    return None
