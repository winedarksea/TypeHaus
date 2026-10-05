"""The chess table has a square 8 x 8 inlay and accessible piece storage below its top."""

from __future__ import annotations

from collections import Counter

import pytest

from typehaus.library.placeables import CHESS_TABLE_315
from typehaus.model.placeable_symbols import model_parts, plan_symbol_strokes
from typehaus.quantities import inch


def test_chessboard_tiles_match_between_plan_and_model() -> None:
    width, depth = (length.meters for length in CHESS_TABLE_315.footprint)
    height = CHESS_TABLE_315.height.meters
    _, *squares = plan_symbol_strokes("chess-table", width, depth)
    parts = model_parts("chess-table", width, depth, height)
    surface_parts = [part for part in parts
                     if part["center"][2] + part["size"][2] / 2 == pytest.approx(height)]
    border_parts, inlay_parts = surface_parts[:4], surface_parts[4:]
    assert len(squares) == len(inlay_parts) == 64
    assert Counter(square["fill"] for square in squares) == {"wood": 32, "wood-dark": 32}
    for index, (square, part) in enumerate(zip(squares, inlay_parts, strict=True)):
        xs, ys = zip(*square["points"], strict=True)
        assert part["center"][:2] == pytest.approx(
            ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
        assert part["size"][:2] == pytest.approx((max(xs) - min(xs), max(ys) - min(ys)))
        assert part["size"][0] == pytest.approx(part["size"][1])
        assert part["color"] == square["fill"]
        row, column = divmod(index, 8)
        assert square["fill"] == ("wood-dark" if (row + column) % 2 == 0 else "wood")
    assert sum(part["size"][0] * part["size"][1]
               for part in (*border_parts, *inlay_parts)) == pytest.approx(width * depth)


def test_chess_table_has_specified_top_four_legs_and_one_drawer() -> None:
    width, depth = (length.meters for length in CHESS_TABLE_315.footprint)
    height = CHESS_TABLE_315.height.meters
    assert (width, depth, height) == pytest.approx(
        tuple(inch(value).meters for value in (31.5, 27.75, 27.5)))
    parts = model_parts("chess-table", width, depth, height)
    tabletop = parts[0]
    tabletop_bottom = tabletop["center"][2] - tabletop["size"][2] / 2
    assert height - tabletop_bottom == pytest.approx(inch(2.25).meters)
    legs = [part for part in parts
            if part["center"][2] - part["size"][2] / 2 == pytest.approx(0)]
    assert len(legs) == 4
    assert all(part["center"][2] + part["size"][2] / 2 == pytest.approx(tabletop_bottom)
               for part in legs)
    drawer_parts = [part for part in parts
                    if 0 < part["center"][2] < tabletop_bottom
                    and part not in legs]
    assert len(drawer_parts) == 6  # bottom, four sides and a single pull
    pulls = [part for part in drawer_parts if part["color"] == "metal"]
    assert len(pulls) == 1
    assert pulls[0]["center"][1] < 0
    assert CHESS_TABLE_315.storage

