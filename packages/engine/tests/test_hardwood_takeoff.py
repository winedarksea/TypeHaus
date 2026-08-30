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
    # 33 since 2026-08-29 — see test_millwork.py for which six windows left with the attic
    # knee walls and the south gable's corner pair.
    assert stools and sum(row["pieces"] for row in stools) == 33
    for row in stools:
        assert row["nominal_stock"] == "8/4"
        assert row["nominal_quarters"] == 8
        assert row["milling_profile"] == "eased"
        assert row["layup"] == "one board"
        assert row["boards_per_piece"] == 1
        assert row["finished_thickness_in"] == pytest.approx(1.5)
        assert row["stock_note"] is None, "a 10\" stool comes off one 18\" board"


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

def test_a_panel_is_declared_only_when_no_ONE_BOARD_could_do_it(rows):
    """The width test is on the ROUGH face, and the distinction is the whole flag.

    A mill has to find a board it can straight-line and joint DOWN to the finished face, so
    the question is never "is the finished piece under 18-inch" — it is "is the rough
    piece". The pantry is the case that proves it: 18" finished against an 18" supply reads
    clear on the finished number and is 3/4" short on the real one, so it lays up as two
    boards rather than one.
    """
    from typehaus.takeoff.hardwood import _WIDTH_LOSS_IN

    pantry = next(row for row in _use(rows, "shelf") if "SB-M-PANTRY" in row["tags"])
    assert pantry["finished_width_in"] == pytest.approx(18.0)
    assert pantry["layup"] == "edge-glued panel"
    assert pantry["boards_per_piece"] == 2
    assert pantry["board_width_in"] == pytest.approx(9.0)
    assert pantry["rough_width_in"] == pytest.approx(9.0 + _WIDTH_LOSS_IN)
    # And the rule, over every piece row: a panel is declared when and only when one board
    # of the declared supply could not yield the finished face.
    for row in rows:
        if row["layup"] not in ("one board", "edge-glued panel"):
            continue
        too_wide = row["finished_width_in"] + _WIDTH_LOSS_IN > 18.0 + 1e-9
        assert (row["layup"] == "edge-glued panel") == too_wide


def test_a_panel_names_the_boards_it_is_actually_made_of(rows):
    """A bare "too wide" tells a sawyer nothing; the split is the actionable number."""
    panels = [row for row in rows if row["layup"] == "edge-glued panel"]
    assert panels, "the reference house has two, both shelves"
    for row in panels:
        assert row["boards_per_piece"] >= 2
        assert row["board_width_in"] * row["boards_per_piece"] == pytest.approx(
            row["finished_width_in"], abs=0.01)
        assert f'{row["boards_per_piece"]} boards' in row["stock_note"]
        assert '18.00"' in row["stock_note"], "the note names the supply it is measured on"


def test_a_shelf_inside_the_board_width_stays_one_board(rows):
    """The complement, and the assertion that keeps the panel call from being vacuous.

    Note the filter is on the FINISHED face plus the jointing loss, not on
    ``rough_width_in`` — that column is per BOARD, so a panel's is small by construction and
    filtering on it would quietly re-admit the panels this test exists to exclude.
    """
    from typehaus.takeoff.hardwood import _WIDTH_LOSS_IN

    narrow = [row for row in _use(rows, "shelf")
              if row["finished_width_in"] + _WIDTH_LOSS_IN <= 18.0]
    assert narrow and all(row["layup"] == "one board" for row in narrow)
    assert all(row["boards_per_piece"] == 1 for row in narrow)


def test_a_shelf_deeper_than_it_is_wide_is_milled_front_to_back(rows):
    """RM-S-BATH1's alcove is 18-1/2" wide in a 30"-deep carcass — the one shelf in the
    house whose depth is its LONGER plan dimension. Grain runs the long way, so the board's
    width is 18-1/2" and the layup is two boards, not a 30" panel."""
    bath = next(row for row in _use(rows, "shelf") if "SB-S-BATH1" in row["tags"])
    assert bath["finished_width_in"] == pytest.approx(18.5)
    assert bath["finished_length_in"] == pytest.approx(30.0)
    # And the rule is derived, not authored for this one case: every shelf in the house
    # has its width on the shorter of the two plan dimensions.
    for row in _use(rows, "shelf"):
        assert row["finished_width_in"] <= row["finished_length_in"]


def test_the_elm_posts_are_sawn_to_section_not_laminated_from_boards(rows):
    """The tudor posts are milled 6-1/8" square out of an elm log. They are not a stack.

    This is a REGRESSION test with a date on it. For part of 2026-08-29 the schedule read
    "5 laminations of 1-1/2" stock" here, because the row builder had one boolean for
    "bigger than the stock" and turned every such piece into a glue-up. Laminating an 8/4
    stack is a real way to make a post — it is simply not how these four are made, and the
    difference is 93 rough board feet of elm.
    """
    post = next(row for row in _use(rows, "timber post"))
    assert post["material"] == "elm-timber" and post["pieces"] == 4
    assert post["layup"] == "sawn timber"
    assert post["boards_per_piece"] == 1
    assert post["nominal_stock"] == "timber", "a timber has no nominal quarter stock"
    assert post["nominal_quarters"] is None
    # The only loss is the skim that takes the saw marks off, on both cross-section faces.
    from typehaus.takeoff.hardwood import _TIMBER_DRESS_ALLOWANCE_IN

    assert post["rough_width_in"] == pytest.approx(6.125 + _TIMBER_DRESS_ALLOWANCE_IN)
    assert "sawn" in post["stock_note"] and "dressed back" in post["stock_note"]
    # Still more rough than finished — but by the skim, not by a factor of five.
    assert post["finished_board_feet"] < post["rough_board_feet"]
    assert post["rough_board_feet"] < post["finished_board_feet"] * 1.5


def test_the_elm_material_does_not_claim_to_be_board_stock(catlin_model_ro):
    """The fix's other half, and the one that would otherwise drift back.

    ``nominal_quarters`` on a timber is what let the schedule reach for a lamination count.
    A sawn section has no nominal stock, and the material has to say so.
    """
    elm = next(m for m in catlin_model_ro.plan.library.materials
               if m.tag == "elm-timber")
    assert elm.nominal_quarters is None
    assert elm.species == "elm"


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
    for row in decks:
        # A landing resolves as ONE member because that is what the framing pass needs. A
        # schedule that reads that literally asks a mill for a 45" board; it is a walking
        # SURFACE, laid up out of boards exactly like the floor it steps onto.
        assert row["layup"] == "boards"
        assert row["boards_per_piece"] > 1
        assert row["board_width_in"] <= 18.0
        assert row["board_width_in"] * row["boards_per_piece"] == pytest.approx(
            row["finished_width_in"], abs=0.01)


def test_a_coverage_field_is_boards_and_never_a_panel(rows):
    """A floor, a wainscot and a wall liner are tongued or lapped boards, full stop."""
    for use in ("floor", "wainscot", "wall liner"):
        for row in _use(rows, use):
            assert row["layup"] == "boards"
            assert row["stock_note"] is None


# --- the exports --------------------------------------------------------------------------

def test_the_csv_and_the_markdown_carry_the_same_rows_and_the_species(rows, tmp_path):
    """Two files, one schedule. A mill gets emailed the Markdown and an estimator opens the
    CSV, so a column that exists in one and not the other is a bug waiting to be argued
    about — both are built from ``_flat_rows`` for exactly that reason.
    """
    import csv as csv_module

    from typehaus.cli.cmd_millwork import MILLWORK_COLUMNS, _flat_rows, _markdown

    assert "species" in MILLWORK_COLUMNS, "the mill sorts its pile by species first"
    assert "layup" in MILLWORK_COLUMNS

    flat = _flat_rows(rows)
    assert len(flat) == len(rows)
    assert all(set(entry) == set(MILLWORK_COLUMNS) for entry in flat)

    path = tmp_path / "milling.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv_module.DictWriter(handle, fieldnames=list(MILLWORK_COLUMNS))
        writer.writeheader()
        writer.writerows(flat)
    read_back = list(csv_module.DictReader(path.open(encoding="utf-8")))
    assert [entry["species"] for entry in read_back] == [
        str(entry["species"]) for entry in flat]

    text = _markdown(rows)
    # One table row per schedule row, plus the header and its rule.
    body = [line for line in text.splitlines() if line.startswith("| ")]
    assert len(body) >= len(rows) + 1
    for species in {str(row["species"]) for row in rows}:
        assert species in text
    assert "Rough board feet by species" in text
    assert "sawn timber" in text and "edge-glued panel" in text
