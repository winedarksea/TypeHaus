"""First-fit-decreasing packing of cut pieces into stock lengths (trim, flashing)."""

from __future__ import annotations

import math

#: Length lost per cut piece in inches: squaring the board end plus a miter or cope.
CUT_ALLOWANCE_IN = 1.0


def boards_for(lengths_in: list[float], stock_in: float | None,
               allowance_in: float = CUT_ALLOWANCE_IN) -> tuple[int, float, int]:
    """``(boards, board length, splices)`` to cut ``lengths_in`` from."""
    if stock_in is None:
        longest = max(lengths_in)
        return math.ceil(sum(lengths_in) / longest - 1e-9), longest, 0
    cuts: list[float] = []
    splices = 0
    for length in lengths_in:
        # A run longer than a board is spliced from full boards plus a remainder.
        cut = length + allowance_in
        whole = 0 if cut <= stock_in + 1e-9 else math.floor(length / stock_in)
        cuts.extend([stock_in] * whole)
        rest = cut - whole * stock_in
        if rest > allowance_in + 1e-9:
            cuts.append(rest)
        splices += whole - (rest <= allowance_in + 1e-9) if whole else 0
    remaining: list[float] = []
    for cut in sorted(cuts, reverse=True):
        slot = next((i for i, left in enumerate(remaining) if left >= cut - 1e-9), None)
        if slot is None:
            remaining.append(stock_in - cut)
        else:
            remaining[slot] -= cut
    return len(remaining), stock_in, splices
