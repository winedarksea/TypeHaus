# Minnesota permit-set guide

`haus permit-check houses/catlin` is the pre-print gate for the M3 permit set. It reports
only the Minnesota residential subset the engine actually evaluates and returns a non-zero
exit code for a failure or an unknown result. `haus print` runs the same gate before it writes
the PDF or DXF sheets.

The current `mn-2024` profile checks:

- habitable-room and roof-following ceiling height;
- emergency escape openings for sleeping rooms;
- exterior egress-door clear width;
- smoke/CO alarm placement;
- resolved footing and detached-pad bases at the profile's 42-inch frost depth; and
- resolved-model errors and uncovered transition conditions.

The profile is intentionally a declared subset, not a claim of permit approval or code
compliance. Local amendments, site/setback data, loads and engineered headers, energy,
plumbing, mechanical, electrical, and final professional review remain outside this gate.
Those items remain visible in `haus check`; do not suppress or reinterpret them as passing
permit review.

Typical handoff sequence:

```bash
haus permit-check houses/catlin
haus print houses/catlin --handoff
```

Verify the emitted core IFC in the M3 target importer, Bonsai for Blender:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/verify_bonsai_import.py -- houses/catlin/out/handoff/model_core.ifc
```

The verifier requires imported walls, roofs, spaces, storeys, and Blender geometry; it does
not replace a professional's visual review of the drawing set.

The handoff bundle contains the permit PDF, per-plan DXFs, `model.json`, project brief, and
decision log. Core IFC is included when the optional `ifcopenshell` dependency is installed.

Furniture meshes remain house-local. For a `.glb`, `.gltf`, or `.dae` download, use
`haus import furniture <mesh> <house> --room <room-tag> --at-m x,y`. The importer converts
the asset to `furniture/meshes/*.glb`, records its derived footprint/height in
`furniture/imports.json`, and can place it immediately. Review mesh licensing before moving a
type into the shared library.
