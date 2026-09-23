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

#: The balcony's two edge beams, treated structural glulam at 3 1/2" since 2026-09-03. They
#: have NO ply seam — a glulam arrives as one member — but they still take the wide roll,
#: because the common "double joist" roll is 3 1/8" and would leave a 3 1/2" top uncovered
#: at both arrises. (The centre beam BM-SG-BLC left with the centre support line, 2026-09.)
GLULAM_BEAMS = {"BM-SG-BLW", "BM-SG-BLE"}
#: The north entry canopy's two headers, added with RF-BW-CANOPY on 2026-09-10: 3-ply 2x12
#: KDAT, so 4 1/2" across and two open ply seams each — the site-built beam this section
#: was written for. Since the porch's four 3-ply beams were retired (2026-09) they are the
#: only ply beams left.
PLY_BEAMS = {"BM-BW-RW", "BM-BW-RE"}
#: The porch's two single-2x12 ledgers (2026-09), on the COMMON roll at 1 1/2": no seam.
LEDGERS = {"BM-SG-LDGW", "BM-SG-LDGE"}
#: Every beam on the wide roll, whatever its width.
BUILT_UP_BEAMS = PLY_BEAMS | GLULAM_BEAMS


@pytest.fixture(scope="module")
def rows(catlin_model_ro):
    return member_protection_takeoff(catlin_model_ro)


def test_only_authored_members_are_taped(rows):
    """The section derives nothing. Untaped framing — the whole house — must not appear."""
    taped = {tag for row in rows for tag in row["tags"]}
    # BM-BW-FW left on 2026-09-10 with the north entry's middle tier of beams; BM-BW-SCSILL
    # arrived in the same pass — the west screen panel's sill, which doubles as the deck's
    # west rim, and which is an exposed treated top like every other member in this set.
    assert taped == BUILT_UP_BEAMS | LEDGERS | {
        "FS-SG-PORCH", "FS-SG-DECK", "FS-BW-FLOOR", "FS-BW-GARAGE",
        "BM-BW-SCSILL", "BM-BW-FC", "BM-BW-FE",
        "BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"}


def test_the_beams_take_the_wide_roll_at_their_own_widths(rows):
    """Two widths on the wide SKU, and they must not collapse onto one row, or one order.

    The width is read off each member's own section, so the canopy's 4 1/2" ply beams and the
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
    for tag in LEDGERS:
        assert by_tag[tag]["material"] == "butyl-tape", tag
        assert by_tag[tag]["width_in"] == pytest.approx(1.5), tag


def test_beam_length_is_the_axis_length(rows):
    """Taken off the beam's two nodes, exactly as ``_resolve_beam`` takes it. A cap or a tape
    run measured off anything else — the deck outline, the solid's bounding box — drifts the
    moment the beam's bearing moves, which is the failure this pins.
    """
    wide = [r for r in rows if r["scope"] == "beam" and r["width_in"] == 4.5]
    assert len(wide) == 1
    # The canopy's two 3-2x12 headers at 5'-8 5/8" each — PIER_LINE_Y_FT 37'-6" to
    # GARAGE_Y_SOUTH 43'-2 5/8" — for 11.4'. The porch's four ply beams (50.5' with the
    # headers) left with the centre support line in 2026-09; a beam's billed length is its
    # AXIS, so the tape followed the retirement exactly, which is the property pinned here.
    assert wide[0]["length_ft"] == pytest.approx(11.4, abs=0.1)
    assert wide[0]["count"] == 2

    glulam = [r for r in rows if r["scope"] == "beam" and r["width_in"] == 3.5]
    assert len(glulam) == 1
    # 2 balcony edge beams at 9'-8" node to node = 19.3'
    assert glulam[0]["length_ft"] == pytest.approx(19.3, abs=0.1)
    assert glulam[0]["count"] == 2

    ledgers = [r for r in rows if r["scope"] == "beam" and r["material"] == "butyl-tape"]
    assert len(ledgers) == 1
    # Two porch ledgers, N-SGM-FW..NW at 8'-8" each (y -9'-6" to -10") = 17.3'
    assert ledgers[0]["length_ft"] == pytest.approx(17.3, abs=0.1)
    assert ledgers[0]["count"] == 2


def test_deck_rows_follow_the_joist_field(rows):
    """A deck's tape is per stick, not per square foot — the distinction the field exists for.

    Modelling it as a ``DeckLayer`` would bill a 1 5/8" strip over the deck's whole AREA.
    These rows must therefore total the joists' own lineal feet, and must include the rim
    (a 1.25" member) as its own width so the narrow roll's order is not short.
    """
    deck_rows = [r for r in rows if r["scope"] == "deck"]
    assert {r["width_in"] for r in deck_rows} == {1.25, 1.5}
    porch_and_deck_ft = sum(r["length_ft"] for r in deck_rows)
    # A bound on the ORDER OF MAGNITUDE, which is all this assertion is entitled to claim
    # (a tight bound once tripped on 17.3 lf of flank blocks). Since 2026-09 both garden
    # decks are 2x12 at 12" o.c. — about one lf of stick per SF — and the north entry's two
    # floors share these rows: ~490 lf measured. Cannot be 300 and cannot be 700.
    assert 350.0 < porch_and_deck_ft < 700.0


def test_untaped_model_reports_nothing(swinburne_model):
    """No ``top_protection`` anywhere is an empty section, never a zero-length row.

    A zero-foot row would price as free; an absent row is reported as unpriced scope. The
    Swinburne fixture is framed walls only — no deck and no beam — so it is the case.
    """
    assert member_protection_takeoff(swinburne_model) == []
