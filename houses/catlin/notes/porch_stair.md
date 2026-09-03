# The porch stair to grade — ST-SG-PORCH

Model: `params/sunken_garden.py` (`PORCH_STAIR`, `PORCH_STAIR_RAILS`,
`PORCH_STAIR_THRESHOLD_RAILS`, `_PORCH_STAIR_*`, `_PORCH_GUARD_PATH`, `HP_PAD`),
`plan/electrical.py` (the two disconnects), `plan/lighting.py` (`ED-M-STAIR-LT`),
`plan/site.py` (the pads' fall), `prices.toml`. Authored 2026-09-03; **moved to the pocket's
south half and given its own pad on 2026-09-04**, when `PT-SG-BR3` turned out to be standing
on the threshold. The heat pumps that had to turn, and then cross the pocket, to make room
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
was nothing to overlap; and the flight starts at the wall's east face, x 28'-6", which is
*exactly* `PT-SG-BR3`'s east face, so the two solids were tangent and
`structural.member_interference` had nothing to say either. **A stair whose head lands on a
wall TOP has to be read against what stands on that top**, and no rule in this engine does
that yet — `plans/TODO.md` carries it.

## The flight

`ST-SG-PORCH`: **5 risers at 6.60", 4 treads at 11" with no nosing, 36" wide, KDAT** — the
`ST-G-SERVICE` pattern in `plan/storeys/garage.py`, which is the same five-riser
0'-0"-to-grade flight and is already priced and tested.

| | |
|---|---|
| run | x 28'-6"..32'-2" (`start` is the FOOT, at the east end; the flight climbs west) |
| width | y -9'-0"..-6'-0" |
| base | `_HP_PAD_TOP`, -2'-8" — the pad top, shared with `SL-SG-HPPAD` |
| top | `_porch_walking_surface`, +0'-1" — the composite plank, not the 0'-0" joist top |
| rise | 2'-9" = 33" over five risers |

Both elevations are **stated on the element**, because neither is a storey datum:
`from_storey` and `to_storey` are both `main`, which is the step-down-within-one-storey case
`floor_opening=None` exists for. 6.60" is inside R311.7.5.1's 7 3/4" and the 11" going leaves
R311.7.5.2's 10" minimum with an inch to spare. No `bearing_refs`: the stringers bear on the
`W-SG-E1` wall top at the head and on `SL-SG-STAIRPAD` at the foot, and a `bearing_refs` tag
that names no wall on `from_storey` is an `integrity.stair_bearing` error rather than a
permission.

**Why y -9'-0"..-6'-0" and not somewhere else in the 6'-9 1/4" of walkable wall top.** The
flight is pushed as far south as the machines want and no further. `-6'-0"` leaves 3'-6"
between HP2's discharge face and the north rail, against a published 24"; `-9'-0"` leaves
9 1/4" to `PT-SG-BF3` for the south rail's baseplates. North of that crowds the condensers,
south of it crowds the column.

### Its own pad

`SL-SG-STAIRPAD`, x 28'-6"..35'-3" by y -9'-0"..-6'-0" — **20.3 sf, 0.25 cy** at 4", on the
same `HP_PAD_ON_GRADE` specification and topped at the same -2'-8" as the equipment pad, so
the flight's authored base is the surface it actually lands on. The west edge is `W-SG-E1`'s
east face where the stringers foot; the flight covers x 28'-6"..32'-2"; and the 3'-1" east of
that is **R311.7.6's bottom landing**, which wants 36" in the direction of travel and gets
37".

It shared one 56.9 sf pour with the condensers for a day. They are 2'-8" apart in y now, and
the smallest rectangle covering both is 94 sf — 54 sf of concrete to save one form, which at
20 sf a pour is the wrong way round.

### The 12" wall top is a threshold, not a tread — and it is NOT MODELLED

`W-SG-E1`'s top is 0'-0", **one inch below the porch plank**. A flight springing from the
wall's west face at x 27'-6" would want its first tread 5.6" *below* the concrete it has to
cross. So the flight starts at the wall's **east** face, x 28'-6", and the 12" of wall top
between the porch plank and the head of the flight is decked flush at +0'-1" with a
**3'-0" x 12" board of the porch's own composite plank** — 3 sf, at y -9'-0"..-6'-0", which
is clear of both columns by 3'-0" and 9 1/4".

That board is trim over 12" of concrete with nothing to frame under it, so no element models
it and no takeoff row would find it. It is priced with the plank instead: `prices.toml`
`[sheet_goods] "composite-deck"`, where the material rides inside the 6 sheets already
bought (192 SF against 184.1 net) and +$20–45 of labour was added for the cut-in and the
anchoring. **An unmodelled detail that is not written down is just a missing detail** — this
is the same call the framed-wall line-set sleeve got.

## Guards and the handrail

`RL-SG-PSTAIR-S` and `RL-SG-PSTAIR-N`, one each side, Williams aluminium (ICC-ES ESR-3485
black, the `RAILING-EXT-ALUMINUM-SURFACE` product `RL-SG-PORCH` uses), 36" with
`role="guard_and_handrail"`, `serves_stair="ST-SG-PORCH"`, `top_height=inch(36)` and a
`graspable_profile` — the `RL-G-SERVICE` authoring in `plan/storeys/garage.py`.

One 36" run with a graspable top rail answers two rules at once. The total rise is 33" > 30",
so `code.R312_1_1_stair_open_side` wants a guard on each open side, and 36" clears
R312.1.2's 34" stair minimum measured off the nosing line; five risers is over R311.7.8's
four, so the flight wants a handrail, and 36" is inside R311.7.8.1's 34"–38". A 36" tread
past two 1 1/2" sections leaves **33" clear** against R311.7.1's 27" for two rails (the check
measures 34.50", which is the same number with the rail lines on the tread edges).

**Both sides are open yard**, since 2026-09-04: the flight sits in the middle of the pocket,
5'-2" south of the house and 1'-6" north of the `W-RG-EAST-BALCONY` apron, so there is no
wall on either side that `code.R312_1_1_stair_open_side` could credit even in principle.
While the flight ran along the house the north rail was authored for a subtler reason —
`W-M-S2`'s band starts at 0'-0" and every nosing but the last runs below it, so the check,
which asks whether a wall's own z band brackets the nosing, would not have credited it there
either — and the pair is unchanged.

### The threshold's two cheeks

`RL-SG-PTHRESH-S` and `RL-SG-PTHRESH-N`, 1'-0" each, **level** at 42" to match `RL-SG-PORCH`,
on the wall top between the porch plank and the head of the flight — at y -9'-0" and -6'-0"
since 2026-09-04, clear of `PT-SG-BF3` by 9 1/4" at the south end. That foot of walking
surface is 33" above the pad on **both** its north and south sides, and nothing in the engine
asks for a guard there:

- `code.R312_1_1_stair_open_side` measures the FLIGHT, whose top tread is only 26.4" over the
  pad — under the 30" trigger. It reports PASS on this stair with or without any guard at all.
- `code.R312_1_guard_height` tests `RL-SG-PORCH` against the deck edge **segment** with a
  plain `LineString` distance (`_railing_runs_edge`,
  `checks/code/mn_residential/fall_protection.py`), and the east edge's midpoint stays
  guarded, so the 3'-0" opening reports PASS either way. Splitting the run in two on
  2026-09-04 did not improve that: the two pieces together still cover the midpoint, and the
  check would report PASS if the gap were 9'. Recorded in `plans/TODO.md`.

The guard return at an opening is on the author, and these are it. They are separate elements
rather than 12" more on the two stair rails because a `serves_stair` `Railing` is **raked
along the nosing line for its whole authored path** — a foot of level wall top on the end of
one resolves at 0" above the (absent) nosings and fails R311.7.8.1 outright. Two elements is
not a workaround: one raked handrail-guard on the flight, one level guard on the wall top, is
the true statement.

### And the porch guard has to split in two

`RL-SG-PORCH` opened for the flight at the **end** of its east leg while the stair was in the
north strip: `_PORCH_GUARD_PATH`'s last point moved from `_y_in_n` (-0'-10") to the flight's
edge, one path edit, no split. Moving the flight to y -9'-0"..-6'-0" put the opening in the
**middle** of that leg instead, and a `path` cannot carry a hole.

So the east leg is two elements now. `RL-SG-PORCH` runs the west leg, the south leg and the
east leg up to the flight's south side at -9'-0"; **`RL-SG-PORCH-NE`** picks up at the north
side, -6'-0", and runs the 5'-2" to the porch's north edge. Same `type_ref`, same mount, same
height, same assembly — it is one run of guard with a doorway in it, and it is two elements
only because the schema says so. The long one keeps its uid: it is the same element,
shortened.

**The total footage does not move**: 42.7 LF over six runs instead of five, because the
doorway is 3'-0" wherever it sits. What the split does cost is a run start/stop and two end
posts of labour, flagged on the `RAILING-EXT-ALUMINUM-SURFACE` price row.

The four `_PORCH_STAIR_*` constants are shared by the flight, its pad, the opening and all
four rails, so none of them can drift apart. `_PORCH_GUARD_SOUTH_STATIONS` reads the *middle*
path segment and is unaffected either way.

## Electrical

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
  electrical layout, and it is why the flight cannot slide north.

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
full-cutoff luminaire as `ED-G-EXT-LT`, on `CKT-LT-MAIN` and switched by
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
the total by nothing), the KDAT flight (32 LF of 2x12 stringer, 32 LF of 11x1.5 tread, shared
with `ST-G-SERVICE` in the BOM's kdat groups), one exterior sconce, 3 sf of unmodelled
composite threshold board, and one more run start and two more end posts of railing labour.
The line sets got **shorter** on 2026-09-04, not longer — both cabinets now stand 1'-9" from
the band penetration instead of 5'-0" of run along a pad — so the ~8 LF the 2026-09-03 turn
added is mostly given back, all of it inside the same lump allowance either way.

**No new engineered item** — the flight is wood on grade and neither pad is a foundation.

## What is not modelled

- **The threshold board** — above, priced with the plank.
- **The raked stair-post premium.** Every post in the `RAILING-EXT-ALUMINUM-SURFACE` rate
  stands on a 12" concrete wall top and arrives welded to a 5x5 baseplate. A post on a 2x12
  KDAT stringer is a different baseplate on a different substrate, through-bolted rather than
  anchored, and it wants a rake-adjustable post-and-rail kit. Flagged on the price row
  against the two raked runs; it is not in the numbers.
- **The raked runs' true length.** The BOM bills a `Railing` by the PLAN length of its path,
  so 3.7 LF of plan is 4.6 LF of rail on a 33"-in-44" rake — the two `PSTAIR` runs read ~1.9
  LF light between them. Noted on the price row.
