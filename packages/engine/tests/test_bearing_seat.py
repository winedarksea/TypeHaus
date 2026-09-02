"""The flat bearing seat under catlin's mixed deck, and what breaks it.

``structural.mixed_deck_bearing_seat`` exists because the arithmetic in
``houses/catlin/params/main_deck.py`` was right and unguarded: the deck's soffit could sit
1 9/16" above the plane the wood bay's mudsill lands on, and nothing in the engine had an
opinion. These tests nudge each of the six numbers that plane is made of and assert the
build goes red.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.structural.bearing_seat import (
    floor_bearing_grid,
    mixed_deck_bearing_seat,
)
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN, inch


def _context(plan, model, _prefs=None):
    return check_context(plan, model)


def _results(findings, result):
    return [f for f in findings if f.result is result]


def test_the_seat_is_flat_and_the_check_says_so(catlin_plan, catlin_model):
    findings = mixed_deck_bearing_seat(_context(catlin_plan, catlin_model))
    assert findings, "the rule is stated; the check must grade something"
    assert not _results(findings, Result.FAIL), [f.message for f in findings]
    graded = {f.element_tags[1] for f in findings}
    # Every wood bay that touches the concrete band, and only those.
    assert graded == {"FS-M-WEST", "FS-M-EAST", "FS-M-STAIR"}
    for finding in findings:
        assert "-13.44\"" in finding.message


def _nudged(catlin_plan, tag, **updates):
    """``catlin_plan`` with one element replaced — the same trick the deck tests use."""
    element = catlin_plan.by_tag(tag)
    replaced = element.model_copy(update=updates)
    storey = next(s.tag for s in catlin_plan.storeys
                  if any(e.tag == tag for e in catlin_plan.storey_elements(s.tag)))
    kept = [e if e.tag != tag else replaced for e in catlin_plan.storey_elements(storey)]
    return catlin_plan.with_elements(storey, kept)


@pytest.mark.parametrize("thickness_in,which", [(4.0, "a thinner cast cover"),
                                                (5.0, "a thicker one")])
def test_moving_the_cover_moves_the_seat_and_fails(catlin_plan, catlin_model,
                                                   thickness_in, which):
    """The cover is what tunes the finished plane; the seat below it is not free to move.

    ``Slab.thickness`` is form + cover, and ``top_elevation`` pins the cap top, so changing
    the cover without re-pinning the top drags the soffit off the mudsill's plane. That is
    the exact failure this whole rework was written to make impossible — and note it is a
    *different* failure from ``integrity.slab_thickness``, which would also fire here: that
    one says the number stopped landing on a layer boundary, this one says the deck stopped
    landing on the pour.
    """
    plan = _nudged(catlin_plan, "SL-M-DECK", thickness=inch(10.0 + thickness_in))
    from typehaus.resolve import resolve

    model, _findings = resolve(plan)
    fails = _results(mixed_deck_bearing_seat(_context(plan, model)),
                     Result.FAIL)
    assert fails, which
    assert any("soffit" in f.message for f in fails)


def test_a_stepped_pour_fails_before_anything_else_is_measured(catlin_plan, catlin_model):
    """One flat seat means one plane. Step a single wall and the check names it."""
    plan = _nudged(catlin_plan, "W-B-CS2", top_elevation=inch(-12.0))
    from typehaus.resolve import resolve

    model, _findings = resolve(plan)
    fails = _results(mixed_deck_bearing_seat(_context(plan, model)),
                     Result.FAIL)
    assert fails
    assert any("do not top out on one plane" in f.message and "W-B-CS2" in f.message
               for f in fails)


def test_joists_left_sitting_in_the_pour_fail(catlin_plan, catlin_model):
    """The plate is what holds the joists off the concrete, and it is 1 1/2" plus a gasket.

    Taking the walls up to the joist soffit leaves the deck landing on them with the wood
    having nothing between it and the pour.
    """
    from typehaus.resolve import resolve

    plan = catlin_plan
    for tag in ("W-B-W1", "W-B-W2", "W-B-CS", "W-B-CS2", "W-B-CN", "W-B-CN2",
                "W-B-STR", "W-B-STR3", "W-B-E1"):
        plan = _nudged(plan, tag, top_elevation=inch(-11.875))
    model, _findings = resolve(plan)
    fails = _results(mixed_deck_bearing_seat(_context(plan, model)),
                     Result.FAIL)
    assert any("inside the pour" in f.message for f in fails), [f.message for f in fails]


def test_the_bearing_grid_holds_every_joist_cut_over_its_own_wall(
        catlin_plan, catlin_model):
    findings = floor_bearing_grid(_context(catlin_plan, catlin_model))
    assert findings
    assert not _results(findings, Result.FAIL), [f.message for f in findings]
    assert {f.element_tags[0] for f in findings} >= {"FS-M-WEST", "FS-M-MECH",
                                                     "FS-M-STAIR", "FS-M-EAST"}


def test_an_alignment_offset_that_stops_matching_the_thickness_is_caught(
        catlin_plan, catlin_model):
    """W-B-CS's alignment offset is a hand-written HALF of its structure thickness. Change
    the structure and leave the number and the bearing layer slides off the x=18' grid while
    the joists keep stopping on it — the silent failure the check is for.

    It reads ``face("stud-ext", offset=inch(-2.75))`` against 5 1/2" of stud, now that the
    wall is framed rather than poured. The trap is not about the pour; it follows the wall,
    which is why this test does too."""
    # -5" against 5 1/2" of stud: the studs then run 17'-9 1/4"..18'-2 3/4" shifted 2 1/4"
    # west, so the joists that stop on x=18' have well under the 1 1/2" the check wants on
    # the near side. (-2.75", the authored number, is a genuine half of 5.5". The rule is
    # bearing, not tidiness — a small error still passes, and should.)
    from typehaus.model.refs import face
    from typehaus.resolve import resolve

    plan = _nudged(catlin_plan, "W-B-CS", alignment=face("stud-ext", offset=inch(-5)))
    model, _findings = resolve(plan)
    fails = _results(floor_bearing_grid(_context(plan, model)), Result.FAIL)
    assert fails, "a 5 1/2\" stud under a -5\" offset is off the grid and must be caught"
    assert any("W-B-CS" in f.element_tags for f in fails)


def test_the_seat_is_the_number_the_basement_walls_are_authored_to(catlin_model):
    """``plan/storeys/basement.py`` is editable-dialect and cannot import the arithmetic, so
    it repeats -13 7/16" and -9'-1 7/16" as literals. This is the tie between the copies."""
    # W-B-S2 and W-B-S3 are the 7 1/4" curbs under the framed walkout.
    # They stand on the same slab and the same footings as every other pour here, but they
    # stop at -102 3/16" by design and have nothing to say about the seat — the framed
    # walls on them do, and they reach it. Excluded by name rather than by height so a wall
    # cannot quietly leave this assertion by getting shorter.
    _CURBS = {"W-B-S2", "W-B-S3"}
    walls = [w for w in catlin_model.walls
             if w.tag.startswith("W-B-") and w.is_foundation
             and w.tag != "W-B-BRICK" and w.tag not in _CURBS]
    # W-B-STR and W-B-STR3 are framed 2x6 bearing walls, not FoundationWalls, so they are no
    # longer pours authored to the seat. What they stand on did not move — their own z0 is
    # still the basement floor and their footings are unchanged — but they have nothing to
    # say about the pour's top. W-B-CS was framed the same way, and W-B-S3 split into
    # W-B-S3 + W-B-S4 at the excavation edge, of which only W-B-S4 is a full-height pour.
    assert len(walls) == 13
    # The two curbs, separately: same base, same 7 1/4" of pour, top on the framed walls'
    # own base so the chain footing -> curb -> plate is continuous.
    for tag in sorted(_CURBS):
        curb = catlin_model.wall(tag)
        assert curb.z0_m / M_PER_IN == pytest.approx(-109.4375, abs=1e-6), tag
        assert curb.z1_m / M_PER_IN == pytest.approx(-102.1875, abs=1e-6), tag
        framed = catlin_model.wall(f"{tag}-FR")
        assert framed.z0_m == pytest.approx(curb.z1_m), tag
    for wall in walls:
        assert wall.z1_m / M_PER_IN == pytest.approx(-13.4375, abs=1e-6), wall.tag
        assert wall.z0_m / M_PER_IN == pytest.approx(-109.4375, abs=1e-6), wall.tag
        assert (wall.z1_m - wall.z0_m) / M_PER_IN == pytest.approx(96.0, abs=1e-6)
