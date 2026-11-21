"""EQ-B-ERV's strut trapeze: the derived rods and ``structural.equipment_hangers``."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from typehaus.checks.structural.equipment_hangers import equipment_hangers
from typehaus.findings import Result

_IN = 0.0254


def _rods(model):
    return [h for h in model.equipment_hangers if h.equipment_tag == "EQ-B-ERV"]


def test_erv_hangs_on_four_bridged_rods(catlin_model_ro) -> None:
    rods = _rods(catlin_model_ro)
    assert len(rods) == 4 and all(r.gap is None for r in rods)
    # Joist underside (-11 7/8") less the case bottom: derived, not authored.
    assert all(abs(r.drop_m / _IN - 57.56) < 0.1 for r in rods)
    for rod in rods:
        assert [s.profile for s in rod.bridge] == ["11.875 TJI 230"] * 2
        assert abs(sum(s.share for s in rod.bridge) - 1.0) < 1e-9
        # 21" side + 2 x 2" (2026-11-21: the 1 1/2" overhang put a rod into EQ-B-ERV-MAN-SUP).
        assert abs(rod.strut_length_m / _IN - 25.0) < 0.01
        assert abs(rod.load_lb - 47 / 4) < 1e-9
        # The bridge bears on the flange tops (TJI 230's 1 1/4") inside the bay, clear of the
        # ceiling board under the joists, cut between the two webs (16" less a 3/8" web).
        underside = rod.strut_top_z_m + rod.drop_m
        assert abs((rod.bridge_z_m - underside) / _IN - 1.25) < 1e-6
        assert abs(rod.bridge_length_m / _IN - (16.0 - 0.375)) < 0.01
        assert {s.side for s in rod.bridge} <= {1, -1}
    tags = {s.tag for s in catlin_model_ro.solids if s.category == "equipment_hanger"}
    assert {"EQ-B-ERV-STRUT-1", "EQ-B-ERV-ROD-4", "EQ-B-ERV-BRIDGE-1"} <= tags


def _grade(model, plan, rods, products=None):
    library = SimpleNamespace(products=plan.library.products if products is None else products,
                              joist_flange_allowances=plan.library.joist_flange_allowances)
    return equipment_hangers(SimpleNamespace(model=SimpleNamespace(equipment_hangers=rods),
                                             plan=SimpleNamespace(library=library)))


def test_check_passes_and_names_what_is_unread(catlin_model_ro, catlin_plan) -> None:
    rods = _rods(catlin_model_ro)
    assert {f.result for f in _grade(catlin_model_ro, catlin_plan, rods)} == {Result.PASS}
    loose = [replace(rods[0], hangs_from=None, bridge=(), gap="nothing overhead"), *rods[1:]]
    unread = [p for p in catlin_plan.library.products if p.tag != "PROD-BLINE-ATR-3-8"]
    findings = (_grade(catlin_model_ro, catlin_plan, loose)
                + _grade(catlin_model_ro, catlin_plan, rods, unread))
    messages = [f.message for f in findings if f.result is Result.UNKNOWN]
    assert any("nothing overhead" in m for m in messages)
    assert any("PROD-BLINE-ATR-3-8 has no published rated_load_lb" in m for m in messages)


class _Hung:
    """The model with its trapeze rods swapped, read-only."""

    def __init__(self, model, rods) -> None:
        self._model, self.equipment_hangers = model, rods

    def __getattr__(self, name):
        return getattr(self._model, name)


def test_clearance_grades_a_rod_against_a_wrapped_run(catlin_model_ro) -> None:
    """A rod on DU-ERV-EA's centreline is inside its 1" wrap; 1/32" of contact is a touch."""
    from typehaus.checks.structural.equipment_hanger_clearance import (
        equipment_hanger_clearance,
    )

    duct = next(d for d in catlin_model_ro.ducts if d.tag == "DU-ERV-EA")
    (x0, y), (x1, _) = duct.path[3], duct.path[4]  # an east-west leg
    # 8" duct + 1" wrap + 3/16" rod radius.
    reach = (4.0 + 1.0 + 0.1875) * _IN

    def grade(offset_m):
        rod = replace(_rods(catlin_model_ro)[0], point=((x0 + x1) / 2.0, y + offset_m),
                      bridge=(), bridge_ends=())
        model = _Hung(catlin_model_ro, [rod])
        return [f for f in equipment_hanger_clearance(SimpleNamespace(model=model))
                if "DU-ERV-EA" in f.element_tags]

    hit = grade(0.0)
    assert [f.result for f in hit] == [Result.FAIL] and "rod 1 is 5.19\"" in hit[0].message
    assert grade(reach - _IN / 32.0) == []
