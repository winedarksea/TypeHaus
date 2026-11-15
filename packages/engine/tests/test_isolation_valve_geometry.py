"""Small synthetic hosts isolate geometry and orientation from the whole-house fixture."""

from dataclasses import replace
from math import isfinite

import pytest

from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.isolation_valve_geometry import host_pipe_frame, isolation_valve_solid
from typehaus.resolve.model import ResolvedPipeRun


@pytest.fixture
def host():
    return ResolvedPipeRun(uid="pipe", tag="PR-TEST", storey="main", system="water_cold",
        path=((-1., 0.), (1., 0.)), diameter_m=0.0254, z_start_m=0., z_end_m=0.,
        z_m=(0., 0.), length_m=2.)


def _solid(host, center=(0., 0., 0.)):
    return isolation_valve_solid(uid="valve", tag="PA-TEST", storey="main", category="shutoff",
                                 center=center, host=host)


@pytest.mark.parametrize(("path", "elevations", "axis"), [
    (((-1., 0.), (1., 0.)), (0., 0.), (1., 0., 0.)),
    (((0., -1.), (0., 1.)), (0., 0.), (0., 1., 0.)),
    (((0., 0.), (0., 0.)), (-1., 1.), (0., 0., 1.)),
    (((1., 0.), (-1., 0.)), (0., 0.), (-1., 0., 0.)),
    (((-1., 0.), (1., 0.)), (-1., 1.), (2 ** -.5, 0., 2 ** -.5)),
])
def test_pipe_frame_is_orthonormal_and_follows_the_host(host, path, elevations, axis):
    frame = host_pipe_frame(replace(host, path=path, z_m=elevations), (0., 0., 0.))
    assert frame[0] == pytest.approx(axis)
    for i in range(3):
        for j in range(3):
            assert sum(a * b for a, b in zip(frame[i], frame[j], strict=True)) == pytest.approx(
                1. if i == j else 0., abs=1e-12)


def test_frame_uses_nearest_3d_leg_and_ignores_duplicate_vertices(host):
    riser = replace(host, path=((0., 0.), (0., 0.), (0., 0.), (2., 0.)),
                    z_m=(-2., -2., 0., 0.))
    assert host_pipe_frame(riser, (0., 0., -1.))[0] == (0., 0., 1.)
    assert host_pipe_frame(riser, (1., 0., 0.))[0] == (1., 0., 0.)


def test_authored_elevation_can_orient_on_a_host_without_elevations(host):
    assert host_pipe_frame(replace(host, z_m=None), (0., 0., 4.))[0] == (1., 0., 0.)


def test_valve_mesh_scales_with_bore_and_translates_without_changing_shape(host):
    original = _solid(host).body_mesh
    enlarged = _solid(replace(host, diameter_m=host.diameter_m * 2), (3., 4., 5.)).body_mesh
    assert original.triangles == enlarged.triangles
    for point, scaled in zip(original.positions, enlarged.positions, strict=True):
        expected = tuple(2 * p + c for p, c in zip(point, (3, 4, 5), strict=True))
        assert scaled == pytest.approx(expected)


@pytest.mark.parametrize("vertical", [False, True])
def test_mesh_has_outward_faces_unit_normals_and_matching_bounds(host, vertical):
    if vertical:
        host = replace(host, path=((0., 0.), (0., 0.)), z_m=(-1., 1.))
    solid = _solid(host)
    mesh = solid.body_mesh
    assert signed_volume(mesh.positions, mesh.triangles) > 0
    assert all(isfinite(value) for point in mesh.positions for value in point)
    for normal in mesh.normals:
        assert sum(value * value for value in normal) == pytest.approx(1.)
    for triangle in mesh.triangles:
        a, b, c = [mesh.positions[i] for i in triangle]
        ab = tuple(y - x for x, y in zip(a, b, strict=True))
        ac = tuple(y - x for x, y in zip(a, c, strict=True))
        cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        assert sum(value * value for value in cross) > 0
        assert sum(x * n for x, n in zip(cross, mesh.normals[triangle[0]], strict=True)) > 0
    assert solid.z0_m == min(p[2] for p in mesh.positions)
    assert solid.z1_m == max(p[2] for p in mesh.positions)
    assert solid.outline[0] == tuple(min(p[i] for p in mesh.positions) for i in range(2))
    assert solid.outline[2] == tuple(max(p[i] for p in mesh.positions) for i in range(2))
