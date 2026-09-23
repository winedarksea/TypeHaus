"""``haus route`` — a smoke test, and the one assertion that matters most.

**Nothing under ``houses/<name>/plan/`` may change.** ``haus route`` prints dialect source
for a person to paste and has no ``--write``; the reasons are in
``typehaus/routing/proposal.py``, and they are that the prose in a plan file IS the design
record and that accepting a route is a judgement. (The reason once given here — that
``source/loader._content_hash`` would stale every pinned engineering seal — is FALSE and is
retired: a seal pins ``engineering/fingerprint.fingerprint(record)``, which hashes a
record's inputs and ratio and never the model's bytes. See CLAUDE.md.) A test that only
checked the output would pass on a version that wrote the file as well.
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

    ``refusals`` is contract 3's other half, added in Phase 4: a terminal that was NOT
    served, with the blockers standing on it, each one's conflict location and mobility
    class, the shortage and whether impossibility is established. ``problems`` carries the
    same facts as prose for a person; this is the half an agent reads, and the key set is
    pinned here so adding one is a deliberate act.
    """
    import json

    result = runner.invoke(app, ["route", str(_CATLIN), "--fixture",
                                 "FX-S-SUITEBATH-WC", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert set(payload) == {"house", "storey", "proposals", "evaluations",
                            "problems", "notices", "refusals"}
    # This fixture routes, so there is nothing refused — the key is present regardless,
    # because a consumer that has to branch on whether a field exists is a contract with a
    # hole in it.
    assert payload["refusals"] == []
    proposal = payload["proposals"][0]
    assert proposal["diameter_m"] == pytest.approx(3 * 0.0254)
    assert proposal["points_m"] and len(proposal["points_m"][0]) == 3
    assert "PipeRun(tag=" in proposal["source"]
    assert payload["evaluations"][0]["tag"] == proposal["tag"]


# --- Phase 6: the whole-house campaign ---------------------------------------------------

def test_a_campaign_lays_many_runs_against_one_occupancy_and_writes_no_plan(runner) -> None:
    """The deliverable: a coordinated set, and the plan still untouched.

    Scoped to one storey and one trade so the test is minutes rather than an hour; the
    property being asserted is the same at any scope. Catlin's basement drainage does NOT
    come back fully served, and it is not meant to — the roadmap's decision is that the
    reference house need not be forced green while its fixed design holds unresolved
    conflicts, and what a campaign owes is an accurate account of which ones.
    """
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN), "--house",
                                 "--trades", "drain", "--storey", "basement"])
    # Exit 1 is the honest code here: something was refused, and a script should find out.
    assert result.exit_code in (0, 1), result.output
    assert "target(s)" in result.output
    assert "targets laid" in result.output
    assert _plan_digest() == before


def test_a_campaign_writes_its_report_and_its_source_only_where_it_is_told(
        runner, tmp_path) -> None:
    """``--out`` is two files for two readers, and neither of them is under ``plan/``."""
    import json

    before = _plan_digest()
    out = tmp_path / "route"
    result = runner.invoke(app, ["route", str(_CATLIN), "--house",
                                 "--trades", "drain", "--storey", "basement",
                                 "--out", str(out)])
    assert result.exit_code in (0, 1), result.output
    report = json.loads((out / "report.json").read_text())
    assert report["settings"]["trade_order"] == [
        "drain", "vent", "duct", "supply", "conduit"]
    assert report["termination"]
    assert "PROPOSED, NOT WRITTEN" in (out / "proposed.py").read_text()
    assert _plan_digest() == before


def test_a_campaign_refuses_a_trade_it_does_not_lay_with_the_list(runner) -> None:
    """A typo empties a campaign silently; a refusal that names the five does not."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--house", "--trades", "plumbing"])
    assert result.exit_code == 2
    assert "is not a trade this campaign lays" in result.output


def test_house_is_exclusive_with_the_single_target_selectors(runner) -> None:
    result = runner.invoke(app, ["route", str(_CATLIN), "--house",
                                 "--run", "PR-B-KITCH-DRAIN"])
    assert result.exit_code == 2
    assert "exactly one of" in result.output


# --- Phase 8: the space view -------------------------------------------------------------

def test_the_space_view_classifies_instead_of_routing_and_writes_no_plan(runner) -> None:
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN), "--space", "PR-B-KITCH-DRAIN"])
    assert result.exit_code == 0, result.output
    assert "classified region(s)" in result.output
    assert "PROPOSED" not in result.output, "--space reports a space, it does not propose"
    assert _plan_digest() == before


def test_the_space_view_json_carries_the_classes_and_the_levels(runner) -> None:
    import json

    result = runner.invoke(app, ["route", str(_CATLIN), "--space", "PR-B-KITCH-DRAIN",
                                 "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["target"] == "PR-B-KITCH-DRAIN"
    assert payload["levels_m"]
    assert set(payload["summary"]["by_class"]) <= {"green", "orange", "red", "gray"}
    assert all(region["action"] for region in payload["regions"])


def test_the_space_view_writes_one_overlay_per_level(runner, tmp_path) -> None:
    """A plan is one elevation; stacking eleven into one picture is a picture of nothing."""
    out = tmp_path / "space"
    result = runner.invoke(app, ["route", str(_CATLIN), "--space", "PR-B-KITCH-DRAIN",
                                 "--out", str(out)])
    assert result.exit_code == 0, result.output
    svgs = sorted(out.glob("*.svg"))
    assert svgs, "no overlay was written"
    assert '<g id="routing">' in svgs[0].read_text()


def test_a_vent_may_be_proposed_into_a_SIBLING_and_not_only_its_own_chase(runner) -> None:
    """A vent's downstream is a chase, not another run, so ``drain_tie_ins`` derives nothing
    for it and ``--run`` used to refuse outright: "nothing downstream of it is derivable".
    Two branch vents on a common vent is ordinary IRC P3104 work, and the router could not
    propose it. The goal set is now every sibling vent landing on the same station."""
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "PR-S-BATH1-VENT"])
    # Exit 1: this particular vent turns out to be AT its goal already, so there is nothing
    # to paste (see the test below). What must not appear is the old structural refusal.
    assert "nothing downstream of it is derivable" not in result.output
    assert _plan_digest() == before


def test_a_route_that_is_already_AT_its_goal_is_a_finding_and_not_a_paste(runner) -> None:
    """catlin's PR-S-BATH1-VENT starts 0.9" off PR-S-SUITEBATH-VENT's north leg, so the
    shortest route to a sibling is no route at all. A one-point polyline printed as dialect
    is a 1-tuple that will not even parse — so it is reported, never proposed."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "PR-S-BATH1-VENT"])
    assert "already stands on what it is being routed to" in result.output
    assert "PR-S-BATH1-VENT-PROPOSED" not in result.output


def test_a_vent_is_still_refused_as_a_TREE_main_with_a_reason(runner) -> None:
    """``--tree`` builds a directed Steiner tree under a gravity search — head budgets,
    inverts, a fall profile — and none of that describes a vent. The refusal is the honest
    answer until that path exists; what it must NOT do is return the wrong tuple shape,
    which every early return in ``_propose_tree`` did while the success path returned four."""
    result = runner.invoke(app, ["route", str(_CATLIN), "--tree", "PR-S-SUITEBATH-VENT"])
    assert result.exit_code == 1, result.output
    assert "not a drain run in this model" in result.output


def _endpoints(tag: str, mode: str):
    """The endpoint record one target hands the search, with its refusals."""
    from typehaus.cli.route_support import _endpoints as build
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(_CATLIN).plan)
    problems: list[str] = []
    return build(model, tag, mode, problems), problems, model


def test_a_supply_branch_ties_onto_its_trunk_rather_than_a_vent_chase() -> None:
    """Until 2026-09-19 a supply run fell through to `_vent_siblings`, which takes
    `path[-1]` as the root and matches on ENDPOINTS. Supply is the mirror: the tee is
    `path[0]` and it sits on a SEGMENT, which no endpoint tolerance can find."""
    ends, problems, model = _endpoints("PR-B-CW-BATH1", "run")
    assert ends is not None, problems
    assert ends.falls is False
    assert ends.tie_is_the_goal is True
    run = next(r for r in model.pipe_runs if r.tag == "PR-B-CW-BATH1")
    # The ORIGIN is the fixture riser — the fixed end — and the tie is the goal.
    assert ends.origin[:2] == (run.path[-1][0], run.path[-1][1])
    assert ends.root_paths and all(len(v) == 3 for v in ends.root_paths[0])
    assert {"PR-B-CW-BATH1", "PR-B-CW-TRUNK"} <= ends.touch
    # A DFU drain table says nothing about a water branch; the run's own size stands.
    assert ends.diameter_m == run.diameter_m


def test_a_supply_proposal_lands_on_the_trunks_LINE_not_its_endpoint(runner) -> None:
    before = _plan_digest()
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", "PR-B-HW-BATH2"])
    assert result.exit_code == 0, result.output
    assert "PR-B-HW-BATH2-PROPOSED" in result.output
    assert "vent" not in result.output.lower()
    assert _plan_digest() == before


@pytest.mark.parametrize("tag,fragment", [
    # Each real cause, asserted AS TEXT: a refusal's wording is its contract, and one
    # sentence about a vent chase was false about all of them.
    #
    # `PR-B-HW-TRUNK` read "no run of any system passes" until 2026-09-23; the tie-in
    # reader now sees EQ-B-WH's hot tap as its source, and the refusal says so.
    ("PR-B-HW-TRUNK", "it leaves EQ-B-WH.hot, an equipment port"),
    ("PR-M-CW-PORCH-HYD", "no run of any system passes under its first vertex"),
    ("PR-M-CW-COLDSTORE-STUB", "passes under its first vertex but 12.0\" above it"),
])
def test_a_parentless_supply_run_refuses_naming_which_cause(runner, tag, fragment) -> None:
    result = runner.invoke(app, ["route", str(_CATLIN), "--run", tag])
    printed = " ".join(result.output.split())
    assert fragment in printed, result.output
    assert "chase" not in printed
    assert "PROPOSED" not in printed


def test_the_root_line_z_gate_keeps_a_branch_off_the_trunks_plan_shadow() -> None:
    """**The one place this change can produce a confidently wrong route.** `_line_nodes`
    was plan-only with no z filter, and `falls=False` means the search is 3-D — so a branch
    could "arrive" on the trunk's plan line five feet below the trunk and be reported found.
    `_root_nodes(..., with_z=True)` would never catch it, because `_line_nodes` returned a
    non-empty set first."""
    from typehaus.cli.cmd_route_tree import _line_nodes
    from typehaus.routing.graph import Graph, Node

    line = ((0.0, 0.0, 2.0), (4.0, 0.0, 2.0))
    graph = Graph(nodes=[Node(index=0, x=2.0, y=0.0, z=2.0),
                         Node(index=1, x=2.0, y=0.0, z=0.5)])
    assert _line_nodes(graph, line) == {0, 1}                     # plan-only, as before
    assert _line_nodes(graph, line, z_tolerance=0.05) == {0}      # the gate
