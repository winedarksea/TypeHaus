"""A rectangular riser on a carried frame (``SolidSweep.vertical_up``) keeps its section."""

from __future__ import annotations

from typehaus.resolve.model import SolidSweep
from typehaus.resolve.sweep import carried_up, rect_profile, sweep_legs, sweep_plan_silhouette

_PROFILE = rect_profile(0.254, 0.1524)  # 10" wide (u) x 6" deep (v)
_RISER = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.5), (2.5, 0.0, 1.5))


def _span(ring, axis: int) -> float:
    return max(p[axis] for p in ring) - min(p[axis] for p in ring)


def test_a_carried_riser_keeps_the_level_legs_width_across_the_run() -> None:
    up = carried_up(_RISER)
    assert up == (-1.0, 0.0, 0.0)
    legs = sweep_legs(SolidSweep(path=_RISER, profile=_PROFILE, vertical_up=up))
    # Level legs run along X: 10" across in Y. The riser must stay 10" in Y, 6" in X.
    for leg in legs:
        assert abs(_span(leg[0], 1) - 0.254) < 1e-12
    assert abs(_span(legs[1][0], 0) - 0.1524) < 1e-12
    # Each ring point keeps its profile corner's side: u maps to +Y on every leg.
    for leg in legs:
        assert [p[1] > 0 for p in leg[0]] == [u > 0 for u, _v in _PROFILE]


def test_a_drop_carries_the_same_right_as_a_riser() -> None:
    hat = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (2.0, 0.0, 1.0),
           (2.0, 0.0, 0.0), (3.0, 0.0, 0.0))
    legs = sweep_legs(SolidSweep(path=hat, profile=_PROFILE, vertical_up=carried_up(hat)))
    for leg in legs:
        assert [p[1] > 0 for p in leg[0]] == [u > 0 for u, _v in _PROFILE]


def test_none_is_todays_frame_and_rolls_the_riser() -> None:
    plain = SolidSweep(path=_RISER, profile=_PROFILE)
    assert sweep_legs(plain) == sweep_legs(SolidSweep(path=_RISER, profile=_PROFILE,
                                                      vertical_up=None))
    assert abs(_span(sweep_legs(plain)[1][0], 0) - 0.254) < 1e-12  # the +Y fallback


def test_a_pure_vertical_run_silhouette_follows_the_carried_frame() -> None:
    drop = SolidSweep(path=((0.0, 0.0, 1.0), (0.0, 0.0, 0.0)), profile=_PROFILE,
                      vertical_up=(-1.0, 0.0, 0.0))
    ring = sweep_plan_silhouette(drop)
    assert abs(_span(ring, 1) - 0.254) < 1e-12 and abs(_span(ring, 0) - 0.1524) < 1e-12


def test_carried_up_needs_a_riser_and_a_level_leg() -> None:
    assert carried_up(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))) is None
    assert carried_up(((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))) is None
    assert carried_up(((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 2.0, 1.0))) == (0.0, -1.0, 0.0)
