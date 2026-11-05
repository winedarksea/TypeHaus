"""The duct standard's three advisory grades (decision #114).

* ``mep.duct_terminations`` — every duct end lands on a collar, a port, a case, a terminal,
  another duct or caps a served leg; every derived part has a row (M4-103/114/120, M1-103).
* ``mep.duct_supports`` — every derived hanger hangs from something (M1-105, M4-109).
* ``mep.duct_gauge`` — every round size has a gauge at the stated pressure class
  (M4-106/115).
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable, passed, unknown
from typehaus.quantities import M_PER_IN

_ENDS = "mep.duct_terminations"
_SUPPORTS = "mep.duct_supports"
_GAUGE = "mep.duct_gauge"
_CODE = "IMC 603"


def _standard(ctx: CheckContext):
    from typehaus.resolve.duct_standard import duct_standard

    return duct_standard(ctx.plan)[0]


def _missing(cid: str) -> list[Finding]:
    return [unknown(cid, "the house declares no DuctStandard, so no duct part is derived",
                    fix="declare one DuctStandard (decision #114)")]


@check(Tier.ADVISORY, _ENDS)
def duct_terminations(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.duct_terminations import end_landings

    if not ctx.model.ducts:
        return [not_applicable(_ENDS, "no duct runs")]
    if _standard(ctx) is None:
        return _missing(_ENDS)
    out: list[Finding] = []
    for end in end_landings(ctx.model):
        if end.landing is None:
            out.append(unknown(_ENDS, f"{end.run_tag}'s {'start' if end.index == 0 else 'end'}"
                                      " lands on no collar, port, case, terminal or duct",
                               (end.run_tag,), code=_CODE))
    gaps: dict[str, list[str]] = defaultdict(list)
    for part in ctx.model.duct_parts:
        if part.gap is not None:
            gaps[part.run_tag].append(f"{part.kind} at {part.other or part.port}: {part.gap}")
    out.extend(unknown(_ENDS, f"{tag}: {'; '.join(items)}", (tag,), code=_CODE,
                       fix="add the row to the house's DuctStandard")
               for tag, items in sorted(gaps.items()))
    named = sum(1 for part in ctx.model.duct_parts if part.gap is None)
    out.append(passed(_ENDS, f"{named} duct part(s) at ends and branches name a product, a "
                             "shop part or the terminal's own collar", code=_CODE))
    return out


@check(Tier.ADVISORY, _SUPPORTS)
def duct_supports(ctx: CheckContext) -> list[Finding]:
    if not ctx.model.ducts:
        return [not_applicable(_SUPPORTS, "no duct runs")]
    standard = _standard(ctx)
    if standard is None:
        return _missing(_SUPPORTS)
    hung: dict[str, int] = defaultdict(int)
    loose: dict[str, list[str]] = defaultdict(list)
    for support in ctx.model.duct_supports:
        if support.hangs_from is None:
            x, y, z = (v / M_PER_IN / 12 for v in support.point)
            loose[support.run_tag].append(f"({x:.1f}', {y:.1f}', {z:.1f}')")
        else:
            hung[support.run_tag] += 1
    unruled = sorted(d.tag for d in ctx.model.ducts if standard.support_for(
        "flex" if d.material == "flex" else "round" if d.diameter_m else "rectangular",
        d.diameter_m or (d.width_m + d.depth_m)) is None)
    out = [advisory(_SUPPORTS, f"{tag}: {len(points)} hanger(s) with no framing to hang "
                               f"from — {', '.join(points[:4])}"
                               f"{f' (+{len(points) - 4})' if len(points) > 4 else ''}",
                    (tag,), Result.UNKNOWN, code="IMC 603.10",
                    fix="detail the support (a saddle on the framing below, a trapeze off "
                        "the nearest member) or re-route")
           for tag, points in sorted(loose.items())]
    if unruled:
        out.append(unknown(_SUPPORTS, f"no support row covers {', '.join(unruled)}",
                           tuple(unruled), code="IMC 603.10"))
    out.append(passed(_SUPPORTS, f"{sum(hung.values())} hanger(s) on {len(hung)} run(s) hang "
                                 "from named framing", code="IMC 603.10"))
    return out


@check(Tier.ADVISORY, _GAUGE)
def duct_gauge(ctx: CheckContext) -> list[Finding]:
    round_runs = [d for d in ctx.model.ducts if d.diameter_m is not None
                  and d.material != "flex"]
    if not round_runs:
        return [not_applicable(_GAUGE, "no rigid round duct")]
    standard = _standard(ctx)
    if standard is None:
        return _missing(_GAUGE)
    bare = sorted({d.tag for d in round_runs
                   if standard.gauge_for(d.diameter_m, d.material or "galvanized") is None})
    out = []
    if bare:
        out.append(unknown(_GAUGE, f"no gauge row at {standard.pressure_class_in_wg:g} in. "
                                   f"w.g. covers {', '.join(bare)}", tuple(bare), code=_CODE))
    out.append(passed(_GAUGE, f"{len(round_runs) - len(bare)} round run(s) carry a gauge at "
                              f"{standard.pressure_class_in_wg:g} in. w.g.", code=_CODE))
    return out

