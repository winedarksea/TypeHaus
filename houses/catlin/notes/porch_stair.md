# The porch stair to grade — ST-SG-PORCH

Model: `params/sunken_garden.py` (`PORCH_STAIR`, `PORCH_STAIR_RAILS`,
`_PORCH_STAIR_*`, `HP_PAD`), `params/porch_guards.py` (the level porch guard),
`plan/electrical.py` (the two disconnects), `plan/porch_lighting.py` (`ED-M-STAIR-LT`),
`plan/site.py` (the pads' fall), `prices.toml`. Authored 2026-09-03; **moved to the pocket's
south half and given its own pad on 2026-09-04**, when `PT-SG-BR3` turned out to be standing
on the threshold; **widened north to 45" and given a separate ADA handrail on 2026-10-30**. The heat pumps that had to turn, and then cross the pocket, to make room
are `notes/heat_pump_ground_pad.md`.

## Why

The porch floor sits at 0'-0" and grade east of it at -2'-10", and until now there was **no
way down**. You reached the porch through `D-M-BALC`, the French pair at x 21'-4", and
`RL-SG-PORCH` railed all three open edges. The owner wanted a stair off the east edge into
the yard pocket — which is where `EQ-M-HP1-OD` and `EQ-M-HP2-OD` had stood since the
2026-09-02 move off the balcony. Turning both condensers to face south, and then moving the
whole row across to the house wall, freed a 3'-0" band of the pocket's **south** half, which
is exactly a straight flight with no landing and no turn.

**It went to the north strip first, and that was wrong for a reason no check could state.**
The flight springs from `W-SG-E1`'s top, and that top carries two 12" ROUND cast columns —
`PT-SG-BR3` at y -3'-0"..-2'-0" and `PT-SG-BF3` at y -10'-9 1/4"..-9'-9 1/4". A 12" round on
a 12" wall is flush with both faces, so each fills the top edge to edge and the wall is
walkable only between them: **y -9'-9 1/4"..-3'-0"**. The north-strip flight put its 3'-0"
threshold straight across `PT-SG-BR3`, leaving 10" of passage one side and 14" the other.

Nothing reported it. The threshold board is trim rather than an element (below), so there
was nothing to overlap; and the flight starts at the wall's east face, x 27'-6", which is
*exactly* `PT-SG-BR3`'s east face, so the two solids were tangent and
`structural.member_interference` had nothing to say either. **A stair whose head lands on a
wall TOP has to be read against what stands on that top**, and no rule in this engine does
that yet — `plans/TODO.md` carries it.

## The flight

`ST-SG-PORCH`: **5 risers at 6.788", 4 treads at 11" with no nosing, 45" wide, Trex Enhance Basics Tide Pool treads on KDAT** — the
`ST-G-SERVICE` pattern in `plan/storeys/garage.py`, which is the same five-riser
0'-0"-to-grade flight and is already priced and tested.

| | |
|---|---|
| run | x 27'-6"..31'-2" (`start` is the FOOT, at the east end; the flight climbs west) |
| width | y -9'-0"..-5'-3" (`_PORCH_STAIR_WIDTH_IN`) |
| base | `_STAIR_PAD_TOP`, -2'-9" — the pad top, shared with `SL-WK-D` |
| top | `_porch_walking_surface`, +0'-0.94" — the composite plank, not the 0'-0" joist top |
| rise | 2'-9.94" = 33.94" over five risers |

Both elevations are **stated on the element**, because neither is a storey datum:
`from_storey` and `to_storey` are both `main`, which is the step-down-within-one-storey case
`floor_opening=None` exists for. 6.788" is inside R311.7.5.1's 7 3/4" and the 11" going leaves
R311.7.5.2's 10" minimum with an inch to spare. No `bearing_refs`: the stringers bear on the
`W-SG-E1` wall top at the head and on `SL-SG-STAIRPAD` at the foot, and a `bearing_refs` tag
that names no wall on `from_storey` is an `integrity.stair_bearing` error rather than a
permission.

**Why y -9'-0"..-5'-3" and not somewhere else in the 6'-9 1/4" of walkable wall top.** The
south side stays pinned at `-9'-0"`, 9 1/4" off `PT-SG-BF3`. The flight was 36" until
2026-10-30, when it widened **north** to 45": the Williams post's 4.99" cast base has to land
wholly on a tread, and R311.7.1 wants 36" between the posts above the handrail — 45" less two
4 1/4" (2 3/4" inset + half the 3" post) is 36 1/2", the 1/2" spare so the 36" is not held at
zero. Widening was cheaper than fascia-mounting the guards. `-5'-3"` keeps ~2'-9" to HP2's
cabinet face against its published 24", and 2'-3" to `PT-SG-BR3`.

### Its own pad

`SL-SG-STAIRPAD`, x 27'-6"..36'-7 7/8" by y -9'-0"..-5'-3" — **34.4 sf, 0.42 cy** at 4", on the
same `HP_PAD_ON_GRADE` specification, topped at -2'-9" to match walk D, 1" below the equipment pad, so
the flight's authored base is the surface it actually lands on. The west edge is `W-SG-E1`'s
east face where the stringers foot; the flight covers x 27'-6"..31'-2"; and everything east
of that is **R311.7.6's bottom landing**, which wants 36" in the direction of travel and gets
5'-6". The east edge is walk leg `SL-WK-D`'s west edge less a 1/2" isolation joint: since
2026-09-23 the pad is the walk's south end, and the 1'-4" connector `SL-WK-E` is gone.

It shared one 56.9 sf pour with the condensers for a day. They were 2'-8" apart in y (1'-11" since the 45" widening), and
the smallest rectangle covering both is 94 sf — 54 sf of concrete to save one form, which at
20 sf a pour is the wrong way round.

### The 12" wall top is a threshold, not a tread — and it is NOT MODELLED

`W-SG-E1`'s top is 0'-0", **0.94" below the porch plank**. A flight springing from the
wall's west face at x 26'-6" would want its first tread 5.848" *below* the concrete it has to
cross. So the flight starts at the wall's **east** face, x 27'-6", and the 12" of wall top
between the porch plank and the head of the flight is decked flush at +0'-0.94" with a
**3'-9" x 12" board of the porch's own composite plank** — 3.75 sf, at y -9'-0"..-5'-3", which
is clear of both columns by 2'-3" and 9 1/4".

That board is trim over 12" of concrete with nothing to frame under it, so no element models
it and no takeoff row would find it. It is priced with the plank instead: `prices.toml`
`[sheet_goods] "composite-deck"`, where the material rides inside the 6 sheets already
bought (192 SF against 184.1 net) and +$20–45 of labour was added for the cut-in and the
anchoring. **An unmodelled detail that is not written down is just a missing detail** — this
is the same call the framed-wall line-set sleeve got.

## Guards and the handrail

`RL-SG-PSTAIR-S` and `RL-SG-PSTAIR-N`, one each side, are **guards** (`role="guard"`): the
Williams Colonial panel on the 42" surface post kit (ICC-ES ESR-3485 black, the
`RAILING-EXT-ALUMINUM-SURFACE` product `RL-SG-PORCH` uses), 36" over the nosings, which clears
R312.1.2's 34" stair minimum; the Williams stair panel (CS252306B) spans 34"-38" there. Their
path runs **2 3/4" inside each flight edge** (`_POST_INSET_FT`) so the 3" post's 4.99" cast
base fits on its landing. Each guard is **one bay**: foot and head bases both on concrete,
as detailed below, and no post stands over the flight.

**The Colonial top rail is not a handrail** — ESR-3485 §5.7 puts it outside the report's
scope, and it is 2.25" wide. Until 2026-10-30 the two guards claimed `guard_and_handrail` on a
"1.5in round" profile they do not have. Five risers is over R311.7.8's four, so the flight
gets one real one: **`RL-SG-PSTAIR-HR`**, the Williams Black ADA Pipe Rail and 90 deg Return
Kit (AD901102B, `RAILING-EXT-ALUMINUM-ADA-HANDRAIL`), on the **south** side — the right hand
going down. It is `mount="post"`: its two 90 deg returns fix to the south guard's end posts (the head one
is `RL-SG-PORCH-SE`'s)
with 3 x #10 TEK screws and a backer (`newel` ends), within the kit's 72 inch support spacing, so there is no mid bracket — ESR-3485 Table 1 lists the midspan bracket on a 2"
post only, and there is no middle post. Its
line is 3 3/8" inboard of the guard line, 1 1/2" clear of the Colonial rail, with its
centreline 34 1/4" over the nosings (pipe top 35"). The ~1.5" OD is read off the part names
and the returns' standoff is unpublished: **measure both on delivery**.

`code.R311_7_1_stair_width` reads 45" of flight and 38 1/8" past the handrail now that no
post stands over the flight. By hand to the guards' 2.25" Colonial top rails (centred
2 3/4" in): 37 1/4" between them (>= 36") and 34 1/4" from the pipe to the north rail
(>= 31 1/2"). `code.R301_5_handrail_support_spacing` grades the two supports (62.0" along
the rake) against the kit's 72".

**Both sides are open yard**, since 2026-09-04: the flight sits in the middle of the pocket,
4'-5" south of the house and 1'-6" north of the `W-RG-EAST-BALCONY` apron, so there is no
wall on either side that `code.R312_1_1_stair_open_side` could credit even in principle.

**Modeled mounting assembly (2026-11-04).** Each side has two post stations, the head one
shared. Foot bases stand on `SL-SG-STAIRPAD`, 3 inches beyond the lowest riser. Head bases
stand directly on W-SG-E1's concrete top, 5 inches back from its east face; notch the
composite threshold board around them. The threshold cheek owns that post, base and four
anchors; the raked guard emits none at its shared end.

**One bay, no middle post (owner, 2026-11-04; read the same day).** Foot to head is 52 3/4"
c/c in plan (x 27'-1" to 31'-5 3/4"), 62.0" along the 31.7 deg rake. The limit is the
maker's, not the report's: ESR-3485 (reissued 10/2025) §2.0 scopes the system to
"balconies, porches, and decks", and Table 1 has no stair row — its 91.313" IRC span is
level, inside face to inside face (fn 1). The
[Williams Picket Panel Planner](https://www.williamsrailing.com/filesimages/Resources/Project%20Planner/williams-project-planner-baluster-railing.pdf)
p.1 gives the 6' stair panel (69.43" actual) **55.68" max c/c at 37 deg**, shipped at 37 deg
and adjustable 30-40 deg. **That figure is horizontal**: 69.43 cos 37 = 55.45 and the 8'
panel's 72.89 = 91.31 cos 37 (0.7983 against cos 37's 0.7986), whereas measured along the
rake it would be shorter than the panel it is cut from. The panel's rail length is fixed,
so at 31.7 deg it reaches 55.68 x cos 31.7 / cos 37 = **~59.3"**; 52 3/4" fits with 6 1/2"
to spare, and the rail between post faces (49 3/4" / cos 31.7 = 58.5") is under both the
panel's 69.43" and ESR's 91.313". The tread-3 post and its KDAT block are deleted.
The planner's "42in H post kits are required for middle and bottom stair posts" for a 36"
rail is the kit these posts already use.

The cast BP04450 base envelope is 4.99 inches square. Base thickness, hole spacing and
fastener head contours are display dimensions, identified in `SurfaceMountSpec`; use
the physical product as the drilling template. Concrete anchors use the existing
ESR-3485 1/4 x 3 inch schedule. Both end bases fit entirely on their supporting concrete;
the modeled head anchor row is more than 3 inches from the wall's east face.

The panels and handrail keep the straight nosing-line rake between the landing-mounted
end posts (`extend_stair_rake`). Posts remain plumb and their bases use actual level
bearings independently of the rail's nosing datum. Stair bottom rails clear the nosing
line by 1 inch; level threshold bottom rails by 3 inches. The short raked portion over
the threshold still has less than 4 inches of opening at the head post's inside face.
The handrail extends beyond both end risers and keeps its two post returns; there is no
second post at either head. The existing 42 inch post kit has **43.5 inches actual length**,
so the pad-mounted foot post fits it: see the
[Williams project planner](https://www.williamsrailing.com/filesimages/Resources/Project%20Planner/williams-project-planner-baluster-railing.pdf).

Production viewer reviews: `cd ui && npm run railing-review`, after building Catlin JSON.
The review includes foot, head and the complete stair guard/handrail.

### The porch guard: the columns are its posts (2026-11-04)

The level porch guard's bases used to hang half off their substrate: west/east-leg posts
centred on W-SG-W1/E1's inner face, south-leg posts on the plank's south edge. The house
rule is that a base sits wholly on one substrate and a concrete anchor row stays >= 3" off a
face. Owner call: the side legs run on the wall tops and **the cast corner columns
PT-SG-BR1/BF1/BR3/BF3 are their posts**; only the south leg stands on the plank; at the house
each side leg ends on its own post, not a wall bracket.

- A `path` cannot carry a hole, so the guard is one `Railing` per span between columns
  (`params/porch_guards.py`): `RL-SG-PORCH-W-HOUSE` and `-W` on W-SG-W1's centreline (anchor
  rows 4 1/8" off both faces); `RL-SG-PORCH` (south leg, wood mounts) 2 5/8" inside the
  plank's edges, its end posts 2 3/4" clear of BF1/BF3; `-SE`, `-NE` and `-E-HOUSE` on the
  stair guards' head-post line, 5" back from W-SG-E1's east face.
- A column end is named by `start_post_ref`/`end_post_ref` and the path stops on the
  column's drawn face. The engine draws no post there, only one rail bracket per rail
  (`{tag}-COLBRK{n}`, `resolve/railings/column_ends.py`), and the infill bay runs to the face.
  A path end off that face draws the post and WARNs `railing_shared_post_missing`.
- **The threshold cheeks `RL-SG-PTHRESH-S/N` are gone.** `-SE` and `-NE` start on the stair
  guards' head posts and draw them at the porch's 42"; `RL-SG-PSTAIR-S/N` name them with
  `end_post_ref`. The threshold's foot of walking surface is guarded by those two pieces.
- The south leg's eight solid blocks (`FS-SG-PORCH.reinforcements`, `_PORCH_GUARD_BLOCK_XS`)
  take each base's inner screw row; the outer row lands on the edge joist / ledger centre.
- Graded by tests, not a check: `test_porch_guard_bases_stand_wholly_on_one_substrate`.

Open with the trade: GRK RSS 5/16" edge distance in a single 1 1/2" member (0.75" as centred;
a third-party sheet asks 0.8-1.0", so double the member if the ESR agrees); and the
rail-to-column bracket and its concrete anchor (Titen Turbo at >= 3" edge distance; the rail
maker's anchor schedule governs).

## Electrical

**History, superseded (checked 2026-10-31):** `ED-M-STAIR-LT` is now wall-hosted on `W-M-S2`
at 7'-0" (`plan/porch_lighting.py`) and `ED-M-HP2-DISC` on `W-SG-E1` at -0'-10"
(`plan/electrical.py`); the stations below predate both moves and W-SG-E1's east face is
x 27'-6", not 28'-6".

**The two disconnects moved twice**, and by the second move they had left the house
altogether. `notes/heat_pump_ground_pad.md` carries the full argument; the stair's share of
it is this:

- **2026-09-03, x 30'-0" / 35'-0" at 5'-0" → x 34'-3 1/2" / 35'-7" at 3'-6".** NEC 110.26(A)
  working space cannot be a stairway, and the north-strip flight ran straight under the old
  x 30'-0" station. (The same move also fixed a NEC 404.8(A) reach-height error that had
  nothing to do with the stair: `Mount.elevation` is storey-relative, so `ft(5)` on a
  main-floor wall put the handles 7'-10" above the grade they are operated from.)
- **2026-09-04, onto `W-SG-E1`'s east face at (28'-7 5/8", -3'-6") and (28'-7 5/8", -4'-6"),
  at -0'-8".** The condenser row tucked west against the house and took the whole south
  elevation with it. The only stretch of wall left is the **42" between the cabinets and this
  flight**, y -2'-6 1/16"..-6'-0"; two 12" cans there share a 30" working space spanning
  -3'-0"..-5'-6", which leaves **6" to the stair**. That 6" is the stair's constraint on the
  electrical layout, and it is why the flight cannot slide north. **2026-10-30:** HP1's can
  has since left for the north face, so only `ED-M-HP2-DISC` (y -4'-6") is here; the 45"
  flight's north side at -5'-3" leaves its 30" space y -5'-3"..-2'-9", flush with the stair
  and 3" off HP2's cabinet. No further widening north.

**`ED-M-STAIR-LT` moved with the flight, and changed character doing it.**
`code.R303_8_exterior_stairway_illumination` wants a luminaire within 4'-0" of the flight's
plan outline on its `to_storey`, and nothing already authored reaches — `ED-M-PORCH-FAN` and
`ED-M-PORCH-FLOOD` are both at x 18'-0", ten feet west. It hung on `W-M-S2` at
(30'-0", -0'-9 3/4") at 7'-0" while the flight ran along the house; with the flight in the
south half, the nearest point of that wall is **5'-2" away** and R303.8 would report a stair
with no light.

It is now on **`W-SG-E1`'s east face at (28'-8 1/2", -9'-3"), at -0'-8"** — the top landing
itself rather than a wall six feet from it. Three things follow from that wall:

- **x 28'-8 1/2"** puts the 5" body's back on the x 28'-6" face. A device footprint is
  CENTRED on its position, so the position owes the face half the depth — and *not* the
  1 5/8" the two disconnects use, which would bury this one an inch in the concrete.
  `rotation=deg(90)` turns the depth onto x so it stands off an east face.
- **-0'-8" makes it a step light, and that is the point.** This wall tops out at 0'-0", so
  there is no 7'-0" to mount at; 8" below the top puts it 2'-2" over the pad, washing the
  treads from beside them instead of throwing the user's own shadow down the flight. It
  clears the 18"–24" snow band the stands are sized against.
- **South of the flight, not north.** North is the two disconnects and their 110.26(A)
  working space, and a 5" body projecting into that is the same objection from the other
  side. Three inches south of the treads it stands clear of the walking surface, and 6" north
  of `PT-SG-BF3`.

The fitting and the circuit are unchanged: `ED-T-LT-SCONCE-EXT`, the same wet-rated
full-cutoff luminaire as the garage door pair `ED-G-EXT-LT-E`/`-W`, on `CKT-LT-MAIN` and switched by
`ED-M-PORCH-FLOOD-SW` — NEC 210.70(A)(2)(b) wants the exterior light switched from inside,
that switch already is, and the flood and the stair light are wanted on the same errand. It
reuses that type rather than minting a full-cutoff downlight of its own **because an unpriced
`LuminaireType` is silently dropped from the takeoff**, so a new type would have bought a
fixture the bill never showed. What did change is the feed: a drop down the porch framing
onto a concrete wall rather than a box in a stud bay, so the labour is taken at the high end
of the row.

## What this cost

+0.13 cy of concrete — and that is a *net* figure worth reading twice. The equipment pad was
0.36 cy alone; adding the flight took it to 0.70 in one pour on 2026-09-03; splitting the two
on 2026-09-04 brought the pair to **0.49**. So the stair costs 0.13 cy over the original pad,
not the 0.34 the single-pour arrangement implied, and the second form is what buys the
difference back.

Also +6.4 LF of `RAILING-EXT-ALUMINUM-SURFACE` net (−3.0 for the doorway, +7.4 over four new
runs; the 2026-09-04 split of `RL-SG-PORCH` moved 5.2 LF onto `RL-SG-PORCH-NE` and changed
the total by nothing), the composite-on-KDAT flight (six 2x12 stringers at no more than 9" o.c.
since the 45" widening,
four 0.94" composite tread assemblies, closed 3/4" KDAT risers and butyl stringer tape,
matching `ST-G-SERVICE`), one exterior sconce, 3 sf of unmodelled
composite threshold board, and one more run start and two more end posts of railing labour.
The line sets got **shorter** on 2026-09-04, not longer — both cabinets now stand 1'-9" from
the band penetration instead of 5'-0" of run along a pad — so the ~8 LF the 2026-09-03 turn
added is mostly given back, all of it inside the same lump allowance either way.

**No new engineered item** — the flight is wood on grade and neither pad is a foundation.

## What is not modelled

- **The threshold board** — above, priced with the plank.
- **The stair-panel premium.** Every post in the `RAILING-EXT-ALUMINUM-SURFACE` rate stands
  on concrete on the post kit's cast 4.99" base; the two raked runs take the stair panel
  CS252306B at a premium over the level parts. Flagged on the price row; it is not in the
  numbers.
- **The raked runs' true length.** The BOM bills a `Railing` by the PLAN length of its path,
  so 3.7 LF of plan is 4.6 LF of rail on a 33.94"-in-44" rake — the two `PSTAIR` runs read ~1.9
  LF light between them. Noted on the price row.
