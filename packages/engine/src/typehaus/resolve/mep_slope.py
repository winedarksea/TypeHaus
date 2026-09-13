"""Solving a pipe run's inverts: the authored ones, and the ones a *grade* implies.

Split out of :mod:`typehaus.resolve.mep` for the reason AGENTS.md gives (that module ran
past 500 lines), and it is the right seam: everything here answers one question — what
elevation is this run at, at each of its vertices — and nothing else in ``mep.py`` asks it.

``typehaus.resolve.mep`` re-exports :func:`_pipe_vertex_z`, which is the name every existing
call site and test already imports.

Two trades route through it. A ``DuctRun`` now carries the same field set a ``PipeRun``
does — per-vertex elevations, a start/end pair, an optional grade — because a riser is a
riser whatever is inside it, and nothing in the solving is about water. The only
plumbing-specific thing left was the *check id* on a finding, so that is a parameter
(``prefix``): a duct reports ``integrity.duct_run_elevations``, a pipe
``integrity.pipe_run_elevations``, and one solver answers both.
"""

from __future__ import annotations

from typing import Protocol

from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import Length, inch
from typehaus.resolve.geometry import length, sub


class _SlopedRun(Protocol):
    """What the solver actually reads off a run — ``PipeRun`` and ``DuctRun`` both do."""

    tag: str
    start_elevation: Length | None
    end_elevation: Length | None
    elevations: tuple[Length | None, ...] | None
    slope_in_per_ft: float | None


def _pipe_vertex_z(run: _SlopedRun, path: list[tuple[float, float]],
                   datum: float, prefix: str = "pipe"
                   ) -> tuple[list[float] | None, list[Finding]]:
    """Absolute project-frame invert per path vertex.

    Authored ``elevations`` win; a ``None`` among them is *solved* at
    ``slope_in_per_ft`` over the developed plan length from the last authored invert
    (see :func:`_solve_slope`). Otherwise interpolate linearly between
    ``start_elevation``/``end_elevation`` over developed plan length. Both absent → None
    (no vertical information at all)."""
    if run.elevations is not None:
        if len(run.elevations) != len(path):
            return None, [Finding(
                severity=Severity.ERROR, check_id=f"integrity.{prefix}_run_elevations",
                message=(f"{prefix} run {run.tag} authors {len(run.elevations)} elevations "
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
            solved, findings = _solve_slope(run, path, z, authored, prefix)
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
                    severity=Severity.ERROR, check_id=f"integrity.{prefix}_run_elevations",
                    message=(f"{prefix} run {run.tag} {label}_elevation disagrees with "
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


def _slope_error(run: _SlopedRun, message: str, prefix: str) -> list[Finding]:
    return [Finding(severity=Severity.ERROR, check_id=f"integrity.{prefix}_run_slope",
                    message=f"{prefix} run {run.tag} {message}",
                    element_tags=(run.tag,), result=Result.FAIL)]


def _solve_slope(run: _SlopedRun, path: list[tuple[float, float]],
                 z: list[float | None], authored: list[bool], prefix: str = "pipe"
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
                                    "slope_in_per_ft to solve it from", prefix)
    if not any(authored):
        return z, _slope_error(run, "states slope_in_per_ft but authors no invert at all "
                                    "— a grade needs somewhere to start from", prefix)
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
                 "leg has no plan run to fall over, so both its ends must be authored",
            prefix)
    return z, []


# ---------------------------------------------------------------------------
# The minimum grade a drain must hold, and the document that says so.
# ---------------------------------------------------------------------------
#
# **This lives in ``resolve`` because both ``checks/`` and ``routing/`` need it and neither
# may import the other.** ``routing/gravity.minimum_slope`` and ``mep.drain_slope`` each
# carried their own copy of the pair of numbers, and a verdict that disagreed with the
# router about whether a route was feasible would be worse than either being wrong alone.
#
# ** MINNESOTA IS NOT AN IRC PLUMBING STATE, AND THE ENGINE SAID IT WAS. ** Minn. R.
# 1309.0010 subp. 3.D **deletes IRC chapters 25 through 33**; P3005 is in chapter 30. What
# governs is Minn. R. ch. 4714, which adopts the UPC, and **UPC 708.0 is 1/4" per foot at
# every size**. The `>3" -> 1/8"/ft` row both modules used to carry is IRC P3005.3's, and it
# has no force here: on catlin it read PR-B-MAIN-DRAIN's 4" line as holding twice its
# required grade when it is in fact 0.017"/ft over the minimum.
#
# The reduced-slope exception is real but narrow, and it is **not a house preference**: UPC
# 708.0 reaches it only for pipe 4" and larger, only where 1/4" is impractical, and only with
# the building official's approval — which is an approval of ONE pipe, granted on one set of
# drawings. So it is authored on the run (``PipeRun.reduced_slope_approval``) and the finding
# quotes the approval rather than claiming the code permits it.

#: UPC 708.0's grade, at every size. Not IRC P3005.3's two-row table.
MIN_DRAIN_SLOPE_IN_PER_FT = 0.25
#: The grade UPC 708.0's exception may reduce to, with the building official's approval.
REDUCED_SLOPE_IN_PER_FT = 0.125
#: The smallest pipe that exception reaches. Below this an authored approval is a FAIL: the
#: code has nothing to approve, so the paper cannot be what it claims to be.
REDUCED_SLOPE_MIN_DIAMETER_M = 4 * inch(1).meters

_UPC_SLOPE_CODE = "MN Plumbing Code (ch. 4714) 708.0"


def minimum_drain_slope_in_per_ft(diameter_m: float,
                                  approval: str | None = None) -> tuple[float, str]:
    """The grade this drain must hold, and the sentence a finding should cite for it.

    ``approval`` is ``PipeRun.reduced_slope_approval`` — the building official's approval
    for *this pipe*, authored verbatim. It lowers the grade only where UPC 708.0's exception
    actually reaches; on smaller pipe the caller is told the approval does not apply, and
    :func:`reduced_slope_approval_is_valid` is the predicate a check grades that with.
    """
    if approval and diameter_m >= REDUCED_SLOPE_MIN_DIAMETER_M - 1e-9:
        return (REDUCED_SLOPE_IN_PER_FT,
                f"{_UPC_SLOPE_CODE} exception (pipe 4\" and larger, where 1/4\" per foot is "
                f"impractical, as approved by the building official: {approval})")
    return (MIN_DRAIN_SLOPE_IN_PER_FT,
            f"{_UPC_SLOPE_CODE} — 1/4\" per foot at every size")


def reduced_slope_approval_is_valid(diameter_m: float, approval: str | None) -> bool:
    """Whether an authored reduced-slope approval is one UPC 708.0 could have granted.

    An approval on pipe under 4" is not a tight call to be advised about: the exception does
    not reach that pipe, so no building official could have approved what the run claims.
    """
    return not approval or diameter_m >= REDUCED_SLOPE_MIN_DIAMETER_M - 1e-9
