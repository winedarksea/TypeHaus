# Main-floor exterior doors: structural-wall mounting

Design decision, 2026-10-24. Applies to **D-M-ENTRY** and **D-M-BALC** only.
Their door products, handing, rough openings and landings remain as authored.

The factory jambs anchor into the structural stud opening. The 3/8-inch plywood
outboard buck is a flashing substrate, not door anchorage or a threshold bearing.
The factory frame, leaf and hardware now share an explicit resolved placement;
the factory frame no longer impersonates a full-depth exterior jamb extension.
Until the factory jamb/hinge dimensions are documented, the frame is explicitly
schematic within the stud depth. This does not certify a factory jamb size.

Outboard of the factory frame, three **3/4-inch painted KDAT return boards** close
the two jambs and head through the exterior wall build-up. **3-1/2-inch face ×
3/4-inch thick painted KDAT casing** finishes the exterior perimeter in the existing
charcoal trim color. The head flashing clears this casing, including its thickness
and end laps. Interior extensions use painted finger-jointed pine where necessary.
These are separate measured boards in the trim takeoff, with cut dimensions and
material references; factory-included sill components are not billed again.

The interior LVP extends to the frame's interior edge until a documented threshold
provides the actual finish-stop and expansion-gap dimensions. Each side resolves
independently; an exterior deck needs no room or interior finish assignment.
The bounded exterior probe crosses the intentional drainage gap and reads actual
landing elevations rather than requiring the landing to equal the interior subfloor.
Sole plates obstructing a known floor-level passage are cut. Structural mudsills,
raised rough sills, bearing below the walking plane, and documented sill supports remain.

## Manufacturer research and remaining supplier information

**Therma-Tru:** design family selected: composite adjustable inswing sill.
The [2026 Comp 7 manual](https://outdoorsandsecurity.widen.net/content/6ybzlyty7g/original/2026-Arch-Comp-BOOK---COMP-7-Sills.pdf),
page 7.3, provides 4-9/16, 5-3/4 and 7-3/4-inch sections with a **1-1/2-inch
height plus 3/16-inch adjustment**. Page 7.10 documents extensions. These replace
the obsolete 2017 dimensions in earlier research, but do not identify the selected
installed sill/jamb/sweep combination. Needed: exact depth/extension selection,
installed dimensional section of substrate, approach, adjustable cap, mating sweep,
factory jamb depth/hinge position, finish-stop/expansion-gap locations and support contacts.
Use the applicable [installation manual](https://outdoorsandsecurity.widen.net/content/cjranjizwq/original/2026-Site-Manual---SITE-1-Installation.pdf)
for sealant and anchorage; do not generalize the garage note's back-dam-only sealant rule.

**Cascadia:** design family selected: high-performance inswing threshold.
The current [door download page](https://www.cascadiawindows.com/products/doors)
links [UW6 PDF, dated July 30, 2026](https://www.cascadiawindows.com/files/file/6a7e455007bf8/Door-Page---Profile--Install-Details-Inswing-Door-double--triple-glazed---20260813.pdf)
and [version 5 DWG library](https://www.cascadiawindows.com/files/file/6a7e43e438e0c/Cascadia-Windows---Detail-Library---Version-5---20260813.dwg).
The DWG was downloaded, converted with LibreDWG, and its UW6 layout inspected in
inch units. Its sill outlines are recoverable as research geometry, including the
`CW-DOOR SILL-FRAME` outlines. Neither the generic inswing layout nor its outlines
establish the ordered high-performance French pair's complete installed contract.
Needed: variant applicability to the triple-glazed pair, dimensioned factory frame,
leaf/sweep and jamb terminations, finished-floor stops, bearing/shim contact datums,
and the coordinated interior angle/beauty cap and drainage section. UW6 specifies
an angle 1-1/4 × 1-1/4 × 1/8 inch, shims at 8 inches o.c. and sill screws at
6 inches o.c., kept 3 inches from vertical frame members. Those installation notes
alone do not define an installed threshold model. Do not scale the N.T.S. PDF.

**Support and drainage:** the threshold needs manufacturer-required support tied to
the structure. The exterior approach also needs its own support; painted return
boards and the thin buck carry neither foot traffic nor the factory sill. Until
bearing and approach details are specified, these remain explicitly unresolved.
The pan starts behind the installed structural-wall frame and drains outward.
It must ultimately be concealed below the supported threshold and finished approach,
with the outlet open. No flashing is an acceptable horizontal walking finish.

## Model status and review

A documented section may generate design geometry before supplier order confirmation.
Section coordinates on this installation start at the factory frame’s interior face;
leaf-mounted seals follow the leaf, and transitions follow the interior finish joint.
`section_documented` records that evidence; `supplier_confirmed` records the separate
purchase confirmation. Doorway JSON/IFC expose section, supplier and fit statuses.
Missing geometry or installation data remains UNKNOWN; measured conflicts remain FAIL.
Existing `verified` section records retain their behavior for compatibility.

**Neither reported doorway passes finished-threshold visual acceptance yet.** The
placement, trim, flooring, sole-plate and head-flashing changes are modeled, but no
invented sill or unsupported approach is inserted to cover the remaining pan.

Reproduce actual sill/head/jamb cuts, JSON and optional framed IFC/glTF with:

```sh
.venv/bin/python scripts/review-exterior-doors.py --export
node ui/scripts/door-review.mjs --exterior
```

Artifacts, manufacturer PDFs/DWG, CAD inspection plots and validation logs are under
`out/exterior-door-review/`. The section plots and screenshots explicitly label the
unfinished threshold condition. The garage service raised rough sill, overhead door,
other French pairs and the outie window detail are not reinstalled by this change.

## Measured review, 2026-10-24

Elevations below use the main-floor datum. The 5-1/2-inch structural frame envelope
is schematic; it is not a documented factory jamb depth.

| Door | Interior finished floor | Exterior landing | Exterior return depth |
| --- | ---: | ---: | ---: |
| D-M-ENTRY | +0.9862 in | 0 in | 7.75 in |
| D-M-BALC | +0.9862 in | +0.9400 in | 7.75 in |

Each doorway has nine measured trim pieces: three exterior returns, three exterior
casing boards and three interior extensions. Cut schedules retain the 3/4-inch stock
thickness even where an interior extension's face width is narrower than that thickness.
The garage service door retains its raised framed sill; its support and the overhead
door operation were checked separately from the two reinstalled doors.

Validation artifacts are in `out/exterior-door-review/`:

- `focused-tests.log`: doorway, flashing, installation, trim/hardware pricing and
  fixture-discipline coverage: 1,321 passed, 20 skipped.
- `typecheck.log`, `ui-tests.log`: UI typechecking and geometry tests passed.
- `starter-checks.log`: 317 checks passed.
- `house-check.json`: Catlin has 2,116 PASS, zero FAIL, 104 UNKNOWN, 87 N/A and
  54 engineered findings. The two doors' missing factory data is UNKNOWN.
- `viewer-review.log`: nine close-up views generated with the production viewer builders,
  covering faces, jambs and floors in light, dark and schematic modes.
- `verify.log`: the standard gate was run; its engine stage initially reported
  9,413 PASS, 24 FAIL and 33 SKIP. Three failures caused by this change (the material
  default and hardware classification of trim) were corrected and their tests passed.
- `baseline-tests.log`: the same failing tests were rerun against an isolated clean HEAD;
  15 already fail there. Five further failures reproduce in the concurrent laundry-sink
  and kitchen-installation work (`other-failures.log`); an alarm-label failure from the
  full suite passes in isolation. Existing section/elevation golden failures
  also include intentional door geometry changes; unrelated geometry was not blessed.

The standard gate is therefore not green. Neither its unrelated failures nor zero
measured house failures establish visual acceptance for the unfinished thresholds.
