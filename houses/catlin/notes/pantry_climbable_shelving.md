# RM-M-PANTRY — shelving designed to be climbed

2026-08-24, with the kitchen peninsula/pantry rework.

The owner asked for shelves in the reach-in pantry that can be **stood on**, because that
is how the top shelf of a 7'-0" stack actually gets reached. This note is the build, and it
exists because there is no model field for "rated to stand on" — `FT-KIT-PANTRY-SHELVES-70`
carries the summary on its `source`, and the arithmetic is here.

## The room

Interior clear **5'-10 1/4" (E-W) x 2'-6" (N-S)**, 9'-0" to the ceiling.

| face | what it is | station |
|---|---|---|
| west | `W-M-C5B`'s east gypsum | x = 18'-3 3/8" |
| east | `W-M-PAN-E`'s west gypsum | x = 24'-1 5/8" |
| north | `W-M-N1B`'s interior gypsum | y = 35'-5 3/8" |
| south | `W-M-PAN-S`'s north gypsum, with `D-M-PANTRY`'s 60" bypass in it | y = 32'-11 3/8" |

Shelves are **70 1/4" wide** — wall face to wall face, the room's whole clear span — and
**24" deep** against the north wall (owner's decision, 2026-08-24; see *Depth* below).

## Why a 3/4" plywood shelf cannot span this room

The first draft had 3/4" birch ply spanning the full 70 1/4" clear. **It fails at either
depth.** For a 3/4" shelf carrying a 250 lb adult at midspan (E ~ 1.3 x 10^6 psi):

| | 24" deep (built) | 16" deep (first draft) |
|---|---|---|
| `S = b*d^2/6` | 2.25 in^3 | 1.5 in^3 |
| `I = b*d^3/12` | 0.84375 in^4 | 0.5625 in^4 |
| `M = P*L/4` (L = 70.25") | 4,391 in-lb | 4,391 in-lb |
| `f = M/S` | **≈ 1,950 psi** | **≈ 2,900 psi** |
| `d = P*L^3/(48*E*I)` | **≈ 1.65"** | **≈ 2.4"** |

Against a flatwise allowable of roughly **1,500–2,000 psi**, the 16" shelf is a break. The
24" shelf is borderline on stress and **fails outright on deflection**: 1.65" of sag under
one person is not a floor and is not a shelf either.

Note which way depth cuts: **going deeper HELPS**, because `b` grows with the depth while
the span does not. It does not help nearly enough to skip the gable.

Published guidance caps 3/4" birch ply shelving at 36"–42" even at ordinary *storage*
loads, and says to derate 30–50% for a point load.

## What makes it standable

### 1. A full-height centre gable at mid-span — NOT OPTIONAL

A 3/4" ply gable, floor to top shelf, notched around the cleats, splitting the run into two
~34 3/4" bays. Same arithmetic at half the span:

```
M = 250 * 34.75 / 4 = 2,172 in-lb
f = M/S  = 2,172 / 2.25          ≈ 965 psi    (well inside allowable)
d = P*L^3/(48*E*I)               ≈ 0.20"
```

(At the 16" depth the same numbers are ≈ 1,450 psi and ≈ 0.30".)

This is the member that makes the whole thing legal to stand on. It is structure, not
joinery, and it must not be "opened up" later for a wider shelf.

### 2. A 1x3 hardwood nose, glued and screwed on edge

Still springy underfoot at 0.20", so every shelf front gets a 3/4" x 2 1/2" hardwood edge,
on edge, glued and screwed to the ply. That nearly triples the shelf's effective I and is
the cheapest stiffener available.

### 3. Continuous 1x3 cleats on three sides

Shelf glued and screwed **down onto** the cleats, so the load path is
**cleat → fastener → stud** and never **shelf → pin**.

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

## Depth: 24" — the owner's call, and past the published guidance

This was drawn at 16" and changed to **24"** on 2026-08-24 at the owner's direction. The
trade is worth stating plainly, because the drawings will not show it:

- 16" is the usual published practical maximum for a reach-in (14" is better), and 20"+ is
  normally called too deep to see into.
- The room is **30" deep**. At 24" the shelves run y 33'-5 3/8"..35'-5 3/8" and leave
  **6"** of floor in front of them, at y 32'-11 3/8"..33'-5 3/8". **RM-M-PANTRY is
  therefore reached from the doorway, not walked into** — it is a very deep wall of
  shelving behind a 60" opening, not a room you step inside.
- The back ~8" of every shelf is a second row: reaching it means moving the front row.

Two things make 24" work rather than merely fit, and both are already in this design:

1. **The shelves are standable**, so the bottom bay is a step and the back of the top shelf
   is genuinely reachable. At 16" this was a convenience; at 24" it is what makes the depth
   usable at all.
2. **`ED-M-PANTRY-LT` is a vertical slot**, which is the one fixture that lights the depth
   *behind* what is on each shelf. At this depth an overhead-only pantry would be a cave.

Also check at rough-in that the bypass leaves and their track clear the shelf noses — 6" is
not much, and the door hardware is the thing most likely to want some of it.

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
