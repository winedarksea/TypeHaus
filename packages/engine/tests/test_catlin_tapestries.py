"""The theatre's opposed artwork stays aligned and its clips reach the fabric."""

import math

import pytest

from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import M_PER_IN


def test_opposed_tapestries_share_height_and_northing(catlin_model_ro):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    east = objects["FURN-B-PLAY-TAPESTRY"]
    west = objects["FURN-B-PLAY-TAPESTRY-W"]
    assert west.position[1] == pytest.approx(east.position[1])
    assert west.position[0] < east.position[0]
    assert west.z_m == pytest.approx(east.z_m)
    assert abs(west.rotation_degrees - east.rotation_degrees) % 360 == pytest.approx(180)
    assert west.type_ref == "FT-TAPESTRY-HUNT-80X60"
    assert east.type_ref == "FT-TAPESTRY-DRAGON-80X60"
    for fabric in (east, west):
        rod = objects[fabric.tag + "-ROD"]
        assert rod.position[1] == pytest.approx(fabric.position[1])
        assert rod.rotation_degrees == fabric.rotation_degrees
        assert rod.z_m + 3 * M_PER_IN == pytest.approx(fabric.z_m + 62.5 * M_PER_IN)


def test_clip_rings_have_outward_normals_and_connect_to_the_fabric():
    parts = model_parts("tapestry-rod-clips", 96 * M_PER_IN, 4 * M_PER_IN, 4 * M_PER_IN)
    # Each of the fourteen ring meshes has a narrow axial thickness; shafts run along x.
    rings = [part for part in parts if part["shape"] == "mesh"
             and part["size"][0] < part["size"][1] / 5]
    assert len(rings) == 14
    clips = [part for part in parts if part["shape"] == "box"
             and part["center"][2] - part["size"][2] / 2 < M_PER_IN]
    assert len(clips) == 14
    fabric_top = 0.5 * M_PER_IN  # hardware base is 71½ inches, fabric top 72 inches
    assert all(part["center"][2] - part["size"][2] / 2 <= fabric_top
               <= part["center"][2] + part["size"][2] / 2 for part in clips)
    for ring in rings:
        mesh = ring["mesh"]
        for triangle in mesh["triangles"]:
            a, b, c = [mesh["positions"][index] for index in triangle]
            ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
                      ab[0] * ac[1] - ab[1] * ac[0])
            assert math.hypot(*normal) > 0
            assert sum(n * f for n, f in zip(mesh["normals"][triangle[0]], normal, strict=True)) > 0
