"""IRC 2018 Tables R602.10.3(1), R602.10.3(2) and R602.10.5, transcribed — wall bracing
(→ checks/structural/bracing_tables.py, which is what a check reads).

**Transcription discipline, the ``_r404_table.py`` one.** Fetched and parsed mechanically
(headless Chromium over ICC Digital Codes' viewer for IRC2018P6 and IRC2021P2; curl for the
rest) with a rowspan/colspan-aware parser, never read by eye, then diffed cell by cell
against three further independent renderings:

* ICC Digital Codes, 2018 IRC and 2021 IRC, chapter 6 — the primary.
* UpCodes, 2018 IRC as adopted by **Minnesota**, New Jersey and Maryland (identical to one
  another), and 2021 IRC for NJ/MD/MT/UT.
* ABTG (Applied Building Technology Group), *IRC Wall Bracing Code Compliance Guide*, 2024
  IRC, Tables 3/7/8/9 — an independently typeset reproduction.

**No numeric disagreement was found**: 0 differences on all 90 cells of Table
R602.10.3(1), on Table R602.10.3(2), and on every row of Table R602.10.5, across every
source; and the 2018 and 2021 editions agree cell for cell (2021 only ADDS a "< 95 mph"
speed block). Where a conservative value would have been taken there was nothing to choose
between, so nothing here is a judgement call. Three EDITORIAL faults are flagged in place:

1. Table R602.10.3(1)'s third column heading prints "... PFH, **PFC**, CS-SFB" in ICC's
   2018 *and* 2021 renderings. PFC is not a method in Table R602.10.4; it is a typo for
   PFG, which is what UpCodes' 2021 and ABTG's 2024 print. Read as PFG.
2. R602.10.2.2's SI conversion prints "within 10 feet (**3810 mm**)". 3810 mm is 12.5 ft;
   the customary value governs and the companion R602.10.2.2.1 prints "10 feet (3048 mm)"
   correctly. The 12.5 ft figure is a *2012-era* rule ("total combined distance from each
   end") that no longer exists — do not resurrect it from the SI erratum.
3. Table R602.10.5's CS-WSP block is NOT monotonic in wall height: at an 80" adjacent
   opening a 8'-0" wall needs 32" and a 9'-0" wall needs 30". A wall between two tabulated
   heights therefore takes the LARGER of the two bracketing columns, not the taller row.

Footnote a on all three tables permits linear interpolation. This engine does not
interpolate: it reads the next column that covers the model (round UP on speed, spacing,
wall height and opening height), which is the conservative side of every axis and is a read
a plan reviewer can repeat with a ruler.

Seismic Tables R602.10.3(3)/(4) are **not** transcribed: Minnesota is SDC A statewide and
R602.10.3 items 1-2 never reach them (decision #79).
"""

from __future__ import annotations

#: Not permitted — the method may not be used at this speed/spacing/story.
NOT_PERMITTED = "NP"

#: Table R602.10.3(1)'s four method columns. The key is this module's short name; the value
#: is every R602.10.4 method the published column heading lists.
METHOD_COLUMNS: dict[str, tuple[str, ...]] = {
    "LIB": ("LIB",),
    "GB": ("GB",),
    "WSP": ("DWB", "WSP", "SFB", "PBS", "PCP", "HPS", "BV-WSP", "ABW", "PFH", "PFG",
            "CS-SFB"),
    "CS": ("CS-WSP", "CS-G", "CS-PF"),
}

#: The three story-location rows, in the order the table prints their pictograms.
STORY_TOP = "top"
STORY_FIRST_OF_TWO = "first_of_two_or_second_of_three"
STORY_FIRST_OF_THREE = "first_of_three"
STORY_LOCATIONS: tuple[str, ...] = (STORY_TOP, STORY_FIRST_OF_TWO, STORY_FIRST_OF_THREE)

#: Ultimate design wind speeds the 2018 table publishes, as printed: <=110, <=115, <=120,
#: <=130, <140 mph. (2021 adds a "<95" block ahead of them; no published cell changes.)
SPEEDS_MPH: tuple[int, ...] = (110, 115, 120, 130, 140)
#: Braced wall line spacings, feet.
SPACINGS_FT: tuple[int, ...] = (10, 20, 30, 40, 50, 60)

#: Table R602.10.3(1) — MINIMUM TOTAL LENGTH (FEET) OF BRACED WALL PANELS REQUIRED ALONG
#: EACH BRACED WALL LINE, at the header's stated basis: EXPOSURE CATEGORY B, 30-FOOT MEAN
#: ROOF HEIGHT, 10-FOOT WALL HEIGHT, 2 BRACED WALL LINES (and, implicitly, a 10-foot
#: eave-to-ridge height — that one is not in the header, it is the 1.00 row of the
#: adjustment table). Everything else is an adjustment factor below.
#: Keyed ``(speed mph, story location, braced wall line spacing ft)``.
REQUIRED_LENGTH_FT: dict[tuple[int, str, int], dict[str, float | str]] = {
    (110, STORY_TOP, 10): {'LIB': 3.5, 'GB': 3.5, 'WSP': 2.0, 'CS': 1.5},
    (110, STORY_TOP, 20): {'LIB': 6.0, 'GB': 6.0, 'WSP': 3.5, 'CS': 3.0},
    (110, STORY_TOP, 30): {'LIB': 8.5, 'GB': 8.5, 'WSP': 5.0, 'CS': 4.5},
    (110, STORY_TOP, 40): {'LIB': 11.5, 'GB': 11.5, 'WSP': 6.5, 'CS': 5.5},
    (110, STORY_TOP, 50): {'LIB': 14.0, 'GB': 14.0, 'WSP': 8.0, 'CS': 7.0},
    (110, STORY_TOP, 60): {'LIB': 16.5, 'GB': 16.5, 'WSP': 9.5, 'CS': 8.0},
    (110, STORY_FIRST_OF_TWO, 10): {'LIB': 6.5, 'GB': 6.5, 'WSP': 3.5, 'CS': 3.0},
    (110, STORY_FIRST_OF_TWO, 20): {'LIB': 11.5, 'GB': 11.5, 'WSP': 6.5, 'CS': 5.5},
    (110, STORY_FIRST_OF_TWO, 30): {'LIB': 16.5, 'GB': 16.5, 'WSP': 9.5, 'CS': 8.0},
    (110, STORY_FIRST_OF_TWO, 40): {'LIB': 21.5, 'GB': 21.5, 'WSP': 12.5, 'CS': 10.5},
    (110, STORY_FIRST_OF_TWO, 50): {'LIB': 26.5, 'GB': 26.5, 'WSP': 15.5, 'CS': 13.0},
    (110, STORY_FIRST_OF_TWO, 60): {'LIB': 31.5, 'GB': 31.5, 'WSP': 18.0, 'CS': 15.5},
    (110, STORY_FIRST_OF_THREE, 10): {'LIB': 'NP', 'GB': 9.5, 'WSP': 5.5, 'CS': 4.5},
    (110, STORY_FIRST_OF_THREE, 20): {'LIB': 'NP', 'GB': 17.0, 'WSP': 10.0, 'CS': 8.5},
    (110, STORY_FIRST_OF_THREE, 30): {'LIB': 'NP', 'GB': 24.5, 'WSP': 14.0, 'CS': 12.0},
    (110, STORY_FIRST_OF_THREE, 40): {'LIB': 'NP', 'GB': 32.0, 'WSP': 18.5, 'CS': 15.5},
    (110, STORY_FIRST_OF_THREE, 50): {'LIB': 'NP', 'GB': 39.5, 'WSP': 22.5, 'CS': 19.0},
    (110, STORY_FIRST_OF_THREE, 60): {'LIB': 'NP', 'GB': 46.5, 'WSP': 26.5, 'CS': 23.0},
    (115, STORY_TOP, 10): {'LIB': 3.5, 'GB': 3.5, 'WSP': 2.0, 'CS': 2.0},
    (115, STORY_TOP, 20): {'LIB': 6.5, 'GB': 6.5, 'WSP': 3.5, 'CS': 3.5},
    (115, STORY_TOP, 30): {'LIB': 9.5, 'GB': 9.5, 'WSP': 5.5, 'CS': 4.5},
    (115, STORY_TOP, 40): {'LIB': 12.5, 'GB': 12.5, 'WSP': 7.0, 'CS': 6.0},
    (115, STORY_TOP, 50): {'LIB': 15.0, 'GB': 15.0, 'WSP': 9.0, 'CS': 7.5},
    (115, STORY_TOP, 60): {'LIB': 18.0, 'GB': 18.0, 'WSP': 10.5, 'CS': 9.0},
    (115, STORY_FIRST_OF_TWO, 10): {'LIB': 7.0, 'GB': 7.0, 'WSP': 4.0, 'CS': 3.5},
    (115, STORY_FIRST_OF_TWO, 20): {'LIB': 12.5, 'GB': 12.5, 'WSP': 7.5, 'CS': 6.5},
    (115, STORY_FIRST_OF_TWO, 30): {'LIB': 18.0, 'GB': 18.0, 'WSP': 10.5, 'CS': 9.0},
    (115, STORY_FIRST_OF_TWO, 40): {'LIB': 23.5, 'GB': 23.5, 'WSP': 13.5, 'CS': 11.5},
    (115, STORY_FIRST_OF_TWO, 50): {'LIB': 29.0, 'GB': 29.0, 'WSP': 16.5, 'CS': 14.0},
    (115, STORY_FIRST_OF_TWO, 60): {'LIB': 34.5, 'GB': 34.5, 'WSP': 20.0, 'CS': 17.0},
    (115, STORY_FIRST_OF_THREE, 10): {'LIB': 'NP', 'GB': 10.0, 'WSP': 6.0, 'CS': 5.0},
    (115, STORY_FIRST_OF_THREE, 20): {'LIB': 'NP', 'GB': 18.5, 'WSP': 11.0, 'CS': 9.0},
    (115, STORY_FIRST_OF_THREE, 30): {'LIB': 'NP', 'GB': 27.0, 'WSP': 15.5, 'CS': 13.0},
    (115, STORY_FIRST_OF_THREE, 40): {'LIB': 'NP', 'GB': 35.0, 'WSP': 20.0, 'CS': 17.0},
    (115, STORY_FIRST_OF_THREE, 50): {'LIB': 'NP', 'GB': 43.0, 'WSP': 24.5, 'CS': 21.0},
    (115, STORY_FIRST_OF_THREE, 60): {'LIB': 'NP', 'GB': 51.0, 'WSP': 29.0, 'CS': 25.0},
    (120, STORY_TOP, 10): {'LIB': 4.0, 'GB': 4.0, 'WSP': 2.5, 'CS': 2.0},
    (120, STORY_TOP, 20): {'LIB': 7.0, 'GB': 7.0, 'WSP': 4.0, 'CS': 3.5},
    (120, STORY_TOP, 30): {'LIB': 10.5, 'GB': 10.5, 'WSP': 6.0, 'CS': 5.0},
    (120, STORY_TOP, 40): {'LIB': 13.5, 'GB': 13.5, 'WSP': 8.0, 'CS': 6.5},
    (120, STORY_TOP, 50): {'LIB': 16.5, 'GB': 16.5, 'WSP': 9.5, 'CS': 8.0},
    (120, STORY_TOP, 60): {'LIB': 19.5, 'GB': 19.5, 'WSP': 11.5, 'CS': 9.5},
    (120, STORY_FIRST_OF_TWO, 10): {'LIB': 7.5, 'GB': 7.5, 'WSP': 4.5, 'CS': 3.5},
    (120, STORY_FIRST_OF_TWO, 20): {'LIB': 14.0, 'GB': 14.0, 'WSP': 8.0, 'CS': 7.0},
    (120, STORY_FIRST_OF_TWO, 30): {'LIB': 20.0, 'GB': 20.0, 'WSP': 11.5, 'CS': 9.5},
    (120, STORY_FIRST_OF_TWO, 40): {'LIB': 25.5, 'GB': 25.5, 'WSP': 15.0, 'CS': 12.5},
    (120, STORY_FIRST_OF_TWO, 50): {'LIB': 31.5, 'GB': 31.5, 'WSP': 18.0, 'CS': 15.5},
    (120, STORY_FIRST_OF_TWO, 60): {'LIB': 37.5, 'GB': 37.5, 'WSP': 21.5, 'CS': 18.5},
    (120, STORY_FIRST_OF_THREE, 10): {'LIB': 'NP', 'GB': 11.0, 'WSP': 6.5, 'CS': 5.5},
    (120, STORY_FIRST_OF_THREE, 20): {'LIB': 'NP', 'GB': 20.5, 'WSP': 11.5, 'CS': 10.0},
    (120, STORY_FIRST_OF_THREE, 30): {'LIB': 'NP', 'GB': 29.0, 'WSP': 17.0, 'CS': 14.5},
    (120, STORY_FIRST_OF_THREE, 40): {'LIB': 'NP', 'GB': 38.0, 'WSP': 22.0, 'CS': 18.5},
    (120, STORY_FIRST_OF_THREE, 50): {'LIB': 'NP', 'GB': 47.0, 'WSP': 27.0, 'CS': 23.0},
    (120, STORY_FIRST_OF_THREE, 60): {'LIB': 'NP', 'GB': 55.5, 'WSP': 32.0, 'CS': 27.0},
    (130, STORY_TOP, 10): {'LIB': 4.5, 'GB': 4.5, 'WSP': 2.5, 'CS': 2.5},
    (130, STORY_TOP, 20): {'LIB': 8.5, 'GB': 8.5, 'WSP': 5.0, 'CS': 4.0},
    (130, STORY_TOP, 30): {'LIB': 12.0, 'GB': 12.0, 'WSP': 7.0, 'CS': 6.0},
    (130, STORY_TOP, 40): {'LIB': 15.5, 'GB': 15.5, 'WSP': 9.0, 'CS': 7.5},
    (130, STORY_TOP, 50): {'LIB': 19.5, 'GB': 19.5, 'WSP': 11.0, 'CS': 9.5},
    (130, STORY_TOP, 60): {'LIB': 23.0, 'GB': 23.0, 'WSP': 13.0, 'CS': 11.0},
    (130, STORY_FIRST_OF_TWO, 10): {'LIB': 8.5, 'GB': 8.5, 'WSP': 5.0, 'CS': 4.5},
    (130, STORY_FIRST_OF_TWO, 20): {'LIB': 16.0, 'GB': 16.0, 'WSP': 9.5, 'CS': 8.0},
    (130, STORY_FIRST_OF_TWO, 30): {'LIB': 23.0, 'GB': 23.0, 'WSP': 13.5, 'CS': 11.5},
    (130, STORY_FIRST_OF_TWO, 40): {'LIB': 30.0, 'GB': 30.0, 'WSP': 17.5, 'CS': 15.0},
    (130, STORY_FIRST_OF_TWO, 50): {'LIB': 37.0, 'GB': 37.0, 'WSP': 21.5, 'CS': 18.0},
    (130, STORY_FIRST_OF_TWO, 60): {'LIB': 44.0, 'GB': 44.0, 'WSP': 25.0, 'CS': 21.5},
    (130, STORY_FIRST_OF_THREE, 10): {'LIB': 'NP', 'GB': 13.0, 'WSP': 7.5, 'CS': 6.5},
    (130, STORY_FIRST_OF_THREE, 20): {'LIB': 'NP', 'GB': 24.0, 'WSP': 13.5, 'CS': 11.5},
    (130, STORY_FIRST_OF_THREE, 30): {'LIB': 'NP', 'GB': 34.5, 'WSP': 19.5, 'CS': 17.0},
    (130, STORY_FIRST_OF_THREE, 40): {'LIB': 'NP', 'GB': 44.5, 'WSP': 25.5, 'CS': 22.0},
    (130, STORY_FIRST_OF_THREE, 50): {'LIB': 'NP', 'GB': 55.0, 'WSP': 31.5, 'CS': 26.5},
    (130, STORY_FIRST_OF_THREE, 60): {'LIB': 'NP', 'GB': 65.0, 'WSP': 37.5, 'CS': 31.5},
    (140, STORY_TOP, 10): {'LIB': 5.5, 'GB': 5.5, 'WSP': 3.0, 'CS': 2.5},
    (140, STORY_TOP, 20): {'LIB': 10.0, 'GB': 10.0, 'WSP': 5.5, 'CS': 5.0},
    (140, STORY_TOP, 30): {'LIB': 14.0, 'GB': 14.0, 'WSP': 8.0, 'CS': 7.0},
    (140, STORY_TOP, 40): {'LIB': 18.0, 'GB': 18.0, 'WSP': 10.5, 'CS': 9.0},
    (140, STORY_TOP, 50): {'LIB': 22.5, 'GB': 22.5, 'WSP': 13.0, 'CS': 11.0},
    (140, STORY_TOP, 60): {'LIB': 26.5, 'GB': 26.5, 'WSP': 15.0, 'CS': 13.0},
    (140, STORY_FIRST_OF_TWO, 10): {'LIB': 10.0, 'GB': 10.0, 'WSP': 6.0, 'CS': 5.0},
    (140, STORY_FIRST_OF_TWO, 20): {'LIB': 18.5, 'GB': 18.5, 'WSP': 11.0, 'CS': 9.0},
    (140, STORY_FIRST_OF_TWO, 30): {'LIB': 27.0, 'GB': 27.0, 'WSP': 15.5, 'CS': 13.0},
    (140, STORY_FIRST_OF_TWO, 40): {'LIB': 35.0, 'GB': 35.0, 'WSP': 20.0, 'CS': 17.0},
    (140, STORY_FIRST_OF_TWO, 50): {'LIB': 43.0, 'GB': 43.0, 'WSP': 24.5, 'CS': 21.0},
    (140, STORY_FIRST_OF_TWO, 60): {'LIB': 51.0, 'GB': 51.0, 'WSP': 29.0, 'CS': 25.0},
    (140, STORY_FIRST_OF_THREE, 10): {'LIB': 'NP', 'GB': 15.0, 'WSP': 8.5, 'CS': 7.5},
    (140, STORY_FIRST_OF_THREE, 20): {'LIB': 'NP', 'GB': 27.5, 'WSP': 16.0, 'CS': 13.5},
    (140, STORY_FIRST_OF_THREE, 30): {'LIB': 'NP', 'GB': 39.5, 'WSP': 23.0, 'CS': 19.5},
    (140, STORY_FIRST_OF_THREE, 40): {'LIB': 'NP', 'GB': 51.5, 'WSP': 29.5, 'CS': 25.0},
    (140, STORY_FIRST_OF_THREE, 50): {'LIB': 'NP', 'GB': 63.5, 'WSP': 36.5, 'CS': 31.0},
    (140, STORY_FIRST_OF_THREE, 60): {'LIB': 'NP', 'GB': 75.5, 'WSP': 43.0, 'CS': 36.5},}

# --- Table R602.10.3(2): WIND ADJUSTMENT FACTORS ---------------------------------------
# "Multiply the length from Table R602.10.3(1) by this factor." Footnote b: the total
# adjustment is the PRODUCT of all applicable factors. Footnote a: interpolation permitted.

#: Item 1 — exposure category, by how many stories the STRUCTURE has. Footnote d: one factor
#: for the whole structure, at the worst-case exposure.
EXPOSURE_FACTOR: dict[tuple[int, str], float] = {
    (1, "B"): 1.00, (1, "C"): 1.20, (1, "D"): 1.50,
    (2, "B"): 1.00, (2, "C"): 1.30, (2, "D"): 1.60,
    (3, "B"): 1.00, (3, "C"): 1.40, (3, "D"): 1.70,
}

#: Item 2 — roof eave-to-ridge height, by what the story supports. "Not permitted" is a
#: real cell: a 20-foot eave-to-ridge over a story carrying the roof plus two floors has no
#: prescriptive answer.
EAVE_TO_RIDGE_HEIGHTS_FT: tuple[int, ...] = (5, 10, 15, 20)
EAVE_TO_RIDGE_FACTOR: dict[tuple[str, int], float | str] = {
    ("roof_only", 5): 0.70, ("roof_only", 10): 1.00,
    ("roof_only", 15): 1.30, ("roof_only", 20): 1.60,
    ("roof_plus_1_floor", 5): 0.85, ("roof_plus_1_floor", 10): 1.00,
    ("roof_plus_1_floor", 15): 1.15, ("roof_plus_1_floor", 20): 1.30,
    ("roof_plus_2_floors", 5): 0.90, ("roof_plus_2_floors", 10): 1.00,
    ("roof_plus_2_floors", 15): 1.10, ("roof_plus_2_floors", 20): NOT_PERMITTED,
}

#: Item 3 — story height (R301.3, whose own limit for wood framing is 11'-7").
WALL_HEIGHTS_FT: tuple[int, ...] = (8, 9, 10, 11, 12)
WALL_HEIGHT_FACTOR: dict[int, float] = {8: 0.90, 9: 0.95, 10: 1.00, 11: 1.05, 12: 1.10}

#: Item 4 — number of braced wall lines per plan direction. Footnote c allows 1.0 for an
#: INTERMEDIATE line whose neighbours were sized ignoring it; that credit is not taken here.
LINE_COUNT_FACTOR: dict[int, float] = {2: 1.00, 3: 1.30, 4: 1.45, 5: 1.60}

#: Item 5 — an additional 800-lb hold-down at each end of each panel. **Top story only**,
#: and the applicable methods are the INTERMITTENT ones: a continuously sheathed line does
#: not get it (which is why a CS-WSP line's hold-downs buy an end condition, never a
#: shorter required length).
HOLD_DOWN_FACTOR = 0.80
HOLD_DOWN_FACTOR_METHODS: tuple[str, ...] = ("DWB", "WSP", "SFB", "PBS", "PCP", "HPS")

#: Item 6 — interior gypsum board finish omitted from the inside face of the panels. This
#: one DOES reach CS-WSP (R602.10.4.3 exception 3 is the companion text).
GYPSUM_OMITTED_FACTOR = 1.40
GYPSUM_OMITTED_METHODS: tuple[str, ...] = ("DWB", "WSP", "SFB", "PBS", "PCP", "HPS",
                                           "CS-WSP", "CS-G", "CS-SFB")

#: Item 7 — gypsum board fastened 4" o.c. at all edges with horizontal joints blocked.
GYPSUM_FASTENING_FACTOR = 0.70
GYPSUM_FASTENING_METHODS: tuple[str, ...] = ("GB",)

#: Item 8 — horizontal blocking omitted at a horizontal sheathing joint. 2018 names WSP and
#: CS-WSP; 2021 adds PBS. Doubling the required length is the largest single factor in the
#: table, and it applies only where there IS a horizontal joint to block.
NO_BLOCKING_FACTOR = 2.00
NO_BLOCKING_METHODS: tuple[str, ...] = ("WSP", "CS-WSP")

# --- Table R602.10.5: MINIMUM LENGTH OF A BRACED WALL PANEL (inches) ---------------------
# By method and wall height. ``None`` is the table's "—": that height is not tabulated for
# the method. CS-WSP and CS-SFB are the one block with a third axis and live below.
MIN_PANEL_LENGTH_IN: dict[str, dict[int, int | None]] = {
    # DWB, WSP, SFB, PBS, PCP, HPS, BV-WSP share one row; GB matches it (its contributing
    # length halves for single-sided, which is a contribution rule, not a length rule).
    "WSP": {8: 48, 9: 48, 10: 48, 11: 53, 12: 58},
    "GB": {8: 48, 9: 48, 10: 48, 11: 53, 12: 58},
    "LIB": {8: 55, 9: 62, 10: 69, 11: None, 12: None},
    "CS-G": {8: 24, 9: 27, 10: 30, 11: 33, 12: 36},
    "PFG": {8: 24, 9: 27, 10: 30, 11: None, 12: None},
    # ABW / SDC A, B and C, V_ult < 140 mph.
    "ABW": {8: 28, 9: 32, 10: 34, 11: 38, 12: 42},
    # PFH supporting one story and roof (the roof-only row is 16/16/16).
    "PFH": {8: 24, 9: 24, 10: 24, 11: None, 12: None},
    # CS-PF / SDC A, B and C.
    "CS-PF": {8: 16, 9: 18, 10: 20, 11: None, 12: None},
}

#: The CS-WSP / CS-SFB block: minimum panel length (inches) by MAXIMUM ADJACENT CLEAR
#: OPENING HEIGHT (inches) and wall height (feet). R602.10.5: "Where a panel has an opening
#: on either side of differing heights, the taller opening height shall be used."
CS_WSP_OPENING_HEIGHTS_IN: tuple[int, ...] = (
    64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136,
    140, 144)
CS_WSP_MIN_PANEL_LENGTH_IN: dict[int, dict[int, int | None]] = {
     64: {8: 24, 9: 27, 10: 30, 11: 33, 12: 36},
     68: {8: 26, 9: 27, 10: 30, 11: 33, 12: 36},
     72: {8: 27, 9: 27, 10: 30, 11: 33, 12: 36},
     76: {8: 30, 9: 29, 10: 30, 11: 33, 12: 36},
     80: {8: 32, 9: 30, 10: 30, 11: 33, 12: 36},
     84: {8: 35, 9: 32, 10: 32, 11: 33, 12: 36},
     88: {8: 38, 9: 35, 10: 33, 11: 33, 12: 36},
     92: {8: 43, 9: 37, 10: 35, 11: 35, 12: 36},
     96: {8: 48, 9: 41, 10: 38, 11: 36, 12: 36},
    100: {8: None, 9: 44, 10: 40, 11: 38, 12: 38},
    104: {8: None, 9: 49, 10: 43, 11: 40, 12: 39},
    108: {8: None, 9: 54, 10: 46, 11: 43, 12: 41},
    112: {8: None, 9: None, 10: 50, 11: 45, 12: 43},
    116: {8: None, 9: None, 10: 55, 11: 48, 12: 45},
    120: {8: None, 9: None, 10: 60, 11: 52, 12: 48},
    124: {8: None, 9: None, 10: None, 11: 56, 12: 51},
    128: {8: None, 9: None, 10: None, 11: 61, 12: 54},
    132: {8: None, 9: None, 10: None, 11: 66, 12: 58},
    136: {8: None, 9: None, 10: None, 11: None, 12: 62},
    140: {8: None, 9: None, 10: None, 11: None, 12: 66},
    144: {8: None, 9: None, 10: None, 11: None, 12: 72},}

# --- The rules that are sentences rather than cells -------------------------------------
# Transcribed from the adopted 2018 text (read end to end before any of these citations
# shipped), so a check can quote the clause it is grading rather than paraphrase it.

#: R602.10.1.3 + Table R602.10.1.3, wind bracing, detached/townhouse, V_ult < 140 mph.
#: The published exception column reads "None".
MAX_LINE_SPACING_FT = 60.0
#: R602.10.1.2 — an exterior wall parallel to a braced wall line may be offset this far.
MAX_LINE_OFFSET_FT = 4.0
#: R602.10.2.2 — "A braced wall panel shall begin within 10 feet from each end of a braced
#: wall line." See the SI erratum above: this is 10 feet, not 12.5.
MAX_PANEL_END_DISTANCE_FT = 10.0
#: R602.10.2.2 — "The distance between adjacent edges of braced wall panels ... not greater
#: than 20 feet."
MAX_BETWEEN_PANELS_FT = 20.0
#: R602.10.2.3 — a line over 16 feet long carries not less than two panels.
MIN_TWO_PANELS_OVER_FT = 16.0
#: Figure R602.10.7 — the corner return, for a line sheathed with wood structural panels
#: (32" where it is sheathed with structural fiberboard).
MIN_RETURN_CORNER_IN = 24.0
#: Figure R602.10.7 end conditions 2 and 5 — the device at the panel edge nearest the
#: corner, fastened to the foundation or floor framing below.
MIN_END_HOLDOWN_LB = 800.0
#: Figure R602.10.7 end condition 3 — a panel at the end of the line, on its own.
END_PANEL_ALONE_IN = 48.0

#: Figure R602.10.7's five conditions, in the figure's own order, for a finding to name.
END_CONDITIONS: dict[int, str] = {
    1: "panel at the end of the line plus a 24-inch return panel around the corner",
    2: "panel at the end of the line with an 800-lb hold-down device",
    3: "a 48-inch minimum panel at the end of the line",
    4: "first panel within 10 ft of the end, with a 24-inch return panel at the corner",
    5: "first panel within 10 ft of the end, with an 800-lb hold-down on that panel",
}
