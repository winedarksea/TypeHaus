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


# `haus check` on catlin is a full registry run, ~20 s, and these two invocations were each
# made twice for the same bytes. Module scope, not session: `--dist loadfile` keeps a module
# on one worker, and nothing outside this file wants a CliRunner result.
@pytest.fixture(scope="module")
def catlin_json():
    """``haus check houses/catlin --json`` — invoked once. Read ``.output``, never mutate."""
    return runner.invoke(app, ["check", str(CATLIN), "--json"])


@pytest.fixture(scope="module")
def catlin_json_summary():
    """``haus check houses/catlin --json-summary`` — invoked once."""
    return runner.invoke(app, ["check", str(CATLIN), "--json-summary"])


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

    catlin exits 0 clean, so it cannot prove an exit code it does not produce. starter is
    unfinished by design — it carries real advisory FAILs at WARN severity, which is exactly
    the case the default gate exists to catch.
    """
    result = runner.invoke(app, ["check", str(STARTER), "--plain"])
    assert result.exit_code == 1
    lines = [ln for ln in result.output.splitlines() if ln[:1].isupper() and ":" in ln]
    assert any(ln.startswith("FAIL") for ln in lines), result.output


def test_exit_on_error_is_the_looser_gate() -> None:
    """`scripts/verify.sh` uses this one. It is looser than the default by construction: an
    advisory FAIL is ``severity=WARN``, so ERROR-only lets it through where the default
    stops. starter is what shows the gap — it carries advisory FAILs and no ERROR-severity
    finding at all, so the default gate closes on it and ERROR-only opens.

    ** CATLIN STOPPED SHOWING BOTH GATES OPEN ON 2026-09-18, AND IT IS NOT A TEST BUG. **
    It used to carry no FAIL at all, so both gates opened on it. It now carries one (two
    until 2026-09-19), and it is an ENGINEERED FAIL — ``engineered()`` gives a
    computed-and-over item ``severity=ERROR``, because "this engine did the calculation and
    it does not pass" is not an advisory. So ERROR-only closes too, which is the looser gate
    doing exactly what it is for. See `test_catlin_carries_no_failures` for what it is and
    what closes it; when that fix lands this line goes back to 0.
    """
    assert runner.invoke(app, ["check", str(STARTER), "--plain"]).exit_code == 1
    assert runner.invoke(
        app, ["check", str(STARTER), "--exit-on", ExitOn.error.value]).exit_code == 0
    assert runner.invoke(
        app, ["check", str(CATLIN), "--exit-on", ExitOn.error.value]).exit_code == 1


def test_catlin_carries_no_failures(catlin_json) -> None:
    """The reference house checks clean — 0 FAIL, not "0 errors", bar one accepted advisory.

    Asserted through the JSON surface rather than the exit code so the failure message
    names the offending finding instead of just saying 1 != 0.

    `accepted` below is the allow-list for a real, owner-decided advisory FAIL — never add
    one without a design-record citation beside it. (`structural.deck_joist_span` reads the
    back span per IRC Table R507.5(1); R507.6.1 bounds the overhang separately in
    `structural.deck_joist_cantilever` — do not conflate the two when reasoning about an
    entry here.) See `houses/catlin/CLAUDE.md` and
    `test_catlin_contract_m3.py::test_the_attic_south_juliet_pair_straddles_the_ridge_at_full_unclipped_height`
    for the kind of decision that earns an entry).
    """
    import json

    payload = json.loads(catlin_json.output)
    failures = [
        (f["check_id"], tuple(sorted(f["element_tags"] or ())))
        for f in payload["findings"] if f["result"] == "fail"
    ]
    # Take an entry out rather than leaving it stale — that is what the assertion message
    # below asks of the next person.
    # EMPTY, and it is meant to stay that way. `code.site_parcel_is_surveyed` lived here
    # while the parcel was a drawn placeholder; the owner has since stated the real
    # 50' x 133' lot, so the basis is "plat" and the check reports UNKNOWN rather than
    # FAIL (houses/catlin/plan/site.py's `parcel_basis` block).
    # ** THIS ONE IS NOT AN ACCEPTED ADVISORY. IT IS AN OPEN DESIGN GAP, PARKED HERE
    # DELIBERATELY SO THE REST OF THE GATE STILL RUNS. ** (2026-09-18, the engineering gap
    # review.) `engineering/column_base.py` grades what every `deck_post` record has been
    # NAMING and not grading since 2026-09-11 — the embedment IBC 1807.3.2.1 needs for a
    # column free to translate at grade — and the north entry canopy's cast columns did not
    # have it. `notes/entry_column_base_fixity.md` works it by hand; §6 works the closures.
    #
    # ** IT WAS TWO UNTIL 2026-09-19, AND WHAT MOVED PT-BW-RE WAS THE DEMAND, NOT THE
    # GROUND. ** The canopy's deck is a declared diaphragm now and `W-BW-SCREEN` a declared
    # shear panel, so the frame shear is shared in proportion to rigidity (IBC 2018 §1604.4,
    # §7 of that note). PT-BW-RE went from 8.08' of required embedment to 6.25' against the
    # 6.12' it has — INSIDE §1806.3.4's judgement band, so UNKNOWN rather than FAIL, and
    # NOT a pass: 1.02 is exactly at the line. PT-BW-RNE wants 7.74' and has 3.50'.
    #
    # DELETE THE ENTRY when a closure lands. An entry that outlives its fix is how a 0-FAIL
    # gate stops meaning anything, which is the exact failure this whole review was about.
    accepted: set[tuple[str, tuple[str, ...]]] = {
        ("structural.lateral_racking", ("PT-BW-RNE", "RF-BW-CANOPY")),
    }
    assert accepted <= set(failures), (
        "an accepted advisory stopped firing — delete it from `accepted` rather than "
        "leaving a stale entry", sorted(accepted - set(failures)))
    failures = [item for item in failures if item not in accepted]
    assert not failures, sorted(failures)


def test_exit_on_none_never_gates() -> None:
    result = runner.invoke(app, ["check", str(CATLIN), "--exit-on", "none"])
    assert result.exit_code == 0


def test_json_output_is_complete_regardless_of_only() -> None:
    """--only is a human-output filter. The machine surface must not lose findings to it."""
    import json

    result = runner.invoke(app, ["check", str(CATLIN), "--json", "--only", "fail"])
    payload = json.loads(result.output)
    verdicts = ("pass", "fail", "unknown", "not_applicable")
    assert len(payload["findings"]) == sum(payload[key] for key in verdicts)
    assert payload["pass"] > 0
    # `engineered` is an Authority, not a verdict — it cuts across the four buckets above
    # and must never be summed with them.
    assert payload["engineered"] <= len(payload["findings"])


def test_json_summary_agrees_with_json_on_the_counts_but_is_far_smaller(
        catlin_json, catlin_json_summary) -> None:
    """`--json-summary` is the compact agent surface (#52): same pass/fail/unknown as
    `--json` (other tests, and callers, already assert on those three keys), but without a
    full `model_dump()` per finding — an order of magnitude smaller on catlin's ~700
    findings."""
    import json

    full, summary = catlin_json, catlin_json_summary
    # Compared rather than pinned to 0: what this test is about is that the two machine
    # surfaces AGREE, not what catlin's exit code happens to be — that is
    # `test_catlin_carries_no_failures`'s job.
    assert full.exit_code == summary.exit_code
    full_payload = json.loads(full.output)
    summary_payload = json.loads(summary.output)
    assert summary_payload["pass"] == full_payload["pass"]
    assert summary_payload["fail"] == full_payload["fail"]
    assert summary_payload["unknown"] == full_payload["unknown"]
    assert summary_payload["not_applicable"] == full_payload["not_applicable"]
    assert summary_payload["engineered"] == full_payload["engineered"]
    assert "findings" not in summary_payload
    assert len(summary.output) < len(full.output) / 10


def test_json_summary_categories_sum_to_the_totals(catlin_json_summary) -> None:
    """Each category is a check_id namespace (`structural.foo` -> `structural`); the
    per-category counts must reconcile with the top-level pass/fail/unknown exactly, since
    every finding lands in exactly one category."""
    import json

    payload = json.loads(catlin_json_summary.output)
    categories = payload["categories"]
    assert categories, payload
    assert sum(c["pass"] for c in categories.values()) == payload["pass"]
    assert sum(c["fail"] for c in categories.values()) == payload["fail"]
    assert sum(c["unknown"] for c in categories.values()) == payload["unknown"]
    assert (sum(c["not_applicable"] for c in categories.values())
            == payload["not_applicable"])
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


def test_no_suppress_lifts_the_house_suppressions_and_writes_nothing() -> None:
    """A ``[checks] suppress`` entry is a debt with a number on it — the entries in catlin's
    own ``preferences.toml`` say exactly that. Measuring the number should not mean editing
    the file and remembering to put it back, which is how a campaign loses its score."""
    import hashlib
    import json

    prefs = CATLIN / "preferences.toml"
    before = hashlib.sha256(prefs.read_bytes()).hexdigest()

    quiet = json.loads(runner.invoke(
        app, ["check", str(CATLIN), "--json-summary"]).output)
    loud = json.loads(runner.invoke(
        app, ["check", str(CATLIN), "--json-summary", "--no-suppress"]).output)

    # 1, not 0, since 2026-09-18 (2 until 2026-09-19): `PT-BW-RNE` does not have the IBC
    # 1807.3.2.1 embedment its assumed fixity needs. An open design gap, not a
    # suppression — `test_catlin_carries_no_failures` carries the citation and the closures.
    assert quiet["fail"] == 1, "the reference house's only FAIL is the open one"
    assert loud["fail"] > quiet["fail"], "the suppressed debt is real and is now visible"
    assert "mep.run_interference" in loud["failing_check_ids"]
    assert "mep.run_interference" not in quiet["failing_check_ids"]
    assert hashlib.sha256(prefs.read_bytes()).hexdigest() == before, "it writes nothing"
