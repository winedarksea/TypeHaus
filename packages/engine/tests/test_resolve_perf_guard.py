"""A ceiling on rebuild time, so a 15x regression cannot go unnoticed again.

PERF.md recorded a 44 ms ``move_nodes`` and a "sub-50 ms resolve pipeline"; by the time
anyone measured again, resolve alone was 488 ms of a 533 ms rebuild. Nothing failed in
between, because nothing was watching. This is the thing that watches.

The budgets are deliberately loose — roughly 2.5x the figure the CI runner measures —
because CI hardware, a loaded laptop and a cold import cache all move the number by a
factor of two and a flaky perf test gets deleted rather than fixed. It is a tripwire for
an order-of-magnitude regression, not a benchmark.

Which is why the bench grades these budgets on the *fastest* of its N samples rather than
the median (→ ``bench_rebuild.py::_min_timings``). This test subprocesses that bench from
inside a six-way parallel suite, so a median here measures the other five workers as much
as the engine: ``resolve`` is ~480 ms alone and hit 1764 ms against a 1500 ms budget on a
loaded run, with nothing regressed. Grading the least-contended sample keeps the tripwire
honest — an algorithmic regression raises the floor too.

Grading the minimum does not, however, make a slow machine fast. See the budget block below
for why these numbers are set against the CI runner rather than against this laptop.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from _helpers import CATLIN, REPO_ROOT

# ``slow`` (→ pyproject.toml, AGENTS.md §3): subprocesses bench_rebuild.py in a cold
# interpreter; a tripwire for an order-of-magnitude regression, not a correctness test.
# `scripts/verify.sh --fast` deselects it; the full gate still runs it.
pytestmark = pytest.mark.slow

BENCH = REPO_ROOT / "packages" / "engine" / "scripts" / "bench_rebuild.py"

# Measured minima on the development machine at 0.1.1: full rebuild ~570 ms, resolve
# ~480 ms, junctions ~70 ms, placeables ~40 ms, draw.details ~1280 ms.
#
# The previous figures here ("full rebuild ~360 ms, resolve ~220 ms, junctions ~90 ms,
# placeables ~28 ms", from the Phase 1.5 work) were already stale by v0.1.0 — resolve
# measured 437 ms at that tag — which is why a 2x regression in one 40 ms stage read as a
# 20x blowout when someone finally went looking. A baseline nobody re-measures is worse than
# no baseline, so these are dated: re-measure with ``bench_rebuild.py --iters 7`` and update
# them whenever the budgets move.
#
# ``draw.details`` is the whole derived-detail set (~76 full cuts of the model). It is
# budgeted because nothing else here watches the drawing stage, and the section migration is
# exactly the kind of change that could quietly make every detail a full geometry walk.
#
# The budgets are set against CI hardware, not this machine, because that is where they
# gate. The GitHub runner measures ~2.8x slower than the development machine (draw.details:
# 3570 ms there against 1283 ms here), and best-of-N grading — added to stop the six-way
# parallel suite from being what the median measured — defeats *contention*, not a slower
# CPU. Budgeting the local number therefore fired on every release run: the v0.1.0 and
# v0.1.1 CI attempts both died here, on resolve and draw.details, with nothing regressed.
# Each budget below is ~2.5x the observed or projected CI figure, which still catches the
# order-of-magnitude regression this file exists to catch (a 15x ``move_nodes`` blowout went
# unnoticed once) while leaving the runner room to be slow.
REBUILD_BUDGET_MS = 5000
STAGE_BUDGETS_MS = {"resolve": 4000, "resolve.junctions": 700, "draw.details": 9000}


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
