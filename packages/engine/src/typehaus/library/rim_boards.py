"""Published capacities of stock LSL rim boards, read off the maker's guide, never derived.

A rim the table does not hold is an UNKNOWN in the record that wanted it.
"""

from __future__ import annotations

from dataclasses import dataclass

TJ8000 = "Weyerhaeuser TJ-8000 TimberStrand LSL rim board guide (March 2025)"


@dataclass(frozen=True)
class RimBoardRow:
    """One rim section: allowable vertical load (plf, and lb concentrated) and, where the
    guide publishes it, the 1-ply header row as ``(clear span ft, total plf)``, uniform
    load only."""

    thickness_in: float
    depth_in: float
    vertical_plf: float
    concentrated_lb: float
    header_plf: tuple[tuple[float, float], ...]
    source: str


RIM_BOARDS = (
    RimBoardRow(1.25, 11.875, 5400.0, 3760.0, ((5.0, 951.0), (5.5, 864.0)),
                f"{TJ8000} pp.2, 5-6; ICC-ES ESR-1387, 1 1/4\" 1.3E"),
    RimBoardRow(1.5, 11.875, 6480.0, 4520.0, (), f"{TJ8000} p.2; ICC-ES ESR-1387"),
    RimBoardRow(1.75, 11.875, 7560.0, 7470.0, (), f"{TJ8000} p.2; ICC-ES ESR-1387"),
)


def rim_board(thickness_in: float, depth_in: float) -> RimBoardRow | None:
    return next((r for r in RIM_BOARDS if abs(r.thickness_in - thickness_in) < 1e-3
                 and abs(r.depth_in - depth_in) < 1e-3), None)


def header_row(row: RimBoardRow, clear_ft: float) -> tuple[float, float] | None:
    """The first published clear span at or past ``clear_ft``: reading up is conservative."""
    return next(((span, plf) for span, plf in row.header_plf if span >= clear_ft - 1e-9), None)
