"""Which sheets belong to which SET, and the house's own overrides.

`haus print` emits two documents from one composer. ``full`` is everything this engine
can draw; ``permit`` is what a plan checker is asked to review, which is a deliberately
smaller thing — the Saint Paul DSI new-construction checklist wants fixtures on the floor
plans and lists no separate E or P drawings at all. Named sets rather than a boolean
because a third one (a bid set, an as-built) is a sheet-list question, not another flag on
every spec.

Its own module because ``sheets.py`` is at the 500-line limit and this is the one part of
it that has no opinion about what a sheet CONTAINS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.checks.registry import Preferences

PERMIT_SET = "permit"
FULL_SET = "full"
BOTH_SETS = frozenset({PERMIT_SET, FULL_SET})
FULL_ONLY = frozenset({FULL_SET})

#: ``--details`` was the older name for the same filter and only ever had two values.
_DETAILS_ALIAS = {"primary": PERMIT_SET, "all": FULL_SET}


class _Numbered(Protocol):
    number: str
    sets: frozenset[str]


def resolve_set_name(sets: str, details: str | None) -> str:
    """``details=`` wins when given, because a caller passing it means it."""
    if details is not None:
        return _DETAILS_ALIAS.get(details, FULL_SET)
    return sets


def in_set(sheet: _Numbered, name: str, preferences: Preferences | None) -> bool:
    """Whether ``sheet`` belongs in the named set, after the house's own overrides.

    ``permit_drop`` beats ``permit_add`` so a house cannot author a contradiction that
    silently resolves one way; and neither touches the full set, which is by definition
    everything the engine drew.
    """
    if name == FULL_SET:
        return True
    options = preferences.print_options if preferences is not None else None
    drop = options.permit_drop if options is not None else ()
    add = options.permit_add if options is not None else ()
    if any(sheet.number.startswith(prefix) for prefix in drop):
        return False
    if any(sheet.number.startswith(prefix) for prefix in add):
        return True
    return name in sheet.sets
