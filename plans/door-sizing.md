# Door sizing: leaf, unit, rough opening, clear passage

Status: decisions agreed 2026-10-28, revised after review and a second round of questions
the same day. Phase 1 implemented 2026-10-29 (decisions #96-#98 in `01-decisions.md`).
Replaces the missing `plans/default-door-appearance.md` that the TODO item cited.

## The problem

A door has four widths: the **nominal leaf** you order (32x80), the **unit** (leaf plus its
jamb, about 33.5 wide), the **rough opening** you frame (about 34 x 82), and the **clear
passage** a code reads (about 29.5 for a 32" leaf). `DoorType.width` and `height` hold one of
these, and *which one* depends on the type:

| Type | `width` | Means |
|---|---|---|
| `DT-INT-SWING32` (library), most interior types | 2'8" | nominal leaf, going by the tag and the pocket-kit lookup |
| `DT-POCKET-INT-*` | leaf | nominal: `_door_pocket` looks up the kit with `round(width.inches)` |
| `DT-EXT-SWING32-G`, `DT-EXT-FRENCH60-CATALOG` | 34", 63.3" | RO; nominal and unit live in `catalog_dimensions` |
| `DT-INT-BOOKCASE36` | 38" | RO; nominal lives in `bookcase_door` |
| `DT-EXT-SWING36`, `DT-EXT-FRENCH60` | 3', 5' | ambiguous: no catalog data |

But resolve reads every one of them as the RO:

- `resolve/pipeline._opening_size` makes it the void, the centre, the swing arc and the
  pocket run. It never reads `catalog_dimensions`.
- `resolve/framing/openings` frames that number: jack/king stations and the header length.
- `resolve/door_product_spec` and `geometry_cased_doors` (with UI `casedDoors.ts`) draw the
  leaf as `void - 2 x (jamb_allowance + leaf_gap)`. So a "32" door comes out a ~29.8" leaf
  in a 32" RO.
- Casing and base runs in `interior_trim_*` stop at the void.

Readers that already know the difference: `checks/.../egress._door_leaf` (R311.2),
`takeoff/openings` (groups by nominal), `emit/draw/schedules/openings` (prints nominal,
unit and RO), and `emit/ifc/architectural`. All four read `catalog_dimensions` directly.

## Decisions (agreed 2026-10-28)

1. **`DoorType.width/height` is the nominal leaf.** A pair counts as one width.
2. **The RO is derived from the `TrimStandard`** unless a product publishes one.
3. **Doors are stock sizes and sourced.** `DT-EXT-SWING36` and `DT-EXT-FRENCH60` get
   `catalog_dimensions` and a `rough_opening` read from the actual product, the same way
   `DT-EXT-SWING32-G` has them. Nothing custom.
4. **R311.2 grades clear width, strictly: below 32" FAILs.** A published clear width and
   height win. Without them, the clear width is estimated from the leaf (see Sizing rules).
   That estimate is a real number and gets graded, not an UNKNOWN.
5. **Only the designated egress door is graded for R311.2.** Mark it explicitly (Phase 4).
6. **Don't re-fit doors on a hunch.** Many are already as wide as they can be. Where the
   derived RO causes a conflict, that one opening keeps its current framing as a **held**
   RO until the change is confirmed. Investigate each case on its own (one sonnet subagent
   per case) and bring it back as a question.
7. **No interior clear-width advisory.**
8. **Windows are out:** `WindowType.width/height` is already the RO, and
   `resolve/opening_flashing` derives the orderable unit from each product's
   `minimum_rough_opening_allowance` and `frame_size_increment`.
9. **D-M-ENTRY takes its published RO, after investigation.** Therma-Tru 3/0 x 6/8
   inswing, composite frame (2026 Arch 1, Single – Inswing): unit 37-5/8 x 82, RO
   38-3/8 x 82-1/2. Adding the 3/8" pan allowance the French types use makes it 82-7/8.
   That is 2-3/8" wider than today's 36" framing. A 2/10 slab doesn't help: its published
   31-5/16" clear fails R311.2. **Agreed: grow west.** The east jamb stays 6" off
   W-M-STRW's bearing tee, and the RO ends 3-5/8" short of the mech-closet tee at MECH3
   (`from_node` places the opening's start edge; see resolve/pipeline.py `_opening_center`).
   - Trim braced panel BWP-M-N3-0042 to clear the door. Braced line BWL-W-A-N1 has 28'-2"
     against 12.56' needed.
   - Try to keep the doubled hardening pack on the hinge side by framing it with care, for
     example letting the pack bear on or share the MECH-E tee's studs, as the east side
     already does with the STRW tee (exterior_door_hardening.md, "Entry fit"). If it truly
     won't fit, a single king and jack on the hinge side is acceptable. The strike side
     stays doubled.
   - Accept the hinge-side casing scribed to about 2.2" against W-M-MECH-E.
   - Check the raised head (+2-7/8") against the canopy truss chords at +7'-4"
     (lighting.py ~1074).
10. **D-M-BALC stays its own type.** It differs from the patio and study pairs on purpose:
    the main-floor pair is the more secure one (dearer hardware against break-in), and the
    other two relax that where it clearly saves cost. All three are the same Therma-Tru
    Smooth-Star full-lite pair with a 7/8" astragal, so `DT-EXT-FRENCH60` takes the same
    Arch 1.4 sizes (5/0 x 6/8: unit 62-9/16 x 82, RO 63-5/16 x 82-1/2, plus the pan
    allowance). It keeps its own hardware and installation and is **not** retired. Goals
    for its main-floor installation review: secure, well designed, ready to build, with
    rot-resistant detailing.
    **Agreed: re-centre it under D-S-DECK-E.** Grown in place it would sit 1.66" off the
    pair above and clip the porch switch casing. Re-centred (offset 8-11/32" off N-M-S1,
    like upstairs), it clears the switch and the exterior GFCI.
    - Shorten corner braced panel BWP-M-S2-0000 to about 8.3" (corner panel about 33"),
      and confirm its hold-down end condition.
    - About 2.3" remains between the doubled pack and the W-M-C1 tee.
    - Raise curtain-rod backing BK-M-S2-ROD (backing.py:164) above the new head.
    - Correct the 19" gap comment at main.py:1328 (WIN-M-LIV-S2 is now about 17" off).
    **But first, try moving all three French pairs together.** D-B-PATIO, D-M-BALC and
    D-S-DECK-E may shift together so that each lands on an ideal façade line *and* the stud
    module, if a shared position exists. Today D-M-BALC is 8" off the module
    (`structural.door_framing_module` suggests centre 48"). Give this its own
    investigation in phase 2, and come back with the options before settling on the plain
    re-centre.
11. **A pair is graded on both leaves**, unless a fixed centre post or mullion stands
    between them (some tilt-turn pairs have one). Then only the active leaf counts. R311.2
    asks for 32" of clear width and has no single-leaf clause; the one-leaf rule is the
    IBC's (1010.1.1), a commercial rule.
12. **A held RO is an advisory.** It is listed by `haus check`, but it doesn't block the
    permit gate.

Record decisions 1, 2, 4, 5, 6, 11 and 12 in `01-decisions.md`.

## Sizing rules

One equation, used both to derive an RO and to check that a leaf fits one. `a` is
`TrimStandard.jamb_allowance` (jamb board plus shim, 1" in catlin), `g` the leaf gap
(`CasedDoorDefaults.leaf_gap_m`, 3 mm). With no `TrimStandard`, `a` falls back to
`CasedDoorDefaults.jamb_allowance_m`, as `door_product_spec` already does, and the basis
says so.

- **Width:** `rough_w = leaf_w + 2(a + g)`. A 32" leaf needs 34.24". A pair adds one more
  `g` at the meeting stiles.
- **Height, from the subfloor:** `rough_h = finish + undercut + leaf_h + g + a`. `finish` is
  the floor build-up at that opening (the higher of the two sides, as `door_product_spec`
  takes `max(base, *floors)`), so height depends on the opening, not just the type.
- **Fit:** an RO fits when it is at least the derived one in both directions.
- **By operation** (the six real `DoorOperation` members; the table test needs a row each):
  - `SWING`, `DOUBLE_SWING`: the equations above.
  - `POCKET`: see below.
  - `SLIDE`, `BIFOLD`: the same equations until a sourced track or bifold product says
    otherwise; the basis says "generic".
  - `OVERHEAD`: the door is sized to the RO (garage doors are ordered by opening). `rough_w/h`
    are the authored width/height; no leaf derivation.
- **Pocket doors carry two widths.** `passage_w` is the leaf (36"); `frame_w` is the kit's
  whole cassette RO (Eclisse 36: 74.5"). `width_m` stays the passage, and
  `pocket_run_m = frame_w - width_m` (38.5"), so positioning and every consumer that adds
  `pocket_run_m` are unchanged. The kit table has widths only; add the RO height
  (Eclisse: H1 + 1/4" from **finished** floor, 83.25" for an 80" leaf) as a new kit field,
  which closes the "RO height" gap in `houses/catlin/notes/pocket_frame_eclisse.md`.
- `catalog_dimensions` keeps the **unit** and the source; its `nominal_*` fields fold into
  `width/height` (one place for nominal). `bookcase_door.nominal_*` does the same. When a
  published unit is present, the check is that `unit + 2a_shim` fits the published RO.
- **Clear width**, swing at 90°. A published figure wins, on `catalog_dimensions` as
  `clear_width_90` and `clear_height`, so the egress door is graded on its maker's
  numbers. Therma-Tru, 2026 Arch 1.29–1.30 "Hinged Clear Opening":
  - Single, composite frame: 2/8 → 29-5/16", 2/10 → 31-5/16", 3/0 → **33-5/16"**. That is
    a flat **2-11/16"** under the slab at every size.
  - French with 7/8" astragal, both leaves at 90°: 5/0 → 56-3/8".
  - Clear height, 6/8 inswing composite: **79-1/4"** (outswing composite 78-7/16").
  Without a published figure, the estimate is `leaf_w - 2-11/16"`, citing that table, with
  the basis "estimated: Therma-Tru deduction". An authored `clear_passage` on the type, or
  `bookcase_door.clear_passage_width`, overrides both.
  - A **pair** (decision 11) is graded on both leaves together, using the published pair
    width or `2 x leaf_w - 2 x 2-11/16"`. When the type has a fixed centre post or
    mullion (`DoorType.center_post: bool`), only the active leaf counts.
  - A door **limited below 90°** (a stop or wall) is graded at its limit angle; the swing
    already carries the angle.
- **Clear height** is installed, not the leaf: top of threshold to underside of head stop.
  A published figure wins. Otherwise it is computed per opening, from the sill's
  `threshold_height` (D-M-ENTRY authors 1.5") to the head stop. Basis string as for width.

## Phases

### 1. One resolver, zero geometry diff

- New `resolve/door_sizing.py`:
  `door_sizing(opening, door_type, trim_standard, kit, floor_finish) -> DoorSizing` with
  `leaf_w/h`, `unit_w/h | None`, `rough_w/h`, `passage_w`, `frame_w`, `clear_w`, `clear_h`,
  and a `basis` per value ("published RO", "derived: 1\" jamb allowance", "pocket kit
  1500PF", "held"). Put it on `ResolvedOpening` as `sizing`. `width_m/height_m` stay the RO.
- Add `DoorType.rough_opening: OpeningSize | None` for a **product's published** RO, and
  `Door.held_rough_opening: OpeningSize | None` for **one opening's temporary framing
  constraint** (decision 6). They are different things: a type is shared (catlin uses
  `DT-INT-SWING32` six times and `DT-POCKET-INT-36` three times), so a held RO on the type
  would hold every opening of it. Confirm `haus build --inspect` accepts the constructor in
  the editable dialect.
- Migrate: catalog and bookcase types move `width` into `rough_opening` and their nominal
  into `width`. Every other door that is not overhead gets `held_rough_opening` equal to
  today's width/height. For a held opening the leaf is inferred from the RO
  (`rough_w - 2(a + g)`, what is drawn today), and an advisory lists each held opening and
  the RO its nominal leaf needs.
- Point `_opening_size`, `_door_pocket`, `egress._door_leaf`, `takeoff/openings`,
  `takeoff/doors` (kit selection by `passage_w`, not `width_m`), `schedules/openings`,
  `emit/ifc/architectural` and `door_product_spec` at `sizing`, so no reader opens
  `catalog_dimensions` or `bookcase_door` for a dimension any more.
- Gate, three parts, since the catalog JSON changes on purpose:
  - Resolved geometry equal: a test snapshots each opening's void, centre, swing,
    `pocket_run_m` and framing members before and after.
  - `haus check houses/catlin --only all` findings equal, apart from the new held advisory.
  - `haus build --json` diff limited to an explicit allowlist of keys (type `width`,
    `rough_opening`, `catalog_dimensions.nominal_*`, `sizing`). Drawing and schedule
    goldens untouched.

### 2. Derive ROs, one opening at a time

- Drop `held_rough_opening` from openings, so they derive. Each interior door's framing
  grows by about 1.1" per side and roughly 2" in height.
- Expected blast radius: stud stations, header length (takeoff LF), base and casing LF,
  receptacle and switch spacing at latch jambs (`DT-INT-SWING32-TRIMLESS-PUSH` was sized
  down for 4" of switch wall), door-to-wall-end and door-to-corner clearances, swing
  conflicts, placeable collisions.
- Measure first: drop all holds in a detached worktree and diff the FAILED lists and
  `takeoff --csv`. Openings with no new finding lose their hold in main. Each opening that
  conflicts keeps it and goes to its own sonnet subagent, which reports what the wider
  opening would hit and the options (widen and move X, or step down a leaf size), and does
  not edit. Each one comes back to you as a question.
- `DT-EXT-SWING36` and `DT-EXT-FRENCH60` get their Arch 1 sizes and clear figures in
  phase 1 (decisions 9 and 10), with D-M-ENTRY and D-M-BALC held at today's framing. Both
  were investigated on 2026-10-28 (each change measured in a detached worktree; baseline 0
  FAIL). Release the holds here with the agreed changes:
  - D-M-ENTRY grows west: one braced-panel FAIL, fixed by trimming the panel, plus one
    casing scribe advisory.
  - D-M-BALC is re-centred: one braced-panel FAIL and one stud-module advisory. Before
    settling it, the three-pair façade/stud-line study from decision 10 runs (one sonnet
    subagent, report only).
- Since the inferred leaf equals the nominal once the RO is derived, leaves barely move.
  Framing, trim and takeoff do.

### 3. Every leaf, arc and symbol from `sizing`

- `_door_swing_clearance` hinges at the jamb face (`rough_w/2 - a`) and sweeps `leaf_w`.
- Every consumer that derives a leaf or arc from the void reads `sizing` instead:
  - Engine: `door_product_spec` / `geometry_cased_doors`, trimless and glazed leaves in
    `geometry_door_products`, French pair, slide, bifold and overhead leaves in
    `geometry_openings`, and the plan symbols in `emit/draw/door_symbols` and `floorplan`.
  - UI: `three/builders/casedDoors.ts`, `doorProducts.ts`, `components/plan/OpeningShapes.tsx`
    (its arc sweeps `o.width_m` today), and placement, which turns the chosen type's width
    into an opening start. The catalog serializes each type's derived `rough_w` for that.
    The UI reads `sizing` from the model and never re-derives it.
- Fit enforcement starts here, after the migration: a published or derived RO that the
  leaf doesn't fit is a load-time ERROR. A held RO is exempt; it stays an advisory.
- Parity: engine and UI fixtures for cased, trimless/glazed, pair and pocket leaves agree
  with the plan symbol on leaf width and hinge point.

### 4. Designate the egress door, then grade it

- Today `code.R311_door_width` and `code.R311_2_door_height` grade **every** exterior door,
  including the garage service door and the overhead door, because nothing designates one.
- Add `Door.egress: bool = False` on the placed door (placement makes a door the egress
  door, not its type). Catlin marks `D-M-ENTRY`.
- New `code.R311_1_egress_door`. FAIL when no door is designated, or when a designated door
  is not exterior, not side-hinged (`SWING` or `DOUBLE_SWING`), or its interior side is the
  garage. The adjoining room needn't be habitable: `D-M-ENTRY` opens from
  `RM-M-MUDROOM`, a STORAGE room, which R311.1 allows. It doesn't grade the route from
  every room (see Out of scope), and the checklist text says so.
- R311.2 width and height grade **only** designated doors, against `sizing.clear_w` and
  `sizing.clear_h` (installed, not the leaf). Other exterior doors get no R311.2 finding,
  which is not an N/A: the rule doesn't cover them.
- **Landings (R311.3), corrected.** The 2018 IRC and MN 1309.0311 subp. 1 (read
  2026-10-28) give:
  - Required egress door (R311.3.1, not amended): ≤ 1.5" below the threshold, or ≤ 7.75"
    on the exterior side if the door doesn't swing over the landing.
  - Any other exterior door (MN R311.3.2): "not more than 7-3/4 inches (196 mm) below the
    top of the threshold", **with no swing condition**. Exception: no landing is needed
    where a stairway less than 30" high, measured from the interior floor to finished
    grade, is on the exterior side and the door doesn't swing over it. (The IRC's own
    exception counts two risers; MN measures height instead.)
  Today's check applies the egress rule to every door, so a non-egress outswing door with
  a step over 1.5" FAILs falsely. Rewrite the branch to read the flag, and cite 1309.0311
  in the code comment.
- Register `code.R311_1_egress_door` on the permit checklist in
  `checks/code/mn_residential/profile.py`, beside the R311.2 line.
- Oracle note: `houses/catlin/notes/egress_door_clear_width.md` quotes the Arch 1.29–1.30
  rows for D-M-ENTRY (33-5/16" clear, 79-1/4" high: PASS) and hand-works the
  2-11/16" fallback for a 3/0 to the same figure, so the estimate is checked against
  the published one.

## Out of scope

- Windows (decision 8).
- Route validation for R311.1 (garage avoidance from every room). catlin's garage is
  detached, so no route can pass through it. A prototype room graph confirmed it on
  2026-10-28: every room reaches RM-M-MUDROOM through doors and stairs, and RM-GARAGE
  connects to nothing indoors. If an attached-garage house ever needs the check, the
  pieces exist: `_sides` in `checks/advisory/acoustics.py` for door room-pairs, and stair
  outlines for links between storeys. It would also need "passable" defined (doors and
  walk-through rough openings, not hose-bib, ERV or niche openings).
- Jamb stock and purchased prehung jamb width: `jamb_allowance` stays the single knob.

## Tests

Add a test only where it catches a regression nothing else does; prefer extending an
existing test to adding a module, and pure functions over catlin fixtures.

- One small table test on `door_sizing` (a pure function, no house load): a row per
  `DoorOperation`, published RO wins, and a derived RO passes its own fit check.
- Pocket: `width_m + pocket_run_m == kit RO`, folded into the existing pocket-run test.
- Phases 2 and 3: re-bless the existing cased-door fixtures (engine and UI parity) and
  jamb-pack tests; no new ones.
- Phase 4: two regressions, as rows in the existing egress tests: no designated door
  FAILs, and a non-egress outswing door at a 7.75" step passes (today's false FAIL).
  catlin's own `haus check` covers the rest.
- Phase 1's zero-diff gate is a one-off measurement in a detached worktree, not a
  committed test.
