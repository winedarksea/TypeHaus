"""Sheet layouts react to cut sizes and quantities, independent of door naming."""

import pytest

from typehaus.takeoff.door_trim_layout import TrimSheetStock, layout_trim_strips

STOCK = TrimSheetStock("test sheet", "finish", .75, 48, 96, .125)


def piece(name, width, length=80, thickness=.75):
    return dict(door="arbitrary-door", part=name, thickness_in=thickness,
                width_in=width, length_in=length)


def test_layout_charges_kerf_and_adds_stock_for_new_cuts():
    cuts = [piece("a", 24), piece("b", 23.875)]
    assert len(layout_trim_strips(cuts, STOCK)) == 2
    cuts = [piece("a", 24), piece("b", 23.75)]
    sheets = layout_trim_strips(cuts, STOCK)
    assert len(sheets) == 1
    assert sheets[0]["used_width_in"] == 48
    assert sheets[0]["pieces"][1]["rip_offset_in"] == 24.125
    assert sheets == layout_trim_strips(cuts[::-1], STOCK)
    assert len(layout_trim_strips(cuts + [piece("extra", 1)], STOCK)) == 2
    assert layout_trim_strips([], STOCK) == []


@pytest.mark.parametrize("cut", [piece("wide", 48), piece("long", 2, 97),
                                 piece("thick", 2, thickness=1), piece("invalid", -1)])
def test_unbuildable_cut_is_rejected(cut):
    with pytest.raises(ValueError):
        layout_trim_strips([cut], STOCK)
