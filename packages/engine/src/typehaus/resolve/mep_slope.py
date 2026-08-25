"""Solving a pipe run's inverts: the authored ones, and the ones a *grade* implies.

Split out of :mod:`typehaus.resolve.mep` for the reason AGENTS.md gives (that module ran
past 500 lines), and it is the right seam: everything here answers one question — what
elevation is this run at, at each of its vertices — and nothing else in ``mep.py`` asks it.

``typehaus.resolve.mep`` re-exports :func:`_pipe_vertex_z`, which is the name every existing
call site and test already imports.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.mep import PipeRun
from typehaus.quantities import inch
from typehaus.resolve.geometry import length, sub


def _pipe_vertex_z(run: PipeRun, path: list[tuple[float, float]],
                   datum: float) -> tuple[list[float] | None, list[Finding]]:
    """Absolute project-frame invert per path vertex.

    Authored ``elevations`` win; a ``None`` among them is *solved* at
    ``slope_in_per_ft`` over the developed plan length from the last authored invert
    (see :func:`_solve_slope`). Otherwise interpolate linearly between
    ``start_elevation``/``end_elevation`` over developed plan length — exactly the old
    two-invert behaviour, so legacy runs resolve unchanged. Both absent → None (no
    vertical information at all, matching the old None/None endpoints)."""
    if run.elevations is not None:
        if len(run.elevations) != len(path):
            return None, [Finding(
                severity=Severity.ERROR, check_id="integrity.pipe_run_elevations",
                message=(f"pipe run {run.tag} authors {len(run.elevations)} elevations "
                         f"for {len(path)} path points — one invert per vertex"),
                element_tags=(run.tag,), result=Result.FAIL)]
        z: list[float | None] = [None if e is None else datum + e.meters
                                 for e in run.elevations]
        authored = [value is not None for value in z]
        if z[0] is None and run.start_elevation is not None:
            z[0] = datum + run.start_elevation.meters
            authored[0] = True
        if z[-1] is None and run.end_elevation is not None:
            z[-1] = datum + run.end_elevation.meters
            authored[-1] = True
        if not all(authored):
            solved, findings = _solve_slope(run, path, z, authored)
            if findings:
                return None, findings
            z = solved
        for label, stated in (("start", run.start_elevation), ("end", run.end_elevation)):
            if stated is None:
                continue
            index = 0 if label == "start" else -1
            if run.elevations[index] is None:
                continue  # the endpoint *came from* this field; nothing to disagree with
            endpoint = z[index]
            if endpoint is None or abs(datum + stated.meters - endpoint) > 1e-6:
                return None, [Finding(
                    severity=Severity.ERROR, check_id="integrity.pipe_run_elevations",
                    message=(f"pipe run {run.tag} {label}_elevation disagrees with "
                             f"elevations[{0 if label == 'start' else -1}]"),
                    element_tags=(run.tag,), result=Result.FAIL)]
        return [0.0 if value is None else float(value) for value in z], []
    if run.start_elevation is None and run.end_elevation is None:
        return None, []
    stated_start = run.start_elevation or run.end_elevation
    stated_end = run.end_elevation or run.start_elevation
    assert stated_start is not None and stated_end is not None  # both-None returned above
    z0 = datum + stated_start.meters
    z1 = datum + stated_end.meters
    plan_cum = [0.0]
    for i in range(len(path) - 1):
        plan_cum.append(plan_cum[-1] + length(sub(path[i], path[i + 1])))
    total = plan_cum[-1] or 1.0
    return [z0 + (z1 - z0) * (c / total) for c in plan_cum], []


#: Metres of fall per (inch per foot) of grade, per metre of developed plan run.
_M_PER_IN_PER_FT = inch(1).meters / 0.3048


def _slope_error(run: PipeRun, message: str) -> list[Finding]:
    return [Finding(severity=Severity.ERROR, check_id="integrity.pipe_run_slope",
                    message=f"pipe run {run.tag} {message}",
                    element_tags=(run.tag,), result=Result.FAIL)]


def _solve_slope(run: PipeRun, path: list[tuple[float, float]],
                 z: list[float | None], authored: list[bool]
                 ) -> tuple[list[float | None], list[Finding]]:
    """Fill every unauthored invert by falling at ``slope_in_per_ft`` from the last one.

    A drain that runs at one grade for forty feet is *one* fact, and hand-computing its
    inverts off that grade is arithmetic the file can neither show its working for nor be
    checked against. Written this way the grade is the authored thing and every invert
    follows from it, which is also how the plumber reads it.

    Fall is measured over the **developed plan length**, the same datum ``mep.drain_slope``
    grades against and the same one the two-invert interpolation above already used. Leading
    unauthored vertices — a run whose only anchor is downstream — rise backward off that
    anchor at the same grade, because a grade is a grade in either direction.
    """
    if run.slope_in_per_ft is None:
        return z, _slope_error(run, "leaves an invert unauthored but states no "
                                    "slope_in_per_ft to solve it from")
    if not any(authored):
        return z, _slope_error(run, "states slope_in_per_ft but authors no invert at all "
                                    "— a grade needs somewhere to start from")
    fall_per_m = run.slope_in_per_ft * _M_PER_IN_PER_FT
    for i in range(1, len(z)):
        previous = z[i - 1]
        if z[i] is None and previous is not None:
            z[i] = previous - fall_per_m * length(sub(path[i], path[i - 1]))
    for i in range(len(z) - 2, -1, -1):
        following = z[i + 1]
        if z[i] is None and following is not None:
            z[i] = following + fall_per_m * length(sub(path[i + 1], path[i]))
    for i in range(len(path) - 1):
        if length(sub(path[i], path[i + 1])) >= 1e-6:
            continue
        if authored[i] and authored[i + 1]:
            continue
        return z, _slope_error(
            run, f"drops vertically at path point {i} with an unauthored invert; a vertical "
                 "leg has no plan run to fall over, so both its ends must be authored")
    return z, []
