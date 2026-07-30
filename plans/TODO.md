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
- ~~**Service load exceeds the service**~~ — **decided 2026-07-27: the EV EMS lever.**
  `LM-EV` (Emporia Vue, `strategy="ems"`) caps `CKT-EV-1450` + `CKT-EV-620` at 5,760 VA
  (24A @ 240V), credited per NEC 625.42. Demand falls 223.7A → 191.7A and fits the 200A
  service, so the check passes. 5,760 VA is the largest round setpoint inside the 32.3A of
  headroom the rest of the house leaves, and stays well above the 6A floor an EVSE may
  never be throttled below. Authored in `houses/catlin/plan/circuits.py`.
- **Panel needs to be a 54-space one (2026-07-26).** All 35 circuits now carry slot
  assignments and `electrical.panel_spaces` measures 48 required against ED-T-PANEL's
  declared 42 — an honest FAIL until the panel type is swapped to a 54-circuit enclosure
  (one-line change on the type). That swap is yours.

## Remaining Work

- **`Alarm` has no position — it draws at its room's seed.** Fine while every alarm had a
  room its own size; exposed on 2026-07-28 when RM-M-HALL was retired into RM-M-LIVING under
  BM-M-HALL and AL-M-HALL's symbol moved with it to (27', 12'), out in the dining end. The
  code check only asks for *an* alarm on a non-sleeping room, so it still passes, but R314.3
  wants it "in the immediate vicinity of the bedrooms" and the sheet now draws it elsewhere.
  Needs an optional `position` on `Alarm` (falling back to the seed), not a room split.
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
- **Gree capacities are representative placeholders (2026-07-29).** The three-system HVAC
  design below is modeled; every capacity on `EQ-T-GREE-*` and the ERV's SRE carries
  `# TODO verify datasheet` and a `source` saying so. `mep.heating_capacity` now sizes per
  *zone of rooms* (`Equipment.zone_rooms` + `outdoor_ref`) off `estimate_block_load(rooms=…)`.
  Current honest findings, whole-house block load 56,434 Btu/h at design:
  - System 1 (Vireo GEN3 + ducted air handler, upstairs + 2 attic rooms): 11,415 vs 16,500
    at-design — PASS.
  - System 2 (Multi Ultra 3-port, basement + west main + living room): **37,078 vs 22,000
    at-design — undersized by ~15,000 Btu/h.** Reported UNKNOWN today only because five
    basement door U-factors are missing from the block-load inputs; once those are authored
    it is an advisory FAIL. Either the zone splits (the basement wants its own system) or
    the outdoor unit grows — a real design decision, not a modelling artifact.
  - System 3 (Sapphire R32, stair + mudroom + mech): 4,094 vs 8,000 at-design — PASS.
  - `RM-A-WEST` and `RM-A-DEN` are in **no** zone: only RM-A-EAST and RM-A-STUDY get attic
    branches, so the check names the other two unclaimed rather than guessing.
- **RM-S-SUITE has no conditioned-air terminal (2026-07-29).** It is in System 1's
  `zone_rooms`, but the chase runs down the *east* hall; reaching the west suite needs a
  branch across the stair well that is not drawn. Its ERV supply is unaffected.
- **Hall cans sit inside the new soffit (2026-07-29).** `ED-S-HALL-CAN1/2/3` are at x=20',
  inside `SF-S-DUCT`'s widened plan extent, still mounted at the 9'-0" ceiling. They want
  re-setting into the soffit face at 7'-10" in a lighting pass.
- **Heat-pump condensate is not modeled (2026-07-29).** Each indoor unit drains to a
  collected air-gap line terminating over the mechanical-room sink; needs the plumbing pass
  that gives that sink its own drain. Refrigerant linesets are also unmodeled — only the
  indoor→outdoor pairing is recorded (`Equipment.outdoor_ref`).
- **The panel is now 52 spaces over a 42-space enclosure (2026-07-29).** Two more two-pole
  circuits (CKT-HP1-AH, CKT-HP2) landed with the three-system design; `electrical.panel_spaces`
  FAILs until the panel is swapped for a 54-space unit, which was already true at 48.
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
- **Guards draw in 2D** (`emit/draw/floorplan.py::_emit_railings`, layer `A-RAIL`). Every
  resolved railing solid is drawn as its own plan outline, so a post reads at its true
  section and a rail as the band it sweeps. Coincident stacked rails are deduped. An open
  well edge and a guarded one used to draw identically on plan.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

### Items after Phase 6
- Double check that the default toilet has a realistic size (do we separate the code required toilet clearance with the size of the toilet itself?)
- DONE: object inspector relabeled (every row on `.field-label`, positions and distances in
  ft-in) and given a "Mount height above floor" field on the new `set_placeable_mount` macro,
  which rewrites only the mount's elevation and keeps kind/drop/recessed. Clicking no longer
  moves anything: the plan canvas needs 5px of screen travel before a drag starts, and a drag
  keeps the grab point under the pointer instead of snapping the object's centre to it.
- DONE: Views ▾ → Labels: All / Hover / Off, covering room labels and object names together
  (replaces the "Space labels" checkbox). A selected element always shows its own label.
- RM-M-STORAGE should become the "Mudroom". Doors should go as far east on both walls as is practical with framing. WIN-M-STOR should be replaced by a 14" wide fixed (picture) window on the midpoint of the west wall (midpoint, but such that it fits elegantly between studs). Then on the north and south sides of the mudroom, from door to west wall, there should be full closests added, leaving a hallway width (36") between them, and a 36" width bench under the window there for changing shoes. The mudroom should have an ERV ventilation intake (but not an outlet). Maybe sliding doors on those closets (like shower doors, two panels that can overlap, not the sash kind that go into the wall).
- Make Wall W-M-STRW a special wall type. It will not have drywall facing the mudroom, so it can have space for hanging coats between the studs. The studs will be Select Grade S4S 2x6 for better visual appearance (likely douglas fir, perhaps slightly rounded (eased) corners). The rear side of the wall (facing the stairs) will have 3/4" cabinet-grade plywood (which can support coat hooks directly). Try to keep electrical and plumbing out of this wall then (it might work carefully but easier to avoid.)
- Unittests that the stairs align between floors and reach the correct ceiling height while meeting code. The winders for ST-S2A are still messed up (last winder is level with the floor, not a step up), and the regular stair tread can come down to 11".

Questions:
- Do we want floor drains in kitchen/laundry room
- Is the door opening inside the breezeway code compliant
- No overhang roof 
- ~~2nd floor hallway dropped ceiling for HVAC~~ (done 2026-07-29: `SF-S-DUCT`)
- Outdoor hydrants plus more complete internal plumbing 
- Edits in 2d don't always update all the necessary pieces (like when we switched a shower to showertub)
- Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?
- Should we add paint as a layer over gwb where appropriate (also allowing color choice), and if it is used as a Class III vapor retarder (ie latex paint over drywall)
- Add tracking costs in the UI (so BOM can show costs if known, possibly check off if/when paid, and extra items not present in the 2d or 3d model)

##  HVAC
**Modeled 2026-07-29** — all four items below are implemented; the open follow-ups are in
the honest-state list above (Gree datasheet verification, System 2 undersizing, RM-S-SUITE's
missing terminal, the hall cans, condensate plumbing). The BTU model now carries blower-door
infiltration (LBL N-factor off `preferences.toml`'s `ach50`) and ERV ventilation air net of
sensible recovery, and can be scoped to a zone of rooms — see `energy.py`, whose docstring
says plainly where that room attribution is approximate.

Gree Slim Concealed Ducted Series with Gree Vireo GEN3 / Ultra outdoor unit running in RM-S-STUDY2 in a dropped HVAC chase that runs north from there along the hallway, with outlets in each of the bedrooms and near the stairs, plus also outlets into RM-A-EAST and RM-A-STUDY directly above it (very short branches, this is a straight run duct meant to operate at low flow)

Gree Multi Ultra 3-port outdoor unit (heats down to -22°F) powering the 3 wall mounts (basement in gym near ceiling, master bedroom on south wall near the center wall, living room on south wall near the center line wall)

Unit three is on the north side of the house. It is mounted on the main floor over the stairs, with a cutout in the wall (W-M-STRW) in which it is partly placed to also reach the mudroom directly. This unit is on backup battery circuit, and is an ultra high efficiency unit (something like Gree Sapphire R32 Series, with a true VFD inverter for softer power start) likely something like 9100 BTUs.

ERV system nears clearer inlets and outlets. They are currently style more like old fashioned grilles, not true ERV inputs/outputs.

### Cleanup
- Update the screenshots in the landing page and remove the "pre alpha" notes
