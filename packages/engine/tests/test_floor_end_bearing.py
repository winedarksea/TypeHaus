"""Where a deck's joists stop, what they are seated on, and what a truss order says.

The one member this house buys made-to-length is the second floor's open-web floor truss,
and until ``resolve/floor_ends.py`` existed the model could not state either number a
fabricator needs. The trusses were drawn 18'-0" long — the *bearing grid*, not the member —
running out to x=0'-0", which is the outside of the sheathing, half an inch past the plate
they sit on. At the other end they were cut on the centreline of the 2x6 they share with the
east half's I-joists: 2 3/4" of seat each, where an open-web truss wants 3".
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _helpers import CATLIN, copy_house

M_PER_IN = 0.0254


@pytest.fixture(scope="module")
def catlin():
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    loaded = load_plan(CATLIN)
    model, _ = resolve(loaded.plan)
    return model


def _floor(model, tag):
    return next(f for f in model.floors if f.tag == tag)


def _inches(metres: float) -> float:
    return round(metres / M_PER_IN, 4)


def test_the_truss_is_the_length_it_is_fabricated_to(catlin):
    """17'-11" tip to tip: the 18'-0" grid less 1 1/4" of rim and 3/4" of plate split.

    West end: the plate runs x 0 1/2"..6", the rim board takes the first 1 1/4" of it, and
    the truss starts behind the rim at 1 3/4". East end: 3 1/2" onto the x=18' plate, whose
    near face is at 17'-9 1/4".
    """
    west = _floor(catlin, "FS-S-WEST")
    full = [m for m in west.members
            if m.category == "joist" and m.length_m > 4.0]
    assert len(full) == 20
    assert {_inches(m.length_m) for m in full} == {215.0}
    assert _inches(west.ends.tip_lo) == 1.75
    assert _inches(west.ends.tip_hi) == 216.75


def test_the_two_halves_of_the_second_floor_meet_on_the_plate_they_share(catlin):
    """3 1/2" of seat to the truss, 2" to the I-joist, and the 5 1/2" plate exactly spent.

    Both numbers are authored (``params/second_deck.py``) precisely because the split is a
    decision: a centreline split gives 2 3/4" each, which is under the truss fabricator's
    3" and over what the I-joist needs.
    """
    west, east = _floor(catlin, "FS-S-WEST"), _floor(catlin, "FS-S-EAST")
    assert west.ends.tip_hi == pytest.approx(east.ends.tip_lo)
    assert _inches(west.ends.seat_hi) == 3.5
    assert _inches(east.ends.seat_lo) == 2.0
    assert _inches(west.ends.seat_hi) + _inches(east.ends.seat_lo) == 5.5


def test_a_shared_plate_carries_no_rim_from_either_deck(catlin):
    """Two coincident bands, billed twice and interpenetrating both decks' joists, are gone.

    The rims that remain are the free ends, where a band board has a framing face to sit
    flush with — and there its outboard face is that face, not a half-thickness past it.
    """
    for tag in ("FS-S-WEST", "FS-S-EAST"):
        floor = _floor(catlin, tag)
        assert len([m for m in floor.members if m.category == "rim"]) == 1, tag
        assert (floor.ends.rim_lo is None) != (floor.ends.rim_hi is None), tag
    west = _floor(catlin, "FS-S-WEST")
    rim = next(m for m in west.members if m.category == "rim")
    # 1 1/4" band, outboard face on the 0 1/2" stud face: axis at 1 1/8".
    assert _inches(rim.p0[0]) == 1.125


def test_the_fabrication_schedule_states_span_and_bearing(catlin):
    """The truss order's four numbers, none of them restated anywhere else."""
    from typehaus.takeoff.fabrication import fabricated_member_schedule

    rows = [row for row in fabricated_member_schedule(catlin)
            if row["floor"] == "FS-S-WEST" and row["category"] == "joist"]
    full = next(row for row in rows if row["pieces"] == 20)
    assert full["overall_length_ft_in"] == "17'-11\""
    assert full["clear_span_ft_in"] == "17'-3.25\""
    assert (full["bearing_low_in"], full["bearing_high_in"]) == (4.25, 3.5)
    assert full["chord_clear_opening_in"] == 8.875
    assert full["spacing_in"] == 16.0
    # The stair-clipped pieces land on a header, not a plate, and claim no seat.
    clipped = next(row for row in rows if row["pieces"] == 8)
    assert clipped["clear_span_ft_in"] is None


def test_end_bearing_is_graded_against_what_the_member_needs(tmp_path):
    """A truss on 2 3/4" passes the 1 1/2" code floor and fails its own 3" requirement."""
    from typehaus.checks import run
    from typehaus.findings import Result
    from typehaus.source import load_plan

    house = copy_house(CATLIN, tmp_path / "catlin")
    deck = Path(house) / "params" / "second_deck.py"
    deck.write_text(deck.read_text().replace("_TRUSS_BEARING = inch(3.5)",
                                             "_TRUSS_BEARING = inch(2.75)"))
    report = run(load_plan(Path(house)).plan, Path(house))
    findings = [f for f in report.findings
                if f.check_id == "integrity.floor_end_bearing"]
    assert [f.result for f in findings] == [Result.FAIL]
    assert "2.75\"" in findings[0].message and "FS-S-WEST" in findings[0].element_tags
