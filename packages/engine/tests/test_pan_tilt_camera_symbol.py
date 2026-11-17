"""Camera envelope, optical layout, and closed export geometry."""

from collections import Counter

import numpy as np
import pytest

from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import model_parts


def test_camera_catalog_orientation_mount_and_shared_geometry():
    from houses.catlin.plan.smart_home import MAIN_ELEMENTS
    from houses.catlin.plan.smart_home_types import DEVICE_TYPES

    camera = next(item for item in DEVICE_TYPES if item.tag == "ED-T-CAM-PANTILT")
    dimensions = (*(length.meters for length in camera.footprint), camera.height.meters)
    assert dimensions == pytest.approx((.151, .125, .202))
    instance = next(item for item in MAIN_ELEMENTS if item.tag == "ED-M-CAM-PORCH")
    assert instance.mount.elevation.meters + camera.height.meters == pytest.approx(105.75 * .0254)
    parts = model_parts(camera.model_representation.symbol, *dimensions)
    wire_parts = _symbol_geometry(camera, camera.footprint)["model_parts"]
    assert [part["mesh"] for part in wire_parts] == [part["mesh"] for part in parts]
    # Two panorama lenses above a larger tracking lens, all looking toward local -Y.
    bezels = [part for part in parts if part["color"] == "device-accent"]
    assert len(bezels) == 3
    assert sorted(part["center"][0] for part in bezels)[1] == 0
    assert all(part["center"][1] < 0 for part in bezels)
    tracking = min(bezels, key=lambda part: part["center"][2])
    assert all(tracking["size"][0] > part["size"][0] for part in bezels if part is not tracking)


def test_camera_meshes_are_closed_outward_and_inside_envelope():
    dimensions = np.array((.151, .125, .202))
    parts = model_parts("reolink-omvi-3i-ceiling", *dimensions)
    all_points = np.concatenate([part["mesh"]["positions"] for part in parts])
    assert all_points.min(axis=0) == pytest.approx((-.151 / 2, -.125 / 2, 0))
    assert all_points.max(axis=0) == pytest.approx((.151 / 2, .125 / 2, .202))
    for part in parts:
        mesh = part["mesh"]
        triangles = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        normals = np.asarray(mesh["normals"])[np.asarray(mesh["triangles"])]
        assert np.all(np.sum(cross[:, None, :] * normals, axis=2) > 0)
        assert np.sum(triangles[:, 0] * np.cross(triangles[:, 1], triangles[:, 2])) > 0
        edges = Counter()
        for triangle in triangles:
            vertices = [tuple(np.round(vertex, 12)) for vertex in triangle]
            for a, b in zip(vertices, (*vertices[1:], vertices[0]), strict=True):
                edges[tuple(sorted((a, b)))] += 1
        assert set(edges.values()) == {2}
