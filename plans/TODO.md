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

- **`EQ-S-HP1-AH.zone_rooms` names `RM-A-STUDIO-BATH`, a tag that names no room — and two
  parts of the repo disagree about whether that is a typo (2026-08-30).** The attic guest
  bath is `RM-A-STUBATH`.
  - `plan/electrical.py`'s comment above that list (2026-08-29) says all three of the split
    west loft's rooms are named there because one boot conditions the whole footprint, and
    that "dropping either from this list would report them as unheated rather than as what
    they are". The typo does exactly that, silently.
  - `tests/test_heating_capacity.py::test_catlin_zone_loads_do_not_exceed_the_whole_house_load`
    (also 2026-08-29) pins `RM-A-STUBATH` as **deliberately** unclaimed, with a physical
    argument: it is exhaust-only (`REG-A-STUBATH-EXH`, 20 cfm continuous) and takes make-up
    air under the door, so a supply boot would short-circuit its own extract.
  - Both cannot be right, and the difference is a real HVAC decision, not bookkeeping.
    Whichever way it goes, the dead tag should stop being a dead tag. Fixing it silences one
    of `mep.heating_capacity`'s four unclaimed rooms; the other three (`RM-B-ESS`,
    `RM-M-MUD-CLOSET`, `RM-M-PANTRY`) are documented as intentional and should stay.

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

- **What braces the porch and balcony east-west, now that the arch is gone?**
  (raised 2026-08-18, and the one item on this list that the arch swap *created*.)
  **HALF-CLOSED 2026-08-30, and read which half.** `W-SG-ARCH` is back on the same node pair
  as a buried grade beam, so the FOUNDATION has an E-W element again and the retaining walls'
  loop is closed — that is what took catlin back to 0 FAIL. But the beam is entirely **below
  the garden floor**: it braces the concrete box, and it does nothing for the porch deck or
  the balcony one and two storeys above it, which is what this item was actually about. The
  masonry the pillars were grouted into is still gone and still is not coming back. Everything
  below stays live for the structure above -9'-1 7/16".
  Removing
  `W-SG-ARCH` and the three `W-SG-RAIL-*` parapets removed the structure's only E-W shear
  element: the two side walls run N-S and brace that direction only, and the masonry the
  balcony pillars were grouted into was the de facto fixity for five of the six. Simpson say
  so themselves — ESR-1622/ESR-3050: *"post bases do not provide adequate resistance to
  prevent members from rotating about the base"*, and they are *"not recommended for
  non-top-supported installations (such as … guard rails)."* Nothing is authored for this and
  **nothing should be until it is decided** — a number invented in the model is worse than an
  open question.

  **2026-08-30: the model now carries a design wind speed, and this entry stays open.**
  `plan/site.py` authors `design_wind_speed_mph=115.0`, `wind_exposure="B"`,
  `risk_category="II"` — MN Rules 1309.0301's amendment to IRC Table R301.2(1), which is
  statewide, plus a site-specific exposure per R301.2.1.4. That removes the input whose
  absence every `structural.uplift_load_path` finding used to name, and it is the input a
  demand calculation needs. It is **not** a lateral design and does not close anything below:
  a speed is not a pressure, a pressure is not a storey shear, and a storey shear is not a
  distribution to elements. What it does mean is that the "cheapest option" bullet's
  parenthetical — that nobody can even check whether the two centre pillars need bracing — is
  no longer true, and `structural.lateral_racking` now reports a computed demand-to-capacity
  ratio per braced bay. Read that check's findings and
  `houses/catlin/notes/balcony_lateral_bracing_design.md` before re-litigating any bullet
  here; the doctrine at the head of this item is unchanged.

  **2026-08-30: the balcony's E-W COLLECTOR is decided; the engineered-lateral question
  below is not.** The four E-W girts (the horizontal members the corner knee braces rose
  into) are retired for two continuous 2x8 "brace rails," one per pillar row, face-bolted
  to the inboard face of all three posts in that row rather than seated on their tops
  (`houses/catlin/params/sunken_garden.py::SPEC.balcony_brace_rail`). This is deliberately
  **lateral-capacity-neutral** — same four corner posts braced, same two directions each,
  same 2x6 `APVKB45-6` braces, same 3' leg; only what the E-W braces land on changed (a 2x8
  rail instead of a 2x12 girt segment) — so it does not answer, and does not presume an
  answer to, any option below. What it does do: it removes a bookkeeping fiction (a girt
  claiming `bearing_refs` on the two centre pillars it only incidentally lapped 0.5"x1.5"
  of, which billed 8 phantom `KBS1Z` uplift straps at joints that were not real beam-on-post
  bearing), and it ties the two centre pillars into the braced end bays through the rail's
  own continuity — which is what lets leaving them unbraced (Option 1 below) stay
  defensible, on a narrower rationale than before: "the rail already reaches them," not
  "thrust would hit `PT-SG-BR2`" (already false since 2026-08-28). What is genuinely still
  open, narrower than before: what a licensed lateral design would actually spec for the
  RAIL/BOLT connection itself — the 2 x 1/2" HDG through-bolts per post (12 total) are an
  *assumed*, not an engineered, schedule, pending real numbers.

  **The porch's own E-W bracing is a separate question and this change does not touch it.**
  The porch bears directly on the two concrete side walls (`W-SG-W1`/`E1`) rather than on
  post bases, so its E-W lateral path is a concrete/geotech question — wall reinforcement,
  footing width, whatever a lateral design calls for there — not a framing-collector
  question the way the balcony's was. It stays open, undiscussed by anything above.

  The options, in ascending cost:
  - **Extend the knee-brace rule to the centre pillars.** DCA6-2015 p.10 wants a brace on any
    post over 2'-0"; `PT-SG-BR2`/`BF2` are deliberately left as leaning columns today
    (`params/sunken_garden.py`, KNEE_BRACES). **The stated reason for that is gone as of
    2026-08-28**, and this entry has to say so: the objection was that bracing them pushes
    thrust into `PT-SG-BR2`, the one pillar standing on the *cantilevered tip* of the porch
    joists. The rear pillar row has since moved onto the back-beam line, so `PT-SG-BR2` now
    lands over `PT-SG-COL` on a full stack to concrete, and `PT-SG-BF2` always did over
    `PT-SG-FCOL`. Both centre pillars are over a beam-and-column line now. That makes this
    the cheapest option on the list at **$120-250** and removes the reason it was rejected —
    it does **not** make it the answer. **Do not author bracing here.** The lateral design
    stays the consultant's call, per the doctrine at the head of this item: a number invented
    in the model is worse than an open question. What changed is the premise, not the verdict.
  - **A moment base at the four corner pillars.** `MPB66Z`, ESR-3050 Table 11: 2,680 lb-ft
    unreinforced — but it needs **5" of side cover**, and *no column in this structure has
    it any more*. `PT-SG-FCOL` did while it was a 16" square (5.00" at a centred 6" plate's
    corners); it went to a **16" round on 2026-08-28**, which leaves 3.76", because the
    square was costing $478-1,327 against $304-633 for a fibre tube and nothing was bolted
    to its top. That was a deliberate trade with this option written down as its price —
    see `houses/catlin/notes/uplift_load_path.md` and `plan/assemblies.py`. It is also a
    cheap revert: an **18" tube gives 4.76" at $335-705** and a **20" gives 5.76" at
    $369-781**, so the cover comes back for *less* than the square cost, not more. The four
    pillars that actually want the base bear on 12" concrete wall tops and were never
    covered either, so this option always needed a pour change somewhere.

    **Correction 2026-08-28: the "18"/20" revert" above is cheaper than it looks only in
    concrete, and this entry understated it.** `SPEC.front_column_size_in` fed
    `_y_ax_front = _y_in_n - porch_clear_depth_ft - front_column_size_in/24`, so widening
    the column moved the balcony's front pillar row, the deck outline, `RL-SG-BALCONY`, the
    gutter and leader line, and another module's geometry through
    `PORCH_FRONT_AXIS_Y_FT`.

    **Superseded 2026-08-29 on both halves, and the numbers here are now stale.**
    (a) The coupling is gone: `porch_front_edge_offset_in` holds the beam plane at -9.5'
    and the column's diameter no longer says anything about it, precisely because the
    column stopped being centred on that plane. (b) `PT-SG-FCOL` **is a 20" round now**,
    for an unrelated reason — it became the shared bearing for the two front beams AND
    `PT-SG-BF2` when the balcony's front row moved 12" south — so the 5.76" of side cover
    arrived as a side effect and the "$369-781 revert" price is not what it cost. The
    installed line is `$478-967` (10.08 LF of 20" tube; see `prices.toml`), and the step
    over the 16" was ~`$85-150`, already spent. **What has NOT changed is the verdict:**
    the four pillars that actually want an MPB66Z are the corner ones on 12" concrete wall
    tops, and they are still not covered. Re-do the side-cover arithmetic against 20"
    before quoting any number in this bullet.

    **2026-08-30, one number to be careful with.** The 5.76" above is a plate centred on
    the *column*. The one base that actually sits on `PT-SG-FCOL` is `CN-SG-BASE-F2`, under
    `PT-SG-BF2`, and that post is 4 3/8" off the column axis — so its plate corners have
    ~2.0" of cover, not 5.76". (It was ~1.6" before the front pillar row came 2 3/4" north
    the same day.) An `ABU66SS` is a pinned base and asks for edge distance at the anchor,
    which is 5 5/8" and fine. An `MPB66Z` there would not be, and never was.

  - **An engineer's lateral design.** The honest answer, and the same consultant the two
    side walls below already need. **Narrower since 2026-08-30**: with the MPB66Z option
    closed and the balcony's E-W collector now a capacity-neutral construction detail (the
    brace-rail redesign above), what specifically needs a licensed number is the rail/bolt
    connection — the 2 x 1/2" HDG through-bolts per post assumed in
    `params/sunken_garden.py` — plus whatever, if anything, the consultant wants at the two
    still-unbraced centre pillars. The porch's own E-W path (see above) is a separate ask
    to the same consultant, not folded into this one.

    **2026-08-30, second pass: the bolt question got bigger, not smaller.** The four E-W
    braces' feet were re-read and found unbuildable — coplanar with the rail, they had been
    detailed as if they butted the pillar, and resolved onto the pillar's *corner* with zero
    contact area. They are face laps now (`KneeBrace.plane_offset` / `.foot_lap`), lapping
    5 1/2" across the pillar's inboard face on two 1/2" x 8" HDG bolts. So the assumed bolt
    schedule this bullet already flags is no longer only the rail's: on those four braces it
    is the **entire connection at that end**, with no strap beside it and no bearing behind
    it. `notes/balcony_lateral_bracing_design.md` §4a records the geometry and §5 the two
    NDS yield modes it works and the four it does not. Nothing about the demand moved.

- **Two porch/balcony span knife-edges, written down 2026-08-28.** Neither is a finding
  today and neither had been recorded anywhere before. `structural.deck_beam_span` looks IRC
  Table R507.5(1) up on the **joist** span the beam carries, and the table's rows are
  6/8/10/12/14/16/18', so the lookup steps down in cliffs rather than sliding — a small
  change in a joist span can fail four beams at once.
  - **Porch: 9" of joist-span headroom.** `FS-SG-PORCH`'s joists span 7.25', which reads the
    8' row → a 10.25' limit against the four porch beams' 10.00' span. At a joist span of
    8.01' the lookup drops to the 10' row (9.17') and **all four porch beams FAIL by 10"**.
    Deepening the porch, or moving the back-beam line north, is what would do it.
  - **Balcony: retired, and worth keeping visible.** `FS-SG-DECK`'s joist span is *exactly*
    10.00', reading the 10' row (9.17'). Any increase drops it to the 12' row (8.33'). Until
    2026-08-28 the balcony beams spanned 8.667' and that step would have failed all three;
    moving the rear pillar row onto the back-beam line took the span to 7.00'. The front row
    then moved 12" south on 2026-08-29 and gave 12" of that back — **the back span is 8.00'
    now**, which still clears the 12' row (8.33') by 4". The knife-edge is gone, the cliff is
    not, and the margin is a third of what it was a day earlier.
  Anything that changes a beam section here — including the PWT LVL lead below — has to be
  re-checked against both. Also in `houses/catlin/notes/beam_water_protection.md`.

- **Widen `structural.landing_post_bearing` past stair landings.** It is the rule that
  would *positively confirm* what the 2026-08-29 change bought — `PT-SG-BF2` bearing on
  concrete rather than through a 2x8 — and it cannot see the joint, because it is scoped to
  stair landing posts only. Nothing else in the model grades cross-grain bearing under a
  post, which is why `PT-SG-BR2` stood on a single joist ply for a day with 0 FAIL and why
  its squash blocks are authored rather than derived. **Not a one-line scope widening:**
  `_bearing_element_under` has to learn about a FloorSystem's blocking members and its sheet
  thickness first, or turning it on adds ~10 FAILs to a house that has none — the eight
  heat-pump stand legs, `PT-SG-BR2` and `PT-SG-BF2` — every one of them a false report about
  a joint that is answered.

- **Verify the PWT treated LVL lead — one phone call.** `notes/beam_water_protection.md`
  records that the real durability defect in these beams is **fourteen site-built ply seams**
  that hold water and grit and freeze ~100×/year, and an *unverified* Pro Deck Supply
  (Minneapolis) listing for PWT treated LVL 1¾" × 11⅞" at $223.20/12'. Two plies over the
  three balcony beams is ≈ $970 against ~$242-413 for the 3-2x12s: a **~$550-725 delta that
  removes the seams rather than taping them**. If it holds, the "Treated LVL is not a
  product" answer immediately below — and the 2026-08-23 note that carries it in
  `params/sunken_garden.py` — needs rewriting, because it was about Parallam Plus PSL depths
  and says nothing about LVL. Not verified; nothing should move until it is.

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
  - **six earned N/A** — four balcony pillars on `W-SG-W1`/`E1` (foundation walls with their
    own strip footings), `PT-SG-BR2` on `FS-SG-PORCH` (a post on a deck is not a post on the
    ground), `PT-SG-BF2` on `PT-SG-FCOL` (its load leaves through that column, and that
    column's own item picks up the share);
  - **two PASS** — `spread_footing/PT-SG-COL` and `/PT-SG-FCOL` compute bearing on the belled
    piers: 1,245 and 1,477 psf against IBC Table 1806.2's presumptive 2,000 for this site's
    GM. `engineering/spread_footing.py`, oracled by `notes/sunken_garden_piers.md`;
  - **two still UNKNOWN, for a NEW and better reason.** `deck_post/PT-SG-COL` and `/PT-SG-FCOL`
    now compute the axial demand and find the sections at d/c 0.095 and 0.054 — a factor of
    ten and nineteen spare. What they cannot do is grade a column ACI 318 does not permit to
    be plain concrete, because **`Post` carries no `vertical_reinforcement` field** and this
    model therefore cannot state a bar schedule even if one existed. Both are COLUMNS and not
    pedestals (h/d 10.7 and 6.4 against a pedestal's 3). See the decision below.
  (`deck_beam_span` itself is fully green: two genuine R507.5(1) overspans closed 2026-07-31
  by going engineered, and the balcony three closed 2026-08-23 prescriptively.)

- **DECISION: should `Post` grow a `vertical_reinforcement` field?** (raised 2026-08-30 by the
  two piers above.) `FoundationWall` has one and it is what let the sunken-garden retaining
  stems be graded properly the same day. Without it on `Post`, `deck_post/*` can never report
  anything but INCOMPLETE for a cast column, however well designed — the engine has nowhere
  to put the answer. The alternative is to close both items in `engineering.toml` with the
  engineer's cage schedule and leave the model silent, which works and leaves the drawings
  unable to say what the columns contain. Not decided here.
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

- **`DU-S-HP-SOUTH`'s rise — STILL OPEN, and now for a reason rather than for want of a
  field.** Every comment in `plan/mep_hvac.py` calls it "the riser out of the trunk head at
  x=19'-4"", and the trunk head is at (19'-4", 9'-7") — but `SF-S-DUCT` stops at y=6'-0" and
  the branch drops into its bay at (19'-4", 3'-4"). Nothing connects those two points without
  either crossing five FS-ATTIC I-joists in a bay (illegal) or running along the attic floor
  through a habitable room. Both are route decisions rather than draughting, and the
  2026-08-25 pass was explicitly forbidden from moving a System 1 trunk. Decide the route,
  then draw it: the field is there and waiting.

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
  the manufacturer's fan curve, not the rating point. Those comments want correcting.

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
- Make sure all desired access panels are in (deferred pending more design items settling)
- Make sure the floor trusses (of the first to second floor) are modeled more accurately in 3d and make sure their measurements in the BOM are very exact for manufacturing
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

 - Make sure 7" threshold to basement from sunken garden
 - Basement under the stairs storage closet
 - For the breezeway sonotubes, something like https://www.homedepot.com/p/Bigfoot-20-in-Pier-Footing-Form-489-20-BF/300325004 for a "single pour footing". However right now it looks like those footings bisect the house and garage foundation walls. Perhaps the beams should be slightly cantilever to push them further out? Or we could link it in straight to the garage footings as one level?
 - Improve the framing logic of the girts/outriggers holding the insulation and cladding of the catlin house. Especialy on the gable ends, it seems the spacing of these isn't always correct and optimal. Perhaps also increase the spacing (I believe and earlier review concluded 32" OC was sufficient)

- **The R312.1.1 guard on the garage stair's 34" landing.** An owner decision with a cost
  and a look to it, flagged in `plan/storeys/garage.py`. It comes with an engine gap worth
  its own item: `code.R312_1_guard_height` censuses `FloorSystem`s and `code.R312_1_guard`
  censuses `FloorOpening`s, so `SL-G-STEP-0` — a `Slab` — is in neither census and its 34"
  drop is graded by nothing. A rule that walks slab edges would close it.
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
- I am reasonably certain that FX-S-BATH1-LAV is in the way of the door swing for the bathroom.
- Sink FX-A-STUDIO-BAR-SINK is floating off the floor and doesn't appear to have a plumbing connection, nor do the bathroom fixtures for that attic bathroom.

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
- **`ResolvedRoom` carries neither clear height nor glazing ratio** (`resolve/model.py`).
  Every consumer re-derives them and neither reaches `model.json` — which is why the glazing
  table above had to be scraped out of check messages rather than read off the model.
- **Four `AlarmKind` members only** (SMOKE / CO / COMBO / HEAT). No leak or freeze kind, and
  `emit/draw/floorplan.py:316-317` is a hard index that `KeyError`s the whole plan sheet on a
  new member without a label — so adding one is a two-file change, not a one-line enum edit.
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


## What I am unhappy with
- The price (cost-options.md is missing some of the style details as 'optional' and it needs to be slimmed down to be more concise)
- The concrete deck of the basement (either size up for completeness or down for cost savings)
