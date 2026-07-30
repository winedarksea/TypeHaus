# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

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

## Remaining Work

- **In-plan variant forks + compare UI** (scoped out of the sweep by decision: catalog only).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.
- **Gree capacities are representative placeholders (2026-07-29).** Every capacity on
  `EQ-T-GREE-*` and the ERV's SRE carries `# TODO verify datasheet` and a `source` saying so.
  `mep.heating_capacity` sizes per *zone of rooms* (`Equipment.zone_rooms` + `outdoor_ref`)
  off `estimate_block_load(rooms=…)`. Current honest findings, whole-house block load
  56,434 Btu/h at design:
  - System 1 (Vireo GEN3 + ducted air handler, upstairs + 3 attic rooms): 14,810 vs 16,500
    at-design — PASS (was 11,415/2 rooms before RM-A-WEST joined the zone on 2026-07-30
    via REG-A-HP-WEST; the margin is thinner now, +1,690).
  - System 2 (Multi Ultra 3-port, basement + west main + living room): **37,303 vs 22,000
    at-design — undersized by ~15,000 Btu/h.** Reported UNKNOWN today only because five
    basement door U-factors are missing from the block-load inputs; once those are authored
    it is an advisory FAIL. Either the zone splits (the basement wants its own system) or
    the outdoor unit grows — a real design decision, not a modelling artifact.
  - System 3 (Sapphire R32, stair + mudroom + mech): 4,094 vs 8,000 at-design — PASS.
  - `RM-A-DEN` is in **no** zone; the check names it unclaimed rather than guessing.
    (RM-A-WEST left this list 2026-07-30.)
- **Refrigerant linesets are unmodeled** — only the indoor→outdoor pairing is recorded
  (`Equipment.outdoor_ref`). (Heat-pump *condensate* is modeled as of the plumbing pass:
  `PR-M-COND-HEADS` drops the two main-storey wall heads through `SP-M-COND` to
  `PR-B-COND`, the collected air-gap line falling to terminate over the mechanical-room
  sink — which now has the drain that was the blocker. `EQ-S-HP1-AH`'s line down the
  second-floor chase is still undrawn.)
- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. `deck_beam_span` also surfaces genuine
  R507.5(1) overspans (porch 2-2x12 @ 10' vs 8.25'; balcony 2-2x10 @ 8.67' vs 5.75').
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

### Residuals from the 2026-07-30 batch

- **`N-M-STRJ` junction WARN (honest fallback).** W-M-STRW's studs are `df-select-s4s`
  while W-M-STRW2/W-M-STOS2 carry `spf`, and the junction solver only calls a through-pair
  continuous on an identical bearing-material string. Physically continuous (both dimensional
  softwood under a lapped double top plate); fixing it properly wants a species-class notion
  in `resolve/topology.py` rather than lying about the stud species.
- **W-M-STRW2 (the 6" jog) kept the standard gwb assembly** — its mudroom face now stands
  1/2" proud of the exposed-stud wall's face. Small step, mostly hidden by the STOS2 tee.
  Decide whether the exposed-stud look should wrap the jog (then it takes
  `CATLIN_MUDROOM_INT_2X6_EXPOSED` too).
- **`FURN-M-MUD-CLOSET-N` type is unused** — the north mudroom closet became RM-M-MECH
  (radon + plumbing riser) instead. Delete the type or place it elsewhere.
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
- **A u-split's landing depth is floored at 36", not at the stair width** (2026-07-28,
  `stairs/common.py::_MIN_LANDING_DEPTH_M`). R311.7.6 has two numbers and the resolver was
  applying the wrong one to the wrong axis: the *width* rule ("not less than the stairway
  served") is cross-run, which a half-landing meets by construction; only the 36" is
  measured in the direction of travel. The old floor silently lengthened every U-well by
  (width - 36").
- **`turn_direction` now names a u-split's hand too** (2026-07-28), not just a winder's.
  It swaps which lane each flight occupies and nothing else — the well, the partition and
  the landing zone are symmetric — so mirroring a stair never changes the opening it needs.
  `None`/`"right"` is the pre-existing behaviour; catlin's ST-B2M and ST-M2S are `"left"`.
- **The two wells share one south edge, and it is the stair wall's face** (2026-07-28).
  Not a free choice either: `FO-S-STAIR`'s south edge is ST-M2S's *springing point* — its
  first tread starts there — so any wall north of that line stands on that tread, and
  `FO-M-STAIR` cannot start south of the wall or the wall overhangs the slab opening. Each
  well then takes whatever run its own north limit leaves, which is why ST-B2M's treads are
  11 15/16" and ST-M2S's are 11". Worth remembering before moving W-M-STRS again.
  (2026-07-30: W-M-STRW is now the exposed-stud coat wall; its stair face is pinned by an
  explicit `alignment` so the well geometry cannot drift with assembly thickness.)
- **Guards draw in 2D** (`emit/draw/floorplan.py::_emit_railings`, layer `A-RAIL`). Every
  resolved railing solid is drawn as its own plan outline, so a post reads at its true
  section and a rail as the band it sweeps. Coincident stacked rails are deduped. An open
  well edge and a guarded one used to draw identically on plan.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

### Items after Phase 6
- Confirm the default toilet's 28" body depth vs an elongated bowl (29–31") — the code
  clearance is already modeled separately (`_water_closet_required_clearance` in
  `library/placeables/fixtures.py`), so this is a one-line footprint question.
- Laundry room needs to fit a sink + closet, 24" W x 21" D x 43" H. like https://www.homedepot.com/p/Glacier-Bay-24-in-W-x-21-in-D-x-34-in-L-Stainless-Steel-Laundry-Utility-Sink-with-Faucet-and-Cabinet-in-White-QL033Y/206057007 The sink will double as the air gapped condensate drain for the heat pump dryer. The sink will have a wall rack over it (one of those that folds down). It looks like we also need to model the standard air gapped clothes washer drain too. The washer/dryer becomes a stacked unit (floorplan area 28 inch width, 40 inch depth, 80 inch height, something like). No vent is needed for a heat pump dryer.
- It looks like beams BM-S-HALL and BM-M-HALL are not getting grouped as part of the framing in the view. Also want to double check that beams are properly considered as a type of framing, for example the hall beams should likely be defined similarly to RIDGE-BEAM, garage header HEADER-0, the porch beams such as BM-SG-BKW, and possibly some of the window and door headers. We also may have some cases where we have headers specified over windows or doors when a large beam
- D-S-STUDY2 can be replaced with just an opening. Likely framed the same as a door of 30", so perhaps a new type of door that is just an opening.
- D-B-PLAY door needs to have a "glazed 60 interior french door" style, not a bifold.
- O-S-CLOSET actually needs to be a bifold closet door.
- The 'Sun' slider doesn't actually seem to do anything. I think the basic idea was just to move a sun icon so users could get a sense of where the sun would be at certain times (not actually modeling shadows), but if that happens now, it isn't visible on the main canvas.
- The tube grow lights need to look in 3d more like suspended lights (which is basically a box with two poles/strings coming down from the ceiling on each end).

Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Is the door opening inside the breezeway code compliant
- No overhang roof 
- Outdoor hydrants plus more complete internal plumbing 
- Edits in 2d don't always update all the necessary pieces (like when we switched a shower to showertub)
- Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?
- Add tracking costs in the UI (so BOM can show costs if known, possibly check off if/when paid, and extra items not present in the 2d or 3d model)

## Windows
We want to make some of the south facing windows, and generally make windows more symmetrical from the outside view of the house (while still following stud spacing needs and being 'pleasantly' spaced from an inside perspective as well).

The main consideration here for symmetric are the south facing windows on RM-S-PLANT, RM-S-STUDY2, RM-A-STUDY and RM-A-DEN/WEST. 
We also might want a bit more symmetric between the main and second floor windows on the east side (RM-S-LIVING versus the bedrooms above).

RM-S-PLANT and RM-S-STUDY2 should have bigger windows, likely 42" wide, breaking two studs in line.
