"""resolve/slab_layers.py: a slab's base course and under-slab board are drawn, never billed."""

from __future__ import annotations

import pytest

_IN = 0.0254


def _layers(model, slab_tag):
    return sorted((s for s in model.solids
                   if s.category == "sub_slab" and s.tag.startswith(slab_tag + ":")),
                  key=lambda s: -s.z1_m)


def test_the_garage_slab_stands_on_its_foam_and_stone(catlin_model_ro) -> None:
    slab = next(s for s in catlin_model_ro.solids if s.tag == "SL-G-FLOOR")
    xps, stone = _layers(catlin_model_ro, "SL-G-FLOOR")  # the 10-mil poly is not drawn
    assert (xps.material, stone.material) == ("xps", "capillary-break-stone")
    assert xps.z1_m == pytest.approx(slab.z0_m)
    assert (xps.z1_m - xps.z0_m) / _IN == pytest.approx(1.0)
    assert (stone.z1_m - stone.z0_m) / _IN == pytest.approx(4.0)
    assert stone.z1_m == pytest.approx(xps.z0_m - 0.01 * _IN)  # the poly's depth is kept
    assert all(s.derived for s in (xps, stone))


def test_flatwork_draws_its_class_5(catlin_model_ro) -> None:
    (drive,) = _layers(catlin_model_ro, "SL-DW-DRIVE")
    (walk,) = _layers(catlin_model_ro, "SL-WK-B")
    assert (drive.z1_m - drive.z0_m) / _IN == pytest.approx(8.0)
    assert (walk.z1_m - walk.z0_m) / _IN == pytest.approx(6.0)
    assert len(walk.voids) == 6  # the planting pockets go through the base too


def test_a_slab_drawn_full_depth_or_hung_over_a_ceiling_adds_nothing(catlin_model_ro) -> None:
    # SL-M-DECK's thickness spans cap + EPS form; its furring and gypsum are the ceiling.
    assert _layers(catlin_model_ro, "SL-M-DECK") == []
    assert _layers(catlin_model_ro, "SL-SG-FIELD") == []


def test_the_layers_bill_nothing_new(catlin_model_ro) -> None:
    from typehaus.takeoff.bom import bill_of_materials

    rows = bill_of_materials(catlin_model_ro)["structural_solids"]
    assert not [r for r in rows if r["category"] == "sub_slab"]
