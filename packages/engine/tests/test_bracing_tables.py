"""IRC R602.10's tables, as transcribed — pinned cells, shape, and the round-up rule.

A transcription is only as good as the cells somebody checked by hand. These are those
cells, read from the 2018 IRC and confirmed against UpCodes' Minnesota rendering and ABTG's
2024 guide (see ``_r602_bracing_table.py``'s header for the full source list).
"""

from __future__ import annotations

import pytest

from typehaus.checks.structural._r602_bracing_table import (
    CS_WSP_MIN_PANEL_LENGTH_IN,
    NOT_PERMITTED,
    REQUIRED_LENGTH_FT,
    SPACINGS_FT,
    SPEEDS_MPH,
    STORY_FIRST_OF_THREE,
    STORY_FIRST_OF_TWO,
    STORY_LOCATIONS,
    STORY_TOP,
)
from typehaus.checks.structural.bracing_tables import (
    MAX_PANEL_END_DISTANCE_FT,
    eave_to_ridge_factor,
    exposure_factor,
    line_count_factor,
    method_column,
    min_panel_length_in,
    required_bracing_length_ft,
    wall_height_factor,
)


def test_the_table_is_the_published_shape():
    assert len(REQUIRED_LENGTH_FT) == len(SPEEDS_MPH) * len(STORY_LOCATIONS) * len(SPACINGS_FT)
    assert len(REQUIRED_LENGTH_FT) == 90
    assert SPEEDS_MPH == (110, 115, 120, 130, 140)


@pytest.mark.parametrize(("speed", "story", "spacing", "method", "expected"), [
    # Twelve cells read by hand, across all three story rows and every method column.
    (110, STORY_TOP, 10, "CS-WSP", 1.5),
    (110, STORY_TOP, 60, "WSP", 9.5),
    (115, STORY_TOP, 20, "CS-WSP", 3.5),
    (115, STORY_TOP, 30, "CS-WSP", 4.5),
    (115, STORY_TOP, 40, "CS-WSP", 6.0),          # catlin: second storey and the garage
    (115, STORY_FIRST_OF_TWO, 30, "CS-WSP", 9.0),
    (115, STORY_FIRST_OF_TWO, 40, "CS-WSP", 11.5),  # catlin: the main storey
    (115, STORY_FIRST_OF_TWO, 40, "WSP", 13.5),
    (115, STORY_FIRST_OF_TWO, 40, "LIB", 23.5),
    (115, STORY_FIRST_OF_THREE, 40, "CS-WSP", 17.0),
    (130, STORY_TOP, 40, "CS-WSP", 7.5),
    (140, STORY_FIRST_OF_THREE, 60, "GB", 75.5),
])
def test_pinned_cells(speed, story, spacing, method, expected):
    read = required_bracing_length_ft(story, spacing, speed, method)
    assert read is not None
    assert read.value == pytest.approx(expected)
    assert f"{spacing} ft" in read.row and f"{speed} mph" in read.row


def test_lib_is_not_permitted_on_the_first_of_three():
    for speed in SPEEDS_MPH:
        for spacing in SPACINGS_FT:
            assert REQUIRED_LENGTH_FT[(speed, STORY_FIRST_OF_THREE, spacing)]["LIB"] \
                == NOT_PERMITTED
    assert required_bracing_length_ft(STORY_FIRST_OF_THREE, 30, 115, "LIB") is None


def test_required_length_rises_with_speed_and_with_spacing():
    for story in STORY_LOCATIONS:
        for column in ("GB", "WSP", "CS"):
            for spacing in SPACINGS_FT:
                values = [REQUIRED_LENGTH_FT[(s, story, spacing)][column] for s in SPEEDS_MPH]
                values = [v for v in values if v != NOT_PERMITTED]
                assert values == sorted(values), (story, column, spacing)
            for speed in SPEEDS_MPH:
                values = [REQUIRED_LENGTH_FT[(speed, story, s)][column] for s in SPACINGS_FT]
                values = [v for v in values if v != NOT_PERMITTED]
                assert values == sorted(values), (story, column, speed)


def test_continuous_sheathing_never_asks_for_more_than_wsp():
    for key, row in REQUIRED_LENGTH_FT.items():
        if NOT_PERMITTED in (row["CS"], row["WSP"]):
            continue
        assert row["CS"] <= row["WSP"], key


def test_a_speed_or_spacing_between_columns_rounds_up():
    read = required_bracing_length_ft(STORY_TOP, 36.0, 113.0, "CS-WSP")
    assert read is not None
    assert read.value == REQUIRED_LENGTH_FT[(115, STORY_TOP, 40)]["CS"]
    assert required_bracing_length_ft(STORY_TOP, 61.0, 115, "CS-WSP") is None
    assert required_bracing_length_ft(STORY_TOP, 40, 141.0, "CS-WSP") is None


def test_the_method_columns_cover_what_they_publish():
    assert method_column("CS-WSP") == "CS"
    assert method_column("WSP") == "WSP"
    assert method_column("PFG") == "WSP"      # the "PFC" in ICC's heading is a typo for PFG
    assert method_column("GB") == "GB"
    assert method_column("NOT-A-METHOD") is None


# --- Table R602.10.5 ---------------------------------------------------------------------

def test_the_cs_wsp_minimum_reads_off_the_adjacent_opening():
    for opening, expected in ((64, 27), (80, 30), (84, 32)):
        read = min_panel_length_in("CS-WSP", 9.0, opening)
        assert read is not None and read.value == expected
    assert min_panel_length_in("CS-WSP", 9.0, None).value == 27   # no adjacent opening


def test_an_opening_between_rows_rounds_up():
    assert min_panel_length_in("CS-WSP", 9.0, 78.0).value \
        == CS_WSP_MIN_PANEL_LENGTH_IN[80][9]
    assert min_panel_length_in("CS-WSP", 9.0, 200.0) is None


def test_a_wall_between_height_columns_takes_the_LARGER_of_the_two():
    """Table R602.10.5 is NOT monotonic in wall height — at an 80" opening an 8'-0" wall
    needs 32" and a 9'-0" wall 30" — so rounding up is not the conservative direction.
    The garage's 8'-4" wall is the case."""
    read = min_panel_length_in("CS-WSP", 100.0 / 12.0, 84.0)
    assert read is not None
    assert read.value == 35   # the 8 ft column, not the 9 ft column's 32
    assert "not monotonic" in read.row


def test_the_intermittent_methods_keep_their_own_rows():
    assert min_panel_length_in("WSP", 9.0, None).value == 48
    assert min_panel_length_in("LIB", 9.0, None).value == 62
    assert min_panel_length_in("LIB", 11.0, None) is None   # the table's "NP"


# --- Table R602.10.3(2) ------------------------------------------------------------------

def test_the_adjustment_factors_read_their_rows():
    assert exposure_factor("B", 2).value == 1.00
    assert exposure_factor("C", 2).value == 1.30
    assert exposure_factor("D", 3).value == 1.70
    assert eave_to_ridge_factor(4.0, "roof_only").value == 0.70
    assert eave_to_ridge_factor(11.25, "roof_only").value == 1.30       # rounds up to 15 ft
    assert eave_to_ridge_factor(11.25, "roof_plus_1_floor").value == 1.15
    assert eave_to_ridge_factor(20.0, "roof_plus_2_floors") is None     # "Not permitted"
    assert wall_height_factor(9.0).value == 0.95
    assert wall_height_factor(100.0 / 12.0).value == 0.95               # 8'-4" rounds up
    assert line_count_factor(2).value == 1.00
    assert line_count_factor(6).value == 1.60
    assert line_count_factor(1) is None


def test_the_ten_foot_end_rule_is_ten_feet():
    """R602.10.2.2's SI conversion prints 3810 mm (12.5 ft) against its own "10 feet"; the
    customary value governs and the 12.5 ft rule it looks like was deleted after 2012."""
    assert MAX_PANEL_END_DISTANCE_FT == 10.0
