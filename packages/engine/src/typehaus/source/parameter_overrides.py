"""Scoped house-parameter overrides applied while a plan module is imported.

House parameters are ordinary Python evaluated during import.  Variant overrides therefore
have to be visible before ``plan.manifest`` is executed; changing the finished ``PlanModel``
is too late for dimensions that determined which elements were constructed.  A context
variable keeps the values local to one serialized load and makes nested/test loads restore
their caller's state reliably.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from types import MappingProxyType
from typing import TypeVar

ParameterValue = bool | int | float | str
_T = TypeVar("_T", bool, int, float, str)

_ACTIVE: ContextVar[Mapping[str, ParameterValue]] = ContextVar(
    "typehaus_house_parameter_overrides", default=MappingProxyType({})
)
_CONSUMED: ContextVar[set[str] | None] = ContextVar(
    "typehaus_consumed_house_parameter_overrides", default=None
)


@contextmanager
def activated(values: Mapping[str, ParameterValue] | None) -> Iterator[set[str]]:
    """Expose ``values`` for exactly one house import and restore prior state afterward."""

    token = _ACTIVE.set(dict(values or {}))
    consumed: set[str] = set()
    consumed_token = _CONSUMED.set(consumed)
    try:
        yield consumed
    finally:
        _CONSUMED.reset(consumed_token)
        _ACTIVE.reset(token)


def parameter(name: str, default: _T) -> _T:
    """Return an override after enforcing the default's scalar type.

    ``bool`` is checked before ``int`` because it subclasses ``int`` in Python.  Numeric
    defaults accept either TOML integer or float and return the default's numeric type.
    """

    active = _ACTIVE.get()
    value = active.get(name, default)
    if name in active:
        consumed = _CONSUMED.get()
        if consumed is not None:
            consumed.add(name)
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise ValueError(f"parameter override {name!r} must be boolean")
        return value  # type: ignore[return-value]
    if isinstance(default, int):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"parameter override {name!r} must be an integer")
        return value  # type: ignore[return-value]
    if isinstance(default, float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"parameter override {name!r} must be numeric")
        return float(value)  # type: ignore[return-value]
    if not isinstance(value, str):
        raise ValueError(f"parameter override {name!r} must be a string")
    return value  # type: ignore[return-value]
