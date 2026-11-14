"""Product datums and mesh validity, without constructing another house model."""

import math

import pytest

from typehaus.model.placeable_symbols import model_parts, place_local

INCH = .0254


def _parts():
    return model_parts('toto-ap-duofit', 14.9375 * INCH, 21.25 * INCH, 13.125 * INCH)


def test_carrier_is_behind_finish_and_stands_on_floor():
    parts = _parts()
    wall = 21.25 * INCH / 2
    uprights = [p for p in parts if p.get('role') == 'carrier-upright']
    assert len(uprights) == 2
    for part in uprights:
        assert part['center'][1] - part['size'][1] / 2 > wall
        assert part['center'][2] - part['size'][2] / 2 == pytest.approx(-3 * INCH)
        assert part['center'][2] + part['size'][2] / 2 == pytest.approx(42.3125 * INCH)
    cistern = next(p for p in parts if p.get('role') == 'concealed-cistern')
    assert cistern['center'][1] - cistern['size'][1] / 2 > wall
    plate = next(p for p in parts if p.get('role') == 'flush-plate')
    assert plate['size'] == pytest.approx((9.5 * INCH, .375 * INCH, 6.25 * INCH))
    assert plate['center'][2] - plate['size'][2] / 2 > 13.125 * INCH
    assert len([p for p in parts if p.get('role') == 'flush-button']) == 2


def test_drop_meets_existing_floor_port_and_rotates_with_fixture():
    drop = next(p for p in _parts() if p.get('role') == 'carrier-waste-drop')
    bottom = drop['center'][2] - drop['size'][2] / 2
    assert (*drop['center'][:2], bottom) == pytest.approx((0, 13.875 * INCH, -3 * INCH))
    # Same local-frame transform used by the viewer/export consumers.
    assert place_local([drop['center'][:2]], (2., 3.), 180)[0] == pytest.approx(
        (2., 3. - 13.875 * INCH))


def test_china_has_full_product_envelope_and_finite_nondegenerate_meshes():
    parts = _parts()
    china = parts[0]
    assert china['size'] == pytest.approx((14.9375 * INCH, 21.25 * INCH, 13.125 * INCH))
    for part in parts:
        if 'mesh' not in part:
            continue
        mesh = part['mesh']
        assert all(math.isfinite(v) for point in mesh['positions'] for v in point)
        for normal in mesh['normals']:
            assert sum(v * v for v in normal) == pytest.approx(1.)
        for triangle in mesh['triangles']:
            assert len(set(triangle)) == 3
            assert all(0 <= index < len(mesh['positions']) for index in triangle)


def test_ifc_exports_the_complete_assembly_as_tessellated_parts():
    import ifcopenshell

    from typehaus.emit.ifc.architectural import is_parts_fixture
    from typehaus.emit.ifc.placeable_parts import parts_representation

    assert is_parts_fixture("toto-ap-duofit")
    document = ifcopenshell.file(schema="IFC4")
    context = document.create_entity("IfcGeometricRepresentationContext")
    parts = _parts()
    representation = parts_representation(document, context, parts, (0, 0), 180, 3 * INCH)
    assert len(representation.Items) == len(parts)
    coordinates = [p for item in representation.Items for p in item.Coordinates.CoordList]
    assert min(p[2] for p in coordinates) == pytest.approx(0)
    assert max(p[2] for p in coordinates) == pytest.approx(45.3125 * INCH)
    assert min(p[1] for p in coordinates) < -21.25 * INCH / 2
