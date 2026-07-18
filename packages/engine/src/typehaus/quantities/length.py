"""Length — canonical meters, authored unit preserved (→ 10 §Quantities)."""

from __future__ import annotations

import re
from enum import Enum
from fractions import Fraction
from typing import TYPE_CHECKING, Any, final

from typehaus.quantities._base import UnitSystem, pydantic_quantity_schema

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

    from typehaus.quantities.area import Area

# Ported from ifcplot/units.py — the two constants that must not drift.
M_PER_FT = 0.3048
M_PER_IN = 0.0254


class AuthoredUnit(Enum):
    FT_IN = "ft_in"  # authored via ft(feet, inches)
    INCH = "inch"
    MM = "mm"
    M = "m"


@final
class Length:
    """A length in canonical meters that remembers how it was authored.

    Dimensional arithmetic is closed and type-checked: ``Length + Length -> Length``,
    ``Length * float -> Length``, ``Length * Length -> Area``. ``Length + float`` is a
    static type error (no ``__add__`` overload accepts a bare float).
    """

    __slots__ = ("_m", "_unit", "_args")

    def __init__(self, meters: float, unit: AuthoredUnit, args: tuple[float, ...]) -> None:
        object.__setattr__(self, "_m", float(meters))
        object.__setattr__(self, "_unit", unit)
        object.__setattr__(self, "_args", args)

    # --- accessors -----------------------------------------------------------
    @property
    def meters(self) -> float:
        return self._m

    @property
    def feet(self) -> float:
        return self._m / M_PER_FT

    @property
    def inches(self) -> float:
        return self._m / M_PER_IN

    @property
    def mm(self) -> float:
        return self._m * 1000.0

    # --- arithmetic (closed & type-checked) ----------------------------------
    def __add__(self, other: Length) -> Length:
        return Length(self._m + other._m, self._unit, self._args)

    def __sub__(self, other: Length) -> Length:
        return Length(self._m - other._m, self._unit, self._args)

    def __mul__(self, k: float) -> Length:
        return Length(self._m * k, self._unit, self._args)

    __rmul__ = __mul__

    def __truediv__(self, k: float) -> Length:
        return Length(self._m / k, self._unit, self._args)

    def times_length(self, other: Length) -> Area:
        """Length * Length -> Area (explicit; kept off ``__mul__`` for mypy clarity)."""
        from typehaus.quantities.area import Area

        return Area(self._m * other._m)

    def __neg__(self) -> Length:
        return Length(-self._m, self._unit, self._args)

    def __abs__(self) -> Length:
        return Length(abs(self._m), self._unit, self._args)

    # --- comparison ----------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Length) and abs(self._m - other._m) < 1e-9

    def __lt__(self, other: Length) -> bool:
        return self._m < other._m

    def __le__(self, other: Length) -> bool:
        return self._m <= other._m

    def __gt__(self, other: Length) -> bool:
        return self._m > other._m

    def __ge__(self, other: Length) -> bool:
        return self._m >= other._m

    def __hash__(self) -> int:
        return hash(round(self._m, 9))

    # --- display / source ----------------------------------------------------
    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        if system is UnitSystem.METRIC:
            return f"{self.mm:.0f} mm"
        total_in = round(self.inches * 16) / 16  # nearest 1/16"
        feet = int(total_in // 12)
        rem = total_in - feet * 12
        whole = int(rem)
        frac = Fraction(rem - whole).limit_denominator(16)
        parts = f'{whole}'
        if frac != 0:
            parts += f" {frac.numerator}/{frac.denominator}"
        return f'{feet}\'-{parts}"'

    def to_source(self) -> str:
        if self._unit is AuthoredUnit.FT_IN:
            feet, inches = self._args
            return f"ft({feet:g}, {inches:g})" if inches else f"ft({feet:g})"
        if self._unit is AuthoredUnit.INCH:
            return f"inch({self._args[0]:g})"
        if self._unit is AuthoredUnit.MM:
            return f"mm({self._args[0]:g})"
        return f"m({self._args[0]:g})"

    def __repr__(self) -> str:
        return f"Length({self.to_source()})"

    # --- parsing -------------------------------------------------------------
    _PARSE = re.compile(
        r"""^\s*(?:(?P<ft>-?\d+(?:\.\d+)?)\s*')?\s*
             -?\s*(?:(?P<in>\d+(?:\.\d+)?)?\s*(?:(?P<num>\d+)\s*/\s*(?P<den>\d+))?\s*")?\s*$""",
        re.VERBOSE,
    )

    @classmethod
    def parse(cls, text: str) -> Length:
        """Parse UI/field input like ``12'-6 1/2\"`` or ``48\"`` or ``3ft``."""
        t = text.strip()
        m = cls._PARSE.match(t.replace("-", " ") if "'" in t else t)
        if m and (m.group("ft") or m.group("in") or m.group("num")):
            feet = float(m.group("ft") or 0)
            inches = float(m.group("in") or 0)
            if m.group("num"):
                inches += float(m.group("num")) / float(m.group("den"))
            return ft(feet, inches)
        raise ValueError(f"cannot parse length: {text!r}")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: m(x), from_source_str=_from_source
        )


def ft(feet: float, inches: float = 0.0) -> Length:
    return Length(feet * M_PER_FT + inches * M_PER_IN, AuthoredUnit.FT_IN, (feet, inches))


def inch(x: float) -> Length:
    return Length(x * M_PER_IN, AuthoredUnit.INCH, (x,))


def mm(x: float) -> Length:
    return Length(x / 1000.0, AuthoredUnit.MM, (x,))


def m(x: float) -> Length:
    return Length(x, AuthoredUnit.M, (x,))


def _from_source(text: str) -> Length:
    """Evaluate a ``to_source()`` string safely (only the four constructors)."""
    env: dict[str, Any] = {"ft": ft, "inch": inch, "mm": mm, "m": m}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307 - closed constructor env
