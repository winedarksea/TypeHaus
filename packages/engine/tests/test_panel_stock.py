"""Sheet orders respect stock geometry and keep unlike purchases separate."""
from dataclasses import replace

import pytest

from typehaus.cli.cmd_millwork import _flat_rows
from typehaus.takeoff.panel_stock import PanelStockConfig, _sheet_count, panel_order_rows


@pytest.mark.parametrize(("blanks", "expected"), [
    ([], 0),
    ([(20, 60), (20, 60)], 1),
    # Area alone says one sheet, but these cannot share a grain-aligned sheet.
    ([(30, 60), (30, 60)], 2),
    ([(20, 60)] * 4, 2),
])
def test_count_respects_rectangular_fit(blanks, expected):
    assert _sheet_count(blanks, PanelStockConfig()) == expected


def test_kerf_and_edge_trimming_change_order_quantity():
    stock = PanelStockConfig(saw_kerf_in=0, edge_trim_in=0)
    assert _sheet_count([(24, 60)] * 2, stock) == 1
    assert _sheet_count([(24, 60)] * 2, replace(stock, saw_kerf_in=.125)) == 2
    assert _sheet_count([(24, 60)] * 2, replace(stock, edge_trim_in=.25)) == 2


def test_oversize_blank_is_not_silently_rotated_across_veneer_grain():
    with pytest.raises(ValueError, match="does not fit"):
        _sheet_count([(60, 20)], PanelStockConfig())


@pytest.mark.parametrize("changes", [
    {"width_in": 0}, {"saw_kerf_in": -1}, {"edge_trim_in": -1},
    {"edge_trim_in": 24},
])
def test_invalid_stock_is_rejected(changes):
    with pytest.raises(ValueError):
        PanelStockConfig(**changes)


def test_orders_combine_occurrences_but_keep_materials_separate():
    row = {"material": "birch", "species": "birch", "panel_grade": "A-1",
           "panel_core": "veneer core", "finish": "sealer", "nominal_stock": "0.75 in panel",
           "finished_width_in": 20, "finished_length_in": 60, "pieces": 1, "tags": ["bench-1"],
           "material_source": "Sound cores; no MDF."}
    orders = panel_order_rows([row, {**row, "tags": ["bench-2"]},
                               {**row, "material": "walnut", "species": "black walnut"}])
    assert len(orders) == 2
    birch, walnut = orders
    assert birch["sheets_to_order"] == walnut["sheets_to_order"] == 1
    assert birch["tags"] == ["bench-1", "bench-2"]
    assert "Sound cores; no MDF." in birch["stock_note"]
    assert birch["also_in_placeables"] and "rough_board_feet" not in birch
    flat = _flat_rows(orders)
    assert flat[0]["sheets_to_order"] == 1
    assert flat[0]["sheet_size"] == '48" x 96"'
    assert flat[0]["pieces"] == flat[0]["finished_size"] == ""
