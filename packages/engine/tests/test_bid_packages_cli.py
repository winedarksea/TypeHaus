"""``haus bids --all`` twice, byte for byte. Split from ``test_bid_packages.py``: two full
subprocess builds of catlin is a slow-gate test, not a fast-loop one.
"""

from __future__ import annotations

import filecmp
import json
import subprocess
import sys
from pathlib import Path

import pytest
from _helpers import CATLIN

pytestmark = pytest.mark.slow


def test_all_is_byte_deterministic(tmp_path: Path) -> None:
    for name in ("a", "b"):
        result = subprocess.run([sys.executable, "-m", "typehaus.cli.app", "bids", str(CATLIN),
                                 "--all", "--out", str(tmp_path / name)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    match, mismatch, errors = filecmp.cmpfiles(
        tmp_path / "a", tmp_path / "b", [p.name for p in (tmp_path / "a").iterdir()],
        shallow=False)
    assert not mismatch and not errors, (mismatch, errors)
    manifest = json.loads((tmp_path / "a" / "MANIFEST.json").read_text())
    assert "framing.md" in manifest["files"] and "README.md" in manifest["files"]
