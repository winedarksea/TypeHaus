# Catlin structural engineering gap review — 2026-09-18

The house is **not yet ready for a quick PE confirmation-and-signoff review**. There is
substantial useful arithmetic, but several complete load paths remain undesigned, some
loads disagree between successive members, and the handoff overstates its completeness.
These are design and reviewability gaps; this review does not establish that the house's
members are inadequate, nor replace a structural design.

Reviewed working tree at `3f365ff6`, model content hash `b40789b412df2d6d`. Existing user
changes were left intact. No structural sizes, reinforcement, or engineering logic were
changed by this review.

The regenerated register contains **34 items: 18 locally passing, 2 incomplete, and 14
without local calculations; none sealed**. The structural-tier run reports 282 PASS,
50 UNKNOWN, 25 NOT_APPLICABLE, and zero FAIL. These counts include MEP checks registered
in that tier; they are not counts of unique structural defects. The draft permit gate
is OPEN despite those gaps. Its declared subset is not a completeness certificate.

Evidence is saved in [the regenerated handoff](../out/engineering-review-2026-09-18/handoff/README.md),
[the separate courtyard study](../out/engineering-review-2026-09-18/courtyard-study/comparison.md),
and [the structural findings](../out/engineering-review-2026-09-18/catlin-structural-review.json).

## Findings, in closure priority

### 1. Canopy snow loads do not follow the load path

**Confirmed implementation gap.** `BM-BW-RW/RE` are checked at 73.7 psf snow, including
the authored drift allowance. `PT-BW-RE/RNE` below them use 50 psf ground snow instead.
The west column/pier chain has the same discrepancy. Each east column's 40 ft² canopy
share is consequently missing **948 lb of service snow** relative to the header's load
basis. Ground snow is not a substitute for the roof's drift load.

The Pad checks also use 50 psf for the canopy. They omit the concrete shaft and pad
self-weight, evaluate the two landing floor systems separately rather than aggregating
their loads, and do not share all of `pier_basis`'s small-roof tributaries. Thus their
large apparent margins do not represent a reconciled foundation reaction.

For scale only: carrying the header's 73.7 psf through the same 40 ft² share, and adding
the existing column and pad weights, gives approximately **1,525 psf under PD-BW-RE**
versus the footing check's 1,500 psf allowance. This is an unreduced gross-bearing
sensitivity, not a final footing verdict: actual truss reactions, load combinations,
overburden/net-bearing convention, eccentricity and soil assumptions still need agreement.
It demonstrates why this discrepancy cannot be dismissed from the current PASS.

**Close with:** one load schedule containing D, occupancy L, balanced/drift S and W;
reactions propagated from trusses to headers, columns and foundations; checks that
downstream reactions reconcile. Use actual support locations and discrete truss loads
when replacing the current uniform-load/equal-share approximation.

Evidence: [roof_beam.py](../../../packages/engine/src/typehaus/engineering/roof_beam.py)
`_design_load_psf`; [pier_basis.py](../../../packages/engine/src/typehaus/engineering/pier_basis.py)
`cast_piers`, `_Pier.live_lb`; [deck.py](../../../packages/engine/src/typehaus/checks/structural/deck.py)
`_roof_borne_posts`, `deck_footing_size`; [preferences.toml](../preferences.toml).

### 2. Fixed-base columns lack a completed foundation/connection design

**Confirmed engineering gap.** The balcony corner columns and the entry's east columns
resist lateral loads by assumed base fixity. Checking their concrete shafts in bending
does not establish that their bases can transmit those moments to the ground.

- Balcony: `column_support/W-SG-W1` and `/W-SG-E1` explicitly defer the wall-top joint,
  dowel development, local wall reinforcement/bearing, and rotational restraint.
- Entry: the east columns have no comparable completed lateral-foundation calculation.
  Their pads receive a gravity-bearing check. Soil lateral resistance, pad rotation,
  overturning/contact pressure and connection force transfer remain unverified.
- The September 17 hook-development hand pass is useful: four entry pads were deepened
  to 12 inches. It does **not** establish the foundation's rotational stiffness. The
  later §8d statement of 4 ft 2 in embedment is stale; the same note updates it to 4 ft 6 in.
- The column calculation's “dowel lap” PASS compares required lap with **column height**,
  not the actual provided lap and anchorage into the supporting wall/pad.

**Close with:** a drawn and calculated joint at each distinct base type, reconciled
column/base forces, actual bar/hook/lap geometry, foundation contact and lateral-resistance
checks, and a defensible stiffness/fixity assumption. Full finite-element soil modeling
is not mandatory if a valid hand method or conservative bound closes the same questions.

Evidence: [deck_post.py](../../../packages/engine/src/typehaus/engineering/deck_post.py)
`_moment_column`; [deferred.py](../../../packages/engine/src/typehaus/engineering/deferred.py)
`column_support`; [north_entry_piers.md](north_entry_piers.md) §§6 and 8d;
[balcony_moment_columns.md](balcony_moment_columns.md) §9.

### 3. The retaining court's passing result is conditional, and its adverse cases are outside the handoff

**Confirmed engineering and integration gap.** `retaining_system/W-SG-ARCH` passes
sliding at **FS 1.628 versus 1.50 required**, with opposed wall thrusts canceled through
the connected court and friction taken at 0.35 on the replacement stone. The documented
no-stone sensitivity is about 1.16. This makes the assumed interface and connected load
path consequential, not incidental.

The register grades stem and footing strength, strut compression and a corner shear
screen. It does not complete corner force transfer/development, construction-stage
restraint, differential backfilling, compaction/traffic surcharge, settlement or global
stability of the tiered excavation. The corner shear row is a concrete section check;
it is not a reinforcement-development or construction-joint design. The 42-inch stone
replacement also needs assessment of the underlying native soil and interfaces.

**Correction to the older notes:** the current walls have modeled dimpleboard drainage
layers and collectors. “No drainage behind the wall is modeled” is no longer true.
What remains open is the groundwater/infiltration basis, continuity and elevations of
the discharge path, emergency overflow, and the agreed blocked-drain design case.

The separate `sunken-garden-study` actually examines a blocked-drain wet envelope and
reports the reference alternative as **revise, governing ratio 7.66**. It also refuses
the coupled project solve without soil stiffness and balcony reactions. This study uses
different case assumptions from the register; 7.66 is **not** a certified utilization
of the current wall. It is important adverse-case evidence that the main handoff omits.

**Close with:** a site-specific geotechnical/drainage basis, accepted wet and dry cases,
explicit transfer and reinforcement details, and a staged stability assessment. Reconcile
the study and registered calculation; include the adopted cases and rejected-case
justifications in the package. Do not redesign the wall solely from the study ratio.

Evidence: [retaining_system.py](../../../packages/engine/src/typehaus/engineering/retaining_system.py),
[retaining_wall.py](../../../packages/engine/src/typehaus/engineering/retaining_wall.py),
[assemblies.py](../plan/assemblies.py) `SUNKEN_GARDEN_WALL_DRAINED`, and the regenerated study.
The adopted code's retaining-wall design scope includes sliding, overturning, foundation
pressure and water uplift: [2020 Minnesota Residential Code, R404.4](https://codes.iccsafe.org/content/MNRC2020P1/chapter-4-foundations).

### 4. Column checks do not establish a complete load-combination or lateral-system envelope

**Confirmed scope gap; numerical consequences need analysis.** `_moment_column` checks
wind and guard moment against P–M capacity at one factored axial load, then magnifies the
larger moment. It does not search the applicable gravity/wind/uplift combinations at
their corresponding axial loads. Using a larger axial force is not automatically
conservative on a P–M interaction curve.

Column shear, torsion where applicable, drift/serviceability, diaphragm force distribution
and the relevant connection capacities are still excluded. The entry's west screen and
continuous garage/canopy sheathing need a coherent stiffness/load-transfer explanation
even where assigning all canopy shear to the east columns bounds their member demand.
The HGAM10/shim connections need directional shear, uplift, bearing and anchorage checks;
they need not be moment connections if the adopted structural model does not require that.

**Close with:** a load-case/combination matrix, governing P–M pairs, lateral displacement
criteria, and diaphragm/collector/connection schedules for both directions. Record any
seismic exemption or minimum-force basis using this site's hazard information.

Evidence: [deck_post.py](../../../packages/engine/src/typehaus/engineering/deck_post.py)
`_moment_column`; [roof_moment.py](../../../packages/engine/src/typehaus/engineering/roof_moment.py);
[north_entry_structure.md](north_entry_structure.md) §1a; column oracle exclusions.

### 5. Some “prescriptive” passes depend on unverified or incompatible conditions

**Confirmed applicability gap.** The balcony glulams use a manufacturer row labeled
dry-use while the project applies wet-service NDS reductions in a separate check. That
NDS check is useful and currently passes, but it is a calculation supporting an exposed
installation, not evidence that the dry-use row covers it. It has no engineered record
or fingerprint. The manufacturer's guide also calls for separate sizing of a center
beam supporting joists on both sides.

The published-span helper permits PASS while printing unchecked conditions as prose.
For the glulam call it does not receive `demand_psf`, so even its existing load-basis
comparison is not exercised. Deck demand is fixed at 40 psf live + 10 psf dead; establish
snow/drift, actual finishes and any intended planter loading before accepting that basis.
Similarly, `RF-HOUSE` passes its span read while its own note leaves the high-end support
condition unconfirmed. Resolve that document/detail question rather than perpetuating
contradictory transcriptions about ridge boards and ridge beams.

**Close with:** exact source edition/page/row and machine-checkable applicability
conditions: species/grade, treatment/service moisture, span, bearing, cantilever,
loads and restraint. Obtain an applicable supplier table/design output when possible;
otherwise register the small engineering calculation already needed. A failed applicability
condition should remain unresolved until another valid design path covers it.

Evidence: [deck.py](../../../packages/engine/src/typehaus/checks/structural/deck.py)
`_off_table_beam`; [published.py](../../../packages/engine/src/typehaus/checks/structural/published.py);
[roof_rafter_span_read.md](roof_rafter_span_read.md) §3. Independently checked against
[Anthony/Canfor's deck guide](https://www.anthonyforest.com/assets/pdf/power-preserved-glulam-deck-guide-2020.pdf),
including its dry-use heading and center-beam instruction.

### 6. Other structural gaps need to appear in one closure register

These are not all new discoveries; several already have good deferral descriptions.

| Scope | Current gap | Shortest credible closure |
|---|---|---|
| `W-SG-BRKBM` veneer beam | Registered as NO_CALC although a separate screening exists; end restraint/development, torsion detailing, insulated-standoff masonry anchorage and movement joints unresolved | Connect the actual beam calculation to the register; complete joint/torsion/anchor details |
| Four `DW-SG-*` thermal-break transfers | Demand, differential movement, GFRP stiffness/development and pour support unresolved | State what force/movement the break must transmit, then select/detail a qualified system |
| Five `W-RG-*` upper-tier walls | Upper wall and coupled/global stability deferred | Geotechnical basis plus applicable supplier engineering; height alone does not close the tiered condition |
| `PT-BW-W/GW` | INCOMPLETE because `BM-BW-SCSILL` load is unaccounted for | Model the screen/sill dead and lateral load; remove the irrelevant legacy shelter-roof wording from the missing-input explanation |
| `PT-BW-IC/IE` on garage slab | Footing check says N/A and explicitly says slab bending, punching and subgrade bearing are ungraded | Verify and detail the noted 2-ft-square, 10-in thickening and its reinforcement/anchorage |
| House/garage/entry bracing | Six braced-wall-panel UNKNOWNs: lines exist, qualifying panels are not modeled | Complete IRC bracing layouts, lengths and hold-down/portal details where permitted; engineer exceptions |
| Garage/canopy trusses and uplift chain | Component designs/reactions deferred; downstream capacity unfinished | Supplier sealed truss package with drift cases, plus a reconciled connection-to-foundation schedule |

The ordinary framing, qualifying headers, joists and deck details should stay on valid
prescriptive/manufacturer paths. Treating every UNKNOWN as new custom engineering would
work against the stated goal; distinguish missing table evidence from an actual table limit.

### 7. The runnable analysis export is a verification aid, not the completed analysis

**Verified by generation and execution.** The exported PyNite script runs successfully.
Its current data contain **zero shell elements, zero soil springs, and only five
single-case combinations**: dead, live, snow, wind and guard. There are no combined
strength/service envelopes in that export. Column self-weight is excluded, and base
fixity is assumed. The retaining walls, their supporting system, wall-top joints and
veneer beam are listed as gaps.

The separate courtyard shell-model implementation is useful but is not integrated into
this handoff and lacks the project's required soil/reaction inputs. Successful execution
of the frame therefore does not close findings 1–4. Tests confirming that a frame reproduces
the same assumed fixed-base moment do not independently verify that base restraint.

**Close with:** a runnable package for each adopted engineering system, pinned solver
dependencies, actual load combinations, equilibrium/reaction reconciliation, assumptions
and limitations, plus a verified import example for any advertised PE software route.
Native PyNite execution was tested here; SAP2000/ETABS/RISA import was not.

### 8. The PDF is not presently easy to review

**Visually confirmed defect.** The generated PDF is **136 pages**. It prints literal
Markdown table delimiters as monospaced text. On PDF page 34, sheet S-22, the entry-column
analysis table extends beyond the right page edge, cutting off citations. Identical
column families repeat long references and exclusions across multiple sheets. The cover
index also stops listing items when it exhausts its space.

The engineering bundle does not include the structural plan/connection-detail sheets or
the prescriptive evidence schedule. Many calculation pages are numeric result tables;
the explanatory equations are in long separate notes. Review requires cross-navigation
and reconstruction of what supports what.

**Close with:** properly rendered tables, complete clickable index/bookmarks, small
annotated load-path plans/sections, one calculation per distinct design family with a
member schedule, substitutions/units alongside equations, and linked construction details.
Keep the comprehensive machine data and historical notes as appendices.

Evidence: [rendered S-22](../out/engineering-review-2026-09-18/catlin-pe-review-page34.png)
and [calc_pdf.py](../../../packages/engine/src/typehaus/takeoff/calc_pdf.py).

### 9. “Computed” and “ready for review” are conflated

**Confirmed reporting defect.** The handoff README calls the 18 computed items checked
with “nothing missing,” while their notes exclude required parts of the design. It calls
the 14 deferred items “not yours,” although several explicitly belong to the structural
engineer of record. The criteria sheet says every cited capacity is ASD despite the ACI
strength checks; it lists only ground snow rather than the canopy's design drift case.

Older oracle notes also conflict with current geometry, drainage and pour sequencing.
For example, the court note still describes missing drainage and cold-jointed corners,
where the authored placement note specifies monolithic court walls. These contradictions
cost review time and undermine the claimed independent verification.

**Close with:** separate statuses for arithmetic completed, scope completed, externally
designed/accepted, and professionally reviewed. Make every exclusion an owned closure item
or an explicit justified exclusion. Generate the design criteria from the actual cases,
and separate the current verified hand pass from the historical decision record.

Evidence: [handoff.py](../../../packages/engine/src/typehaus/takeoff/handoff.py),
[calc_criteria.py](../../../packages/engine/src/typehaus/takeoff/calc_criteria.py),
[sunken_garden_court_free_body.md](sunken_garden_court_free_body.md) §9.

### 10. Seal freshness does not capture all design changes, and external acceptance is unfinished

**Reproduced in memory; no signoff file created.** Changing the E2 retaining calculation's
concrete strength from **5,000 to 4,000 psi** changes stem/footing capacities, yet both
records remain OK with the same fingerprint, `22c251adaa8b0ba0`. Concrete strength and
reinforcement are absent from that record's input list; the governing sliding ratio stays
unchanged, so the ratio-based tripwire cannot catch the edit.

The documented external-design workflow cannot ordinarily finish: deferred items have no
model-dependent fingerprint and the scaffold comments them out. Conversely, directly
pinning the generic hash of a NO_CALC record returns **FRESH** from
`EngineeringRegister.freshness`, despite containing zero design inputs. This is not a
legitimate workaround; it demonstrates that the underlying freshness API does not enforce
the limitation stated by the CLI.

**Close with:** fingerprints over the complete engineering input/dependency set, including
materials, reinforcement and critical support/detail assumptions; explicit refusal of
generic NO_CALC freshness; and a real external-design acceptance record tied to the
supplier's document revision/hash and the geometry/load envelope it covers. Professional
review remains a human act; software should reliably record its scope and detect changes.

Evidence: [probe output](../out/engineering-review-2026-09-18/catlin-pe-review-probes.txt),
[retaining_wall.py](../../../packages/engine/src/typehaus/engineering/retaining_wall.py)
input list, [fingerprint.py](../../../packages/engine/src/typehaus/engineering/fingerprint.py),
[register.py](../../../packages/engine/src/typehaus/engineering/register.py) `freshness`.

## Recommended completion sequence

1. **Repair the evidence first:** unify loads/reactions, fix applicability gates and
   fingerprints, expose every outstanding structural scope, and render legible PDFs.
   These are software/documentation tasks that do not require inventing site properties.
2. **Resolve site facts:** commission the focused geotechnical and drainage work for the
   court and moment-column foundations; obtain site hazard criteria and supplier reactions.
3. **Complete three coordinated design packages:** court/terrace/drainage/veneer/thermal
   breaks; balcony columns/connections/diaphragm/wall supports; entry canopy/landing/screen/
   columns/foundations. Keep supplier truss engineering as an explicit linked deliverable.
4. **Prepare the short review route:** one-page readiness/scope summary; design criteria;
   annotated load-path drawings; governing calculations by family; prescriptive evidence;
   construction details; executable model/results; independent checks and signed-document
   acceptance. A PE should be confirming a resolved design, not discovering what is missing.

## Verification performed

- Regenerated `haus engineering`, structural-tier JSON, full IFC/GLB/calculation/analysis
  handoff, and the separate sunken-garden study from the working tree.
- Executed the generated PyNite script successfully.
- Ran 123 existing tests successfully across `test_pier_calcs.py`,
  `test_north_entry_piers.py`, `test_retaining_court.py`, `test_analytical_oracle.py`, and
  `test_handoff.py`. This verifies the existing implementation's tested contracts, not
  completeness of its engineering assumptions. The full repository gate was not run.
- Inspected extracted PDF text and a rendered calculation page; reproduced the
  material-change fingerprint defect and NO_CALC freshness behavior in memory.
- Checked official Minnesota code sources and the original glulam guide. Minnesota's
  [current code listing](https://www.dli.mn.gov/business/codes-and-laws/2020-minnesota-state-building-codes)
  still lists the 2020 residential code; site snow/frost inputs should cite the applicable
  [Minnesota rules](https://www.revisor.mn.gov/rules/1303/full).

Commands can be rerun with `haus handoff houses/catlin --out <review>/handoff`,
`haus sunken-garden-study houses/catlin --out <review>/courtyard-study`, and
`haus check houses/catlin --tier structural --json --exit-on none`, using `.venv/bin/haus`.
Generated evidence lives under ignored `out/`; this review note is the persistent source artifact.
