"""``engineering/deck_tie.py`` against ``houses/catlin/notes/north_entry_piers.md`` §10.

The note was worked by hand before the module: the tie joints as a bolt group, the landing's
loads placed where they act, the HL33HDG's interaction per joint and ACI 318 Ch. 17 on the
stem anchors (§10a-§10e).
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
    """§10a: three joints, a pair each — two over the stem core, one into W-G-W."""
    ectx = catlin_ctx.engineering.context
    joints = wall_ties(ectx, ectx.plan.by_tag("FS-BW-FLOOR"))
    assert [(j.member, j.wall, len(j.parts), j.model, j.wall_axis, j.heel_axis,
             j.on_concrete) for j in joints] == [
        ("BM-BW-FC", "W-GF-S1", 2, "HL33HDG", "x", "y", True),
        ("BM-BW-FE", "W-GF-S-DR", 2, "HL33HDG", "x", "y", True),
        ("W-BW-SCREEN", "W-G-W", 2, "HL33HDG", "y", None, False)]
    assert [round(j.x_ft, 4) for j in joints] == [7.125, 9.4583, 6.1979]
    assert [round(j.y_ft, 4) for j in joints] == [43.6771, 43.6771, 43.1458]


def test_the_loads_reproduce_section_10b(catlin_ctx):
    record = catlin_ctx.engineering[_ITEM]
    # The landing's OWN edge band (§10b): 8 1/4" of joist and board, not TR-SG-FASCIA.
    assert _input(record, "x:FS-BW-FLOOR deck wind") == pytest.approx(68.61, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN face") == pytest.approx(407.50, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN-SKIRT face") == pytest.approx(112.27, abs=0.01)
    assert _input(record, "y:FS-BW-FLOOR deck wind") == pytest.approx(103.14, abs=0.01)
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(980.74, abs=0.01)


def test_the_verdicts_reproduce_section_10c(catlin_ctx):
    """§10c/§10d: still OVER, at 1.18 on E-W wind at BM-BW-FE; N-S 0.89; guard 1.04."""
    record = catlin_ctx.engineering[_ITEM]
    assert record.status is Status.OVER
    assert _state(record, "tie interaction, N-S wind").ratio == pytest.approx(0.886, abs=1e-3)
    assert _state(record, "tie interaction, E-W wind").ratio == pytest.approx(1.177, abs=1e-3)
    assert _state(record, "tie interaction, guard").ratio == pytest.approx(1.040, abs=1e-3)
    assert record.governing.name == "tie interaction, E-W wind"
    assert "132.4 lb along the wall / 518.0 + 671.0 lb across it / 728.0" in (
        record.governing.citation)


def test_the_stem_anchors_reproduce_section_10e(catlin_ctx):
    """§10e: ACI 318-19 Ch. 17 on the Titen HDs, worst at BM-BW-FE under E-W wind."""
    record = catlin_ctx.engineering[_ITEM]
    assert _state(record, "wall anchors, tension").ratio == pytest.approx(0.5455, abs=5e-4)
    assert _state(record, "wall anchors, shear").ratio == pytest.approx(0.3682, abs=5e-4)
    assert _state(record, "wall anchors, tension-shear").ratio == pytest.approx(0.7614,
                                                                                abs=5e-4)
    assert _state(record, "wall anchor edge").capacity == pytest.approx(3.0)
    assert _state(record, "wall anchor spacing").capacity == pytest.approx(7.5)


def test_the_hl_reading_by_heel():
    """§10a: heel across the wall reads F1 across; a vertical heel doubles uplift along."""
    from typehaus.engineering.deck_tie import capacity

    stem = capacity(TieJoint("FE", "S-DR", ("a", "b"), "HL33HDG", 0, 0, "x", "y"))
    screen = capacity(TieJoint("SC", "G-W", ("a", "b"), "HL33HDG", 0, 0, "y", None, False))
    assert (stem.along_lb, stem.across_lb) == pytest.approx((518.0, 728.0))
    assert (screen.along_lb, screen.across_lb) == pytest.approx((1036.0, 518.0))


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
    assert {"PT-BW-RE", "PT-BW-RNE"} <= lateral
    for kind in ("base_rotation", "column_base", "column_head_joint"):
        assert not set(keys_of(kind, ectx)) & set(_LANDING), kind
    # The interior landing rides the same carriers but relieved no column: no item.
    assert keys_of("deck_tie", ectx) == ["FS-BW-FLOOR"]
