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
"$VHAUS" print houses/catlin

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
