"""Angle (canonical radians, authored degrees) and Pitch (rise/run, first-class)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, final

from typehaus.quantities._base import UnitSystem, pydantic_quantity_schema

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


@final
class Angle:
    """An angle in canonical radians, authored in degrees for the imperial market."""

    __slots__ = ("_rad",)

    def __init__(self, radians: float) -> None:
        object.__setattr__(self, "_rad", float(radians))

    @property
    def radians(self) -> float:
        return self._rad

    @property
    def degrees(self) -> float:
        return math.degrees(self._rad)

    def __add__(self, other: Angle) -> Angle:
        return Angle(self._rad + other._rad)

    def __sub__(self, other: Angle) -> Angle:
        return Angle(self._rad - other._rad)

    def __neg__(self) -> Angle:
        return Angle(-self._rad)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Angle) and abs(self._rad - other._rad) < 1e-12

    def __hash__(self) -> int:
        return hash(round(self._rad, 12))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        return f"{self.degrees:g}°"

    def to_source(self) -> str:
        return f"deg({self.degrees:g})"

    def __repr__(self) -> str:
        return f"Angle({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: Angle(x), from_source_str=_angle_from_source
        )


def deg(degrees: float) -> Angle:
    return Angle(math.radians(degrees))


def rad(radians: float) -> Angle:
    return Angle(radians)


def _angle_from_source(text: str) -> Angle:
    env: dict[str, Any] = {"deg": deg, "rad": rad}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307


@final
class Pitch:
    """Roof pitch as rise-over-run (e.g. ``Pitch(rise=4, run=12)``)."""

    __slots__ = ("_rise", "_run")

    def __init__(self, rise: float, run: float = 12.0) -> None:
        if run == 0:
            raise ValueError("Pitch run cannot be zero")
        object.__setattr__(self, "_rise", float(rise))
        object.__setattr__(self, "_run", float(run))

    @property
    def rise(self) -> float:
        return self._rise

    @property
    def run(self) -> float:
        return self._run

    @property
    def slope(self) -> float:
        return self._rise / self._run

    def to_angle(self) -> Angle:
        return Angle(math.atan2(self._rise, self._run))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Pitch) and abs(self.slope - other.slope) < 1e-12

    def __hash__(self) -> int:
        return hash(round(self.slope, 12))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        return f"{self._rise:g}:{self._run:g}"

    def to_source(self) -> str:
        return f"Pitch(rise={self._rise:g}, run={self._run:g})"

    def __repr__(self) -> str:
        return f"Pitch({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls,
            to_canonical=lambda x: Pitch(rise=x, run=12.0),
            from_source_str=_pitch_from_source,
        )


def _pitch_from_source(text: str) -> Pitch:
    env: dict[str, Any] = {"Pitch": Pitch}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307
