"""Finished floor area against houses/catlin/notes/finished_floor_area.md (hand-worked)."""

from __future__ import annotations

import pytest

from typehaus.resolve.conditioned_area import SF_PER_M2
from typehaus.resolve.finished_area import finished_floor_area


def test_catlin_finished_area_matches_the_hand_note(catlin_model_ro) -> None:
    """Attic 273.08 sf (§3), house 4,021.1 = 2,725.1 above + 1,296.0 below (§4)."""
    finished = finished_floor_area(catlin_model_ro)
    attic = next(row for row in finished.storeys if row.storey == "attic")
    assert attic.area_ft2 == pytest.approx(273.08, abs=0.5)
    assert finished.area_m2 * SF_PER_M2 == pytest.approx(4021.1, rel=0.01)
    assert finished.below_grade_m2 * SF_PER_M2 == pytest.approx(1296.0, abs=1.0)
    assert set(finished.excluded_rooms) == {"RM-A-EAST-UNFIN", "RM-A-POCKET"}
