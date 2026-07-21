## Remaining Work
Still missing for full M2: variants/compare, full takeoff/BOM
The 3D UI builds geometry directly from model.json and renders furniture as boxes; it does not yet consume the planned glTF artifact ([Panel3D.tsx (line 7)](/Users/colincatlin/Documents-NoCloud/TypeHaus/ui/src/components/Panel3D.tsx:7)).
M3 details are incomplete: Catlin has transitions, but no authored detail Slices. The permit composer emits placeholder/generic sheets; S-100/S-101 are reused floor/energy views rather than complete foundation/framing sheets ([sheets.py (line 30)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/emit/draw/sheets.py:30)).
M3 site work is incomplete: no parcel/contour GeoJSON basemap support.
M3 equivalence is only hardcoded contract testing, not an actual old-IFC semantic comparison.
Catlin’s full checks still report two failures and 13 building-science UNKNOWNs. The declared permit-check passes only because it intentionally covers a narrow subset.
M5 is not acceptance-complete: condensation analysis lacks material permeance inputs, producing UNKNOWN results ([plans/50-m5-science.md (line 61)](/Users/colincatlin/Documents-NoCloud/TypeHaus/plans/50-m5-science.md:61)).
Emplace furniture (3d files from library or imported models) and able to move furniture. Ideally double click on an view/modify details as appropriate.
Need to be able to cleanly turn parts on/off in the 2d and 3d views, either by trade (ie plumbing on/off) or by role (ie hide the floors in the 3d model so we can see clearly stairway continuity across levels). Another toggle (defaults to on), is for the to 2d viewer of the house plan (ie catlin house) to clearly show the name of each room/area (or perhaps unique id if name is missing), such that a user can easily vibe code a change to that area with the text/id as a reference.

IFC openings (WP7 follow-ups): glTF core-LOD opening cutouts (windows/doors currently emit voids + fillings only in IFC, not the glTF core mesh); shared IfcWindowType/IfcDoorType so repeated openings reference one type rather than per-instance property sets.

French/double-swing doors now render in the 2D plan (PNG + UI) and are editable via a
click-to-open door settings popover (type, hinge/swing, position, sill height); the 3D
glTF/Panel3D view still cuts doors as plain void rectangles with no leaf panel geometry
(single or double) — see `emit/gltf/emitter.py:_add_wall`.

## Catlin detail parity — remaining

The fidelity bar is the five hand-authored reference details in
`/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/*_ifc.png`; the
scripts that draw them and the parameter dicts behind them are copied read-only into
`packages/engine/tests/fixtures/catlin_reference/` (see its README). Compare against
`houses/catlin/out/render/detail_*.png` after `haus render . --view details`.

Done so far: cavity fill lives on the structure layer (parallel-path R, no polygon overlap,
IfcMaterialLayerSet summing to true depth); the sauna is a real wall type; exterior walls
span floor-to-floor with framing stopping at the top plate; detail crops/scale/anchoring are
fixed; hatches fill by material; below-grade grade/soil/drain components are derived.

### Drawing vocabulary still missing

Each item names the reference drawing it comes from.

- **Flashings** — `basement_to_framed_wall_detail_ifc.png` (Z-flashing at the sill,
  L-flashing at the slab edge) and `roof_wall_eave_detail_ifc.png` (drip edge, apron).
  Port `_flashing`/`_path_from_steps` from the reference `detail_utils.py` into
  `emit/draw/detail_components.py` and derive them from the resolved faces, the way the
  grade/soil components already are. Supersedes the older "gutter/flashing profiles as
  detail-component symbols" note — they must be polyline+hatch, not `Symbol`, because
  `Symbol` renders as a bare circle in `DetailCanvas.tsx` and a marker in `pdf_writer.py`.
- **Box gutter and vent path** — `roof_wall_eave_detail_ifc.png`. The eave is zero-overhang
  with a box gutter; neither the gutter nor the ventilation path is drawn.
- **Insect screen, sill gasket, sealant beads, thermal-break wedge** —
  `basement_to_framed_wall_detail_ifc.png`. The reference params fix the sill gasket at
  1/4" and the slab thermal break at 1".
- **Sauna and garage details have no components at all** —
  `sauna_basement_wall_detail_ifc.png`, `sauna_shower_basement_detail_ifc.png`,
  `garage_wall_detail_side_ifc.png`. The sauna's benches, heater clearance, floor slope and
  drop ceiling are all in `saunashowerdetail.json` and none are drawn.
- **Birdsmouth seat-cut** so the eave rafter reads as a notched member (currently a straight
  raked bar), and **I-joist flange dashes** in section.

### Sheet composition (Phase 3d, not started)

- **Dimension strings.** `ArchDimension` nodes for what the reference dimensions — total CI,
  XPS layer count × thickness, footing width/depth, stud depth — derived from resolved layer
  thicknesses. Today a detail carries only the per-layer callout ladder.
- **Legend.** One swatch per distinct material in the scene with its resolved thickness,
  in a reserved band. Now that hatches carry `material`, the data is there.
- **Notes column.** `Transition.notes` points at `houses/catlin/notes/*.md` and only the
  *filename* reaches the drawing. Load, wrap and lay out in a right-hand column — port
  `load_markdown_notes`/`_wrap_notes` semantics from the reference `detail_utils.py`.
- **Title / attribution block** from `model.plan.project`.

### Model questions surfaced by the details

- **Which side of the basement wall is outdoors?** `W-B-S1`'s layers resolve
  interior→exterior as concrete (u −12"..0") then damp-proof and XPS (0"..4.05"), so the
  assembly puts the exterior insulation at *high* u — but `SL-M-DECK` also occupies high u,
  which would put the slab outdoors. One of the two is mirrored. The detail components read
  the exterior side off layer order and so follow the assembly, which is why the foundation
  detail currently draws soil over the slab edge. Answer: deck, balcony, and sunken garden are structurally separate concrete structure right next to the house. The deck/balcony/garden don't have insulation, are unconditioned outside, so interior doesn't matter.
- **French drain diameter has nowhere to live.** The reference fixes 4"
  (`basementconstruction.json`), but `FootingBedding` models drain tile as a bool.
  `detail_components.py` hardcodes the 4"/10"/8" drain and rock dimensions; they should come
  from the model once the fields exist.
- **`Transition.overlay` recipe ids are unused.** `zero-overhang-eave`,
  `basement-framed-wall`, `rim-band-air-seal`, `stack-width-shelf` etc. are authored in
  `houses/catlin/plan/transitions.py` and printed, but nothing dispatches components off
  them. That dispatch is how the per-detail vocabulary above should be wired.
- **Opening void lines run the full crop height** in details where the cut passes through a
  window (visible as long blue verticals in the foundation detail). They are inside the crop
  and dimensionally correct, but at detail scale a glazing centreline through the whole
  drawing reads as an error; the cut should show the actual jamb/head/sill instead.

### Editor

- Anchor-relative annotation drag → PatchOp editor; the v1 detail viewer is read-only.

### Framing follow-ups found while working on the above

- Most corners don't show proper 3-stud framing (it's defined in code but not present in
  most corners).

# Deferred TODO tasks
* clean import/export (so ship to another computer running this app)
* bypass libcst entirely for the mutation path for fully offline PWA (high risk, deferred)

Arches are missing on the balcony/porch concrete.
The current modeled concrete arches are:
2 arches per wall, on the north and south porch walls
Each opening: 8 ft wide × 8 ft high
Semicircular top: 4 ft radius
Straight vertical portion: 4 ft high
Outer concrete piers: 1 ft wide
Porch wall thickness: 12 in

## Current Orientation:
+X: east
+Y: north
+Z: vertical/up
will need to support rotating the house off axis in the future


