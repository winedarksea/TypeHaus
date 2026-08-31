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
> 1.58 against 1.50 is a screening that clears. It is not a design and it is not a seal**, and
> `FoundationWall.engineering_spec` stays unset for the reason the screening note's §6 gives.

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Written:** 2026-08-30, by hand, before the calculation it oracles was encoded.
**Oracles:** `engineering/retaining_system.py` and `engineering/retaining_basis.py`;
reproduced by `tests/test_retaining_court.py`.
**Companions:** `notes/sunken_garden_retaining_screening.md` (the isolated-wall case, still
correct on its own terms), `notes/balcony_lateral_bracing_design.md` (the structure standing
on these walls).

---

## 0. The convention question, worked both ways, with a stated choice

The screening note and the engine both read `-9'-10 7/16"` as the **underside** of the
footing. It is the **top**. `resolve/envelope.py::_resolve_footing` resolves a wall-hosted
footing at `z1 = wall.z0_m`, so the footing hangs entirely below the wall:

```
W-SG-E2     z0  -118.4375"      z1   +6.0000"     (the wall)
FT-SG-E2    z0  -130.4375"      z1  -118.4375"    (the footing, entirely below it)
```

Two different heights were being conflated, and the choice matters because they differ by a
whole footing depth:

| quantity | value | what it is for |
|---|---|---|
| `unbalanced_fill` | **10.37'** | the **IRC** quantity — fill against the wall, to the wall's base. R404.1.1's 48" threshold and Table R404.1.2(8)'s rows are read against it. **Correct as authored; nothing in `params/` moves.** |
| `H` for stability | **11.37'** | top of retained soil to the **underside of the footing**. Soil bears on the back of the heel as well as the back of the stem, and the plane being slid along is the footing's underside. |
| stem height | **10.37'** | what stands above the footing — the concrete's own weight, the soil column on the heel, and the flexural cantilever in §6. |

**Worked the other way,** for the record: if `-9'-10 7/16"` really were the footing underside,
the stem would be 9.37' and `H` 10.37', giving a thrust of `½ × 60 × 10.37² = 3,226 plf`
instead of 3,878 — 17% light — while also under-counting the stem's own dead weight and the
soil on the heel by a foot each. The two errors are in opposite directions and **do not
cancel**: the old engine reported W-SG-E2 at FS 0.80 where the corrected convention gives
0.73.

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
   +0'-6"   ============  top of wall = top of the terrace the apron holds
            |          |
            | 12" stem |   <-- soil, 10'-4 7/16" of it, pushing this way
   terrace  |          |
   at +0'-6"|          |
            |          |
  -9'-10 7/16"  +------+----------+    <-- footing TOP = wall bottom
                | 3'-0" |  1'-0"  |  4'-0"      8'-0" x 1'-0" strip
                |  heel |  stem   |  toe        offset 6" INTO the court
  -10'-10 7/16" +-------+---------+
                |  42" of ASTM C33 #57 washed crushed stone  |
                |  (FB-SG-*, non_frost_susceptible, tiled)   |
  -14'-4 7/16"  +--------------------------------------------+
```

**The one thing this drawing says that the old one did not:** `W-SG-W2` and `W-SG-E2` are
the same wall mirrored about x = 18'-0". Same 12" section, same top (+0'-6"), same bottom
(−9'-10 7/16"), same 18'-4" length, same footing. Their thrusts are **equal and opposite**,
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
| soil class | GM (silty gravel) | MN profile — **and it is a *Hennepin* soil survey for a *Ramsey* parcel** |
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
| stem | 12" cast concrete, **10'-4 7/16"** above the footing |
| footing | **8'-0" wide × 1'-0" deep**, offset **6" toward the court** — toe 4'-0", heel 3'-0" |
| `H`, top of soil to footing underside | **11.3698'** |
| retained face | outboard, terrace at +0'-6" (the raised garden's apron holds it) |
| resisting face | inboard, court floor at −9'-1 7/16"; toe buried 6 1/2" |
| cross-member | `W-SG-ARCH`, 12" × 17 1/2", 20'-0" clear, buried |
| reinforcement | **`#6 @ 10" o.c.` vertical, retained face**, 2" cover — sized in §6 |

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
P        = ½ × 60 × 11.3698²                      = 3,878.2 plf
W_stem   = 1.0  × 10.3698 × 150                   = 1,555.5 plf
W_ftg    = 8.0  ×  1.0    × 150                   = 1,200.0 plf
W_heel   = 3.0  × 10.3698 × 110                   = 3,422.0 plf
W                                                 = 6,177.5 plf
F        = 0.35 × 6,177.5                         = 2,162.1 plf

M_ot     = 3,878.2 × 11.3698/3                    = 14,698   ft-lb/ft
M_r      = 1,200×4.0 + 1,555.5×4.5 + 3,422.0×6.5  = 34,043   ft-lb/ft
x̄        = (34,043 − 14,698)/6,177.5              = 3.132 ft
e        = 4.000 − 3.132                          = 0.869 ft   (kern B/6 = 1.333 ft) ✓
q_max    = 6,177.5/8 × (1 + 6×0.869/8)            = 1,275 psf  (allow 3,000)          ✓
FS_ot    = 34,043 / 14,698                        = 2.32       (need 1.50)            ✓

SYSTEM
  total thrust  = 3,878.2 × (18.333 + 18.333 + 20.0) = 219,763 lb
  resultant     = 3,878.2 × 20.0                     =  77,563 lb   (E-W cancels exactly)
  cancelled                                          = 142,199 lb
  capacity      = 2,162.1 × 56.667                   = 122,520 lb
  FS_sliding    = 122,520 / 77,563                   = 1.58       (need 1.50)         ✓
```

### All four corners of (active, at-rest) × (110, 130 pcf)

| case | system FS | FS overturning | e / kern | q_max |
|---|---|---|---|---|
| **at-rest 60, 110 pcf — GRADED** | **1.58** ✓ | **2.32** ✓ | **0.869 / 1.333** ✓ | **1,275** ✓ |
| at-rest 60, 130 pcf | 1.74 ✓ | 2.59 ✓ | 0.560 / 1.333 ✓ | 1,207 ✓ |
| active 45, 110 pcf | 2.11 ✓ | 3.09 ✓ | 0.274 / 1.333 ✓ | 931 ✓ |
| active 45, 130 pcf | 2.32 ✓ | 3.45 ✓ | 0.070 / 1.333 ✓ | 887 ✓ |
| required | 1.50 | 1.50 | within B/6 | ≤ 3,000 |

**The graded row is the worst of the four.** Both ends of the soil band agree on the verdict,
so the answer does not turn on the one input no code table publishes — which is exactly the
condition under which `retaining_basis` is willing to report a verdict at all.

### Why at-rest, and the deflection that settles it

**You cannot cite a permanent base restraint in the resistance term and simultaneously claim
the walls are free enough to shed to the active wedge in the demand term.** Crediting the
restraint concedes the point. Worked, as a base-restrained top-free cantilever under the
triangular at-rest load:

```
w₀ = 60 × 10.3698 / 12                = 51.85 lb/in per 12" of wall
E  = 57,000 √3,000                    = 3,122,000 psi
Ig = 12 × 12³/12                      = 1,728 in⁴
δ  = w₀ L⁴ / (30 E I)  ,  L = 124.44"

   uncracked, I = Ig          δ = 0.077"  =  0.00056 H
   cracked,   I ≈ 0.35 Ig     δ = 0.219"  =  0.00161 H
```

Against Clough & Duncan (1991), as **AASHTO LRFD Table C3.11.1-1** and Caltrans *Trenching
and Shoring Manual* Table 4-1 — dense sand **0.001H**, medium dense 0.002H, loose 0.004H.
(Do **not** cite NAVFAC DM 7.02 for these; its figures are 0.0005/0.002, roughly half, and
citing the friendlier source for the number you want is how a screening stops being one.)

The honest reading: **the answer straddles the threshold.** Uncracked the wall does not move
enough to mobilise the active state at all; cracked it barely reaches the dense-sand figure.
Active is *arguable*. At-rest is *defensible*, and it costs 1.58 instead of 2.11 — margin
this design can afford. **Active is the sensitivity, not the design.**

---

## 5. ⚠ The corner that does not clear, and what the design therefore depends on

**Without the washed-stone bed, at μ = 0.25 throughout, the system reaches FS 1.13 against
the 1.50 required.**

```
capacity = 0.25 × 6,177.5 × 56.667  =  87,514 lb
FS       = 87,514 / 77,563          =  1.13     ✗
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
> the court is at 1.13 and does not meet IRC R404.4. Inspect and document the bed at
> placement. It is not an incidental levelling course; it is the reason the walls stand.

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

Cantilever from the top of the footing, at-rest, stem 10.3698':

```
M   = ½ × 60 × 10.3698² × 10.3698/3       = 11,151 ft-lb/ft   (service)
Mu  = 1.6 × 11,151                        = 17,841 ft-lb/ft   (IBC §1605.2 on H)
S   = 12 × 12²/6                          = 288 in³/ft
f   = 11,151 × 12 / 288                   = 465 psi           (service flexural tension)
```

**Plain**, ACI 318 §14.5.2, φ = 0.60 (Table 21.2.1):

```
φMn = 0.60 × 5√3,000 × 288 / 12           = 3,944 ft-lb/ft    d/c = 4.52   ✗
```

**And "4.52 over" understates it.** ACI 318 R22.6.3 says the plain-concrete wall provisions
apply *"only for walls laterally supported in such a manner as to prohibit relative lateral
displacement at top and bottom"*, and that the Code *"does not cover walls without horizontal
support … Such laterally unsupported walls are to be designed as reinforced concrete
members."* A retaining wall is unsupported at the top by definition — the same condition that
trips R404.4. **An unreinforced stem here is not a section that fails a check; it is a section
outside the Code.**

**Reinforced**, ACI 318 §22.3, φ = 0.90. Steel on the **retained** face — that is where the
cantilever puts the tension, and putting it on the wrong face is the classic way a correctly
sized wall falls over. Cover 2" (ACI Table 20.5.1.3.1, earth and weather, #6 and larger;
also IRC Table R404.1.2(8) footnote i's outside-face figure for bars larger than #5):

| schedule | Aₛ in²/ft | d in | a in | φMn ft-lb/ft | d/c | |
|---|---|---|---|---|---|---|
| `#6 @ 16"` | 0.330 | 9.625 | 0.647 | 13,813 | 1.29 | ✗ |
| `#5 @ 10"` | 0.372 | 9.688 | 0.729 | 15,606 | 1.14 | ✗ |
| `#6 @ 12"` | 0.440 | 9.625 | 0.863 | 18,203 | 0.98 | ✓ but 2% |
| **`#6 @ 10"`** | **0.528** | **9.625** | **1.035** | **21,639** | **0.82** | **✓ selected** |
| `#6 @ 8"` | 0.660 | 9.625 | 1.294 | 26,664 | 0.67 | ✓ more than needed |

`#6 @ 12"` is the arithmetic minimum and 2% is not a margin for a screening on presumptive
values. `#6 @ 8"` buys nothing this design needs. **`#6 @ 10" o.c.` is the selection.**

Checked alongside:

* **tension-controlled**, so φ = 0.90 is the right factor: `c = a/0.85 = 1.22"`,
  `εt = 0.003 (9.625 − 1.22)/1.22 = 0.0207`, far past 0.005.
* **minimum reinforcement**, ACI 318-19 §11.6.1: ρl ≥ 0.0015 for bars larger than #5 →
  0.216 in²/ft. And §11.6.2 raises it to 0.0025 → 0.360 in²/ft where `Vu > 0.5 φVc`, which
  this wall is: `Vu = 1.6 × 3,226 = 5,162 lb/ft` against `0.5 φVc = 0.5 × 0.75 × 2√3,000 ×
  12 × 9.625 = 4,745 lb/ft`. **0.528 clears the stricter figure.**
* **one-way shear** at the base: `φVc = 9,489 lb/ft` against `Vu = 5,162 lb/ft`, d/c 0.54 ✓.

**Authoring reinforcement makes the SECTION work. It does not make the DETAILING anything
this engine has looked at** — bar development into the footing, the corner cold joints, the
splice at the top of the pour. Those are the engineer's, and §8 says so.

---

## 7. The cross-member

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
* `SL-SG-FLOOR` is **untouched** — same 3 1/2", same assembly-less open excavation floor,
  same −9'-1 7/16" datum for eleven footings and for the 7 1/4" flood curb at `W-B-S2`/`S3`.

### The strut check

Force: **half the largest member's whole thrust, with no friction credit.** A wall tied at
both ends delivers about half its thrust to each end; netting base friction off first would
spend that friction twice, once here and once in §4's sliding row. Taking the *largest*
member (the south wall, which the strut does not directly tie) rather than a side wall is
conservative by 9% — 38,782 lb against 35,550 lb — and keeps the check from having to know
which walls face each other.

```
P     = 0.5 × 77,563                                     = 38,782 lb  (service)
Pu    = 1.6 × 38,782                                     = 62,051 lb
Ag    = 12 × 17.5                                        =    210 in²
λ     = 1 − (240 / (32 × 12))²                           =  0.609
φPn   = 0.60 × 0.45 × 3,000 × 210 × 0.609                = 103,655 lb   d/c 0.60  ✓
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
stone, and the same 4" sock-wrapped tile to `DRW-SG-MAIN`. The beam's underside is flush with
the retaining footings' at −10'-10 7/16", so the excavation has **one bottom** and the well's
top — derived from the wall beds' underside — already sits on that plane.

---

## 8. What this note does NOT do

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
  course embedment since grade moved on 2026-08-21) and it is what creates the terrace these
  walls retain. The two are **one coupled tiered system** and fixing either in isolation is
  guesswork.
- **MN Rules 1309.0402 amends IRC Table R402.2 and adds a FOOTINGS row at 5,000 psi**
  (footnote g allows 2,500 with an approved water/vapour-resistance admixture; footnote h
  exempts deck/porch post footings, wood foundations and floating slabs — none of which is a
  retaining-wall strip footing). Nothing in this model states a mix design, and f'c above is
  the 3,000 psi the *wall* row requires. **The footing pours want checking against that
  amendment before anyone orders concrete.**

---

## 9. What a reviewer must still be told

Even at 0 FAIL these walls are **screened, not designed**, and the items stay unsealed:
presumptive values only, no geotechnical report, a soil class from a survey for the wrong
county, an unbounded 110–130 pcf band, no hydrostatic case, no seismic, no global stability,
no settlement, no compaction surcharge, corner bar development nobody has checked, and **a
design that depends on the stone bed being built as specified — 1.13 without it.**

**1.58 against 1.50 is a screening that clears. It is not a stamp.**
