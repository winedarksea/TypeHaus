# RM-M-PANTRY — shelving that is safe to climb

From the kitchen peninsula/pantry rework; reworked 2026-11-20 (open middle, strut post,
continuous boards, west return).

The shelves in the reach-in pantry must be **safe to stand on**, because that is how the top
of a 7'-0" stack gets reached. They do not have to be easy to climb: the owner's priority is
a stand mixer and an optional microwave at middle height. There is no model field for
"rated to stand on", so the types in `plan/pantry_shelf_types.py` carry the summary and the
arithmetic is here.

## The room

Interior clear **6'-1 1/2" (E-W) x 2'-2 1/4" (N-S)**, 9'-0" to the ceiling.

| face | what it is | station |
|---|---|---|
| west | `W-M-C5B`'s east gypsum | x = 18'-3 1/4" |
| east | `W-M-PAN-E`'s west gypsum | x = 24'-4 3/4" |
| north | `W-M-N1B`'s interior gypsum (the exterior wall) | y = 35'-5 1/2" |
| south | `W-M-PAN-S`'s north gypsum, with `D-M-PANTRY`'s 36" pocket opening at the east | y = 33'-3 1/4" |

The case is **73 1/4" wide**, a 1/8" scribe off each side wall, and **18" deep**, standing
1/4" off the north wall (see *Depth* below). The west return fills the 8" strip in front of
it at the west wall.

## Why a 3/4" plywood shelf cannot span this room

This section is the reason the shelves are **not** plywood. It was the original design and
the arithmetic retired it.

For a 3/4" shelf carrying a 250 lb adult at midspan (E ~ 1.3 x 10^6 psi):

| | 18" deep (built depth) | 16" deep (first draft) |
|---|---|---|
| `S = b*d^2/6` | 1.6875 in^3 | 1.5 in^3 |
| `I = b*d^3/12` | 0.6328 in^4 | 0.5625 in^4 |
| `M = P*L/4` (L = 73.25") | 4,578 in-lb | 4,578 in-lb |
| `f = M/S` | **≈ 2,713 psi** | **≈ 3,052 psi** |
| `d = P*L^3/(48*E*I)` | **≈ 2.49"** | **≈ 2.80"** |

Against a flatwise allowable of roughly **1,500–2,000 psi**, both are breaks, and both fail
outright on deflection. Note which way depth cuts: **going deeper HELPS**, because `b` grows
with the depth while the span does not. At 24" it was ≈1,950 psi and ≈1.65" — borderline on
stress and still a deflection failure. Plywood never worked at any depth this room allows.

Published guidance caps 3/4" birch ply shelving at 36"–42" even at ordinary *storage*
loads, and says to derate 30–50% for a point load.

## What is built: continuous 1 1/4" red oak on a strut post (2026-11-20)

Owner stock, scheduled as `SB-M-PANTRY` in `plan/millwork.py`, milled **6/4**. Red oak's E is
~1.8 x 10^6 psi; the conservative 1.6 x 10^6 psi stands. `b` = 18", `d` = 1.25":
`S` = 4.69 in^3, `I` = 2.93 in^4.

**Each level is ONE board, 71 3/4" clear**, on an oak end cleat at each upright and one
steel bracket at mid-length, off a strut post on the x=21'-4" stud. Span `L` is the upright
face to the post centre, **35 7/8"** each side.

### The board: two equal spans, a point at mid-span

Standard beam diagram, two equal spans, concentrated load at the centre of one span:
R1 = 13/32 P, R2 (the bracket) = 11/16 P, R3 = -3/32 P (the far end lifts; its cleat screws
hold it), M+ = 13/64 PL, M- (over the bracket) = 3/32 PL, deflection = 0.015 PL^3/EI.

| P | M+ | f, full depth | defl., full depth | f, front-edge strip (b = 9") | defl., strip |
|---|---|---|---|---|---|
| 250 lb | 1,822 in-lb | 389 psi | 0.037" | 777 psi | 0.074" |
| 300 lb | 2,186 in-lb | 466 psi | 0.044" | 933 psi | 0.089" |

L/360 = 0.100". **The front-edge case is the one that matters**: a foot lands on the nose,
and oak is weak across the grain, so take about half the depth as working. Even at 300 lb it
is L/405 and under 1,000 psi. Uniform 40 psf is w = 5.0 lb/in: M- = wL^2/8 = 804 in-lb,
deflection wL^4/185EI = 0.010", and the bracket takes R2 = 1.25 wL = 224 lb.

Continuity is what buys this. The old ply-ladder design had the same span, simply supported
between uprights (P = 250: 0.050" full depth, ~0.10" on the strip); the continuous board
over the bracket is stiffer at the same thickness. 6/4 stays the floor: at 5/4 (`I` = 1.50)
the strip case is ~0.14".

### The rear notch

Each board is notched round the post, **1 3/4" wide x 1 5/8" deep**: 1 3/8" of the post
stands inside the board's 18" (the board is 1/4" off the gypsum, the post 1 5/8" deep) and
1/4" is the board's front-to-back movement. The board is fixed at its front hole, so the
rear edge moves. Drill the two inside corners at 3/8" radius before sawing.

The notch sits at the negative-moment peak, over the bracket. Net section b = 16 3/8":
`S` = 4.26 in^3.

| case | M- | f at the notch |
|---|---|---|
| 250 lb mid-bay | 841 in-lb | 197 psi |
| 300 lb mid-bay | 1,009 in-lb | 237 psi |
| 40 psf both bays | 804 in-lb | 189 psi |

A front-edge load is carried by the front strip, which the notch does not touch.

### The bracket

**B-Line B409-18 ZN** (`PROD-BLINE-B409-18-ZN`), a single-channel cantilever bracket, cut to
**15 5/8"** so its tip stops 1" short of the board front; cold-galvanize the cut end. Read
from the catalog, not from memory: Eaton B-Line *Cable Tray Systems*, p. HST-18, "Cantilever
Bracket": B409-12 **960 lb**, B409-18 **640 lb**, B409-24 **480 lb**, uniform load, Safety
Load Factor 2.5. A uniform load W over 'A' is a root moment WA/2, and all three rows give
**5,760 in-lb**: one section, moment-governed. Cutting the free end does not change it.

| case on one bracket | root moment | ratio |
|---|---|---|
| 300 lb at the tip | 4,688 in-lb | **0.81** |
| 250 lb at the tip | 3,906 in-lb | 0.68 |
| 40 psf, R2 = 224 lb along the bracket | 1,750 in-lb | 0.30 |
| 250 lb at the tip with 40 psf | 5,656 in-lb | 0.98 |

The last row is not a design case: like a floor (ASCE 7-16 §4.4), the shelf takes the
uniform load OR the concentrated one, not both. It still holds, with the catalog's 2.5 behind
it; 300 lb on a fully loaded shelf would be 1.12. All 300 lb is put on the bracket when it
lands at the post line, which is conservative.

Unistrut P2231 is not a cantilever bracket and B-Line B297 is the double-channel one, so the
plan's "P2231 / B297 series" became the B409.

### The post and its lags

One Unistrut **P1000** (`PROD-UNISTRUT-P1000-PG`), 82 3/4" (floor to the top board's
underside), open face south, against the gypsum on `W-M-N1B`'s **stud-002 at x = 21'-4"**,
which is the resolved stud nearest the old gable and the bay's mid-length. Each bracket bolts
to it on a spring channel nut. A **3/8" x 5" lag** (`PROD-LAG-3-8X5-ZN`) goes through the web
**just above each bracket's channel nut** into the stud, set before the bracket, so the post
cannot rotate. This replaces the old top angle. Keep RC1's cable bores in stud-002 clear of
the six lag heights.

The bracket's moment pulls the post off the wall above the bracket and pushes it on below.
The post is stiff against the gypsum, so take the couple as that bracket's lag in tension
over the spacing to the lag below, about the gypsum face. The arm is the post's 1 5/8" plus
the bracket's 15 5/8": 17 1/4". The tightest spacing is 9 3/4" (54 1/4 to 64):

- T = 300 x 17.25 / 9.75 = **531 lb** (300 lb at the tip); 442 lb at 250 lb.
- Withdrawal, NDS 12.2.1: W = 1800 G^1.5 D^0.75 = 1800 x 0.42^1.5 x 0.375^0.75 =
  **235 lb/in** (G 0.42, SPF; the stud is a 2x6 LSL and denser).
- Thread: a 3/8" x 5" lag threads 3" less a 7/32" tip, **2.78"** (NDS Table L2; the tip
  does not count). The 2" shank spans the 12 ga web, 1/2" gypsum and washer (0.69"), so all
  the thread is in the stud, 4.3" deep in its 5 1/2": **653 lb** at C_D 1.0.
- **531 / 653 = 0.81** (0.68 at 250 lb). The 4" lag first drawn has 2.28" of thread, 535 lb:
  0.99, too close.

The top board (84") is not a step: 24" to the ceiling. Its bracket carries storage only.
The post carries its own brackets' gravity to the floor; the lags take only the couples.

### The end uprights

Two 3/4" prefinished maple ply uprights stand on the finished floor, carry the board ends
(R1 = 102 lb at 250 lb) to it, and screw to the corner framing at `N-M-N1` and `N-M-PAN3`:
through the 1/8" scribe into the corner studs, low and high. **The west upright is 25 3/4"
deep**, 1/4" off both the north and south walls, so its forward 7 3/4" is the return's west
end. It screws only to the west-wall framing, never to `W-M-PAN-S`: the pocket cassette fills
that wall and limits screws there to 1". The east upright is 18".

Cleats are **1x3 red oak, 16" long**, stopping 2" short of the front, one per board end (12,
4/4 owner stock), glued and screwed to the uprights on the bench off one **story stick**.
Each board screws UP through its cleats, a round hole at the front and a **3/8" slot at the
rear**, and up through a slot in its bracket. Boards run the bay (grain along it), so
seasonal movement runs front to back, about 1/4" in red oak over a Minnesota RH swing; the
1/4" gap to the north wall and the notch depth take it. **No adjustable standards and no
shelf pins.** A pin carries a jar, not a person.

**Design load: 40 psf, or 250-300 lb anywhere.**

### The west return (`FURN-M-PANTRY-RETURN`, `SB-M-PANTRY-RETURN`)

Once bins travel along the shelves, the west end of the 8" strip is dead floor, so a return
fills it: **12" clear (E-W) x 7 3/4" deep**, six boards at the main tops, butted to the main
boards' front edges and not glued to them. It bears at both ends: the west upright's forward
7 3/4" and a new **7 3/4" x 84" maple ply end panel** standing on the floor, cleats on both.
It stands 1/4" off `W-M-PAN-S` with nothing fixed to it. The panel is held in line by the six
boards screwed to its cleats, which are screwed to the west upright.

Simply supported, 12" span, `b` = 7.75": `S` = 2.02 in^3, `I` = 1.26 in^4. A 250 lb point at
mid-span is M = 750 in-lb, **f = 372 psi**, deflection = PL^3/48EI = **0.004"**. Nothing here
is close.

## Shelf schedule

Top of board above the finished floor, every board, main and return (`board_tops` on both
types, so every drawing and the 3D carry it):

| tops | clear openings |
|---|---|
| 17, 35, 54 1/4, 64, 74, 84 | 15 3/4, 16 3/4, **18**, 8 1/2, 8 3/4, 8 3/4 |

Continuous boards are why the heights unify: only 64/74/84 lined up across the old gable, so
a lane would have been useless at the other three. The **35" -> 53" opening** holds the
mixer (a bowl-lift is ~16 1/2" tall) and the microwave, side by side on the 72" board, with
`ED-M-PANTRY-RC1` at 48" on `CKT-KITCH-SA2` inside it (moved to x = 21'-6 3/4" so its plate
clears the post by 9/16"). Pick a microwave 15 1/2" deep or less so it stands in front of the
post with rear vent clearance, and run it with the pocket door open.

## Using it: a lane in front of the post

The post takes the back 1 3/8" of each board, so the board's front **16 5/8"** is a clear
lane end to end. A 15" bin slides along it from the west end to the doorway, which is what
retires review item 9's complaint that the west bins had no way out. The doorway exposes the
east half, so everyday items live there and backstock in clear bins further west; the return
holds narrow things (cans, jars, spices) in the strip.

## Depth: 18" — and the mill is what set it, not the ergonomics

Drawn at 16", changed to **24"** at the owner's direction, and settled at **18"**. The last
move is the one worth explaining, because it looks like a retreat from the 24" decision and
is not:

- **18" is the edge of the supply.** The owner's red oak runs to 18" wide. A finished face
  needs about 3/4" more than that in the rough — one edge straight-lined, the other jointed
  — so 18" finished asks for an 18 3/4" board; `haus millwork` lays it up as two 9" boards,
  which is how a solid 18" shelf is normally made anyway. At 24" every shelf was a glue-up
  of two wider, scarcer boards.
- **The published guidance was against 24" the whole time.** 16" is the usual practical
  maximum for a reach-in (14" is better) and 20"+ is normally called too deep to see into.
  The depth that made the stock work is also the depth that makes the pantry work, which is
  the only reason this was an easy change.
- **What is given up is real: about 25% of the shelf area.** The 24" decision was made for
  volume and the volume is what pays for the boards.
- **The room gets its floor back.** The room is **26 1/4" deep**. At 24" the shelves left
  about **2"** to stand in; at 18", 1/4" off the north wall, they run
  y 33'-11 1/4"..35'-5 1/4" and leave **8"**, whose west 13 1/2" the return now fills.
  RM-M-PANTRY is reached from the doorway rather than walked into.
- **The second row is gone.** At 24" the back ~8" of every shelf was a row you had to move
  the front row to reach. At 18" a shelf is one reach deep.

Two things still make an 18" standable reach-in good rather than merely legal, and both
were already in this design:

1. **The shelves are standable**, so the bottom bay is a step and the top of a 7'-0" stack
   is genuinely reachable.
2. **The bay is lit from both ends** by vertical jamb channels (below), which light the
   depth *behind* what is on each shelf.

**Door change, 2026-10-20:** a 36 x 80 Eclisse EKC3680 pockets west in the south wall.
The refrigerator already blocked about 23 inches of the old western bypass opening.
The doorway exposes the east half; the west half is reached by sliding bins along the lane.
No shelf fastener or long screw may enter the cassette. The RO spans the perpendicular
stud faces, with explicit corner supports; see `pocket_frame_eclisse.md`.

## Lighting (2026-10-30; two channels since 2026-11-20)

Two **vertical 24V COB channels** (`ED-T-LT-JAMB72`, mark **T**), one on each end upright's
inside face: west (`ED-M-PANTRY-LT`) and east (`ED-M-PANTRY-LT4`). Each runs **12" -> 84"**,
about 1" behind the shelf front, and they face each other across the open 72". The centre
pair (`-LT2`, `-LT3`) went with the gable that hosted them; the fallback, if the owner wants
them back, is a pair on the strut post's side faces.

- **Channel and tape:** a generic 45-degree aluminium channel cut to 72"
  (`PROD-CHANNEL-45-GENERIC`) with Armacost RibbonFlex Pro 24V COB, 3000 K, 90 CRI, mark E's
  tape, 18 W a channel (generic COB since 2026-10-31; the S45/VALENT X selection is retired).
  Fitted in the shop on the ply; each board's front corners are notched past them.
- **Driver:** `ED-M-PANTRY-LT-PSU`, a 96 W Class 2 HLG (`ED-T-LT-PSU-96-WE`),
  surface-mounted on `W-M-N1B` above the case top at **90"**, over the post. 2 x 18 W x 1.25 =
  45 W: oversized now, kept as authored. Reachable from the top shelf, ventilated, and clear
  under the 8'-4" cold-water crossing in `plan/mep_supply.py`.

### Controls

`ED-M-PANTRY-SW` is a **PIR-only occupancy sensor** (Leviton ODS10-IDW) on the INSIDE face of
`W-M-PAN-E`, 56" above the floor, with the lens's south half masked so it sees along the
shelves and not the kitchen (moved inside 2026-10-27). It switches the driver's 120V line on
`CKT-LT-MAIN`, so both channels come on together. There is no manual pantry switch on
the kitchen side; the 46" box on `W-M-PAN-E`'s kitchen face is the undercabinet switch
(`ED-M-KITCH-SW-UC`, a plain paddle since 2026-11-03) only.

## Sources

- Bracket: Eaton B-Line *Cable Tray Systems* catalog, p. HST-18, "Cantilever Bracket" (B409
  and B297 tables, read 2026-11-20)
- Lag withdrawal: NDS 2018 §12.2.1, W = 1800 G^1.5 D^0.75

- Span limits: [WoodWeb, span limits for plywood shelving](https://woodweb.com/knowledge_base/Span_Limits_for_Plywood_Shelving.html),
  [The Sagulator](https://woodbin.com/calcs/sagulator/),
  [APA load-span tables (PDF)](https://www.innovativepanel.com/wp-content/uploads/2015/11/American-Plywood-Association-Load-Span-Table.pdf)
- Depth and spacing: [Kitchen Cabinet Kings, pantry shelf spacing](https://kitchencabinetkings.com/blog/pantry-shelf-spacing/),
  [Closet America, shelf height and depth](https://www.closetamerica.com/12-04-2018-finding-your-ideal-pantry-shelf-height-and-depth/)
- Reach-in lighting: [Sketched Interiors, butler pantry lighting](https://sketchedinteriors.com/butler-pantry-lighting-ideas/)
