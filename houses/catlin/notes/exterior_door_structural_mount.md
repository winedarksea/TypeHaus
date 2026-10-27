# Exterior doors: structural-wall mounting

**Current study/patio coordination (2026-10-26):**
[french_door_catalog_installation.md](french_door_catalog_installation.md) supersedes
D-S-DECK-E's schematic steel-wrapped/aluminum-plate installation below. Those two doors
now have independent catalog ROs, composite exterior trim, a digitized ZAI outline and
stock AridDek approach envelopes. The patio includes an XMN5 sill extension and blind
recesses through the exterior layers, stopping at structural framing and concrete. Both
approach sections pass the geometric interference check. Study nominal crest differences are about 0.397 inch
above oak and 0.988 inch above the landing, with a separate +0.250 inch allowance.
The support member checks pass; root connections, concrete development, installed
pan/apron interfaces and flashing-end application evidence remain open. The main-floor
installations described below are unchanged. This is not a construction-ready detail.

Design decision, 2026-10-24; extended to **D-S-DECK-E** on 2026-10-26.
Applies to **D-M-ENTRY**, **D-M-BALC**, and **D-S-DECK-E**.
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

The interior floor finish extends to the frame's interior edge until a documented threshold
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

The main entry D-M-ENTRY and main balcony D-M-BALC retain an explicitly selected
**schematic sill design**, rather than leaving the exposed pan as the only bottom
geometry. It does **not**
set `section_documented`, `supplier_confirmed`, or a VERIFIED fit. The factory frame,
threshold internals, cap, jamb/leaf terminations and seals still require supplier data.
`exterior_placement.sill_design_status` is `SCHEMATIC` for those two doors. This is an
explicit early-coordination option, never an automatic fallback when catalog resolution
fails. Catalog selection produces `CATALOG_DESIGN`; the two specifications are mutually
exclusive. Neither status certifies installation fit. Retire a door's schematic selection
when its documented section is selected; do not add a third generator. The owner-approved
quality criterion and the entry/balcony migration requirements are recorded in
[the design log](../DESIGN-LOG.md#main-floor-sills-retain-explicit-schematic-selections-pending-coordinated-replacement-2026-10-26).

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

**Study balcony, current coordination.** D-S-DECK-E uses the digitized catalog ZAI
outline, composite exterior returns and short AridDek approach boards. It no longer uses
the schematic plate or steel-wrapped returns described above for the main-floor doors.
Independent house/deck flashing ends are modeled as coordination envelopes. Current
geometry, support and installation evidence holds are maintained in
[french_door_catalog_installation.md](french_door_catalog_installation.md).

### Study door: installation research and design criteria, 2026-10-26

The [Therma-Tru site manual, pre-hung unit installation, pp. 1.3–1.6](https://outdoorsandsecurity.widen.net/content/cjranjizwq/original/2026-Site-Manual---SITE-1-Installation.pdf)
specifies a flat, level, solid weight-bearing surface for the sill pan or sill. For its
rigid pan, it specifies a sealed pan-to-subfloor joint and no sealant on the bottom of
the sill when using the pan; retain a free outward drainage path. Its composite-frame
instructions call for shims and screws into the studs at hinges and between hinge
locations, with additional anchorage as applicable. Double doors need alignment and
weatherstrip contact checked at both leaves. The inswing installation calls for sealant
at each cap-to-jamb joint and corner seal pads. Adjust the cap to the door bottom and
check contact; follow the actual prehanger's instructions for the Endura sill, astragal,
pan, sealant compatibility and anchorage. These general instructions do not establish
the factory-specific geometry or authorize drilling through the custom pan.

The [Endura ZAI description](https://www.enduraproducts.com/products/sills-sill-systems/z-series-adjustable-inswing-sill/)
identifies an adjustable cap, composite substrate and integrated high-dam seal; it does
not supply the installed leaf, sweep or frame section. Require a compatible sweep, jamb
end seals and passive-leaf bolt receiver from the prehanger, with cap adjustment and
receiver installation instructions. The modeled cap and leaf clearance do not represent
the sweep's compression. Therma-Tru's [general installation guide](https://projectcenter.thermatru.com/knowledge/full_door_installation)
describes a sill receiver for a double-door slide bolt, but the selected Endura FLA's
receiver and its location must be confirmed rather than assumed interchangeable.

The study now uses the catalog installation. Read its current floor datums, nominal
crest and tolerance-adjusted crest from the engine-generated report described in
[french_door_catalog_installation.md §3](french_door_catalog_installation.md#3-height-and-geometry-review).
The earlier schematic seat/cap figures are superseded. Floor-to-landing drop alone is
not an installed threshold height. Supplier sections and field measurements remain required.

For the study approach, develop a continuous, level structural seat under the factory
sill, and support the AridDek boards and cross bearers back to the house structure. The
support design must preserve the pan's outlet and isolation, and identify
members, fasteners, load path, thermal/water-control transitions, deflection and bearing;
neither the insulation nor the thin buck is a support. A useful precedent is the
[Building Science Corporation exterior-door sill detail](https://buildingscience.com/sites/default/files/migrate/pdf/GM_DER_Guide_2013-01-18.pdf),
which uses structure-connected blocking and retains drainage; its retrofit wall section
is not a structural design for this independently supported balcony.

At each interrupted rear flashing, develop a formed end closure and a house-side
water-shedding transition that directs water outward without sealing the pan outlet or
bridging the independently moving house/deck joint. Confirm laps, end dams, metal
isolation, joint movement and inspection access in a three-dimensional detail. The
[BSC pan-flashing guidance](https://buildingscience.com/documents/information-sheets/pan-flashing-for-exterior-wall-openings)
explains the need for end dams and an open outlet; the present model does not yet show
these proposed flashing-end pieces, so the transition remains open.

The [Therma-Tru Tru-Defense component requirements](https://www.thermatru.com/project-center/faqs/)
list specific Therma-Tru sill, sweep, corner-pad, astragal and hardware requirements for
the rider. The selected Endura ZAI and FLA cannot be assumed to meet those requirements;
the owner prefers the Endura ZAI basis and expects it to be compatible. Request the
actual assembled system's compatibility, warranty, product approval and performance
label in writing. As a fallback, ask the prehanger to quote a complete Therma-Tru
Tru-Defense-eligible pair, with the requested glazing and hardware where available,
and identify any substitutions, dimensions, performance and price differences.
The manufacturer's composite-frame sample demonstrates a 4-9/16-inch option, but does
not establish the depth or hinge datum of this ordered pair. Keep the modeled factory
frame schematic until the prehanger confirms its section and mounting.

Reproduce actual sill/head/jamb cuts, JSON and optional framed IFC/glTF with:

```sh
.venv/bin/python scripts/review-exterior-doors.py --export
node ui/scripts/door-review.mjs --exterior
```

Artifacts, manufacturer PDFs/DWG, CAD inspection plots and validation logs are under
`out/exterior-door-review/`. The section plots and screenshots explicitly label the
schematic threshold condition. The garage service raised rough sill, overhead door,
basement French pair and the outie window detail are not reinstalled by this change.

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
