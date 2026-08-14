"""Regression: strapping/furring battens and courses split around window/door openings
instead of running straight through them (``resolve/framing/furring.py``).

Builds a minimal wall + FURRING layer + assembly double directly, following the fixture
convention in ``test_solver_units.py`` (a bare ``ResolvedWall``/``SimpleNamespace`` plan,
no full house), so the vertical/horizontal split logic is asserted independent of any
authored house's geometry.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.framing.furring import frame_wall_furring
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall

_BAND = ((0.0, 0.05), (3.6576, 0.05), (3.6576, -0.05), (0.0, -0.05))


def _opening(center_along_m: float, width_m: float, height_m: float,
            sill_m: float) -> ResolvedOpening:
    return ResolvedOpening(
        uid="O1", tag="WIN-1", host_wall="W-TEST", type_ref=None,
        width_m=width_m, height_m=height_m, sill_m=sill_m, center_along_m=center_along_m,
        kind="window", is_door=False,
    )


def _vertical_wall(spacing_in: float | None):
    layer = Layer(name="strap", material_ref="spf", thickness=inch(0.75),
                 function=LayerFunction.FURRING,
                 framing=FramingSpec(member="1x4", direction="vertical",
                                     spacing=inch(spacing_in) if spacing_in else None))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    resolved = ResolvedLayer(name="strap", material_ref="spf", function="furring",
                             thickness_m=inch(0.75).meters, polygon=_BAND)
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (3.6576, 0.0)), layers=(resolved,), z0_m=0.0, z1_m=2.5,
    )
    return plan, rw


def test_vertical_batten_splits_around_a_mid_height_window():
    plan, rw = _vertical_wall(spacing_in=150.0)  # forces exactly two stations: first + last
    # First station sits at face/2 (~0.04445 m); a 0.2 m-wide window centred there overlaps
    # only that station, not the far one at ~3.61315 m.
    opening = _opening(center_along_m=0.04445, width_m=0.2, height_m=0.5, sill_m=1.0)
    members, findings = frame_wall_furring(plan, rw, [opening])
    assert not findings

    at_first = sorted((m for m in members if abs(m.p0[0] - 0.04445) < 1e-6),
                      key=lambda m: m.z0_m)
    assert len(at_first) == 2
    assert abs(at_first[0].z0_m - 0.0) < 1e-6 and abs(at_first[0].z1_m - 1.0) < 1e-6
    assert abs(at_first[1].z0_m - 1.5) < 1e-6 and abs(at_first[1].z1_m - 2.5) < 1e-6

    at_last = [m for m in members if abs(m.p0[0] - 3.61315) < 1e-6]
    assert len(at_last) == 1
    assert abs(at_last[0].z0_m - 0.0) < 1e-6 and abs(at_last[0].z1_m - 2.5) < 1e-6


def test_vertical_batten_unaffected_with_no_openings():
    plan, rw = _vertical_wall(spacing_in=150.0)
    members, _ = frame_wall_furring(plan, rw, [])
    assert len(members) == 2
    assert all(abs(m.z0_m - 0.0) < 1e-6 and abs(m.z1_m - 2.5) < 1e-6 for m in members)


def _horizontal_wall():
    layer = Layer(name="strap", material_ref="spf", thickness=inch(0.75),
                 function=LayerFunction.FURRING,
                 framing=FramingSpec(member="1x4", direction="horizontal",
                                     spacing=inch(60.0)))  # forces exactly two courses
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    band = ((0.0, 0.05), (3.0, 0.05), (3.0, -0.05), (0.0, -0.05))
    resolved = ResolvedLayer(name="strap", material_ref="spf", function="furring",
                             thickness_m=inch(0.75).meters, polygon=band)
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (3.0, 0.0)), layers=(resolved,), z0_m=0.0, z1_m=1.0,
    )
    return plan, rw


def test_horizontal_course_splits_around_a_window_in_its_band():
    plan, rw = _horizontal_wall()
    # Bottom course covers z in [0, ~0.0889]; a window from z=[0, 0.05] overlaps it and no
    # other course. Centred mid-band so the split leaves a real piece on both sides.
    opening = _opening(center_along_m=1.5, width_m=0.5, height_m=0.05, sill_m=0.0)
    members, findings = frame_wall_furring(plan, rw, [opening])
    assert not findings

    bottom = sorted((m for m in members if abs(m.z0_m - 0.0) < 1e-6), key=lambda m: m.p0[0])
    assert len(bottom) == 2
    assert abs(bottom[0].p1[0] - 1.25) < 1e-6 and abs(bottom[1].p0[0] - 1.75) < 1e-6

    top = [m for m in members if m.z0_m > 0.5]
    assert len(top) == 1
    assert top[0].p0[0] < 0.02 and top[0].p1[0] > 2.98


def test_horizontal_course_unaffected_with_no_openings():
    plan, rw = _horizontal_wall()
    members, _ = frame_wall_furring(plan, rw, [])
    assert len(members) == 2
