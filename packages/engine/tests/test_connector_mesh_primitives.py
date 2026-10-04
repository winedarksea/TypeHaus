"""Closed thin steel, concave cutouts and mirrored winding survive mesh construction."""

import math
from collections import Counter

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, plate_mesh, transform_mesh


def _volume(mesh):
    return sum(
        a[0] * (b[1] * c[2] - b[2] * c[1])
        + a[1] * (b[2] * c[0] - b[0] * c[2])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
        for indices in mesh.triangles
        for a, b, c in [tuple(mesh.positions[index] for index in indices)]
    ) / 6.0


def test_concave_plate_preserves_removed_corner_and_is_closed():
    profile = ((0, 0, 0), (3, 0, 0), (3, 1, 0), (1, 1, 0), (1, 3, 0), (0, 3, 0))
    mesh = plate_mesh(profile, (0, 0, 0.05))
    assert _volume(mesh) == pytest.approx(5 * 0.05 * M_PER_IN ** 3)
    edges = Counter(tuple(sorted(pair)) for a, b, c in mesh.triangles
                    for pair in ((a, b), (b, c), (c, a)))
    assert set(edges.values()) == {2}
    for indices in mesh.triangles:
        center = [sum(mesh.positions[j][i] for j in indices) / 3 / M_PER_IN for i in (0, 1)]
        assert center[0] <= 1 or center[1] <= 1


@pytest.mark.parametrize("extrusion", [(0, 0, 0.05), (0, 0, -0.05)])
def test_plate_winding_is_outward_for_both_extrusion_directions(extrusion):
    mesh = plate_mesh(((0, 0, 0), (3, 0, 0), (3, 2, 0), (0, 2, 0)), extrusion)
    assert _volume(mesh) == pytest.approx(6 * 0.05 * M_PER_IN ** 3)


def test_reflected_placement_keeps_outward_normals_and_physical_volume():
    mesh = box_mesh((-1, -2, -3), (1, 2, 3))
    mirrored = transform_mesh(mesh, origin_m=(7, 3, 2), x_axis=(-1, 0, 0))
    assert _volume(mirrored) == pytest.approx(_volume(mesh))
    assert all(math.isfinite(value) for point in mirrored.positions for value in point)


@pytest.mark.parametrize("start", range(6))
def test_concave_perimeter_start_does_not_change_outward_winding(start):
    profile = ((0, 0, 0), (3, 0, 0), (3, 1, 0), (1, 1, 0), (1, 3, 0), (0, 3, 0))
    profile = profile[start:] + profile[:start]
    mesh = plate_mesh(profile, (0, 0, 0.05))
    assert _volume(mesh) == pytest.approx(5 * 0.05 * M_PER_IN ** 3)


def test_degenerate_plate_and_placement_raise():
    with pytest.raises(ValueError, match="extrusion"):
        plate_mesh(((0, 0, 0), (1, 0, 0), (1, 1, 0)), (1, 0, 0))
    with pytest.raises(ValueError, match="invertible"):
        transform_mesh(box_mesh((0, 0, 0), (1, 1, 1)), x_axis=(0, 1, 0))
