"""face_run_m and framing_side_span over a mitred and a butt-cut corner (synthetic)."""

from types import SimpleNamespace

import pytest

from typehaus.resolve.face_extent import face_run_m, framing_side_span


def _layer(polygon, thickness, **kw):
    return SimpleNamespace(polygon=polygon, thickness_m=thickness, is_cavity=False, **kw)


WALL = SimpleNamespace(axis=((0.0, 0.0), (4.0, 0.0)), layers=())
STUDS = ((0.0, 0.0), (4.0, 0.0), (4.0, 0.14), (0.0, 0.14))


def test_a_mitred_band_bills_its_mean_face_and_lays_on_its_short_one():
    # Sheathing on the -y side, mitred 45 deg at both ends: 4.0 m inside, 4.04 m outside.
    mitre = _layer(((0.0, 0.0), (4.0, 0.0), (4.02, -0.02), (-0.02, -0.02)), 0.02)
    assert face_run_m(mitre, 4.0) == pytest.approx(4.02)
    lo, hi = framing_side_span(WALL, mitre, STUDS)
    assert hi - lo == pytest.approx(4.0 + 2 * 0.02 * (0.5 - 0.45), abs=1e-6)


def test_a_butt_cut_through_band_runs_past_the_axis_on_both_faces():
    butt = _layer(((-0.16, 0.0), (4.0, 0.0), (4.0, -0.02), (-0.16, -0.02)), 0.02)
    assert face_run_m(butt, 4.0) == pytest.approx(4.16)
    assert framing_side_span(WALL, butt, STUDS) == pytest.approx((-0.16, 4.0))


def test_a_coating_bills_half_its_ring_and_a_cavity_fill_its_hosts_run():
    coat = _layer(((0.0, 0.0), (4.1, 0.0)), 0.0)
    assert face_run_m(coat, 4.0) == pytest.approx(4.0)  # degenerate ring falls back
    host = _layer(((0.0, 0.0), (3.8, 0.0), (3.8, 0.14), (0.0, 0.14)), 0.14, name="stud")
    fill = SimpleNamespace(polygon=host.polygon, thickness_m=0.05, is_cavity=True,
                           cavity_host="stud")
    wall = SimpleNamespace(axis=WALL.axis, layers=(host, fill))
    assert face_run_m(fill, 4.0, wall) == pytest.approx(3.8)
