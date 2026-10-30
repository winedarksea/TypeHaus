"""Bedroom product selection reaches the estimate once, with its own cushion and visit."""

from __future__ import annotations

import pytest
from _helpers import CATLIN

from typehaus.cli.prices import PriceRange, estimate_costs, load_prices
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.finishes import floor_finish_rows
from typehaus.takeoff.product_labels import product_labels
from typehaus.takeoff.task_state import load_tasks

_BEDROOM_FINISH = "catlin-carpet-raised"
_BEDROOM_CUSHION = "catlin-bedroom-carpet-pad"
_BEDROOM_ROOMS = {"RM-M-BED", "RM-M-CLOSET", "RM-S-BED1", "RM-S-BED2", "RM-S-BED3"}


def test_bedroom_carpet_presentation_matches_the_provisional_selection(catlin_plan):
    material = next(item for item in catlin_plan.library.materials
                    if item.tag == _BEDROOM_FINISH)
    assert material.color == "#e5dccb"
    assert material.finish == "carpet-pile"
    # Product pile height is not the installed assembly depth; keep coordination pending.
    assert material.finish_thickness_in == 0.75


@pytest.fixture(scope="module")
def floor_rows(catlin_model_ro):
    return floor_finish_rows(catlin_model_ro)


@pytest.mark.parametrize(("material_tag", "model", "url"), [
    (_BEDROOM_FINISH, "7L89100101", "https://www.lowes.com/pd/5013298681"),
    (_BEDROOM_CUSHION, "150553488-33", "https://www.homedepot.com/p/203393650"),
])
def test_bedroom_materials_resolve_to_the_selected_products(catlin_plan, material_tag, model, url):
    material = next(item for item in catlin_plan.library.materials if item.tag == material_tag)
    product = catlin_plan.library.product(material.product_ref)
    assert product is not None
    assert product.model == model
    assert product.url == url
    labels = product_labels(catlin_plan)
    assert model in labels["floor_finishes", material_tag]


def test_bedroom_cushion_is_ordered_once_for_only_the_bedroom_area(catlin_model_ro, floor_rows):
    bedroom = next(row for row in floor_rows if row["finish"] == _BEDROOM_FINISH)
    cushions = [row for row in floor_rows if row["finish"] == _BEDROOM_CUSHION]
    assert len(cushions) == 1
    cushion = cushions[0]
    assert cushion["under"] == _BEDROOM_FINISH
    assert cushion["known"]
    assert set(bedroom["rooms"]) == set(cushion["rooms"]) == _BEDROOM_ROOMS
    area_sqft = sum(room.field_area_m2 for room in catlin_model_ro.rooms
                    if room.tag in _BEDROOM_ROOMS) * 10.7639104
    assert bedroom["net_area_sqft"] == pytest.approx(area_sqft, abs=0.05)
    for quantity in ("net_area_sqft", "order_area_sqft"):
        assert cushion[quantity] == bedroom[quantity]
    generic_pads = [row for row in floor_rows if row["finish"] == "carpet-pad"]
    assert len(generic_pads) == 1
    assert generic_pads[0]["under"] == "carpet"
    assert generic_pads[0]["rooms"] == ["RM-B-PLAY-N"]
    # Bedroom procurement must not change the carpeted flight's walking surface.
    stair = next(item for item in catlin_model_ro.stairs if item.tag == "ST-B2M")
    assert stair.finish_material == "carpet"


def test_bedroom_estimate_and_installation_visit_include_every_selected_layer(
        catlin_model_ro, catlin_areas):
    catlin_plan = catlin_model_ro.plan
    prices = load_prices(CATLIN)
    assert prices is not None
    carpet_rate = prices.floor_finishes[_BEDROOM_FINISH]
    cushion_rate = prices.floor_finishes[_BEDROOM_CUSHION]
    assert carpet_rate.material == PriceRange(3, 4)
    assert carpet_rate.labour == PriceRange(1, 2.25)
    assert cushion_rate.material == PriceRange(0.35, 1)
    assert cushion_rate.labour == PriceRange(0, 0)

    estimate = estimate_costs(bill_of_materials(catlin_model_ro), prices, catlin_areas,
                              products=product_labels(catlin_plan))
    rows = estimate["sections"]["floor_finishes"]["rows"]
    visits = load_tasks(CATLIN).visits.entries
    for key in (_BEDROOM_FINISH, _BEDROOM_CUSHION, "catlin-carpet-underlayment"):
        billed = [row for row in rows if row["key"] == key]
        assert len(billed) == 1
        # Underlayment is $0 on the low side (owner: only if the mock-up needs it); high stays priced.
        if key == "catlin-carpet-underlayment":
            assert billed[0]["cost"]["low"] >= 0 and billed[0]["cost"]["high"] > 0
        else:
            assert billed[0]["cost"]["low"] > 0
        assert not any(row["key"] == key for row in estimate["unpriced"])
        assigned = [slug for slug, visit in visits.items()
                    if f"floor_finishes:{key}" in visit.rows]
        assert assigned == ["task/flooring/building/carpet"]
    cushion_row = next(row for row in rows if row["key"] == _BEDROOM_CUSHION)
    assert cushion_row["product"] == "Future Foam 150553488-33"
    assert cushion_row["labour"] == {"low": 0, "high": 0}
