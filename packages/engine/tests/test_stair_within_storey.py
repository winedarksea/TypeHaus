"""A stair that passes through no floor, and a stair that is made of something.

``Stair`` took its rise from a pair of storey elevations through a ``FloorOpening`` in the
storey above, and had no other way to state one. A step-down *within* a storey — the garage
service stair, five risers from the slab to the house entry landing — has no deck overhead
and nothing to open, so it could not be a ``Stair`` at all and was authored as a stack of
concrete ``Slab``s. That stack is invisible to every stair rule in the engine:
``structural.stair_riser_uniformity`` and ``code.R311_7_8_handrail`` both iterate
``model.stairs``, so a 5-riser flight with no handrail drew no finding whatsoever.

``Stair`` also carried no material, so the generators' hard-coded 2x12 stringers and tread
boards reached every renderer as the category palette's generic lumber.
"""

from __future__ import annotations

import pytest

from typehaus.model.spatial import Stair
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.stairs.dispatch import _resolve_stair


@pytest.fixture
def one_storey_model(catlin_model):
    """The catlin model, used only for its storey table and wall list."""
    return catlin_model


def _garage_flight(**overrides):
    """Five risers @ 6.8" on 11" treads, 3'-0" wide — the garage service stair."""
    kwargs = dict(
        uid="TESTST01AA", tag="ST-TEST-SERVICE",
        from_storey="garage", to_storey="garage",
        base_elevation=ft(0), top_elevation=inch(34),
        width=ft(3), run_direction="y", start=pt(ft(5), ft(45)),
        tread_depth=inch(11), nosing_depth=inch(1),
    )
    kwargs.update(overrides)
    return Stair(**kwargs)


def _storeys(catlin_model):
    return {s.tag for s in catlin_model.plan.storeys}


def test_a_flight_with_no_opening_resolves_from_its_own_elevations(catlin_model):
    """The case the model could not express: rise stated, not derived from two storeys."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=inch(34))
    resolved, findings = _resolve_stair(catlin_model, stair, storey)
    assert not findings, [f.message for f in findings]
    assert resolved is not None
    assert resolved.riser_count == 5
    assert resolved.riser_height_m == pytest.approx(34 * 0.0254 / 5)


def test_the_flight_bounds_itself_when_no_opening_bounds_it(catlin_model):
    """``outline`` is read by the plan drawing and the room-area deduction alike, and it
    used to be the opening's ring because that was the only footprint there was."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=inch(34),
                           start=pt(ft(5), ft(45)), run_direction="y")
    resolved, _ = _resolve_stair(catlin_model, stair, storey)
    xs = [x for x, _y in resolved.outline]
    ys = [y for _x, y in resolved.outline]
    # 3'-0" across the run, and four goings (11" tread less a 1" nose) along it.
    assert max(xs) - min(xs) == pytest.approx(ft(3).meters)
    assert max(ys) - min(ys) == pytest.approx(4 * inch(10).meters)
    assert min(ys) == pytest.approx(ft(45).meters)


def test_half_an_explicit_rise_is_an_authoring_error(catlin_model):
    """Both ends or neither — a flight that states one is stating nothing."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=None)
    resolved, findings = _resolve_stair(catlin_model, stair, storey)
    assert resolved is None
    assert findings and findings[0].check_id == "integrity.stair_rise"


def test_no_opening_and_no_elevations_is_an_authoring_error(catlin_model):
    """Without a hole *and* without stated ends there is no rise to be had."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=None, top_elevation=None)
    resolved, findings = _resolve_stair(catlin_model, stair, storey)
    assert resolved is None
    assert findings and findings[0].check_id == "integrity.stair_rise"


def test_no_opening_needs_a_start(catlin_model):
    """The opening used to supply the origin; with none, the flight must say where it is."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=inch(34), start=None)
    resolved, findings = _resolve_stair(catlin_model, stair, storey)
    assert resolved is None
    assert findings and findings[0].check_id == "integrity.stair_opening"


def test_the_flights_material_reaches_every_member_it_generated(catlin_model):
    """Stringers, treads and anything the bearing pass posts down under them alike."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=inch(34), material="kdat")
    resolved, findings = _resolve_stair(catlin_model, stair, storey)
    assert not findings, [f.message for f in findings]
    assert resolved.members
    assert {member.material for member in resolved.members} == {"kdat"}


def test_an_unstated_material_leaves_every_member_exactly_as_it_was(catlin_model):
    """The whole existing house renders off the category palette; nothing may move."""
    storey = sorted(_storeys(catlin_model))[0]
    stair = _garage_flight(from_storey=storey, to_storey=storey,
                           base_elevation=ft(0), top_elevation=inch(34))
    resolved, _ = _resolve_stair(catlin_model, stair, storey)
    assert {member.material for member in resolved.members} == {None}


def test_the_existing_house_stairs_are_untouched(catlin_model):
    """Three authored stairs, all through openings, all still resolving as they did."""
    tags = {stair.tag for stair in catlin_model.stairs}
    assert {"ST-B2M", "ST-M2S", "ST-S2A"} <= tags
    for stair in catlin_model.stairs:
        assert stair.riser_count > 0 and stair.members
