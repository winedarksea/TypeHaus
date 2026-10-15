"""Frozen Pydantic base for all model objects (→ 10 §Element model)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict

# Construction observer: when set, called with every Element as it is built. The model
# layer knows nothing about who listens — the source loader injects a callable while it
# imports a house manifest (runtime authorship capture) and clears it after. Inert
# (a single `is not None` check per construction) when unset. Per THREAD: a server's
# rebuild worker loading a house must not replace or clear another thread's capture.
_observer_state = threading.local()


def set_construction_observer(observer: Callable[[Element], None] | None) -> None:
    _observer_state.observer = observer


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
        observer = getattr(_observer_state, "observer", None)
        if observer is not None:
            observer(self)

    @property
    def element_kind(self) -> str:
        return type(self).__name__
