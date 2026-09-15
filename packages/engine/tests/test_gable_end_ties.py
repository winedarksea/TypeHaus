"""Where a gable-end tie actually is — the elevation dimension nothing graded.

``joints/gable.py`` located these ties in plan correctly from the day it was written, and
put every one of them at one scalar elevation for the whole run. On a flat-plate (trussed)
gable that is right. On a RAKED one it is not: a ``ToRoof`` wall keeps its full bounding
prism in ``z1_m`` on purpose (``resolve/model.py`` says so, for consumers that only
understand prisms), and the raked top lives in ``top_z0_m``/``top_z1_m`` instead — so the
fallback put sixteen of catlin's thirty-six H10A markers in the air over the roof, the worst
by 9'-0".

Nothing caught it because nothing tested it. ``test_uplift_takeoff`` and
``test_uplift_load_path`` grade coverage and counts; the only other test touching
``connector_markers`` is a runtime budget. ``Joint.z_m`` in this role was untested outright.

These are written against the RULE — every tie sits on its own wall's plate, wherever that
wall's plate is at that station — and not against catlin's numbers, so they keep holding
when the house moves. The two shapes are asserted separately because the whole point is
that one rule answers both: the attic's raked gables and the garage's flat trussed ones.
"""

from __future__ import annotations

import pytest

from typehaus.hardware.catalog import ROLE_GABLE_END_TIE
from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.joints import derived_joints
from typehaus.joints.gable import gable_end_ties
from typehaus.resolve.geometry_walls import is_raked, wall_top_at

_TOL_M = 1e-6


@pytest.fixture(scope="module")
def ends(catlin_model_ro):
    found = gable_end_ties(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG.gable_end_ties)
    assert found, "catlin has gable roofs over gable-end walls; this rule must find them"
    return found


def test_every_station_carries_its_own_plate_elevation(catlin_model_ro, ends) -> None:
    """The rule itself: a tie lands on the plate where it stands, not where the wall tops out."""
    for end in ends:
        assert len(end.station_z_m) == len(end.stations_m), end.wall_tag
        wall = catlin_model_ro.wall(end.wall_tag)
        (x0, y0), (x1, y1) = wall.axis
        run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        for station_m, z_m in zip(end.stations_m, end.station_z_m, strict=True):
            t = station_m / run
            point = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            assert abs(z_m - wall_top_at(wall, *point)) < _TOL_M, (end.wall_tag, station_m)


def test_a_raked_gable_climbs_and_a_flat_one_does_not(catlin_model_ro, ends) -> None:
    """Both shapes, one rule — and the raked case must actually vary, or the test proves nothing."""
    raked = [e for e in ends if is_raked(catlin_model_ro.wall(e.wall_tag))]
    flat = [e for e in ends if not is_raked(catlin_model_ro.wall(e.wall_tag))]
    assert raked and flat, "catlin carries both: raked attic gables and trussed garage gables"

    for end in raked:
        # A rake with more than one tie must show a spread, or the scalar bug is back and
        # simply agreeing with itself.
        if len(end.station_z_m) > 1:
            assert max(end.station_z_m) - min(end.station_z_m) > 0.05, end.wall_tag

    for end in flat:
        # Asserted, not assumed (the plan's own instruction): the flat-plate case must fall
        # out of the same call unchanged, which is what keeps the garage from moving.
        assert set(end.station_z_m) == {end.z_m}, end.wall_tag


def test_no_derived_gable_tie_floats_above_its_wall(catlin_model_ro) -> None:
    """The defect as a reader would see it: a marker drawn over the roof instead of on it."""
    joints = [j for j in derived_joints(catlin_model_ro, DEFAULT_HARDWARE_TAKEOFF_CONFIG)
              if j.role == ROLE_GABLE_END_TIE]
    assert joints
    for joint in joints:
        # ``members`` is (wall_tag, roof_tag) for this role — the wall is the anchor.
        wall = catlin_model_ro.wall(joint.members[0])
        assert wall is not None, joint.members
        assert abs(joint.z_m - wall_top_at(wall, *joint.point)) < _TOL_M, joint.key
