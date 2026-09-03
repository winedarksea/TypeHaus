#!/usr/bin/env python3
"""Diff a house's estimate between two git refs, section by section.

Written for the rebar back-out (``houses/catlin/notes/rebar_backout.md``), where the whole
question is whether a change moved exactly the money it was supposed to and none besides.
The acceptance condition that back-out has to meet is:

    Δconcrete + Δwall_structure + Δreinforcement ~= 0,  and every other section's Δ is 0.00

**The second clause is the real protection.** Any nonzero Δ elsewhere means the change
leaked — an assembly quietly re-grouped, a price key that stopped resolving, a BOM row that
moved between sections. A total that happens to land in the right place tells you nothing
about that.

Usage:

    scripts/price_delta.py <base-ref> [head-ref] [--house houses/catlin]

Both refs are checked out into throwaway git worktrees, so nothing touches the working tree
— which matters here, because this repo is routinely worked in by more than one session at
once and ``git stash`` is shared across worktrees.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _estimate(ref: str, house: str, python: Path) -> dict[str, float]:
    """``{section: subtotal}`` for ``house`` as of ``ref``, via a temporary worktree.

    ``PYTHONPATH`` is set to the worktree's own engine because the editable install's
    ``.pth`` is an ABSOLUTE path to the main checkout — without it the worktree's house is
    priced by the working tree's engine, which is the one comparison that proves nothing.
    """
    tmp = Path(tempfile.mkdtemp(prefix="price-delta-"))
    tree = tmp / "tree"
    subprocess.run(["git", "-C", str(REPO), "worktree", "add", "--detach", str(tree), ref],
                   check=True, capture_output=True)
    try:
        out = subprocess.run(
            [str(python), "-m", "typehaus.cli.app", "takeoff", house, "--json"],
            cwd=tree, check=True, capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin", "HOME": str(tmp),
                 "PYTHONPATH": str(tree / "packages" / "engine" / "src")})
        payload = json.loads(out.stdout)
        sections = (payload.get("cost_estimate") or {}).get("sections") or {}
        # Every rate is a LOW-HIGH band, so a section's subtotal is a band too. Both ends are
        # carried: a change that moves the low end and not the high one has still moved the
        # estimate, and a mid-point would hide exactly that.
        out_rows: dict[str, float] = {}
        for name, row in sections.items():
            subtotal = row.get("subtotal") or {}
            out_rows[f"{name}.low"] = float(subtotal.get("low") or 0.0)
            out_rows[f"{name}.high"] = float(subtotal.get("high") or 0.0)
        return out_rows
    finally:
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(tree)],
                       capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("head", nargs="?", default="HEAD")
    parser.add_argument("--house", default="houses/catlin")
    parser.add_argument("--allow", nargs="*", default=["concrete", "wall_structure",
                                                       "reinforcement"],
                        help="sections permitted to move; every other Δ must be 0.00")
    args = parser.parse_args()

    python = REPO / ".venv" / "bin" / "python"
    before = _estimate(args.base, args.house, python)
    after = _estimate(args.head, args.house, python)

    names = sorted(set(before) | set(after))
    leaked: list[str] = []
    allowed_delta = 0.0
    print(f"{'section':24} {'before':>12} {'after':>12} {'delta':>12}")
    for name in names:
        delta = after.get(name, 0.0) - before.get(name, 0.0)
        if abs(delta) < 0.005:
            continue
        print(f"{name:24} {before.get(name, 0.0):12,.2f} {after.get(name, 0.0):12,.2f} "
              f"{delta:12,.2f}")
        if name.rsplit(".", 1)[0] in args.allow:
            allowed_delta += delta
        else:
            leaked.append(name)

    print(f"\nsum of permitted deltas: {allowed_delta:,.2f}")
    if leaked:
        print(f"LEAKED — these sections moved and were not supposed to: {leaked}")
        return 1
    print("no section outside --allow moved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
