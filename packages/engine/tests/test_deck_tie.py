"""``engineering/deck_tie.py`` against ``houses/catlin/notes/north_entry_piers.md`` §10.

The note was worked by hand before the module: the tie joints as a bolt group, the landing's
loads placed where they act, each angle's interaction per joint at its own C_M (§10a-§10e).
Since 2026-10-13 (§10h) the two joints are wood to wood: HL43HDG wet on BM-BW-FE into W-G-S,
HL33HDG dry into W-G-W. The stem tie and its anchors retired with the carriers.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.deck_tie import distribute
from typehaus.engineering.deck_tie_basis import Load, TieJoint, wall_ties
from typehaus.engineering.item import Status

_ITEM = "deck_tie/FS-BW-FLOOR"
#: The four landing piers the tie takes out of the lateral system (§10, and the withdrawn
#: sections it names in three notes).
_LANDING = ("PT-BW-E", "PT-BW-GE", "PT-BW-GW", "PT-BW-W")


def _state(record, name):
    return next(s for s in record.limit_states if s.name.startswith(name))


def _input(record, prefix):
    return next(q.value for q in record.inputs if q.name.startswith(prefix))


def test_the_tie_is_derived_from_the_authored_hardware(catlin_ctx):
    """§10h: two joints, a pair each, both wood to wood: FE into W-G-S (wet), the screen into
    W-G-W (dry). FE runs INTO its wall, the screen alongside its own."""
    ectx = catlin_ctx.engineering.context
    joints = wall_ties(ectx, ectx.plan.by_tag("FS-BW-FLOOR"))
    assert [(j.member, j.wall, len(j.parts), j.model, j.wall_axis, j.heel_axis,
             j.on_concrete, j.service_condition, j.member_axis) for j in joints] == [
        ("BM-BW-FE", "W-G-S", 2, "HL43HDG", "x", None, False, None, "y"),
        ("W-BW-SCREEN", "W-G-W", 2, "HL33HDG", "y", None, False, "dry", "y")]
    assert "windblown" in joints[1].service_basis
    assert [round(j.x_ft, 4) for j in joints] == [9.5833, 6.1979]
    assert [round(j.y_ft, 4) for j in joints] == [43.1458, 43.1458]


def test_the_loads_reproduce_section_10b(catlin_ctx):
    record = catlin_ctx.engineering[_ITEM]
    # The landing's OWN edge band (§10b): 8.19" of joist and board (2026-10-15, §10i), not TR-SG-FASCIA.
    assert _input(record, "x:FS-BW-FLOOR deck wind") == pytest.approx(66.9232, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN face") == pytest.approx(407.00, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN-SKIRT face") == pytest.approx(112.27, abs=0.01)
    # Seat beams 3.3542' from the column's east face (§10b addendum 2026-09-23).
    assert _input(record, "y:FS-BW-FLOOR deck wind") == pytest.approx(98.6669, abs=0.01)
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(1038.35, abs=0.1)
    canopy = catlin_ctx.engineering["lateral_system/RF-BW-CANOPY"]
    delivered = next(q.value for q in canopy.inputs if q.name == "delivered_shear_y")
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(delivered)


def test_the_verdicts_reproduce_section_10h(catlin_ctx):
    """§10h: every row passes; N-S wind at W governs at 0.778, E-W at W 0.773 after §10i."""
    record = catlin_ctx.engineering[_ITEM]
    assert record.status is Status.OK
    ns = _state(record, "tie interaction, N-S wind")
    assert ns.ratio == pytest.approx(0.7780, abs=5e-4)
    assert record.governing.name == ns.name
    ew = _state(record, "tie interaction, E-W wind")
    assert ew.ratio == pytest.approx(0.7728, abs=5e-4)
    assert _state(record, "tie interaction, guard").ratio == pytest.approx(0.6314, abs=5e-4)
    assert "557.6 lb along the wall / 1,480.0 + 293.1 lb across it / 740.0" in ew.citation
    # W's dry service is a judgement named for the engineer of record, on the record.
    assert any("DRY SERVICE at W-BW-SCREEN/W-G-W" in n and "engineer of record" in n
               for n in record.notes)


def test_no_tie_lands_on_concrete_since_the_stem_tie_retired(catlin_ctx):
    """§10h: the stem anchors (§10e) went with the carriers; no anchor row is graded."""
    record = catlin_ctx.engineering[_ITEM]
    assert not [s for s in record.limit_states if s.name.startswith("wall anchor")]
    assert not [n for n in record.notes if "EMPTY" in n]


def test_the_stem_anchors_reproduce_section_10e():
    """§10e by hand, no house: one Titen HD per HL35 leg, 3" to each face, 7.5" apart, FE's
    old E-W demand (1,124.5 lb toward a face, 199.1 along). catlin retired the stem tie on
    2026-10-13; ``deck_tie_anchor`` stays oracled by the section it was written against."""
    from typehaus.engineering.deck_tie_anchor import Demand, Group, grade

    group = Group("FE", 2, 7.5, 3.0, 3.0, 5_000.0)
    tension, shear, both, _how = grade(group, Demand("E-W", 1124.5, 199.1, False))
    assert tension == pytest.approx(0.5336, abs=5e-4)
    assert shear == pytest.approx(0.3668, abs=5e-4)
    assert both == pytest.approx(0.7503, abs=5e-4)


def test_the_hl_reading_by_heel():
    """§10a: heel across the wall reads F1 across; a vertical heel doubles uplift in the tied
    member's leg plane (§10h: along the wall for a screen, across it for a beam that runs
    into it); C_M 0.70 unless the parts author dry service."""
    from typehaus.engineering.deck_tie import capacity

    stem = capacity(TieJoint("FE", "S-DR", ("a", "b"), "HL35HDG", 0, 0, "x", "y"))
    wet = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False))
    dry = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False,
                            "dry", "covered"))
    mixed = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False,
                              "mixed"))
    # A beam running INTO its wall: the leg on its side face takes the across force in plane.
    into = capacity(TieJoint("FE", "G-S", ("a", "b"), "HL43HDG", 0, 0, "x", None, False,
                             member_axis="y"))
    assert (stem.along_lb, stem.across_lb) == pytest.approx((518.0, 917.0))
    assert (wet.along_lb, wet.across_lb) == pytest.approx((1036.0, 518.0))
    assert (dry.along_lb, dry.across_lb) == pytest.approx((1480.0, 740.0))
    assert (into.along_lb, into.across_lb) == pytest.approx((892.5, 1785.0))
    assert isinstance(mixed, str)


def test_the_anchored_hole_follows_where_the_angle_is_put():
    """§10e: the hole nearest the core centreline is anchored. An HL35 centred on the core
    leaves it 1 1/4" off (the 1.132 case); set 1 1/4" over, it lands on the centreline."""
    from typehaus.engineering.deck_tie_anchor import ANGLES, anchor_station

    hl35 = ANGLES["HL35HDG"]
    assert abs(anchor_station(hl35, 0.0, 0.0)) == pytest.approx(1.25)
    assert anchor_station(hl35, 1.25, 0.0) == pytest.approx(0.0)
    assert anchor_station(ANGLES["HL33HDG"], 0.0, 0.0) == pytest.approx(0.0)
    assert hl35.heel_arm_in == pytest.approx(1.25)


def test_the_bolt_group_arithmetic_by_hand():
    """§10c's N-S line, term by term, with no model in the way."""
    joints = [TieJoint("FC", "S1", ("a", "b"), "HGAM10", 7.125, 43.6771, "x"),
              TieJoint("FE", "S-DR", ("a", "b"), "HGAM10", 9.458333, 43.6771, "x")]
    loads = [Load("screen", 0.0, 980.74, 6.0, 39.9323),
             Load("deck", 0.0, 310.56, 7.7917, 39.9323)]
    (x_fc, y_fc), (x_fe, y_fe) = distribute(joints, loads)
    assert (x_fc, x_fe) == (0.0, 0.0)
    assert y_fc == pytest.approx(1_675.43, abs=0.05)
    assert y_fe == pytest.approx(-384.13, abs=0.05)
    # One joint cannot take a moment: a mechanism, reported rather than graded.
    assert distribute(joints[:1], loads) == []


def test_the_tie_takes_the_landing_piers_out_of_every_lateral_register(catlin_ctx):
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.engineering.registry import keys_of

    ectx = catlin_ctx.engineering.context
    lateral = {p.tag for p in cast_piers(ectx) if p.lateral_system}
    assert not lateral & set(_LANDING)
    assert {"PT-BW-PE", "PT-BW-PNE"} <= lateral
    for kind in ("base_rotation", "column_base", "column_head_joint"):
        assert not set(keys_of(kind, ectx)) & set(_LANDING), kind
    # The interior landing (retired 2026-10-13) relieved no column and never had an item.
    assert keys_of("deck_tie", ectx) == ["FS-BW-FLOOR"]
