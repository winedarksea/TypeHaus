"""Sump details preserve a hollow basin, real cover penetrations, and one pit identity."""

from types import SimpleNamespace

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model.mep import Sump
from typehaus.quantities import inch, pt
from typehaus.resolve.geometry_ir import signed_volume
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.sump import VISUALIZATION, resolve_sump


def _resolve(*, sealed=True, pipes=(), hosted=True):
    sump = Sump(tag="PIT", position=pt(inch(0), inch(0)), diameter=inch(18),
                depth=inch(24), sealed_cover=sealed, host_ref="SLAB" if hosted else None)
    slab = ResolvedSolid(uid="slab", tag="SLAB", storey="B", category="slab",
                         outline=((-1, -1), (1, -1), (1, 1), (-1, 1)),
                         z0_m=-.1, z1_m=0)
    model = SimpleNamespace(solids=[slab] if hosted else [], pipe_runs=list(pipes))
    resolve_sump(model, sump, SimpleNamespace(tag="B", elevation=inch(0)))
    return model, model.solids[-1]


def _horizontal_faces(solid, z):
    mesh = solid.body_mesh
    return [Polygon([mesh.positions[i][:2] for i in face]) for face in mesh.triangles
            if all(abs(mesh.positions[i][2] - z) < 1e-9 for i in face)]


@pytest.mark.parametrize("sealed", [True, False])
def test_basin_has_a_bottom_a_cavity_and_a_separate_bolted_cover(sealed):
    model, basin = _resolve(sealed=sealed)
    assert len([solid for solid in model.solids if solid.category == "sump"]) == 1
    assert basin.material == "polyethylene"
    assert Polygon(model.solids[0].voids[0]).equals(Polygon(basin.outline))
    assert basin.z0_m == pytest.approx(-.1 - inch(24).meters)
    bottom_faces = _horizontal_faces(basin, basin.z0_m + VISUALIZATION.bottom_m)
    assert any(face.covers(Point(0, 0)) for face in bottom_faces)
    # The old cylinder billed/drew its entire water-holding capacity as solid plastic.
    volume = signed_volume(basin.body_mesh.positions, basin.body_mesh.triangles)
    envelope_volume = Polygon(basin.outline).area * (basin.z1_m - basin.z0_m)
    assert 0 < volume < .1 * envelope_volume
    cover_top = 0
    assert any(face.covers(Point(0, 0)) for face in _horizontal_faces(basin, cover_top))
    assert basin.z1_m == pytest.approx(cover_top)
    assert _horizontal_faces(basin, cover_top - VISUALIZATION.bolt_recess_m)
    radius = inch(9).meters
    assert any(abs((x*x + y*y)**.5 - radius) < 1e-9 and z < 0
               for x, y, z in basin.body_mesh.positions)


def _pipe(x=0, *, system="radon", storey="B", z=(-.2, .4)):
    return SimpleNamespace(storey=storey, system=system, path=((x, 0), (x, 0)),
                           z_m=z, diameter_m=inch(3).meters)


def test_cover_holes_follow_pipe_positions_and_sizes():
    _, basin = _resolve(pipes=[_pipe(-.08), _pipe(.08, system="sump_discharge")])
    top = 0
    faces = _horizontal_faces(basin, top)
    for x in (-.08, .08):
        assert not any(face.covers(Point(x, 0)) for face in faces)
        assert not any(face.covers(Point(x + inch(1.5).meters, 0)) for face in faces)
    assert any(face.covers(Point(0, 0)) for face in faces)


@pytest.mark.parametrize("pipe", [_pipe(z=(.1, .4)), _pipe(storey="M"),
                                   _pipe(system="vent"), _pipe(.5), _pipe(z=None)])
def test_unrelated_or_unresolved_pipes_do_not_punch_the_cover(pipe):
    _, basin = _resolve(pipes=[pipe])
    faces = _horizontal_faces(basin, 0)
    assert any(face.covers(Point(0, 0)) for face in faces)


def test_unhosted_basin_uses_storey_datum():
    model, basin = _resolve(hosted=False)
    assert len(model.solids) == 1
    assert basin.z0_m == pytest.approx(-inch(24).meters)
