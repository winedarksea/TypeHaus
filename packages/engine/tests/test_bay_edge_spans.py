"""A short ply or joist is a bay edge only over its own extent (not the whole bay line)."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.enums import DuctRouting
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import bay_edge_faces, duct_bay_occupancy, joist_line_stations
from typehaus.resolve.model import FramedMember
from typehaus.routing.corridors import floor_corridors

_IN = M_PER_IN


def _member(key: str, category: str, y_in: float, x0_in: float, x1_in: float) -> FramedMember:
    return FramedMember(
        parent_uid="u", child_key=key, category=category, profile="2x10",
        p0=(x0_in * _IN, y_in * _IN), p1=(x1_in * _IN, y_in * _IN), z0_m=0.0, z1_m=9.25 * _IN,
        length_m=abs(x1_in - x0_in) * _IN)


def _floor() -> SimpleNamespace:
    """Joists at y = 0/16/32/48" over x 0..120"; a 24"-long sister ply at y = 24", x 40..64"."""
    members = [_member(f"joist-{i}", "joist", 16.0 * i, 0.0, 120.0) for i in range(4)]
    members.append(_member("sister-0", "sister_joist", 24.0, 40.0, 64.0))
    return SimpleNamespace(tag="F-X", direction="x", members=members, deck_z0_m=9.25 * _IN)


def test_a_short_ply_is_a_joist_line_only_where_it_reaches() -> None:
    floor = _floor()
    assert 24.0 * _IN not in joist_line_stations(floor, (0.0, 30.0 * _IN))
    assert 24.0 * _IN in joist_line_stations(floor, (50.0 * _IN, 52.0 * _IN))
    assert len(bay_edge_faces(floor)) == 5  # the unspanned reading still lists every line


def test_a_short_ply_narrows_a_corridor_only_over_its_own_extent(monkeypatch) -> None:
    # The fixture holds no runs: stub the two readers that walk the plan for them.
    monkeypatch.setattr("typehaus.resolve.mep_envelopes.run_polylines", lambda model: [])
    monkeypatch.setattr("typehaus.resolve.mep_packing.run_occupants", lambda *a, **k: [])
    model = SimpleNamespace(floors=[floor := _floor()])
    corridors = [c for c in floor_corridors(model) if c.tag.startswith(floor.tag)]
    wide = [c for c in corridors if abs(c.station - 24.0 * _IN) < 1e-6]  # bay 16..32
    extents = [(round(c.lo_m / _IN), round(c.hi_m / _IN))
               for c in sorted(wide, key=lambda c: c.lo_m)]
    assert extents == [(0, 40), (64, 120)]
    # Beside the ply the 16" bay is two half bays, too narrow to be a field bay: no corridor.
    assert not any(40 * _IN < (c.lo_m + c.hi_m) / 2.0 < 64 * _IN and 16 * _IN < c.station
                   < 32 * _IN for c in corridors)


def test_a_duct_straddles_a_short_ply_only_where_it_reaches() -> None:
    floor = _floor()

    def conflicts(x0: float, x1: float) -> list[str]:
        y = 24.0 * _IN  # centred on the ply's line
        return duct_bay_occupancy(
            [(x0 * _IN, y), (x1 * _IN, y)], width_m=6 * _IN, depth_m=6 * _IN,
            routing=DuctRouting.JOIST_BAY, floor=floor, bearing_walls=[],
            spacing_m=16 * _IN)[0]

    assert not conflicts(0.0, 30.0)
    assert conflicts(30.0, 50.0)
