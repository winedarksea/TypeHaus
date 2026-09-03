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

#: The porch's four 3-ply 2x12s — 4 1/2" across, and the members this section was written
#: for: a site-built beam with two open ply seams running its whole length.
PLY_BEAMS = {"BM-SG-BKW", "BM-SG-BKE", "BM-SG-FRW", "BM-SG-FRE"}
#: The balcony's three beams, treated structural glulam at 3 1/2" since 2026-09-03. They
#: have NO ply seam — a glulam arrives as one member — but they still take the wide roll,
#: because the common "double joist" roll is 3 1/8" and would leave a 3 1/2" top uncovered
#: at both arrises. Same SKU, different width, and the BOM's width column is what says so.
GLULAM_BEAMS = {"BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"}
#: Every beam on the wide roll, whatever its width.
BUILT_UP_BEAMS = PLY_BEAMS | GLULAM_BEAMS


@pytest.fixture(scope="module")
def rows(catlin_model_ro):
    return member_protection_takeoff(catlin_model_ro)


def test_only_authored_members_are_taped(rows):
    """The section derives nothing. Untaped framing — the whole house — must not appear."""
    taped = {tag for row in rows for tag in row["tags"]}
    assert taped == BUILT_UP_BEAMS | {"FS-SG-PORCH", "FS-SG-DECK"}


def test_the_beams_take_the_wide_roll_at_their_own_widths(rows):
    """Two widths on the wide SKU, and they must not collapse onto one row, or one order.

    The width is read off each member's own section, so the porch's 4 1/2" ply beams and the
    balcony's 3 1/2" glulams land on two rows of the same material. A single row would buy
    one roll width for both and leave whichever is wider under-covered.
    """
    by_tag = {tag: row for row in rows for tag in row["tags"]}
    for tag in PLY_BEAMS:
        assert by_tag[tag]["material"] == "butyl-tape-beam", tag
        assert by_tag[tag]["width_in"] == pytest.approx(4.5), tag
    for tag in GLULAM_BEAMS:
        assert by_tag[tag]["material"] == "butyl-tape-beam", tag
        assert by_tag[tag]["width_in"] == pytest.approx(3.5), tag


def test_beam_length_is_the_axis_length(rows):
    """Taken off the beam's two nodes, exactly as ``_resolve_beam`` takes it. A cap or a tape
    run measured off anything else — the deck outline, the solid's bounding box — drifts the
    moment the beam's bearing moves, which is the failure this pins.
    """
    wide = [r for r in rows if r["scope"] == "beam" and r["width_in"] == 4.5]
    assert len(wide) == 1
    # 2 back beams at 10' + 2 front beams at 10' = 40.0'
    assert wide[0]["length_ft"] == pytest.approx(40.0, abs=0.1)
    assert wide[0]["count"] == 4

    glulam = [r for r in rows if r["scope"] == "beam" and r["width_in"] == 3.5]
    assert len(glulam) == 1
    # 3 balcony beams at 9'-8" node to node = 29.0'
    assert glulam[0]["length_ft"] == pytest.approx(29.0, abs=0.1)
    assert glulam[0]["count"] == 3


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
