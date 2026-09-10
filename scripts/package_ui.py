#!/usr/bin/env python3
"""Stage the built UI into the package so `pip install typehaus && haus serve` works.

`haus serve` delivers the compiled browser app; without this step a pip-installed engine
answers `/` with the "UI not built" 404 and the only way to get the editor is a checkout
plus node. Run it after `cd ui && npm run build` and before `python -m build packages/engine`
— the wheel's `artifacts` entry picks up whatever this leaves behind.

`catlin-house.json` (3.8 MB of the 15 MB dist) is a demo payload the reference house
regenerates, so it is excluded and the wheel grows by roughly 11 MB instead.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ui" / "dist"
TARGET = ROOT / "packages" / "engine" / "src" / "typehaus" / "server" / "static"

# Demo payloads that belong to the reference house, not to the engine.
EXCLUDE = {"catlin-house.json"}


def main() -> int:
    if not (SOURCE / "index.html").is_file():
        print(f"no built UI at {SOURCE} — run `cd ui && npm run build` first", file=sys.stderr)
        return 1
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=lambda _d, names: {n for n in names if n in EXCLUDE})
    size = sum(f.stat().st_size for f in TARGET.rglob("*") if f.is_file())
    print(f"staged {SOURCE} -> {TARGET} ({size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
