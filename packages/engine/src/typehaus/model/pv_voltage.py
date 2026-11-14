"""Table 690.7(A) (2026 NEC, printed 2026-11-14): the factor that corrects a crystalline or
multicrystalline silicon module's rated Voc to the lowest expected ambient, for a
source-circuit maximum voltage when the module lists no temperature coefficient (690.7(A)(2)).
A leaf under ``model``; the Catlin array uses the listed coefficient ((A)(1)) instead.
"""

from __future__ import annotations

from typing import Final

#: (lowest ambient of the row in °C, factor), warmest row first. Row "24 to 20" is 1.02.
_ROWS: Final = ((20, 1.02), (15, 1.04), (10, 1.06), (5, 1.08), (0, 1.10), (-5, 1.12),
                (-10, 1.14), (-15, 1.16), (-20, 1.18), (-25, 1.20), (-30, 1.21),
                (-35, 1.23), (-40, 1.25))


def voc_factor(ambient_c: float) -> float:
    """The Table 690.7(A) factor for a whole-degree ambient from 24 °C down to -40 °C."""
    if not -40 <= ambient_c <= 24:
        raise ValueError("Table 690.7(A) covers -40 to 24 degC")
    return next(f for low, f in _ROWS if ambient_c >= low)


def max_source_voltage(voc: float, series_modules: int, ambient_c: float) -> float:
    """690.7(A): rated Voc times the series count times the table factor."""
    return voc * series_modules * voc_factor(ambient_c)
