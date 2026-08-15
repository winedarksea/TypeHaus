"""Shared test helpers (→ AGENTS.md §3: factor setup used in 3+ files).

Import these instead of re-deriving them: the catlin path constant alone was duplicated
byte-for-byte in 61 test files, each spelling out its own ``parents[3]`` walk.
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOUSES = REPO_ROOT / "houses"
STARTER = HOUSES / "starter"
CATLIN = HOUSES / "catlin"

# A house sandbox needs the authored plan, never the build output. ``houses/catlin`` is 65 MB of
# which ``out/`` is 64 MB (renders, glb, ifc, model.json), so an unfiltered copy costs seconds and
# the suite builds 25 sandboxes. ``out/`` is gitignored, so CI never had it and never paid this —
# it was a purely local tax, and the handful of sites that already passed an ignore list ran an
# order of magnitude faster than the ones that did not.
HOUSE_IGNORE = shutil.ignore_patterns("out", "__pycache__", ".claude", ".DS_Store", ".git")


def copy_house(src: Path, dst: Path) -> Path:
    """Copy an authored house into a sandbox, leaving build output behind."""
    shutil.copytree(src, dst, ignore=HOUSE_IGNORE)
    return dst
