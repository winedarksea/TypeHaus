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
# catlin is held to a clean report, so this gates on any FAIL — but on the same terms as
# `test_catlin_carries_no_failures` in the engine tests above, which allows exactly one
# owner-decided advisory. The two were NOT in step: the test allowed that entry and this
# stage allowed none, so the script could only ever go red here. It was invisible for as long
# as the mypy stage above stopped the run before reaching this line.
#
# `--exit-on error` is the wrong loosening — it lets *any* FAIL through. Gate on the JSON
# instead, subtracting the identical allow-list, so a real regression still stops the build.
# Keep this list and the test's `accepted` set in step; a new entry needs a design-record
# citation in both.
#
# `--exit-on none` is what hands the verdict to that JSON. Without it `haus check` exits 1
# on the accepted FAIL and `set -e` kills the script before the gate below ever runs.
#
# It spent 2026-08-23 on the looser `--exit-on error` while three `structural.deck_beam_span`
# advisories stood against BM-SG-BLW/BLC/BLE, and is back to the strict gate now that they
# are fixed rather than accepted — the beams are three-ply KDAT 2x12 and clear IRC Table
# R507.5(1) at the 10' joist-span row.
CATLIN_CHECK="$(mktemp -t catlin-check)"
$HAUS check houses/catlin --json --exit-on none > "$CATLIN_CHECK"
$PY - "$CATLIN_CHECK" <<'PYEOF'
import json, sys

# The parcel ring. Owner/project state, not a defect: no lot has been bought, so every lot
# line, setback and coverage figure on C-101 was drawn rather than measured. The MN profile
# already declares the permit line `blocking=False`, so `haus print` does not stop on it.
ACCEPTED = {("code.site_parcel_is_surveyed", ())}

payload = json.load(open(sys.argv[1]))
failures = {
    (f["check_id"], tuple(sorted(f["element_tags"] or ())))
    for f in payload["findings"] if f["result"] == "fail"
}
stale = ACCEPTED - failures
if stale:
    sys.exit(f"an accepted advisory stopped firing — delete it from the list: {sorted(stale)}")
unexpected = sorted(failures - ACCEPTED)
if unexpected:
    sys.exit(f"catlin FAILs: {unexpected}")
print(f"{payload['pass']} pass, {payload['fail']} fail "
      f"({len(ACCEPTED)} accepted), {payload['unknown']} not evaluable, "
      f"{payload['not_applicable']} not applicable")
PYEOF
rm -f "$CATLIN_CHECK"

# `build` emits model.json + model.ifc + the vocabulary manifest, and nothing else: GLB
# comes from `haus render`, the permit PDFs from `haus print`. The label here claimed all
# three for a long time.
echo "== full build: catlin (model.json + IFC) =="
$HAUS build houses/catlin --timing

# bench_rebuild is deliberately NOT run standalone here: test_resolve_perf_guard.py in the
# engine tests above already subprocesses the same benchmark and asserts on its result, so
# this stage was measuring the same thing a second time and a slower way.

echo "== ui: typecheck, test, build =="
(cd ui && npm run typecheck && npm test && npm run build)

echo "== verify.sh: all gates passed =="
