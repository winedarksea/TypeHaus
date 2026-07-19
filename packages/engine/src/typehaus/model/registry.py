"""Open element registry + capability protocols (→ 10 §Schema headroom req. 1 & 3).

Adding an element kind is one model class registered here plus registered emitter/check
functions; a unit test asserts every registered kind has an emitter — completeness is
enforced by test, not by ``match`` statements scattered across the code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from typehaus.quantities import Length, Point2D

# --- element-kind registry ---------------------------------------------------
_ELEMENT_KINDS: dict[str, type] = {}


def register_element(cls: type) -> type:
    """Class decorator: record an authored element kind under its class name."""
    _ELEMENT_KINDS[cls.__name__] = cls
    return cls


def element_kinds() -> dict[str, type]:
    return dict(_ELEMENT_KINDS)


def is_registered_element(name: str) -> bool:
    return name in _ELEMENT_KINDS


# --- authoring-constructor registry (the dialect allowlist, → source/dialect) ----
_CONSTRUCTORS: dict[str, object] = {}


def register_constructor(name: str, obj: object) -> None:
    _CONSTRUCTORS[name] = obj


def constructor_names() -> frozenset[str]:
    """Names the plan dialect may call. Populated as the model package imports."""
    return frozenset(_CONSTRUCTORS)


def constructor_namespace() -> dict[str, object]:
    """The dialect call namespace (Wall, Node, ft, pt, enums, …) for evaluating a single
    authored constructor expression in-memory — the same names a plan module imports.

    Used by the in-memory op applicator to build a pydantic element from the exact source
    text the libcst writeback would emit, so there is one value-encoding path, not two."""
    return dict(_CONSTRUCTORS)


# --- capability protocols (drawing IR / checks consume these, not concretes) -----
@runtime_checkable
class HasAxis(Protocol):
    """An element defined by a node-to-node axis (walls, beams)."""

    start_node: str
    end_node: str


@runtime_checkable
class HasFootprint(Protocol):
    """An element with a plan polygon (rooms, slabs, soffits, pads)."""

    def footprint_m(self) -> list[tuple[float, float]]: ...


@runtime_checkable
class HasProfile(Protocol):
    """An element with a layered cross-section profile (assemblies)."""

    def profile_thickness_m(self) -> float: ...


@runtime_checkable
class Positioned(Protocol):
    position: Point2D


@runtime_checkable
class Tagged(Protocol):
    uid: str
    tag: str


def height_of(_length: Length) -> float:  # pragma: no cover - placeholder helper
    return _length.meters
