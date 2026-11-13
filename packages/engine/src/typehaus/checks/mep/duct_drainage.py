"""``mep.duct_drainage`` — a pitched duct drains at its low points (house practice, opt-in).

A run opts in by declaring ``slope_in_per_ft`` or ``drains``; nothing else is graded, so a
level radial layer reports nothing. On such a run, off the resolved z profile:

* every interior low point is a drain (``DuctRun.drains``); a low END is fine where it lands
  on equipment or a terminal, which takes the water (a machine's port, a hood's collar);
* no leg 12" or longer in plan is level (under 1/16"/ft), since water stands on it;
* each drain names a vertex and a product, and its ``pipe_ref`` starts at the tap. No
  ``pipe_ref`` is a capped tee, emptied by hand: said, not failed.
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, advisory_fail, not_applicable, passed
from typehaus.quantities import M_PER_IN

CID = "mep.duct_drainage"
#: A leg this long in plan is graded for fall.
LEVEL_LEG_MIN_M = 12.0 * M_PER_IN
#: Under this fall (in./ft) a leg is level: half the 1/8" a pitched duct is given.
LEVEL_FALL_IN_PER_FT = 1.0 / 16.0
#: Two vertices this close in z are one plateau.
_Z_TOL_M = 1e-4
#: A drain pipe starts at its tap within the duct's radius plus this, in plan.
_PIPE_START_TOL_M = 1.0 * M_PER_IN
_DRAINING_ENDS = ("port", "collar", "equipment", "terminal")


@check(Tier.ADVISORY, CID)
def duct_drainage(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.duct_terminations import end_landings

    runs = sorted((e for e in ctx.plan.all_elements() if e.element_kind == "DuctRun"
                   and (e.slope_in_per_ft is not None or e.drains)), key=lambda e: e.tag)
    if not runs:
        return [not_applicable(CID, "no duct run declares a slope or a drain")]
    ducts = {d.tag: d for d in ctx.model.ducts}
    ends = {(e.run_tag, e.index): e.landing for e in end_landings(ctx.model)}
    out: list[Finding] = []
    for run in runs:
        duct = ducts.get(run.tag)
        if duct is None or len(duct.z_m) != len(duct.path) or len(duct.path) < 2:
            continue
        problems = _grade(ctx, run, duct, ends)
        out.extend(advisory_fail(CID, f"{run.tag}: {p}", (run.tag,)) for p in problems)
        if not problems:
            capped = [d for d in run.drains if d.pipe_ref is None]
            note = (f"; {len(capped)} capped tee(s), emptied by hand" if capped else "")
            out.append(passed(CID, f"{run.tag} falls to {len(run.drains)} drain(s) and its "
                                   f"draining ends, with no level leg of 12\" or more{note}",
                              (run.tag,)))
    return out


def _grade(ctx: CheckContext, run, duct, ends: dict) -> list[str]:
    from typehaus.resolve.duct_drains import drain_vertex

    path, z = duct.path, duct.z_m
    problems: list[str] = []
    drained: set[int] = set()
    for drain in run.drains:
        index = drain_vertex(duct, (drain.at.x.meters, drain.at.y.meters))
        if index is None:
            problems.append(f"the drain at ({drain.at.x}, {drain.at.y}) is on no vertex")
            continue
        drained.add(index)
        if ctx.plan.library.product(drain.product_ref) is None:
            problems.append(f"the drain at vertex {index} names no product "
                            f"{drain.product_ref!r}")
        if drain.pipe_ref is not None:
            problems.extend(_pipe_start(ctx, duct, drain, index))
    for first, last in _low_plateaus(z):
        if drained & set(range(first, last + 1)):
            continue
        at_end = 0 if first == 0 else (len(z) - 1 if last == len(z) - 1 else None)
        if at_end is not None and ends.get((duct.tag, at_end)) in _DRAINING_ENDS:
            continue
        where = "its end" if at_end is not None else "a low point"
        problems.append(f"{where} at vertex {first} ({path[first][0] / M_PER_IN:.1f}\", "
                        f"{path[first][1] / M_PER_IN:.1f}\") holds water and names no drain")
    for i in range(len(path) - 1):
        plan = math.dist(path[i], path[i + 1])
        fall = abs(z[i] - z[i + 1]) / M_PER_IN / (plan / 0.3048) if plan > 1e-9 else math.inf
        if plan >= LEVEL_LEG_MIN_M and fall < LEVEL_FALL_IN_PER_FT:
            problems.append(f"leg {i + 1} is level ({fall:.3f}\"/ft over "
                            f"{plan / M_PER_IN:.1f}\"), so water stands on it")
    return problems


def _low_plateaus(z) -> list[tuple[int, int]]:
    """(first, last) vertex of every run of equal z lower than both neighbours (one at an end)."""
    out, i = [], 0
    while i < len(z):
        j = i
        while j + 1 < len(z) and abs(z[j + 1] - z[i]) <= _Z_TOL_M:
            j += 1
        left = z[i - 1] > z[i] + _Z_TOL_M if i > 0 else None
        right = z[j + 1] > z[i] + _Z_TOL_M if j + 1 < len(z) else None
        if (left, right) in ((True, True), (None, True), (True, None)):
            out.append((i, j))
        i = j + 1
    return out


def _pipe_start(ctx: CheckContext, duct, drain, index: int) -> list[str]:
    pipe = next((r for r in ctx.model.pipe_runs if r.tag == drain.pipe_ref), None)
    if pipe is None:
        return [f"the drain at vertex {index} names pipe {drain.pipe_ref}, which resolves "
                "to no pipe run"]
    tap = next((p for p in ctx.model.duct_parts if p.kind == "drain_tee"
                and p.run_tag == duct.tag and p.other == drain.pipe_ref), None)
    start_z = pipe.z_m[0] if pipe.z_m else pipe.z_start_m
    reach = (duct.diameter_m or duct.width_m) / 2.0 + _PIPE_START_TOL_M
    if tap is None or math.dist(pipe.path[0], tap.point[:2]) > reach or (
            start_z is not None and start_z > tap.point[2]):
        return [f"{drain.pipe_ref} does not start at the drain at vertex {index}"]
    return []
