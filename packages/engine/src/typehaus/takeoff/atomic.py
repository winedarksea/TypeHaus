"""One safe way to replace a site-state file, and one way to name its version.

``tasks.toml``, ``inspections.toml`` and ``costs.toml`` are small, hand-editable and
outside the undo journal, so a half-written one is not recoverable from anywhere. Every
writer here serialises to a temp file **in the same directory** — ``os.replace`` is atomic
only within a filesystem — flushes it to disk, and replaces the target in one step. A crash
between the two leaves the previous file intact and complete.

``revision`` is the content hash a ``GET`` echoes and a ``PUT`` may send back as
``if_revision``. It is deliberately a hash of the bytes rather than an mtime or a counter: a
hand edit in an editor is a legitimate way to change these files, and it moves no counter.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> Path:
    """Write ``text`` to ``path`` so that ``path`` is never partially written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.",
                                         suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return path


def revision(*paths: Path) -> str:
    """A short content hash over the given files, absent ones included as absent.

    Stable across processes and machines: it is the bytes and the file names, nothing else.
    """
    digest = hashlib.sha256()
    for path in paths:
        target = Path(path)
        digest.update(target.name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(target.read_bytes() if target.exists() else b"")
        digest.update(b"\xff")
    return digest.hexdigest()[:16]
