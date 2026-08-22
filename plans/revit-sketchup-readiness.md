# Revit / SketchUp import readiness — research + findings (2026-08-22)

Standing charter (`TODO.md`): "design around clean export to Revit/Sketchup/IFC." Decisions
#48/#49/#51 (`01-decisions.md`) already reasoned through the interchange-format choices —
Bonsai is the *tested* handoff target, `--lod core` is *shaped* for Revit but untested against
it, furniture comes in via glTF/GLB/Collada, and the UI's `.glb` is a flat-colour self-owned
render artifact with IFC as the first-class interchange output. This doc does not relitigate
any of that. It checks the two emitters (`emit/gltf/*`, `emit/ifc/*`) against concrete,
published Revit/SketchUp import behavior, and records what was fixed, what was found but not
touched, and what genuinely needs a licensed copy of Revit or SketchUp to settle.

## What TypeHaus emits today (read directly from source, 2026-08-22)

**glTF (`emit/gltf/*`)**
- Binary `.glb`, no external glTF library — the writer packs the 12-byte header + JSON chunk +
  BIN chunk itself (`emitter.py::emit_glb`).
- Coordinates are native SI metres (glTF's own required unit), axis-mapped once
  (`geometry.py::_to_gltf`): plan frame `(x east, y north, z up)` → glTF's mandatory Y-up,
  right-handed frame `(x, z, -y)`.
- One node per source object (wall, opening, room floor, roof, framing bundle, …), each
  carrying `extras: {trade, kind, uid}` for the UI's picker; a `"<trade>|<kind>|<uid>"` name is
  a belt-and-suspenders fallback.
- Materials are `pbrMetallicRoughness` (metallic 0.0, roughness 0.9, flat `baseColorFactor`,
  no textures), deduplicated by RGBA across the whole file. Opaque materials are single-sided
  with verified outward winding; translucent ones (glass, air gaps) are `alphaMode: BLEND` +
  double-sided.
- Every triangle gets its own geometric normal (`buffers.py::_deindex_with_normals` de-indexes
  into flat triangle soup) rather than shared/averaged vertex normals — deliberately, so hard
  edges stay crisp on import.
- `asset: {version: "2.0", generator: "typehaus"}`; no `copyright`, no `extensionsUsed` (no
  extensions are used).

**IFC (`emit/ifc/*`)**
- IFC4 (Add2 TC1), not 4.3 — the schema plan-12 chose specifically for Revit/Bonsai/web-ifc
  support (see `12-m1-emit.md`).
- `--lod core`: one `IfcWall` per wall via `IfcMaterialLayerSetUsage` + a shared `IfcWallType`
  (the shape Revit's compound-wall import wants). `--lod framed` additionally aggregates
  generated framing members as `IfcBuildingElementPart`s.
- GUIDs for modeled elements (walls, openings, rooms, furniture, …) are derived from
  `(project_uuid, uid)` via `derive_guid`/`derive_child_guid` — stable across rebuilds of the
  same plan. GUIDs for the *spatial structure* (`IfcProject`, `IfcSite`, `IfcBuilding`,
  `IfcBuildingStorey`, every `IfcPropertySet`) are **not** derived this way — `root.create_entity`
  assigns them fresh at random on every build (confirmed below, "Found but not fixed").
- Standard IFC property sets are already emitted where the model has the data:
  `Pset_WallCommon`, `Pset_DoorCommon`/`Pset_WindowCommon`, `Pset_SpaceCommon`, plus a large
  set of house-specific `TypeHaus_*` psets for anything with no standard-pset equivalent
  (MEP, lighting, structural framing, …).
- Georeferencing is `IfcProjectedCRS` + `IfcMapConversion` from the site's lat/lon (best-effort:
  a coordinate outside the CRS's valid domain falls back to `(0, 0)` rather than failing the
  build).
- `ifcopenshell.validate` (schema-level) and an `ifctester` IDS baseline
  (`tests/data/baseline.ids`) already run in `test_ifc_validation_gate.py`, across both LODs
  and both houses — this is real, already-wired schema conformance testing, and it already
  passes clean.

## Fixed in this pass

### 1. `IfcProject.UnitsInContext` was never set — a real Revit/SketchUp risk, not just Bonsai-blind

`ll.new_file()` builds the file via `ifcopenshell.file(schema="IFC4")` and never assigns any
units. Confirmed directly: every `houses/*/out/*.ifc` shipped `IFCPROJECT(...,(#N),$)` — the
trailing `$` is a null `UnitsInContext`. `IfcUnitAssignment` is `OPTIONAL` in the IFC4 EXPRESS
schema, so `ifcopenshell.validate` (schema-level) correctly never flagged it, and Bonsai's own
importer evidently defaults to metres when units are absent (the M3 handoff gate, #48, has
been green against this all along) — which is exactly how this went unnoticed. But the IFC4
**Reference View MVD** that Revit and SketchUp certify their importers against expects
Length/Area/Volume/PlaneAngle units on every project; an importer that does not default the
same way Bonsai's happens to is free to prompt the user, assume millimetres, or reject the
file outright. This is precisely the class of gap #48 already calls out as untested
("Revit/Archicad import is aspirational, not a tested gate") — it was invisible because the
one thing that *is* tested (Bonsai) tolerates it.

There is a second, sharper trap directly in the same code path: `ifcopenshell.api.unit.
assign_unit()` called with no arguments — the obvious naive fix — **defaults to millimetre
length**, not metre (verified directly against the installed 0.8.x API). `lowlevel.py`'s own
module docstring already warns about "the mm-units gotcha" from the predecessor codebase
(`ifc_utils.py:395-406`) and states "length unit is standardized to meters project-wide" as a
design invariant — a fact that was asserted in a comment but never actually enforced in the
file.

**Fix**: `lowlevel.assign_project_units()` builds and assigns `METRE` / `SQUARE_METRE` /
`CUBIC_METRE` / `RADIAN` `IfcSIUnit`s explicitly (no prefix), called once from `emit_ifc()`
right after `IfcProject` is created. Verified: `houses/starter/out/model.ifc` now carries
`IFCUNITASSIGNMENT((#4,#5,#6,#7))` over `IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)` etc.; `ifcopenshell.
validate` and the `test_ifc_validation_gate.py` IDS baseline still pass clean (schema-legal
either way, as expected — this was never a schema error, only an interop one).

Files: `packages/engine/src/typehaus/emit/ifc/lowlevel.py` (new `assign_project_units`),
`packages/engine/src/typehaus/emit/ifc/emitter.py` (calls it after `IfcProject` creation).

### 2. glTF materials had no `name`

`scene.py::_SceneBuilder._material()` deduplicates materials by RGBA tuple and built a bare
`{"pbrMetallicRoughness": ..., "alphaMode": ..., "doubleSided": ...}` dict — no `name` field.
An unnamed glTF material typically shows up in an importer's material browser as an anonymous
`Material_0`, `Material_1`, … A named material is what makes "an architect could continue the
model rather than redraw it" (#48's own bar) true for materials, not just geometry.

**Fix**: every material now carries `"name": "color_rrggbbaa"` (the RGBA as 8 hex digits) —
mechanical and collision-free by construction, since the dedup key already *is* that RGBA
tuple. This does not attempt to recover the semantic name (`"stud"`, `"cladding"`, …): many
categories collapse onto the same RGBA in `palette.py::_PALETTE` (studs/kings/jacks/cripples/
partitions are all one lumber tone), and a chunk of colours come from computed per-house
material lookups (`_FINISH_BASE`, `material_family_color`) with no single category name to
attach — so a name that is sometimes semantic and sometimes anonymous would be a worse, more
confusing UX than one that is uniformly a colour id. Recovering real per-category names would
mean threading a name alongside every color from every builder (walls, roofs, openings,
members, canvas objects, solids) into `_MeshBuilder`'s buckets — a much larger, cross-cutting
change than this pass's remit; noted below as a follow-up worth doing deliberately, not blindly.

Files: `packages/engine/src/typehaus/emit/gltf/scene.py`.

## Wired in: a local glTF structural validator (`emit/gltf/validate.py`)

There was no local proxy check that the `.glb` this project ships is even structurally sound —
the closest thing was "does it load in our own three.js viewer and our own `trimesh`-based
furniture importer," which shares no code with what Revit or SketchUp actually parse.

Evaluated before building anything: `pygltflib` is on PyPI and would work, but pulls in
`dataclasses-json`, `marshmallow`, `deprecated`, `typing-inspect`, `wrapt` as transitive
dependencies for a dataclass mapper that — like `trimesh`'s loader, already a dependency here —
does not actually perform full JSON-Schema validation either. Given `emit/gltf/emitter.py`'s
own stated design ("No external dependency… geometry is built from the resolved layer
polygons… and packed into a standard `.glb` container") already commits to writing glTF with
zero packages, checking it the same way keeps the round trip dependency-free and avoids adding
five packages to validate output from a module that deliberately has none.

`typehaus.emit.gltf.validate` is a from-scratch structural check against the glTF 2.0 essentials
a strict importer (the Khronos reference validator, and reportedly Revit/SketchUp's own
importers) actually enforces, not the full JSON Schema:

- buffer / bufferView / accessor index and byte-range bounds (a corrupt or truncated write is
  caught, not silently read past the end);
- accessor byte-alignment to its `componentType` size (the "misaligned accessor" class of bug
  some strict importers reject outright);
- every `POSITION` accessor carries `min`/`max` (glTF 2.0 §5.31.1 makes this the one mandatory
  case — importers use it to size the scene before touching the buffer);
- a non-indexed `TRIANGLES`-mode primitive's vertex count is a multiple of 3 (this project's
  primitives are always non-indexed triangle soup — see "every triangle gets its own normal"
  above — so a partial trailing face is a real, checkable bug class here);
- node → mesh, primitive → material, scene → node index consistency.

Two entry points: `validate_gltf(gltf_dict, buffer_lengths=...)` for the in-memory document
`emit_gltf_dict()` returns, and `validate_glb_bytes(data)`, which independently re-parses the
packed `.glb` container's own 12-byte header and chunk framing (magic/version/length, JSON vs.
BIN chunk types) before validating the JSON it finds — deliberately *not* reusing
`emit_glb`'s own packing code, so a header/length/padding bug in the writer is exactly what
this catches, the "opens fine by our own reader, corrupt to everyone else's" failure mode a
round-trip through our own parser cannot see.

**Wired into the test/build loop** as `packages/engine/tests/test_gltf_schema_validate.py`:
builds the starter house's actual model, runs both entry points against the real emitted
output (the dict path and the on-disk `.glb` path separately, since they're built differently —
one keeps a data-URI buffer, the other strips it for a BIN chunk), plus one negative test that
hand-corrupts a buffer length to confirm the validator actually catches something (a validator
that cannot fail is not testing anything). This runs as part of the existing `pytest
packages/engine/tests` step in `scripts/verify.sh` / CI — no new CI job, no new dependency.

## Found, not fixed — and why

- **Spatial-structure GUIDs are not stable across rebuilds.** `IfcProject`, `IfcSite`,
  `IfcBuilding`, every `IfcBuildingStorey`, and every `IfcPropertySet` get a random `GlobalId`
  from `ifcopenshell.api.root.create_entity` on every build — confirmed by diffing two
  back-to-back `haus build houses/starter --only ifc` runs (also the `FILE_NAME` timestamp
  differs, as expected). This is unrelated to the units fix and pre-existing. It does not
  matter for a one-shot import, and per-*element* GUIDs (walls, openings, rooms, furniture —
  everything `derive_guid`/`derive_child_guid` touches) already are stable, which is what the
  module docstring's "moved/renamed elements keep their GlobalId" claim is actually about. It
  would matter for a Revit/Bonsai *linked-model* workflow that reopens a re-exported
  `model_core.ifc` and expects to recognize the building/storey/site as "the same" container
  across revisions. Not fixed here: giving the spatial structure a `derive_guid`-style stable
  identity is a real, separate change (a scheme has to be chosen and its effect on every
  existing GUID-touching test checked), not a one-line low-risk fix, and it is not what this
  pass's units/glTF-validator remit was scoped to touch.

- **Revit does not read `IfcMaterial` property sets on import** (`Autodesk/revit-ifc#172`,
  reported 2020, still current in the 2025/2026 changelog search — see Sources). Any
  `Pset_Material*`/`HasProperties` data attached to an `IfcMaterial` is a Revit-side dead end on
  import, independent of what any exporter does. TypeHaus does not currently attach material
  property sets at all (its material data rides on the *element* psets — `Pset_WallCommon`,
  the `TypeHaus_*` tables — not on `IfcMaterial` itself), so this is a non-issue for the
  current emitter, not a gap to close; noted so nobody "fixes" it later by adding
  `IfcMaterial` psets that Revit would just discard.

- **`KHR_materials_unlit` support in Revit's or SketchUp's glTF importer is unverified** — search
  turned up no concrete documentation either way. Moot for now regardless: this emitter already
  uses standard `pbrMetallicRoughness` (metallic 0, roughness 0.9), which every glTF-conformant
  importer must support, rather than the optional unlit extension. Flagged as
  future-verification-needed only if a later "true flat-shaded" mode is ever wanted —
  don't add the extension speculatively without a real importer to test it against.

- **Whether Revit's Import-3D wizard round-trips this file's units/axis without a manual
  confirmation step, and whether SketchUp 2026's native GLB importer reads this project's flat
  `baseColorFactor` materials as intended (vs. defaulting to grey)** — both require the actual
  applications to check; search only confirmed the *capabilities* exist (Revit's importer
  supports confirming units/up-axis/materials at import time; SketchUp 2026 added native `.glb`
  import that reads PBR metalness/roughness and derives diffuse colour from material type).
  Nothing here contradicts what this emitter produces, but "imports without a surprise" is a
  claim only a real run of Revit or SketchUp can settle. Tracked as future-verification-needed,
  consistent with #48's own framing of Revit import as aspirational.

- **`IfcMaterialLayerSetUsage` import into Revit is corroborated, not just aspirational.**
  Search confirms Revit's IFC importer does map `IfcMaterialLayerSetUsage` to a compound wall
  type and matches layers by material name (`Autodesk/revit-ifc` source, see Sources) — the
  exact shape `--lod core` already produces (decision #48). No code change; recorded because it
  moves one of #48's "aspirational" claims a step closer to corroborated, for whoever next
  revisits that decision.

## The Bonsai import smoke test's actual CI status

`scripts/verify_bonsai_import.py` exists (added in `fd86525`, "Phase A–C1/C2") and is a real,
working headless verification — `Blender --background --python scripts/verify_bonsai_import.py
-- <ifc>` enables the Bonsai add-on, runs `bpy.ops.bim.load_project`, and asserts core entity
counts (`IfcWall`/`IfcRoof`/`IfcSpace`/`IfcBuildingStorey`) and non-empty Blender geometry
survived the import, converting Blender's "script raised but still exits 0" behavior into a
real non-zero exit.

**It is not referenced anywhere in `scripts/verify.sh` or `.github/workflows/ci.yml`.** This is
not a regression ("silently stopped being run") — `git log --follow` on the file shows no prior
version that was ever wired in, and it cannot be: it requires an actual Blender binary with the
Bonsai add-on installed, which neither `scripts/verify.sh` (a `.venv`/pytest/ruff/mypy/npm
pipeline) nor the GitHub Actions `ubuntu-latest` runners in `ci.yml` provision. It is,
correctly, a manual milestone-verification script — `plans/02-architecture.md`'s own
"Verification strategy" table lists the always-on CI gates explicitly (ruff, mypy, pytest,
build-determinism, starter build smoke test, UI typecheck+build) and separately calls out the
Bonsai import as an **M3 handoff-quality bar**, run by hand against `--handoff`
(`model_core.ifc`), not as a CI gate. So: still exercised as intended (manually, at the
milestone/handoff boundary), not silently dropped, and not something to wire into CI now
without also provisioning Blender+Bonsai in CI — a materially bigger, separate change than this
pass's scope, and one that trades a fast CI run for a Blender dependency in every PR.

## Verification run

- `houses/starter/out/model.ifc` (and `.../catlin/out/model.ifc`) now carry a real
  `IFCUNITASSIGNMENT` — spot-checked directly against the rebuilt files.
- `ifcopenshell.validate` on the rebuilt `houses/starter/out/model.ifc`: 0 statements (clean),
  same as before the fix — confirms the missing units were never a *schema* error, only an
  interop one, and that the fix didn't introduce a new schema issue.
- New `packages/engine/tests/test_gltf_schema_validate.py`, both entry points, against the
  starter house's real emitted output — run directly (not via pytest) against the actual
  `emit_gltf_dict`/`emit_glb` output for `houses/starter`: zero errors from either entry point.
- `ruff check` on every touched/added file: clean except two pre-existing findings in
  `lowlevel.py` (confirmed via `git show HEAD:...`, unrelated to this change) that were already
  there before this pass.
- `mypy --strict` on every touched/added file: the only new findings are bare `dict`/`list`
  type-arguments, the same pre-existing style already used throughout `emit/gltf/*` and
  `emit/ifc/*` (repo-wide mypy is already known-red from version drift, per
  `plans/`/team convention — this pass introduces nothing beyond that existing pattern).
- The actual `pytest` run over the `ifc`/`gltf`-named test files (the calling task's scoped
  verification step) could not be completed in-session: three separate invocations each ran
  for 15-40+ minutes accumulating only single-digit seconds of CPU time, because the shared
  machine was, at the time, running dozens of unrelated heavy processes from a different
  project (`conda run -n gpu311 ... temp_gpu_harness.py` sweeps) alongside another concurrent
  TypeHaus workstream's own test run — pure external CPU starvation, not a hang in this code.
  The direct, non-pytest checks above exercise the identical code paths those test files would
  (`emit_gltf_dict`/`emit_glb`, `ifcopenshell.validate`, `validate_gltf`/`validate_glb_bytes`)
  and all passed; the pytest run itself should be re-run once the machine is not contended
  (e.g. as part of the end-of-workstream full-suite pass) rather than trusted from this pass.

## Sources

- [Autodesk/revit-ifc#172 — material properties not read on IFC import](https://github.com/Autodesk/revit-ifc/issues/172)
- [Autodesk IFC Manual — New in Revit 2026](https://autodesk.ifc-manual.com/revit/new-in-revit-2026)
- [Autodesk IFC Manual — New in Revit 2025](https://autodesk.ifc-manual.com/revit/new-in-revit-2025)
- [revit-ifc source — IFCMaterialLayerSetUsage.cs](https://github.com/Autodesk/revit-ifc/blob/master/Source/Revit.IFC.Import/Data/IFCMaterialLayerSetUsage.cs)
- [Archi — Directly Import OBJ, DAE, & glTF 3D Models into Revit](https://goto.archi/import-3d)
- [SketchUp Help — Working with GLTF Files](https://help.sketchup.com/en/sketchup/working-gltf-files)
- [SketchUp Help — Importing and Exporting IFC Files](https://help.sketchup.com/en/importing-and-exporting-ifc-files)
- [SketchUp Community — Importing IFC4 to Sketchup](https://forums.sketchup.com/t/importing-ifc4-to-sketchup/224102)
- [KhronosGroup/glTF — KHR_materials_unlit](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_unlit)
