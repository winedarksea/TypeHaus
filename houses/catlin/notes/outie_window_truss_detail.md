---
title: "Outie Window in a Truss Wall — detail and build order"
applied_to:
  - detail: outie_window_truss_detail
  - assembly: CATLIN_EXT_2X6
  - assembly: PLANT_EXT_2X6_HUMID
  - transition: TR-CATLIN-FRAMED-OPENING
tags:
  - wall
  - window
  - insulation
  - air-barrier
  - water-management
  - sequencing
source:
  - plan/assemblies.py CATLIN_EXT_2X6
  - resolve/framing/truss_wall.py
  - resolve/framing/truss_girts.py
  - resolve/framing/truss_common.py
  - emit/draw/detail_components/opening.py outie_window_truss
  - notes/catlin_truss_engineering.md
---

# Notes

## What the wall is

`CATLIN_EXT_2X6` is a **catlin truss wall** (2026-08-26). Outboard of the 2x6 studs and their
1/2" plywood sheathing there is 4" of 2 lb closed-cell spray foam, and the cladding stands off
on **two tiers of flat horizontal girts** — all 2x4 stock, all laid flat, nothing on edge:

| piece | what it is | where |
|---|---|---|
| block-1 | SPF 2x4 offcut, 3-1/2" along the wall × 3-1/2" tall × 1-1/2" thick | on the sheathing over a stud, under every girt course, 0 → 1-1/2" |
| inner girt | **SPF** 2x4 flat, horizontal, 32" o.c. | on the block-1s, 1-1/2" → 3", buried in foam |
| block-2 | **KDAT** 2x4 offcut, same piece | on the inner girt, MID-BAY (8" off block-1), 3" → 4-1/2" |
| outer girt | **KDAT** 2x4 flat, same 32" courses at the SAME elevations | on the block-2s, 4-1/2" → 6"; the cladding nailer and the window mount plane |
| jamb post | 2x4 flat, vertical, one per band | at every RO edge, inner face ON the edge |
| head/sill course | 2x4 flat, one per band | spanning the RO between the two posts |
| cladding | snap-lock standing seam | clipped to the outer girts, 6" → 6-1/2" |

Foam total 4": band A (1-1/2", crossed by block-1), the inner girt's own 1-1/2" band, and the
inner 1" of band C. Behind the outer girt is a **1/2" vented gap** — the drainage plane —
and that gap plus the 1-1/2" between girt courses is the 2" of drained, back-vented cavity
the bug screen at the base of the wall closes.

**Materials are by exposure, and it is a rule of the design.** Everything inboard of the foam
face is plain SPF: it is encapsulated in closed-cell foam and never sees water. Everything
standing in or outboard of the vent gap is KDAT — the outer girt is a 3-1/2"-deep horizontal
ledge behind the cladding that will wet-cycle for the life of the wall, and block-2's face is
the same ledge every 16" on the foam plane. That is why the two blocks are two BOM rows.

**Two blocks at one station, at a band end.** Both tiers carry the same courses cut into the
same segments, so wherever a course *ends* — at a mitred band edge, at the raked top of an
attic gable — each tier puts its own end block there and the two land at the same station.
Their screws would then be in line, block-2's point arriving in the inner girt exactly where
block-1's shank already is. **Drive that pair with an inch of vertical stagger inside the
block's 3-1/2" height.** It is a construction note and not geometry: everywhere else on the
wall the half-bay offset keeps the two apart on its own, and this is the one place it cannot.

**The blocks are on the STUD module, the girts on their own.** A girt course climbs a 32"
elevation module measured from the storey's floor datum (see the phase below); the blocks
under it are what carry it back to
the framing, so they land at whole multiples of the 16" stud spacing from the wall's layout
line — the same phase the studs take. **Block-2 takes that same module shifted half a bay**,
so the two tiers' screws are offset 8" rather than stacked. That is not a detail: it is what
makes each tier's 5" screw a plain wood-to-wood connection with continuous lateral support
(girt → block → sheathing → stud, or girt → block → inner girt) instead of a fastener bearing
on foam. See `notes/catlin_truss_engineering.md` §3 and §6.

## What this replaced, and how to go back

Until 2026-08-26 this was a **Swinburne truss wall** (2026-08-23): a three-piece chiral pack —
a 2x4 flat block on the sheathing, a 1/2" plywood tab, and a KDAT 2x4 **outrigger on edge**,
vertical, 16" o.c., lap-screwed to the tab. It worked. What went wrong with it was not
structural:

- it is fussy to build — a chiral pack the engine has to slide and sometimes drop, and tab
  lap-screws that were never even billed;
- the outriggers are **vertical**, and so is the standing seam, so the cladding clips had no
  horizontal nailer anywhere;
- and about 150 lines of `truss_frame.py` exist only to resolve pack collisions.

**Nothing vertical was deleted.** `resolve/framing/truss_frame.py` and its branch of the pass
are untouched and still selected by their own predicate (`laid="edge"` + vertical); the girt
frame is a SIBLING selected by `standoff="block"`; the corner box is still there; and the old
layer tuple is kept verbatim in `plan/assemblies.py` as **`CATLIN_EXT_2X6_SWINBURNE`**,
referenced by nothing, like `glazed-green-brick`. Reverting is three edits:

1. give `CATLIN_EXT_2X6` and `PLANT_EXT_2X6_HUMID` that assembly's layer tuple;
2. restore `_WALL_OUTBOARD_IN` (`params/roof_trim.py`) and `_HOUSE_CLADDING_Y`
   (`params/breezeway.py`) to their 5.5"-proud values, and the garage lines 1" south;
3. uncomment the 2026-08-23 rows in `prices.toml` (`2-2x4`, `5x0.5 panel`, `5x0.375 panel`,
   `3-2x4`, `3.5x3.5 panel`, `SDWS22400DB`) and comment the girt ones.

## ** THE WRB IS GONE. THE FOAM IS THE WATER PLANE. **

There is no housewrap and no sheet membrane anywhere in this wall. Closed-cell foam is the
air barrier, the water barrier, the vapour retarder (4" ≈ 0.4 perm, Class II) and the
insulation in one bonded, seamless application. `plan/transitions.py` names `spray-foam-ext`
as the water and thermal continuity face for exactly this reason.

**That makes the build order part of the detail, not a preference**, and the girts add a
second reason on top of the first: *spray foam cannot reach behind a flat girt lying 1-1/2"
off the sheathing.* A flat board shadows the pocket behind it, and foam sprayed after the
girt is on will void there. So band A is its own lift, before the inner girts.

1. Frame the wall. Sheathe it. Cut the rough openings.
2. **Set the bucks.** 3/8" plywood lining each RO on all four sides, from the sheathing face
   out to the mount plane — **6" now, not 5"** — square and plumb. Non-structural: it closes
   the foam at the reveal, gives the reveal a face, and carries the pan and the head flashing.
3. Snap the stud lines. **Tack the block-1s** — one nail each. The block is the screw's
   *spacer*, not its anchor; the 5" SDWS that holds it is driven later, through the girt.
4. **First foam lift, 1-1/2", flush to the block-1 faces.** *Before the inner girts.* This
   step cannot be reordered — see above.
5. **Inner girts**, plus the jamb posts and head/sill courses at every opening, set on the
   blocks. One 5" SDWS per block through girt + block + sheathing into the stud.
6. **Tack the block-2s** mid-bay on the inner girts, 8" off the block-1 line.
7. **Second foam lift, 2-1/2", shaved to a gauge 1/2" behind the block-2 faces** — i.e. to
   the inner-girt face plus 1". Half an inch is inside ccSPF surface tolerance, so this is a
   gauge, not a target; the alternative margins are a 2" block-2 or 3-3/4" of foam.
8. **Outer girts** on the block-2s, one 5" SDWS each.
9. Sill pan, window, head flashing, cladding.

Spraying before the bucks go in leaves a cut edge of foam at every reveal, which is a
discontinuity in the water plane that no sealant closes honestly. Do not do it.

## The window is OUTIE

The unit sits in the **mount plane, 6" outboard of the sheathing** — the outer face of the
outer girt, which is also what the cladding lands on — with its flanges bearing on the jamb
posts and on the head and sill courses. It is not in the stud plane, and no window in this
house carries a depth dimension: the mount plane is derived from the outermost furring
layer's outer face, so it followed the assembly from 5" to 6" without a single window moving.

**Jamb bearing is no longer a question of luck.** The Swinburne wall depended on where a
vertical outrigger happened to land relative to the RO, and had a three-case table (nothing /
filler / jamb outrigger) to handle the misses. A girt wall has **no field member at a jamb at
all** — the field courses are horizontal — so every opening gets its own frame, always:

| piece | where | material |
|---|---|---|
| jamb post | inner face ON the RO edge, 3-1/2" of wall outboard of it, from 3-1/2" below the sill to 3-1/2" above the head | that band's own — SPF inner, KDAT outer |
| head course | post inner face to post inner face, `z_head … z_head + 3-1/2"` | same |
| sill course | post inner face to post inner face, `z_sill − 3-1/2" … z_sill` | same |
| blocks | under every course elevation the post crosses, and under the head and sill courses at every stud station across the RO | block-1 SPF, block-2 KDAT |

**No doubling anywhere, and that is not a saving — it is a consequence.** The Swinburne head
blocking spanned the full clear width between two outriggers, so a 60" French door's head
needed two plies. The girt head course is blocked back to the framing at every stud station
under it — landing on the cripples above the header, ordinary wall, not the void — so its span
is 16" regardless of how wide the opening is. `prices.toml`'s `2-2x4` and `3-2x4` rows are
retired for the same reason; so is the jamb filler, since a post set to the RO edge never
leaves a gap to fill.

All of it is derived, not authored: `resolve/framing/truss_girts.py` places it, and
`structural.truss_wall_opening_support` FAILs if any RO jamb ends up further than a flange's
bearing (1") from wood **that exists at that opening's own elevation**. That check reads the
OUTER band's posts on a girt wall and the outriggers on a Swinburne one — one check, one
constant, two walls — and it is what keeps this table true after the next window moves.

**Field courses stop clear of the frame.** `furring.OPENING_MARGIN_IN` holds every field
course one piece width (3-1/2") clear of each RO, in both axes, so a course never lands in
the plan a jamb post or a head course already occupies. Beyond that margin the courses simply
resume.

## Window elevations against the girt courses

This is the one thing a horizontal stand-off asks of a facade that a vertical one does not,
and it was checked rather than assumed. Re-derived on 2026-08-30, when the band went to
**32" o.c.** and its module was re-phased (`plans/cost-options.md`, the 24"→32" row).

**The finding: no window needs to move.** Measured on the built model, the largest clear gap
between two adjacent nailer courses anywhere beside an opening — above a head or below a
sill — is **29"**, against the field's own 28-1/2" (32" o.c. less the 3-1/2" board). The
median beside an opening is 12-1/2". The girt field around every opening in the house is as
regular as the field away from it. Any window taller than 32" necessarily interrupts some
courses; that is inherent to a horizontal girt and is not a defect, because the courses it
interrupts are replaced by the opening's own head and sill courses at the same job.

### The course phase, and why it is where it is

Two fields on the band's `FramingSpec` say where the module counts from
(`resolve/framing/furring.course_phase`):

```python
spacing=inch(32), course_datum="framing-base", course_offset=inch(-3.5),
```

`course_datum="framing-base"` is `rw.base_ref_z_m` — **the datum a sill height is measured
from**. It is not the wall base: `platform.py` extends a main-storey wall 13-7/16" down over
the floor rim band, and until this change the courses counted from the bottom of that lap
while every sill in the same wall counted from the floor. `course_offset=inch(-3.5)` is one
board face, which registers the module so that **a course TOP lands on the sill datum** —
course bands run `[d − 3.5 + 32k, d + 32k]` above the finished floor.

That phase was chosen by sweeping every offset at 1/8" against all 39 openings on girt walls
and counting **conflicts**: a field course whose bottom is within 7" of an opening's own head
or sill course bottom, which is two nailers inside one board face — either half-lapped in
elevation, or separated by a gap too narrow to be worth a board. Landing exactly on the line
is the best case and is not a conflict: there the field course *is* the head or sill course.

| module | conflicts | edges landing exactly on a course | courses | widest bay |
|---|---|---|---|---|
| 24" from the wall base (until 2026-08-30) | 38 | 8 | 212 | 24" |
| 32", framing-base, **−3-1/2"** | **19** | **16** | **186** | 32" |
| 32", framing-base, +8" | 15 | 13 | 206 | 32" |
| 32", every other offset | 21–43 | | | |

**−3-1/2" is the choice, and +8" is the one it was chosen over.** +8" buys four fewer
conflicts for twenty more courses — it drops the module to 8" above each upper-storey wall
base, so the mandatory starter at the base and the first module course end up 4-1/2" clear of
each other on thirty walls, which is a redundant board at every one of them. −3-1/2" carries
the most exact hits, the fewest courses, and a minimum bay of 6-7/16" that occurs once (the
main storey's starter under the rim band).

**Zero is not reachable, and the plan that asked for it was wrong about that.** The second
storey carries sills at 152" and at 156" — 4" apart, on different walls but on one module.
Any phase that lands exactly on one group is 4" off the other, and 4" is inside the 7"
window. The residual 19 are: eleven at 1/2" clear (the 156" sill group), two at 2", two at
3", two overlapping a gable head by 3", and two door sill courses at a wall base, which is an
artifact of a door whose sill IS the floor and not something a phase can move.

**What a designer should do with a NEW opening**, stated once so it does not have to be
re-derived: land the **sill on the 32" module above the finished floor** (32", 64", 96"), or
the **head 3-1/2" below one** (28-1/2", 60-1/2", 92-1/2"). Either makes that opening's own
sill or head course the field course. `haus build` then shows it, and
`test_truss_girt_courses.py` counts it; a miss costs a redundant board, not a defect.

## Water at the head and the sill

Drawn by the `outie-window-truss` recipe
(`emit/draw/detail_components/opening.py::outie_window_truss`), which is a sibling of the
innie `window-head-jamb-sill` rather than a variant of it — the innie measures both pieces
from the sheathing face, and on this wall neither piece is anywhere near it.

- **Sill pan.** Lies on the sill buck, back dam turned up against the buck's inboard leg,
  running out to the mount plane and turning **down into the vent gap**. It discharges
  *behind* the cladding. An outie pan carried out to a visible drip would put a metal lip
  under every window on the facade, which is not what this house looks like.
- **Head flashing.** Starts on the **foam face** above the head course — the foam is the water
  plane, so lapping onto it is what makes the head continuous — turns out over the head
  course, laps past the cladding and drips. Sealant at the cladding-to-frame joint sits at the
  mount plane, tucked under the drip.

One number told the recipe which wall it is on: the head course is **3-1/2"** tall here (a 2x4
laid flat) against the Swinburne wall's **1-1/2"** (the same board on edge), so the flashing's
upstand starts two inches higher. Everything else — the mount plane, the foam face, the vent
depth — the recipe already read off the resolved stack and needed no telling.

The buck, the head/sill courses and the girts themselves are **not** drawn as convention
linework. They are resolved members, so the cut carries them as the solids they are; drawing
them again would be a second, disagreeing picture of the same wood.

## Why the change, honestly

**Not R-value, and the model's own card overstates it.** `haus explain CATLIN_EXT_2X6 --card`
reads **R-41.4**; the honest number is **≈ R-38.2** (R-40.7 / ≈R-37.5 at the 24" courses this
wall carried until 2026-08-30 — the 32" spacing thins the girt fraction in band B from 14.6 %
to 10.9 % and is worth +R-0.7), and the difference is two modelling
artifacts, both stated in `notes/catlin_truss_engineering.md` §7: the blocks are framed by the
resolver rather than authored as a `CavityFill`, so bands A and C read as unbroken foam; and
the outer girt is credited its own R-1.4 although it stands outboard of a vented gap and is
thermally outside the envelope. Against the Swinburne wall's honest ≈R-36.8 that is about
+2%. **`preferences.toml wall_r = 40` is still not met.** Code minimum is R-21, so there is no
risk in either direction — but do not read the card as saying the target is met.

There is a real thermal gain the 1-D reading cannot credit: the buried inner girt is a fin
connecting a block-1 and a block-2 that are **8" apart along the wall**, not stacked, so heat
has to travel that 8" through 1-1/2" of wood before it can cross the next band. The stagger is
a thermal decision as much as a fastening one.

The case is **buildability and the cladding**:

- **A horizontal nailer for a vertical seam.** The standing-seam clips had nothing horizontal
  to land on before. More to the point, the girts are exactly the substrate a vertical
  **exposed-fastener ribbed panel** wants — which the owner is considering, and which the
  outriggers made impossible.
- **No tab, no chirality, no corner box, no jamb filler.** Three of the four special cases in
  `truss_frame.py` do not arise. Every piece is the same 2x4 turned one of four ways.
- **A simpler fastener story.** One screw per block instead of two, and every screw
  wood-to-wood with continuous lateral support. 3,304 five-inch SDWS against the Swinburne's
  2,570 four-inch ones — the count is up because a girt wall blocks every course at every stud
  station (16" × 32") where an outrigger wall blocked every outrigger every 40", and one screw
  instead of two takes half of that back. (4,154 at the 24" courses this wall carried until
  2026-08-30.)
- **The KDAT question is settled, and settled both ways.** The Swinburne note left it open
  whether the outrigger needed to be treated at all. On the girt wall the answer splits: the
  inner tier is buried in foam and is plain SPF (the saving, taken — about 3,600 LF of it),
  and the outer tier is a horizontal ledge in a wet cavity and is unambiguously KDAT.
