"""Catalog dimensions and member openings, without resolving a house."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.bases_caps import base_cap_mesh
from typehaus.resolve.geometry_ir import GMesh


def _mesh(part: str, **kwargs: float) -> GMesh:
    mesh = base_cap_mesh(part, **kwargs)
    assert mesh is not None
    return mesh


def _bounds_in(mesh: GMesh) -> tuple[tuple[float, ...], tuple[float, ...]]:
    return tuple(min(point[axis] for point in mesh.positions) / M_PER_IN for axis in range(3)), (
        tuple(max(point[axis] for point in mesh.positions) / M_PER_IN for axis in range(3)))


def _crossings_in(mesh: GMesh, axis: int, fixed_coordinates_in: tuple[float, float]) -> list[float]:
    """Intersect a line with triangle faces to measure the actual clear opening."""
    transverse = tuple(index for index in range(3) if index != axis)
    point = tuple(value * M_PER_IN for value in fixed_coordinates_in)
    crossings = []
    for triangle in mesh.triangles:
        a, b, c = (mesh.positions[index] for index in triangle)
        u = tuple(b[index] - a[index] for index in transverse)
        v = tuple(c[index] - a[index] for index in transverse)
        delta = tuple(point[i] - a[index] for i, index in enumerate(transverse))
        determinant = u[0] * v[1] - u[1] * v[0]
        if abs(determinant) < 1e-12:
            continue
        weight_b = (delta[0] * v[1] - delta[1] * v[0]) / determinant
        weight_c = (u[0] * delta[1] - u[1] * delta[0]) / determinant
        if min(weight_b, weight_c) >= -1e-9 and weight_b + weight_c <= 1.0 + 1e-9:
            crossings.append((a[axis] + weight_b * (b[axis] - a[axis])
                              + weight_c * (c[axis] - a[axis])) / M_PER_IN)
    return sorted({round(value, 7) for value in crossings})


@pytest.mark.parametrize(("part", "dimensions_in"), (
    ("ABU44", (3.0, 3.5625 + 2 * 0.1046, 5.5)),
    ("ABU66SS", (5.0, 5.5 + 2 * 0.1345, 6.0625)),
    ("CBSQ66-SDS2", (5.5, 5.5 + 2 * 0.1345, 15.625)),
    ("PC6Z", (7.0, 5.5 + 2 * 0.0598, 3.0 + 1.625 + 0.0598)),
    ("CCQ46SDS2.5", (11.0, 3.625 + 2 * 0.1793, 15.5)),
    ("AC6Z", (8.5, 5.5 + 2 * 0.0478, 5.5)),
    ("ACE6Z", (6.5 + 0.0478, 5.5 + 2 * 0.0478, 5.5)),
    ("HL33HDG", (2.5, 3.25 + 0.1793, 3.25 + 0.1793)),
    ("HL35HDG", (5.0, 3.25 + 0.1793, 3.25 + 0.1793)),
    ("L50Z", (5.0, 2.375 + 0.0598, 1.375 + 0.0598)),
))
def test_manufactured_dimensions(part: str, dimensions_in: tuple[float, float, float]) -> None:
    lower, upper = _bounds_in(_mesh(part))
    assert tuple(b - a for a, b in zip(lower, upper, strict=True)) == pytest.approx(dimensions_in)


@pytest.mark.parametrize(("part", "width_in", "strap_in"), (
    ("ABU44Z", 3.5625, 0.1046), ("ABU66SS", 5.5, 0.1345),
))
def test_abu_has_open_u_channel_and_one_inch_raised_seat(
    part: str, width_in: float, strap_in: float,
) -> None:
    mesh = _mesh(part)
    assert _crossings_in(mesh, 1, (0.0, 3.0)) == pytest.approx(
        [-width_in / 2 - strap_in, -width_in / 2, width_in / 2, width_in / 2 + strap_in])
    assert _crossings_in(mesh, 0, (0.0, 3.0)) == []
    assert max(_crossings_in(mesh, 2, (0.0, 0.0))) == 1.0
    # Along the underside of the pan, only its end aprons cross the ray: the anchor bay
    # is an air space, not a 1" high black plinth.
    crossings = _crossings_in(mesh, 0, (0.0, 0.5))
    assert len(crossings) == 4
    assert crossings[1] < 0.0 < crossings[2]
    assert _bounds_in(mesh)[0][2] == 0.0


def test_cbsq_keeps_cast_in_u_strap_and_open_post_clearance() -> None:
    mesh = _mesh("CBSQ66-SDS2HDG")
    lower, upper = _bounds_in(mesh)
    assert lower[2] == -6.875
    assert upper[2] == 8.75
    assert _crossings_in(mesh, 1, (0.0, 4.0)) == pytest.approx(
        [-2.75 - 0.1345, -2.75, 2.75, 2.75 + 0.1345])
    assert _crossings_in(mesh, 0, (0.0, 4.0)) == []
    assert _crossings_in(mesh, 0, (0.0, -3.0)) == []
    assert max(_crossings_in(mesh, 2, (0.0, 0.0))) == 1.0


def test_ccq_has_separate_beam_and_post_openings_and_bearing_plate() -> None:
    mesh = _mesh("CCQ46SDS2.5")
    assert _crossings_in(mesh, 1, (0.0, 3.0)) == pytest.approx(
        [-1.8125 - 0.1793, -1.8125, 1.8125, 1.8125 + 0.1793])
    assert _crossings_in(mesh, 0, (0.0, -3.0)) == pytest.approx(
        [-2.75 - 0.1793, -2.75, 2.75, 2.75 + 0.1793])
    assert _crossings_in(mesh, 0, (0.0, 3.0)) == []
    assert _crossings_in(mesh, 2, (0.0, 0.0)) == pytest.approx([-0.1793, 0.0])


def test_pc6_post_flange_is_narrower_than_its_beam_leaf() -> None:
    mesh = _mesh("PC6Z")
    assert len(_crossings_in(mesh, 1, (0.0, -1.0))) == 4
    assert _crossings_in(mesh, 1, (2.0, -1.0)) == []
    assert len(_crossings_in(mesh, 1, (2.0, 1.0))) == 4
    assert _crossings_in(mesh, 0, (0.0, 1.0)) == []


def test_ac_pair_can_space_pieces_without_stretching_their_leaves() -> None:
    mesh = _mesh("AC6Z", member_width_in=5.125, member_depth_in=11.25)
    lower, upper = _bounds_in(mesh)
    assert upper[0] - lower[0] == 8.5
    assert upper[2] - lower[2] == 5.5
    assert _crossings_in(mesh, 1, (0.0, 1.0)) == pytest.approx(
        [-2.5625 - 0.0478, -2.5625, 2.5625, 2.5625 + 0.0478])
    assert _crossings_in(mesh, 0, (0.0, 1.0)) == []
    assert _crossings_in(mesh, 2, (0.0, 0.0)) == []  # direct wood-to-wood bearing


def test_ace_beam_leaf_starts_at_post_end_face() -> None:
    mesh = _mesh("ACE6Z")
    assert _crossings_in(mesh, 0, (2.76, 1.0)) == pytest.approx([-2.75, 3.75])


@pytest.mark.parametrize("part", ("L50Z", "HL33HDG", "HL35HDG"))
def test_angles_leave_the_inside_quadrant_empty(part: str) -> None:
    mesh = _mesh(part)
    assert _crossings_in(mesh, 0, (0.5, 0.5)) == []
    assert len(_crossings_in(mesh, 0, (-0.01, 0.5))) == 2
    assert len(_crossings_in(mesh, 0, (0.5, -0.01))) == 2


@pytest.mark.parametrize(("plain", "coated"), (
    ("ABU44", "ABU44Z"), ("ABU66", "ABU66SS"),
    ("CBSQ66-SDS2", "CBSQ66-SDS2HDG"),
    ("CCQ46SDS2.5", "CCQ46SDS2.5HDG"), ("HL35", "HL35PC"),
))
def test_coatings_do_not_change_shape(plain: str, coated: str) -> None:
    assert _mesh(plain) == _mesh(coated)


def test_unknown_part_stays_unsupported() -> None:
    assert base_cap_mesh("SIMPLIFIED-MYSTERY-CAP") is None
