"""French drains carry a round pipe and a constant-depth, continuously sloping trench."""

import math

import pytest

from typehaus.model import ft, inch, pt
from typehaus.model.structure import DrainTile, FrenchDrain
from typehaus.resolve.drain_tile import PIPE_BEDDING_M
from typehaus.resolve.drainage import _segment_inverts
from typehaus.resolve.french_drain_geometry import french_drain_solids
from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.sweep import sweep_legs
from typehaus.takeoff.framing import solid_volume_m3


@pytest.mark.parametrize("fall_inches", [0, 1, 28, -12])
@pytest.mark.parametrize("tile", [DrainTile(diameter=inch(4)), None])
def test_trench_depth_and_volume_do_not_grow_with_fall(fall_inches, tile):
    drain = FrenchDrain(
        uid="FDGEOMETRY", tag="FD-TEST", path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
        invert=ft(-4), end_invert=ft(-4) - inch(fall_inches),
        trench_width=inch(6), trench_depth=inch(8), tile=tile)
    path = [point.xy_m for point in drain.path]
    inverts = _segment_inverts(path, drain.invert.meters, drain.end_invert.meters)
    solids = french_drain_solids(drain, "basement", path, inverts)
    trench, *pipes = solids
    mesh = trench.body_mesh
    assert mesh is not None
    assert len(mesh.positions) == 8, "a sloping trench needs no intermediate level steps"
    assert signed_volume(mesh.positions, mesh.triangles) > 0, "outward mesh winding"
    for bottom, top in zip(mesh.positions[:4], mesh.positions[4:], strict=True):
        assert top[:2] == bottom[:2]
        assert top[2] - bottom[2] == pytest.approx(drain.trench_depth.meters)
        ratio = bottom[0] / ft(10).meters
        assert bottom[2] == pytest.approx(inverts[0] + ratio * (inverts[1] - inverts[0]))
    assert solid_volume_m3(trench) == pytest.approx(
        ft(10).meters * drain.trench_width.meters * drain.trench_depth.meters)
    if tile is None:
        assert pipes == []
        return
    pipe, = pipes
    sweep = pipe.sweep
    assert sweep is not None
    radius = tile.diameter.meters / 2
    assert len(sweep.profile) >= 8
    assert [math.hypot(u, v) for u, v in sweep.profile] == pytest.approx(
        [radius] * len(sweep.profile))
    assert [point[2] for point in sweep.path] == pytest.approx(
        [invert + PIPE_BEDDING_M + radius for invert in inverts])
    for leg in sweep_legs(sweep):
        for ring in leg:
            assert all(pipe.z0_m <= point[2] <= pipe.z1_m for point in ring)


def test_bent_open_run_keeps_distance_weighted_fall_and_skips_duplicate_vertices():
    drain = FrenchDrain(
        uid="FDBENTTEST", tag="FD-BENT",
        path=(pt(ft(0), ft(0)), pt(ft(2), ft(0)), pt(ft(2), ft(0)), pt(ft(2), ft(8))),
        invert=ft(-4), end_invert=ft(-5), trench_width=inch(6), trench_depth=inch(8),
        tile=DrainTile(diameter=inch(4)))
    path = [point.xy_m for point in drain.path]
    inverts = _segment_inverts(path, drain.invert.meters, drain.end_invert.meters)
    solids = french_drain_solids(drain, "basement", path, inverts)
    pipes = [solid for solid in solids if solid.sweep is not None]
    assert len(pipes) == 2, "an open run has no phantom closing segment"
    first, second = (pipe.sweep for pipe in pipes)
    assert first.path[-1] == second.path[0]
    assert first.path[0][2] - first.path[-1][2] == pytest.approx(inch(2.4).meters)
    assert second.path[0][2] - second.path[-1][2] == pytest.approx(inch(9.6).meters)
