# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Needs your decision

These are blocked on a call only you can make, not on work. Everything else in this file is
work.

- **D2 — winder narrow-end tread depth.** The geometry is fixed: each winder starts where its
  own ray leaves the newel post's *face*, so the narrow ends are distinct rather than
  converging on a point. That buys **0.9"**, and IRC R311.7.5.2.1 wants **6"**. Three winders
  around a 4x4 cannot reach it. The fix is a layout choice — more risers in the turn, or a
  wider newel/well the winders wrap — not a number the generator can invent.
  `structural.winder_narrow_tread_depth` measures and reports the shortfall meanwhile.
- **D3 — the catlin stair does not fit its own well.** `FO-S-STAIR` offers 84", but the
  finished well between `W-M-STRW`'s and `W-M-C5`'s stair-side gwb faces is **77.25"** — the
  two 3'-6" flights are **6.75" too wide**. Either the flights narrow or the opening is
  re-drawn to the finished face. This blocks two other items: the framed-wall ledger below,
  and narrowing `checks/structural/interference.py`'s `_STAIR_SUPPORT` (its ~80 whitelisted
  catlin contacts are stair members physically inside stud cavities — an annotation does not
  move geometry).
- **Condensation boundary condition.** `building_science.condensation` now emits real results
  and reports 3 FAILs (`CATLIN_EXT_2X6`, `CATLIN_EXT_2X4`, `CATLIN_ROOF` — dew point at the
  sheathing at −15 °F / 35% RH). The walls are vapour-open mineral wool with no interior
  retarder. That is correct **for the boundary condition `plans/50-m5-science.md:13` mandates**
  (the 99% design hour). ISO 13788, which Glaser comes from, uses **monthly means** precisely
  because a design-day walk flags code-compliant CI walls; at Minneapolis' winter mean these
  same walls are comfortably safe. Whether this check is a pass/fail gate or a cold-snap
  screening signal is a plan decision — the implementation follows the plan as written.
- **Knee brace count.** The hardware note asks for 4 knee braces (main corners) × 2
  `APVKB45-6`. `houses/catlin/params/sunken_garden.py` authors a `KNEEBRACE` connector at
  **all six** pillars, so the take-off bills **12**. It counts what the model contains rather
  than hardcoding 4; if the design is corner-only, delete the two non-corner connectors.
- **`RM-M-BATH1` is too small.** Clear face is 3'-2" × 4'-3¼". A 2'-6" WC plus a 1'-9" lav is
  4'-3" of that 4'-3¼". The fixtures now pack wall-to-wall with ~⅛" at each end and nothing
  between them. The design fix is a bigger bath or no lav.
- **`D-G-OVERHEAD` needs an engineered header.** The 16' garage door exceeds the prescriptive
  table. A genuine engineering input, not a modelling gap.
- **`advisory.window_size_variety`** — 10 unique window sizes. Fewer eases ordering; whether
  to consolidate is a design call.
- **Phase 2 junctions** (own section below) — every item there is construction-rule authoring
  that needs your intent, not mechanical work.
- **`install.sh` installs a package that does not exist.** `landing/install.sh` runs
  `pipx install "typehaus[server]"`, but `typehaus` is not on PyPI. Either publish it or drop
  the install link; `/app` (the PWA) does not depend on it.

## Remaining Work

- **M2 variants/compare — engine + CLI in, UI + forks missing.** `variants.toml` declares
  named variants (assembly swaps, layer-thickness overrides); `haus variants
  list|compare|assemblies` builds them and reports element, take-off, R-value/thickness and
  check deltas, including the `#53` assembly delta compare. Still missing: in-plan forks
  (`variant_of`/`active`/`forked_from` on storeys, one-active integrity check,
  promote-with-uid-remap) and the UI's side-by-side compare canvases (→ 21b §Variant compare).
  `model.json` also does not carry the variant catalog — `model_to_dict` has no house
  directory to read `variants.toml` from; variants surface as `out/variants.json` instead.
- **No `$` ranges in the delta compare.** `prices.toml` (#28) is unimplemented everywhere.
- **IFC storeys carry no elevation.** The exporter gives `IfcBuildingStorey` neither an
  `Elevation` nor a placement, so the M3 semantic equivalence cannot compare storey
  elevations at all. `test_catlin_equivalence_m3.py` asserts the current state explicitly, so
  it will fail loudly and demand a real comparison once elevations are emitted.
- **Opening details are never scaffolded.** 70 `opening_perimeter` conditions exist and 9
  overlay ids target them, but `derive_detail_slices` produces no slice for any (it requires a
  host wall + junction elevation). Same for the single `roof_ridge` condition. This is the
  largest remaining gap in detail coverage, and the fix is in `details.py` scaffolding, not in
  the vocabulary. Recorded in `UNDRAWN_RECIPES`.
- **Shower detail vocabulary** (`saunashowerdetail.json` `shower`: glass, recess, tile,
  backer, HRV duct) is undrawn. The four sauna items all draw.
- **Below-grade walls are modelled against outdoor air** in `energy.py`. Foundation UA is 915
  of 1,650 total — the biggest single inaccuracy in the block load. A correct fix needs ASHRAE
  below-grade F-factors or a design soil temperature, i.e. a new `Site`/`Preferences` input.
- **An unconditioned garage's clad walls still count as envelope** in the block load;
  excluding them needs room adjacency, not just storey occupancy.
- **Two library starter walls report UNKNOWN vapour permeance.** Their cladding layer carries
  `FramingSpec(1x4, vertical)` — it *is* a back-vented rainscreen — but is authored as
  CLADDING rather than a separate FURRING layer, so the rainscreen truncation misses it. Fix
  by re-authoring those two assemblies, or by sourcing a fibre-cement perm rating.
- **`lsl` and `fiber-cement` have no sourced permeance** and deliberately report UNKNOWN
  rather than carry an invented number.

## Catlin detail parity — remaining

The fidelity bar is the five hand-authored reference details in
`/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/*_ifc.png`; the
scripts that draw them and the parameter dicts behind them are copied read-only into
`packages/engine/tests/fixtures/catlin_reference/` (see its README). Compare against
`houses/catlin/out/render/detail_*.png` after `haus render . --view details`.

**The drawing vocabulary is now largely present** — flashings (Z/L, drip edge, apron), box
gutter, vent path, insect screen, sill gasket, sealant beads, thermal-break wedge, birdsmouth
seat-cut and I-joist flange dashes all draw as polyline+hatch derived from resolved faces, and
`Transition.overlay` recipe ids now dispatch through `OVERLAY_RECIPES` (4 recipes) with
`UNDRAWN_RECIPES` recording the 9 that deliberately draw nothing and why. What remains is
**style and item alignment** against the reference drawings, plus the opening-detail
scaffolding gap noted above.

- **`assembly-change-jog` is deliberately undrawn.** The jog runs *along* the wall while the
  derived detail cuts perpendicular at the wall midpoint, so that junction is not in the cut
  plane. Drawing it would be linework describing something the view does not contain.
- **`interior_slab_drip_flashing` was built and deleted.** Every derivable gate fired on the
  wrong details, because `SL-M-DECK` (suspended deck over the basement) and `SL-G-FLOOR`
  (slab-on-grade) are geometrically indistinguishable — both tops at z=0, both with their own
  thickness below. The distinction is "is there enclosed space beneath", which needs storey
  elevations the resolved `Room` does not carry. (The *assemblies* now encode the distinction;
  the geometry still does not.)

### Model fields the details still want

- **French drain.** `FootingBedding` models the drain as a bare `drain_tile: bool`. It needs
  `drain_diameter`, `drain_rock_width`, `drain_rock_depth` (or a `DrainTile` sub-model). The
  reference fixes 4"; the values are pinned in `detail_components/config.py` with docstrings
  naming the field that should replace them.
- **Sill gasket** wants a `FramingSpec.sill_gasket` thickness (reference: 1/4").
- **Slab thermal break** wants a perimeter-edge layer on the slab assembly (reference: 1").

## Phase 2 — Complete Catlin junctions

Phase 1 resolves same-assembly L/T/X geometry and ordinary exterior-wall/interior-partition
tees, and now resolves real corner squares from the junction solver's own output. Catlin
currently reports **zero** `integrity.junction_fallback` warnings. The remaining conditions
below are construction-rule authoring — they need your intent:

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence Catlin nodes with explicit
  bearing and layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions, including membrane laps,
  sealants, flashing, and thermal-control continuity. `Transition` remains post-resolve
  documentation and must not mutate construction geometry.
- Add `Node.junction_override` only if the Catlin audit proves an assembly/interface rule
  cannot express a real condition.

## Editor

- **Anchor-relative annotation drag → PatchOp editor.** The v1 detail viewer is still
  read-only.
- **Per-stud selection.** Wall bodies are pickable; individual framing members are not. Needs
  `InstancedMesh` instanceId picking plus a stable member-uid the engine emits. Note
  `FramedMember.trade` now exists for the "a fascia is envelope trim by category but the
  carpenter frames it" case.
- **Floor joists are not drawn in 2D**, so the "hide floors to read stair continuity" idea
  works in 3D only. Trades with no plan geometry (roof surfaces, floor joists, concrete
  solids, site) are badged **3D** in the Views panel rather than silently inert.
- **Console noise:** `THREE.Color: Unknown color model var(--material-siding)` from
  `nordic/palette`.

## Framing follow-ups

- **Windows: 8 residual member-interference overlaps** (measured with the check's
  junction-proximity clear disabled — the honest metric). 4 at two L corners where the
  *neighbouring* wall's studs run 1.5" above the wall's plate stack (an elevation mismatch
  between walls, not a corner-layout bug), and 4 at one T where an opening's jamb pack sits at
  the junction. Both are outside the corner rule. Total went 138 → 8; corner-stud 17 → 0;
  T-junction stud-stud 88 → 1.
- `FramingPreferences.max_window_ro_unbroken_in` no longer drives the ideal-position choice
  (geometry does); it survives as the declared header-free width and feeds a fix hint.

## Roof-eave follow-ups

- **Rake clip rules are extrapolated.** The golden reference draws the *eave* only, so the
  west/east-vs-south/north setbacks for a rake come from applying the same wall-stack clip
  faces there. A rake detail drawing would confirm (or correct) them. Same for the rake trim
  band: at a gable it stands in as rake trim, which is real construction but not something the
  reference confirms.
- **Layer end faces stay perpendicular to the slope**, not vertical as the 2D detail draws
  them: the mitered offsetter is what gives each layer its true thickness. The serialized
  setbacks are drift-corrected (`d·sinθ` at the eaves) so the edges land at the right *plan*
  positions, but the cut face itself is still raked.
- **No closed-cell spray-foam wedge at the roof/wall foam interface.** The reference cuts the
  wall foam flat at one elevation and fills the resulting angled mismatch against the sloped
  roof foam with spray foam. Each closure band here instead follows the slope at its own
  layer's plan position, so the mismatch never forms — the idealised version of the same
  detail. Modelling the wedge means modelling the flat cut first.
- **The roof-edge cladding band is a flat panel, not a formed edge.** A real standing-seam
  edge is a formed cleat + hemmed drip, and the band's four runs simply lap at the corners.
  Fine at model scale; a detail drawing would want the profile. See
  `plans/standing_seam_design_hints.md`.
- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls: a raked wall top is a straight line, so a gable wall must
  split at the ridge, and `W-G-E`'s ridge is exactly where the 16' overhead door is centred.
  Accepted for now; a second pass on the roof/wall eave detail should revisit it.

## Stair framing follow-ups

- **Framed-wall ledger emission.** `_bear_stair_on_walls` annotates a stringer/rim borne by a
  framed wall with `framed-wall-ledger:{tag}` but emits no member, so the take-off is missing
  the 2x ledger a framer installs. A wall's `axis` is its *centreline*, so any band drawn on it
  would be invented geometry inside the stud cavity — **blocked on D3**.
- **Winders keep the `tapered tread` 1.5" band.** A trapezoid is not expressible as axis +
  band width in this IR, and a going-wide band would make the fan self-overlap.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in the
future.

## File-size debt (AGENTS.md wants < 500 lines)

- `ui/src/components/Canvas2D.tsx` — **1812**
- `ui/src/components/Panel3D.tsx` — **1652**
- `ui/src/state/store.ts` — **680**
- `packages/engine/src/typehaus/resolve/stairs.py` — **736** (a clean three-way split —
  straight / u-split-landing / winder — exists but is a large diff)
- `houses/catlin/plan/assemblies.py` — **523**

(`emit/gltf/emitter.py` is done: 1425 → 182 across 10 modules, GLB byte-identical.
`detail_components.py` and `takeoff.py` are likewise now packages.)

## General polishing

- **Warnings.** `haus check houses/catlin` is at **127 pass / 7 fail / 0 not evaluable of 134
  rules, 0 ERRORs**. Every one of the 7 failures is listed under "Needs your decision" above —
  they are building facts, not defects. Nothing is unevaluable any more.
- **Emitters still place a recessed body at the floor plane.** `resolved_mount_elevation` does
  not read `Mount.recessed_into_host_surface`, so IFC/glTF draw catlin's registers sitting on
  the floor rather than let into their boots. Cosmetic; no check depends on it.
- **Wall-object protrusion is measured on the footprint's local-y extent**, relying on the
  library convention that local `-y` faces the room. Correct for every authored placeable
  today, but a wall-attached object rotated off that convention would be measured on the
  wrong axis. Revisit if wall attachments grow arbitrary rotation offsets.
- **The BOM is complete.** S-103 lists every member grouped by size and type with per-stock
  -length buckets; S-104 tables the derived connection hardware with a keyed basis-of-quantity
  note per row, plus structural solids by volume. `haus takeoff` prints the same sections.
