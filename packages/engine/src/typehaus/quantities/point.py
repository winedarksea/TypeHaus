"""Point2D — a project-north (x, y) coordinate pair of Lengths (→ 02 §Project north)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from typehaus.quantities.length import Length, m

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


@final
class Point2D:
    """A 2D point in the orthogonal project-north plan frame."""

    __slots__ = ("_x", "_y")

    def __init__(self, x: Length, y: Length) -> None:
        object.__setattr__(self, "_x", x)
        object.__setattr__(self, "_y", y)

    @property
    def x(self) -> Length:
        return self._x

    @property
    def y(self) -> Length:
        return self._y

    @property
    def xy_m(self) -> tuple[float, float]:
        return (self._x.meters, self._y.meters)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point2D) and self._x == other._x and self._y == other._y

    def __hash__(self) -> int:
        return hash((self._x, self._y))

    def to_source(self) -> str:
        return f"pt({self._x.to_source()}, {self._y.to_source()})"

    def __repr__(self) -> str:
        return f"Point2D({self.to_source()})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from pydantic_core import core_schema

        def _validate(value: Any) -> Point2D:
            if isinstance(value, Point2D):
                return value
            if isinstance(value, (list, tuple)) and len(value) == 2:
                x, y = value
                return Point2D(x if isinstance(x, Length) else m(float(x)),
                               y if isinstance(y, Length) else m(float(y)))
            raise ValueError(f"cannot coerce {value!r} into Point2D")

        return core_schema.no_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: [v.x.to_source(), v.y.to_source()], when_used="json"
            ),
        )


def pt(x: Length, y: Length) -> Point2D:
    return Point2D(x, y)
