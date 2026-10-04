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


@pytest.mark.parametrize("part", [
    "H2.5A", "H10ASS", "LSTA24", "MSTA12Z", "A35Z", "LS30", "HGAM10",
    "LTP4", "STHD14", "STHD14RJ", "HETA20Z", "MASA", "DTT2Z", "SP4", "SP6",
    "APVKB45-6", "KBS1Z",
])
def test_meshes_have_closed_nonzero_steel_components_and_outward_winding(part):
    mesh = tie_mesh(part)
    edges = {}
    volume = 0.0
    for triangle in mesh.triangles:
        a, b, c = (mesh.positions[index] for index in triangle)
        cross = (b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2],
                 b[0] * c[1] - b[1] * c[0])
        volume += sum(a[index] * cross[index] for index in range(3)) / 6.0
        for first, second in zip(triangle, (triangle[1], triangle[2], triangle[0]), strict=True):
            edge = tuple(sorted((first, second)))
            edges[edge] = edges.get(edge, 0) + 1
    assert volume > 0.0
    assert set(edges.values()) == {2}


def test_unknown_and_unmeasured_coil_do_not_invent_product_geometry():
    assert tie_mesh("unlisted-simpson-part") is None
    assert tie_mesh("CS16") is None
    with pytest.raises(ValueError, match="cut length"):
        tie_mesh("CS16", strap_length_in=-1.0)
