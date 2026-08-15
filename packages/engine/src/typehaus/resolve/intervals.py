"""1D interval arithmetic on ``(lo, hi)`` float pairs (meters, along a wall/run axis).

Four resolvers hand-rolled the same merge-then-subtract logic for cutting openings out of a
band (``framing/furring.py``, ``checks/mep/electrical.py``, ``geometry_walls.py``,
``paneling.py``). This is that logic, in one place — ``framing/furring.py``'s was the most
complete of the four and is what this module is built from.
"""

from __future__ import annotations

Interval = tuple[float, float]


def merge(intervals: list[Interval]) -> list[Interval]:
    """Sorted, overlap-merged form of ``intervals``. Touching intervals (within 1e-9) merge
    too, so a caller never has to worry about a zero-width gap surviving as its own span."""
    ordered = sorted((lo, hi) for lo, hi in intervals if hi > lo)
    merged: list[Interval] = []
    for lo, hi in ordered:
        if merged and lo <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def subtract(lo: float, hi: float, cuts: list[Interval]) -> list[Interval]:
    """``[lo, hi]`` with each interval in ``cuts`` removed, left to right.

    ``cuts`` may be unsorted, overlap each other, or reach outside ``[lo, hi]`` — every cut is
    clamped to ``[lo, hi]`` here, so a caller (an opening taller than the wall, one that sits
    right at the band's edge) never has to clamp its own cuts before calling. An empty ``cuts``
    returns ``[(lo, hi)]`` unchanged, the identity a wall with no openings relies on.
    """
    if hi - lo <= 1e-9:
        return []
    clamped = merge([(max(lo, c0), min(hi, c1)) for c0, c1 in cuts if c1 > c0])

    segments: list[Interval] = []
    cursor = lo
    for c0, c1 in clamped:
        if c0 - cursor > 1e-9:
            segments.append((cursor, c0))
        cursor = max(cursor, c1)
    if hi - cursor > 1e-9:
        segments.append((cursor, hi))
    return segments
