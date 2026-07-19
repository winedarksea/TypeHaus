"""HVAC checks — duct/joist-bay coordination (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.mep import is_parallel_to_floor

_M_TO_IN = 39.37007874015748


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, result=Result.UNKNOWN)


@check(Tier.STRUCTURAL, "mep.duct_joist_bay")
def duct_joist_bay(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay":
            continue
        if duct.floor_ref is None or not any(f.tag == duct.floor_ref for f in ctx.model.floors):
            out.append(_unknown(
                "mep.duct_joist_bay", f"duct {duct.tag} floor_ref did not resolve",
                (duct.tag,),
            ))
            continue
        if duct.conflicts or not duct.depth_ok:
            problems = list(duct.conflicts)
            if not duct.depth_ok:
                problems.append(f"depth {duct.depth_m * _M_TO_IN:.1f}\" exceeds joist depth")
            out.append(_fail(
                "mep.duct_joist_bay", f"duct {duct.tag}: " + "; ".join(problems), (duct.tag,),
            ))
            continue
        note = f"duct {duct.tag} occupies its joist bay cleanly"
        if duct.crossings:
            points = ", ".join(
                f"({x * _M_TO_IN / 12:.1f}', {y * _M_TO_IN / 12:.1f}')" for x, y in duct.crossings
            )
            note += (f"; crosses bearing wall(s) at {points} — "
                    "provide fire blocking per R302.11")
        out.append(_pass("mep.duct_joist_bay", note, (duct.tag,)))
    return out


@check(Tier.ADVISORY, "mep.duct_direction_hint")
def duct_direction_hint(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    floors = {f.tag: f for f in ctx.model.floors}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        if not is_parallel_to_floor(list(duct.path), floors[duct.floor_ref]):
            out.append(_advisory_fail(
                "mep.duct_direction_hint",
                f"duct {duct.tag} runs across joists in JOIST_BAY routing — "
                "route across joists in a soffit or chase", (duct.tag,),
            ))
    return out
