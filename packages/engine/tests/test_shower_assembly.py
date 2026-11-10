"""Shower mounting, handedness and connection contracts without loading a house."""

import pytest
from pydantic import ValidationError

from typehaus.checks.mep.shower_assembly import endpoint_meets_hub
from typehaus.model import ShowerAssemblySpec, ShowerComponent, inch
from typehaus.model.placeable_symbols._shower_hardware import shower_hardware_parts


@pytest.mark.parametrize("normal", [(1, 0), (0, 1), (-1, 0), (0, -1)])
def test_side_hubs_are_behind_face_and_hot_is_users_left(normal):
    spec = ShowerAssemblySpec(valve_face=(inch(3), inch(5), inch(48)),
                             wall_direction=normal, components=())
    hot, cold = spec.inlet_ports()
    nx, ny = normal
    for port, side in ((hot, 1), (cold, -1)):
        x, y, z = [v.meters / .0254 for v in port.position]
        assert (x, y, z) == pytest.approx((3 + 1.75 * nx - side * 2 * ny,
                                         5 + 1.75 * ny + side * 2 * nx, 48))
        assert port.direction == (-side * ny, side * nx, 0)
        assert not port.is_exact()


def test_head_uses_standing_surface_and_not_surround_height():
    spec = ShowerAssemblySpec(valve_face=(inch(0), inch(18), inch(48)),
                             wall_direction=(0, 1), standing_surface_height=inch(2),
                             components=(ShowerComponent(name="head", kind="head"),))
    assert spec.component_point(spec.components[0])[2] / .0254 == pytest.approx(80)
    parts = shower_hardware_parts(spec)
    arm = next(p for p in parts if p["role"] == "shower:head-arm")
    assert arm["center"][2] / .0254 == pytest.approx(80)
    changed = spec.model_copy(update={"head_mount_height": inch(75)})
    assert changed.component_point(changed.components[0])[2] / .0254 == pytest.approx(77)


@pytest.mark.parametrize("neighbor, expected", [((2, 0, 0), True), ((-2, 0, 0), False),
                                               ((0, 0, 2), False), ((2, 1, 0), False)])
def test_hub_arrival_requires_outboard_axial_segment(neighbor, expected):
    assert endpoint_meets_hub((0, 0, 0), neighbor, (0, 0, 0), (1, 0, 0), .001) is expected
    assert not endpoint_meets_hub((0, .1, 0), neighbor, (0, 0, 0), (1, 0, 0), .001)


def test_component_graph_rejects_missing_connections():
    with pytest.raises(ValidationError, match="invalid shower component connection"):
        ShowerAssemblySpec(valve_face=(inch(0), inch(18), inch(48)), wall_direction=(0, 1),
                           components=(ShowerComponent(name="handheld", kind="handheld",
                                                       connection="missing"),))


def test_layer_pocket_preserves_remaining_geometry_and_material_volume():
    from types import SimpleNamespace
    from shapely.geometry import Polygon
    from typehaus.resolve.layer_pockets import subtract_layer_region
    from typehaus.resolve.model import ResolvedLayer

    wall = SimpleNamespace(axis=((0, 0), (10, 0)), z0_m=0, z1_m=10)
    layer = ResolvedLayer(name="insulation", material_ref="foam", function="insulation",
                          thickness_m=2, polygon=[(0, 0), (10, 0), (10, 2), (0, 2)])
    cutter = Polygon([(3, -1), (5, -1), (5, 1), (3, 1)])
    regions = subtract_layer_region(wall, layer, cutter, 4, 7, "valve")
    assert sum(Polygon(region.polygon).area * (region.band(wall)[1]-region.band(wall)[0])
               for region in regions) == pytest.approx(200-6)
    assert sum((region.run_span_m[1]-region.run_span_m[0]) * region.thickness_m
               * (region.band(wall)[1]-region.band(wall)[0]) for region in regions) == pytest.approx(200-6)
    assert all(Polygon(region.polygon).intersection(cutter).area < 1e-10
               for region in regions if region.band(wall)[0] < 7 and region.band(wall)[1] > 4)


def test_shower_component_graph_rejects_cycles():
    with pytest.raises(ValidationError, match="cyclic"):
        ShowerAssemblySpec(valve_face=(inch(0), inch(18), inch(48)), wall_direction=(0, 1),
                           components=(ShowerComponent(name="a", kind="diverter", connection="b"),
                                       ShowerComponent(name="b", kind="head", connection="a")))


def test_docked_handheld_follows_configurable_head_mount():
    head = ShowerComponent(name="head", kind="head")
    handheld = ShowerComponent(name="handheld", kind="handheld", connection="head",
                               relative_to_connection=True, vertical_offset=inch(-3))
    spec = ShowerAssemblySpec(valve_face=(inch(0), inch(18), inch(48)), wall_direction=(0, 1),
                             standing_surface_height=inch(2), components=(head, handheld))
    assert spec.component_point(handheld)[2] / .0254 == pytest.approx(77)
    moved = spec.model_copy(update={"head_mount_height": inch(75)})
    assert moved.component_point(handheld)[2] / .0254 == pytest.approx(74)
