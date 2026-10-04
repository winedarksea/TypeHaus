"""Catalog envelopes, folded installation and datum tests without a house fixture."""

from collections import Counter
from math import atan, cos, sin, tan

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.hangers import hanger_mesh


def _positions_in(part, **placement):
    mesh = hanger_mesh(part, **placement)
    assert mesh is not None
    return tuple(tuple(value / M_PER_IN for value in point) for point in mesh.positions)


@pytest.mark.parametrize("part,width,height,bearing,thickness", [
    ("LUS28", 1.5625, 6.625, 1.75, 0.048),
    ("LUS210Z", 1.5625, 7.8125, 1.75, 0.048),
    ("LUS210SS", 1.5625, 7.8125, 1.75, 0.048),
    ("LUS28-2Z", 3.125, 7.0, 2.0, 0.048),
    ("LUS48", 3.5625, 6.75, 2.0, 0.048),
    ("HHUS410", 3.625, 9.0, 3.0, 0.075),
    ("HU28-2Z", 3.125, 6.3125, 2.5, 0.075),
    ("HU212-3", 4.6875, 9.8125, 2.5, 0.075),
    ("HUC212-3", 4.6875, 9.8125, 2.5, 0.075),
    ("HUCQ410-SDS", 3.5625, 9.0, 3.0, 0.075),
    ("IUS2.56/11.88", 2.625, 11.875, 2.0, 0.048),
])
def test_published_envelope_keeps_clear_opening_and_thin_seat(part, width, height,
                                                            bearing, thickness):
    positions = _positions_in(part)
    assert max(z for _, _, z in positions) - min(z for _, _, z in positions) == (
        pytest.approx(height))
    assert min(z for _, _, z in positions) == pytest.approx(-thickness)
    assert max(y for _, y, _ in positions) == pytest.approx(bearing)
    for side_x in (-width / 2, width / 2):
        assert any(x == pytest.approx(side_x) and z > height / 2
                   for x, _, z in positions)
    assert not any(-width / 2 + 1e-8 < x < width / 2 - 1e-8 and y > 0 and z > 0
                   for x, y, z in positions)


def test_hu_and_huc_turn_the_mounting_wings_in_opposite_directions():
    exposed = _positions_in("HU212-3")
    concealed = _positions_in("HUC212-3")
    assert max(abs(x) for x, _, _ in exposed) == pytest.approx(4.6875 / 2 + 0.075 + 1.25)
    assert max(abs(x) for x, _, _ in concealed) == pytest.approx(4.6875 / 2 + 0.075)
    assert any(abs(x) < 4.6875 / 2 and y < 0 and z > 5 for x, y, z in concealed)
    assert not any(abs(x) < 4.6875 / 2 and y < 0 and z > 5 for x, y, z in exposed)


@pytest.mark.parametrize("family,width,depth,expected_part", [
    ("LUS", 1.5, 3.5, "LUS24"),
    ("LUSZ", 1.5, 5.5, "LUS26Z"),
    ("LUS", 1.5, 7.25, "LUS28"),
    ("LUSZ", 1.5, 9.25, "LUS210Z"),
    ("LUSZ", 1.25, 7.25, "LUS28Z"),
    ("LUS", 1.5, 11.25, "LUS210"),
    ("LUS", 2.0, 11.875, "LUS210-2"),
    ("LUS", 2.5, 11.875, "LUS210-2"),
    ("LUS", 3.0, 7.25, "LUS28-2"),
    ("LUS", 3.5, 7.25, "LUS48"),
    ("HUC", 4.5, 11.25, "HUC212-3"),
    ("IUS", 2.3125, 11.875, "IUS2.37/11.88"),
    ("IUS", 2.5, 11.875, "IUS2.56/11.88"),
    ("LSSR", 1.75, 11.875, "LSSR1.81Z"),
    ("LSSR", 2.3125, 11.875, "LSSR2.37Z"),
])
def test_family_resolves_a_catalog_size_without_scaling_the_stamping(family, width, depth,
                                                                   expected_part):
    assert hanger_mesh(family, member_width_in=width, member_depth_in=depth) == (
        hanger_mesh(expected_part))


def test_authored_stamping_does_not_change_when_member_depth_changes():
    assert hanger_mesh("LUS28Z", member_width_in=1.5, member_depth_in=11.25) == (
        hanger_mesh("LUS28Z", member_width_in=1.5, member_depth_in=7.25))


def test_ius_has_waisted_cheeks_and_locator_tabs_over_the_header():
    positions = _positions_in("IUS2.56/11.88")
    side_x = 2.625 / 2
    cheek_y = {round(y, 5) for x, y, z in positions
               if x == pytest.approx(side_x) and 0 < z < 11}
    assert 2.0 in cheek_y
    assert any(0 < y < 1 for y in cheek_y)
    assert any(y < -0.048 and z > 11 for _, y, z in positions)


@pytest.mark.parametrize("pitch", [-6 / 12, 6 / 12])
def test_lssr_adjusts_its_seat_while_mounting_wings_remain_plumb(pitch):
    slope = atan(pitch)
    positions = _positions_in("LSSR2.37Z", slope_radians=slope)
    width = 2.375
    bearing_reach = 4.125
    assert any(x == pytest.approx(width / 2)
               and y == pytest.approx(bearing_reach * cos(slope))
               and z == pytest.approx(bearing_reach * sin(slope)) for x, y, z in positions)
    # A face wing still has both edges in the support plane, even on a raked joist.
    face_x = width / 2 + 0.048 + 1.25
    wing = [(y, z) for x, y, z in positions if x == pytest.approx(face_x)]
    assert {round(y, 5) for y, _ in wing} == {-0.048, 0.0}
    assert len({round(z, 5) for _, z in wing}) == 2
    assert any(abs(x) == pytest.approx(width / 2) and y > 0
               and z == pytest.approx(y * tan(slope)) for x, y, z in positions)


def test_lsc_is_one_sided_and_keeps_the_published_developed_length():
    positions = _positions_in("LSCZ")
    assert max(y for _, y, _ in positions) == pytest.approx(6.75)
    assert max(z for _, _, z in positions) == pytest.approx(11.0625 - 6.75)
    assert min(x for x, _, _ in positions) == pytest.approx(-0.75)
    assert max(x for x, _, _ in positions) == pytest.approx(0.75 + 0.048)
    sloped = _positions_in("LSCZ", slope_radians=atan(-7 / 11))
    assert any(y > 4 and z < -2 for _, y, z in sloped)
    assert any(y == 0 and z > 4 for _, y, z in sloped)


@pytest.mark.parametrize("support_width", [2.0, 3.5, 5.25])
def test_tha_straps_wrap_the_carrier_and_preserve_22_inches_of_stock(support_width):
    depth = 11.875
    positions = _positions_in("THA422", member_depth_in=depth, support_width_in=support_width)
    assert max(z for _, _, z in positions) == pytest.approx(depth)
    assert min(y for _, y, _ in positions) == pytest.approx(-support_width - 0.060)
    back_return_bottom = min(z for _, y, z in positions
                             if y == pytest.approx(-support_width - 0.060))
    return_length = depth - back_return_bottom
    assert depth + support_width + return_length == pytest.approx(22.0)
    assert any(y < 0 and z == pytest.approx(depth) for _, y, z in positions)
    assert max(y for _, y, _ in positions) == pytest.approx(1.75)


def test_unformed_tha_preserves_the_catalog_stock_height():
    positions = _positions_in("THA422")
    assert max(z for _, _, z in positions) - min(z for _, _, z in positions) == (
        pytest.approx(22.0))


@pytest.mark.parametrize("part", ["LUS28", "IUS2.56/11.88", "HU28-2Z", "HUC212-3",
                                  "HHUS410", "LSSR2.37Z", "LSCZ", "THA422"])
def test_folded_plates_are_closed_and_faces_are_non_degenerate(part):
    mesh = hanger_mesh(part)
    assert mesh is not None
    edge_counts = Counter()
    volume = 0.0
    for a, b, c in mesh.triangles:
        for start, end in ((a, b), (b, c), (c, a)):
            edge_counts[tuple(sorted((start, end)))] += 1
        p, q, r = (mesh.positions[index] for index in (a, b, c))
        u, v = ([point[i] - p[i] for i in range(3)] for point in (q, r))
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                 u[0] * v[1] - u[1] * v[0])
        assert sum(value * value for value in cross) > 1e-20
        volume += (p[0] * (q[1] * r[2] - q[2] * r[1])
                   + p[1] * (q[2] * r[0] - q[0] * r[2])
                   + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6
    assert set(edge_counts.values()) == {2}
    assert volume > 0


def test_unknown_products_and_unsupported_family_dimensions_are_not_guessed():
    assert hanger_mesh("LUS999") is None
    assert hanger_mesh("IUS2.56/13") is None
    assert hanger_mesh("LUS") is None
    assert hanger_mesh("LSSR") is None
    assert hanger_mesh("LUS", member_width_in=7.0, member_depth_in=11.25) is None
