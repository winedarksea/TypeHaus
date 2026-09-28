"""``structural.stair_stringer`` / ``structural.stair_tread_span`` against catlin's flights.

Reproduces ``houses/catlin/notes/stair_stringer_basis.md`` §3–§5, and first of all asks
whether the rule would have caught what it exists for: ST-S2A's 10'-0" run on sawn 2x12s.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus.checks.structural.stair_stringers import (
    CHECK_ID,
    _flights,
    _grade,
    _run_in,
    _throat_in,
    stair_stringer,
    stair_tread_span,
)
from typehaus.findings import Result


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


def _restring(stair, profile):
    """The same flight with every stringer re-sectioned."""
    return replace(stair, members=tuple(
        replace(m, profile=profile) if m.category == "stringer" else m
        for m in stair.members))


def test_catlin_passes_both_rules(catlin_model):
    ctx = check_context(model=catlin_model)
    findings = stair_stringer(ctx) + stair_tread_span(ctx)
    assert findings and all(f.result is Result.PASS for f in findings), [
        f.message for f in findings if f.result is not Result.PASS]
    [s2a] = [f for f in findings if f.check_id == CHECK_ID and "ST-S2A" in f.element_tags]
    assert "10.00' <= 11.67'" in s2a.message


@pytest.mark.parametrize(("tag", "run_in", "throat_in"), [
    ("ST-B2M", 60.0, 5.32), ("ST-M2S", 70.0, 5.23), ("ST-S2A", 120.0, 5.875)])
def test_hand_numbers(catlin_model, tag, run_in, throat_in):
    """§3's table: every flight's free run and its notch throat."""
    stair = _stair(catlin_model, tag)
    for members in _flights(stair).values():
        assert max(_run_in(m) for m in members) == pytest.approx(run_in, abs=0.01)
        assert _throat_in(stair, members[0].profile) == pytest.approx(throat_in, abs=0.01)


@pytest.mark.parametrize("tag", ["ST-B2M", "ST-M2S", "ST-S2A"])
def test_interior_flights_carry_three_stringers(catlin_model, tag):
    for members in _flights(_stair(catlin_model, tag)).values():
        assert len(members) == 3


def test_sawn_2x12_at_the_attic_flight_fails(catlin_model):
    """The state the note retires: sawn 2x12s over a 10'-0" run."""
    stair = _restring(_stair(catlin_model, "ST-S2A"), "2x12")
    authored = catlin_model.plan.by_tag("ST-S2A")
    [(flight, members)] = _flights(stair).items()
    finding = _grade(stair, authored, flight, members)
    assert finding.result is Result.FAIL
    assert "10.00' horizontally, past 6'-0\"" in finding.message


@pytest.mark.parametrize(("update", "reason"), [
    ({"stringer_spacing": None}, "o.c. spacing"),
    ({"width": None}, "carried span"),
])
def test_the_row_refuses_a_drifted_flight(catlin_model, update, reason):
    stair = _stair(catlin_model, "ST-S2A")
    authored = catlin_model.plan.by_tag("ST-S2A")
    authored = authored.model_copy(update=update)
    [(flight, members)] = _flights(stair).items()
    finding = _grade(stair, authored, flight, members)
    assert finding.result is Result.UNKNOWN
    assert reason in finding.message


def test_the_row_refuses_a_retype_and_a_deeper_notch(catlin_model):
    stair = _stair(catlin_model, "ST-S2A")
    authored = catlin_model.plan.by_tag("ST-S2A")
    shallower = _restring(stair, "1.75x9.5 LSL")
    [(flight, members)] = _flights(shallower).items()
    assert _grade(shallower, authored, flight, members).result is Result.UNKNOWN
    row = authored.published_stringer_span.model_copy(update={"min_throat_in": 6.0})
    [(flight, members)] = _flights(stair).items()
    finding = _grade(stair, authored.model_copy(update={"published_stringer_span": row}),
                     flight, members)
    assert finding.result is Result.UNKNOWN and "throat" in finding.message


def test_a_flight_ledgered_throughout_does_not_span(catlin_model):
    stair = _stair(catlin_model, "ST-SG-PORCH")
    carried = replace(stair, members=tuple(
        replace(m, connection="concrete-wall-hanger:W-TEST") if m.category == "stringer"
        else m for m in stair.members))
    [(flight, members)] = _flights(carried).items()
    finding = _grade(carried, None, flight, members)
    assert finding.result is Result.PASS and "ledgered" in finding.message
