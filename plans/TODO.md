# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

*2026-07-25: the parallel-workstream sweep cleared most of this file (windows, 2x6, BATH1,
condensation gate, soil ΔT, IFC geometry, detail scaffolding, sunken-garden third pass,
ridge vents, fascia removal, Canvas2D split, variants/BOM/prices, PyPI prep). What follows is
what genuinely remains, with fresh measurements.*

## Needs your decision

- **D2 — the winder turn does not fit in a 3'-0" well, and framing cannot fix that.** The
  turn is now a Haun tiered corner box (real boxes, ledgers, diagonal blocks — see "Stair
  framing follow-ups"), which fixed the *framing* fiction but moves neither code number,
  because both are set by the well:
  - narrow end **1.375"** against IRC R311.7.5.2.1's **6"** (`structural.winder_narrow_tread_depth`)
  - walk-line going **5.0"** against the same rule's **10"** (`structural.winder_walk_line_depth`, new)

  Three winders sweep 22.5° each, so the walk line would have to sit ~2'-2" out from the
  pivot to open to 10" — the levers are a wider well or a turn spread over more risers (a
  layout change to the RM-S-STUDY-2 opening), and there is 2.5" of tread slack in the
  straight run to pay for it (11.28" against the 10" minimum). Both checks stay advisory
  WARN and keep printing the measured numbers.
- **Service load exceeds the service — decision still open (2026-07-26).** The model and
  checks are done: `electrical.service_load` reads the measured 223.7A (NEC 220.82) against
  the 200A service and names the three levers — an EV EMS per 625.42, interlocking the
  sauna, or a service upgrade. A `LoadManagement` element exists (capability only, none
  authored); authoring one with the chosen strategy flips the check. Pick a lever.
- **Panel needs to be a 54-space one (2026-07-26).** All 35 circuits now carry slot
  assignments and `electrical.panel_spaces` measures 48 required against ED-T-PANEL's
  declared 42 — an honest FAIL until the panel type is swapped to a 54-circuit enclosure
  (one-line change on the type). That swap is yours.

## Remaining Work

- **In-plan variant forks + compare UI** (scoped out of the sweep by decision: catalog only).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.
- **Authored gutter runs are still solid bars.** The *derived* eave gutters are open-top
  3-band channels now; `TR-SG-GUTTER`/`TR-RF-GUTTER` (authored `Gutter` runs in
  `resolve/accessories.py::_resolve_edge_run`) should get the same treatment. Exact recipe
  recorded in the roof-eave stream report (E5); purely visual. (Deferred from the 2026-07-26
  batch because that file was owned by the then-pending breezeway stream S2; S2 has now
  landed, so this is unblocked.)
- **Minisplit ratings are representative placeholders (2026-07-26).** `mep.heating_capacity`
  now sizes per zone off `estimate_block_load`; EQ-T-MINISPLIT-LG/-SM carry placeholder
  hyper-heat ratings (30,000/21,000 and 12,000/8,700 Btu/h rated/at-design) to be
  overwritten with the selected models' datasheet numbers. Current honest findings: upstairs
  zone −14,330 Btu/h at design (advisory FAIL), basement UNKNOWN (five basement door
  U-factors missing from the block-load inputs).
- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. `deck_beam_span` also surfaces genuine
  R507.5(1) overspans (porch 2-2x12 @ 10' vs 8.25'; balcony 2-2x10 @ 8.67' vs 5.75').
- **SP-M-WC2 sleeve holds the old drain position (2026-07-26).** The BATH2 WC moved to the
  wet wall but the cast-in sleeve's `drain_position` deliberately stays at (3', 18') so
  `mep.sleeve_alignment` resolves; re-pointing sleeve + PR-B-MAIN-DRAIN at the new flange is
  a follow-up in `plan/mep.py`.
- **`lsl` and `fiber-cement` have no sourced permeance** — deliberately UNKNOWN rather than
  invented. (The two library starter walls no longer need it for a verdict: their rainscreen
  is a real FURRING layer now and the Glaser walk truncates at the vented cavity.)
- **Polycarbonate has no authored vapour permeance** (five-wall extrusion ≠ solid-sheet ASTM
  E96 figures). Needs a sourced figure.
- **KneeBrace paint is authored but not rendered.** `KneeBrace.assembly="POST_WHITE_PAINT"`
  is in the schema and the catlin plan; the diagonal resolves to a `FramedMember`, which has
  no finish slot — rendering the paint needs an IR + emitter change. (The APVKB bands are
  correctly black hardware.)
- **`diff/equivalence.py` storey keys are last-wins** over duplicate reference names (porch
  storeys shadow the house's "basement"); the equivalence test works around it via the
  `building` attribute — a cleanup could prefer the house building when collapsing keys.
- **Windows: 8 residual member-interference overlaps** (junction-proximity clear disabled —
  the honest metric): 4 at two L corners from a neighbouring wall's 1.5" stud/plate
  elevation mismatch, 4 at one T where a jamb pack sits at the junction. Outside the corner
  rule. (Historic: 138 → 8.)
- **`interior_slab_drip_flashing` detail gate** still needs "is there enclosed space
  beneath" (storey elevations on resolved rooms) to distinguish `SL-M-DECK` from
  `SL-G-FLOOR`.

## Phase 2 — Complete Catlin junctions (needs your intent — construction-rule authoring)

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence Catlin nodes with explicit
  bearing and layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions (membrane laps, sealants,
  flashing, thermal-control continuity). `Transition` stays post-resolve documentation.
- Add `Node.junction_override` only if the audit proves a rule cannot express a condition.

## Roof-eave follow-ups (accepted-for-now / awaiting reference drawings)

- **Rake clip rules are extrapolated** from the eave-only golden reference; a rake detail
  drawing would confirm or correct them (same for the rake trim band).
- **Layer end faces stay perpendicular to the slope**, not vertical as the 2D detail draws
  them; serialized setbacks are drift-corrected but the cut face is raked.
- **No closed-cell spray-foam wedge** at the roof/wall foam interface — the closure bands
  follow the slope per-layer so the mismatch never forms; modelling the wedge means
  modelling the flat cut first.
- **The roof-edge metal is a flat band, not a formed cleat + hemmed drip.** Fine at model
  scale; see `plans/standing_seam_design_hints.md`. (House fascia itself is gone: siding and
  roofing are one continuous standing-seam skin with corner trim and a derived ridge-vent
  cap on house + garage.)
- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls (`W-G-E`'s ridge lands where the 16' door is centred).
  Accepted for now. (The gable-closure studs now lie flat in the drop-truss plane — the
  visible-stud defect is fixed.)

## Breezeway — remaining niggles

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a
  `Beam` is a prism). If the wedge becomes a real element the fall moves into it.

## Stair framing follow-ups

- **Winders keep the `tapered tread` 1.5" band** — a trapezoid is not expressible as
  axis + band width in this IR. (These are also the only 3 of 2099 members without a real
  IFC representation, by design.) Sharper now that the turn is boxed: the band is the pie
  panel's *leading edge*, and the box tier under it carries the panel's real footprint.
- **The turn is framed Haun-style** (2026-07-25): one platform box per winder step, sides
  ripped to a riser less the deck (`1.5x6 rim`) so tiers stack dead flush, a diagonal block
  per box, rims ledgered to W-S-E1/W-S-SS2 (`bearing_refs`, newly authored) and dying into
  the newel at the inside corner, and the straight flight landing on the top box's doubled
  departing rim. The two raked "winder carriages" and the slung header are gone — no framer
  cuts a compound-angle carriage through a turn.
- **Every tread/landing board is now dropped to its step elevation** (`stairs/common.py::
  _notch_z`), house-wide rather than winder-only. Boards used to sit *on* the theoretical
  step, which stretched each flight's first riser by 1.5" and shortened its last by the
  same — 9" and 6" against a 7.5" design riser. `structural.stair_riser_uniformity` (new,
  IRC R311.7.5.1) measures the built risers off the members; all three catlin stairs now
  read 0.00" variation.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Items after Phase 4 — done (2026-07-25/26)

All eight shipped, merged in order S1 → S3 → S5 → S7 → S4 → S8 → S2 → S6. Four findings
outlived the items themselves and are recorded below rather than deleted with them.

- **Ridge vent cap** — composed from a riser, shoulders and skirts instead of one flat box
  (the member IR is boxes only; `_gutter_members` already worked around that the same way),
  each band seated on the plane under its own centreline and lapped so no pitch opens a
  crack. White in the viewer: `isSeamMember()` gated the painted-metal finish on
  `category == "cladding"`, so `ridge_cap` fell through to the generic metal grey.
- **Breezeway polycarbonate** — each standing sheet now runs beam soffit to roof-sheet
  underside (9'-10 3/4"), and the two meet in one `profile="H"` channel per side. See the
  retired-premise note below.
- **Flooring** — most of this item was already true: second-storey bedrooms were carpet and
  `RM-A-STUDY` was already oak. What was missing is that *nothing rendered* `floor_finish`.
  Now: a viewer room-floor builder, real `Material`s behind every finish string, GLB parity,
  and the finishes reach the BOM by area with waste and companion layers. Second-storey
  circulation and all three baths run one continuous LVP floor; both walk-ins are carpet.
  Along the way: `Room.finish_zones` was authored-only — `ResolvedRoom` had no field for it,
  so a `FinishZone` in plan source was silently dropped at resolve. It carries through now.
- **Frost-free hydrant** — the project's first `PipeSystem.WATER_COLD` run, plus the
  pedestal, the slab sleeve, the gravel pit, a `hydrant` plan symbol and
  `mep.hydrant_freeze_depth`. The rationale for having no floor drain, and what that trade
  costs, is in `houses/catlin/notes/garage_hydrant.md`.
- **Garage heat detector** — half this item was already satisfied (every bedroom carries a
  COMBO alarm, enforced by `code.R314_R315_alarms`). Added `AlarmKind.HEAT`, `AL-G-HEAT`,
  an `Alarm.circuit` field pointing every alarm at the unswitched `CKT-LT-BACKUP`, and
  `code.R315_garage_alarms` for the garage detector plus CO coverage beside it.
- **BOM sweep** — see the stale-premise note below.
- **U-stair 2D drawing** — root-caused to `782a607`, which turned a landing from one member
  into ~7 and left them all categorised `"landing"`, so the Jul-20 drawer filter started
  painting stair framing as plan linework (~12 stray polylines per landing zone, 13 per
  winder box). Split the semantics (`landing_framing`); a landing now draws as its outline
  rather than its axis. Secondary fix: `u_split.py` never read `stair.start` while the
  validator did, so generation and validation ran on two different origins.
- **Raised garden** — `W-RG-BLOCK` is a U wrapping the sunken garden; `W-RG-INNER` deleted.
  It is no longer a 36" planter but a mostly-buried retaining apron, and
  `params/raised_garden.py` now says so instead of describing the planter.

### Findings worth keeping

1. **The BOM item's premise was stale.** Hangers, connectors, sill anchors and screws had
   been billing all along — `hardware_takeoff` aggregates all four families and 15 tests pin
   them. The real gaps were elsewhere and none of them announced itself: plumbing, ducts,
   sleeves, footing beddings, openings, non-sheathing envelope layers, floor finishes,
   stair treads, conductors and `FloorSystem.ceiling_below` were all resolved and reaching
   no order. All bill now, and
   `test_framing_takeoff.py::test_every_resolved_collection_is_billed_or_waived` is the gate
   that keeps the list honest: every `ResolvedModel` collection must be billed or waived
   with a reason. `haus takeoff` was also silently dropping `lighting_controls`, which a
   second test now prevents.
2. **The engine BOM and the browser BOM are two implementations with different coverage.**
   `ui/src/model/bom.ts` was billing footing beddings when the engine was not. Reconciling
   them was deliberately out of scope for this pass; they still diverge, and nothing tests
   that they agree. That is the next thing to do here.
3. **The breezeway's "three 4x8 sheets, uncut" sheet economy is retired.** It was the stated
   organising idea of `params/breezeway.py`, and it cost 8 1/4" of bare framing below each
   sheet and 14 1/2" of open elevation at the head. The shared H channel costs a 10' sheet
   and the roof's 3 1/4" drip oversail; the sill U-channel's weep holes are now the only
   drainage path. The module docstring owns this rather than describing the old scheme.
4. **The U-stair drawing regression shipped because the 2D stair symbol had essentially no
   test coverage.** The only 2D stair test asserted that no A-STAIR polyline had zero
   length — which every one of those ~12 strays passed. There are now tests for the polyline
   set (surfaces only, framing named explicitly), the landing rectangle, and even tread
   spacing along a flight.
