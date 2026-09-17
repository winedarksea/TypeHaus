"""Stage-1 furniture editing macros: room lookup without a resolve, followers and impacts,
slide along a wall, place with rotation/kind, delete with reference guards.

Beside ``test_canvas_placeables.py``, which is past the 500-line guideline.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.model import ft, inch
from typehaus.source import load_plan
from typehaus.source.macros import (
    MacroError,
    _containing_room,
    attach_placeable,
    delete_placeable,
    detach_placeable,
    duplicate_canvas_object,
    move_placeable,
    place_placeable,
    slide_placeable,
)
from _helpers import copy_house


@pytest.fixture
def starter_plan(tmp_path: Path, starter_dir: Path):
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    plan = load_plan(dst).plan
    assert plan is not None
    return plan


def test_containing_room_uses_supplied_rooms_without_resolving(starter_plan, monkeypatch):
    import typehaus.resolve as resolve_pkg

    def refuse(_plan):
        raise AssertionError("resolved despite supplied rooms")

    monkeypatch.setattr(resolve_pkg, "resolve", refuse)
    monkeypatch.setattr(resolve_pkg, "resolve_preview", refuse)
    square = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
    rooms = [SimpleNamespace(tag="RM-Other", storey="upper", clear_face=square),
             SimpleNamespace(tag="RM-Here", storey="main", clear_face=square)]
    assert _containing_room(starter_plan, "main", (1.0, 1.0), rooms=rooms) == "RM-Here"
    assert _containing_room(starter_plan, "main", (5.0, 1.0), rooms=rooms) is None


def _apply(plan, result):
    from typehaus.source.inmemory import apply_ops_to_plan

    return apply_ops_to_plan(plan, result.ops)[0]


def _attached_chair(plan):
    placed = place_placeable(plan, "main", type_ref="FURN-ARMCHAIR-35", position=(3.0, 3.0),
                             tag="F-CHAIR")
    plan = _apply(plan, placed)
    return _apply(plan, attach_placeable(plan, "main", tag="F-CHAIR", wall="W-101",
                                         face="left", distance="4'", gap="2\"",
                                         rotation_offset=90))


def test_move_reports_wall_ref_left_behind(catlin_plan):
    fixture = next(e for e in catlin_plan.all_elements() if e.tag == "FX-M-BATH1-WC")
    x, y = fixture.position.xy_m
    near = move_placeable(catlin_plan, "main", tag="FX-M-BATH1-WC", position=(x, y + 0.05))
    assert not [i for i in near.impacts if i.kind == "left_behind"]
    far = move_placeable(catlin_plan, "main", tag="FX-M-BATH1-WC", position=(x + 4, y + 4))
    left = [i for i in far.impacts if i.kind == "left_behind"]
    assert len(left) == 1 and "W-M-BAE" in left[0].reason
    assert left[0].reason in far.warnings


def test_free_move_of_attached_item_reports_attachment_dropped(starter_plan):
    plan = _attached_chair(starter_plan)
    moved = move_placeable(plan, "main", tag="F-CHAIR", position=(4.0, 4.0))
    assert [(i.tag, i.kind) for i in moved.impacts] == [("F-CHAIR", "left_behind")]
    assert "W-101" in moved.impacts[0].reason
    detached = detach_placeable(plan, "main", tag="F-CHAIR", position=(4.0, 4.0))
    assert detached.impacts == ()


def test_drain_followers_are_carried_impacts(catlin_plan):
    fixture = next(e for e in catlin_plan.all_elements() if e.tag == "FX-B-BATH-WC")
    x, y = fixture.position.xy_m
    result = move_placeable(catlin_plan, "basement", tag="FX-B-BATH-WC",
                            position=(x + 0.1, y - 0.05))
    kinds = {(i.tag, i.kind) for i in result.impacts}
    assert {("SP-B-BATH-WC", "carried"), ("PR-B-BATH-DRAIN", "carried")} <= kinds
    assert ("FX-B-BATH-WC", "needs_review") in kinds  # the vent/supply left as routed
    pinned = move_placeable(catlin_plan, "basement", tag="FX-B-BATH-LAV", position=(5.1, 6.2))
    assert [i.kind for i in pinned.impacts] == ["carried"] and pinned.warnings == ()


def test_delete_placeable_refuses_served_fixture(catlin_plan, starter_plan):
    with pytest.raises(MacroError, match="PR-B-BATH-DRAIN"):
        delete_placeable(catlin_plan, "basement", tag="FX-B-BATH-WC")
    result = delete_placeable(starter_plan, "main", tag="ED-Main-RC1")
    assert [(op.op, op.tag) for op in result.ops] == [("delete", "ED-Main-RC1")]


def test_duplicate_copies_no_service_network(catlin_plan):
    result = duplicate_canvas_object(catlin_plan, "basement", tag="FX-B-BATH-WC")
    assert [(op.op, op.type) for op in result.ops] == [("add", "Fixture")]
    add = result.ops[0]
    assert add.tag != "FX-B-BATH-WC" and "uid" not in add.fields
    assert not {"drain_position", "location"} & set(add.fields)


def test_slide_placeable_keeps_gap_and_rotation_offset(starter_plan):
    plan = _attached_chair(starter_plan)
    result = slide_placeable(plan, "main", tag="F-CHAIR", distance="10'")
    slid = _apply(plan, result)
    attachment = next(e for e in slid.all_elements() if e.tag == "F-CHAIR").location.attachment
    assert attachment.wall_ref == "W-101" and attachment.face == "left"
    assert attachment.distance_from_start.meters == pytest.approx(ft(10).meters)
    assert attachment.normal_gap.meters == pytest.approx(inch(2).meters)
    assert attachment.rotation_offset.degrees == pytest.approx(90)
    past_end = _apply(plan, slide_placeable(plan, "main", tag="F-CHAIR", distance=99))
    far = next(e for e in past_end.all_elements() if e.tag == "F-CHAIR").location.attachment
    assert far.distance_from_start.meters == pytest.approx(7.3152)
    with pytest.raises(MacroError, match="not attached"):
        slide_placeable(plan, "main", tag="ED-Main-RC1", distance=1)


def test_place_placeable_carries_rotation_and_kind(starter_plan):
    plan = _apply(starter_plan, place_placeable(
        starter_plan, "main", type_ref="FURN-SOFA-84", position=(3.0, 3.0), rotation=90,
        tag="F-SOFA"))
    sofa = next(e for e in plan.all_elements() if e.tag == "F-SOFA")
    assert sofa.rotation.degrees == pytest.approx(90) and sofa.room == "RM-Main"
    switch = place_placeable(starter_plan, "main", type_ref="ED-T-SWITCH", position=(1, 1))
    assert switch.ops[0].fields["kind"].expr == "DeviceKind.SWITCH"
    gfci = place_placeable(starter_plan, "main", type_ref="ED-T-RECEPTACLE", position=(1, 1),
                           kind="gfci")
    assert gfci.ops[0].fields["kind"].expr == "DeviceKind.RECEPTACLE_GFCI"


def test_equipment_kind_inference_matches_catlin(catlin_plan):
    """Placing equipment from the catalog must not file every machine as a furnace.

    ``EquipmentType`` carries no kind, so the macro reads the product's own words. Catlin's
    21 authored equipment types are the oracle: each one's authored kind is what a person
    chose for that product, and the inference has to reproduce all of them. A new product
    whose name defeats the tokens fails here rather than landing silently as a FURNACE.
    """
    from typehaus.source.macros_placeables import _infer_equipment_kind

    authored = {el.type_ref: el.kind for el in catlin_plan.all_elements()
                if type(el).__name__ == "Equipment"}
    assert len(authored) >= 20
    wrong = {ref: (_infer_equipment_kind(catlin_plan, ref), kind)
             for ref, kind in authored.items()
             if _infer_equipment_kind(catlin_plan, ref) is not kind}
    assert not wrong, f"inferred != authored: {wrong}"


def test_register_kind_inference_reads_the_exhaust_products(catlin_plan):
    """A grille's system is a guess — but the clear-cut products must come out right.

    One product serves two systems (catlin files ``REG-T-ERV-EXH`` as both EXHAUST and
    RETURN), so this pins only what the words do settle, and that the fallback is SUPPLY.
    """
    from typehaus.model.enums import DuctSystem
    from typehaus.source.macros_placeables import _infer_register_kind

    assert _infer_register_kind(catlin_plan, "REG-T-HP-SUP") is DuctSystem.SUPPLY
    assert _infer_register_kind(catlin_plan, "REG-T-HP-RET") is DuctSystem.RETURN
    assert _infer_register_kind(catlin_plan, "REG-T-ERV-EXH") is DuctSystem.EXHAUST
    assert _infer_register_kind(catlin_plan, "REG-T-TRANSFER-1210") is DuctSystem.TRANSFER
    assert _infer_register_kind(catlin_plan, "REG-T-ERV-SUP") is DuctSystem.SUPPLY
