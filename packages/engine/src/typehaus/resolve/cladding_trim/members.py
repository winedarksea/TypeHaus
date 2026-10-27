"""Stock allocation for continuous formed-metal trim runs.

Lengths use a common unit chosen by the caller. A lap consumes material at every
joint, including joints between different stock lengths.
"""

from __future__ import annotations

from itertools import product
from math import ceil, isfinite


def split_stock_run(
    run_length: float, stock_lengths: tuple[float, ...], lap: float,
) -> tuple[tuple[float, float, float], ...]:
    """Return (start, end, purchased length) for the least-waste stock combination.

    The first two values are stations on the installed run; adjacent pieces overlap
    by ``lap``. Ties in purchased length favor fewer pieces, then longer pieces first.
    """
    if not isfinite(run_length) or run_length <= 0:
        raise ValueError("run length must be finite and positive")
    if not isfinite(lap) or lap < 0:
        raise ValueError("lap must be finite and nonnegative")
    lengths = tuple(sorted(set(stock_lengths), reverse=True))
    if not lengths or any(not isfinite(length) or length <= lap for length in lengths):
        raise ValueError("each stock length must be finite and greater than the lap")

    limits = [ceil(max(0.0, run_length - lap) / (length - lap)) for length in lengths]
    best = None
    for counts in product(*(range(limit + 1) for limit in limits)):
        number = sum(counts)
        if not number:
            continue
        purchased = sum(count * length for count, length in zip(counts, lengths, strict=True))
        if purchased - lap * (number - 1) + 1e-9 < run_length:
            continue
        score = (purchased, number, tuple(-count for count in counts))
        if best is None or score < best[0]:
            best = (score, counts)
    assert best is not None
    pieces = []
    start = 0.0
    for length, count in zip(lengths, best[1], strict=True):
        for _ in range(count):
            end = min(start + length, run_length)
            pieces.append((start, end, length))
            start = end - lap
    return tuple(pieces)
