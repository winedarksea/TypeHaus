"""IRC 2018 Tables R602.7(1) and R602.7(2), transcribed — girder and header spans with the
required number of jack studs (NJ). One module, two consumers: the framing solver picks a
header from it (``framing/header_choice.py``) and ``structural.header_span`` grades one.

**Transcription discipline, the ``_r602_bracing_table.py`` one.** Fetched 2026-11-06 and
parsed mechanically with a rowspan/colspan-aware parser, never read by eye:

* **Primary:** UpCodes, 2018 IRC as adopted by **Minnesota** (this house's mn-2020 code).
* UpCodes 2018 IRC as adopted by Maryland: 0 differences on both tables.
* UpCodes 2021 IRC (Maryland, Montana, Utah): 0 differences on all 75 rows x 18 cells of
  R602.7(1) and all 22 rows x 6 cells of R602.7(2). 2018 = 2021.
* Waterloo IA's 2021 brochure (``Headers.pdf``), R602.7(2): checked cell by cell, 0
  differences. Its R602.7(1) page has no snow axis (it is the 30 psf column) and is not used.

**The 2015 edition is superseded and differs.** It indexes width at 20/28/36' and its spans
are longer: at 50 psf, 36', "roof, ceiling and one center-bearing floor", a 2-2x8 reads 4-1
in 2015 and 3-9 in 2018. Do not read a 2015 copy for this house.

Rows are as printed: "span/NJ" per column, span in feet-inches. R602.7(1) runs ground snow
30, 50, 70 psf, each over building width 12, 24, 36'; R602.7(2) runs width only. Notes:
a feet-inches; b No. 2 DF-L, HF, SP, SPF; c width is measured perpendicular to the ridge,
and may be interpolated; d NJ per end; e (R602.7(1) only) use 30 psf where ground snow is
below 30 and roof live load is 20 psf or less; f (e on R602.7(2)) spans assume the header's
top is laterally braced by perpendicular framing — where it is not ("cripple studs bearing
on the header"), 2x8, 2x10 and 2x12 spans are multiplied by 0.70.

This engine does not interpolate: it reads the next column that covers the model (round UP
on width and snow), a read a plan reviewer can repeat with a ruler.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

EXTERIOR_TABLE = "IRC 2018 Table R602.7(1)"
INTERIOR_TABLE = "IRC 2018 Table R602.7(2)"

ROOF_CEILING = "roof_ceiling"
ONE_CENTER_FLOOR = "one_center_floor"
ONE_CLEAR_FLOOR = "one_clear_floor"
TWO_CENTER_FLOORS = "two_center_floors"
TWO_CLEAR_FLOORS = "two_clear_floors"
ONE_FLOOR = "one_floor"
TWO_FLOORS = "two_floors"

#: The row headings as printed.
ROW_LABELS: dict[str, str] = {
    ROOF_CEILING: "Roof and ceiling",
    ONE_CENTER_FLOOR: "Roof, ceiling and one center-bearing floor",
    ONE_CLEAR_FLOOR: "Roof, ceiling and one clear-span floor",
    TWO_CENTER_FLOORS: "Roof, ceiling and two center-bearing floors",
    TWO_CLEAR_FLOORS: "Roof, ceiling, and two clear-span floors",
    ONE_FLOOR: "One floor only",
    TWO_FLOORS: "Two floors",
}

SNOW_COLUMNS_PSF: tuple[int, ...] = (30, 50, 70)
WIDTH_COLUMNS_FT: tuple[int, ...] = (12, 24, 36)
#: Note f (R602.7(1)) / e (R602.7(2)): the unbraced-top multiplier, and the depths it hits.
UNBRACED_FACTOR = 0.70
UNBRACED_MEMBERS = frozenset({"2x8", "2x10", "2x12"})
#: Note e's roof live load ceiling for reading the 30 psf column under 30 psf ground snow.
NOTE_E_ROOF_LIVE_PSF = 20.0

EXTERIOR_ROWS: dict[tuple[str, str], str] = {
    (ROOF_CEILING, "1-2x6"): "4-0/1 3-1/2 2-7/2 3-5/1 2-8/2 2-3/2 3-0/2 2-4/2 2-0/2",
    (ROOF_CEILING, "1-2x8"): "5-1/2 3-11/2 3-3/2 4-4/2 3-4/2 2-10/2 3-10/2 3-0/2 2-6/3",
    (ROOF_CEILING, "1-2x10"): "6-0/2 4-8/2 3-11/2 5-2/2 4-0/2 3-4/3 4-7/2 3-6/3 3-0/3",
    (ROOF_CEILING, "1-2x12"): "7-1/2 5-5/2 4-7/3 6-1/2 4-8/3 3-11/3 5-5/2 4-2/3 3-6/3",
    (ROOF_CEILING, "2-2x4"): "4-0/1 3-1/1 2-7/1 3-5/1 2-7/1 2-2/1 3-0/1 2-4/1 2-0/1",
    (ROOF_CEILING, "2-2x6"): "6-0/1 4-7/1 3-10/1 5-1/1 3-11/1 3-3/2 4-6/1 3-6/2 2-11/2",
    (ROOF_CEILING, "2-2x8"): "7-7/1 5-9/1 4-10/2 6-5/1 5-0/2 4-2/2 5-9/1 4-5/2 3-9/2",
    (ROOF_CEILING, "2-2x10"): "9-0/1 6-10/2 5-9/2 7-8/2 5-11/2 4-11/2 6-9/2 5-3/2 4-5/2",
    (ROOF_CEILING, "2-2x12"): "10-7/2 8-1/2 6-10/2 9-0/2 6-11/2 5-10/2 8-0/2 6-2/2 5-2/3",
    (ROOF_CEILING, "3-2x8"): "9-5/1 7-3/1 6-1/1 8-1/1 6-3/1 5-3/2 7-2/1 5-6/2 4-8/2",
    (ROOF_CEILING, "3-2x10"): "11-3/1 8-7/1 7-3/2 9-7/1 7-4/2 6-2/2 8-6/1 6-7/2 5-6/2",
    (ROOF_CEILING, "3-2x12"): "13-2/1 10-1/2 8-6/2 11-3/2 8-8/2 7-4/2 10-0/2 7-9/2 6-6/2",
    (ROOF_CEILING, "4-2x8"): "10-11/1 8-4/1 7-0/1 9-4/1 7-2/1 6-0/1 8-3/1 6-4/1 5-4/2",
    (ROOF_CEILING, "4-2x10"): "12-11/1 9-11/1 8-4/1 11-1/1 8-6/1 7-2/2 9-10/1 7-7/2 6-4/2",
    (ROOF_CEILING, "4-2x12"): "15-3/1 11-8/1 9-10/2 13-0/1 10-0/2 8-5/2 11-7/1 8-11/2 7-6/2",
    (ONE_CENTER_FLOOR, "1-2x6"): "3-3/1 2-7/2 2-2/2 3-0/2 2-4/2 2-0/2 2-9/2 2-2/2 1-10/2",
    (ONE_CENTER_FLOOR, "1-2x8"): "4-1/2 3-3/2 2-9/2 3-9/2 3-0/2 2-6/3 3-6/2 2-9/2 2-4/3",
    (ONE_CENTER_FLOOR, "1-2x10"): "4-11/2 3-10/2 3-3/3 4-6/2 3-6/3 3-0/3 4-1/2 3-3/3 2-9/3",
    (ONE_CENTER_FLOOR, "1-2x12"): "5-9/2 4-6/3 3-10/3 5-3/2 4-2/3 3-6/3 4-10/3 3-10/3 3-3/4",
    (ONE_CENTER_FLOOR, "2-2x4"): "3-3/1 2-6/1 2-2/1 3-0/1 2-4/1 2-0/1 2-8/1 2-2/1 1-10/1",
    (ONE_CENTER_FLOOR, "2-2x6"): "4-10/1 3-9/1 3-3/2 4-5/1 3-6/2 3-0/2 4-1/1 3-3/2 2-9/2",
    (ONE_CENTER_FLOOR, "2-2x8"): "6-1/1 4-10/2 4-1/2 5-7/2 4-5/2 3-9/2 5-2/2 4-1/2 3-6/2",
    (ONE_CENTER_FLOOR, "2-2x10"): "7-3/2 5-8/2 4-10/2 6-8/2 5-3/2 4-5/2 6-1/2 4-10/2 4-1/2",
    (ONE_CENTER_FLOOR, "2-2x12"): "8-6/2 6-8/2 5-8/2 7-10/2 6-2/2 5-3/3 7-2/2 5-8/2 4-10/3",
    (ONE_CENTER_FLOOR, "3-2x8"): "7-8/1 6-0/1 5-1/2 7-0/1 5-6/2 4-8/2 6-5/1 5-1/2 4-4/2",
    (ONE_CENTER_FLOOR, "3-2x10"): "9-1/1 7-2/2 6-1/2 8-4/1 6-7/2 5-7/2 7-8/2 6-1/2 5-2/2",
    (ONE_CENTER_FLOOR, "3-2x12"): "10-8/2 8-5/2 7-2/2 9-10/2 7-8/2 6-7/2 9-0/2 7-1/2 6-1/2",
    (ONE_CENTER_FLOOR, "4-2x8"): "8-10/1 6-11/1 5-11/1 8-1/1 6-4/1 5-5/2 7-5/1 5-11/1 5-0/2",
    (ONE_CENTER_FLOOR, "4-2x10"): "10-6/1 8-3/2 7-0/2 9-8/1 7-7/2 6-5/2 8-10/1 7-0/2 6-0/2",
    (ONE_CENTER_FLOOR, "4-2x12"): "12-4/1 9-8/2 8-3/2 11-4/2 8-11/2 7-7/2 10-4/2 8-3/2 7-0/2",
    (ONE_CLEAR_FLOOR, "1-2x6"): "2-11/2 2-3/2 1-11/2 2-9/2 2-1/2 1-9/2 2-7/2 2-0/2 1-8/2",
    (ONE_CLEAR_FLOOR, "1-2x8"): "3-9/2 2-10/2 2-5/3 3-6/2 2-8/2 2-3/3 3-3/2 2-6/3 2-2/3",
    (ONE_CLEAR_FLOOR, "1-2x10"): "4-5/2 3-5/3 2-10/3 4-2/2 3-2/3 2-8/3 3-11/2 3-0/3 2-6/3",
    (ONE_CLEAR_FLOOR, "1-2x12"): "5-2/2 4-0/3 3-4/3 4-10/3 3-9/3 3-2/4 4-7/3 3-6/3 3-0/4",
    (ONE_CLEAR_FLOOR, "2-2x4"): "2-11/1 2-3/1 1-10/1 2-9/1 2-1/1 1-9/1 2-7/1 2-0/1 1-8/1",
    (ONE_CLEAR_FLOOR, "2-2x6"): "4-4/1 3-4/2 2-10/2 4-1/1 3-2/2 2-8/2 3-10/1 3-0/2 2-6/2",
    (ONE_CLEAR_FLOOR, "2-2x8"): "5-6/2 4-3/2 3-7/2 5-2/2 4-0/2 3-4/2 4-10/2 3-9/2 3-2/2",
    (ONE_CLEAR_FLOOR, "2-2x10"): "6-7/2 5-0/2 4-2/2 6-1/2 4-9/2 4-0/2 5-9/2 4-5/2 3-9/3",
    (ONE_CLEAR_FLOOR, "2-2x12"): "7-9/2 5-11/2 4-11/3 7-2/2 5-7/2 4-8/3 6-9/2 5-3/3 4-5/3",
    (ONE_CLEAR_FLOOR, "3-2x8"): "6-11/1 5-3/2 4-5/2 6-5/1 5-0/2 4-2/2 6-1/1 4-8/2 4-0/2",
    (ONE_CLEAR_FLOOR, "3-2x10"): "8-3/2 6-3/2 5-3/2 7-8/2 5-11/2 5-0/2 7-3/2 5-7/2 4-8/2",
    (ONE_CLEAR_FLOOR, "3-2x12"): "9-8/2 7-5/2 6-2/2 9-0/2 7-0/2 5-10/2 8-6/2 6-7/2 5-6/3",
    (ONE_CLEAR_FLOOR, "4-2x8"): "8-0/1 6-1/1 5-1/2 7-5/1 5-9/2 4-10/2 7-0/1 5-5/2 4-7/2",
    (ONE_CLEAR_FLOOR, "4-2x10"): "9-6/1 7-3/2 6-1/2 8-10/1 6-10/2 5-9/2 8-4/1 6-5/2 5-5/2",
    (ONE_CLEAR_FLOOR, "4-2x12"): "11-2/2 8-6/2 7-2/2 10-5/2 8-0/2 6-9/2 9-10/2 7-7/2 6-5/2",
    (TWO_CENTER_FLOORS, "1-2x6"): "2-8/2 2-1/2 1-10/2 2-7/2 2-0/2 1-9/2 2-5/2 1-11/2 1-8/2",
    (TWO_CENTER_FLOORS, "1-2x8"): "3-5/2 2-8/2 2-4/3 3-3/2 2-7/2 2-2/3 3-1/2 2-5/3 2-1/3",
    (TWO_CENTER_FLOORS, "1-2x10"): "4-0/2 3-2/3 2-9/3 3-10/2 3-1/3 2-7/3 3-8/2 2-11/3 2-5/3",
    (TWO_CENTER_FLOORS, "1-2x12"): "4-9/3 3-9/3 3-2/4 4-6/3 3-7/3 3-1/4 4-3/3 3-5/3 2-11/4",
    (TWO_CENTER_FLOORS, "2-2x4"): "2-8/1 2-1/1 1-9/1 2-6/1 2-0/1 1-8/1 2-5/1 1-11/1 1-7/1",
    (TWO_CENTER_FLOORS, "2-2x6"): "4-0/1 3-2/2 2-8/2 3-9/1 3-0/2 2-7/2 3-7/1 2-10/2 2-5/2",
    (TWO_CENTER_FLOORS, "2-2x8"): "5-0/2 4-0/2 3-5/2 4-10/2 3-10/2 3-3/2 4-7/2 3-7/2 3-1/2",
    (TWO_CENTER_FLOORS, "2-2x10"): "6-0/2 4-9/2 4-0/2 5-8/2 4-6/2 3-10/3 5-5/2 4-3/2 3-8/3",
    (TWO_CENTER_FLOORS, "2-2x12"): "7-0/2 5-7/2 4-9/3 6-8/2 5-4/3 4-6/3 6-4/2 5-0/3 4-3/3",
    (TWO_CENTER_FLOORS, "3-2x8"): "6-4/1 5-0/2 4-3/2 6-0/1 4-9/2 4-1/2 5-8/2 4-6/2 3-10/2",
    (TWO_CENTER_FLOORS, "3-2x10"): "7-6/2 5-11/2 5-1/2 7-1/2 5-8/2 4-10/2 6-9/2 5-4/2 4-7/2",
    (TWO_CENTER_FLOORS, "3-2x12"): "8-10/2 7-0/2 5-11/2 8-5/2 6-8/2 5-8/3 8-0/2 6-4/2 5-4/3",
    (TWO_CENTER_FLOORS, "4-2x8"): "7-3/1 5-9/1 4-11/2 6-11/1 5-6/2 4-8/2 6-7/1 5-2/2 4-5/2",
    (TWO_CENTER_FLOORS, "4-2x10"): "8-8/1 6-10/2 5-10/2 8-3/2 6-6/2 5-7/2 7-10/2 6-2/2 5-3/2",
    (TWO_CENTER_FLOORS, "4-2x12"): "10-2/2 8-1/2 6-10/2 9-8/2 7-8/2 6-7/2 9-2/2 7-3/2 6-2/2",
    (TWO_CLEAR_FLOORS, "1-2x6"): "2-3/2 1-9/2 1-5/2 2-3/2 1-9/2 1-5/3 2-2/2 1-8/2 1-5/3",
    (TWO_CLEAR_FLOORS, "1-2x8"): "2-10/2 2-2/3 1-10/3 2-10/2 2-2/3 1-10/3 2-9/2 2-1/3 1-10/3",
    (TWO_CLEAR_FLOORS, "1-2x10"): "3-4/2 2-7/3 2-2/3 3-4/3 2-7/3 2-2/4 3-3/3 2-6/3 2-2/4",
    (TWO_CLEAR_FLOORS, "1-2x12"): "4-0/3 3-0/3 2-7/4 4-0/3 3-0/4 2-7/4 3-10/3 3-0/4 2-6/4",
    (TWO_CLEAR_FLOORS, "2-2x4"): "2-3/1 1-8/1 1-4/1 2-3/1 1-8/1 1-4/1 2-2/1 1-8/1 1-4/2",
    (TWO_CLEAR_FLOORS, "2-2x6"): "3-4/1 2-6/2 2-2/2 3-4/2 2-6/2 2-2/2 3-3/2 2-6/2 2-1/2",
    (TWO_CLEAR_FLOORS, "2-2x8"): "4-3/2 3-3/2 2-8/2 4-3/2 3-3/2 2-8/2 4-1/2 3-2/2 2-8/3",
    (TWO_CLEAR_FLOORS, "2-2x10"): "5-0/2 3-10/2 3-2/3 5-0/2 3-10/2 3-2/3 4-10/2 3-9/3 3-2/3",
    (TWO_CLEAR_FLOORS, "2-2x12"): "5-11/2 4-6/3 3-9/3 5-11/2 4-6/3 3-9/3 5-8/2 4-5/3 3-9/3",
    (TWO_CLEAR_FLOORS, "3-2x8"): "5-3/1 4-0/2 3-5/2 5-3/2 4-0/2 3-5/2 5-1/2 3-11/2 3-4/2",
    (TWO_CLEAR_FLOORS, "3-2x10"): "6-3/2 4-9/2 4-0/2 6-3/2 4-9/2 4-0/2 6-1/2 4-8/2 4-0/3",
    (TWO_CLEAR_FLOORS, "3-2x12"): "7-5/2 5-8/2 4-9/3 7-5/2 5-8/2 4-9/3 7-2/2 5-6/3 4-8/3",
    (TWO_CLEAR_FLOORS, "4-2x8"): "6-1/1 4-8/2 3-11/2 6-1/1 4-8/2 3-11/2 5-11/1 4-7/2 3-10/2",
    (TWO_CLEAR_FLOORS, "4-2x10"): "7-3/2 5-6/2 4-8/2 7-3/2 5-6/2 4-8/2 7-0/2 5-5/2 4-7/2",
    (TWO_CLEAR_FLOORS, "4-2x12"): "8-6/2 6-6/2 5-6/2 8-6/2 6-6/2 5-6/2 8-3/2 6-4/2 5-4/3",
}
INTERIOR_ROWS: dict[tuple[str, str], str] = {
    (ONE_FLOOR, "2-2x4"): "4-1/1 2-10/1 2-4/1",
    (ONE_FLOOR, "2-2x6"): "6-1/1 4-4/1 3-6/1",
    (ONE_FLOOR, "2-2x8"): "7-9/1 5-5/1 4-5/2",
    (ONE_FLOOR, "2-2x10"): "9-2/1 6-6/2 5-3/2",
    (ONE_FLOOR, "2-2x12"): "10-9/1 7-7/2 6-3/2",
    (ONE_FLOOR, "3-2x8"): "9-8/1 6-10/1 5-7/1",
    (ONE_FLOOR, "3-2x10"): "11-5/1 8-1/1 6-7/2",
    (ONE_FLOOR, "3-2x12"): "13-6/1 9-6/2 7-9/2",
    (ONE_FLOOR, "4-2x8"): "11-2/1 7-11/1 6-5/1",
    (ONE_FLOOR, "4-2x10"): "13-3/1 9-4/1 7-8/1",
    (ONE_FLOOR, "4-2x12"): "15-7/1 11-0/1 9-0/2",
    (TWO_FLOORS, "2-2x4"): "2-7/1 1-11/1 1-7/1",
    (TWO_FLOORS, "2-2x6"): "3-11/1 2-11/2 2-5/2",
    (TWO_FLOORS, "2-2x8"): "5-0/1 3-8/2 3-1/2",
    (TWO_FLOORS, "2-2x10"): "5-11/2 4-4/2 3-7/2",
    (TWO_FLOORS, "2-2x12"): "6-11/2 5-2/2 4-3/3",
    (TWO_FLOORS, "3-2x8"): "6-3/1 4-7/2 3-10/2",
    (TWO_FLOORS, "3-2x10"): "7-5/1 5-6/2 4-6/2",
    (TWO_FLOORS, "3-2x12"): "8-8/2 6-5/2 5-4/2",
    (TWO_FLOORS, "4-2x8"): "7-2/1 5-4/1 4-5/2",
    (TWO_FLOORS, "4-2x10"): "8-6/1 6-4/2 5-3/2",
    (TWO_FLOORS, "4-2x12"): "10-1/1 7-5/2 6-2/2",
}

#: Candidate order: the 2-ply sizes, then 3-ply, smallest first. Single-member rows are never
#: offered (a 1-2x header is a girder detail, not a wall header).
CANDIDATES: tuple[str, ...] = ("2-2x4", "2-2x6", "2-2x8", "2-2x10", "2-2x12",
                               "3-2x8", "3-2x10", "3-2x12")
_NOMINAL_DEPTH_IN = {"4": 3.5, "6": 5.5, "8": 7.25, "10": 9.25, "12": 11.25}
_PLY_IN = 1.5


def size_rank(size: str) -> tuple[float, int]:
    """(depth in, plies): what "smaller than" means for ``HeaderStandard``'s minimum."""
    plies, nominal = size.split("-2x")
    return _NOMINAL_DEPTH_IN[nominal], int(plies)


def size_depth_in(size: str) -> float:
    return size_rank(size)[0]


def _feet_inches(cell: str) -> float:
    feet, inches = cell.split("-")
    return int(feet) * 12 + int(inches)


@dataclass(frozen=True)
class TableCondition:
    """Which table, row and column a header is read at."""

    table: str
    row: str
    width_ft: int
    snow_psf: int | None = None

    def column(self) -> int:
        width = WIDTH_COLUMNS_FT.index(self.width_ft)
        if self.snow_psf is None:
            return width
        return SNOW_COLUMNS_PSF.index(self.snow_psf) * len(WIDTH_COLUMNS_FT) + width

    def describe(self) -> str:
        snow = f", {self.snow_psf} psf ground snow" if self.snow_psf is not None else ""
        return f'{self.table}, "{ROW_LABELS[self.row]}"{snow}, {self.width_ft}\' width'


@dataclass(frozen=True)
class HeaderRow:
    size: str
    span_in: float
    jacks: int
    condition: TableCondition
    unbraced: bool = False

    @property
    def allowable_in(self) -> float:
        return self.span_in * (UNBRACED_FACTOR if self.unbraced else 1.0)

    def describe(self) -> str:
        span = f"{int(self.span_in // 12)}'-{int(self.span_in % 12)}\""
        factor = f" x {UNBRACED_FACTOR:.2f} (top unbraced, cripples)" if self.unbraced else ""
        return (f"{self.condition.describe()}: {self.size} {span}{factor} = "
                f"{self.allowable_in:.1f}\", NJ {self.jacks}")


def _snow_column(ground_snow_psf: float) -> int | None:
    if ground_snow_psf < SNOW_COLUMNS_PSF[0]:
        return SNOW_COLUMNS_PSF[0]  # note e; the IRC roof live load is 20 psf (R301.6)
    return next((c for c in SNOW_COLUMNS_PSF if ground_snow_psf <= c + 1e-9), None)


def table_condition(exterior: bool, roof: bool, floors: tuple[str, ...],
                    width_ft: float | None,
                    ground_snow_psf: float | None) -> TableCondition | str:
    """The table cell a header with this load reads at, or the reason there is none.

    ``floors`` holds ``"center"`` or ``"clear"`` per floor carried. An exterior wall reads
    R602.7(1), whose every row carries the roof (a floor-only exterior wall reads the roof
    row too, which only adds load). An interior wall reads R602.7(2), which has no roof row.
    """
    if not roof and not floors:
        return "it carries no derivable roof or floor"
    if len(floors) > 2:
        return f"it carries {len(floors)} floors; R602.7 stops at two"
    if width_ft is None:
        return "no building width is derivable from its roof or floor bearing lines"
    width = next((c for c in WIDTH_COLUMNS_FT if width_ft <= c + 1e-6), None)
    if width is None:
        return f"building width {width_ft:.1f}' is past the table's 36'"
    if not exterior:
        if roof:
            return "an interior wall carrying roof has no R602.7(2) row"
        return TableCondition(INTERIOR_TABLE, ONE_FLOOR if len(floors) == 1 else TWO_FLOORS,
                              width)
    if ground_snow_psf is None:
        return "the site's ground snow load is not authored"
    snow = _snow_column(ground_snow_psf)
    if snow is None:
        return f"ground snow {ground_snow_psf:g} psf is past the table's 70 psf"
    clear = "clear" in floors
    row = (ROOF_CEILING if not floors
           else (ONE_CLEAR_FLOOR if clear else ONE_CENTER_FLOOR) if len(floors) == 1
           else (TWO_CLEAR_FLOORS if clear else TWO_CENTER_FLOORS))
    return TableCondition(EXTERIOR_TABLE, row, width, snow)


def row_for(condition: TableCondition, size: str, unbraced: bool = False) -> HeaderRow | None:
    """The tabulated cell for ``size`` at ``condition``, or None where the table has none."""
    rows = EXTERIOR_ROWS if condition.table == EXTERIOR_TABLE else INTERIOR_ROWS
    printed = rows.get((condition.row, size))
    if printed is None:
        return None
    span, jacks = printed.split()[condition.column()].split("/")
    member = size.split("-", 1)[1]
    return HeaderRow(size, _feet_inches(span), int(jacks), condition,
                     unbraced and member in UNBRACED_MEMBERS)


def header_row(condition: TableCondition, clear_span_in: float, stud_depth_in: float, *,
               min_size: str | None = None,
               unbraced: Callable[[str], bool] = lambda size: False,
               fits: Callable[[str], bool] = lambda size: True) -> HeaderRow | None:
    """The smallest candidate whose allowable span covers ``clear_span_in``, or None.

    Plies must fit the stud depth; ``min_size`` drops anything smaller; ``unbraced(size)``
    says the header would carry cripples (note f); ``fits(size)`` that it stands under the
    plates. A size that does not fit is tried only when nothing that fits passes.
    """
    floor = size_rank(min_size) if min_size else None
    sized = [size for size in CANDIDATES
             if int(size[0]) * _PLY_IN <= stud_depth_in + 1e-6
             and (floor is None or size_rank(size) >= floor)]
    for require_fit in (True, False):
        for size in sized:
            if require_fit and not fits(size):
                continue
            row = row_for(condition, size, unbraced(size))
            if row is not None and row.allowable_in + 1e-6 >= clear_span_in:
                return row
    return None
