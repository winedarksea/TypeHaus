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
    """§10p: FE into W-G-S as two joints (a DTT pair N-S, an HL43 pair E-W), the screen's
    MSTA49Z collector into W-G-W; all wet, wood to wood."""
    ectx = catlin_ctx.engineering.context
    joints = wall_ties(ectx, ectx.plan.by_tag("FS-BW-FLOOR"))
    assert [(j.member, j.wall, len(j.parts), j.model, j.wall_axis, j.heel_axis,
             j.on_concrete, j.service_condition) for j in joints] == [
        ("BM-BW-FE", "W-G-S", 2, "DTT2Z", "x", "y", False, None),
        ("BM-BW-FE", "W-G-S", 2, "HL43HDG", "x", None, False, None),
        ("W-BW-SCREEN", "W-G-W", 1, "MSTA49Z", "y", "y", False, None)]
    assert [round(j.x_ft, 4) for j in joints] == [9.7187, 9.3958, 6.0365]
    assert [round(j.y_ft, 4) for j in joints] == [43.3125, 43.1458, 43.1458]


def test_the_loads_reproduce_section_10b(catlin_ctx):
    record = catlin_ctx.engineering[_ITEM]
    # The landing's OWN edge band (§10b): 8.19" of joist and board (2026-10-15, §10i), not TR-SG-FASCIA.
    # The deck's south edge moved 5/8" north for D-M-ENTRY's sill beam (2026-11-17).
    assert _input(record, "x:FS-BW-FLOOR deck wind") == pytest.approx(66.8159, abs=0.01)
    # The screen's south end moved 1/2" north, clear of D-M-ENTRY's casing (2026-11-18).
    assert _input(record, "x:W-BW-SCREEN face") == pytest.approx(402.485, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN-SKIRT face") == pytest.approx(111.026, abs=0.01)
    # §10o (2026-11-18): the landing is 3.3177' wide and the seat beams 3.0511' long, the
    # column line 3/16" west behind the garage's 7/16" ZIP.
    assert _input(record, "y:FS-BW-FLOOR deck wind") == pytest.approx(90.355, abs=0.01)
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(1034.57, abs=0.1)
    canopy = catlin_ctx.engineering["lateral_system/RF-BW-CANOPY"]
    delivered = next(q.value for q in canopy.inputs if q.name == "delivered_shear_y")
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(delivered)


def test_the_verdicts_reproduce_section_10p(catlin_ctx):
    """§10p: the screen's strap governs N-S at 0.734; E-W is the HL43's at 0.574."""
    record = catlin_ctx.engineering[_ITEM]
    assert record.status is Status.OK
    assert record.governing.name == "tie interaction, N-S wind"
    ns = _state(record, "tie interaction, N-S wind")
    assert ns.ratio == pytest.approx(0.7338, abs=5e-4)
    assert "W-BW-SCREEN at W-G-W" in ns.citation
    ew = _state(record, "tie interaction, E-W wind")
    assert ew.ratio == pytest.approx(0.5737, abs=5e-4)
    assert "owner-accepted" in ew.citation
    assert _state(record, "tie interaction, guard").ratio == pytest.approx(0.4422, abs=5e-4)


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
    """§10a/§10p: heel across the wall reads F1 across; a vertical heel carries F1 along the
    wall only (owner-accepted reading, 2026-11-23); a tension tie carries its own axis only;
    C_M 0.70 unless the parts author dry service."""
    from typehaus.engineering.deck_tie import capacity

    stem = capacity(TieJoint("FE", "S-DR", ("a", "b"), "HL35HDG", 0, 0, "x", "y"))
    wet = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False))
    dry = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False,
                            "dry", "covered"))
    mixed = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False,
                              "mixed"))
    fe = capacity(TieJoint("FE", "G-S", ("a", "b"), "HL43HDG", 0, 0, "x", None, False,
                           member_axis="y"))
    dtt = capacity(TieJoint("FE", "G-S", ("a", "b"), "DTT2Z", 0, 0, "x", "y", False))
    strap = capacity(TieJoint("SC", "G-W", ("a",), "MSTA49Z", 0, 0, "y", "y", False))
    assert (stem.along_lb, stem.across_lb) == pytest.approx((518.0, 917.0))
    assert (wet.along_lb, wet.across_lb) == pytest.approx((728.0, 0.0))
    assert (dry.along_lb, dry.across_lb) == pytest.approx((1040.0, 0.0))
    assert (fe.along_lb, fe.across_lb) == pytest.approx((1011.5, 0.0))
    assert (dtt.along_lb, dtt.across_lb) == pytest.approx((0.0, 1277.5))
    assert (strap.along_lb, strap.across_lb) == pytest.approx((1414.0, 0.0))
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
    # §10p: each direction shared among the joints that carry it (strap and DTT N-S only,
    # HL43 E-W only). Strap Y = 562.46 + 1,749.69 x 1.841146 / 6.779637 = 1,037.6 lb.
    tie = [TieJoint("S", "G-W", ("a",), "MSTA49Z", 6.036458, 43.1458, "y"),
           TieJoint("D", "G-S", ("a",), "DTT2Z", 9.71875, 43.3125, "x"),
           TieJoint("H", "G-S", ("a",), "HL43HDG", 9.395833, 43.1458, "x")]
    ns = [Load("screen", 0.0, 1034.57, 6.182292, 39.9), Load("deck", 0.0, 90.35, 7.924479, 39.9)]
    (_, ys), (_, yd), (xh, yh) = distribute(tie, ns, 1.0, [(False, True), (False, True),
                                                            (True, False)])
    assert ys == pytest.approx(1037.6, abs=0.2) and yd == pytest.approx(87.3, abs=0.2)
    assert (xh, yh) == (0.0, 0.0)


def test_the_tie_takes_the_landing_piers_out_of_every_lateral_register(catlin_ctx):
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.engineering.registry import keys_of

    ectx = catlin_ctx.engineering.context
    lateral = {p.tag for p in cast_piers(ectx) if p.lateral_system}
    assert not lateral & set(_LANDING)
    assert not {"PT-BW-PE", "PT-BW-PNE"} & lateral, "short poles since decision 16"
    for kind in ("base_rotation", "column_base", "column_head_joint"):
        assert not set(keys_of(kind, ectx)) & set(_LANDING), kind
    # The interior landing (retired 2026-10-13) relieved no column and never had an item.
    assert keys_of("deck_tie", ectx) == ["FS-BW-FLOOR"]
