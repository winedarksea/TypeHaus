"""Hot-water pipe insulation against R-3, per run (decision #154).

MN 1322 adopts the 2012 IECC residential chapters 2-5 (Minn. R. 1322.0010) and leaves
R403.4 alone (1322.0403 amends only R403.2.1, R403.5, R403.12), so R403.4.2 stands: hot
water pipe takes R-3 where it is (1) larger than 3/4", (2) serving more than one dwelling,
(3) from the water heater to kitchen outlets, (4) outside the conditioned space, (5) from the
heater to a distribution manifold, (6) under a slab, (7) buried, (8) supply/return of a
recirculation loop, or (9) longer than Table R403.4.2's run length (3/8" 30 ft, 1/2" 20 ft,
3/4" 10 ft, over 3/4" 5 ft, from the manifold to the point of use); "all remaining piping
shall be insulated to at least R-3 or meet the run length requirements". Read in ICC's
2012-13 code-change proposals RE-R403.4.2 (docs/local-code-notes/mn-1322-r403-pipe.md).

Derived here: 1, 3 (the run serves a fixture or appliance whose type declares
``kitchen_outlet``, wherever its room), 4/6/7 (a step outside a conditioned room), 9 (developed
run length: a branch starts at the manifold, so it is a lower bound). Not derived: 2, 5, 8.
Refrigerant linesets (R403.3, below 55 F) are ungraded: their own standard (#139).
A spec names a ``PipeInsulationStandard`` row; no row, or no R, is UNKNOWN.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.duct_insulation import _Cells, _steps
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_FT, M_PER_IN

CID = "mep.pipe_insulation"
CODE = "MN Rules 1322.0010 (2012 IECC) R403.4.2"
R_MIN = 3.0
#: Table R403.4.2: (nominal diameter in, max run ft); over 3/4" is 5 ft.
RUN_FT = ((0.375, 30.0), (0.5, 20.0), (0.75, 10.0))
OVER_FT = 5.0
OUTSIDE = frozenset({"ground", "exterior", "unconditioned", "over_ceiling"})


def _run_limit_ft(d_in: float) -> float:
    return next((ft for size, ft in RUN_FT if d_in <= size + 1e-3), OVER_FT)


def _kitchen_tags(plan: Any) -> frozenset[str]:
    """Tags of the placed fixtures and appliances whose type declares ``kitchen_outlet``."""
    lib = plan.library
    kinds = {t.tag for t in (*lib.fixture_types, *lib.appliance_types) if t.kitchen_outlet}
    return frozenset(e.tag for e in plan.all_elements()
                     if getattr(e, "type_ref", None) in kinds)


def _triggers(run: Any, cells: _Cells, kitchen: frozenset[str]) -> list[str]:
    d_in = run.diameter_m / M_PER_IN
    out = []
    if d_in > 0.75 + 1e-3:
        out.append(f'{d_in:g}" is larger than 3/4" (item 1)')
    elif run.length_m / M_PER_FT > _run_limit_ft(d_in) + 1e-6:
        out.append(f'{run.length_m / M_PER_FT:.1f} ft of {d_in:g}" is past Table R403.4.2\'s '
                   f"{_run_limit_ft(d_in):g} ft (item 9)")
    if served := sorted(kitchen.intersection(run.serves)):
        out.append(f"it serves kitchen outlet {', '.join(served)} (item 3)")
    if run.z_m and len(run.z_m) == len(run.path):
        outside = sum(ln for _, ln, cls in _steps(run, cells) if cls in OUTSIDE)
        if outside > 1e-6:
            out.append(f"{outside / M_PER_FT:.1f} ft lie outside the conditioned space "
                       "(items 4, 6, 7)")
    return out


@check(Tier.CODE, CID)
def pipe_insulation(ctx: CheckContext) -> list[Finding]:
    """R403.4.2 — each hot-water run's insulation spec against R-3 where the code asks."""
    from typehaus.model.pipe_insulation import PipeInsulationStandard

    runs = [r for r in ctx.model.pipe_runs if r.system == "water_hot"]
    if not runs:
        return [by_result(CID, Result.NOT_APPLICABLE, "no hot-water run is modeled", (), CODE)]
    found = [e for e in ctx.plan.all_elements() if isinstance(e, PipeInsulationStandard)]
    rows = {r.spec: r for s in found for r in s.insulations}
    cells, kitchen = _Cells(ctx.model), _kitchen_tags(ctx.plan)
    out, free = [], []
    for run in sorted(runs, key=lambda r: r.tag):
        why = _triggers(run, cells, kitchen)
        tags = (run.tag,)
        if not why:
            free.append(run.tag)
            continue
        need = f"{run.tag} needs R-{R_MIN:g}: {'; '.join(why)}"
        if not run.insulation:
            out.append(by_result(CID, Result.FAIL, f"{need}, and is bare", tags, CODE,
                                 fix="name a PipeInsulationStandard spec on the run"))
            continue
        row = rows.get(run.insulation)
        if row is None or row.r_value is None:
            out.append(by_result(CID, Result.UNKNOWN, f"{need}; {run.insulation!r} has no "
                                 "PipeInsulationStandard row with an R", tags, CODE))
        elif row.r_value + 1e-9 < R_MIN:
            out.append(by_result(CID, Result.FAIL, f"{need}; {row.spec} is only "
                                 f"R-{row.r_value:g}", tags, CODE))
        else:
            out.append(by_result(CID, Result.PASS, f"{need}; {row.spec} is "
                                 f"R-{row.r_value:g}", tags, CODE))
    if free:
        out.append(by_result(CID, Result.PASS, f"{len(free)} hot-water run(s) trigger no "
                             "R403.4.2 item derived here (3/4\" or less, inside Table "
                             "R403.4.2's run length, indoors, no kitchen outlet; items 2, 5, 8 "
                             "unread): "
                             f"{', '.join(free)}", tuple(free), CODE))
    return out
