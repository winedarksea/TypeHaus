"""One-shot: pull the catlin-house reference detail parameters into test fixtures.

The reference drawings under ``catlin-house/catlin_house/*_ifc.py`` are IFC-driven: every
dimension they draw comes from a ``Pset_ifcPlot_*`` ``ParamsJSON`` property on the building.
Those parameter dicts — not the drawings — are the dimensional source of truth for parity.

Extracting them once and committing the JSON keeps the test suite independent of the other
repository (and of ifcopenshell being installed to run it).

Usage:
    PYTHONPATH=packages/engine/src .venv/bin/python \
        scripts/extract_catlin_reference_params.py [path/to/catlin_house.ifc]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_IFC = Path(
    "/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/catlin_house.ifc"
)
OUT_DIR = Path("packages/engine/tests/fixtures/catlin_reference")


def main(argv: list[str]) -> int:
    import ifcopenshell
    import ifcopenshell.util.element

    ifc_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_IFC
    if not ifc_path.exists():
        print(f"reference IFC not found: {ifc_path}", file=sys.stderr)
        return 1

    f = ifcopenshell.open(str(ifc_path))
    house = next((b for b in f.by_type("IfcBuilding") if b.Name == "House"), None)
    if house is None:
        print("no IfcBuilding named 'House' in the reference model", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, props in sorted(ifcopenshell.util.element.get_psets(house).items()):
        raw = props.get("ParamsJSON")
        if not raw:
            continue
        slug = name.replace("Pset_ifcPlot_", "").lower()
        path = OUT_DIR / f"{slug}.json"
        path.write_text(json.dumps(json.loads(raw), indent=2, sort_keys=True) + "\n")
        print(f"wrote {path}")
        written += 1
    if not written:
        print("no ParamsJSON psets found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
