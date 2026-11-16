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


def run_body_owners(model: Any) -> dict[str, str]:
    """Solid uid -> the owning pipe/duct/conduit run's tag, for every hard run-body solid.

    A run's swept stretches and elbow solids carry ``uid = f"{run.uid}-<suffix>"`` (the run's
    whole uid, which may itself hold a hyphen) or ``host_ref == run.tag``. Its parts, supports
    and wraps are not hard, so they stay out.
    """
    from typehaus.resolve.solid_categories import SOLID_CATEGORIES

    runs = [*model.pipe_runs, *model.ducts, *model.conduits]
    by_uid = {run.uid: run.tag for run in runs if run.uid}
    tags = {run.tag for run in runs}
    out: dict[str, str] = {}
    for solid in model.solids:
        row = SOLID_CATEGORIES.get(solid.category)
        if row is None or row.collision != "hard":
            continue
        tag = solid.host_ref if solid.host_ref in tags else None
        # Longest uid prefix wins: a derived run's uid extends its authored parent's.
        end = len(solid.uid)
        while tag is None and (end := solid.uid.rfind("-", 0, end)) > 0:
            tag = by_uid.get(solid.uid[:end])
        if tag is not None:
            out[solid.uid] = tag
    return out
