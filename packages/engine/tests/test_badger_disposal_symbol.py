"""Disposal fittings must export as valid solids, including the curved elbow."""

import numpy as np
import pytest
import trimesh

from typehaus.model.placeable_symbols import model_parts


@pytest.mark.parametrize("size", [(0.1603375, 0.1603375, 0.2921), (0.3, 0.1, 0.04)])
@pytest.mark.parametrize("symbol", ["insinkerator-badger-5", "badger-5-with-dearborn-p9703wbg"])
def test_disposal_curved_parts_are_closed_outward_solids(size, symbol):
    parts = model_parts(symbol, *size)
    triangle_count = 0
    for part in parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        solid = trimesh.Trimesh(vertices=mesh["positions"], faces=mesh["triangles"])
        assert solid.is_watertight
        assert solid.is_winding_consistent
        assert solid.volume > 0
        normals = np.asarray(mesh["normals"])
        assert np.linalg.norm(normals, axis=1) == pytest.approx(1)
        corners = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        face_normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        assert np.all(np.sum(face_normals * normals[np.asarray(mesh["triangles"])[:, 0]],
                             axis=1) > 0)
        triangle_count += len(mesh["triangles"])
    assert triangle_count < 7000
