#!/usr/bin/env python3
"""Assert a built wheel actually contains what a `pip install typehaus` needs.

0.1.0a0 shipped a wheel holding only `typehaus/`: no shared catalog, no `haus new` template,
no license text. Every house plan does `from library import ...`, so that wheel installed an
engine that could not load or scaffold a single house — and nothing in the source tree could
see it, because from a checkout every one of those paths resolves anyway.

Usage: python scripts/check_wheel.py dist/typehaus-*.whl
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

# Paths that must exist inside the wheel. The UI is checked separately: it is staged by
# `scripts/package_ui.py` and a wheel built without that step is still a valid engine.
REQUIRED = (
    "typehaus/library/__init__.py",
    "typehaus/library/placeables/__init__.py",
    "typehaus/library/assemblies.py",
    "typehaus/library/materials.py",
    "typehaus/templates/starter/plan/manifest.py",
    "typehaus/templates/starter/preferences.toml",
)


def main(path: Path) -> int:
    names = zipfile.ZipFile(path).namelist()
    problems: list[str] = []

    missing = [r for r in REQUIRED if r not in names]
    if missing:
        problems.append(f"missing: {missing}")

    if not any(n.endswith("/licenses/LICENSE") for n in names):
        problems.append("no LICENSE in the dist-info")

    # `library` is an occupied name on PyPI (an unrelated media library). A top-level one
    # here would shadow or be shadowed by it, breaking whichever was installed second.
    tops = {n.split("/")[0] for n in names}
    if "library" in tops:
        problems.append(f"installs a top-level `library`: {sorted(tops)}")

    ui = [n for n in names if n.startswith("typehaus/server/static/")]
    if any(n.endswith("typehaus/server/static/index.html") for n in ui):
        print(f"packaged UI: {len(ui)} files")
    else:
        print("packaged UI: absent (run scripts/package_ui.py before building to ship it)")

    if problems:
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        return 1
    print(f"wheel ok: {path.name}, top-level {sorted(tops)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
