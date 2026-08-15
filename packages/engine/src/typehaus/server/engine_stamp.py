"""Is the running server still the code that is on disk?

`haus serve` calls ``uvicorn.run(create_app(...))`` with no ``reload=``, and the internal
watcher (``server.app._watch``) watches ``houses/<name>/`` only. Editing anything under
``packages/engine/`` therefore changes nothing the running process can see: the viewer keeps
rendering geometry from the modules imported at startup, the plan reloads cleanly, and
**no error appears anywhere**. The only symptom is that a fix does not take, which reads as
a bug in the fix.

This module makes that state observable. The engine's newest source mtime is sampled once
at import (that *is* the code the process is running) and re-sampled on request; when the
tree has moved on, ``engine_stamp()["stale"]`` is True and the UI says so.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import typehaus

_PACKAGE_ROOT = Path(typehaus.__file__).resolve().parent

# Re-walking ~500 source files on every GET /model would put a stat storm on the hot path
# for a fact that changes at human speed. One sample per interval is plenty.
_RESAMPLE_SECONDS = 2.0


def _tree_mtime() -> float:
    newest = 0.0
    for path in _PACKAGE_ROOT.rglob("*.py"):
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:  # a file deleted mid-walk is not a staleness signal
            continue
    return newest


_IMPORTED_MTIME = _tree_mtime()
_cache: tuple[float, float] = (0.0, _IMPORTED_MTIME)


def engine_stamp() -> dict[str, Any]:
    """``{imported_mtime, source_mtime, stale}`` for the engine package tree."""
    global _cache
    now = time.monotonic()
    sampled_at, source_mtime = _cache
    if now - sampled_at > _RESAMPLE_SECONDS:
        source_mtime = _tree_mtime()
        _cache = (now, source_mtime)
    return {
        "imported_mtime": _IMPORTED_MTIME,
        "source_mtime": source_mtime,
        # Strictly newer: equal mtimes are the normal steady state.
        "stale": source_mtime > _IMPORTED_MTIME,
    }
