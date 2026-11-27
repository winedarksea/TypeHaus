"""resolve/compass.py: the one plan→compass path (decision #153), and its lint."""

from __future__ import annotations

import math
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.quantities import deg
from typehaus.resolve import compass

_SRC = Path(__file__).resolve().parents[1] / "src" / "typehaus"
# The only modules that may read ``site.true_north`` itself.
_TRUE_NORTH_READERS = {
    "resolve/compass.py", "model/project.py", "emit/ifc/site.py", "emit/ifc/lowlevel.py",
    "server/model_json_document.py",
}


def _site(theta: float, lon: float = -93.0, lat: float = 45.0) -> SimpleNamespace:
    return SimpleNamespace(true_north=deg(theta), crs="EPSG:26915", lon=lon, lat=lat)


@pytest.mark.parametrize(("theta", "plan_north", "plan_east"), [
    (0, "N", "E"), (37, "N", "E"), (90, "W", "N"), (-30, "N", "E"), (-60, "E", "S"),
])
def test_facade_names_follow_theta(theta: float, plan_north: str, plan_east: str) -> None:
    site = _site(theta)
    assert compass.facade_name((0.0, 1.0), site) == plan_north
    assert compass.facade_name((1.0, 0.0), site) == plan_east


@pytest.mark.parametrize("theta", [0, 37, 90, -30])
def test_true_bearing_is_plan_bearing_less_theta(theta: float) -> None:
    site = _site(theta)
    for plan_deg in (0, 45, 90, 200, 359):
        b = math.radians(plan_deg)
        got = math.degrees(compass.true_bearing(math.sin(b), math.cos(b), site))
        assert got == pytest.approx((plan_deg - theta) % 360, abs=1e-9)
    north = compass.plan_vector_for_true_bearing(0.0, site)
    assert compass.true_bearing(*north, site) == pytest.approx(0.0, abs=1e-9)


def test_bearing_text() -> None:
    assert compass.quadrant_bearing_text(math.radians(45)) == "N 45°00' E"
    assert compass.quadrant_bearing_text(math.radians(180 + 12.5)) == "S 12°30' W"
    assert compass.facade_bearing_text((0.0, 1.0), _site(0)) is None
    assert compass.facade_bearing_text((0.0, 1.0), _site(37)) == "faces N 37° W"


def test_exact_tie_goes_clockwise() -> None:
    assert compass.cardinal(math.radians(45)) == "E"
    assert compass.cardinal(math.radians(44.9)) == "N"
    assert compass.cardinal(math.radians(315)) == "N"
    assert compass.cardinal(math.radians(22.5), points=8) == "NE"


def test_grid_plan_round_trip() -> None:
    site = _site(37, lon=-91.0)  # 2° east of the UTM 15 central meridian
    x, y = compass.grid_to_plan(*compass.plan_to_grid(12.0, -34.0, site), site)
    assert (x, y) == pytest.approx((12.0, -34.0), abs=1e-6)
    # East of the central meridian grid north lies east of true north.
    assert math.degrees(compass.grid_origin(site)[2]) < 0.0
    assert compass.lonlat_to_plan(-91.0, 45.0, site) == pytest.approx((0.0, 0.0), abs=1e-6)


def test_ifc_x_axis_at_ninety() -> None:
    # θ = 90: true north is plan +x, so project east points (grid) north on the meridian.
    assert compass.project_east_grid_axis(_site(90)) == pytest.approx((0.0, 1.0), abs=1e-6)
    assert compass.project_east_grid_axis(_site(0)) == pytest.approx((1.0, 0.0), abs=1e-6)


def test_out_of_domain_site_is_best_effort() -> None:
    site = _site(0, lon=0.0, lat=0.0)
    assert compass.grid_origin(site) is None
    assert compass.grid_rotation_rad(site) == 0.0


def test_lint_compass_is_the_only_true_north_reader() -> None:
    reads = re.compile(r"(?<!Site)\.true_north\b")
    binning = re.compile(r"//\s*\(?\s*math\.pi\s*/\s*2\s*\)?\s*\)?\s*%\s*4")
    offenders = []
    for path in _SRC.rglob("*.py"):
        rel = path.relative_to(_SRC).as_posix()
        text = path.read_text()
        if rel not in _TRUE_NORTH_READERS and reads.search(text):
            offenders.append(f"{rel}: reads .true_north")
        if rel != "resolve/compass.py" and binning.search(text):
            offenders.append(f"{rel}: bins a bearing by hand (use compass.cardinal)")
    assert not offenders, "\n".join(offenders)
