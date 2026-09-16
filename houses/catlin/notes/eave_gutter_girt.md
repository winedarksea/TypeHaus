---
title: "Eave gutter girt and eave blocking — hand calc"
tags: [roof, eave, gutter, girt, blocking]
source:
  - resolve/framing/roof_eave.py
  - resolve/roof_eave_girt.py
  - takeoff/eave_fasteners.py
  - params/roof_trim.py
---

# Eave gutter girt and eave blocking (RF-HOUSE, 2026-09-16)

A hand pass by itself. No engine record computes this, so nothing oracles against it. It
sizes what `Roof.eave_blocking` and the gutter girt put in the model, and it is why the girt
is a 2x6 and not a 2x4 like the wall girts.

## 1. Geometry (east eave, from `out/model.json`; west mirrors)

| Piece | x (in) | z (in) |
|---|---|---|
| rafter plate W-A-E1/E2 | 426.0–431.5 | top 242.25 |
| 2x6 eave block, on edge, between flanges (21.69" clear) | 430.0–431.5 | 242.25–247.75 |
| closure sheathing | 431.5–432.0 | |
| 3-2x6 standoff (4.5"), at each bay centre | 432.0–436.5 | 242.25–247.75 |
| 2x6 girt, flat | 436.5–438.0 | 242.25–247.75 |
| PBR cladding | 438.0–439.25 | |
| box gutter back sheet (inner face) / front | 439.58 / 445.58 | 243.6–248.6 |
| top wall girt course 007 | 436.5–438.0 | 237.25–240.75 |

TLOK08 through the stack: girt 1.5 + standoff 4.5 + sheathing 0.5 = 6.5", leaving 1.5" in
the block, all of it thread (2" thread, ESR-1078 Table 1A). The clamped stack is 6.0" and
the plain shank is 6.0". It is the same screw and the same geometry as the wall girt
(`catlin_truss_engineering.md` §3).

## 2. Load

A 6" x 5" box full of ice: 30 in² / 144 x 57 pcf = 11.9 plf. Water would be 13.0 plf.
Coil and hangers add about 1.5 plf. Design with **w = 25 plf**, about 1.8x that, to cover
ice built up on the rim.
Per 24" bay: **P = 50 lb**, one standoff per bay.

The centroid is at the trough's mid-width, x = 442.6. Its lever about the sheathing face
(x 432.0) is e = 10.6", so **M = 50 x 10.6 = 530 in-lb per standoff**. It does not matter
how the gutter is hung from the girt: the whole moment has to cross the standoff-to-block
joint.

## 3. The girt screws (withdrawal and pull-through)

The standoff tries to roll outward about its bottom edge, which bears on the sheathing at
z 242.25. Two screws sit 1" in from the top and bottom (z 246.75 and 243.25), so their arms
are d = 4.5" and 1.0". Screw forces grow linearly with arm:

    sum d^2 = 4.5^2 + 1.0^2 = 21.25 in^2
    T_top = 530 x 4.5 / 21.25 = 112 lb        T_bot = 530 x 1.0 / 21.25 = 25 lb

Capacities are the house's own reads (plan/assemblies.py EXT_2X6, ESR-1078):
- **Withdrawal:** 170 lb/in x 1.5" of thread in the block = 255 lb. The 0.5" in the
  sheathing is not counted. **112 / 255 = 0.44.**
- **Head pull-through:** 200 lb, so **112 / 200 = 0.56.**
- Sensitivity: if bearing is taken 1/2" in from the edge, the arms are 4.0 and 0.5 and
  T_top = 130 lb. That gives 0.51 and 0.65.

**Why not the wall's 2x4 and one screw:** one screw at mid-height of a 3.5" standoff has a
1.75" arm, so T = 530 / 1.75 = 303 lb. That is 1.19x the withdrawal and 1.5x the
pull-through, and it fails. The 5-1/2" face and a second screw are what make the joint
work.

**Screw bending and shear.** The screw runs wood-to-wood with no gap through girt, plies and
sheathing. The standoff is solid timber clamped by the screw, not a gap the screw
cantilevers across (the same reading as `catlin_truss_engineering.md` §3.6). The vertical
shear is 50 / 2 = 25 lb per screw, against lateral design values in the hundreds of pounds.
Bending is not a mechanism here.

## 4. The blocking against rolling

The block takes the same 530 in-lb: an outward pull at the screws and an inward push from
the sheathing at its foot. That rolls the 2x6 about its outer bottom edge on the plate, so
its inboard heel lifts, 1.5" from the pivot.

**Gravity:** the block bears straight on the plate, so no fastener carries weight.

**Plate toe screws**, 2 per block, SDWS22400DB. Each is driven at 45° from 1-1/4" up the
inboard face, and only the plate's 1.5" depth is counted as embedment.
NDS 2018 §12.2.1 lag-screw withdrawal: W = 1800 G^1.5 D^0.75 = 1800 x 0.42^1.5 x 0.22^0.75
= 157 lb/in. The toe factor C_tn = 0.67 (§12.5.4) gives 105 lb/in, and 1.5" gives **158 lb
per screw**.

    heel uplift = 530 / 1.5 = 353 lb      two plate screws = 316 lb      -> 0.90 of it

**End toe screws**, 2 per end, SDWS22300DB, into the beveled web stiffener pair. The
screws at each end are about 3" apart vertically. They carry the remainder as a couple:
(530 − 316 x 1.5) = 56 in-lb, over 2 ends x 3" is **9 lb per screw**. Even with no credit
for the plate screws, the ends alone take 530 / (2 x 3) = 88 lb per screw in lateral load.
That is inside ordinary 0.220" screw values in SPF but is **not graded here**, because the
main member is 23/32" plywood either side of a 3/8" web. A reviewer should confirm it if
the plate screws are ever dropped.

## 5. What would change these numbers

- **The gutter moving outboard.** M scales with e. Moving the back sheet 1" out (e = 11.6)
  takes T_top to 123 lb and 0.61 of pull-through.
- **A heavier gutter**, such as a 7" box or heated cable with its own ice load.
- **Standoff plies other than 2x6.** Less face height means a shorter lever between the
  screws (§3).
- **Toe screws omitted in the field.** The plate screws carry 90% of the rolling moment.

## Counts billed (takeoff/eave_fasteners.py)

36 blocks and 36 standoffs (18 bays per eave):
- 72 x TLOK08 (girt standoffs);
- 144 x SDWS22300DB (block ends);
- 72 x SDWS22400DB (block to plate).
