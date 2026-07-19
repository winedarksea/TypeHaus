"""Rebuild/resolve micro-benchmark (Phase 0 instrumentation → responsiveness plan).

Opens a house, runs N full rebuilds and one simulated ``move_nodes`` patch, and prints
per-stage medians so each later optimization phase is measured, not assumed.

Run with the repo .venv::

    PYTHONPATH=packages/engine/src .venv/bin/python packages/engine/scripts/bench_rebuild.py \
        --house houses/catlin --iters 15
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
    args = ap.parse_args()

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
    print(f"\nfull rebuild wall time: median {statistics.median(wall_times):.1f} ms "
          f"(min {min(wall_times):.1f}, max {max(wall_times):.1f})")
    _print_table("rebuild stage medians", _median_timings(rebuild_runs))

    # --- one simulated move_nodes patch via the slow path (writeback + rebuild), then undo ---
    if plan is not None:
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


if __name__ == "__main__":
    main()
