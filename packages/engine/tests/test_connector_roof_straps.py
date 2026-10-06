"""Roof-mounted straps retain stock dimensions on either slope and along either ridge."""

import math

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.roof_straps import roof_strap_mesh
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.roof_geometry import roof_height_at


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize(("form", "station"), [
    ("gable", 2.0), ("gable", 4.0), ("gable", 6.0), ("shed", 2.0),
])
def test_roof_strap_dimensions_and_mounting_plane(direction, form, station):
    roof = ResolvedRoof(
        uid="roof", tag="RF", storey="main", form=form,
        footprint=[(0, 0), (8, 0), (8, 8), (0, 8)],
        eave_z_m=3, ridge_z_m=5, ridge_direction=direction,
        assembly="roof", surface_area_m2=64)
    point = (3.0, station) if direction == "x" else (station, 3.0)
    mesh = roof_strap_mesh(roof, point, "LSTA24")
    developed_width = 0.0
    for start in range(0, len(mesh.positions), 8):
        a, b, c, d = mesh.positions[start:start + 4]
        assert all(p[2] == pytest.approx(roof_height_at(roof, p[:2])) for p in (a, b, c, d))
        assert math.dist(b, c) == pytest.approx(24 * M_PER_IN)
        developed_width += math.dist(a, b)
        # Both long edges stay level, even when the narrow width straddles a ridge.
        assert a[2] == pytest.approx(d[2])
        assert b[2] == pytest.approx(c[2])
        thickness = math.dist(a, mesh.positions[start + 4])
        assert thickness == pytest.approx(0.0359 * M_PER_IN)
    assert developed_width == pytest.approx(1.25 * M_PER_IN)
    assert len(mesh.positions) == (16 if form == "gable" and station == 4.0 else 8)
