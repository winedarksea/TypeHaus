#!/usr/bin/env bash
# Reproduce the CI `engine` job locally, in a THROWAWAY venv built only from the declared
# dependencies.
#
# This exists because `scripts/verify.sh` cannot catch a whole class of break: it runs in
# `.venv`, which has accumulated packages nobody declared. `pytest-xdist` was one — the root
# pyproject's addopts carry `-n 6 --dist loadfile` unconditionally, so CI's pytest died with
# "unrecognized arguments: -n --dist loadfile" before collecting a test, while every local run
# was green. An undeclared dependency is invisible from an environment that already has it.
#
# Usage: scripts/ci_local.sh [--keep]
#   --keep   leave the venv in place (it prints the path) instead of deleting it
#
# The one intentional divergence from ci.yml: CI builds the wheel with `uv build` and this
# uses `python -m build`, because uv is not installed here. Same backend, same output.
set -euo pipefail

KEEP=0
[[ "${1:-}" == "--keep" ]] && KEEP=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENVDIR="$(mktemp -d -t typehaus-ci)"
cleanup() { [[ "$KEEP" == "1" ]] || rm -rf "$ENVDIR"; }
trap cleanup EXIT

echo "== fresh venv from declared deps only: $ENVDIR =="
# `.venv/bin/python` only to get a 3.11 interpreter; nothing from .venv is inherited.
.venv/bin/python -m venv "$ENVDIR/venv"
VPY="$ENVDIR/venv/bin/python"
VHAUS="$ENVDIR/venv/bin/haus"
"$VPY" -m pip install --quiet --upgrade pip build
# Mirrors CI's `uv sync --all-packages --all-extras`: every declared extra, nothing else.
"$VPY" -m pip install --quiet -e "packages/engine[dev,server]"

echo "== ruff =="
"$ENVDIR/venv/bin/ruff" check packages/engine/src

echo "== pytest =="
"$VPY" -m pytest packages/engine/tests -q

echo "== checks-as-tests on the starter house =="
TYPEHAUS_HOUSE=houses/starter "$VPY" -m pytest -p no:typehaus_checks \
  packages/engine/src/typehaus/checks/pytest_plugin.py -q

echo "== starter build =="
"$VHAUS" build houses/starter

echo "== catlin build =="
"$VHAUS" build houses/catlin

echo "== permit checklist renders (starter) =="
"$VHAUS" permit-check houses/starter --json > "$ENVDIR/permit.json" || true
"$VPY" -c "import json,sys; d=json.load(open('$ENVDIR/permit.json')); \
  sys.exit(0 if d['items'] else 'permit checklist produced no items')"

echo "== catlin permit print =="
# ** THE DRAFT GATE IS SHUT ON PURPOSE, AND THIS IS THE ONLY SCRIPT THAT NOTICES. **
# `scripts/verify.sh` never runs `haus print`, so when the 2026-09-18 engineering gap
# review wired `engineering/column_base.py` to a check and the north entry canopy's two
# cast columns went red on IBC 1807.3.2.1 embedment, this step — and only this step —
# started refusing. The refusal is correct: a permit printoff is exactly what a shut gate
# is for. What would be wrong is a script that cannot tell THAT refusal from any other.
#
# ** THE COLUMNS THAT SHUT IT ARE NOT THE COLUMNS THAT SHUT IT IN SEPTEMBER, AND THE GREP
# IS UNCHANGED BECAUSE THE PERMIT LINE IS. ** That is the point of asserting an ITEM rather
# than a column count. The history: two canopy columns red on 2026-09-18; sharing the frame
# shear with `W-BW-SCREEN` by relative rigidity closed `PT-BW-RE` to a §1806.3.4 judgement on
# 2026-09-19 (`notes/entry_column_base_fixity.md` §7); §6a put both canopy bases on one plane
# at -10'-2" on 2026-09-20 and closed them outright, so `haus check` is back to 0 FAIL and
# verify.sh's ACCEPTED list is EMPTY.
#
# ** WHAT STILL SHUTS THE GATE IS AN UNKNOWN, NOT A FAIL. ** `haus print` gates on UNKNOWN
# too. `PT-BW-GW` and `-GE` — the two GARAGE-SIDE LANDING columns, whose case is the R301.5
# guard load and not the canopy's wind — need 4.45' at the table's lateral bearing and 3.39'
# at §1806.3.4's isolated-pole double against the 3.50' they have. They straddle, so no
# verdict publishes, exactly as `PT-BW-RE` used to. §4 of that note has the table.
#
# So the refusal is expected, and it is expected to name that one item. See
# `notes/entry_column_base_fixity.md` §4 and §6 for the arithmetic and the closures. DELETE
# THIS BLOCK, and restore the bare `"$VHAUS" print houses/catlin`, the day those two land.
PRINT_OUT="$ENVDIR/catlin-print.txt"
if "$VHAUS" print houses/catlin > "$PRINT_OUT" 2>&1; then
  cat "$PRINT_OUT"
  echo "the catlin draft gate is OPEN again — the column_base embedment gap is closed."
  echo "restore the plain 'haus print houses/catlin' here and delete this whole block."
  exit 1
fi
cat "$PRINT_OUT"
grep -q "Fixed column base embedment" "$PRINT_OUT" \
  || { echo "catlin's permit print is blocked by something OTHER than the accepted"; \
       echo "column_base embedment gap — read the output above."; exit 1; }
# One blocker, not a pile of them behind the one we accept: every line the gate lists has
# to be that item.
"$VPY" - "$PRINT_OUT" <<'PYEOF'
import sys

blocked = [line.strip() for line in open(sys.argv[1])
           if line.startswith("  ") and line.strip()]
other = [line for line in blocked if not line.startswith("Fixed column base embedment")]
if other:
    sys.exit("the permit gate lists blockers beyond the accepted one:\n  "
             + "\n  ".join(other))
print(f"permit print refused as expected: {len(blocked)} accepted blocker(s)")
PYEOF

echo "== wheel installs and scaffolds a buildable house =="
"$VPY" -m build --wheel packages/engine --outdir "$ENVDIR/wheel"
"$VPY" scripts/check_wheel.py "$ENVDIR"/wheel/*.whl
.venv/bin/python -m venv "$ENVDIR/wheelenv"
"$ENVDIR/wheelenv/bin/python" -m pip install --quiet "$ENVDIR"/wheel/*.whl
"$ENVDIR/wheelenv/bin/haus" new "$ENVDIR/wheelhouse" --name "Wheel House"
"$ENVDIR/wheelenv/bin/haus" build "$ENVDIR/wheelhouse"

echo "== build determinism (two builds byte-identical) =="
"$VHAUS" build houses/starter --only json
cp houses/starter/out/model.json "$ENVDIR/a.json"
"$VHAUS" build houses/starter --only json
diff "$ENVDIR/a.json" houses/starter/out/model.json

echo "== ci_local.sh: the engine job passes from declared deps alone =="
[[ "$KEEP" == "1" ]] && echo "venv kept at $ENVDIR"
exit 0
