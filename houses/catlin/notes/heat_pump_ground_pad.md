# Heat pumps on a ground pad — siting, pad, stands, line sets

Model: `params/sunken_garden.py` (`HP_PAD`, `_HP_STAND_AT`, `HP_STAND_LEGS`,
`HP_STAND_ANCHORS`) for **system 2 alone in the pocket**, `params/hp3_pad.py` for system 3's
slot pad and `params/hp1_north_pad.py` for **system 1's north-face pad** — both added
2026-09-04, and each has its own section below. `plan/electrical.py` (all three units and
their disconnects),
`plan/assemblies.py` (`HP_PAD_ON_GRADE`, `EQUIP_STAND_ALUM`), `plan/site.py` (the pad's
fall). Supersedes `notes/superseded/heat_pump_deck_mounting.md`, which is kept because the rule it
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
| south | the `W-RG-EAST-BALCONY` apron return at y = -10'-6", top 0'-0", axis spanning **x 28'-6"..32'-0"** (12" block, so the band is x 28'-6"..32'-6", y -11'-0"..-10'-0") |
| east | **open side yard**, out to the EAST (SIDE) setback line at x 58'-0" |

The house is **gable-ended** here, so nothing sheds off the roof onto the units. The
basement wall behind is `W-B-S4`, which has no windows. The only neighbour in the pocket is
`TR-SG-LEADER-SE` at (29'-0", -10'-6"), discharging at +0'-6" over the apron return's cap
and turned south on a 1'-0" shoe onto the terrace stone, well south of everything here. Nothing was authored in `plan/site.py` inside it.

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

### The pocket as built — ONE cabinet, since 2026-09-04

| | centre | cabinet W x D | extent |
|---|---|---|---|
| `EQ-M-HP2-OD` | (30'-8 3/32", -1'-9 21/32") | 40 5/32 x 16 13/16 | x 29'-0"..32'-4 5/32", y -1'-1 1/4"..-2'-6 1/16" |

`rotation` is `deg(0)` and has been since 2026-09-03 — the long axis runs in **x**, so the
discharge face reads south. It is 6" off `W-SG-E1` at its west end and its east end stops
**3'-7 27/32" short of the house's SE corner at x 36'-0"**. The stand leg pattern in
`params/sunken_garden.py::_HP_STAND_AT` follows the cabinet: the **width** pitch is in x and
the **depth** pitch in y.

### THE ROW, THE TUCK AND THE OVERSAIL ARE ALL GONE (later on 2026-09-04)

For most of a day this was a two-cabinet row, and the argument recorded here was about which
end of it oversailed the pocket's SE corner. `EQ-M-HP1-OD` then crossed to the NORTH face
with its air handler (see **System 1 crosses to the north face**, below), and every one of
those constraints dissolved at once:

- **The 7 1/6" oversail is gone.** It was arithmetic — 40 5/32" + 12" + 39" = 7'-7 1/6" of
  cabinet against 7'-6" of wall to the corner — so one unit had to stand past x 36'-0" in
  any tucked arrangement. One cabinet is 3'-4 5/32", and it sits well inside.
- **The 12" service gap is gone**, and with it the tightest clearance in the pocket. There
  is no second cabinet to keep 12" from.
- **The pad shrank 19.6 sf to 8.96 sf.** Its east edge is still 2 3/4" past HP2's cabinet,
  by the same rule that set the old one.
- **What the owner bought on 2026-09-04 — a condenser shadowed behind the SE corner rather
  than out past it — is kept, and cost less.** The living room now takes one machine under
  `WIN-M-LIV-S1` instead of two.
- **The disconnects did NOT come back.** `ED-M-HP2-DISC` stays on `W-SG-E1`'s east face; the
  110.26(A)(3) argument that evicted the pair still holds against the one that is left.

### What the swap cost, stated plainly

Three things were held against a row on this side on 2026-09-02, and each has an answer or
a price now:

- **Nowhere for the disconnects.** True, and paid rather than solved. `ED-M-HP2-DISC` is on
  `W-SG-E1`'s east face at 2'-2" above grade instead of the house's at 6'-4". See
  **Electrical** below.
- **The flight in the discharge plume.** Answered, and it is the swap's main prize. HP2's
  discharge face is y -2'-6 1/16" and the flight's north side is -6'-0" — **3'-6" of clear
  yard against a published 24"**. The flight is not downwind of the machine in heating, and
  defrost meltwater drips at the cabinet base onto its own pad 2'-8" away from the treads.
- **The casing 6" off the house wall, under `WIN-M-LIV-S1`.** True, and taken. 6" is HP2's
  published minimum. This is the one objection that is neither answered nor priced, only
  accepted, and it is a **sound** judgement rather than a code one. What softens it: the
  discharge faces *away* from the wall, so there is no stream up the cladding to the sill.
  It is also half the problem it was — there were TWO cabinets under that window until HP1
  crossed to the north face. If it turns out to matter in use, the move that touches no
  clearance is an absorptive facing inside the cabinet's back gap.

## Clearances, against the submittals (fetched 2026-09-02)

Each cabinet's published requirement belongs to a *face*, and the faces moved with the
2026-09-03 rotation: HP2's discharge went east→south, its back west→north, its service side
south→west, its far end north→east. **The table splits into three now**, one per unit, since
the three cabinets stand on three separate pads on three different sides of the house.

**HP2, in the pocket** (`rotation=deg(0)`, discharge south):

| | required | provided |
|---|---|---|
| discharge (S) | 24" | **41 15/16"** to `ST-SG-PORCH`'s north rail, with nothing at all in between |
| back (N) | 6" | **6.0"**, the published minimum, and the only figure left in the pocket at one |
| west end | — | 6.0" to `W-SG-E1`'s east face |
| east end | — | 3'-7 27/32" of open pocket to the house's SE corner, then open side yard |

**HP1, on the north face** (`rotation=deg(180)`, discharge north — see its own section):

| | required | provided |
|---|---|---|
| discharge (N) | 40" | open front yard. Legal ONLY because the cabinet stands east of the garage's plan extent — see below |
| back (S) | 4" | **6.0"** to the house cladding |
| service side (E) | 12" | **23 3/4"** |
| west end | 4" | **14"** to the garage rake |

**HP3, in the slot**: unchanged, in its own section below.

**The pocket went from three figures at a minimum to one**, and that is the clearest
statement of what the 2026-09-04 move bought. The 12" service gap that used to be the row's
governing dimension no longer exists — there is no second cabinet — and HP1's four
clearances are all generous where three of them used to be scant.

## The pads — FOUR pours on one specification

`SL-SG-HPPAD` and `SL-SG-STAIRPAD`, both on assembly `HP_PAD_ON_GRADE`: 4" unreinforced
concrete on 4" of open-graded stone, both topped at **-2'-8"**, two inches proud of the
-2'-10" site grade — Gree's "install 2 in above the expected snow line", and the first two
of the ~20" the 18" stands then add.

| | extent | area | volume |
|---|---|---|---|
| `SL-SG-HPPAD` | x 29'-0"..32'-7", y -3'-4"..-0'-10" | 8.96 sf | 0.11 cy |
| `SL-SG-STAIRPAD` | x 28'-6"..35'-3", y -9'-0"..-6'-0" | 20.3 sf | 0.25 cy |
| `SL-M-HP3PAD` | x 9'-9"..13'-1", y 36'-10 1/4"..38'-11" | 6.9 sf | 0.08 cy |
| `SL-M-HP1PAD` | x 26'-3 1/4"..29'-11 3/4", y 36'-10"..39'-4" | 9.27 sf | 0.11 cy |

**45.4 sf and 0.56 cy over the four**, against 46.7 sf / 0.58 cy over three earlier the same
day: HP1's crossing traded 10.6 sf of pocket pad for 9.27 sf of north-face pad and a fourth
form. `prices.toml`'s labour band was re-solved for that form, because a $/cy rate that only
follows the volume prices a whole extra pour at nothing. Each falls 2.5% away
from the house, authored as an `ImperviousSurface` in `plan/site.py` where
`code.R401_3_impervious` reads it against R401.3's 2%; the `Slab`s are modelled flat at their
high edge, because the fall is a finishing fact.

**Two pours rather than one L, in the pocket.** They are 2'-8" apart in y, and the smallest rectangle
covering both is 94 sf — 54 sf of concrete poured to serve nothing, in order to save one
form. At 20 sf apiece the second form is the cheaper half. The 2026-09-03 note argued the
opposite and was right at the time, when the flight and the cabinets shared one band.

**What decides each edge.** `SL-SG-STAIRPAD`'s west edge is `W-SG-E1`'s east face, where the
stringers foot; the flight covers x 28'-6"..32'-2"; and the 3'-1" east of that is R311.7.6's
bottom landing, which wants 36" in the direction of travel and gets 37".
`SL-SG-HPPAD`'s west edge is HP2's own cabinet face and its east edge runs 2 3/4" past that
same cabinet — the rule is unchanged, the cabinet it measures from is not. Its **north**
edge stops 3" short of the house cladding rather than butting it: a pad
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
set cannot absorb. A frost-depth footing under a mini-split is a foundation for a 145 lb
building. The stair pad is the same call for the same reason — a flight of five risers that
heaves an inch is still a flight of five risers.

## Stands and anchors

**THREE 18" aluminium ground stands on three separate pads**, all on `EQUIP_STAND_ALUM`,
each modelled as four legs, one 3/8" x 3" 316 stainless wedge anchor per leg (part
`SS316-WEDGE-38x3` in `library/hardware.py`) — **twelve anchors in the house**:

| unit | pad | legs | anchors | form |
|---|---|---|---|---|
| `EQ-M-HP2-OD` | `SL-SG-HPPAD` | `PT-SG-HPB1..4` | `CN-SG-HPB1..4` | leg under each published foot hole |
| `EQ-M-HP1-OD` | `SL-M-HP1PAD` | `PT-M-HP1-L1..4` | `CN-M-HP1-A1..4` | leg under each published foot hole |
| `EQ-M-HP3-OD` | `SL-M-HP3PAD` | `PT-M-HP3-L1..4` | `CN-M-HP3-A1..4` | two rails; no foot pattern published |

`PT-SG-HPA1..4` and `CN-SG-HPA1..4` are gone — they were HP1's, and they moved to
`params/hp1_north_pad.py` with the unit. The cross-rails are in the price row, not in the
geometry — only the legs resolve as solids.

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

Both cabinets have their long axis in **x** — HP2 at `rotation=deg(0)` facing south since
2026-09-03, HP1 at `deg(180)` facing north since 2026-09-04 — so the **width** pitch runs in
x and the **depth** pitch in y for both, and a 180-degree turn maps a symmetric foot pattern
onto itself. The depth direction still has no adjustment: the cast foot's obround slot runs
the width way, about 1/4" of travel there and none across the depth. That mattered most when
the two shared a pad and a 12" service gap; on separate pads there is nothing to shuffle
toward.

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

## System 1 crosses to the north face (2026-09-04)

**The move is not about the condenser. It is about where the air handler sits.**
`EQ-S-HP1-AH` came out of `SF-S-HP1` in `RM-S-STUDY2`'s ceiling, where it dropped 42.8 sf of
a 159 sf study to 7'-3", and went into a box over `RM-S-NCLOSET` and the north hall at the
opposite end of the second storey. With the machine there, the short line set is up the
NORTH wall — and a condenser 27 ft from its own indoor unit, on the far side of the house,
is a route nobody would draw deliberately. So the cabinet followed.

`params/hp1_north_pad.py` carries `SL-M-HP1PAD`, `PT-M-HP1-L1..4` and `CN-M-HP1-A1..4`. The
cabinet centre is (28'-1 1/2", 37'-8 17/32") — the same literal written in
`plan/electrical.py`, held together by `test_catlin_outdoor_structures.py`, exactly as the
other two pads are.

**`rotation=deg(180)`: the discharge faces NORTH, away from the wall.** `mount.elevation`
is unchanged at -14", because the new pad tops out at the same -2'-8" under the same 18"
stand — all three cabinets keep one base plane at -1'-2".

### The 40" discharge is legal only because the cabinet stands east of the garage

This is the load-bearing siting fact and it is easy to lose. The garage occupies
**x 0'..24'** with its roof to +25'-4"; the slot between it and the house is 48 1/2" wide,
which is where `SL-M-HP3PAD` sits and where a 9k unit's 25 11/16" of throw just fits. **A 24k
unit's 40" discharge could never have come out of that slot.** This cabinet is at
x 26'-6"..29'-9" — past the garage's plan extent — throwing north into open front yard with
nothing in front of it. Move it 3 feet west and the siting fails.

**Snow shed: nothing sheds onto it.** It stands off the north gable END of `RF-HOUSE`, whose
eaves are east and west, and it is clear of the garage in plan. That was true of the pocket
row too, so this is breakeven rather than a gain — but it is the first thing to re-check if
the cabinet ever moves west.

### A condenser under the kitchen sink window, and it is unavoidable

`WIN-M-KITCH` is centred **x 29'-4"**, RO 28'-2 1/2"..30'-5 1/2". The cabinet is 39" wide and
spans x 26'-6"..29'-9", so it laps the opening's west half. **There is no window-free band
39" wide anywhere on this wall** — the widest is 34 1/2" west of the RO — so any north-face
siting laps a window. This one is chosen with open eyes:

- The discharge faces **away** from the wall, so there is no stream up the cladding to the
  sill.
- The sill clears the cabinet top by **18 3/16"**.
- What is lost is a view out of the kitchen sink window's lower half, and the sound of a
  compressor 6" off the wall beneath it. The mitigation, if it matters in use, is the
  pocket's: an absorptive facing inside the 6" back gap.

The window is also the north face's three-storey column
(`WIN-M-KITCH` / `WIN-S-HALL-N`), and it moved to x 29'-4" to sit over the kitchen sink
base — that is a facade decision with its own reasons, and the condenser does not get to
re-open it.

### The pad, the stand and the 6"

`SL-M-HP1PAD`: x 26'-3 1/4"..29'-11 3/4", y 36'-10"..39'-4" — **9.27 sf, 0.11 cy at 4"**,
topped at -2'-8", falling 3/4" straight NORTH over 30" (2.5% against R401.3's 2%). Straight
north and not on the diagonal `SL-M-HP3PAD` takes, because that pad's north neighbour is the
garage stem and this one's is open ground.

**The back clearance is 6", against Gree's published 4", and the two extra inches are what
make the pad buildable.** At 4" the pad's south edge lands 3/4" off the cladding instead of
the 3" convention `SL-SG-HPPAD` set, and forcing the 3" back hangs a 2" leg half an inch off
the slab and fails `pad.contains(ring)`. At 6" the pocket's arithmetic reproduces exactly —
2 3/4" from pad edge to cladding, legs standing half an inch proud of the cabinet's own
south face on the published 15 9/16" depth pitch.

The stand takes the POCKET's form and not `hp3_pad`'s: a leg directly under each of the four
published foot holes (29 3/4" x 15 9/16"), no rail spanning two grids. 18" of leg, for the
pocket's reasons, plus one this face adds: **north is the shaded side all winter.**

### The return, and the wall grille that could not be framed

The move put `SF-S-HP1` over `RM-S-NCLOSET`, and that raised a question about System 1's
return which is worth recording because the answer is *forced* and the wrong answers all look
reasonable. **The air handler's return face is its NORTH face** — supply has to face south to
feed the trunk — so the plenum has to sit north of the cabinet. But the soffit's north end is
over a **closet**, and IMC 601.5(7) forbids taking return air from one; and the soffit's south
end is the **supply** side, carrying the discharge, the strip heater and the trunk in the
west/centre lane. So the room-air inlet must be in the **hall ceiling, in the east lane**,
with a duct carrying it north past the cabinet. There is no other arrangement.

**A grille in `W-S-C4B` facing the stair well was the obvious alternative and it cannot be
built.** That wall is the only one on the well's east side at this storey, and it is the
**x=18' bearing line** — `RB-HOUSE`'s load path down to the footings. Its studs resolve at
y 369 / 384 / 400 / 416 / 424 5/8 with a double top plate at 225"..228", so:

- the only stud bay overlapping the plenum band (y 400 3/4"..415 1/4") is blocked by the
  cabinet below y=408, leaving **7 1/4" of clear bay** — a 115 in² boot at 800 fpm;
- cutting a stud to widen it puts the double 2x6 top plate over a ~31" span carrying
  ~1,600 plf of attic floor and roof: **f ≈ 1,940 psi against Fb ≈ 1,310**. It needs a real
  header, and a header eats the hole's height out of the 15 7/8" between the plate and the
  cavity floor.

Moving the air handler does not rescue it: the wall is the constraint, not the cabinet.

**What was built instead.** `EQ-S-ERV-MIX` grew from a 10 x 12 x 8 mixing box into a
**12 x 29 1/2 x 18 return plenum** filling the east lane south of the cabinet, and
`REG-S-HP-RET` shrank from 30 x 16 to 28 x 12 so its whole **336 in²** face sits inside it.
The defect that fixed was real and silent: the old grille lapped the duct (240 in²), the box
(120 in²) and **120 in² of bare soffit cavity** at once, which is IMC 601.5's
building-cavity-as-plenum. `mep.register_duct_match` grades the pair in plan only and a boot
is unmodelled by convention here, so nothing reported it.

Its `design_cfm` is **650, not 750**, and that is a correction rather than a resizing: the
machine moves 750 and the ERV puts 100 of it into the same plenum through its own drop, so
the room air this grille draws is 650. 336 in² at 650 cfm is **279 fpm**, inside Manual D
SS4-10's 300 for a grille carrying the filter.

### One more thing the move fixed, incidentally

`ED-M-HP1-DISC` had been on `W-SG-E1`'s east face at -0'-8", in the splash and the plough
line. It went with its unit to `W-M-N1` at (32'-0", 36'-8 7/8"), **3'-6" above the main
datum = 6'-4" above the grade it is operated from**, dry and at standing height. x 32'-0"
is the only clear band on that wall — 30'-7 1/2"..33'-3", between the two kitchen windows'
framing bumpers. And putting a second can on this wall is what surfaced
`ED-M-HP3-DISC`'s 404.8(A) defect; see below.

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
| north | the garage's south cladding face, y 40'-7 3/4" (`params/north_entry_frame.py::GARAGE_CLADDING_Y_FT`) |
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

### `ED-M-HP3-DISC` — the 404.8(A) defect, FIXED

This section read "Still open on system 3" for a few hours. `ED-M-HP3-DISC` hung on
`W-M-N2`'s exterior face at `ft(5)`, and `Mount.elevation` is storey-relative on a
main-floor wall reached from grade at -2'-10" — so the handle was **7'-10" above the ground
you operate it from**, against 404.8(A)'s 6'-7". The same arithmetic that moved
`ED-M-HP1-DISC` and `ED-M-HP2-DISC` down to 3'-6" on 2026-09-03, and nothing in the engine
measures it.

**It is `ft(3, 6)` now — 6'-4" above grade** — and what surfaced it was HP1's own disconnect
arriving on the same north face later on 2026-09-04, two cans on one wall at two different
heights. Verified clear of `D-M-ENTRY`'s near jamb by 2'-2 3/4", so the lower handle fouls
nothing.

**The guard is `test_every_condenser_disconnect_is_reachable_under_NEC_404_8_A`**, which
grades all three against grade AND asserts the census — so a fourth system joining the house
with a comfortable-looking `ft(5)` cannot pass silently the way this one did.


## Sound

60 dBA (HP1) and 58 dBA (HP2) at the manufacturer's rating distance.

**The 2026-09-03 turn is still the biggest single improvement, and the 2026-09-04 tuck gives
part of it back on purpose.** Facing east, both cabinets discharged into the pocket's own
north and west faces, which returned the stream **east and up** — and up meant
`WIN-M-LIV-S1` (x 31'-5"..33'-11") and `WIN-S-STUDY2` above it. Facing south they discharge
into open ground: `W-RG-EAST-BALCONY`'s axis spans x 28'-6"..32'-0" and it tops out at
0'-0", below the middle of either cabinet. That has not changed.

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
Crossing the pocket gave most of it back and improved the geometry as well as the length:
HP2 stands **1'-9" from the band penetration at x 30'-6", on the same wall it enters**, so
it leaves the casing, crosses a foot and a half of gravel and goes straight in. The
2026-09-03 layout ran 5'-0" of east-west line along the pad first, and the 2026-09-02 one
ran it under what is now the stair.

**And then HP1's route inverted outright.** Its condenser is on the NORTH face and its air
handler is at the north end of the second storey, so the whole run turned round: ~36 ft
became **~31 ft**, and it no longer climbs an occupied second-storey stud bay. The route is
below. The allowance is a lump and is not re-priced for any of this (at $26-49/LF the
footage is inside its own spread), but 31 ft is now essentially the FXU24's own 31 ft
precharge, so there is no meaningful field-charge adder either.

Gree's published limits, from the same submittals:

| | line | total | per port | rise | precharge |
|---|---|---|---|---|---|
| FXU24 (HP1) | 3/8"–3/4" | 164 ft | — | 49 ft | 31 ft + 0.323 oz/ft |
| MUL30 (HP2) | 1/4"–3/8" per port | 263 ft | 82 ft | 82 ft | 131 ft |

**One penetration through the main-floor band on the SOUTH side**, at y = 0, x ≈ 30'-6" —
now HP2's alone; HP1 has its own on the north face, below. Sleeved, sloped to
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
**The SE-corner stud bay is a dead entry now, kept for the record.** East of
`WIN-M-LIV-S1`'s jamb pack both `W-M-S2` and `W-S-S2` frame a king at x 33'-5 1/4" and a stud
at x 34'-8", leaving a **13 1/4" clear bay at x 33'-6 3/4"..34'-8"** that lines up floor to
floor (the corner bay beyond it is only 7 3/4" clear and carries the corner strapping, so it
is not the one). It was HP1's alternative riser while HP1 stood in the pocket. **HP1 is on
the north face and no system needs a riser on this wall at all**, so the bay is recorded as
verified-and-available and nothing more.

- **HP1** (3/8–3/4), **north face since 2026-09-04**: **~2 ft** south out of the casing at
  (28'-1 1/2", 37'-8 17/32") to a band penetration on `W-M-N1` — the same detail as the
  south one, sleeved, sloped out, flashed, expansion loop inside, and **not modelled** for
  the same reason. Then up an outside stud bay through the main top plates, the
  second-floor band and the second top plates into an `FS-ATTIC` bay, **~6'-4" west ALONG
  that bay** — along, so nothing is bored, `FS-ATTIC`'s I-joists spanning x — and down into
  `SF-S-HP1` over `RM-S-NCLOSET`. About **31 ft of line and 21 ft of rise against 164 ft and
  49 ft**: comfortable on both, and essentially AT the FXU24's 31 ft precharge, so no
  meaningful field charge.
  - **It was ~36 ft up the `W-M-S2` / `W-S-S2` bay** on the south face — an occupied
    second-storey stud bay in a bedroom-side wall, then 5'-0" west along an attic bay. Both
    ends of that route moved, so both the length and the acoustic exposure improved.
  - **A SECOND framed-wall penetration now exists in prose only.** `SleevePenetration` is
    concrete-only and there is no refrigerant `PipeRun` system, so the model carries neither
    hole. Two undrawn penetrations rather than one is the honest count.

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

- **The line sets and their TWO sleeves** — above; the sleeves because no framed-wall
  sleeve type exists, the line sets because no refrigerant `PipeRun` system does. There are
  two framed-wall penetrations now, one on the south band for HP2 and one on the north for
  HP1, and neither is an element.
- **`CD-B-HP1`, a power raceway from the panel to the north pad.** Deliberately not added in
  the 2026-09-04 pass: no check requires one, and the omission got *cheaper* with the move
  (about 60 LF of unmodelled home run down to about 45). Adding it drags in a
  `SleevePenetration` through `W-B-N1` and a below-grade riser transition — a raceway design
  pass, not a geometry move. Named here as a sized gap rather than left implicit.
- **The stands' cross-rails** — in `column:EQUIP_STAND_ALUM`'s price row, not in geometry.
- **Every pad's fall** — each `Slab` is flat at its high edge; the fall is the
  `ImperviousSurface` in `plan/site.py`. Four of them now.
- **A discharge-side baffle on the north face.** The prevailing winter wind here is NW and
  HP1's coil now faces into it. The 24" the stand already gives is half the answer; a baffle
  on the discharge side is the other half, and it is a detailing item for the drawings, not
  a model element.
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
  on the same cabinet at +10'-0"; it is still not calculated here. The twelve wedge anchors
  are a bolt-down-per-the-instruction detail (IRC M1401.4), not a designed restraint.

---

**Stale extents corrected 2026-09-11.** Three figures above quoted the apron return and the
leader as they stood before two earlier passes: the return was 3'-0" (x 29'-0"..32'-0") until
2026-09-03, when the balcony's joist cantilever went 6" -> 9" and the return gave 3" back to
keep the leader's slot; and the whole court's tops came down 2" to the porch datum on
2026-09-10, so +0'-6" became 0'-0". The leader followed the deck edge east to x 29'-0" and
its outlet is +0'-6", not +1'-0". None of it changes a conclusion in this note — the return
is still below the middle of either cabinet and the leader is still well south of the pocket
— but the numbers are now the model's.

**Then the return reached the concrete, 2026-09-12.** Its inboard end went x 29'-3" ->
28'-6", closing the 9" notch between it and `W-SG-E1`'s outer face where the terrace fill
met this pocket behind nothing. That is 9" of block along the pocket's south edge at
y -11'-0"..-10'-0" — 7'-0" south of the pad and 1'-6" south of the flight's bottom nosing,
so nothing this note concludes moves. The leader does: the return runs under it now, 6"
below its outlet, and the outlet takes a cast elbow and a 1'-0" shoe south to discharge past
the cap rather than onto the crest of a dry-stacked wall. The shoe is a drawing note, not a
modelled solid. The returns are no longer derived from the leader's slot — that contract is
retired in `params/sunken_garden.py` — so the figure to re-read if the court walls ever move
is `RETAINING_WALL_SPAN_X_FT`, not the deck edge.
