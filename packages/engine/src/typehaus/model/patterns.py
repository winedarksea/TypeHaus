"""Shared fnmatch glob helper (coverage check, scaffolder, annotation binding).

Extracted from ``checks/integrity/checks.py`` so condition-key matching, LayerJoin
layer globs, and detail-annotation binding all agree on one wildcard semantics.
"""

from __future__ import annotations

import fnmatch


def matches(pattern: str, key: str) -> bool:
    """True when ``key`` matches the fnmatch wildcard ``pattern``."""
    return fnmatch.fnmatch(key, pattern)


def first_match(transitions, key: str):
    """The Transition that binds ``key``: the FIRST whose pattern matches, in authored order.

    Every reader of a binding (the derived detail, coverage, continuity, star curation) goes
    through this, so a later, narrower pattern behind a wildcard binds nothing anywhere.
    """
    return next((tr for tr in transitions if matches(tr.condition_pattern, key)), None)
