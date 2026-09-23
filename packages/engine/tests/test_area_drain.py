"""An area drain: a grated basin in a slab, a solid riser, a SOURCE in the drainage graph.

Built on ``_soakaway_plan``'s pads: a 4" slab over them carries AD-TEST, whose riser lets go
inside FB-TEST-SOAK's flood course.
"""

from __future__ import annotations

import copy

import pytest
from _helpers import check_context
from _soakaway_plan import PAD_BOTTOM_FT, soak_bed, soak_plan

from typehaus.checks.mep.drainage import discharge_consistency
from typehaus.checks.mep.drainage_network import (
    inlet_reciprocity,
    network_outfall,
    outfall_connection,
)
from typehaus.findings import Result
from typehaus.model.floors import Slab
from typehaus.model.stormwater import AreaDrain
from typehaus.quantities import ft, inch, pt
from typehaus.resolve import resolve
from typehaus.resolve.drainage_network import EdgeKind, build_network

_IN = 0.0254
_SLAB_TOP_FT = PAD_BOTTOM_FT + 1.5
_OUTLET = ft(PAD_BOTTOM_FT) - inch(30)   # mid-course


def _slab() -> Slab:
    return Slab(uid="TSTADSL001", tag="SL-TEST-AD", assembly="GARDEN_COURT_SLAB",
                thickness=inch(4), top_elevation=ft(_SLAB_TOP_FT),
                outline=(pt(ft(70), ft(10)), pt(ft(78), ft(10)),
                         pt(ft(78), ft(14)), pt(ft(70), ft(14))))


def _drain(**update) -> AreaDrain:
    drain = AreaDrain(
        uid="TSTAD00001", tag="AD-TEST", position=pt(ft(72), ft(12)), grate_size=inch(12),
        basin_depth=inch(12), outlet_diameter=inch(4), outlet_invert=_OUTLET,
        host_ref="SL-TEST-AD", discharge_ref="FB-TEST-SOAK", product="NDS 1200",
        catchment=(pt(ft(70), ft(10)), pt(ft(78), ft(10)), pt(ft(78), ft(14)),
                   pt(ft(70), ft(14))))
    return drain.model_copy(update=update)


def _plan(catlin_plan, drain=None):
    soak = soak_bed(inlet_refs=("FB-TEST-PLAIN", "FD-TEST-SOAK", "AD-TEST"))
    return soak_plan(catlin_plan, soak=soak,
                     extra=(_slab(), drain if drain is not None else _drain()))


@pytest.fixture(scope="module")
def drained(catlin_plan):
    plan = _plan(catlin_plan)
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], [
        f.message for f in findings if f.severity.value == "error"]
    return plan, model


def _ctx(plan, model):
    model = copy.copy(model)
    model.plan = plan
    return check_context(model=model)


def test_the_rim_defaults_to_the_host_slab_top(drained):
    basin = next(s for s in drained[1].solids if s.tag == "AD-TEST")
    assert basin.category == "area_drain"
    assert basin.z1_m == pytest.approx(_SLAB_TOP_FT * 0.3048)
    assert basin.z1_m - basin.z0_m == pytest.approx(12 * _IN)


def test_the_riser_runs_from_the_basin_floor_to_the_outlet(drained):
    basin = next(s for s in drained[1].solids if s.tag == "AD-TEST")
    riser = next(s for s in drained[1].solids if s.tag == "AD-TEST-RISER")
    assert riser.category == "area_drain_riser"
    assert riser.z1_m == pytest.approx(basin.z0_m)
    assert riser.z0_m == pytest.approx(_OUTLET.meters)


@pytest.mark.parametrize(("drain", "cid"), [
    (_drain(host_ref="SL-NOWHERE"), "integrity.area_drain_host"),
    (_drain(grate_size=inch(0)), "integrity.area_drain_geometry"),
    (_drain(outlet_invert=ft(_SLAB_TOP_FT)), "integrity.area_drain_geometry"),
])
def test_a_drain_that_cannot_be_built_is_an_error(catlin_plan, drain, cid):
    _, findings = resolve(_plan(catlin_plan, drain))
    assert any(f.check_id == cid and f.severity.value == "error" for f in findings)


def test_an_area_drain_is_a_source_with_a_primary_edge(drained):
    network = build_network(drained[0])
    assert network.nodes["AD-TEST"].kind == "area_drain"
    assert "AD-TEST" in network.sources()
    edge, = network.out_edges("AD-TEST", EdgeKind.PRIMARY)
    assert edge.target == "FB-TEST-SOAK"
    assert edge.out_invert_m == pytest.approx(_OUTLET.meters)
    assert not [f for f in network_outfall(check_context(model=drained[1]))
                if "AD-TEST" in f.element_tags and f.result is Result.FAIL]


def _arrival(plan, model):
    return [f for f in outfall_connection(_ctx(plan, model))
            if "AD-TEST" in f.element_tags and f.result is Result.FAIL]


def test_the_riser_arrives_in_the_stone(drained, catlin_plan):
    assert not _arrival(*drained)
    # Let go 12" under the course's floor: undisturbed ground.
    deep = _plan(catlin_plan, _drain(outlet_invert=ft(PAD_BOTTOM_FT) - inch(48)))
    assert _arrival(deep, drained[1])


def test_reciprocity_and_consistency(drained, catlin_plan):
    assert not [f for f in inlet_reciprocity(check_context(model=drained[1]))
                if "AD-TEST" in f.element_tags]
    assert not [f for f in discharge_consistency(check_context(model=drained[1]))
                if "AD-TEST" in f.element_tags]
    orphan = soak_plan(catlin_plan, extra=(_slab(), _drain()))
    assert [f for f in inlet_reciprocity(_ctx(orphan, drained[1]))
            if "AD-TEST" in f.element_tags and f.result is Result.FAIL]
    lost = _plan(catlin_plan, _drain(discharge_ref="FB-NOWHERE"))
    assert [f for f in discharge_consistency(_ctx(lost, drained[1]))
            if "AD-TEST" in f.element_tags and f.result is Result.FAIL]


def test_takeoff_trade_and_ifc(drained):
    from typehaus.emit.ifc.structural import _SOLID_IFC_CLASS
    from typehaus.emit.trades import DRAINAGE_CATEGORIES
    from typehaus.takeoff.drainage import drainage_takeoff

    rows = {r["category"]: r for r in drainage_takeoff(drained[1])
            if "AD-TEST" in r["tags"]}
    assert rows["area_drain"]["count"] == 1 and rows["area_drain"]["product"] == "NDS 1200"
    riser_ft = (PAD_BOTTOM_FT + 1.5 - 1.0) - (PAD_BOTTOM_FT - 2.5)
    assert rows["area_drain_riser"]["length_ft"] == pytest.approx(riser_ft, abs=0.05)
    assert {"area_drain", "area_drain_riser"} <= set(DRAINAGE_CATEGORIES)
    assert _SOLID_IFC_CLASS["area_drain"] == ("IfcWasteTerminal", "GULLYSUMP")
