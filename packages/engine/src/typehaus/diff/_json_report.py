"""Shared ``write()`` for the diff/compare/equivalence report dataclasses.

Every report type in :mod:`typehaus.diff` already renders itself with a ``to_json`` method;
persisting that to disk is the same three lines everywhere, so it lives here once.
"""

from __future__ import annotations

from pathlib import Path


class JsonReport:
    """Mixin: a report that can render itself as JSON (``to_json``) can also write itself."""

    def to_json(self) -> str:
        raise NotImplementedError

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        return path
