"""PAX interiors retain their storage layout and glass in the viewer contract."""

from types import SimpleNamespace

import pytest

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model import FurnitureType, inch
from typehaus.model.canvas import _symbol_geometry
from typehaus.model.placeable_symbols import PART_COLORS, model_parts, plan_symbol_strokes
from typehaus.model.placeable_symbols.furniture import wardrobe_corner_points

WIDTH = inch(39.375).meters
DEPTH = inch(22.875).meters
HEIGHT = inch(92.875).meters


NARROW = inch(19.625).meters


def _rod_centres(parts: list) -> list[float]:
    zs = sorted(part["center"][2] for part in parts if part["color"] == "metal")
    rods: list[list[float]] = []
    for z in zs:
        if rods and z - rods[-1][-1] < inch(2).meters:
            rods[-1].append(z)
        else:
            rods.append([z])
    return [sum(rod) / len(rod) for rod in rods]


def _boards_above(parts: list, width: float, z_inches: float) -> list:
    return [part for part in parts if part["size"][0] > width * 0.9
            and part["size"][1] > DEPTH * 0.9 and part["center"][2] > inch(z_inches).meters]


def test_dress_frame_hangs_sixty_inches_clear_under_three_shelves() -> None:
    parts = model_parts("wardrobe-dress", NARROW, DEPTH, HEIGHT)
    assert _rod_centres(parts) == [pytest.approx(inch(61.5).meters, abs=1e-3)]
    # No drawers: nothing short-and-wood stands between the bottom panel and the rod.
    assert not [part for part in parts if part["color"] == "wood"
                and inch(2).meters < part["center"][2] < inch(60).meters
                and part["size"][2] < inch(30).meters]
    # Three shelves and the frame cap above the rod.
    assert len(_boards_above(parts, NARROW, 62)) == 4
    assert not any(part["color"] == "glass" for part in parts)


def test_double_hang_frame_has_two_rods_and_one_shelf() -> None:
    parts = model_parts("wardrobe-double-hang", NARROW, DEPTH, HEIGHT)
    rods = _rod_centres(parts)
    assert rods == [pytest.approx(inch(38.75).meters, abs=1e-3),
                    pytest.approx(inch(78.75).meters, abs=1e-3)]
    assert len(_boards_above(parts, NARROW, 79)) == 2


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


def test_shelves_frame_has_six_shelves_and_no_rod() -> None:
    parts = model_parts("wardrobe-shelves", NARROW, DEPTH, HEIGHT)
    shelves = [part for part in parts if part["size"][0] > NARROW * 0.9
               and part["size"][1] > DEPTH * 0.9
               and inch(2).meters < part["center"][2] < inch(90).meters]
    assert len(shelves) == 6
    assert not any(part["color"] == "metal" for part in parts)


CORNER = inch(43.375).meters


def test_corner_set_fills_its_l_and_hangs_two_doors_on_the_inner_faces() -> None:
    from shapely.geometry import Polygon
    from shapely.geometry import box as shapely_box

    ring = Polygon(wardrobe_corner_points(CORNER, CORNER))
    assert ring.area == pytest.approx(CORNER**2 - (CORNER - DEPTH)**2)
    parts = model_parts("wardrobe-corner", CORNER, CORNER, HEIGHT)
    for part in parts:  # every solid stays inside the L, notch included
        (cx, cy, _), (sx, sy, _) = part["center"], part["size"]
        assert ring.buffer(1e-6).contains(shapely_box(cx - sx / 2, cy - sy / 2,
                                                      cx + sx / 2, cy + sy / 2))
    doors = [part for part in parts if part["color"] == "appliance-white"]
    assert len(doors) == 2
    widths = sorted(max(part["size"][:2]) for part in doors)
    assert widths == [pytest.approx(CORNER - DEPTH)] * 2
    # The frame is the full 39 3/8" along the back wall, not the half its door covers.
    back_run = [part for part in parts if part["color"] == "wood"
                and part["center"][1] > CORNER / 2 - DEPTH]
    xs = [part["center"][0] + sign * part["size"][0] / 2
          for part in back_run for sign in (-1, 1)]
    assert max(xs) - min(xs) == pytest.approx(inch(39.375).meters, abs=1e-6)
    # The frame's two rods (38 3/4" / 78 3/4") hang in the back run.
    assert _rod_centres(parts) == [pytest.approx(inch(38.75).meters, abs=1e-3),
                                   pytest.approx(inch(78.75).meters, abs=1e-3)]
    outline = plan_symbol_strokes("wardrobe-corner", CORNER, CORNER)[0]
    assert len(outline["points"]) == 6


def test_sliding_pair_puts_the_mirror_on_the_right_in_the_front_track() -> None:
    width, depth = inch(78.75).meters, inch(3.125).meters
    parts = model_parts("wardrobe-sliding-pair", width, depth, HEIGHT)
    mirror = [part for part in parts if part["color"] == "mirror"]
    white = [part for part in parts if part["color"] == "appliance-white"]
    assert len(mirror) == len(white) == 1
    assert mirror[0]["center"][0] > 0 > white[0]["center"][0]
    assert mirror[0]["center"][1] < white[0]["center"][1]  # front track is -y
    assert mirror[0]["size"][0] == pytest.approx(width / 2)


@pytest.mark.parametrize("symbol", ("wardrobe-show", "wardrobe-dress",
                                    "wardrobe-double-hang", "wardrobe-corner"))
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
