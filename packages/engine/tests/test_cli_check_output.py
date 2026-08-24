"""`haus check`'s output contract: what it prints, and when it exits non-zero.

Both halves were quietly wrong. ``Finding.render`` led with *severity*, and every passing
check is built by ``findings.passed()`` at ``Severity.WARN`` — so every one of catlin's passing
checks rendered as ``WARN``, and a reader who trusted the prefix read a green house as 716
warnings. Meanwhile the exit code gated on ``Severity.ERROR`` only, and an advisory failure is
``advisory(result=FAIL, severity=WARN)`` — so the command printed failures and exited 0,
which is why nothing scripted could use it as a gate.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from typehaus.checks.registry import Tier
from typehaus.cli._shared import ExitOn, TierName
from typehaus.cli.app import app
from typehaus.cli.cmd_build import _parse_only
from typehaus.findings import Finding, Result, Severity

from _helpers import CATLIN, STARTER

runner = CliRunner()


def _finding(result: Result, severity: Severity = Severity.WARN) -> Finding:
    return Finding(severity=severity, check_id="advisory.demo", message="demo", result=result)


@pytest.mark.parametrize("result", list(Result))
def test_render_leads_with_the_result_not_the_severity(result: Result) -> None:
    assert _finding(result).render().startswith(result.value.upper())


def test_an_error_severity_is_still_visible_after_the_result() -> None:
    """Result answers "did the rule hold"; severity answers "does it stop the build".
    Leading with the result must not lose the second question."""
    line = _finding(Result.FAIL, Severity.ERROR).render()
    assert line.startswith("FAIL (error) ")
    assert "(error)" not in _finding(Result.FAIL, Severity.WARN).render()


def test_the_cli_tier_enum_matches_the_registry() -> None:
    """`TierName` is duplicated in the CLI so `haus --version` does not import the checks
    package. Duplication is only safe while something proves the two agree."""
    assert {t.value for t in TierName} == {t.value for t in Tier}


def test_only_parses_result_names_and_all() -> None:
    assert _parse_only("all") is None
    assert _parse_only("fail,unknown") == frozenset({Result.FAIL, Result.UNKNOWN})
    assert _parse_only(" PASS , fail ") == frozenset({Result.PASS, Result.FAIL})


def test_only_rejects_a_typo_with_exit_2_not_a_traceback() -> None:
    result = runner.invoke(app, ["check", str(CATLIN), "--only", "warn"])
    assert result.exit_code == 2
    assert "--only" in result.output


def test_tier_is_a_choice_so_a_typo_is_not_a_traceback() -> None:
    """A bare ``Tier(tier)`` raised ValueError inside the command body and Typer printed a
    40-line traceback for a one-character typo."""
    result = runner.invoke(app, ["check", str(CATLIN), "--tier", "advisry"])
    assert result.exit_code == 2
    assert "Traceback" not in result.output


def test_check_hides_passing_findings_by_default() -> None:
    """Default output is failures + unevaluable rules only — never the passing majority.

    On catlin that is now the unevaluable ones alone: the house carries no FAIL. The
    assertion that matters here is the *filter*, so it is stated against both houses.
    """
    result = runner.invoke(app, ["check", str(CATLIN), "--plain"])
    lines = [ln for ln in result.output.splitlines() if ln[:1].isupper() and ":" in ln]
    assert lines, result.output
    assert not any(ln.startswith("PASS") for ln in lines)
    assert not any(ln.startswith("WARN") for ln in lines)


def test_check_exits_1_on_a_fail() -> None:
    """The gate half of the contract, on a house that actually fails.

    This used to ride on catlin's four accepted advisory FAILs. Two of those were the
    ventilation rooms (drawn 2026-08-16) and two were a bug in
    ``structural.foundation_unbalanced_fill`` (fixed the same day), so catlin exits 0 now and
    can no longer prove an exit code it does not produce. starter is unfinished by design —
    it carries real advisory FAILs at WARN severity, which is exactly the case the default
    gate exists to catch.
    """
    result = runner.invoke(app, ["check", str(STARTER), "--plain"])
    assert result.exit_code == 1
    lines = [ln for ln in result.output.splitlines() if ln[:1].isupper() and ":" in ln]
    assert any(ln.startswith("FAIL") for ln in lines), result.output


def test_exit_on_error_is_the_looser_gate() -> None:
    """`scripts/verify.sh` uses this one. It is looser than the default by construction: an
    advisory FAIL is ``severity=WARN``, so ERROR-only lets it through where the default
    stops. starter is now the house that shows the gap — it carries advisory FAILs and, since
    it grew its passive radon system (2026-08-16), no ERROR-severity finding at all, so the
    default gate closes on it and ERROR-only opens. catlin shows both open."""
    assert runner.invoke(app, ["check", str(STARTER), "--plain"]).exit_code == 1
    assert runner.invoke(
        app, ["check", str(STARTER), "--exit-on", ExitOn.error.value]).exit_code == 0
    assert runner.invoke(
        app, ["check", str(CATLIN), "--exit-on", ExitOn.error.value]).exit_code == 0


def test_catlin_carries_no_failures(catlin_model) -> None:
    """The reference house checks clean — 0 FAIL, not "0 errors".

    Asserted through the JSON surface rather than the exit code so the failure message
    names the offending finding instead of just saying 1 != 0.

    Between 2026-08-16 and 2026-08-23 this was `test_catlin_carries_only_its_accepted_
    failures`, pinning three `structural.deck_beam_span` advisories on BM-SG-BLW/BLC/BLE
    by (check_id, tags). They came from reading IRC Table R507.5(1) at its 12' joist-span
    row, which was the wrong row: the balcony joists span 10'-0" and then overhang the
    outer beams 6", and `structural.deck_joist_span` was counting that cantilever as span.
    The check reads the back span now (R507.6.1 bounds the overhang separately, in
    `structural.deck_joist_cantilever`), and the beams are three-ply KDAT 2x12, so all
    three PASS on their merits. Deleting the allow-list is the point — do not re-add one
    without an owner decision written down beside it.
    """
    import json

    result = runner.invoke(app, ["check", str(CATLIN), "--json"])
    payload = json.loads(result.output)
    failures = [
        (f["check_id"], tuple(sorted(f["element_tags"] or ())))
        for f in payload["findings"] if f["result"] == "fail"
    ]
    assert not failures, sorted(failures)


def test_exit_on_none_never_gates() -> None:
    result = runner.invoke(app, ["check", str(CATLIN), "--exit-on", "none"])
    assert result.exit_code == 0


def test_json_output_is_complete_regardless_of_only() -> None:
    """--only is a human-output filter. The machine surface must not lose findings to it."""
    import json

    result = runner.invoke(app, ["check", str(CATLIN), "--json", "--only", "fail"])
    payload = json.loads(result.output)
    assert len(payload["findings"]) == payload["pass"] + payload["fail"] + payload["unknown"]
    assert payload["pass"] > 0


def test_json_summary_agrees_with_json_on_the_counts_but_is_far_smaller() -> None:
    """`--json-summary` is the compact agent surface (#52): same pass/fail/unknown as
    `--json` (other tests, and callers, already assert on those three keys), but without a
    full `model_dump()` per finding — an order of magnitude smaller on catlin's ~700
    findings."""
    import json

    full = runner.invoke(app, ["check", str(CATLIN), "--json"])
    summary = runner.invoke(app, ["check", str(CATLIN), "--json-summary"])
    # Compared rather than pinned to 0: what this test is about is that the two machine
    # surfaces AGREE, not what catlin's exit code happens to be — that is
    # `test_catlin_carries_no_failures`'s job.
    assert full.exit_code == summary.exit_code
    full_payload = json.loads(full.output)
    summary_payload = json.loads(summary.output)
    assert summary_payload["pass"] == full_payload["pass"]
    assert summary_payload["fail"] == full_payload["fail"]
    assert summary_payload["unknown"] == full_payload["unknown"]
    assert "findings" not in summary_payload
    assert len(summary.output) < len(full.output) / 10


def test_json_summary_categories_sum_to_the_totals() -> None:
    """Each category is a check_id namespace (`structural.foo` -> `structural`); the
    per-category counts must reconcile with the top-level pass/fail/unknown exactly, since
    every finding lands in exactly one category."""
    import json

    result = runner.invoke(app, ["check", str(CATLIN), "--json-summary"])
    payload = json.loads(result.output)
    categories = payload["categories"]
    assert categories, payload
    assert sum(c["pass"] for c in categories.values()) == payload["pass"]
    assert sum(c["fail"] for c in categories.values()) == payload["fail"]
    assert sum(c["unknown"] for c in categories.values()) == payload["unknown"]
    assert isinstance(payload["failing_check_ids"], list)
    assert isinstance(payload["unknown_check_ids"], list)


def test_json_summary_surfaces_a_fail_on_the_starter_house() -> None:
    """starter carries real advisory FAILs (see test_check_exits_1_on_a_fail) — the summary
    must show them in `fail`/`fail_severity`, not only in the full `--json` dump."""
    import json

    result = runner.invoke(app, ["check", str(STARTER), "--json-summary"])
    payload = json.loads(result.output)
    assert payload["fail"] > 0
    assert payload["failing_check_ids"]
    assert sum(payload["fail_severity"].values()) == payload["fail"]
