"""Product proportions and mounting geometry in the shared indoor-plant symbols."""

from __future__ import annotations

import pytest

from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import inch


def _bounds(part, axis):
    return (part["center"][axis] - part["size"][axis] / 2,
            part["center"][axis] + part["size"][axis] / 2)


def test_stand_draws_three_trays_at_the_pots_support_heights():
    parts = model_parts("wall-plant-stand", inch(5.5).meters, inch(5.5).meters,
                        inch(30.75).meters)
    trays = [part for part in parts if part["shape"] == "prism"]
    assert len(trays) == 3
    assert [_bounds(part, 2)[1] for part in trays] == pytest.approx(
        [inch(height).meters for height in (2, 14.25, 27)])
    assert all(part["color"] == "metal-black" for part in parts)
    assert all(_bounds(part, 1)[1] <= inch(2.75).meters for part in parts)


def test_small_plant_has_a_three_and_a_half_inch_open_pot_and_leaf_meshes():
    parts = model_parts("small-potted-plant", inch(5.5).meters, inch(5.5).meters,
                        inch(8).meters)
    pot = parts[0]
    assert pot["shape"] == "mesh"
    assert pot["size"][:2] == pytest.approx((inch(3.5).meters,) * 2)
    assert _bounds(pot, 2) == pytest.approx((0, inch(3.5).meters))
    leaves = [part for part in parts if part["color"] == "foliage"]
    assert len(leaves) >= 12
    assert all(part["shape"] == "mesh" for part in leaves)


def test_hanging_basket_has_three_actual_cords_and_trailing_foliage():
    parts = model_parts("hanging-vine-planter", inch(16).meters, inch(16).meters,
                        inch(46).meters)
    pot = parts[0]
    assert pot["size"][:2] == pytest.approx((inch(12).meters,) * 2)
    assert _bounds(pot, 2) == pytest.approx((inch(16).meters, inch(24).meters))
    cords = [part for part in parts
             if part["color"] == "metal-black" and part["shape"] == "mesh"]
    assert len(cords) == 3
    assert all(_bounds(part, 2)[1] > inch(45).meters for part in cords)
    lowest_leaf = min(_bounds(part, 2)[0] for part in parts if part["color"] == "foliage")
    assert inch(24).meters - lowest_leaf == pytest.approx(inch(24).meters, abs=inch(1).meters)
    assert max(_bounds(part, 2)[1] for part in parts) == pytest.approx(inch(46).meters)
