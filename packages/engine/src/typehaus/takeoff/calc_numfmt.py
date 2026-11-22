"""How a number prints in the calculation package: positional, never an exponent.

``,.4g`` printed ``fy 6e+04`` and ``seat_eccentricity 8.882e-16``, and ``,.1f`` printed a
factor of safety of 1.538 against 1.5 as ``1.5 / 1.5``. A reviewer reads margins off these.
"""

from __future__ import annotations

import math

#: Below this a value is float noise from a solver, not a quantity.
_ZERO = 1e-9


def num(value: float, sig: int = 4) -> str:
    """``value`` to at least ``sig`` significant figures, comma-grouped, no exponent."""
    if not math.isfinite(value):
        return str(value)
    if abs(value) < _ZERO:
        return "0"
    decimals = min(12, max(0, sig - 1 - math.floor(math.log10(abs(value)))))
    text = f"{value:,.{decimals}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def ratio_text(value: float) -> str:
    """A demand/capacity ratio. Three places: 0.975 is not 0.98."""
    return f"{value:.3f}"
