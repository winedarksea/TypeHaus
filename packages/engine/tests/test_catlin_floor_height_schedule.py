"""Doorway probes for Catlin's coordinated finished-floor schedule."""

from __future__ import annotations

from math import hypot

import pytest

from typehaus.resolve.walking_surface import surfaces_at

INCH_M = 0.0254
FLUSH_TOLERANCE_IN = 1 / 16  # Catlin design target, notes/floor_heights.md


@pytest.mark.parametrize(("opening", "first", "second", "difference_in"), [
    ("D-S-BED1", "RM-S-BED1", "RM-S-HALL", 0),
    ("D-S-BED2", "RM-S-BED2", "RM-S-HALL", 0),
    ("D-S-BED3", "RM-S-BED3", "RM-S-HALL", 0),
    ("D-S-SUITE", "RM-S-SUITE", "RM-S-HALL", 0),
    ("D-S-SUITEBATH", "RM-S-SUITE", "RM-S-SUITEBATH", 0),
    ("O-S-VANITY", "RM-S-HALL", "RM-S-VANITY", 0),
    ("D-S-BATH1", "RM-S-HALL", "RM-S-BATH1", 0),
    ("D-S-NCLOSET", "RM-S-HALL", "RM-S-NCLOSET", 0),
    ("D-S-STUDY2", "RM-S-HALL", "RM-S-STUDY2", 0),
    ("D-S-PLANT", "RM-S-STUDY2", "RM-S-PLANT", 0.63),
    ("D-M-MUD", "RM-M-LIVING", "RM-M-MUDROOM", 0),
    ("D-M-MECH", "RM-M-MUDROOM", "RM-M-MECH", 0),
    ("D-M-MUDC", "RM-M-MUD-CLOSET", "RM-M-MUDROOM", 0),
    ("D-M-BED2", "RM-M-LIVING", "RM-M-BED", 0.5138),
    ("D-M-BED", "RM-M-BED", "RM-M-CLOSET", 0),
    ("D-M-BATH2", "RM-M-BED", "RM-M-BATH2", 0),
])
def test_finished_planes_beside_each_door(
    catlin_model_ro, opening, first, second, difference_in,
):
    door = next(item for item in catlin_model_ro.openings if item.tag == opening)
    wall = next(item for item in catlin_model_ro.walls if item.tag == door.host_wall)
    start, end = wall.axis[0], wall.axis[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = hypot(dx, dy)
    middle = (start[0] + dx * door.center_along_m / length,
              start[1] + dy * door.center_along_m / length)
    found = {}
    # Cross the wall far enough to clear its finish face. Narrow closet doors can
    # require a deeper probe; retain the closest valid surface in each named room.
    for distance in (0.20, 0.35, 0.50, 0.80, 1.0):
        for sign in (-1, 1):
            point = (middle[0] - sign * dy / length * distance,
                     middle[1] + sign * dx / length * distance)
            for surface in surfaces_at(catlin_model_ro, point):
                if surface.room_tag in (first, second) and surface.surface_m is not None:
                    found.setdefault(surface.room_tag, surface.surface_m / INCH_M)
        if len(found) == 2:
            break
    assert set(found) == {first, second}, (opening, found)
    difference = abs(found[first] - found[second])
    assert difference == pytest.approx(difference_in, abs=0.002), (opening, found)
    if difference_in == 0:
        assert difference <= FLUSH_TOLERANCE_IN


def test_stair_heads_match_their_finished_floors(catlin_model_ro):
    stairs = {stair.tag: stair for stair in catlin_model_ro.stairs}
    assert stairs["ST-M2S"].base_elevation_m / INCH_M == pytest.approx(0.9862)
    assert stairs["ST-M2S"].arrival_elevation_m / INCH_M == pytest.approx(121.5)
    assert stairs["ST-M2S"].riser_height_m / INCH_M == pytest.approx(
        (121.5 - 0.9862) / 16)
    assert stairs["ST-S2A"].base_elevation_m / INCH_M == pytest.approx(121.5)
