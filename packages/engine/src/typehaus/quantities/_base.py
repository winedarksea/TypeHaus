"""Shared machinery for the hand-rolled quantity types.

We deliberately do *not* use pint (it defeats ``mypy --strict`` and drags a global
registry). Instead each quantity is a small frozen value type storing a canonical SI
float plus the *authored* representation, so a value authored as ``ft(12, 6)`` survives
a round-trip through source as ``ft(12, 6)`` — never ``m(3.9624)`` (→ 10 §Quantities).
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


class UnitSystem(Enum):
    """Display unit system. Authoring may mix systems; display picks one."""

    IMPERIAL = "imperial"
    METRIC = "metric"


def pydantic_quantity_schema(
    cls: type,
    *,
    to_canonical: Any,
    from_source_str: Any,
) -> CoreSchema:
    """Build a pydantic-core schema for a quantity type.

    Validation accepts (a) an existing instance, (b) a ``to_source()``-style string
    which is parsed back, or (c) a raw float treated as the canonical SI value.
    Serialization emits the ``to_source()`` string so JSON round-trips preserve the
    authored unit.
    """
    from pydantic_core import core_schema

    def _validate(value: Any) -> Any:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return from_source_str(value)
        if isinstance(value, (int, float)):
            return to_canonical(float(value))
        raise TypeError(f"cannot coerce {value!r} into {cls.__name__}")

    return core_schema.no_info_plain_validator_function(
        _validate,
        serialization=core_schema.plain_serializer_function_ser_schema(
            lambda v: v.to_source(), when_used="json"
        ),
    )


class QuantityMeta:
    """Mixin providing pydantic-v2 integration hook expectations.

    Concrete quantity classes implement ``to_source`` and ``fmt`` and register a core
    schema via ``__get_pydantic_core_schema__``; this base just documents the contract.
    """

    def to_source(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def fmt(self, system: UnitSystem = UnitSystem.IMPERIAL) -> str:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:  # pragma: no cover - interface
        raise NotImplementedError
