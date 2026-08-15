#!/usr/bin/env bash
# Phase-boundary verification gate for the Type:Haus optimization plan
# (plans/make-a-plan-to-humble-truffle.md). Run after every phase.
#
# Usage: scripts/verify.sh [--baseline-dir DIR]
# With --baseline-dir, diffs houses/{catlin,starter}/out/model.json against
# DIR/{catlin,starter}-model.json instead of only building them.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONPATH=packages/engine/src

BASELINE_DIR=""
if [[ "${1:-}" == "--baseline-dir" ]]; then
  BASELINE_DIR="$2"
fi

echo "== engine tests =="
.venv/bin/python -m pytest packages/engine/tests -n 6 --dist loadfile -q

echo "== starter house checks-as-tests =="
# pytest_plugin.py is also registered as the `typehaus_checks` pytest11 entry point
# (pyproject.toml), so passing it as a file argument too double-loads it — under pytest
# 9.x that raises "duplicate parametrization of 'registered_check'" instead of the older,
# silently-tolerant behavior. -p no:typehaus_checks disables the auto-load so only the
# explicit file collection runs.
TYPEHAUS_HOUSE=houses/starter .venv/bin/python -m pytest -p no:typehaus_checks \
  packages/engine/src/typehaus/checks/pytest_plugin.py -q

echo "== ruff =="
.venv/bin/ruff check packages/engine/src library

echo "== mypy --strict =="
.venv/bin/mypy packages/engine/src

echo "== build: starter (json) =="
.venv/bin/python -m typehaus.cli.app build houses/starter --only json
if [[ -n "$BASELINE_DIR" ]]; then
  diff "$BASELINE_DIR/starter-model.json" houses/starter/out/model.json \
    && echo "starter model.json: byte-identical" \
    || echo "starter model.json: DIFFERS (verify this is an intended phase, e.g. Phase 5)"
fi

echo "== build: catlin (json) =="
.venv/bin/python -m typehaus.cli.app build houses/catlin --only json
if [[ -n "$BASELINE_DIR" ]]; then
  diff "$BASELINE_DIR/catlin-model.json" houses/catlin/out/model.json \
    && echo "catlin model.json: byte-identical" \
    || echo "catlin model.json: DIFFERS (verify this is an intended phase, e.g. Phase 5)"
fi

echo "== haus check: catlin =="
.venv/bin/python -m typehaus.cli.app check houses/catlin | tail -3

echo "== full build: catlin (IFC + glTF + permit PDFs) =="
.venv/bin/python -m typehaus.cli.app build houses/catlin

echo "== perf: bench_rebuild =="
.venv/bin/python packages/engine/scripts/bench_rebuild.py --house houses/catlin --iters 15

echo "== ui: typecheck, test, build =="
(cd ui && npm run typecheck && npm test && npm run build)

echo "== verify.sh: all gates passed =="
