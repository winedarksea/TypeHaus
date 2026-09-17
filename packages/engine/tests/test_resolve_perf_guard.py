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
import warnings

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
# These budgets grade THIS machine and gate nothing on CI — see ``_ON_CI`` below.
#
# They are sized against the *loaded* suite, not a quiet one, because the loaded suite is
# what gates: `scripts/verify.sh` runs six-way parallel and that is where this fires. The
# distinction is not academic. Quiet, `resolve` mins at ~480 ms; inside the parallel suite
# it mins at ~1767 ms — and it measured 1764 ms there *before* the walking-surface fix that
# cut its quiet median by 30%. Under six-way contention the minimum is set by the other five
# workers, so grading it cannot see a change of this size at all. Budget the quiet number
# and the guard fails every honest run; budget this one and it still catches the large
# regression it exists for.
#
# Measured minima, 0.1.1, inside the six-way suite: full rebuild 2331 ms, resolve 1767 ms,
# junctions 355 ms, draw.details ~2500 ms. Each budget is ~2.2-2.5x that. Re-measure with
# `scripts/verify.sh` — not a bare `bench_rebuild.py` — whenever these move.
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


#: A GitHub runner's wall clock is not a measurement of this engine (→ module docstring),
#: so the budgets do not gate there. Actions sets ``CI=true``; so does most other hosted CI.
_ON_CI = bool(os.environ.get("CI"))


def test_rebuild_stays_inside_its_order_of_magnitude() -> None:
    result = subprocess.run(
        # Best-of-3, not best-of-5. The budgets below are 2.2-2.5x the measured minimum,
        # so this stays an order-of-magnitude tripwire rather than a stopwatch, and two
        # fewer rebuilds is ~40% of this module. Raise the ITERS, never the budget, if it
        # turns noisy.
        [sys.executable, str(BENCH), "--house", str(CATLIN), "--iters", "3",
         "--skip-macro", "--assert-under", str(REBUILD_BUDGET_MS),
         *(arg for stage, ms in STAGE_BUDGETS_MS.items()
           for arg in ("--assert-stage-under", f"{stage}={ms}"))],
        capture_output=True, text=True, cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "packages" / "engine" / "src")},
    )
    if _ON_CI:
        # Report, never gate. A warning rather than a print because pytest runs ``-q`` here
        # and swallows the stdout of a passing test, while the warnings summary survives —
        # so the timings stay readable in the run log and someone can watch the trend.
        if result.returncode != 0:
            warnings.warn(
                "perf budget breached on CI — NOT failing the build, because a runner's "
                "wall clock varies ~2x run to run (see the module docstring). Reproduce "
                f"locally before believing it.\n{result.stdout}\n{result.stderr}",
                stacklevel=2)
        return
    assert result.returncode == 0, (
        "rebuild budget breached — read the timings below before raising the budget; "
        "these are ~2.5-3x the local minimum, so this firing means a real regression "
        f"or a badly loaded machine.\n{result.stdout}\n{result.stderr}")
