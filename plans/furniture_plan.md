# Unified Canvas Objects, Furniture, Openings, and Interchange

## Summary

- Build one catalog, selection, drag, preview, inspector, and details framework for:
  - Doors, windows, and rough openings.
  - Furniture and appliances.
  - Plumbing fixtures.
  - Mechanical equipment and HVAC registers.
  - Electrical devices and lights.
- Preserve separate placement strategies:
  - `OpeningHosted`: doors/windows cut and fill a host wall.
  - `FreePlaced`: floor- or ceiling-positioned items.
  - `WallAttached`: explicitly locked items that track a resolved wall face.
- Use the 2D floorplan for editing and the 3D view for synchronized inspection/selection.
- Make IFC4 the semantic interchange format for Revit, SketchUp, Bonsai, and similar BIM tools. Use GLB/SVG for detailed visual assets.
- Support external IFC comparison and reconciliation reports, but do not attempt lossless RVT/SKP/IFC-to-TypeHaus source conversion.

## Models and Public Interfaces

- Introduce a normalized client contract:
  - `model.canvas_objects`: resolved doors, windows, furniture, fixtures, appliances, equipment, registers, and electrical devices.
  - `catalog.canvas_object_types`: all types that can be placed, grouped by domain and declaring their placement strategy.
  - Each object exposes UID/tag, domain kind, type, storey, room, host/attachment, transformed footprint, resolved height/mounting, visual representations, clearances, and service ports.
- Keep engine domain models distinct. Door/window topology, fixture drain overrides, electrical circuits, and duct references remain typed fields rather than generic metadata.
- Add common placeable value types:
  - `Footprint2D`: local physical-space polygon.
  - `ClearanceZone`: local polygon, purpose, source, and `required` or `recommended` policy.
  - `ServicePort`: stable tag, service kind, local XYZ point, optional connection size and notes.
  - `PlanRepresentation`: labeled shape or sanitized SVG.
  - `ModelRepresentation`: primitive or canonical GLB.
  - `Location`: free position/rotation or persistent wall attachment.
  - `Mount`: floor, wall, or ceiling with resolved elevation/drop.
- Add `Appliance`/`ApplianceType`; migrate the washer from plumbing fixture to appliance.
- Add typed catalogs for equipment, registers, and electrical devices. Extend `Service` with `power_120`, `supply_air`, and `return_air`; service filters derive from ports.
- Persistent wall attachments store host wall, left/right face relative to wall direction, distance from the start node, normal gap, and rotation offset. The resolver places the object’s footprint edge against the resolved finish face.
- Doors/windows retain `OpeningPosition`, host wall, sill, handing, swing, and opening relationships. They implement the shared canvas contract through `OpeningHosted`, not through the placeable wall-attachment model.
- Store project-local/imported types in revisioned `assets/placeables.json`; shared library types remain read-only. Catalog mutations participate in project hashing, file watching, conflict checks, undo, and redo.

## Unified Editing and Resolution

- Shared canvas controller:
  - One searchable, category-grouped palette for openings and placeables.
  - One selection/hover/highlight system and one sidebar/details shell.
  - Strategy adapters own geometry-specific preview and commit behavior.
  - Single-click selects; double-click opens the focused instance/type dialog.
  - Shared delete, duplicate, visibility, keyboard, provenance, and finding navigation behavior.
- Opening adapter:
  - Placement requires a compatible wall and previews the cut, swing, and framing bumper.
  - Dragging along the current wall updates `OpeningPosition`.
  - Dragging onto another wall previews and atomically commits rehosting when the opening fits.
  - Invalid host, insufficient wall length, framing conflicts, or unsupported geometry remain explicit findings/rejections.
  - Inspector edits type, along-wall position, sill, handing, swing, and host.
- Placeable adapter:
  - Dragging moves the object; a rotation handle and numeric field control rotation.
  - Rotation snaps to a configurable 15° increment, with a modifier for free rotation.
  - Dragging near a wall previews alignment but does not persist it. The inspector’s Attach action creates the durable wall relationship; Detach converts the resolved location back to free coordinates.
  - Floor-, wall-, and ceiling-mounted instances resolve consistently in 2D, 3D, and IFC.
- Room behavior:
  - Assign the room containing the footprint center after placement or drag.
  - Show and allow changing/clearing the assigned room in the inspector/dialog.
  - Warn when an explicit assignment does not contain the object.
  - When every boundary node of a room translates by the same delta, move the room seed and its free assigned objects in the same transaction.
  - A partial-boundary resize leaves free objects at project coordinates. Wall-attached objects follow their wall; newly outside objects receive orphan/mismatch findings.
- Clearance behavior:
  - Keep physical footprint, required clearance, and recommended use space distinct.
  - Rotate and transform true clearance polygons rather than axis-aligned envelopes.
  - Required/code conflicts produce errors; recommended/use conflicts produce warnings. Neither blocks dragging.
  - Code-derived zones—initially MN/IRC water-closet clearances—come from the active code profile.
  - Door swings and framing bumpers join the same resolved overlay/finding contract.
- Visual behavior:
  - 2D uses SVG when present, then labeled footprint fallback.
  - 3D uses GLB, then primitive, then footprint-box fallback.
  - All 3D objects support raycast selection and synchronized highlighting, but no direct 3D movement.
  - Trade visibility separates furniture, plumbing, electrical, and mechanical while reusing the common renderer.
  - Technical PDF/DXF output falls back to physical polygon plus label when arbitrary SVG cannot be represented safely.

## Asset Import and Interoperability

- Add a staged import flow:
  - Analyze without mutating the project.
  - Preview bounds, footprint, orientation, materials, and detected metadata.
  - Require confirmation of units, up-axis, rotation, and floor-centered origin.
  - Commit normalized, content-hashed GLB plus catalog metadata atomically.
- Accept:
  - Self-contained GLB.
  - Packaged/multi-file glTF and DAE.
  - Sanitized SVG plan symbols.
  - Single-object IFC extraction: choose one occurrence/type, extract its geometry/classification/properties/ports, create a project type, and normalize its display geometry to GLB.
- Do not directly ingest proprietary `.rvt`, `.rfa`, or `.skp`. Revit content enters through IFC export; SketchUp content enters through IFC, GLB, or DAE export.
- Preserve import provenance: source filename/format, content hash, IFC class/type GUID where present, original bounds, license/source note, and namespaced external properties.
- Re-importing matching content updates the project type/visual asset while preserving TypeHaus type tags and placed instance UIDs.
- Configure import limits centrally: 100 MB total, 20 files, and 30-minute staging expiry. Reject path traversal, active SVG content, unresolved dependencies, and external URLs.

### IFC4 export contract

- Emit stable occurrence `GlobalId`s from project UUID + element UID; moving, rotating, rehosting, or changing types does not change identity.
- Emit stable shared type objects and assign occurrences with `IfcRelDefinesByType`, including `IfcDoorType` and `IfcWindowType`.
- Preserve opening semantics with `IfcOpeningElement`, `IfcRelVoidsElement`, and `IfcRelFillsElement`.
- Map placeables through an allowlisted per-type IFC mapping:
  - Furniture → `IfcFurniture`.
  - Plumbing fixtures → `IfcSanitaryTerminal`.
  - Appliances → faithful standard class where available; otherwise an explicitly typed proxy.
  - Lights → `IfcLightFixture`.
  - Receptacles/panels → `IfcOutlet` or appropriate distribution class.
  - Registers → `IfcAirTerminal`.
  - Mechanical equipment → appropriate energy-conversion/distribution class, falling back to an identified proxy rather than a misleading class.
- Emit service ports as stable `IfcDistributionPort` children related to their occurrence. This establishes future pipe/duct/circuit endpoint identity without implementing route editing now.
- Use standard property sets where applicable plus a `TypeHaus_Identity` property set containing UID, tag, source type, and import provenance.
- Use SI units, explicit local placements, storey containment, project/site orientation, and georeferencing when site coordinates are available.
- Export simplified swept-solid/core bodies for predictable BIM import. Do not tessellate detailed GLB furniture into IFC; retain the GLB/source reference in metadata and the TypeHaus visual artifact.
- Extend `haus diff` to include openings and every placeable IFC class, matching by stable GUID first and geometry/type fallback second. Report add/delete/move/rotate/resize/rehost/type/property/port changes without automatically mutating TypeHaus source.

This aligns with current tool behavior: SketchUp supports IFC2x3/IFC4 and GLB exchange, while Revit supports IFC workflows but treats linked IFC as read-only and uses IFC GUIDs to update linked entities. [SketchUp IFC](https://help.sketchup.com/en/importing-and-exporting-ifc-files), [SketchUp GLB](https://help.sketchup.com/en/sketchup/working-gltf-files), [Revit IFC](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-6708CFD6-0AD7-461F-ADE8-6527423EC895.htm), [Revit IFC linking](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-Model/files/GUID-BAA2ED9C-5107-4F21-ABE1-1ACF609AEEE3.htm).

## Starter Content and Tests

- Add a small starter furniture set using `plans/furniture_size_reference.md`: standard sofa, queen-bed planning envelope, six-seat dining table, and writing desk.
- Add refrigerator, gas range, and electric range types to exercise water, gas, 120 V, and 240 V ports.
- Migrate toilet, lavatory, shower, washer, existing door/window types, receptacle, switch, light, panel, supply/return register, furnace, and water heater into the shared catalog contract.
- Give the dining table a recommended chair-use zone and the toilet a profile-derived required zone.

Test coverage:

- Verify each placement strategy, source/catalog round-trip, undo/redo, room translation/resize behavior, rotated clearances, wall-face attachment, and wall assembly thickness changes.
- Verify door/window move and cross-wall rehost preserve UID, recreate correct host relationships, and reject non-fitting placements.
- Test GLB/glTF/DAE/SVG/IFC analysis, normalization, dependency handling, path security, limits, expiry, deduplication, re-import, and atomic rollback.
- Validate IFC4 schema, type assignments, opening relationships, storey containment, property sets, port relationships, and stable GUIDs with IfcOpenShell.
- Require a zero-change self-diff after TypeHaus IFC export and test generated external changes for every reconciliation category.
- Add UI integration coverage for the unified palette, strategy dispatch, selection, drag/rotate, room reassignment, attach/detach, opening rehost, type editing, clearances, filters, and 3D fallbacks.
- Add documented manual smoke tests in current Revit and SketchUp versions: open/link the IFC, verify categories/types/placement, reload a moved-element export by GUID, and verify the simplified furniture/device bodies.
- End-to-end Catlin acceptance: move/rehost an opening, move a toilet, place a table, translate then resize its room, attach an object to a wall and change wall thickness, place electrical/HVAC devices, import one GLB and one single-object IFC asset, and reconcile an externally modified IFC.

## Assumptions

- Doors/windows share interaction infrastructure but retain wall-cutting domain semantics.
- Editing remains 2D-only; 3D supports inspection and selection.
- Pipe/duct paths, sleeves, alarms, circuits, and automatic routing remain future tools.
- IFC4 is the supported semantic handoff format; IFC2x3 export is not added in this milestone.
- External IFC can be compared or imported as an individual catalog asset, but whole-building editable IFC import and automatic reverse-merge are out of scope.
- Detailed visual fidelity belongs in GLB/SVG; IFC prioritizes semantic class, type, placement, relationships, ports, and robust core geometry.
