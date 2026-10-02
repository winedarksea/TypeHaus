"""The open lower configuration must have actual shelf bays, without hidden fronts."""

import pytest

from typehaus.model.placeable_symbols import model_parts

INCH = 0.0254


@pytest.mark.parametrize("symbol,front_bottoms", [
    ("sektion-tall-open-lower", (34.5625, 44.5625, 74.5625)),
    ("sektion-tall-drawers", (4.5625, 19.5625, 34.5625, 44.5625, 74.5625)),
])
def test_voxtorp_fronts_only_occupy_the_selected_modules(symbol, front_bottoms):
    parts = model_parts(symbol, 24 * INCH, 24.875 * INCH, 94.5 * INCH)
    fronts = [part for part in parts if part["color"] == "porcelain"]
    bottoms = sorted((part["center"][2] - part["size"][2] / 2) / INCH for part in fronts)
    assert bottoms == pytest.approx(front_bottoms)
    if symbol == "sektion-tall-open-lower":
        # Test the usable openings at their centres, rather than the builder's part count.
        for height_inches in (12, 27):
            assert not any(
                abs(part["center"][0]) < part["size"][0] / 2
                and abs(part["center"][1]) < part["size"][1] / 2
                and abs(height_inches * INCH - part["center"][2]) < part["size"][2] / 2
                for part in parts
            )

