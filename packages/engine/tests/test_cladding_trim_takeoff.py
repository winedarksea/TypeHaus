from types import SimpleNamespace

import pytest

from typehaus.takeoff.cladding_trim import cladding_trim_takeoff


def test_inventory_groups_stock_by_part_and_length():
    def piece(tag, stock, length):
        return SimpleNamespace(category="cladding_trim", product="WIDE_OUTSIDE_CORNER",
                               trim_stock_length_in=stock, trim_length_m=length, tag=tag)

    model = SimpleNamespace(solids=[piece("long", 243.0, 5.0),
                                    piece("short-a", 122.0, 1.0),
                                    piece("short-b", 122.0, 2.0)])
    rows = cladding_trim_takeoff(model)
    assert [(row["part"], row["stock_length_in"], row["count"]) for row in rows] == [
        ("58132XX", 122.0, 2), ("58136XX", 243.0, 1),
    ]
    assert rows[0]["cut_length_ft"] == pytest.approx(3.0 / 0.3048, abs=0.01)


def test_inventory_rejects_missing_stock_metadata():
    model = SimpleNamespace(solids=[SimpleNamespace(category="cladding_trim", product=None,
                                                    trim_length_m=None,
                                                    trim_stock_length_in=None, tag="missing")])
    with pytest.raises(ValueError, match="missing"):
        cladding_trim_takeoff(model)
