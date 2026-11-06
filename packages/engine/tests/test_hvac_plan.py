"""HVAC plan builder — M-101 (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.hvacplan import build_hvac_plan, duct_storeys, has_hvac_content
from typehaus.emit.draw.scene import Polyline, Symbol, Text
from typehaus.quantities import M_PER_IN


def test_every_storey_has_hvac_content(catlin_model):
    # ERV distribution reaches all four storeys now (houses/catlin/plan/mep.py).
    for storey in ("basement", "main", "second", "attic"):
        assert has_hvac_content(catlin_model, storey), storey


def test_hvac_plan_symbol_census(catlin_model):
    scene = build_hvac_plan(catlin_model, "second")
    layers = scene.by_layer()
    assert "M-HVAC-SDFF" in layers and "M-HVAC-RDFF" in layers
    # The ensuite shower's dedicated stale pull draws on its own exhaust layer.
    assert "M-HVAC-EXHS" in layers
    registers = [n for n in scene.nodes if isinstance(n, Symbol)
                 and n.name.startswith("register-")]
    # Count read off the plan source, not pinned: every second-storey Register.
    expected = sum(1 for e in catlin_model.plan.storey_elements("second")
                   if e.element_kind == "Register")
    assert len(registers) == expected
    assert any(n.name == "register-exhaust" for n in registers)
    duct_polys = [n for n in scene.nodes if isinstance(n, Polyline)
                 and n.layer in ("M-HVAC-SDFF", "M-HVAC-RDFF", "M-HVAC-EXHS")]
    assert duct_polys


def test_hvac_plan_marks_every_crossing_and_explains_fire_blocking_once(catlin_model):
    # The main ceiling's ducts lie in the second floor's trusses: they print on main (M1-108).
    scene = build_hvac_plan(catlin_model, "main")
    drawn_on = duct_storeys(catlin_model)
    crossed_ducts = [duct for duct in catlin_model.ducts
                     if drawn_on.get(duct.uid, duct.storey) == "main" and duct.crossings]
    assert crossed_ducts
    assert sum("fire blocking" in note for note in scene.notes) == 1
    assert "every marked crossing" in scene.notes[0]
    for duct in crossed_ducts:
        for x, y in duct.crossings:
            center = (x / M_PER_IN, y / M_PER_IN)
            marks = [node for node in scene.nodes if isinstance(node, Polyline)
                     and len(node.points) == 2
                     and all(abs((node.points[0][axis] + node.points[1][axis]) / 2
                                 - center[axis]) < 1e-6 for axis in (0, 1))]
            assert len(marks) >= 2


def test_hvac_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_hvac_plan(catlin_model, "second")
    path = write_dxf(scene, tmp_path / "hvac.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"M-HVAC-SDFF", "M-HVAC-RDFF"} <= names


def test_erv_legs_print_where_they_meet_the_erv(catlin_model):
    """OA/EA are filed on main and lie in the basement ceiling (M1-108); the wrapped OD and
    the ERV's own port tags print with them (M1-002, M1-009)."""
    texts = {n.content for n in build_hvac_plan(catlin_model, "basement").nodes
             if isinstance(n, Text)}
    assert '8" RD OUTDOOR AIR, 2" WRAP = 12" OD' in texts
    assert {'SUPPLY 6" RD', 'RETURN 6" RD', 'OUTDOOR 6" RD', 'EXHAUST 6" RD'} <= texts
