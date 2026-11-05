"""Every derived duct part and hanger is one drawn, closed product solid (decision #114)."""

from __future__ import annotations

import pytest

m3d = pytest.importorskip("manifold3d")

from typehaus.resolve.duct_part_solids import parse_section  # noqa: E402
from typehaus.resolve.solid_categories import solid_category  # noqa: E402
from typehaus.solids3d.convert import mesh_manifold  # noqa: E402

_CATEGORIES = ("duct_fitting", "duct_damper", "duct_connector", "duct_support")


def test_sections_parse_as_ordered():
    assert parse_section("4in").is_round
    rect = parse_section("18x8")
    assert (round(rect.width / 0.0254), round(rect.depth / 0.0254)) == (18, 8)
    assert parse_section("none") is None and parse_section(None) is None


def test_one_closed_solid_per_non_integral_part_and_hanger(catlin_model_ro):
    model = catlin_model_ro
    drawn = [s for s in model.solids if s.category in _CATEGORIES]
    expected = (sum(1 for p in model.duct_parts if not p.integral)
                + len(model.duct_supports))
    assert expected and len(drawn) == expected
    assert all(s.derived and s.body_mesh is not None and s.host_ref for s in drawn)
    assert len({s.uid for s in drawn}) == len(drawn)
    assert {solid_category(c).collision for c in _CATEGORIES} == {None}
    bad = []
    for solid in drawn:
        manifold = mesh_manifold(solid.body_mesh.positions, solid.body_mesh.triangles)
        if manifold.status() != m3d.Error.NoError or manifold.volume() <= 0:
            bad.append(solid.tag)
    assert not bad, bad[:10]
    named = {p.product_ref for p in model.duct_parts if p.product_ref and not p.integral}
    assert named <= {s.product for s in drawn}
