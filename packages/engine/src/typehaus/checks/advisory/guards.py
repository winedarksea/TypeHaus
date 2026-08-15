"""Cable-guard spacing — trade practice, not code text.

R312.1.3 says 4", and a cable guard authored at 4" satisfies it on paper and fails at the
inspection. A tensioned cable is not a picket: push a 4"-spaced run with a knee and the
cables spread perhaps a quarter of their spacing, so the sphere goes through a guard that
measured compliant at rest. The published trade answer is 3" to 3-1/4" at a 4' post span,
tightened further as the span grows, because deflection scales with the unsupported run.

This is advisory precisely because the code text does not say it. It never blocks the permit
gate; it is the thing a cable-rail supplier tells you before you order 200' of cable at a
spacing that will not pass.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, passed, unknown

_CHECK_ID = "advisory.cable_guard_deflection"

#: Spacing a cable run holds at the reference post span. The trade range is 3"-3-1/4"; the
#: looser end is used so this never disagrees with a supplier who did the arithmetic.
_BASE_SPACING_IN = 3.25
#: The post span the base figure assumes. Beyond it the cable has more free length to give.
_REFERENCE_SPAN_FT = 4.0
#: How much tighter the spacing goes per additional foot of unsupported run.
_TIGHTEN_IN_PER_FT = 0.25
#: A spacing below this is a cable count nobody builds; the rule stops tightening there.
_FLOOR_SPACING_IN = 2.0


def max_cable_spacing_in(post_span_ft: float) -> float:
    """The spacing a cable run of this post span should hold, in inches."""
    over = max(post_span_ft - _REFERENCE_SPAN_FT, 0.0)
    return max(_BASE_SPACING_IN - _TIGHTEN_IN_PER_FT * over, _FLOOR_SPACING_IN)


@check(Tier.ADVISORY, _CHECK_ID)
def cable_guard_deflection(ctx: CheckContext) -> list[Finding]:
    """A cable guard's spacing allows for the ~25% deflection a tensioned cable has.

    UNKNOWN — never a pass — for a house with no cable guard in it: this rule has nothing
    to say about a picket guard, and saying "fine" about a thing it never looked at is how
    an advisory tier stops being read.
    """
    from typehaus.model.structure import Railing

    cable_guards = [e for e in ctx.plan.all_elements()
                    if isinstance(e, Railing) and e.infill == "cable"
                    and e.role in ("guard", "guard_and_handrail")]
    if not cable_guards:
        return [unknown(_CHECK_ID, "no guard in the plan is cable-filled, so cable "
                        "deflection has nothing to grade")]
    out: list[Finding] = []
    for guard in cable_guards:
        span_ft = guard.post_spacing.meters / 0.3048
        allowed = max_cable_spacing_in(span_ft)
        if guard.baluster_spacing is None:
            out.append(unknown(_CHECK_ID, f"{guard.tag} is cable-filled but states no "
                               "baluster_spacing (the clear gap between cables)",
                               (guard.tag,)))
        elif guard.baluster_spacing.inches > allowed + 1e-9:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_ID, result=Result.FAIL,
                element_tags=(guard.tag,),
                message=(f"{guard.tag} spaces its cables {guard.baluster_spacing.inches:.2f}\" "
                         f"over a {span_ft:.1f}' post span; a tensioned cable deflects about "
                         f"a quarter of its spacing under load, so trade practice is "
                         f"{allowed:.2f}\" here even though R312.1.3 reads 4\""),
                fix=(f"tighten the cable spacing to {allowed:.2f}\" or add an intermediate "
                     "post to shorten the unsupported run")))
        else:
            out.append(passed(_CHECK_ID, f"{guard.tag} spaces its cables "
                              f"{guard.baluster_spacing.inches:.2f}\" over a {span_ft:.1f}' "
                              f"post span, at or under the {allowed:.2f}\" that survives "
                              "the deflection a tensioned cable has under load"))
    return out
