"""The bonded bowl remains visible through the deck and above the floating cabinet."""

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model.placeable_symbols import model_parts


def test_bonded_bowl_has_an_open_deck_and_curved_five_inch_recess():
    inch = 0.0254
    parts = model_parts("solid-surface-vanity", 48 * inch, 18 * inch, 41.5 * inch)
    deck = 41.5 * inch - 0.14
    basin_y = -0.5 * inch
    shell = next(part for part in parts if part["shape"] == "mesh")
    vertices = shell["mesh"]["positions"]
    assert max(p[2] for p in vertices) == pytest.approx(deck)
    assert min(p[2] for p in vertices) == pytest.approx(deck - 5 * inch, abs=0.0002)
    assert len({round(p[2], 5) for p in vertices}) > 10
    assert {part["color"] for part in parts} == {"porcelain", "appliance-white", "metal"}
    for part in parts:
        if part["shape"] != "box":
            continue
        (x, y, z), (w, d, h) = part["center"], part["size"]
        if z + h / 2 >= deck - 1e-9 and z - h / 2 < deck:
            outline = Polygon(((x-w/2, y-d/2), (x+w/2, y-d/2),
                               (x+w/2, y+d/2), (x-w/2, y+d/2)))
            assert not outline.contains(Point(0, basin_y))
    cabinet = [part for part in parts if part["color"] == "appliance-white"]
    assert min(p["center"][2] - p["size"][2] / 2 for p in cabinet) == pytest.approx(
        5.5 * inch, abs=0.0002)
