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

- **`mep.heating_capacity` now fails for real on the HP2 zone** (2026-07-31, newly
  measurable — see the envelope-wall fix below). Block load 30,764 Btu/h at design over the
  basement plus the main-floor bedroom/bath/living side, against 22,000 Btu/h of at-design
  capacity: **-8,764 Btu/h**. The radiant mats, the fireplace and the garage heater are
  excluded from the zone total by design (`plan/circuits.py` calls them supplemental), so
  the open question is whether the radiant is in fact carrying that difference — in which
  case it should stop being modeled as supplemental — or whether the zone wants a bigger
  outdoor unit. Was UNKNOWN before because four *interior* basement doors were being asked
  for envelope U-factors.
- **`electrical.receptacle_spacing`'s last catlin gap is the kitchen's north wall**
  (2026-07-31). RM-M-LIVING now reports one gap at (17.8', 35.9'): 13'-7" of wall between
  FO-M-STAIR's east edge and ED-M-LIVING-KGF1 over the dishwasher. Two things are tangled in
  it, and they want separate answers:
  1. 7'-1" of that run is full-height pantry casework (FURN-M-KIT-TALL-N/S, -PANTRY-E).
     NEC 210.52(A)(2)(1) breaks wall space at "fixed cabinets that do not have countertops or
     similar work surfaces" — so that stretch is arguably not wall space at all, and the check
     has no way to know. Teaching it would mean a real signal on the type (a work-surface
     flag), not a guess from height or `plan_symbol`.
  2. The counter run x 24'-7"..33'-4" carries **no 125V receptacle** over 6'-6" of it —
     only ED-M-LIVING-KET1, which is a 240V 6-20R kettle outlet and does not count. That is
     a genuine 210.52(C)(1) violation (no point on a countertop more than 2' from a
     receptacle) that the check explicitly does not evaluate. Two GFCIs at about x=26'-0"
     and x=28'-6" on CKT-KITCH-SA1/SA2 would close it. Related: the island receptacle item
     under "Items after Phase 6".

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

- ~~**`N-M-STRJ` junction WARN**~~ and ~~**W-M-STRW2 kept the standard gwb assembly**~~ —
  both closed 2026-07-30 by giving the 6" jog `CATLIN_MUDROOM_INT_2X6_EXPOSED` and
  W-M-STRW's alignment. One continuous plane, no 1/2" step, and the through-pair matches
  on material so the tee resolves. The jog itself has to stay a separate `Wall`:
  `resolve/topology.py` builds junction incidents from wall endpoints only, so the
  W-M-STOS2 tee needs a node both walls terminate at.
- **`N-M-STR1` junction WARN (honest fallback).** The successor to the above: W-M-STRS's
  2x4 `spf` partition dies into the end of W-M-STRW2's 2x6 `df-select-s4s`, and an L only
  resolves on an identical assembly or a shared bearing material. Physically a partition
  butting an end stud. Same underlying gap as before — `resolve/topology.py` wants a
  species-class notion rather than lying about the stud species — but now on a finish
  detail rather than on the bearing line.
- ~~**`electrical.receptacle_spacing`'s RM-M-LIVING gap now sits over the stair well**~~ —
  closed in the check 2026-07-31, as this entry proposed. `_floor_opening_intervals` breaks
  wall space where the room boundary runs within 12" of a `FloorOpening`, on the same footing
  as a doorway: 210.52(A)(2) measures "along the floor line" and a well is where the floor
  line stops. It also surfaced three receptacles that were *on* those ledges and therefore
  never reachable — ED-A-STUDY-RC1 (1 3/4" of deck against RM-A-STUDY's north wall) and
  ED-A-STUDY-RC2 (6 5/8" against its east wall), both moved; and ED-S-SUITE-RC2, which was
  not on a ledge but was sitting inside O-S-CLOSET's 4'-8" cased opening. RM-S-SUITE also
  gained ED-S-SUITE-RC7 on the 2'-2" of wall between D-S-SUITE and the closet opening.
  RM-S-SUITE and RM-A-STUDY now pass; only the kitchen wall above is left.
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

### Check-tier changes from the 2026-07-31 sweep

Catlin went from 30 build warnings to 1, and from 404 pass / 17 fail / 39 unknown to
411 / 7 / 20. Almost all of it was the checks describing the house wrongly, not the house:

- **A ≤4" wall projection clears a floor space at any height**
  (`resolve/placeable_clear_floor_obstruction.py`). A117.1 §307.2 states its 4" limit for
  leading edges above 27"; below 27" it sets no limit at all, so a body inside the stated
  limit is clear either way. The old code applied the allowance only above 27", which made
  every receptacle at 16"–18" AFF an "obstruction" of the floor beside a bed — eight of
  catlin's warnings.
- **A clearance zone stops at the owner's own footprint, and at a partition**
  (`resolve/placeables.py`). A `surround_zone` is authored as the whole enlarged rectangle,
  so a pendant hung over the table it lights read as an encroachment on that table's
  chair-use margin; and a zone drawn through a bedroom wall read as encroached by whatever
  stood in the next room.
- **A door leaf is stopped by the same bodies a clear floor space is.** The swing check
  shares `clear_floor_space_obstruction` now instead of testing plan overlap under the head,
  so a leaf passes over a flush floor register and clears a 2" switch plate.
- **Interior foundation walls are not thermal envelope** (`energy.py::_is_envelope_wall`).
  `is_foundation` was the whole below-grade test, but a basement's centre bearing walls carry
  that flag with conditioned space on both faces. 810 ft2 of catlin's bare interior concrete
  was in every block load, and four interior basement doors were being asked for envelope
  U-factors — which is what kept `mep.heating_capacity` UNKNOWN. HP2's zone load fell 38,548
  → 30,764 Btu/h and HP1's cooling finding became evaluable.
- **Three advisories report as facts, not verdicts** (`Result.PASS`, same message, same WARN
  severity): `advisory.window_size_variety` (any house has more than one window size),
  `advisory.floor_finish_over_radiant` (a commissioning constraint on a legal pairing), and
  `building_science.condensation.cold_snap` — whose own fix_hint says the monthly gate is the
  verdict and this is a screen. A fail count nobody can drive to zero is a fail count nobody
  reads.

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

- ~~**D2 — the winder turn does not fit in a 3'-0" well**~~ — closed 2026-07-31, no layout
  decision needed. The radial fan the numbers came from (narrow end 1.375", walk line 5.0")
  is gone: the fan is now laid out with narrow ends *constructed* at exact 6" offsets around
  the inside corner (`resolve/stairs/winder.py`, "the inside ends deliberately do not
  converge at the newel"), so the code-minimum path is built in rather than measured after
  the fact. Measured today: narrow end **6.0"** (= R311.7.5.2.1's 6" minimum) and walk-line
  going **11.1"** against the 10" minimum — both PASS, pinned by
  `test_stair_tread_geometry.py`. The well never widened; stair `width` (3'-0"), not the
  well, sets the walk-line spread. The "~2'-2" from the pivot" arithmetic described the old
  radial fan only.
- **Winders keep the `tapered tread` 1.5" band** — a trapezoid is not expressible as
  axis + band width in this IR. (These are also the only 3 of 2099 members without a real
  IFC representation, by design.) Sharper now that the turn is boxed: the band is the pie
  panel's *nosing/fan line*, and the box tier under it carries the panel's real footprint
  (true as of 2026-07-31 — see the next item). Wedge rings are now stripped of coincident
  and collinear vertices (`winder.py::_clean_ring`, guarded by
  `test_winder_wedge_rings_are_minimal_simple_polygons`): the first wedge no longer
  carries a zero-area excursion through the outer corner, which was the doubled outer
  edge line in plan and the overlapping pie panels in 3D.
- **The turn is framed Haun-style** (2026-07-25; re-framed 2026-07-31): one platform box
  per winder step, sides ripped to a riser less the deck (`1.5x6 rim`) so tiers stack dead
  flush, a diagonal block per box, rims ledgered to W-S-E1/W-S-SS2 (`bearing_refs`) and
  dying into the newel at the inside corner, and the straight flight landing on the top
  box's doubled departing rim. 2026-07-31: box `k` is now bounded by its *leading* fan
  line (`k-1`; the square's entering edge for box 0), so box 0 is the full corner
  platform, tiers nest wedding-cake, and every pie panel bears on its own box. The old
  framing bounded box `k` by its *own* fan line — complementary wedges, every panel
  cantilevered one riser above its support (the "floating pies" in 3D), and the top tier
  collapsed to two coincident rims. The two raked "winder carriages" and the slung header
  are gone — no framer cuts a compound-angle carriage through a turn.
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
  (2026-07-30: W-M-STRW/STRW2 are now the exposed-stud coat wall; the stair face is pinned
  by an explicit `alignment` so the well geometry cannot drift with assembly thickness.
  Same day, W-M-STRS was cut back to the well partition at x=14'-2 1/4" — it frames
  D-M-STAIR and stops — so the up-flight's lane is open to the living room. RO-1 went with
  the removed length, and RM-M-STAIR retired into RM-M-LIVING, since the well is inside
  that room's polygonized face now.)
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
- It looks like beams BM-S-HALL and BM-M-HALL are not getting grouped as part of the framing in the view. Also want to double check that beams are properly considered as a type of framing, for example the hall beams should likely be defined similarly to RIDGE-BEAM, garage header HEADER-0, the porch beams such as BM-SG-BKW, and possibly some of the window and door headers. We also may have some cases where we have headers specified over windows or doors when a large beam
- The 'Sun' slider doesn't actually seem to do anything. I think the basic idea was just to move a sun icon so users could get a sense of where the sun would be at certain times (not actually modeling shadows), but if that happens now, it isn't visible on the main canvas.
- The tube grow lights need to look in 3d more like suspended lights (which is basically a box with two poles/strings coming down from the ceiling on each end).
- We need a zoom in/zoom out little button to click (material design 3 style integrated)
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
