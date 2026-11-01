"""Transition binding checks: coverage, star overrides, and shadowing (→ 11b).

Binding is first-match (``model.patterns.first_match``, what the drawing reads), so a narrow
pattern authored behind a wildcard binds nothing: its notes, overlay, continuity and star
never print. TR-CATLIN-PLANT-RIM behind TR-CATLIN-RIM-BAND was exactly this (C5-E10).
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory_fail, failed, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.patterns import first_match, matches

CHECK_ID = "integrity.transition_shadowed"


@check(Tier.INTEGRITY, "integrity.condition_coverage")
def condition_coverage(ctx: CheckContext) -> list[Finding]:
    """Every derived boundary condition should be bound to a Transition or warn-flagged
    (warn-tier during design; hard-gated only in /permit-check, → 11b risk 8)."""
    out: list[Finding] = []
    transitions = ctx.plan.library.transitions
    for cond in ctx.model.conditions:
        if first_match(transitions, cond.key) is None:
            out.append(advisory_fail("integrity.condition_coverage",
                                     f"boundary condition {cond.key} has no Transition binding",
                                     cond.element_tags))
    return out


@check(Tier.INTEGRITY, "integrity.condition_star_override")
def condition_star_override(ctx: CheckContext) -> list[Finding]:
    """Per-condition star overrides must name condition keys that still exist (→ 11b).

    ``Transition.starred_conditions``/``unstarred_conditions`` address conditions by their
    exact derived key, and those keys are spelled out of assembly tags — rename an assembly
    and every override naming it silently stops applying, quietly re-curating the primary
    drawing set. An override that matches nothing is either a typo or a rename that never
    got followed through, so it warns rather than degrading in silence.
    """
    out: list[Finding] = []
    derived = {cond.key for cond in ctx.model.conditions}
    for tr in ctx.plan.library.transitions:
        for field in ("starred_conditions", "unstarred_conditions"):
            for key in getattr(tr, field, ()):
                if key not in derived:
                    out.append(advisory_fail("integrity.condition_star_override",
                                             f"transition {tr.tag} {field} names {key!r}, which no "
                                             f"longer derives to any boundary condition",
                                             (tr.tag,)))
                elif not matches(tr.condition_pattern, key):
                    # The key is real, but this transition never binds it — the override is
                    # inert, and the detail is curated by whichever transition does bind it.
                    out.append(advisory_fail(
                        "integrity.condition_star_override",
                        f"transition {tr.tag} {field} names {key!r}, which its "
                        f"pattern {tr.condition_pattern!r} does not match",
                        (tr.tag,)))
                elif (binder := first_match(ctx.plan.library.transitions, key)) is not tr:
                    # Matched but bound first by an earlier transition: just as inert.
                    out.append(advisory_fail(
                        "integrity.condition_star_override",
                        f"transition {tr.tag} {field} names {key!r}, which "
                        f"{binder.tag} binds first", (tr.tag,)))
    return out


@check(Tier.INTEGRITY, CHECK_ID)
def transition_shadowed(ctx: CheckContext) -> list[Finding]:
    """A Transition that is first match for no derived key. Starred, it is a submittal
    sheet that silently never prints (ERROR). Unstarred and shadowed, its overlay and
    continuity never apply (warning). Unstarred and matching nothing, it is a binding held
    for a condition this house does not have: harmless, so silent."""
    transitions = tuple(ctx.plan.library.transitions)
    keys = sorted({cond.key for cond in ctx.model.conditions})
    winner = {key: first_match(transitions, key) for key in keys}
    out: list[Finding] = []
    for tr in transitions:
        reached = [key for key in keys if matches(tr.condition_pattern, key)]
        if any(winner[key] is tr for key in reached):
            continue
        if reached:
            by = sorted({winner[key].tag for key in reached})
            why = (f"matches {len(reached)} derived condition(s) but binds none: "
                   f"{', '.join(by)} comes first for every one (e.g. {reached[0]})")
            fix = "move it ahead of the wider pattern, or narrow that one"
        else:
            why = f"pattern {tr.condition_pattern!r} matches no derived condition"
            fix = "retarget the pattern (an assembly rename?) or delete the transition"
        msg = f"transition {tr.tag} {why}"
        if tr.star or tr.starred_conditions:
            out.append(failed(CHECK_ID, msg + " — its starred detail never prints", (tr.tag,),
                              fix=fix))
        elif reached:
            out.append(advisory_fail(CHECK_ID, msg, (tr.tag,), fix=fix))
    if not out and transitions:
        out.append(passed(CHECK_ID, f"no transition of {len(transitions)} is shadowed by "
                                    f"an earlier pattern"))
    return out
