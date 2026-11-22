"""Head/sill cripples step aside for a wall register's box (``framing/terminal_bays.py``)."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.terminal_bays import CLEARANCE_M, clear_of_spans

T = 1.5 * M_PER_IN


def _in(*values: float) -> list[float]:
    return [v * M_PER_IN for v in values]


def test_cripple_moves_to_the_nearer_side_of_the_box():
    # D-S-SUITE: RO 152.875-187.125", cripples at 168.875/184.875, a 12" box at 164-176.
    low, high, box = *_in(152.875, 187.125), tuple(_in(164, 176))
    stations = list(enumerate(_in(168.875, 184.875), start=1))
    moved = dict(clear_of_spans(stations, (box,), T, low, high))
    assert moved[1] == pytest.approx(box[0] - T / 2 - CLEARANCE_M)
    assert moved[2] == pytest.approx(184.875 * M_PER_IN), "a clear cripple stays"


def test_no_room_keeps_the_cripple_and_a_landing_on_a_neighbour_drops():
    low, high = _in(0, 20)
    # The box fills the opening: neither side clears the jacks, so the cripple stays put.
    assert clear_of_spans([(0, 10 * M_PER_IN)], (tuple(_in(1, 19)),), T, low, high) \
        == [(0, 10 * M_PER_IN)]
    # Stepping south lands on the cripple already there: one member, not two.
    near = _in(3.5, 6)
    kept = clear_of_spans(list(enumerate(near)), (tuple(_in(5.5, 7)),), T, *_in(0, 40))
    assert len(kept) == 1
