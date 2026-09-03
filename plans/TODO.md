# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **RESOLVED 2026-08-30 — the sunken-garden retaining walls check, and the lever table this
  entry used to carry is now history.** This item stood **twice** on this list (at FS 0.80
  and, staler, at FS 0.57) saying the same thing: `W-SG-E2`/`S`/`W2` reached FS 0.73-0.80
  against sliding where IRC R404.4 requires 1.5, `haus check` exited 1, and `verify.sh`'s
  0-FAIL contract on catlin was broken. Both copies are collapsed here.
  - **The fix was the free body, not the base.** Every option the old table priced —
    rebalance the toe, widen to 9'-0", add a 2'-0" shear key, widen to 11'-0" — was arithmetic
    on the wrong drawing. These are not three cantilevers; they are three sides of a closed
    loop, and `W-SG-W2` and `W-SG-E2` face each other across a 19'-0" court and cancel. What
    was missing was the fourth side. `W-SG-ARCH` is back as a buried 12" x 17 1/2" grade beam
    — not the retired arch, not its parapet — and `engineering/retaining_system.py` sums the
    court as ONE free body: **FS 1.58 against 1.50**, graded at at-rest.
  - **The blocking finding this entry named is fixed, and differently.** It said an eccentric
    footing was "inexpressible" and a shear key had no field. `Footing.offset` expresses the
    first; the shear key turned out **unnecessary**. What eccentricity needed was 12" of toe,
    and it had to go INBOARD because the raised garden's apron measures its 3'-0" clear off
    these footings' outboard edges — the owner's figure, from the brief. Toe 4'-0" / heel
    3'-0", outboard edges unmoved to four figures, +2.10 CY.
  - **And the section, which neither entry had noticed.** The stems were plain concrete at
    465 psi — which ACI 318 R22.6.3 does not cover *at all* for a wall unsupported at the
    top. `#6 @ 10" o.c.` now, sized in the note. Fixing sliding alone would have turned the
    report green over a louder uncomputed failure.
  - `notes/sunken_garden_court_free_body.md` is the hand-worked oracle. It supersedes the
    screening note's CONCLUSION and not its arithmetic.
  - **What is NOT resolved:** §6 of the screening note still holds — `engineering_spec` is
    unset and these items are **unsealed**. 1.58 against 1.50 is a screening on presumptive
    values, with no geotechnical report, a soil class from a survey for the wrong county, and
    **a design that depends on the washed-stone bed being built as specified — 1.13 without
    it.** MN Rules 1309.0402 also amends IRC Table R402.2 with a **5,000 psi FOOTINGS row**
    this model states no mix design against; that wants checking before anyone orders.

- **`EQ-S-HP1-AH.zone_rooms` named `RM-A-STUDIO-BATH`, a tag that names no room — RESOLVED
  2026-08-31 as a typo.** The attic guest bath is `RM-A-STUBATH`, and it is in the zone now.
  - The two parts of the repo that disagreed: `plan/electrical.py`'s comment above that list
    (2026-08-29) said all three of the split west loft's rooms are named there because one
    boot conditions the whole footprint, and that "dropping either from this list would
    report them as unheated rather than as what they are" — which the typo did, silently.
    Against it, `tests/test_heating_capacity.py` pinned `RM-A-STUBATH` as **deliberately**
    unclaimed, arguing it is exhaust-only (`REG-A-STUBATH-EXH`, 20 cfm continuous) and takes
    make-up air under the door, so a supply boot would short-circuit its own extract.
  - **The comment won, and the test's argument was about the wrong thing.** It is a true
    statement about AIR — the bath still has no supply boot and still should not have one —
    and a false one about the HEATING ZONE, which is what `zone_rooms` is. A 50 sf
    conditioned room off a conditioned bedroom is inside System 1's zone whether or not it
    has a terminal of its own, and its load belongs in that zone's block load. The test now
    says so where it used to argue the opposite.
  - Three unclaimed rooms left (`RM-B-ESS`, `RM-M-MUD-CLOSET`, `RM-M-PANTRY`), all documented
    as intentional.

  - **The entry's "and now it would pass" was wrong.** `RM-A-STUBATH` FAILED: its only
    125 V receptacle, `ED-A-STUBATH-GFCI`, was 44.4" from the lavatory carcass — right room,
    right height, right circuit, wrong wall. It moved to `W-A-HALL-S`'s south face in the
    same commit, which then opened a real 210.52(A) gap in `RM-A-STUDIO` (the old position
    was covering for the studio *through* `W-A-STU-W`) and `ED-A-STUDIO-RC10` closes it.
  - Both traps the entry names do fire, and the check kills both: `ED-M-BATH2-TUB-RC` on the
    enclosure gate (a `ResolvedSolid` over it, E3901.1 item 3) and `ED-M-LIVING-RC8` — 16.5"
    from `FX-M-BATH1-LAV` — on the room gate.
  - **Still open, and named in the check's docstring:** the model carries no basin extent,
    so the distance is measured to the whole vanity CARCASS. That is a lower bound on the
    real 210.52(D) distance, so the rule is permissive; tightening it means a
    `FixtureType.basin`. The (D)(2) cabinet-face branch reports UNKNOWN for the same kind of
    reason — it is bounded 12" below the countertop and `FixtureType.height` is the whole
    assembly, not the deck.

- **`Room.clear_face` is not the wall's finish face, and something should say so louder
  (2026-08-29).** It is inset from the wall AXIS by the room's lining, so on RM-M-BATH2's
  13 7/8" exterior wall it reports x=5/8" where the paint is at x=6 5/8". A 54" vanity was
  authored off the reported number during this pass and stood **six inches inside the
  studs** — and `haus check` reported 0 FAIL throughout, because nothing in the engine
  grades a *fixture* against a wall face the way
  `test_catlin_contract_m3.py::test_wall_mounted_devices_resolve_against_a_wall_face` grades
  a device. The floor-heat polygon beside it went into the wall the same way, and that has
  no face check either.
  - **STILL OPEN, and it is what actually removes the trap:** give `ResolvedRoom` a second
    polygon that IS the finish face, so the honest number is available to author from. Note
    that `resolve/floor_heat.py` falls back to `room.clear_face` when no zone is authored,
    so the fallback carries the trap into every unauthored mat. That change moves every
    room's area and every `clear_face`-derived check at once and is its own pass.

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

- ~~**What braces the porch and balcony east-west, now that the arch is gone?**~~
  **CLOSED 2026-09-03. The answer is four fixed concrete columns, and every option below
  lost.** (Raised 2026-08-18; the longest-running item on this list.)

  The balcony's four CORNER pillars are now **12" round reinforced-concrete columns fixed at
  their bases**, doweled into the wall tops of `W-SG-W1`/`E1`, and those four columns are the
  entire lateral system in both plan directions. The eight knee braces and both E-W brace
  rails are **deleted**. The two centre pillars stay wood 6x6 on pinned `ABU66SS` bases,
  leaning columns tied in by the deck diaphragm — which is the one claim here that is still
  a claim. `houses/catlin/notes/balcony_moment_columns.md` is the design: base moments from
  wind and from R301.5's guard load, the P-M interaction on the round section worked term by
  term, slenderness at k = 2.1 against §6.2.5's sway limit, and the class B dowel lap.
  `structural.lateral_racking` names each column and delegates to `deck_post/<tag>`; both are
  on the permit checklist as "Freestanding deck lateral resistance".

  **How the three options closed:**
  - **Extend the knee-brace rule to the centre pillars** — moot. There is no knee brace left
    to extend, and the members the rule braced against are gone with it.
  - **A moment base at the four corner pillars (`MPB66Z`)** — **FORECLOSED, on capacity and
    not on cover.** The cover arithmetic that ran through three section shapes in this entry
    (16" square, 16" round, 20" round) never got to be the deciding factor: ESR-3050 Table
    A's wet-service cap is **2,610 lb-ft**, and the guard case alone is **2,502 lb-ft** on
    one column before any wind, with nothing between them. It also wants 5" of side cover —
    about 16" of concrete, cast in — which neither a 12" round nor a 12" wall top has. Every
    number quoted in the struck-through text below is stale twice over: `PT-SG-FCOL` is a
    **12" round** now, and the four pillars this bullet was written about are the columns.
  - **An engineer's lateral design** — **still the answer, and now it has something to
    stamp.** What changed is that the ask is no longer "please design a lateral system": it
    is "please check and seal `deck_post/PT-SG-B{R,F}{1,3}`", a computed design with a
    hand-worked oracle beside it. The screening list at §9 of that note is what a reviewer
    should look at first: base fixity itself (the wall top's own capacity to receive the
    moment, and the foundation's rotational stiffness), column shear, and the diaphragm claim
    that delivers storey shear to four corners rather than six posts.

  **The porch's own E-W path was never this question and is now answered by inspection.**
  `FS-SG-PORCH` lands its four beams in `W-SG-W1`/`E1`, two 12" concrete retaining walls — it
  is braced by shear walls in both directions. `structural.lateral_racking` skips it
  explicitly for that reason (`_bears_on_a_wall`), because without the gate its two cast
  columns would each be reported as "the lateral system", which is a false claim about a real
  structure.

  **The doctrine at the head of this item held all the way through and is worth keeping:**
  nothing was authored for the lateral system until it was decided, and what is authored now
  is a section and a cage with a calculation behind them, not a number invented in the model.

- **Two porch/balcony span knife-edges, written down 2026-08-28.** Neither is a finding
  today and neither had been recorded anywhere before. `structural.deck_beam_span` looks IRC
  Table R507.5(1) up on the **joist** span the beam carries, and the table's rows are
  6/8/10/12/14/16/18', so the lookup steps down in cliffs rather than sliding — a small
  change in a joist span can fail four beams at once.
  - **Porch: 9" of joist-span headroom.** `FS-SG-PORCH`'s joists span 7.25', which reads the
    8' row → a 10.25' limit against the four porch beams' 10.00' span. At a joist span of
    8.01' the lookup drops to the 10' row (9.17') and **all four porch beams FAIL by 10"**.
    Deepening the porch, or moving the back-beam line north, is what would do it.
  - ~~**Balcony: retired, and worth keeping visible.**~~ **OFF THE TABLE 2026-09-03: the
    three balcony beams are treated GLULAM and have no row in Table R507.5(1) at all.** They
    are engineered items now (`deck_beam/BM-SG-BL*`, `engineering/glulam_beam.py`, oracled by
    `notes/balcony_moment_columns.md` §5), graded on NDS bending, shear, bearing and
    deflection with AWC Table 5.3.1's wet-service factors applied. Bearing governs at under
    half. A joist-span cliff cannot reach them, because there is no lookup to step.
  The porch half above is unchanged and still live. Anything that changes a PORCH beam
  section has to be re-checked against it. Also in
  `houses/catlin/notes/beam_water_protection.md`.

- **Widen `structural.landing_post_bearing` past stair landings.** **The premise changed on
  2026-09-03 and the item got MORE important, not less.** It used to be the rule that would
  confirm what the 2026-08-29 change bought — `PT-SG-BF2` bearing on concrete rather than
  through a 2x8. BF2 moved back onto the porch deck when `PT-SG-FCOL` shrank to 12", so
  **both** centre pillars now bear cross-grain through one 1 1/2" ply (~315 psi under the
  base, ~385 psi where that joist crosses the beam, against an Fc-perp of 425 with no
  duration factor), and both are answered by authored squash blocks that nothing grades.
  The rule still cannot see either joint, because it is scoped to stair landing posts only. Nothing else in the model grades cross-grain bearing under a
  post, which is why `PT-SG-BR2` stood on a single joist ply for a day with 0 FAIL and why
  its squash blocks are authored rather than derived. **Not a one-line scope widening:**
  `_bearing_element_under` has to learn about a FloorSystem's blocking members and its sheet
  thickness first, or turning it on adds ~10 FAILs to a house that has none — the eight
  heat-pump stand legs, `PT-SG-BR2` and `PT-SG-BF2` — every one of them a false report about
  a joint that is answered. The four balcony corner pillars left this list entirely: they are
  cast concrete on cast concrete now and have no cross-grain bearing to grade.

- ~~**Verify the PWT treated LVL lead — one phone call.**~~ **ANSWERED 2026-09-03, and the
  answer was a different product.** `notes/beam_water_protection.md` recorded that the real
  durability defect in these beams is **fourteen site-built ply seams** that hold water and
  grit and freeze ~100x/year, and chased an unverified Pro Deck Supply listing for PWT
  treated LVL. The three BALCONY beams are now **treated SYP structural glulam, 3-1/2" x
  11-7/8", 24F-V5M1/SP** (Anthony Power Preserved / Boise Cascade, ~$35/LF through
  Lakeville) — one manufactured member with published engineered values, no ply seam at all,
  and a stocked product rather than a listing nobody had called about. `BEAM_GLULAM_TREATED`
  in `plan/assemblies.py`; the material is `glulam-treated` in `library/materials.py`; the
  design is `notes/balcony_moment_columns.md` §5.

  **Two things this does NOT close.** (a) The **four porch beams** are still 3-ply KDAT 2x12
  with eight seams between them, taped and capped, and the same trade is available there for
  the same reasons — it was not taken because nothing about the porch redesign forced the
  question. (b) The 2026-08-23 note in `params/sunken_garden.py` that says "treated LVL is
  not a product" was about **Parallam Plus PSL depths** and said nothing about LVL or about
  glulam; it has been rewritten where it sat, on `SPEC.balcony_beam`.

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

- ~~**The girt bands have no RAKE NAILER at an attic gable.**~~ **DONE 2026-08-30.** One
  raked `strapping-{band}-rake-{i}` member per band along each gable's raked top, on
  `FramedMember`'s `z0_end_m`/`z1_end_m`, cut around any opening it crosses, with its own
  blocks on the stud module (`GirtFrame.rake_blocks` — its own branch, because the field
  pass pairs the two tiers by a single `z0_m` and a rake has an elevation per station). 12
  nailers, 160 LF, 114 blocks. The field is held one full board clear of it, which is the
  same rule that holds a course clear of an opening's head course and which retired the
  short raked stub the `snap` `bounds` argument existed to paper over.

**Deliberately not done, and why:**

- **Deck post/footing UNKNOWNs (2026-07-26, by design) — MOSTLY CLOSED 2026-08-30, and the
  "by design" half of this entry was half true.** It read: `deck_post_size` has no R507.4 row
  for the 12" round column PT-SG-COL, and PT-SG-COL plus the six balcony pillars bear on
  non-Pad chains so `deck_footing_size` "can't resolve". The first clause is right and
  permanent — R507.4 tabulates SAWN LUMBER posts and a round cast column will never have a
  row. **The second was a check bug wearing a design rationale.** The model says exactly what
  every one of those posts bears on; the check followed one `Post -> Post` link and knew about
  `Pad` and nothing else, so it reported "does not bear on a resolvable Pad" — a sentence
  about its own reach — and minted `spread_footing/<post>` items for footings that do not
  exist. Now:
  - **six earned N/A** — four balcony corner pillars on `W-SG-W1`/`E1` (foundation walls
    with their own strip footings), and both centre pillars on `FS-SG-PORCH` (a post on a
    deck is not a post on the ground; `PT-SG-BF2` was on `PT-SG-FCOL`'s top from 2026-08-29
    until it came north onto the deck on 2026-09-03). Either way the load leaves through the
    column beside it, and that column's own item picks up the share —
    `pier_basis._piers_below` is what makes the promise true, and it did not exist for the
    deck-borne case until 2026-09-03;
  - **two PASS** — `spread_footing/PT-SG-COL` and `/PT-SG-FCOL` compute bearing on the belled
    piers: **1,603 and 1,159 psf** against IBC Table 1806.2's presumptive 2,000 for this
    site's GM. `engineering/spread_footing.py`, oracled by `notes/sunken_garden_piers.md`.
    The two swapped places on 2026-09-03: FCOL fell from 1,477 when its column shrank from
    20" round to 12", and COL rose from 1,245 when `PT-SG-BR2`'s share of the balcony was
    finally handed to it. COL is now the pier with the least margin in this structure;
  - **four more, and they are BENDING** — `deck_post/PT-SG-B{R,F}{1,3}`, the balcony's corner
    columns, graded on base moment rather than on axial load because they are that deck's
    entire lateral system. `engineering/deck_post.py::_moment_column`, oracled by
    `notes/balcony_moment_columns.md`. `spread_footing` deliberately declines them
    (`_Pier.shared_wall_footing`): they stand on a wall's strip footing, which
    `structural.foundation_unbalanced_fill` already grades as `retaining_wall/<tag>`;
  - **two more PASS, as of 2026-08-30** — `deck_post/PT-SG-COL` and `/PT-SG-FCOL`. They were
    UNKNOWN because ACI 318-19 §14.1.5 does not permit a plain concrete COLUMN at any stress
    and `Post` had no field to state a cage in. **It has one now** (`vertical_reinforcement`,
    the decision below, answered YES), and the record grades seven limit states: the §22.4.2 axial cap, §10.6.1.1's 1%
    floor and 8% ceiling, §10.7.3.1(b)'s four-bar minimum, §25.7.2's tie size and spacing,
    and the §6.6.4.5.4 minimum eccentricity magnified per §6.6.4.5.2. Both piers carry
    `(4) #5` with #3 ties at 10" — FCOL came down from `(8) #6` at 12" when it shrank to a
    12" round on 2026-09-03. **The cages are the Code minimum and the axial d/c is 0.056** —
    the steel is there for creep, shrinkage and the accidental moment, not for strength,
    which is exactly why it cannot be value-engineered out. `notes/sunken_garden_piers.md`
    §4 is the oracle.
  (`deck_beam_span` is green too, and by both routes: two genuine R507.5(1) overspans closed
  2026-07-31 by going engineered, the porch four pass the table prescriptively, and the
  balcony three went ENGINEERED on 2026-09-03 when they became glulam — a section the table
  publishes no row for. `engineering/glulam_beam.py`.)
- **Spec fiber in concrete almost everywhere. Also galvanized rebar.** The galvanized half
  is PARTLY DONE: the owner settled it on 2026-09-02 (hot-dip, ASTM A767 cl. 1 or A1094 —
  epoxy delaminates, stainless costs 4-6x and fights the concrete thermally), and the five
  sunken-garden cast columns and their dowels are specified galvanized in
  `SUNKEN_GARDEN_COLUMN_12`. **House-wide is still open**, and so are the Sika/Vector
  Galvashield XPX embedded zinc anodes (330 g zinc, 20+ yr, ~$1,400/box of 20) weighed for
  the salt-splash sunken-garden walls. Note that rebar rides INSIDE the $/cy rates
  (`prices.toml` `[basis_notes]`), so a house-wide switch is a rate note plus a plan of its
  own, not an element edit. `notes/balcony_moment_columns.md` §7 has the reasoning. Fiber is
  untouched. ALSO set rebar coverage to 3" everywhere exterior where possible, and make sure that wood beams bearing on the sonotube concrete have gaskets or standoffs if they need to.
- **DECIDED 2026-08-30: `Post` grew a `vertical_reinforcement` field.** (Raised the same day
  by the two piers above, and answered the same day.) The alternative — closing both items in
  `engineering.toml` with the engineer's cage schedule and leaving the model silent — works
  for the permit and leaves the DRAWINGS unable to say what the columns contain, which is the
  wrong trade for a field that costs one line. The spec shape deliberately differs from
  `FoundationWall`'s: a wall's bars are a **spacing** because a wall is billed per foot, a
  column's are a **count** because ACI bounds the cage by `0.01Ag` and by four bars, and
  neither question can be asked of a spacing. `deck_post.parse_cage` reads it, and an
  unreadable string is NO steel, the same conservative contract
  `retaining_basis.parse_reinforcement` keeps.
- ~~**FOUND OUT OF SCOPE 2026-08-30: the four breezeway piers are the same defect, unfixed.**~~
  **DONE 2026-09-03, taking the staged option this entry proposed.** `PR-BW-1..4` are graded
  now: `deck_post/PR-BW-*` and nothing else — they carry `'(4) #5 vertical, #3 ties @ 10"
  o.c.'`, ACI's own minimum for a 113.10 in² section, oracled by
  `houses/catlin/notes/breezeway_piers.md`.
  1. **The gate widened, and gained a concrete test it never had.** `cast_piers` admits a
     post on a `Pad`, gated by `assembly_structure_material(...) == "concrete"` — the
     predicate `checks/structural/uplift_path.py` uses, because `"12 round"` is a SHAPE and a
     12" round wood column is an ordinary thing. It had no material test at all before, so
     this closed a latent bug as well. `spread_footing` stays scoped to `Footing`s: a `Pad`
     **is** an R507.3.1 row and `structural.deck_footing_size` grades it, and two authorities
     on one number is worse than one.
  2. **The axial state is INCOMPLETE, and the demand is not faked.** `_Pier.unmodelled_load`
     derives which beams bear on a pier with no plan area behind them — here `BM-BW-RW/RE`,
     the breezeway roof, which is neither a `Roof` nor a `FloorSystem` — and
     `deck_post._detailing_only` grades the six load-independent detailing states in full
     while OMITTING the §22.4.2 comparison. `deck_post.BASIS_VERSION` 2 → 3. The note's §3
     carries a bounding estimate (d/c ≈ 0.007 even with 50 psf of snow on the roof) so nobody
     reads the INCOMPLETE as "the pier might be too small"; the register publishes no ratio,
     because a bound is not a design. **Closing it is upstream work**: give the roof a
     modelled area to divide, or have the engineer state the demand.
  Cost: **+28 lb of steel over 18.92 LF, +$18-36** — this entry's "~+16 lb per pier"
  overstated it about fourfold (16 lb was the whole of `PT-SG-COL`'s 10.68 LF, not one
  pier's). `column:PIER_CONCRETE_12` is re-struck and no longer says it is uncounted.
- **Windows: 4 residual member-interference overlaps** — now **pinned** by
  `test_catlin_window_member_overlaps_pinned_at_four` (junction clear disabled — the
  honest metric). Measured composition drifted from this file's memory of 4+4: it is 2 at
  one T (CSW148's king stud), 1 L corner, 1 vs the stair soffit plate. The T was 6 until
  2026-08-22, when O-S-VANITY moved off the corner square that the 8" suite sound wall grew
  the day before — its whole jamb pack had been standing inside it. (Historic: 138 → 8 → 4.)

### Undrawn verticals

`DuctRun` had no elevation field at all, so every vertical leg in the house's air side was
a plan polyline that teleported between floors, ducts emitted no 3D solids, and the take-off
billed plan length. It carries per-vertex elevations now, the same field set `PipeRun` has
had since MEP Phase 2 and solved by the same solver — a riser is a repeated plan point at
two elevations, which is exactly how a drain drop has always been written.

- **`DU-S-HP-SOUTH`'s rise — CLOSED 2026-08-30, and the reason it stayed open for weeks is
  worth keeping.** The blocker was never the route: it was that `SF-S-DUCT`'s south end had
  no lane a branch could leave through, because a 21"-wide air handler filled a 30 3/4" box.
  That air handler did not exist. `EQ-T-GREE-SLIM24` was an explicit "REPRESENTATIVE
  PLACEHOLDER … TODO verify datasheet", and the only real 43 3/8" cabinet matching it, Gree's
  discontinued low-static `DUCT24HP230V1AD`, tops out at 589 cfm against the 750 cfm this
  whole duct system is sized to — so the packing problem, and the airflow the packing was
  arranged around, were both artifacts of an unverified type. The real machine
  (`EQ-T-GREE-DUC24`, 44 1/2 x 29 11/16 x 11 13/16) went into a new wide bulkhead in
  `RM-S-STUDY2`'s ceiling, `SF-S-HP1`, and `DU-S-HP-SOUTH-RISE` is the vertical: 15" from
  that box's cavity into the `FS-ATTIC` bay at (23'-0 1/2", 3'-4"). **The lesson generalises:
  a `# TODO verify datasheet` on a type is not a documentation debt — every clearance, lane
  and velocity downstream of it is provisional.**
  - **AND THE RISER STILL DID NOT TOUCH THE MACHINE — closed properly 2026-08-31.** Both its
    ends sat at x=276.5" while the cabinet's east face was at 269.235": a 7 1/4" gap, in
    mid-air, with a comment here and in `plan/mep_hvac.py` asserting that "the plenum is
    fabricated out to x=23'-5 1/2" to catch this take-off". Nothing in the engine can catch
    that — no check validates that a `DuctRun` endpoint reaches equipment or another run, and
    `Register.duct_ref` is an unvalidated string — so a branch feeding three registers hung
    off a sentence for a day. It has a real take-off leg now, running east from the air
    handler's discharge face. **The same lesson, one level up: closing a TODO about a missing
    vertical is not the same as closing the connection, and only one of the two was checked.**
  - Closed with it, the airflow: the trunk carried 750 cfm and this riser 250, and because
    they joined nothing they SUMMED — 1,000 cfm against a machine that moves 760. The
    discharge is 750 now, split 500 north up the trunk and 250 east into the riser, and all
    ten of System 1's supply registers carry a `design_cfm` that sums to it. Nine of the ten
    had none at all.
  - Closed with it: `DU-A-HP-STUDY`, which was orphaned, straddled the joist at y=32",
    overlapped `DU-S-HP-SOUTH` by 4" in a 13 1/2" bay, and ran 6'-8" of bare duct across
    `RM-A-STUDY`'s finished floor. `REG-A-HP-STUDY` is a straight boot off the branch now.
  - Closed with it: the return grille sat 1" north of the case, on the same face the supply
    left from, and `EQ-S-ERV-MIX` injected 100 cfm of -15 F outdoor air downstream of both
    the coil and the strip heater. Both are on the return side now.

### Found in passing, 2026-08-30 (System 1's south branch)

- **Nothing validates that a duct actually connects to anything.** No check tests that a
  `DuctRun` endpoint reaches equipment or another run, and `Register.duct_ref` is an
  unvalidated string. The whole `DU-S-HP-SOUTH`/`DU-A-HP-STUDY` tree was joined to nothing
  for a fortnight and every check passed. The only duct-to-equipment geometry in the
  codebase, `resolve/mep_soffit.py::_pair_is_plumbed`, exists to *suppress* a clash — the
  same predicate run the other way round is the check that was missing.
- **The AH/ERV blower interlock has nowhere to live in the schema.** With the ERV running
  and the air handler off, 100 cfm enters a still return chamber and leaves through
  `REG-S-HP-RET` into `RM-S-STUDY2`, the only low-resistance path; distribution to the rest
  of the house needs the blower turning (continuously, or on ERV call). That is a controls
  fact, no `Equipment` field holds it, and it matters because
  `code.N1103_6_whole_house_ventilation` is already tight at 210 cfm provided / 203 required.
- **No `Equipment` field records a filter or an access panel anywhere in the model.**
  `REG-T-HP-RET` is a filter-back grille and the only serviceable face on System 1; the
  model knows it as a rectangle with a `RETURN_AIR` port.

### ERV residuals (2026-08-25)

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
- **`DU-M-ERV-R-PLANT` is the longest radial in the house at 55'-8"** — level-2 manifold at
  the north end, south through the `FS-S-WEST` trusses, then up inside `W-S-C1` to a high
  sidewall grille (it moved off the attic manifold and out of the guest studio 2026-08-29,
  and 9'-4" of that length is the rise). Its pressure drop wants checking before 75 mm is
  committed to; there is no airflow solver here and there will not be one. **Check it against
  0.4" w.g., not 0.2":** HVI certifies the B210E75RT at 206 cfm net supply at 0.4" (HVI ID
  2004940), and the 0.2"/210 cfm figure several comments quote is the model-name point off
  the manufacturer's fan curve, not the rating point. **The comments were corrected
  2026-09-01** at 9 sites; `ventilation_cfm=210` is deliberately still authored (moving it to
  206 takes N1103.6 from 210/203 to 206/203 and breaks `test_catlin_erv`), so the pressure-drop
  check itself is what is left here.

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

- ~~**The 1" fall toward the garage is drawn, not framed**~~ **DONE 2026-09-03, and half of
  it was WITHDRAWN rather than built.**
  - **The E-W crown is framed.** `Wedge` is a real element: six tapered 2x4:kdat rips,
    `WG-BW-R{1..3}{W,E}`, a back-to-back pair on every rafter, 1" at the crown feathering to
    nothing over a 2'-0" half-span. They are ordered, cut, counted (12 LF, +$32) and cut in
    section like any other stick. **No sloped-`Beam` schema change was needed** — the
    deferral's premise was wrong. `FramedMember` already carried `z0_end_m`/`z1_end_m` and
    `member_box` already built the raked hexahedron; `KneeBrace` was the working precedent
    for an element that resolves to raked lumber and hosts itself. What was actually missing
    was one escape hatch, `FramedMember.plan_width_m`: `plan_cross_section_m` classifies
    flat-vs-on-edge from a member's vertical extent, and a taper is neither.
  - **The N-S fall is WITHDRAWN, not deferred.** Owner decision 2026-09-02. It was never a
    roof question: the 1" house-to-garage slope was *walkway* drainage, and the walkway is a
    composite deck that drains through the 3/16" gaps between its boards. Stated in
    `PORCH_DECK_COMPOSITE`'s source and in `params/breezeway.py`'s deviation 3. There is no
    gap field in the model and one would buy nothing.
  - Two things fell out on the way, both fixed: `cross_section` sent every `"2x4:kdat"` to
    the 1.5 x 5.5 fallback (a treatment suffix is not a section), and `SL-D-BREEZEWAY`'s crop
    was cutting off the east half of its own subject.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Rename all the wall assemblies to just their type (no need for "CATLIN" in them) and make sure they are in the library
- **The showers are still unclassified — one of four is answered (2026-09-02).**
    Same axis, same rules, same question to answer first: what is actually behind the tile.
    The sauna is the worked example of what answering it costs — a liner variant on the wall
    that turned out not to have one. `FX-M-BATH2-SH` now has a modelled surround:
    `WP-M-BATH2-SURR`, a marble-look cast panel on the pan's two closed sides, priced as an
    upgrade delta against the fixture row that already buys a kit surround. `FX-A-STUBATH-SH`
    and the two flanged inserts still have nothing, and the same logic points at giving
    `FX-A-STUBATH-SH` the same panel.
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
    **Confirmed again on RM-M-STUDY, 2026-08-29, and it bites hardest in a small room.**
    The study's published area is 19.3 sf on the axis box; measured off the four bounding
    walls' own resolved layer polygons it is a 48 5/8" x 45 5/8" clear box — **15.4 sf**, a
    fifth smaller — and off the wainscot faces the joiner actually scribes to, 14.4 sf.
    Retyping two of its walls to `INT_2X4_STAGGERED_DOUBLE_GWB` took another 1 5/8" off each
    axis and **`clear_face` did not move at all**, because `_lining_inset` is a constant.
    No check saw the room shrink. The call booth's bench and desk are therefore dimensioned
    off `out/model.json`'s wall layer polygons, the way the sauna benches are — nothing in
    `houses/catlin/plan/` should size millwork off `Room.clear_face`.
  - **A floor drain in RM-S-PLANT** (the room should be hoseable): implies a drain line, a
    trap primer — the trap *will* dry — and slope in `FS-SECOND`. See the Questions list.
  - `SL-SG-DECK` is gone: the aluminium plank is `FS-SG-DECK`'s `subfloor` and bills as
    182.0 SF in `[sheet_goods]`. The conversion was exact — the balcony joists cantilever 6"
    and the deleted slab's outline *was* that cantilever.
  - ~~**`SL-BW-DECK` stays a Slab, and that is the finding.**~~ **DONE 2026-09-03 — the
    engine can say it now, and the deck is a subfloor.** `FloorSystem.subfloor_outline` is an
    authored sheet polygon consumed in place of the derived corners: one field, one branch in
    `resolve/floors.py`, and `deck_voids`, the elevations and the joist solver all untouched.
    The plank bills 16.4 SF into `[sheet_goods] composite-deck` (164.7 → 181.1 SF) and the
    `[concrete] slab:PORCH_DECK_COMPOSITE` row is dormant. Three things came with it:
    - **`sheet_goods_takeoff` had to move too**, or the order would silently disagree with
      the geometry: it computed area from the bounding box of `floor.members`, so a wider
      sheet would draw wide, pass R311.3 and still bill the joist field. The subfloor reads
      `deck_outline` now; `ceiling_below` keeps the framed extent, because a ceiling is
      nailed to the joists. (It was already understating every deck by a rim thickness at
      each end — +12 SF house-wide, no change in sheet count.)
    - **The oversail is bounded, not just documented.** `structural.subfloor_oversail` grades
      an authored sheet against `[framing] bearing_plan_tolerance_in`, because past that the
      uplift pass finds neither a derived tie nor a hanger and FAILs every member under the
      deck, reported nowhere near the deck (`params/sunken_garden.py` records that failure).
      The breezeway's worst edge is 3 5/8" of 8".
    - **No section drew a subfloor sheet at all**, which only showed up when the Slab left:
      a floor's deck is an IR element on the floor's own uid and `emit_framing_cuts` reaches
      `<uid>::framing`. `emit_floor_deck_cuts` closes it, and 58 goldens gained the plywood
      their joists have always been carrying.
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- Window sealing detail (RM-S-PLANT's is drawn — TR-CATLIN-PLANT-OPENING, 2026-08-18 — and
  is the strictest case in the house; the rest of the envelope still rides
  TR-CATLIN-FRAMED-OPENING)
- Does balcony access have to pass through the plant room? `D-S-DECK-W` is a 60" exterior
  French door in a 70 %-RH room and its threshold will condense (raised 2026-08-18)
- Floor drain in RM-S-PLANT — Answer: No floor drain necessary. Spilled water is mopped up as needed.
- Make sure all desired access panels are in (deferred pending more design items settling)
- ~~Make sure the floor trusses (of the first to second floor) are modeled more accurately
  in 3d and make sure their measurements in the BOM are very exact for manufacturing~~ —
  DONE 2026-09-02. `resolve/floor_ends.py` cuts every deck's joists to where they physically
  stop rather than to the bearing grid, so `FS-S-WEST`'s truss is **17'-11"** overall (was a
  drawn 18'-0" that floated 1/2" outside the framing) on a 17'-3 1/4" clear span; the x=18'
  plate it shares with `FS-S-EAST` is split 3 1/2" / 2" instead of on the centreline, which
  was shorting the truss against its fabricator's 3" seat. `haus takeoff` prints the
  fabrication schedule (`takeoff/fabrication.py`), `integrity.floor_end_bearing` grades the
  seats per member type, and the viewer draws chords + end blocks + diagonal webs
  (`ui/src/three/floorTruss.ts`) instead of a solid bar. Still open, if it ever matters: the
  GLB and IFC exports keep the one-box representation.
- The house's own strip footings are eccentric under their walls, the same way the garage
  stem's were before 2026-08-15: `FT-B-*` is a 20" strip centred on the y=0 node line,
  under a `face("concrete-ext")` wall whose concrete runs inboard from it. **The -2" north
  toe in this note is stale**: that wall went 12" -> 8" on 2026-08-21 and only its inside
  face moved, so the south toe is 10" and the north one is now **+2"**, not -2".
  `Footing.center_on="wall"` now exists to
  fix it, but it is deliberately *not* authored there: the glazed-brick plinth's whole
  derivation (`params/foundations.py`, `FT-B-BRICK`) leans on that 10" toe being there
  to bear on. Correcting the footings means re-deriving the plinth with them.
- **Wall-hung WC — the cost half is answered: NO (2026-08-31).** Making `FX-TOILET-STD`
  wall-hung to save slab penetrations does not pay, on four counts:
  1. **The premise reaches one fixture.** Only `FX-B-BATH-WC` (RM-B-BATH) sits on a slab;
     the other four WCs are over framed decks, where a "slab penetration" is not a cost.
  2. **A carrier on a slab still penetrates the slab.** The 3" drop moves inside the wall.
     It relocates a penetration; it removes none.
  3. **That one fixture is already a recorded owner decision (2026-07-30)**, on other
     grounds: the west end of RM-B-BATH is 12" cast concrete and a carrier would cost
     6 1/2" of furring (`houses/catlin/plan/fixtures.py`). The attic WC carries the same
     decision for the same reason.
  4. **`prices.toml` puts the wall-hung unit at ~3x the floor unit** and records that
     ordering as an invariant. Nothing in (1)-(3) offsets it.

  If a hard number is ever wanted, price it by ablation (filter the resolved model and
  re-run the BOM) — never by editing the house.

  The modelling half is **done (2026-08-31)**: `FX-TOILET-WH` draws and models as a
  tankless wall-hung bowl (`toilet-wall-hung` symbol), its carrier is a first-class framing
  keepout with its own flanking studs and blocking, the type states its own wall-drainage
  so no instance override is needed, and `advisory.carrier_bay_depth` /
  `advisory.carrier_bay_conflict` grade the host wall and what else is in it. The carrier
  is also its own price line now (`plumbing-wall-hung-wc-carrier`), split out of the
  `FX-TOILET-WH` fixture row so the framing-stage cost is billed where it is incurred.

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

 - Make sure 7" threshold to basement from sunken garden
 - Basement under the stairs storage closet
 - ~~For the breezeway sonotubes, something like a Bigfoot single-pour footing form. However
   right now it looks like those footings bisect the house and garage foundation walls.~~
   **CONFIRMED AND FIXED 2026-09-03 — it was real, and worse than it read.** Measured from
   source, with 2'-0" pads on the frame line:

   | interface | plan overlap | vertically |
   |---|---|---|
   | `PD-BW-1/2` ↔ `FT-B-N*` strip footing | 12 3/4" | pad 3'-1 7/16" **above** it — no contact |
   | `PD-BW-1/2` ↔ `W-B-N*` wall assembly | **6 1/16"** | the pad's full 12" **inside** the wall band |
   | `PD-BW-3/4` ↔ `FT-GF-S*` strip footing | 12 7/8" | pad bottom only **4" above** the footing top |
   | `PD-BW-3/4` ↔ `W-GF-S*` ICF stem | **8 3/8"** | the pad's full 12" **inside** the stem band |
   | `PR-BW-3/4` ↔ `W-GF-S*` ICF stem | 1 5/8" | over 4'-0" of shared height |

   **Nothing in the engine could see any of it, at 0 FAIL.**
   `structural.member_interference` deliberately skips `slab`/`footing`/`pad` solids ("beams
   legitimately bear into concrete") and a `FoundationWall` contributes no framed members, so
   no rule graded concrete against concrete anywhere in the house.
   - **The remedy was the cantilever**, per the owner's own first suggestion and
     `params/sunken_garden.py`'s exact precedent (a sonotube moved 17" south rather than
     merging pours). The pads shrank 2'-0" → 1'-4" — `structural.deck_footing_size` graded
     them at 4.00 ft² against a 1.00 ft² requirement, and 1.00 is already the 12" minimum
     side, not the load — and the posts moved onto the band's centre at 2'-8" spacing, the
     practical maximum. The floor and roof beams cantilever 0.3615' and 0.5552' against
     R507.5.2's 0.6667'. Nothing above the beams moved.
   - **The Bigfoot single-pour reading was rejected deliberately.** `Footing.bottom_elevation`
     exists for exactly the belled pour, so it is a supported idiom — but
     `checks/structural/deck.py` returns `_engineered` for a post on a `Footing`, converting
     four PASSes into four UNKNOWNs, and the bearing area does not remotely demand a bell.
   - **The engine gap is closed**: `structural.concrete_interference`, its own check rather
     than a widening of `member_interference` (whose framing-into-concrete exclusion is
     correct and must not move). Scoped to an ISOLATED pour — a `Pad`, or a wall-less
     `Footing` — against any other concrete, and it says so in the module rather than
     silently clearing the rest: the wider sweep reports ~80 findings of correct continuous
     foundation work, because strip footings and walls lap at every corner by design.
     `test_concrete_interference.py` re-creates the old pad and watches it go red.
   - Two things fell out: the two garage-end piers no longer need to stop a course lower to
     dodge `W-G-S`'s bottom plate (all four top out on one plane now), and `DETAIL_CUT_Y_FT`
     can no longer cross both the foundation and the frame — it stays on the frame line, and
     the 6x6 post is the one thing it now misses.
 - ~~Improve the framing logic of the girts/outriggers holding the insulation and cladding of the catlin house. Especialy on the gable ends, it seems the spacing of these isn't always correct and optimal. Perhaps also increase the spacing (I believe and earlier review concluded 32" OC was sufficient)~~ **DONE 2026-08-30.** All three parts. The gable ends were genuinely wrong: a forced course at the lower top re-phased the whole rake band 11-1/2" off the module of the wall below it, and one wall carried a doubled course mid-run. There is now ONE module from the wall base through the rake. The spacing went to 32" o.c. (2x the stud module, so no block moved), and the module was re-phased onto the datum the window sills are measured from. See `houses/catlin/notes/outie_window_truss_detail.md` — the saving is real but small ($466-742), because the same change also nails two places that had no backing at all: the rake, and the cladding lap over the floor rim band.

- **The R312.1.1 guard on the garage stair's 34" landing.** An owner decision with a cost
  and a look to it, flagged in `plan/storeys/garage.py`. It comes with an engine gap worth
  its own item: `code.R312_1_guard_height` censuses `FloorSystem`s and `code.R312_1_guard`
  censuses `FloorOpening`s, so `SL-G-STEP-0` — a `Slab` — is in neither census and its 34"
  drop is graded by nothing. A rule that walks slab edges would close it.
- **A guard opening at the END of a deck edge is invisible to `code.R312_1_guard_height`**
  (2026-09-03, same shape as the item above). `_railing_runs_edge`
  (`checks/code/mn_residential/fall_protection.py:353`) is a plain `LineString` distance test
  of the guard path against the WHOLE edge segment, so a guard that covers the segment's
  midpoint satisfies it however much of either end is missing. `RL-SG-PORCH`'s east leg was
  shortened 3'-0" on 2026-09-03 to open `ST-SG-PORCH`'s doorway and the check reports PASS
  either way — with the opening, without it, and with a 12'-0" opening it has never seen.
  The guard return at the opening is on the author (`PORCH_STAIR_THRESHOLD_RAILS` is that
  return, and `notes/porch_stair.md` says so). The fix is the same shape as the slab-edge
  rule: grade the guard's COVERAGE of each edge, not its distance from it.
- **`W-SG-W2`/`E2`/`S` are screened and DO NOT reach R404.4's 1.5 against sliding**
  (2026-08-30). Two things landed that day, and the first is why the second matters.
  **(a) The retained height was understated by 3'-4".** `structural.foundation_unbalanced_fill`
  derived fill from the single global `Site.grade`, which cannot see that
  `params/raised_garden.py`'s SRW apron holds a terrace at +0'-6" — these walls' own top
  elevation, read from the same constant — against their outer faces. `unbalanced_fill` is
  now authored on all three at **10.37'**, up from a derived 7.0'. No verdict moved (both are
  far past R404.1.1's 48"); what moved is what an engineer is being asked to design for.
  **(b) The screening on IBC presumptive values finds sliding at 0.58-0.64.** Overturning
  (3.06-3.43) and bearing (~1,000 psf of 2,000) are fine; sliding is not, and the soil-density
  band moves it by 0.06, so compaction is not the lever. The footing is centred — 3'-0" of toe
  doing nothing for sliding — and its toe is buried 6 1/2" because the garden floor sits below
  natural grade. `houses/catlin/notes/sunken_garden_retaining_screening.md` has the full
  arithmetic, the cited inputs, and a lever table (rebalance the toe -> 0.84; widen to 9'-0"
  -> 1.11; add a 2'-0" shear key -> 1.30; 11'-0" + key -> 1.56).
  **`FoundationWall.engineering_spec` is deliberately left unset on all three** and must stay
  unset: it would make the check PASS, and there is no design to cite. The cheapest real move,
  per the screening's own math, is a **geotechnical boring** — mu = 0.25 is the presumptive
  floor for a broad soil class and a real test could plausibly support 0.35-0.45, which
  changes the answer more than any amount of concrete. This and the balcony's lateral design
  are **one ask to one consultant**: the apron's own documented negative-embedment defect
  makes it and these three walls a coupled tiered system.
  **(c) `structural.foundation_unbalanced_fill` now computes R404.4 itself and FAILs all
  three**, having grown that calculation the same day from a different direction: *"sliding is
  over by 162% (d/c = 2.62, governed by sliding (IRC R404.4))"*, an implied F.S. of 0.57
  against the hand-worked 0.58 in the note. Two independent implementations agreeing to within
  a percent. The check **will not run off the derived grade plane** ("the grade-plane proxy is
  not a safe input for a retaining-wall design"), so it needs (a)'s authored value; removing
  that would hide a real defect behind a modelling gap. **Catlin is therefore off 0 FAIL, and
  closing that is an owner's decision**: a stamped design, a geometry change from the note's
  lever table, or a deliberate decision to carry these three reds the way `houses/starter`
  carries its own. Do not close it by authoring `engineering_spec`.
  **(d) CLOSED 2026-08-30 by a fourth wall, not by any of (c)'s three options.** The lever
  table in (b) priced four ways to fix a base that was never the problem: these are three
  sides of a closed loop, not three cantilevers, and `W-SG-W2`/`E2` cancel across the court.
  `W-SG-ARCH` returns as a buried grade beam, `engineering/retaining_system.py` sums the
  court as one free body, and it reaches **FS 1.58 against 1.50** at at-rest. `engineering_spec`
  is still unset and these items are still unsealed, exactly as (b) requires — the engine
  computes a draft verdict, and a stamp is a different thing.
  **The 0.58 in (b) and the 0.57 in (c) are both a foot short**, incidentally: both read
  -9'-10 7/16" as the footing's underside when it is its top, so H was 10.37' where the
  stability free body wants 11.37'. Corrected, the isolated wall is 0.73, not 0.80.
  See `notes/sunken_garden_court_free_body.md` §0.

- **`FT-SG-*`'s frost cover**, 12"-21" below the sunken garden's own floor against 42".
  `structural.frost_depth` routes all seven to UNKNOWN — a structure retaining the
  excavation it stands in is an engineered design under IRC R404.4, and
  `structural.foundation_unbalanced_fill` already sends the same walls to the same
  consultant. The permit checklist's "Foundation frost depth" item is UNKNOWN because of it,
  and `test_catlin_contract_m3.py` pins exactly that so nothing else can regress behind it.

- Make sure the basement door keeps the 7" step threshold (reduces flood risk)
  — **it does, and it is 7 1/4" (`W-B-S2`/`W-B-S3`, top -102 3/16" over the garden floor at
  -109 7/16"). Re-verified byte-for-byte 2026-08-30** across the sunken-garden court work,
  along with `SL-SG-FLOOR`'s datum and every `FT-SG-*`/`FT-B-*` underside, because that work
  moved concrete inside the court. `test_retaining_court.py` now asserts the 7 1/4" directly
  so it cannot drift out silently. Still worth a check nobody has written: nothing in the
  engine *enforces* the step, and the curb's height is a literal on two walls.
- The french drains can likely be a type of form-a-drain product (a drain that doubles as footing form). We also can probably have fewer drains slightly.
- The frost protection and the thermal breaks are wrong around the brick footing FT-B-BRICK. Brick is cold, so thermal breaks need to be on the inward side of it (possible this footing uses ICF)
- ~~FX-S-BATH1-LAV is in the way of the bathroom door swing.~~ **NOT A CONFLICT — measured
  and struck 2026-09-01.** Against the resolved quarter-disc `swing_clearance` polygon (not
  the bbox): vanity x 95.62..116.62, y 345.88..393.88; `D-S-BATH1`'s swing x 84..114,
  y 318..348. **Intersection area 0.0 sf, minimum distance 0.21".** The BOUNDING BOXES
  overlap 2.12" in y, which is exactly why it reads wrong on a plan sheet, and
  `integrity.door_swing_conflict` tests the arc and is correctly silent. Recorded in
  `plan/fixtures.py` — including that 0.21" is now the tighter of the two margins on that
  cabinet, ahead of the 0.62" shelf scribe.
- ~~FX-A-STUDIO-BAR-SINK is floating and unplumbed, and so are the attic bath fixtures.~~
  **HALF FALSE, AND THE REAL DEFECT WAS DIFFERENT — 2026-09-01.** The plumbing is complete:
  `PR-A-BAR-DRAIN` (2" PVC, 10.5 LF, 1.0 DFU against 1.25" required), supply at
  `plan/mep_supply.py:576,583`, vent at `plan/mep_venting.py:191-197`. The attic bath
  fixtures are neither floating nor unserved — `FX-A-STUBATH-WC/LAV/SH` carry no `mount=` so
  they default to FLOOR on the attic deck, and `PR-A-STUBATH-DRAIN` names all three. That
  clause was simply wrong.
  The real defect: the bar sink is `Mount(WALL, elevation=27")` with **no casework under
  it** — the same mount `FX-M-KITCH-SINK` survives only because a sink base stands under it.
  Fixed with `FT-STUDIO-BAR-BASE-2418` + one `Furniture` row. It is 18" deep, not the
  catalog's 24": measured against `D-A-STUBATH`'s arc, 24" puts 52 in^2 inside it, 21" puts
  15 in^2, and 18" clears by 0.42".

## Found while doing the 2026-09-01 batch — recorded so they are not rediscovered

- **`mep.duct_connectivity` IS REGISTERED, AND THE ERV WAS PLUMBED TO NOTHING (closed
  2026-09-01).** The check grades every duct end against four honest terminations — another
  duct (matched in plan AND elevation, against a *segment* rather than a vertex), a machine
  footprint at the height of its case, a register naming this run within a 36" boot reach, or
  a cap past the last take-off on a served trunk — plus the outdoor-hood exemption. catlin is
  0 FAIL with it on.

  The batch plan predicted five orphans and named five; the unregistered draft found two; the
  registered check finds **four**, and the difference is the elevation band on the equipment
  probe. Without it `DU-ERV-RISER-SUP`'s basement end "landed on" `EQ-M-ERV-HOOD-OA` 67"
  above it and `DU-S-HP-SUP`'s cap "landed on" the fridge 220" below — the same coincidence
  the draft had already fixed for duct-to-duct and never applied to machines. The four:

      DU-ERV-OA        end   at (1'-11", 33'-7 1/2")   -> EQ-B-ERV
      DU-ERV-EA        start at (1'-11", 34'-8")       -> EQ-B-ERV
      DU-ERV-RISER-SUP start at (0'-5",  33'-7 1/2")   -> EQ-B-ERV-MAN-SUP
      DU-ERV-RISER-EXH end   at (1'-2",  33'-7 1/2")   -> EQ-B-ERV-MAN-EXH

  **And a fifth thing nothing could report: `EQ-B-ERV` had no duct to either manifold.** The
  six basement radials started at boxes that nothing fed. No check says so — this one grades
  duct ENDS, and a manifold with nothing arriving at it has no end to orphan. A machine-side
  rule ("every equipment port that names a service is reached by a run of that service") is
  the missing companion and is not written.

  **The machine had to come down 18" before any of it could be drawn.**
  `EQ-T-BROAN-B210E75RT`'s four air ports are all 6" round on its TOP face. Hung at 6'-0" the
  21.6" case topped out at 7'-9 5/8" under a 8'-0 15/16" ceiling — 3 5/16" for four collars,
  which is not an installation, and is why nothing had ever been drawn to it. It hangs at
  4'-6" now (case top 6'-3 5/8"), which opens the 6'-10 7/16" crossing band the outdoor legs
  and the return trunk use: 1 5/8" under the 7'-6" radial layer, 6 13/16" over the case,
  6'-7 3/8" of headroom beneath. `PR-B-ERV-COND`'s inverts came down the same 18" at the same
  0.3"/ft.

- **`DU-ERV-RISER-EXH`'s top passes 2" from `DU-A-ERV-R-BATH1` at the same elevation.** The
  connectivity check reads that as its joint — correctly, by its own rule — but the riser is
  46" short of `EQ-A-ERV-MAN-EXH`, which is what it is described as reaching, and two ducts
  2" apart on centre at one elevation is an interference, not a tee. Worth a look; the same
  is true of `DU-S-ERV-HP-FEED` passing the same point.

- **`REG-S-HP-PLANT` was NOT moved east, and the reason is the short circuit.** Trimming
  `DU-S-HP-SOUTH` back to the plant room's door would save about 10'-4" of 10x6, but
  `REG-S-ERV-PLANT-EXH` is at (17'-7", 7'-4") and the supply at (6'-8", 3'-4") — an 11'-7 1/2"
  throw across an 18' x 9' room that `plan/mep_registers.py` argues for explicitly: the air
  lands on the south glass and crosses the planting before it is pulled out. Both terminals
  within a foot of the east wall leaves the west 14 feet of a 70%-RH room unswept, and that
  extract is its only moisture removal path. A middle station (x ~12'-6") would take about
  half the duct and keep a 5'-0" throw, if the saving is wanted.

- **A plan-only proximity test is not a duct joint, and neither is a vertex-only one.** The
  first draft of the check matched ends in plan alone and read a basement riser as connected
  to a SECOND-STOREY run 231" above it. The elevations must not be required to be *equal*
  either — a riser is one plan point spanning a z range — so the rule is that the end's z
  falls in the matched *segment's* z range, widened by the joint tolerance. Segment, because
  a branch tees into the side of a trunk: `DU-S-HP-SUITE` leaves `DU-S-HP-SUP` 118" from
  either end of its only segment, and a vertex-only test called it an orphan while crediting
  it to a register 39" away.

- **`concrete-window-bucks-and-blockouts` named the wrong two openings.** Its comment claimed
  "the sunken garden's patio door and the sauna window, both in the basement's daylight wall".
  Driven off the new `openings.host_structure`, the two openings that actually pierce a
  concrete wall are **D-B-GYM and D-B-NE**, through `FOUNDATION_WALL_12_INT`. `D-B-PATIO` is
  hosted by `W-B-S3-FR` (`CATLIN_GARDEN_FRAMED_2X6`) and `WIN-B-SAUNA` by `W-B-S2-FR`
  (`SAUNA_LINER_ON_GARDEN_FRAMED`) — framed walls standing in FRONT of the pour, which need a
  rough opening, not a buck. The count was right for the wrong reason.

- **No check is elevation-aware about a luminaire and the stair it lights.**
  `ED-S-STUDY2-STAIR-SC1` sat 2'-11 1/2" BELOW its own tread and 2'-0" under the stringer
  soffit, with its plan point inside the stair outline, and `haus check` was silent:
  `code.R303_7_stairway_illumination` counts luminaires serving the flight (nine for ST-S2A),
  `electrical.room_lighting` counts by room, and the fc advisory is planar. Nothing compares a
  wall-mount elevation against the stair. Worth a check.

- **A rate corrected by a ratio is a defect, not a workaround.** Four price rows carried
  hand-applied corrections (`x 35/37`, `x 131.4/143.4`) because the takeoff had no field to
  filter on. Every one drifts silently the moment the model changes — which is the actual
  failure mode, not the arithmetic. All four are now driven off a real predicate with the
  researched rate restored. **When a driver cannot express a scope, add the field; do not
  take the correction in the rate.**

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
- **There is no trap-primer element, field or `PipeAccessoryKind` member.** This is what
  blocks the `RM-S-PLANT` floor drain: `library/placeables/fixtures.py:108-110` says the
  existing `FX-FLOOR-DRAIN` type is for wet-room floors and *"a floor drain in a room that
  stays dry for months wants a primer line, which would be a different type."*
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
- **`_append_track_jamb_legs` bottoms its track jambs on a plate that is no longer there.**
  `framing/openings.py` puts `trackjamb-0-l`/`-r` inside `D-G-OVERHEAD`'s rough opening,
  standing on the sole plate that 2026-08-30's `sole_plate_breaks` correctly removes. They were
  already wrong — they stop 22" above the slab — so this is not a regression, but it is now
  a member bearing on nothing at all. The garage contract test deliberately asserts nothing
  about them.
- **`IfcBuildingElementPart` bodies carry no voids** (`ifc/lowlevel.py:435-436`) while glTF
  cuts openings out of banded layers, so a banded band crossing a window is already
  inconsistent between the two exports. Cross-storey `LINE_BASE` bands make it likelier hit.
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

**From the pattern-language review, 2026-08-29** (`plans/pattern_language_review.md` has the
number, the pattern and the reasoning against every one of these; the rows with a MEASURED
number are ready to move to `plans/cost-options.md` whenever the owner wants them):

Implement now:
Raise the electric fireplace to seated eye level, buy one that reads as fire at 11 feet, give it
a dark surround, and turn the seats toward it (181/185). Likely a small section of oak, walnut, or cherry wainscot.
An exterior stair off the porch -- the house currently has no route from a door to its own
ground anywhere on the site (168/120)

Deferred:
Retype the east living row 27x48 -> 27x64, the type already exists (192) -- MEASURED +$269-562.  Note: deferred pending decision.
Oak in the second-floor hall, so the oak stair stops landing on vinyl between two oak rooms
(233) -- MEASURED +$1,943-2,695. Note: deferred pending decision.
Unglazed quarry tile in the mudroom instead of the lab-grade sheet vinyl (248) -- MEASURED,
effectively free at +$33-360. Note: deferred pending decision.
A 10" soffit band over the dining table -- the ONLY lever for ceiling variety on main/second,
because Room.ceiling as a Length produces no geometry there (190/182). Perhaps more oak. Note: deferred pending decision.
Trees: one canopy tree north, two ironwood west, one serviceberry east -- and none within 25'
of the sunken-garden walls (171). Note: deferred pending decision.
Two lounge chairs on the porch -- it is roofed, fanned, lit, wired and curtained, and has
nothing on it (241).


## Takeoff and price-model gaps found by the 2026-08-30 allowance audit

All five were handled **price-side** in `houses/catlin/prices.toml` — the rate was corrected
for the true quantity and the row's comment says so. Each is really a takeoff-code fix, and a
takeoff change alters quantities for **every** house, so each deserves its own commit with its
own test rather than riding inside a documentation restructure.

- **No fabricated ROOF-truss profile exists.** `resolve/framing/profiles.py` has exactly one
  fabricated-member shape, `_RE_FLOOR_TRUSS` (`"<depth> floor truss"`). A trussed roof
  therefore resolves its chords as plain `2x4` sticks and bills at stick rates — which is why
  the 2026-08-29 trussed-cold-attic measurement had to be corrected by hand and made the
  framing swap look like a wash. `prices.toml` now carries a **dormant** `"36 roof truss"` row
  that starts working the day the profile lands.

Two pricing decisions that are correct today and become double bills the moment anything moves:

- **Rebar, ~5 tons, $10,000–18,000, is deliberately inside the `[concrete]` $/cy rates** and
  documented at both ends. It is the strongest "could be authored as real elements" candidate
  in the file. **If it is ever authored, cut the `[concrete]` rates the same day** — nothing
  enforces that, and nothing can.
- **`CATLIN_BASEMENT_12`'s all-in $/cy note says its rate absorbs damp-proofing** on the
  argument that damp-proofing is "not in the model at all". It is now: `damp-proof`
  (`library/assemblies.py:170`) bills in `[envelope_layers]` as `air-barrier`. Either the
  concrete rate should come down ~$7–18/LF or that note should be rewritten. Not touched in
  the 2026-08-30 pass because it is a rate re-derivation, not a defect fix.

## What I am unhappy with
- ~~The price (cost-options.md is missing some of the style details as 'optional' and it needs to be slimmed down to be more concise)~~ — **DONE 2026-08-31**, decision #66. `plans/cost-options.md` is 325 lines: three tables (cost cutting, self-perform, upgrades) plus a premium-feature table, an imports table, an anti-summation map, a *Do not reopen* list and an *upward exposures* list, every row against one stated baseline. The narrative, the superseded pricings and the duplicate allowance register are gone to git history.
- The concrete deck of the basement (either size up for completeness or down for cost savings)
