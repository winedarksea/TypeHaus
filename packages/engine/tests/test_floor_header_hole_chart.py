"""`notes/framing_bore_limits.md` §12: Boise's VERSA-LAM hole chart on a floor header."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from shapely.geometry import LineString

from typehaus import PublishedHole, inch
from typehaus.checks.mep.floor_members import _chart_station, _opening_tag
from typehaus.checks.mep.framing_envelope import Leg
from typehaus.resolve.mep_bores import header_bore

IN = 0.0254
PROFILE = "2-1.75x11.875 LVL"
CHART = PublishedHole(
    source="Boise MTP-E7000 Rev. 07/26 p.26", table="9 1/4\" to < 18\": 2\"", member=PROFILE,
    max_diameter=inch(2), zone_fraction=1 / 3, depth_fraction=1 / 3, min_spacing_diameters=2.0)
#: FO-S-ERV-CHASE's header: x = 34.8", y 400.0"..425.4", z 108.125"..120.0".
HEADER = SimpleNamespace(p0=(34.8 * IN, 400.0 * IN), p1=(34.8 * IN, 425.4 * IN),
                         z0_m=108.125 * IN, z1_m=120.0 * IN)


def _leg(y_in: float, z_in: float) -> Leg:
    """A 1.9" pipe level west across the header at y."""
    a, b = (43.875 * IN, y_in * IN), (30.3 * IN, y_in * IN)
    return Leg("pipe", "T", 0, a, b, z_in * IN, z_in * IN, 0.95 * IN,
               LineString([a, b]).buffer(0.95 * IN), 0.95 * IN)


def _verdict(y_in: float, z_in: float):
    station = _chart_station(HEADER, _leg(y_in, z_in))
    return header_bore(PROFILE, 1.9, chart=CHART, **station)


def test_a_hole_in_the_middle_third_of_span_and_depth_passes() -> None:
    assert _verdict(412.7, 114.0).ok is True


def test_the_end_third_fails() -> None:
    """y = 406.17": 6.17" from the south end against 25.4/3 = 8.47"."""
    assert _verdict(406.17, 114.0).ok is False


def test_the_top_third_fails_at_the_trap_arm_s_height() -> None:
    """z = 115.44" (weir 117.0 less 1.5625"): top edge 3.61" under the top against 3.958"."""
    assert _verdict(412.7, 115.4375).ok is False
    assert _verdict(412.7, 115.09).ok is True


def test_station_numbers_are_the_notes() -> None:
    station = _chart_station(HEADER, _leg(410.0, 115.66))
    assert station["span_in"] == pytest.approx(25.4)
    assert station["from_bearing_in"] == pytest.approx(10.0)
    assert station["edge_clear_in"] == pytest.approx(3.39, abs=0.01)
    assert math.isclose(120.0 - 115.66 - 0.95, 3.39, abs_tol=1e-9)


def test_the_opening_is_named_by_the_member_key() -> None:
    assert _opening_tag(SimpleNamespace(child_key="header-FO-S-ERV-CHASE-1")) == "FO-S-ERV-CHASE"
    assert _opening_tag(SimpleNamespace(child_key="trimmer-FO-S-ERV-CHASE-0-0")) == ""
