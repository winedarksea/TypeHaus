"""The mudroom's upper finish and full-depth bay caps share the six-foot edge."""

import math

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.geometry_walls import layer_solids
from typehaus.server.model_json_fabric import wall_graph_json
from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2
from typehaus.takeoff.framing import framing_takeoff


def test_only_the_mudroom_wall_uses_the_upper_closure(catlin_plan, catlin_model_ro):
    variant = "INT_2X6_BRG_MUDROOM_UPPER_GWB"
    assert [element.tag for element in catlin_plan.all_elements()
            if getattr(element, "assembly", None) == variant] == ["W-M-STRW"]
    for tag in ("W-M-STRW2", "W-B-STR2", "W-B-STR3B"):
        wall = catlin_model_ro.wall(tag)
        assert wall.assembly == "INT_2X6_BRG_EXPOSED_PLY"
        assert not any("mudroom-upper" in layer.name for layer in wall.layers)
        assert not any(member.child_key.startswith("blocking-") for member in wall.members)


def test_upper_finish_is_on_the_mudroom_face_and_stops_at_the_ceiling(catlin_model_ro):
    wall = catlin_model_ro.wall("W-M-STRW")
    studs = next(layer for layer in wall.layers if layer.name == "stud")
    stair_plywood = next(layer for layer in wall.layers if layer.name == "ply-stair")
    # The bearing band's x bounds and stair face are fixed construction datums.
    assert min(x for x, _ in studs.polygon) == pytest.approx(inch(117.125).meters)
    assert max(x for x, _ in studs.polygon) == pytest.approx(inch(122.625).meters)
    assert max(x for x, _ in stair_plywood.polygon) == pytest.approx(inch(123.25).meters)
    for name, thickness, material in (("gwb-mudroom-upper", 0.5, "gwb"),
                                      ("paint-mudroom-upper", 0.01, "latex-paint")):
        layer = next(layer for layer in wall.layers if layer.name == name)
        assert layer.material_ref == material
        assert layer.thickness_m == pytest.approx(inch(thickness).meters)
        assert layer.band(wall) == pytest.approx((inch(72).meters, inch(108).meters))
        assert max(x for x, _ in layer.polygon) <= min(x for x, _ in studs.polygon) + 1e-9
        solids = catlin_model_ro.geometry.part(wall.uid, f"layer:{name}").solids
        assert solids == layer_solids(wall, layer.polygon, [], band=layer.band(wall),
                                      layer_name=name)
        assert solids
        assert all(solid.z0_m == pytest.approx(inch(72).meters) for solid in solids)
        assert all(solid.z1_m == pytest.approx(inch(108).meters) for solid in solids)
        net_area = wall_layer_net_area_m2(catlin_model_ro, wall, layer,
                                         wall_net_areas_m2(catlin_model_ro)[wall.tag])
        assert net_area == pytest.approx(math.dist(*wall.axis) * inch(36).meters)
    assert wall.z1_m > inch(108).meters  # The platform skin must not extend this finish.


def test_flat_caps_close_the_clear_stud_bays_and_bill_matching_wood(catlin_model_ro):
    wall = catlin_model_ro.wall("W-M-STRW")
    blocks = [member for member in wall.members if member.child_key.startswith("blocking-")]
    assert len(blocks) == 6
    studs = [member for member in wall.members if member.category == "stud"]
    for block in blocks:
        assert block.profile == "2x6"
        assert block.material == "df-select-s4s"
        ring, z0, z1 = member_footprint(block)
        assert (z0, z1) == pytest.approx((inch(72).meters, inch(73.5).meters))
        assert max(x for x, _ in ring) - min(x for x, _ in ring) == pytest.approx(
            inch(5.5).meters)
        # Both block ends butt a real stud face rather than overlapping its centreline.
        for endpoint in (block.p0, block.p1):
            assert min(abs(math.dist(endpoint, stud.p0) - inch(0.75).meters)
                       for stud in studs) < 1e-9
    rows = [row for row in framing_takeoff(catlin_model_ro)
            if row["category"] == "blocking" and row["material"] == "df-select-s4s"]
    assert len(rows) == 1
    assert rows[0]["profile"] == "2x6"
    assert rows[0]["pieces"] == len(blocks)
    assert rows[0]["cut_length_ft"] == pytest.approx(
        sum(block.length_m for block in blocks) / inch(12).meters, abs=0.1)


def test_upper_gypsum_is_stamped_for_the_drywall_view_toggle(catlin_model_ro):
    wall = next(wall for wall in wall_graph_json(catlin_model_ro, None)["walls"]
                if wall["tag"] == "W-M-STRW")
    layers = {layer["name"]: layer for layer in wall["layers"]}
    assert layers["gwb-mudroom-upper"]["material"] == "gwb"
    assert layers["gwb-mudroom-upper"]["trades"] == ["drywall"]
    assert layers["paint-mudroom-upper"]["trades"] == ["paint"]
