"""``structural.hanger_seat_fit``'s bound, on the catalog rows it was written for (C3-E11)."""

from __future__ import annotations

import pytest

from typehaus.checks.structural.hanger_seat_fit import seat_fits
from typehaus.resolve.connector_geometry.hangers import hanger_dimensions


@pytest.mark.parametrize("part,width_in,fits", [
    ("HU28-2Z", 1.5, False),    # catlin's BM-BW-SCSILL before 2026-10-31: 1 5/8" of slop
    ("LUS28Z", 1.5, True),      # its fix
    ("HU28-2Z", 3.0, True),     # these three sit exactly on +1/8"
    ("LUS26-2Z", 3.0, True),
    ("LUS210-3Z", 4.5, True),
    ("LUS28Z", 3.0, False),     # a double member in a single seat
])
def test_the_seat_width_bound(part, width_in, fits) -> None:
    row = hanger_dimensions(part, member_width_in=width_in, member_depth_in=7.25)
    assert seat_fits(row.clear_width_in - width_in) is fits
