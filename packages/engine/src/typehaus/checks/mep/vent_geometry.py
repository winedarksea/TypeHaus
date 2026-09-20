"""A vent's PROFILE — the one fact about vent piping nothing in this engine read.

``mep.vent_grade`` grades every vent run MONOTONE: from the drainage connection to the
terminal a vent may only rise. A vertex that sits below both its neighbours is a sag, and a
sag in a vent is a water trap — condensate collects in it, the vent seals, and the fixture
traps it protects start siphoning. Nothing graded it, so a profile that zig-zagged over and
under a duct bank passed every check in the house: ``mep.run_interference`` is happy with a
pipe that dodges, and ``mep.drain_slope`` never looks at ``system == "vent"``.

``mep.vent_grade_margin`` is the advisory half, the way ``mep.drain_slope_margin`` is the
advisory half of ``mep.drain_slope``: monotone is what the code asks for, and
:data:`_MIN_VENT_GRADE_IN_PER_FT` is what the house asks for on top of it.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _M_TO_FT, VERTICAL_PLAN_FT
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

#: The section that governs a vent's grade in Minnesota. **Not IRC P3104.1** — Minn. R.
#: 1309.0010 subp. 3.D deletes IRC chapters 25-33, and P3104 is in chapter 31; what governs
#: is the UPC as adopted by ch. 4714. UPC 905.1 ("Vent Grade and Connections"): vent pipes
#: shall be free of drops and sags, and every vent shall be graded and connected so as to
#: drip back to the drainage pipe by gravity. ``mep.drain_slope``'s ``708.0`` is the same
#: correction made for the drainage half.
_VENT_CODE = "MN Plumbing Code (ch. 4714) 905.1"

#: Inches of rise per foot of plan run this house asks a vent to hold back toward the
#: drain, over and above UPC 905.1's *free of drops and sags*. **It is not a code number**:
#: 905.1 states a direction and no figure, exactly as
#: ``MepPreferences.min_drain_slope_margin_in_per_ft`` is not UPC 708.0's number. 1/8"/ft is
#: the figure ``houses/catlin/plan/mep_venting.py``'s own header has always worked to, and
#: it is the grade a horizontal vent is set at in the field so that condensate returns
#: rather than beading and standing.
_MIN_VENT_GRADE_IN_PER_FT = 0.125

_ADVISORY = "ADVISORY — "


def _profile(run) -> list[tuple[int, float, float]] | None:
    """``(index, plan_ft, rise_in)`` per segment, or ``None`` when no elevations resolve.

    Two branches, ``mep.drain_slope``'s exactly: per-vertex ``z_m`` when the run carries a
    routed 3D path, else the ``z_start_m``/``z_end_m`` pair interpolated over the whole run.
    Elevations are storey-relative as authored and the resolver has already put them on one
    datum per run; a *difference* along one run is the same number either way, which is why
    this reads them without touching ``storeys``.
    """
    if run.z_m is not None and len(run.z_m) == len(run.path):
        out = []
        for index in range(len(run.path) - 1):
            a, b = run.path[index], run.path[index + 1]
            plan_ft = (((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5) * _M_TO_FT
            out.append((index, plan_ft, (run.z_m[index + 1] - run.z_m[index]) / M_PER_IN))
        return out
    if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
        return None
    # One segment standing for the whole run: with two inverts and nothing between them
    # there is no interior vertex that could be a sag, and the grade is the average.
    return [(0, run.length_m * _M_TO_FT, (run.z_end_m - run.z_start_m) / M_PER_IN)]


def _vents(ctx: CheckContext) -> list:
    return [r for r in ctx.model.pipe_runs if r.system == "vent"]


@check(Tier.CODE, "mep.vent_grade")
def vent_grade(ctx: CheckContext) -> list[Finding]:
    """A vent may only rise on its way to the terminal — no drop, no sag.

    UPC 905.1 asks for two things and they are one thing: *free of drops and sags*, and
    *graded to drip back to the drainage pipe by gravity*. A vent whose profile goes up,
    then down, then up has a low point, and a low point in a vent fills with condensate and
    seals. What is downstream of that is not a slow leak — it is the trap seals the vent
    exists to protect, drawn out by the next fixture that discharges.

    **The run's own path order is the direction of the test.** A vent is authored from its
    connection at the drainage piping to its terminal, the same way a drain is authored in
    flow order, so "rises toward the terminal" is "never falls in path order". A run that
    falls throughout — authored backwards — reports as such rather than as eight sags.

    **Vertical segments are exempt and carry no grade**, on
    :data:`~typehaus.checks.mep.plumbing_common.VERTICAL_PLAN_FT`, the tolerance
    ``mep.drain_slope`` and ``mep.drain_offset_geometry`` already share. A riser is the
    whole point of a vent; it is the horizontal legs between risers that hold water.

    This is what makes a run like ``PR-M-WC-VENT`` one decision rather than five: it cannot
    take whichever duct tier is free at each crossing, because once it is high it must
    stay high.
    """
    cid = "mep.vent_grade"
    vents = _vents(ctx)
    if not vents:
        return [_na(cid, "this model routes no vent piping, so no vent has a profile to "
                         "grade", code=_VENT_CODE)]
    out: list[Finding] = []
    for run in vents:
        profile = _profile(run)
        if profile is None:
            out.append(_unknown(cid, f"pipe run {run.tag} has no resolved elevations — "
                                     "neither per-vertex nor a start/end pair — so its "
                                     "profile cannot be read", (run.tag,), code=_VENT_CODE))
            continue
        drops = [(index, rise) for index, plan_ft, rise in profile if rise < -1e-9]
        if not drops:
            rises = [plan for _i, plan, rise in profile if plan > VERTICAL_PLAN_FT]
            out.append(_pass(
                cid, f"pipe run {run.tag} rises over every one of its {len(profile)} "
                     f"segment(s) ({len(rises)} of them horizontal) — no drop and no sag, "
                     "so condensate drains back to the drainage pipe by gravity",
                (run.tag,), code=_VENT_CODE))
            continue
        ups = [index for index, _plan, rise in profile if rise > 1e-9]
        worst = min(drops, key=lambda item: item[1])
        if not ups:
            detail = (f"pipe run {run.tag} FALLS over its whole length "
                      f"({sum(rise for _i, rise in drops):.2f}\" down) — it is drawn from "
                      "the terminal back to the drain, or it does not reach a terminal "
                      "at all")
        else:
            detail = (f"pipe run {run.tag} segment {worst[0]} drops {-worst[1]:.2f}\" after "
                      f"rising earlier — the vertex between them is a low point, and a low "
                      "point in a vent fills with condensate and seals")
        out.append(_fail(
            cid, detail + f". {len(drops)} of {len(profile)} segment(s) fall",
            (run.tag,), code=_VENT_CODE,
            fix="re-profile the run so it only ever rises toward its terminal: take the "
                "high side of every obstacle it crosses, or raise the whole leg. A vent "
                "cannot dodge up and over one duct and back down under the next"))
    return out


@check(Tier.ADVISORY, "mep.vent_grade_margin")
def vent_grade_margin(ctx: CheckContext) -> list[Finding]:
    """How much grade a horizontal vent holds back toward the drain, against 1/8"/ft.

    ``mep.vent_grade`` answers UPC 905.1's yes/no — does it ever fall. A leg at +0.018"/ft
    passes that as cleanly as one at +0.445"/ft, and the two are not the same building: the
    first is level within the tolerance anybody builds to, and a vent that is level in
    practice holds the condensate that lands in it.

    **PASS-with-a-prefix, never a FAIL**, and deliberately, the way
    ``mep.equipment_turndown`` reports an over-sized unit: UPC 905.1 states a direction and
    no number, so a shortfall against :data:`_MIN_VENT_GRADE_IN_PER_FT` is not a code defect
    and no authority grades it. The arithmetic is printed either way — which is most of the
    value here, since "holds 0.084"/ft at its flattest" is a fact nothing in the model could
    state before, on a PASS as much as on a shortfall.

    Vertical segments are skipped on ``VERTICAL_PLAN_FT``: a riser holds no grade, so it has
    no margin either. A run that falls anywhere is left to ``mep.vent_grade`` — one defect,
    one finding.
    """
    cid = "mep.vent_grade_margin"
    vents = _vents(ctx)
    if not vents:
        return [_na(cid, "this model routes no vent piping, so no vent has a grade to hold")]
    out: list[Finding] = []
    for run in vents:
        profile = _profile(run)
        if profile is None:
            continue  # mep.vent_grade says so, and says it once
        if any(rise < -1e-9 for _i, _p, rise in profile):
            continue  # a drop is mep.vent_grade's FAIL, not a thin margin
        horizontal = [(index, plan, rise) for index, plan, rise in profile
                      if plan > VERTICAL_PLAN_FT]
        if not horizontal:
            continue  # all riser — nothing here holds a grade
        flattest = min(horizontal, key=lambda item: item[2] / item[1])
        grade = flattest[2] / flattest[1]
        held = (f"pipe run {run.tag} holds {grade:.3f}\"/ft at its flattest "
                f"(segment {flattest[0]}, {flattest[1]:.2f} ft of plan)")
        if grade >= _MIN_VENT_GRADE_IN_PER_FT - 1e-9:
            out.append(_pass(cid, held + f", at or over the {_MIN_VENT_GRADE_IN_PER_FT}\"/ft "
                                         "this house grades a vent to", (run.tag,)))
        else:
            out.append(_pass(
                cid, _ADVISORY + held + f" — under the {_MIN_VENT_GRADE_IN_PER_FT}\"/ft this "
                "house asks a horizontal vent to hold back toward the drain. Not a FAIL: "
                "UPC 905.1 states a direction and no figure, and this leg does rise. It is "
                "flat enough that the tolerance a hanger is set to could level it, and a "
                "level vent keeps the condensate that lands in it",
                (run.tag,)))
    if not out:
        return [_unknown(cid, f"{len(vents)} vent run(s), and not one has a horizontal "
                              "segment whose grade could be measured — every one is "
                              "vertical, or carries no resolved elevations")]
    return out
