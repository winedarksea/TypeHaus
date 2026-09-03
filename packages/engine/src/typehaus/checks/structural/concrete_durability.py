"""Does the mix buy the exposure class it claims? (→ 12 §checks/structural)

A ``ConcreteSpec`` states an ACI 318-19 Table 19.3.1.1 exposure class *and* the mix meant to
satisfy it, and those two can disagree. Claiming F3 is free; buying F3 — w/cm ≤ 0.40, f'c
≥ 5,000, air-entrained — is not. A pour that says "class F3" over a 0.50 w/cm mix is a
specification that will be read by a ready-mix plant, batched as written, and will not be F3
concrete. Nothing else in the repo compares the two halves.

**This grades the SPEC against the STANDARD, not the pour against its site.** That boundary
is deliberate. Whether a given wall is really in freeze-thaw with deicing salt is a
site-and-detail judgement — proximity to a salted drive, whether the splash zone reaches it,
whether the drainage works — and deriving it from a plan geometry would be a guess wearing a
calculation's clothes. What the engine CAN do without guessing is hold a house to the
arithmetic of the class it chose, which is where the real error lives: a class picked
correctly and then not paid for.

**It deliberately does NOT second-guess the class from geometry, and that was tried.** A
first cut flagged any pour with an exterior face that claimed F0, on the argument that
Minnesota's weathering probability is Severe by rule rather than by map (MN Rules 1309.0301
subp. 2 writes "Severe" into IRC Table R301.2(1) outright). It fired 45 times on catlin — on
every buried strip footing, each of which states F0 *correctly and with a written reason*,
because a footing bearing below Ramsey County's 42" frost depth does not freeze. "Exterior"
and "exposed to freezing" are not the same predicate, this model has no honest way to tell
them apart (``Site.grade`` is a single global plane and cannot see a terrace), and a rule
that fires on every correct pour is worse than no rule. It also cost 45 UNKNOWNs, which
``haus print --sealed`` gates on. The right authority for "is this pour in the freezing zone"
is the person writing the ``ConcreteSpec``, and the note beside it.

``Result.NOT_APPLICABLE`` is EARNED here: it is returned only where the model contains no
concrete pour at all, which is positive evidence of absence. A house with concrete and no
``ConcreteSpec`` on it is UNKNOWN — a real gap, not an inapplicable rule.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable, passed, unknown
from typehaus.resolve.concrete import concrete_spec_for

#: ACI 318-19 Table 19.3.2.1 — the mix each exposure class requires, as
#: ``(max w/cm or None, min f'c psi)``. ``None`` where the class imposes no limit and only
#: the 2,500 psi floor of §19.2.1.1 applies.
_TABLE_19_3_2_1: dict[str, tuple[float | None, float]] = {
    "F0": (None, 2500.0), "F1": (0.55, 3500.0), "F2": (0.45, 4500.0), "F3": (0.40, 5000.0),
    "S0": (None, 2500.0), "S1": (0.50, 4000.0), "S2": (0.45, 4500.0), "S3": (0.45, 4500.0),
    "W0": (None, 2500.0), "W1": (0.50, 4000.0), "W2": (0.45, 4500.0),
    "C0": (None, 2500.0), "C1": (None, 2500.0), "C2": (0.40, 5000.0),
}

#: Classes that require entrained air (ACI 318-19 Table 19.3.3.1). The target depends on the
#: nominal maximum aggregate and on whether the exposure is moderate or severe; at 3/4"
#: aggregate — the size every catlin mix specifies — both F2 and F3 want 6.0%, and F1 wants
#: 6.0% at severe weathering too. A single figure is stated rather than the full table
#: because a house that specifies a different aggregate is told to check it rather than
#: graded against the wrong row.
_AIR_REQUIRED = {"F1", "F2", "F3"}
_AIR_TARGET_PCT = 6.0
_AIR_AGGREGATE_IN = 0.75

#: The element kinds a ``ConcreteSpec`` can reach. A pour with no assembly reaches none of
#: this — see ``integrity.element_assembly``, which is the rule that catches THAT.
_POUR_KINDS = ("FoundationWall", "Footing", "Pad", "Slab", "Post")


@check(Tier.STRUCTURAL, "structural.concrete_mix_matches_exposure")
def concrete_mix_matches_exposure(ctx: CheckContext) -> list[Finding]:
    """Every authored exposure class, against the mix ACI 318-19 Table 19.3.2.1 requires."""
    pours = [el for el in ctx.plan.all_elements() if el.element_kind in _POUR_KINDS
             and getattr(el, "assembly", None)]
    specs = [(el, concrete_spec_for(ctx.plan, el)) for el in pours]
    with_spec = [(el, spec) for el, spec in specs if spec is not None]

    if not specs:
        return [not_applicable(
            "structural.concrete_mix_matches_exposure",
            "this model contains no concrete pour that names an assembly, so there is no "
            "mix to grade — not a rule that does not apply to this building's concrete, but "
            "a building with none in scope",
            code="ACI 318-19 Table 19.3.2.1")]
    if not with_spec:
        return [unknown(
            "structural.concrete_mix_matches_exposure",
            f"{len(specs)} concrete pour(s) name an assembly and NONE of them states a "
            f"ConcreteSpec, so no exposure class, w/cm or air content is on record to grade. "
            f"That is a gap in the model, not an exposure this building does not have",
            tuple(sorted(el.tag for el, _ in specs))[:8],
            code="ACI 318-19 Table 19.3.2.1",
            fix="author `concrete=ConcreteSpec(...)` on the assembly's STRUCTURE layer")]

    out: list[Finding] = []
    graded = 0
    for element, spec in sorted(with_spec, key=lambda pair: pair[0].tag):
        problems = _mix_problems(spec)
        graded += 1
        if problems:
            out.append(structural_advisory(
                "structural.concrete_mix_matches_exposure",
                f"{element.tag}'s mix does not buy the exposure class it claims: "
                + "; ".join(problems)
                + ". A plant batches what the specification says, so a class the mix does "
                  "not deliver is a class this pour will not have",
                (element.tag,), Result.FAIL,
                "raise f'c / lower w/cm / entrain air to match the class, or state the "
                "class the mix actually is"))

    if not any(f.result is Result.FAIL for f in out):
        out.append(passed(
            "structural.concrete_mix_matches_exposure",
            f"{graded} concrete pour(s) state an exposure class and a mix that delivers it",
            code="ACI 318-19 Table 19.3.2.1"))
    return out


def _mix_problems(spec: Any) -> list[str]:
    """Every way this spec's mix falls short of the classes it declares, named one by one.

    Reported together rather than first-wins: an under-strength, over-wet, unentrained F3 mix
    has three things wrong with it, and fixing one at a time across three runs of the checker
    is how the other two get lost.
    """
    problems: list[str] = []
    declared = [value for value in (spec.exposure_f, spec.exposure_s, spec.exposure_w,
                                    spec.exposure_c) if value]
    if not declared:
        # No class claimed is not a claim broken. The engine has no honest way to decide
        # what class a pour SHOULD be (see the module docstring), so silence here is
        # silence, not a pass and not a failure.
        return problems

    max_wcm = min((_TABLE_19_3_2_1[c][0] for c in declared
                   if _TABLE_19_3_2_1[c][0] is not None), default=None)
    min_fc = max(_TABLE_19_3_2_1[c][1] for c in declared)
    governing = ", ".join(sorted(declared))

    if spec.fc_psi < min_fc:
        problems.append(f"f'c {spec.fc_psi:,.0f} psi against the {min_fc:,.0f} psi that "
                        f"class {governing} requires")
    if max_wcm is not None:
        if spec.w_cm_max is None:
            problems.append(f"class {governing} caps w/cm at {max_wcm:.2f} and this mix "
                            f"states none — an unstated w/cm is not a low one")
        elif spec.w_cm_max > max_wcm + 1e-9:
            problems.append(f"w/cm {spec.w_cm_max:.2f} against the {max_wcm:.2f} cap of "
                            f"class {governing}")

    needs_air = sorted(set(declared) & _AIR_REQUIRED)
    if needs_air:
        if spec.air_content_pct is None:
            problems.append(
                f"class {', '.join(needs_air)} is a freeze-thaw class and air entrainment is "
                f"its mechanism, but this mix states no air content. A non-entrained mix is "
                f"not F1/F2/F3 concrete at any strength (Table 19.3.3.1)")
        elif (spec.max_aggregate is not None
              and abs(spec.max_aggregate.inches - _AIR_AGGREGATE_IN) < 1e-6
              and spec.air_content_pct + (spec.air_tolerance_pct or 0.0)
              < _AIR_TARGET_PCT - 1e-9):
            problems.append(
                f"air {spec.air_content_pct:.1f}%"
                + (f" +/-{spec.air_tolerance_pct:.1f}" if spec.air_tolerance_pct else "")
                + f" against the {_AIR_TARGET_PCT:.1f}% Table 19.3.3.1 asks of class "
                  f"{', '.join(needs_air)} at {_AIR_AGGREGATE_IN:g}\" aggregate")
    return problems
