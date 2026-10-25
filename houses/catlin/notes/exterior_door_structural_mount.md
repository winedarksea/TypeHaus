# Main-floor exterior doors: structural-wall mounting

Design decision, 2026-10-24. Applies to **D-M-ENTRY** and **D-M-BALC** only.
Their door products, handing, rough openings and landings remain as authored.

The factory jambs anchor into the structural stud opening. The 3/8-inch plywood
outboard buck is a flashing substrate, not door anchorage or a threshold bearing.
The factory frame, leaf and hardware now share an explicit resolved placement;
the factory frame no longer impersonates a full-depth exterior jamb extension.
Until the factory jamb/hinge dimensions are documented, the frame is explicitly
schematic within the stud depth. This does not certify a factory jamb size.

Outboard of the factory frame, three **3/4-inch KDAT return substrates** close
the two jambs and head through the exterior wall build-up. **3-1/2-inch face ×
3/4-inch thick KDAT casing substrates** finish the exterior perimeter. Owner selected
**charcoal PVDF steel over wood**, matching the house trim. The model separates the
0.024-inch steel skins from the 0.020-inch isolation membrane and the wood beneath;
the casing jambs also have outer edge returns. These are finish skins, not factory
jambs or structural threshold plates. The head flashing clears the complete wrapped
casing, including its thickness and end laps. Interior extensions use painted pine.
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

**French pairs: Therma-Tru Smooth-Star / Endura ZAI (2026-10-25).**
The [ZAI product page](https://www.enduraproducts.com/adjustable-door-sills-2/) and
[Z-Series Sill Options](https://marketing.poweredbyendura.com/hubfs/Sills_TechnicalDocuments/Z-Series%20Sills%20-%20Line%20Drawings.pdf),
p.5, publish ZAI4565FN at 4-9/16 × 1-3/8 inches with a 5° deck. This supports the schematic
envelope, not an installed product section. Needed from the prehanger: Therma-Tru approval
and NFRC/NAFS label for the composite-frame pair with ZAI, FLA and PanoLock+; exact sill,
frame, leaf/sweep and jamb terminations; floor stops, support/seat contacts and drainage
coordinated with the pan. The requested laminated triple remains a special-quote item.

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

The follow-up to c1b1b25f adds a **separately identified schematic sill design** to both
doors, rather than leaving the exposed pan as the only bottom geometry. It does **not**
set `section_documented`, `supplier_confirmed`, or a VERIFIED fit. The factory frame,
threshold internals, cap, jamb/leaf terminations and seals still require supplier data.
`exterior_placement.sill_design_status` is `SCHEMATIC`; approved product sections cannot
be overlaid with this design envelope.

The entry envelope uses the published 7-3/4 × 1-1/2-inch Therma-Tru option. The balcony
envelope uses the published 4-9/16 × 1-3/8-inch Endura ZAI4565FN dimensions.
These overall dimensions do not establish the chosen cap width, cap height, ramp shape,
seat, underside, or seal. Those are explicit project design parameters. The solids are
simplified masses, not traced or verified extrusions; the generic composite cap material
is illustrative. The leaf bottom clears the design crest, the factory jamb envelope
starts at the design seat, and the French-door astragal ends above the sill.

A separate **1/4-inch aluminum walking plate**, pitched outward 1/4 inch per foot,
covers the remaining deep approach. It sits on outward-running KDAT bearing strips at
no more than 8 inches o.c.; the channels between strips remain open.
The strips' metal contact faces have separate 0.020-inch isolation films; the aluminum
does not bear directly on treated wood. These films use the opening-flashing allowance.
A 1/8-inch side joint separates the plate from the steel-wrapped returns.
The nosing shields the pan's downturned
edge, with an open discharge behind it and no bottom return. The tall pan end dams now
end behind the jamb returns; beyond that, only a low edge lip continues beneath the
approach. Previously, six-inch fins projected past the casing into open air.
The sill outlet projects 1/8 inch beyond the wrapped casing; the separate head drip still
projects 1/2 inch. The nosing's vertical leg is 1/16-inch aluminum, with 1/8 inch of open
drainage behind it. At the entry, decking originally overlapped this outlet. The resolved
deck cover now has a local notch leaving 1/2 inch beyond the nosing; the joists are not
cut. Board-end blocking at that notch remains part of the unresolved support detail.
The viewer reads the resolved deck outline and voids, including this notch, rather than
reconstructing a smaller rectangle from the joist centerlines.

**The approach support is not structurally resolved.** The plate gauge, strip spacing,
seat adjustment and nosing are reviewable design choices, not a capacity calculation or
manufacturer installation. A load path from the strips/pan substrate through the exterior
build-up to structure, plate sizing, connections, isolation and anchorage still need a
designed detail. Foam, the plywood buck and the return boards are not bearing supports.
The model explicitly reports this as UNKNOWN. Do not use these envelopes as fabrication
or installation drawings. The interior back-dam cover is also a project design envelope,
not an assertion that either manufacturer's optional cap supplies it.

Reproduce actual sill/head/jamb cuts, JSON and optional framed IFC/glTF with:

```sh
.venv/bin/python scripts/review-exterior-doors.py --export
node ui/scripts/door-review.mjs --exterior
```

Artifacts, manufacturer PDFs/DWG, CAD inspection plots and validation logs are under
`out/exterior-door-review/`. The section plots and screenshots explicitly label the
schematic threshold condition. The garage service raised rough sill, overhead door,
other French pairs and the outie window detail are not reinstalled by this change.

## Follow-up validation

- Doorway, flashing and IR/export parity: **142 passed, 12 skipped**. Includes mirrored
  walls, pan coverage, metal/treated-wood isolation, drainage slope, local deck clearance,
  material vocabulary, sweep exports and factory-cost exclusion.
- UI typechecking and geometry tests pass, including resolved deck cutbacks/voids and
  installation sweep placement. Nine production-builder review views were regenerated.
- Starter: **318 checks passed**. Catlin's three FAIL findings are the same acoustic-box
  spacing advisories on clean `b94c1e7e`; neither reported door has a measured FAIL.
- The standard gate initially had **9,441 passes, 23 failures, 33 skips**. Its three new
  failures (one invalid finish key and two prism-only parity tests) were fixed and rerun
  in the passing focused suite. All other **20 failing test identities reproduce on clean
  `b94c1e7e`**. Existing section/elevation goldens also contain the intentional door changes;
  unrelated differences were not blessed. The full gate is not green.
- Refreshed JSON, sections, framed IFC/glTF and `followup-*` validation logs are in
  `out/exterior-door-review/`. Supplier sections and structural bearing/anchorage remain
  explicitly unresolved; these tests do not certify them.

## Prior review, 2026-10-24 (before the wrapped-trim/sill-design follow-up)

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
