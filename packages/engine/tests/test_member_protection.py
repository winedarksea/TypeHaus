"""Framing-top membrane: measured off the members it covers, split by the roll it needs.

The section exists because nothing else in the BOM can address it — ``framing`` groups sticks
by (profile, category) across the whole house and ``structural_solids`` bills a standalone
beam by the cubic yard, so "feet of tape on the garden decks" was unaskable and the membrane
over a built-up beam's ply seams was carried nowhere at all.

The one thing here that is a real ordering trap, and so the thing most of this module is
about: **the width is per MEMBER and it decides the SKU**. A 3-ply 2x12 is 4 1/2" across; the
common joist roll is 1 5/8". Buy by the foot without reading the width and both ply seams —
the entire point of taping a built-up beam — stay open under a roll that looks like it did
the job.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.member_protection import member_protection_takeoff

#: Every sunken-garden beam that is three plies of 2x12, and so wants the wide roll.
BUILT_UP_BEAMS = {"BM-SG-BKW", "BM-SG-BKE", "BM-SG-FRW", "BM-SG-FRE",
                  "BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"}
#: The single-ply 2x12 girts. Taped for an exposed top, not for a seam — narrow roll.
GIRTS = {"BM-SG-GIRT-RW", "BM-SG-GIRT-RE", "BM-SG-GIRT-FW", "BM-SG-GIRT-FE"}


@pytest.fixture(scope="module")
def rows(catlin_model_ro):
    return member_protection_takeoff(catlin_model_ro)


def test_only_authored_members_are_taped(rows):
    """The section derives nothing. Untaped framing — the whole house — must not appear."""
    taped = {tag for row in rows for tag in row["tags"]}
    assert taped == BUILT_UP_BEAMS | GIRTS | {"FS-SG-PORCH", "FS-SG-DECK"}


def test_built_up_beams_take_the_wide_roll(rows):
    """The 4 1/2" beams and the 1 1/2" girts must not land on one row, or one order."""
    by_tag = {tag: row for row in rows for tag in row["tags"]}
    for tag in BUILT_UP_BEAMS:
        assert by_tag[tag]["material"] == "butyl-tape-beam", tag
        assert by_tag[tag]["width_in"] == pytest.approx(4.5), tag
    for tag in GIRTS:
        assert by_tag[tag]["material"] == "butyl-tape", tag
        assert by_tag[tag]["width_in"] == pytest.approx(1.5), tag


def test_beam_length_is_the_axis_length(rows):
    """Taken off the beam's two nodes, exactly as ``_resolve_beam`` takes it.

    The three balcony beams span 9'-8" node to node since 2026-08-29 (the balcony's front
    plane moved 12" south of the porch's; the beams keep both ends and grew with it). A cap
    or a tape run measured off anything else — the deck outline, the solid's bounding box —
    drifts the moment the beam's bearing moves, which is the failure this pins.
    """
    beam_rows = [r for r in rows if r["scope"] == "beam" and r["width_in"] == 4.5]
    assert len(beam_rows) == 1
    # 3 balcony beams at 9.667' + 2 back beams at 10' + 2 front beams at 10' = 69.0'
    assert beam_rows[0]["length_ft"] == pytest.approx(69.0, abs=0.1)
    assert beam_rows[0]["count"] == 7


def test_deck_rows_follow_the_joist_field(rows):
    """A deck's tape is per stick, not per square foot — the distinction the field exists for.

    Modelling it as a ``DeckLayer`` would bill a 1 5/8" strip over the deck's whole AREA.
    These rows must therefore total the joists' own lineal feet, and must include the rim
    (a 1.25" member) as its own width so the narrow roll's order is not short.
    """
    deck_rows = [r for r in rows if r["scope"] == "deck"]
    assert {r["width_in"] for r in deck_rows} == {1.25, 1.5}
    porch_and_deck_ft = sum(r["length_ft"] for r in deck_rows)
    # Two decks of 2x8s at 16" o.c.; well past the ~180 SF the plank sheet-count sees.
    assert 300.0 < porch_and_deck_ft < 420.0


def test_untaped_model_reports_nothing(swinburne_model):
    """No ``top_protection`` anywhere is an empty section, never a zero-length row.

    A zero-foot row would price as free; an absent row is reported as unpriced scope. The
    Swinburne fixture is framed walls only — no deck and no beam — so it is the case.
    """
    assert member_protection_takeoff(swinburne_model) == []
