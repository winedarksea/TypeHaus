"""Rebuild/resolve micro-benchmark (Phase 0 instrumentation → responsiveness plan).

Opens a house, runs N full rebuilds and one simulated ``move_nodes`` patch, and prints
per-stage medians so each later optimization phase is measured, not assumed.

Run with the repo .venv::

    PYTHONPATH=packages/engine/src .venv/bin/python packages/engine/scripts/bench_rebuild.py \
        --house houses/catlin --iters 15

As a regression guard (exits non-zero when a budget is blown)::

    PYTHONPATH=packages/engine/src .venv/bin/python packages/engine/scripts/bench_rebuild.py \
        --house houses/catlin --iters 10 --skip-macro \
        --assert-under 400 --assert-stage-under resolve=300

Budgets are medians, and a median is only meaningful against a quiet machine: pick a
threshold with real headroom over the measured number (roughly 2x) so the guard catches an
algorithmic regression rather than whatever else happened to be running.
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

from typehaus.server.macros_api import build_macro_ops
from typehaus.server.state import ProjectState


def _median_timings(runs: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({k for r in runs for k in r})
    return {k: statistics.median([r[k] for r in runs if k in r]) for k in keys}


def _print_table(title: str, timings: dict[str, float]) -> None:
    print(f"\n== {title} ==")
    for k, v in sorted(timings.items(), key=lambda kv: -kv[1]):
        print(f"  {v:8.2f} ms  {k}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", default="houses/catlin")
    ap.add_argument("--iters", type=int, default=15)
    ap.add_argument("--storey", default="main")
    ap.add_argument("--node", default="N-M-S1")
    ap.add_argument("--skip-macro", action="store_true",
                    help="only run the plain rebuilds — the macro paths dominate wall time "
                         "and a perf guard does not need them")
    ap.add_argument("--assert-under", type=float, metavar="MS",
                    help="exit 1 if the median full-rebuild wall time exceeds MS")
    ap.add_argument("--assert-stage-under", action="append", default=[],
                    metavar="STAGE=MS",
                    help="exit 1 if the median of timing key STAGE exceeds MS; repeatable "
                         "(e.g. resolve=300, resolve.junctions=120)")
    args = ap.parse_args()
    budgets = _parse_stage_budgets(args.assert_stage_under)

    house = Path(args.house).resolve()
    print(f"opening {house} ...")
    state = ProjectState.open(house)
    plan = state.model.plan if state.model else None
    n_walls = len(state.model.walls) if state.model else 0
    print(f"opened: {n_walls} resolved walls, ok={state.ok}")

    # --- N plain rebuilds (load_plan + resolve + checks) ---
    rebuild_runs: list[dict[str, float]] = []
    wall_times: list[float] = []
    for _ in range(args.iters):
        t0 = time.perf_counter()
        state.rebuild()
        wall_times.append((time.perf_counter() - t0) * 1000.0)
        rebuild_runs.append(dict(state.timings))
    rebuild_median = statistics.median(wall_times)
    print(f"\nfull rebuild wall time: median {rebuild_median:.1f} ms "
          f"(min {min(wall_times):.1f}, max {max(wall_times):.1f})")
    stage_medians = _median_timings(rebuild_runs)
    _print_table("rebuild stage medians", stage_medians)

    breaches = _budget_breaches(rebuild_median, stage_medians, args.assert_under, budgets)

    # --- one simulated move_nodes patch via the slow path (writeback + rebuild), then undo ---
    if plan is not None and not args.skip_macro:
        body = {"macro": "move_nodes", "storey": args.storey,
                "nodes": [args.node], "dx": 0.01, "dy": 0.0}
        patch_runs: list[dict[str, float]] = []
        commit_times: list[float] = []
        for _ in range(min(args.iters, 8)):
            t0 = time.perf_counter()
            result = build_macro_ops(state.model.plan, body)
            state.coordinator.apply_patch(result.ops, None)
            state.rebuild()
            commit_times.append((time.perf_counter() - t0) * 1000.0)
            patch_runs.append(dict(state.timings))
            state.coordinator.undo()
            state.rebuild()
        print(f"\nmove_nodes commit wall time (slow path, writeback+rebuild): median "
              f"{statistics.median(commit_times):.1f} ms")
        _print_table("patch-triggered rebuild stage medians",
                     _median_timings(patch_runs))

        # --- the same macro via the fast path (Phase 2b: in-memory apply, async writeback) ---
        fast_times: list[float] = []
        for _ in range(min(args.iters, 8)):
            result = build_macro_ops(state.model.plan, body)
            t0 = time.perf_counter()
            state.apply_edit(result.ops, None)
            fast_times.append((time.perf_counter() - t0) * 1000.0)
            state._flush_writes()  # keep source/plan settled before the next undo
            state.history(undo=True)
        print(f"\nmove_nodes commit wall time (fast path, in-memory apply): median "
              f"{statistics.median(fast_times):.1f} ms")

    if breaches:
        print("\n== budget breaches ==")
        for line in breaches:
            print(f"  FAIL {line}")
        raise SystemExit(1)
    if args.assert_under is not None or budgets:
        print("\nall budgets met")


def _parse_stage_budgets(raw: list[str]) -> dict[str, float]:
    budgets: dict[str, float] = {}
    for entry in raw:
        stage, separator, value = entry.partition("=")
        if not separator or not stage:
            raise SystemExit(f"--assert-stage-under expects STAGE=MS, got {entry!r}")
        budgets[stage] = float(value)
    return budgets


def _budget_breaches(rebuild_median: float, stage_medians: dict[str, float],
                     rebuild_budget: float | None,
                     stage_budgets: dict[str, float]) -> list[str]:
    """Every budget the run missed, as printable lines.

    Collected rather than raised at the first miss so one run reports every regression.
    """
    breaches: list[str] = []
    if rebuild_budget is not None and rebuild_median > rebuild_budget:
        breaches.append(f"full rebuild median {rebuild_median:.1f} ms "
                        f"> budget {rebuild_budget:.1f} ms")
    for stage, budget in sorted(stage_budgets.items()):
        if stage not in stage_medians:
            breaches.append(f"stage {stage!r} was never timed — "
                            f"known keys: {', '.join(sorted(stage_medians))}")
        elif stage_medians[stage] > budget:
            breaches.append(f"stage {stage} median {stage_medians[stage]:.1f} ms "
                            f"> budget {budget:.1f} ms")
    return breaches


if __name__ == "__main__":
    main()
