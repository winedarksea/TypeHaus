"""House modules import past a stale ``.pyc`` (the undo that did not undo).

CPython validates cached bytecode by the source's whole-second mtime and its size. An editor
writeback and its undo can land in the same second with the same byte count (``m(3.648)`` →
``m(4.048)``), and the re-import then runs the old bytecode: the server reports the undo and
serves the pre-undo model. So a house source modified within ``_YOUNG_S`` is compiled from
source and its bytecode never written; only a settled file gets a ``.pyc``, whose mtime
second can no longer be shared by a later write.
"""

from __future__ import annotations

import importlib.machinery
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from types import CodeType

_YOUNG_S = 2.5
_HOUSE_ROOTS = ("plan", "params")


class FreshSourceLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname: str) -> CodeType | None:
        if time.time() - os.stat(self.path).st_mtime < _YOUNG_S:
            return self.source_to_code(self.get_data(self.path), self.path)
        return super().get_code(fullname)


class _HouseFinder:
    @staticmethod
    def find_spec(name, path=None, target=None):
        if name.split(".", 1)[0] not in _HOUSE_ROOTS:
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None and isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            spec.loader = FreshSourceLoader(spec.name, spec.origin)
        return spec


@contextmanager
def fresh_house_imports() -> Iterator[None]:
    """Route ``plan.*``/``params.*`` imports through :class:`FreshSourceLoader` meanwhile."""
    sys.meta_path.insert(0, _HouseFinder)
    try:
        yield
    finally:
        sys.meta_path.remove(_HouseFinder)
