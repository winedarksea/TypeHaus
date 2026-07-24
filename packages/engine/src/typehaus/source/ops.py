"""PATCH /plan op model + field-value → CST-source encoding (→ 20 §libcst writeback).

An op is element-level and flat: ``{op, type, tag, fields}``. ``fields`` carry
*authored-unit* strings (``"12'-6\\""``) and plain scalars from the UI/JSON seam; this
module turns them into the exact source text the dialect printer emits — always a
keyword-arg constructor call, never anything the linter would reject (→ 20 §libcst).
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from typehaus.model.registry import element_kinds
from typehaus.quantities import Angle, Length, Pitch, RValue, Temperature, UFactor


class WritebackError(RuntimeError):
    """An op could not be applied to the given source (missing target, no host list…).

    Defined here (the pure-Python op model) rather than in ``writeback`` so both the libcst
    and the ast (libcst-free) writeback backends can share one exception type without a
    circular import.
    """


@dataclass
class WritebackResult:
    source: str
    minted_uids: dict[str, str]  # tag -> newly minted uid (add ops only)


@dataclass(frozen=True)
class RawExpr:
    """A pre-encoded dialect expression (e.g. a prior field value read from source).

    Passing one as a field value bypasses re-encoding — used to build inverse ops for the
    undo journal so a round-trip restores the exact authored text.
    """

    expr: str


# Sentinel field value meaning "remove this keyword argument" (undo of an added field).
DELETE_FIELD = "__haus_delete_field__"


@dataclass(frozen=True)
class PatchOp:
    """One element-level mutation. ``type`` is an element kind name (e.g. ``"Wall"``)."""

    op: str  # "add" | "update" | "delete"
    type: str
    tag: str
    fields: dict[str, Any] = field(default_factory=dict)
    # Origin file (relative posix path) pinning an ``add`` to a specific storey file — set
    # on the inverse of a delete so undo returns the element to where it came from, and
    # settable by the UI to place a new element in the current storey's file.
    hint_file: str | None = None
    # The module-level list variable an ``add`` appends to (e.g. ``"OPENINGS"``). Openings
    # of different kinds share one list, so kind alone can't pick it; the delete inverse
    # records the origin list so undo re-adds to exactly the right one.
    hint_list: str | None = None

    @staticmethod
    def from_json(raw: dict[str, Any]) -> PatchOp:
        op = raw.get("op", "")
        if op not in ("add", "update", "delete"):
            raise ValueError(f"unknown op {op!r} (add|update|delete)")
        if "type" not in raw or "tag" not in raw:
            raise ValueError("op requires 'type' and 'tag'")
        return PatchOp(op=op, type=str(raw["type"]), tag=str(raw["tag"]),
                       fields=dict(raw.get("fields") or {}))

    def to_json(self) -> dict[str, Any]:
        return {"op": self.op, "type": self.type, "tag": self.tag, "fields": self.fields}


# --- field-type introspection ------------------------------------------------

def _field_annotation(kind: str, name: str) -> Any:
    cls = element_kinds().get(kind)
    if cls is None:
        return None
    fld = getattr(cls, "model_fields", {}).get(name)
    return fld.annotation if fld is not None else None


# types.UnionType only exists on Python 3.10+ (the `X | Y` runtime form).
_UNION_TYPE = getattr(types, "UnionType", None)


def _union_members(annotation: Any) -> tuple[Any, ...]:
    origin = typing.get_origin(annotation)
    if origin is typing.Union or (_UNION_TYPE is not None and origin is _UNION_TYPE):
        return typing.get_args(annotation)
    return (annotation,)


def _has_quantity(annotation: Any, quantity: type) -> bool:
    return any(m is quantity for m in _union_members(annotation))


# --- value encoding ----------------------------------------------------------

_QUANTITY_PARSERS: tuple[tuple[type, Any], ...] = (
    (Length, Length),
    (Angle, Angle),
    (RValue, RValue),
    (UFactor, UFactor),
    (Temperature, Temperature),
)


def encode_value(kind: str, name: str, value: Any) -> str:
    """Encode a single field value to dialect source text for field ``name`` of ``kind``.

    Uses the model field's annotation so a ``"12'-6\\""`` bound to a ``Length`` field
    serializes to ``ft(12, 6)`` while the same string on a ``str`` field stays quoted.
    """
    if isinstance(value, RawExpr):
        return value.expr
    annotation = _field_annotation(kind, name)

    if isinstance(value, bool):  # bool before int (bool is an int subclass)
        return "True" if value else "False"
    if isinstance(value, (int, float)) and not _is_quantity_field(annotation):
        return f"{value}"

    if isinstance(value, str):
        if _has_quantity(annotation, Pitch):
            try:
                rise, run = (float(part.strip()) for part in value.replace(":", "/").split("/"))
                return Pitch(rise, run).to_source()
            except (TypeError, ValueError):
                raise ValueError(f"invalid pitch {value!r}; use rise/run, e.g. 4/12") from None
        # Quantity-typed field: parse the authored-unit string into a constructor call.
        for quantity, parser in _QUANTITY_PARSERS:
            if _has_quantity(annotation, quantity) and hasattr(parser, "parse"):
                try:
                    return parser.parse(value).to_source()  # type: ignore[attr-defined]
                except (ValueError, AttributeError):
                    pass
        # Enum-typed field: bare member name → "EnumName.MEMBER".
        enum_src = _encode_enum(annotation, value)
        if enum_src is not None:
            return enum_src
        return _quote(value)

    if isinstance(value, (list, tuple)):
        inner = ", ".join(encode_value(kind, name, v) for v in value)
        return f"({inner},)" if len(value) == 1 else f"({inner})"

    if value is None:
        return "None"
    raise ValueError(f"cannot encode {name}={value!r} for {kind}")


def _is_quantity_field(annotation: Any) -> bool:
    return any(_has_quantity(annotation, q) for q, _ in _QUANTITY_PARSERS)


def _encode_enum(annotation: Any, value: str) -> str | None:
    if "." in value:  # already qualified, e.g. "Occupancy.LIVING"
        return value
    for member in _union_members(annotation):
        if isinstance(member, type) and issubclass(member, Enum):
            if value in member.__members__:
                return f"{member.__name__}.{value}"
    return None


def _quote(value: str) -> str:
    if '"' in value and "'" not in value:
        return f"'{value}'"
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
