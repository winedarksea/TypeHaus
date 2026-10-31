# RM-M-PANTRY — shelving designed to be climbed

From the kitchen peninsula/pantry rework.

The owner asked for shelves in the reach-in pantry that can be **stood on**, because that
is how the top shelf of a 7'-0" stack actually gets reached. This note is the build, and it
exists because there is no model field for "rated to stand on" — `FT-KIT-PANTRY-SHELVES-70`
carries the summary on its `source`, and the arithmetic is here.

## The room

Interior clear **6'-1 1/2" (E-W) x 2'-2 1/4" (N-S)**, 9'-0" to the ceiling.

| face | what it is | station |
|---|---|---|
| west | `W-M-C5B`'s east gypsum | x = 18'-3 1/4" |
| east | `W-M-PAN-E`'s west gypsum | x = 24'-4 3/4" |
| north | `W-M-N1B`'s interior gypsum (the exterior wall) | y = 35'-5 1/2" |
| south | `W-M-PAN-S`'s north gypsum, with `D-M-PANTRY`'s 36" pocket opening at the east | y = 33'-3 1/4" |

The carcass is **73 1/4" wide**, a 1/8" scribe off each side wall, and **18" deep**, standing
1/4" off the north wall (see *Depth* below). (Until 2026-10-30 this table read 1/8" tight
on every face; the model's finish faces are the ones above.)

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

## What is built instead: 1 1/4" solid red oak

Owner stock, scheduled as `SB-M-PANTRY` in `plan/millwork.py` and milled **6/4** (8/4 at
1 1/2" until 2026-10-16, when the pile turned out to be red oak and the thickness was cut
back to the thinnest that still passes). Red oak's E is ~1.8 x 10^6 psi and its MOR is
comparable to white oak's, so the conservative 1.6 x 10^6 psi stands. `b` = 18", `d` = 1.25":

| | full 73 1/4" span | between uprights, 35 1/2" |
|---|---|---|
| `S = b*d^2/6` | 4.69 in^3 | 4.69 in^3 |
| `I = b*d^3/12` | 2.93 in^4 | 2.93 in^4 |
| `M = P*L/4` | 4,578 in-lb | 2,219 in-lb |
| `f = M/S` | **≈ 977 psi** | **≈ 473 psi** |
| `d = P*L^3/(48*E*I)` | **≈ 0.437"** | **≈ 0.050"** |
| L/360 | 0.203" | 0.099" |

**The centre upright is the whole design.** Between uprights the point load deflects 0.050"
against the floor criterion's 0.099" (about L/710), and 473 psi is far inside any grade of red
oak. Ungabled the same shelf deflects **0.44"**: it fails badly. Uniform load agrees: 40 psf
over 18" is w = 5.0 lb/in, and `5wL^4/384EI` is ≈ 0.400" full-span and ≈ 0.022" per bay.

**The front-edge caveat (2026-10-30).** The table spreads the 250 lb across all 18" of depth.
A foot lands on the front edge, and oak is weak across the grain, so only a strip near the
nose really carries it. Take that strip as about half the depth and the numbers double:
**≈ 0.10" and ≈ 950 psi, right at L/360.** The stress is still easy. The deflection is why
6/4 is the floor: at 5/4 (1", `I` = 1.50 in^4) even the full-depth case is ≈ 0.097", and the
front-edge case is about twice that.

## What makes it standable

### 1. A 3-panel ply ladder, standing on the floor (2026-10-30)

Three 3/4" prefinished maple ply uprights (`maple-ply-prefin-34`, the bath-shelf stock): a
west end, the centre gable and an east end, each **18" x 84"**, standing on the finished
floor, with **no back panel**. Bays are **35 1/2"** clear.

- **Gravity goes to the floor through the ply.** The walls only hold the uprights plumb.
- **The end uprights screw to the corner framing**, which is certain at `N-M-N1` and
  `N-M-PAN3`: through the 1/8" scribe into the corner studs, low and high.
- **The centre upright is tied by every shelf**, plus one steel angle at the top to a
  north-wall stud above the case top.
- **No blocking anywhere, and no shelf fasteners in the exterior wall** apart from that one
  angle (the receptacle box and the driver, below, are electrical). Shelf heights no longer have to be fixed at framing.

It is structure, not joinery: the centre upright must never be "opened up" later for a wider
shelf.

### 2. ~~A 1x3 hardwood nose~~ — RETIRED 2026-08-29

It was a stiffener for the ply-shelf design, and solid oak needs none of it.

### 3. 1x3 oak cleats on the uprights, made on the bench

Cleats are **1x3 red oak, 16" long**, stopping 2" short of the front: 24 of them, two per
board (`FT-KIT-PANTRY-SHELVES-70`'s cut list, 4/4 owner stock). They are glued and screwed
to the uprights on the bench, set out from one **story stick** so both faces of the centre
upright match. Where both faces of the centre upright carry a cleat at the same height,
stagger the screws so they cannot meet. There are **no back cleats**: the shelf spans
one-way between the uprights, which is what the calc above assumes.

**Each shelf is screwed UP through its cleats**: a round hole at the front, a **3/8" slot at
the rear**. Boards run the bay (grain along it), so seasonal movement runs across the 18" depth,
front to back, roughly 1/4" in red oak over a Minnesota RH swing. The shelf stops **1/4" short of the
north wall**, which takes that movement, so nothing needs slotting into a wall. A solid shelf
pinned hard on all sides splits in year two, not on the day it goes in.

**No adjustable standards and no shelf pins.** A pin carries a jar, not a person.

### 4. Design load: treat it as floor, not shelf

**40 psf uniform PLUS a 250–300 lb concentrated load anywhere.** The concentrated case
governs, which is the reason for the centre upright.

## Shelf schedule

Top of board, above the finished floor; six boards per bay, the case top included
(`board_tops` on the type, so every drawing and the 3D carry it):

| bay | tops | clear openings |
|---|---|---|
| west (backstock, bins) | 21¼, 36½, 50¾, 64, 74, 84 | 20, 14, 13, 12, 8¾, 8¾ |
| east (everyday + microwave) | 17, 35, 54¼, 64, 74, 84 | 15¾, 16¾, 18, 8½, 8¾, 8¾ |

The east bay's 35" → 53" opening holds the microwave trial and `ED-M-PANTRY-RC1` at 48" on
`CKT-KITCH-SA2`. Pick a unit 15½" deep or less so the 18" shelf leaves rear vent clearance,
and run it with the pocket door open. The 64, 74 and 84 tops line up across the centre
upright. The west bay's 20" bottom opening takes the stand mixer.

Uniform spacing wastes roughly two shelves' worth of volume. **Every shelf is rated to be
stood on regardless of pitch**, so climbing does not need even rungs.

## Using it: bins west, everyday east

The doorway exposes the **east** bay, so it holds the everyday items. The **west** bay is
reached sideways across the 8" strip, so it holds **backstock in clear pull-out bins about 15"
deep**, sized three to a shelf, carried to the doorway to be picked through. That is what
makes an 18" bay you cannot face usable. Nothing to model.

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
  y 33'-11 1/4"..35'-5 1/4" and leave **8"**. RM-M-PANTRY is still reached from the doorway
  rather than walked into — 8" is a foothold, not a floor — so the shelves are still the
  thing you stand on, which is what this whole note is about. It is simply no longer true
  that there is nowhere at all to put a foot.
- **The second row is gone.** At 24" the back ~8" of every shelf was a row you had to move
  the front row to reach. At 18" a shelf is one reach deep.

Two things still make an 18" standable reach-in good rather than merely legal, and both
were already in this design:

1. **The shelves are standable**, so the bottom bay is a step and the top of a 7'-0" stack
   is genuinely reachable.
2. **Every bay is lit from both sides** by vertical jamb channels (below), which light the
   depth *behind* what is on each shelf.

**Door change, 2026-10-20:** a 36 x 80 Eclisse EKC3680 pockets west in the south wall.
The refrigerator already blocked about 23 inches of the old western bypass opening.
The new doorway exposes the east bay; the west bay is reached sideways across the
8-inch strip in front of the shelves. No shelf fastener or long screw may enter the cassette. The RO spans the perpendicular
stud faces, with explicit corner supports; see `pocket_frame_eclisse.md`.

## Lighting (2026-10-30)

The old single slot on the west wall grazed east along the shelf noses, and the 18"-deep
centre upright shaded the east bay, which is the one you see from the doorway. It is retired.

Four **vertical 24V tape channels** (`ED-T-LT-JAMB72`, mark **T**), one on each inside face
of the uprights: west-E (`ED-M-PANTRY-LT`), centre-W (`-LT2`), centre-E (`-LT3`) and east-W
(`-LT4`). Each runs **12" → 84"**, about 1" behind the shelf front, aimed into its bay, so
every bay is lit from both sides.

- **Channel:** Diode LED **S45** 45° aluminium channel (`DI-CHB-S45-96AL`, 96" bundle with a
  frosted lens, end caps and clips, cut to 72"), recorded as `PROD-DIODE-S45-CHANNEL`. It is fitted in the shop
  on the ply, and each shelf's two front corners are notched so the channel runs straight
  through.
- **Tape:** the house VALENT X at **1.9 W/ft** (3000 K, 95+ CRI). Four 6' runs are 45.6 W,
  57 W with the 125% factor, inside one 60 W driver. The 2.8 W/ft step would need 84 W.
- **Driver:** one 60 W OMNIDRIVE X (`ED-M-PANTRY-LT-PSU`, `ED-T-LT-PSU-60`), surface-mounted
  on `W-M-N1B` above the case top at **90"**, over the centre upright. The four leads are
  wired at the tops of the channels. It is reachable from the top shelf, ventilated, and
  clear under the 8'-4" cold-water crossing in `plan/mep_supply.py`.

### Controls

`ED-M-PANTRY-SW` is a **PIR-only occupancy sensor** (Leviton ODS10-IDW) on the INSIDE face of
`W-M-PAN-E`, 56" above the floor, with the lens's south half masked so it sees along the
shelves and not the kitchen (moved inside 2026-10-27). It switches the driver's 120V line on
`CKT-LT-BACKUP`, so all four channels come on together. There is no manual pantry switch on
the kitchen side; the 46" box on `W-M-PAN-E`'s kitchen face is the undercabinet relay
(`ED-M-KITCH-SW-UC`, a D215S) only.

## Sources

- Span limits: [WoodWeb, span limits for plywood shelving](https://woodweb.com/knowledge_base/Span_Limits_for_Plywood_Shelving.html),
  [The Sagulator](https://woodbin.com/calcs/sagulator/),
  [APA load-span tables (PDF)](https://www.innovativepanel.com/wp-content/uploads/2015/11/American-Plywood-Association-Load-Span-Table.pdf)
- Depth and spacing: [Kitchen Cabinet Kings, pantry shelf spacing](https://kitchencabinetkings.com/blog/pantry-shelf-spacing/),
  [Closet America, shelf height and depth](https://www.closetamerica.com/12-04-2018-finding-your-ideal-pantry-shelf-height-and-depth/)
- Reach-in lighting: [Sketched Interiors, butler pantry lighting](https://sketchedinteriors.com/butler-pantry-lighting-ideas/)
