# Heat pumps on a ground pad — siting, pad, stands, line sets

Model: `params/sunken_garden.py` (`HP_PAD`, `_HP_STAND_AT`, `HP_STAND_LEGS`,
`HP_STAND_ANCHORS`) for the pocket pair and `params/hp3_pad.py` for system 3's north-side
pad (added 2026-09-04 — see the section on it), `plan/electrical.py` (all three units and
their disconnects),
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

## The pocket, the row, and the flight

The yard pocket immediately east of the porch, bounded:

| | |
|---|---|
| west | `W-SG-E1`, the porch's east wall — faces x 27'-6" / 28'-6", top 0'-0", y -11'-0"..-0'-10" |
| north | the house's south wall, cladding face y -0'-7 1/4" |
| south | the `W-RG-EAST-BALCONY` apron return at y = -10'-6", top +0'-6", spanning **x 29'-0"..32'-0" only** |
| east | **open side yard**, out to the EAST (SIDE) setback line at x 58'-0" |

The house is **gable-ended** here, so nothing sheds off the roof onto the units. The
basement wall behind is `W-B-S4`, which has no windows. The only neighbour in the pocket is
`TR-SG-LEADER-SE` at (28'-9", -10'-6"), discharging at +1'-0" into the terrace slot, well
south of everything here. Nothing was authored in `plan/site.py` inside it.

**The pocket now holds two things and they are laid out around each other**: the condenser
row against the house across the north strip, and `ST-SG-PORCH` — the porch's only way down
to grade — across the south. The stair is the reason the siting was revisited at all, and it
took three passes in three days to land.

### Why the 99" figure did not bind (2026-09-03)

The 2026-09-02 siting concluded that "a row against the house facing south does not fit —
two cabinets 14 9/16" and 16 13/16" deep, each wanting its discharge clearance in front,
needs 99" of the pocket's 90"". **The 99" was right and the 90" was not.** The 90" assumed
the row had to end at the house's east face, x 36'-0". It does not: east of the SE corner is
open side yard, and `plan/site.py`'s parcel runs x -32..68 with `SetbackSpec(edge=1,
distance=ft(10))`, putting the east side setback line at **x 58'-0"**. Letting one cabinet
stand past the corner — with 19'-5" still to the setback — is what makes the layout fit.

Both units therefore stand **side by side in one east-west row, discharging south**. That
part has not changed since.

### Why the row is against the house and not across the south half (2026-09-04)

For one day it was the other way round: the row across the pocket's south half, the flight
in the north strip along the house. **`PT-SG-BR3` is why that could not stay.**

`ST-SG-PORCH` springs from `W-SG-E1`'s top, and that top is a 12" wall carrying two **12"
round** cast columns — `PT-SG-BR3` at y -3'-0"..-2'-0" and `PT-SG-BF3` at
y -10'-9 1/4"..-9'-9 1/4". A 12" round on a 12" wall is flush with both faces, so each one
fills the wall top edge to edge and the top is walkable only **between** them:
y -9'-9 1/4"..-3'-0", six foot nine. A row in the south half sits inside exactly that window,
and the flight in the north strip put its 3'-0" threshold across `PT-SG-BR3` — 10" of
passage on one side of the column, 14" on the other.

**Nothing in the engine reported it, and the reason is worth keeping.** The threshold board
is 3 sf of trim over concrete, deliberately not modelled (see `notes/porch_stair.md`), so
there was no element to overlap. And the flight itself starts at the wall's *east* face,
x 28'-6", which is *exactly* `PT-SG-BR3`'s east face — the two solids are tangent, not
overlapping, so `structural.member_interference` had nothing to say either. A stair whose
head lands on a wall TOP has to be read against what stands on that top. Recorded in
`plans/TODO.md`.

So the row and the flight swapped halves. What that swap costs and buys is below, and the
short version is that it buys the stair and the line sets and it costs the backs.

### The row as built

| | centre | cabinet W x D | extent |
|---|---|---|---|
| `EQ-M-HP2-OD` | (30'-8 3/32", -1'-9 21/32") | 40 5/32 x 16 13/16 | x 29'-0"..32'-4 5/32", y -1'-1 1/4"..-2'-6 1/16" |
| `EQ-M-HP1-OD` | (34'-11 21/32", -1'-8 17/32") | 39 x 14 9/16 | x 33'-4 5/32"..36'-7 1/6", y -1'-1 1/4"..-2'-3 13/16" |

`rotation` is `deg(0)` on both and has been since 2026-09-03 — the long axis runs in **x**,
so the discharge face reads south. HP2 is the west unit, 6" off `W-SG-E1`; HP1 stands
7 1/6" past the house's SE corner. The stand leg patterns in
`params/sunken_garden.py::_HP_STAND_AT` follow the cabinets: the **width** pitch is in x and
the **depth** pitch in y.

### The row is tucked as far west as it goes, and that was an owner call

**It cannot tuck all the way.** 40 5/32" + 12" + 39" is **7'-7 1/6"**, and the porch wall to
the SE corner is **7'-6"**. One cabinet oversails by 7 1/6" in any tucked arrangement; the
only question is which and by how much.

It sat 2'-4" further east for part of 2026-09-04, at x 31'-0", which left a 30" band of the
house's south face free for the two disconnects at NEC 110.26(A) working space. **The owner
took the tuck instead** (2026-09-04): a condenser standing behind the SE corner is shadowed
by the house's own mass down the whole east side yard, where one out past the corner
radiates into it. The price is a louder living room — both cabinets are now under
`WIN-M-LIV-S1` — and the disconnects, which had to leave the house entirely (below).

### What the swap and the tuck cost, stated plainly

Three things were held against a row on this side on 2026-09-02, and each has an answer or
a price now:

- **Nowhere for the disconnects.** True, and paid rather than solved. They are on
  `W-SG-E1`'s east face at 2'-2" above grade instead of the house's at 6'-4". See
  **Electrical** below.
- **The flight in the discharge plume.** Answered, and it is the swap's main prize. HP2's
  discharge face is y -2'-6 1/16" and the flight's north side is -6'-0" — **3'-6" of clear
  yard against a published 24"** — and HP1's 40" zone is east of the flight's x entirely.
  The flight is not downwind of either machine in heating, and defrost meltwater drips at
  the cabinet base onto its own pad 2'-8" away from the treads.
- **Both casings 4"–6" off the house wall, under `WIN-M-LIV-S1`.** True, and taken. Both
  backs are at 6" — HP2's published minimum, HP1's is 4". This is the one objection that is
  neither answered nor priced, only accepted, and it is a **sound** judgement rather than a
  code one. What softens it: the discharge faces *away* from the wall, so there is no stream
  up the cladding to the sill, and the 12" service gap between the two cabinets falls at
  x 32'-4"..33'-4", under the middle of that window. If it turns out to matter in use, the
  move that touches no clearance is an absorptive facing inside the cabinets' back gap.

## Clearances, against the submittals (fetched 2026-09-02)

Each cabinet's published requirement belongs to a *face*, and the faces moved with the
2026-09-03 rotation: HP1's discharge went east→south, its back west→north, its service side
south→west, its far end north→east, and HP2's the same quarter-turn. The 2026-09-04 swap
moved the cabinets but not their facings, so this is the same table with new numbers.

| | required | provided |
|---|---|---|
| HP1 discharge (S) | 40" | open yard — the 40" zone reaches y -5'-7 13/16", and the nearest thing south of it is `SL-SG-STAIRPAD`'s north edge at -6'-0", 2 1/2" further on and 4" lower |
| HP1 service side (W) | 12" | 12.0" to HP2's east end |
| HP1 back (N) | 4" | **6.0"** to the house cladding |
| HP1 east end | 4" | ~21'-5" of open side yard to the setback line |
| HP2 discharge (S) | 24" | **41 15/16"** to `ST-SG-PORCH`'s north rail, with nothing at all in between |
| HP2 service side (E) | 12" | 12.0" to HP1's west end |
| HP2 back (N) | 6" | **6.0"**, the published minimum |
| HP2 west end | — | 6.0" to `W-SG-E1`'s east face |

**Three figures sit at a minimum now, where the 2026-09-03 layout had one.** The 12" service
gap between the units is unchanged and is still what the row is laid out from — moving either
cabinet in x breaks it, and the eight stand legs derive from these centres and would move
with it. The two new ones are **both backs at 6"**, which is what tucking against the house
costs: HP1 has 2" of slack there against its published 4" and HP2 has none. The clearance
that actually governs performance went the other way — HP2's discharge from 16 2/5" to
41 15/16", and HP1's onto open ground.

## The pads — two in the pocket (and a third on the north side, below)

`SL-SG-HPPAD` and `SL-SG-STAIRPAD`, both on assembly `HP_PAD_ON_GRADE`: 4" unreinforced
concrete on 4" of open-graded stone, both topped at **-2'-8"**, two inches proud of the
-2'-10" site grade — Gree's "install 2 in above the expected snow line", and the first two
of the ~20" the 18" stands then add.

| | extent | area | volume |
|---|---|---|---|
| `SL-SG-HPPAD` | x 29'-0"..36'-10", y -3'-4"..-0'-10" | 19.6 sf | 0.24 cy |
| `SL-SG-STAIRPAD` | x 28'-6"..35'-3", y -9'-0"..-6'-0" | 20.3 sf | 0.25 cy |

**39.8 sf and 0.49 cy together**, against 56.9 sf / 0.70 cy for the single pour of
2026-09-03 and 29.4 sf / 0.36 cy for the original equipment-only pad. Each falls 2.5% away
from the house, authored as an `ImperviousSurface` in `plan/site.py` where
`code.R401_3_impervious` reads it against R401.3's 2%; the `Slab`s are modelled flat at their
high edge, because the fall is a finishing fact.

**Two pours rather than one L.** They are 2'-8" apart in y, and the smallest rectangle
covering both is 94 sf — 54 sf of concrete poured to serve nothing, in order to save one
form. At 20 sf apiece the second form is the cheaper half. The 2026-09-03 note argued the
opposite and was right at the time, when the flight and the cabinets shared one band.

**What decides each edge.** `SL-SG-STAIRPAD`'s west edge is `W-SG-E1`'s east face, where the
stringers foot; the flight covers x 28'-6"..32'-2"; and the 3'-1" east of that is R311.7.6's
bottom landing, which wants 36" in the direction of travel and gets 37".
`SL-SG-HPPAD`'s west edge is HP2's own cabinet face and its east edge runs 2 3/4" past
HP1's. Its **north** edge stops 3" short of the house cladding rather than butting it: a pad
that never touches the house has no isolation joint to detail, and the 3" gap drops the
wall's runoff into gravel instead of against a lip. The feet decide that edge as much as the
cabinets do — both published foot patterns are *wider than the casing across the depth*
(15 9/16" of feet under a 14 9/16" cabinet), so the north legs stand half an inch proud of
the north face and the pad clears them by 2 3/4", not 3 1/4".

**No XPS, no vapour retarder, no frost footing**, and all three omissions are deliberate.
Nothing above either pad is conditioned, so there is no heat to break; a retarder under an
exterior pad only traps the water that arrives from the top. And an equipment pad is not a
foundation: it carries 333 lb of cabinet on eight legs, it is free to move with the ground,
and a pad that lifts an inch in February and settles back in April has done nothing a line
set cannot absorb. A frost-depth footing under a mini-split is a foundation for a 333 lb
building. The stair pad is the same call for the same reason — a flight of five risers that
heaves an inch is still a flight of five risers.

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

## System 3, and the pad it did not have (2026-09-04)

`EQ-M-HP3-OD` (Gree Sapphire R32 9k, 78 lb) has stood at grade on the north side since it
was authored, and the paragraph above says so — "on exactly those terms". **It was standing
on nothing.** No pad, no stand, and no `mount.elevation` at all, so a `FLOOR` mount put the
cabinet's base on the `main` datum at 0'-0" — 2'-10" in the air over bare soil. Nothing
reported it: `mep.deck_equipment_support_coverage` sees no deck equipment in this house any
more, and no check asks what a floor-mounted exterior machine bears on. It is now
`params/hp3_pad.py`, and `test_catlin_outdoor_structures.py` holds it to the same pad top
and stand height as the pocket pair, so all three cabinets' bases are one number: -2'-8"
plus 18" is -1'-2".

Three other figures on that element were stale rather than chosen, and giving it a pad is
what surfaced them.

| | was | is | why |
|---|---|---|---|
| `footprint` | 31 x 13 | 34 3/8 x 14 51/64 | the outline the TYPE record shed on 2026-08-31 when the SAP09 submittal replaced a placeholder. The **type's** footprint is what geometry reads (`resolve/placeables.py::_local_footprint` prefers it), so the plan has been drawing the true cabinet while every comment said 31 x 13. Restated, not changed |
| `rotation` | absent = `deg(0)` | `deg(180)` | `deg(0)` is the convention HP1/HP2 use to face **south**: local -y is the discharge. Here it aimed the fan at a house wall 1 15/16" away |
| `position` | (3.44566 m, 11.3941 m) | (11'-5 3/16", 37'-10 41/64") | derived instead of authored: west face on the round foot at x 10'-0", back face 8" off the cladding. A 4 1/16" move north and 1 9/16" east |

### The slot, and what fits in it

| | |
|---|---|
| south | the house's north cladding face, y 36'-7 1/4" (`_WALL_OUTBOARD_IN` off the y=36' sheathing line) |
| north | the garage's south cladding face, y 40'-7 3/4" (`params/breezeway.py::_GARAGE_CLADDING_Y`) |
| west | `D-M-ENTRY`, near jamb x 9'-6", and the R311.3 landing that door owes (x 6'-6"..9'-6") |
| east | open, out to the front walk at x 14'-0" |

**48 1/2" of slot and a 14 51/64" cabinet leaves 33 3/4" to split between the back and the
discharge.** It is split 8" / 25 11/16". Neither figure is a published minimum for this
chassis — **Gree's clearance diagram for the SAP09 could not be sourced**, the same 403 wall
this note hit for the FXU24/MUL30 stacking allowance — so the 8" is HP2's published 6" plus
two, taken because the slot has the room and because the pad's south edge then clears the
legs by 2 5/8" instead of a scant half inch. The discharge gets the rest.

**The discharge faces the garage, and that is a wall too.** A stream crossing 25 11/16" at a
parallel wall recirculates to some degree, and there is no arrangement in a 4' slot that
avoids it; what the turn buys is 25 11/16" instead of 1 15/16", and a slot open at both ends
for the return. Facing the house instead would have put the plume under `WIN-M-MUD` and
beside the entry door. If it matters in use the move is the same one the pocket pair have
named: an absorptive facing on the surface the stream lands on.

### The pad

`SL-M-HP3PAD`, on `HP_PAD_ON_GRADE` like both pocket pads: x 9'-9"..13'-1", y 36'-10
1/4"..38'-11" — **6.9 sf, 0.08 cy at 4"**, topped at -2'-8". Its **south** edge stops 3"
short of the house cladding, the convention `SL-SG-HPPAD` set (no isolation joint to detail,
and the wall's runoff lands in gravel). Its **north** edge is not that convention against
the garage: it stops 20 3/4" short, because the pad is sized to the stand rather than to the
slot, and that 20 3/4" is the way through. It falls 1" from the south-west corner to the
north-east — away from the house, toward the open east end — authored as an
`ImperviousSurface` in `plan/site.py` where `code.R401_3_impervious` reads it. North would
have been the garage stem, which is what the front walk's own note declines to drain into.

No XPS, no vapour retarder, no frost footing, for the pocket pads' reasons exactly. The
energy check had to be told about it: `checks/code/mn_energy.py`'s
`_FREESTANDING_SLAB_PREFIXES` is a naming convention, `SL-M-` is the house's own storey key,
and this pad graded as a conditioned slab edge at R-1.2 against R-10 until it was named
there in full.

### The stand — and the one departure from the pocket pair

Four 2" aluminium legs (`PT-M-HP3-L1..4`), 18", on `EQUIP_STAND_ALUM`, one
`SS316-WEDGE-38x3` anchor each (`CN-M-HP3-A1..4`). Twelve anchors in the house now, not
eight.

**The legs are NOT the feet here, and that is deliberate.** The pocket stands put a leg
directly under each published foot hole, which the note above calls the whole simplification
the move to grade bought. It is available there because Gree publishes a foot pattern for
the FXU24 (29 3/4 x 15 9/16) and the MUL30 (25 x 15 19/32). **No mounting-hole drawing for
the SAP09 chassis could be sourced**, so a leg on an invented pitch would be asserting a
dimension nobody read.

So this stand is specified the way it is actually bought: **two rails running the depth way
at 26" centres, 17 1/2" long, and the cabinet's own feet bolt to the rails wherever its
pitch puts them.** The four legs are the rails' ends. 17 1/2" is chosen against the two
patterns that *are* published — both ~15 9/16" across the depth, an inch **wider** than the
FXU24's own casing — so a rail sized to this cabinet's 14 51/64" could have missed its feet
outboard on both sides. Whatever the SAP09's pitch turns out to be, it lands on the rail.
Every leg's full 2" section is on the pad, by 2 5/8" at the tightest.

### Still open on system 3

**`ED-M-HP3-DISC` has the NEC 404.8(A) defect this note recorded and fixed for the other
two, and it is NOT fixed here.** It hangs on `W-M-N2`'s exterior face at `ft(5)`, and
`Mount.elevation` is storey-relative on a main-floor wall that is reached from grade at
-2'-10" — so the handle is **7'-10" above the ground you operate it from**, against
404.8(A)'s 6'-7". That is the same arithmetic that moved `ED-M-HP1-DISC` and
`ED-M-HP2-DISC` down to 3'-6" on 2026-09-03, and nothing in the engine measures it. It is
left as found rather than fixed in the same pass, because dropping it is a siting decision
about the entry door's wall and not part of giving the machine a pad.


## Sound

60 dBA (HP1) and 58 dBA (HP2) at the manufacturer's rating distance.

**The 2026-09-03 turn is still the biggest single improvement, and the 2026-09-04 tuck gives
part of it back on purpose.** Facing east, both cabinets discharged into the pocket's own
north and west faces, which returned the stream **east and up** — and up meant
`WIN-M-LIV-S1` (x 31'-5"..33'-11") and `WIN-S-STUDY2` above it. Facing south they discharge
into open ground: `W-RG-EAST-BALCONY` spans only x 29'-0"..32'-0" and tops out at +0'-6",
below the middle of either cabinet. That has not changed.

What the tuck changed is the **casings**, and it is a real trade rather than a wash:

- **Both compressors are now 6" off the house wall**, directly under the living room's south
  window, where the 2026-09-03 layout stood them 4'-7" and 4'-9 3/8" out with nothing behind
  them. This is the cost, and it is paid to the living room.
- **Both are behind the SE corner instead of past it.** HP1's east end is 7 1/6" beyond
  x 36'-0" rather than 2'-10", so the house's own mass shadows the east side yard. That is
  what the cost was paid *for* (owner, 2026-09-04), and it is the elevation people stand on.
- **The discharge still faces away from the wall**, so what couples to the cladding is
  casing radiation and compressor structure-borne energy, not a stream up to the sill. The
  stands sit on their own pad with the ordinary neoprene grommets, not on the house.

**No mitigation is modelled, and one is now worth naming.** If it matters in use, the move
that touches no clearance is an absorptive facing on the house wall *inside* the cabinets'
6" back gap — the one surface in this arrangement that is both close enough to matter and
free of any published clearance. A screen anywhere else takes the 12" service gap, the
discharge, or the stair.

## Line sets — routes, lengths, limits

**Not modelled.** `pipe_runs` carries drain, vent, water_cold and water_hot and no
refrigerant system, so there is no `PipeRun` for a line set to be; the `outdoor_ref` pairing
on each head is the record, and the money is in the `hvac-refrigerant-line-sets` allowance
in `prices.toml`, which grew ~50 LF for the move to grade and ~8 LF more for the 2026-09-03
turn, and is not re-priced (at $26–49/LF the added footage is inside its own spread, and the
number was always a lump).

**The 2026-09-04 swap is the only change that made these SHORTER, and it is why the owner
noticed the arrangement was wrong.** The 2026-09-03 turn cost HP1 about 8 LF of outdoor run.
Crossing the pocket gives most of it back and improves the geometry as well as the length:
both cabinets now stand **1'-9" from the band penetration at x 30'-6", on the same wall they
enter**, so each system leaves the casing, crosses a foot and a half of gravel and goes
straight in. The 2026-09-03 layout ran 5'-0" of east-west line along the pad first, and the
2026-09-02 one ran it under what is now the stair. Call it 3-4 ft back per system; the
allowance is a lump and is not re-priced for it either way.

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
worth ~4' out of 128 ft of unused line-set slack. Recorded as verified-and-available in case
a later move makes it the cheaper answer. The 2026-09-04 tuck moved HP1's cabinet **west**,
to x 33'-4 5/32"..36'-7 1/6", so this bay now sits behind the cabinet's own west half rather
than off its end — closer still, and the argument against taking it is unchanged.

- **HP1** (3/8–3/4): 1'-9" north out of the casing to the single band penetration — no
  east-west leg along the pad at all since 2026-09-04 — then up the
  `W-M-S2` / `W-S-S2` stud bay at x ≈ 29'–30' as before, clear of
  `WIN-M-LIV-S1` (31'-5"..33'-11"), `WIN-S-STUDY1` (27'-4"), `WIN-S-STUDY2` (32'-8") and
  `D-S-DECK-E` (18'-10"..23'-10"); neither wall is braced, so the bay is available. Through
  the main top plates, the second-floor band and the second top plates into `FS-ATTIC`'s
  first bay (y 0"..16", joists in x), then 5'-0" west into `SF-S-HP1`'s east end at
  x 24'-9". About **36 ft of line and 21 ft of rise against 164 ft and 49 ft** — comfortable
  on both, and about +2 oz of R32 over the 31 ft precharge.

## Electrical

`ED-M-HP1-DISC` and `ED-M-HP2-DISC` came down from the second-storey south wall on
2026-09-02 with the units they kill — a disconnect one storey above its machine is not within
sight of it in any sense NEC 440.14 means. They then moved twice more, and the last move took
them off the house.

**2026-09-03, on `W-M-S2` still: x 30'-0" / 35'-0" at 5'-0" → x 34'-3 1/2" / 35'-7" at
3'-6".** Two code reasons, neither visible in any check:

- **NEC 110.26(A) working space cannot be a stairway**, and the flight then ran under the
  old x 30'-0" station.
- **NEC 404.8(A) caps an operating handle at 6'-7" above the standing surface.** These are on
  a MAIN-floor wall but are operated from grade at -2'-10", and `Mount.elevation` is
  storey-relative, so `ft(5)` put the handles **7'-10"** above the ground you reach them
  from — nearly a foot past the limit, and nothing in the engine was measuring it. 3'-6"
  reads 6'-4" from grade.

**2026-09-04, off the house: `W-SG-E1`'s east face at (28'-7 5/8", -3'-6") and
(28'-7 5/8", -4'-6"), at -0'-8".** 1 5/8" off the concrete for the can's true 3 1/4" depth
(the `ED-M-HP3-DISC` convention), turned `deg(90)` so the depth runs in x against an east
face.

**The tuck evicted them and 110.26(A)(3) is why there was no appeal.** With the cabinets
against the house from x 29'-0" east, `W-M-S2`'s exterior face is casing from the porch wall
to past the corner; the 6" left at x 28'-6"..29'-0" is not the 30" 110.26(A)(2) wants. And
height does not rescue it — **(A)(3) measures the clear space from the grade up**, so a 3'-4"
cabinet standing 6" off the wall consumes the working space whatever the handle height is.
The row at x 31'-0" left a compliant 30" band and the owner traded it away knowingly.

**The 42" between the cabinets and the flight is the only stretch left, and it fits.**
`W-SG-E1`'s east face is clear from HP2's south face at y -2'-6 1/16" to `ST-SG-PORCH`'s
north side at -6'-0". Two 12" cans at -3'-6" and -4'-6" are 24" of equipment; the 30" space
they share spans y -3'-0"..-5'-6", leaving 6" to the cabinets and 6" to the stair, over 36"
of depth (x 28'-6"..31'-6") with nothing in it. Within sight of both units at 1'-9" — 440.14
asks for sight, and here it is nearly reach as well.

**The mount drops to -0'-8", and access is fine.** This wall tops out at 0'-0", so there is
no 3'-6" to hang from; -0'-8" puts the handles **2'-2" above grade**, well inside 404.8(A)'s
6'-7". Readily accessible standing on the pocket grade beside the units, which is the access
440.14 turns on, and reachable a second way over the porch guard from the deck 8" above them
(owner, 2026-09-04) — a convenience, not the compliance path.

**What the low mount does cost is exposure.** These 3R cans now sit in the splash and the
plough line where the `W-M-S2` position had them at 6'-4" and dry. Specify them
stainless-hinged and gasketed, and take the knockouts on the **bottom** so nothing drains
into the enclosure. That is a durability call the model cannot carry and the drawings must.

`CKT-HP1` and `CKT-HP2` carry no route, so nothing in `plan/circuits.py` changed through any
of this.

## What is not modelled

- **The line sets and their sleeve** — above; the sleeve because no framed-wall sleeve type
  exists, the line sets because no refrigerant `PipeRun` system does.
- **The stands' cross-rails** — in `column:EQUIP_STAND_ALUM`'s price row, not in geometry.
- **Both pads' fall** — each `Slab` is flat at its high edge; the fall is the
  `ImperviousSurface` in `plan/site.py`.
- **The disconnects' exposure detail** — gasketing, hinge material and bottom knockouts, all
  of which the -0'-8" mount makes matter and none of which the model has a field for.
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
