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


def test_an_unknown_run_is_refused_rather_than_crashing(runner) -> None:
    """A selector naming nothing must come back as a line, not a traceback.

    `_endpoints` returns a fixed-arity tuple of Nones on every refusal and the caller
    unpacks it; a refusal path that returned one element short crashed on the unpack
    instead of printing the reason, which is the one failure mode this whole CLI is
    written against — "reported, never approximated".
    """
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "PR-NOT-A-RUN"])
    assert result.exit_code == 1, result.output
    assert "not a run in this model" in result.output
    assert "Traceback" not in result.output


def test_the_tree_mode_routes_every_fixture_the_main_serves(runner) -> None:
    """`--tree` builds the branch→main topology, not a re-route of the main.

    Three assertions, and the middle one is the whole difference from running `--fixture`
    three times: every fixture the main names gets a proposal, they are ordered by head
    slack rather than by tag, and the tree's own cost is reported. A `--tree` that quietly
    behaved like `--run` printed one proposal and looked fine.
    """
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN),
                                 "--tree", "PR-M-S-SUITE-DRAIN", "--explain"])
    assert result.exit_code == 0, result.output
    for fixture in ("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV", "FX-S-SUITEBATH-TUBSH"):
        assert f'{fixture}-PROPOSED' in result.output
    assert "routed 3 terminal(s), 0 unserved" in result.output
    assert "deepest first" in result.output
    assert _plan_digest() == before


def test_a_tree_branch_ties_at_the_stack_and_not_at_its_basement_leg(runner) -> None:
    """The tie band is `mep.fixture_drain_reach`'s, and it has to be.

    `PR-M-S-SUITE-DRAIN` is a stack: its plan polyline passes the second-floor bath at
    115.5" and then again, twelve feet lower, as the basement horizontal that leaves it.
    In plan those are the same lines. Without the band a branch ties into the basement leg
    and reports feet of head to spare, which is a true statement about a pipe nobody can
    build.
    """
    result = runner.invoke(app, ["route", str(_CATLIN),
                                 "--tree", "PR-M-S-SUITE-DRAIN", "--explain"])
    assert result.exit_code == 0, result.output
    slacks = [float(line.split('"')[0].split()[-1])
              for line in result.output.splitlines() if "of head to spare" in line]
    assert len(slacks) == 3
    # A second-floor bath on a 2" branch has inches of head, not feet. Ten is far past
    # anything the geometry allows and far short of the 140" the basement leg reported.
    assert max(slacks) < 10.0, slacks


def test_a_tree_terminal_short_of_head_is_reported_with_the_number(runner) -> None:
    """An infeasible branch names its shortfall in inches, and blocks the proposal.

    `PR-B-KITCH-DRAIN` is the kitchen sink's own main and a tree onto it is tight: the
    branch the router finds is short of head at the code minimum grade. "No feasible
    route" is not actionable and is not what comes out — an inch count is, and it is what
    `gravity.HeadBudget.shortfall_in` exists to say.
    """
    result = runner.invoke(app, ["route", str(_CATLIN), "--tree", "PR-B-KITCH-DRAIN"])
    assert result.exit_code == 1, result.output
    assert "of head" in result.output
    assert "PROPOSED" not in result.output
