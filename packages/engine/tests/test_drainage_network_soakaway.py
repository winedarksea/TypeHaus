"""A soakaway bed in the drainage graph: a disposal, graded per body of stone.

Built on ``_soakaway_plan``: FB-TEST-PLAIN's tile and FD-TEST-SOAK both discharge into
FB-TEST-SOAK, whose course overflows to daylight.
"""

from __future__ import annotations

import copy

import pytest
from _helpers import check_context
from _soakaway_plan import lateral, plain_bed, soak_bed, soak_plan

from typehaus.checks.mep.drainage import discharge_consistency
from typehaus.checks.mep.drainage_network import (
    inlet_reciprocity,
    network_fallback,
    network_outfall,
    outfall_connection,
)
from typehaus.findings import Result
from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.resolve.drainage_network import EdgeKind, build_network

_TEST = ("FB-TEST-SOAK", "FB-TEST-PLAIN", "FD-TEST-SOAK")


@pytest.fixture(scope="module")
def soak(catlin_plan):
    plan = soak_plan(catlin_plan)
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return plan, model


def _ctx(plan, model):
    """The checks read ``ctx.model.plan``: a variant plan rides on a copy of the model."""
    model = copy.copy(model)
    model.plan = plan
    return check_context(model=model)


def _mine(findings):
    return [f for f in findings if set(f.element_tags) & set(_TEST)]


def test_a_soakaway_bed_disposes_and_is_not_a_source(soak):
    network = build_network(soak[0])
    node = network.nodes["FB-TEST-SOAK"]
    assert node.kind == "soakaway" and node.disposes and node.in_invert_m is None
    assert "FB-TEST-SOAK" not in network.sources()
    assert "FB-TEST-PLAIN" in network.sources()
    reached, path, _ = network.reaches_disposal("FB-TEST-PLAIN", first_hop=EdgeKind.PRIMARY)
    assert reached and path == ["FB-TEST-PLAIN", "FB-TEST-SOAK"]


def test_the_keyword_adds_no_edge_and_is_unresolved_on_a_plain_bed(soak, catlin_plan):
    network = build_network(soak[0])
    assert not network.out_edges("FB-TEST-SOAK", EdgeKind.PRIMARY)
    assert [e.target for e in network.out_edges("FB-TEST-SOAK", EdgeKind.OVERFLOW)] == [
        "daylight"]
    bad = soak_plan(catlin_plan, plain=plain_bed(
        drain_tile_spec=soak_bed().drain_tile_spec))
    assert ("FB-TEST-PLAIN", "soakaway") in build_network(bad).unresolved


def test_every_source_reaches_an_outfall(soak):
    assert not [f for f in _mine(network_outfall(check_context(model=soak[1])))
                if f.result is Result.FAIL]


def test_the_fallback_is_graded_once_per_body(soak, catlin_plan):
    found = _mine(network_fallback(check_context(model=soak[1])))
    assert len(found) == 1 and found[0].result is Result.PASS, [f.message for f in found]
    assert set(found[0].element_tags) == {"FB-TEST-SOAK", "FB-TEST-PLAIN"}
    # No overflow on any bed of the body: ONE FAIL for the body, not one per bed.
    plan = soak_plan(catlin_plan, soak=soak_bed(overflow_ref=None, overflow_invert=None))
    found = _mine(network_fallback(_ctx(plan, soak[1])))
    assert len(found) == 1 and found[0].result is Result.FAIL


def test_an_overflow_back_into_the_same_body_is_no_fallback(soak, catlin_plan):
    plan = soak_plan(catlin_plan, soak=soak_bed(overflow_ref="FB-TEST-PLAIN"))
    found = _mine(network_fallback(_ctx(plan, soak[1])))
    assert [f.result for f in found] == [Result.FAIL], [f.message for f in found]


def _arrival(plan, model):
    return [f for f in _mine(outfall_connection(_ctx(plan, model)))
            if "FD-TEST-SOAK" in f.element_tags and f.result is not Result.PASS]


def test_a_lateral_arrives_inside_the_stone_band(soak, catlin_plan):
    assert not _arrival(*soak)
    # 8" below the course's floor: into undisturbed ground under the stone.
    deep = soak_plan(catlin_plan, run=lateral(end_invert=ft(-8) - inch(44)))
    assert _arrival(deep, soak[1])
    # Stops 4' short of the bed in plan.
    from typehaus.quantities import pt
    short = soak_plan(catlin_plan, run=lateral(path=(pt(ft(72), ft(0)), pt(ft(72), ft(6)))))
    assert _arrival(short, soak[1])


def test_the_soakaway_names_what_feeds_it(soak, catlin_plan):
    assert not _mine(f for f in inlet_reciprocity(check_context(model=soak[1]))
                     if f.result is not Result.PASS)
    plan = soak_plan(catlin_plan, soak=soak_bed(inlet_refs=("FB-TEST-PLAIN",)))
    found = [f for f in inlet_reciprocity(_ctx(plan, soak[1]))
             if "FD-TEST-SOAK" in f.element_tags]
    assert found and found[0].result is Result.FAIL


def test_discharges_to_a_soakaway_bed_resolve(soak, catlin_plan):
    assert not _mine(f for f in discharge_consistency(check_context(model=soak[1]))
                     if f.result is Result.FAIL)
    bad = soak_plan(catlin_plan, plain=plain_bed(
        drain_tile_spec=soak_bed().drain_tile_spec))
    found = [f for f in discharge_consistency(_ctx(bad, soak[1]))
             if "FB-TEST-PLAIN" in f.element_tags]
    assert found and "only a bed with its own soakaway course" in found[0].message


def test_a_pipeless_bed_drains_through_its_stone(catlin_plan):
    """No tile: the plain bed's stone lets go into the soakaway it abuts, and that is both a
    network edge and the drainage ``structural.frost_depth`` reads."""
    from typehaus.checks.mep.drainage_network import tile_lead
    from typehaus.resolve.drainage_network import drainage_evidence, stone_bodies

    pipeless = plain_bed(drain_tile=False, drain_tile_spec=None, discharge_ref="FB-TEST-SOAK")
    plan = soak_plan(catlin_plan, plain=pipeless)
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    assert not [s for s in model.solids if s.tag.startswith("FB-TEST-PLAIN-DT")]

    network = build_network(plan)
    assert network.nodes["FB-TEST-PLAIN"].kind == "bed_stone"
    reached, path, _ = network.reaches_disposal("FB-TEST-PLAIN", first_hop=EdgeKind.PRIMARY)
    assert reached and path == ["FB-TEST-PLAIN", "FB-TEST-SOAK"]
    assert stone_bodies(model)["FB-TEST-PLAIN"] == {"FB-TEST-PLAIN", "FB-TEST-SOAK"}
    assert "continuous stone into FB-TEST-SOAK" in drainage_evidence(model)["FB-TEST-PLAIN"]
    assert all(f.result is Result.PASS for f in _mine(tile_lead(_ctx(plan, model))))

    # Named at a bed its stone does not reach, it drains nothing.
    stray = pipeless.model_copy(update={"discharge_ref": "FB-SG-W2"})
    plan = soak_plan(catlin_plan, plain=stray)
    model, _ = resolve(plan)
    assert "FB-TEST-PLAIN" not in drainage_evidence(model)
    assert any(f.result is Result.FAIL for f in _mine(tile_lead(_ctx(plan, model))))
