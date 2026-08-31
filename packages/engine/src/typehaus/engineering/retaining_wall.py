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

The free body itself — geometry, one load case, the limit states — is
`engineering/retaining_basis.py`, which `engineering/retaining_system.py` shares. This
module is the per-wall RECORD: which walls are in scope, and what a reader of one wall's
row is told. `_Geometry` and `analyse` are re-exported here under their old names.
"""

from __future__ import annotations

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.retaining_basis import (
    BASIS,
    REQUIRED_FS,
    _base_interface,
    _Case,
    _Geometry,
    _geometry,
    _limit_states,
    analyse,
)
from typehaus.engineering.retaining_system import KIND as SYSTEM_KIND
from typehaus.engineering.retaining_system import _loops, system_factors
from typehaus.engineering.soil import (
    CONCRETE_UNIT_WEIGHT_PCF,
    SOIL_UNIT_WEIGHT_BAND_PCF,
    presumptive,
)

#: Re-exported at their old names on purpose. ``tests/test_retaining_wall_calc.py`` imports
#: ``_Geometry`` and ``analyse`` from here and its ORACLE is the frozen hand pass; the split
#: that moved them to ``retaining_basis`` must not be visible to it.
__all__ = ["KIND", "BASIS", "BASIS_VERSION", "REQUIRED_FS", "_Case", "_Geometry", "analyse",
           "compute", "enumerate_walls"]

KIND = "retaining_wall"

#: Bumped whenever the arithmetic below changes. It rides in the fingerprint, so a seal goes
#: stale when the *calculation* changes and not only when the model does.
#:
#: 1 -> 2 (2026-08-30): the stem/footing elevation convention, per the module docstring. The
#: stem was a footing depth short and ``H`` a footing depth short with it.
#: 2 -> 3 (2026-08-30): a ``lateral_support="base"`` branch graded at at-rest against the
#: court's own free body, and a ``stem flexure`` limit state on every branch.
BASIS_VERSION = "3"


def _retaining_walls(ctx: EngineeringContext) -> list:
    """Free retaining walls — the ones IRC R404.4 sends to an engineered design.

    Scoped to ``lateral_support in ("unsupported", "base")``: a wall braced top and bottom is
    a basement wall and the prescriptive table answers it. **``"base"`` has to be in this set
    or a restrained wall LEAVES the suite** — the register would go quiet on exactly the
    walls the restraint was authored to explain, and a wall that stops being computed reads
    the same as a wall that has no problem.

    This deliberately does *not* re-implement `foundation_unbalanced_fill`'s other handoff
    branches (an off-table thickness, a DR cell); those walls still reach the register
    through the check that delegates them, and get a NO_CALC record until someone widens
    this module's scope.
    """
    from typehaus.model.structure import FoundationWall

    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall)
            and getattr(w, "lateral_support", None) in ("unsupported", "base")]


@keys(KIND)
def enumerate_walls(ctx: EngineeringContext) -> list[str]:
    return [wall.tag for wall in _retaining_walls(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    """Every wall in scope, with the court's free body resolved **once** and threaded in.

    ``EngineeringResults._run`` calls this once per kind, which is the only reason the loop
    can be solved here rather than per wall: three walls each re-tracing the same wall graph
    and re-analysing the same three members would be the same answer computed nine times.
    """
    systems: dict[str, tuple[float, float, float, str]] = {}
    for ref, members in _loops(ctx).items():
        factors = system_factors(ctx, ref, members)
        if factors is None:
            continue
        demand, capacity = factors[f"{SOIL_UNIT_WEIGHT_BAND_PCF[0]:.0f}"]
        for member in members:
            systems[member.tag] = (capacity / demand if demand else float("inf"),
                                   demand, capacity, item_id(SYSTEM_KIND, ref))
    return [_one(ctx, wall, systems.get(wall.tag)) for wall in _retaining_walls(ctx)]



def _restate(states: tuple, system: tuple[float, float, float, str] | None) -> tuple:
    """Swap ``sliding`` for ``base restraint`` where the wall stands in a verified loop.

    **Per-wall sliding is not a meaningful number once the free body is wrong.** Grading
    ``W-SG-E2`` as an isolated cantilever asks whether its own footing's friction resists its
    own thrust, and the answer is no and always will be — while the wall it faces across the
    court pushes back with an equal and opposite thrust through the concrete between them.
    Reporting 0.66 there would be reporting the arithmetic of a wall nobody built.

    The other three rows are NOT swapped. Overturning, bearing and eccentricity stay on the
    isolated free body, which is conservative twice over: the restraint's own restoring
    moment is neglected, and so is the horizontal spanning that carries much of the thrust to
    the corners. A conservative row that passes needs no apology.
    """
    if system is None:
        return states
    fs, _demand, _capacity, item = system
    return tuple(
        LimitState("base restraint", REQUIRED_FS, fs, "", f"IRC R404.4 via {item}",
                   is_safety_factor=True)
        if state.name == "sliding" else state
        for state in states)


def _one(ctx: EngineeringContext, wall,  # type: ignore[no-untyped-def]
         system: tuple[float, float, float, str] | None = None) -> EngineeringRecord:
    tag = wall.tag
    missing: list[str] = []
    # **The restrained branch is graded at AT-REST and the free one at active, and the
    # difference is not a preference.** A free cantilever is normally designed active and
    # may be; a wall whose base is held by a permanent strut is not free to move enough to
    # mobilise the active wedge, and citing the strut in the resistance term concedes it.
    # ``retaining_system``'s module docstring works the deflection argument.
    restrained = getattr(wall, "lateral_support", None) == "base"
    if restrained and system is None:
        missing.append(f"a verified base restraint for {tag} — it declares "
                       f"lateral_support=\"base\" and names "
                       f"{getattr(wall, 'base_restraint_ref', None) or 'nothing'}, and the "
                       f"court that restraint belongs to does not check out "
                       f"(see the retaining_system record)")

    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")

    geometry, geometry_missing = _geometry(ctx, wall)
    missing.extend(geometry_missing)

    if soil is None or geometry is None or missing:
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
    lower = analyse(geometry, soil, at_rest=restrained, soil_pcf=low, base=base)
    upper = analyse(geometry, soil, at_rest=restrained, soil_pcf=high, base=base)
    states_low = _restate(_limit_states(lower, geometry, soil, base), system)
    states_high = _restate(_limit_states(upper, geometry, soil, base), system)
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
    ) + ((
        # What makes moving the cross-member, or moving the wall on the FAR side of the
        # court, stale THIS wall's seal. Without these two the fingerprint would cover only
        # the wall's own geometry, and the number it reports would depend on three walls.
        Quantity("system_demand", system[1], "lb", 1.0),
        Quantity("system_capacity", system[2], "lb", 1.0),
    ) if system is not None else ())
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
    ) + ((
        f"BASE RESTRAINT: this wall does not resist sliding alone. Its base is held in a "
        f"closed loop of cast concrete and the whole court is graded as one free body by "
        f"{system[3]} — which is why this row's number depends on walls other than this one, "
        f"and why editing any of them stales this record.",
        "Graded at AT-REST (60 psf/ft), not active, because the restraint is credited. The "
        "free-cantilever branch of this same module grades at active; the two are not "
        "comparable row for row.",
    ) if system is not None else ())

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
