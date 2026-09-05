"""``Soffit.openings`` — the framed hatch, and what the generator does with one.

A soffit hatch used to be a lid in a plane and nothing else: an access panel authored as a
``Furniture`` placeable in the ceiling below, with ``resolve/framing/soffit.py`` laying its
rungs straight through the hole underneath it. Nothing reported the rung standing in the
opening, because nothing compared them — a placeable's footprint is a plan rectangle and
``structural.member_interference`` does not test placeables against members. So the model
asserted a panel that could not be opened, at 0 FAIL.

These tests pin the three things authoring an opening now buys:

* the rung it crosses is **cut**, not omitted — what is left either side still carries the
  board out to the rail;
* two **headers** run ALONG the box between the stations bounding the hole, which is what
  the cut ends and the panel's frame bear on;
* a soffit with **no** opening frames byte-identical members to the ones it framed before
  the field existed, so no golden, take-off row or interference pairing moves under a house
  that never authors one.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.model import (
    Assembly, Building, FramingSpec, Layer, LayerFunction, Library, Material, Node,
    PlanModel, Project, Site, Soffit, SoffitOpening, Storey, Wall, degF, ft, inch, pt,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve import resolve
from typehaus.resolve.framing.soffit import (
    SOFFIT_HEADER_KEY_PREFIX,
    SOFFIT_RUNG_KEY_PREFIX,
)

_OPENING_CHECK_ID = "structural.soffit_opening"

# A 40" x 96" box on a 21" drop, framed like SF-S-HP1: 2x4 rungs on 2x2 rails at 16" o.c.
# 40" finished, less 2 x 5/8" of lining and 2 x 1 1/2" of rail depth, is 35.75" of clear span
# at x 6 1/8"..41 7/8" — the same derivation `soffit_clear_section` makes, restated here only
# because a hole has to be authored in real coordinates and there is nothing else to author
# it against. 96" in y so the LONG axis is y and the rungs span x.
_OUTLINE = (pt(ft(0, 4), ft(1)), pt(ft(3, 8), ft(1)),
            pt(ft(3, 8), ft(9)), pt(ft(0, 4), ft(9)))
_FRAMING = FramingSpec(member="2x4", plate_member="2x2", spacing=inch(16))


def _plan(openings: tuple[SoffitOpening, ...]) -> PlanModel:
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="SoffitOpening", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b3"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="SoffitOpening"),
    )
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1)
    )
    walls = tuple(
        Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}", end_node=f"N-{end}",
             assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
    )
    soffit = Soffit(uid="SF00000001", tag="SF-1", outline=_OUTLINE, drop=inch(21),
                    framing=_FRAMING, openings=openings)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(assembly,)), storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, soffit))


def _framed(openings: tuple[SoffitOpening, ...] = ()):
    model, _ = resolve(_plan(openings))
    return next(s for s in model.soffits if s.tag == "SF-1")


def _keys(soffit, prefix: str) -> list[str]:
    return sorted(m.child_key for m in soffit.members if m.child_key.startswith(prefix))


# A hole straddling ONE station, inset from both rails so it takes a header on each side.
# The stations resolve at y 13 3/8" / 28 5/8" / 44 5/8" / 60 5/8" / 76 5/8" / 92 5/8" /
# 106 5/8" (16" o.c. off the end blocking), so y 3'-2"..4'-6" crosses 44 5/8" and NOTHING
# else — deliberately, because the interesting cases are one cut rung and a full-width hole,
# and a fixture that quietly cut two would make the header span a different number than the
# one this file asserts. x 1'-0"..2'-6" leaves a stub either side.
_ONE_STATION = (SoffitOpening(
    tag="AO-1",
    outline=(pt(ft(1), ft(3, 2)), pt(ft(2, 6), ft(3, 2)),
             pt(ft(2, 6), ft(4, 6)), pt(ft(1), ft(4, 6)))),)


def test_a_soffit_with_no_opening_frames_exactly_what_it_always_did() -> None:
    """The regression that matters most, because it is the silent one.

    ``_segments`` returns the un-suffixed key when nothing is cut, so every existing soffit
    in every house frames members with the same keys, the same count and the same lengths as
    it did before ``Soffit.openings`` existed. A suffix appearing here would move section
    goldens, take-off rows and ``member_interference`` pairings on boxes nobody touched.
    """
    soffit = _framed()
    rungs = _keys(soffit, SOFFIT_RUNG_KEY_PREFIX)
    assert rungs == ["soffit-rung-001", "soffit-rung-002", "soffit-rung-003",
                     "soffit-rung-004", "soffit-rung-005"]
    assert _keys(soffit, SOFFIT_HEADER_KEY_PREFIX) == []
    spans = {round(m.length_m / M_PER_IN, 3)
             for m in soffit.members if m.child_key.startswith(SOFFIT_RUNG_KEY_PREFIX)}
    assert spans == {35.75}


def test_the_rung_an_opening_crosses_is_cut_and_not_omitted() -> None:
    """Two stubs, not zero members: what is left either side still carries the board.

    Omitting the rung outright would be the easy implementation and the wrong one — the
    ceiling board between the hole and the rail would then hang on nothing for 16" of the
    box, which is exactly the defect a hatch is supposed not to introduce.
    """
    soffit = _framed(_ONE_STATION)
    rungs = _keys(soffit, SOFFIT_RUNG_KEY_PREFIX)
    assert "soffit-rung-002" not in rungs, "the crossed rung must not survive whole"
    assert {"soffit-rung-002a", "soffit-rung-002b"} <= set(rungs)
    stubs = sorted(round(m.length_m / M_PER_IN, 3) for m in soffit.members
                   if m.child_key.startswith("soffit-rung-002"))
    # The clear span is x 6 1/8"..41 7/8"; the hole runs x 12"..30", so the stubs are
    # 12 - 6.125 = 5.875" west and 41.875 - 30 = 11.875" east.
    assert stubs == [5.875, 11.875]
    # Every other station is untouched and still spans the full width.
    assert all(
        round(m.length_m / M_PER_IN, 3) == 35.75 for m in soffit.members
        if m.child_key.startswith(SOFFIT_RUNG_KEY_PREFIX)
        and not m.child_key.startswith("soffit-rung-002"))


def test_two_headers_run_along_the_box_between_the_bounding_stations() -> None:
    """The header is the member the cut ends bear on, and it runs the OTHER way.

    A rung spans ACROSS; a header spans ALONG, from the last station south of the hole to
    the first station north of it. Getting that backwards would frame a member parallel to
    the thing it is supposed to carry.
    """
    soffit = _framed(_ONE_STATION)
    headers = [m for m in soffit.members
               if m.child_key.startswith(SOFFIT_HEADER_KEY_PREFIX)]
    assert sorted(m.child_key for m in headers) == [
        "soffit-header-AO-1-hi", "soffit-header-AO-1-lo"]
    for header in headers:
        # Along the box (y here, since the box is 96" in y against 40" in x).
        assert header.p0[0] == pytest.approx(header.p1[0])
        # The stations at y 28 5/8" and 60 5/8" bound the hole: a 32" header.
        assert header.length_m / M_PER_IN == pytest.approx(32.0, abs=1e-6)
    lines = sorted(round(m.p0[0] / M_PER_IN, 3) for m in headers)
    assert lines == [12.0, 30.0], "a header sits on each across-edge of the hole"


def test_a_full_width_hole_takes_no_header_because_the_rails_carry_it() -> None:
    """An edge landing ON a rail gets no header — the rail is already there.

    This is the ordinary full-width hatch, and framing a header against a rail would put two
    members in the same square, which is the same mistake the end-blocking rule avoids.
    """
    # Drawn to the RAILS' inner faces (x 6 1/8"..41 7/8"), not to the finished box: an
    # opening authored to the box's own outline runs past the rails and is refused, which is
    # the neighbouring test.
    full = (SoffitOpening(
        tag="AO-FULL",
        outline=(pt(inch(6.125), ft(3, 2)), pt(inch(41.875), ft(3, 2)),
                 pt(inch(41.875), ft(4, 6)), pt(inch(6.125), ft(4, 6)))),)
    soffit = _framed(full)
    assert _keys(soffit, SOFFIT_HEADER_KEY_PREFIX) == []
    assert not [m for m in soffit.members if m.child_key.startswith("soffit-rung-002")]


def test_an_opening_outside_the_ladder_reports_rather_than_framing_a_header_on_nothing() -> None:
    """v1 declines what it cannot head off, and says so.

    An opening running past the rails or the end blocking is not a hatch: it is a hole
    through the members that hold the box together. Guessing a header for it would put
    lumber in the take-off bearing on air, under a passing build.
    """
    outside = (SoffitOpening(
        tag="AO-OUT",
        outline=(pt(ft(1), ft(0, 6)), pt(ft(2, 6), ft(0, 6)),
                 pt(ft(2, 6), ft(2)), pt(ft(1), ft(2)))),)
    _, findings = resolve(_plan(outside))
    shape = [f for f in findings if f.check_id == "framing.soffit_shape"]
    assert len(shape) == 1, [f.message for f in findings]
    assert shape[0].result is Result.UNKNOWN
    assert "AO-OUT" in shape[0].message
    assert "clear span" in shape[0].message


def test_the_check_grades_the_header_and_earns_its_not_applicable() -> None:
    """``structural.soffit_opening`` reports on the header, and is N/A when nothing is cut.

    N/A rather than silence: "no soffit in this building has a hatch" is a fact read off the
    model, not an input that went missing, and the distinction is the one this repo holds
    every check to.
    """
    model, _ = resolve(_plan(_ONE_STATION))
    graded = [f for f in run_from_model(model, [], tier=Tier.STRUCTURAL).findings
              if f.check_id == _OPENING_CHECK_ID]
    assert len(graded) == 1
    assert graded[0].result is Result.PASS
    assert "AO-1" in graded[0].message
    assert "32.00" in graded[0].message  # the header span it actually graded

    bare, _ = resolve(_plan(()))
    none = [f for f in run_from_model(bare, [], tier=Tier.STRUCTURAL).findings
            if f.check_id == _OPENING_CHECK_ID]
    assert len(none) == 1
    assert none[0].result is Result.NOT_APPLICABLE


def test_catlin_heads_off_one_rung_for_its_air_handler_hatch(catlin_model) -> None:
    """The live case: SF-S-HP1's AO-S-HP1-AP, and the panel that covers it.

    The two are authored in different files — the opening in ``plan/storeys/second.py``, the
    lid in ``plan/placeables.py`` — and nothing in the engine ties them together, so this is
    where the two rectangles are held to be the same rectangle. A panel drawn larger than its
    hole is a panel whose flange lands on the rungs; drawn smaller, it is a hole nobody closed.
    """
    soffit = next(s for s in catlin_model.soffits if s.tag == "SF-S-HP1")
    assert [tag for tag, _ring in soffit.openings] == ["AO-S-HP1-AP"]
    _tag, ring = soffit.openings[0]
    hole = (round(min(x for x, _ in ring) / M_PER_IN, 3),
            round(max(x for x, _ in ring) / M_PER_IN, 3),
            round(min(y for _, y in ring) / M_PER_IN, 3),
            round(max(y for _, y in ring) / M_PER_IN, 3))
    panel = next(o for o in catlin_model.canvas_objects if o.tag == "FURN-S-NCLOSET-AP")
    lid = (round(min(x for x, _ in panel.footprint) / M_PER_IN, 3),
           round(max(x for x, _ in panel.footprint) / M_PER_IN, 3),
           round(min(y for _, y in panel.footprint) / M_PER_IN, 3),
           round(max(y for _, y in panel.footprint) / M_PER_IN, 3))
    assert hole == lid, "the access panel and the framed opening are one rectangle"

    # Exactly one rung is cut, into a 4 1/2" stub west and a 2" stub east, and the two
    # headers span the 32" between the rungs either side of it.
    stubs = sorted(round(m.length_m / M_PER_IN, 3) for m in soffit.members
                   if m.child_key.startswith("soffit-rung-004"))
    assert stubs == [2.0, 4.5]
    headers = [m for m in soffit.members
               if m.child_key.startswith(SOFFIT_HEADER_KEY_PREFIX)]
    assert len(headers) == 2
    assert all(m.length_m / M_PER_IN == pytest.approx(32.0, abs=1e-6) for m in headers)

    # And the hole is under the machine it serves, in the closet a ladder stands in.
    handler = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-HP1-AH")
    assert min(y for _, y in handler.footprint) / M_PER_IN < hole[3]
    assert hole[2] > 370.0, "wholly inside RM-S-NCLOSET, which starts at y=30'-10\""
