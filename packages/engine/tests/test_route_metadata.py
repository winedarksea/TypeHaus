"""A reroute keeps the product that is sized, wrapped, and graded."""

from types import SimpleNamespace

import pytest

from typehaus.cli.route_eval import candidate_element
from typehaus.cli.route_support import _duct_endpoints
from typehaus.cli.trial_score import render, score
from typehaus.model.enums import DuctRouting, DuctSystem
from typehaus.model.mep import DuctRun
from typehaus.quantities import ft, inch, pt
from typehaus.routing.proposal import RouteProposal


def _duct_model(insulation='2" R-8 wrap, vapour-sealed'):
    duct = DuctRun(tag="DU-TEST", system=DuctSystem.OUTDOOR_AIR,
                   path=(pt(ft(1), ft(1)), pt(ft(4), ft(1))),
                   elevations=(ft(7), ft(7)), diameter=inch(8),
                   routing=DuctRouting.CHASE, insulation=insulation,
                   material="galvanized", design_cfm=210)
    resolved = SimpleNamespace(tag=duct.tag, storey="basement",
                               path=tuple(p.xy_m for p in duct.path),
                               z_m=(ft(-2).meters, ft(-2).meters),
                               diameter_m=inch(8).meters, width_m=0.0, depth_m=0.0,
                               system="outdoor_air", insulation=insulation)
    plan = SimpleNamespace(all_elements=lambda: (duct,),
                           storeys=(SimpleNamespace(tag="basement", elevation=ft(-9)),))
    return SimpleNamespace(plan=plan, ducts=(resolved,), pipe_runs=(), conduits=())


def _endpoints(monkeypatch, model, problems):
    monkeypatch.setattr("typehaus.cli.route_support._duct_size_advice", lambda *_: ())
    monkeypatch.setattr("typehaus.cli.route_support._port_terminal",
                        lambda _model, duct, index: (*duct.path[index], duct.z_m[index]))
    return _duct_endpoints(model, model.ducts[0], problems)


def test_routing_reserves_the_wrapped_twelve_inch_envelope(monkeypatch):
    ends = _endpoints(monkeypatch, _duct_model(), [])
    assert ends.radius_m == pytest.approx(inch(6).meters)
    assert ends.diameter_m == pytest.approx(inch(8).meters)


def test_routing_refuses_an_undimensioned_insulation_envelope(monkeypatch):
    problems = []
    assert _endpoints(monkeypatch, _duct_model("R-8 wrap"), problems) is None
    assert "insulation states no thickness" in problems[0]


def test_candidate_and_printed_duct_keep_identical_airflow_material_and_wrap(monkeypatch):
    model = _duct_model()
    ends = _endpoints(monkeypatch, model, [])
    proposal = RouteProposal(tag="DU-TEST-PROPOSED", kind="duct",
                             points=[ends.origin, ends.root], diameter_m=ends.diameter_m,
                             system=ends.system, routing="chase", echo=ends.echo)
    storey, candidate = candidate_element(model, proposal)
    printed, = eval(proposal.source(storey_datum_m=ft(-9).meters), {
        "DuctRun": DuctRun, "DuctSystem": DuctSystem, "DuctRouting": DuctRouting,
        "ft": ft, "inch": inch, "pt": pt,
    })
    assert storey == "basement"
    assert candidate.model_dump() == printed.model_dump()
    assert candidate.design_cfm == 210
    assert candidate.material == "galvanized"
    assert candidate.insulation == '2" R-8 wrap, vapour-sealed'


def test_trial_reports_advisories_without_counting_them_as_failures(monkeypatch, tmp_path):
    finding = {"check_id": "integrity.clear_zone_intrusion", "result": "advisory",
               "element_tags": ["CZ-TEST", "DU-TEST"], "message": "intrudes"}
    baseline = {"suppress": True, "findings": [], "runs": {},
                "engine": "test", "profile": "test", "content_hash": "before"}
    current = {**baseline, "findings": [finding], "content_hash": "after"}
    monkeypatch.setattr("typehaus.cli.trial_score.record", lambda *_, **__: current)
    card = score(tmp_path, baseline)
    assert card.new_advisory == [finding]
    assert card.exit_code == 0
    assert card.as_dict()["new_advisory"] == [finding]
    assert any("NEW ADVISORY" in line for line in render(card))
    assert not any("no finding changed" in line for line in render(card))
