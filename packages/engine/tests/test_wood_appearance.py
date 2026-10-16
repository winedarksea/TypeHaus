"""Wood presentation metadata is independent of quantities and glTF colours are linear."""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from typehaus.emit.gltf.palette import (
    _authored_material_color,
    _hex_rgba,
    _material_finish_color,
    _room_floor_color,
    _solid_color,
)
from typehaus.library.materials import ALL_MATERIALS
from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS
from typehaus.model.materials import Material


@pytest.mark.parametrize("species,color", NATURAL_WOOD_COLORS.items())
def test_library_contains_reusable_natural_solid_boards(species, color):
    material = next(m for m in ALL_MATERIALS if m.species == species and m.finish == "solid-board")
    assert material.color == color
    assert material.wood_surface == "natural-clear"
    assert material.stock_bf_per_sqft is None
    assert material.nominal_quarters is None
    assert not material.requires_custom_milling


@pytest.mark.parametrize("species,color", NATURAL_WOOD_COLORS.items())
def test_all_export_paths_use_the_same_linear_wood_base_color(species, color):
    material = Material(tag="wood", name="Sample", species=species, color=color)
    model = SimpleNamespace(plan=SimpleNamespace(library=SimpleNamespace(materials=(material,))))
    authored = {"wood": material}
    srgb = _hex_rgba(color)
    expected = tuple(((c + 0.055) / 1.055) ** 2.4 for c in srgb[:3]) + (1.0,)
    assert _authored_material_color(material) == pytest.approx(expected)
    assert _material_finish_color("wood", "finish", authored) == pytest.approx(expected)
    assert _room_floor_color(model, "wood") == pytest.approx(expected)
    solid = SimpleNamespace(material="wood", assembly=None, category="column")
    assert _solid_color(model, solid) == pytest.approx(expected)


def test_linear_conversion_handles_dark_channels_and_preserves_opacity():
    wood = Material(tag="wood", name="Sample", species="oak", color="#08080880")
    assert _authored_material_color(wood) == pytest.approx((8 / 255 / 12.92,) * 3 + (128 / 255,))
    metal = Material(tag="metal", name="Sample", color="#aabbcc")
    assert _authored_material_color(metal) == _hex_rgba("#aabbcc")


def test_finish_metadata_does_not_change_species_or_milling():
    material = Material(tag="wood", name="Sample", species="locust", finish="solid-board",
                        wood_surface="unfinished", nominal_quarters=4, milling_profile="S4S")
    painted = material.model_copy(update={"wood_surface": "painted"})
    assert painted.species == material.species == "locust"
    assert painted.nominal_quarters == material.nominal_quarters == 4
    assert painted.milling_profile == material.milling_profile
    with pytest.raises(ValidationError):
        Material(tag="bad", name="Bad", wood_surface="stained")
