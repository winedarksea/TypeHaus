"""The open corner shelf keeps its plan outline and fourteen shelf panels in agreement."""

from collections import Counter

import pytest
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from typehaus.model.placeable_symbols import model_parts, plan_symbol_strokes
from typehaus.quantities import inch


def test_corner_bookcase_has_seven_paired_tiers_and_an_open_front():
    width, depth, height = (inch(value).meters for value in (23.62, 23.62, 78.74))
    outline, *_ = plan_symbol_strokes("corner-bookcase", width, depth)
    parts = model_parts("corner-bookcase", width, depth, height)
    shelves = [part for part in parts if part["color"] == "wood-dark"]
    assert len(shelves) == 14
    levels = Counter(round(part["center"][2], 9) for part in shelves)
    assert len(levels) == 7
    assert set(levels.values()) == {2}
    assert max(part["center"][2] + part["size"][2] / 2
               for part in shelves) == pytest.approx(height)

    def footprint(part):
        x, y, _ = part["center"]
        w, d, _ = part["size"]
        return box(x - w / 2, y - d / 2, x + w / 2, y + d / 2)

    top_pair = shelves[-2:]
    assert footprint(top_pair[0]).intersection(footprint(top_pair[1])).area < 1e-12
    top_outline = unary_union([footprint(part) for part in top_pair])
    assert top_outline.symmetric_difference(Polygon(outline["points"])).area < 1e-12
    assert not top_outline.intersects(box(-width / 2, -depth / 2, 0, 0))
    assert all(part["color"] == "metal-black" for part in parts if part not in shelves)
    # The black members are posts, not a solid rear panel concealing the open shelves.
    assert all(part["size"][0] < inch(2).meters and part["size"][1] < inch(2).meters
               for part in parts if part not in shelves)
