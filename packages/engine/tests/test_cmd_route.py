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
    # Not PR-M-S-SUITE-TUB-DRAIN since 2026-09-16: the KITCH/BED2 returns moved into its
    # 22'-0" bay (off BM-M-HALL) and cover its terminal in plan, so it has no lane to explain.
    result = runner.invoke(app, ["route", str(_CATLIN), "--run",
                                 "PR-B-KITCH-DRAIN", "--explain"])
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


def test_the_tree_mode_routes_each_branch_at_its_own_derived_size(runner) -> None:
    """`--tree` builds the branch→main topology, not a re-route of the main.

    **One lattice per branch SIZE.** Every branch used to be 2" because the CLI held one
    literal; each is now sized from its own fixture's drainage load, so the suite bath is
    3" / 1 1/2" / 1 1/4" and each size gets its own world — inflating one shared world at
    the widest walls the narrow branches out of lanes they fit perfectly well.

    **One of three routes, and the other two are named with their size.** That is the
    honest report of this bath as it stands, and two corrections made it so: branches are
    sized from the fixture rather than assumed at 2", and every existing run is now
    inflated by its REAL outside diameter plus its insulation rather than by its nominal
    bore (3" DWV is 3.500" and `PR-A-HW-STUBATH` carries a 1/2" sleeve). The suite bath is
    genuinely tight, the refusals name the runs standing in the way, and the roadmap's own
    decision is that catlin is not to be forced green while its fixed design holds
    unresolved conflicts.
    """
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN),
                                 "--tree", "PR-M-S-SUITE-DRAIN", "--explain"])
    assert result.exit_code == 0, result.output
    assert "FX-S-SUITEBATH-LAV-PROPOSED" in result.output
    assert "diameter=inch(1.25)" in result.output
    assert 'FX-S-SUITEBATH-WC: no route in plan' in result.output
    assert 'at 3"' in result.output and 'at 1.5"' in result.output
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
    assert slacks, "a routed branch prints the head it holds"
    # A second-floor bath on a 1 1/4" branch has inches of head, not feet. Ten is far past
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


def test_a_branch_is_sized_from_its_own_drainage_load(runner) -> None:
    """3", not 2", for a water closet — and the table alone does not say so.

    Table 703.2 puts a 3 DFU closet comfortably inside the 2" row's 6 DFU, which is why
    sizing from capacity alone is the classic error. 710.1 sets the floor and
    `plumbing_calc.MINIMUM_DRAIN_IN_BY_SYMBOL` carries it, so the proposal comes out at the
    size the house itself authors.
    """
    result = runner.invoke(app, ["route", str(_CATLIN),
                                 "--fixture", "FX-S-SUITEBATH-WC"])
    assert result.exit_code == 0, result.output
    assert "diameter=inch(3)" in result.output


def test_a_duct_run_is_routed_rather_than_called_not_a_run(runner) -> None:
    """`_endpoints` indexed `model.pipe_runs` alone, so every duct came back "not a run in
    this model" — a true sentence about the wrong index.

    A duct keeps its own two ends (it is not a tree onto a main), searches the full
    multi-level lattice, and prints `routing=`/`floor_ref=` read back out of the corridors
    the winning legs actually rode rather than asserted.
    """
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "DU-S-HP-SUITE",
                                 "--margin", "2"])
    assert result.exit_code == 0, result.output
    assert "DuctRun(tag=" in result.output
    assert "system=DuctSystem.SUPPLY" in result.output
    assert "routing=DuctRouting." in result.output
    assert "width=" in result.output and "depth=" in result.output


def test_a_congested_terminal_is_refused_with_the_tags_that_block_it(runner) -> None:
    """"Every lane is blocked" is true and useless.

    `CD-B-PV-INV` leaves the basement NW chase, where 37 known interpenetrations sit and
    five runs stand on the raceway's own terminal. The refusal names them and says how much
    of the lattice was reachable at all, which is the difference between "move something"
    and "give up".
    """
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "CD-B-PV-INV",
                                 "--margin", "2"])
    assert result.exit_code == 1, result.output
    assert "lattice nodes are reachable" in result.output
    assert "CD-B-" in result.output
    assert "Traceback" not in result.output


def test_timing_reports_where_the_time_went_even_on_a_refusal(runner) -> None:
    """The measurement Phase 7 is gated on, and a refusal is exactly the case whose
    build-space and lattice counts say why."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "CD-B-PV-INV",
                                 "--margin", "2", "--timing"])
    assert "build-space" in result.output
    assert "build-graph" in result.output
    assert "nodes" in result.output


def test_explain_prints_the_weights_the_route_was_actually_priced_at(runner) -> None:
    """`cost_from_preferences` existed and nothing called it, so every route was priced at
    the module defaults while `--explain` printed a breakdown from a table the house had
    never been asked about."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--explain"])
    assert result.exit_code == 0, result.output
    assert "weights:" in result.output
    assert "cheapest possible inch of travel" in result.output


def test_alternatives_offers_more_than_one_lane_and_says_to_paste_one(runner) -> None:
    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--alternatives", "3"])
    assert result.exit_code == 0, result.output
    assert "paste exactly ONE" in result.output or "-PROPOSED-A" in result.output


def test_alternatives_is_refused_with_tree_rather_than_multiplying_trees(runner) -> None:
    result = runner.invoke(app, ["route", str(_CATLIN), "--tree",
                                 "PR-M-S-SUITE-DRAIN", "--alternatives", "3"])
    assert result.exit_code == 2, result.output


def test_an_unknown_level_is_refused_rather_than_silently_ignored(runner) -> None:
    """`--level` was implemented as a validation and nothing else: it checked the storey
    name and then changed no part of the lattice."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--level", "not-a-storey"])
    assert result.exit_code == 2, result.output


def test_json_emits_the_proposal_and_its_evaluation_together(runner) -> None:
    """Contracts 2 and 3 of the roadmap, in one shape.

    A proposal and what it does to the house are one answer: shipping the first without the
    second is what "the engine proposes" would mean with nobody judging it. Both the
    structured geometry and the source a person pastes are carried, because the two readers
    are different and a re-derivation is a place for them to drift.
    """
    import json

    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {"house", "storey", "proposals", "evaluations",
                            "problems", "notices"}
    proposal = payload["proposals"][0]
    assert proposal["diameter_m"] == pytest.approx(3 * 0.0254)
    assert proposal["points_m"] and len(proposal["points_m"][0]) == 3
    assert "PipeRun(tag=" in proposal["source"]
    assert payload["evaluations"][0]["tag"] == proposal["tag"]
