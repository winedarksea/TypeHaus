"""``Layer.sheet_length`` — the premise the blocking factor and the sheet order share.

Table R602.10.3(2) item 8 doubles a CS-WSP line's requirement where a panel has a horizontal
sheathing joint left unblocked. Whether there is a joint is a fact about the SHEET, so the
check reads it off the layer, and the order bills the same sheet. Unstated is UNKNOWN.
"""

from __future__ import annotations

from copy import copy

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.braced_wall import braced_wall_panels
from typehaus.checks.structural.bracing_eval import evaluate_storey
from typehaus.findings import Result
from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import ft, inch
from typehaus.resolve.sheet_stock import sheet_label, sheets_for
from typehaus.takeoff.framing import sheet_goods_takeoff


def _stamp(layers, length):
    return tuple(layer.model_copy(update={"sheet_length": length})
                 if layer.function is LayerFunction.SHEATHING else layer for layer in layers)


def _with_sheets(model, length):
    """A shallow copy of ``model`` whose every sheathing layer states ``length``."""
    library = model.plan.library
    assemblies = tuple(
        a.model_copy(update={
            "layers": _stamp(a.layers, length),
            "substitute": tuple(s.model_copy(update={"replacement": _stamp(s.replacement,
                                                                           length)})
                                for s in a.substitute)})
        for a in library.assemblies)
    out = copy(model)
    out.plan = model.plan.model_copy(
        update={"library": library.model_copy(update={"assemblies": assemblies})})
    return out


def _ctx(model):
    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2020)


def _ratios(model):
    return {(storey, ev.line.tag): ev.provided_ft / ev.required_ft
            for storey in ("main", "second", "garage")
            for ev in evaluate_storey(model, storey) if ev.required_ft}


def test_an_unstated_sheet_is_unknown_and_names_the_wall(catlin_model_ro):
    model = _with_sheets(catlin_model_ro, None)
    evaluations = evaluate_storey(model, "main")
    assert evaluations and all(ev.required_ft is None for ev in evaluations)
    e1 = next(ev for ev in evaluations if ev.line.tag == "BWL-W-A-E1")
    assert any("W-M-E1 (sheathing) states no sheet_length" in gap for gap in e1.gaps)
    findings = braced_wall_panels(_ctx(model))
    assert not [f for f in findings if f.result is Result.PASS]
    assert any(f.result is Result.UNKNOWN and "sheet_length" in f.message for f in findings)


def test_eight_foot_sheets_fail_three_lines(catlin_model_ro):
    """The note's 'one line' was four: 108" and 100" walls both joint a 96" sheet. Three
    since 2026-09-24: the plant room's gypsum lifted the second storey's S1 line off the
    x1.40 non-gypsum factor (0.82 -> 1.14)."""
    ratios = _ratios(_with_sheets(catlin_model_ro, ft(8)))
    failing = {key: round(r, 2) for key, r in ratios.items() if r < 1.0}
    assert failing == {("main", "BWL-W-A-E1"): 0.78, ("main", "BWL-W-A-S1"): 0.94,
                       ("garage", "BWL-W-G-N"): 0.94}
    e1 = next(ev for ev in evaluate_storey(_with_sheets(catlin_model_ro, ft(8)), "main")
              if ev.line.tag == "BWL-W-A-E1")
    item8 = [f for f in e1.factors if "item 8" in f.row]
    assert item8 and "R602.10.4.4 exception 1" in item8[0].row
    assert "W-M-E1 (4x8 on 108.0 in)" in item8[0].row


@pytest.mark.parametrize("length", [ft(9), ft(10)])
def test_a_sheet_that_reaches_the_plate_takes_no_factor(catlin_model_ro, length):
    model = _with_sheets(catlin_model_ro, length)
    ratios = _ratios(model)
    assert len(ratios) == 12 and min(ratios.values()) > 1.5
    e1 = next(ev for ev in evaluate_storey(model, "main") if ev.line.tag == "BWL-W-A-E1")
    assert not [f for f in e1.factors if "item 8" in f.row]
    assert any("item 8" in note and sheet_label(length.inches) in note
               for note in e1.not_taken)


def _walls(model):
    return {(r["material"], r["sheet"]): r for r in sheet_goods_takeoff(model)
            if r["scope"] == "exterior wall"}


def test_the_order_bills_the_same_sheet(catlin_model_ro):
    """Catlin (owner, 2026-09-22): the house in 4x10, the garage in 4x9."""
    house = _walls(catlin_model_ro)
    assert ("struct-1-plywood", "4x10") in house and ("cdx-plywood", "4x9") in house
    for (_material, size), row in house.items():
        length = {"4x8": 96.0, "4x9": 108.0, "4x10": 120.0}[size]
        assert abs(int(row["sheets"]) - sheets_for(float(row["net_area_sqft"]), length)) <= 1
    unstated = _walls(_with_sheets(catlin_model_ro, None))
    assert {size for (_m, size) in unstated} == {"4x8"}
    assert (unstated[("struct-1-plywood", "4x8")]["sheets"]
            > house[("struct-1-plywood", "4x10")]["sheets"])


def test_sheet_length_must_be_positive():
    with pytest.raises(ValueError):
        Layer(name="s", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING, sheet_length=inch(0))


def test_sheet_labels():
    assert [sheet_label(x) for x in (96.0, 108.0, 120.0, 114.0, 100.0)] == [
        "4x8", "4x9", "4x10", "4x9.5", "4x100in"]
