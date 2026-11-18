"""Published capacities of stock LSL rim boards, read off the maker's guide, never derived.

A rim the table does not hold is an UNKNOWN in the record that wanted it.
"""

from __future__ import annotations

from dataclasses import dataclass

TJ8000 = "Weyerhaeuser Trus Joist Rim Board Specifier's Guide TJ-8000 (March 2025)"


#: p.5 note: the concentrated row needs at least this bearing width; p.6: the header's end
#: bearing.
MIN_BEARING_IN = 4.5


@dataclass(frozen=True)
class RimBoardRow:
    """One rim section: allowable vertical load at bearing (p.5: plf, and lb concentrated,
    neither increased for duration) and, where read, the 1-ply header row (p.6) as
    ``(span ft c-c of bearing, total plf)``: uniform load, simple span, L/240 total."""

    thickness_in: float
    depth_in: float
    vertical_plf: float
    concentrated_lb: float
    header_plf: tuple[tuple[float, float], ...]
    source: str


RIM_BOARDS = (
    RimBoardRow(1.25, 11.875, 5400.0, 3760.0, ((5.0, 951.0), (5.5, 864.0), (6.0, 792.0)),
                f"{TJ8000} pp.5-6; ICC-ES ESR-1387 Table 4, 1 1/4\" 1.3E"),
    RimBoardRow(1.5, 11.875, 6480.0, 4520.0, (), f"{TJ8000} p.5, 1 1/2\" 1.3E"),
    # TJ-8000 sells its 1 3/4" as 1.55E beam stock; a 1.3E 1 3/4" rates 4,520 lb (ESR-1387).
    RimBoardRow(1.75, 11.875, 7560.0, 7470.0, (), f"{TJ8000} p.5, 1 3/4\" 1.55E"),
)


def rim_board(thickness_in: float, depth_in: float) -> RimBoardRow | None:
    return next((r for r in RIM_BOARDS if abs(r.thickness_in - thickness_in) < 1e-3
                 and abs(r.depth_in - depth_in) < 1e-3), None)


def header_row(row: RimBoardRow, span_ft: float) -> tuple[float, float] | None:
    """The first published span at or past ``span_ft`` (c-c of bearing, p.6 "How to Use"
    step 2): reading up is conservative."""
    return next(((span, plf) for span, plf in row.header_plf if span >= span_ft - 1e-9), None)
