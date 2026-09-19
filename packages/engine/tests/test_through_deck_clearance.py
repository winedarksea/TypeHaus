"""``resolve/through_deck.py`` + ``structural.through_deck_clearance``.

The derivation nobody authors: a wall whose framing spans a floor deck cuts the sheet around
itself and nothing else — no header, no trimmer, no hanger, no ``FloorOpening``. Catlin's
three ``W-M-FIRE-STUB-*`` piers are the whole of it, and the blast radius is the subject of
this module, because a predicate that widened by one wall would subtract a strip of subfloor
along an exterior wall's entire run.
"""

from __future__ import annotations

import pytest
from shapely.geometry import LineString, Polygon

from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember
from typehaus.resolve.partition import framing_top_z_m
from typehaus.resolve.through_deck import (
    _SHEET_CLEARANCE_M,
    _THROUGH_TOL_M,
    _wall_face,
    through_deck_cuts,
    through_deck_walls,
)

_CHECK_ID = "structural.through_deck_clearance"
_PIERS = {"W-M-FIRE-STUB-S", "W-M-FIRE-STUB-M", "W-M-FIRE-STUB-N"}
_IN = inch(1).meters


def _deck(model, tag: str):
    return next(floor for floor in model.floors if floor.tag == tag)


def _findings(report):
    return [f for f in report.findings if f.check_id == _CHECK_ID]


# --- the blast radius -----------------------------------------------------------------


def test_catlin_through_deck_set_is_exactly_the_three_piers(catlin_model_ro) -> None:
    """Set equality across the whole house, not a membership test.

    Any wall joining this set takes a bite out of a subfloor sheet, silently, with no
    authored element anywhere to point at. Two walls deserve naming as near misses:
    ``W-M-TUBDK-W``/``-S`` are the ordinary partition-on-a-subfloor case and miss clause 1
    by the deck's full 12 5/8"; the basement walls miss clause 2 by 14 3/16".
    """
    got = {(floor.tag, tag)
           for floor in catlin_model_ro.floors
           for tag in (floor.through_walls or ())}
    assert got == {("FS-M-EAST", tag) for tag in _PIERS}


def test_starter_has_no_through_deck_wall_at_all(starter_dir) -> None:
    """The template authors no ``base_elevation`` or ``top_elevation`` anywhere, so there is
    not even a candidate — and the check earns N/A rather than going quiet."""
    from typehaus.checks.run import run
    from typehaus.source import load_plan

    result = load_plan(starter_dir)
    assert result.plan is not None
    report = run(result.plan, starter_dir, tier=Tier.STRUCTURAL)
    matched = _findings(report)
    assert [f.result for f in matched] == [Result.NOT_APPLICABLE]


def test_the_platform_trap_is_the_whole_reason_framing_extents_are_read(catlin_model_ro):
    """``W-M-E1``, by name, and BOTH halves of it asserted.

    ``platform._drop`` grows an exterior wall's BODY down over the mudsill and rim and
    ``_lift`` grows it up to the wall above, so ``W-M-E1``'s body band satisfies clauses 1
    and 2 against ``FS-M-EAST`` — while its FRAMING band, which is what the predicate reads,
    does not. Read the body and every platform-framed exterior wall in the house subtracts a
    6" strip of subfloor along its whole run.
    """
    wall = catlin_model_ro.wall("W-M-E1")
    deck = _deck(catlin_model_ro, "FS-M-EAST")
    soffit = min(member.z0_m for member in deck.members)

    # The body: down over the rim, up to the storey above. Both clauses hold.
    assert wall.z0_m <= soffit + _THROUGH_TOL_M
    assert wall.z1_m >= deck.deck_z1_m + _THROUGH_TOL_M
    # The framing: bottom plate on the storey datum, a foot above the soffit. Clause 1 fails.
    assert wall.base_ref_z_m > soffit + _THROUGH_TOL_M
    assert wall.base_ref_z_m - soffit == pytest.approx(inch(11.875).meters, abs=1e-6)
    assert framing_top_z_m(wall) >= deck.deck_z1_m + _THROUGH_TOL_M
    assert "W-M-E1" not in (deck.through_walls or ())


def test_walls_do_die_exactly_on_deck_planes_in_this_house(catlin_model_ro) -> None:
    """The condition ``_THROUGH_TOL_M`` exists for is real, and there is a lot of it.

    Eleven sunken-garden and roof-garden walls top out at exactly 0", which is exactly the
    two breezeway landings' sheet plane, and the three fireplace piers top at 15/16" against
    ``FS-SG-PORCH``'s 1". None of them stands INSIDE the deck in question, so containment
    keeps them out today — but "does this wall come out the other side" must never be decided
    by an exact float compare on numbers that are equal by construction.
    """
    grazing = {(floor.tag, wall.tag)
               for floor in catlin_model_ro.floors if len(floor.deck_outline) >= 3
               for wall in catlin_model_ro.walls
               if abs(framing_top_z_m(wall) - floor.deck_z1_m) < _THROUGH_TOL_M}
    assert len(grazing) >= 3, sorted(grazing)


def test_a_wall_stopping_exactly_at_the_sheet_is_not_passing_through_it() -> None:
    """The tolerance at the unit level, where it can be made to bite.

    A wall whose framing top IS the deck's sheet plane stops at the deck; one 1/8" proud of
    it comes out the other side. Synthetic because catlin has no wall that is both contained
    in a deck and level with its sheet — which is the state this keeps it in.
    """
    from types import SimpleNamespace

    from typehaus.model.elements import Wall

    outline = [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)]
    authored = Wall(uid="TESTWALL01", tag="W-TEST", start_node="A", end_node="B",
                    assembly="INT_2X4")
    system = SimpleNamespace(joists=SimpleNamespace(bearing_refs=()))

    def model_with(top_m: float):
        wall = SimpleNamespace(
            tag="W-TEST", z0_m=-1.0, z1_m=top_m, plate_base_z_m=None, plate_top_z_m=None,
            base_ref_z_m=-1.0,
            layers=[SimpleNamespace(polygon=[(1.0, 1.0), (1.2, 1.0), (1.2, 2.0), (1.0, 2.0)])])
        return SimpleNamespace(walls=[wall],
                               plan=SimpleNamespace(by_tag=lambda tag: authored))

    # Dies on the sheet plane: not a penetration.
    assert through_deck_walls(model_with(0.05), system, -0.3, 0.05, outline) == ()
    # A hair under it: still not.
    assert through_deck_walls(model_with(0.05 + _THROUGH_TOL_M / 2), system,
                              -0.3, 0.05, outline) == ()
    # Out the other side.
    assert len(through_deck_walls(model_with(0.2), system, -0.3, 0.05, outline)) == 1


def test_a_deck_the_sheet_merely_dies_into_is_not_a_penetration(catlin_model_ro) -> None:
    """``W-G-S`` satisfies clauses 1, 2 and 4 against both breezeway landings.

    A deck outline runs to the AXIS of the line it dies into, so every wall standing at a
    deck's edge overlaps it by half its own thickness — 59 and 285 sq in with the saw's own
    clearance allowed for, 38 and 265 without. Clause 3 is
    containment for exactly this: the sheet is already drawn to that wall and cutting it
    again deducts the same strip twice.
    """
    wall = catlin_model_ro.wall("W-G-S")
    for tag in ("FS-BW-FLOOR", "FS-BW-GARAGE"):
        deck = _deck(catlin_model_ro, tag)
        soffit = min(member.z0_m for member in deck.members)
        assert wall.base_ref_z_m <= soffit + _THROUGH_TOL_M
        assert framing_top_z_m(wall) >= deck.deck_z1_m + _THROUGH_TOL_M
        face = _wall_face(wall).buffer(_SHEET_CLEARANCE_M, join_style=2)
        overlap = face.intersection(Polygon(deck.deck_outline))
        assert overlap.area / (_IN ** 2) > 30, tag
        assert not Polygon(deck.deck_outline).covers(face)
        assert not (deck.through_walls or ())


# --- the cut --------------------------------------------------------------------------


def test_the_derived_voids_are_the_three_piers_and_the_sheet_still_bills(catlin_model_ro):
    """Three cuts, each the pier plus 1/2" all round, and no authored opening left."""
    deck = _deck(catlin_model_ro, "FS-M-EAST")
    assert len(deck.deck_voids) == 3
    for ring in deck.deck_voids:
        minx, miny, maxx, maxy = Polygon(ring).bounds
        # 3 5/8" brick + 1/8" wash + 1/2" of clearance each side.
        assert (maxx - minx) / _IN == pytest.approx(4.75, abs=1e-6)
        assert 13.0 <= (maxy - miny) / _IN <= 13.2
    assert not any(opening.tag == "FO-M-FIRE"
                   for opening in catlin_model_ro.plan.all_elements()
                   if hasattr(opening, "outline"))


def test_the_clearance_constant_never_outruns_the_checks_threshold(catlin_ctx) -> None:
    """The split the design turns on: the saw cut is a DERIVATION constant and the minimum
    gap is a VERDICT threshold, and they are allowed to be different numbers — but not in
    this direction. A cut wider than the gap a check will accept removes plywood from the
    member it is nailed to and passes."""
    threshold = inch(catlin_ctx.preferences.structural.min_through_deck_clearance_in).meters
    assert _SHEET_CLEARANCE_M <= threshold


def test_the_frame_subtraction_is_what_makes_the_clearance_safe(catlin_model_ro) -> None:
    """At 3/4" the derived cut would run over joists 005 and 008, which clear the piers by
    5/8". Subtracting the member footprints is what keeps that from being silent."""
    deck = _deck(catlin_model_ro, "FS-M-EAST")
    walls = [catlin_model_ro.wall(tag) for tag in sorted(_PIERS)]
    wide = [Polygon(ring) for ring in through_deck_cuts(walls, list(deck.members),
                                                        deck.deck_outline)]
    assert wide
    for cut in wide:
        for member in deck.members:
            if member.category != "joist":
                continue
            box = Polygon([(member.p0[0], member.p0[1] - inch(1.25).meters),
                           (member.p1[0], member.p1[1] - inch(1.25).meters),
                           (member.p1[0], member.p1[1] + inch(1.25).meters),
                           (member.p0[0], member.p0[1] + inch(1.25).meters)])
            assert cut.intersection(box).area < 1e-6, member.child_key


# --- the check ------------------------------------------------------------------------


def test_catlin_passes_with_the_five_eighths_it_was_left_by_a_sixteen_inch_module(
        catlin_check_report) -> None:
    """Six findings — a clearance and a bearing verdict per pier — and every one a PASS.

    The governing gap is 5/8" against a 1/2" threshold, and that 5/8" is residue of a
    44 1/4" panel laid out on a 16" joist module rather than a margin anybody chose.
    """
    matched = _findings(catlin_check_report(Tier.STRUCTURAL))
    assert len(matched) == 6
    assert {f.result for f in matched} == {Result.PASS}
    clearances = [f for f in matched if "clear of every member" in f.message]
    assert len(clearances) == 3
    assert any('0.625" against 0.50"' in f.message for f in clearances)
    assert all(tag in {t for f in matched for t in f.element_tags} for tag in _PIERS)


def test_the_historical_defect_was_a_trimmer_and_it_fails_here(catlin_ctx) -> None:
    """Scoped to joists this check would miss the bug it was written for.

    The fireplace opening was first drawn at the brick's own 45 1/2"; the resolver puts the
    first trimmer ply's AXIS on the opening edge, so the ply reached into the hole and shared
    volume with the brick over the full depth of the joist zone.
    ``structural.member_interference`` walks framing against framing and a masonry layer is
    not framing, so it sat at 0 FAIL until the member boxes were read by hand. Reconstructed
    here by laying a trimmer back across a pier.
    """
    from typehaus.checks.structural.through_deck import through_deck_clearance

    deck = _deck(catlin_ctx.model, "FS-M-EAST")
    pier = catlin_ctx.model.wall("W-M-FIRE-STUB-M")
    axis = LineString(pier.axis)
    # A ply on the pier's own line: this is what an opening edge drawn at the brick face does.
    offending = FramedMember(
        deck.uid, "trimmer-SYNTHETIC-0-0", "trimmer", "1.75x11.875 LVL",
        (axis.centroid.x, pier.axis[0][1]), (axis.centroid.x, pier.axis[1][1]),
        deck.deck_z0_m - inch(11.875).meters, deck.deck_z0_m, axis.length)
    index = catlin_ctx.model.floors.index(deck)
    import dataclasses
    catlin_ctx.model.floors[index] = dataclasses.replace(
        deck, members=(*deck.members, offending))
    try:
        matched = [f for f in through_deck_clearance(catlin_ctx)
                   if f.result is Result.FAIL and "trimmer-SYNTHETIC-0-0" in f.element_tags]
        assert len(matched) == 1
        assert "sq in of plan" in matched[0].message
    finally:
        catlin_ctx.model.floors[index] = deck


def test_walls_are_the_subject_and_a_stair_well_is_still_an_opening(catlin_model_ro) -> None:
    """``Railing`` and ``Stair`` are outside the scope by the ``isinstance(_, Wall)`` clause.

    A stair genuinely does span a deck; its well is a ``FloorOpening``, which is the right
    article for it because somebody walks down it and it needs a header and trimmers.
    """
    from typehaus.model.elements import Wall

    for floor in catlin_model_ro.floors:
        for tag in (floor.through_walls or ()):
            assert isinstance(catlin_model_ro.plan.by_tag(tag), Wall), tag
    assert any(floor.chases for floor in catlin_model_ro.floors)


def test_the_predicate_is_exercised_directly_against_a_decks_own_numbers(catlin_model_ro):
    """``through_deck_walls`` re-run on the resolved deck reproduces ``through_walls``."""
    deck = _deck(catlin_model_ro, "FS-M-EAST")
    soffit = min(member.z0_m for member in deck.members)
    system = next(element for element in catlin_model_ro.plan.all_elements()
                  if getattr(element, "tag", None) == "FS-M-EAST")
    walls = through_deck_walls(catlin_model_ro, system, soffit, deck.deck_z1_m,
                               deck.deck_outline)
    assert {wall.tag for wall in walls} == _PIERS


def test_the_platform_passes_leave_the_piers_alone(catlin_model_ro) -> None:
    """The predicate's whole basis is that the piers' authored band IS their resolved band.

    ``platform._drop`` needs a gap to the foundation and the piers' base IS ``W-B-E1``'s top;
    ``_lift`` needs a band to the wall above and the plinth's base IS their top. So neither
    fires, ``plate_base_z_m``/``plate_top_z_m`` stay ``None``, and the framing extents the
    predicate reads are the authored elevations unchanged. If a future pass does grow one of
    these, the through-deck verdict moves with it and this is where it shows.
    """
    for tag in sorted(_PIERS):
        wall = catlin_model_ro.wall(tag)
        authored = catlin_model_ro.plan.by_tag(tag)
        assert wall.plate_base_z_m is None, tag
        assert wall.plate_top_z_m is None, tag
        assert wall.z0_m == pytest.approx(authored.base_elevation.meters, abs=1e-9)
        assert wall.z1_m - wall.z0_m == pytest.approx(authored.top.meters, abs=1e-9)
