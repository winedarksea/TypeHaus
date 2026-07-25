"""Framing solver (#20 signature) — pure records until emit (→ 11).

The re-exports below resolve lazily (PEP 562). Importing them eagerly made *any* import of
a leaf module in this package — ``profiles``, ``tables`` — drag in the whole solver and roof
framer, and those import ``resolve.roof_geometry``, which imports ``profiles`` straight back.
That cycle stayed dormant only while nothing imported ``roof_geometry`` first. Keeping the
package root free of eager submodule imports removes the class of bug, not just the instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # for type checkers only — never executed at runtime
    from typehaus.resolve.framing.openings import WallOpening
    from typehaus.resolve.framing.roof import frame_roofs
    from typehaus.resolve.framing.solver import frame_model, frame_wall

_LAZY_EXPORT_MODULES = {
    "WallOpening": "typehaus.resolve.framing.openings",
    "frame_model": "typehaus.resolve.framing.solver",
    "frame_wall": "typehaus.resolve.framing.solver",
    "frame_roofs": "typehaus.resolve.framing.roof",
}

__all__ = ["WallOpening", "frame_model", "frame_wall", "frame_roofs"]


def __getattr__(name: str) -> Any:
    module_path = _LAZY_EXPORT_MODULES.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    return getattr(import_module(module_path), name)


def __dir__() -> list[str]:
    return sorted([*globals(), *__all__])
