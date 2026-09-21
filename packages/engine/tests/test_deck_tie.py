"""``engineering/deck_tie.py`` against ``houses/catlin/notes/north_entry_piers.md`` §10.

The note was worked by hand before the module: the tie line as a bolt group, the landing's
loads placed where they act, and FL11473's interaction per joint.
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
    return next(s for s in record.limit_states if s.name == name)


def _input(record, prefix):
    return next(q.value for q in record.inputs if q.name.startswith(prefix))


def test_the_tie_is_derived_from_the_authored_hardware(catlin_ctx):
    """§10a: two joints, a pair each, over the stem core at y = 43.6771'."""
    ectx = catlin_ctx.engineering.context
    joints = wall_ties(ectx, ectx.plan.by_tag("FS-BW-FLOOR"))
    assert [(j.member, j.wall, len(j.parts), j.model, j.wall_axis) for j in joints] == [
        ("BM-BW-FC", "W-GF-S1", 2, "HGAM10", "x"),
        ("BM-BW-FE", "W-GF-S-DR", 2, "HGAM10", "x")]
    assert [round(j.x_ft, 4) for j in joints] == [7.125, 9.4583]
    assert all(j.y_ft == pytest.approx(43.6771, abs=1e-4) for j in joints)


def test_the_loads_reproduce_section_10b(catlin_ctx):
    record = catlin_ctx.engineering[_ITEM]
    assert _input(record, "x:FS-BW-FLOOR deck wind") == pytest.approx(110.08, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN face") == pytest.approx(407.50, abs=0.01)
    assert _input(record, "x:W-BW-SCREEN-SKIRT face") == pytest.approx(112.27, abs=0.01)
    assert _input(record, "y:FS-BW-FLOOR deck wind") == pytest.approx(310.56, abs=0.01)
    assert _input(record, "y:W-BW-SCREEN panel share") == pytest.approx(980.74, abs=0.01)


def test_the_verdicts_reproduce_section_10c(catlin_ctx):
    """§10c/§10d: OVER at 1.82 on N-S wind at BM-BW-FC; E-W 1.60; guard 1.30."""
    record = catlin_ctx.engineering[_ITEM]
    assert record.status is Status.OVER
    assert _state(record, "tie interaction, N-S wind").ratio == pytest.approx(1.821, abs=1e-3)
    assert _state(record, "tie interaction, E-W wind").ratio == pytest.approx(1.599, abs=1e-3)
    assert _state(record, "tie interaction, guard").ratio == pytest.approx(1.302, abs=1e-3)
    assert record.governing.name == "tie interaction, N-S wind"
    assert "1,675.4 lb across it / 920.0" in record.governing.citation


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
