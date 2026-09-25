"""A ceiling on rebuild time, so a 15x regression cannot go unnoticed again.

PERF.md recorded a 44 ms ``move_nodes`` and a "sub-50 ms resolve pipeline"; by the time
anyone measured again, resolve alone was 488 ms of a 533 ms rebuild. Nothing failed in
between, because nothing was watching. This is the thing that watches.

The budgets are deliberately loose — roughly 2.5x the minimum measured inside the
six-way parallel suite that runs them — because contention and a cold import cache both
move the number and a flaky perf test gets deleted rather than fixed. It is a tripwire
for a large regression, not a benchmark.

It does not gate CI, and that is deliberate. A GitHub runner's wall clock varies about
2x run to run: across two release runs of code that differed in nothing touching the
drawing stage, ``resolve`` best-of measured 1712 ms and then 3345 ms, and
``draw.details`` breached a 3000 ms budget in one and passed it in the other. A budget
tight enough to be a useful tripwire is therefore a coin flip up there, and it lost the
toss on the v0.1.0 and v0.1.1 release runs, blocking a publish with nothing regressed.
On CI the bench still runs and still reports — the timings ride out as a warning so they
stay in the log — but only this machine, where the measurement means something, can fail
the build.

Which is why the bench grades these budgets on the *fastest* of its N samples rather than
the median (→ ``bench_rebuild.py::_min_timings``). This test subprocesses that bench from
inside a six-way parallel suite, so a median here measures the other five workers as much
as the engine. A parallel run reports an overrun as a warning; the full local gate reruns
the same test serially after the suite, where its budget is meaningful. Grading the
least-contended sample keeps the tripwire honest — an algorithmic regression raises the
floor too.

Grading the minimum does not, however, make a slow machine fast. See the budget block below
for why these numbers are set against the CI runner rather than against this laptop.
"""

from __future__ import annotations

import os
import subprocess
import sys
import warnings

import pytest
from _helpers import CATLIN, REPO_ROOT

# ``slow`` (→ pyproject.toml, AGENTS.md §3): subprocesses bench_rebuild.py in a cold
# interpreter; a tripwire for an order-of-magnitude regression, not a correctness test.
# `scripts/verify.sh --fast` deselects it; the full gate still runs it.
pytestmark = pytest.mark.slow

BENCH = REPO_ROOT / "packages" / "engine" / "scripts" / "bench_rebuild.py"

# A serial Catlin measurement on 2026-09-25: full rebuild min 2215 ms / median 2320 ms,
# resolve median 2090 ms, junctions 131 ms, and draw.details 1138 ms. The wider budgets below
# allow ordinary variation while still catching a large regression. ``draw.details`` covers
# the whole derived-detail set (~80 full cuts); it is budgeted because a change that makes each
# detail walk the full geometry could otherwise slow every drawing without a tripwire.
#
# The test reports rather than gates when it runs under xdist or CI: parallel worker load makes
# the wall clock untrustworthy. `scripts/verify.sh` reruns it serially on this machine, which is
# where the budget is enforced. Re-measure with `scripts/verify.sh` before moving thresholds.
REBUILD_BUDGET_MS = 5000
STAGE_BUDGETS_MS = {"resolve": 4000, "resolve.junctions": 900, "draw.details": 6000,
                    # The derived connector markers get a tripwire of their own rather than
                    # hiding inside resolve's total: the stage's cost is a function of how
                    # many roles ``joints/markers.py`` sets ``draw=True`` on, and widening
                    # that table is a one-character edit. ~530 markers measured at a 20 ms
                    # minimum under two-way contention; budgeted well above a six-way one,
                    # because what this has to catch is somebody drawing five thousand.
                    "resolve.connector_markers": 300,
                    # The rebar layout (decision #75): ~1,180 pieces at a 14 ms minimum.
                    # What this catches is a layout that went quadratic in bars per host.
                    "resolve.rebar": 150}


#: A GitHub runner's or another xdist worker's wall clock is not a measurement of this engine
#: (→ module docstring), so those runs report breaches without gating. Actions sets
#: ``CI=true``; xdist workers set ``PYTEST_XDIST_WORKER``.
_ON_CI = bool(os.environ.get("CI"))
_UNDER_XDIST = bool(os.environ.get("PYTEST_XDIST_WORKER"))


def test_rebuild_stays_inside_its_order_of_magnitude() -> None:
    result = subprocess.run(
        # Best-of-3, not best-of-5. The full-rebuild and resolve ceilings leave about 2x
        # headroom over the serial baseline, keeping this an order-of-magnitude tripwire
        # rather than a stopwatch. Two fewer rebuilds is ~40% of this module. Raise ITERS,
        # never the budget, if it turns noisy.
        [sys.executable, str(BENCH), "--house", str(CATLIN), "--iters", "3",
         "--skip-macro", "--assert-under", str(REBUILD_BUDGET_MS),
         *(arg for stage, ms in STAGE_BUDGETS_MS.items()
           for arg in ("--assert-stage-under", f"{stage}={ms}"))],
        capture_output=True, text=True, cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "engine" / "src")},
    )
    if _ON_CI or _UNDER_XDIST:
        # CI runners and parallel workers report, never gate. A warning rather than a print
        # because pytest runs ``-q`` here and swallows passing stdout, while the warnings
        # summary survives. The local full gate reruns this test with xdist disabled.
        if result.returncode != 0:
            warnings.warn(
                "perf budget breached under CI/parallel load — NOT failing this run, because "
                "the wall clock includes other workers (see the module docstring). Reproduce "
                f"locally before believing it.\n{result.stdout}\n{result.stderr}",
                stacklevel=2)
        return
    assert result.returncode == 0, (
        "rebuild budget breached — read the timings below before raising the budget; "
        "these are ~2.5-3x the local minimum, so this firing means a real regression "
        f"or a badly loaded machine.\n{result.stdout}\n{result.stderr}")
