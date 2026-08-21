"""A ceiling on rebuild time, so a 15x regression cannot go unnoticed again.

PERF.md recorded a 44 ms ``move_nodes`` and a "sub-50 ms resolve pipeline"; by the time
anyone measured again, resolve alone was 488 ms of a 533 ms rebuild. Nothing failed in
between, because nothing was watching. This is the thing that watches.

The budgets are deliberately loose — roughly 2.5x the measured median on the development
machine — because CI hardware, a loaded laptop and a cold import cache all move the
number by a factor of two and a flaky perf test gets deleted rather than fixed. It is a
tripwire for an order-of-magnitude regression, not a benchmark.
"""

from __future__ import annotations

import os
import subprocess
import sys

from _helpers import CATLIN, REPO_ROOT

BENCH = REPO_ROOT / "packages" / "engine" / "scripts" / "bench_rebuild.py"

# Measured medians on the development machine after the Phase 1.5 work: full rebuild
# ~360 ms, resolve ~220 ms, junctions ~90 ms, placeables ~28 ms. See PERF.md.
#
# ``draw.details`` is the whole derived-detail set (~50 full cuts of the model, ~240 ms
# measured). It is budgeted because nothing else here watches the drawing stage, and the
# section migration is exactly the kind of change that could quietly make every detail a
# full geometry walk.
REBUILD_BUDGET_MS = 2500
STAGE_BUDGETS_MS = {"resolve": 1500, "resolve.junctions": 700, "draw.details": 1200}


def test_rebuild_stays_inside_its_order_of_magnitude() -> None:
    result = subprocess.run(
        [sys.executable, str(BENCH), "--house", str(CATLIN), "--iters", "5",
         "--skip-macro", "--assert-under", str(REBUILD_BUDGET_MS),
         *(arg for stage, ms in STAGE_BUDGETS_MS.items()
           for arg in ("--assert-stage-under", f"{stage}={ms}"))],
        capture_output=True, text=True, cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "engine" / "src")},
    )
    assert result.returncode == 0, (
        "rebuild budget breached — read the timings below before raising the budget; "
        "a 2.5x-headroom tripwire firing means something got an order of magnitude "
        f"slower.\n{result.stdout}\n{result.stderr}")
