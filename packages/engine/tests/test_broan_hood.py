"""Manufacturer silhouette and export contract for the ductless BWP1304SS."""

import ifcopenshell
import pytest

from typehaus.emit.ifc.placeable_parts import parts_representation
from typehaus.model.placeable_symbols import model_parts

INCH = 0.0254
SYMBOL = "broan-bwp1304ss-recirculating"


@pytest.fixture
def hood_parts():
    return model_parts(SYMBOL, 29.5 * INCH, 19.6875 * INCH, 40.375 * INCH)


def test_canopy_tapers_to_wall_backed_manufacturer_flue(hood_parts):
    canopy = next(part for part in hood_parts if part["shape"] == "mesh")
    positions = canopy["mesh"]["positions"]
    lower = {point for point in positions if point[2] == pytest.approx(1.375 * INCH)}
    upper = {point for point in positions if point[2] == pytest.approx(9.6875 * INCH)}
    assert len(lower) == len(upper) == 4
    assert max(p[0] for p in lower) - min(p[0] for p in lower) == pytest.approx(29.5 * INCH)
    assert max(p[0] for p in upper) - min(p[0] for p in upper) == pytest.approx(8.75 * INCH)
    assert max(p[1] for p in upper) - min(p[1] for p in upper) == pytest.approx(6.75 * INCH)
    assert max(p[1] for p in lower) == max(p[1] for p in upper)
    # Sloping front and sides must have upward-facing normals, not inverted surfaces.
    sloped = [n for n in canopy["mesh"]["normals"] if 0 < n[2] < 1]
    assert sloped
    assert any(n[1] < 0 for n in sloped)
    assert any(n[0] > 0 for n in sloped) and any(n[0] < 0 for n in sloped)


def test_lights_filters_and_recirculation_returns_are_visible(hood_parts):
    lights = [p for p in hood_parts if p["color"] == "lamp"]
    filters = [p for p in hood_parts if p["color"] == "metal"]
    assert len(lights) == len(filters) == 2
    assert all(p["center"][1] < 0 for p in lights)
    returns = [p for p in hood_parts if p["color"] == "metal-black"
               and p["center"][2] > 35 * INCH]
    assert {1 if p["center"][0] > 0 else -1 for p in returns} == {-1, 1}
    assert max(p["center"][2] + p["size"][2] / 2 for p in hood_parts) == pytest.approx(
        40.375 * INCH)


def test_all_hood_parts_export_to_ifc(hood_parts):
    file = ifcopenshell.file(schema="IFC4")
    context = file.create_entity("IfcGeometricRepresentationContext", CoordinateSpaceDimension=3)
    representation = parts_representation(file, context, hood_parts, (0, 0), 0, 66 * INCH)
    assert len(representation.Items) == len(hood_parts)
    assert all(item.is_a("IfcTriangulatedFaceSet") for item in representation.Items)
