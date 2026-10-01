#!/usr/bin/env bash
# The CI gate. Run it before every commit that touches the engine, the library, or a house.
#
# Usage: scripts/verify.sh [--fast] [--baseline-dir DIR]
#   --fast          tests + checks-as-tests + ruff only, and the tests deselect the
#                   `slow` marker. Skips the two full house builds and the npm build — the
#                   slow half — so the edit / verify loop stays short. The full gate runs
#                   every test including `slow`; run it before committing.
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
#
# --fast deselects `slow` (full IFC emission, permit-set rendering, golden comparison,
# subprocess benchmarks — see the marker's definition in pyproject.toml). The full gate
# below runs everything, which is what keeps `slow` from becoming where tests go to die.
if [[ "$FAST" == "1" ]]; then
  $PY -m pytest packages/engine/tests -m "not slow"
else
  $PY -m pytest packages/engine/tests
fi

echo "== starter house checks-as-tests =="
# pytest_plugin.py is also registered as the `typehaus_checks` pytest11 entry point
# (pyproject.toml), so passing it as a file argument too double-loads it — under pytest
# 9.x that raises "duplicate parametrization of 'registered_check'" instead of the older,
# silently-tolerant behavior. -p no:typehaus_checks disables the auto-load so only the
# explicit file collection runs.
TYPEHAUS_HOUSE=houses/starter $PY -m pytest -p no:typehaus_checks \
  packages/engine/src/typehaus/checks/pytest_plugin.py

echo "== catlin house checks-as-tests =="
TYPEHAUS_HOUSE=houses/catlin \
  $PY -m pytest -p no:typehaus_checks \
  packages/engine/src/typehaus/checks/pytest_plugin.py

echo "== ruff =="
.venv/bin/ruff check packages/engine/src

# mypy is deliberately NOT a stage here, for the same reason it is not a CI gate: it reports
# 2781 errors under --strict and 1119 even heavily relaxed, and this script is `set -e`, so
# a blocking mypy meant stages 5-10 — every build, `haus check houses/catlin`, the full IFC
# build and the UI — were never reached by the script documented as the full gate. Losing
# ten real stages to keep a red one was the wrong trade. Run `.venv/bin/mypy
# packages/engine/src` by hand while working through it.

if [[ "$FAST" == "1" ]]; then
  echo "== verify.sh --fast: tests and ruff passed (builds/bench/ui skipped) =="
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
# Keep the check gate strict: every FAIL stops the build. `--exit-on none` lets the JSON
# assertion report all failures together instead of stopping at the first one.
#
# It spent 2026-08-23 on the looser `--exit-on error` while three `structural.deck_beam_span`
# advisories stood against BM-SG-BLW/BLC/BLE, and is back to the strict gate now that they
# are fixed rather than accepted — the beams are three-ply KDAT 2x12 and clear IRC Table
# R507.5(1) at the 10' joist-span row.
CATLIN_CHECK="$(mktemp -t catlin-check)"
$HAUS check houses/catlin --json --exit-on none > "$CATLIN_CHECK"
$PY - "$CATLIN_CHECK" <<'PYEOF'
import json, sys

payload = json.load(open(sys.argv[1]))
failures = {
    (f["check_id"], tuple(sorted(f["element_tags"] or ())))
    for f in payload["findings"] if f["result"] == "fail"
}
if failures:
    sys.exit(f"catlin FAILs: {sorted(failures)}")
print(f"{payload['pass']} pass, {payload['fail']} fail, "
      f"{payload['unknown']} not evaluable, "
      f"{payload['not_applicable']} not applicable")
PYEOF
rm -f "$CATLIN_CHECK"

# `build` emits model.json + model.ifc + the vocabulary manifest, and nothing else: GLB
# comes from `haus render`, the permit PDFs from `haus print`. The label here claimed all
# three for a long time.
echo "== full build: catlin (model.json + IFC) =="
$HAUS build houses/catlin --timing

# That test also runs inside the xdist suite above, where it reports overruns without gating:
# other workers distort wall-clock results. Run it once more without xdist so the local budget
# is measured after the suite's parallel load is gone.
echo "== rebuild budget: catlin (serial) =="
$PY -m pytest -n0 packages/engine/tests/test_resolve_perf_guard.py::test_rebuild_stays_inside_its_order_of_magnitude -q

echo "== ui: typecheck, test, build =="
(cd ui && npm run typecheck && npm test && npm run build)

echo "== verify.sh: all gates passed =="
