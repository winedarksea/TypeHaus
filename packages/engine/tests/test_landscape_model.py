"""The planting and bioretention vocabulary: registered, dialect-callable, integrity-checked."""

from __future__ import annotations

import dataclasses

from _helpers import check_context

from typehaus.checks.integrity.catalog_tags import CATALOGS
from typehaus.checks.integrity.plant_refs import plant_type_ref
from typehaus.findings import Result
from typehaus.model import FloorOpeningPurpose, Plant, PlantingBed, PocketLayout
from typehaus.model.registry import constructor_names, element_kinds
from typehaus.quantities import ft, pt


def test_every_new_kind_is_registered_and_callable_from_plan_source() -> None:
    kinds = element_kinds()
    for name in ("Plant", "PlantingBed", "Trellis", "RainGarden"):
        assert name in kinds
    for name in ("PlantType", "GridLayout", "PocketLayout", "AccentRule",
                 "DischargeExtension", "Plant", "RainGarden"):
        assert name in constructor_names()
    assert FloorOpeningPurpose.PLANTING.value == "planting"
    assert "plant_types" in CATALOGS


def _ctx(catlin_model_ro, *extra):
    plan = catlin_model_ro.plan.with_elements(
        "yard-grade", (*catlin_model_ro.plan.storey_elements("yard-grade"), *extra))
    return check_context(plan, dataclasses.replace(catlin_model_ro, plan=plan))


def test_catlin_plant_references_all_resolve(catlin_model_ro) -> None:
    assert plant_type_ref(check_context(model=catlin_model_ro)) == []


def test_an_unknown_plant_type_is_an_error(catlin_model_ro) -> None:
    ctx = _ctx(catlin_model_ro, Plant(uid="TSTP000001", tag="PL-TEST", type_ref="PT-NOPE",
                                      position=pt(ft(0), ft(-40))))
    failures = [f for f in plant_type_ref(ctx) if f.result is Result.FAIL]
    assert failures and failures[0].severity.value == "error"
    assert "PT-NOPE" in failures[0].message


def test_a_bed_needs_exactly_one_layout_and_real_slabs(catlin_model_ro) -> None:
    neither = PlantingBed(uid="TSTP000002", tag="PB-TEST-0", type_ref="PT-SCH-JAZZ")
    bad_slab = PlantingBed(uid="TSTP000003", tag="PB-TEST-1", type_ref="PT-SCH-JAZZ",
                           pockets=PocketLayout(slab_refs=("W-M-N1",)))
    messages = [f.message for f in plant_type_ref(_ctx(catlin_model_ro, neither, bad_slab))]
    assert any("exactly one of grid or pockets" in m for m in messages)
    assert any("not a Slab" in m for m in messages)
