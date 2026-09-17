"""``haus trial`` against the reference house. Nothing under ``plan/`` may change."""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest
from typer.testing import CliRunner

from typehaus.cli.app import app
from typehaus.cli.trial_score import BASELINE_PATH

pytestmark = pytest.mark.slow

_CATLIN = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _plan_digest() -> dict[str, str]:
    return {str(p.relative_to(_CATLIN)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((_CATLIN / "plan").rglob("*.py"))}


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    return CliRunner()


def test_recording_a_baseline_touches_no_plan_file(runner) -> None:
    before = _plan_digest()
    result = runner.invoke(app, ["trial", str(_CATLIN), "--record"])
    assert result.exit_code == 0, result.output
    assert (_CATLIN / BASELINE_PATH).is_file()
    assert _plan_digest() == before


def test_an_unedited_tree_scores_clean_against_its_own_baseline(runner) -> None:
    """The scorecard's null case, and the one that says the machinery is honest: recording
    and immediately scoring must report nothing, or every later reading is noise."""
    assert runner.invoke(app, ["trial", str(_CATLIN), "--record"]).exit_code == 0
    result = runner.invoke(app, ["trial", str(_CATLIN)])
    assert result.exit_code == 0, result.output
    assert "no finding changed" in result.output
    assert "no plan file changed since the baseline" in result.output


def test_the_baseline_carries_every_check_even_though_the_diff_is_filtered(runner) -> None:
    """Recording only the MEP set would make a baseline useless the moment somebody wanted
    to ask a different question, and re-recording to change the question would mean
    re-recording AFTER the edit — which is the mistake that makes a scorecard lie."""
    assert runner.invoke(app, ["trial", str(_CATLIN), "--record"]).exit_code == 0
    payload = json.loads((_CATLIN / BASELINE_PATH).read_text())
    families = {str(row["check_id"]).split(".")[0] for row in payload["findings"]}
    assert families - {"mep", "integrity", "structural"}, families
    assert payload["runs"], "the run schedule is half of what a trial reports"
    assert all("digest" in entry for entry in payload["runs"].values())


def test_json_is_the_same_scorecard_and_names_its_coverage_gaps(runner) -> None:
    assert runner.invoke(app, ["trial", str(_CATLIN), "--record"]).exit_code == 0
    result = runner.invoke(app, ["trial", str(_CATLIN), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["new_fail"] == []
    assert payload["coverage"], "a silent hole reads as a pass"


def test_a_bad_check_set_is_refused_rather_than_guessed(runner) -> None:
    result = runner.invoke(app, ["trial", str(_CATLIN), "--checks", "nonsense"])
    assert result.exit_code == 2, result.output
