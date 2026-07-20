"""Shared fnmatch glob helper (coverage check, scaffolder, annotation binding).

Extracted from ``checks/integrity/checks.py`` so condition-key matching, LayerJoin
layer globs, and detail-annotation binding all agree on one wildcard semantics.
"""

from __future__ import annotations

import fnmatch


def matches(pattern: str, key: str) -> bool:
    """True when ``key`` matches the fnmatch wildcard ``pattern``."""
    return fnmatch.fnmatch(key, pattern)
