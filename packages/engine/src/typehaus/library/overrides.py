"""House-side overrides of library catalog items.

A library item cannot name a house-owned ``Product`` (every other house would resolve the tag
to nothing), and a house appending a duplicate tag is shadowed for geometry yet wins in
``product_labels``. The seam is a same-tag copy: wrap the library items in the house manifest.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, TypeVar

T = TypeVar("T", bound=Any)


def with_product_refs(items: Iterable[T], refs: Mapping[str, str]) -> tuple[T, ...]:
    """``items`` with each tag in ``refs`` copied under its ``product_ref``; order is kept.

    Works on any catalog row carrying ``tag`` and ``product_ref`` (materials, types). A tag
    that matches no item raises ``ValueError``: a silent miss is the override not applying.
    """
    rows = tuple(items)
    unmatched = set(refs) - {row.tag for row in rows}
    if unmatched:
        raise ValueError(f"with_product_refs: no item with tag {sorted(unmatched)}")
    return tuple(row.model_copy(update={"product_ref": refs[row.tag]}) if row.tag in refs
                 else row for row in rows)
