"""Direct-applied panels seat over opening laps; rainscreen supports already clear them."""

import math
from dataclasses import replace

import pytest

from typehaus.model import Building, PlanModel, Project, Site, Storey, m
from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.resolve.opening_flashing import resolve_opening_flashing
from typehaus.resolve.panel_support import panel_support_clearance_m


@pytest.fixture
def panel_model():
    stud = ResolvedLayer("stud", "spf", "structure", .1, [(0, 0), (4, 0), (4, .1), (0, .1)])
    skin = ResolvedLayer("skin", "metal", "cladding", .022225,
                         [(0, .1), (4, .1), (4, .122225), (0, .122225)])
    wall = ResolvedWall("wall", "W", "main", None, ((0, 0), (4, 0)), (stud, skin), 0, 3)
    plan = PlanModel(project=Project(name="panel support",
                     project_uuid="00000000-0000-0000-0000-000000000045",
                     building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
                     storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
                     elements={"main": ()})
    opening = ResolvedOpening("opening", "O", "W", None, 1, 1.2, .8, 2, "window", False)
    return ResolvedModel(plan, walls=[wall], openings=[opening])


@pytest.mark.parametrize("angle", [0, .73, math.pi / 2])
@pytest.mark.parametrize("reverse", [False, True])
def test_lap_seating_follows_the_resolved_water_plane(panel_model, angle, reverse):
    c, s = math.cos(angle), math.sin(angle)

    def rotate(point):
        return (4 + c * point[0] - s * point[1], 6 + s * point[0] + c * point[1])

    wall = panel_model.walls[0]
    wall = replace(wall, axis=tuple(rotate(p) for p in wall.axis), layers=tuple(
        replace(layer, polygon=[rotate(p) for p in layer.polygon]) for layer in wall.layers))
    if reverse:
        wall = replace(wall, axis=wall.axis[::-1])
    panel_model.walls = [wall]
    resolve_opening_flashing(panel_model)
    clearance = panel_support_clearance_m(panel_model, wall, wall.layers[-1])
    assert clearance == pytest.approx(FLASHING.sheet_m + FLASHING.perimeter_membrane_m)


def test_rainscreen_supports_already_clear_the_concealed_laps(panel_model):
    wall = panel_model.walls[0]
    skin = wall.layers[-1]
    skin = replace(skin, polygon=[(x, y + .05) for x, y in skin.polygon])
    wall = replace(wall, layers=(*wall.layers[:-1], skin))
    panel_model.walls = [wall]
    resolve_opening_flashing(panel_model)
    assert panel_support_clearance_m(panel_model, wall, skin) == 0


def test_unflashed_openings_do_not_move_the_panel(panel_model):
    wall = panel_model.walls[0]
    assert panel_support_clearance_m(panel_model, wall, wall.layers[-1]) == 0


def test_seating_uses_the_configured_sheet_and_membrane_thickness(panel_model):
    wall = panel_model.walls[0]
    cfg = replace(FLASHING, sheet_m=.001, perimeter_membrane_m=.0008)
    resolve_opening_flashing(panel_model, cfg)
    assert panel_support_clearance_m(panel_model, wall, wall.layers[-1], cfg) == pytest.approx(.0018)


def test_catalog_window_head_clears_membrane_at_mount_plane(panel_model):
    from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
    from typehaus.resolve.model_window_seat import WindowSeat

    wall = panel_model.walls[0]
    resolve_opening_flashing(panel_model)
    panel_model.openings[0] = replace(panel_model.openings[0],
        window_seat=WindowSeat(.01, .01, .01, 0, outer_m=.1, mount="metal_trim"))
    assert panel_support_clearance_m(panel_model, wall, wall.layers[-1]) == pytest.approx(
        FLASHING.sheet_m + FLASHING.perimeter_membrane_m + SHEET_24_GA_M)


def test_profiled_skin_seats_over_every_base_back_leg(catlin_model_ro):
    """The skin laps a base trim's back leg: its pan stands at or outboard of the leg."""
    walls = {wall.tag: wall for wall in catlin_model_ro.walls}
    checked = 0
    for solid in catlin_model_ro.solids:
        tag = solid.tag.rsplit("-BASE-S", 1)
        if not solid.tag.startswith("TRIM-") or len(tag) != 2 or solid.body_mesh is None:
            continue
        assert solid.under_skin
        wall = walls[tag[0].removeprefix("TRIM-")]
        (x0, y0), (x1, y1) = wall.axis[0], wall.axis[-1]
        length = math.hypot(x1 - x0, y1 - y0)
        n = (-(y1 - y0) / length, (x1 - x0) / length)
        sign = 1 if wall.layers[-1].polygon[0][0] * n[0] + wall.layers[-1].polygon[0][1] * n[1] \
            > x0 * n[0] + y0 * n[1] else -1
        off = sorted(sign * ((x - x0) * n[0] + (y - y0) * n[1]) for x, y, _ in
                     solid.body_mesh.positions)
        leg_front = min(v for v in off if v > off[0] + 1e-5)
        for layer in wall.layers:
            if layer.surface_mesh is not None:
                pan_back = min(sign * ((x - x0) * n[0] + (y - y0) * n[1])
                               for x, y, _ in layer.surface_mesh.positions)
                assert pan_back >= leg_front - 1e-6, (solid.tag, layer.name)
                checked += 1
    assert checked
