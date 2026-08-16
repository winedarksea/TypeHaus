#!/usr/bin/env bash
# The CI gate. Run it before every commit that touches the engine, the library, or a house.
#
# Usage: scripts/verify.sh [--fast] [--baseline-dir DIR]
#   --fast          tests + checks-as-tests + ruff + mypy only. Skips the two full house
#                   builds, the bench, and the npm build — the slow half — so the edit /
#                   verify loop stays short. Run the full gate before committing.
#   --baseline-dir  diff houses/{catlin,starter}/out/model.json against
#                   DIR/{catlin,starter}-model.json instead of only building them.
set -euo pipefail
cd "$(dirname "$0")/.."

HAUS=.venv/bin/haus
PY=.venv/bin/python

FAST=0
BASELINE_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fast) FAST=1; shift ;;
    --baseline-dir) BASELINE_DIR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "== engine tests =="
# Flags come from [tool.pytest.ini_options] in the root pyproject (-n 6 --dist loadfile).
$PY -m pytest packages/engine/tests

echo "== starter house checks-as-tests =="
# pytest_plugin.py is also registered as the `typehaus_checks` pytest11 entry point
# (pyproject.toml), so passing it as a file argument too double-loads it — under pytest
# 9.x that raises "duplicate parametrization of 'registered_check'" instead of the older,
# silently-tolerant behavior. -p no:typehaus_checks disables the auto-load so only the
# explicit file collection runs.
TYPEHAUS_HOUSE=houses/starter $PY -m pytest -p no:typehaus_checks \
  packages/engine/src/typehaus/checks/pytest_plugin.py

echo "== ruff =="
.venv/bin/ruff check packages/engine/src library

echo "== mypy --strict =="
.venv/bin/mypy packages/engine/src

if [[ "$FAST" == "1" ]]; then
  echo "== verify.sh --fast: tests, ruff and mypy passed (builds/bench/ui skipped) =="
  exit 0
fi

echo "== build: starter (json) =="
$HAUS build houses/starter --only json
if [[ -n "$BASELINE_DIR" ]]; then
  diff "$BASELINE_DIR/starter-model.json" houses/starter/out/model.json \
    && echo "starter model.json: byte-identical" \
    || echo "starter model.json: DIFFERS (verify this is an intended phase, e.g. Phase 5)"
fi

echo "== build: catlin (json) =="
$HAUS build houses/catlin --only json
if [[ -n "$BASELINE_DIR" ]]; then
  diff "$BASELINE_DIR/catlin-model.json" houses/catlin/out/model.json \
    && echo "catlin model.json: byte-identical" \
    || echo "catlin model.json: DIFFERS (verify this is an intended phase, e.g. Phase 5)"
fi

echo "== haus check: catlin =="
# catlin carried four accepted advisory FAILs until 2026-08-16 — two rooms without a supply
# register (drawn) and the unbalanced-fill screen (a bug in the check, not the house; see
# plans/TODO.md). It now carries none, so the default `fail` gate is the honest one and a new
# advisory FAIL stops the build instead of being waved through. `--exit-on error` is still
# there if a house ever needs to accept one; using it here would only hide a regression.
$HAUS check houses/catlin | tail -3

echo "== full build: catlin (IFC + glTF + permit PDFs) =="
$HAUS build houses/catlin

echo "== perf: bench_rebuild =="
$PY packages/engine/scripts/bench_rebuild.py --house houses/catlin --iters 15

echo "== ui: typecheck, test, build =="
(cd ui && npm run typecheck && npm test && npm run build)

echo "== verify.sh: all gates passed =="
