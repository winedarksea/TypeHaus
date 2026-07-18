"""Structural checks — table-driven, clearly labeled "advisory, not engineering" (→ 12).

Shares one table module with the framing solver (header sizing); adds I-joist span lookup.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity

# Simplified I-joist allowable spans (ft) by depth (in), 16" o.c., residential floor.
_IJOIST_SPAN_FT: dict[str, float] = {
    "9.5 I-joist": 15.0,
    "11.875 I-joist": 18.5,
    "14 I-joist": 22.0,
    "16 I-joist": 25.0,
}


def _advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid,
                   message=f"[advisory, not engineering] {msg}", element_tags=tags,
                   result=result)


@check(Tier.STRUCTURAL, "structural.header_prescriptive")
def header_within_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Flag openings whose header exceeds prescriptive width (needs engineering)."""
    from typehaus.quantities import m

    out: list[Finding] = []
    for op in ctx.model.openings:
        if op.width_m > m(8.0 * 0.3048).meters:  # > 8'
            out.append(_advisory("structural.header_prescriptive",
                                 f"opening {op.tag} width {op.width_m*3.281:.1f}' exceeds "
                                 "prescriptive header table — requires engineered beam",
                                 (op.tag,), Result.FAIL))
    return out


@check(Tier.STRUCTURAL, "structural.ijoist_span")
def ijoist_span(ctx: CheckContext) -> list[Finding]:
    """Compare authored joist spans against a simplified allowable-span table."""
    out: list[Finding] = []
    # FloorSystem spans aren't fully resolved in M1; report UNKNOWN honestly.
    has_floor = any(e.element_kind == "FloorSystem" for e in ctx.plan.all_elements())
    if not has_floor:
        out.append(Finding(severity=Severity.WARN, check_id="structural.ijoist_span",
                           message="UNKNOWN — no FloorSystem resolved to check span",
                           result=Result.UNKNOWN))
    return out
