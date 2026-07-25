"""V8 — first-class compare of two variants of the same design (→ 20 §Diff)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.diff import (CompareReport, VariantSelection, apply_assembly_swaps,
                           compare_models, compare_variants)
from typehaus.resolve import resolve
from typehaus.source import load_plan

_OLD = "HOUSE_WALL_2X6_WITH_ZIPR"
_NEW = "HOUSE_WALL_2X4_WITH_CI"


def test_same_variant_has_no_substantive_change(starter_dir: Path):
    a = VariantSelection(house=starter_dir, label="A")
    b = VariantSelection(house=starter_dir, label="B")
    report = compare_variants(a, b)
    assert isinstance(report, CompareReport)
    assert report.diff.substantive() == []
    assert report.quantity_deltas == []


def test_report_structure_is_stable_and_serializable(starter_dir: Path):
    report = compare_variants(VariantSelection(house=starter_dir),
                              VariantSelection(house=starter_dir, swaps={_OLD: _NEW}))
    payload = report.as_dict()
    assert set(payload) == {"variants", "element_counts", "element_changes", "quantity_deltas",
                            "envelope_deltas", "check_deltas"}
    assert set(payload["variants"]) == {"a", "b"}
    for change in payload["element_changes"]:
        assert {"kind", "tag", "ifc_class", "delta"} <= set(change)
    for qty in payload["quantity_deltas"]:
        assert {"profile", "metric", "baseline", "variant", "delta"} <= set(qty)
    for envelope in payload["envelope_deltas"]:
        assert {"assembly", "metric", "baseline", "variant", "delta", "note"} <= set(envelope)
    assert report.to_json() == report.to_json()  # deterministic


def test_assembly_swap_produces_element_and_quantity_deltas(starter_dir: Path):
    result = load_plan(starter_dir)
    base_plan = result.plan
    swapped_plan = apply_assembly_swaps(base_plan, {_OLD: _NEW})

    # The swap is a pure rewrite: only walls that referenced the old assembly change.
    base_walls = {w.tag: w.assembly for s in base_plan.storeys
                  for w in base_plan.storey_elements(s.tag) if w.element_kind == "Wall"}
    swapped_walls = {w.tag: w.assembly for s in swapped_plan.storeys
                     for w in swapped_plan.storey_elements(s.tag) if w.element_kind == "Wall"}
    assert any(base_walls[tag] == _OLD for tag in base_walls)
    assert all(swapped_walls[tag] == _NEW for tag, old in base_walls.items() if old == _OLD)

    model_a, _ = resolve(base_plan)
    model_b, _ = resolve(swapped_plan)
    report = compare_models(model_a, model_b, "2x6", "2x4")

    # Changing the exterior stud depth resizes the affected walls (thinner) and shifts the
    # framing takeoff off 2x6 studs — both surfaced without hardcoding either side.
    assert report.diff.substantive(), "swapping the wall assembly must register element changes"
    assert report.quantity_deltas, "swapping the stud size must move the framing takeoff"


def test_swap_leaves_unrelated_plan_untouched(starter_dir: Path):
    result = load_plan(starter_dir)
    unchanged = apply_assembly_swaps(result.plan, {"NO_SUCH_ASSEMBLY": _NEW})
    assert unchanged is result.plan
