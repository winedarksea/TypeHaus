"""Whole sheets for a set of laid sheathing pieces (decision #146).

A ``full`` piece is a sheet. A piece cut across its width only (``rip``, ``cut``) still
needs a sheet-length strip, so those are packed first-fit-decreasing by width, a kerf
between cuts. Two raked pieces share one strip where the second, turned end for end, fits
the first's offcut above the rake (a gable's diagonal cut). ``short`` pieces (course
remainders) are pooled by area, first against the packed sheets' offcut strips at least
``offcut_min`` wide, and the rest ceiled once per row.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_TOL_M = 0.125 * 0.0254


@dataclass(frozen=True)
class PackedSheets:
    sheets: int
    full: int
    ripped_sheets: int
    rips: int
    short_area_m2: float


def _rake(piece, vertical: bool) -> tuple[float, float] | None:
    """``(low, high)`` end heights of a raked, unholed piece; None for anything else."""
    if not vertical or piece.opening_cuts or abs(piece.z1 - piece.z1_far) <= _TOL_M:
        return None
    a, b = piece.z1 - piece.z0, piece.z1_far - piece.z0
    return min(a, b), max(a, b)


def _strips(pieces, sheet_l: float, vertical: bool) -> list[float]:
    """Strip widths to pack: raked pieces paired off where they nest, the rest as is."""
    raked = sorted(((r, p.width_m) for p in pieces if (r := _rake(p, vertical))),
                   key=lambda item: -item[0][1])
    widths = [p.width_m if vertical else p.height_m for p in pieces if not _rake(p, vertical)]
    used = [False] * len(raked)
    for i, ((lo_a, hi_a), width_a) in enumerate(raked):
        if used[i]:
            continue
        used[i] = True
        mate = next((j for j in range(i + 1, len(raked)) if not used[j]
                     and lo_a + raked[j][0][1] <= sheet_l + _TOL_M
                     and hi_a + raked[j][0][0] <= sheet_l + _TOL_M), None)
        if mate is not None:
            used[mate] = True
            width_a = max(width_a, raked[mate][1])
        widths.append(width_a)
    return widths


def pack_pieces(pieces, sheet_w: float, sheet_l: float, kerf: float, vertical: bool = True,
                offcut_min: float = 0.0) -> PackedSheets:
    """Sheets for ``pieces`` (``SheetPiece``) hung ``vertical`` (length up) or not."""
    full = sum(1 for p in pieces if p.kind == "full")
    short_area = sum(p.area_m2 for p in pieces if p.kind == "short")
    cut = [p for p in pieces if p.kind not in ("full", "short")]
    bins: list[float] = []
    for width in sorted(_strips(cut, sheet_l, vertical), reverse=True):
        need = min(width, sheet_w) + kerf
        slot = next((i for i, left in enumerate(bins) if left + _TOL_M >= need), None)
        if slot is None:
            bins.append(sheet_w + kerf - need)
        else:
            bins[slot] -= need
    offcuts = sum(left - kerf for left in bins if left - kerf >= offcut_min > 0.0) * sheet_l
    still_short = max(0.0, short_area - offcuts)
    pooled = math.ceil(still_short / (sheet_w * sheet_l) - 1e-9) if still_short > 0 else 0
    return PackedSheets(full + len(bins) + pooled, full, len(bins), len(cut), short_area)
