"""R311.7.5.1 at the two ends of a flight — the risers nothing used to measure.

A flight's interior is uniform by construction: the generator lays every tread on the same
design rise, so ``structural.stair_riser_uniformity`` can only ever find a generator bug
there. The building is at the two ends, where the flight meets a floor it did not draw, and
both older rules close the loop on the flight's own design riser rather than on that floor.

catlin's ST-B2M is the case this exists for. It derived its rise from the storey table,
which on a wood bay is the TOP OF JOISTS, so it climbed 9'-1 7/16" to the joists and left an
8 1/4" step onto a living-room floor 15/16" higher — over R311.7.5.1's 7 3/4" cap and its
3/8" spread, and PASSING in both older checks. The first test below reproduces exactly that
and asserts the new rule fails it; the rest pin the pieces it is built from.
"""

from __future__ import annotations

import pytest

from typehaus.checks.code.mn_residential.stairs import stair_end_risers, stair_geometry
from typehaus.checks.structural.stairs import stair_riser_uniformity
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.walking_surface import (
    deck_owning_opening,
    room_finish_at,
    surfaces_at,
)

from _helpers import check_context

_FT = 0.3048
_IN = 0.0254


def _by_tag(findings, tag):
    return next(f for f in findings if tag in f.message)


def _with_element_replaced(plan, tag, **updates):
    """A copy of ``plan`` with one element swapped for an edited copy of itself.

    ``PlanModel.elements`` is a storey-keyed mapping of frozen tuples and there is no
    in-place edit; rebuilding the mapping is the supported move (model elements are
    pydantic, so ``model_copy`` and not ``dataclasses.replace``).
    """
    rebuilt = {}
    for storey, group in plan.elements.items():
        rebuilt[storey] = tuple(
            element.model_copy(update=updates)
            if getattr(element, "tag", None) == tag else element
            for element in group)
    return plan.model_copy(update={"elements": rebuilt})


# ------------------------------------------------------------------ 1. the regression
def test_a_flight_stopping_at_the_joist_tops_fails(catlin_plan):
    """ST-B2M, rewound to the datum-derived rise that shipped until 2026-09-11.

    ``top_elevation`` back at 0'-0" is precisely what omitting both fields used to compute,
    so this is the real historical geometry and not a synthetic one. The FAIL has to name
    the 8.28" riser: a spread-only message would not tell the reader the step is also over
    the absolute cap.
    """
    rewound = _with_element_replaced(catlin_plan, "ST-B2M", top_elevation=inch(0.0))
    ctx = check_context(plan=rewound)
    finding = _by_tag(stair_end_risers(ctx), "ST-B2M")
    assert finding.result is Result.FAIL
    assert "8.28" in finding.message and "7.75" in finding.message

    # And the two rules that already existed still pass it — which is the whole point.
    assert _by_tag(stair_geometry(ctx), "ST-B2M").result is Result.PASS
    assert _by_tag(stair_riser_uniformity(ctx), "ST-B2M").result is Result.PASS


# ------------------------------------------------------------- 2. the house as it stands
def test_every_catlin_flight_meets_its_floors(catlin_model):
    """All six flights, both ends, measured — no UNKNOWN and no FAIL.

    An UNKNOWN here is not a lesser pass: it means the surface at one end of a flight is not
    in the model, which is what the porch stair's deliberately unmodelled threshold board
    would report if the probe reach were shorter than R311.7.6's landing.
    """
    findings = stair_end_risers(check_context(model=catlin_model))
    assert {f.result for f in findings} == {Result.PASS}
    assert len(findings) == len(catlin_model.stairs) == 6


def test_the_end_risers_equal_the_design_riser_exactly(catlin_model):
    """Every flight is drawn between the two surfaces it really meets, to the micron.

    Not a restatement of the PASS above: that allows R311.7.5.1's 3/8". Nothing in this
    house should be spending any of it, and a flight that starts to is a flight whose ends
    have drifted from its floors.
    """
    ctx = check_context(model=catlin_model)
    for finding in stair_end_risers(ctx):
        assert "within 0.00\"" in finding.message, finding.message


# ------------------------------------------------------- 3. the walking-surface helper
def test_a_storey_datum_is_not_a_walking_surface(catlin_model):
    """The 15/16" this whole rule turns on: joist tops, subfloor, then the plank."""
    deck = deck_owning_opening(catlin_model, "main", "FO-M-STAIR")
    assert deck is not None
    _tag, deck_top = deck
    storey = catlin_model.plan.storey("main")
    assert storey.elevation.meters == pytest.approx(0.0)
    # The subfloor sheet is 3/4" of the gap...
    assert deck_top == pytest.approx(inch(0.75).meters, abs=1e-9)
    # ...and RM-M-LIVING's plank is the rest.
    room, finish, depth = room_finish_at(catlin_model, "main", (12.0 * _FT, 26.4 * _FT))
    assert (room, finish) == ("RM-M-LIVING", "lvp")
    assert deck_top + depth * _IN == pytest.approx(inch(0.9862).meters, abs=1e-6)


def test_a_coating_is_a_sourced_zero_not_a_missing_number(catlin_model):
    """RM-B-STAIR is sealed concrete: the slab top IS the surface, and that is authored.

    ``Material.coating`` already said a sealer has no plane of its own, so the finish depth
    is 0.0 rather than ``None`` — the difference between a basement flight that measures and
    one that reports UNKNOWN.
    """
    room, finish, depth = room_finish_at(
        catlin_model, "basement", (15.8 * _FT, 26.4 * _FT))
    assert (room, finish) == ("RM-B-STAIR", "sealed-concrete")
    assert depth == 0.0


def test_an_unstated_finish_depth_is_unknown_not_zero(catlin_model):
    """Strip the plank's thickness and the flight must refuse to answer.

    Falling back to the deck top would under-measure by exactly the number that went
    missing, and would do it silently — a PASS by absence.
    """
    library = catlin_model.plan.library
    stripped = [material.model_copy(update={"finish_thickness_in": None})
                if material.tag == "lvp" else material
                for material in library.materials]
    plan = catlin_model.plan.model_copy(update={
        "library": library.model_copy(update={"materials": tuple(stripped)})})
    ctx = check_context(plan=plan)
    finding = _by_tag(stair_end_risers(ctx), "ST-B2M")
    assert finding.result is Result.UNKNOWN
    assert "'lvp'" in finding.message


def test_surfaces_are_found_across_storey_filing(catlin_model):
    """ST-G-SERVICE is filed on ``garage`` at both ends and arrives on a ``main`` deck.

    A storey-scoped lookup finds only SL-G-FLOOR, 2'-10" under the flight's own foot, and
    reports a 27" top riser. ``surfaces_at`` asks the physical question instead.
    """
    # (8'-3", 46'-8 3/8") is inside the interior landing's sheet, x 6'-7"..9'-11 5/8" since
    # the service door moved into the garage's SW corner (2026-09-11; it was 8'-6"..11'-6").
    found = {surface.deck_tag: surface.deck_top_m
             for surface in surfaces_at(catlin_model, (8.25 * _FT, 46.7 * _FT))}
    assert "SL-G-FLOOR" in found and "FS-BW-GARAGE" in found
    assert found["SL-G-FLOOR"] == pytest.approx(inch(-34).meters, abs=1e-9)
    assert found["FS-BW-GARAGE"] == pytest.approx(0.0, abs=1e-9)


def test_hardscape_counts_as_a_surface_a_flight_foots_on(catlin_model):
    """ST-BW-ENTRY springs from a paver field, which is no deck and no slab."""
    finding = _by_tag(stair_end_risers(check_context(model=catlin_model)), "ST-BW-ENTRY")
    assert finding.result is Result.PASS
    assert "passage floor" in finding.message
