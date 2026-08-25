"""``PipeRun.slope_in_per_ft``: the grade is the authored fact, the inverts follow from it.

A drain that runs at one grade for forty feet is *one* fact. Authoring twelve hand-computed
inverts off it is twelve chances to get the arithmetic wrong and no way for the file to say
what it meant — which is how the reference house ended up with runs whose comments declared
"a uniform 0.3"/ft" against numbers that were 0.2941 and 0.3013 on adjacent legs.

Three runs in catlin were converted (PR-B-BATH-DRAIN, PR-B-SAUNA-DRAIN, PR-B-COND); their
inverts are pinned below so the conversion is provably not a silent geometry change.
"""

from __future__ import annotations

import math

import pytest

from typehaus.findings import Result
from typehaus.model.enums import PipeSystem
from typehaus.model.mep import PipeRun
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.mep import _pipe_vertex_z

_FT = 0.3048


class _Storey:
    tag = "basement"
    elevation = ft(0)


def _solve(run: PipeRun):
    path = [point.xy_m for point in run.path]
    return _pipe_vertex_z(run, path, 0.0)


def _run(**kw) -> PipeRun:
    defaults = dict(uid="AAAAAAAAAA", tag="PR-T", system=PipeSystem.DRAIN, diameter=inch(3))
    defaults.update(kw)
    return PipeRun(**defaults)


# --- solving ---------------------------------------------------------------------------

def test_a_none_invert_falls_at_the_authored_grade() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0)), pt(ft(20), ft(0))),
               elevations=(ft(0), None, ft(-0.5)), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert not findings
    assert z[1] == pytest.approx(-0.3 * 10 * inch(1).meters, abs=1e-12)


def test_the_fall_is_over_developed_plan_length_not_vertex_count() -> None:
    """Two legs of different length must not fall by the same amount."""
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(4), ft(0)), pt(ft(20), ft(0))),
               elevations=(ft(0), None, None), slope_in_per_ft=0.25,
               start_elevation=ft(0))
    z, findings = _solve(run)
    assert not findings
    assert z[1] == pytest.approx(-0.25 * 4 * inch(1).meters, abs=1e-12)
    assert z[2] == pytest.approx(-0.25 * 20 * inch(1).meters, abs=1e-12)


def test_a_leading_none_rises_backward_off_the_anchor_downstream() -> None:
    """A grade is a grade in either direction; a run anchored only at its outfall solves."""
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(None, ft(-1)), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert not findings
    assert z[0] == pytest.approx(-1 * _FT + 0.3 * 10 * inch(1).meters, abs=1e-12)


def test_a_fully_authored_run_is_untouched() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))), elevations=(ft(1), ft(0.5)))
    z, findings = _solve(run)
    assert not findings
    assert z == pytest.approx([1 * _FT, 0.5 * _FT], abs=1e-12)


def test_the_start_elevation_can_be_the_anchor_a_none_solves_from() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(None, None), start_elevation=ft(2), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert not findings
    assert z[0] == pytest.approx(2 * _FT, abs=1e-12)
    assert z[1] < z[0]


# --- refusals ---------------------------------------------------------------------------

def test_a_none_with_no_grade_to_solve_it_is_an_error() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))), elevations=(ft(0), None))
    z, findings = _solve(run)
    assert z is None
    assert [f.check_id for f in findings] == ["integrity.pipe_run_slope"]
    assert findings[0].result is Result.FAIL


def test_a_grade_with_no_anchor_invert_is_an_error() -> None:
    """A grade needs somewhere to start from; picking a datum would be inventing one."""
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(None, None), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert z is None
    assert findings[0].check_id == "integrity.pipe_run_slope"
    assert "no invert at all" in findings[0].message


def test_a_vertical_leg_with_an_unauthored_end_is_an_error() -> None:
    """A drop has no plan run to fall over, so a grade cannot say where it lands."""
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(ft(0), None, None), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert z is None
    assert findings[0].check_id == "integrity.pipe_run_slope"
    assert "vertical" in findings[0].message


def test_a_vertical_leg_authored_at_both_ends_is_fine() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(ft(2), ft(0), None), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert not findings
    assert z[2] == pytest.approx(-0.3 * 10 * inch(1).meters, abs=1e-12)


def test_the_endpoint_cross_check_still_bites() -> None:
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(ft(1), ft(0)), start_elevation=ft(3))
    z, findings = _solve(run)
    assert z is None
    assert findings[0].check_id == "integrity.pipe_run_elevations"


def test_a_solved_endpoint_does_not_argue_with_the_field_it_came_from() -> None:
    """``elevations[0] is None`` means the endpoint *is* ``start_elevation``."""
    run = _run(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
               elevations=(None, ft(0)), start_elevation=ft(1))
    z, findings = _solve(run)
    assert not findings
    assert z[0] == pytest.approx(1 * _FT, abs=1e-12)


# --- the catlin conversion is not a geometry change --------------------------------------

#: Inverts as they resolve after the conversion, in PROJECT-FRAME feet (the resolved IR
#: carries absolute elevations; the source authors them storey-relative). PR-B-COND
#: reproduces its hand-authored numbers exactly; the two slab branches move by 0.004"-0.010",
#: which is the rounding that was in the old hand-computed numbers rather than a change of
#: grade — the comments on all three already declared the uniform 0.3"/ft this now solves at.
_PINNED_FT = {
    "PR-B-COND": [-1.675, -1.9, -2.0125, -2.10625, -8.36979],
    "PR-B-BATH-DRAIN": [-9.11979, -9.87779, -9.99446, -10.10696, -10.20779],
    "PR-B-SAUNA-DRAIN": [-8.95312, -9.83479, -9.85315, -9.90836, -10.17079],
}


@pytest.mark.parametrize("tag", sorted(_PINNED_FT))
def test_the_converted_runs_resolve_to_the_inverts_they_always_had(catlin_model, tag) -> None:
    run = next(r for r in catlin_model.pipe_runs if r.tag == tag)
    got = [round(z / _FT, 5) for z in run.z_m]
    assert got == pytest.approx(_PINNED_FT[tag], abs=1e-4), tag


def test_the_converted_runs_still_fall_at_the_grade_their_comments_declare(
        catlin_model) -> None:
    for tag in sorted(_PINNED_FT):
        run = next(r for r in catlin_model.pipe_runs if r.tag == tag)
        for i in range(len(run.path) - 1):
            plan = math.dist(run.path[i], run.path[i + 1])
            if plan < 1e-6:
                continue  # a vertical drop has no grade
            grade = (run.z_m[i] - run.z_m[i + 1]) / plan * 0.3048 / inch(1).meters
            assert grade == pytest.approx(0.3, abs=0.01), f"{tag} leg {i}"


def test_the_main_drain_stays_hand_authored(catlin_model) -> None:
    """PR-B-MAIN-DRAIN deliberately varies — ~2"/ft on the first leg so the 46' kitchen
    branch can hold 1/4"/ft off it — so a uniform grade is exactly what it must NOT have."""
    element = catlin_model.plan.by_tag("PR-B-MAIN-DRAIN")
    assert element.slope_in_per_ft is None
    assert all(e is not None for e in element.elevations)
