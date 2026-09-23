"""``mep.vent_grade`` / ``mep.vent_grade_margin`` against ``notes/vent_grade_basis.md``.

UPC 905.1 asks a vent to be free of drops and sags and to drip back to the drainage pipe by
gravity, and nothing in ``checks/mep/`` read a vent's profile at all: a run that zig-zagged
over one duct and back under the next passed every rule in the house. Every number asserted
below is hand-worked in the note, section by section.
"""

from __future__ import annotations

import copy

import pytest
from _helpers import check_context

from typehaus.checks.mep.vent_geometry import (
    _MIN_VENT_GRADE_IN_PER_FT,
    vent_grade,
    vent_grade_margin,
)
from typehaus.findings import Result, Severity
from typehaus.quantities import M_PER_IN


def _grade(model):
    return vent_grade(check_context(model=model))


def _margin(model):
    return vent_grade_margin(check_context(model=model))


def _for(findings, tag):
    return next(f for f in findings if tag in f.element_tags)


def _vent_index(model, tag) -> int:
    return next(i for i, r in enumerate(model.pipe_runs) if r.tag == tag)


def _with_run(model, index, run):
    clone = copy.copy(model)
    runs = list(clone.pipe_runs)
    runs[index] = run
    object.__setattr__(clone, "pipe_runs", tuple(runs))
    return clone


def test_catlin_is_eight_for_eight_on_the_code_check(catlin_model_ro) -> None:
    """Note §3: nothing in this house drops or sags on its way to a terminal."""
    findings = _grade(catlin_model_ro)
    assert len(findings) == 8
    assert all(f.result is Result.PASS for f in findings)
    assert all(f.code_ref == "MN Plumbing Code (ch. 4714) 905.1" for f in findings)


def test_the_citation_is_the_upc_and_not_the_irc(catlin_model_ro) -> None:
    """Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33, and P3104 is in chapter 31 —
    the same correction ``mep.drain_slope`` carries for 708.0 vs P3005.3."""
    from typehaus.checks.mep import vent_geometry

    assert "905.1" in vent_geometry._VENT_CODE
    assert "P3104" not in vent_geometry._VENT_CODE


def test_kitchen_vent_profile_is_the_note_section_1(catlin_model_ro) -> None:
    """Note §1, segment by segment: five authored rises off six authored elevations."""
    run = catlin_model_ro.pipe_runs[_vent_index(catlin_model_ro, "PR-M-KITCH-VENT")]
    elevations = [z / M_PER_IN for z in run.z_m]
    assert elevations == pytest.approx(
        [111.0, 112.0, 114.375, 116.75, 117.0, 117.25], abs=1e-6)
    rises = [b - a for a, b in zip(elevations, elevations[1:], strict=False)]
    assert rises == pytest.approx([1.0, 2.375, 2.375, 0.25, 0.25], abs=1e-6)
    assert _for(_grade(catlin_model_ro), "PR-M-KITCH-VENT").result is Result.PASS


def test_the_kitchen_vents_flattest_leg_is_the_advisory(catlin_model_ro) -> None:
    """0.250" over 14.0000 ft = 0.018"/ft — a seventh of the house's 1/8"/ft, and still a
    PASS, because 905.1 states a direction and no figure."""
    finding = _for(_margin(catlin_model_ro), "PR-M-KITCH-VENT")
    assert finding.result is Result.PASS
    assert finding.message.startswith("ADVISORY — ")
    assert '0.018"/ft at its flattest (segment 3, 14.00 ft of plan)' in finding.message


def test_bath1_vent_is_the_interpolated_branch_and_both_branches_agree(
        catlin_model_ro) -> None:
    """Note §2. Two authored inverts over 229.38" of developed plan = 0.052"/ft — and the
    same run read through the start/end branch has to produce the identical number."""
    index = _vent_index(catlin_model_ro, "PR-S-BATH1-VENT")
    run = catlin_model_ro.pipe_runs[index]
    assert run.length_m * 3.280839895 == pytest.approx(229.38 / 12.0, abs=2e-3)
    resolved = _for(_margin(catlin_model_ro), "PR-S-BATH1-VENT")
    assert '0.052"/ft' in resolved.message

    blind = copy.copy(run)
    object.__setattr__(blind, "z_m", None)
    legacy = _for(_margin(_with_run(catlin_model_ro, index, blind)), "PR-S-BATH1-VENT")
    assert '0.052"/ft' in legacy.message
    assert _for(_grade(_with_run(catlin_model_ro, index, blind)),
                "PR-S-BATH1-VENT").result is Result.PASS


def test_the_two_attic_runs_clear_the_house_grade(catlin_model_ro) -> None:
    """Note §3's last column: 0.152"/ft and 0.300"/ft are the only vents in catlin built at
    a grade a plumber would recognise as one."""
    findings = _margin(catlin_model_ro)
    assert _MIN_VENT_GRADE_IN_PER_FT == 0.125
    plain = [f for f in findings if not f.message.startswith("ADVISORY — ")]
    assert {t for f in plain for t in f.element_tags} == {
        "PR-A-STUBATH-VENT", "PR-A-BAR-VENT"}
    assert '0.152"/ft' in _for(findings, "PR-A-STUBATH-VENT").message
    assert '0.300"/ft' in _for(findings, "PR-A-BAR-VENT").message
    assert all(f.result is Result.PASS for f in findings), "advisory never FAILs"


def test_a_sag_fails_and_the_margin_stays_quiet(catlin_model_ro) -> None:
    """Drop the kitchen vent's fourth vertex a foot: it rises, falls, rises — a low point,
    which is the defect the check exists for. One defect, one finding: the margin check
    leaves a run with a drop in it to ``mep.vent_grade``."""
    index = _vent_index(catlin_model_ro, "PR-M-KITCH-VENT")
    run = catlin_model_ro.pipe_runs[index]
    sagged = copy.copy(run)
    z = list(run.z_m)
    z[3] = z[3] - 12.0 * M_PER_IN
    object.__setattr__(sagged, "z_m", z)
    model = _with_run(catlin_model_ro, index, sagged)

    finding = _for(_grade(model), "PR-M-KITCH-VENT")
    assert finding.result is Result.FAIL
    assert finding.severity is Severity.ERROR
    assert "low point" in finding.message
    assert not [f for f in _margin(model) if "PR-M-KITCH-VENT" in f.element_tags]


def test_a_run_drawn_backwards_says_so(catlin_model_ro) -> None:
    """A vent authored terminal-first falls throughout; reporting that as five sags would
    describe one authoring mistake five times."""
    index = _vent_index(catlin_model_ro, "PR-M-KITCH-VENT")
    run = catlin_model_ro.pipe_runs[index]
    flipped = copy.copy(run)
    object.__setattr__(flipped, "path", tuple(reversed(run.path)))
    object.__setattr__(flipped, "z_m", list(reversed(run.z_m)))
    finding = _for(_grade(_with_run(catlin_model_ro, index, flipped)), "PR-M-KITCH-VENT")
    assert finding.result is Result.FAIL
    assert "FALLS over its whole length" in finding.message


def test_a_riser_holds_no_grade_and_no_margin(catlin_model_ro) -> None:
    """``VERTICAL_PLAN_FT`` is shared with ``mep.drain_slope``, so the three checks cannot
    disagree about which segments exist. A run that is all riser is graded by neither."""
    import inspect

    from typehaus.checks.mep import vent_geometry

    assert "VERTICAL_PLAN_FT" in inspect.getsource(vent_geometry)
    index = _vent_index(catlin_model_ro, "PR-A-BAR-VENT")
    run = catlin_model_ro.pipe_runs[index]
    stack = copy.copy(run)
    object.__setattr__(stack, "path", (run.path[0], run.path[0], run.path[0]))
    object.__setattr__(stack, "z_m", list(run.z_m[:3]))
    model = _with_run(catlin_model_ro, index, stack)
    assert _for(_grade(model), "PR-A-BAR-VENT").result is Result.PASS
    assert not [f for f in _margin(model) if "PR-A-BAR-VENT" in f.element_tags]


def test_no_vents_is_not_applicable_and_no_elevations_is_unknown(catlin_model_ro) -> None:
    """N/A is earned from positive evidence of absence; a model that HAS vents and cannot
    read one is a different, honest, UNKNOWN."""
    model = copy.copy(catlin_model_ro)
    object.__setattr__(model, "pipe_runs",
                       tuple(r for r in model.pipe_runs if r.system != "vent"))
    verdict = _grade(model)
    assert len(verdict) == 1 and verdict[0].result is Result.NOT_APPLICABLE
    assert _margin(model)[0].result is Result.NOT_APPLICABLE

    model = copy.copy(catlin_model_ro)
    blinded = []
    for run in model.pipe_runs:
        if run.system != "vent":
            continue
        blind = copy.copy(run)
        object.__setattr__(blind, "z_m", None)
        object.__setattr__(blind, "z_start_m", None)
        object.__setattr__(blind, "z_end_m", None)
        blinded.append(blind)
    object.__setattr__(model, "pipe_runs", tuple(blinded))
    assert all(f.result is Result.UNKNOWN for f in _grade(model))
    verdict = _margin(model)
    assert len(verdict) == 1 and verdict[0].result is Result.UNKNOWN
