"""Exterior hoods retain an open mouth and outward-facing, exportable sheet solids."""

import numpy as np
import pytest

from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import inch


def test_hood_is_a_sloping_open_shell_with_quarter_inch_screen():
    parts = model_parts("renewaire-fa8-wall-hood", *([inch(12).meters] * 3))
    cover = next(part for part in parts if part.get("role") == "hood:rain-cover")
    vertices = np.asarray(cover["mesh"]["positions"])
    # Local +y is the wall; the rain cover drops toward the exterior (-y).
    assert vertices[vertices[:, 1].argmax(), 2] > vertices[vertices[:, 1].argmin(), 2]
    screen = [part for part in parts if part.get("role") == "hood:screen"]
    assert all(part["center"][2] < inch(1).meters for part in screen)
    wires_across_width = sorted(part["center"][0] for part in screen
                                if part["size"][0] == pytest.approx(inch(.025).meters))
    assert np.diff(wires_across_width) == pytest.approx(inch(.25).meters)
    assert len([part for part in parts if part.get("role") == "hood:side"]) == 2
    assert not any(part.get("role") == "hood:damper" for part in parts)
    for part in parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        normals = np.asarray(mesh["normals"])
        assert np.isfinite(normals).all()
        assert np.linalg.norm(normals, axis=1) == pytest.approx(1)
        triangles = np.asarray(mesh["positions"])[np.asarray(mesh["triangles"])]
        volume = np.einsum("ij,ij->i", triangles[:, 0],
                           np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6
        assert volume > 0


def test_ifc_exports_the_sloping_hood_mesh():
    import ifcopenshell

    from typehaus.emit.ifc.placeable_parts import parts_representation

    parts = model_parts("renewaire-fa8-wall-hood", *([inch(12).meters] * 3))
    model = ifcopenshell.file(schema="IFC4")
    origin = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
    context = model.createIfcGeometricRepresentationContext(
        None, "Model", 3, 1e-5, model.createIfcAxis2Placement3D(origin))
    representation = parts_representation(model, context, parts, (0, 0), 0, 0)
    assert len(representation.Items) == len(parts)
    for part, item in zip(parts, representation.Items, strict=True):
        if "mesh" in part:
            assert np.asarray(item.Coordinates.CoordList) == pytest.approx(
                np.asarray(part["mesh"]["positions"]))
