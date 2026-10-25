"""Line loads must weigh all slot regions at their actual heights."""
from types import SimpleNamespace

import pytest

from typehaus.resolve.assembly_weight import KG_PER_M_TO_PLF, dead_load_plf
from typehaus.resolve.model import ResolvedLayer


def _layer(name, material, bottom=None, top=None, slot=None):
    return ResolvedLayer(name=name, material_ref=material, function="cladding",
                         thickness_m=0.1, polygon=((0, 0), (1, 0), (1, 1), (0, 1)),
                         z0_m=bottom, z1_m=top, slot=slot)


def _context_and_wall(layers):
    materials = [SimpleNamespace(tag="dense", density=1000, areal_density_kg_m2=None),
                 SimpleNamespace(tag="sheet", density=None, areal_density_kg_m2=10),
                 SimpleNamespace(tag="unknown", density=None, areal_density_kg_m2=None)]
    context = SimpleNamespace(plan=SimpleNamespace(
        library=SimpleNamespace(materials=materials, assemblies=())))
    wall = SimpleNamespace(z0_m=0, z1_m=3, assembly="A",
                           body_layers=lambda: layers, depth_layers=lambda: layers[:1])
    return context, wall


def test_split_depth_slot_weighs_both_materials_at_their_own_heights():
    context, wall = _context_and_wall([
        _layer("plinth", "dense", 0, 1, "face"),
        _layer("upper", "sheet", 1, 3, "face"),
    ])
    # 1m of 100 kg/m2 plus 2m of 10 kg/m2, not 3m of the first region.
    assert dead_load_plf(context, wall, 3) == pytest.approx(120 * KG_PER_M_TO_PLF)


def test_clipped_empty_band_does_not_require_material_weight():
    context, wall = _context_and_wall([
        _layer("face", "dense", 1, 2), _layer("empty", "unknown", 3, 3),
    ])
    assert dead_load_plf(context, wall, 3) == pytest.approx(100 * KG_PER_M_TO_PLF)


def test_nonempty_unknown_band_keeps_the_whole_line_load_unknown():
    context, wall = _context_and_wall([
        _layer("face", "dense"), _layer("unweighed", "unknown", 1, 2),
    ])
    assert dead_load_plf(context, wall, 3) is None
