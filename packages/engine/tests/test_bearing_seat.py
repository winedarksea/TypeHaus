"""One flat bearing seat under a mixed deck, and what breaks it.

``structural.mixed_deck_bearing_seat`` guards the plane a pour deck's soffit and a wood bay's
mudsill share. Catlin's ``SL-M-DECK`` retired 2026-11-01 (decision #112), so the check is
graded on ``_mixed_deck_plan``: these tests nudge the numbers that plane is made of and
assert the build goes red. The bearing-grid tests below still read catlin.
"""

from __future__ import annotations

import pytest
from _helpers import check_context
from _mixed_deck_plan import DECK, WOOD, deck, mixed_deck_model, mixed_deck_plan

from typehaus.checks.structural.bearing_seat import (
    floor_bearing_grid,
    mixed_deck_bearing_seat,
)
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve import resolve


def _context(plan, model, _prefs=None):
    return check_context(plan, model)


def _results(findings, result):
    return [f for f in findings if f.result is result]


def _graded(plan):
    model, _findings = resolve(plan)
    return mixed_deck_bearing_seat(_context(plan, model))


def test_the_seat_is_flat_and_the_check_says_so():
    findings = mixed_deck_bearing_seat(_context(mixed_deck_plan(), mixed_deck_model()))
    assert [f.result for f in findings] == [Result.PASS], [f.message for f in findings]
    assert findings[0].element_tags == (DECK, WOOD)
    assert "-13.44\"" in findings[0].message


@pytest.mark.parametrize("thickness_in,which", [(4.0, "a thinner cast cover"),
                                                (5.0, "a thicker one")])
def test_moving_the_cover_moves_the_seat_and_fails(thickness_in, which):
    """``top_elevation`` pins the cap top, so a new cover without a re-pinned top drags the
    soffit off the mudsill's plane — a different failure from ``integrity.slab_thickness``."""
    fails = _results(_graded(mixed_deck_plan(slab=deck(thickness=inch(10.0 + thickness_in)))),
                     Result.FAIL)
    assert fails, which
    assert any("soffit" in f.message for f in fails)


def test_a_stepped_pour_fails_before_anything_else_is_measured():
    """One flat seat means one plane. Step a single wall and the check names it."""
    fails = _results(_graded(mixed_deck_plan(wall_tops_in={"W-E": -12.0})), Result.FAIL)
    assert any("do not top out on one plane" in f.message and "W-E" in f.message
               for f in fails), [f.message for f in fails]


def test_joists_left_sitting_in_the_pour_fail():
    """Walls taken up to the joist soffit leave nothing between the wood and the pour."""
    tops = dict.fromkeys(("W-S", "W-E", "W-N", "W-W"), -11.875)
    fails = _results(_graded(mixed_deck_plan(wall_tops_in=tops)), Result.FAIL)
    assert any("inside the pour" in f.message for f in fails), [f.message for f in fails]


def _nudged(catlin_plan, tag, **updates):
    """``catlin_plan`` with one element replaced."""
    replaced = catlin_plan.by_tag(tag).model_copy(update=updates)
    storey = next(s.tag for s in catlin_plan.storeys
                  if any(e.tag == tag for e in catlin_plan.storey_elements(s.tag)))
    kept = [e if e.tag != tag else replaced for e in catlin_plan.storey_elements(storey)]
    return catlin_plan.with_elements(storey, kept)


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
    # The perimeter pours only. W-B-CS/CS3/STR/STR3 were framed first; W-B-CS2/CN2/CN
    # followed with the floor-truss bay (decision #112, 2026-11-01), so no interior pour
    # is left to top out on the seat.
    assert sorted(w.tag for w in walls) == [
        "W-B-E1", "W-B-E2", "W-B-N1", "W-B-N2", "W-B-N3", "W-B-N4", "W-B-S1", "W-B-S4",
        "W-B-W1", "W-B-W2"]
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
