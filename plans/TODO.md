# Unorganized TODO tasks
* clean import/export (so ship to another computer running this app)
* UI contractor focused view toggles (ie concrete, framing, plumbing)
* bypass libcst entirely for the mutation path for fully offline PWA (high risk, deferred)
* needs a dark mode

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

Interior walls do not consider the roof slope for the sloped attic level ceiling.

Roof assembly still isn't showing on the 3d model.

Studs seem to go too high on the exterior walls, to the top level of the joists. It should instead be top plate, floor joists and rim joist, then sheathing (platform framing standard). In Catlin house, the first and second floor are 9' high with then another 12" nominal for the joist.

Some interior walls seem to be shown with a pink layer (insulation?), it is unclear why.

Catlin house stairs are supposed to be u-shaped from basement to main floor and main floor to second floor. U-shape stairs have a two landings in the split (separated by a single step themselves). This type of stair should be properly part of the stair designer (as should the right angle with winder which the attic stairs have, but which seems might be partly hacked on the side)

Most of the corners don't seem to show proper 3 stud framing (it's defined in code, but not present in most corners).

Some of the windows are too tall, headers going above the height of the ceiling (two in the garage stand out as examples, although it is hard to tell door vs window because the 2d floor plan does not show doors or windows elegantly)

Arches are missing on the balcony/porch concrete.
The current modeled concrete arches are:
2 arches per wall, on the north and south porch walls
Each opening: 8 ft wide × 8 ft high
Semicircular top: 4 ft radius
Straight vertical portion: 4 ft high
Outer concrete piers: 1 ft wide
Porch wall thickness: 12 in

