"""Shelf procurement routes each bank to exactly one ordering path."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.model import Material, ShelfProcurement
from typehaus.resolve.model import ResolvedShelf, ResolvedShelfBank


def _bank(procurement: str, *, host_kind: str = "placeable") -> ResolvedShelfBank:
    return ResolvedShelfBank(
        uid="SHELFTEST1", tag="SB-TEST", storey="main", host="CASE-TEST",
        host_kind=host_kind, material_ref="factory-oak-shelf", thickness_m=0.01905,
        depth_m=0.3048, profile="S4S", procurement=procurement,
        shelves=(ResolvedShelf(bay_index=0, width_m=0.9144, depth_m=0.3048,
                               clear_height_m=0.9144, count=3),),
    )


def _model(procurement: str):
    material = Material(tag="factory-oak-shelf", name="Factory oak shelf panel",
                        species="oak", product_ref="PROD-SHELF")
    return SimpleNamespace(
        shelf_banks=[_bank(procurement)],
        window_stools=(), stairs=(), openings=(), panelings=(), walls=(), solids=(), rooms=(),
        plan=SimpleNamespace(
            library=SimpleNamespace(materials=(material,)),
            storeys=(),
            all_elements=lambda: (),
            storey_elements=lambda _storey: (),
        ),
    )


def test_purchased_shelves_make_one_order_with_waste_cuts_and_product_label() -> None:
    from typehaus.cli.prices import PriceRange, Prices, estimate_costs
    from typehaus.takeoff.shelving import shelving_takeoff

    rows = shelving_takeoff(_model("purchased_separately"))
    assert len(rows) == 1
    row = rows[0]
    assert row["material"] == "factory-oak-shelf"
    assert row["pieces"] == 3
    assert row["net_area_sqft"] == pytest.approx(9.0)
    assert row["waste_pct"] == 10.0
    assert row["order_area_sqft"] == 10.0
    assert row["cuts"] == [{"pieces": 3, "finished_thickness_in": 0.75,
                              "finished_width_in": 36.0, "finished_depth_in": 12.0,
                              "tags": ["SB-TEST"]}]

    estimate = estimate_costs(
        {"shelving": rows}, Prices(Path("prices.toml"), shelving={"factory-oak-shelf": PriceRange(8, 8)}),
        products={("shelving", "factory-oak-shelf"): "Acme Oak Panel OP-12"},
    )
    priced = estimate["sections"]["shelving"]["rows"][0]
    assert priced["quantity"] == 10.0 and priced["cost"] == {"low": 80.0, "high": 80.0}
    assert priced["product"] == "Acme Oak Panel OP-12"


def test_host_included_shelves_produce_no_separate_stock_or_mill_order() -> None:
    from typehaus.takeoff.hardwood import hardwood_takeoff
    from typehaus.takeoff.shelving import shelving_takeoff

    model = _model("included_in_host")
    assert shelving_takeoff(model) == []
    assert hardwood_takeoff(model) == []


def test_custom_milled_shelves_skip_purchase_stock_and_enter_the_mill_schedule() -> None:
    from typehaus.takeoff.hardwood import hardwood_takeoff
    from typehaus.takeoff.shelving import shelving_takeoff

    model = _model("custom_milled")
    material = model.plan.library.materials[0].model_copy(update={"nominal_quarters": 4})
    model.plan.library.materials = (material,)
    assert shelving_takeoff(model) == []
    rows = hardwood_takeoff(model)
    assert len(rows) == 1 and rows[0]["use"] == "shelf"
    assert rows[0]["material"] == "factory-oak-shelf"


def test_wall_hosted_included_shelf_is_a_validation_error(catlin_plan) -> None:
    from typehaus.findings import Severity
    from typehaus.model.millwork import ShelfBank
    from typehaus.resolve import resolve

    model, findings = resolve(catlin_plan)
    assert not [f for f in findings if f.severity is Severity.ERROR]
    wall_tag = model.walls[0].tag
    for storey in catlin_plan.storeys:
        elements = catlin_plan.storey_elements(storey.tag)
        shelf = next((item for item in elements if isinstance(item, ShelfBank)), None)
        if shelf is None:
            continue
        changed = shelf.model_copy(update={"host": wall_tag,
                                           "procurement": ShelfProcurement.INCLUDED_IN_HOST})
        plan = catlin_plan.with_elements(
            storey.tag, [changed if item.tag == shelf.tag else item for item in elements])
        _model, findings = resolve(plan)
        errors = [f for f in findings if f.severity is Severity.ERROR]
        assert any(f.check_id == "integrity.shelf_bank_procurement" for f in errors)
        return
    pytest.fail("Catlin needs a wall-hosted ShelfBank for this validation contract")


def test_custom_milled_shelf_requires_rough_stock_metadata(catlin_plan) -> None:
    from typehaus.findings import Severity
    from typehaus.model.millwork import ShelfBank
    from typehaus.resolve import resolve

    for storey in catlin_plan.storeys:
        elements = catlin_plan.storey_elements(storey.tag)
        shelf = next((item for item in elements if isinstance(item, ShelfBank)), None)
        if shelf is None:
            continue
        changed = shelf.model_copy(update={"material_ref": "oak"})
        plan = catlin_plan.with_elements(
            storey.tag, [changed if item.tag == shelf.tag else item for item in elements])
        _model, findings = resolve(plan)
        errors = [f for f in findings if f.severity is Severity.ERROR]
        assert any(f.check_id == "integrity.shelf_bank_procurement" for f in errors)
        return
    pytest.fail("Catlin needs a custom ShelfBank for this validation contract")


def test_included_shelves_leave_the_host_placeable_billed(catlin_plan) -> None:
    from typehaus.resolve import resolve
    from typehaus.takeoff.placeables import placeables_takeoff

    model, findings = resolve(catlin_plan)
    assert not [f for f in findings if f.severity.value == "error"]
    bank = next(bank for bank in model.shelf_banks if bank.host_kind == "placeable")
    model.shelf_banks = [replace(item, procurement="included_in_host")
                         if item.tag == bank.tag else item for item in model.shelf_banks]
    host = next(item for item in model.canvas_objects if item.tag == bank.host)
    assert any(row["type"] == host.type_ref and row["count"] > 0
               for row in placeables_takeoff(model))
