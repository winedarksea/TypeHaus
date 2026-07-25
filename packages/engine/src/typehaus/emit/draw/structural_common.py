"""Shared primitives for the structural permit sheets S-100/S-101 (→ 30 §Sheets).

Notation (feet-and-inches, bearing elevations) and the handful of plan-geometry helpers
both structural sheet builders need. Keeping them here rather than in ``_shared`` keeps the
architectural plan family and the structural sheet family independent.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import M_TO_IN

M_TO_FT = 3.280839895013123
IN_PER_FT = 12.0


def feet_inches(meters: float) -> str:
    """Architectural length notation, e.g. ``12'-6"`` — rounded to the nearest inch."""
    total_inches = round(meters * M_TO_IN)
    sign = "-" if total_inches < 0 else ""
    total_inches = abs(total_inches)
    return f"{sign}{int(total_inches // IN_PER_FT)}'-{int(total_inches % IN_PER_FT)}\""


def inches(meters: float) -> str:
    """Thickness notation to the nearest eighth, e.g. ``8"`` / ``3-1/2"``.

    A 3-1/2" slab must not print as 4" on a schedule the concrete crew reads, so this keeps
    the eighth-inch fraction carpenters and the authored ``Length`` both work in.
    """
    return inches_text(meters * M_TO_IN)


EIGHTHS_PER_INCH = 8


def inches_text(total_inches: float) -> str:
    eighths = round(total_inches * EIGHTHS_PER_INCH)
    whole, remainder = divmod(abs(eighths), EIGHTHS_PER_INCH)
    sign = "-" if eighths < 0 else ""
    if remainder == 0:
        return f"{sign}{whole}\""
    numerator, denominator = remainder, EIGHTHS_PER_INCH
    while numerator % 2 == 0:
        numerator //= 2
        denominator //= 2
    return f"{sign}{whole}-{numerator}/{denominator}\"" if whole else \
        f"{sign}{numerator}/{denominator}\""


def elevation_feet(meters: float) -> str:
    """Bearing/top-of-wall elevation in decimal feet off the project grade datum.

    Decimal feet (not feet-and-inches) is the surveying convention a footing schedule and a
    site plan share, and the project datum is grade, so the sign reads as depth directly.
    """
    return f"{meters * M_TO_FT:+.2f}'"


def outline_center(outline) -> tuple[float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def outline_bbox(outline) -> tuple[float, float, float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def bboxes_overlap(a: tuple[float, float, float, float],
                   b: tuple[float, float, float, float], tolerance: float = 0.0) -> bool:
    return (a[0] <= b[2] + tolerance and b[0] <= a[2] + tolerance
            and a[1] <= b[3] + tolerance and b[1] <= a[3] + tolerance)


def point_in_bbox(point: tuple[float, float],
                  box: tuple[float, float, float, float]) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def outline_area_m2(outline) -> float:
    """Shoelace area of a plan ring (rings are simple, → resolve.model.Ring)."""
    if len(outline) < 3:
        return 0.0
    total = 0.0
    for index, (x0, y0) in enumerate(outline):
        x1, y1 = outline[(index + 1) % len(outline)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def wall_center(wall) -> tuple[float, float]:
    (x0, y0), (x1, y1) = wall.axis
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def wall_length_m(wall) -> float:
    (x0, y0), (x1, y1) = wall.axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
