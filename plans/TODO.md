# Unorganized TODO tasks
* clean import/export (so ship to another computer running this app)
* UI contractor focused view toggles (ie concrete, framing, plumbing)
* bypass libcst entirely for the mutation path for fully offline PWA (high risk)

## Remaining Work
Still missing for full M2:
variants/compare, full takeoff/BOM, and Playwright acceptance tests.
The 3D UI builds geometry directly from model.json and renders furniture as boxes; it does not yet consume the planned glTF artifact ([Panel3D.tsx (line 7)](/Users/colincatlin/Documents-NoCloud/TypeHaus/ui/src/components/Panel3D.tsx:7)).
M3 details are incomplete: Catlin has transitions, but no authored detail Slices. The permit composer emits placeholder/generic sheets; S-100/S-101 are reused floor/energy views rather than complete foundation/framing sheets ([sheets.py (line 30)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/emit/draw/sheets.py:30)).
M3 site work is incomplete: no parcel/contour GeoJSON basemap support.
M3 equivalence is only hardcoded contract testing, not an actual old-IFC semantic comparison.
Catlin’s full checks still report two failures and 13 building-science UNKNOWNs. The declared permit-check passes only because it intentionally covers a narrow subset.
M5 is not acceptance-complete: condensation analysis lacks material permeance inputs, producing UNKNOWN results ([plans/50-m5-science.md (line 61)](/Users/colincatlin/Documents-NoCloud/TypeHaus/plans/50-m5-science.md:61)).
Emplace furniture (3d files from library or imported models) and able to move furniture. Ideally double click on an view/modify details as appropriate.
Need to be able to cleanly turn parts on/off in the 2d and 3d views, either by trade (ie plumbing on/off) or by role (ie hide the floors in the 3d model so we can see clearly stairway continuity across levels). Another toggle (defaults to on), is for the to 2d viewer of the house plan (ie catlin house) to clearly show the name of each room/area (or perhaps unique id if name is missing), such that a user can easily vibe code a change to that area with the text/id as a reference.

IFC openings (WP7 follow-ups): glTF core-LOD opening cutouts (windows/doors currently emit voids + fillings only in IFC, not the glTF core mesh); shared IfcWindowType/IfcDoorType so repeated openings reference one type rather than per-instance property sets.
Transition details (11b follow-ups): birdsmouth seat-cut so the eave rafter reads as a notched member (v1 draws a straight raked bar); gutter/flashing profiles as detail-component symbols; I-joist flange dashes; anchor-relative annotation drag→PatchOp editor (v1 detail viewer is read-only).

Attic level stairs have a bug with their winders. This was due to incorrectly asking for 2 winders, when really it should have been "as many as needed to get around 90 degrees" (probably 3). The current two trends are also incorrectly angled opposed to each other, another part of the bug.

Roof joists are badly angled
