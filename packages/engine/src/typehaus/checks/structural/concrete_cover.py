"""Is the specified clear cover the minimum ACI requires? (→ 12 §checks/structural)

Cover is the whole corrosion-protection system for a reinforced pour. Everything else — the
mix, the w/cm, the coating — buys *time* against chloride reaching the bar; cover sets the
distance it has to travel, and nothing in this repo compared the figure a house authored
against the figure the Code demands. A pour could have stated 3/4" on a footing and passed
every one of 972 rules in silence.

**The exposure condition is derived from what the house AUTHORED, never from geometry.**
That boundary is the same one ``concrete_durability`` draws and for the same reason: the
first cut of that rule tried to infer "is this pour exposed" from plan geometry, fired 45
times on correctly-specified buried footings, and was deleted. So the condition here comes
from two authored facts and no measurements:

* a ``Footing`` or ``Pad`` bears on soil — that is what those kinds *mean* in this model, not
  a guess about where they sit — so its bottom mat is cast against ground and takes row 1;
* everything else is graded on the exposure classes its own ``ConcreteSpec`` declares. Any
  non-zero F/S/W/C class is a wet or weathered pour (row 2); all-zero classes is a dry
  interior one (row 3).

A pour with no ``ConcreteSpec`` is not graded here at all. That is not a hole — it is
``integrity.element_assembly`` and ``structural.concrete_mix_matches_exposure``'s subject,
and two rules reporting one gap is how a fix gets counted twice.

The bar governing is the LARGEST in the schedule, because row 2's threshold moves at #6 and
a bundle graded on its smallest bar is graded on the one that does not govern.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable, passed
from typehaus.resolve.concrete import concrete_spec_for, cover_for

#: ACI 318-19 Table 20.5.1.3.1, cast-in-place non-prestressed. Row 3 splits by member, which
#: is why it is two entries: a wall or slab gets 3/4" where a column gets 1-1/2".
_CAST_AGAINST_GROUND_IN = 3.0
_EXPOSED_IN = {True: 2.0, False: 1.5}          # keyed on "bar is #6 or larger"
_INTERIOR_SLAB_OR_WALL_IN = 0.75
_INTERIOR_COLUMN_IN = 1.5

#: Kinds whose bottom is cast against and permanently in contact with ground by definition.
_GROUND_CAST_KINDS = ("Footing", "Pad")
#: Kinds graded as a column rather than as a slab or wall in row 3.
_COLUMN_KINDS = ("Post",)

_POUR_KINDS = ("FoundationWall", "Footing", "Pad", "Slab", "Post")


@check(Tier.STRUCTURAL, "structural.concrete_cover_meets_minimum")
def concrete_cover_meets_minimum(ctx: CheckContext) -> list[Finding]:
    """Every reinforced pour's authored cover, against ACI 318-19 Table 20.5.1.3.1."""
    subjects = []
    for element in ctx.plan.all_elements():
        if element.element_kind not in _POUR_KINDS:
            continue
        schedule = getattr(element, "reinforcement", None)
        if schedule is None or not getattr(schedule, "bars", ()):
            continue
        spec = concrete_spec_for(ctx.plan, element)
        if spec is None and element.element_kind not in _GROUND_CAST_KINDS:
            # Unclassifiable without a declared exposure, and owned by another rule.
            continue
        subjects.append((element, schedule, spec))

    if not subjects:
        return [not_applicable(
            "structural.concrete_cover_meets_minimum",
            "this model contains no reinforced concrete pour that states a schedule, so "
            "there is no cover to grade — a building with no subject for the rule, not a "
            "rule that does not apply to this building's reinforcement",
            code="ACI 318-19 Table 20.5.1.3.1")]

    out: list[Finding] = []
    for element, schedule, spec in sorted(subjects, key=lambda row: row[0].tag):
        required, condition = _required_cover_in(element, spec, schedule)
        authored, source = cover_for(ctx.plan, element)
        if authored is None:
            out.append(structural_advisory(
                "structural.concrete_cover_meets_minimum",
                f"{element.tag} is reinforced and states no clear cover anywhere — not on "
                f"its schedule and not on its mix. {condition} wants "
                f"{required:.2f}\", and an unstated cover is not that figure: it is the "
                f"one dimension of a reinforced pour that a placer sets by eye if nobody "
                f"writes it down",
                (element.tag,), Result.FAIL,
                "author `cover=inch(...)` on the element's ReinforcementSpec"))
            continue
        if authored < required - 1e-9:
            out.append(structural_advisory(
                "structural.concrete_cover_meets_minimum",
                f"{element.tag} specifies {authored:.2f}\" clear cover on {source}, under "
                f"the {required:.2f}\" ACI 318-19 Table 20.5.1.3.1 requires: {condition}",
                (element.tag,), Result.FAIL,
                f"raise the cover to {required:.2f}\", or restate the exposure classes if "
                f"this pour is not the condition its mix declares"))

    if not any(f.result is Result.FAIL for f in out):
        out.append(passed(
            "structural.concrete_cover_meets_minimum",
            f"{len(subjects)} reinforced pour(s) specify clear cover at or above the ACI "
            f"318-19 Table 20.5.1.3.1 minimum for their exposure and bar size",
            code="ACI 318-19 Table 20.5.1.3.1"))
    return out


def _required_cover_in(element: Any, spec: Any, schedule: Any) -> tuple[float, str]:
    """``(inches, the condition in words)`` — the row of Table 20.5.1.3.1 this pour is on."""
    if element.element_kind in _GROUND_CAST_KINDS:
        return _CAST_AGAINST_GROUND_IN, (
            f"a {element.element_kind} bears on soil, so its mat is cast against and "
            f"permanently in contact with ground")

    if _is_exposed(spec):
        largest = max(bar.bar for bar in schedule.bars)
        declared = ", ".join(sorted(
            value for value in (spec.exposure_f, spec.exposure_s, spec.exposure_w,
                                spec.exposure_c)
            if value and not value.endswith("0")))
        return _EXPOSED_IN[largest >= 6], (
            f"its mix declares class {declared}, so this pour is exposed to weather or in "
            f"contact with ground, and its largest bar is a #{largest}")

    if element.element_kind in _COLUMN_KINDS:
        return _INTERIOR_COLUMN_IN, (
            "its mix declares no wet, salted or freezing exposure, and a column's primary "
            "bar and ties take 1-1/2\" even dry")
    return _INTERIOR_SLAB_OR_WALL_IN, (
        "its mix declares no wet, salted or freezing exposure, so it is a dry interior "
        "slab or wall")


def _is_exposed(spec: Any) -> bool:
    """Does this mix declare any exposure beyond the four "0" classes?

    ``None`` is not "0". A mix that leaves ``exposure_s`` unset — as catlin's three do,
    deliberately, because nobody has run a soil sulfate test — has not claimed the pour is
    dry; it has said nothing. Only an explicit ``S0`` is evidence of absence, and this
    predicate reads an unset field as no evidence either way rather than as a class.
    """
    declared = [value for value in (spec.exposure_f, spec.exposure_s, spec.exposure_w,
                                    spec.exposure_c) if value]
    return any(not value.endswith("0") for value in declared)
