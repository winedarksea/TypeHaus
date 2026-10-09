"""The shared framed IFC preserves the physical winder oak and plywood prisms."""

import ifcopenshell
import pytest
from shapely.geometry import Polygon

pytestmark = pytest.mark.slow


def test_ifc_contains_the_same_oak_and_plywood_prisms(catlin_model_ro, catlin_ifc_path):
    stair = next(s for s in catlin_model_ro.stairs if s.tag == "ST-S2A")
    file = ifcopenshell.open(str(catlin_ifc_path))
    products = {product.Name: product for product in file.by_type('IfcProduct') if product.Name}
    for member in (m for m in stair.members if m.category in {'winder', 'stair_subdeck'}):
        product = products[f'{stair.tag}/{member.child_key}']
        body = next(rep for rep in product.Representation.Representations
                    if rep.RepresentationIdentifier == 'Body')
        [extrusion] = body.Items
        ring = [tuple(point.Coordinates) for point in extrusion.SweptArea.OuterCurve.Points[:-1]]
        assert Polygon(ring).equals(Polygon(member.plan_outline))
        assert extrusion.Position.Location.Coordinates[2] == pytest.approx(member.z0_m)
        assert extrusion.Depth == pytest.approx(member.z1_m - member.z0_m)
        if member.category == 'stair_subdeck':
            assert product.is_a('IfcPlate')
