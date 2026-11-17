"""DoorScope geometry must stay on the leaf when a wall rotates or reverses."""
from math import cos, sin

import pytest

from typehaus.resolve.geometry_door_viewer import DOORSCOPE_DIMENSIONS, doorscope_parts
from typehaus.resolve.geometry_ir import PartCatalogRef, signed_volume
from typehaus.resolve.geometry_slice import sweep_mesh


@pytest.mark.parametrize("angle", [0, .73, 3.141592653589793])
@pytest.mark.parametrize("exterior_sign", [-1, 1])
def test_doorscope_faces_and_closed_solids(angle, exterior_sign):
    tangent = (cos(angle), sin(angle))
    normal = (-sin(angle), cos(angle))
    center = (3, 7, 1.55)
    thickness = .04445
    dimensions = DOORSCOPE_DIMENSIONS
    parts = doorscope_parts("hardware:7", PartCatalogRef(role="viewer", name="DS2000"),
                            center, tangent, normal, thickness, exterior_sign)
    assert [part.key for part in parts] == ["hardware:7", "hardware:7:optics"]
    for part in parts:
        for solid in part.solids:
            mesh = sweep_mesh(solid)
            assert signed_volume(mesh.positions, mesh.triangles) > 0
            edges = {}
            for tri in mesh.triangles:
                for a, b in zip(tri, (*tri[1:], tri[0]), strict=True):
                    edge = tuple(sorted((a, b)))
                    edges[edge] = edges.get(edge, 0) + 1
            assert set(edges.values()) == {2}, "Every solid must be watertight"
            offsets = [(p[0]-center[0])*normal[0] + (p[1]-center[1])*normal[1]
                       for p in mesh.positions]
            assert min(abs(offset) for offset in offsets) >= thickness/2 - 1e-9
    optics = parts[1].solids
    interior = next(s for s in optics if len(s.profile) == dimensions.facets)
    exterior = next(s for s in optics if len(s.profile) == 4)
    for solid, side, width, height in (
        (interior, -exterior_sign, dimensions.screen_diameter_m, dimensions.screen_diameter_m),
        (exterior, exterior_sign, dimensions.exterior_aperture_width_m,
         dimensions.exterior_aperture_height_m),
    ):
        stations = [(p[0]-center[0])*tangent[0] + (p[1]-center[1])*tangent[1]
                    for p in solid.profile]
        heights = [p[2] for p in solid.profile]
        assert max(stations)-min(stations) == pytest.approx(width)
        assert max(heights)-min(heights) == pytest.approx(height)
        assert (max(heights)+min(heights))/2 == pytest.approx(center[2])
        assert side * sum(solid.extrude[i]*normal[i] for i in (0, 1)) > 0
