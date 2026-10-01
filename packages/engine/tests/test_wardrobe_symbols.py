"""PAX interiors retain their storage layout and glass in the viewer contract."""

from types import SimpleNamespace

import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model import FurnitureType, inch
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import PART_COLORS, model_parts, plan_symbol_strokes

WIDTH = inch(39.375).meters
DEPTH = inch(22.875).meters
HEIGHT = inch(92.875).meters


def test_hanging_frame_leaves_dress_length_space_between_drawer_and_rod() -> None:
    parts = model_parts("wardrobe-hang", WIDTH, DEPTH, HEIGHT)
    rod = [part for part in parts if part["color"] == "metal"]
    assert rod
    rod_bottom = min(part["center"][2] - part["size"][2] / 2 for part in rod)
    rod_top = max(part["center"][2] + part["size"][2] / 2 for part in rod)
    assert (rod_bottom + rod_top) / 2 == pytest.approx(inch(72).meters)
    assert rod_bottom - inch(10).meters > inch(60).meters
    # Full-width horizontal boards above the drawer are the two shelves and frame cap.
    shelves = [part for part in parts if part["size"][0] > WIDTH * 0.9
               and part["size"][1] > DEPTH * 0.9
               and part["center"][2] > inch(10).meters]
    assert len(shelves) == 3
    assert not any(part["color"] == "glass" for part in parts)


def test_display_frame_has_solid_lower_fronts_and_two_glass_upper_drawers() -> None:
    parts = model_parts("wardrobe-show", WIDTH, DEPTH, HEIGHT)
    glass = [part for part in parts if part["color"] == "glass"]
    assert len(glass) == 2
    assert all(inch(26).meters < part["center"][2] < inch(44).meters for part in glass)
    solid_fronts = [part for part in parts if part["center"][1] < -DEPTH * 0.4
                    and part["size"][0] > WIDTH * 0.9
                    and part["size"][2] > inch(7).meters]
    assert len(solid_fronts) == 3
    assert not any(part["color"] == "metal" for part in parts)


def test_browser_receives_glass_alpha_and_keeps_the_existing_plan_glyph() -> None:
    furniture = FurnitureType(tag="PAX", name="Display wardrobe",
                              footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
                              plan_symbol="wardrobe-show")
    record = _symbol_geometry(furniture, furniture.footprint)
    translucent = [part for part in record["model_parts"] if "opacity" in part]
    assert len(translucent) == 2
    assert all(part["opacity"] == 0.55 for part in translucent)
    assert plan_symbol_strokes("wardrobe-show", WIDTH, DEPTH) == \
        plan_symbol_strokes("bookcase", WIDTH, DEPTH)


@pytest.mark.parametrize("symbol", ("wardrobe-show", "wardrobe-hang"))
def test_gltf_uses_the_same_wood_interior_and_glass_or_metal(symbol: str) -> None:
    furniture = FurnitureType(tag="PAX", name="Open wardrobe",
                              footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
                              plan_symbol=symbol)
    item = SimpleNamespace(position=(0.0, 0.0), rotation_degrees=180.0, z_m=0.25)
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, item, furniture, {})
    assert PART_COLORS["wood"] in mesh._buckets
    accent = "glass" if symbol == "wardrobe-show" else "metal"
    assert PART_COLORS[accent] in mesh._buckets
