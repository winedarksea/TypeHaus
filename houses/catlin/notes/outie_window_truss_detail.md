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

`CATLIN_EXT_2X6` is a **catlin truss wall**, ONE girt tier. Outboard of the 2x6 studs and their 1/2" plywood sheathing there is 4" of 2 lb closed-cell
spray foam, and the cladding stands off on **one tier of flat horizontal girts on 4-1/2"
blocks** — all 2x4 stock, all laid flat, nothing on edge:

| piece | what it is | where |
|---|---|---|
| block | **KDAT**, three loose 2x4 offcuts, 3-1/2" along the wall × 3-1/2" tall × 1-1/2" thick each, stacked to 4-1/2" | on the sheathing over every OTHER stud, under every girt course, 0 → 4-1/2" |
| girt | **KDAT** 2x4 flat, horizontal, 24" o.c. | on the blocks, 4-1/2" → 6", standing in free air; the cladding nailer and the window mount plane |
| jamb post | KDAT 2x4 flat, vertical | at every RO edge, inner face ON the edge |
| head/sill course | KDAT 2x4 flat | spanning the RO between the two posts |
| cladding | PBR / board & batten panel | screwed to the girts, 6" → 7-1/4" |

Foam total 4", in ONE application, crossed only by the blocks. The block stands **1/2" proud**
of the foam face, and that proud half inch is the **vented gap** behind every course — the
drainage plane. It is CONTINUOUS now that nothing else stands in it, and together with the
20-1/2" of open foam face between courses it is the 2" drained, back-vented cavity the bug
screen at the base of the wall closes. The cavity depth is unchanged from the two-tier wall.

**The inner girt tier is deleted.** Bands B and C used to carry a plain SPF 2x4
flat, buried in the foam, with the outer tier's blocks bearing on it and a second 5" screw
into it. It gave its own screw no thermal break (it sat on the sheathing), cost a 10.9 %
framing fraction in the first 1-1/2" of foam, and held up nothing but the tier above it. The
foam needs no backing — ESR-4073 §4.4.2 permits 7-1/4" on a vertical surface with nothing in
it — and ccSPF's racking contribution is its bond to the sheathing face, which is unchanged.
See `notes/catlin_truss_engineering.md` §1 and §7.

**Everything outboard of the sheathing is KDAT**, and there is no longer an exposure rule to
apply: the girt is a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle for
the life of the wall, and the block plies stand in the same foam-face plane at every crossing.
The encapsulated SPF tier that used to justify a second BOM row no longer exists.

**The blocks are on the STUD module, the girts on their own — and the block module is every
OTHER stud.** A girt course climbs a 24" elevation module measured from the storey's floor
datum (see the phase below); the blocks under it carry it back to the framing, so they land
at whole multiples of **32"** from the wall's LAYOUT LINE, on the same phase the studs take.
32" x 24" is the crossing tributary every load in the engineering note is derived from.

> The phase is solved for the BLOCK module, not the stud module, and that is not pedantry:
> a phase is only line-locked modulo the spacing it was solved for, so a wall standing 16"
> along its line has stud phase 0 mod 16 but block phase 16 mod 32. Reusing the stud phase
> put half of a facade's wall segments on the opposite 32" parity from the rest — every block
> faithfully on a stud, and the facade's grid different storey to storey.

**One 8" SDWS22800DB per crossing**, through the girt (1-1/2"), the three plies (4-1/2") and
the sheathing (1/2"), 1-1/2" into the stud. One fastener pass, no nails, and it is the entire
load path: the block bears the cladding's gravity in direct compression on the sheathing, so
the screw is a pure withdrawal element. It is wood-to-wood with continuous lateral support
over its whole through-length, never bearing on foam. **Mark the stud line across the girt
face as it is laid** — the screw is otherwise blind through 6" of wood into a 1-1/2" target.
See `notes/catlin_truss_engineering.md` §3 and §6.

## What this replaced, and how to go back

This wall replaced a **Swinburne truss wall**: a three-piece chiral pack —
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

**That makes the build order part of the detail, not a preference.** The whole frame goes
together BEFORE any foam exists, on the flat wall, and the sprayer comes once to a finished
frame. The old two-lift order existed because a flat girt lying 1-1/2" off the sheathing
would shadow the pocket behind it; with the girt standing 1/2" clear of the foam face there
is no pocket, and the applicator reaches the whole plane from outside through the 20-1/2"
between courses.

1. Frame the wall, flat on the deck. Sheathe it. Cut the rough openings.
2. **Set the bucks.** 3/8" plywood lining each RO on all four sides, from the sheathing face
   out to the mount plane — **6"**, unchanged — square and plumb. Non-structural: it closes
   the foam at the reveal, gives the reveal a face, and carries the pan and the head flashing.
3. **Mark the 24" course lines off the sole plate** and snap the stud lines across them.
4. **Drop three offcuts at each crossing**, on every other stud line. Loose — no tack. The
   girt screw clamps them; the block is the screw's spacer, not its anchor.
5. **Lay the girt over them, mark the stud line across its face, and drive the 8" SDWS.**
   Head recessed flush: the panel bears on this face.
6. **Jamb posts and head/sill courses at each RO**, on their own blocks, screwed at ≤ 24".
7. **Tilt.**
8. **Foam: one 4" application**, sprayed through the clear between courses and behind them.
   **Fillet against the block sides** (BSI-048) rather than butting square — planed lumber
   shrinks, and a square cold joint at a block is where the crack goes. **Shave to a gauge
   1/2" behind the block's outer face**; the blocks stand proud at every crossing and are the
   gauge, which is what retired the old "1/2" is inside spray tolerance" risk.
9. Sill pan, window, head flashing, cladding.

**Inspect the screw pattern from the ground before the sprayer arrives.** It is a single load
path and this is the last moment it can be seen.

Spraying before the bucks go in leaves a cut edge of foam at every reveal, which is a
discontinuity in the water plane that no sealant closes honestly. Do not do it.

## The window is OUTIE

The unit sits in the **mount plane, 6" outboard of the sheathing** — the outer face of the
girt, which is also what the cladding lands on — with its flanges bearing on the jamb posts
and on the head and sill courses. It is not in the stud plane, and no window in this house
carries a depth dimension: the mount plane is derived from the outermost furring layer's
outer face, so it followed the assembly from 5" to 6" without a single window moving, and
deleting a whole girt tier moved nothing outside this wall either. The 6" came out of the
stack a different way (a 4-1/2" block plus a 1-1/2" girt
instead of four 1-1/2" layers), and the stack is what the mount plane is read from.

**Jamb bearing is no longer a question of luck.** The Swinburne wall depended on where a
vertical outrigger happened to land relative to the RO, and had a three-case table (nothing /
filler / jamb outrigger) to handle the misses. A girt wall has **no field member at a jamb at
all** — the field courses are horizontal — so every opening gets its own frame, always:

| piece | where | material |
|---|---|---|
| jamb post | inner face ON the RO edge, 3-1/2" of wall outboard of it, from 3-1/2" below the sill to 3-1/2" above the head | KDAT |
| head course | post inner face to post inner face, `z_head … z_head + 3-1/2"` | KDAT |
| sill course | post inner face to post inner face, `z_sill − 3-1/2" … z_sill` | KDAT |
| blocks | under every course elevation the post crosses (so at ≤ 24"), and under the head and sill courses at every module station across the RO | KDAT, three plies |

**No doubling anywhere, and that is not a saving — it is a consequence.** The Swinburne head
blocking spanned the full clear width between two outriggers, so a 60" French door's head
needed two plies. The girt head course is blocked back to the framing at every stud station
under it — landing on the cripples above the header, ordinary wall, not the void — so its span
is the block module regardless of how wide the opening is. `prices.toml`'s `2-2x4` row is
retired for the same reason, and so is the jamb filler, since a post set to the RO edge never
leaves a gap to fill. (`3-2x4` is back as a different piece entirely: it is the three-ply
BLOCK now, not a jamb filler.)

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
and it was checked rather than assumed. **Re-derived** when the band moved to **24" o.c.**
with the one-tier truss and its module was re-phased; the sweep's history is in git and in
`plans/TODO.md`.

**The finding is unchanged: no window needs to move.** Measured on the built model, the
largest clear gap between two adjacent nailer courses anywhere beside an opening — above a
head course or below a sill course — is **20-1/2"**, which is exactly the field's own clear
(24" o.c. less the 3-1/2" board). The median beside an opening is **9-3/4"**. The girt field
around every opening in the house is as regular as the field away from it, and at 24" it is
regular at a finer pitch than the 32" band managed. 39 openings, 220 courses.

Any window taller than 24" necessarily interrupts some courses; that is inherent to a
horizontal girt and is not a defect, because the courses it interrupts are replaced by the
opening's own head and sill courses at the same job.

### The course phase, and why it is where it is

Two fields on the band's `FramingSpec` say where the module counts from
(`resolve/framing/furring.course_phase`):

```python
spacing=inch(24), course_datum="framing-base", course_offset=inch(0),
```

`course_datum="framing-base"` is `rw.base_ref_z_m` — **the datum a sill height is measured
from**. It is not the wall base: `platform.py` extends a main-storey wall 13-7/16" down over
the floor rim band, and the courses would otherwise count from the bottom of that lap while
every sill in the same wall counts from the floor.

`course_offset` is **zero**, and that is a swept result rather than a default left in place.
The whole 1/8" sweep from −16" to +8" was re-run against all 39 openings on girt walls,
counting two things: **exact hits** (an opening's own head or sill course landing on a field
course line, where the two are one board and nothing extra is cut) and **conflicts** (a field
course whose bottom is within 7" of one, which is two nailers inside one board face — either
half-lapped or separated by a gap too narrow to be worth a board).

| module | phase | conflicts | exact hits | widest bay |
|---|---|---|---|---|
| 24" from the wall base (to 2026-08-30) | — | 38 | 8 | 24" |
| 32", framing-base (2026-08-30 to 2026-09-01) | −3-1/2" | 19 | 16 | 32" |
| **24", framing-base** | **0** | **30** | **13** | **24.00"** |
| 24", framing-base | −3-1/2" | 24 | 9 | **24.75"** ← fails |
| 24", framing-base | −16" / +8" | 38 | 14 | 24.00" |
| 24", framing-base | −7" to −8-1/2" | 25 | 0 | 24.00" |

**Two things constrain the choice, and the first one is new.** The −3-1/2" phase the 32"
module used is *not available at 24"*: it opens a **24.75"** bay on nine walls, because the
forced top course pops the module course under it (`furring.course_elevations`), and
`structural.girt_course_spacing` FAILs on any bay wider than the authored spacing. Of the
phases that keep every bay at or under 24.00", **zero carries the most exact hits by a clear
margin** — the runners-up trade 5 fewer conflicts for all 13 of them, which is a bad trade: a
conflict is a sliver, an exact hit is a whole board not cut.

**30 conflicts against the 32" band's 19 is not worse layout, it is more course.** A third
more courses fall within 7" of an opening edge no matter what the phase is. Per course the
rate is unchanged.

**Zero is not reachable, and the plan that first asked for it was wrong about that.** The
second storey carries sills at 152" and at 156" — 4" apart, on different walls but on one
module. Any phase that lands exactly on one group is 4" off the other, and 4" is inside the
7" window.

**THE DESIGN RULE FLIPPED WITH THE SIGN.** At −3-1/2" a course TOP landed on the sill datum;
at zero a course BOTTOM lands on the framing-base module. So for a NEW opening: land the
**HEAD on a 24" multiple above the sole plate** (24", 48", 72", 96"), or the **SILL 3-1/2"
above one** (27-1/2", 51-1/2", 75-1/2", 99-1/2"). Either makes that opening's own head or
sill course the field course. `haus build` then shows it, and
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
reads **R-43.5**; the honest number is **≈ R-39.8** wood-only, or **≈ R-37.9** once the girt
screws are counted the same isothermal-planes way the blocks are. The difference between the
card and the honest figure is two modelling artifacts, both stated in
`notes/catlin_truss_engineering.md` §7: the blocks are framed by the resolver rather than
authored as a `CavityFill`, so band A reads as unbroken foam; and the girt is credited its own
R-1.4 although it stands outboard of a vented gap and is thermally outside the envelope.

**Deleting the inner girt tier is worth about +2.5 R** (37.3 -> 39.8 wood-only; 36.1 -> 37.9
with fasteners), and every point of it is the wood that came out of the foam: that tier was a
10.9 % framing fraction through the first 1-1/2" of the insulation, holding up nothing but the
tier above it. **`preferences.toml wall_r = 40` is now effectively met on the wood-only
basis** — 39.85 against 40 — and is 2.1 short with fasteners counted. Code minimum is R-21, so
there was never risk in either direction; do not read the card as saying the target is met.

**The 2-D credit the old wall claimed here is gone with the girt that provided it**, and that
is honest rather than a loss: the buried inner girt was a fin between two blocks 8" apart, so
heat had to travel that 8" through wood before crossing the next band, and a 1-D reading could
not credit it. There is no buried fin now. The new wall's uncredited 2-D effect runs the other
way and is small — a straight column of block plies with the screw up its middle.

**§7.1 of the engineering note is the comparison this wall type exists to win**: against a
4" polyiso + furring wall with the same studs, sheathing and 8" screws, this wall is about
**+3 R** — ccSPF's R/inch over cold-derated polyiso (+4), half the
screw density because the block carries gravity in bearing (+1), less the blocks themselves
(−1.6). The owner's objection — *we pay for wood in the insulation layer and a rigid-foam wall
does not* — is half right, and that is what pays it back.

The case is **buildability and the cladding**:

- **A horizontal nailer for a vertical seam.** The standing-seam clips had nothing horizontal
  to land on before. More to the point, the girts are exactly the substrate a vertical
  **exposed-fastener ribbed panel** wants — which the owner is considering, and which the
  outriggers made impossible.
- **No tab, no chirality, no corner box, no jamb filler.** Three of the four special cases in
  `truss_frame.py` do not arise. Every piece is the same 2x4 turned one of four ways.
- **ONE fastener pass, and one fastener.** 1,128 eight-inch SDWS, against the two-tier wall's
  3,304 five-inch ones and the Swinburne pack's 2,570 four-inch ones. Half of that fall is
  deleting a tier; the other half is putting the block on every OTHER stud (32" x 24") where
  both earlier schemes went to every stud. Every screw is still wood-to-wood with continuous
  lateral support, and every one of them is driven on the flat wall before the foam exists.
  **The cost is that there is no redundancy left** — see the engineering note §3 and §10.
- **The KDAT question is settled, one way.** The Swinburne note left it open whether the
  outrigger needed to be treated at all. On the two-tier girt wall the answer split (SPF
  inner, KDAT outer); with the inner tier gone, everything outboard of the sheathing is a
  ledge in a vented cavity and everything out there is KDAT — the girt, the jamb posts, the
  head/sill courses and all three block plies.
