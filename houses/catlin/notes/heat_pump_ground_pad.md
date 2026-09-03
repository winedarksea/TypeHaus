# Heat pumps on a ground pad — siting, pad, stands, line sets

Model: `params/sunken_garden.py` (`HP_PAD`, `_HP_STAND_AT`, `HP_STAND_LEGS`,
`HP_STAND_ANCHORS`), `plan/electrical.py` (the two units and their disconnects),
`plan/assemblies.py` (`HP_PAD_ON_GRADE`, `EQUIP_STAND_ALUM`), `plan/site.py` (the pad's
fall). Supersedes `notes/heat_pump_deck_mounting.md`, which is kept because the rule it
established — decision #64, a fastener through a waterproof deck lands in a sacrificial
member — still governs any future deck. The stair that shares this pad and made the
2026-09-03 turn necessary is `notes/porch_stair.md`.

## Why the balcony was left

Owner decision, 2026-09-02. `EQ-M-HP1-OD` (Gree FLEXX Ultra 24k, 187 lb) and `EQ-M-HP2-OD`
(Gree Multi R32 30k, 145 lb) stood on `FS-SG-DECK` at +10'-0", the watertight aluminium
roof of an occupied porch. Nothing about that was unbuildable; the previous note works the
whole detail through and it holds. It was simply expensive in kinds of cost that do not
appear in a bid:

- **Eight lagged penetrations through a plane that had none**, hosted on sixteen sacrificial
  2x8 blocks laid by four `JoistReinforcement`s, each one taped, each one billed.
- **Two 3/4" condensate runs with self-regulating heater cable**, plus a cable down
  `TR-SG-LEADER-SE` that the model could not even carry, because an untraced defrost line
  over that deck is a line of ice by December.
- **Spring isolators** sized to ~44 lb/corner, because the balcony is a lightweight
  freestanding diaphragm over a porch with no house mass to borrow.
- **A standing "never soffit this balcony" constraint**, because the open joist bays were
  simultaneously the only drying path and the only inspection path those eight holes had.
- **Both units directly over the master bedroom's south windows**, and reachable for
  replacement only through a French door or by crane.

On the ground all six disappear at once, and what replaces them is a pad and eight wedge
anchors. The balcony returns to **zero deck penetrations**, which is what it was designed
as.

## The pocket, and why the row faces south

The yard pocket immediately east of the porch, bounded:

| | |
|---|---|
| west | `W-SG-E1`, the porch's east wall — faces x 27'-6" / 28'-6", top 0'-0", y -11'-0"..-0'-10" |
| north | the house's south wall, cladding face y ≈ -0'-5" |
| south | the `W-RG-EAST-BALCONY` apron return at y = -10'-6", top +0'-6", spanning **x 29'-0"..32'-0" only** |
| east | **open side yard**, out to the EAST (SIDE) setback line at x 58'-0" |

The house is **gable-ended** here, so nothing sheds off the roof onto the units. The
basement wall behind is `W-B-S4`, which has no windows. The only neighbour in the pocket is
`TR-SG-LEADER-SE` at (28'-9", -10'-6"), discharging at +1'-0" into the terrace slot, well
south of the pad. Nothing was authored in `plan/site.py` inside it.

### Why the 99" figure did not bind (2026-09-03)

The 2026-09-02 siting concluded that "a row against the house facing south does not fit —
two cabinets 14 9/16" and 16 13/16" deep, each wanting its discharge clearance in front,
needs 99" of the pocket's 90"". **The 99" was right and the 90" was not.** The 90" assumed
the row had to end at the house's east face, x 36'-0". It does not: east of the SE corner is
open side yard, and `plan/site.py`'s parcel runs x -32..68 with `SetbackSpec(edge=1,
distance=ft(10))`, putting the east side setback line at **x 58'-0"**. Letting one cabinet
stand 7 1/5" past the corner — with 21'-5" still to the setback — is what makes the whole
layout fit.

So both units now stand **side by side in one east-west row across the pocket's south half,
discharging south into open yard**, and the pocket's north strip is free for `ST-SG-PORCH`,
the porch's stair to grade (`notes/porch_stair.md`). That stair is the reason the layout was
revisited at all: the porch had no way down, and a 36" flight plus two cabinets in one
north-south row wants 3'-0" + 12" + 3'-3" + 12" + 3'-4" = **11'-7"** of the 9'-6" of usable
y. Turned, the row is 8'-4" of x and the flight is 3'-0" of y, and neither is fighting the
other for the same feet.

**Stacking the two units was considered first and does not work at this size.** The cabinets
are 37 13/16" (`FXU24`) and 32 33/64" (`MUL30`) tall — three-foot boxes, not the ~21" units
a dual-level stand is built for; the linked Vevor dual-level stand is 35.43" *overall* and
rated 9,000–18,000 Btu, so its upper rail sits below the height of either cabinet. Gree's
outdoor clearance diagram calls for 500 mm (19.7") above a unit to any cover, so a compliant
stack is 18" + 32 1/2" + 19.7", putting HP1's base at 5'-10" and its top at **9'-0"** above
the pad; nested with no gap it is still ~7'-6" and the lower unit has no top clearance at
all. 187 lb at a 4'-4" centre of gravity on a 4" unreinforced pad also turns the anchorage
into a sealed `equipment_anchorage` item, which the ground move had just retired.
**A stacked allowance for these two models could not be sourced** — greecomfort.com and its
mirrors return 403 — so the 19.7" is the general Gree installation figure, not the FXU24's
or the MUL30's own sheet, and that gap is recorded rather than papered over. The line-set
argument for stacking does not survive arithmetic either: raising HP1 34" saves ~2.8 ft of
a 40 ft run and 2.8 ft of a 21 ft rise, against limits of 164 ft and 49 ft.

### The row as built

| | centre | cabinet W x D | extent |
|---|---|---|---|
| `EQ-M-HP2-OD` | (30'-8 1/10", -5'-10 4/5") | 40 5/32 x 16 13/16 | x 29'-0"..32'-4 1/5", y -5'-2 2/5"..-6'-7 1/5" |
| `EQ-M-HP1-OD` | (34'-11 7/10", -5'-7 1/4") | 39 x 14 9/16 | x 33'-4 1/5"..36'-7 1/5", y -5'-0"..-6'-2 1/2" |

`rotation` goes from `deg(90)` to `deg(0)` on both — the long axis runs in **x** now, so the
discharge face reads south. HP2 is the west unit; HP1 stands 7 1/5" past the house's SE
corner. The stand leg patterns in `params/sunken_garden.py::_HP_STAND_AT` transpose with the
cabinets: the **width** pitch is in x and the **depth** pitch in y, the reverse of before.

### Why not the mirror of this — units north, stair south

It reads like the tidier option: equipment by the back door, the porch's south half clear,
and the units 1'-9" from the band penetration instead of 5'-0". Three things rule it out,
and all three are constraints rather than preferences.

- **Nowhere for the disconnects.** The cabinets would occupy the house's south face from
  x 28'-10" to 36'-5" at exactly the height a disconnect wants, leaving only `W-SG-E1`'s east
  face — 34" of exposed concrete whose own 36" working space falls inside the units' back
  clearance.
- **The flight would stand in the discharge plume.** HP1's 40" clear zone would end at
  y -5'-3" and the stair would start at -5'-6": several hundred cfm of air 15–20 °F below
  ambient across a flight in heating, and defrost meltwater onto the treads in a Minnesota
  winter. Stair-north puts the flight on the units' **inlet** side — ambient air, no plume,
  no water.
- **Both casings 4"–6" off the house wall**, directly under `WIN-M-LIV-S1` and
  `WIN-S-STUDY2` (both x 31'-5"..33'-11") — structure-borne coupling plus a discharge stream
  up the cladding to the sill. That is the same objection that ruled out a row at the SE
  corner in the first place.

Secondary, and each true on its own: shovelling the stair would mean working inside the
discharge and piling spoil where the 24"/40" clearances are; the pad would have to cover both
the north and south bands (an L, or ~68 sf against 57); `RL-SG-PORCH` would need splitting
into two `Railing`s around a 12" stub at the SE corner instead of one path point moving; and
`D-M-BALC` is at the porch's **north** edge, so a north stair is ~7' from the door against
~12' across the porch.

The one real cost of stair-north is that the machines sit beside the porch's seating half
rather than by its door.

## Clearances, against the submittals (fetched 2026-09-02)

Each cabinet's published requirement belongs to a *face*, and the faces moved with the
rotation: HP1's discharge went east→south, its back west→north, its service side
south→west, its far end north→east, and HP2's the same quarter-turn.

| | required | provided |
|---|---|---|
| HP1 discharge (S) | 40" | open yard — the 40" zone reaches y -9'-6 1/2" and `W-RG-EAST-BALCONY` stops at x 32'-0", so there is nothing in front of it at all |
| HP1 service side (W) | 12" | 12.0" to HP2's east end |
| HP1 back (N) | 4" | **55.0"** to the house cladding, nothing in between |
| HP1 east end | 4" | ~21'-5" of open side yard to the setback line |
| HP2 discharge (S) | 24" | **46 4/5"** to the `W-RG-EAST-BALCONY` apron, whose top (+0'-6") is below the middle of the cabinet; 46 9/10" to `TR-SG-LEADER-SE` |
| HP2 service side (E) | 12" | 12.0" to HP1's west end |
| HP2 back (N) | 6" | **16 2/5"** to `RL-SG-PSTAIR-S`, the stair's south guard; 57 3/8" to the house cladding past it |
| HP2 west end | — | 6.0" to `W-SG-E1`'s east face |

**Every clearance gained slack except the one between the two units.** HP2's back was at the
published 6" minimum and is now 16 2/5"; HP1's back was 5.9" and is now 55". The 12" service
gap is the only figure still at its minimum, and it is the one the row is laid out from:
**moving either cabinet in x breaks it**, and the stand legs are derived from these centres
and would have to move with it.

## The pad

`SL-SG-HPPAD`, assembly `HP_PAD_ON_GRADE`: 4" unreinforced concrete on 4" of open-graded
stone, x 28'-6"..36'-9" by y -7'-6"..-0'-7 1/5" — **56.9 sf, 0.70 cy** (it was 29.4 sf /
0.36 cy until 2026-09-03) — with an isolation joint where it meets `W-SG-E1`. Top at
**-2'-8"**, two inches proud of the -2'-10" site grade, falling 2 1/2" over the ~6'-11" the
grading check measures to its far (south-east) corner, which lands 1/2" below grade so the
sheet leaves onto gravel instead of ponding at a lip. The `Slab` is modelled flat at its
high edge; the fall is authored as the `ImperviousSurface` "hp pad" in `plan/site.py`, where
`code.R401_3_impervious` reads it (**3.0%** against the 2% required).

**Why it reaches the porch wall, and why it reaches the SE corner.** The west edge is
`W-SG-E1`'s east face because that is where `ST-SG-PORCH`'s stringers land and where its
step-off begins; the north strip up to y -0'-7 1/5" is the flight and that step-off; the east
edge runs 2" past HP1's cabinet, which puts it 9" past the house's SE corner and still 21'
inside the setback. It is **one pour rather than a pad plus a separate stair footing**: at
two thirds of a yard the second form costs more than the concrete it would save. The south
edge came *in* by 18" at the same time — the old row ran to y -9'-0" and nothing stands
there now.

The feet still decide the edges as much as the cabinets do: HP1's published foot pattern is
15 9/16" across the depth against a 14 9/16" cabinet, so its leg lines sit half an inch
outside the cabinet's own faces on that axis — which is now the **y** axis, and the pad
clears them by a foot and a half in both directions.

**No XPS, no vapour retarder, no frost footing**, and all three omissions are deliberate.
Nothing above the pad is conditioned, so there is no heat to break; a retarder under an
exterior pad only traps the water that arrives from the top. And an equipment pad is not a
foundation: it carries 333 lb of cabinet on eight legs, it is free to move with the ground,
and a pad that lifts an inch in February and settles back in April has done nothing a line
set cannot absorb. A frost-depth footing under a mini-split is a foundation for a 333 lb
building.

## Stands and anchors

Two 18" aluminium ground stands, `EQUIP_STAND_ALUM`, modelled as four legs each
(`PT-SG-HPA1..4`, `PT-SG-HPB1..4`, 2" square, `supported_by="SL-SG-HPPAD"`), one 3/8" x 3"
316 stainless wedge anchor per leg (`CN-SG-HPA1..4` / `CN-SG-HPB1..4`, part
`SS316-WEDGE-38x3` in `library/hardware.py`). The cross-rails are in the price row, not in
the geometry — only the legs resolve as solids.

**On a pad the legs ARE the feet.** This is the one thing the move simplifies outright. On
the balcony the leg positions belonged to the deck — bay centres, six inches off every beam
axis — and could not also honour the cabinets' published foot patterns, so each stand needed
a frame spanning two different grids (decision #64 works through why). A flat slab has no
grid. Each leg now stands directly under a published foot hole and the rails carry no
cantilever:

| | part | feet, width x depth | weight |
|---|---|---|---|
| `EQ-M-HP1-OD` | `FXU24HP230V1R32AO` | 29 3/4" x 15 9/16" | 187.4 lb |
| `EQ-M-HP2-OD` | `MUL30HP230V1R32AO` | 25" x 15 19/32" | 145.5 lb |

Both cabinets sit **square to the plan** (`rotation=deg(0)`) since 2026-09-03, so the
**width** pitch runs in x and the **depth** pitch in y — the transpose of what it was while
they faced east. The depth direction still has no adjustment: the cast foot's obround slot
runs the width way, about 1/4" of travel there and none across the depth. Which is a further
reason the 12" service gap is the figure to protect — it is measured along the axis with the
1/4" of slot, and the two stands cannot be shuffled toward each other to buy any of it back.

**Aluminium legs, 316 stainless anchors.** Not a finish choice: the pad is at grade in a
de-iced climate and the base plates sit in the splash and the plough line all winter.
Aluminium with 316 is the pair that does not couple; galvanised steel legs on a salted pad
are the ones that go first. The butyl-under-every-plate story from the balcony detail is
**gone** — there is no waterproof plane here and nothing to seal.

**Vibration isolation is no longer load-bearing.** The balcony needed spring isolators
because it was a low-damping timber diaphragm over occupied space. A 4" slab on stone is
not, and the ordinary neoprene or rubber grommets that ship with a stand are appropriate.
Isolating the **line set** still is — that is the transmission path most often missed, and
HP1's now runs inside a stud bay of an occupied wall.

## Snow, and Gree's 2" rule

Gree's outdoor-unit instruction says to "install 2 in above the expected snow line". The pad
gives the first 2" and the stand gives 18 more, so the **coil bottom sits about 20" above
grade**. The owner's 12" on the balcony was a balcony number, and the note that recorded it
said so: a deck swept by wind keeps its snow depth low in a way ground never does. At grade
the cold-climate guidance (18"–24") applies as written, and 18" is inside it.

Both units carry a **factory base-pan heater** — confirmed in the submittals, which closes
the open question the deck note left ("verify availability with Gree"). Defrost meltwater
drips onto the pad and runs east onto gravel: no drain pan, no piped condensate, no heater
cable, no `pan_drain_ref`. `EQ-M-HP3-OD` has stood at grade on the north side on exactly
those terms since it was authored.

## Sound

60 dBA (HP1) and 58 dBA (HP2) at the manufacturer's rating distance.

**Turning the row south is the quietest of the arrangements considered, for three reasons
rather than one.**

- **The compressors left the walls.** Facing east they backed onto `W-SG-E1` at 5.9" and
  6.0"; they now stand **4'-7" (HP1) and 4'-9 3/8" (HP2) south of the house cladding** with
  nothing behind them at all. Neither casing is close enough to excite the wall it used to
  sit against.
- **The discharge turns into open yard.** Facing east it went into the pocket's own faces,
  which returned it **east and up** — and up meant `WIN-M-LIV-S1` (x 31'-5"..33'-11") and
  `WIN-S-STUDY2` above it. South is open ground: `W-RG-EAST-BALCONY` spans only x 29'-0"..
  32'-0" and tops out at +0'-6", below the middle of either cabinet, so HP1 faces nothing
  and HP2 faces a low wall 46 4/5" away against a 24" requirement.
- **The louder unit moved furthest.** HP1 at 60 dBA is now 5'-2" out from the wall and 5'-0"
  east of the windows above, instead of tucked under them.

**No mitigation is modelled, and none is proposed** — on paper there is nothing left to
mitigate. If it turns out to matter in use, a slatted or absorptive facing on the apron's
**north** face is the move that touches no clearance; a screen anywhere else in the pocket
takes either the 12" service gap or the stair.

**How far east the row sits is a live dial, not a settled number.** It is drawn tucked
against the porch wall — HP2's west end 6" off `W-SG-E1` — because that is shortest for HP2's
three ports, which are the runs with the routing constraint. Sliding the whole row east buys
porch quiet and costs about a foot of line set per foot moved, plus some of the tucked-in
look. The east side yard has 21'-5" of room for it; the 12" service gap and the eight stand
legs move as one piece if it ever does.

## Line sets — routes, lengths, limits

**Not modelled.** `pipe_runs` carries drain, vent, water_cold and water_hot and no
refrigerant system, so there is no `PipeRun` for a line set to be; the `outdoor_ref` pairing
on each head is the record, and the money is in the `hvac-refrigerant-line-sets` allowance
in `prices.toml`, which grew ~50 LF for the move to grade and ~8 LF more for the 2026-09-03
turn, and is not re-priced (at $26–49/LF the added footage is inside its own spread, and the
number was always a lump).

**The turn cost HP2 nothing and HP1 about 8 LF.** HP2 barely moved — +1'-0" east and
+1'-0" north — so its three runs are unchanged. HP1 moved +5'-4" east and +3'-0" south, all
of it outdoors, on the pad, before the band penetration. No layout that also fits the stair
makes the line sets *shorter*: the pre-turn position was already the closest to the band
penetration at x 30'-6".

Gree's published limits, from the same submittals:

| | line | total | per port | rise | precharge |
|---|---|---|---|---|---|
| FXU24 (HP1) | 3/8"–3/4" | 164 ft | — | 49 ft | 31 ft + 0.323 oz/ft |
| MUL30 (HP2) | 1/4"–3/8" per port | 263 ft | 82 ft | 82 ft | 131 ft |

**One penetration through the main-floor band**, at y = 0, x ≈ 30'-6" — sleeved, sloped to
the outside, flashed, with an expansion loop inside. The band there runs -1'-1 7/16"..0'-0",
i.e. 1'-9"..2'-10" above grade, and `FS-M-EAST`'s joists run in x, so the south bay is a
straight east-west run with nothing to notch. **No sleeve element is authored**, and that is
deliberate rather than an omission: `SleevePenetration` is concrete-only in this engine and
there is no framed-wall equivalent, so a fake sleeve would put a cast-in item on the pour-day
schedule that nobody pours. It is recorded here instead.

- **HP2** (three ports, 1/4–3/8): west inside the band bay to x 20'-0" and x 16'-0", then
  7'-6" up the wall cavity behind `EQ-M-HP2-LIVING` and `EQ-M-HP2-BED`; the gym head runs
  north 9'-0" in the basement ceiling to `EQ-B-HP2-GYM`. About 25–30 ft each against an 82 ft
  per-port limit and 263 ft total. Inside the 131 ft precharge — no added charge.
**The stud bay at the SE corner was checked and is available, and is NOT taken.** East of
`WIN-M-LIV-S1`'s jamb pack both `W-M-S2` and `W-S-S2` frame a king at x 33'-5 1/4" and a stud
at x 34'-8", leaving a **13 1/4" clear bay at x 33'-6 3/4"..34'-8"** that lines up floor to
floor (the corner bay beyond it is only 7 3/4" clear and carries the corner strapping, so it
is not the one). It would put HP1's riser 10" from its own cabinet — but it would also want
its **own band penetration**, and one more hole through the band and its flashing is not
worth ~4' out of 124 ft of unused line-set slack. Recorded as verified-and-available in case
a later move makes it the cheaper answer.

- **HP1** (3/8–3/4): east-west along the pad to the single band penetration, then up the
  `W-M-S2` / `W-S-S2` stud bay at x ≈ 29'–30' as before, clear of
  `WIN-M-LIV-S1` (31'-5"..33'-11"), `WIN-S-STUDY1` (27'-4"), `WIN-S-STUDY2` (32'-8") and
  `D-S-DECK-E` (18'-10"..23'-10"); neither wall is braced, so the bay is available. Through
  the main top plates, the second-floor band and the second top plates into `FS-ATTIC`'s
  first bay (y 0"..16", joists in x), then 5'-0" west into `SF-S-HP1`'s east end at
  x 24'-9". About **40 ft of line and 21 ft of rise against 164 ft and 49 ft** — comfortable
  on both, and about +3 oz of R32 over the 31 ft precharge.

## Electrical

`ED-M-HP1-DISC` and `ED-M-HP2-DISC` moved from the second-storey south wall down to
`W-M-S2`'s exterior face on 2026-09-02, centres 1 5/8" off the cladding for the can's true
3 1/4" depth (the `ED-M-HP3-DISC` convention). A disconnect one storey above the machine it
kills is not within sight of it in any sense NEC 440.14 means, so that was not optional once
the units came down. `CKT-HP1` and `CKT-HP2` carry no route, so nothing changed in
`plan/circuits.py`.

**They moved again on 2026-09-03, from x 30'-0" / 35'-0" at 5'-0" to x 34'-3 1/2" /
35'-7" at 3'-6", and both moves are code rather than taste.**

- **NEC 110.26(A) working space cannot be a stairway.** `ST-SG-PORCH` now runs x 28'-6"..
  32'-2", straight under the old x 30'-0" station. East of `WIN-M-LIV-S1`'s rough opening
  (x 31'-5"..33'-11") the 36" working depth falls over the flight's **level step-off**
  instead, which is a floor you can stand on.
- **NEC 404.8(A) caps an operating handle at 6'-7" above the standing surface.** These are
  on a MAIN-floor wall but are operated from grade at -2'-10", and `Mount.elevation` is
  storey-relative, so `ft(5)` put the handles **7'-10"** above the ground you reach them
  from — nearly a foot past the limit, and nothing in the engine was measuring it. 3'-6"
  reads 6'-4" from grade.

Both remain within sight of both units and clear of either unit's own 110.26 working space,
which is the pad in front of it.

## What is not modelled

- **The line sets and their sleeve** — above; the sleeve because no framed-wall sleeve type
  exists, the line sets because no refrigerant `PipeRun` system does.
- **The stands' cross-rails** — in `column:EQUIP_STAND_ALUM`'s price row, not in geometry.
- **The pad's fall** — the `Slab` is flat at its high edge; the fall is the
  `ImperviousSurface`.
- **A stacked allowance for the FXU24 / MUL30.** Every Gree PDF mirror returned 403; the
  19.7" figure above is the general Gree installation diagram, not these two models' own
  sheets. It does not change the answer — the cabinets are too tall for any dual-level stand
  on the market — but it is an unverified number and is flagged as one.
- **Anchorage capacity.** Both units left the deck, so `mep.deck_equipment_support_coverage`
  no longer sees them and the engineering register no longer carries
  `equipment_anchorage/EQ-M-HP1-OD` / `-HP2-OD`. That is honest — the item those records
  named was *anchorage to a deck*, and there is no deck. Wind on a cabinet 20" off the
  ground behind a 2'-10" wall in Exposure B is a different and far smaller problem than wind
  on the same cabinet at +10'-0"; it is still not calculated here. The eight wedge anchors
  are a bolt-down-per-the-instruction detail (IRC M1401.4), not a designed restraint.
