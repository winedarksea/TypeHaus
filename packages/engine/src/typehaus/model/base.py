"""Frozen Pydantic base for all model objects (→ 10 §Element model)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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

    @property
    def element_kind(self) -> str:
        return type(self).__name__
