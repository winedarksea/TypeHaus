"""A joist field on tilted bearings: joist ends off the bearings, the deck as their plane."""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.resolve.floor_tilt import JoistLift, twisted

IN = inch(1).meters


def _rise(per_m: float):
    """A beam rising ``per_m`` per metre of +y from y = 0 (its start node)."""
    return lambda _x, y: per_m * y


def test_level_joists_between_two_equal_tilts_and_a_plane_through_them() -> None:
    lift = JoistLift(along_x=True, lines=((0.0, _rise(0.02)), (5.0, _rise(0.02))))
    # Both ends of a joist on line y = 2 sit 4 cm up: level, whatever the station.
    assert lift.at(0.0, 2.0) == pytest.approx(0.04)
    assert lift.at(5.0, 2.0) == pytest.approx(0.04)
    assert lift.at(-0.3, 2.0) == pytest.approx(0.04)  # a cantilever tip
    plane, miss = lift.plane(0.0, 4.0)
    assert plane.lift(2.5, 3.0) == pytest.approx(0.06)
    assert not twisted(miss)


def test_a_joist_rakes_between_a_wall_and_a_tilted_beam() -> None:
    lift = JoistLift(along_x=True, lines=((0.0, None), (4.0, _rise(0.05))))
    assert lift.at(0.0, 2.0) == pytest.approx(0.0)
    assert lift.at(4.0, 2.0) == pytest.approx(0.10)
    assert lift.at(2.0, 2.0) == pytest.approx(0.05)  # straight between its bearings
    # The field twists (the wall end is level, the beam end is not), and says so.
    _plane, miss = lift.plane(0.0, 4.0)
    assert twisted(miss)


def test_catlin_balcony_joists_sit_on_their_beams_and_the_deck_follows(catlin_model_ro) -> None:
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-DECK")
    assert floor.deck_plane is not None
    ys = [p[1] for p in floor.deck_outline]
    x = floor.deck_outline[0][0]
    low, high = floor.deck_top_range()
    assert floor.deck_top_at(x, min(ys)) == pytest.approx(low)
    assert floor.deck_top_at(x, max(ys)) == pytest.approx(high)
    # 1/4" per foot over the 116" plank (notes/balcony_differential_movement.md §2).
    assert (high - low) / IN == pytest.approx(116 / 48, abs=1e-3)
    # The storey datum is the beams' START (south node) — the plank's south edge.
    assert low == pytest.approx(floor.deck_z1_m, abs=1e-9)
    beam = next(s for s in catlin_model_ro.solids if s.tag == "BM-SG-BLW")
    (x0, y0, z0), (_x1, y1, z1) = beam.sweep.path
    depth = beam.z1_m - beam.z0_m - abs(z1 - z0)
    for joist in (m for m in floor.members if m.category == "joist"):
        y = joist.p0[1]
        beam_top = z0 + depth / 2.0 + (z1 - z0) * (y - y0) / (y1 - y0)
        assert joist.z0_end_m is None  # level E-W: both beams rise alike
        assert joist.z0_m == pytest.approx(beam_top, abs=1e-6), joist.child_key
