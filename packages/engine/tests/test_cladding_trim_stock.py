"""Installed trim overlaps and purchased stock are separate quantities."""

import pytest

from typehaus.resolve.cladding_trim.members import split_stock_run


def test_corner_uses_mixed_stock_and_three_inch_lap():
    pieces = split_stock_run(22 * 12 + 4.4, (10 * 12 + 2, 20 * 12 + 3), 3)
    assert [piece[2] for piece in pieces] == [243, 122]
    assert pieces[0][1] - pieces[1][0] == 3
    assert pieces[-1][1] == pytest.approx(268.4)
    assert all(end - start <= stock for start, end, stock in pieces)


def test_short_run_chooses_short_stock():
    assert split_stock_run(50, (122, 243), 2) == ((0.0, 50, 122),)


@pytest.mark.parametrize("run, lengths, lap", [(0, (10,), 1), (10, (), 1), (10, (1,), 1)])
def test_invalid_run(run, lengths, lap):
    with pytest.raises(ValueError):
        split_stock_run(run, lengths, lap)
