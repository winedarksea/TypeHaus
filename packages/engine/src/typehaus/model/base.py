"""Frozen Pydantic base for all model objects (→ 10 §Element model)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict

# Construction observer: when set, called with every Element as it is built. The model
# layer knows nothing about who listens — the source loader injects a callable while it
# imports a house manifest (runtime authorship capture) and clears it after. Inert
# (a single `is not None` check per construction) when unset.
_construction_observer: Callable[[Element], None] | None = None


def set_construction_observer(observer: Callable[[Element], None] | None) -> None:
    global _construction_observer
    _construction_observer = observer


class HausModel(BaseModel):
    """Common config: frozen, arbitrary types (our quantity value types), strict-ish."""

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )


class Element(HausModel):
    """Base for every authored element carrying identity (#16).

    ``uid`` is the immutable round-trip anchor; ``tag`` is the mutable human name.
    A hand-authored element may omit ``uid`` (empty string) — the dialect linter flags
    it and ``haus fmt`` inserts a fresh one; ``haus build`` never mutates source.
    """

    uid: str = ""
    tag: str

    def model_post_init(self, __context: Any) -> None:
        if _construction_observer is not None:
            _construction_observer(self)

    @property
    def element_kind(self) -> str:
        return type(self).__name__
