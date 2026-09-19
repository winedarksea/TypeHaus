"""The fixity a cast column's base is ASSUMED to have, graded against what the ground gives.

** THIS IS THE ASSUMPTION ``deck_post`` HAS BEEN NAMING AND NOT GRADING. ** Every record
``_moment_column`` publishes carries the sentence "the base is taken as FIXED, which the
doweled lap is detailed to deliver and which no calculation here proves — nothing here
grades the EMBEDMENT that fixity needs against IBC 1807.3.2.1, and on a shallow-founded
column that is the assumption most likely to be the weak one." It is now graded.

**ONE mechanism is graded, and the second is reported as the reason it is the one.**

An embedded shaft and a spread pad are **alternative** load paths for a base moment, not
additive ones. A shaft that turns in soil sheds its moment into lateral bearing along its
buried length; a pad that resists by bearing does so because the shaft above it does not.
Adding the two would count the same moment twice, and the engine cannot compute the split
between them — that is a soil-structure stiffness problem, and it is named as ungraded.

1. **Embedment** — IBC 1807.3.2.1's non-constrained formula, and this is the mechanism these
   columns actually have. A pole free to translate at grade needs a depth that mobilises
   enough lateral soil bearing to turn the applied shear around.
2. **The pad alone**, reported as evidence rather than graded. ``e = M / P`` on catlin's
   north entry is about 1.7' against a 0.25' kern and a 0.75' half-width: the pad would not
   merely lift at one edge, it would have no contact at all. That is not a failure — it is
   the arithmetic showing that the pad is not what makes this column fixed, which is exactly
   why the embedment above is the state that matters. Grading it as a limit state would
   report a FAIL about a mechanism the structure does not use.

Concentric bearing on the same pad is ``structural.deck_footing_size``'s and is not restated
here: one question, one authority.

**The band convention, applied to the input that actually has two ends.** ``soil.py``'s
comment about running a band at both ends is usually about unit weight; here the two-ended
input is IBC **1806.3.4**, which permits the lateral bearing value to be DOUBLED for an
isolated pole "not adversely affected by a 1/2 inch motion at the ground surface". Whether a
half-inch of sway at grade is acceptable is a judgement about the structure above, not a
soil property, so this module refuses to make it: it runs the formula at ``S1`` and at
``2 S1`` and reports INCOMPLETE naming the missing judgement where the two ends disagree.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md``, hand-worked in a separate
pass.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.soil import presumptive

KIND = "column_base"

BASIS = ("IBC 2018 §1807.3.2.1 (non-constrained embedment) and §1806.2/§1806.3 "
         "(presumptive lateral bearing); ACI 318-19 for the pad in partial contact")

#: 1: the kind as introduced, 2026-09-18.
BASIS_VERSION = "1"

#: IBC §1806.3.4 — the lateral bearing value may be doubled for an isolated pole where a
#: 1/2" motion at the ground surface does not harm the structure. A judgement about what
#: stands on the column, not about the soil, so both ends are run and neither is chosen.
ISOLATED_POLE_FACTOR = 2.0

#: How far past the reported embedment a shortfall has to be before it is a FAIL, in feet.
#: Zero: a required depth is a required depth.
_TOLERANCE_FT = 0.0

oracled_by(
    KIND,
    Oracle(note="entry_column_base_fixity.md",
           test="tests/test_column_base_calcs.py"),
)


def required_embedment_ft(shear_lb: float, height_ft: float, diameter_ft: float,
                          lateral_psf_per_ft: float) -> float:
    """IBC 2018 §1807.3.2.1, the non-constrained case, solved for ``d``.

    ``A = 2.34 P / (S1 b)`` and ``d = 0.5 A [1 + sqrt(1 + 4.36 h / A)]``, where ``S1`` is
    the allowable lateral soil bearing **at one third the embedment depth** — so ``S1``
    depends on ``d`` and the pair is solved by fixed point rather than in closed form. It
    converges in a handful of passes because ``d`` enters ``S1`` linearly and ``A`` as a
    square root.

    ``P`` is the applied lateral force, ``h`` its height above grade, ``b`` the round
    column's diameter. All three at ALLOWABLE stress: §1806.2's lateral bearing is an
    allowable value and mixing a strength-level shear into it would overstate the demand by
    a third.
    """
    if shear_lb <= 0.0 or diameter_ft <= 0.0 or lateral_psf_per_ft <= 0.0:
        return 0.0
    depth = 1.0
    for _ in range(60):
        s1 = lateral_psf_per_ft * depth / 3.0
        a = 2.34 * shear_lb / (s1 * diameter_ft)
        nxt = 0.5 * a * (1.0 + math.sqrt(1.0 + 4.36 * max(height_ft, 0.0) / a))
        if abs(nxt - depth) < 1e-9:
            return nxt
        depth = nxt
    return depth


def _grade_ft(ctx: EngineeringContext) -> float | None:
    grade = getattr(getattr(ctx.plan.project, "site", None), "grade", None)
    return None if grade is None else float(grade.inches) / 12.0


def _pad_of(ctx: EngineeringContext, pier: _Pier):  # type: ignore[no-untyped-def]
    """The ``Pad`` or ``Footing`` this column stands on, or ``None``."""
    from typehaus.model.structure import Footing, Pad

    post = ctx.plan.by_tag(pier.tag)
    support = ctx.plan.by_tag(getattr(post, "supported_by", "") or "")
    if isinstance(support, Pad):
        return support
    if pier.footing_tag:
        footing = ctx.plan.by_tag(pier.footing_tag)
        if isinstance(footing, Footing):
            return footing
    return None


def _in_scope(ctx: EngineeringContext) -> list[_Pier]:
    """Every cast column that IS a lateral system and stands on its OWN spread base.

    A column doweled into a foundation WALL is out: ``structural.foundation`` already raises
    ``column_support/<wall tag>`` for exactly that joint, and two items over one question is
    how a register starts contradicting itself. A leaning column is out because it has no
    base moment to be fixed against.
    """
    return [pier for pier in cast_piers(ctx)
            if pier.lateral_system and not pier.shared_wall_footing
            and pier.base_kind in ("pad", "footing")]


@keys(KIND)
def enumerate_column_bases(ctx: EngineeringContext) -> list[str]:
    return sorted(pier.tag for pier in _in_scope(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, pier) for pier in sorted(_in_scope(ctx), key=lambda p: p.tag)]


def _pad_plan_ft(ctx: EngineeringContext, pad) -> tuple[float, float] | None:  # type: ignore[no-untyped-def]
    """``(least plan dimension ft, bearing area ft2)`` of the base, or ``None``.

    The LEAST dimension, because the base moment is free to act about either plan axis and
    nothing in this model says which way the wind blows — taking the larger would pick the
    favourable axis and call it a design.
    """
    outline = getattr(pad, "outline", None)
    if outline:
        xs = [p.xy_m[0] for p in outline]
        ys = [p.xy_m[1] for p in outline]
        width = (max(xs) - min(xs)) / 0.3048
        depth = (max(ys) - min(ys)) / 0.3048
        if width > 0.0 and depth > 0.0:
            return min(width, depth), width * depth
    width_in = getattr(getattr(pad, "width", None), "inches", None)
    if width_in:
        side = float(width_in) / 12.0
        return side, side * side
    return None


def _one(ctx: EngineeringContext, pier: _Pier) -> EngineeringRecord:
    from typehaus.engineering.roof_moment import base_shear_of

    ident = item_id(KIND, pier.tag)
    pad = _pad_of(ctx, pier)
    tags = tuple(t for t in (pier.tag, getattr(pad, "tag", None)) if t)
    soil = presumptive(getattr(ctx, "soil_class", None))
    grade_ft = _grade_ft(ctx)
    shear = base_shear_of(pier.tag)
    plan = _pad_plan_ft(ctx, pad) if pad is not None else None

    missing = [text for ok, text in (
        (soil is not None, "a declared soil class (Site/profile soil_class)"),
        (grade_ft is not None, "Site.grade — the embedment is measured from it"),
        (shear is not None,
         "a derived base shear for this column (engineering/roof_moment)"),
        (plan is not None, "a resolvable plan outline on the base this column stands on"),
    ) if not ok]
    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the base-fixity check could not run",
            missing=tuple(missing), element_tags=tags)

    shear_lb, arm_ft = shear
    least_ft, area_ft2 = plan
    base_top_ft = _base_top_ft(pad)
    embedment_ft = (grade_ft - base_top_ft) if base_top_ft is not None else None
    # The shear's arm is measured from the COLUMN's base — `roof_moment` takes the lever as
    # the full shaft, footing top to soffit. IBC 1807.3.2.1's `h` is measured from GRADE, so
    # the buried length comes back off it.
    height_ft = max(arm_ft - (embedment_ft or 0.0), 0.0)
    diameter_ft = pier.diameter_in / 12.0

    states: list[LimitState] = []
    notes: list[str] = []
    if embedment_ft is None:
        missing.append("a bottom elevation on the base, to measure embedment from")
    else:
        plain = required_embedment_ft(shear_lb, height_ft, diameter_ft,
                                      soil.lateral_bearing_psf_per_ft)
        doubled = required_embedment_ft(
            shear_lb, height_ft, diameter_ft,
            soil.lateral_bearing_psf_per_ft * ISOLATED_POLE_FACTOR)
        # Both ends of §1806.3.4, and the verdict is only published where they agree.
        if (plain <= embedment_ft + _TOLERANCE_FT) == (doubled <= embedment_ft
                                                       + _TOLERANCE_FT):
            states.append(LimitState(
                "embedment, non-constrained", plain, embedment_ft, "ft",
                f"IBC 2018 §1807.3.2.1 at S1 = {soil.lateral_bearing_psf_per_ft:.0f} psf/ft "
                f"(Table 1806.2 class {soil.ibc_class}) taken at d/3, P {shear_lb:,.0f} lb "
                f"ASD at h {height_ft:.2f}' above grade on a {diameter_ft:.2f}' round. "
                f"§1806.3.4's isolated-pole doubling would need {doubled:.2f}' and does not "
                f"change the verdict, so it is not claimed"))
        else:
            missing.append(
                f"a judgement on IBC §1806.3.4: the embedment needs {plain:.2f}' at the "
                f"table's lateral bearing and {doubled:.2f}' at the isolated-pole double, "
                f"and this column has {embedment_ft:.2f}' — so the verdict turns on whether "
                f"a 1/2\" lateral motion at grade harms what stands on it, which is a "
                f"judgement about the structure and not about the soil")
        notes.append(
            f"EMBEDMENT is measured from Site.grade ({grade_ft:+.2f}') to the top of "
            f"{getattr(pad, 'tag', 'the base')} ({base_top_ft:+.2f}'), i.e. "
            f"{embedment_ft:.2f}'. The pad's own thickness below that is NOT counted as "
            f"embedment: §1807.3.2.1 is about a shaft turning in soil, and a footing under "
            f"it resists by a different mechanism the formula does not describe.")

    # --- the pad alone, as EVIDENCE that the pad is not the mechanism -------------------
    # Gravity at SERVICE, lateral at ASD: IBC §1605.3's basis, not the strength basis
    # `deck_post` grades the section on.
    moment_lb_ft = pier.wind_base_moment_lb_ft
    axial_lb = pier.service_lb + area_ft2 * _pad_thickness_ft(pad) * 150.0
    eccentricity_ft = moment_lb_ft / axial_lb if axial_lb > 0.0 else float("inf")
    kern_ft = least_ft / 6.0
    notes.append(
        f"THE PAD IS NOT WHAT MAKES THIS COLUMN FIXED, and the arithmetic says so rather "
        f"than the prose. Taken as a rigid spread base with no help from the buried shaft, "
        f"the resultant of {axial_lb:,.0f} lb service axial and {moment_lb_ft:,.0f} lb-ft "
        f"ASD base moment sits {eccentricity_ft:.2f}' off centre, against a kern of "
        f"{kern_ft:.2f}' and a half-width of {least_ft / 2.0:.2f}' — so the pad alone would "
        f"have {'partial' if eccentricity_ft <= least_ft / 2.0 else 'NO'} contact. That is "
        f"reported and NOT graded, because an embedded shaft and a spread pad are "
        f"ALTERNATIVE paths for one moment and not additive ones: adding them counts the "
        f"same moment twice. The embedment above is the mechanism this column has.")

    notes.extend((
        f"SCREENING on presumptive code values, not a design: {soil.citation}. No "
        f"geotechnical report is on file for this site.",
        f"THE DEMAND IS THE ONE `deck_post` GRADES THE SECTION ON, at its own basis. "
        f"`engineering/roof_moment` derives {shear_lb:,.0f} lb of ASD storey shear at an "
        f"effective {arm_ft:.2f}' above this column's base; IBC §1807.3.2.1 wants that "
        f"force and its height above GRADE, so the buried length comes off it. Splitting "
        f"one moment into a force and an arm has infinitely many answers — this is the "
        f"factorisation the demand was actually built from, which is why the shear is "
        f"carried out of that module rather than back-solved here.",
        "NOT GRADED, and each is a real question: how the base moment SPLITS between the "
        "buried shaft and the pad (a soil-structure stiffness problem, and the reason only "
        "one mechanism is graded above); the foundation's rotational STIFFNESS, which is "
        "what the sway magnifier in `deck_post` implicitly assumes is infinite; group "
        "effect with the pier line beside it; and passive resistance on the pad's own "
        "faces, which is neglected and is the conservative direction.",
        "IBC §1806.3.4's doubling is NOT claimed wherever it would change the verdict. A "
        "1/2\" lateral motion at the ground surface is the price of it, and whether that "
        "harms a canopy header and the standoff shims under it is a judgement about the "
        "structure rather than a soil property.",
    ))

    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the base is assumed FIXED and this check could not "
                    f"finish confirming it",
            inputs=_inputs(pier, shear_lb, height_ft, embedment_ft, least_ft, area_ft2,
                           soil, eccentricity_ft),
            limit_states=tuple(states), missing=tuple(missing),
            notes=tuple(notes), element_tags=tags)

    over = any(not state.ok for state in states)
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag}: the FIXED base `deck_post` assumes, graded — "
                 f"{embedment_ft:.2f}' of embedment and a {least_ft:.2f}' base under "
                 f"{shear_lb:,.0f} lb of ASD shear; {worst.name} governs at "
                 f"{worst.demand / worst.capacity:.2f}"),
        inputs=_inputs(pier, shear_lb, height_ft, embedment_ft, least_ft, area_ft2, soil,
                       eccentricity_ft),
        limit_states=tuple(states), notes=tuple(notes), element_tags=tags)


def _base_top_ft(pad) -> float | None:  # type: ignore[no-untyped-def]
    bottom = getattr(pad, "bottom_elevation", None)
    thickness = getattr(pad, "thickness", None) or getattr(pad, "depth", None)
    if bottom is None or thickness is None:
        return None
    return (float(bottom.inches) + float(thickness.inches)) / 12.0


def _pad_thickness_ft(pad) -> float:  # type: ignore[no-untyped-def]
    thickness = getattr(pad, "thickness", None) or getattr(pad, "depth", None)
    return float(thickness.inches) / 12.0 if thickness is not None else 0.0


def _inputs(pier: _Pier, shear_lb: float, height_ft: float, embedment_ft: float | None,
            least_ft: float, area_ft2: float, soil, eccentricity_ft: float,
            ) -> tuple[Quantity, ...]:  # type: ignore[no-untyped-def]
    return tuple(q for q in (
        Quantity("column_diameter", pier.diameter_in, "in", 0.5),
        Quantity("lateral_shear_asd", shear_lb, "lb", 1.0),
        Quantity("shear_height_above_grade", height_ft, "ft", 0.01),
        Quantity("embedment", embedment_ft, "ft", 0.01)
        if embedment_ft is not None else None,
        Quantity("base_least_dimension", least_ft, "ft", 0.01),
        Quantity("base_area", area_ft2, "ft2", 0.01),
        Quantity("base_moment_asd", pier.wind_base_moment_lb_ft, "lb-ft", 1.0),
        Quantity("service_axial", pier.service_lb, "lb", 1.0),
        Quantity("eccentricity", eccentricity_ft, "ft", 0.001),
        Quantity("lateral_bearing", soil.lateral_bearing_psf_per_ft, "psf/ft", 1.0),
        Quantity("allowable_bearing", soil.allowable_bearing_psf, "psf", 1.0),
    ) if q is not None)
