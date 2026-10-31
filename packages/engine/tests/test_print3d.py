"""`haus print3d` on the starter house: valid objects that fit the bed, byte-identical runs."""

from __future__ import annotations

import re
import zipfile

import numpy as np
import pytest

m3d = pytest.importorskip("manifold3d")

from typehaus.print3d.build import build_print  # noqa: E402
from typehaus.print3d.policy import PrintSettings, Treatment  # noqa: E402
from typehaus.print3d.threemf import write_3mf  # noqa: E402

_OBJECT = re.compile(r'<object id="\d+" type="model" name="([^"]+)"><mesh><vertices>(.*?)'
                     r"</vertices><triangles>(.*?)</triangles>")


@pytest.fixture(scope="module")
def starter_run(starter_dir):
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(starter_dir).plan)
    return model, build_print(model, PrintSettings())


def _objects(path):
    text = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    for name, vertices, triangles in _OBJECT.findall(text):
        points = np.array(re.findall(r'x="([^"]+)" y="([^"]+)" z="([^"]+)"', vertices),
                          dtype=float)
        faces = np.array(re.findall(r'v1="(\d+)" v2="(\d+)" v3="(\d+)"', triangles),
                         dtype=np.uint32)
        mesh = m3d.Mesh64(vert_properties=points, tri_verts=faces)
        mesh.merge()
        yield name, m3d.Manifold(mesh)


def test_every_object_reimports_as_a_valid_solid_that_fits_the_bed(starter_run, tmp_path):
    _, run = starter_run
    assert run.pieces
    path = write_3mf(tmp_path / "house.3mf", run.pieces, "starter")
    settings = PrintSettings()
    usable = [side - 2 * settings.margin_mm for side in settings.bed_mm]
    for (name, solid), piece in zip(_objects(path), run.pieces, strict=True):
        assert solid.status() == m3d.Error.NoError, name
        assert solid.volume() > 0, name
        assert sorted(piece.dims_mm[:2]) <= sorted(usable[:2]) and piece.dims_mm[2] <= usable[2]


def test_two_runs_write_identical_bytes(starter_run, tmp_path):
    model, run = starter_run
    again = build_print(model, PrintSettings())
    first = write_3mf(tmp_path / "a.3mf", run.pieces, "starter").read_bytes()
    assert first == write_3mf(tmp_path / "b.3mf", again.pieces, "starter").read_bytes()


def test_a_dropped_kind_never_prints(starter_run):
    _, run = starter_run
    assert run.dropped["framing"] > 0
    assert "framing" not in run.kept and "opening" not in run.kept
    assert all(result.item.treatment is not Treatment.DROP for result in run.thickened)
