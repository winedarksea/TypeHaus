"""The milling schedule — yield arithmetic, glue-up flagging, and the no-double-billing
contract (→ takeoff/hardwood.py).

Two things are being defended here. The first is that this section is a **view**: it
re-presents wood that is already ordered somewhere else, and a row that mirrors another
section has to say so, or a caller summing sections buys the same oak twice. The second is
that rough stock is not finished stock — a schedule that reported finished dimensions to a
sawyer would under-order every piece in the house.
"""

from __future__ import annotations

import pytest

M_TO_IN = 39.37007874


@pytest.fixture(scope="module")
def rows(catlin_model_ro):
    from typehaus.takeoff.hardwood import hardwood_takeoff

    return hardwood_takeoff(catlin_model_ro)


def _use(rows, name):
    return [row for row in rows if row["use"] == name]


# --- the view contract ---------------------------------------------------------------------

def test_every_shared_row_declares_where_it_really_bills(rows):
    """``wood_surfaces``'s contract, followed: a mirror row names its primary section.

    Only the stools and the shelf boards are this section's own — everything else is wood
    the BOM already orders under another name, and summing the sections must not double it.
    """
    mirrors = ("also_in_framing", "also_in_stair_finish", "also_in_wood_surfaces",
               "also_in_floor_finishes", "also_in_envelope_layers",
               "also_in_structural_solids")
    for row in rows:
        own = row["use"] in ("window stool", "shelf")
        flagged = any(row.get(flag) for flag in mirrors)
        assert own != flagged, (
            f"{row['use']} / {row['material']}: a row is either this section's own or a "
            f"mirror of another, never both and never neither")


def test_the_schedule_is_declared_unpriced(rows):
    """It reaches the BOM but never the estimate — the fabrication labour is an allowance."""
    from typehaus.cli.prices import UNPRICED_VIEWS

    assert "hardwood" in UNPRICED_VIEWS
    assert rows, "catlin resolves hardwood; the waiver is not covering an empty section"


def test_coverage_rows_reconcile_with_wood_surfaces_to_the_digit(rows, catlin_model_ro):
    """Area and board feet come straight off the ``wood_surfaces`` row, never re-derived."""
    from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff

    source = {row["material"]: row for row in wood_surfaces_takeoff(catlin_model_ro)}
    coverage = [row for row in rows if row["pieces"] is None]
    assert coverage
    for row in coverage:
        origin = source[row["material"]]
        assert row["coverage_sqft"] == origin["order_area_sqft"]
        assert row["rough_board_feet"] == origin["board_feet"]


def test_a_panelling_band_with_no_species_stays_out(rows):
    """``wood_surfaces`` carries the sauna's tile splash; a milling schedule must not."""
    assert all(row["species"] is not None for row in rows)
    assert "tile" not in {row["material"] for row in rows}


# --- rough-stock yield ----------------------------------------------------------------------

def test_rough_stock_always_exceeds_the_finished_piece(rows):
    """The whole reason the section exists. Width loss to straight-lining and jointing, a
    defect-and-trim length allowance, and the stock's own thickness over the dressed one."""
    for row in _use(rows, "window stool") + _use(rows, "shelf") + _use(rows, "stair tread"):
        assert row["rough_board_feet"] > row["finished_board_feet"], row["use"]


def test_a_stool_is_scheduled_at_its_rough_size_from_eight_quarter_stock(rows):
    stools = _use(rows, "window stool")
    assert stools and sum(row["pieces"] for row in stools) == 39
    for row in stools:
        assert row["nominal_stock"] == "8/4"
        assert row["nominal_quarters"] == 8
        assert row["milling_profile"] == "eased"
        assert row["laminations"] == 1
        assert row["finished_thickness_in"] == pytest.approx(1.5)
        assert not row["glue_up"], "a 10\" stool comes off one 18\" board"


def test_the_yield_arithmetic_is_the_documented_one(rows):
    """Re-derived from the module's own named constants, so a silent change to either the
    width loss or the length allowance fails here rather than in a mill's invoice."""
    from typehaus.takeoff.hardwood import _LENGTH_ALLOWANCE, _WIDTH_LOSS_IN

    row = max(_use(rows, "window stool"), key=lambda r: r["pieces"])
    rough_sf = (row["pieces"] * (row["finished_width_in"] + _WIDTH_LOSS_IN)
                * row["finished_length_in"] * (1.0 + _LENGTH_ALLOWANCE) / 144.0)
    assert row["rough_surface_sqft"] == pytest.approx(round(rough_sf, 1), abs=0.05)
    assert row["rough_board_feet"] == pytest.approx(
        round(rough_sf * row["nominal_quarters"] / 4.0, 1), abs=0.05)


def test_a_tng_or_shiplap_face_exceeds_its_coverage(rows):
    """The tongue and the lap are face width the mill saws and the wall never sees."""
    liner = next(row for row in _use(rows, "wall liner"))
    assert liner["milling_profile"] == "shiplap"
    assert liner["rough_surface_sqft"] > liner["coverage_sqft"]
    floor = next(row for row in _use(rows, "floor"))
    assert floor["milling_profile"] == "T&G"
    assert floor["rough_surface_sqft"] > floor["coverage_sqft"]


def test_the_oak_floor_finally_carries_board_feet(rows):
    """It printed none until ``oak`` authored ``stock_bf_per_sqft`` — 4/4, so bf == sf."""
    floor = next(row for row in _use(rows, "floor"))
    assert floor["rough_board_feet"] == pytest.approx(floor["coverage_sqft"], abs=0.05)


# --- the glue-up flag -------------------------------------------------------------------

def test_a_piece_wider_than_the_available_board_is_flagged(rows):
    """The flag the schedule exists to raise. 18" is the owner's stock; these are past it."""
    flagged = {(row["use"], row["finished_width_in"])
               for row in rows if row["glue_up"]}
    widths = {width for use, width in flagged if use in ("shelf", "stair landing deck")}
    assert 24.0 in widths, "the 24\"-deep pantry shelf cannot come off one board"
    assert 30.0 in widths, "the 30\"-deep bath alcove shelf cannot either"
    for row in rows:
        if row["glue_up"] and row["finished_width_in"] > 18.0:
            assert "width" in row["glue_up_reason"]


def test_a_shelf_inside_the_board_width_is_not_flagged(rows):
    """The complement, and the assertion that keeps the flag from being vacuously true."""
    narrow = [row for row in _use(rows, "shelf") if row["finished_width_in"] <= 18.0]
    assert narrow and not any(row["glue_up"] for row in narrow)


def test_the_elm_posts_schedule_as_a_glue_up_not_as_four_timbers(rows):
    """A clear 6" elm timber would check badly drying, so it is laminated from 8/4 stock.

    ``wood_surfaces`` bills it as a section over an ordered length, which is right for an
    estimator and unbuildable for a mill: five layers of a 1-1/2" dressed board is the
    instruction, and the rough quantity is five times the piece.
    """
    post = next(row for row in _use(rows, "timber post"))
    assert post["material"] == "elm-timber" and post["pieces"] == 4
    assert post["nominal_stock"] == "8/4"
    assert post["laminations"] == 5
    assert post["glue_up"] and "thickness" in post["glue_up_reason"]
    # Five 1-1/2" laminae make 7-1/2" of stock for a 6-1/8" finished face, and the width
    # loss and length allowance ride on top — so the rough order is comfortably more than
    # the finished volume ``wood_surfaces`` reports, and that gap IS the glue-up.
    assert post["rough_board_feet"] > post["finished_board_feet"] * 1.5


# --- stairs ------------------------------------------------------------------------------

def test_only_the_two_oak_flights_are_scheduled(rows, catlin_model_ro):
    """28 treads: ST-M2S's 13 and ST-S2A's 15. ST-B2M is carpeted and the garage flight is
    KDAT, and until ``MillworkStandard`` said so that split lived in a price comment."""
    treads = _use(rows, "stair tread")
    assert sum(row["pieces"] for row in treads) == 28
    scheduled = {tag for row in treads for tag in row["tags"]}
    assert scheduled == {"ST-M2S", "ST-S2A"}
    assert all(row["milling_profile"] == "bullnose" for row in treads)


def test_a_tread_is_scheduled_lying_flat(rows):
    """Thickness is the narrow face of the section whichever order the profile names them
    in — ``deck 11x1.5`` and ``tapered tread`` parse to opposite orders."""
    for row in _use(rows, "stair tread"):
        assert row["finished_thickness_in"] == pytest.approx(1.5)
        assert row["finished_width_in"] > row["finished_thickness_in"]


def test_the_landing_decks_are_scheduled_and_flagged(rows):
    decks = _use(rows, "stair landing deck")
    assert sum(row["pieces"] for row in decks) == 2
    assert all(row["glue_up"] for row in decks), "a 44\" deck is boards, not a board"
