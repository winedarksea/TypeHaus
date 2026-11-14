"""Report contracts at the CLI boundary, using small proposals instead of house searches."""

from __future__ import annotations

import ast
import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from typehaus.cli import cmd_route, route_eval
from typehaus.cli.app import app
from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import ft
from typehaus.routing.campaign import CampaignTarget
from typehaus.routing.cost import RouteCost
from typehaus.routing.diagnostics import Blocker, Mobility, Refusal
from typehaus.routing.proposal import ProposedCleanout, RouteProposal, render


@pytest.fixture
def routing_cli(monkeypatch, tmp_path):
    proposal = RouteProposal(
        tag="R-PROPOSED", kind="pipe", system="water_cold", diameter_m=0.0254,
        points=[(0.0, 0.0, ft(11).meters), (ft(3).meters, 0.0, ft(11).meters)],
        cost=36.0, terms={"travel_in": 36.0}, notes=["confirm the port"],
        after=("reroute the child",))
    evaluation = route_eval.Evaluation(
        tag=proposal.tag, coverage=["port geometry is approximate"],
        introduced=[Finding(check_id="mep.example", severity=Severity.ERROR,
                            result=Result.UNKNOWN, message="missing body", element_tags=("R",))],
        resolved=[Finding(check_id="mep.old", severity=Severity.WARN, message="old clash")])
    model = SimpleNamespace(
        pipe_runs=[SimpleNamespace(tag="R", storey="main")], ducts=[], conduits=[],
        plan=SimpleNamespace(storeys=[SimpleNamespace(tag="main", elevation=ft(10)),
                                     SimpleNamespace(tag="upper", elevation=ft(20))]))
    state = SimpleNamespace(
        directory=tmp_path / "house", model=model, proposals=[(proposal, "main")],
        evaluations=[evaluation], problems=["terminal overlaps another run"],
        notices=["confirm a ¼-inch clearance [at the tie]"], refusals=[],
        targets=["R"], evaluated=[], calls=[])

    def propose(*args, **kwargs):
        state.calls.append(kwargs)
        if kwargs.get("timing") is not None:
            kwargs["timing"].append("build-space 2 ms")
        return state.proposals, state.problems, state.notices, state.refusals

    def evaluate(_directory, _model, proposals):
        state.evaluated.append(proposals)
        return state.evaluations

    monkeypatch.setattr(cmd_route, "_load", lambda _house: (state.directory, model))
    monkeypatch.setattr(cmd_route, "_route_cost", lambda _directory: RouteCost())
    monkeypatch.setattr(cmd_route, "_propose", propose)
    monkeypatch.setattr(cmd_route, "_propose_tree", propose)
    monkeypatch.setattr(cmd_route, "_unconnected_fixtures", lambda *_args: state.targets)
    monkeypatch.setattr(route_eval, "evaluate_proposals", evaluate)
    state.invoke = lambda *args: CliRunner().invoke(app, ["route", str(state.directory), *args])
    return state


def _blocked():
    from typehaus.cli.route_takeoff_table import TakeoffRow

    duct = Blocker("DUCT", "run", Mobility.MOVABLE, 1.0, 2.0, 3.0)
    return Refusal(
        target="BLOCKED", service="supply", end="origin", reachable_nodes=1, total_nodes=20,
        blockers=[duct], shortages=("bay is two inches narrow",), attempts=("margin 8 ft",),
        takeoffs=[TakeoffRow((98.0, 216.0), 22.0, "W-1", duct, 34.75),
                  TakeoffRow((100.0, 216.0), 25.0, None)])


def test_json_keeps_warning_timing_and_evaluation_without_console_prose(routing_cli):
    result = routing_cli.invoke("--run", "R", "--json", "--explain", "--timing")
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["problems"] == routing_cli.problems
    assert routing_cli.notices[0] in report["notices"]
    assert "timing: build-space 2 ms" in report["notices"]
    assert report["proposals"][0]["terms_in"] == {"travel_in": 36.0}
    assert report["proposals"][0]["storey"] == "main"
    assert report["evaluations"][0]["introduced"][0]["result"] == "unknown"
    assert report["evaluations"][0]["coverage"]


@pytest.mark.parametrize("geometric_refusal", [False, True])
def test_no_proposal_still_returns_json_and_exit_one(routing_cli, geometric_refusal):
    routing_cli.proposals = []
    if geometric_refusal:
        routing_cli.refusals = [_blocked()]
    result = routing_cli.invoke("--run", "BLOCKED", "--json")
    assert result.exit_code == 1, result.output
    report = json.loads(result.stdout)
    assert report["proposals"] == report["evaluations"] == []
    assert report["storey"] is None
    assert report["problems"]
    assert not routing_cli.evaluated
    if geometric_refusal:
        assert report["refusals"][0]["blockers"][0]["mobility"] == "movable"


def test_empty_unconnected_scope_returns_json_without_evaluating(routing_cli, tmp_path):
    routing_cli.targets = []
    routing_cli.proposals = []
    routing_cli.problems = []
    result = routing_cli.invoke("--unconnected", "--json", "--summary", "--out", str(tmp_path))
    assert result.exit_code == 0, result.output
    view = json.loads(result.stdout)["decision"]
    assert view["candidates"]["count"] == 0 and view["network"] is None
    assert view["completion"]["notices"] >= 1
    assert not routing_cli.evaluated
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["proposals"] == report["evaluations"] == []
    assert any("Nothing to propose" in line for line in report["notices"])


def test_partial_proposals_keep_refusals_and_existing_success_exit(routing_cli):
    routing_cli.targets = ["R", "BLOCKED"]
    routing_cli.refusals = [_blocked()]
    result = routing_cli.invoke("--unconnected", "--json")
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["proposals"] and report["refusals"] and report["evaluations"]


def test_summary_preserves_decisions_and_full_artifacts(routing_cli, tmp_path, monkeypatch):
    monkeypatch.setattr(RouteProposal, "fittings", lambda _self: [SimpleNamespace(
        index=1, angle_deg=30.0, order_key=None, spec=None, gap="no catalogued bend")])
    routing_cli.refusals = [_blocked()]
    result = routing_cli.invoke("--run", "R", "--json", "--summary", "--out", str(tmp_path))
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    full = json.loads((tmp_path / "report.json").read_text())
    assert len(result.stdout.strip().splitlines()) == 1
    assert set(summary) == {"house", "storey", "decision", "artifacts"}
    assert summary["artifacts"]["report"] == str(tmp_path / "report.json")
    # report.json keeps everything, including a take-off row's station.
    rows = full["refusals"][0]["takeoffs"]
    assert rows[0]["station_in"] == [98.0, 216.0] and rows[0]["blocker"] == "DUCT"
    assert all(key in full["proposals"][0] for key in ("points_m", "source", "terms_in"))
    assert "confirm the port" in (tmp_path / "proposed.py").read_text()

    view = summary["decision"]
    assert view["mode"] == "candidates" and view["network"] is None
    candidate, = view["candidates"]["items"]
    assert candidate["report_ptr"] == "/proposals/0" and candidate["cost_in_equivalent"] == 36.0
    assert candidate["fittings"] == {"count": 1, "gaps": 1} and candidate["notes"] == 1
    assert candidate["cleanouts"] == {"placed": 0, "required": 0}
    assert candidate["after_paste"]["items"] == ["reroute the child"]
    grade = candidate["grade"]
    assert (grade["status"], grade["fail"], grade["unknown"]) == ("evaluated", {}, {"other": 1})
    assert grade["resolved"] == 1 and grade["coverage_gaps"]["count"] == 1
    found, = grade["findings"]
    assert found["ptr"] == "/evaluations/0/introduced/0"
    assert full["evaluations"][0]["introduced"][0]["check_id"] == found["check_id"]
    # Refusals: blockers grouped by tag and mobility; the take-off table stays in report.json.
    refusal, = view["completion"]["refusals"]["items"]
    assert refusal["by_mobility"] == {"movable": 1}
    assert refusal["blockers"] == [{"tag": "DUCT", "kind": "run", "mobility": "movable",
                                    "count": 1}]
    assert "takeoffs" not in json.dumps(summary)


@pytest.mark.parametrize("selector", [
    ["--run", "R"], ["--fixture", "FX"], ["--tree", "R"], ["--unconnected"],
])
def test_every_proposal_selector_can_save_artifacts_without_json(routing_cli, tmp_path, selector):
    result = routing_cli.invoke(*selector, "--out", str(tmp_path))
    assert result.exit_code == 0, result.output
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["proposals"][0]["source"] in (tmp_path / "proposed.py").read_text()
    assert report["evaluations"] == []
    assert "PROPOSED, NOT WRITTEN" in result.stdout


@pytest.mark.parametrize("flags", [
    ["--run", "R", "--out", "out"], ["--run", "R", "--json"],
    ["--space", "R", "--json", "--out", "out"],
    ["--fixture", "FX", "--sweep", "8", "--json", "--out", "out"],
])
def test_invalid_summary_combinations_are_rejected(routing_cli, flags):
    result = routing_cli.invoke(*flags, "--summary")
    assert result.exit_code == 2
    assert "--summary requires" in result.output
    assert not routing_cli.calls


def test_artifacts_cannot_overwrite_the_house_plan(routing_cli):
    result = routing_cli.invoke("--run", "R", "--out", str(routing_cli.directory / "plan"))
    assert result.exit_code == 2
    assert not (routing_cli.directory / "plan").exists()


def test_mixed_storeys_and_absolute_conduit_source_round_trip(routing_cli, tmp_path):
    from typehaus.model.enums import DuctSystem, PipeSystem, Service
    from typehaus.model.mep import ConduitRun, DrainCleanout, DuctRun, PipeRun
    from typehaus.quantities import Point2D, inch, pt

    cleanout = ProposedCleanout(
        tag="CO-R-PROPOSED-A-1", point=(0.5, 0.0, ft(11).meters), reason="upper terminal",
        access="wall", wall_ref="W-1", clear_in=18.0, concealed=True,
        cap=(0.5, 0.1, ft(11).meters + 0.1))
    proposals = [
        RouteProposal(tag="R-PROPOSED-A", kind="pipe", system="drain", diameter_m=0.0508,
                      points=[(0.0, 0.0, ft(11).meters), (1.0, 0.0, ft(11).meters)],
                      cleanouts=(cleanout,)),
        RouteProposal(tag="R-PROPOSED-B", kind="pipe", system="water_cold", diameter_m=0.0254,
                      points=[(0.0, 0.0, ft(12).meters), (1.0, 0.0, ft(12).meters)]),
        RouteProposal(tag="D-PROPOSED", kind="duct", system="supply", diameter_m=0.1,
                      points=[(0.0, 0.0, ft(22).meters), (1.0, 0.0, ft(22).meters)]),
        RouteProposal(tag="C-PROPOSED", kind="conduit", system="power_120", diameter_m=0.0254,
                      points=[(0.0, 0.0, ft(21).meters), (1.0, 0.0, ft(22).meters)]),
    ]
    routing_cli.proposals = list(zip(proposals, ("main", "main", "upper", "upper"), strict=True))
    result = routing_cli.invoke("--unconnected", "--json", "--out", str(tmp_path))
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    namespace = dict(PipeRun=PipeRun, DuctRun=DuctRun, ConduitRun=ConduitRun, ft=ft, inch=inch,
                     DrainCleanout=DrainCleanout,
                     PipeSystem=PipeSystem, DuctSystem=DuctSystem, Service=Service,
                     Point2D=Point2D, pt=pt)
    for row, expected in zip(report["proposals"], [(1, 1), (2, 2), (2, 2), (21, 22)], strict=True):
        element, *extra = eval(f"[{row['source']}\n]", {"__builtins__": {}, **namespace})
        assert len(extra) == len(row["cleanouts"])
        assert [e.meters for e in element.elevations] == pytest.approx(
            [ft(value).meters for value in expected])
    source = (tmp_path / "proposed.py").read_text()
    ast.parse(source)
    # The pasted cleanout is the one graded: saved source, console and eval all agree.
    _run, pasted = eval(f"[{report['proposals'][0]['source']}\n]",
                        {"__builtins__": {}, **namespace})
    (graded,) = route_eval._cleanout_elements(routing_cli.model, "main", proposals[0])
    assert pasted.model_dump() == graded.model_dump()
    assert f'DrainCleanout(tag="{pasted.tag}"' in source
    assert proposals[0].full_source(storey_datum_m=ft(10).meters) in render(
        [proposals[0]], storey_datum_m=ft(10).meters)
    assert "ALTERNATIVES for R: paste exactly ONE" in source
    assert "STOREY: upper; elevations are storey-relative" in source
    assert "STOREY: upper; elevations are project-frame absolute" in source


@pytest.mark.parametrize("scope", ["empty", "partial", "complete"])
@pytest.mark.parametrize("flags", [
    ["--json"], ["--json", "--summary"], ["--evaluate"],
])
def test_campaign_json_and_artifacts_include_network_evaluation(
        routing_cli, monkeypatch, tmp_path, scope, flags):
    from typehaus.routing import campaign

    targets = [] if scope == "empty" else [CampaignTarget("R", "supply", "pipe", "main", 0.0254)]
    if scope == "partial":
        targets.append(CampaignTarget("BLOCKED", "supply", "pipe", "main", 0.0254))
    monkeypatch.setattr(campaign, "order_targets", lambda *_args, **_kwargs: targets)

    def propose(_model, tags, **kwargs):
        if tags == ["BLOCKED"]:
            return [], ["terminal blocked"], [], [_blocked()]
        return routing_cli.proposals, routing_cli.problems, routing_cli.notices, []

    def evaluate(_directory, _model, proposals):
        if not proposals:
            return route_eval.Evaluation(tag="campaign", refused="nothing was laid")
        return route_eval.Evaluation(
            tag="campaign", introduced=routing_cli.evaluations[0].introduced,
            coverage=["network coverage gap"])

    monkeypatch.setattr(cmd_route, "_propose", propose)
    monkeypatch.setattr(route_eval, "evaluate_network", evaluate)
    result = routing_cli.invoke("--house", "--orders", "3", *flags,
                                "--out", str(tmp_path))
    assert result.exit_code == (1 if scope == "partial" else 0), result.output
    report = json.loads((tmp_path / "report.json").read_text())
    summary = json.loads(result.stdout) if "--json" in flags else report
    if flags == ["--json"]:
        assert summary == report
    if "--summary" in flags:
        view = summary["decision"]
        assert view["mode"] == "network" and len(view["orders_tried"]) == 3
        assert view["network"]["report_ptr"] == "/evaluations/0"
        assert view["network"]["status"] == ("refused" if scope == "empty" else "evaluated")
        assert view["candidates"]["count"] == (0 if scope == "empty" else 1)
    else:
        assert report["evaluations"] == summary["evaluations"]
    assert report["evaluations"][0]["tag"] == "campaign"
    assert len(report["orders_tried"]) == 3
    if scope == "empty":
        assert report["accepted"] == []
        assert report["evaluations"][0]["refused"]
    else:
        assert report["accepted"][0]["storey"] == "main"
        assert "ft(1)" in report["accepted"][0]["source"]
        assert report["evaluations"][0]["introduced"]
        assert report["evaluations"][0]["coverage"]
        if "--summary" in flags:
            assert view["network"]["unknown"] == {"other": 1}
            assert view["network"]["findings"][0]["ptr"] == "/evaluations/0/introduced/0"
    if scope == "partial":
        if "--summary" in flags:
            refusal, = view["completion"]["refusals"]["items"]
            assert view["completion"]["refused"]["count"] == 1
            assert refusal["blockers"][0]["tag"] == "DUCT"
        else:
            assert summary["refused"]
            assert summary["refusals"][0]["blockers"][0]["tag"] == "DUCT"
