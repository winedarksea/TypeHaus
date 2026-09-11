""""Above the floor" means above the FINISHED floor, and three planes stack under it.

The storey datum is the top of joists. The deck's ``deck_z1_m`` is the top of the subfloor
sheet. The covering stands on that, and only then is it the plane a foot lands on. Every
mount height in the house was measured from the first of those until 2026-09-11 — 15/16" low
on catlin's second storey, 1 1/2" low in the attic, and silent (plans/TODO.md).

The pair that has to stay split is here too: a thicker carpet spends clear height, it does
not lift the joists, so the storey CEILING plane keeps reading the structural floor.
"""

from __future__ import annotations

import pytest

from typehaus.checks.advisory.floor_finish import floor_finish_depth
from typehaus.findings import Result
from typehaus.quantities import ft, inch
from typehaus.resolve.room_floor import (
    room_finished_floor_elevation,
    room_floor_elevation,
)
from typehaus.resolve.walking_surface import surfaces_at

from _helpers import check_context

_IN = 0.0254
_SUBFLOOR_IN = 0.75


def _room(model, tag):
    return next(room for room in model.rooms if room.tag == tag)


def _build_up_in(model, tag) -> float:
    """Inches from the room's structural anchor up to the plane a foot lands on."""
    room = _room(model, tag)
    return (room_finished_floor_elevation(model, room)
            - room_floor_elevation(model, room)) / _IN


# ------------------------------------------------------------------ 1. the three planes
@pytest.mark.parametrize(("tag", "finish_in"), [
    ("RM-S-HALL", 0.2362),    # lvp, 6 mm nominal
    ("RM-A-STUDY", 0.75),     # 4/4 oak
    ("RM-S-BED2", 0.5),       # carpet over a 1/4" cushion
    ("RM-A-STUBATH", 0.0787), # 2 mm sheet vinyl
])
def test_a_floored_room_walks_above_its_storey_datum(catlin_model, tag, finish_in):
    """Datum → subfloor → covering, and the sum is what a height is measured from."""
    room = _room(catlin_model, tag)
    datum = catlin_model.plan.storey(room.storey).elevation.meters
    walked = (room_finished_floor_elevation(catlin_model, room) - datum) / _IN
    assert walked == pytest.approx(_SUBFLOOR_IN + finish_in, abs=1e-4)
    # And the structural answer is neither of the other two planes: it is the wall base, so
    # it misses the subfloor sheet as well as the covering. That is why it is only an anchor.
    assert room_floor_elevation(catlin_model, room) == pytest.approx(datum, abs=1e-6)


def test_a_deck_that_is_its_own_finish_outranks_the_rooms_field_finish(catlin_model):
    """RM-M-LIVING is authored LVP and its centroid lands on polished concrete.

    ``Room.floor_finish`` is the FIELD finish; SL-M-DECK carries its own and its cap top IS
    the finished floor there (params/main_deck.py pins it flush with the plywood beside it).
    Taking the room's finish at that probe stood the plank on top of the polish.
    """
    living = _room(catlin_model, "RM-M-LIVING")
    assert living.floor_finish == "lvp"
    assert _build_up_in(catlin_model, "RM-M-LIVING") == pytest.approx(0.0, abs=1e-9)
    band = next(s for s in surfaces_at(catlin_model, (8.0, 4.0))
                if s.deck_tag == "SL-M-DECK")
    assert band.finish_ref == "polished-concrete"
    assert band.finish_in == 0.0


# ------------------------------------------------------------------ 2. what reads it
def test_a_stated_mount_height_is_measured_from_the_finished_floor(catlin_model):
    """ED-M-LIVING-SW's authored 48" is 48" off the plane a hand reaches from."""
    switch = next(item for item in catlin_model.canvas_objects
                  if item.tag == "ED-M-LIVING-SW")
    living = _room(catlin_model, "RM-M-LIVING")
    assert switch.z_m == pytest.approx(
        room_finished_floor_elevation(catlin_model, living) + inch(48).meters)


def test_a_ceiling_mount_does_not_ride_the_floor_covering_up(catlin_model):
    """The joists do not move when the carpet gets thicker — the clear height shrinks.

    RM-S-BED2 carries 1/2" of carpet-over-cushion. A recessed can in it hangs off the storey
    ceiling plane, which is built on the STRUCTURAL floor; measuring it from the finished
    floor instead would push every ceiling fitting on the storey up into the bay above.
    """
    bed = _room(catlin_model, "RM-S-BED2")
    assert _build_up_in(catlin_model, "RM-S-BED2") == pytest.approx(
        _SUBFLOOR_IN + 0.5, abs=1e-4)
    storey = catlin_model.plan.storey("second")
    can = next(item for item in catlin_model.canvas_objects
               if item.tag == "ED-S-BED2-CAN2")
    assert can.z_m == pytest.approx(room_floor_elevation(catlin_model, bed)
                                    + storey.default_ceiling_height.meters)


# ------------------------------------------------- 3. the honest gap, said out loud
def test_every_catlin_covering_states_its_depth(catlin_model):
    findings = floor_finish_depth(check_context(model=catlin_model))
    assert findings and {f.result for f in findings} == {Result.PASS}


def test_a_coating_is_a_sourced_zero(catlin_model):
    finding = next(f for f in floor_finish_depth(check_context(model=catlin_model))
                   if "RM-B-FURNACE" in f.message)
    assert finding.result is Result.PASS
    assert "coating" in finding.message
    assert _build_up_in(catlin_model, "RM-B-FURNACE") == pytest.approx(0.0, abs=1e-9)


def test_an_unstated_covering_is_unknown_and_resolves_to_the_structure(catlin_plan):
    """Strip oak's depth and the attic study must report UNKNOWN, not a quiet 0.

    The resolver still has to return a number and returns the structural top — the answer it
    gave before finishes carried a depth at all. What must not happen is the check calling
    that a pass (decision #32).
    """
    library = catlin_plan.library
    stripped = tuple(
        material.model_copy(update={"finish_thickness_in": None})
        if material.tag == "oak" else material
        for material in library.materials)
    plan = catlin_plan.model_copy(update={
        "library": library.model_copy(update={"materials": stripped})})
    ctx = check_context(plan=plan)

    finding = next(f for f in floor_finish_depth(ctx) if "RM-A-STUDY" in f.message)
    assert finding.result is Result.UNKNOWN
    assert "finish_thickness_in" in finding.message

    # It falls back to the plane the covering would have stood on — the subfloor sheet, the
    # deck's own top — which is the best structural answer available and exactly what this
    # returned before finishes carried a depth at all.
    study = _room(ctx.model, "RM-A-STUDY")
    datum = ctx.model.plan.storey(study.storey).elevation.meters
    assert (room_finished_floor_elevation(ctx.model, study) - datum) / _IN == pytest.approx(
        _SUBFLOOR_IN, abs=1e-4)


def test_a_house_with_no_floor_covering_is_not_applicable(catlin_plan):
    """N/A is earned from positive absence, never from "no data" (plans/01-decisions.md)."""
    bare = {}
    for storey, group in catlin_plan.elements.items():
        bare[storey] = tuple(
            element.model_copy(update={"floor_finish": None})
            if element.element_kind == "Room" else element
            for element in group)
    ctx = check_context(plan=catlin_plan.model_copy(update={"elements": bare}))
    findings = floor_finish_depth(ctx)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]
