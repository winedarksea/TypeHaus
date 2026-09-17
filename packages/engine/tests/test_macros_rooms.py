"""P1 ``draw_room_rect`` / ``delete_wall`` and P8 attachment remap on split/heal, on a starter
copy. Starter main storey: a 24' x 20' loop N-1..N-4, walls W-101 (south, west→east),
W-102 (east), W-103 (north, east→west), W-104 (west); RM-Main seeded at (12', 10')."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import pytest

from typehaus.model.ids import new_uid
from typehaus.quantities import ft
from typehaus.resolve import resolve
from typehaus.source import load_plan, macros
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.inmemory import apply_ops_to_plan
from typehaus.source.macros_graph import station_map
from typehaus.source.ops import PatchOp, RawExpr
from _helpers import copy_house

EXT = "HOUSE_WALL_2X6_WITH_ZIPR"
PART = "INT_2X4_PARTITION"


@pytest.fixture
def plan(starter_dir: Path):
    return load_plan(starter_dir).plan


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    return copy_house(starter_dir, tmp_path / "starter")


def _apply(plan, result):
    return apply_ops_to_plan(plan, result.ops)[0]


def _resolve_clean(plan, storey="main"):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.check_id == "integrity.wall_loop_open"]
    walls = [e for e in plan.storey_elements(storey) if e.element_kind == "Wall"]
    pairs = Counter(frozenset((w.start_node, w.end_node)) for w in walls)
    assert max(pairs.values()) == 1
    return model


def _rooms(model, storey="main"):
    return {r.tag for r in model.rooms if r.storey == storey}


def _opening_xy(model, tag):
    op = next(o for o in model.openings if o.tag == tag)
    (x0, y0), (x1, y1) = model.wall(op.host_wall).axis
    f = op.center_along_m / math.hypot(x1 - x0, y1 - y0)
    return (x0 + f * (x1 - x0), y0 + f * (y1 - y0))


def _pin_uids(ops):
    for op in ops:
        if op.op == "add" and "uid" not in op.fields:
            op.fields["uid"] = new_uid()
    return ops


def _dump(plan):
    return {el.tag: el.model_dump(mode="python") for el in plan.all_elements()}


def _assert_equivalent(house: Path, ops) -> None:
    base = load_plan(house).plan
    mem = apply_ops_to_plan(base, ops)[0]
    ProjectCoordinator(house).apply_patch(ops, None)
    reloaded = load_plan(house)
    assert reloaded.plan is not None, [f.message for f in reloaded.findings]
    assert _dump(mem) == _dump(reloaded.plan)


# --- draw_room_rect ----------------------------------------------------------

def test_adjacent_rect_shares_east_wall(plan):
    result = macros.draw_room_rect(plan, "main", ("24'", "0'"), ("34'", "20'"), EXT, "bedroom")
    kinds = Counter((o.op, o.type) for o in result.ops)
    assert kinds == {("add", "Node"): 2, ("add", "Wall"): 3, ("add", "Room"): 1}
    assert not any(o.tag == "W-102" for o in result.ops)
    room = next(o.tag for o in result.ops if o.type == "Room")
    model = _resolve_clean(_apply(plan, result))
    assert _rooms(model) == {"RM-Main", room}


def test_shorter_neighbour_tees_and_rehosts_window(plan):
    before = _opening_xy(resolve(plan)[0], "WIN-103")
    result = macros.draw_room_rect(plan, "main", ("24'", "5'"), ("34'", "15'"), EXT, "office")
    after_plan = _apply(plan, result)
    host = next(e for e in after_plan.storey_elements("main") if e.tag == "WIN-103").host
    assert host != "W-102"
    assert any(i.tag == "WIN-103" and i.kind == "carried" for i in result.impacts)
    model = _resolve_clean(after_plan)
    assert _rooms(model) == {"RM-Main", "RM-1"}
    assert _opening_xy(model, "WIN-103") == pytest.approx(before, abs=1e-6)


def test_partition_reseeds_swallowed_room(plan):
    result = macros.draw_room_rect(plan, "main", ("0'", "0'"), ("14'", "20'"), PART, "bedroom")
    assert any(i.tag == "RM-Main" and i.kind == "carried" for i in result.impacts)
    after = _apply(plan, result)
    model = _resolve_clean(after)
    assert _rooms(model) == {"RM-Main", "RM-1"}
    seed = next(e for e in after.storey_elements("main") if e.tag == "RM-Main").seed
    assert seed.xy_m[0] > ft(14).meters


def test_partition_through_a_centred_seed_reseeds_it(tmp_path: Path):
    # A drawn room's seed is its centre, so halving it puts the seed inside the new wall.
    from typehaus.cli.scaffold import scaffold_house

    scaffold_house(tmp_path / "blank", "Blank", template="empty")
    plan = load_plan(tmp_path / "blank").plan
    plan = _apply(plan, macros.draw_room_rect(plan, "main", ("0'", "0'"), ("16'", "12'"), EXT,
                                              "living"))
    result = macros.draw_room_rect(plan, "main", ("0'", "0'"), ("8'", "12'"), PART, "bedroom")
    assert any(i.tag == "RM-1" and i.kind == "carried" for i in result.impacts)
    assert _rooms(_resolve_clean(_apply(plan, result))) == {"RM-1", "RM-2"}


def test_interior_rect_is_its_own_room(plan):
    result = macros.draw_room_rect(plan, "main", ("6'", "6'"), ("10'", "9'"), PART, "storage")
    assert not [o for o in result.ops if o.op != "add"]
    assert _rooms(_resolve_clean(_apply(plan, result))) == {"RM-Main", "RM-1"}


def test_crossing_wall_is_refused(plan):
    with pytest.raises(macros.MacroError, match="W-102"):
        macros.draw_room_rect(plan, "main", ("20'", "5'"), ("30'", "15'"), EXT, "bedroom")


def test_near_miss_corner_is_refused(plan):
    with pytest.raises(macros.MacroError, match="N-2"):
        macros.draw_room_rect(plan, "main", ("24'-3\"", "0'"), ("34'", "20'"), EXT, "bedroom")


def test_draw_room_rect_in_memory_matches_writeback(house: Path):
    base = load_plan(house).plan
    ops = macros.draw_room_rect(base, "main", ("24'", "5'"), ("34'", "15'"), EXT, "office").ops
    _assert_equivalent(house, _pin_uids(ops))


# --- delete_wall -------------------------------------------------------------

def _partition(plan):
    result = macros.draw_room_rect(plan, "main", ("0'", "0'"), ("10'", "20'"), PART, "bedroom")
    wall = next(o.tag for o in result.ops if o.type == "Wall" and o.fields.get("assembly") == PART)
    return result, wall


def test_delete_wall_merges_and_heals(house: Path):
    base = load_plan(house).plan
    drawn, wall = _partition(base)
    ProjectCoordinator(house).apply_patch(_pin_uids(drawn.ops), None)
    drawn_plan = load_plan(house).plan
    result = macros.delete_wall(drawn_plan, "main", wall)
    assert result.remap.renamed["RM-1"] == "RM-Main"
    _assert_equivalent(house, result.ops)
    healed = load_plan(house).plan
    walls = {e.tag: (e.start_node, e.end_node)
             for e in healed.storey_elements("main") if e.element_kind == "Wall"}
    assert walls == {"W-101": ("N-1", "N-2"), "W-102": ("N-2", "N-3"),
                     "W-103": ("N-3", "N-4"), "W-104": ("N-4", "N-1")}
    model = _resolve_clean(healed)
    assert _rooms(model) == {"RM-Main"}
    assert _opening_xy(model, "WIN-102") == pytest.approx(
        _opening_xy(resolve(base)[0], "WIN-102"), abs=1e-6)


def test_delete_wall_keep_room(plan):
    drawn, wall = _partition(plan)
    after = _apply(plan, drawn)
    result = macros.delete_wall(after, "main", wall, keep_room="RM-1")
    assert result.remap.renamed["RM-Main"] == "RM-1"
    alarm = next(o for o in result.ops if o.tag == "AL-Main")
    assert alarm.fields == {"room": "RM-1"}


def test_delete_wall_refuses_on_backing_ref(plan):
    backing = PatchOp("add", "WallBacking", "WB-1", {
        "wall_ref": "W-102", "elevation": RawExpr("ft(3)"), "height": RawExpr("inch(12)")},
        storey="main")
    with_backing = apply_ops_to_plan(plan, [backing])[0]
    with pytest.raises(macros.MacroError, match="WB-1.wall_ref"):
        macros.delete_wall(with_backing, "main", "W-102")
    with pytest.raises(macros.MacroError, match="names W-103"):
        macros.delete_wall(plan, "main", "W-103")


def test_delete_wall_cascades_openings(plan):
    result = macros.delete_wall(plan, "main", "W-102")
    assert ("delete", "WIN-103") in {(o.op, o.tag) for o in result.ops}
    kinds = {(i.tag, i.kind) for i in result.impacts}
    assert ("WIN-103", "left_behind") in kinds and ("RM-Main", "needs_review") in kinds


def test_macro_endpoint_room_rect_round_trip(house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    storey_file = house / "plan/storeys/main.py"
    original = storey_file.read_text()
    with fastapi_testclient.TestClient(create_app(house)) as c:
        rev = c.get("/model").json()["revision"]
        resp = c.post("/macro", json={"macro": "draw_room_rect", "storey": "main",
                                      "revision": rev, "a": ["0'", "0'"], "b": ["10'", "20'"],
                                      "assembly": PART, "occupancy": "bedroom"})
        assert resp.status_code == 200, resp.json()
        body = resp.json()
        assert [t for t in body["minted"] if t.startswith("RM-")] == ["RM-1"]
        c.app.state.project._flush_writes()  # the source writeback is queued, not synchronous
        wall = next(e.tag for e in load_plan(house).plan.storey_elements("main")
                    if getattr(e, "assembly", None) == PART)
        resp = c.post("/macro", json={"macro": "delete_wall", "storey": "main", "wall": wall})
        assert resp.status_code == 200, resp.json()
        assert "RM-1" in resp.json()["deleted"]
        assert c.post("/undo").status_code == 200
        assert c.post("/undo").status_code == 200
    assert storey_file.read_text() == original


# --- P8: attachments through split and heal -----------------------------------

_SCONCE = PatchOp("add", "ElectricalDevice", "ED-SCONCE", {
    "kind": RawExpr("DeviceKind.LIGHT"), "position": RawExpr("pt(ft(18), ft(0))"),
    "mount": RawExpr("Mount(kind=MountKind.WALL, elevation=ft(6))"),
    "location": RawExpr('Location(attachment=WallAttachment(wall_ref="W-101", face="left", '
                        'distance_from_start=ft(18)))')},
    hint_file="plan/placeables.py", hint_list="MAIN_PLACEABLES", storey="main")


def _sconce(model):
    obj = next(o for o in model.canvas_objects if o.tag == "ED-SCONCE")
    return obj.attachment_wall, obj.position


def test_station_map_hand_worked():
    # Old wall runs 10' → 0' along x; station 3' is x = 7'. The new wall runs 0' → 20',
    # so 7' = 10' - 3': shift 10', reversed.
    shift, rev = station_map(((10.0, 0.0), (0.0, 0.0)), ((0.0, 0.0), (20.0, 0.0)))
    assert (shift, rev) == (10.0, True)
    assert station_map(((10.0, 0.0), (24.0, 0.0)), ((0.0, 0.0), (24.0, 0.0))) == (10.0, False)


def test_split_carries_attached_sconce_with_shifted_distance(house: Path):
    ProjectCoordinator(house).apply_patch(_pin_uids([_SCONCE]), None)
    base = load_plan(house).plan
    wall, xy = _sconce(resolve(base)[0])
    # Hand-worked: W-101 runs (0,0) → (24',0); station 18' from N-1 puts the centre at x=18'.
    assert wall == "W-101" and xy[0] == pytest.approx(ft(18).meters)
    result = macros.split_wall(base, "main", "W-101", ("10'", "0'"))
    new_wall = next(o.tag for o in result.ops if o.op == "add" and o.type == "Wall")
    op = next(o for o in result.ops if o.tag == "ED-SCONCE")
    assert f'wall_ref="{new_wall}"' in op.fields["location"].expr
    assert "distance_from_start=ft(8)" in op.fields["location"].expr
    assert result.remap.shift["ED-SCONCE"] == pytest.approx(-ft(10).meters)
    ProjectCoordinator(house).apply_patch(result.ops, None)
    after = load_plan(house).plan
    assert _sconce(resolve(after)[0]) == (new_wall, pytest.approx(xy, abs=1e-6))


def test_heal_restores_attachment_distance(house: Path):
    ProjectCoordinator(house).apply_patch(_pin_uids([_SCONCE]), None)
    base = load_plan(house).plan
    split = macros.split_wall(base, "main", "W-101", ("10'", "0'"))
    mid = next(o.tag for o in split.ops if o.type == "Node")
    ProjectCoordinator(house).apply_patch(_pin_uids(split.ops), None)
    healed = macros.heal_walls(load_plan(house).plan, "main", mid)
    ProjectCoordinator(house).apply_patch(healed.ops, None)
    after = load_plan(house).plan
    sconce = next(e for e in after.all_elements() if e.tag == "ED-SCONCE")
    att = sconce.location.attachment
    assert (att.wall_ref, att.distance_from_start.meters) == ("W-101",
                                                               pytest.approx(ft(18).meters))
    assert _sconce(resolve(after)[0])[1][0] == pytest.approx(ft(18).meters)


def test_split_reports_backing_needs_review(plan):
    backing = PatchOp("add", "WallBacking", "WB-1", {
        "wall_ref": "W-102", "elevation": RawExpr("ft(3)"), "height": RawExpr("inch(12)")},
        storey="main")
    with_backing = apply_ops_to_plan(plan, [backing])[0]
    result = macros.split_wall(with_backing, "main", "W-102", ("24'", "10'"))
    assert ("WB-1", "needs_review") in {(i.tag, i.kind) for i in result.impacts}


def test_heal_reversed_segment_flips_face_and_keeps_pose(plan):
    split = macros.split_wall(plan, "main", "W-101", ("10'", "0'"))
    seg = next(o for o in split.ops if o.op == "add" and o.type == "Wall")
    mid = seg.fields["start_node"]
    # Author the b-side backwards (N-2 → mid): station 6' from N-2 is x = 18', on its right.
    sconce = PatchOp("add", "ElectricalDevice", "ED-SCONCE", {
        **_SCONCE.fields, "location": RawExpr(
            f'Location(attachment=WallAttachment(wall_ref="{seg.tag}", face="right", '
            'distance_from_start=ft(6), rotation_offset=deg(180)))')}, storey="main")
    before = apply_ops_to_plan(_apply(plan, split), [
        PatchOp("update", "Wall", seg.tag, {"start_node": "N-2", "end_node": mid}), sconce])[0]
    pose = next((o.position, o.rotation_degrees % 360)
                for o in resolve(before)[0].canvas_objects if o.tag == "ED-SCONCE")
    healed = macros.heal_walls(before, "main", mid)
    assert "ED-SCONCE" in healed.remap.reversed
    expr = next(o for o in healed.ops if o.tag == "ED-SCONCE").fields["location"].expr
    assert 'face="left"' in expr and "distance_from_start=ft(18)" in expr
    after = next((o.position, o.rotation_degrees % 360)
                 for o in resolve(_apply(before, healed))[0].canvas_objects
                 if o.tag == "ED-SCONCE")
    assert after == (pytest.approx(pose[0], abs=1e-6), pytest.approx(pose[1]))
