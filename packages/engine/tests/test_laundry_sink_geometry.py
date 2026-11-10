"""Utility tub must expose its bowl through the cabinet and rim."""

import pytest

from typehaus.library.placeables.fixtures import LAUNDRY_SINK
from typehaus.model.placeable_symbols import model_parts


def test_utility_basin_is_visible_from_above():
    width, depth = (dimension.meters for dimension in LAUNDRY_SINK.footprint)
    height = LAUNDRY_SINK.height.meters
    parts = model_parts(LAUNDRY_SINK.plan_symbol, width, depth, height)
    rim = 34 * 0.0254
    # Probe the centre and corners of the usable bowl. A full countertop or a solid
    # cabinet masks the bottom even when a hollow bowl has been added inside it.
    for x in (-width * 0.35, 0, width * 0.35):
        for y in (-depth * 0.30, -depth * 0.05, depth * 0.20):
            surfaces = [part for part in parts
                        if abs(x - part["center"][0]) < part["size"][0] / 2
                        and abs(y - part["center"][1]) < part["size"][1] / 2
                        and part["center"][2] < rim]
            visible_surface = max(surfaces, key=lambda p: p["center"][2] + p["size"][2] / 2)
            assert visible_surface["color"] in {"appliance-steel", "metal"}
            top = visible_surface["center"][2] + visible_surface["size"][2] / 2
            assert rim - top == pytest.approx(9 * 0.0254, abs=0.006)
    steel = [part for part in parts if part["color"] == "appliance-steel"]
    assert max(p["center"][2] + p["size"][2] / 2 for p in steel) == pytest.approx(rim)


def test_utility_faucet_reaches_over_the_open_bowl():
    width, depth = (dimension.meters for dimension in LAUNDRY_SINK.footprint)
    height = LAUNDRY_SINK.height.meters
    parts = model_parts(LAUNDRY_SINK.plan_symbol, width, depth, height)
    faucet = [part for part in parts
              if part["color"] == "metal" and part["center"][2] > 34 * 0.0254]
    assert all("mesh" in part for part in faucet)
    faucet_top = max(p["center"][2] + p["size"][2] / 2 for p in faucet)
    assert faucet_top == pytest.approx(height, abs=0.001)
    # A downturned outlet must project into the bowl, rather than remain a rear peg.
    assert any(part["center"][1] < depth * 0.10 and part["size"][2] > part["size"][1]
               for part in faucet)
