# Doorway product sections — research and supplier register

Reviewed 2026-10-23. Authored opening/landing elevations remain fixed. An ordered door
line is not approval of a particular sill. The `doorway` records in `plan/door_types.py`
are deliberately **unverified** and contain no polygons. UNKNOWN is the correct result
until the supplier identifies the installed variant, dimensioned section and revision.
Factory sills and kit components are included in the door/kit price, not separate BOM items.

| Opening/product | Verified source information | Supplier question / unresolved dimensions |
|---|---|---|
| D-M-ENTRY, opaque Therma-Tru Smooth-Star, inswing | [Manufacturer sill catalog](https://store.thermatru.com/collections/sills) lists adjustable composite, basic fixed, public access, outswing and other distinct systems. The [composite adjustable product](https://store.thermatru.com/products/composite-adjustable-sill) describes composite substrate/cap, aluminum approach and vertical adjustment. | Which exact sill, cap, depth, extension and sweep is in the quote? Supply section showing seat, walking crest, leaf clearance, adjustment range and exterior direction. Catalog size choices are not approval of an installed section. No height or sloped outline is inferred. |
| Cascadia Universal inswing French pairs | [Manufacturer door page](https://www.cascadiawindows.com/products/doors) offers high-performance and low-profile thresholds. Its current [inswing section download](https://www.cascadiawindows.com/files/file/6a7e455007bf8/Door-Page---Profile--Install-Details-Inswing-Door-double--triple-glazed---20260813.pdf), UW6, drawing dated July 30, 2026, detail 2, shows the sill and continuous aluminum angle. The angle is dimensioned 1-1/4 × 1-1/4 × 1/8 in; shims 8 in o.c.; sill screws 6 in o.c., 3 in away from vertical members. These are published installation dimensions, not a digitized full sill profile. | Confirm high-performance versus low-profile, pair configuration/label, applicability of UW6 to the triple-glazed order, optional beauty cap and installed interior/exterior direction. Supply exact sill cross-section and support/heel/walking datums. The exterior seal/drainage path and the sill angle must be coordinated with the modeled pan, not substituted for one another. |
| D-G-SERVICE, Masonite flush steel, outswing | [Masonite terminology](https://www.masonite.com/discover-and-learn/door-buying-key-terms/) distinguishes a particular Performance Door System with a self-adjusting sill. That does not establish the commodity prehung unit's outswing sill. | Identify the prehanger, SKU, outswing sill manufacturer/variant, depth and extension. Supply dimensioned section, seal, supported floor-height range and orientation. Retain the raised rough sill and its support. Do not reverse an inswing sill to approximate this product. |
| Clopay Modern Steel Intellicore | [Manufacturer construction description](https://www.clopaydoor.com/residential-garage-doors/modern-steel-collection) identifies a replaceable vinyl bottom seal in an aluminum retainer. It is carried by the door, not a floor threshold. | Supply the selected bottom section/retainer and seal part numbers, installed/compressed section, slab contact datum and clearances. No pan or spanning floor track is inferred from overhead operation. |

The UW6 sheet has been inspected directly, including its dimension callouts. Its sill
profile contains multiple hollow extrusions and seals. A bounding rectangle or a traced
silhouette with assumed wall thicknesses would not be a verified section, so none is
entered in the geometry catalog. The older 2020 D-1.01 dual-glazed drawing is not silently
used for the current triple-glazed pair.

## Interior flooring and transitions

Choose the actual flooring manufacturer's matching trim first. Catlin's generic finish
material references and thicknesses do not identify an orderable matching reducer or its
expansion requirements. Obtain flooring SKU, underlayment, transition SKU, installed
cross-section, compatible substrates and documented expansion gaps for every changed
finish pair at a doorway.

The [Schluter same-height families](https://www.schluter.com/schluter-us/en_US/Profiles/For-Floors/Same-height-Transitions/c/P-FF-SHT)
are candidates, not automatic substitutes for floating-floor trim. For a tile-to-lower-floor
condition, investigate [RENO-U](https://www.schluter.com/schluter-us/en_US/Profiles/For-Floors/Sloped-Transitions/Schluter-RENO-U/p/EU175)
and its [floor-profile data sheet](https://assets.schluter.com/asset/570120892212/document_fkpq5q8afd67l9f4unaspal14b/floor-profiles-data-sheet-pdf.pdf?content-disposition=inline).
Height selection must include membranes above the anchoring leg. A nominal profile height
alone does not establish floor compatibility or the installed reducer geometry. No Schluter
profile is selected for Catlin until these questions are answered.

## Implemented model contract

`DoorType.doorway` supplies defaults; `Door.doorway` replaces the treatment explicitly.
`floor_treatment="continuous"` asserts matching known finishes and elevations. Otherwise
actual adjacent walking surfaces, including finish zones, decide continuity. Differing
finishes meet beneath the closed leaf. A documented transition reserves its footprint and
its two expansion gaps in the shared finish polygons and takeoff area.

Verified multipart sections use metres `(normal, height)` and an explicit installed normal
sign, datum and offset. Floor profiles also require documented finish-stop positions and
floor contact planes; overlapping cap wings do not remove the flooring underneath them.
Exterior sill fit requires the published leaf/jamb terminations and bearing contact points. They are swept identically into viewer, glTF and IFC. Sill, track,
guide, leaf seal and floor transition are separate roles. Missing section/compatibility/
floor information is UNKNOWN; measured fit conflicts are FAIL. Guides and seals require
an explicit span; door operation never invents a floor-spanning section.

The generic bottom frame and assumed slider track are omitted. A plate above a known
walking surface is interrupted across the passage unless it carries the documented sill;
structural mudsills, support below the floor and raised rough sills remain. If the adjacent
floor is unknown, potential support remains and the assembly reports UNKNOWN. The pan
coordinator checks the documented sill against existing back dam, support, membrane,
width and outlet; it reports conflicts instead of moving the authored installation.

Remaining supplier work: all four exterior sections above, matching interior transition
SKUs, documented pocket/bifold/bypass guide variants, and continuous bearing/shim details.

## Validation record

The full standard gate completed with 9,191 passes, 68 failures and 32 skips. All 68
remaining failures also fail in an isolated baseline checkout containing the workspace
changes that predated the doorway work; no new failure identity remains in that gate.
The baseline comparison initially identified nine doorway regressions, which were fixed
and covered by the focused regression suite (209 passing tests, including 40 synthetic
doorway cases). Starter checks pass (316), the Catlin
strict check reports zero FAIL findings, and UI typechecking/geometry tests pass.

Native IFC and glTF plus six sections are generated under `out/doorway-review/`.
`catlin-doorway-sections.png` uses the actual resolved solids for the mudroom, bath 2,
entry, balcony, garage service and overhead openings. The live viewer's mudroom/laundry
floor and jamb views were inspected in light, dark and schematic modes. Synthetic
fixtures verify sloped and mirrored section vertices, IFC tessellation, reducer contacts,
finish-stop overlaps, pan bearing/drainage conflicts and purchasing quantities. Supplier
submittals above remain open; the model does not fabricate their missing sections.
