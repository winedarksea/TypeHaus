"""Minnesota sanitary cleanout audit and physical Catlin deliverables."""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.profile import get_profile
from typehaus.checks.mep.drain_cleanouts import drain_cleanouts, required_cleanout_locations
from typehaus.emit.draw.plumbingplan import build_plumbing_plan
from typehaus.emit.draw.scene import Leader, Symbol
from typehaus.quantities import ft
from typehaus.resolve.model import ResolvedDrainCleanout, ResolvedPipeRun
from typehaus.takeoff.plumbing import plumbing_takeoff


def _model(path, z, *, tag="PR-TEST-MAIN-DRAIN", serves=(), sanitary=True, cleanouts=()):
    run = ResolvedPipeRun(uid="TEST000001", tag=tag, storey="basement", system="drain",
                          path=tuple(path), diameter_m=ft(0, 3).meters,
                          z_start_m=z[0], z_end_m=z[-1], z_m=tuple(z),
                          length_m=sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
                                        + (z[i + 1] - z[i]) ** 2) ** 0.5
                                       for i, (a, b) in enumerate(zip(path, path[1:],
                                                                       strict=False))),
                          serves=serves, sanitary=sanitary)
    plan = SimpleNamespace(storeys=(SimpleNamespace(elevation=ft(0)),))
    return SimpleNamespace(pipe_runs=[run], drain_cleanouts=list(cleanouts), plan=plan)


def _cleanout(*, accessible=True, width=24, depth=24):
    return ResolvedDrainCleanout(
        uid="TESTCO0001", tag="CO-TEST", storey="basement",
        pipe_ref="PR-TEST-MAIN-DRAIN", position=(0.0, 0.0), fitting_z_m=0.0,
        cap_position=(0.0, 0.0), cap_z_m=ft(1).meters,
        direction="one_way", access="floor", wall_ref=None,
        clear_width_m=ft(0, width).meters,
        clear_depth_m=ft(0, depth).meters, accessible=accessible,
        diameter_m=ft(0, 3).meters)


def test_short_line_vertical_and_above_floor_exceptions():
    short = _model(((0, 0), (ft(4).meters, 0)), (0, -0.01))
    assert required_cleanout_locations(short) == []
    sink = _model(short.pipe_runs[0].path, (0, -0.01), serves=("FX-SINK",))
    assert [r.reason for r in required_cleanout_locations(sink)] == ["upper terminal"]
    vertical = _model(((0, 0), (ft(1).meters, 0)), (0, -ft(1).meters))
    assert required_cleanout_locations(vertical) == []
    above = _model(((0, 0), (ft(10).meters, 0)), (ft(1).meters, ft(1).meters - .01),
                   tag="PR-UPPER")
    assert required_cleanout_locations(above) == []
    assert required_cleanout_locations(_model(above.pipe_runs[0].path,
                                             above.pipe_runs[0].z_m,
                                             tag="PR-KITCH", serves=("FX-KITCH-SINK",)))
    assert required_cleanout_locations(_model(((0, 0), (ft(120).meters, 0)),
                                             (0, -0.1), sanitary=False)) == []


def test_100_foot_spacing_and_cumulative_turns():
    long_line = _model(((0, 0), (ft(110).meters, 0)), (0, -0.1))
    requirements = required_cleanout_locations(long_line)
    assert [r.reason for r in requirements] == ["upper terminal", "100 ft spacing"]
    assert requirements[1].point[0] == pytest.approx(ft(100).meters, abs=0.02)
    parent = _model(((ft(60).meters, 0), (ft(120).meters, 0)),
                    (-0.01, -0.02)).pipe_runs[0]
    child = _model(((0, 0), (ft(60).meters, 0)), (0, -0.01), tag="PR-CHILD").pipe_runs[0]
    chained = _model(((0, 0), (ft(1).meters, 0)), (0, -0.001))
    chained.pipe_runs = [parent, child]
    assert any(r.pipe_ref == parent.tag and r.reason == "100 ft spacing"
               and r.point[0] == pytest.approx(ft(100).meters, abs=0.02)
               for r in required_cleanout_locations(chained))
    turned = _model(((0, 0), (ft(6).meters, 0), (ft(6).meters, ft(6).meters),
                     (ft(12).meters, ft(6).meters)), (0, -0.01, -0.02, -0.03))
    assert any(r.reason == "cumulative turns >135 deg"
               for r in required_cleanout_locations(turned))


def test_missing_inaccessible_and_insufficient_clearance_fail():
    model = _model(((0, 0), (ft(10).meters, 0)), (0, -0.01))
    assert any(f.result.value == "fail" and "missing" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))
    model.drain_cleanouts = [_cleanout(accessible=False)]
    assert any(f.result.value == "fail" and "inaccessible" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))
    model.drain_cleanouts = [replace(_cleanout(), clear_width_m=ft(1).meters)]
    assert any(f.result.value == "fail" and "clear" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))
    model.drain_cleanouts = [replace(_cleanout(), pipe_ref="PR-WRONG")]
    assert any(f.result.value == "fail" and "not connected" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))
    model.drain_cleanouts = [replace(_cleanout(), fitting_z_m=ft(-8).meters)]
    assert any(f.result.value == "fail" and "missing upper terminal" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))


def test_two_way_grade_cleanout_substitutes_for_building_drain_terminal():
    model = _model(((0, 0), (ft(10).meters, 0)), (0, -0.01))
    model.plan.project = SimpleNamespace(site=SimpleNamespace(grade=ft(0)))
    two_way = replace(_cleanout(), position=(ft(10).meters, 0),
                      cap_position=(ft(10).meters, 0), fitting_z_m=-0.01,
                      cap_z_m=0, direction="two_way", access="grade")
    model.drain_cleanouts = [two_way]
    assert not any("missing upper terminal" in f.message
                   for f in drain_cleanouts(SimpleNamespace(model=model)))
    model.drain_cleanouts = [replace(two_way, direction="one_way")]
    assert any("missing upper terminal" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))


def test_catlin_cleanouts_have_plan_schedule_and_three_solids(catlin_model_ro):
    model = catlin_model_ro
    assert len(model.drain_cleanouts) == 12
    assert not any(r.pipe_ref.startswith("PR-A-")
                   for r in required_cleanout_locations(model))
    assert all(f.result.value == "pass"
               for f in drain_cleanouts(SimpleNamespace(model=model)))
    schedule = {row["tag"] for row in plumbing_takeoff(model)["takeoff"]["cleanouts"]}
    for cleanout in model.drain_cleanouts:
        assert cleanout.tag in schedule
        components = [s for s in model.solids
                      if s.tag == cleanout.tag or s.tag.startswith(cleanout.tag + "-")]
        assert {s.category for s in components} == {
            "cleanout_fitting", "cleanout_extension", "cleanout_cap"}
        assert len(components) == (5 if cleanout.direction == "two_way" else 3)
        assert all(s.sweep is not None for s in components)
        scene = build_plumbing_plan(model, cleanout.storey)
        assert any(isinstance(n, Symbol) and n.name == "cleanout"
                   and n.insert == pytest.approx(tuple(v / 0.0254
                                                        for v in cleanout.cap_position))
                   for n in scene.nodes)
        assert any(isinstance(n, Leader) and cleanout.tag in n.text for n in scene.nodes)


def test_minnesota_permit_checklist_includes_cleanouts():
    profile = get_profile("mn-2020")
    assert any("mep.drain_cleanouts" in item.check_ids for item in profile.permit_items)


def test_floor_cap_covered_by_fixture_fails(catlin_model_ro):
    model = copy.copy(catlin_model_ro)
    original = next(c for c in model.drain_cleanouts if c.tag == "CO-B-BATH")
    wc = next(item for item in model.canvas_objects if item.tag == "FX-B-BATH-WC")
    model.drain_cleanouts = [replace(c, cap_position=wc.position) if c.tag == original.tag else c
                             for c in model.drain_cleanouts]
    assert any(f.result.value == "fail" and "hidden by FX-B-BATH-WC" in f.message
               for f in drain_cleanouts(SimpleNamespace(model=model)))


def test_catlin_ifc_cleanout_components_are_sanitary_and_represented(catlin_ifc_path: Path,
                                                                      catlin_model_ro):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    f = ifcopenshell.open(str(catlin_ifc_path))
    sanitary = next(s for s in f.by_type("IfcDistributionSystem") if s.Name == "Sanitary")
    members = {member.Name for rel in f.by_type("IfcRelAssignsToGroup")
               if rel.RelatingGroup == sanitary for member in rel.RelatedObjects}
    fittings = {e.Name: e for e in f.by_type("IfcPipeFitting")}
    for cleanout in catlin_model_ro.drain_cleanouts:
        for tag in (cleanout.tag, cleanout.tag + "-EXT", cleanout.tag + "-CAP"):
            assert tag in members
            assert fittings[tag].Representation is not None
