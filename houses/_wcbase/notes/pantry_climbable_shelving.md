# RM-M-PANTRY — shelving designed to be climbed

From the kitchen peninsula/pantry rework.

The owner asked for shelves in the reach-in pantry that can be **stood on**, because that
is how the top shelf of a 7'-0" stack actually gets reached. This note is the build, and it
exists because there is no model field for "rated to stand on" — `FT-KIT-PANTRY-SHELVES-70`
carries the summary on its `source`, and the arithmetic is here.

## The room

Interior clear **5'-10 1/4" (E-W) x 2'-2" (N-S)**, 9'-0" to the ceiling.

| face | what it is | station |
|---|---|---|
| west | `W-M-C5B`'s east gypsum | x = 18'-3 3/8" |
| east | `W-M-PAN-E`'s west gypsum | x = 24'-1 5/8" |
| north | `W-M-N1B`'s interior gypsum | y = 35'-5 3/8" |
| south | `W-M-PAN-S`'s north gypsum, with `D-M-PANTRY`'s 60" bypass in it | y = 33'-3 3/8" |

Shelves are **70 1/4" wide** — wall face to wall face, the room's whole clear span — and
**18" deep** against the north wall (owner's decision, replacing 24"; see *Depth* below).

## Why a 3/4" plywood shelf cannot span this room

This section is the reason the shelves are **not** plywood. It was the original design and
the arithmetic retired it.

For a 3/4" shelf carrying a 250 lb adult at midspan (E ~ 1.3 x 10^6 psi):

| | 18" deep (built depth) | 16" deep (first draft) |
|---|---|---|
| `S = b*d^2/6` | 1.6875 in^3 | 1.5 in^3 |
| `I = b*d^3/12` | 0.6328 in^4 | 0.5625 in^4 |
| `M = P*L/4` (L = 70.25") | 4,391 in-lb | 4,391 in-lb |
| `f = M/S` | **≈ 2,600 psi** | **≈ 2,900 psi** |
| `d = P*L^3/(48*E*I)` | **≈ 2.1"** | **≈ 2.4"** |

Against a flatwise allowable of roughly **1,500–2,000 psi**, both are breaks, and both fail
outright on deflection. Note which way depth cuts: **going deeper HELPS**, because `b` grows
with the depth while the span does not. At 24" it was ≈1,950 psi and ≈1.65" — borderline on
stress and still a deflection failure. Plywood never worked at any depth this room allows.

Published guidance caps 3/4" birch ply shelving at 36"–42" even at ordinary *storage*
loads, and says to derate 30–50% for a point load.

## What is built instead: 1 1/2" solid white oak

Owner stock, scheduled as `SB-M-PANTRY` in `plan/millwork.py` and milled 8/4. Same
arithmetic, `b` = 18", `d` = 1.5", E ~ 1.6 x 10^6 psi:

| | full 70 1/4" span | gabled to ~34 3/4" |
|---|---|---|
| `S = b*d^2/6` | 6.75 in^3 | 6.75 in^3 |
| `I = b*d^3/12` | 5.06 in^4 | 5.06 in^4 |
| `M = P*L/4` | 4,391 in-lb | 2,172 in-lb |
| `f = M/S` | **≈ 650 psi** | **≈ 322 psi** |
| `d = P*L^3/(48*E*I)` | **≈ 0.223"** | **≈ 0.027"** |

**Strength is no longer the argument, and the gable stays anyway.** 650 psi is well inside
any grade of white oak. But this shelf is graded as a *floor* (see *Design load* below), so
the deflection criterion is **L/360 = 0.195"**, and the ungabled span misses it at 0.223".
Uniform load lands in the same place: 40 psf over 18" x 70 1/4" is w ≈ 4.9 lb/in and
`5wL^4/384EI` ≈ 0.20". Both cases sit right on the limit unsupported and nowhere near it
gabled.

## What makes it standable

### 1. A full-height centre gable at mid-span — NOT OPTIONAL

A 3/4" ply gable, floor to top shelf, notched around the cleats, splitting the run into two
~34 3/4" bays. It is what takes the shelf from L/315 to L/1300, and it is the member the
cleat and blocking layout is built around. It is structure, not joinery, and it must not be
"opened up" later for a wider shelf.

### 2. ~~A 1x3 hardwood nose~~ — RETIRED 2026-08-29

The ply design got a 3/4" x 2 1/2" hardwood edge glued and screwed on edge at every shelf
front. It was a **stiffener**: it nearly tripled a ply shelf's effective I, and it was the
cheapest way to take 0.20" of gabled sag out from underfoot. There is 0.027" to take out
now. Its second job — giving a plywood edge a hardwood face — is done by the shelf being
hardwood. It is deleted, not deferred, and that closes a quantity gap: the nose was ~41 LF
of hardwood that nothing in the model counted.

### 3. Continuous 1x3 cleats on three sides

Shelf screwed **down onto** the cleats, so the load path is **cleat → fastener → stud**
and never **shelf → pin**.

**Not glued, and the side-cleat holes are slotted.** Boards run the 34 3/4" bay, so the
grain is along the bay and the shelf's 18" of seasonal movement is **front to back** —
along the side cleats, across their line of screws. That is roughly 1/4" of tangential
movement in white oak over a Minnesota RH swing. Screw tight at the **front** only and
elongate every side- and back-cleat hole rearward. A solid shelf pinned hard on three sides
splits, and it splits in year two, not on the day it goes in. This is the one detail the
switch from plywood introduced and the one most likely to be built the old way.

**No adjustable standards and no shelf pins.** A pin carries a jar, not a person. Losing
adjustability is the price and it is worth paying; the graduated spacing below is what buys
the flexibility back.

### 4. Fasteners and blocking

- Two **#10 x 3" structural screws per cleat into solid wood at EVERY bay** — not "where
  a stud happens to land".
- **Flat 2x4 blocking laid in each bay BEFORE the gypsum.** This is a sequencing item, and
  it is the one that gets missed: once the board is on, there is nothing to hit.

### 5. Design load: treat it as floor, not shelf

**40 psf uniform PLUS a 250–300 lb concentrated load anywhere.** The concentrated case
governs, which is the whole reason for the gable and the nose.

## Shelf spacing — graduated, not uniform

| bay | clear height | what it holds |
|---|---|---|
| bottom | ~20" | small appliances, bulk |
| middle | 12"–14" | boxes, bottles |
| top | 8"–10" | cans, jars |

Uniform 16" wastes roughly two shelves' worth of volume. **Every shelf is rated to be stood
on regardless of pitch**, so climbing does not require an even rung spacing — the two
requirements do not actually fight.

## Depth: 18" — and the mill is what set it, not the ergonomics

Drawn at 16", changed to **24"** at the owner's direction, and settled at **18"**. The last
move is the one worth explaining, because it looks like a retreat from the 24" decision and
is not:

- **18" is the widest shelf that comes off ONE board.** The owner's white oak runs to 18"
  wide. A finished face needs about 3/4" more than that in the rough — one edge
  straight-lined, the other jointed — so 18" finished asks for an 18 3/4" board and is the
  edge of the supply; `haus millwork` flags it, and the flag means *hand-pick the widest
  boards in the stack*, not *glue it up*. At 24" every shelf was a two-board edge glue-up
  outright.
- **The published guidance was against 24" the whole time.** 16" is the usual practical
  maximum for a reach-in (14" is better) and 20"+ is normally called too deep to see into.
  The depth that made the stock work is also the depth that makes the pantry work, which is
  the only reason this was an easy change.
- **What is given up is real: about 25% of the shelf area.** The 24" decision was made for
  volume and the volume is what pays for the boards.
- **The room gets its floor back.** The room is **26" deep**. At 24" the shelves ran
  y 33'-5 3/8"..35'-5 3/8" and left **2"** to stand in; at 18" they run
  y 33'-11 3/8"..35'-5 3/8" and leave **8"**. RM-M-PANTRY is still reached from the doorway
  rather than walked into — 8" is a foothold, not a floor — so the shelves are still the
  thing you stand on, which is what this whole note is about. It is simply no longer true
  that there is nowhere at all to put a foot.
- **The second row is gone.** At 24" the back ~8" of every shelf was a row you had to move
  the front row to reach. At 18" a shelf is one reach deep.

Two things still make an 18" standable reach-in good rather than merely legal, and both
were already in this design:

1. **The shelves are standable**, so the bottom bay is a step and the top of a 7'-0" stack
   is genuinely reachable.
2. **`ED-M-PANTRY-LT` is a vertical slot**, which lights the depth *behind* what is on each
   shelf. Less critical at 18" than it was at 24", and still the right fixture.

**Check at rough-in that the bypass leaves and their track clear the shelf noses.** This was
the tightest dimension in the room at 24" and it has 6" more slack now, but the requirement
is unchanged: the leaves and their two-track head must hang INSIDE the 4 1/2" jamb depth of
a 2x4 partition. Specify the track with the door, not after the shelves are in.

## Lighting

`ED-M-PANTRY-LT` (`ED-T-LT-SLOT72`, schedule mark **T**) is a 6'-0" vertical LED slot on
the west wall, base at 1'-6", so the lit line runs 1'-6"..7'-6" past every shelf edge.

A vertical strip is the correct single fixture for a reach-in, and at 24" deep it stops
being a preference: **overhead alone is the worst option**, because every shelf below the
top sits in its own shadow — and the shadow is 24" long here, not 16". Switched from
the kitchen side (`ED-M-PANTRY-SW`, on the 8 7/8" of `W-M-PAN-S` east of the door's RO).

Two refinements worth taking at rough-in, neither modelled:

- **A door-jamb switch**, instead of or wired parallel to the wall switch, so opening the
  bypass lights the pantry — the standard for a closet.
- Optionally a second layer of **shelf-edge strips** at the front underside of each shelf,
  facing back. 3000–4000 K either way.

## Sources

- Span limits: [WoodWeb, span limits for plywood shelving](https://woodweb.com/knowledge_base/Span_Limits_for_Plywood_Shelving.html),
  [The Sagulator](https://woodbin.com/calcs/sagulator/),
  [APA load-span tables (PDF)](https://www.innovativepanel.com/wp-content/uploads/2015/11/American-Plywood-Association-Load-Span-Table.pdf)
- Depth and spacing: [Kitchen Cabinet Kings, pantry shelf spacing](https://kitchencabinetkings.com/blog/pantry-shelf-spacing/),
  [Closet America, shelf height and depth](https://www.closetamerica.com/12-04-2018-finding-your-ideal-pantry-shelf-height-and-depth/)
- Reach-in lighting: [Sketched Interiors, butler pantry lighting](https://sketchedinteriors.com/butler-pantry-lighting-ideas/)
