"""Area — canonical square meters, authored in the display system's units."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from typehaus.quantities._base import UnitSystem, pydantic_quantity_schema
from typehaus.quantities.length import M_PER_FT

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema

_SQFT_PER_SQM = 1.0 / (M_PER_FT * M_PER_FT)


@final
class Area:
    """An area in canonical square meters."""

    __slots__ = ("_m2",)

    def __init__(self, sq_meters: float) -> None:
        object.__setattr__(self, "_m2", float(sq_meters))

    @property
    def sq_m(self) -> float:
        return self._m2

    @property
    def sq_ft(self) -> float:
        return self._m2 * _SQFT_PER_SQM

    def __add__(self, other: Area) -> Area:
        return Area(self._m2 + other._m2)

    def __sub__(self, other: Area) -> Area:
        return Area(self._m2 - other._m2)

    def __mul__(self, k: float) -> Area:
        return Area(self._m2 * k)

    __rmul__ = __mul__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Area) and abs(self._m2 - other._m2) < 1e-9

    def __lt__(self, other: Area) -> bool:
        return self._m2 < other._m2

    def __hash__(self) -> int:
        return hash(round(self._m2, 9))

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:
        if system is UnitSystem.METRIC:
            return f"{self._m2:.2f} m²"
        return f"{self.sq_ft:.1f} sf"

    def to_source(self) -> str:
        return f"sqft({self.sq_ft:g})"

    def __repr__(self) -> str:
        return f"Area({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return pydantic_quantity_schema(
            cls, to_canonical=lambda x: Area(x), from_source_str=_area_from_source
        )


def sqft(x: float) -> Area:
    return Area(x / _SQFT_PER_SQM)


def sqm(x: float) -> Area:
    return Area(x)


def _area_from_source(text: str) -> Area:
    env: dict[str, Any] = {"sqft": sqft, "sqm": sqm}
    return eval(text, {"__builtins__": {}}, env)  # noqa: S307
