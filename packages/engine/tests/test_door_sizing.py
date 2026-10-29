"""``resolve/door_sizing`` — one equation derives an RO and checks a leaf fits one."""

from __future__ import annotations

import pytest

from typehaus import DoorCatalogDimensions, DoorType, OpeningSize
from typehaus.model.enums import DoorOperation
from typehaus.quantities import ft, inch
from typehaus.resolve.door_sizing import door_sizing

_IN = 0.0254


class _Door:
    held_rough_opening = None
    maximum_opening_degrees = 90.0
    exterior_installation = None


class _Kit:
    model = "KIT"
    rough_opening_in_by_length_in = {36: 74.5}
    rough_opening_head_over_leaf_in = 3.25


# (operation, nominal width in, RO width in, RO height in, swings) with a = 1", no finish.
_ROWS = [
    (DoorOperation.SWING, 32, 34.236, 81.512, True),
    (DoorOperation.DOUBLE_SWING, 60, 62.354, 81.512, True),
    (DoorOperation.SLIDE, 48, 50.236, 81.512, False),
    (DoorOperation.BIFOLD, 56, 58.236, 81.512, False),
    (DoorOperation.POCKET, 36, 74.5, 83.25, False),
    (DoorOperation.OVERHEAD, 192, 192, 84, False),
]


@pytest.mark.parametrize(("operation", "width", "rough_w", "rough_h", "swings"), _ROWS)
def test_every_operation_derives_its_rough_opening(operation, width, rough_w, rough_h, swings):
    height = 84 if operation == DoorOperation.OVERHEAD else 80
    door_type = DoorType(tag="T", width=inch(width), height=inch(height), operation=operation)
    kit = _Kit() if operation == DoorOperation.POCKET else None
    sizing = door_sizing(_Door(), door_type, None, kit, 0.0)
    assert sizing.rough_w_m / _IN == pytest.approx(rough_w, abs=0.01)
    assert sizing.rough_h_m / _IN == pytest.approx(rough_h, abs=0.01)
    assert sizing.leaf_w_m == pytest.approx(door_type.width.meters)
    assert (sizing.clear_w_m is not None) == swings
    assert sizing.fits and not sizing.held
    if operation == DoorOperation.POCKET:
        assert sizing.passage_w_m + sizing.pocket_run_m == pytest.approx(74.5 * _IN)


def test_published_rough_opening_wins_and_its_unit_must_fit():
    unit = DoorCatalogDimensions(unit_width=inch(37.625), unit_height=inch(82),
                                 clear_width_90=inch(33.3125), clear_height=inch(79.25),
                                 source_url="u", source_drawing="d")
    door_type = DoorType(tag="T", width=ft(3), height=ft(6, 8), catalog_dimensions=unit,
                         rough_opening=OpeningSize(width=inch(38.375), height=inch(82.875)))
    sizing = door_sizing(_Door(), door_type, None, None, 0.0)
    assert sizing.rough_w_m / _IN == pytest.approx(38.375)
    assert sizing.basis_of("rough") == "published RO" and sizing.fits
    assert sizing.clear_w_m / _IN == pytest.approx(33.3125)
    # A published RO the unit cannot fit is a load-time error (decision #96).
    with pytest.raises(ValueError, match="does not fit"):
        DoorType(tag="T", width=ft(3), height=ft(6, 8), catalog_dimensions=unit,
                 rough_opening=OpeningSize(width=inch(37.75), height=inch(82.875)))


def test_a_held_opening_keeps_its_void_and_infers_the_leaf():
    door = _Door()
    door.held_rough_opening = OpeningSize(width=ft(2, 8), height=ft(6, 8))
    door_type = DoorType(tag="T", width=ft(2, 8), height=ft(6, 8))
    sizing = door_sizing(door, door_type, None, None, 0.0)
    assert sizing.held and sizing.rough_w_m == pytest.approx(ft(2, 8).meters)
    assert sizing.leaf_w_m / _IN == pytest.approx(32 - 2.236, abs=0.01)
    assert sizing.required_w_m / _IN == pytest.approx(34.236, abs=0.01)
    # The estimate: 2-11/16" under the leaf, both leaves of a pair, active leaf at a post.
    pair = DoorType(tag="P", width=ft(5), height=ft(6, 8), operation="double_swing")
    assert door_sizing(_Door(), pair, None, None, 0.0).clear_w_m / _IN == pytest.approx(54.625)
    post = pair.model_copy(update={"center_post": True})
    assert door_sizing(_Door(), post, None, None, 0.0).clear_w_m / _IN == pytest.approx(27.3125)
