"""Framing dimension tables — one module, two consumers (solver + structural checks, → 11)."""

from __future__ import annotations

from typehaus.quantities import Length, inch

# Nominal → actual dressed lumber dimensions (thickness, depth) in inches.
LUMBER_ACTUAL: dict[str, tuple[float, float]] = {
    "2x4": (1.5, 3.5),
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
    "1x4": (0.75, 3.5),
    "6x6": (5.5, 5.5),  # dressed post (e.g. balcony pillars)
}

DEFAULT_SPACING = inch(16)


def member_actual(nominal: str) -> tuple[float, float]:
    return LUMBER_ACTUAL.get(nominal, (1.5, 5.5))


def king_jack_counts(opening_width: Length) -> tuple[int, int]:
    """King + jack (trimmer) studs per side, from opening width (simplified table)."""
    w_ft = opening_width.feet
    if w_ft <= 4.0:
        return (1, 1)
    if w_ft <= 6.0:
        return (1, 1)
    if w_ft <= 8.0:
        return (1, 2)
    return (2, 2)


def header_size(opening_width: Length, bearing: bool = True) -> str:
    """Header size over an opening (simplified prescriptive lookup, R602.7)."""
    w_ft = opening_width.feet
    if not bearing:
        return "2-2x6"
    if w_ft <= 4.0:
        return "2-2x8"
    if w_ft <= 6.0:
        return "2-2x10"
    if w_ft <= 8.0:
        return "2-2x12"
    return "engineered-LVL"  # beyond prescriptive; structural check flags it
