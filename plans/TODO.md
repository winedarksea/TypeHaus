# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Needs your decision

- **The building drain is at 3" and the basement's real load is now ~42 DFU (2026-07-30).**
  The stair-foot bathroom and the sauna shower end added four slab fixtures (WC 3 + lav 1 +
  shower 2 + floor drain 2 = 8 DFU). They ride their own under-slab branches —
  `PR-B-BATH-DRAIN` and `PR-B-SAUNA-DRAIN` — and by the convention FX-1 set they are *not*
  re-listed in `PR-B-MAIN-DRAIN`'s `serves`, so `mep.pipe_sizing` still measures the main at
  34 of the 35 DFU a 3" horizontal branch carries (Table 703.2) and passes. The pipe is
  carrying ~42. Sizing the building drain up to 4" is the honest fix and it is not a one-liner:
  `SP-B-SLAB-MAIN`, `SP-B-SEWER-EXIT` and the under-slab inverts the 2026-07-30 sewer decision
  set all move with it, and there is only ~10" between the slab underside and that leg to move
  them in. Yours, because it re-opens that decision.

## Accepted, by decision (2026-07-31 warnings sweep)

- **The 200A service stays, and `electrical.service_load` stays failing at 220.9A.**
  Accepted rather than fixed: NEC 220.82 is a whole-house estimate and this house never runs
  range + spa + sauna + both EVs at once. The lever if it ever needs pulling is a second
  `LoadManagement` over `CKT-SPA` + `CKT-SAUNA` capped at 11,500 VA — they are mutually
  exclusive by use, and the 9,000 VA credit lands the estimate near 183A without touching
  the meter. (`LM-EV` already caps the two EV circuits; that credit is in the 220.9A.)
- **Both sunken-garden beam lines are engineered, so R507.5(1) no longer verifies them**
  (2026-07-31). `SPEC.back_beam` is a 2-1.75x11.25 LVL and `SPEC.balcony_beam` a
  2-1.75x9.25 LVL, both at their sawn predecessor's depth so no elevation moved.
  `structural.deck_beam_span` now reports all five UNKNOWN — an engineered member is sized
  off the manufacturer's span table, not the prescriptive one. The porch pair could have
  stayed checkable as a 3-ply sawn 2x12 (10'-3" allowed vs the 10'-0" span); the balcony had
  no prescriptive answer at all, since its 10'-6" joists read the 12' row where even 3-2x12
  stops at 8'-4" against an 8'-8" span.

## Remaining Work

- **`mep.heating_capacity` still fails on the HP2 zone, by 764 Btu/h** (2026-07-31). Block
  load 30,764 Btu/h at design over the basement plus the main-floor bedroom/bath/living
  side. `EQ-T-GREE-MULTI-U30` is the max-heating variant of the 3-port box (36,000 Btu/h at
  47F, 30,000 at design), which leaves **-764 Btu/h** rather than pretending the zone is
  covered. Both capacity figures are still REPRESENTATIVE PLACEHOLDER — the real answer
  wants the Gree datasheet. The radiant mats, the fireplace and the garage heater stay
  excluded from the zone total by design (`plan/circuits.py` calls them supplemental); if
  the radiant is in fact carrying that last 764, it should stop being modeled as
  supplemental.
- **Handrail schema + real R311.7.8 check** (2026-07-31). `Railing` needs a
  role/kind (handrail vs guard) plus per-flight authoring before presence, 34"–38" height
  and continuity can be measured; `code.R311_7_8_handrail` reports the gap as UNKNOWN on
  every 4+-riser flight until then. (Headroom is now really measured —
  `code.R311_7_2_stair_headroom` samples the sloped nosing line plumb against floor/roof/
  soffit structure; `code.R311_7_1_stair_width` and `code.R311_7_6_landing_depth` measure
  the built members. The old check reported the arrival storey's nominal ceiling height as
  "headroom".)
- **Stair/well guard check (R312)** — next in line after headroom: classify each floor
  opening's edges as wall-backed vs open (against resolved wall faces), and require a
  `railing` solid path at >= 36" along the open ones. Measurable today from resolved
  geometry, no new authoring; catlin's RL-S-STAIR/RL-S-STAIRHEAD guards are the first
  real fixture.
- **In-plan variant forks + compare UI** (scoped out of the sweep by decision: catalog only).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.
- **Refrigerant linesets are unmodeled** — only the indoor→outdoor pairing is recorded
  (`Equipment.outdoor_ref`). (Heat-pump *condensate* is modeled as of the plumbing pass:
  `PR-M-COND-HEADS` drops the two main-storey wall heads through `SP-M-COND` to
  `PR-B-COND`, the collected air-gap line falling to terminate over the mechanical-room
  sink — which now has the drain that was the blocker. `EQ-S-HP1-AH`'s line down the
  second-floor chase is still undrawn.)
- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span`'s two genuine R507.5(1)
  overspans were closed 2026-07-31 by going engineered — see "Accepted, by decision".)
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

### Residuals from the 2026-07-30 batch

- **`N-M-STR1` junction WARN (honest fallback).** W-M-STRS's 2x4 `spf` partition dies into
  the end of W-M-STRW2's 2x6 `df-select-s4s`, and an L only resolves on an identical
  assembly or a shared bearing material. Physically a partition butting an end stud.
  `resolve/topology.py` wants a species-class notion rather than the plan lying about the
  stud species.
- **The mudroom 6" jog has to stay its own `Wall`** — a standing constraint, not a task.
  `resolve/topology.py` builds junction incidents from wall endpoints only, so the
  W-M-STOS2 tee needs a node both walls terminate at; merging the jog re-opens `N-M-STRJ`.
- **RM-S-PLANT has no fresh-air terminal, by decision (2026-07-30)** — a dedicated mini-HRV
  just for the plant room is under consideration. RM-S-STUDY2 likewise has no fresh-air
  terminal, by decision. `mep.ventilation_distribution` names exactly these two rooms and
  the test pins that set.
- **Workshop ERV intake is positioned off the light** `ED-B-WORKSHOP-PANEL1` ("over a
  bench") — no workbench placeable exists in RM-B-WORKSHOP yet; move the register when the
  bench is actually placed.
- **The ERV→System 1 fresh feed's vertical is undrawn.** `DU-S-ERV-HP-FEED` (2026-07-30)
  taps `DU-M1-ERV-SUP` in its FS-SECOND joist bay under the hall at y=12'-8" and runs in
  SF-S-DUCT's box to the wye behind `REG-S-HP-RET`, but the rise from the joist bay up
  into the soffit is not modeled (`DuctRun` carries no elevation) — same status as
  EQ-S-HP1-AH's condensate drop. Physically it wants the hall/bedroom wall corner furred
  or the soffit's east cheek; decide when the chase details get drawn.
- **Per-wall paint colour.** `latex-paint` over gwb is modeled (Class III, IRC R702.7.1) but
  `Layer` has no colour slot; a second colour needs a second paint `Material` plus per-room
  `wall_lining` overrides. Rationale in the comment above `_PAINT_FINISH` in
  `houses/catlin/plan/assemblies.py`.

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

## Stair framing — accepted limitations and standing constraints

- **Winders keep the `tapered tread` 1.5" band** — a trapezoid is not expressible as
  axis + band width in this IR. (These are also the only 3 of 2099 members without a real
  IFC representation, by design.) The band is the pie panel's *nosing/fan line*; the box
  tier under it carries the panel's real footprint.
- **The two wells share one south edge, and it is the stair wall's face** (2026-07-28).
  Not a free choice either: `FO-S-STAIR`'s south edge is ST-M2S's *springing point* — its
  first tread starts there — so any wall north of that line stands on that tread, and
  `FO-M-STAIR` cannot start south of the wall or the wall overhangs the slab opening. Each
  well then takes whatever run its own north limit leaves, which is why ST-B2M's treads are
  11 15/16" and ST-M2S's are 11". Worth remembering before moving W-M-STRS again.
  (2026-07-30: W-M-STRW/STRW2 are now the exposed-stud coat wall; the stair face is pinned
  by an explicit `alignment` so the well geometry cannot drift with assembly thickness.
  Same day, W-M-STRS was cut back to the well partition at x=14'-2 1/4" — it frames
  D-M-STAIR and stops — so the up-flight's lane is open to the living room. RO-1 went with
  the removed length, and RM-M-STAIR retired into RM-M-LIVING, since the well is inside
  that room's polygonized face now.)

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

### Items after Phase 6
- Confirm the default toilet's 28" body depth vs an elongated bowl (29–31") — the code
  clearance is already modeled separately (`_water_closet_required_clearance` in
  `library/placeables/fixtures.py`), so this is a one-line footprint question.
- It looks like beams BM-S-HALL and BM-M-HALL are not getting grouped as part of the framing in the view. Also want to double check that beams are properly considered as a type of framing, for example the hall beams should likely be defined similarly to RIDGE-BEAM, garage header HEADER-0, the porch beams such as BM-SG-BKW, and possibly some of the window and door headers. We also may have some cases where we have headers specified over windows or doors when a large beam
- Make sure there is an electric outlet in the kitchen island where usable for appliances in accordance with code

Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Is the door opening inside the breezeway code compliant
- No overhang roof 
- Outdoor hydrants plus more complete internal plumbing 
- Edits in 2d don't always update all the necessary pieces (like when we switched a shower to showertub)
- Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?
- Add tracking costs in the UI (so BOM can show costs if known, possibly check off if/when paid, and extra items not present in the 2d or 3d model)
- Pantry

### Other visual ideas
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements
Architectural lighting on facade (try to aim to be dark sky friendly)
