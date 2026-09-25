"""Plan-authoring shorthand: rectangles and rings of ``Point2D``.

A bare number is FEET (the unit plan source is written in); a ``Length`` is taken as is.
"""

from __future__ import annotations

from collections.abc import Iterable

from typehaus.model import Point2D, pt
from typehaus.quantities import Length, ft


def _len(v: float | Length) -> Length:
    return v if isinstance(v, Length) else ft(v)


def ring(points: Iterable[tuple[float | Length, float | Length]]) -> tuple[Point2D, ...]:
    """A closed outline from ``(x, y)`` corner pairs, in order."""
    return tuple(pt(_len(x), _len(y)) for x, y in points)


def rect(x0: float | Length, y0: float | Length,
         x1: float | Length, y1: float | Length) -> tuple[Point2D, ...]:
    """The axis-aligned rectangle between two corners, counter-clockwise from ``(x0, y0)``."""
    return ring(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
