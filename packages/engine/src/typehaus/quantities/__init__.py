"""Typed quantity value types — the tier-zero type-safety story (→ 10 §Quantities).

All canonical-SI internally; authored unit preserved for source round-trips.
"""

from __future__ import annotations

from typehaus.quantities._base import UnitSystem
from typehaus.quantities.angle import Angle, Pitch, deg, rad
from typehaus.quantities.area import Area, sqft, sqm
from typehaus.quantities.length import M_PER_FT, M_PER_IN, Length, ft, inch, m, mm
from typehaus.quantities.point import Point2D, pt
from typehaus.quantities.thermal import (
    RValue,
    Temperature,
    UFactor,
    degC,
    degF,
    r_us,
    rsi,
    u_us,
)

__all__ = [
    "UnitSystem",
    "Length", "ft", "inch", "mm", "m", "M_PER_FT", "M_PER_IN",
    "Angle", "deg", "rad", "Pitch",
    "Area", "sqft", "sqm",
    "RValue", "r_us", "rsi", "UFactor", "u_us",
    "Temperature", "degC", "degF",
    "Point2D", "pt",
]
