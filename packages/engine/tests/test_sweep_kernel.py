"""The sweep kernel: the mitre, the silhouette, the developed length, the turn snapping.

``resolve/sweep.py`` is the one piece of geometry a handrail, a drain and a raceway all go
through, and it is written twice — once here and once in ``ui/src/three/tubeGeometry.ts``.
So this file has two jobs: pin the maths (a mitre that closes, a butt that does not spike, a
straight flight that collapses to two points), and pin the *fixture* the TS side reads, so
the two implementations cannot drift apart unnoticed.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys

import pytest
from _helpers import REPO_ROOT

from typehaus.quantities import inch
from typehaus.resolve.model import SolidSweep
from typehaus.resolve.sweep import (
    MAX_MITER_DEG,
    clean_path,
    is_round_profile,
    leg_frame,
    profile_radius_m,
    rect_profile,
    round_profile,
    simplify_path,
    sweep_leg_axes,
    sweep_legs,
    sweep_length_m,
    sweep_plan_silhouette,
    sweep_turns,
    sweep_z_extent,
)

FIXTURE = REPO_ROOT / "ui" / "src" / "generated" / "sweepParity.json"


def _sweep(path, profile) -> SolidSweep:
    return SolidSweep(path=tuple(path), profile=profile)


# --- profiles -------------------------------------------------------------------------

def test_round_profile_is_ccw_and_on_its_radius() -> None:
    profile = round_profile(0.05, 12)
    assert len(profile) == 12
    assert all(math.isclose(math.hypot(u, v), 0.05, abs_tol=1e-12) for u, v in profile)
    area = sum(profile[i][0] * profile[(i + 1) % 12][1]
               - profile[(i + 1) % 12][0] * profile[i][1] for i in range(12)) / 2.0
    assert area > 0, "the profile must wind CCW in (u, v) or GBox faces its sides inward"


def test_rect_profile_is_width_across_and_depth_through() -> None:
    profile = rect_profile(0.2, 0.05)
    assert max(u for u, _v in profile) == 0.1
    assert max(v for _u, v in profile) == 0.025


def test_round_profile_recognised_and_a_square_is_not() -> None:
    # The IFC fork: a circular run is one IfcSweptDiskSolid, a shaped one is not.
    assert is_round_profile(round_profile(0.05, 12))
    assert is_round_profile(round_profile(0.019, 8))
    assert not is_round_profile(rect_profile(0.0381, 0.0381))
    assert math.isclose(profile_radius_m(round_profile(0.05, 12)), 0.05, abs_tol=1e-12)


# --- the frame ------------------------------------------------------------------------

def test_frame_keeps_a_rectangular_face_level_on_a_rake() -> None:
    """The whole reason "up" is world +Z projected: a rail's flat face must not roll."""
    right, up = leg_frame((3.0, 0.0, 2.0))
    assert math.isclose(right[0], 0.0, abs_tol=1e-12)
    assert math.isclose(right[1], 1.0, abs_tol=1e-12)
    assert math.isclose(right[2], 0.0, abs_tol=1e-12)
    assert up[2] > 0, "up must point up, not down the slope"


def test_a_vertical_leg_falls_back_to_world_y() -> None:
    right, up = leg_frame((0.0, 0.0, -1.0))
    assert math.isclose(up[1], 1.0, abs_tol=1e-12)
    assert math.isclose(math.hypot(right[0], right[1]), 1.0, abs_tol=1e-12)


# --- the mitre ------------------------------------------------------------------------

def test_a_straight_run_is_one_leg_square_at_both_ends() -> None:
    legs = sweep_legs(_sweep([(0, 0, 0), (4, 0, 0)], rect_profile(0.1, 0.2)))
    assert len(legs) == 1
    start, end = legs[0]
    assert all(math.isclose(p[0], 0.0, abs_tol=1e-12) for p in start)
    assert all(math.isclose(p[0], 4.0, abs_tol=1e-12) for p in end)


def test_a_45_degree_turn_mitres_closed() -> None:
    """The two legs' shared ring must be the SAME points, or the tube has a hole in it."""
    legs = sweep_legs(_sweep([(0, 0, 0), (1, 0, 0), (2, 1, 0)], rect_profile(0.05, 0.05)))
    assert len(legs) == 2
    for a, b in zip(legs[0][1], legs[1][0]):
        assert all(math.isclose(x, y, abs_tol=1e-12) for x, y in zip(a, b))


def test_a_90_degree_turn_butts_rather_than_spiking() -> None:
    """Past MAX_MITER_DEG the mitre would run four diameters past the corner."""
    assert MAX_MITER_DEG < 90.0
    legs = sweep_legs(_sweep([(0, 0, 0), (1, 0, 0), (1, 1, 0)], rect_profile(0.2, 0.2)))
    ends = legs[0][1]
    assert all(math.isclose(p[0], 1.0, abs_tol=1e-12) for p in ends), "square to leg 0"
    starts = legs[1][0]
    assert all(math.isclose(p[1], 0.0, abs_tol=1e-12) for p in starts), "square to leg 1"
    reach = max(math.hypot(p[0] - 1.0, p[1]) for ring in (ends, starts) for p in ring)
    assert reach < 0.2, "a butt joint must not reach past the section's own half-diagonal"


def test_doubling_back_stays_bounded() -> None:
    legs = sweep_legs(_sweep([(0, 0, 0), (1, 0, 0), (0.02, 0.05, 0)],
                             round_profile(0.0254, 12)))
    assert len(legs) == 2
    assert max(abs(c) for leg in legs for ring in leg for p in ring for c in p) < 2.0


def test_a_near_collinear_vertex_still_mitres() -> None:
    legs = sweep_legs(_sweep([(0, 0, 0), (1, 0, 0.003), (2, 0, 0.006)],
                             rect_profile(0.0381, 0.0381)))
    for a, b in zip(legs[0][1], legs[1][0]):
        assert all(math.isclose(x, y, abs_tol=1e-12) for x, y in zip(a, b))


def test_a_vertical_leg_is_just_a_leg() -> None:
    """The repeated-plan-point special case the band code needed has nothing left to do."""
    legs = sweep_legs(_sweep([(0, 0, 0), (0, 0, -2), (2, 0, -2.05)],
                             round_profile(0.0508, 12)))
    assert len(legs) == 2


def test_a_degenerate_repeat_is_dropped_not_drawn() -> None:
    path = [(0, 0, 0), (1, 0, 0), (1, 0, 0), (1, 1, -0.01)]
    assert len(clean_path(path)) == 3
    assert len(sweep_legs(_sweep(path, round_profile(0.0254, 12)))) == 2


# --- silhouette, length, extent -------------------------------------------------------

def test_plan_silhouette_of_a_straight_run_is_its_rectangle() -> None:
    ring = sweep_plan_silhouette(_sweep([(0, 0, 0), (4, 0, 0)], rect_profile(0.1, 0.2)))
    assert sorted(ring) == sorted([(0.0, 0.05), (4.0, 0.05), (4.0, -0.05), (0.0, -0.05)])


def test_plan_silhouette_mitres_a_right_angle_to_the_union_of_its_legs() -> None:
    """At a butted 90° the mitred offset IS the union of the two squared-off legs."""
    ring = sweep_plan_silhouette(_sweep([(0, 0, 0), (1, 0, 0), (1, 1, 0)],
                                        rect_profile(0.2, 0.2)))
    assert (0.9, 0.1) in ring and (1.1, -0.1) in ring


def test_developed_length_follows_the_rake_not_its_projection() -> None:
    sweep = _sweep([(0, 0, 0), (3, 0, 4)], rect_profile(0.0381, 0.0381))
    assert math.isclose(sweep_length_m(sweep), 5.0, abs_tol=1e-12)


def test_z_extent_includes_the_section() -> None:
    z0, z1 = sweep_z_extent(_sweep([(0, 0, 1.0), (4, 0, 1.0)], rect_profile(0.1, 0.2)))
    assert math.isclose(z0, 0.9, abs_tol=1e-12)
    assert math.isclose(z1, 1.1, abs_tol=1e-12)


def test_leg_axes_are_the_extrusion_ifc_wants() -> None:
    axes = sweep_leg_axes(_sweep([(0, 0, 0), (0, 0, -2), (2, 0, -2)],
                                 round_profile(0.0508, 12)))
    assert len(axes) == 2
    (origin, axis, _ref, run) = axes[0]
    assert origin == (0.0, 0.0, 0.0)
    assert math.isclose(axis[2], -1.0, abs_tol=1e-12)
    assert math.isclose(run, 2.0, abs_tol=1e-12)


# --- turns ----------------------------------------------------------------------------

def test_a_vertical_meeting_a_horizontal_measures_a_real_90() -> None:
    """The old estimate hard-coded ``return 90.0`` here because plan geometry said nothing."""
    turns = sweep_turns(_sweep([(0, 0, 0), (0, 0, -2), (2, 0, -2)],
                               round_profile(0.0508, 12)))
    assert len(turns) == 1
    assert math.isclose(turns[0].angle_deg, 90.0, abs_tol=1e-9)
    assert math.isclose(turns[0].plan_angle_deg, 0.0, abs_tol=1e-9)


def test_a_pitched_branch_off_a_stack_measures_less_than_90() -> None:
    """A 1/4 bend into a 2"/ft branch is 80.5° of geometry — the fitting take-off's window."""
    drop = 2.0 / 12.0  # 2 inches of fall per foot, in feet
    turns = sweep_turns(_sweep([(0, 0, 0), (0, 0, -2), (3.0, 0, -2 - 3.0 * drop)],
                               round_profile(0.0508, 12)))
    assert 78.0 < turns[0].angle_deg < 82.0


def test_a_straight_run_has_no_turns() -> None:
    assert sweep_turns(_sweep([(0, 0, 0), (1, 0, 0), (2, 0, 0)],
                              rect_profile(0.05, 0.05))) == []


# --- simplify -------------------------------------------------------------------------

def test_a_straight_flight_collapses_to_the_two_points_it_is_cut_at() -> None:
    sampled = [(i * 0.25, 0.0, i * 0.25 * 0.6818) for i in range(60)]
    assert len(simplify_path(sampled, 0.0015875, 0.0015875)) == 2


def test_a_winder_keeps_the_vertices_its_curve_needs() -> None:
    """A quarter turn of 0.9 m radius, sampled at the rail's own 0.25 m step.

    Nothing here is collinear to a sixteenth of an inch, so nothing is dropped — which is the
    point: the collapse is not a smoothing pass, it only removes vertices that carry no shape.
    """
    steps = 6
    sampled = [(0.9 * math.cos(i * math.pi / 2 / steps), 0.9 * math.sin(i * math.pi / 2 / steps),
                i * 0.05) for i in range(steps + 1)]
    kept = simplify_path(sampled, 0.0015875, 0.0015875)
    assert 3 <= len(kept) <= len(sampled)
    assert kept[0] == sampled[0] and kept[-1] == sampled[-1]


def test_simplify_never_drifts_past_its_tolerance() -> None:
    sampled = [(i * 0.25, 0.0, 0.001 * i * i) for i in range(40)]
    kept = simplify_path(sampled, 0.002, 0.002)
    for point in sampled:
        assert any(abs(point[0] - k[0]) < 1e-9 for k in kept) or _near_polyline(point, kept)


def _near_polyline(point, polyline) -> bool:
    return min(_point_to_segment(point, a, b)
               for a, b in zip(polyline, polyline[1:])) <= 0.002 + 1e-9


def _point_to_segment(p, a, b) -> float:
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    denominator = sum(v * v for v in ab)
    t = 0.0 if denominator < 1e-18 else max(0.0, min(1.0, sum(
        ap[i] * ab[i] for i in range(3)) / denominator))
    return math.dist(p, [a[i] + ab[i] * t for i in range(3)])


# --- sections through a run -----------------------------------------------------------
#
# The slice kernel's ``GBox`` fast path reads the bottom ring as a PLAN FOOTPRINT and pairs
# each crossing with the top ring at the same fraction — right for every member, panel and
# closure band, and wrong for a swept leg, whose two rings are separated along the LEG AXIS.
# For a horizontal pipe the "bottom" ring is a vertical disc whose plan footprint is a line,
# so walking it drew nothing at all: every drain silently vanished from every section the day
# sweeps landed, and the only thing that noticed was a golden file full of deletions.

def _tube_boxes(sweep):
    from typehaus.resolve.geometry_ir import GBox

    return [GBox(corners_bottom=start, corners_top=end) for start, end in sweep_legs(sweep)]


def test_a_cut_across_a_pipe_draws_the_pipe_and_not_nothing() -> None:
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid

    radius = inch(2).meters
    sweep = _sweep([(0, 0, 2.0), (6, 0, 1.9)], round_profile(radius, 12))
    plane = CutPlane(axis="y", station_m=3.0)
    profiles = [profile for box in _tube_boxes(sweep)
                for profile in slice_solid(box, plane)]
    assert profiles, "a pipe crossing the cut plane has to draw something"
    us = [u for profile in profiles for u, _z in profile.outline]
    zs = [z for profile in profiles for _u, z in profile.outline]
    assert max(us) - min(us) == pytest.approx(2.0 * radius, abs=1e-3)
    assert max(zs) - min(zs) == pytest.approx(2.0 * radius, abs=1e-3)


def test_a_cut_along_a_pipe_draws_its_flank() -> None:
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid

    sweep = _sweep([(0, 0, 2.0), (6, 0, 2.0)], round_profile(inch(2).meters, 12))
    plane = CutPlane(axis="x", station_m=0.0)
    profiles = [profile for box in _tube_boxes(sweep)
                for profile in slice_solid(box, plane)]
    assert profiles
    us = [u for profile in profiles for u, _z in profile.outline]
    assert max(us) - min(us) == pytest.approx(6.0, abs=1e-3)


def test_an_upright_box_keeps_the_fast_path() -> None:
    """The shortcut is load-bearing: 15,160 member solids per resolve go through it."""
    from typehaus.resolve.geometry_ir import GBox
    from typehaus.resolve.geometry_slice import _box_is_upright

    member = GBox(corners_bottom=((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
                  corners_top=((0, 0, 3), (1, 0, 3), (1, 1, 3.2), (0, 1, 3.2)))
    assert _box_is_upright(member)
    assert not _box_is_upright(_tube_boxes(
        _sweep([(0, 0, 0), (2, 0, 0)], round_profile(0.05, 12)))[0])


def test_every_swept_leg_in_catlin_draws_when_it_is_cut(catlin_model) -> None:
    """Cut every leg of every run both ways, at its own mid-station. Every one must draw.

    The section kernel discards a face it cannot close rather than fabricating one — the
    right call — so a leg that failed here would silently draw *nothing at all*, which is
    exactly how every drain vanished from the sections the day sweeps landed. Cutting at the
    midpoint rather than at an end is deliberate: a plane tangent to a tube meets it in a
    hairline, and a hairline is a degenerate drawing for any solid, not a swept one.
    """
    from typehaus.resolve.geometry_ir import GBox
    from typehaus.resolve.geometry_slice import CutPlane, perp_values, slice_solid

    swept = [solid for solid in catlin_model.solids if solid.sweep is not None]
    assert len(swept) > 50, "the reference house should be full of runs by now"
    missing = []
    for solid in swept:
        for index, (start, end) in enumerate(sweep_legs(solid.sweep)):
            box = GBox(corners_bottom=start, corners_top=end)
            for axis in ("x", "y"):
                values = perp_values(box, CutPlane(axis=axis, station_m=0.0).perp_index)
                low, high = min(values), max(values)
                if high - low < 1e-9:
                    continue  # the leg lies in the plane; there is no cut to make
                station = (low + high) / 2.0
                if not slice_solid(box, CutPlane(axis=axis, station_m=station)):
                    missing.append(f"{solid.tag} leg {index} at {axis}={station:.4f}")
    assert not missing, missing[:5]


def test_a_tube_cut_on_its_own_axis_plane_still_draws() -> None:
    """The cut that used to break, named: a 12-gon has two vertex rows on its axis plane.

    Welding segments into a ring drops anything shorter than 1e-6, so a plane grazing a
    vertex left two slivers, lost both, and the ring fell open. A section down the centreline
    of a drain stack is an ordinary thing to draw, so the swept branch takes the hull of its
    crossings instead — no welding, nothing to fall open.
    """
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid

    radius = inch(2).meters
    sweep = _sweep([(0, 0, 2.0), (6, 0, 2.0)], round_profile(radius, 12))
    box = _tube_boxes(sweep)[0]
    profiles = slice_solid(box, CutPlane(axis="y", station_m=3.0))
    assert len(profiles) == 1
    zs = [z for _u, z in profiles[0].outline]
    assert max(zs) - min(zs) == pytest.approx(2.0 * radius, abs=1e-6)


def test_a_butted_corner_draws_at_the_station_its_cap_sits_on() -> None:
    """``CD-B-KITCHEN-RUN`` turns at x=10.668 m — 35 ft exactly, a station a detail may well
    be cut at. The leg arriving there is capped square on that plane, so the cut grazes a
    whole ring of vertices at once rather than two of them."""
    from typehaus.resolve.geometry_slice import CutPlane, slice_solid

    radius = inch(1.5).meters
    sweep = _sweep([(0, 0, 0), (10.668, 0, 0), (10.668, -0.5, 0)], round_profile(radius, 12))
    arriving = _tube_boxes(sweep)[0]
    profiles = slice_solid(arriving, CutPlane(axis="y", station_m=10.668))
    assert len(profiles) == 1, "the leg's own end cap is the face the cut lands on"
    zs = [z for _u, z in profiles[0].outline]
    assert max(zs) - min(zs) == pytest.approx(2.0 * radius, abs=1e-6)


def test_the_hull_cut_agrees_with_the_mesh_walk_it_replaced(catlin_model) -> None:
    """Two independent kernels over every run, at twenty stations each: the same face.

    The hull is the *more* accurate of the two — the mesh walk snaps its endpoints to the
    1e-6 weld grid — so this is a tolerance on that snapping, not on the hull.
    """
    from typehaus.resolve.geometry_ir import GBox
    from typehaus.resolve.geometry_slice import (CutPlane, _box_hull_profile, _box_mesh,
                                                 _mesh_profiles, _nudge_off, perp_values)

    def area(ring) -> float:
        count = len(ring)
        return abs(sum(ring[i][0] * ring[(i + 1) % count][1]
                       - ring[(i + 1) % count][0] * ring[i][1]
                       for i in range(count))) / 2.0

    compared = 0
    for solid in (s for s in catlin_model.solids if s.sweep is not None):
        for start, end in sweep_legs(solid.sweep):
            box = GBox(corners_bottom=start, corners_top=end)
            mesh = _box_mesh(box)
            for axis in ("x", "y"):
                values = perp_values(box, CutPlane(axis=axis, station_m=0.0).perp_index)
                low, high = min(values), max(values)
                if high - low < 1e-6:
                    continue
                for step in range(1, 20):
                    station = low + (high - low) * step / 20.0
                    plane = _nudge_off(CutPlane(axis=axis, station_m=station),
                                       values, low, high)
                    hulled = _box_hull_profile(box, plane)
                    walked, open_chains = _mesh_profiles(mesh, plane)
                    if open_chains or len(walked) != 1 or len(hulled) != 1:
                        continue  # the mesh walk's own failures are what the hull replaces
                    compared += 1
                    assert area(hulled[0].outline) == pytest.approx(
                        area(walked[0].outline), rel=1e-4)
    assert compared > 5000, f"only {compared} cuts compared — the sample went thin"


def test_a_non_convex_swept_box_falls_back_to_the_mesh_walk() -> None:
    """The hull is only the section of a *convex* solid, and the guard says so out loud."""
    from typehaus.resolve.geometry_ir import GBox
    from typehaus.resolve.geometry_slice import _box_is_convex

    assert _box_is_convex(_tube_boxes(
        _sweep([(0, 0, 0), (2, 0, 0)], round_profile(0.05, 12)))[0])
    chevron = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 0.4, 0.0), (1.0, 1.0, 0.0),
               (0.0, 1.0, 0.0))
    assert not _box_is_convex(GBox(
        corners_bottom=chevron,
        corners_top=tuple((x, y, z + 1.0) for x, y, z in chevron)))


# --- the TS fixture -------------------------------------------------------------------

def test_the_shared_parity_fixture_is_current() -> None:
    """``ui/src/generated/sweepParity.json`` is what the TS port is asserted against.

    Stale, it would pin ``tubeGeometry.ts`` to a mitre this module no longer draws — which is
    exactly the silent divergence the fixture exists to prevent. Regenerate with
    ``.venv/bin/python scripts/gen_sweep_parity.py``.
    """
    generator = REPO_ROOT / "scripts" / "gen_sweep_parity.py"
    result = subprocess.run([sys.executable, "-c",
                             f"import runpy,json,sys; sys.argv=['x'];"
                             f"m=runpy.run_path({str(generator)!r});"
                             f"print(json.dumps(m['payload']()))"],
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == json.loads(FIXTURE.read_text()), (
        "sweepParity.json is stale — run scripts/gen_sweep_parity.py")
