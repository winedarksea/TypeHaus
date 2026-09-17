"""The scorecard's arithmetic, on synthetic baselines — no house required.

`test_cmd_trial.py` drives the command against catlin; this pins what "the same finding"
means and what the filter keeps, which are the two decisions a loop's behaviour rests on.
"""

from __future__ import annotations

import json

from typehaus.cli.trial_score import (
    BASELINE_PATH,
    Scorecard,
    _digest,
    _key,
    load_baseline,
    render,
    write_baseline,
)


def _finding(check_id="mep.drain_slope", result="fail", tags=("PR-X",), message="short"):
    return {"check_id": check_id, "result": result, "severity": "warn",
            "element_tags": list(tags), "message": message}


def test_a_message_that_changed_is_a_different_finding() -> None:
    """Deliberate. A check that still FAILs a run but by a different number has told you
    something, and folding the two into one would hide exactly the improvement a loop is
    looking for."""
    assert _key(_finding(message='short 1.50"')) != _key(_finding(message='short 0.10"'))
    assert _key(_finding()) == _key(_finding())


def test_element_tag_order_is_not_part_of_the_identity() -> None:
    assert _key(_finding(tags=("A", "B"))) == _key(_finding(tags=("B", "A")))


def test_a_run_digest_moves_with_the_geometry_and_not_with_the_tag() -> None:
    row = {"tag": "PR-X", "path": [[0, 0], [1, 0]], "z": [1.0, 1.0], "size_in": 3.0,
           "developed_ft": 3.3, "storey": "main"}
    assert _digest(row) == _digest({**row, "tag": "PR-RENAMED"})
    assert _digest(row) != _digest({**row, "z": [1.0, 0.9]})


def test_a_baseline_round_trips_through_a_temp_file_and_replace(tmp_path) -> None:
    """Half a baseline written by an interrupted run would score every later trial against
    nonsense, so the write is temp-file + os.replace like `schedule/site_ops`."""
    payload = {"content_hash": "abc", "engine": "0.0.0", "findings": [], "runs": {}}
    path = write_baseline(tmp_path, payload)
    assert path == tmp_path / BASELINE_PATH
    assert not list(path.parent.glob("*.tmp"))
    assert load_baseline(tmp_path) == payload
    assert json.loads(path.read_text())["content_hash"] == "abc"


def test_no_baseline_is_none_rather_than_an_empty_dict(tmp_path) -> None:
    assert load_baseline(tmp_path) is None


def test_a_new_fail_is_the_only_thing_that_sets_a_non_zero_exit() -> None:
    assert Scorecard(house="h").exit_code == 0
    assert Scorecard(house="h", new_unknown=[_finding(result="unknown")]).exit_code == 0
    assert Scorecard(house="h", new_fail=[_finding()]).exit_code == 1


def test_the_coverage_lines_are_printed_even_on_a_clean_card() -> None:
    """An absent finding reads as a pass, which is the one failure mode a loop cannot
    recover from. The holes are named on every scorecard, not only on a bad one."""
    lines = render(Scorecard(house="h"))
    assert any("not graded" in line for line in lines)
    assert any("no finding changed" in line for line in lines)
