"""The one-dimensional sheet walk shared by columns (along s) and courses (along z).

A walk lays ``size`` pieces from ``lo`` toward ``hi``. Each break snaps back to the last
candidate at or before ``lo + k*size`` whose joint is backed (and no nearer than
``min_rip`` to the previous break); none, and it takes the least-unbacked candidate. A
last piece under ``min_rip`` pulls the previous break back. ``tail`` lets the band end
that much past whole pieces without another (``max_course_shortfall``). A walk from
``hi`` mirrors it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

_EPS = 1e-6


def _snap(start: float, target: float, latest: Iterable[float], cost: Callable[[float], float],
          min_rip: float, tol: float) -> float:
    """The latest backed station; failing one, the least-unbacked (the module on a tie)."""
    floor = start + min_rip - _EPS
    options = sorted({min(target, x) for x in latest if min(target, x) >= floor}, reverse=True)
    best, best_cost = target, cost(target)
    if best_cost <= tol:
        return target
    for x in options:
        unbacked = cost(x)
        if unbacked <= tol:
            return x
        if unbacked < best_cost - tol:
            best, best_cost = x, unbacked
    return best


def _backtrack(breaks: list[float], lo: float, cursor: float, latest: list[float],
               cost: Callable[[float], float], min_rip: float, tol: float,
               size: float) -> float:
    """Pull the previous break back to an earlier face where that lets this one land on
    better framing (one level: an opening's head often has nothing over it)."""
    before = breaks[-2] if len(breaks) > 1 else lo
    floor = before + min_rip - _EPS
    prev_cost, best = cost(breaks[-1]), cost(cursor)
    for alt in sorted({x for x in latest if floor <= x < breaks[-1] - _EPS}, reverse=True):
        alt_cost = cost(alt)
        if alt_cost > prev_cost + tol:
            continue
        nxt = _snap(alt, alt + size, latest, cost, min_rip, tol)
        if alt_cost + cost(nxt) < prev_cost + best - tol:
            breaks[-1] = alt
            return nxt
    return cursor


def walk_forward(lo: float, hi: float, size: float, latest: list[float],
                 cost: Callable[[float], float], min_rip: float, tol: float,
                 tail: float = 0.0) -> list[float]:
    """Breaks laid from ``lo``; ``latest`` holds each backing face's preferred station."""
    breaks: list[float] = []
    cursor = lo
    while hi - cursor > size + tail + _EPS:
        start = cursor
        cursor = _snap(start, start + size, latest, cost, min_rip, tol)
        if breaks and cost(cursor) > tol:
            cursor = _backtrack(breaks, lo, cursor, latest, cost, min_rip, tol, size)
        breaks.append(cursor)
    if breaks and _EPS < hi - cursor < min_rip - _EPS:
        before = breaks[-2] if len(breaks) > 1 else lo
        breaks[-1] = _snap(before, min(before + size, hi - min_rip), latest, cost, min_rip,
                           tol)
    return breaks


def walk(lo: float, hi: float, size: float, faces: list[tuple[float, float]], bearing: float,
         cost: Callable[[float], float], min_rip: float, tol: float, from_hi: bool = False,
         tail: float = 0.0) -> list[float]:
    """Ascending breaks between ``lo`` and ``hi`` over backing ``faces`` ``(a, b)``.

    A break snaps to a face's centre line (or the module where that lies past it, inside
    the face); ``cost`` is a station's
    unbacked joint length and ``tol`` the most that still counts as backed.
    """
    if not from_hi:
        latest = [(a + b) / 2.0 for a, b in faces if b - a > 2 * bearing]
        return walk_forward(lo, hi, size, latest, cost, min_rip, tol, tail)
    latest = [-(a + b) / 2.0 for a, b in faces if b - a > 2 * bearing]
    mirrored = walk_forward(-hi, -lo, size, latest, lambda x: cost(-x), min_rip, tol, tail)
    return sorted(-x for x in mirrored)


def pieces(lo: float, hi: float, breaks: list[float], size: float,
           from_hi: bool = False) -> list[tuple[float, float]]:
    """The intervals between breaks, the end piece held to ``size`` (a shortfall)."""
    edges = [lo, *breaks, hi]
    spans = list(zip(edges, edges[1:], strict=False))
    if from_hi:
        a, b = spans[0]
        spans[0] = (max(a, b - size), b)
    else:
        a, b = spans[-1]
        spans[-1] = (a, min(b, a + size))
    return spans
