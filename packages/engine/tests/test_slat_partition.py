"""The slat screen lays whole pitches, centred, so two abutting screens keep one rhythm."""

import pytest

from typehaus.model.placeable_symbols import model_parts, plan_symbol_strokes
from typehaus.model.placeable_symbols._slat_partition import SLAT_PITCH_M, slat_count
from typehaus.quantities import inch


def _slats(width_in: float, height_in: float = 100.0):
    parts = model_parts("slat-partition", inch(width_in).meters, inch(2.5).meters,
                        inch(height_in).meters)
    return sorted((p for p in parts if p["size"][0] < inch(2).meters),
                  key=lambda p: p["center"][0])


@pytest.mark.parametrize(("width_in", "count"), [(16.5, 6), (44.0, 16), (2.75, 1)])
def test_slat_count_is_whole_pitches(width_in, count):
    assert slat_count(inch(width_in).meters) == count
    assert len(_slats(width_in)) == count


def test_slats_are_on_one_pitch_with_half_gaps_at_both_ends():
    width = inch(16.5).meters
    slats = _slats(16.5)
    xs = [p["center"][0] for p in slats]
    assert all(b - a == pytest.approx(SLAT_PITCH_M) for a, b in zip(xs, xs[1:]))
    assert xs[0] == pytest.approx(-width / 2 + SLAT_PITCH_M / 2)
    assert xs[-1] == pytest.approx(width / 2 - SLAT_PITCH_M / 2)
    assert all(p["color"] == "wood" for p in slats)


def test_cleats_run_the_full_width_at_floor_and_ceiling():
    height = inch(100).meters
    parts = model_parts("slat-partition", inch(16.5).meters, inch(2.5).meters, height)
    cleats = [p for p in parts if p["size"][0] == pytest.approx(inch(16.5).meters)]
    assert len(cleats) == 2
    tops = sorted(p["center"][2] + p["size"][2] / 2 for p in parts)
    assert tops[-1] == pytest.approx(height)
    assert len(plan_symbol_strokes("slat-partition", inch(16.5).meters,
                                   inch(2.5).meters)) == 7
