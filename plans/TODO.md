# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **Zoning height, after the lift — now 2'-10" (raised 2026-08-18, grew 2026-08-21).**
  Grade moved to -2'-6" so the house stands out of the ground, and to -2'-10" when the
  basement-ceiling overhaul put a 12 5/8" deck where a 9" slab had been and the house rose
  4" to keep the basement's headroom. The building's peak above average grade grew by
  exactly that much both times (`building_height_summary.peak_above_grade_m`, and the
  north/south elevations' ridge dimension). Nothing in the engine enforces a height limit —
  `SetbackSpec` is plan-only, and there is no `height_limit` on a jurisdiction profile — so
  this is a note rather than a check, but it is a real 2'-10" against whatever the local
  limit for this district is. If a limit is close, the levers are the attic's 11' ceiling
  and the 4:12 ridge, not the lift.

  **JURISDICTION CORRECTION, 2026-08-22 — the site is most likely SAINT PAUL, not
  Minneapolis, and "Minneapolis" in this repo has meant the metro generally.** That matters
  because the two cities measure height from different data, so the number this note is
  worried about is not the number `building_height_summary` computes:
  - **St Paul §520.160 measures from NATURAL GRADE at the curb**, or at a point 10 ft from
    the front lot line's centre — not from average grade around the building.
    `peak_above_grade_m` uses average grade, which is the datum every other check in this
    model shares. On a lot that falls away from the street the two disagree by the whole
    fall, and in either direction.
  - So **no `height_limit` and no check is being authored here.** Encoding a limit measured
    from a datum the model does not carry would produce a confident wrong answer, which is
    worse than the note. The item stays ON HOLD pending two facts only a survey and a
    parcel lookup can supply: the zoning district, and the natural grade at the curb.
  - **Two knock-ons of the correction, FLAGGED AND DELIBERATELY NOT CHANGED**, because both
    want confirming against Ramsey County rather than swapping on a guess:
    - ~~`plan/site.py:73` authors the ground snow load as "Hennepin County / Minneapolis".~~
      **DONE 2026-08-23, and the number did not move.** The citation is now **MN Rules
      1303.1700**, which is the document that actually sets it: 50 psf in every Minnesota
      county EXCEPT twenty-nine named northern ones, and neither Ramsey nor Hennepin is
      among them. So `ground_snow_load_psf=50.0` is right either way, and the citation now
      names the rule and its exception list rather than a county and a blank IRC table —
      which is what makes it survive the parcel lookup instead of needing to be redone
      after it.
    - `prices.toml [tax]` uses suburban Hennepin's **8.525%**. **HELD ENTIRELY, owner
      decision 2026-08-23 — the rate and its note are untouched**, because changing it before
      the parcel is confirmed would replace one sourced-but-possibly-wrong number with
      another. The research is done, though, so whoever picks this up is not starting cold:
      - **Suburban Ramsey is 8.375%** (6.875 state + 1.5 metro; Ramsey County levies no local
        sales tax of its own).
      - **The City of Saint Paul is 9.875%** (+1.5% city, since 2024-04-01).
      - MN taxes materials **where they are RECEIVED**: a job-site delivery takes the site's
        rate and a contractor-yard pickup takes the yard's, so a single house can legitimately
        carry two.
      Against the current 8.525%, suburban Ramsey is 0.15 points LOWER (~$450-900 on
      $300-600k of taxable material) and Saint Paul 1.35 points higher (~$4,000-8,100). The
      spread between the two candidate answers is what makes this worth the parcel lookup and
      not worth a guess.

- **What braces the porch and balcony east-west, now that the arch is gone?**
  (raised 2026-08-18, and the one item on this list that the arch swap *created*.) Removing
  `W-SG-ARCH` and the three `W-SG-RAIL-*` parapets removed the structure's only E-W shear
  element: the two side walls run N-S and brace that direction only, and the masonry the
  balcony pillars were grouted into was the de facto fixity for five of the six. Simpson say
  so themselves — ESR-1622/ESR-3050: *"post bases do not provide adequate resistance to
  prevent members from rotating about the base"*, and they are *"not recommended for
  non-top-supported installations (such as … guard rails)."* Nothing is authored for this and
  **nothing should be until it is decided** — a number invented in the model is worse than an
  open question. The options, in ascending cost:
  - **Extend the knee-brace rule to the centre pillars.** DCA6-2015 p.10 wants a brace on any
    post over 2'-0"; `PT-SG-BR2`/`BF2` are deliberately left as leaning columns today
    (`params/sunken_garden.py`, KNEE_BRACES) because bracing them pushes thrust into
    `PT-SG-BR2`, the one pillar bearing on porch decking. That reasoning is still right, so
    this is the cheap option and not obviously the correct one.
  - **A moment base at the four corner pillars.** `MPB66Z`, ESR-3050 Table 11: 2,680 lb-ft
    unreinforced — but it needs **5" of side cover**, which the new 16" square `PT-SG-FCOL`
    has and the 12" round `PT-SG-COL` does not. The four pillars that want it bear on 12"
    concrete wall tops, so it is not free there either.
  - **An engineer's lateral design.** The honest answer, and the same consultant the two
    side walls below already need.

- **DONE 2026-08-23 — the three sunken-garden items that stood here are closed.** Kept as a
  paragraph rather than deleted outright, because two of the three answers are worth
  carrying:
  - **"Treated LVL" is not a product.** The exposed beam item asked for treated Parallam Plus
    PSL. It cannot be had at 11 1/4": Weyerhaeuser make PSL in 9 1/4" / 11 7/8" / 14" / 16"
    only and forbid resawing it in depth, so the depth the whole porch is derived from was
    never buyable treated. All seven beams went to **3-ply KDAT sawn stock** instead — 3-2x12
    on the porch four and, after the second pass below, 3-2x12 on the balcony three too.
    The porch four are a strict improvement: `structural.deck_beam_span` grades them PASS at
    10'-0" against a 10'-3" limit where it used to report UNKNOWN, and their swap held every
    derived elevation to the byte (only the four front girt nodes moved, exactly 1/2", with
    the beam width).
    **The balcony three took a second pass the same day** and are now the same improvement —
    see the entry below.
  - **`CN-SG-HGR-W`/`E` were already `HUCQ410-SDS`**, retyped 2026-08-22. The item was two
    revisions stale; `prices.toml` still said `# 2 ea` for a part the takeoff bills 4 of, and
    that is fixed too.
  - **`W-SG-W1`/`E1` are `lateral_support="top_and_bottom"` with `#6 @ 38" o.c.`**, authored
    2026-08-22. The 1" residual that kept them UNKNOWN — they resolved 10'-1" against IRC
    Table R404.1.2(8)'s 10'-0" maximum — is closed: the walls are trimmed to exactly 10'-0"
    and `structural.foundation_unbalanced_fill` PASSES both. The inch came out of the wall,
    not the ground: `FT-SG-W1`/`E1` went 12" -> 13" thick so their undersides stayed put and
    the 21" of frost cover the R403.3 wing insulation is sized against did not move.

- **DONE 2026-08-23 (second pass): the three balcony beams PASS `structural.deck_beam_span`.**
  This was written up earlier the same day as ACCEPTED-not-open, on the reading that no
  built-up sawn size answers the 8'-8" span. That reading was right about the sizes and
  wrong about the row. R507.5(1) is indexed by the joist span a beam carries, and the check
  was handing it 10'-6" — the balcony joists span **10'-0"** beam to beam and then overhang
  the outer beams by `joist_cantilever_in` (6"), and `structural.deck_joist_span` was
  measuring the whole member and rounding that up to the 12' row. A cantilever is not span.
  Two changes, and both stand on their own:
  - **`checks/structural/deck.py` reads the back span now**, subtracting the authored
    `JoistSpec.cantilever` / `cantilever_start` / `cantilever_end` the resolver used to
    build the tips. It is read back off the member geometry rather than the member key, so
    it holds for any bay count including a single bay overhanging both ends.
  - **`structural.deck_joist_cantilever` is new**, and is where the overhang is now
    actually bounded: IRC R507.6.1, a quarter of the back span. Without it the fix above
    would be a loosening — a 5' overhang would have vanished out of both checks. The garden
    porch is the interesting case and it passes on its merits: 1'-5" against a 1'-10" limit.
  With the right row (10'), a 3-2x12 reaches 9'-2" against the 8'-8" span, so
  `SPEC.balcony_beam` went 3-2x10 -> **3-2x12** — the identical member to the porch pairs
  below it, in the same stocked KDAT. The four E-W girts followed it 2x10 -> 2x12 because
  they ride the same pillar tops and their tops have to finish in plane with the beams'.
  Costs ~$60-125 in material and nothing in labour (`prices.toml`, 1.04 -> 1.13 cy).
  The 2" of depth is real: beam soffit, pillar tops, girts and both knee-brace families all
  drop 2", headroom under the balcony goes 8'-7 1/2" -> 8'-5 1/2", and the walking surface
  at `balcony_level_ft` does not move. `_balcony_beam_depth_ft` and `_girt_depth_ft` are
  derived from the size strings now instead of hardcoded, which is what made that safe.
  **catlin is back to 0 FAIL**: `ACCEPTED_CATLIN_FAILURES` is deleted,
  `test_catlin_carries_no_failures` is restored, and `scripts/verify.sh` is off
  `--exit-on error` and back on the strict gate.
  **Note while reading the old item: its "open porch under a slatted balcony" premise was
  already stale.** `FS-SG-DECK`'s plank is `aluminum-deck` — Wahoo AridDeck-style, watertight,
  with a drip trough and leader — so the balcony beams sit under a DRY-BELOW surface and only
  the porch beams sit under gapped composite. That asymmetry is the real ESR-1387 5.3 story.

- **2D-edit sync — fix design proposed** (investigated 2026-08-02). Root cause confirmed: a
  PatchOp rewrites one constructor; derived data recomputes, authored cross-references
  don't. `retype_placeable` (2026-08-01) already re-anchors wall-fitted placeables and
  scans tag references. Still open, ~3–4 days if approved: (i) authored refs +
  advisory checks for geometry-coupled consumers (`Slice.subject_ref`, `DuctRun.serves`),
  (ii) promote retype warnings to durable review findings, (iii) route *opening* retypes
  through a centre-holding macro (raw PATCH still slides them today).
  **Re-affirmed deferred 2026-08-07.** One slice of it did land, though — see "Moving
  toilet needs to move its flange too" below, which was the same class of bug with a
  concrete instance behind it.

## Remaining Work

### Framing follow-ups from the 2026-08-25 corner audit

- **The 1/2" sheathing lap is undeclared.** `_clip_l_corner` (`resolve/topology.py:630-643`)
  mitres **all** layers on the angular bisector through the node; there is no per-layer logic
  and thickness is not an input, so the sheathing course mitres exactly like the studs
  behind it. Real sheathing laps: one wall's sheet runs long and the other's stops short by
  its thickness. Whichever wall loses the 1/2"x1/2" square starts its first sheet 1/2" late,
  so a 4' sheet breaks at 48.5" on a stud centred at 48" — 1/4" bearing, under APA's 1/2"
  minimum. `junction.framing_owner` **is** already available at `_clip_l_corner` time (a free
  input, zero plumbing) but the `PlanModel` is not, so an authored lap direction would need a
  field on `ResolvedJunction` populated in `_classify_tier`. `test_junction_solver.py:85`
  asserts no-gap/no-overlap but does **not** pin the 50/50 split, so a lap would still pass
  it. Sheathing takeoff area comes from the node axis (`takeoff/framing.py:265-272`), not the
  polygon, so the lapping wall's extra 1/2" per corner is never billed today — a second,
  pre-existing gap independent of the first. And nothing in the engine lays out sheathing
  sheets at all, so a "sheet break lands >=1/2" onto a stud" check has no home yet.

- **California corners as the next `corner_style` value.** `corner_stud_stations`
  (`resolve/framing/corners.py:125-143`) packs supplemental studs face-to-face with
  `orient=d` — the wall direction, same as the module studs. A California corner is one stud
  turned **flat** instead — `orient=normal(d)` — so it stands the same way a batten laid flat
  does, closing more of the corner cavity to a batt but landing a bay off the drywall
  screw-line. The extension is a third `Literal` value (`FramingSpec.corner_style` and
  `Wall.corner_style_start/end`) plus an orientation flag threaded through
  `corner_stud_stations`, not just a count change like 3-stud -> 4-stud was.

- **Plywood ordered by the sheet.** `takeoff/framing.py:117-141` bills every framing member
  by lineal foot, so a panel-profile member is billed as nested 8-ft sticks of
  `"NxN panel"` with a board-foot figure. There is no member-fed sheet-goods path
  (`sheet_goods_takeoff` at `takeoff/framing.py:253-310` reads **layers** only, never
  `model.all_members()`). Ordering plywood by the sheet — nesting panel-profile members onto
  4x8 stock the way `_bucket_cut_lengths` nests lumber onto stock lengths — is separate work.
  **Shrunk on 2026-08-26 by the catlin truss**, which is why this is worth less than it was:
  the corner box and the plywood tab both went with the Swinburne outrigger band, so the
  only panel members left on an exterior wall are the 176 window **bucks** (`6x0.375 panel`,
  560 LF ordered). The item stands, but it is now a ~$300 line, not a ~$1,200 one.

- **The girt bands have no RAKE NAILER at an attic gable.** `furring.course_elevations` runs
  the horizontal courses up a raked wall and they thin out toward the high end — correct as
  far as it goes — but nothing runs *along* the rake, so the top foot or so of cladding on a
  gable end has a nailer only where the last full course reaches it. On the Swinburne wall
  the vertical outriggers ran to the raked top and this did not arise. What it wants is one
  raked `strapping-{band}-rake` member per band from the topmost full course to the peak
  (`FramedMember`'s `z0_end_m`/`z1_end_m` already carry a raked member), with blocks at the
  module along it. Deferred out of the 2026-08-26 girt work deliberately: it is its own step,
  it touches only the four attic gables, and it is a construction note today rather than a
  hole in the model.

**Deliberately not done, and why:**

- **The four exterior placeables keep their false room refs** (both wall hydrants, both
  porch curtain rods). Giving them an honest home means unconditioned `Room`s for the porch
  and the balcony — enclosing walls, envelope, energy and ventilation consequences — for
  four UNKNOWNs this file already accepts. Not worth the complexity.

- **In-plan variant forks + compare UI** (deferred again by decision 2026-08-02,
  **re-affirmed 2026-08-07**). `model.json` now carries the variant catalog; `prices.toml`
  $-ranges work in `haus variants compare` and takeoff. Still missing: `variant_of`/`active`
  forks with one-active integrity + promote-with-uid-remap, and the UI side-by-side compare
  canvases.

- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span` itself is fully green:
  two genuine R507.5(1) overspans closed 2026-07-31 by going engineered, and the balcony
  three closed 2026-08-23 prescriptively — see the second-pass entry above.)
- **Windows: 4 residual member-interference overlaps** — now **pinned** by
  `test_catlin_window_member_overlaps_pinned_at_four` (junction clear disabled — the
  honest metric). Measured composition drifted from this file's memory of 4+4: it is 2 at
  one T (CSW148's king stud), 1 L corner, 1 vs the stair soffit plate. The T was 6 until
  2026-08-22, when O-S-VANITY moved off the corner square that the 8" suite sound wall grew
  the day before — its whole jamb pack had been standing inside it. (Historic: 138 → 8 → 4.)

### Residuals from the 2026-07-30 batch

- **The mudroom 6" jog has to stay its own `Wall`** — a standing constraint, not a task.
  `resolve/topology.py` builds junction incidents from wall endpoints only, so the
  W-M-STOS2 tee needs a node both walls terminate at; merging the jog re-opens `N-M-STRJ`.
- **RM-S-PLANT / RM-S-STUDY2 fresh-air terminals — DRAWN (2026-08-16), closing the
  2026-07-30 "by decision" gap.** The study was always the anomaly: `EQ-S-HP1-AH` hangs in
  RM-S-STUDY2's own ceiling soffit, and a room does not breathe by being next to the
  machine. Both now take System 1 air from `DU-S-HP-SOUTH`, a new 8x6 branch in the
  FS-ATTIC joist bay at y=3'-4" — nothing can leave the trunk southward inside SF-S-DUCT
  (the 21"x43" air-handler case fills the box y 6'-0"..9'-7"), and nothing can run west
  along the attic deck (W-A-C1/C1B, the bearing wall under RB-HOUSE), so the branch goes
  over both rooms inside the floor cavity and passes under that wall's bottom plate.
  Terminals: `REG-S-HP-STUDY2` (22'-8", 3'-4") and `REG-S-HP-PLANT` (6'-8", 3'-4"), ceiling
  grilles at 9'-0". 150 cfm is taken out of the trunk's 750 by damper, not added to it.
  The mini-HRV idea for the plant room is dropped — it was solving a distribution problem.
  `mep.ventilation_distribution` now names no unserved room and the test pins the empty set.
  Residual: `DU-S-HP-SOUTH`'s rise is still undrawn — see the item below.

### Undrawn verticals — TWO OF THREE CLOSED (2026-08-25)

`DuctRun` had no elevation field at all, so every vertical leg in the house's air side was
a plan polyline that teleported between floors, ducts emitted no 3D solids, and the take-off
billed plan length. It carries per-vertex elevations now, the same field set `PipeRun` has
had since MEP Phase 2 and solved by the same solver — a riser is a repeated plan point at
two elevations, which is exactly how a drain drop has always been written.

- **`DU-A-HP-STUDY`'s riser lane — DRAWN.** The branch comes up out of the FS-ATTIC joist
  bay it shares with `DU-S-HP-SOUTH` (centreline 228 1/8" + 3") onto the attic deck and
  turns east. 11 7/8" of rise the take-off now bills instead of projecting to zero.
- **`DU-S-ERV-HP-FEED`'s rise — DRAWN, and the run rebuilt around it.** It no longer taps
  `DU-M1-ERV-SUP` (that trunk is deleted with the rest of the rectangular ERV). It comes off
  the attic sub-manifold, rides the FS-ATTIC bay at y=11'-4" east, and **drops into
  SF-S-DUCT** onto the new `EQ-S-ERV-MIX` mixing box — a modeled box with a backdraft damper
  on the ERV leg, which is what keeps System 1's return working when the ERV is off, and
  which replaces a comment describing a 45-degree wye.
- **`DU-S-HP-SOUTH`'s rise — STILL OPEN, and now for a reason rather than for want of a
  field.** Every comment in `plan/mep_hvac.py` calls it "the riser out of the trunk head at
  x=19'-4"", and the trunk head is at (19'-4", 9'-7") — but `SF-S-DUCT` stops at y=6'-0" and
  the branch drops into its bay at (19'-4", 3'-4"). Nothing connects those two points without
  either crossing five FS-ATTIC I-joists in a bay (illegal) or running along the attic floor
  through a habitable room. Both are route decisions rather than draughting, and the
  2026-08-25 pass was explicitly forbidden from moving a System 1 trunk. Decide the route,
  then draw it: the field is there and waiting.

### ERV residuals (2026-08-25)

- **`[ducts]` is priced on a blend.** The BOM keys that section on `system` alone, so one
  `supply` rate covers 6" insulated riser, 3" semi-rigid radial and 14x8 galvanized trunk —
  three products at three prices. `duct_takeoff` already reports `material` and
  `diameter_in` per row, so this wants the qualified-key treatment `[drainage]` and
  `[wall_structure]` already have (`cli/prices.QUALIFIED_KEY_FIELD`).
- **The ERV's condensate shares FX-B-SAUNA-FD rather than tying into `PR-B-COND`.** The
  arithmetic is in `plan/mep_drainage.py`: the condensate main is at 85"-and-change where it
  passes x=13'-6", and the highest a 21.6" case can put its spigot under an 8'-0 15/16"
  basement ceiling is about 75". There is no gravity connection to be made. The alternative
  the plan floated — the mechanical-room sink — still has no drain, which is the open item
  below and the one that would actually fix this.
- **Radials cross one another in the FS-S-WEST field, ungraded.** Nothing in the engine
  grades duct-against-duct outside a modeled `Soffit`; an 11 7/8" bay with an 8 7/8" web
  opening has room for one 3" duct to pass under another, so it builds, but the model cannot
  say so. `mep.duct_soffit_occupancy` is the shape the joist-bay version would take.
- **`DU-A-ERV-R-PLANT` is the longest radial in the house** — attic manifold at the north
  end to the plant room at the south. Its pressure drop wants checking against the machine's
  0.2" w.g. before 75 mm is committed to; there is no airflow solver here and there will not
  be one.

## Phase 2 — Complete Catlin junctions (deferred by decision 2026-08-02 — construction-rule authoring)

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence Catlin nodes with explicit
  bearing and layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions (membrane laps, sealants,
  flashing, thermal-control continuity). `Transition` stays post-resolve documentation.
- Add `Node.junction_override` only if the audit proves a rule cannot express a condition.
- `model/views.py::ConditionKey` (plus `Continuity`/`LayerJoin` alongside it) is schema-only,
  unreferenced until WP1.4 condition derivation lands (→ 11b §Transitions, decision #37) —
  keep it in place, don't flag it dead.

## Breezeway

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a `Beam` is a prism). If the wedge becomes a real element the fall moves into it. (It should be a 1" slope by angle of the framing, plus a east to west slope by a small wedge under the centerpoint of each rafter to slightly bend the polycarbonate)
  **Re-affirmed deferred 2026-08-07:** framing the fall means a sloped-`Beam` schema change,
  which is a bigger piece of work than the batch it kept coming up in.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Pantry (deferred by decision 2026-08-02)
- **The showers are still unclassified.** Same axis, same rules, same question to answer
    first: what is actually behind the tile. The sauna is the worked example of what
    answering it costs — a liner variant on the wall that turned out not to have one.
  - **`FX-S-BALC-HYD`'s sleeve.** A freeze-proof wall hydrant passes through the plant room's
    liner into a −15 °F wall — a vapour leak and a cold surface at once. Needs a sealed,
    insulated sleeve detail; `SleevePenetration` exists but not for this condition.
  - **Cavity "canary" RH sensors** in a south and a west stud bay. The liner has no
    redundancy, and this is how a failure is caught in month three rather than year five.
    There is no sensor element kind.
  - **The humidifier.** An ERV loses ~16 % of the moisture in every air change; at this flow
    against −15 °F outdoor air that is 1.5–2 gal/day unrecovered. Not modelled — it wants an
    `Equipment` with a water supply and a drain.
  - **The room's clear face does not know about the liner.** `RM-S-PLANT` still resolves at
    159.15 sf; the 1 1/4" liner should take it to about 152. `resolve/rooms.py::_lining_inset`
    insets a claimed face by a single uniform figure derived from `Room.wall_lining` (0.635",
    the painted-gypsum stack) rather than by each bounding wall's own resolved lining, so the
    face sits on the node lines less that constant — which is why the sauna's 3 1/2" liner
    does not move its room polygon either. Systemic and pre-existing; fixing it moves every
    room's area and every `clear_face`-derived check at once, so it is its own change. Until
    then R303.1, the clear-floor checks and the finishes takeoff all grade RM-S-PLANT on a
    floor slightly larger than the one that gets built (which is the conservative direction
    for the glazing ratio, and the wrong one for clear floor).
  - **A floor drain in RM-S-PLANT** (the room should be hoseable): implies a drain line, a
    trap primer — the trap *will* dry — and slope in `FS-SECOND`. See the Questions list.
  - `SL-SG-DECK` is gone: the aluminium plank is `FS-SG-DECK`'s `subfloor` and bills as
    182.0 SF in `[sheet_goods]`. The conversion was exact — the balcony joists cantilever 6"
    and the deleted slab's outline *was* that cantilever.
  - **`SL-BW-DECK` stays a Slab, and that is the finding.** It was converted with the
    balcony and converted back the same day. `resolve/floors.py` draws a subfloor
    bearing-line to bearing-line by the outline's perpendicular extent, so a floor system's
    sheet is exactly its joist field; the breezeway plank oversails its rim 2 3/4" at each
    end onto the two door thresholds. Keeping the post-box outline FAILS
    `code.R311_3_exterior_landing` on D-M-ENTRY and D-G-SERVICE (a door has to open onto
    something); stretching the outline to the faces lays a joist through PT-BW-1..4 and its
    own neighbour, five `structural.member_interference` FAILs. These joists are hung flush
    between the beams and cannot cantilever. **The engine has no way to say "sheet wider
    than joist field", and that is the change this wants** — not a re-model of the deck.
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- Window sealing detail (RM-S-PLANT's is drawn — TR-CATLIN-PLANT-OPENING, 2026-08-18 — and
  is the strictest case in the house; the rest of the envelope still rides
  TR-CATLIN-FRAMED-OPENING)
- Does balcony access have to pass through the plant room? `D-S-DECK-W` is a 60" exterior
  French door in a 70 %-RH room and its threshold will condense (raised 2026-08-18)
- Floor drain in RM-S-PLANT — Answer: No floor drain necessary. Spilled water is mopped up as needed.
- Make sure all desired access panels are in
- Small windows on corners?
- Improve the symmetry of the windows on the east and west side
- Permit drawings
- The house's own strip footings are eccentric under their walls, the same way the garage
  stem's were before 2026-08-15: `FT-B-*` is a 20" strip centred on the y=0 node line,
  under a `face("concrete-ext")` wall whose concrete runs inboard from it. **The -2" north
  toe in this note is stale**: that wall went 12" -> 8" on 2026-08-21 and only its inside
  face moved, so the south toe is 10" and the north one is now **+2"**, not -2".
  `Footing.center_on="wall"` now exists to
  fix it, but it is deliberately *not* authored there: the glazed-brick plinth's whole
  derivation (`params/foundations.py`, `FT-B-BRICK`) leans on that 10" toe being there
  to bear on. Correcting the footings means re-deriving the plinth with them.

* **Is this enough glazing for light-feeling rooms (along with LED strips, etc)?** Still
  open, and deliberately: 8% is the code minimum, not an answer about how a room feels. But
  the numbers are knowable, so here they are —
  `code.R303_1_light_and_ventilation` prints them for every habitable room, pass or fail:

  | room | glazing | floor | ratio | openable | ratio |
  |---|---:|---:|---:|---:|---:|
  | RM-S-PLANT | 26.7 sf | 159 sf | **16.8%** | 13.4 sf | 8.4% |
  | RM-S-STUDY2 | 26.7 sf | 159 sf | **16.8%** | 13.4 sf | 8.4% |
  | RM-M-BED | 33.5 sf | 231 sf | **14.5%** | 16.7 sf | 7.2% |
  | RM-S-BED3 | 14.2 sf | 129 sf | **11.0%** | 7.1 sf | 5.5% |
  | RM-A-STUDY | 15.0 sf | 159 sf | **9.4%** | 7.5 sf | 4.7% |
  | RM-S-SUITE | 13.5 sf | 154 sf | **8.8%** | 6.7 sf | 4.4% |
  | RM-S-BED1 | 10.0 sf | 120 sf | **8.3%** | 5.0 sf | 4.2% |
  | RM-S-BED2 | 10.0 sf | 124 sf | **8.1%** | 5.0 sf | 4.0% |
  | RM-M-LIVING | 49.3 sf | 766 sf | 6.4% | — | — |
  | RM-M-STUDY | 0.0 sf | 19 sf | 0% | — | — |
  | RM-B-GYM | 0.0 sf | 324 sf | 0% | — | — |
  | RM-B-PLAY-N | 0.0 sf | 324 sf | 0% | — | — |

  The top eight clear R303.1's 8% glazing and 4% openable outright, and two of them do it
  twice over. **The bottom four pass under R303.1 Exception 1** — artificial light plus
  mechanical ventilation — and they are where the question actually lives:
  - **RM-M-LIVING at 6.4%** is the one worth arguing about. It is a 766 sf open plan and it
    is 12 sf of glass short of the code line, which on a room that size is one more window.
  - **RM-S-BED2 at 8.1% and RM-S-BED1 at 8.3%** clear by 0.1 and 0.4 sf. That is not comfort,
    that is a rounding margin — and `houses/catlin/CLAUDE.md` already records that growing
    either room's clear face fails R303.1 again.
  - **RM-B-GYM and RM-B-PLAY-N have no glass at all** and are lit to 7.4 fc. They are
    basement rooms and always were; whether that is acceptable is a use question, not a
    daylight one.
  - **RM-M-STUDY's 19 sf** is a nook, not a room. Ignore the 0%.
* Plan a revamp off the plumbing to see if we can make any of the runs more efficiently routed. Try to run things through the NW corner of the house's maintenance shaft.
  (**The shutoff half of this item is DONE 2026-08-23** — see the stops below. The routing
  half stays open.)
* **DONE 2026-08-23 — branch and fixture stops.** The house had exactly one valve you could
  close (`PA-B-MAIN-SHUTOFF`) plus a hydrant isolation, so changing a tap meant shutting the
  dwelling off. Fifteen `SHUTOFF` accessories now cover the five bath groups, the kitchen,
  the laundry and the water heater's cold inlet, all `accessible=True`.
  **They sit at the fixture end of each branch, not at the tee, and that is a compromise
  worth knowing about:** every branch tee in this house is at the basement ceiling plane,
  which is 5/8" gypsum end to end, and the four access panels the house owns serve a WC
  carrier, two tub wastes and the NW shaft — none is over a supply tee. So these isolate a
  fixture GROUP at its point of use; working on the pipe between the tee and the room still
  means closing the main. **Putting a real stop at each tee is an access-panel decision and
  it is the open residue of this item.**
* How can we properly anchor the heat pumps on the upper porch without compromising the waterproofing of the aluminum decking? Perhaps we need a different subtype of flooring there?
* **DONE 2026-08-23 — `EQ-B-ESS-BATT` and its Type X closet are in the NE corner.** The
  blocker was `EQ-B-WH`, the water heater, standing in that corner itself; the owner's answer
  was to move the tank, and it went to (5'-6", 24'-0") — south of `EQ-B-ERV`, north of
  `D-B-FURN`'s swing, and clear of the 36" NEC 110.26 working space in front of the panel
  wall. `advisory.ess_clearance` PASSES; put the tank back and it FAILs naming `EQ-B-WH`,
  which is the check that the move is what unblocked it. Three things the item did not
  anticipate, all now in `notes/backup_power.md`:
  - **The corner had no split walls to tee into**, so `W-B-N3` split at x=6'-0" (which is
    `N-M-MECH3`'s line, so the two storeys break in the same place) and `W-B-STR` at
    y=31'-0" (which has no such line — `W-M-STRW` crosses it). `FO-M-STAIR.bearing_refs`
    needed `W-B-STR3` adding or the resolver emitted a 9'-0" LVL header over the stair well.
    (Both walls are framed 2x6 since 2026-08-24 and `W-B-STR` carries the closet's Type X
    leaf on its own assembly; `advisory.ess_enclosure` passed on the pour's mass before and
    passes on that leaf now.)
  - **The tank's coordinate was a literal in eight places** — seven supply runs plus the T&P
    line — and nothing pulls a pipe onto its equipment, so moving it alone would have
    silently disconnected the hot trunk, the cold feed and five branches with the model still
    green. `test_water_heater_connections.py` now pins all eight against the resolved model.
  - **The DC run to `EQ-B-ESS-INV` got ~10' longer.** Flagged on the battery in
    `plan/electrical.py`; a real voltage-drop question on an EG4 12kPV, and the one argument
    that could still send this back. Against it: the battery hangs on cast concrete again
    rather than on the steel studs the 2026-08-21 overhaul left it on.
  - There was never a pan (`mep_drainage.py` explains why P2801.6 needs none) and never a
    vent. The item said both; neither was ever authored.
 - Sunken garden slab (is it needed above footing) and make sure 7" threshold to basement from sunken garden
 - Basement under the stairs storage closet
 - Wall W-B-CS is likely worth making a wood stud wall (if the load bearing math works and the cost is noticeably lower)
 - PLATE-BOTTOM in the garage is still shown incorrectly going right through the overhead garage door (it should terminate where the ICF stem wall does on each side, not going across the opening)
 - For the breezeway sonotubes, something like https://www.homedepot.com/p/Bigfoot-20-in-Pier-Footing-Form-489-20-BF/300325004 for a "single pour footing". However right now it looks like those footings bisect the house and garage foundation walls. Perhaps the beams should be slightly cantilever to push them further out? Or we could link it in straight to the garage footings as one level?
 - ~~The sidebar of the UI shown when items are selected should show the material, if applicable, and chosen product brand/id/name if applicable.~~
   **DONE 2026-08-24, and the second half needed a model change rather than a panel change.**
   *Material* was nearly free: every selectable element already carried a material or an
   assembly tag on the wire, and the one real gap was `Solid.material` — shipped in
   `model.json` since the trim-run work and never rendered, so a gutter, fascia, soffit,
   ridge cap or railing part showed `Assembly —` and nothing else while the viewer coloured
   it from that exact field. `SolidInspector` prints it now.
   *Product identity did not exist as structured data* — a chosen product was prose in a
   type's `name=` with the model number buried again in `source=`, which no panel can lay
   out and no estimator can join against. There is a `Product` catalog record now
   (`model/product.py`), referenced by `product_ref` from `Material` and every `*Type`, with
   `integrity.unknown_product_ref` refusing a dangling one; the sidebar prints brand / model
   / product / SKU wherever a selection resolves to one, and the estimate row carries the
   *specified* product so `costs.toml`'s `product` field records only what actually differed
   (decision #63).
 - Hover text should display in front of all items in the UI
 - **DONE 2026-08-24 — the sectional faced the wrong way because a `footprint_shape` and a
   glyph disagreed.** `FT-SECTIONAL-U-MEDIA`'s ring was authored opening toward +y so an
   *unrotated* instance would face north at the screen, but every seating family in
   `model/placeable_symbols/_families.py` puts its back band at +y and faces -y. The
   collision outline faced the panel; the body you see never did. `footprint_shape` is read
   only by `resolve/placeables.py:_local_footprint`, so nothing in `haus check` compares the
   two — **that gap is still open** (see the clearance-vs-body note below: the checks grade
   declared zones, not what a symbol actually draws). Ring re-authored to the engine's
   convention + `rotation=deg(180)` on the instance; world geometry byte-identical.
   Bookcases went 6'-0" -> 7'-6" on a house-local `FT-BOOKCASE-32-90`, a 6" reveal under
   RM-B-PLAY-N's measured 8'-0" clear (`code.R305_ceiling_height`) — same 2'-8" x 1'-0"
   footprint, so no plan dimension moved. Note the 8'-3 1/2" ceiling quoted in
   plan/placeables.py for the screen was two revisions stale; it is 8'-0".
 - Add some wire shelves and racks to the dedicated closets (mudroom closet aimed at jackets)
 - **DONE 2026-08-24 — a rail is one solid.** `SolidSweep` + `resolve/sweep.py` (→ #62):
   `RL-A-HANDRAIL` went from 297 solids to 6 (one rail plus five brackets), railings from
   1,149 of the house's 2,857 solids to 295 of 953. One glTF node, one `IfcRailing` (a round
   section as a real `IfcSweptDiskSolid`), one plan polyline, one click to select. Posts,
   brackets and infill are unchanged — those are genuinely discrete pieces.
 - **DONE 2026-08-24 — and it did share the code, exactly as guessed.** One `ResolvedSolid`
   per run carrying its own 3D polyline, mitred by the same `resolve/sweep.py` the handrails
   use; `sloped_run_bands` and its "accepted approximation" are deleted, and a vertical drop
   is now just a leg whose direction happens to be down. Two things came with it: a run may
   author its **grade** (`PipeRun.slope_in_per_ft`) and leave the inverts it implies as
   `None`, and fittings are **counted** off the geometry rather than estimated off a 20°
   plan-turn heuristic — which re-based the drain/vent `$/LF` to bare pipe (→ #62).
 - Run a stud alignment pass, and a "custom where standard item could be swapped in" pass
 - As unfinished space, can we just leave exposed subfloor in the attic storage rooms?
 - **DONE 2026-08-24 — the door, the wall and the node are all gone; the head of the stairs
   is open on both lanes.** `W-M-STRS` could not simply lose its door: `D-M-STAIR` filled
   3'-4" of a 4'-2" partition and was the only way onto `ST-B2M`, so a doorless wall there
   would have sealed the basement flight off. Removed instead: the door, the wall, node
   `N-M-STR2`, and `ED-M-LIVING-RC11`, the receptacle that had nothing left to hang on.
   `N-M-STR1` is now `W-M-STRW2`'s free south end (`open_end=True`), which also retired the
   `integrity.junction_fallback` UNKNOWN that the mixed-assembly L there had been raising.
   Two things the item did not anticipate:
   - **The wall had been covering an open floor edge by accident.** With it gone,
     `code.R312_1_guard` FAILed `FO-M-STAIR`'s south edge over x 13'-9 3/4"..14'-2 1/4" —
     the 4 1/2" the shaft reserves between the two flights, open from the basement slab to
     the second floor. Not a fall-through, but wider than R312.1.3's 4" sphere and a
     foot-catcher at the top of a flight. Closed with `RL-M-STAIRHEAD`, a 4 1/2" guard on
     the same faces and of the same family as `RL-S-STAIRHEAD` one storey up — a newel in
     the field. No guard is needed across either lane itself: both flights meet the floor at
     their nosing.
   - **More of `W-M-STRW2`'s appearance-grade west face is now in the open** — 6" instead of
     1 1/4", at the head of the stairs rather than in a corner. It still reads as the
     mudroom wall's exposed-stud return, and the "keep MEP out, a bored stud shows" rule on
     that wall matters more now, not less.
 - Access panel FURN-M-BATH1-AP is in the wrong spot, probably needs to be on W-M-HS1
 - Are horizontal hat channels necessary for the siding of the house? (nail flange over 20 ga galvanized hat channels)
 - D-M-BED2 door can likely be moved slightly to optimize the stud line

- **The sunken garden was a real frost defect, not a review item.** `structural.frost_depth`
  compared every footing to one global grade plane (`Site.grade`), so it PASSED all 35 —
  including `FT-B-S1/S2/S3` with 8" of cover below the garden floor and `FT-B-BRICK` with 2"
  of NEGATIVE cover. Frost depth is measured from the lowest *adjacent* grade (IRC
  R403.1.4.1), and beside those four that is the garden floor at -9'-4". The check derives a
  local grade per footing now; the four are answered by IRC R403.3 wing insulation under the
  garden slab (`SL-SG-FROST-*`) and an FPSF footing form; the garden's own seven footings
  report UNKNOWN and go to the engineer who already owns those walls (R404.4).
- **The garage "stairs" were five concrete `Slab`s**, invisible to `structural.
  stair_riser_uniformity` and `code.R311_7_8_handrail` alike, so a 5-riser flight with no
  handrail drew no finding at all. `Stair.floor_opening` is optional now and
  `base_elevation`/`top_elevation` state a rise directly, so a step-down within one storey is
  expressible: `ST-G-SERVICE`, KDAT, with `RL-G-SERVICE` over it.
- **The ethernet could not ride the spa conduit.** NEC 800.133/725 forbids comms sharing a
  raceway with power, and the model already encodes it (`ConduitRun.service` is one value).
  The route was right; the pipe is not shareable, so `CD-B-DATA-SHOP` runs parallel to
  `CD-B-SPA`, 6" east of it.

Three things NOT done and deliberately left:

- **The R312.1.1 guard on the garage stair's 34" landing.** An owner decision with a cost
  and a look to it, flagged in `plan/storeys/garage.py`. It comes with an engine gap worth
  its own item: `code.R312_1_guard_height` censuses `FloorSystem`s and `code.R312_1_guard`
  censuses `FloorOpening`s, so `SL-G-STEP-0` — a `Slab` — is in neither census and its 34"
  drop is graded by nothing. A rule that walks slab edges would close it.
- **`ED-B-GYM-RC3`/`RC4`** are authored on the wrong side of `W-B-CE`'s finish face
  (y=18'-4.385" against a face at 18'-3 3/8"), so they resolve inside the media room while
  counting toward the gym's NEC 210.52 6-foot rule. They carry no `room=`, so nothing
  reports it. Fixing them means re-running the gym's NEC fill.
- **`FT-SG-*`'s frost cover**, 12"-21" below the sunken garden's own floor against 42".
  `structural.frost_depth` routes all seven to UNKNOWN — a structure retaining the
  excavation it stands in is an engineered design under IRC R404.4, and
  `structural.foundation_unbalanced_fill` already sends the same walls to the same
  consultant. The permit checklist's "Foundation frost depth" item is UNKNOWN because of it,
  and `test_catlin_contract_m3.py` pins exactly that so nothing else can regress behind it.


## Questions from 08-15 session

~~The starter template gained 4 advisory FAILs.~~ **ANSWERED and DONE 2026-08-23.** The
alternatives offered were "a full electrical package" or "loosen the checks". The answer was
neither: `houses/starter/plan/electrical.py` + `plan/circuits.py` are the *smallest honest*
package — one 20-space panel, four circuits, a light + switch in each of the two habitable
rooms, and NEC 210.52 receptacles on their wall lines (eight in RM-Main, nine in RM-Upper).

The result is the gate the item asked for: **the four FAILs are gone, six UNKNOWNs resolved
into twelve PASSes, and not one new finding of any kind** — verified by diffing the whole
`haus check --only all` report before and after. Unlike the four `advisory.control_continuity`
FAILs the template still carries deliberately, none of this is an opinion about a specific
building, which is why it belongs in a template and a rim-band flashing detail does not.

### Plumbing

  Deliberately left for later:
  - **No hose reel, hanger or splash block** at either hydrant, and no water leak/freeze
    `Alarm` anywhere in the house. (Re-affirmed deferred, 2026-08-02.)
  - **The RO unit itself.** `PA-M-RO-STUB` is a capped 1/4" tee with no fixture and no
    fixture units — the provision, not the machine.
  - **`mep.backflow_prevention` grades hose connections only.** The basement's two dual-check
    preventers are reported where authored but are not *required* by the check — a general
    cross-connection survey (hose-end sprayers, the boiler fill that does not exist yet) is
    not encoded.
  - **The wall hydrants draw an `integrity.placeable_room_mismatch` apiece**, which is the
    true description of an exterior hose bib hosted by an interior room's wall rather than a
    defect. The model has no outdoor-room concept to file them under.

Make sure the basement door keeps the 7" step threshold (reduces flood risk)

## Found while doing the 2026-08-23 batch — recorded so they are not rediscovered

- **The published web app runs a GEOS a version behind the dev venv, and a geometry bug can
  therefore ship green.** `.venv` is Shapely 2.1.2 / GEOS **3.13.1**; the app runs the engine
  under Pyodide 0.26.2, which is Shapely 2.0.2 / GEOS **3.12.1**
  (`ui/src/engine/pyodide/worker.ts`). GEOS 3.13 hardened OverlayNG's noding, so 3.12 raised
  a **fatal** `TopologyException` unioning the basement wall bodies in
  `server/space_summary.gross_area_sf` — it killed the worker, so type-haus.com/app never
  rendered — on input rings that carry no defect of their own and that 3.13 absorbs
  silently. Fixed by routing that overlay through `resolve/overlay.py`'s fixed-precision
  (1 micron) helper; measured area-neutral to within a square millimetre per storey.
  **The class of bug is the item.** Either pin a Pyodide smoke test into CI
  (`.github/workflows/deploy-site.yml` already builds the site, and a headless
  `node` + `pyodide` run reproduces it in about 90 seconds) or bump Pyodide — 0.28.x ships a
  newer GEOS. Until one of those, `pytest` passing proves nothing about the published app's
  geometry.
- **The offline PWA's `costs_json` is broken.** `OfflineEngine.costs_json` imports
  `typehaus.cli.prices`, which triggers `typehaus/cli/__init__.py` -> `app.py` -> `typer`,
  and the worker loads only micropip/pydantic/shapely. It raises `ModuleNotFoundError: typer`
  in the browser. Found with the same Pyodide harness as the item above; unrelated to it.
  The fix is to move `load_prices` out from under the `cli` package's import side effects.
- **There is no trap-primer element, field or `PipeAccessoryKind` member.** This is what
  blocks the `RM-S-PLANT` floor drain: `library/placeables/fixtures.py:108-110` says the
  existing `FX-FLOOR-DRAIN` type is for wet-room floors and *"a floor drain in a room that
  stays dry for months wants a primer line, which would be a different type."*
- **`ResolvedRoom` carries neither clear height nor glazing ratio** (`resolve/model.py`).
  Every consumer re-derives them and neither reaches `model.json` — which is why the glazing
  table above had to be scraped out of check messages rather than read off the model.
- **Four `AlarmKind` members only** (SMOKE / CO / COMBO / HEAT). No leak or freeze kind, and
  `emit/draw/floorplan.py:316-317` is a hard index that `KeyError`s the whole plan sheet on a
  new member without a label — so adding one is a two-file change, not a one-line enum edit.
- **`profile.py:82` cites the *Hennepin County* soil survey** for `soil_class="GM"`. Same
  class of wrong-source citation as the snow load fixed in `plan/site.py` on 2026-08-23
  (that one read Hennepin/IRC where it should have read MN Rules 1303.1700 and Ramsey), but
  this one lives in the shared engine profile rather than in a house, so it is a different
  fix: the house should be able to state its own soil class.
- **The HPWH has no combustion/air-volume provision.** An 80-gal Rheem ProTerra in a 160 sf
  mechanical room has a manufacturer air-volume requirement, and no `DuctRun`, `Register` or
  louvre is authored for it. Nothing in `haus check` grades it. The room got 7.7 sf smaller
  on 2026-08-23 when the ESS closet took its NE corner, which does not help.
- **The writeback cannot address a `FoundationWall` as `type: "Wall"`.** A PATCH with
  `{"type": "Wall", "tag": "W-B-STR3"}` comes back 422 *"no editable file hosts update Wall"*
  even though the wall is authored in an editable file. Pre-existing; it surfaced on
  2026-08-23 only because `model["walls"]` is uid-ordered and a new wall landed first in
  `test_server_loader_findings`. A UI drag of any foundation wall presumably fails the same
  way.
- **`W-B-CW3` and `W-B-STR2` are over-specified.** Both are `INT_ESS_CLOSET_STEEL` (steel
  studs, Type X both faces) because they used to bound the ESS closet in the SE corner. The
  closet left on 2026-08-23 and they were deliberately NOT re-specified: matching them to
  their neighbours would widen each by 2", move a room face an inch, and re-open
  `integrity.condition_coverage` on a line nothing else asked about. Worth revisiting the
  next time that wall line is opened for another reason; not worth opening it for.

## Basement Ceiling

**2026-08-23 — the flat bearing seat.** The deck and the wood bays now share one plane at
-13 7/16" (decision #61, `houses/catlin/params/main_deck.py`). What that closed, and what it
opened, is below; the numbers in the older items are marked where they moved.

Left open, and worth doing next:

- **The house-wide datum convention is now split, deliberately, and this is the record of
  it.** The basement's walls are physically true: they top out on the seat, the mudsill sits
  on them, and the joists bear on the mudsill. Every storey above still uses the old
  convention — a framed wall starts at its storey datum, so `W-M-*` float 13 7/16" above the
  concrete they bear on, and `FS-S-WEST`'s joists still sit *inside* `W-M-*` at
  108 1/8"..120". Nothing is wrong in the takeoff or the checks; the model simply says two
  different things about the same joint at two different storeys. Making the upper storeys
  true means starting framed walls at the subfloor top rather than the datum, which moves
  every wall, opening, placeable and MEP elevation in the house. Not this change. Read
  `detail_components/wall_base.py` before touching it — it reads `concrete.z1_m` now, which
  is right in both conventions.
- **`W-B-STR3`'s footing is not sized for what it carries.** It is a bearing line under
  `W-M-STRW2` and it keeps the house-standard 20"x8" strip. That was true before the
  2026-08-23 pass, it is still true after 2026-08-24, and it is the residue of this item:
  framing the wall changed what stands on the footing, not what the footing is sized for
  (`Footing.under` takes any wall tag and `_resolve_footing` reads the wall's own `z0`, so
  `FT-B-STR`/`FT-B-STR3` needed no edit at all).
  **The framing itself is DONE, 2026-08-24.** The 2026-08-23 attempt was backed out because
  it pinned the wall's east face on x=10'-6": a floor system's span boundary is the bearing
  wall's NODE axis, so that leaves FS-M-MECH's joists 1/16" of plate, and centring instead
  uncarries FO-M-STAIR's west edge into a 9'-0" LVL. The way through was neither — align the
  basement studs plumb under `W-M-STRW`'s with `face("stud-ext", offset=inch(-2.625))`, and
  move the well's west face down to x=10'-3 3/8" to match the wall above. ~9.8 cy of pour
  out, `RM-B-FURNACE` gains 3 1/8", the shaft goes 7'-0" -> 7'-2 5/8" (absorbed into the two
  flights, now 3'-5 1/16" each), and the reasoning is on the wall in
  `plan/storeys/basement.py`.
- **Two abutting FloorSystems each lay a joist on the shared edge.** `resolve/floors.py`
  always emits a member at `perp0` and at `perp1`, so splitting a deck perpendicular to its
  joists puts two joists in one place and `structural.member_interference` FAILs — correctly,
  but there is no way to say "this edge is shared". `params/main_deck.py` answers it by
  authoring the transition as a real **double joist**: the south system stops one joist width
  (2 1/2") short and the pair sits face to face, which is what gets built anyway. It costs
  ~3.75 SF of sheet area out of ~1,300 that no system claims. A `FloorSystem` that could name
  a neighbour on an edge would be the real fix.
- **The 6 mm LVP has no home in the model.** `floor_finish` is a bare material-tag string
  with no thickness (`model/floors.py`), and the flush-joint argument at the wood/concrete
  boundary rests entirely on that 6 mm. It lives as `_LVP` in `params/main_deck.py` and in
  the `lvp` material's spec instead, and `structural.mixed_deck_bearing_seat` has to allow a
  loose ±1/4" on the finished planes because of it. Giving finishes a real thickness tightens
  that check and is its own change.
- **~10 LF of mudsill is priced at the delta rate and wants the full assembly.** The sill
  return is the union of the framed-wall runs and the floor bearing runs; `[framing]` has
  already bought a bottom plate on the first and not on the second. See the note on
  `pt-sill-plate` in `houses/catlin/prices.toml`. $13-25 on a $1,100-2,300 row — the fix is
  for the takeoff to split the return by whether a framed wall stands on it.

- ~~**No check enforces IRC R316.4.**~~ **FALSE, and it was false when written.**
  `checks/code/mn_residential/foam_plastic.py` is the whole check — `_CID = "code.R316_4"` at
  :32 — it is on the permit checklist at `profile.py:145`, and it grades thirteen catlin
  assemblies today (ten PASS, three UNKNOWN: two sauna liners and the plant room's sheathing,
  each because no field on `Material` says whether a board is an approved barrier). Deleting
  `CATLIN_DECK_EPS_INT`'s gypsum would be caught. Verified 2026-08-23.
  - **What IS missing is `code.R316_3`** — flame spread and smoke developed, ASTM E84. R316.4
    is the thermal barrier and it is covered; R316.3 is the surface-burning rating and it is
    graded nowhere in this repo.
- ~~**`code.R305_ceiling_height` reads `Storey.default_ceiling_height`.**~~ **FALSE.** It
  derives a measured clear height per room — `rules.py:113-131` walks
  `resolve/ceiling_over.py`'s `ceiling_decks_over` / `ceiling_underside_m` and reports
  "clear under FS-M-WEST". The basement reads **8'-0 15/16"** (7'-10 7/8" under the EPS deck
  band) since the 2026-08-23 seat rework, and read 8'-3 1/2" / 8'-4 1/8" before it — not the
  fictional 9'-0" the storey still authors, and not the 8'-2 3/4" this item quoted, which was
  itself two revisions old when it was written. Both current numbers clear R305.1's 7'-0" by
  more than a foot. Verified 2026-08-23.
  - The residual, recorded in the check's own docstring: the derived height is 3/4" GENEROUS
    on a joisted floor, because the subfloor is not subtracted. Against a 7'-0" minimum on
    rooms clearing by more than a foot, that is not worth stopping for — but it is not exact.
- **No boundary condition for "two decks meet in plan".** The mixed deck's wood/concrete
  line at y=13'-0" is a real movement joint — matched depths, unmatched stiffness — and the
  finish, the ceiling board and any tile field have to break on it
  (`houses/catlin/notes/mixed_deck_movement_joint.md`). It is a note and a drawing
  instruction only: a `Transition` binds to a derived boundary condition and there is no
  `deck_change:<assembly>|<assembly>` deriving on the shared edge of two floor elements, and
  a `ConstructionRule` bills along a wall or a ceiling rather than along a line between two
  floors. Nothing in `haus check` will notice if the finish is run straight through.
  **The *finish* half is derived as of 2026-08-21** — `Slab.floor_finish` on `SL-M-DECK`
  resolves the band as a `FinishZone` inside `RM-M-LIVING`, so the polish and the plank bill,
  draw and price separately and the split tracks `_BAND_Y`. What is still missing is the
  **joint**: the derived condition a `Transition` could bind to bill the 31.5 lf of moulding
  and the soft joint along the y=13' leg of it. (A T-moulding since 2026-08-23, not a
  reducer — the flat bearing seat left the two walking surfaces flush within the plank's own
  tolerance. The *movement* half of the joint is unchanged and is the half that matters.)
- **`room_floor_elevation` never adds a FloorSystem's subfloor**, so a room over joists
  resolves its floor 3/4" below the surface people stand on. It prefers a slab top under the
  room and otherwise falls back to the wall base — which is the storey datum, i.e. the top
  of the joists, with the plywood still above it. Placeables are measured off that
  (`resolve/placeables.py`), so every switch, receptacle, pendant and register in a
  wood-floored room sits 3/4" low. Invisible until 2026-08-21, because every main-storey
  room agreed with every other; now `RM-M-LIVING` reads +3/4" (it is over `SL-M-DECK`,
  whose cap is pinned to the finished floor) and its nine neighbours still read 0'-0". The
  living room is the one that is right. Fixing it means adding the subfloor to the wall-base
  fallback, which moves every placeable in every wood-floored room in the house by the
  subfloor thickness — a real cascade, worth its own pass with the goldens re-blessed
  deliberately. `test_canvas_placeables.py` derives the offset rather than asserting it, so
  it stays honest either way.
- **Basement HVAC could ride the new joist bays.** `DU-B-ERV-SUP`/`-RET` are
  `DuctRouting.CHASE` because the ceiling had no bays at all; two thirds of it does now, and
  the west half's run east-west the way the trunk does. Left as chase because the runs also
  cross the concrete band, and splitting a trunk between bay and chase is its own pass.

- **Four matchers still answer "is this wall above that one", at three tolerances.**
  `platform._collinear_overlap` (tol = wall *thickness*, returns a bool),
  `stacking._axis_match` (tol = `inch(0.5)`, returns overlap length),
  `construction_geometry._stack_overlap` (returns the segment), and — since 2026-08-25 —
  `layout_lines._collinear`, which is `_axis_match`'s rule copied deliberately. Making
  `model.layout_lines` the source of truth for all four is the right end state and is
  **not** a mechanical swap: platform's thickness-scale tolerance is what covers the 8 of
  catlin's 15 second-storey walls that never authored `stacks_on`, and tightening it risks
  re-opening the bare-rim ring `test_platform_continuity` exists to catch. Migrate one
  consumer at a time, behind that test.
  **Narrowed, not fixed, on 2026-08-25:** `layout_lines._stacks` dropped its vertical-
  adjacency gate, so it and `stacking._axis_match` now ask the same *question*. What is
  still not shared is the geometry each is handed — `layout_lines` measures on the
  **datum face** (`Storey.vertical_datum`, so a width change stacks), `_axis_match` on the
  raw **node** axis. On concrete under wood those differ by 43.8 mm (basement) and 57.0 mm
  (garage), outside both `_TOL`s, so **13 stack pairs stack in one pass and not the other**:
  `W-B-S1`→`W-M-S1` and the eight garage `W-GF-*`→`W-G-*`. All 13 are pours under framed
  walls, which frame no studs, so nothing reads the difference today — which is exactly why
  it will be a surprise when something does.

- **`solver.py:231`'s staggered face-parity rule breaks at a non-zero phase.**
  `side = 1.0 if round(station / module_spacing) % 2 == 0 else -1.0` decides which face a
  staggered stud sits on. It assumes `station / spacing` lands on an integer; with a layout-
  line phase it lands anywhere, and at a phase near 4" or 12" the quotient sits on a `.5`,
  where Python's banker's rounding sends consecutive studs to the *same* face —
  float-noise-dependently, so it will not reproduce. Runs of same-face studs destroy the
  acoustic decoupling that is the entire reason for a staggered wall, silently and without
  a finding. **It cannot fire today**: every staggered wall (`INT_2X6_STAGGERED_PLUMBING`,
  `INT_2X4_STAGGERED_DOUBLE_GWB`) is on `layout_origin="wall-start"`, so the phase is
  always 0.0, and the 2026-08-25 interior opt-in deliberately excluded them. It is a trap
  for whoever widens that opt-in. Fix it by tracking the stud's *index*, not its station.
- **`platform._platform_above` uses one number for two jobs.** `tol = max(thickness, 1e-3)`
  is both the off-axis slop *and* the minimum overlap length, so an upper wall overlapping
  by less than ~12" is invisible and a parallel interior wall within 12" can be a false
  match.
- **`platform`'s rake guards are effectively dead.** `apply_to_roof_wall_tops` runs at
  `pipeline.py:76`, after the lift at `:67`, so `top_z0_m` is still `None` when the two
  guards test it.
- **`roof_geometry.py:257-261` drops `plate_top_z_m`** when it rebuilds a `ToRoof` wall,
  discarding the lift for a wall that is both lifted and raked.
- **Neither `plate_top_z_m` nor `plate_base_z_m` is serialized** (`model_json_fabric.py`),
  so the viewer cannot tell wall body from joist band, or wall body from rim lap.
- **`IfcBuildingElementPart` bodies carry no voids** (`ifc/lowlevel.py:435-436`) while glTF
  cuts openings out of banded layers, so a banded band crossing a window is already
  inconsistent between the two exports. Cross-storey `LINE_BASE` bands make it likelier hit.
- ~~**19 catlin windows are off the layout line's grid.**~~ **DONE 2026-08-25.** Both specs
  in `CATLIN_EXT_2X6` are flipped (stud *and* outrigger), and `PLANT_EXT_2X6_HUMID` with
  them — W-S-S1 and W-S-W4 are members of the south and west lines, so leaving that assembly
  on wall-start origin would have put a jog in an otherwise continuous line. 20 window ROs
  moved 3"–8" onto the unified grid. `haus check houses/catlin` is **0 FAIL**, down from 2,
  and the `window_framing_module` exception list in `test_catlin_contract_m3.py` is now
  empty. Four documented facade defects went with it — the west face's spent fifth column,
  the east knee band's 4" miss, the north gable's asymmetry, the juliet pair's accepted 3"
  off-module exception — plus a ladder-backing rung the suite header had been displacing.
  See `houses/catlin/CLAUDE.md` **ONE GRID PER FACADE**.
- **A `Slab` or `FloorSystem` rim has no cladding concept at all.** `SL-M-DECK`'s exposed
  perimeter edge takes no fascia, no edge trim and no drip: the machinery for that
  (`resolve/roof_edge.py`, `resolve/trim_bands.py`) is roof-only and has no analog for a
  horizontal element's edge. Noted 2026-08-24 while closing the *wall* side of the same gap:
  `resolve/platform.extend_walls_to_foundation` now runs a framed wall's skin down over the
  mudsill and rim to lap the foundation below, which covers the basement-to-main line — and
  does nothing whatever for a slab edge, which is a different element with a different
  detail. Scope it on its own.

# Project Management (deferred)
* Track to inspection (list of inspections, calendar, pass registration). Likely includes Kanban somehow
* Report final costs (but also reusable plan)
* Upload pictures/notes/voice notes
* system for collecting bids as a GC (bidders should see estimates for materials for their job but not the estimate cost already, that would give them numbers to aim at).
* Show for bids as the main image the backside of the house (so the design looks cheaper, for lower bids)
* local first (with drive, S3 bucket, or such for backup) or Cloudflare workers

Firstly design a house (with permit checks, building science review, floorplan editing in the 2d UI, 3d review, cost reduction and BOM review).
Secondly gather bids, organize the timeline (inspection gates, etc), then track completed progress.
Thirdly use the house design as a reference (ie for agents understanding live data on home assistant in context), potentially with feedback loop of updating the design or later running a remodel

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)

### Potential cost cutting (just ideas, not a TODO)
~~Remove the attic level and switch to truss/blown in insulation~~ — PRICED 2026-08-24 at
$89,000-160,000 off the bid total, and moved to `plans/cost-options.md` per the rule below,
along with 17 other rows worth $3,000 or more each (the 2026-08-24 cost-reduction sweep).

Once an idea here has a number against it, it moves to `plans/cost-options.md` — the
priced upgrade/downgrade menu (started 2026-08-08).
