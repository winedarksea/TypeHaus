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
2. **The spread or COMBINED base** — eccentricity against the kern, bearing against the
   presumptive allowable, and a factor of safety against overturning, all on the footprint's
   real area, centroid and section modulus (``engineering/spread_base.py``). Where the pad
   names ``cast_with`` pours, that footprint is their union: ACI 318-19 §13.3.4's combined
   footing, which §13.3.4.3 forbids assuming a UNIFORM pressure under and which this
   therefore does not — the distribution is the rigid-body linear one, and where the
   resultant leaves the kern no pressure is published at all.

**Which of the two is GRADED is authored, and it is never "whichever passes".**
``Pad.resists_base_moment`` chooses. Unset — the ordinary case, and catlin's — grades the
embedment and reports the spread arithmetic as evidence; set, it grades the spread mechanism
and reports the embedment. Both numbers are computed either way and both are printed, because
a reader deciding which mechanism a base really has needs to see both.

On catlin's north entry that evidence is emphatic: ``e = M / P`` is about 0.9' against a
0.42' kern, so the pad would lift at one edge before it did anything about the moment. That
is not a failure — it is the arithmetic showing that the pad is not what makes this column
fixed, which is exactly why the embedment is the state that matters here.

Concentric bearing on the same pad is ``structural.deck_footing_size``'s and is not restated
here: one question, one authority.

**The band convention, applied to the input that actually has two ends.** ``soil.py``'s
comment about running a band at both ends is usually about unit weight; here the two-ended
input is IBC **1806.3.4**, which permits the lateral bearing value to be DOUBLED for an
isolated pole "not adversely affected by a 1/2 inch motion at the ground surface". Whether a
half-inch of sway at grade is acceptable is a judgement about the structure above, not a
soil property, so this module refuses to make it: it runs the formula at ``S1`` and at
``2 S1`` and reports INCOMPLETE naming the missing judgement where the two ends disagree.

**A HOUSE MAY MAKE THAT JUDGEMENT, AND IT IS THEN A GRADED CLAIM.**
``Post.isolated_pole_basis`` states, in prose, what tolerates half an inch of motion at
grade and on whose word; where the two ends straddle, the limit state is published at
``2 S1`` and the citation says the doubling was claimed and quotes the basis — a reader may
never see a passing embedment without learning §1806.3.4 was invoked. Two ways to be
refused, both INCOMPLETE naming why: an EMPTY basis (the stale-declaration failure a bare
bool has), and a governing lateral case §1806.3.4's own words do not reach. The section
permits the doubling for motion "due to **short-term** lateral loads"; wind and an R301.5
guard push both qualify, and :func:`_sustained_lateral_cases` refuses anything else rather
than honouring a doubling against a load that never goes away.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md``, hand-worked in a separate
pass.
"""

from __future__ import annotations

import dataclasses
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
from typehaus.engineering.spread_base import (
    REQUIRED_FS_OVERTURNING,
    SpreadResult,
    analyse,
    pours_for,
    union_footprint,
)

KIND = "column_base"

BASIS = ("IBC 2018 §1807.3.2.1 (non-constrained embedment) and §1806.2/§1806.3 "
         "(presumptive lateral bearing); ACI 318-19 §13.3.4 and IRC R404.4 for the spread "
         "or combined base")

#: 1: the kind as introduced, 2026-09-18.
#: 2: the spread/combined mechanism became a graded alternative under
#: ``Pad.resists_base_moment``, and the demand started being shared with a declared
#: diaphragm — 2026-09-19.
#: 3: §1806.3.4's isolated-pole doubling became claimable, as a graded authored claim on
#: ``Post.isolated_pole_basis`` — 2026-09-20.
BASIS_VERSION = "3"

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


#: The ``_Pier`` base-moment fields §1806.3.4's "short-term lateral loads" reaches.
#: WIND is short-term by definition — ASCE 7-16's demand is a 3-second gust — and the IRC
#: R301.5 guard push is a 200 lb concentrated load applied "at any point", a person leaning
#: on a rail and not a standing condition. Half an inch of sway under either recovers.
#:
#: ** ANY OTHER LATERAL CASE A PIER EVER CARRIES HAS TO BE ADDED HERE DELIBERATELY **, by
#: somebody who has decided it is short-term. :func:`_sustained_lateral_cases` scans for
#: base-moment fields that are NOT named here and refuses the claim on them, rather than
#: honouring a doubling against an earth surcharge that never goes away.
_SHORT_TERM_MOMENTS = ("wind_base_moment_lb_ft", "guard_base_moment_lb_ft")


def _sustained_lateral_cases(pier: _Pier) -> tuple[str, ...]:
    """Base moments on this pier that §1806.3.4's doubling may NOT be claimed against."""
    return tuple(sorted(
        f.name for f in dataclasses.fields(pier)
        if f.name.endswith("_base_moment_lb_ft") and f.name not in _SHORT_TERM_MOMENTS
        and abs(float(getattr(pier, f.name, 0.0) or 0.0)) > 0.0))


def _pole_claim(ctx: EngineeringContext, pier: _Pier) -> tuple[str | None, str | None]:
    """``(basis prose, refusal)`` for this column's §1806.3.4 claim. Both ``None`` = unclaimed.

    A claim that makes a demand smaller has to be graded or it is not a claim, and this is
    the grading. Two ways to be refused, and each is reported as a *missing judgement* on
    the record rather than silently ignored: an EMPTY basis (the stale-declaration failure a
    bare bool has, with nothing a reader could use to notice it went stale), and a governing
    lateral case §1806.3.4's own words do not reach.
    """
    post = ctx.plan.by_tag(pier.tag)
    raw = getattr(post, "isolated_pole_basis", None)
    if raw is None:
        return None, None
    if not str(raw).strip():
        return None, (
            "a BASIS for the IBC §1806.3.4 claim on this column: `isolated_pole_basis` is "
            "authored empty, and a doubling with no statement behind it is the stale "
            "declaration this field exists to prevent. State what tolerates 1/2\" of "
            "motion at grade and on whose word")
    sustained = _sustained_lateral_cases(pier)
    if sustained:
        return None, (
            f"a governing lateral case §1806.3.4's doubling may be claimed against. This "
            f"column claims it, and it carries {', '.join(sustained)} — while §1806.3.4 "
            f"permits the doubling only for motion \"due to SHORT-TERM lateral loads\". A "
            f"sustained case does not recover from 1/2\" of movement at grade. Withdraw "
            f"the claim, or grade this column on the table's own S1")
    return str(raw).strip(), None


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
    embed_note = "no embedment this model can measure"
    # ** THE CLAIM IS READ BEFORE EITHER MECHANISM IS WORKED, AND IT DECIDES ONE THING ONLY:
    # WHICH SET OF NUMBERS BECOMES LIMIT STATES. ** Both are computed either way — a reader
    # deciding which mechanism a base really has needs to see both — but only one of them
    # gets graded, and only that one may put anything in `missing`. An embedment that
    # straddles §1806.3.4 is not a gap in a record whose mechanism is the spread base.
    claimed = bool(getattr(pad, "resists_base_moment", False))
    # A SECOND authored claim, and a different question: `claimed` above chooses WHICH
    # mechanism is graded, this one chooses which END of §1806.3.4's band the embedment is
    # graded at. It is subject to the same doctrine as everything else here — only the
    # graded mechanism may put anything in `missing` — so a refusal is raised under the
    # embedment branch and nowhere else.
    pole_basis, pole_refusal = _pole_claim(ctx, pier)
    if embedment_ft is None:
        if not claimed:
            missing.append("a bottom elevation on the base, to measure embedment from")
    else:
        plain = required_embedment_ft(shear_lb, height_ft, diameter_ft,
                                      soil.lateral_bearing_psf_per_ft)
        doubled = required_embedment_ft(
            shear_lb, height_ft, diameter_ft,
            soil.lateral_bearing_psf_per_ft * ISOLATED_POLE_FACTOR)
        # Both ends of §1806.3.4, and the verdict is only published where they agree.
        embed_note = (f"{plain:.2f}' of embedment ({doubled:.2f}' at §1806.3.4's "
                      f"isolated-pole double) against the {embedment_ft:.2f}' it has")
        if not claimed:
            # An authored claim this module cannot honour is a defect in the house whether
            # or not the band happens to turn on it today, so it is raised before the test.
            if pole_refusal is not None:
                missing.append(pole_refusal)
            if (plain <= embedment_ft + _TOLERANCE_FT) == (doubled <= embedment_ft
                                                           + _TOLERANCE_FT):
                states.append(LimitState(
                    "embedment, non-constrained", plain, embedment_ft, "ft",
                    f"IBC 2018 §1807.3.2.1 at S1 = "
                    f"{soil.lateral_bearing_psf_per_ft:.0f} psf/ft (Table 1806.2 class "
                    f"{soil.ibc_class}) taken at d/3, P {shear_lb:,.0f} lb ASD at h "
                    f"{height_ft:.2f}' above grade on a {diameter_ft:.2f}' round. "
                    f"§1806.3.4's isolated-pole doubling would need {doubled:.2f}' and "
                    f"does not change the verdict, so it is not claimed"))
            # ** THE TWO ENDS DISAGREE, SO THE VERDICT TURNS ON A JUDGEMENT ABOUT THE
            # STRUCTURE. ** The house may make it, on `Post.isolated_pole_basis`, and then
            # this module grades the doubled formula and says in the citation that it did.
            # A reader may never see a passing embedment here without learning §1806.3.4
            # was invoked and on whose statement.
            elif pole_basis is not None:
                states.append(LimitState(
                    "embedment, non-constrained", doubled, embedment_ft, "ft",
                    f"IBC 2018 §1807.3.2.1 at 2 S1 — §1806.3.4's ISOLATED-POLE DOUBLING, "
                    f"CLAIMED BY THIS HOUSE and not derived here: "
                    f"{2 * soil.lateral_bearing_psf_per_ft:.0f} psf/ft against Table "
                    f"1806.2 class {soil.ibc_class}'s "
                    f"{soil.lateral_bearing_psf_per_ft:.0f}, taken at d/3, P "
                    f"{shear_lb:,.0f} lb ASD at h {height_ft:.2f}' above grade on a "
                    f"{diameter_ft:.2f}' round. The price of the doubling is 1/2\" of "
                    f"lateral motion at the ground surface under short-term load; on the "
                    f"table's own S1 this column would need {plain:.2f}' and has "
                    f"{embedment_ft:.2f}'. The claim's basis: {pole_basis}"))
            elif pole_refusal is None:
                missing.append(
                    f"a judgement on IBC §1806.3.4: the embedment needs {plain:.2f}' at "
                    f"the table's lateral bearing and {doubled:.2f}' at the isolated-pole "
                    f"double, and this column has {embedment_ft:.2f}' — so the verdict "
                    f"turns on whether a 1/2\" lateral motion at grade harms what stands "
                    f"on it, which is a judgement about the structure and not about the "
                    f"soil")
        notes.append(
            f"EMBEDMENT is measured from Site.grade ({grade_ft:+.2f}') to the top of "
            f"{getattr(pad, 'tag', 'the base')} ({base_top_ft:+.2f}'), i.e. "
            f"{embedment_ft:.2f}'. The pad's own thickness below that is NOT counted as "
            f"embedment: §1807.3.2.1 is about a shaft turning in soil, and a footing under "
            f"it resists by a different mechanism the formula does not describe.")

    # --- the SPREAD or COMBINED base ----------------------------------------------------
    # Gravity at SERVICE, lateral at ASD: IBC §1605.3's basis, not the strength basis
    # `deck_post` grades the section on.
    moment_lb_ft = pier.wind_base_moment_lb_ft
    axial_lb = pier.service_lb + area_ft2 * _pad_thickness_ft(pad) * 150.0
    # ** THE COLUMN'S LOAD, NOT ``axial_lb``, AND THE DIFFERENCE IS THE PAD ITSELF. **
    # ``axial_lb`` already carries the base's own weight for the evidence line below;
    # ``spread_base.analyse`` weighs every pour in the footprint and adds it at its OWN
    # centroid, which on a combined footing is nowhere near the column. Handing it the
    # padded figure counted the concrete twice — 6,281 lb under a base that weighs 5,719 —
    # and the second copy landed on the column's lever rather than on its own.
    spread, spread_how = _spread(ctx, pier, pad, moment_lb_ft, pier.service_lb)
    eccentricity_ft = (spread.eccentricity_ft if spread is not None
                       else (moment_lb_ft / axial_lb if axial_lb > 0.0 else float("inf")))
    if claimed and spread is not None:
        states.extend(_spread_states(spread, soil, spread_how))
        notes.append(
            f"THE SPREAD BASE IS THE MECHANISM THIS COLUMN CLAIMS, and the embedment is "
            f"reported instead of graded. {spread_how} The buried shaft would want "
            f"{embed_note} — an ALTERNATIVE path for the same moment, never an additive "
            f"one: a shaft that turns in soil sheds its moment into lateral bearing, and a "
            f"base that resists by bearing does so because the shaft above it does not. "
            f"Adding them counts one moment twice, and `Pad.resists_base_moment` is what "
            f"chooses between them rather than this module.")
    elif claimed:
        missing.append(
            f"a workable spread base for {getattr(pad, 'tag', 'this base')}: it claims "
            f"`resists_base_moment`, and {spread_how}")
    else:
        if spread is None:
            notes.append(
                f"THE PAD IS NOT GRADED AS THE MECHANISM and its arithmetic could not be "
                f"worked either: {spread_how} `Pad.resists_base_moment` is unset, so "
                f"nothing turns on it.")
        else:
            notes.append(
                f"THE PAD IS NOT WHAT MAKES THIS COLUMN FIXED, and the arithmetic says so "
                f"rather than the prose. {spread_how} That is reported and NOT graded, "
                f"because an embedded shaft and a spread base are ALTERNATIVE paths for one "
                f"moment and not additive ones: adding them counts the same moment twice. "
                f"The embedment above is the mechanism this column has, and "
                f"`Pad.resists_base_moment` is what a base that really is the other one "
                f"says so with.")

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
        (f"IBC §1806.3.4's doubling IS CLAIMED on this column, and the limit state above "
         f"is graded at 2 S1 because of it. A 1/2\" lateral motion at the ground surface "
         f"under short-term load is the price, and the house's statement that this "
         f"structure tolerates it is: {pole_basis}"
         if pole_basis is not None else
         "IBC §1806.3.4's doubling is NOT claimed wherever it would change the verdict. A "
         "1/2\" lateral motion at the ground surface is the price of it, and whether that "
         "harms a canopy header and the standoff shims under it is a judgement about the "
         "structure rather than a soil property."),
    ))

    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the base is assumed FIXED and this check could not "
                    f"finish confirming it",
            inputs=_inputs(pier, shear_lb, height_ft, embedment_ft, least_ft, area_ft2,
                           soil, eccentricity_ft, pole_basis is not None),
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
                       eccentricity_ft, pole_basis is not None),
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
            pole_claimed: bool = False,
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
        # The claim is an INPUT, not a presentation choice: it halves the required depth,
        # so a fingerprint that did not move when it was withdrawn would pin a seal to a
        # design that no longer exists.
        Quantity("isolated_pole_doubling", 1.0 if pole_claimed else 0.0, "-", 0.5),
        Quantity("lateral_bearing", soil.lateral_bearing_psf_per_ft, "psf/ft", 1.0),
        Quantity("allowable_bearing", soil.allowable_bearing_psf, "psf", 1.0),
    ) if q is not None)


def _spread(ctx: EngineeringContext, pier: _Pier, pad, moment_lb_ft: float,
            axial_lb: float) -> tuple[SpreadResult | None, str]:  # type: ignore[no-untyped-def]
    """The spread/combined analysis and one sentence of prose, or ``(None, why not)``.

    Worked whether or not it is the graded mechanism. A reader deciding which mechanism a
    base actually has needs both numbers in front of them, and a record that computed only
    the one it grades could never show its own choice was right.
    """
    from typehaus.engineering.roof_moment import base_axis_of

    axis = base_axis_of(pier.tag)
    if axis is None:
        return None, "no governing moment axis resolves for this column."
    pours = pours_for(ctx, pad)
    if pours is None:
        return None, (f"the base's plan geometry does not resolve, or a pour "
                      f"{getattr(pad, 'tag', 'it')} names in `cast_with` is not concrete "
                      f"and cannot be cast with anything.")
    footprint = union_footprint(pours, axis)
    if footprint is None:
        return None, ("the pours named do not merge into one body, so there is no single "
                      "section modulus to work with.")
    station = (pier_station(ctx, pier)[0] if axis == "x" else pier_station(ctx, pier)[1])
    result = analyse(footprint, axial_lb, station, moment_lb_ft, axis)
    if result is None:
        return None, "the rigid-body analysis of the base could not be formed."
    direction = "E-W" if axis == "x" else "N-S"
    shape = (f"{', '.join(footprint.tags)} as ONE pour" if len(footprint.tags) > 1
             else footprint.tags[0])
    contact = ("the whole base stays in contact" if result.bearing_psf is not None
               else "the base LIFTS at one edge and no linear pressure describes it")
    return result, (
        f"Taken as a rigid body on soil about the {direction} axis, {shape} is "
        f"{footprint.area_ft2:.2f} ft2 with its centroid at {footprint.centroid_ft:+.2f}' "
        f"and I {footprint.inertia_ft4:.3f} ft4; {result.total_vertical_lb:,.0f} lb of "
        f"vertical load against {moment_lb_ft:,.0f} lb-ft ASD puts the resultant "
        f"{result.eccentricity_ft:.2f}' off that centroid, against a kern of "
        f"{result.kern_ft:.2f}' — {contact}, and the factor of safety against overturning "
        f"about {result.tipping_edge} is {result.fs_overturning:.2f}.")


def _spread_states(result: SpreadResult, soil, how: str) -> list[LimitState]:  # type: ignore[no-untyped-def]
    """Three rows: is it in the kern, does it bear, and does it stay standing."""
    states = [
        # Outside the kern the base lifts at one edge and the linear distribution stops
        # describing the contact, so this is a validity check on the row below it as much
        # as a limit state of its own — the identical reading `retaining_basis` gives the
        # same pair.
        LimitState("eccentricity", result.eccentricity_ft, result.kern_ft, "ft",
                   "the kern of the base's own section (S/A), computed on the polygon"),
        LimitState("overturning", REQUIRED_FS_OVERTURNING, result.fs_overturning, "",
                   "IRC R404.4", is_safety_factor=True),
    ]
    if result.bearing_psf is not None:
        states.append(LimitState(
            "bearing", result.bearing_psf, soil.allowable_bearing_psf, "psf",
            f"peak pressure under the rigid-body LINEAR distribution — ACI 318-19 "
            f"§13.3.4.3 forbids assuming a uniform one under a combined footing and none "
            f"is assumed; IBC Table 1806.2 class {soil.ibc_class}. {how}"))
    return states


def pier_station(ctx: EngineeringContext, pier: _Pier) -> tuple[float, float]:
    """The column's own plan position in feet — where its axial load actually stands.

    On a COMBINED footing this is nowhere near the union's centroid, and that offset is
    most of what a combined footing is for. Taking the load at the centroid instead would
    quietly delete the mechanism being graded.
    """
    post = ctx.plan.by_tag(pier.tag)
    position = getattr(post, "position", None)
    if position is None:
        return 0.0, 0.0
    return position.xy_m[0] / 0.3048, position.xy_m[1] / 0.3048
