"""W-M-STRW: gypsum from the 7' cap, oak courses and bench in the bays, a KDAT sole plate."""

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
    for tag in ("W-B-STR2", "W-B-STR3B"):
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
        assert layer.band(wall) == pytest.approx((inch(84).meters, inch(108).meters))
        assert max(x for x, _ in layer.polygon) <= min(x for x, _ in studs.polygon) + 1e-9
        solids = catlin_model_ro.geometry.part(wall.uid, f"layer:{name}").solids
        assert solids == layer_solids(wall, layer.polygon, [], band=layer.band(wall),
                                      layer_name=name)
        assert solids
        assert all(solid.z0_m == pytest.approx(inch(84).meters) for solid in solids)
        assert all(solid.z1_m == pytest.approx(inch(108).meters) for solid in solids)
        net_area = wall_layer_net_area_m2(catlin_model_ro, wall, layer,
                                         wall_net_areas_m2(catlin_model_ro)[wall.tag])
        assert net_area == pytest.approx(math.dist(*wall.axis) * inch(24).meters)
    assert wall.z1_m > inch(108).meters  # The platform skin must not extend this finish.


#: The three oak courses' (bottom, top) off the storey datum: bench support, 6' shelf, 7' cap.
_COURSES_IN = ((15, 16.5), (70.5, 72), (84, 85.5))


def test_oak_courses_fill_the_clear_stud_bays_and_bill_as_oak(catlin_model_ro):
    wall = catlin_model_ro.wall("W-M-STRW")
    blocks = [member for member in wall.members if member.child_key.startswith("blocking-")]
    assert len(blocks) == 3 * 7  # Three courses over the seven clear bays.
    studs = [member for member in wall.members if member.category == "stud"]
    spans = sorted({(z0, z1) for z0, z1 in
                    ((round(b.z0_m / inch(1).meters, 3), round(b.z1_m / inch(1).meters, 3))
                     for b in blocks)})
    assert spans == [pytest.approx(course) for course in _COURSES_IN]
    for block in blocks:
        assert block.profile == "2x6"
        assert block.material == "oak-8q"
        ring, _, _ = member_footprint(block)
        assert max(x for x, _ in ring) - min(x for x, _ in ring) == pytest.approx(
            inch(5.5).meters)
        # Both block ends butt a real stud face rather than overlapping its centreline.
        for endpoint in (block.p0, block.p1):
            assert min(abs(math.dist(endpoint, stud.p0) - inch(0.75).meters)
                       for stud in studs) < 1e-9
    rows = [row for row in framing_takeoff(catlin_model_ro)
            if row["category"] == "blocking" and row["material"] == "oak-8q"]
    assert len(rows) == 1
    assert rows[0]["profile"] == "2x6"
    assert rows[0]["pieces"] == len(blocks)
    assert rows[0]["cut_length_ft"] == pytest.approx(
        sum(block.length_m for block in blocks) / inch(12).meters, abs=0.1)


def test_the_sole_plate_alone_is_kdat(catlin_model_ro):
    plates = [m for m in catlin_model_ro.wall("W-M-STRW").members if m.category == "plate"]
    assert [m.material for m in plates if m.child_key == "plate-bottom"] == ["kdat"]
    assert all(m.material is None for m in plates if m.child_key.startswith("plate-top"))


def test_the_bench_sits_on_the_support_course_and_stands_proud(catlin_model_ro):
    wall = catlin_model_ro.wall("W-M-STRW")
    studs = next(layer for layer in wall.layers if layer.name == "stud")
    stud_face = min(x for x, _ in studs.polygon)
    bench = next(o for o in catlin_model_ro.canvas_objects if o.tag == "FURN-M-STRW-BENCH")
    assert bench.z_m == pytest.approx(inch(_COURSES_IN[0][1]).meters, abs=1e-4)
    assert stud_face - min(x for x, _ in bench.footprint) == pytest.approx(
        inch(3.75).meters, abs=1e-6)


def test_the_mudroom_switches_are_on_mech_s_and_clear_of_its_door(catlin_plan, catlin_model_ro):
    from typehaus.resolve.framing.footprint import member_footprint as footprint

    tags = ("ED-M-STORAGE-SW", "ED-M-MUDROOM-SW", "ED-M-ENTRY-SW")
    devices = {e.tag: e for e in catlin_plan.all_elements() if e.tag in tags}
    assert {d.location.attachment.wall_ref for d in devices.values()} == {"W-M-MECH-S"}
    # face "left" of an east-to-west wall is its south, mudroom face.
    assert {d.location.attachment.face for d in devices.values()} == {"left"}
    # W-M-STRW's mudroom ("right") face is open bays below 7'; its stair face keeps a switch.
    on_strw = [getattr(getattr(e, "location", None), "attachment", None)
               for e in catlin_plan.all_elements()
               if (getattr(e, "type_ref", None) or "").startswith("ED-T-SWITCH")]
    assert not [a for a in on_strw if getattr(a, "wall_ref", None) == "W-M-STRW"
                and a.face == "right"]
    # The plate's bay: D-M-MECH's east king to the wall's end stud, with no stud between.
    wall = catlin_model_ro.wall("W-M-MECH-S")
    xs = sorted((min(x for x, _ in footprint(m)[0]), max(x for x, _ in footprint(m)[0]))
                for m in wall.members if m.category in ("stud", "king", "jack"))
    king_face = max(hi for _, hi in xs if hi < inch(60).meters)
    end_stud = min(lo for lo, _ in xs if lo > inch(60).meters)
    assert end_stud - king_face >= inch(10.5).meters
    # Every device stands east of the king, so its box is in that bay.
    bodies = [o for o in catlin_model_ro.canvas_objects if o.tag in tags]
    assert len(bodies) == 3
    assert all(min(x for x, _ in o.footprint) >= king_face for o in bodies)


def test_upper_gypsum_is_stamped_for_the_drywall_view_toggle(catlin_model_ro):
    wall = next(wall for wall in wall_graph_json(catlin_model_ro, None)["walls"]
                if wall["tag"] == "W-M-STRW")
    layers = {layer["name"]: layer for layer in wall["layers"]}
    assert layers["gwb-mudroom-upper"]["material"] == "gwb"
    assert layers["gwb-mudroom-upper"]["trades"] == ["drywall"]
    assert layers["paint-mudroom-upper"]["trades"] == ["paint"]


def test_exposed_studs_export_the_douglas_fir_appearance(catlin_model_ro):
    from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS

    material = next(m for m in catlin_model_ro.plan.library.materials
                    if m.tag == "df-select-s4s")
    assert material.species == "douglas-fir"
    assert material.color == NATURAL_WOOD_COLORS[material.species]
    assert material.wood_surface == "natural-clear"
    assert material.finish == "clear-satin-hardwax-oil"
    wall = next(w for w in wall_graph_json(catlin_model_ro, None)["walls"]
                if w["tag"] == "W-M-STRW")
    studs = [m for m in wall["members"] if m["category"] == "stud"]
    assert studs and all(m["material"] == material.tag for m in studs)
