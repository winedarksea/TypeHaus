"""``haus route`` — a smoke test, and the one assertion that matters most.

**Nothing under ``houses/<name>/plan/`` may change.** ``haus route`` prints dialect source
for a person to paste and has no ``--write``; the reasons are in
``typehaus/routing/proposal.py``, of which the fatal one is that
``source/loader._content_hash`` hashes every plan file, so a machine edit would stale every
pinned engineering seal in the house. A test that only checked the output would pass on a
version that wrote the file as well.
"""

from __future__ import annotations

import hashlib
import pathlib

import pytest
from typer.testing import CliRunner

from typehaus.cli.app import app

pytestmark = pytest.mark.slow

_CATLIN = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _plan_digest() -> dict[str, str]:
    return {str(p.relative_to(_CATLIN)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((_CATLIN / "plan").rglob("*.py"))}


@pytest.fixture(scope="module")
def runner() -> CliRunner:
    return CliRunner()


def test_a_fixture_proposal_prints_source_and_writes_nothing(runner) -> None:
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN),
                                 "--fixture", "FX-S-SUITEBATH-WC"])
    assert result.exit_code == 0, result.output
    assert "PROPOSED, NOT WRITTEN" in result.output
    assert "PipeRun(tag=" in result.output
    assert "uid=" not in result.output, "haus fmt mints uids; a proposal never hands one out"
    assert _plan_digest() == before


def test_explain_prints_the_terms_the_route_was_chosen_on(runner) -> None:
    """A router that cannot say why it chose a line is one nobody will take a line from."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--run",
                                 "PR-M-S-SUITE-TUB-DRAIN", "--explain"])
    assert result.exit_code == 0, result.output
    assert "travel_in" in result.output
    assert "gravity:" in result.output


def test_exactly_one_selector_is_required(runner) -> None:
    both = runner.invoke(app, ["route", str(_CATLIN), "--fixture", "FX-S-SUITEBATH-WC",
                               "--unconnected"])
    assert both.exit_code == 2
    neither = runner.invoke(app, ["route", str(_CATLIN)])
    assert neither.exit_code == 2


def test_unconnected_reads_the_check_rather_than_re_deriving_it(runner) -> None:
    """The architecture in one command. What is wrong with the house is a FINDING, and the
    router is aimed at findings — catlin's are all fixed, so this reports nothing to do
    rather than proposing branches for fixtures that already have them."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--unconnected"])
    assert result.exit_code == 0, result.output
    assert "mep.fixture_drain_reach" in result.output


def test_a_bad_via_is_refused_rather_than_guessed(runner) -> None:
    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--via", "nonsense"])
    assert result.exit_code != 0
