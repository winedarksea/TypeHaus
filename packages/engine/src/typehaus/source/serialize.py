"""Model → dialect-source serialization (→ 20 §libcst writeback, → 21b WP2.4d).

The assembly editor's *clone-and-tweak* flow (WP2.4d) copies a ``library/`` preset into
``plan/assemblies.py`` as an inline ``Assembly(...)`` declaration. That needs the inverse of
parsing: turn a live model object — with nested ``Layer``/``FramingSpec`` records, quantities,
and enums — back into the exact keyword-arg constructor call the dialect prints (→ 10
§Plan-source dialect: no operators, no control flow, only ``Cls(k=v, ...)`` calls). The output
is emitted as a :class:`~typehaus.source.ops.RawExpr` so the writeback drops it in verbatim.

Only authored fields that differ from their model default are emitted, so a duplicated preset
reads as tightly as a hand-authored one (``haus fmt`` is the canonical normalizer either way).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel

from typehaus.model.base import Element
from typehaus.source.ops import PatchOp, RawExpr, _quote


def value_source(value: Any) -> str:
    """Serialize one field value to dialect source text (recurses into nested models)."""
    if value is None:
        return "None"
    if isinstance(value, bool):  # before int
        return "True" if value else "False"
    if isinstance(value, Enum):
        return f"{type(value).__name__}.{value.name}"
    if hasattr(value, "to_source"):  # quantity value types + Point2D
        return value.to_source()  # type: ignore[no-any-return]
    if isinstance(value, BaseModel):
        return model_source(value)
    if isinstance(value, str):
        return _quote(value)
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (frozenset, set)):
        # Both authored as a set literal in the dialect (the printer never emits
        # ``frozenset(...)``); empty sets can't be ``{}`` (that's a dict) so use ``set()``.
        if not value:
            return "set()"
        inner = ", ".join(value_source(v) for v in sorted(value, key=_sort_key))
        return f"{{{inner}}}"
    if isinstance(value, (list, tuple)):
        inner = ", ".join(value_source(v) for v in value)
        if isinstance(value, tuple):
            return f"({inner},)" if len(value) == 1 else f"({inner})"
        return f"[{inner}]"
    raise TypeError(f"cannot serialize {value!r} ({type(value).__name__}) to dialect source")


def model_source(model: BaseModel) -> str:
    """Serialize a HausModel to its constructor call, omitting fields left at default."""
    parts: list[str] = []
    for name, field in type(model).model_fields.items():
        value = getattr(model, name)
        if _is_default(field, value):
            continue
        parts.append(f"{name}={value_source(value)}")
    return f"{type(model).__name__}({', '.join(parts)})"


def _is_default(field: Any, value: Any) -> bool:
    if field.is_required():
        return False
    try:
        return bool(value == field.get_default(call_default_factory=True))
    except Exception:  # noqa: BLE001 - some defaults aren't comparable; keep the field
        return False


def _sort_key(value: Any) -> str:
    if isinstance(value, Enum):
        return value.name
    return str(value)


def element_add_op(
    element: Element, *, tag: str, hint_list: str, hint_file: str | None = None
) -> PatchOp:
    """Build an ``add`` PatchOp that writes ``element`` as an inline declaration under ``tag``.

    All authored fields become :class:`RawExpr` values (already dialect source), so the
    writeback inserts them verbatim; ``uid`` is left for the coordinator to mint fresh.
    """
    fields: dict[str, Any] = {}
    for name, field in type(element).model_fields.items():
        if name in ("uid", "tag"):
            continue
        value = getattr(element, name)
        if _is_default(field, value):
            continue
        fields[name] = RawExpr(value_source(value))
    return PatchOp("add", type(element).__name__, tag, fields,
                   hint_file=hint_file, hint_list=hint_list)
