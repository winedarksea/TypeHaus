"""Headless Bonsai import verification for a Type:Haus core-LOD IFC.

Run with Blender so the milestone handoff test exercises the actual target importer:

  Blender --background --python scripts/verify_bonsai_import.py -- out/handoff/model_core.ifc
"""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def main() -> None:
    if "--" not in sys.argv:
        raise SystemExit("usage: Blender --background --python verify_bonsai_import.py -- model.ifc")
    path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    if not path.is_file():
        raise SystemExit(f"IFC not found: {path}")

    # Blender's Extensions system can have Bonsai registered under an extension package
    # name before this script starts. Re-enabling it as the legacy ``bonsai`` add-on creates
    # a second module registration and corrupts the preferences lookup.
    if not hasattr(bpy.ops.bim, "load_project"):
        addon_utils.enable("bonsai", default_set=False, persistent=False)
    result = bpy.ops.bim.load_project(filepath=str(path))
    if "FINISHED" not in result:
        raise RuntimeError(f"Bonsai did not finish importing {path}: {result}")

    from bonsai.tool import Ifc

    ifc_file = Ifc.get()
    if ifc_file is None:
        raise RuntimeError("Bonsai import finished without an active IFC file")
    counts = {kind: len(ifc_file.by_type(kind)) for kind in (
        "IfcWall", "IfcRoof", "IfcSpace", "IfcBuildingStorey",
    )}
    if not all(counts.values()):
        raise RuntimeError(f"Bonsai import lost required core entities: {counts}")
    if not bpy.data.objects:
        raise RuntimeError("Bonsai import produced no Blender geometry")
    print(f"Bonsai import OK: {counts}; objects={len(bpy.data.objects)}")


if __name__ == "__main__":
    main()
