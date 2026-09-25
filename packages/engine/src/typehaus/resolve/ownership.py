"""Which derived solids belong to which authored element.

A derived child solid carries ``uid = f"{parent.uid}-{suffix}"``. An authored uid is
Crockford base32 with no hyphen, so the text before the first hyphen names the parent
exactly — unlike a tag prefix, where ``RL-FOO-`` also matches ``RL-FOO-NE-BAL3``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def parent_uid(uid: str) -> str | None:
    """The authored parent's uid of a derived child uid, or None for an authored one."""
    head, sep, _ = uid.partition("-")
    return head if sep and head else None


def children_of(model: Any, element: Any,
                categories: Iterable[str] | None = None) -> list:
    """The solids derived from ``element``, optionally only those in ``categories``."""
    uid = getattr(element, "uid", "") or ""
    if not uid:
        return []
    cats = None if categories is None else frozenset(categories)
    return [s for s in model.solids
            if parent_uid(s.uid) == uid and (cats is None or s.category in cats)]
