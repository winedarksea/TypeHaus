"""Reading IRC R602.10's bracing tables — the accessors, mirroring ``deck_tables.py``.

Every lookup returns **the value and the row it was read at**, because a bracing verdict a
reviewer cannot re-derive is worth nothing: the finding prints "Table R602.10.3(1),
<=115 mph, first of two stories, 40 ft spacing, CS-WSP column: 11.5 ft" and the reviewer
opens the book at that row.

**Off the table is ``None``, never a guess.** Footnote a permits linear interpolation on
every axis; this module does not interpolate, it rounds UP to the next published column
(speed, line spacing, wall height, adjacent opening height), which is the conservative side
of each and a read that can be repeated with a ruler. Past the last column there is no
answer at all.

The one exception is wall height in **Table R602.10.5**, where rounding up is NOT the
conservative direction: the CS-WSP block is non-monotonic (an 80" adjacent opening needs
32" of panel at an 8'-0" wall and 30" at 9'-0"), so a wall between two tabulated heights
takes the LARGER of the two bracketing columns.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.structural._r602_bracing_table import (
    CS_WSP_MIN_PANEL_LENGTH_IN,
    CS_WSP_OPENING_HEIGHTS_IN,
    EAVE_TO_RIDGE_FACTOR,
    EAVE_TO_RIDGE_HEIGHTS_FT,
    END_CONDITIONS,
    END_PANEL_ALONE_IN,
    EXPOSURE_FACTOR,
    GYPSUM_OMITTED_FACTOR,
    GYPSUM_OMITTED_METHODS,
    HOLD_DOWN_FACTOR,
    HOLD_DOWN_FACTOR_METHODS,
    LINE_COUNT_FACTOR,
    MAX_BETWEEN_PANELS_FT,
    MAX_LINE_OFFSET_FT,
    MAX_LINE_SPACING_FT,
    MAX_PANEL_END_DISTANCE_FT,
    METHOD_COLUMNS,
    MIN_END_HOLDOWN_LB,
    MIN_PANEL_LENGTH_IN,
    MIN_RETURN_CORNER_IN,
    MIN_TWO_PANELS_OVER_FT,
    NO_BLOCKING_FACTOR,
    NO_BLOCKING_METHODS,
    NOT_PERMITTED,
    REQUIRED_LENGTH_FT,
    SPACINGS_FT,
    SPEEDS_MPH,
    STORY_FIRST_OF_THREE,
    STORY_FIRST_OF_TWO,
    STORY_LOCATIONS,
    STORY_TOP,
    WALL_HEIGHT_FACTOR,
    WALL_HEIGHTS_FT,
)

__all__ = [
    "TableRead", "required_bracing_length_ft", "min_panel_length_in", "exposure_factor",
    "eave_to_ridge_factor", "wall_height_factor", "line_count_factor", "method_column",
    "END_CONDITIONS", "END_PANEL_ALONE_IN", "GYPSUM_OMITTED_FACTOR",
    "GYPSUM_OMITTED_METHODS", "HOLD_DOWN_FACTOR", "HOLD_DOWN_FACTOR_METHODS",
    "MAX_BETWEEN_PANELS_FT", "MAX_LINE_OFFSET_FT", "MAX_LINE_SPACING_FT",
    "MAX_PANEL_END_DISTANCE_FT", "MIN_END_HOLDOWN_LB", "MIN_RETURN_CORNER_IN",
    "MIN_TWO_PANELS_OVER_FT", "NO_BLOCKING_FACTOR", "NO_BLOCKING_METHODS",
    "STORY_TOP", "STORY_FIRST_OF_TWO", "STORY_FIRST_OF_THREE", "STORY_LOCATIONS",
]


@dataclass(frozen=True)
class TableRead:
    """One lookup: the value, and the row it came from in the reviewer's own words."""

    value: float
    row: str

    def __str__(self) -> str:
        return self.row


def method_column(method: str) -> str | None:
    """Which column of Table R602.10.3(1) an R602.10.4 method is priced in."""
    for column, methods in METHOD_COLUMNS.items():
        if method in methods:
            return column
    return None


def _round_up(value: float, options) -> int | None:
    above = [o for o in options if o >= value - 1e-9]
    return min(above) if above else None


def required_bracing_length_ft(story_location: str, spacing_ft: float, speed_mph: float,
                               method: str) -> TableRead | None:
    """Table R602.10.3(1), unadjusted, for one line. ``None`` off the table or NP."""
    column = method_column(method)
    speed = _round_up(speed_mph, SPEEDS_MPH)
    spacing = _round_up(spacing_ft, SPACINGS_FT)
    if column is None or speed is None or spacing is None:
        return None
    if story_location not in STORY_LOCATIONS:
        return None
    cell = REQUIRED_LENGTH_FT[(speed, story_location, spacing)][column]
    if cell == NOT_PERMITTED:
        return None
    return TableRead(float(cell), (
        f"Table R602.10.3(1), V_ult <= {speed} mph, {_story_words(story_location)}, "
        f"{spacing} ft braced wall line spacing, {method} column: {cell} ft"))


def _story_words(story_location: str) -> str:
    return {
        STORY_TOP: "one story or top story of two",
        STORY_FIRST_OF_TWO: "first story of two (or second of three)",
        STORY_FIRST_OF_THREE: "first story of three",
    }[story_location]


def min_panel_length_in(method: str, wall_height_ft: float,
                        adjacent_opening_in: float | None) -> TableRead | None:
    """Table R602.10.5 — the shortest run that counts as a panel at all.

    For CS-WSP/CS-SFB the third axis is the taller of the two adjacent clear opening
    heights; ``None`` means the panel meets no opening (the table's shortest row).
    """
    brackets = _height_brackets(wall_height_ft)
    if brackets is None:
        return None
    if method in ("CS-WSP", "CS-SFB"):
        opening = _round_up(adjacent_opening_in or 0.0, CS_WSP_OPENING_HEIGHTS_IN)
        if opening is None:
            return None
        row = CS_WSP_MIN_PANEL_LENGTH_IN[opening]
        values = [row[h] for h in brackets if row[h] is not None]
        if len(values) != len(brackets):
            return None  # the table stops before this wall height at this opening
        return TableRead(float(max(values)), (
            f"Table R602.10.5, {method}, adjacent clear opening height <= {opening} in, "
            f"{_height_words(brackets)}: {max(values)} in"))
    row_any = MIN_PANEL_LENGTH_IN.get(method)
    if row_any is None:
        return None
    values = [row_any[h] for h in brackets if row_any[h] is not None]
    if len(values) != len(brackets):
        return None
    return TableRead(float(max(values)), (
        f"Table R602.10.5, {method}, {_height_words(brackets)}: {max(values)} in"))


def _height_brackets(wall_height_ft: float) -> tuple[int, ...] | None:
    """The tabulated wall-height column(s) covering this wall.

    An exact height is one column. A height between two is BOTH, and the caller takes the
    larger value — Table R602.10.5 is not monotonic in wall height, so the taller column
    is not reliably the conservative one.
    """
    if wall_height_ft < WALL_HEIGHTS_FT[0] - 1e-9:
        return (WALL_HEIGHTS_FT[0],)
    above = _round_up(wall_height_ft, WALL_HEIGHTS_FT)
    if above is None:
        return None
    if abs(above - wall_height_ft) < 1e-9:
        return (above,)
    below = max(h for h in WALL_HEIGHTS_FT if h < wall_height_ft)
    return (below, above)


def _height_words(brackets) -> str:
    if len(brackets) == 1:
        return f"{brackets[0]} ft wall height"
    return (f"wall height between the {brackets[0]} ft and {brackets[1]} ft columns "
            f"(the larger of the two, the table is not monotonic here)")


def exposure_factor(exposure: str, stories: int) -> TableRead | None:
    """Table R602.10.3(2) item 1. Footnote d: one factor for the whole structure."""
    value = EXPOSURE_FACTOR.get((min(max(stories, 1), 3), exposure))
    if value is None:
        return None
    return TableRead(value, (f"Table R602.10.3(2) item 1, Exposure {exposure}, "
                             f"{stories}-story structure: x{value:.2f}"))


def eave_to_ridge_factor(height_ft: float, supports: str) -> TableRead | None:
    """Table R602.10.3(2) item 2, by what the story carries above it.

    ``supports`` is "roof_only" / "roof_plus_1_floor" / "roof_plus_2_floors".
    """
    row = _round_up(height_ft, EAVE_TO_RIDGE_HEIGHTS_FT)
    if row is None:
        return None
    value = EAVE_TO_RIDGE_FACTOR.get((supports, row))
    if value is None or value == NOT_PERMITTED:
        return None
    label = "<= 5" if row == 5 else str(row)
    return TableRead(float(value), (
        f"Table R602.10.3(2) item 2, roof eave-to-ridge {label} ft, "
        f"{supports.replace('_', ' ')}: x{value:.2f}"))


def wall_height_factor(height_ft: float) -> TableRead | None:
    """Table R602.10.3(2) item 3 — story height per R301.3."""
    row = _round_up(height_ft, WALL_HEIGHTS_FT)
    if row is None:
        return None
    value = WALL_HEIGHT_FACTOR[row]
    return TableRead(value, (f"Table R602.10.3(2) item 3, {row} ft story height: "
                             f"x{value:.2f}"))


def line_count_factor(lines: int) -> TableRead | None:
    """Table R602.10.3(2) item 4 — braced wall lines per plan direction."""
    if lines < 2:
        return None
    value = LINE_COUNT_FACTOR.get(min(lines, 5), LINE_COUNT_FACTOR[5])
    label = ">= 5" if lines >= 5 else str(lines)
    return TableRead(value, (f"Table R602.10.3(2) item 4, {label} braced wall lines per "
                             f"plan direction: x{value:.2f}"))
