"""How a number prints in the calculation package: positional, never an exponent.

``,.4g`` printed ``fy 6e+04`` and ``seat_eccentricity 8.882e-16``, and ``,.1f`` printed a
factor of safety of 1.538 against 1.5 as ``1.5 / 1.5``. A reviewer reads margins off these.
:func:`num` lives in the engineering leaf so calc modules format their working the same way.
"""

from __future__ import annotations

from typehaus.engineering.item import num

__all__ = ["num", "ratio_text"]


def ratio_text(value: float) -> str:
    """A demand/capacity ratio. Three places: 0.975 is not 0.98."""
    return f"{value:.3f}"
