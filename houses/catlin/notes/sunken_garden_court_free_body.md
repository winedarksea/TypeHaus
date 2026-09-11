# Sunken-garden court — the closed free body, worked by hand

> ## ⚠ STILL A SCREENING. IT NOW CLEARS, AND THAT IS NOT A STAMP.
> This note supersedes the **conclusion** of `notes/sunken_garden_retaining_screening.md`
> and **not its arithmetic**. That note found `W-SG-W2`, `W-SG-E2` and `W-SG-S` at FS
> 0.58–0.64 against sliding where IRC R404.4 requires 1.5, and *as an isolated free
> cantilever each wall really is there*. Its §4 table is the frozen oracle for
> `engineering/retaining_basis.analyse()` and must not be restated or "corrected".
>
> What was wrong was the free body, not the mechanics. The three walls are not three
> cantilevers. They are three sides of a **closed loop of cast concrete**, and two of them
> face each other across a 19'-0" court and cancel.
>
> Every geotechnical input below is still a presumptive code-table value on a site with **no
> geotechnical report**, and the soil class comes from a survey for the wrong county. **FS
> 1.80 against 1.50 is a screening that clears. It is not a design and it is not a seal**, and
> `FoundationWall.engineering_spec` stays unset for the reason the screening note's §6 gives.
>
> **RE-WORKED BY HAND THREE TIMES, AND THE TOP OF THE WALL HAS COME DOWN EACH TIME.**
>
> *First* (2026-09-05), the three retaining footings rose 9" so that their tops became the
> court's walking surface (`params/sunken_garden._wall_bottom`, which is now `_court_top`):
> stem 10.37' → 9.62', `H` 11.37' → 10.62'.
>
> *Then* (2026-09-05), the owner capped the run at 36" out of the yard and the tops fell 4"
> from +0'-6" to +0'-2": stem 9.62' → 9.2865', `H` 10.62' → 10.2865'.
>
> *Then* (2026-09-10), **all five court walls came flush with the porch datum at 0'-0"** —
> one form height, one strip-and-set, one continuous top line, no 2-inch jog at the porch
> corner. The tops fell the last 2": stem 9.2865' → **9.1198'**, `H` 10.2865' →
> **10.1198'**. `SPEC.retaining_top_ft` is `porch_top_ft` now, not a figure derived off
> grade; the 36" is a RESULT, and against the yard `plan/site.py` now authors at -3'-4" the
> run stands 40" out of it.
>
> Thrust goes as `H²` and the resisting weights fall linearly, so all three moves pushed the
> same way and the totals below are the compound of them: FS **1.58 → 1.71 → 1.77 → 1.80**
> sliding, toe flexure 0.72 → 0.61 → 0.56 → **0.54**, stem flexure 0.72 → 0.65 → **0.61**.
> **Nothing here was recomputed from the engine's output**; §4, §6 and §7 are worked term by
> term below and the engine is then checked against them, which is the only order in which
> an oracle means anything. The third pass was worked before `SPEC.retaining_top_ft` was
> touched, and the engine then reproduced §4's `system_demand` 61,446.1 lb and
> `system_capacity` 110,620 lb to the digit.

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Written:** 2026-08-30, by hand, before the calculation it oracles was encoded.
**Oracle for:** `engineering/retaining_system.py` and `engineering/retaining_basis.py`,
reported by `structural.foundation_unbalanced_fill`; reproduced by
`tests/test_retaining_court.py`.
**Companions:** `notes/sunken_garden_retaining_screening.md` (the isolated-wall case, still
correct on its own terms), `notes/superseded/balcony_lateral_bracing_design.md` (the structure standing
on these walls).

---

## 0. The convention question, worked both ways, with a stated choice

The screening note and the engine both read the wall's own bottom as the **underside** of
the footing. It is the **top**. `resolve/envelope.py::_resolve_footing` resolves a
wall-hosted footing at `z1 = wall.z0_m`, so the footing hangs entirely below the wall — and
that same line is why the 2026-09-05 move had to be made by raising the WALL bottom, since
`depth` pushes only `z0` down and `bottom_elevation` is ignored on this branch:

```
                        before 09-05      after 09-05      after 09-10
W-SG-E2     z0          -118.4375"        -109.4375"       -109.4375"   (the wall)
            z1            +6.0000"          +2.0000"          0.0000"   (the porch datum)
FT-SG-E2    z0          -130.4375"        -121.4375"       -121.4375"   (the footing,
            z1          -118.4375"        -109.4375"       -109.4375"    wholly below it)
```

Two different heights were being conflated, and the choice matters because they differ by a
whole footing depth:

| quantity | value | what it is for |
|---|---|---|
| `unbalanced_fill` | **9.1198'** | the **IRC** quantity — fill against the wall, to the wall's base. R404.1.1's 48" threshold and Table R404.1.2(8)'s rows are read against it. Authored as `_ret_top - _wall_bottom`, so it followed the move on its own. |
| `H` for stability | **10.1198'** | top of retained soil to the **underside of the footing**. Soil bears on the back of the heel as well as the back of the stem, and the plane being slid along is the footing's underside. |
| stem height | **9.1198'** | what stands above the footing — the concrete's own weight, the soil column on the heel, and the flexural cantilever in §6. |

**Worked the other way,** for the record — the confusion this convention exists to prevent:
if the wall bottom were read as the footing underside, the stem would be 8.1198' and `H`
9.1198', giving a thrust of `½ × 60 × 9.1198² = 2,495 plf` instead of 3,072 — **19% light** — while also
under-counting the stem's own dead weight and the soil on the heel by a foot each. The two
errors are in opposite directions and **do not cancel**.

**Choice: `H` runs to the footing underside**, and `unbalanced_fill` keeps its IRC meaning.
Everything below uses that. `retaining_wall.BASIS_VERSION` went 1 → 2 for it.

---

## 1. The free body — what is actually built

Plan, at the footing level. The court is 19'-0" clear × 28'-0", walls 12" cast concrete:

```
                     N-SG-MW                         N-SG-ME
      x=8.0  ---------+=================================+--------- x=28.0
                      |   W-SG-ARCH  (grade beam)       |
                      |   12" x 17 1/2", 20'-0" clear   |      y = -11.00
                      |   BURIED — top is the garden    |
                      |   floor's underside             |
                      |                                 |
       soil    -->    |                                 |    <--    soil
       pushes  -->    | W-SG-W2            W-SG-E2      |    <--    pushes
       EAST    -->    | 18'-4"             18'-4"       |    <--    WEST
                      |                                 |
                      |          the court              |
                      |        19'-0" x 28'-0"          |
                      |                                 |
      x=8.0  ---------+=================================+--------- x=28.0
                     N-SG-SW      W-SG-S              N-SG-SE       y = -29.33
                                  20'-0"
                            ^  ^  ^  ^  ^  ^  ^
                            soil pushes NORTH — unopposed
```

Section, one side wall, west (retained) to east (court):

```
    0'-0"   ============  top of wall = the PORCH DATUM, and the terrace the apron holds
            |          |    (40" over the -3'-4" yard the site now authors)
            | 12" stem |   <-- soil, 9'-1 7/16" of it, pushing this way
   terrace  |          |
   at 0'-0" |          |
            |          |
  -9'-1 7/16"   +------+----------+    <-- footing TOP = wall bottom = THE COURT FLOOR
                | 3'-0" |  1'-0"  |  4'-0"      8'-0" x 1'-0" strip
                |  heel |  stem   |  toe        offset 6" INTO the court
  -10'-1 7/16"  +-------+---------+
                |  42" of ASTM C33 #57 washed crushed stone  |
                |  (FB-SG-*, non_frost_susceptible, tiled)   |
  -13'-7 7/16"  +--------------------------------------------+
```

**The toe IS the walking surface (2026-09-05).** It used to top out 5 1/2" below the rim
slab's underside with fill in the gap. `SL-SG-FLOOR` now carries five `FO-SG-TOE-*` voids —
W/E/S over these three strips, N-W/N-E over the two porch strips, which came up to the same
plane later the same day — so the rim bills net concrete while its `outline` still spans the
whole 532 sf court, which is what every derivation that gates on `category == "slab"` needs
(see the note at those openings). The net rim polygon's intersection with every FT-SG-*
footprint is 0.000 sf; it was 2.0 sf for one day, where the W/E toes were cut to the FIELD's
north edge and the footings run 6" further.

**The one thing this drawing says that the old one did not:** `W-SG-W2` and `W-SG-E2` are
the same wall mirrored about x = 18'-0". Same 12" section, same top (0'-0"), same bottom
(−9'-1 7/16"), same 18'-4" length, same footing. Their thrusts are **equal and opposite**,
and they are joined at the south by `W-SG-S` through a cast corner and at the north by
`W-SG-ARCH`. What is between them is concrete, not air.

### The E-W cancellation, from the model's own constants and not asserted

`params/sunken_garden.py` derives both walls from one set of numbers, which is why they are
identical rather than merely similar:

| | `W-SG-W2` | `W-SG-E2` |
|---|---|---|
| nodes | `N-SG-MW` → `N-SG-SW` | `N-SG-SE` → `N-SG-ME` |
| axis | x = `_x_ax_w` = 8.000' | x = `_x_ax_e` = 28.000' |
| length | `_y_ax_mid − _y_ax_s` = 18.3333' | the same expression | 
| top / bottom | `_ret_top` / `_wall_bottom` | `_ret_top` / `_wall_bottom` |
| fill | `_ret_unbalanced_fill` | `_ret_unbalanced_fill` |
| assembly | `SUNKEN_GARDEN_WALL` | `SUNKEN_GARDEN_WALL` |

Every field is the **same symbol**, not a matching literal. There is no arithmetic by which
one can differ from the other, and the cancellation is therefore exact:

```
P_W2 · L_W2 · (+x)  +  P_E2 · L_E2 · (−x)  =  0        identically
```

**The sum is taken over the whole group as one rigid body, not by pairing walls up.** That is
deliberate: pairing needs a special case for "the unopposed one", and it gives no answer at
all for a wall whose restraint reaches nothing. Summed as a resultant, a wall with no partner
simply keeps its thrust.

---

## 2. Geotechnical inputs

Unchanged from `sunken_garden_retaining_screening.md` §3, which is where they are argued.
Repeated here only so this note can be read term by term:

| quantity | value | source |
|---|---|---|
| soil class | GM (silty gravel) | `plan/site.py` states it for this Ramsey parcel; the MN profile carries the same GM regionally |
| active EFP | 45 psf/ft | IBC Table 1610.1 |
| **at-rest EFP** | **60 psf/ft** | IBC Table 1610.1, same row — **this is the graded case, see §4** |
| allowable bearing, on the stone | 3,000 psf | IBC Table 1806.2 class 3 |
| friction, on the stone | **0.35** | IBC Table 1806.2 class 3, footnote a — × dead load |
| friction, on the site's own GM | 0.25 | class 4 — the **no-stone** sensitivity, §5 |
| soil unit weight | **110–130 pcf, a band** | no code table publishes one; both ends run |
| concrete unit weight | 150 pcf | conventional |
| f'c | **3,000 psi** | IRC Table R402.2, foundation walls exposed to weather, severe |

**Severe weathering is not a map lookup in Minnesota.** MN Rules 1309.0301 subp. 2 amends
IRC Table R301.2(1) and writes "Severe" into the weathering column outright. (The figure to
cite if one ever had to is R301.2(**4**); R301.2(3) is the 2012/2015 numbering.)

**The 0.35 is traced, not assumed.** It is IBC Table 1806.2's *class 3* row — "sandy gravel
and/or gravel" — and the engine reaches it only through
`FootingBedding.non_frost_susceptible=True`, which is an authored ASTM D422 gradation claim
(<6% passing #200) about the very stone under these footings. It is **not** inferred from the
`aggregate` free-text string. Eleven footings in this structure already stake their frost
design on that same claim (`structural.frost_depth`, ASCE 32 soil replacement, 2026-08-29).
**§5 says what happens if the bed is not built as specified.**

---

## 3. The geometry, as it now stands

| | |
|---|---|
| stem | 12" cast concrete, **9'-1 7/16"** above the footing |
| footing | **8'-0" wide × 1'-0" deep**, offset **6" toward the court** — toe 4'-0", heel 3'-0" |
| `H`, top of soil to footing underside | **10.1198'** |
| retained face | outboard, terrace at 0'-0" — the porch datum, 40" over the -3'-4" yard (the raised garden's apron holds it) |
| resisting face | inboard, court floor at −9'-1 7/16" — **the toe top IS that floor**, so the toe is buried 0" and `toe_embedment_ft` stays the hardcoded 0.0 it always was |
| cross-member | `W-SG-ARCH`, 12" × 17 1/2", 20'-0" clear, buried |
| stem reinforcement | **`#6 @ 10" o.c.` vertical, retained face**, 2" cover — sized in §6 |
| footing reinforcement | **`#6 @ 10" o.c.` transverse, top AND bottom**, 3" cover — sized in §7; `#4 @ 18"` longitudinal |
| mix | **`EXPOSED_MIX`** — f'c **5,000 psi**, w/cm 0.40, 6% ±1.5 air, ACI class **F3 + C2**, ASTM A767 cl. 1 galvanized bar (galvanized AFTER fabrication; A780 repair at any cut or field bend), macro-synthetic fibre |

### Why the footing grew INBOARD and not symmetrically

The eccentricity check (§4) is what forces a wider base, and a symmetric widening is the
obvious move and the one thing that does not fit. `params/raised_garden.py` measures its
apron 3'-0" clear of these walls' outer faces — **the owner's own figure, from the brief** —
which lands the apron legs' inner faces *exactly* on the 7'-0" footings' outboard edges at
x = 4.5 / 31.5 and y = −32.833. Tangent, no overlap, and asserted. Any symmetric widening
walks the outboard edge under the apron and moves a wall the brief pins.

The court side is free, so the concrete goes there. `Footing.offset` slides the strip 6"
toward the toe:

```
   outboard edge  =  8.000 − 0.500 (half stem) − 3.000 (heel)  =  4.500      UNCHANGED
   inboard edge   =  8.000 + 0.500             + 4.000 (toe)   = 12.500      was 11.500
```

Verified in the resolved model, before and after: **4.50 / 31.50 / −32.83 to four figures.**
The heel — the term that carries the stabilising soil — is untouched at 3'-0", so the extra
12" is pure toe, buys eccentricity, and costs **+2.10 CY** across the three runs with no new
excavation outboard of anything.

---

## 4. The calculation

Per lineal foot, moments about the toe, service loads.

```
P   = ½ · EFP · H²                                       lateral thrust, triangular
W   = W_stem + W_footing + W_soil-on-heel                 all dead load
F   = μ · W                                               passive on the toe neglected
M_ot = P · H/3
M_r  = W_ftg·B/2 + W_stem·(toe + t/2) + W_heel·(B − heel/2)
x̄    = (M_r − M_ot)/W ,   e = B/2 − x̄ ,   q = W/B · (1 + 6e/B)

SYSTEM:  demand   = | Σ P(m)·L(m)·n̂(m) |     a 2-D resultant
         capacity = Σ μ(m)·W(m)·L(m)
```

### The terms, at at-rest 60 / 110 pcf — the graded case

```
P        = ½ × 60 × 10.1198²                      = 3,072.3 plf
W_stem   = 1.0  ×  9.1198 × 150                   = 1,368.0 plf
W_ftg    = 8.0  ×  1.0    × 150                   = 1,200.0 plf
W_heel   = 3.0  ×  9.1198 × 110                   = 3,009.5 plf
W                                                 = 5,577.5 plf
F        = 0.35 × 5,577.5                         = 1,952.1 plf

M_ot     = 3,072.3 × 10.1198/3                    = 10,364   ft-lb/ft
M_r      = 1,200×4.0 + 1,368.0×4.5 + 3,009.5×6.5  = 30,518   ft-lb/ft
x̄        = (30,518 − 10,364)/5,577.5              = 3.6135 ft
e        = 4.000 − 3.6135                         = 0.3865 ft  (kern B/6 = 1.333 ft) ✓
q_max    = 5,577.5/8 × (1 + 6×0.3865/8)           =   899 psf  (allow 3,000)          ✓
FS_ot    = 30,518 / 10,364                        = 2.94       (need 1.50)            ✓

SYSTEM
  total thrust  = 3,072.3 × (18.333 + 18.333 + 20.0) = 174,097 lb
  resultant     = 3,072.3 × 20.0                     =  61,446 lb   (E-W cancels exactly)
  cancelled                                          = 112,651 lb
  capacity      = 1,952.1 × 56.667                   = 110,620 lb
  FS_sliding    = 110,620 / 61,446                   = 1.80       (need 1.50)         ✓
```

**Every term above moved the same way and for one reason.** `P` goes as `H²`. `H` has now
fallen three times — 11.3698' → 10.6198' when the footings rose 9", → 10.2865' when the tops
came down 4" to the 36" cap, → **10.1198'** when all five court walls came flush with the
porch datum — so the thrust is down 24% from where this note started. The resisting terms
fell too, the stem being 14 3/4" shorter than it was and the soil column on the heel with
it, but they fall LINEARLY, which is why every ratio improves rather than staying put. All
three moves made this court more stable, and the reason is the same one each time: thrust is
quadratic in height and weight is not.

**The third cut is the smallest and it is the one that was free.** The first two were paid
for — 9" of extra excavation, then 4" of wall the owner gave up. This one bought a
simplification (one form height across the court instead of two) and the stability came
along with it.

### All four corners of (active, at-rest) × (110, 130 pcf)

| case | system FS | FS overturning | e / kern | q_max |
|---|---|---|---|---|
| **at-rest 60, 110 pcf — GRADED** | **1.80** ✓ | **2.94** ✓ | **0.387 / 1.333** ✓ | **899** ✓ |
| at-rest 60, 130 pcf | 1.98 ✓ | 3.29 ✓ | 0.129 / 1.333 ✓ | 840 ✓ |
| active 45, 110 pcf | 2.40 ✓ | 3.93 ✓ | 0.078 / 1.333 ✓ | 738 ✓ |
| active 45, 130 pcf | 2.64 ✓ | 4.38 ✓ | 0.294 / 1.333 ✓ | 935 ✓ |
| required | 1.50 | 1.50 | within B/6 | ≤ 3,000 |

**Read the last TWO rows' `e` with care: they are on the other side of centre.** At active 45
the resisting moment is large enough that the resultant lands past mid-base, toward the heel —
4.078' from the toe tip at 110 pcf and 4.294' at 130. The magnitude is what the kern test
grades and both clear 1.333' comfortably either way, but those two figures do not mean the
same thing the top two rows' do, and a reader comparing them straight down the column would
be misled. **The split is now clean at the load case**: both at-rest rows sit toward the toe
and both active rows past mid-base. Shortening the stem takes proportionally more off the
overturning moment than off the resisting one, so the resultant walks toward the heel and
rows cross the centre without anything being wrong — one row had crossed before the 36" cap,
and the second crossed with these last two inches.

**The graded row is the worst of the four.** Both ends of the soil band agree on the verdict,
so the answer does not turn on the one input no code table publishes — which is exactly the
condition under which `retaining_basis` is willing to report a verdict at all.

### Why at-rest, and the deflection that settles it

**You cannot cite a permanent base restraint in the resistance term and simultaneously claim
the walls are free enough to shed to the active wedge in the demand term.** Crediting the
restraint concedes the point. Worked, as a base-restrained top-free cantilever under the
triangular at-rest load:

```
w₀ = 60 × 9.1198 / 12                 = 45.60 lb/in per 12" of wall
E  = 57,000 √3,000                    = 3,122,000 psi
Ig = 12 × 12³/12                      = 1,728 in⁴
δ  = w₀ L⁴ / (30 E I)  ,  L = 109.44"

   uncracked, I = Ig          δ = 0.040"  =  0.00033 H
   cracked,   I ≈ 0.35 Ig     δ = 0.115"  =  0.00095 H
```

Against Clough & Duncan (1991), as **AASHTO LRFD Table C3.11.1-1** and Caltrans *Trenching
and Shoring Manual* Table 4-1 — dense sand **0.001H**, medium dense 0.002H, loose 0.004H.
(Do **not** cite NAVFAC DM 7.02 for these; its figures are 0.0005/0.002, roughly half, and
citing the friendlier source for the number you want is how a screening stops being one.)

The honest reading: **the answer is now clearly on the at-rest side, and it has crossed a
line.** Uncracked the wall does not move enough to mobilise the active state at all;
cracked it reaches 0.00095 H, which is **below** the dense-sand 0.001H figure rather than
at it. It sat at 0.00102 H before these last two inches. The L⁴ term turns each height cut
into a much larger one in δ (0.151" → 0.126" → 0.115" cracked across the three moves), so
active is *harder to argue than it was, three times over* — and the wall no longer reaches
even the friendliest published threshold for mobilising it. At-rest is *defensible*, and it
costs 1.80 instead of 2.40 — margin this design can afford. **Active is the sensitivity,
not the design.**

---

## 5. ⚠ The corner that does not clear, and what the design therefore depends on

**Without the washed-stone bed, at μ = 0.25 throughout, the system reaches FS 1.29 against
the 1.50 required.**

```
capacity = 0.25 × 5,577.5 × 56.667  =  79,015 lb
FS       = 79,015 / 61,446          =  1.29     ✗
```

That is not a rounding. **0.35 versus 0.25 is the whole margin**, and it rides entirely on
`FootingBedding.non_frost_susceptible=True` — an authored claim that the 42" section under
these three footings is clean, open-graded, **washed** ASTM C33 #57 crushed stone, placed and
compacted, drained by the 4" sock-wrapped tile to `DRW-SG-MAIN`.

The claim is legitimate: eleven footings in this structure already stake their **frost**
design on the same sentence, and it was reasoned about there. But it must be said out loud
rather than absorbed:

> **This design depends on the stone bed being built as specified.** Unwashed stone, a fines-
> contaminated section, a bed placed without compaction, or a tile that does not drain, and
> the court is at 1.29 and does not meet IRC R404.4. Inspect and document the bed at
> placement. It is not an incidental levelling course; it is the reason the walls stand.
>
> Three height cuts have moved this row — 1.13 → 1.22 when the footings rose, → 1.26 at the
> 36" cap, → **1.29** with the flush tops — and none changed anything about the argument. It
> is still short of 1.50, the whole margin still rides on μ, and 0.35 versus 0.25 is still
> the difference between a court that stands and one that does not. Note what the three
> moves did *not* do: they cannot close this gap, because μ multiplies the same `W` on both
> sides of the comparison, so the ratio moves only through the geometry and never through
> the friction. Only the bed can close it.

The single highest-value thing anyone can buy before pouring remains a **geotechnical
boring**: μ = 0.25 is the presumptive floor for a broad class, and a real test on a genuine
silty gravel could plausibly support 0.35–0.45 on the native soil itself, which would make
the whole question moot — and would change the answer more than any amount of concrete.

---

## 6. The stem — the limit state nothing had computed, and the steel it wants

`SUNKEN_GARDEN_WALL` is one 12" concrete STRUCTURE layer with **no `vertical_reinforcement`
authored**, while the braced sibling `W-SG-E1` carries `#6 @ 38" o.c.` — so the model was
explicit that these three had none. **A base restraint acts inches from the stem's base and
relieves none of this.** Fixing sliding alone would have turned the report green over a
louder, uncomputed failure.

Cantilever from the top of the footing, at-rest, stem 9.1198':

```
M   = ½ × 60 × 9.1198² × 9.1198/3         =  7,585 ft-lb/ft   (service)
Mu  = 1.6 × 7,585                         = 12,136 ft-lb/ft   (IBC §1605.2 on H)
S   = 12 × 12²/6                          = 288 in³/ft
f   = 7,585 × 12 / 288                    = 316 psi           (service flexural tension)
```

**Plain**, ACI 318 §14.5.2, φ = 0.60 (Table 21.2.1):

```
φMn = 0.60 × 5√5,000 × 288 / 12           = 5,091 ft-lb/ft    d/c = 2.38   ✗
```

**And "2.4 times over" understates it.** ACI 318 R22.6.3 says the plain-concrete wall provisions
apply *"only for walls laterally supported in such a manner as to prohibit relative lateral
displacement at top and bottom"*, and that the Code *"does not cover walls without horizontal
support … Such laterally unsupported walls are to be designed as reinforced concrete
members."* A retaining wall is unsupported at the top by definition — the same condition that
trips R404.4. **An unreinforced stem here is not a section that fails a check; it is a section
outside the Code.**

**Reinforced**, ACI 318 §22.3, φ = 0.90. Steel on the **retained** face — that is where the
cantilever puts the tension, and putting it on the wrong face is the classic way a correctly
sized wall falls over. Cover **3"**, which is not the Code minimum and is the point: ACI
Table 20.5.1.3.1 asks 2" of a #6 on a formed face exposed to weather (as does IRC Table
R404.1.2(8) footnote i for bars larger than #5), and `structural.concrete_cover_meets_minimum`
grades against that 2". The extra inch is bought for class **C2** — see §6a.

| schedule | Aₛ in²/ft | d in | a in | φMn ft-lb/ft | d/c | |
|---|---|---|---|---|---|---|
| `#6 @ 16"` | 0.330 | 8.625 | 0.388 | 12,520 | 0.97 | ✓ sufficient, not selected |
| `#5 @ 10"` | 0.372 | 8.688 | 0.438 | 14,177 | 0.86 | ✓ sufficient, not selected |
| `#6 @ 12"` | 0.440 | 8.625 | 0.518 | 16,565 | 0.73 | ✓ sufficient, not selected |
| **`#6 @ 10"`** | **0.528** | **8.625** | **0.621** | **19,755** | **0.61** | **✓ selected** |
| `#6 @ 8"` | 0.660 | 8.625 | 0.776 | 24,463 | 0.50 | ✓ more than needed |

**`#6 @ 10" o.c.` is retained, and it stopped being the arithmetic minimum on 2026-09-05.**
**The table has gained a row under it at each height cut since, and the flush tops gained
the last one**: `#6 @ 12"` crossed first, then `#5 @ 10"`, and `#6 @ 16"` — the coarsest
spacing listed, which failed outright at 1.02 two revisions ago — now clears at 0.97. Every
schedule in this table works. The selection is deliberately **not** dropped, for two reasons
written down here so the question does not have to be re-opened each time the top of the
wall moves:

1. **One bar, one spacing, on one pour.** §7 sizes the footing mat at `#6 @ 10"` and the
   footing's own demand did not fall as far (toe d/c 0.56). Two spacings on the same pour is
   two bundles, two bender setups and two things for an inspector to miscount, and the saving
   is a few hundred dollars of bar.
2. **The margin is not spare.** §5 is unchanged in kind: the entire sliding case rides on
   μ = 0.35, which rides on a stone bed being built as specified, and at μ = 0.25 the court
   is at 1.29. A wall whose stability depends on a construction claim is the wrong place to
   spend flexural margin.

**`#6 @ 16"` clearing is the row to be careful with.** It is the one schedule here whose
passing would actually save something — a third of the bar, at the coarsest spacing a crew
would place — and it clears at 0.97. That is a 3% margin on a wall whose load case
(at-rest rather than active) is itself a judgement worth about 25%, and reason 1 above also
bears on it: §7 sizes the footing mat at `#6 @ 10"`, so `#6 @ 16"` on the stem is two
spacings on one pour for a few hundred dollars of steel.

`#5 @ 10"` sat at exactly 1.00 for two revisions and was listed then only to be rejected; it
clears now, which is worth noticing precisely because nothing about the bar changed — the
wall got shorter three times underneath it.

### 6a. What the third inch costs, and why it is spent anyway

Cover comes straight off `d`, so this is not a free durability upgrade — it is a purchase,
and the price is legible: `d` 9.625" → 8.625", φMn 22,131 → 19,755 ft-lb/ft, **d/c 0.55 →
0.61**. An 11% capacity write-down on the same steel.

It is spent because cover is the only term in the chloride problem that buys **distance**.
Every other lever this wall pulls buys *time* against a front that is still advancing —
w/cm 0.40 slows diffusion, the 25% Class F fly ash refines the pore structure, the ASTM A767
galvanizing raises the chloride threshold the bar can tolerate. Cover is what sets how far
the front has to travel before any of that matters, and it is the one term that cannot be
added later. These six walls are class **C2**: they take deicing salt off the drive above,
and they hold it in a court that has no grade to drain to — the water leaves through
`DRW-SG-MAIN` or it sits there.

The wall still passes at 0.61, and the structure's governing limit state is unchanged: base
restraint at FS 1.80, d/c 0.83 (§4). Nothing about this trade moves the number that governs.

It is authored on the **schedule** (`_RET_STEM_STEEL.cover`) and not on the mix, and that
distinction is load-bearing. `EXPOSED_MIX` pours the footings under these walls too,
where 3" is the Code figure and free; on the stem it costs 11%. One mix, two faces, two
covers — which is exactly why `resolve/concrete.cover_for` reads the element's schedule
before its mix.

**This table has been re-worked four times now, and the selection survived every one.**
Twice on 2026-09-03 — at 5,000 psi instead of 3,000, then at 3" cover instead of 2" — and
once at each of the two height cuts since. The two pull opposite
ways — the mix added 2-3% of capacity, the cover took 11% back — and `#6 @ 10"` is the answer
to all three versions of the question. What did change is its standing: it used to be the
comfortable choice above a working `#6 @ 12"`, and it is now the only schedule below `#6 @ 8"`
that carries the moment.

The mix half of that, for the record. The table was originally worked at
IRC Table R402.2's presumptive 3,000 psi, because until `ConcreteSpec` existed there was
nowhere for a pour to state a mix and the engine hardcoded that value for every concrete
calc it ran. `SUNKEN_GARDEN_WALL` now states the 5,000 psi F3+C2 mix it is actually poured
from, `stem_flexure` reads it, and every capacity above rose 2-3%. **The choice is unchanged
and so is the reason for it** — the margin at `#6 @ 12"` went 2% to 4%, which was not a
margin then. It is 27% now, and what carries the selection is reason 1 in §6 rather than the
arithmetic.

Checked alongside:

* **tension-controlled**, so φ = 0.90 is the right factor. `β1` is **0.80** at 5,000 psi,
  not 0.85 — ACI 318-19 Table 22.2.2.4.3 steps it down 0.05 per 1,000 psi above 4,000, and
  taking 0.85 here is the standard slip. `c = a/β1 = 0.621/0.80 = 0.777"`,
  `εt = 0.003 (8.625 − 0.777)/0.777 = 0.0303`, far past 0.005.
* **minimum reinforcement**, ACI 318-19 §11.6.1: ρl ≥ 0.0015 for bars larger than #5 →
  0.216 in²/ft. This is a fraction of the GROSS section and so does not move with cover.
  §11.6.2 raises it to 0.0025 → 0.360 in²/ft where `Vu > 0.5 φVc`, and this wall is under
  that line with room: `V = ½ × 60 × 9.1198² = 2,495 lb/ft`, `Vu = 1.6 × 2,495 = 3,992 lb/ft`
  against `0.5 φVc = 0.5 × 0.75 × 2√5,000 × 12 × 8.625 = 5,489 lb/ft`, a 27% margin.
  (An earlier revision printed `1.6 × 3,226` here and called the margin 6%. The 3,226 was
  `½ × 60 × 10.37²` — the stem height from *before* the footings rose — left behind when the
  rest of the section was re-worked. It never changed a verdict, and it is the exact kind of
  survival this note's term-by-term discipline exists to catch.) **0.528 clears both figures
  either way**, so the selection has never depended on which side of §11.6.2 the wall falls.
* **one-way shear** at the base: `φVc = 10,978 lb/ft` against `Vu = 3,992 lb/ft`,
  d/c 0.36 ✓.

**Authoring reinforcement makes the SECTION work. It does not make the DETAILING anything
this engine has looked at** — bar development into the footing, the corner cold joints, the
splice at the top of the pour. Those are the engineer's, and §9 says so.

---

## 7. The footing — the OTHER limit state nothing had computed

§6 found that the stem was a cantilever nobody had sized. **The footing is the same
omission, one member down, and it is worse.** §4 computes the bearing pressure under the
strip and then stops: that is a stability analysis of a rigid body, and it never asks
whether the concrete in the strip can carry the pressure it just computed. A **4'-0" toe**
under 899 psf is a flexural cantilever every bit as real as the stem, and it was
unreinforced.

Added to `engineering/retaining_basis.py::footing_states` on 2026-09-03. Same case as §4
and §6 throughout — **at-rest, 110 pcf**, because grading the footing on a different load
case from the stem it holds up would be two designs of one wall. And the same mix: f'c
**5,000 psi**, `EXPOSED_MIX` (§3), so `√f'c = 70.711`.

### 7a. The pressure diagram

From §4's governing case: `W = 5,577.5 plf`, `B = 8.000'`, `e = 0.3865'`.

```
W/B                    = 5,577.5 / 8         =   697.19 psf
6e/B                   = 6 x 0.3865 / 8      =    0.28990
q_toe  = W/B (1 + 6e/B) = 697.19 x 1.28990   =   899.3 psf     (at the toe TIP)
q_heel = W/B (1 - 6e/B) = 697.19 x 0.71010   =   495.1 psf     (at the heel end)
slope                   = (899.3 - 495.1)/8   =    50.53 psf/ft
q at the stem face (x = 4.000' from the tip) =   899.3 - 202.1 =   697.2 psf
```

The trapezoid keeps flattening — `e` has now gone 0.87' → 0.57' → 0.447' → **0.387'** across
the three height cuts, dropping the toe pressure another 5% while the heel pressure rose
another 5%. That is the resultant walking back toward mid-base, and it is the single most
useful consequence of shortening this wall: the toe cantilever is what governs the footing,
and its load is falling faster than the stem's.

**q at the stem face lands on `W/B` exactly, and that is a check rather than a coincidence.**
The stem face sits at 4.000' on an 8.000' base — mid-base — where a linear pressure diagram
equals its own mean whatever `e` is. If those two figures ever disagree, the trapezoid has
been mis-assembled.

### 7b. Toe flexure — the governing number, and a deliberate conservatism

The critical section is the **face of the stem** (ACI 318-19 §13.2.7.1(a), a concrete wall).
The toe is designed for the **upward pressure alone**: the footing's own 150 psf pushes down
and relieves it, and is dropped. That is not laziness — keeping it means factoring a
*relieving* dead load, which ASCE 7-16 §2.3.1 takes at 0.9 and this module has no
combination machinery for. Taken properly — `1.6 x M_pressure - 0.9 x M_concrete` — the
factored demand would be about **10% lighter**. It costs 10% and it costs no argument at
all.

The figure GROWS as the wall gets shorter, which is worth expecting rather than being
surprised by: the relief is the footing's own weight, which does not move, set against a
pressure that falls with the wall. It was 8% at the 36" cap.

```
rectangle   697.2 x 4.000              = 2,788.8 lb   arm 2.000'  =  5,577.5
triangle    ½(899.3 - 697.2) x 4.000   =   404.2 lb   arm 2.667'  =  1,077.9
                                            M service              =  6,655.4 ft-lb/ft
Mu = 1.6 x 6,655.4   (IBC §1605.2 on H, exactly as §6)              = 10,649   ft-lb/ft
```

**PLAIN, ACI 318-19 §14.5.2.1(a).** And note `h` is **10", not 12"**: §14.5.1.7 takes 2" off
a plain footing cast against soil, the Code's allowance for an unformed bottom face poured
into a trench. Capacity goes as `h²`, so skipping that overstates the section by 44%.

```
Sm  = 12 x 10²/6                              = 200 in³/ft
φMn = 0.60 x 5√5,000 x 200 / 12               = 3,536 ft-lb/ft     d/c = 3.01   ✗
```

**Three times over.** ACI §14.1.4 does permit a plain concrete footing — unlike §14.1.5 for a
column — so unlike the stem in §6 this is not a section *outside* the Code. It is simply a
section that does not work. (It was **5.18** while the calculation read the presumptive
3,000 psi; stating the real mix bought 29% of capacity and did not come close to closing a
factor of five. Three height cuts have since taken it 3.38 → 3.13 → **3.01**, which is not
close either — and unlike §6's stem table, no row of this one has changed sides.)

### 7c. Heel flexure

The mirror image, and the standard conservatism: the heel is designed for the **downward**
soil column and concrete alone, with the upward bearing pressure under it dropped. The
heel's job is to hold a column of earth down, and the pressure that would help is exactly
the pressure that vanishes when the wall begins to rotate.

```
soil on heel   3.000 x  9.1198 x 110          = 3,009.5 lb   arm 1.500' = 4,514.3
concrete       3.000 x 1.000 x 150            =   450.0 lb   arm 1.500' =   675.0
                                                  M service             = 5,189.3 ft-lb/ft
Mu = 1.6 x 5,189.3                                                      = 8,303   ft-lb/ft
φMn (plain, as above)                         = 3,536 ft-lb/ft     d/c = 2.35   ✗
```

### 7d. One-way shear on the toe

```
PLAIN: critical section at h = 10" from the stem face (§14.5.5.2(a)),
       i.e. 3.167' from the tip.
q at 3.167'  =   899.3 -  50.53 x 3.167                        =   739.3 psf
V service    = ½(899.3 + 739.3) x 3.167                        = 2,594.4 lb/ft
Vu           = 1.6 x 2,594.4                                   = 4,151   lb/ft
φVn = 0.60 x (4/3)√5,000 x 12 x 10                             = 6,788   lb/ft
                                                                   d/c = 0.61  ✓
```

**And this one PASSES as plain — at 5,000 psi.** At the presumptive 3,000 it was over. It is
worth writing down which way that cuts: shear was never the binding question here, and a
reader who saw only the shear row change sides might conclude the mix fixed the footing. It
did not. **Flexure is still three times over**, and that is the row that decides whether this
footing needs steel.

### 7e. The steel, and why it is the stem's bar

`#6 @ 10" o.c.`, both faces, 3" cover. **Deliberately the same bar and spacing §6 selected
for the stem**: one bar size on this pour is one bundle to order, one bender's setup and one
thing for an inspector to count, and the toe does not need a different one.

3" is ACI 318-19 Table 20.5.1.3.1(a) — cast against and permanently in contact with ground —
which is the footing's actual condition and a full inch more than the stem's formed 2". It
is applied *before* sizing, not bolted onto a `d` derived against something looser.

```
As    = 0.44 x 12/10                                    =  0.528 in²/ft
d     = 12 - 3.000 - 0.750/2                            =  8.625 in
a     = 0.528 x 60,000 / (0.85 x 5,000 x 12)            =  0.621 in
φMn   = 0.90 x 0.528 x 60,000 x (8.625 - 0.311) / 12    = 19,755 ft-lb/ft

  toe flexure    10,649 / 19,755                                d/c = 0.54   ✓
  heel flexure    8,303 / 19,755                                d/c = 0.42   ✓
```

Shear re-runs on the reinforced section — critical at `d` rather than `h`, ACI §22.5.5.1,
`φ` 0.75 rather than 0.60:

```
cut at d = 8.625" from the face, i.e. 3.281' from the tip
q at 3.281'  =   899.3 -  50.53 x 3.281                        =   733.5 psf
Vu = 1.6 x ½(899.3 + 733.5) x 3.281                            = 4,286   lb/ft
φVc = 0.75 x 2√5,000 x 12 x 8.625                              = 10,978  lb/ft
                                                                   d/c = 0.39  ✓
```

`bottom-y` `#4 @ 18"` longitudinal distribution steel is authored alongside. It carries no
graded limit state here and is ordinary detailing practice for a strip footing.

### 7f. What this does NOT settle

The mat makes the **section** work. It does not make the **detailing** anything this engine
has looked at — development of the toe bars into and past the stem face, the hook at the toe
end, the corner mats where three footings meet, and the lap of the stem's own dowels into
this mat. §6 said the same thing about the stem and it is no less true here.

And the whole of §7 rests on §4's pressure diagram, which rests on the washed-stone bed
being built as specified. A softer bearing plane redistributes the trapezoid and every
number above moves with it.

---

## 8. The cross-member

`W-SG-ARCH` returns as a **buried grade beam** on the retired arch's own node pair, reusing
its uid. `a160812` retired a 16" cast cross-wall with two semicircular arches carrying a 42"
masonry parapet and three balcony pillars — "the heaviest and most expensive element of the
structure". **None of that comes back.** 12" × 17 1/2", 20'-0", entirely below the garden
floor, invisible, doing one job.

### Why a beam and not a floor strut

The garden slab is cheaper and does not work:

* **Sequence.** The beam is cast *with* the walls, so the loop is closed before any backfill.
  A slab strut leaves the walls standing as free cantilevers at **FS 0.73** until the floor
  cures — and **backfill is what loads them.** IRC Table R404.1.2(8) footnote g says the same
  thing about its own walls: *"laterally supported at the top and bottom **before**
  backfilling."* This is the single strongest objection to the whole propped scheme and the
  beam simply removes it.
* No control joints, no shrinkage gap to close before the strut bears, no bearing on the
  compressible FPSF wing foam, and no permanent "`SL-SG-FLOOR` can never be saw-cut".
* `SL-SG-FLOOR` is **untouched by the strut question** — the beam needs nothing from it.

  It has since moved twice for unrelated reasons — dropped 7 1/4" on 2026-09-03 so heavy
  rain would pond outside `D-B-PATIO` rather than cross its threshold, and put back flush on
  2026-09-05 — and the floor is now a 3 1/2" **rim** around a 147 sf gravel-and-turf field.
  **None of this note's arithmetic moves with any of that.** The free body is bounded by the
  wall tops and the footing undersides; `_ret_unbalanced_fill` is `_ret_top − _wall_bottom`
  and the low side has never entered the retaining calculation at all (`toe_embedment_ft` is
  hardcoded 0.0). The court's own elevation only ever adds or removes toe overburden the
  model does not credit either way. **What DID move this note is the two ends themselves**
  — the footing tops rising to the court plane and the wall tops falling to the 36" cap —
  and those are worked through §4 term by term.

  The one thing that *would* have changed the strut is shrinking its section, and the court
  floor tried twice — once by holding the beam's TOP against a dropped floor (a 10 1/4"
  section), once by raising its BOTTOM with the retaining footings on 2026-09-05 (8 1/2").

  **⚠ BOTH OF THOSE SECTIONS NOW PASS, AND THIS PARAGRAPH USED TO REJECT THEM BECAUSE THEY
  FAILED. READ ON BEFORE SHRINKING THIS BEAM.** They failed at the thrust of their day —
  10 1/4" at d/c 1.02 against Pu 62,051 lb, 8 1/2" at d/c ~1.01 against Pu 50,789 lb — and
  three height cuts have since taken the demand to **Pu 49,157 lb**, where the arithmetic
  reads:

```
  12" x 17 1/2"   Ag 210 in²   φPn 103,655 lb    d/c 0.47   ✓  as built
  12" x 10 1/4"   Ag 123 in²   φPn  60,712 lb    d/c 0.81   ✓  passes now
  12" x  8 1/2"   Ag 102 in²   φPn  50,347 lb    d/c 0.98   ✓  passes now, by 2%
```

  **The section is held, and it is no longer held on the strength ratio.** Three reasons,
  in the order they bind:

  1. **Sequencing, which is what the whole of §8 rests on.** This beam exists so the loop is
     closed *before backfill*, and its depth is what decouples it from everything that moves
     above it: `_grade_beam_bottom` is HELD at −10'-10 7/16" while the five wall footings
     rose to −10'-1 7/16", so a change to the court floor or to the footing plane cannot
     reach down and thin this member. Re-tying its bottom to either surface is what both
     shallower sections *were* — they were never chosen depths, they were the gap left over
     between two other things, and a strut whose section is a residue gets shaved again the
     next time something above it moves.
  2. **2% is not a margin on the only member with no redundancy.** The 8 1/2" section is the
     entire lateral restraint of a closed loop, and its demand is `0.5 × resultant` with no
     friction credit — an assumption this section itself calls conservative-by-construction
     rather than derived. λ is applied on the 20'-0" clear span and the 12" dimension, and φ
     is the plain-concrete 0.60. Any of those could move a few percent on review.
  3. **The saving is not real.** 87 in² of concrete over 20 feet is about 1.1 CY. The 9"
     step in the dig this depth creates is the genuine cost, and it is being paid down from
     the other end — the beam's *bedding undercut* is what gets trimmed to the wall-bed
     plane, not the beam.

  The 12" × 17 1/2" section this note grades is therefore the one that gets built. The beam
  stands 9" proud below the retaining footings' undersides, which is deliberate and is what
  `test_retaining_court` asserts.

### The strut check

Force: **half the largest member's whole thrust, with no friction credit.** A wall tied at
both ends delivers about half its thrust to each end; netting base friction off first would
spend that friction twice, once here and once in §4's sliding row. Taking the *largest*
member (the south wall, which the strut does not directly tie) rather than a side wall is
conservative by 9% — 30,723 lb against 28,163 lb — and keeps the check from having to know
which walls face each other.

```
P     = 0.5 × 61,446                                     = 30,723 lb  (service)
Pu    = 1.6 × 30,723                                     = 49,157 lb
Ag    = 12 × 17.5                                        =    210 in²
λ     = 1 − (240 / (32 × 12))²                           =  0.609
φPn   = 0.60 × 0.45 × 3,000 × 210 × 0.609                = 103,655 lb   d/c 0.47  ✓
```

ACI 318-19 §14.5.4 (§22.6.5.2 in 318-11). **Note the section number**: §14.5.6 is *bearing*
and carries 0.85 rather than 0.45 — using it here would nearly double the allowable, and it
is the wrong provision. Plain concrete **is** in scope for this member, unlike the stem:
R22.6.3 excludes only walls free to translate at top and bottom, and a strut cast into a
closed loop confined by compacted stone on every face is the opposite case.

The slenderness bracket is applied on the **full 20'-0" clear span** and on the member's
12" dimension, even though the beam is buried in compacted stone on all four faces and is
braced far better than that. It clears anyway, so the conservative reading is free.

### On the front column's bell — checked, and it does NOT merge

An earlier scheme proposed merging `FT-SG-FCOL`'s 36" bell into the beam at midspan, on the
grounds that its south edge lands on the beam line. **In plan that is true and in section it
is not:**

```
FT-SG-FCOL   bell     z  -151.44"  to  -139.44"
W-SG-ARCH    beam     z  -130.44"  to  -112.94"
                              -------------------
                              9" of clear ground between them
```

The bell bottoms 1'-9" deeper and its top is 9" **below** the beam's underside. They do not
touch, there is no shared pour, and the beam gets **no intermediate bearing** — which is why
the slenderness above is computed on the full 20'-0" and not on 2 × 10'-0". The column
*shaft* passes nearest: its south face at y = −10.33' against the beam's north face at
y = −10.50', **2" clear.** Tight, buildable, and worth drawing.

### Frost, and what the beam does and does not need

No `Footing`: the beam carries 219 plf over its own 12" of bearing — **219 psf against 3,000
allowable** — so a strip under it would be concrete spent on nothing.
`FootingBedding.host_ref` takes a `FoundationWall` directly (the five `W-RG-*` beds are the
precedent), and `structural.frost_depth` iterates footing and pad *solids*, so a
`FT-SG-ARCH` would land inside the excavation and reopen the frost question ASCE 32 soil
replacement closed on 2026-08-29.

`FB-SG-ARCH` therefore carries the same 42" undercut, the same NFS claim about the same
stone, and the same 4" sock-wrapped tile to `DRW-SG-MAIN`.

**The excavation no longer has one bottom, and that is the price of §8's held section.** The
beam's underside stays at −10'-10 7/16" while all five wall footings rose to −10'-1 7/16";
`FB-SG-ARCH` therefore bottoms at −14'-4 7/16" and every wall bed at −13'-7 7/16", a 9" step
in the dig along the beam line. **The well follows the WALL beds, not the deepest one.** It
was pinned to the deepest for as long as they were all one plane, and staying pinned there
through the lift left the five tiles that actually feed it discharging 9" above its top of
stone — a gravity break that `drainage.discharge_consistency` cannot see, because it resolves
the tag and never asks where the pipe goes. `_SG_DRYWELL_TOP` is `_SG_WALL_BED_BOTTOM` now,
the two lead runs `FD-SG-LEAD-W/E` carry the ring into it at that invert, and `FB-SG-ARCH`
feeds the column through its side 9" further down instead of standing on it.

---

## 9. What this note does NOT do

Inherited from `sunken_garden_retaining_screening.md` §5, all still open, plus what this pass
added:

- **No drainage or hydrostatic case.** Every number presumes the drainage behind these walls
  works perfectly and no water pressure ever develops. A saturated backfill roughly doubles
  the thrust and would take the system well under 1.0.
- **No seismic.** Minnesota is SDC A and soil and wind govern, but that is asserted here, not
  demonstrated, and no Mononobe-Okabe increment is applied.
- **No global stability, no settlement.** A 10'-4" retained cut next to a tiered apron has a
  slip-circle question this note does not open.
- **No compaction surcharge** behind the placed apron terrace, and no construction traffic.
- **No verification of the soil class.** GM comes from a soil survey for the **wrong county**.
- **Corner bar development is not checked.** The loop's corners are cold joints between
  separate pours. With the steel of §6 and dowelled corners this is ordinary practice — and
  the cancellation of §1 *depends* on those corners, so "ordinary practice" is doing real
  work in this note and nobody has drawn it.
- **No two-way action.** §4 grades overturning, bearing and eccentricity on each wall's
  **isolated** free body, which is conservative twice over: it neglects the strut's own
  restoring moment, and it neglects the horizontal spanning that carries much of the thrust
  to the corners of an 18'-4" wall tied at both ends. Both would help. Neither is claimed.
- **The apron is itself documented as defective** (`params/raised_garden.py`: negative base-
  course embedment) and it is what creates the terrace these
  walls retain. The two are **one coupled tiered system** and fixing either in isolation is
  guesswork.
- **MN Rules 1309.0402 amends IRC Table R402.2 and adds a FOOTINGS row at 5,000 psi**
  (footnote g allows 2,500 with an approved water/vapour-resistance admixture; footnote h
  exempts deck/porch post footings, wood foundations and floating slabs — none of which is a
  retaining-wall strip footing). **ANSWERED 2026-09-03, and the model can now say so.**
  `ConcreteSpec` gives a pour somewhere to state its mix, `BURIED_MIX` states
  5,000 psi at w/cm 0.40 for every strip footing, and `stem_flexure` reads it instead of the
  presumptive 3,000. What is *not* yet changed is the arithmetic in this note: f'c below is
  still the 3,000 psi the wall row requires, which is the safe direction for a stem and is
  re-oracled when the wall assemblies take a spec of their own.

---

## 10. What a reviewer must still be told

Even at 0 FAIL these walls are **screened, not designed**, and the items stay unsealed:
presumptive values only, no geotechnical report, a soil class from a survey for the wrong
county, an unbounded 110–130 pcf band, no hydrostatic case, no seismic, no global stability,
no settlement, no compaction surcharge, corner bar development nobody has checked, and **a
design that depends on the stone bed being built as specified — 1.29 without it.**

**1.80 against 1.50 is a screening that clears. It is not a stamp.**

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ACI 318-19** — Table 20.5.1.3.1, Table 22.2.2.4.3, §11.6.1, §13.2.7.1, §14.5.2.1, §14.5.4
- **ASCE 7-16** — §2.3.1
- ASTM A767, ASTM A780, ASTM C33, ASTM D422
- IBC Table 1610.1, IBC Table 1806.2
- IRC R404.4, IRC Table R301.2(1, IRC Table R402.2, IRC Table R404.1.2(8
- MN Rules 1309.0301, MN Rules 1309.0402
