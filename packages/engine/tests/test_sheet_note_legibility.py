"""``integrity.sheet_note_legibility`` — a note has to be legible on the sheet (→ 30).

The acceptance gate for the note work. INTEGRITY tier, and the same family as
``integrity.reveal_concentric``: the model says something it cannot mean. A bullet of 3,040
characters is not a long note, it is a note that will not print, and the model asserting it
will is the defect.
"""

from __future__ import annotations

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2024
from typehaus.checks.integrity.sheet_notes import _artefacts_in, sheet_note_legibility
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.findings import Result


def _run(model) -> list:
    return sheet_note_legibility(
        CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                     profile=MN_2024))


def test_catlin_passes_on_every_bound_note(catlin_model_ro):
    findings = _run(catlin_model_ro)
    assert findings
    bad = [f for f in findings if f.result is not Result.PASS]
    assert not bad, [f.message for f in bad]
    # Six files, not thirty-eight: the subject is what a Transition BINDS.
    assert len(findings) == 6


def test_a_note_file_nothing_binds_is_out_of_subject(catlin_model_ro):
    """`applied_to` frontmatter is not the test and never was — several catlin notes carry
    it and render nowhere, which is what notes/README.md used to get wrong."""
    graded = {f.element_tags[0] for f in _run(catlin_model_ro) if f.element_tags}
    assert "shower_niche" not in graded
    assert "roof_wall_eave_detail" in graded


def test_a_house_with_no_bound_notes_earns_not_applicable(starter_dir):
    """Earned from positive evidence of absence, per Result's contract — never `[]`."""
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(starter_dir).plan)
    findings = _run(model)
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE


@pytest.mark.parametrize(("line", "fragment"), [
    ("• see `notes/x.md`", "a backtick"),
    ("• **BOTH HALVES ARE BUILT**", "bold markdown"),
    ("• the [eave detail](notes/e.md)", "a markdown link"),
    ("• per plan/storeys/garage.py", "a repository path"),
    ("• breaks sauna.py::ceiling", "a pytest id"),
    ("| a | b |", "a table row"),
    ("• 42″ below grade — confirm", "a character the DXF writer cannot set"),
])
def test_each_authoring_artefact_is_named(line: str, fragment: str) -> None:
    assert any(fragment in problem for problem in _artefacts_in([line]))


def test_one_problem_per_kind_not_per_occurrence() -> None:
    """A file that never migrated has a backtick on every line, and forty identical
    findings say nothing forty times."""
    problems = _artefacts_in([f"• a `tick` on line {i}" for i in range(40)])
    assert len([p for p in problems if "backtick" in p]) == 1


def test_a_clean_note_line_trips_nothing() -> None:
    assert _artefacts_in([
        '• Roof framing: 11-7/8" TJI 230 at 24" o.c. on a structural ridge beam.',
        "K1  Fasten liner furring with masonry anchors; verify embedment.",
    ]) == []


def test_an_unmigrated_file_is_unknown_and_not_a_pass(catlin_model_ro, tmp_path,
                                                      monkeypatch):
    """The legacy path is BETTER than what it replaced and is still not a pass.

    The rule cannot tell whether what survived the sanitizer is a construction note or an
    argument about one, and a rule that cannot evaluate is UNKNOWN (decision #32).
    """
    from typehaus.checks.integrity import sheet_notes as module

    legacy = tmp_path / "legacy.md"
    legacy.write_text("---\ntitle: x\n---\n\n# Notes\n\n- Some rationale, at length.\n")
    monkeypatch.setattr(module, "_bound_note_files",
                        lambda _ctx: {"notes/legacy.md": legacy})
    findings = _run(catlin_model_ro)
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "no '## Sheet notes' section" in findings[0].message


def test_an_over_budget_file_fails_with_the_row_count(catlin_model_ro, tmp_path,
                                                      monkeypatch):
    from typehaus.checks.integrity import sheet_notes as module

    fat = tmp_path / "fat.md"
    body = "\n".join(f"- Note number {i} about a thing on the wall, at some length."
                     for i in range(40))
    fat.write_text(f"## Sheet notes\n\n### General\n{body}\n")
    monkeypatch.setattr(module, "_bound_note_files", lambda _ctx: {"notes/fat.md": fat})
    finding = _run(catlin_model_ro)[0]
    assert finding.result is Result.FAIL
    assert "general notes (max" in finding.message or "wrapped rows" in finding.message


def test_the_check_is_an_error_so_the_permit_gate_sees_it(catlin_model_ro, tmp_path,
                                                          monkeypatch):
    from typehaus.checks.integrity import sheet_notes as module
    from typehaus.findings import Severity

    broken = tmp_path / "b.md"
    broken.write_text("## Sheet notes\n\n### General\n- Fasten as required.\n")
    monkeypatch.setattr(module, "_bound_note_files", lambda _ctx: {"notes/b.md": broken})
    finding = _run(catlin_model_ro)[0]
    assert finding.result is Result.FAIL
    assert finding.severity is Severity.ERROR
