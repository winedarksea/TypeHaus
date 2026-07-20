# Unorganized TODO tasks
* clean import/export (so ship to another computer running this app)
* UI contractor focused view toggles (ie concrete, framing, plumbing)
* bypass libcst entirely for the mutation path for fully offline PWA (high risk)

/goal implement m3 of the plan. Note we've also added images of the floorplan for this design in @catlin_floorplan/ (JPG, PNG, SVG, DXF, all should reflect the same). These drawings are "close" but not quite perfectly in alignment on all dimensions. A reminder that the sunken garden / porch / balcony are all the same concrete arched structure that is right next to the house but freestanding, and the garage is also freestanding (porch / breezeway to it mounted on freestanding 6x6 posts) The main determinant of the outer dimensions was clear framing at 16" oc spacing (which should line up, structural studs, standing seam siding panels, i-joists for floors). Because we are going with exterior insulation, we don't need to pack insulation as critically into the corner, so a three stud or four stud corner (focused on high strength) is what we prefer. Note that for smaller windows, we prefer to align them so they evenly fall between the studs, and they can be resized slightly to fit the stud arrangment better:
Max (N-2) 14" window without breaking stud line (14" is tight but doable)
Max (N*2 - 6) 30" (non load bearing wall, one stud broken)
Max (N* 2 - 9) 27" (load bearing, jack studs added)

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
