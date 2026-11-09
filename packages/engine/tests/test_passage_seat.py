"""A leafless through hole with a sill is a passage only if it lands on its rooms' floors."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve import passage_seat
from typehaus.resolve.model import ResolvedOpening


def _opening(sill_in: float) -> ResolvedOpening:
    return ResolvedOpening(uid="u", tag="O", host_wall="W", type_ref=None, width_m=0.9,
                           height_m=2.0, sill_m=sill_in * M_PER_IN, center_along_m=1.0,
                           kind="rough_opening", is_door=False)


@pytest.mark.parametrize(("sill_in", "floors_in", "expected"), [
    (0.75, (0.75, 0.75), True),   # on the finished floor
    (0.75, (0.0, 0.75), True),    # a floor change: the higher floor counts
    (1.0, (0.75, 0.75), True),    # within the threshold
    (6.0, (0.75, 0.75), False),   # a curb
    (36.0, (0.75, 0.75), False),  # a pass-through
    (0.75, (), False),            # no room either side: nothing to read it against
])
def test_a_seated_passage_is_read_against_its_floors(monkeypatch, sill_in, floors_in, expected):
    wall = SimpleNamespace(tag="W", base_ref_z_m=0.0)
    model = SimpleNamespace(walls=[wall], openings=[_opening(sill_in)])
    monkeypatch.setattr(passage_seat, "_side_floors",
                        lambda *_: [z * M_PER_IN for z in floors_in])
    passage_seat.mark_seated_passages(model)
    assert model.openings[0].is_passage is expected


def test_a_zero_sill_stays_a_passage_unmarked():
    assert _opening(0.0).is_passage
