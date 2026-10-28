"""The selected roof deck, film geometry and purchasing contract."""

import math
import tomllib
from pathlib import Path

import pytest

from typehaus.emit.gltf.palette import _material_finish_color
from typehaus.resolve.geometry_roofs import roof_parts
from typehaus.takeoff.envelope import envelope_layer_takeoff


@pytest.mark.parametrize("tag,deck_material,membrane_material,film_in", [
    ("RF-HOUSE", "cdx-plywood", "roof-adhered-butyl-ht", 0.030),
    ("RF-GARAGE", "struct-1-plywood", "roof-adhered-asphalt-ht", 0.040),
    ("RF-BW-CANOPY", "struct-1-plywood", "roof-adhered-asphalt-ht", 0.040),
])
def test_roof_deck_and_physical_membrane(catlin_model_ro, tag, deck_material,
                                         membrane_material, film_in):
    model = catlin_model_ro
    roof = next(r for r in model.roofs if r.tag == tag)
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    deck = next(layer for layer in assembly.layers if layer.function.value == "sheathing")
    membrane = next(layer for layer in assembly.layers if layer.function.value == "membrane")
    assert deck.material_ref == deck_material
    assert deck.thickness.inches == pytest.approx(19 / 32)
    assert membrane.material_ref == membrane_material
    assert membrane.thickness.inches == pytest.approx(film_in)

    mesh = next(p for p in roof_parts(roof, assembly) if p.key == "layer:membrane").solids[0]
    # Each top triangle is followed by its reversed bottom triangle. The separation
    # projected on the surface normal must equal the film, even at the mitred ridge.
    for index in range(0, 24, 6):
        a, b, c, bottom = mesh.positions[index:index + 4]
        ab = tuple(y - x for x, y in zip(a, b, strict=True))
        ac = tuple(y - x for x, y in zip(a, c, strict=True))
        normal = (ab[1]*ac[2] - ab[2]*ac[1], ab[2]*ac[0] - ab[0]*ac[2],
                  ab[0]*ac[1] - ab[1]*ac[0])
        length = math.sqrt(sum(n*n for n in normal))
        separation = abs(sum((x-y)*n for x, y, n in zip(a, bottom, normal, strict=True)))
        assert separation / length == pytest.approx(film_in * 0.0254, abs=1e-9)

    # The GLB path must preserve the same membrane coordinates and near-black bucket.
    from typehaus.emit.gltf.mesh import _MeshBuilder
    from typehaus.emit.gltf.roofs import _add_roof
    from typehaus.emit.ifc.roof import _shell_solids

    authored = {m.tag: m for m in model.plan.library.materials}
    builder = _MeshBuilder()
    _add_roof(builder, roof, model, authored)
    film_color = _material_finish_color(membrane_material, "membrane", authored)
    positions = next(pos for color, pos, _ in builder.buckets() if color == film_color)
    assert positions[:len(mesh.positions)] == [(x, z, -y) for x, y, z in mesh.positions]
    parts = roof_parts(roof, assembly)
    film_index = next(i for i, part in enumerate(parts) if part.key == "layer:membrane")
    shell = _shell_solids(roof, assembly)[film_index]
    assert shell == [[mesh.positions[i] for i in tri] for tri in mesh.triangles]

    material = model.plan.library.material(membrane_material)
    color = _material_finish_color(membrane_material, "membrane", {material.tag: material})
    assert color[:3] == pytest.approx((47 / 255, 49 / 255, 52 / 255))
    assert color[3] == 1.0


def test_roof_purchasing_and_thickness_qualified_rates(catlin_model_ro):
    from typehaus.cli.prices import candidate_keys

    rows = [r for r in envelope_layer_takeoff(catlin_model_ro) if r["scope"] == "roof"]
    decks = [r for r in rows if r["function"] == "sheathing"]
    films = [r for r in rows if r["function"] == "membrane"]
    assert len(decks) == len(films) == 2
    assert {r["material"] for r in films} == {
        "roof-adhered-butyl-ht", "roof-adhered-asphalt-ht"}
    expected_area = sum(r.surface_area_m2 for r in catlin_model_ro.roofs) / 0.09290304
    assert sum(r["net_area_sqft"] for r in decks) == pytest.approx(expected_area, abs=0.11)
    assert sum(r["net_area_sqft"] for r in films) == pytest.approx(expected_area, abs=0.11)
    assert all(r["thickness_in"] == 0.594 for r in decks)

    prices = tomllib.loads((Path(__file__).resolve().parents[3]
                           / "houses/catlin/prices.toml").read_text())
    for row in decks:
        key = candidate_keys(row["material"], row["thickness_in"])[0]
        assert key in prices["envelope_layers"]
    assert "roof-adhered-asphalt-ht" in prices["envelope_layers"]
    assert "roof-ice-and-water-barrier-code-minimum" not in prices["allowances"]
