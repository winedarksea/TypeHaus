"""``engineering/column_head_joint.py`` against ``houses/catlin/notes/north_entry_piers.md`` §9.

The note was worked by hand before the module. Section capacities are pinned to the note's
numbers; demands are pinned where the note quotes an upstream record, and re-derived off
the resolved piers where they are a plain load sum another stream may move.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.engineering.column_head_geometry import (
    BeamFrame,
    confinement_ratio,
    lever_in,
    seat_centroid,
)
from typehaus.engineering.item import Status
from typehaus.model import HeadConnector
from typehaus.model.structure import Post
from typehaus.quantities import pt

#: The four landing piers left on 2026-09-21: the landing is tied to the garage stem
#: (§10) and they lean, so they have no head joint to grade (`test_deck_tie.py`).
_HEADS = ("PT-BW-RE", "PT-BW-RNE", "PT-SG-BF1", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3")


def _record(ctx, tag):
    return ctx.engineering[f"column_head_joint/{tag}"]


def _state(record, prefix):
    return next(s for s in record.limit_states if s.name.startswith(prefix))


def _input(record, name):
    return next(q.value for q in record.inputs if q.name == name)


def test_every_lateral_column_is_computed_and_none_is_deferred(catlin_ctx):
    from typehaus.engineering.deferred import DEFERRALS
    from typehaus.engineering.registry import keys_of

    assert "column_head_joint" not in DEFERRALS
    assert tuple(keys_of("column_head_joint", catlin_ctx.engineering.context)) == _HEADS
    for tag in _HEADS:
        assert _record(catlin_ctx, tag).status != Status.NO_CALC


def test_section_capacities_reproduce_9d_9e_9f(catlin_ctx):
    """φV_c, A_v,min, φT_th and φB_n — the note's arithmetic, one column's worth."""
    record = _record(catlin_ctx, "PT-SG-BR1")
    assert _state(record, "column shear").capacity == pytest.approx(12_218.8, abs=0.1)
    assert _state(record, "A_v,min").demand == pytest.approx(0.10607, abs=1e-5)
    assert _state(record, "A_v,min").capacity == pytest.approx(0.22)
    assert _state(record, "column torsion").capacity == pytest.approx(1_499.47, abs=0.01)
    assert _state(record, "bearing at the seat").capacity == pytest.approx(67_681.25)


def test_the_head_is_asked_for_no_moment_and_says_so(catlin_ctx):
    state = _state(_record(catlin_ctx, "PT-BW-RE"), "head moment")
    assert state.is_detailing and state.ratio == pytest.approx(0.952, abs=1e-3)
    assert "R6.2.5" in state.citation


def test_canopy_columns_reproduce_9b_9c_9e(catlin_ctx):
    for tag in ("PT-BW-RE", "PT-BW-RNE"):
        record = _record(catlin_ctx, tag)
        assert record.status == Status.OK
        lateral = _state(record, "connector lateral, wind")
        assert lateral.demand == pytest.approx(410.66, abs=0.05)
        assert lateral.capacity == 460.0 and lateral.ratio == pytest.approx(0.893, abs=1e-3)
        assert _state(record, "connector uplift").demand == pytest.approx(433.25, abs=0.1)
        assert _state(record, "connector uplift").capacity == 585.0
        assert _state(record, "column shear").demand == pytest.approx(826.95, abs=0.1)
        torsion = _state(record, "column torsion")
        assert torsion.demand == pytest.approx(44.46, abs=0.01)
        assert _input(record, "torsion_lever") == pytest.approx(2.25)
        assert _input(record, "combined_unity_unverified") == pytest.approx(1.263, abs=1e-3)
    assert _input(_record(catlin_ctx, "PT-BW-RE"), "seat_eccentricity") == pytest.approx(0.875)
    assert _input(_record(catlin_ctx, "PT-BW-RNE"), "seat_eccentricity") == pytest.approx(0.0)


def test_guard_columns_grade_the_guard_at_cd_one(catlin_ctx):
    for tag in ("PT-SG-BF1", "PT-SG-BR3"):
        record = _record(catlin_ctx, tag)
        assert record.status == Status.OK
        guard = _state(record, "connector lateral, guard")
        assert guard.capacity == pytest.approx(287.5)
        assert guard.ratio == pytest.approx(0.6957, abs=1e-4)
        assert not any(s.name == "connector uplift" for s in record.limit_states)
    sg = _record(catlin_ctx, "PT-SG-BR1")
    assert _state(sg, "column torsion").demand == pytest.approx(46.67, abs=0.01)


def test_bearing_demand_is_the_head_reaction(catlin_ctx):
    from typehaus.engineering.pier_basis import cast_piers

    piers = {p.tag: p for p in cast_piers(catlin_ctx.engineering.context)}
    for tag in _HEADS:
        pier = piers[tag]
        expected = 1.2 * (pier.dead_lb - pier.self_weight_lb) + 1.6 * pier.live_lb
        assert _state(_record(catlin_ctx, tag), "bearing").demand == pytest.approx(expected)


def test_the_prop_reaction_is_exported_not_back_solved(catlin_ctx):
    from typehaus.engineering.lateral_system import column_head_reactions
    from typehaus.engineering.roof_moment import frame_cases_of

    heads = column_head_reactions(catlin_ctx.engineering.context)
    for case in frame_cases_of("RF-BW-CANOPY"):
        share = case.columns_governing.shares["PT-BW-RE"]
        assert heads["PT-BW-RE"][case.axis] == pytest.approx(share * case.diaphragm_shear_lb)


# --- geometry, independent of the house ---------------------------------------------------

def _frame(start=(-43.0, 0.0), length=43.0, width=3.0):
    return BeamFrame(tag="BM", origin=start, u=(1.0, 0.0), length_in=length, width_in=width)


def test_a_centred_square_plate_confines_at_2_42():
    assert confinement_ratio(_frame(start=(-20.0, 0.0), length=40.0), (0.0, 0.0), 3.5, 3.5,
                             6.0) == pytest.approx(2.4244, abs=1e-4)


def test_a_beam_ending_on_the_axis_seats_half_the_pack():
    assert seat_centroid(_frame(), (0.0, 0.0), 3.5, 3.5) == pytest.approx((-0.875, 0.0))
    assert seat_centroid(_frame(), (5.0, 0.0), 3.5, 3.5) is None


def test_a_torque_lever_is_the_perpendicular_offset():
    points = [(0.0, 2.25), (0.0, -2.25)]
    assert lever_in(points, (1.0, 0.0)) == pytest.approx(2.25)
    assert lever_in(points, (0.0, 1.0)) == pytest.approx(0.0)
    assert lever_in(points, None) == pytest.approx(2.25)


# --- the model field and its integrity cross-check ----------------------------------------

_HGAM = dict(tie="HGAM10", tie_count=2, uplift_lb=585.0, lateral_lb=460.0,
             load_duration_factor=1.6, bearing="SS316-SHIM-35", bearing_width_in=3.5,
             bearing_length_in=3.5, source="FL11473 Table 1")


def test_head_connector_round_trips_on_a_post():
    post = Post(uid="XXXXXXXXXX", tag="PT-X", position=pt(0, 0),
                head_connector=HeadConnector(**_HGAM))
    restored = Post.model_validate(post.model_dump())
    assert restored == post and restored.head_connector.lateral_lb == 460.0
    head = post.head_connector
    assert HeadConnector.model_validate_json(head.model_dump_json()) == head


@pytest.mark.parametrize("bad", [{"source": " "}, {"tie_count": 0}, {"lateral_lb": 0.0},
                                 {"bearing_length_in": None}])
def test_a_half_quoted_connector_is_refused(bad):
    with pytest.raises(ValueError):
        HeadConnector(**{**_HGAM, **bad})


def _integrity(head):
    from typehaus.checks.integrity.head_connector import head_connector_agrees

    post = Post(uid="XXXXXXXXXX", tag="PT-X", position=pt(0, 0), head_connector=head)
    return head_connector_agrees(SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [post])))


def test_quoted_values_agree_with_the_catalog():
    assert _integrity(HeadConnector(**_HGAM)) == []


def test_a_quoted_795_is_an_error():
    findings = _integrity(HeadConnector(**{**_HGAM, "lateral_lb": 795.0}))
    assert len(findings) == 1 and "lateral_lb" in findings[0].message
    assert findings[0].severity.value == "error"
