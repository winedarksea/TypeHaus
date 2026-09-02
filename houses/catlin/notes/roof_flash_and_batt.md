# CATLIN_ROOF — flash-and-batt, worked by hand (2026-08-31)

## Why this note exists

`AGENTS.md` and the repo guide both say it: *a calc that only
agrees with itself is not verified.* The engine now reports R-53.2 for this assembly and
NOT_APPLICABLE on its condensation gate, deferring to `code.R806_5_unvented_roof`. Both of
those are new code paths written in the same commit as the assembly they grade, which is
exactly the situation that rule is about. Everything below is arithmetic done independently
of the engine, from published material properties, and then compared to what the engine
says.

---

## 1. The assembly

Interior → exterior, as authored in `plan/assemblies.py::CATLIN_ROOF`:

| # | layer | thickness | R/in | R |
|---|---|---|---|---|
| — | interior air film (ASHRAE winter, RSI 0.12) | — | — | 0.682 |
| 1 | latex paint | 0" | 0.0 | 0.000 |
| 2 | gypsum board | 0.625" | 0.90 | 0.563 |
| 3 | **rafter bay** — 11 7/8" TJI 230 @ 24" o.c. | 11.875" | *parallel path, §2* | **50.99** |
| 4 | CDX plywood deck | 0.625" | 1.25 | 0.781 |
| 5 | high-temp adhered butyl membrane | 0.04" | 0.0 | 0.000 |
| 6 | 24 ga standing seam | 0.5" | 0.0 | 0.000 |
| — | exterior air film (RSI 0.03) | — | — | 0.170 |
| | | **13.09"** | | **53.19** |

R/inch values are the catalog's (`library/materials.py`, `plan/assemblies.py`): spf 1.25,
gypsum 0.90, Structural-1 plywood 1.25, ccSPF 6.5, and `fiberglass-r30c` 3.78 (derived in
§4). Steel and butyl are R-0.

## 2. The bay, parallel-pathed

The two fills are in SERIES with each other and in PARALLEL with the joist, which runs past
both. That is the only reading that counts the joist once.

```
framing path   spf, full depth      11.875 x 1.25            = R 14.844
fill path      batt   6.875 x 3.78  = 25.988
               ccSPF  5.000 x 6.50  = 32.500   (series)      = R 58.488

ff = 0.05  (TJI 230 flange 2 5/16" + web 3/8" at 24" o.c.; see §5)

U = 0.05/14.844 + 0.95/58.488
  = 0.0033683 + 0.0162428
  = 0.0196111  ->  R 50.99
```

## 3. Whole assembly

```
0.682 + 0.000 + 0.563 + 50.991 + 0.781 + 0.000 + 0.000 + 0.170  =  R 53.19
```

> **ORACLE — `haus explain CATLIN_ROOF houses/catlin` reports `R-value: R-53.2`.** Agreement
> to the printed precision. Code minimum is R-49 (MN 2024 / IRC Table N1102.1.2, CZ6), so
> the margin is **R-4.2**, and the assembly is 6.81" (perpendicular) shallower than the
> nine-layer stack it replaced, which read R-55.1.

## 4. Where the batt's 3.78/in comes from

An R-30C cathedral batt is 8 1/4" nominal — 30/8.25 = 3.64/in at its rated loft. It is
installed **compressed into 6 7/8"**, and compressing glass wool raises its density, which
LOWERS R per inch while RAISING R per bay. Manufacturer compressed-batt charts (Owens
Corning, CertainTeed) for an R-30 8 1/4" batt read R-27 at 7 1/4" and R-25 at 6 1/4";
linear between those two rows, 6 7/8" is R-26.25, taken as R-26.

```
26.0 / 6.875 = 3.78 per inch
```

**Two wrong answers this replaces**, both of which the material's own comment records:
reusing the label's 3.64/in over the shorter depth reads R-25.0 (understates by R-1);
reusing the `fiberglass` library tag's 3.7/in — a HIGH-DENSITY value for an R-21 squeezed
into 5.5" — reads R-25.4, right number for the wrong product.

## 5. The framing factor, 0.05

A TJI 230 is a 2 5/16" flange top and bottom with a 3/8" OSB web between. Averaged over the
11 7/8" depth the wood-and-web width is

```
(2 x 1.5" x 2.3125" + 8.875" x 0.375") / 11.875"  =  (6.9375 + 3.3281) / 11.875 = 0.864" 
0.864" / 24" o.c.  =  0.036
```

plus blocking, bearing stiffeners at both ends and the ridge-beam face, which the model does
not resolve into the layer. **0.05 is a deliberate round-up on 0.036**, the same
conservatism the 16" o.c. stack carried at 0.07 against a computed 0.054. Do not "correct"
it down to the geometric figure: what it is paying for is the framing this layer does not
name.

## 6. The condensation question — worked as a temperature, not a Glaser walk

**Why not a Glaser walk.** Above the deck sits a 0-perm standing-seam panel. A steady-state
Glaser method has no outward flux to distribute and equilibrates every plane inboard of that
panel to the full INTERIOR vapour pressure by construction — it reports ~100% RH at the deck
for *any* unvented metal roof, at any foam thickness, however it is designed.
`houses/catlin/CLAUDE.md` recorded exactly that, and the old assembly bought its margin by
leaving 5.6" of bay deliberately unfilled as a drying path. That is why
`checks/building_science/condensation.py::_r806_5_deferral` reports NOT_APPLICABLE here, and
why the criterion below is the one that governs.

**The criterion R806.5 actually sets.** In a flash-and-batt bay the plane at risk is the
**batt/foam interface**, not the deck: interior air and vapour can reach it through the
air-permeable batt, and cannot pass the air-impermeable foam. Table R806.5's R-value is
sized to hold that plane above the interior dew point through the heating season.

```
R outboard of the interface = foam 32.500 + plywood 0.781 + membrane 0 + panel 0 + film 0.170
                            = R 33.451
fraction of the total       = 33.451 / 53.187 = 0.6289
```

**Indoor dew point**, Magnus/Tetens over water at 70 F / 35% RH (`Preferences`):

```
es(21.11 C) = 610.94 exp(17.625 x 21.11 / (21.11 + 243.04)) = 2498.8 Pa
gamma       = ln(0.35) + 17.625 x 21.11/264.15 = -1.04982 + 1.40853 = 0.35871
Td          = 243.04 x 0.35871 / (17.625 - 0.35871) = 5.05 C  =  41.1 F
```

**Seasonal (the gate's condition).** Coldest MSP 1991-2020 monthly normal is January,
16.2 F:

```
T_interface = 16.2 + (70 - 16.2) x 0.6289 = 16.2 + 33.84 = 50.0 F
margin against the 41.1 F dew point                      = +8.9 F      PASS
```

**99% design hour (the screen's condition), -15 F:**

```
T_interface = -15 + (70 + 15) x 0.6289 = -15 + 53.46 = 38.5 F
margin                                                 = -2.6 F      CONDENSING
```

> **ORACLE — the engine's cold-snap screen reports "dew point reached at rafter, 63% through
> layer" at -15 F / 35% RH.** 63% of the 11.875" bay measured from its interior face is
> **7.48"**; the batt is 6.875" deep, so the crossing lands **0.6" into the foam** — within
> two-thirds of an inch of the interface this hand calculation puts it at. Two independent
> methods, the same plane.

**So what does that mean.** It means what the repo's own gate/screen split already says: a
crossing at the 99% design hour is a cold snap running a plane wet for hours; a crossing
against a monthly mean is a plane running wet for weeks. This assembly does the first and
not the second, with 8.9 F of seasonal margin — and it does it inside 0.25-perm foam bonded
to the deck, where the moisture available to condense is what the bay's own air holds, not
what a season of vapour drive can deliver. That is the whole basis of R806.5 item 5.3.

**Sensitivity, because the design-hour figure is close.** Foam depth is the lever and it is
nearly linear over this range:

| ccSPF | R (foam) | R (whole) | interface, Jan mean | interface, -15 F |
|---|---|---|---|---|
| 4" | 26.0 | 49.3 | 47.7 F (+6.6) | 33.9 F (-7.2) |
| **5"** | **32.5** | **53.2** | **50.0 F (+8.9)** | **38.5 F (-2.6)** |
| 6" | 39.0 | 56.9 | 51.8 F (+10.7) | 42.2 F (+1.1) |

4" is the row that shows why the design chose 5": it lands at R-49.3 whole-assembly, which
grazes the R-49 code minimum with 0.3 to spare, and its seasonal margin falls by a third.

## 7. The code path, term by term (IRC / MSRC R806.5)

| item | requirement | this assembly | |
|---|---|---|---|
| 1 | assembly inside the building thermal envelope | the attic is conditioned habitable space | ok |
| 2 | **no** interior Class I vapour retarder on the ceiling side | latex paint over gypsum — 5 perm, Class III | ok |
| 4 | CZ 5-8: the air-impermeable insulation is itself Class II or tighter | ccSPF 1.6 perm-in / 5" = **0.32 perm** | ok |
| 5.3 | air-impermeable insulation in direct contact with the sheathing underside, at the Table R806.5 R-value, with the air-permeable insulation directly under it | 5" ccSPF = **R-32.5** against **R-25** (zone 6) and **R-30** (zone 7); batt directly under it; bay filled to the deck (6.875 + 5.000 = 11.875) | ok |

Zone 7 is in the table deliberately: Minnesota holds both zones and the Duluth handout this
was first read against is CZ7. R-32.5 clears both rows, so the AHJ conversation cannot go
wrong on the zone.

> **ORACLE — `haus check` reports:** `PASS code.R806_5_unvented_roof: CATLIN_ROOF: item 5.3 —
> R-32.5 of air-impermeable insulation in direct contact with the sheathing underside, rated
> Class II; Table R806.5 zone 6 = R-25 (also clears the zone-7 row, R-30); no ceiling-side
> Class I retarder (item 2)`.

## 8. What is NOT verified here, and belongs to the PE

Recorded plainly because the engine will neither stop you nor help you on any of it:

- **The joist at 24" o.c.** `structural.rafter_span` is UNKNOWN/engineered at *both*
  spacings — an engineered profile is deliberately absent from the IRC R802.4.1 sawn table.
  The design reading is the Trus Joist TJ-4000 roof table, 11 7/8", **Low** slope column
  (a 6:12 guide direction), interpolated to Ps = 35 psf (Pg 50 per MN Rules 1303.1700,
  Hennepin; 0.7 x 50), against the **18'-0" HORIZONTAL** projection — span tables are
  horizontal, not the 19.9' sloped length. TJI 230 @ 24" reads 19'-3", a 15" margin; the
  TJI 110 that carried this roof at 16" o.c. reads 16'-8" at 24" and does not.
  **Two things make the printed table indicative rather than authoritative here**, and both
  belong in ForteWEB: its general note requires *a support beam or wall at the high end —
  ridge beam applications do not provide adequate support*, and catlin **hangs** its joists
  off `RB-HOUSE` on 38 LSSR hangers rather than bearing on it; and its deflection basis is
  L/180 total, L/240 live, where a gypsum cathedral ceiling may want L/240 total, which
  shortens the allowable span. The second is the stronger reason to take the 230 rather than
  the marginal 210. **The fallback is a TJI 210 at 19.2" o.c.** — 2'-6" of margin, ff ~0.058.
- **Two conservatisms worth banking while reading those spans.** The model takes no ASCE 7
  §7.4 **Cs slope factor**, which a 6:12 slippery standing-seam roof earns; and the new stack
  is LIGHTER than the one it replaces (~10 psf against ~12-14 — 6" of polyiso and a 5/8" OSB
  deck leave, foam and batt arrive). The real load case is below the 35 psf read above.
- **The uplift ties are the constraint, not the joists.** `H2.5A` is published at 700 lbf
  uplift for **SG 0.50** lumber (`library/hardware.py`, ESR-2613) and catlin frames **SPF at
  SG 0.42** — the library says in as many words that using 700 against an SPF plate is
  unconservative and nothing downstream can detect it. At 24" o.c. the tributary rises 1.5x,
  to roughly 480 lb/tie against a derated allowable nearer 560-600 lbf. Inside, but not
  comfortably, and roof corner/edge zone coefficients run higher than the wall figure that
  estimate came from. **Budget for upsizing the eave ties (H10A or equivalent)** rather than
  booking the 378 -> 360 count reduction as a saving.
- **The ridge hangers survive the move comfortably.** `notes/ridge_beam_detail.md` works each
  rafter at 600 lb into the ridge (12 sf tributary at ~50 psf) against an LSSR2.37 rated
  1,565 lb. At 24" that is ~900 lb — **1.74x cover**, down from 2.6x — and the lighter stack
  makes the real number better than that.
- **The deck cantilever.** The 5/8" plywood oversails the last joist at each eave and spans
  the wall girts. Nothing in the engine grades that overhang.
- **Sheathing span and the gypsum ceiling at 24" o.c.** No rule in the engine reads the
  spacing at all. Both are fine — 5/8" CDX is span-rated 40/20 and 5/8" board is rated for a
  24" o.c. ceiling where 1/2" is not, and catlin already specifies 5/8" — but nothing here
  verifies either.

## 9. Site build hold points

Three, and the first is worth more than the other two together.

1. **A moisture meter before the foam.** Verify the plywood at **< 16% MC** on a pin meter,
   bay by bay. Do not spray a wet deck. What wets a sandwiched deck is not diffusion and not
   a leak — it is the water already in the panel the day it was foamed, and after the foam
   goes on there is no drying path in either direction. $30 and an hour.
2. **Full contact, no voids.** Minimum 1.5" first lift, full adhesion to the deck underside,
   and a visual void inspection of every bay before the batts go in. A void holds water AND
   air, which is what a sandwich rots from. After the batts the deck underside is invisible
   for the life of the house.
3. **The ccSPF laps onto the ridge beam and over the hanger flanges, in the same pass.**
   19 bay ends die into `RB-HOUSE`'s faces at 38 hanger flanges — the most awkward
   air-barrier junction in the roof, free if specified and the detail most likely to be
   skipped. There is no separate air barrier to catch it: the foam *is* the air barrier now.

Optional, and the honest answer to the "anoxia preserves wood" argument: **borate or
copper-azole treated 5/8" plywood, about +$930-1,390.** Anoxia genuinely does preserve wood,
because decay fungi need free oxygen — but a roof cannot reach anoxia, since a leak delivers
water and dissolved oxygen together. Preservative treatment removes the fungal risk
regardless of oxygen, which no air seal can. ~$1,000 to make the one permanently hidden
layer in the assembly rot-proof.

## 10. Sources

- MSRC / IRC R806.5, unvented attic and unvented enclosed rafter assemblies, and Table
  R806.5 (insulation for condensation control) — City of Duluth handout 164.
- Trus Joist **TJ-4000** Specifier's Guide, 11 7/8" TJI roof span tables and section
  properties (flange and web geometry for the 110/210/230/360/560 series).
- MN Rules 1303.1700 — ground snow load, 50 psf for Hennepin County.
- Owens Corning / CertainTeed compressed-batt R-value charts (R-30 8 1/4" batt).
- ASHRAE Handbook of Fundamentals — winter surface film resistances, RSI 0.12 / 0.03.
- WMO CIMO Guide Magnus/Tetens saturation curve (the same form
  `checks/building_science/glaser.py` uses).
