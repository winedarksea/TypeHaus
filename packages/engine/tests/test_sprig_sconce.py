"""The selected Sprig retains its published silhouette and usable export solids."""

import pytest
import trimesh

from typehaus.model.placeable_symbols import model_parts

INCH = .0254


def test_sprig_has_round_canopy_five_inch_head_and_downward_lens():
    parts = model_parts("sconce-wac-sprig", 4.375 * INCH, 9.875 * INCH, 8 * INCH)
    canopy = parts[0]
    assert canopy["size"] == pytest.approx((4.375 * INCH, 1.125 * INCH, 4.375 * INCH))
    assert canopy["center"][2] == pytest.approx(4.375 / 2 * INCH)
    head = parts[1]
    assert head["size"][:2] == pytest.approx((1.125 * INCH, 1.125 * INCH))
    assert head["center"][2] + head["size"][2] / 2 == pytest.approx(8 * INCH)
    lens = next(part for part in parts if part["color"] == "lamp")
    assert lens["center"][2] - lens["size"][2] / 2 == pytest.approx(3 * INCH)
    assert lens["center"][2] + lens["size"][2] / 2 == pytest.approx(
        head["center"][2] - head["size"][2] / 2)
    assert head["center"][1] - head["size"][1] / 2 == pytest.approx(-9.875 / 2 * INCH)
    assert {part["color"] for part in parts} == {"metal-black", "screen", "lamp"}


def test_sprig_meshes_are_closed_with_consistent_outward_normals():
    for part in model_parts("sconce-wac-sprig", 4.375 * INCH, 9.875 * INCH, 8 * INCH):
        if "mesh" not in part:
            continue
        mesh = trimesh.Trimesh(vertices=part["mesh"]["positions"],
                               faces=part["mesh"]["triangles"])
        assert mesh.is_watertight
        assert mesh.is_winding_consistent
        assert mesh.volume > 0


def test_catlin_uses_the_sprig_for_both_switching_variants(catlin_plan):
    types = {item.tag: item for item in catlin_plan.library.electrical_device_types}
    for tag in ("ED-T-LT-SCONCE-SPOT", "ED-T-LT-SPOT-SW"):
        product = types[tag]
        assert product.plan_symbol == "sconce-wac-sprig"
        assert product.product_ref == "PROD-WAC-BL-23210-BK"
        assert tuple(d.meters for d in product.footprint) == pytest.approx(
            (4.375 * INCH, 9.875 * INCH))
