"""R303.8 is graded against the top LANDING, which is a surface, not a radius.

The rule's whole text is "exterior stairways shall be provided with an artificial light
source located at the top landing of the stairway" — no illuminance, no switching, and no
distance from the treads. It was being graded against R303.7's shape instead: a 4'-0"
buffer of the flight outline. On this house those are different verdicts. ST-SG-PORCH
arrives on FS-SG-PORCH, a 171 sf porch deck, and the two fixtures that light that deck —
ED-M-PORCH-FAN over it and ED-M-PORCH-FLOOD on its north edge — stand ten feet from the
top nosing, outside any ring drawn round the treads.

What is pinned here is that the landing does the work and that it did not cost the rule its
teeth: the stair is lit by fixtures the ring cannot reach, and a landing with nothing over
it still FAILs.
"""

from __future__ import annotations

import contextlib

import pytest

PORCH_STAIR = "ST-SG-PORCH"
PORCH_DECK = "FS-SG-PORCH"
DECK_LIGHTS = ("ED-M-PORCH-FAN", "ED-M-PORCH-FLOOD")
STEP_LIGHT = "ED-M-STAIR-LT"


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    from typehaus.checks import build_context

    context, _findings = build_context(catlin_plan)
    return context


@contextlib.contextmanager
def _without_lights(ctx, tags: set[str]):
    """Drop luminaires from the AUTHORED plan for the body of a test.

    ``_lights_near`` censuses ``ctx.plan.storey_elements``; the resolved model supplies
    elevations only, so removing a ``ResolvedCanvasObject`` hides nothing from this rule.
    """
    original = dict(ctx.plan.elements)
    try:
        ctx.plan.elements.update({
            storey: tuple(e for e in group if getattr(e, "tag", None) not in tags)
            for storey, group in original.items()
        })
        yield
    finally:
        ctx.plan.elements.clear()
        ctx.plan.elements.update(original)


def _porch_finding(ctx):
    from typehaus.checks.code.mn_residential.illumination import (
        exterior_stairway_illumination,
    )

    return next(f for f in exterior_stairway_illumination(ctx)
                if PORCH_STAIR in f.message)


def test_the_porch_deck_is_the_stairs_arrival_surface(ctx):
    """The landing is found on elevation and adjacency, not on a storey name.

    FS-SG-PORCH's storey is ``court-main`` and the stair's is ``main``, so a name match
    would find nothing. Its deck top is the stair's own ``arrival_elevation_m`` and it lies
    one wall-thickness from the top nosing — W-SG-E1's 12" top is the threshold between
    them, which is why the tolerance is a foot and a half and not an inch.
    """
    from shapely.geometry import Polygon

    stair = next(s for s in ctx.model.stairs if s.tag == PORCH_STAIR)
    deck = next(f for f in ctx.model.floors if f.tag == PORCH_DECK)
    outline = Polygon([p.xy_m if hasattr(p, "xy_m") else p for p in deck.deck_outline])

    assert deck.deck_z1_m == pytest.approx(stair.arrival_elevation_m, abs=1e-9)
    assert outline.distance(Polygon(stair.outline)) == pytest.approx(0.3048, abs=1e-3)


def test_the_deck_lights_are_out_of_reach_of_the_flight_ring(ctx):
    """The premise: without the landing these two fixtures are not near this stair.

    If either ever falls inside the 4'-0" ring the test below stops proving anything, so
    the distance is asserted rather than assumed.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.checks.code.mn_residential.illumination import _STAIR_LIGHT_REACH

    stair = next(s for s in ctx.model.stairs if s.tag == PORCH_STAIR)
    ring = Polygon(stair.outline).buffer(_STAIR_LIGHT_REACH.meters)
    for tag in DECK_LIGHTS:
        light = next(o for o in ctx.model.canvas_objects if o.tag == tag)
        assert not ring.covers(Point(*light.position)), tag


def test_the_porch_stair_is_lit_by_what_stands_over_its_landing(ctx):
    """...and yet the stair is lit, because those fixtures are on the landing R303.8 names."""
    assert "is lit at its top landing" in _porch_finding(ctx).message


def test_a_landing_with_nothing_over_it_still_fails(ctx):
    """The correction is a widening, not an amnesty.

    Every luminaire that reaches this stair is dropped from the authored plan — the two
    over the deck and the fitting at the head of the flight — and the rule reports the stair
    unlit.
    """
    with _without_lights(ctx, {*DECK_LIGHTS, STEP_LIGHT}):
        finding = _porch_finding(ctx)
    assert "has no light at its top landing" in finding.message


def test_a_stair_with_no_modelled_landing_still_grades_on_the_ring(ctx):
    """A flight whose arrival deck the model does not carry is graded as it always was.

    ``_landing_region`` unions; it never replaces. Fed an elevation no deck in the house
    matches, it hands back the ring it was given — which is what keeps this a correction to
    one rule's shape rather than a new dependency on floor geometry.
    """
    from shapely.geometry import Polygon

    from typehaus.checks.code.mn_residential.illumination import _landing_region

    stair = next(s for s in ctx.model.stairs if s.tag == PORCH_STAIR)
    ring = Polygon(stair.outline).buffer(0.5)
    assert _landing_region(ctx, stair, ring, 1000.0) is ring
    assert _landing_region(ctx, stair, ring, None) is ring
    assert _landing_region(ctx, stair, ring, stair.arrival_elevation_m).area > ring.area


def test_the_step_light_is_not_what_carries_the_verdict(ctx):
    """ED-M-STAIR-LT moved back onto W-M-S2 and the stair is still lit without it.

    The house's own record of why (``plan/lighting.py``): the fitting is at the head of the
    flight for the person on it, not because R303.8 has nowhere else to look.
    """
    with _without_lights(ctx, {STEP_LIGHT}):
        finding = _porch_finding(ctx)
    assert "is lit at its top landing" in finding.message
