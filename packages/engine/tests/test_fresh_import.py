"""A same-size rewrite in the same second must not re-import stale bytecode (undo bug)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from typehaus.source.fresh_import import fresh_house_imports


def _import_value(root: Path) -> float:
    for name in [m for m in sys.modules if m == "plan" or m.startswith("plan.")]:
        del sys.modules[name]
    sys.path.insert(0, str(root))
    try:
        with fresh_house_imports():
            from plan import placeables  # type: ignore[import-not-found]

            return placeables.Y
    finally:
        sys.path.remove(str(root))
        for name in [m for m in sys.modules if m == "plan" or m.startswith("plan.")]:
            del sys.modules[name]


def test_same_second_same_size_rewrite_is_seen(tmp_path: Path) -> None:
    pkg = tmp_path / "plan"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    module = pkg / "placeables.py"
    module.write_text("Y = 3.648\n")
    stamp = int(module.stat().st_mtime)
    os.utime(module, (stamp, stamp))
    assert _import_value(tmp_path) == 3.648
    module.write_text("Y = 4.048\n")
    os.utime(module, (stamp, stamp))  # the same whole second, the same size
    assert _import_value(tmp_path) == 4.048
