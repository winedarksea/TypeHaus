"""Catalog envelopes and open folded bodies, without building a house fixture."""

from __future__ import annotations

import math

import pytest

from typehaus.resolve.connector_geometry.ties import STEEL_THICKNESS_IN, tie_mesh


def _bounds_in(mesh):
    return tuple((min(point[axis] for point in mesh.positions) / 0.0254,
                  max(point[axis] for point in mesh.positions) / 0.0254)
                 for axis in range(3))


@pytest.mark.parametrize(("part", "lower", "upper"), [
    ("H2.5A", -2.1875, 3.8125), ("H2.5AZ", -2.1875, 3.8125),
    ("H2.5ASS", -2.1875, 3.8125), ("H10ASS", -2.75, 3.5),
    ("STHD14", -14.0, 26.125), ("STHD14RJ", -14.0, 39.625),
    ("HETA20Z", -4.0, 16.0), ("DTT2Z", 0.0, 6.9375),
])
def test_vertical_datums_follow_manufacturer_drawing(part, lower, upper):
    mesh = tie_mesh(part)
    assert mesh is not None
    assert _bounds_in(mesh)[2] == pytest.approx((lower, upper))


@pytest.mark.parametrize(("part", "width", "height"), [
    ("A35Z", 1.4375, 4.5), ("LS30", 2.25, 3.375),
])
def test_framing_angles_have_thin_perpendicular_leaves(part, width, height):
    mesh = tie_mesh(part)
    bounds = _bounds_in(mesh)
    thickness = STEEL_THICKNESS_IN[18]
    assert bounds[0] == pytest.approx((-thickness, width))
    assert bounds[1] == pytest.approx((-thickness, width))
    assert bounds[2] == pytest.approx((0.0, height))
    # A corner connector leaves the wood-sized interior empty.
    assert all(point[0] <= 0.0 or point[1] <= 0.0 for point in mesh.positions)


def test_h10a_has_open_member_pocket_and_keeps_its_stock_width():
    mesh = tie_mesh("H10ASS", member_width_in=3.0)
    assert mesh == tie_mesh("H10A", member_width_in=1.5)
    assert _bounds_in(mesh)[0] == pytest.approx((-2.5, 2.5))
    opening_half_width = 1.5625 * 0.0254 / 2.0
    # The upper opening remains open across its width; backing fills only below it.
    upper_points = [point for point in mesh.positions if point[2] > 0.0]
    assert all(abs(point[0]) >= opening_half_width - 1e-12 for point in upper_points)


def test_single_sided_hurricane_tie_has_two_orthogonal_attachment_faces():
    mesh = tie_mesh("H2.5A")
    normals = []
    for triangle in mesh.triangles:
        a, b, c = (mesh.positions[index] for index in triangle)
        ab = [b[index] - a[index] for index in range(3)]
        ac = [c[index] - a[index] for index in range(3)]
        normals.append((ab[1] * ac[2] - ab[2] * ac[1],
                        ab[2] * ac[0] - ab[0] * ac[2],
                        ab[0] * ac[1] - ab[1] * ac[0]))
    assert any(abs(normal[0]) > 0.001 for normal in normals)
    assert any(abs(normal[1]) > 0.001 for normal in normals)


@pytest.mark.parametrize(("part", "length", "gauge"), [
    ("LSTA24", 24.0, 20), ("MSTA12Z", 12.0, 18), ("CS16", 42.0, 16),
])
def test_flat_straps_have_published_width_length_and_gauge(part, length, gauge):
    mesh = tie_mesh(part, strap_length_in=length)
    assert _bounds_in(mesh)[0] == pytest.approx((-0.625, 0.625))
    assert _bounds_in(mesh)[1] == pytest.approx((-length / 2.0, length / 2.0))
    assert _bounds_in(mesh)[2] == pytest.approx((0.0, STEEL_THICKNESS_IN[gauge]))


def test_ridge_strap_follows_both_slopes_preserving_developed_length():
    slope = math.atan(6.0 / 12.0)
    mesh = tie_mesh("LSTA24", slope_radians=slope)
    endpoint_y, endpoint_z = 12.0 * math.cos(slope), -12.0 * math.sin(slope)
    assert any(point[1] / 0.0254 == pytest.approx(endpoint_y)
               and point[2] / 0.0254 == pytest.approx(endpoint_z) for point in mesh.positions)
    assert any(point[1] / 0.0254 == pytest.approx(-endpoint_y)
               and point[2] / 0.0254 == pytest.approx(endpoint_z) for point in mesh.positions)
    assert tie_mesh("LSTA24", slope_radians=-slope) == mesh


def test_ridge_strap_lies_level_across_the_beam_top():
    """Over a 3 1/2" beam the strap is flat for 3 1/2", then the legs fall from its edges."""
    slope = math.atan(6.0 / 12.0)
    mesh = tie_mesh("LSTA24", slope_radians=slope, member_width_in=3.5)
    leg = 12.0 - 1.75
    end_y, end_z = 1.75 + leg * math.cos(slope), -leg * math.sin(slope)
    for side in (-1.0, 1.0):
        assert any(point[1] / 0.0254 == pytest.approx(side * 1.75)
                   and point[2] / 0.0254 == pytest.approx(0.0) for point in mesh.positions)
        assert any(point[1] / 0.0254 == pytest.approx(side * end_y)
                   and point[2] / 0.0254 == pytest.approx(end_z) for point in mesh.positions)


def test_unsized_holdown_is_explicit_sthd14_display_representative():
    assert tie_mesh("STHD") == tie_mesh("STHD14")
    assert tie_mesh("STHD14RJ") != tie_mesh("STHD14")


def test_masa_has_two_separate_wrapped_nailing_legs_and_embedded_spoon():
    mesh = tie_mesh("MASA", member_depth_in=2.5)
    bounds = _bounds_in(mesh)
    assert bounds[2] == pytest.approx((-3.375, 2.5 + STEEL_THICKNESS_IN[16]))
    assert bounds[1] == pytest.approx((-STEEL_THICKNESS_IN[16], 4.0))
    nailing_points = [point for point in mesh.positions if point[2] > 0.5 * 0.0254]
    assert all(abs(point[0]) >= 0.75 * 0.0254 - 1e-12 for point in nailing_points)
    assert max(point[1] / 0.0254 for point in nailing_points) == pytest.approx(1.75)
    assert any(point[1] > 0.0 and point[2] < 0.0 for point in mesh.positions)


def _seat_surface_covers(mesh, x_in, y_in):
    x, y = x_in * 0.0254, y_in * 0.0254

    def side(a, b):
        return (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])

    for triangle in mesh.triangles:
        a, b, c = (mesh.positions[index] for index in triangle)
        if any(abs(point[2]) > 1e-12 for point in (a, b, c)):
            continue
        sides = (side(a, b), side(b, c), side(c, a))
        if all(value > 1e-12 for value in sides) or all(value < -1e-12 for value in sides):
            return True
    return False


def test_dtt_seat_has_open_anchor_hole_and_steel_around_it():
    mesh = tie_mesh("DTT2Z")
    assert _bounds_in(mesh)[0] == pytest.approx((-1.625, 1.625))
    assert not _seat_surface_covers(mesh, 0.0, 0.8125)
    assert _seat_surface_covers(mesh, 0.60, 0.85)


@pytest.mark.parametrize(("part", "opening", "length"), [
    ("SP4", 3.5625, 7.25), ("SP6", 5.5625, 7.75),
])
def test_stud_plate_tie_wraps_full_plate_width(part, opening, length):
    mesh = tie_mesh(part)
    assert _bounds_in(mesh)[1] == pytest.approx((-opening / 2.0 - STEEL_THICKNESS_IN[20],
                                               opening / 2.0 + STEEL_THICKNESS_IN[20]))
    assert _bounds_in(mesh)[2] == pytest.approx((-length, STEEL_THICKNESS_IN[20]))


def test_lateral_plate_is_a_thin_notched_plate_at_published_size():
    bounds = _bounds_in(tie_mesh("LTP4"))
    assert bounds[0] == pytest.approx((-1.5, 1.5))
    assert bounds[1] == pytest.approx((-STEEL_THICKNESS_IN[20], 0.0))
    assert bounds[2] == pytest.approx((-2.125, 2.125))


def test_unknown_and_unmeasured_coil_do_not_invent_product_geometry():
    assert tie_mesh("unlisted-simpson-part") is None
    assert tie_mesh("CS16") is None
    with pytest.raises(ValueError, match="cut length"):
        tie_mesh("CS16", strap_length_in=-1.0)


def test_derived_a35z_lies_on_its_sill_and_against_a_member_face(catlin_model_ro):
    """Joist-end and wall-top-station ties: flat leaf on the sill top, upright on a face."""
    from shapely.geometry import LineString, Point, Polygon, box

    from typehaus.resolve.framing.profiles import cross_section

    tol = 1 / 32 * 0.0254
    sills = [(Polygon(s.outline), s.z1_m) for s in catlin_model_ro.solids
             if s.category == "sill_plate"]
    members = [LineString([m.p0, m.p1]).buffer(
        (m.plan_width_m or cross_section(m.profile).width_m) / 2, cap_style=2)
        for f in catlin_model_ro.floors for m in f.members
        if m.category in ("rim", "joist", "sister_joist", "trimmer")]
    ties = [s for s in catlin_model_ro.solids if s.derived and s.product == "A35Z"]
    # 57 joist-end ties (the W-B-W1 and W-B-E1 seams are packs, tied on their outer faces),
    # 2 on FO-M-ERV-OA's south trimmer pack + 45 at the wall-top stations.
    assert len(ties) == 104
    for tie in ties:
        xs, ys, zs = zip(*tie.body_mesh.positions, strict=True)
        spot = box(min(xs), min(ys), max(xs), max(ys))
        tops = [z for poly, z in sills if poly.contains(spot.centroid)]
        assert tops and abs(min(zs) - max(tops)) <= tol, tie.tag
        corners = list(spot.exterior.coords)[:4]
        edges = list(zip(corners, corners[1:] + corners[:1], strict=True))
        assert any(not poly.contains(spot.centroid)
                   and all(poly.exterior.distance(Point(p)) <= tol for p in edge)
                   for poly in members if poly.distance(spot) <= tol
                   for edge in edges), tie.tag


def _member(key, y_in, category="joist", x0_in=1.75, x1_in=200.0, width_in=2.3125):
    from types import SimpleNamespace

    return SimpleNamespace(child_key=key, category=category, profile="11.875 TJI 230",
                           plan_width_m=width_in * 0.0254, z0_m=-0.3016, z1_m=0.0,
                           p0=(x0_in * 0.0254, y_in * 0.0254), p1=(x1_in * 0.0254, y_in * 0.0254))


def test_ends_closer_than_a_tie_slot_are_one_pack_tied_on_its_outer_faces():
    """W-B-W1's seam: three TJI ends 3/4" and 0" apart. Nothing fits between them, so the
    outer two each own one face's tie, the middle none, and every leaf lies clear."""
    from types import SimpleNamespace

    from typehaus.resolve.connector_geometry.plate_angle import plate_angle_dims
    from typehaus.resolve.connector_geometry.sill_tie_pack import sill_pack

    rim = _member("rim", 0.0, "rim", 1.125, 1.125, 1.25)
    rim.p0, rim.p1 = (1.125 * 0.0254, 0.0), (1.125 * 0.0254, 300 * 0.0254)
    ends = [_member(f"j{y}", y) for y in (240.0, 256.0, 259.0625, 261.375, 277.375)]
    floor = SimpleNamespace(members=[rim, *ends])
    dims = plate_angle_dims("A35Z")
    packs = {m.child_key: sill_pack(m, m.p0, floor, [floor], dims) for m in ends}
    assert [len(packs[k].ties) for k in ("j256.0", "j259.0625", "j261.375")] == [1, 0, 1]
    assert packs["j259.0625"].members == 3
    assert [round(v / 0.0254, 3) for v in packs["j256.0"].extent_m] == [254.844, 262.531]
    lo, hi = packs["j256.0"].ties[0], packs["j261.375"].ties[0]
    assert lo.centre[1] / 0.0254 == pytest.approx(254.84375 - 0.125 - 0.71875)
    assert hi.centre[1] / 0.0254 == pytest.approx(262.53125 + 0.125 + 0.71875)
    assert not lo.blocked_by and not hi.blocked_by
    assert len(packs["j240.0"].ties) == 1 and packs["j240.0"].members == 1
    # A ledger across both of a lone end's slots: the tie is reported, not hidden.
    ledger = _member("ledger", 0.0, "ledger", width_in=1.5)
    ledger.p0, ledger.p1 = (3.0 * 0.0254, 230 * 0.0254), (3.0 * 0.0254, 250 * 0.0254)
    floor.members.append(ledger)
    blocked = sill_pack(ends[0], ends[0].p0, floor, [floor], dims).ties[0]
    assert blocked.blocked_by == ("ledger",)


def test_a_spoon_that_cannot_reach_from_the_framing_face_is_cast_at_the_core_face() -> None:
    """A 6" core with the leaf 2 9/16" in: no side holds a 5" spoon, so the strap enters at
    the near face and is bent one cycle (ESR-2920 §4.2) — never clamped short."""
    from typehaus.hardware.esr2920 import max_clear_span_in
    from typehaus.resolve.connector_geometry.embedded_straps import embedded_strap_frame

    inch_m = 0.0254
    core = ((0.0, 0.0), (10.0, 0.0), (10.0, 6.0 * inch_m), (0.0, 6.0 * inch_m))
    point = (5.0, 2.5625 * inch_m)
    _, y_axis, spoon, jog = embedded_strap_frame(core, point, (1.0, 0.0, 0.0),
                                                 (0.0, 1.0, 0.0), 5.0, 0.75)
    assert spoon is None and jog == pytest.approx(2.5625)
    assert y_axis[1] == pytest.approx(1.0)  # toward the far face, 3 7/16" ahead of the leaf
    # Only the RJ prints a clear span; a standard strap is read over Figure 1's one 2x sill.
    assert max_clear_span_in("STHD14") == pytest.approx(1.5)
    assert max_clear_span_in("STHD14RJ") == pytest.approx(17.0)
