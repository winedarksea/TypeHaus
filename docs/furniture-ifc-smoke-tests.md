# Furniture and IFC handoff smoke tests

Run this checklist against the current installed Revit and SketchUp release before a
milestone handoff. Record the application build, operating system, TypeHaus commit, and
the generated IFC filename beside the results. The checks deliberately cover IFC as a
linked/reference exchange, not editable RVT/SKP source conversion.

## Prepare the fixture

1. From a clean Catlin checkout, generate IFC4 (`haus emit ifc houses/catlin`).
2. In the canvas, move one toilet, rehost one door or window, and move one catalog
   furniture object. Export a second IFC4 with the same project UUID.
3. Retain both files and the `haus diff` report. The unchanged export must have an empty
   substantive diff before starting either application check.

## Revit

1. In a new project, use **Insert → Link IFC** and choose origin-to-origin positioning.
2. Confirm walls, doors, windows, furniture, plumbing terminals, outlets/lights, air
   terminals, and mechanical proxies are visible in their mapped categories.
3. Inspect representative door/window/furniture/device properties: occurrence identity,
   shared type, and service-port children should be present; simplified objects are
   intentionally core solids rather than tessellated GLB geometry.
4. Reload the second IFC. Confirm the moved opening and placeables update in place rather
   than creating duplicate linked objects; record any broken Revit face references.
5. Save the Revit link log and screenshots of category/type/placement results.

Revit IFC links are reference content; Autodesk documents that reload uses IFC GUIDs to
match updated entities. See Autodesk’s [IFC linking guidance](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-Model/files/GUID-BAA2ED9C-5107-4F21-ABE1-1ACF609AEEE3.htm).

## SketchUp

1. Import the same IFC4 with the installed SketchUp IFC importer.
2. Confirm storey organization, wall/opening placement, furniture/fixture/device bodies,
   and product names/types in the generated hierarchy or entity information.
3. Check the moved opening and attached object are placed correctly relative to their wall
   faces; inspect a supply/return terminal and electrical device for simplified geometry.
4. Export IFC from SketchUp only when testing external reconciliation. Run `haus diff` on
   that file and verify expected move/type/property changes are reported without source
   mutation.
5. Save screenshots and the exported IFC with the run record.

SketchUp’s [IFC import/export documentation](https://help.sketchup.com/en/importing-and-exporting-ifc-files)
is the reference for release-specific import options.

## Pass criteria

- No application crash or dropped IFC relationship that prevents inspection.
- The first export produces zero substantive `haus diff` changes.
- Reload/re-import recognizes stable GUID identities for moved elements.
- Simplified physical bodies, semantic classes/types, storey containment, and TypeHaus
  identity property sets are inspectable for the sampled placeables.
