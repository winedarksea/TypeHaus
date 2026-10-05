"""``SuspensionAnchor``: its derived joist line, its removal, and its graded load path.

The numbers pinned here are ``houses/catlin/notes/hanging_seat_anchor.md``'s, worked by hand.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.checks.structural._suspension_math import (
    SimpleSpan,
    bolt_double_shear,
    connection_shear,
    point_deflection,
)
from typehaus.checks.structural.suspension_anchor import suspension_anchor
from typehaus.findings import Result
from typehaus.model import FloorSystem, Furniture, SuspensionAnchor
from typehaus.model.suspension import HangingSeatType, dangling_carries
from typehaus.quantities import deg, ft, inch, pt
from typehaus.resolve import resolve
from typehaus.resolve.suspension_anchors import anchor_point, anchor_targets, lay_anchor_lines

ANCHOR, CHAIR, FLOOR = "HA-M-HAMMOCK", "FURN-M-HAMMOCK", "FS-S-EAST"


def _ctx(plan, model, factor=2.0):
    prefs = SimpleNamespace(structural=SimpleNamespace(hanging_seat_impact_factor=factor))
    return SimpleNamespace(plan=plan, model=model, preferences=prefs)


def _finding(ctx, tag=ANCHOR):
    return next(f for f in suspension_anchor(ctx) if tag in f.element_tags)


def _replace_elements(plan, **updates):
    """The plan with each named element model-copied, or dropped where the update is None."""
    storeys = {}
    for storey in plan.storeys:
        kept = []
        for el in plan.storey_elements(storey.tag):
            if el.tag not in updates:
                kept.append(el)
            elif updates[el.tag] is not None:
                kept.append(el.model_copy(update=updates[el.tag]))
        storeys[storey.tag] = kept
    for tag, items in storeys.items():
        plan = plan.with_elements(tag, items)
    return plan


def _east_joists(model):
    floor = next(f for f in model.floors if f.tag == FLOOR)
    return [m for m in floor.members if m.category == "joist"]


# --- the hand note's arithmetic ---------------------------------------------------------


def test_the_note_numbers():
    beam = SimpleSpan(p=740.2, a=106.0, span=216.0, w=50 * 16 / 12 / 12)
    assert beam.reactions == pytest.approx((976.9, 963.3), abs=0.1)
    assert beam.max_moment == pytest.approx(72_344, abs=5)
    assert beam.shear_at_load == pytest.approx(388.0, abs=0.1)
    assert point_deflection(740.2, 106, 216, 2.0e6, 3.5, 11.875, 28.8) == pytest.approx(
        0.168, abs=0.001)
    z, mode = bolt_double_shear(0.625, 3.5, 0.25, 0.50)
    assert (round(z, 1), mode) == (1235.6, "Im")
    assert connection_shear(285, 3.5, 11.875, 0.625, True) == pytest.approx((4156.25, 6.25))


# --- the derived line ------------------------------------------------------------------


def test_catlin_anchor_upgrades_line_003_in_place(catlin_model_ro):
    record = next(r for r in catlin_model_ro.suspension_anchors if r.tag == ANCHOR)
    assert (record.floor, record.line_key, record.reason) == (FLOOR, "003", None)
    assert record.bearings == ("W-M-C2", "W-M-E1")
    assert record.tributary_m == pytest.approx(inch(16).meters)
    lvl = [m for m in _east_joists(catlin_model_ro) if m.profile == "2-1.75x11.875 LVL"]
    assert [m.child_key for m in lvl] == ["joist-0-003-0"]
    assert lvl[0].p0[1] == pytest.approx(ft(4).meters)


def _lines(plan, y_in: float, *extra):
    """Lay anchor lines on FS-S-EAST's regular 16" field for anchors at ``y_in``."""
    system = plan.by_tag(FLOOR)
    model = SimpleNamespace(suspension_anchors=[])
    targets = [SimpleNamespace(anchor=SuspensionAnchor(tag=f"HA-{i}", carries=CHAIR,
                                                       design_load_lb=360.0),
                               xy=(ft(27).meters, inch(y).meters))
               for i, y in enumerate((y_in, *extra))]
    positions = [inch(16 * i).meters for i in range(28)]
    added, members, findings = lay_anchor_lines(
        model, system, targets, positions, [], 0.0, positions[-1],
        [ft(18).meters, ft(36).meters], [("W-M-C2", ft(18).meters), ("W-M-E1", ft(36).meters)],
        True)
    return positions, added, members, findings, model.suspension_anchors


def test_a_bay_centre_adds_a_line(catlin_plan):
    positions, added, members, findings, _ = _lines(catlin_plan, 40)
    assert not findings and added == [pytest.approx(inch(40).meters)]
    assert members == {"a00": "2-1.75x11.875 LVL"}
    assert positions[2:4] == pytest.approx([inch(32).meters, inch(48).meters])


def test_within_six_inches_moves_and_upgrades_the_nearest_line(catlin_plan):
    positions, added, members, findings, _ = _lines(catlin_plan, 44)
    assert not findings and not added
    assert positions[3] == pytest.approx(inch(44).meters)
    assert members == {"003": "2-1.75x11.875 LVL"}


def test_two_anchors_on_one_station_share_one_line(catlin_plan):
    _, added, members, findings, records = _lines(catlin_plan, 40, 40)
    assert not findings and len(added) == 1 and list(members) == ["a00"]
    assert {r.line_key for r in records} == {"a00"}


def test_the_plan_point_follows_rotation_and_offset(catlin_plan):
    chair = catlin_plan.by_tag(CHAIR)
    anchor = SuspensionAnchor(tag="HA-X", carries=CHAIR, design_load_lb=360.0,
                              offset=pt(inch(10), inch(0)))
    plan = _replace_elements(catlin_plan, **{CHAIR: {"rotation": deg(90)}})
    xy, _ = anchor_point(plan, anchor)
    x, y = chair.position.xy_m
    assert xy == pytest.approx((x, y + inch(10).meters))


def test_a_dangling_carries_is_a_load_error(catlin_plan):
    plan = _replace_elements(catlin_plan, **{CHAIR: None})
    [finding] = dangling_carries(plan)
    assert finding.severity.value == "error" and ANCHOR in finding.element_tags


def test_a_truss_host_frames_nothing(catlin_plan):
    plan = _replace_elements(catlin_plan, **{CHAIR: {"position": pt(ft(9), ft(4))}})
    model = SimpleNamespace(plan=plan, suspension_anchors=[], canvas_objects=[])
    assert not anchor_targets(model)
    [record] = model.suspension_anchors
    assert record.floor == "FS-S-WEST" and "truss" in record.reason
    finding = _finding(_ctx(plan, model))
    assert finding.result is Result.UNKNOWN and "truss" in finding.message


# --- removal ----------------------------------------------------------------------------


def test_deleting_the_anchor_leaves_the_floor_as_authored(catlin_plan, catlin_model_ro):
    bare, _ = resolve(_replace_elements(catlin_plan, **{ANCHOR: None, CHAIR: None}))
    spec = catlin_plan.by_tag(FLOOR).joists.member
    assert isinstance(catlin_plan.by_tag(FLOOR), FloorSystem)
    assert {m.profile for m in _east_joists(bare)} == {spec}
    assert not bare.suspension_anchors
    # Joists only: the bearing blocks either side of line 003 are cut to the LVL's width.
    upgraded = [replace(m, profile=spec) for m in _east_joists(catlin_model_ro)]
    assert upgraded == _east_joists(bare)
    floor = next(f for f in bare.floors if f.tag == FLOOR)
    blocks = [m for m in floor.members if m.child_key.startswith("bearing-block-0-00")]
    assert {round(m.length_m / inch(1).meters, 2) for m in blocks[1:4]} == {13.5}


# --- the check ---------------------------------------------------------------------------


def test_catlin_passes_with_the_note_numbers(catlin_plan, catlin_model_ro):
    finding = _finding(_ctx(catlin_plan, catlin_model_ro))
    assert finding.result is Result.PASS, finding.message
    for text in ("P = 360 lb x 2 + 20.2 lb own weight = 740 lb", "6,029/17,848 lb-ft (0.34)",
                 "0.168/0.450 in (0.37)", "740/2,471 lb (0.30)", "388/4,156 lb (0.09)",
                 "3-S-5 WLL 740/6,614 lb", "Governs: deflection", "41.4\" from RM-M-LIVING"):
        assert text in finding.message


def test_no_impact_factor_is_unknown(catlin_plan, catlin_model_ro):
    finding = _finding(_ctx(catlin_plan, catlin_model_ro, factor=None))
    assert finding.result is Result.UNKNOWN
    assert "hanging_seat_impact_factor" in finding.fix_hint


def test_a_seat_rated_over_its_anchors_fails(catlin_plan, catlin_model_ro):
    library = catlin_plan.library
    types = tuple(t.model_copy(update={"rated_load_lb": 500.0})
                  if isinstance(t, HangingSeatType) else t for t in library.furniture_types)
    plan = catlin_plan.model_copy(update={"library": library.model_copy(
        update={"furniture_types": types})})
    findings = suspension_anchor(_ctx(plan, catlin_model_ro))
    assert any(f.result is Result.FAIL and "rated 500 lb" in f.message for f in findings)


def test_a_hang_point_against_the_wall_fails(catlin_plan, catlin_model_ro):
    model = copy.copy(catlin_model_ro)
    model.suspension_anchors = [replace(r, xy=(r.xy[0], inch(20).meters))
                                for r in catlin_model_ro.suspension_anchors]
    finding = _finding(_ctx(catlin_plan, model))
    assert finding.result is Result.FAIL and "FAIL: hang point 13.4\"" in finding.message


def test_the_chair_is_a_placed_hung_seat(catlin_plan, catlin_model_ro):
    chair = next(o for o in catlin_model_ro.canvas_objects if o.tag == CHAIR)
    assert isinstance(catlin_plan.by_tag(CHAIR), Furniture)
    assert chair.suspended_from == "CEIL-RM-M-LIVING"
    assert chair.body_z0_m - chair.z_m == pytest.approx(0)
    assert not any(o.tag == "FURN-M-MEDIA" for o in catlin_model_ro.canvas_objects)


def test_dragging_the_chair_carries_its_line(catlin_plan):
    """The UI's move macro, 6" north: the LVL line follows and the check re-grades."""
    from typehaus.source.inmemory import apply_ops_to_plan
    from typehaus.source.macros_placeables import move_placeable

    x, y = catlin_plan.by_tag(CHAIR).position.xy_m
    result = move_placeable(catlin_plan, "main", tag=CHAIR, position=(x, y + inch(6).meters))
    moved, _ = apply_ops_to_plan(catlin_plan, result.ops)
    assert ANCHOR not in {op.tag for op in result.ops}  # nothing to carry: the anchor is hosted
    model, _ = resolve(moved)
    record = next(r for r in model.suspension_anchors if r.tag == ANCHOR)
    assert (record.line_key, record.reason) == ("a00", None)  # 6" off line 003: a line added
    lvl = [m for m in _east_joists(model) if m.profile == "2-1.75x11.875 LVL"]
    assert [m.p0[1] for m in lvl] == [pytest.approx(inch(54).meters)]
    finding = _finding(_ctx(moved, model))
    assert finding.result is Result.PASS and "line a00" in finding.message
    assert "47.4\" from RM-M-LIVING" in finding.message
