"""Thermal quantities: RValue (canonical RSI), UFactor, Temperature (canonical °C)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from typehaus.quantities._base import UnitSystem, pydantic_quantity_schema

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

# RSI (m²·K/W) per US R-value (ft²·°F·h/BTU).
_RSI_PER_R = 0.1761101838


@final
class RValue:
    """Thermal resistance, canonical RSI. Authored via ``r_us`` for the US market."""

    __slots__ = ("_rsi",)

    def __init__(self, rsi: float) -> None:
        object.__setattr__(self, "_rsi", float(rsi))

    @property
    def rsi(self) -> float:
        return self._rsi

    @property
    def r_us(self) -> float:
        return self._rsi / _RSI_PER_R

    def __add__(self, other: RValue) -> RValue:
        return RValue(self._rsi + other._rsi)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RValue) and abs(self._rsi - other._rsi) < 1e-9

    def __lt__(self, other: RValue) -> bool:
        return self._rsi < other._rsi

    def __hash__(self) -> int:
        return hash(round(self._rsi, 9))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        if system is UnitSystem.METRIC:
            return f"RSI-{self._rsi:.2f}"
        return f"R-{self.r_us:.1f}"

    def to_source(self) -> str:
        return f"r_us({self.r_us:g})"

    def __repr__(self) -> str:
        return f"RValue({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: RValue(x), from_source_str=_r_from_source
        )


def r_us(value: float) -> RValue:
    return RValue(value * _RSI_PER_R)


def rsi(value: float) -> RValue:
    return RValue(value)


def _r_from_source(text: str) -> RValue:
    env: dict[str, Any] = {"r_us": r_us, "rsi": rsi}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307


@final
class UFactor:
    """Thermal transmittance, canonical W/m²·K. Authored via ``u_us`` (BTU/hr·ft²·°F)."""

    __slots__ = ("_si",)

    def __init__(self, si: float) -> None:
        object.__setattr__(self, "_si", float(si))

    @property
    def si(self) -> float:
        return self._si

    @property
    def u_us(self) -> float:
        return self._si * _RSI_PER_R

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UFactor) and abs(self._si - other._si) < 1e-12

    def __hash__(self) -> int:
        return hash(round(self._si, 12))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        return f"U-{self.u_us:.3f}"

    def to_source(self) -> str:
        return f"u_us({self.u_us:g})"

    def __repr__(self) -> str:
        return f"UFactor({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: UFactor(x), from_source_str=_u_from_source
        )


def u_us(value: float) -> UFactor:
    return UFactor(value / _RSI_PER_R)


def _u_from_source(text: str) -> UFactor:
    env: dict[str, Any] = {"u_us": u_us}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307


@final
class Temperature:
    """A temperature, canonical Celsius, authored °F for the imperial market (#41)."""

    __slots__ = ("_c", "_authored_f")

    def __init__(self, celsius: float, authored_f: bool = False) -> None:
        object.__setattr__(self, "_c", float(celsius))
        object.__setattr__(self, "_authored_f", authored_f)

    @property
    def celsius(self) -> float:
        return self._c

    @property
    def fahrenheit(self) -> float:
        return self._c * 9.0 / 5.0 + 32.0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Temperature) and abs(self._c - other._c) < 1e-9

    def __hash__(self) -> int:
        return hash(round(self._c, 9))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        if system is UnitSystem.METRIC:
            return f"{self._c:.1f}°C"
        return f"{self.fahrenheit:.0f}°F"

    def to_source(self) -> str:
        if self._authored_f:
            return f"degF({self.fahrenheit:g})"
        return f"degC({self._c:g})"

    def __repr__(self) -> str:
        return f"Temperature({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: degC(x), from_source_str=_temp_from_source
        )


def degF(value: float) -> Temperature:
    return Temperature((value - 32.0) * 5.0 / 9.0, authored_f=True)


def degC(value: float) -> Temperature:
    return Temperature(value, authored_f=False)


def _temp_from_source(text: str) -> Temperature:
    env: dict[str, Any] = {"degF": degF, "degC": degC}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307
