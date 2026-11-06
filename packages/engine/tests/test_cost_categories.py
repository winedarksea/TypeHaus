"""The Estimate page's sub-trade categories and levels, on catlin's real estimate.

Labels only: a category or a level takes no part in any total, so what these pin is that
the rows land where a reader would look for them, and that splitting by level loses nothing.
"""

from __future__ import annotations

import pytest

from typehaus.cli.prices import estimate_costs, load_prices
from typehaus.takeoff.cost_categories import CategoryFacts, category_of
from typehaus.takeoff.tasks import level_index


@pytest.fixture(scope="module")
def estimate(catlin_model_ro, catlin_areas):
    from pathlib import Path

    from typehaus.takeoff import bill_of_materials

    prices = load_prices(Path("houses/catlin"))
    return estimate_costs(bill_of_materials(catlin_model_ro), prices, catlin_areas,
                          level_of=level_index(catlin_model_ro))


def _rows(estimate):
    return [(section, row) for section, body in estimate["sections"].items()
            for row in body["rows"]]


def _filed(estimate, section, key):
    return {(row["trade"], row["category"]) for s, row in _rows(estimate)
            if s == section and row["key"] == key}


def test_catlin_rows_land_in_the_category_a_reader_looks_for(estimate) -> None:
    assert _filed(estimate, "placeables", "ED-T-LT-CAN4") == {("electrical", "lighting")}
    assert _filed(estimate, "placeables", "ED-T-AP-CEILING") == {("low_voltage", "devices")}
    pipe = {cat for s, row in _rows(estimate) if s == "pipe_runs"
            for cat in [(row["trade"], row["category"])]}
    assert pipe == {("plumbing", "pipe")}
    allowances = {row["category"] for s, row in _rows(estimate) if s == "allowances"}
    assert allowances == {"allowances"}


def test_no_in_total_row_is_uncategorised(estimate) -> None:
    bare = [(s, row["key"]) for s, row in _rows(estimate)
            if estimate["sections"][s]["in_total"] and not row.get("category")]
    assert bare == []


def test_level_subtotals_sum_exactly_to_the_total(estimate) -> None:
    by_level: dict[str, float] = {}
    for s, row in _rows(estimate):
        if estimate["sections"][s]["in_total"]:
            by_level[row["level"]] = by_level.get(row["level"], 0.0) + row["cost"]["low"]
    assert "building" in by_level and len(by_level) > 2
    assert sum(by_level.values()) == pytest.approx(estimate["total"]["low"], abs=0.01)


def test_a_house_override_beats_the_facts() -> None:
    row = {"type": "LUM", "domain": "electrical"}
    facts = CategoryFacts(frozenset({"LUM"}), {})
    assert category_of("placeables", "LUM", "electrical", row, facts) == "lighting"
    overrides = {"placeables": "devices", "placeables:LUM": "decorative"}
    assert category_of("placeables", "LUM", "electrical", row, facts, overrides) == "decorative"
    assert category_of("placeables", "X", "electrical", {}, facts, overrides) == "devices"
