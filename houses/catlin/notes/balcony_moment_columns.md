# The balcony's four moment columns — engineering basis for an engineer's review and stamp

**House:** catlin, Ramsey County, Minnesota (Minnesota Residential Code 2020, adopting the
2018 IRC).
**Structure:** the sunken garden's balcony — a 21'-6" × 9'-8" deck at +10'-0" (+9'-9" since
2026-09-23, §15), carried on
**four 12" round reinforced-concrete columns fixed at the base** (PT-SG-BR1, PT-SG-BR3,
PT-SG-BF1, PT-SG-BF3) and two 6x6 wood centre pillars bearing on the porch framing under
pinned strap-and-angle base ties, under three treated structural-glulam beams.
**Written:** 2026-09-03. It **supersedes `superseded/balcony_lateral_bracing_design.md`**, which
designed the eight knee braces and two brace rails this replaced.
**Oracle for:** `engineering/deck_post.py`'s moment-column branch and, at §5,
`engineering/glulam_beam.py`; reproduced by `tests/test_pier_section_calcs.py`. At §11,
`engineering/column_support.py`, reproduced by `tests/test_column_support_calc.py`.
**Companions:** `notes/centre_pillar_bearing.md` (the two wood pillars among these six),
`notes/sunken_garden_piers.md` (where this load goes next).
**What is asked of the reviewer:** this is a screening design under IRC R301.1.3 engineered
design. It is offered for a licensed engineer's check and stamp. It is **not** a stamped
design, and nothing in the model treats it as one: `haus engineering` reports these items as
`draft` — this engine's own calculation checks out — and `sealed` stays unset until
`engineering.toml` carries a stamp.
**What this note is FOR.** Every number below is worked here from first principles with the
arithmetic shown, and `engineering/deck_post.py` and `engineering/glulam_beam.py` are then
checked against it. A calculation that only agrees with itself is not verified. Where the
hand working and the engine differ, the difference is stated (§4a).

---

## 0. Why the braces went, and why this is not just "the same deck with fatter posts"

`superseded/balcony_lateral_bracing_design.md` opened by saying the balcony has no shear walls: six
posts on `ABU66SS` standoff bases, and Simpson's own reports (ESR-1622, ESR-3050) say a
standoff base *"does not provide adequate resistance to prevent members from rotating about
the base."* Both the bases and the beam bearings were pins. Eight 2x6 knee braces were the
entire lateral system, and **every one of their joints came back UNKNOWN** — the E-W feet
were lapped bolt groups with no product rating at all.

The owner asked for a more durable structure for a hundred-year freeze-thaw exposure, the
clean open look kept, and off-the-shelf parts. Three routes were priced:

| route | why it lost / won |
| --- | --- |
| **Catalog metal moment base under the wood posts** | **No stock base publishes a base moment.** The only one that does is Simpson's MPB66Z, for a WOOD post — and it needs 5" side cover (about 16" of concrete, cast in) and its wet-service cap is 2,610 lb-ft (ESR-3050 Table A), **below the guard case in §3 below**. It cannot go in a 12" round or on a 12" wall top as published. Foreclosed, not deferred. |
| **Stock HDG steel tube columns** | New Castle Steel's 6x6x3/16" with a welded base plate, ~$458 per 10'. Kept as the written **fallback** if forming and caging four tall tubes proves too much labour. Its base still needs a fabricated saddle on a 12" wall top, which is a shop drawing this note does not carry. |
| **Reinforced concrete columns** ✅ | The one braceless design built entirely from catalog parts: a Sonotube, a stock cage, dowels into the wall it stands on. The house already carries the beam-on-concrete detail at PT-SG-COL and PT-SG-FCOL, and the engine already grades cast columns. |

**The lateral system is now the four corner columns' own base fixity.** The two centre
pillars stay wood and stay leaning columns, tied in by the deck diaphragm — the same claim
the old note made about them, and the same one that stays unproven here.

---

## 1. Geometry, and where every dimension comes from

Read off `params/sunken_garden.py` rather than restated:

(Figures as of 2026-09-03; the deck is 3" lower since 2026-09-23 — §15.)

```
deck walking surface            +10'-1 1/2"  (balcony_level_ft + 1 1/2" plank)
beam soffit / column top          9'-0 1/8"  = 10' − 11 7/8" glulam depth
corner column base                0'-0"      = the porch top, W-SG-W1/E1's 12" wall tops
column unbraced length lu         9'-0 1/8"  = 108.125"
guard top                       +13'-7 1/2"  = walking surface + 42"
sunken garden floor               −9'-0"     — the ground this structure stands over
appurtenance height h            23.0'       = guard top − garden floor
column diameter                    12"       round; A_g = π·6² = 113.10 in²
```

**Why 12" and not 10".** Cover. ACI 318-19 §20.5.1.3's 1-1/2" is a code minimum, not a
hundred-year number — MnDOT uses 2.5"-3" in the same deicing regime. Two inches of cover on
a #5 vertical inside a #3 tie puts the bar circle at

```
bar-circle radius = 6" − 2" cover − 0.375" tie − 0.625"/2 bar = 3.3125"   (Ø 6 5/8")
```

which needs a 12" round to hold. (3" was asked for on 2026-09-23 and is refused by the
north-entry pad dowels' spacing, §14.) 12" also drops the slenderness ratio and gives the beam
seat its edge distance for free: an HGAM10's Titen Turbo lands ~3-3/4" from the face where a
10" round would leave 2-3/4", against Simpson's 1-1/2" minimum. And centred on the 12" wall
axis the round is **flush with both wall faces** — no ledge to pond on, and BF3's 3" east
leader keeps 1-1/2" clear. The extra concrete over four columns is about 0.3 cy.

---

## 2. Loads

### 2a. Gravity

IRC R507.1 / Table R301.5: **40 psf live + 10 psf dead = 50 psf.**

**Beam-weighted since 2026-09-03, not an even six-way split.** It was `207.83 ft² / 6 posts
= 34.64 ft² each`, which reads fair and is not: `BM-SG-BLC` runs the deck's full depth onto
`PT-SG-BR2` and `PT-SG-BF2` alone, while `BM-SG-BLW` and `BM-SG-BLE` share four. The rule
now gives each beam its own strip — the 10'-0" joist span it carries, the same width §5 puts
under its 500 plf — times its own 9'-8" length, halved between the two posts it lands on:

```
each beam:   10.00' strip × 9.667' length × 50 psf  =  4,833 lb
per post:    4,833 / 2                              =  2,417 lb   (48.33 ft²)

live   40 × 48.33 =  1,933 lb
dead   10 × 48.33 + column self weight  =  1,564 lb
factored (1.2D + 1.6L, ASCE 7-16 §2.3.1)  =  4,970 lb
```

Every post here is on a two-post beam, so the four corners and the two centres come out the
same 48.33 ft² — but they arrive at it for a reason rather than by division, and the two
CENTRE pillars are where it mattered. Their real reactions are **not** equal: `BM-SG-BLC`
overhangs 20" north of BR2 and 12" south of BF2, which levers 2,647 lb onto the rear pillar
and 2,187 onto the front one. §5 of `notes/centre_pillar_bearing.md` works that split and
grades the cross-grain bearing it lands on.

**21'-6", not 21'-0", since 2026-09-03.** `joist_cantilever_in` went 6" → 9" so the plank
and TR-SG-FASCIA's drip would clear the outer faces of the 12" rounds instead of landing on
them, and 3" per side is the smallest step that keeps the deck width divisible by the
AridDek main board's 6" (43 whole boards, no rip). Nothing changed size for it: these columns
run at d/c 0.02 in axial. Note that the beam-weighted rule above no longer reads the deck's
plan area at all, so a width change reaches these posts only through the beams' own lengths.
**The one place a balcony load increase is not free is `PT-SG-COL`'s 30" bell** — the
centre pillars hand their share down to it and it is at d/c 0.83 in bearing
(`notes/sunken_garden_piers.md` §3c).

**No equipment dead load.** The two Gree condensers (330 lb the pair) left this deck on
2026-09-02 for a poured pad in the yard pocket east of the porch — see
`heat_pump_ground_pad.md`. They were negligible on a 200-odd ft² deck before that, so no member
changed when they went; what changed is that `FS-SG-DECK`'s aluminium plank now carries
**zero penetrations**, which is what keeps RL-SG-BALCONY on fascia brackets (§7).

### 2b. Wind — ASCE 7-16 §29.3, on the same basis as the superseded note

`plan/site.py`, from **MN Rules 1309.0301**: V_ult 115 mph statewide, Exposure B, Risk
Category II. Height is measured from the **sunken garden court surface**, the ground actually
beneath this structure, not from the site grade nine feet higher — the conservative reading
and the physical one.

**That ground has now moved twice, and on 2026-09-05 it came back up.**
`balcony_wind.ground_below_ft` takes the lowest of the site's spot elevations, and the two
over the court govern it. They read -9'-4" (stale by 1 7/16") until 2026-09-03, then
-9'-8 11/16" when the court fell 7 1/4" for the flood step at `D-B-PATIO`, and now
**-9'-1 7/16"**: `court_step_down_in` went back to 0 and the court is flush with the
basement floor plane again, so the whole court is one surface with a single riser at the
door. `h` fell 23.3' -> **22.7'**, `K_z` with it, and q_h 18.8 -> **18.6 psf**.

A *lower* floor is a *taller* structure, so this last move is the SAFE direction — the
demand fell about 1% and no column is re-sized by it. It is written down anyway, because
the failure this figure is exposed to is not a wrong number but a stale one: these spot
elevations are *drafting annotation everywhere else on this site*, and `plan/site.py`
carried a comment asserting exactly that until this edit. They are a structural input here
and nowhere else, which is precisely how one goes stale unnoticed.

```
q_h at h = 22.7'                        18.6 psf        (typehaus/wind.py)
G (rigid, §26.11.1)                     0.85
ASD factor (§2.4.1)                     0.6
```

**Solid area, derived from the model and not authored.** The brace rails are gone, so the
bands are the fascia and the three glulam beams:

```
E-W wind (the beams present their faces):
  fascia + deck edge   9"      × 9.67'   =  7.25 sf
  BM-SG-BLW/BLC/BLE   11 7/8"  × 9.67' ×3 = 28.69 sf
                                     A_s = 35.94 sf
N-S wind (the beams run along the wind and present nothing):
  fascia + deck edge   9"      × 21.0'  = 15.75 sf
                                     A_s = 15.75 sf
```

**E-W governs**, which is the reverse of the braced design's N-S 15.7 / E-W 25.4 split
because the beams got 5/8" deeper and the two 2x8 rails left the E-W band.

**C_f could not be sourced, and is spent rather than left open.** ASCE 7-16 Fig. 29.3-1 is
copyrighted and this repository holds three verified cells of it. The superseded note
*inverted* — reporting the coefficient at which a joint reaches capacity. Here the demand is
taken at **C_f = 1.80**, the largest value Cases A and B are known to reach, so a column
adequate at 1.80 is adequate for any legitimate reading of the figure.

```
F = 0.6 × q_h × G × C_f × A_s
  = 0.6 × 18.6 × 0.85 × 1.80 × 35.94  =  614 lb   storey shear, E-W
split over 4 fixed columns             =  153.4 lb each, delivered at the deck plane
base moment  M_w = 153.4 × 9.03'       =  1,385 lb-ft
```

**The three-beam band is an over-count and is kept deliberately.** Three N-S beams seen from
the east stand behind one another and a real open-frame analysis would shield the second and
third. Counting all three is conservative, it is what `checks/structural/lateral_racking`
already did with the rails, and at d/c 0.07 the margin is not worth an argument about
shielding factors.

(The rear row `PT-SG-BR1/BR3` stands **1 27/32"** proud for the deck's drainage crown, so its
lever is 9.16' and its wind moment **1,408 lb-ft**. The guard case still governs both rows.

**1 27/32" and not 2", since 2026-09-14.** `SPEC.rear_pillar_rise_in = 2.0` was retired for
`SPEC.balcony_fall_in_per_ft = 0.25`: the FALL is the authored number now — 1/4" per foot,
the trade standard for a walking deck and twice AridDek's published minimum — and the rise
follows the run between the bearing rows, which over 7'-4" is 1.833". The flat 2" worked out
to 0.27 in/ft over that run. Both base moments here are `shear × height`, so they follow the
rise exactly and by the same 0.15%.)

### 2c. Guard — IRC R301.5, and it is what governs

Table R301.5 note f: a **200 lb concentrated load in any direction** at the top of the
guard. Its lever to a column base is the whole column plus the guard height:

```
M_g = 200 lb × (9.01' + 3.5')  =  2,502 lb-ft
```

Two columns bound each end bay of the guard and would share this in any real distribution
(~1,250 lb-ft each). **It is taken wholly on one column**: halving it is a diaphragm claim
this note has no standing to make, and the margin is there to spend.

**The two are not summed.** ASCE 7-16 §2.4.1 pairs W with L at 0.75, and a guard load is not
a storey live load in the first place. The guard case governs at **2,502 lb-ft**.

---

## 3. Slenderness and magnification

```
r = d/4 = 3.0"                     (circular section)
k = 2.1                            ACI 318-19 Table R6.2.5, fixed base / free top —
                                   2.1 rather than the ideal 2.0, for real fixity
k·lu/r = 2.1 × 108.125 / 3.0 = 76  against §6.2.5's SWAY limit of 22
```

So it is a slender column and the moment must be magnified. It barely moves, because
magnification needs axial load to bite and there is almost none:

```
E_c = 57,000 √5,000            = 4.03e6 psi
I_g = π·12⁴/64                 = 1,018 in⁴
β_dns = 1.2 D / P_u = 1.2×1,564/4,971 = 0.378
EI = 0.4 E_c I_g /(1+β_dns)    = 1.19e9 lb-in²
P_c = π² EI /(k·lu)²           = π² × 1.19e9 / (227.06)² = 2.28e5 lb
δ  = 1/(1 − P_u/0.75 P_c) = 1/(1 − 4,971/171,037) = 1.030
```

**Magnified design moment M_u = 2,502 × 1.030 = 2,577 lb-ft.**

(Worked at **f'c 5,000 psi**, the mix §4a settled on 2026-09-10. This section stood at
3,000 until 2026-09-15 — E_c 3.12e6, EI 9.23e8, P_c 1.77e5, δ 1.039, M_u 2,600 lb-ft —
while §4 four pages later printed the 5,000 answer, so the note contradicted itself. The
richer mix stiffens the column, so magnification *falls*: δ 1.039 → 1.030 and M_u 2,600 →
2,577 lb-ft. The direction is the reassuring one and the change is 0.9%, which is why the
contradiction survived as long as it did — nothing downstream moved enough to notice.)

(`P_u` is 4,971 lb rather than the 3,845 this section carried before 2026-09-03's
beam-weighted tributary — see §2a. More axial makes the magnifier slightly larger and the
section slightly stronger, and neither moves the verdict: the whole magnification is 4%.)

---

## 4. Capacity — the section, worked by hand

12" round, (4) #5 hot-dip galvanized verticals, #3 galvanized ties @ 10" o.c., 2" cover,
**f'c 5,000 psi** (see §4a — it was 3,000 until 2026-09-10 and that was a modelling
limitation, not the concrete), f_y 60,000 psi.

```
A_s = 4 × 0.31 = 1.24 in²        ρ = 1.24/113.10 = 1.096%
                                 §10.6.1.1 floor 1% = 1.131 in²  ✓ (and ceiling 8% = 9.05)
bar count 4                      §10.7.3.1(b) minimum within circular ties  ✓ exactly
tie #3                           §25.7.2.1, for #10 and smaller  ✓
tie spacing 10"                  §25.7.2.2 least of 16d_b = 10.0", 48d_t = 18.0", h = 12"  ✓
```

Every one of those is **at its limit, not above it**. This is the minimum legal cage on a 12"
round: (4) #4 = 0.80 in² is 29% short of the floor, and four bars is already the count
minimum, so neither the size nor the number can come down.

**Bar orientation.** The four bars are taken at ±45° to the bending axis — the WEAK
orientation of a four-bar cage, about 8% below the strong one. Deliberate: a round column is
built in a round tube and nothing on site orients the cage to the wind. Each bar then sits
3.3125 × cos45° = **2.343"** from the section centre.

**Strain compatibility, P-M interaction at P_u = 4,971 lb.** **β₁ = 0.80 at 5,000 psi** —
ACI 318-19 Table 22.2.2.4.3 steps it down 0.05 per 1,000 psi above 4,000, and taking 0.85
here is the standard slip. Bisecting the neutral axis to satisfy φP_n = P_u lands at
**c = 2.752"**, a = β₁c = 2.202":

```
concrete segment, depth a = 2.202" into a 12" circle
  chord offset above centre  = 6 − 2.202         = 3.798"
  A_seg = 36·acos(3.798/6) − 3.798·√(36−3.798²)  = 31.05 − 16.82 = 14.23 in²
  ȳ_seg = (2/3)(36−3.798²)^1.5 / A_seg           = 4.695" above the centre
  C_c   = 0.85 × 5,000 × 14.23                   = 60,473 lb   at +4.695"

tension pair, offset −2.343" (depth from compression fibre 8.343")
  ε = 0.003 (2.752 − 8.343)/2.752 = −0.00609     yielded
  F = −60,000 × 0.62                             = −37,200 lb  at −2.343"

compression-side pair, offset +2.343" (depth 3.657" > a, no concrete deduction)
  ε = 0.003 (2.752 − 3.657)/2.752 = −0.000987
  F = −29e6 × 0.000987 × 0.62                    = −17,750 lb  at +2.343"

P_n = 60,473 − 37,200 − 17,750                   =   5,523 lb
M_n = 60,473(4.695) + (−37,200)(−2.343) + (−17,750)(2.343)
    = 283,921 + 87,160 − 41,589 = 329,492 lb-in  =  27,454 lb-ft
ε_t = 0.00609  →  φ = 0.900  (Table 21.2.2, past the transition on ε_ty = 0.00207)
φP_n = 4,971 lb = P_u ✓        φM_n = 0.900 × 27,454 =  24,709 lb-ft
```

`engineering/deck_post.py` reports **24,702 lb-ft** on the front row and **24,709** on the
rear, for the same section and load. Agreement to 0.03%; the residue is the bisection
tolerance.

**Note what the richer mix does to the SECTION, not only to the number.** A higher f'c
takes a smaller compression block to balance the same axial load, so `c` falls (3.236" →
2.752") and the neutral axis moves toward the compression face. Two things follow. The
concrete resultant sits further out, +4.375" → +4.695", which is most of the gain. And the
extreme tension strain rises 0.00473 → 0.00609, which carries the section clear of Table
21.2.2's transition band and takes φ from 0.872 to the full 0.900 — worth another 3% on
its own. **Neither of those is intuitive from "the concrete got stronger", and the second
one is the sort of term a reader checks by eye and gets wrong.**

The 17% capacity gain buys nothing that is needed: d/c goes 0.12 → 0.10 on a section that
was never sized by strength. What it buys is that the drawing and the calculation finally
state the same concrete.

### The verdict

| case | demand | φM_n | d/c |
| --- | ---: | ---: | ---: |
| wind, E-W | 1,385 lb-ft | 24,700 | **0.06** |
| guard, R301.5, unshared | 2,502 lb-ft | 24,700 | **0.10** |
| guard magnified, δ 1.030 | 2,577 lb-ft | 24,700 | **0.10** |
| axial, §22.4.2.1 | 4,947 lb | 285,900 lb | **0.02** |

(The front row, PT-SG-BF1/BF3. The rear row stands 1 27/32" proud for the deck's drainage
crown — see §2b — and reads 1,408 / 2,533 / 2,611 against 24,709, the same verdict one
decimal along.)

**The §2.3.1 envelope, added 2026-09-18.** Every row above is one combination's moment
against one combination's P-M point — `1.2D + 1.6L`'s 4,947 lb. A larger axial is not
automatically conservative on an interaction curve: below the balance point, which is where
this column sits at 2% of `P_n,max`, compression *raises* moment capacity. So each of ASCE
7-16 §2.3.1's five combinations is run at ITS OWN `P_u`, for `PT-SG-BR1`:

| §2.3.1 | P_u | M_u (magnified) | φM_n | d/c |
|---|---|---|---|---|
| 1.4D | 2,188 lb | 0 | 23,980 lb-ft | 0.00 |
| 1.2D + 1.6L + 0.5S | 4,969 lb | 4,178 lb-ft | 24,708 lb-ft | 0.17 |
| 1.2D + 1.6S + 0.5W | 1,875 lb | 1,187 lb-ft | 23,898 lb-ft | 0.05 |
| **1.2D + 1.0W + L + 0.5S** | **3,809 lb** | **4,995 lb-ft** | **24,404 lb-ft** | **0.20** |
| 0.9D + 1.0W | 1,407 lb | 2,367 lb-ft | 23,775 lb-ft | 0.10 |

The guard's 200 lb is an occupancy live load and rides the `L` term — full where `L` is,
absent where it is not — and combination 4 takes it CONCURRENTLY with wind, which is
conservative (nobody leans on a rail in a design windstorm) and cheap, because at 0.20 it is
nowhere near governing. Note that φM_n falls with `P_u` down every row: 23,775 at
combination 5 against 24,708 at combination 2, a 4% spread. That spread is the whole reason
the envelope exists, and it is small here only because this column is so lightly loaded.

**The anchorage of the dowels is graded now too** (2026-09-18). The lap between the dowel
and the column bar was checked against the column's own height; the other end — whether the
dowel DEVELOPS in the concrete below — was not, and it is the end the fixed base depends on.
These four columns stand on `W-SG-W1`/`-E1`, and until 2026-09-20 nothing in the model
bounded how far a dowel ran down the stem, so their records said the anchorage was not
graded. The dowel row now authors `embedment=24"` and the records grade STRAIGHT development
against it: ld 21.2" for a #5 at 5,000 psi, d/c 0.88 — worked in §11c. The pad-borne columns in the north entry ARE graded: ACI 318-19 §25.4.3.1 hooked
development, about 7.1" for a #5 at 5,000 psi against a 12" pad less 2" cover and a bar
diameter, d/c 0.76. Straight development would be 21" and would condemn a correctly built
pad; the hook is what makes it work, and the ψ factors it is taken at (ties continuing
through the joint, confined side cover) are conditions a reviewer confirms on the drawing.

**Bending governs and the guard governs the bending, at an eighth of capacity.** The column
is not sized by any of these — it is sized by the 2" of cover the durability case asked for
(§1) and by the 1% steel floor, which is a creep, shrinkage and accidental-moment rule and
not a strength one. That is worth saying plainly, because a reviewer reading d/c 0.12 will
otherwise ask why the column is not smaller. It cannot be: 10" fails the cover case, and no
column may be plain (§14.1.5).

### 4a. Where this note and the engine differed, and why they no longer do

**f'c — CLOSED 2026-09-10.** This section used to say: the mix specified in
`SUNKEN_GARDEN_COLUMN_12` is 5,000 psi (§6), the engine carries no strength on an Assembly,
so `deck_post.py` reads one presumptive 3,000 for every concrete calculation in the house,
and both this note and the record are worked at 3,000 — understated against what will be
poured, which is the safe direction.

`ConcreteSpec` has existed since 2026-09-03 and **the assembly simply had not been given
one**, while its 12"-round sibling `PIER_CONCRETE_12` had. The consequence was worse than
"conservative": PT-SG-FCOL and PT-SG-COL are the same column at the same height four feet
apart, holding the two ends of the same frame, and the register printed the front one as
the weaker — which is backwards, since they come off the same truck. The assembly now
states `concrete=EXPOSED_MIX` and all six of the court's 12" rounds are on it. §4 above is
re-worked by hand at 5,000 psi accordingly, and the engine was checked against that pass
and not the other way round.

**§3 and §7 were missed by that pass and stayed at 3,000 until 2026-09-15.** So for five
days the note *contradicted itself* — §4 printing the 5,000 answer while the slenderness
magnification four pages earlier and the development length three pages later were still
reading the old mix. Both are now re-worked, and the two behaved very differently:
§3's δ moved 1.039 → 1.030 (M_u 2,600 → 2,577 lb-ft, 0.9%, in the reassuring direction),
while §7's `ld` goes as 1/√f'c and moved 23%, which had been making the authored dowel
projection read 5 1/2" short of a splice it in fact clears. **A note that disagrees with
itself is worse than one that is uniformly conservative**, because a reviewer cannot tell
which half to trust — so the rule going forward is that a mix change re-works every section
that names f'c, and `grep "√3,000"` is the whole audit.

**What did NOT change.** The demands. Wind is a pressure on a guard and a deck, the guard
case is R301.5's 200 lb, and neither has any opinion about the concrete. Every d/c in the
verdict above fell purely because the denominator rose.

**φM_n history.** An earlier sketch of this design put φM_n near 13 kip-ft. That was a
pure-flexure estimate that dropped the compression-side bar pair and took a shorter lever
arm. At 3,000 psi the worked value was 20.9 kip-ft against the engine's 20,995; at the real
5,000 it is **24.7 kip-ft** against 24,702. The verdict has never turned on it.

---

## 5. The glulam beams

**Product:** preservative-treated southern yellow pine structural glulam, **3-1/2" ×
11-7/8", 24F-V5M1/SP** (Anthony Power Preserved / Boise Cascade, stocked through Lakeville),
clear-finished. They replaced three site-built 3-ply KDAT 2x12s.

**THE SPAN IS A PUBLISHED-TABLE READ, and these stopped being engineering items on
2026-09-11.** IRC Table R507.5(1) publishes sawn plies only, which is true and was taken to
mean nobody publishes a row for a glulam. The *supplier* does. Anthony/Canfor's **Power
Preserved Glulam Deck Guide (2020), Table 2 "Beam Spans"** (maximum 2' cantilever)
tabulates a 3-1/2" × 11-7/8" at a **10' joist span** carrying a **10' beam span** under
40 psf live + 10 psf dead. This balcony's beams carry a 10' joist span over 7.00'-7.33', so
the read is inside the row on both indices, and reading it is a prescriptive act. The row is
authored once as `_BALCONY_BEAM_PUBLISHED` in `params/sunken_garden.py` and grades all three.

**The NDS arithmetic below did NOT go away, and must not.** The deck guide's values are
**DRY-USE** and every one of these beams stands in weather. `structural.deck_beam_span`
prints the wet-service pass beside the published row as an advisory — the row is the verdict
a reviewer can open a document and confirm, and this is what says how much of its margin
weather spends. `engineering/glulam_beam.py` is now a pure module exposing `nds_states`,
with no registered kind behind it.

**Spans.** BM-SG-BLW and BLE run corner column to corner column at **7.33'** — shortened
from 7.77' when PT-SG-BF1/BF3 came 5-1/4" north so the beams would cantilever clear of the
12" rounds' tops (see §6). That leaves a rear overhang of 20.0" and a south cantilever of
8.0" against R507.5.1's quarter-span limit of **22.0"**. BM-SG-BLC runs PT-SG-BR2 to
PT-SG-BF2 at **7.00'** (it was 6.75' before PT-SG-BF2's last move; the engine's own resolved
back span is the number to trust and this line follows it), which leaves a rear overhang of
20.0" against a limit of 21.0". **Nothing in the engine checks a beam overhang** —
`checks/structural/deck.py` grades beam SPAN only, and `structural.deck_beam_cantilever`
grades the overhang against the back span but not against the published row's own 2' cap —
so both are written down here. Every overhang here is 1'-8", inside that cap.

**Wet service is applied, and it is the difference between this and a supplier's span
table.** AWC NDS 2018 Table 5.3.1: C_M = 0.80 on F_b, 0.875 on F_v, 0.53 on F_c⊥, 0.833 on E.
C_D = 1.0 (Table 2.3.2, occupancy live — not 1.15 snow, and emphatically not 1.6 wind).
C_V = 1.0: the §5.3.6 volume factor computes to 1.07 at this size and is capped. C_L is 1.0
with the compression edge held by a joist field at 16" o.c., and §5.3.6 takes the lesser of
C_L and C_V, so C_V governs.

```
w = 50 psf × 10.00' joist span                     = 500 plf
S = 3.5 × 11.875²/6 = 82.24 in³   I = 488.4 in⁴

BM-SG-BLW / BLE, L = 7.33' = 88.0"
  M   = 500 × 7.33²/8 = 3,361 lb-ft = 40,333 lb-in
  f_b = 40,333 / 82.24 = 490 psi     vs F_b' = 2,400 × 0.80 = 1,920 psi   d/c 0.26
  V at d: 500 (7.33/2 − 0.99) = 1,338 lb
  f_v = 1.5 × 1,338 / 41.56 = 48 psi vs F_v' = 300 × 0.875 = 263 psi      d/c 0.18
  bearing: R = 1,833 lb over 3.5" × 3" (R507.6 on concrete) = 175 psi
                                     vs F_c⊥' = 740 × 0.53 = 392 psi      d/c 0.45
  Δ_live = 5 (400/12) 88.0⁴ / (384 × 1.499e6 × 488.4) = 0.036"
                                     vs L/360 = 0.244"                    d/c 0.15

BM-SG-BLC, L = 6.75'  — every ratio lower; bearing governs at d/c 0.41
```

**Bearing governs, at under half.** 11-7/8" over the slimmer 9-1/2" option is the owner's
planter margin — 9-1/2" would run about 41% in bending against 26% here — and is a decision,
not a calculation. Recorded so nobody "optimises" the depth back out.

### 5a. Edge beams carry their own strip (2026-09-22)

The block above loads every beam with the FULL joist span. That is exact for BM-SG-BLC and
an over-count for the two edge beams, which carry half a bay plus the joist overhang past
them. `glulam_beam` (basis 3) now loads each beam with its own tributary: half of each
adjacent bay, plus the overhang where it is the outermost bearing.

```
BM-SG-BLW / BLE: bays 10.00', overhang 0.75'   tributary = 10.00/2 + 0.75 = 5.75'
w = 50 psf × 5.75'                                = 287.5 plf
L = 9.667' node to node (the engine's beam span)
  M   = 287.5 × 9.667²/8 = 3,358 lb-ft = 40,300 lb-in
  f_b = 40,300 / 82.24 = 490 psi       vs 1,920 psi     d/c 0.26
  V at d: 287.5 (9.667/2 − 0.99) = 1,105 lb
  f_v = 1.5 × 1,105 / 41.56 = 39.9 psi vs 262.5 psi     d/c 0.15
  bearing: R = 287.5 × 9.667/2 = 1,390 lb / 10.5 in² = 132.3 psi
                                       vs 392.2 psi     d/c 0.34   governs
  Δ_live = 5 (230/12) 116.0⁴ / (384 × 1.499e6 × 488.4) = 0.062"
                                       vs L/360 = 0.322" d/c 0.19
```

The same rule on an 18'-0" wall-to-wall deck with a 9" overhang gives 9.00 + 0.75 =
**9.75'** per edge beam, not 18'. `tests/test_pier_calcs.py` reproduces both.

### 5b. The beam's own bearings, by statics (2026-09-22, basis 4)

§5a took `wL/2` over the node-to-node 9.667'. The beams do not bear at their nodes: BM-SG-BLW
runs y = −10.50' to −0.833' over PT-SG-BF1 (y = −9.833') and PT-SG-BR1 (y = −2.50'), so
a = 0.667' south overhang, s = 7.333' back span, b = 1.667' north overhang (BLE the same on
BF3/BR3). The rear reaction was under-reported; bending and shear were over-stated.
Dead on all three segments, live on each of the 8 subsets of them (ASCE 7-16 §4.3.3).

```
w_D = 10 × 9.75 = 97.5 plf   w_L = 40 × 9.75 = 390 plf   w = 487.5 plf
S = 82.26 in³  I = 488.4 in⁴  E' = 1.8e6 × 0.833 = 1.499e6 psi  EI = 7.323e8 lb-in²

Full load:  W = 487.5 × 9.667 = 4,712.5 lb at 4.833' from the south tip
  R_BR1 = 4,712.5 × (4.833 − 0.667) / 7.333 = 2,678 lb   R_BF1 = 2,035 lb
Bearing — live on span + north overhang, south overhang dead only (Σ M about BF1):
  −65.0 × 0.333 + 3,575 × 3.667 + 812.5 × 8.167 = 19,722 lb-ft
  R_BR1 = 19,722 / 7.333 = 2,689 lb → 2,689 / 10.5 = 256.1 psi vs 392.2   d/c 0.65  governs
Bending — live on the span only (Σ M about BR1):
  R_BF1 = (3,575 × 3.667 + 65.0 × 7.667 − 162.5 × 0.833) / 7.333 = 1,837 lb
  V = 0 at 1,772 / 487.5 = 3.635' into the span
  M = −21.7 + 1,772 × 3.635 − 487.5 × 3.635²/2 = 3,199 lb-ft
  f_b = 3,199 × 12 / 82.26 = 466.6 psi vs 1,920                           d/c 0.24
Shear at d — the bearing pattern: 2,689 − 812.5 − 487.5 × 0.990 = 1,394 lb
  f_v = 1.5 × 1,394 / 41.56 = 50.3 psi vs 262.5                           d/c 0.19
Deflection, live alone — span only: 5 (32.5) 88.0⁴ / (384 EI) = 0.0347"
                                    vs 88.0/360 = 0.244"                  d/c 0.14
  north tip, live on both overhangs: 32.5·20⁴/8EI + (6,500·88/3EI)·20 + (1,040·88/6EI)·20
    = 0.00089 + 0.00521 + 0.00042 = 0.0065" vs 2 × 20/360 = 0.111" (R301.7 note b)
```

A single bearing (a cantilever) or three (continuous) is INCOMPLETE naming why, never
guessed. **Against `haus analysis --solve`:** PT-SG-BR1 live 3,955 lb, BF1 3,006 lb split
0.568 / 0.432 — exactly 2,678 / 4,712.5 — so the solve's distribution agrees. Its magnitude
is 18/9.75 = 1.85× this record's because the analytical loads (`pier_basis`) still give each
edge beam the whole 18' joist span (§5a's rule is `glulam_beam`'s alone): 3,955 × 9.75/18 =
2,142 lb live + 989 × 9.75/18 = 536 lb dead = 2,678 lb. Reconciled 2026-09-23: every reader
now takes §5a's strip (§13).

Black locust for the two centre pillars remains an option (IRC R202 naturally durable; mill
order; engineered values) and is **not** taken here.

---

## 6. What else moved, and why

**PT-SG-BF2 came north onto the porch deck**, 3" inside the front beam axis — the exact
mirror of PT-SG-BR2's 3" inside the back one. It stood on PT-SG-FCOL's top, which made it
19-1/2" longer than its five neighbours and forced that column to a 20" round so one pour
could span from the beams' north face to the pillar's south face. With BF2 on the deck,
**PT-SG-FCOL shrinks to 12" centred on the beam axis** and the whole 20" sizing essay
retires with it. 3" is the minimum that keeps the 5-1/2" post on the deck (the porch outline
ends on the beam axis) and it also keeps the base off TR-SG-CAP-FRW/FRE and its butyl.

**PT-SG-FCOL at 12", not 10":** it leaves 3-3/4" of concrete beside each beam end for the
HGAM10's Titen screws where 10" would leave 2-3/4". The rejected variant — BF2 on the column
south of the beams, north face flush with the rim line — fits a 12" only at 4.7" anchor edge
distance against ESR-1622's 4-5/8" minimum, with the beam ends bearing at the circle's
tangent.

**PT-SG-BF1 and BF3 came 5-1/4" north, and the front row's offset is now the round's.** It
had been `_y_balcony_front + 2-3/4"`, half the actual 6x6, which was right for a wood post
and went stale the day the corners became 12" rounds: a 6" radius on a 2-3/4" offset put the
column's south face 3-1/4" PAST the beam end. The wash and drip lip cast into that top are
real, but they do not answer the joint they were then asked to answer — the beam sat on the
north half of a shelf, with a re-entrant corner holding water against its own end grain and
against the HGAM10 seat. The offset is **radius + 2"** instead, so the glulam cantilevers 2"
past the column face and drips into air.

Three things it costs, none of them structural:

- **8" of back span**, 93.25" → 88.0", which takes R507.5.1's overhang limit from 23.3" to
  22.0" against an unmoved 20" rear overhang (§5). The row cannot go north again without
  taking PT-SG-BR1/2/3 with it.
- **RL-SG-PORCH's two front corner posts.** They stand at the rounds' west/east tangent in
  x; the modelled 1-1/2" post still clears by 3/4", but a real 5x5 surface baseplate lands
  inside the concrete. The guard's front corners **die into the columns** — rail ends on the
  concrete, Titen Turbo at ≥3" edge distance, no baseplate at those two stations. The engine
  models no baseplate and will never ask.
- **The porch enclosure's two front track runs** (`plan/placeables.py`, and
  `notes/porch_enclosure.md`). These were curtain rods until 2026-09-03; the rods had already
  moved from y −9'-6" to −9'-1" for the rounds, because at −9'-6" the bare rod would have run
  1" inside BF1's concrete, silently — a Furniture overlapping a column is nobody's check.
  The track sits at −9'-2", on the first balcony joist centreline, clearing the rounds by 2"
  in y. The same blind spot bit the *other* axis in the meantime: the rods hung at 8'-6",
  which the glulam swap left 1 1/8" above the beam soffit they claimed to hang under, i.e.
  inside BM-SG-BLW. The track hangs at 111.75", the joist soffit, which is above every beam.

PT-SG-BF2 is unaffected — a 6x6 on its own line, with BM-SG-BLC cantilevering 15" past it
since it moved onto the deck.

---

## 7. Durability, the detail, and constructability

**Exposure class F3 + C2, not F2.** Deicing salt reaches the porch below and planter runoff
reaches the balcony above: that is external chloride on a freeze-thaw member. **w/cm ≤ 0.40,
f'c ≥ 5,000 psi, 6% ±1.5 air**, SCM caps per ACI 318-19 §19.3.3.4. IRC R402.2 asks the same
of a salt-exposed porch. **Do not reuse the retired 20" column's 4,000 psi / w/cm 0.45 F2
mix here.**

**Bar protection: the GOAL is long-term durability in F3 + C2, and the coating is the margin
on top of a mix that already meets the Code.** Restated 2026-09-12 (BLD-02 finding 4) as a
ladder rather than a single product, so the spec can flex on schedule without losing what it
is for:

1. **Galvanized, either standard — preferred.** **ASTM A767**: galvanize AFTER fabrication
   (A767's classes are COATING WEIGHTS, not a bend-order distinction, so naming a class
   never settled the sequence); repair any field cut or bend per **ASTM A780**; a **welded**
   cage leaves A767 for **ASTM A123**. Route exists locally: **AZZ Galvanizing, Winsted MN
   (800 6th St S)** and **AZZ NE Minneapolis**. Or **ASTM A1094** — coated stock that
   **bends and fabricates after coating without repair**, which removes the sequencing
   question entirely; **CMC GalvaBar** (Catoosa OK) publishes it as stocked, shipping in
   days. **ACI 318-19 §20.2.1.7.2 lists both**, and **ψ_e = 1.0 either way**. The
   fabricator picks and **names the route on the order**.
2. **Black bar at this cover and this mix — accepted only as a written exception**, when
   neither galvanized route can be supplied on schedule. The 5,000 psi / w/cm 0.40 / 6% air
   / 2" cover combination above is what meets the Code on its own; the zinc was always
   margin.
3. **Epoxy and stainless — refused.** Epoxy delaminates and takes ψ_e 1.2–1.5, which
   lengthens every lap in this house by half. Stainless is the only coating that buys a
   century independent of cover, at 4-6× the cost and with an austenitic thermal coefficient
   (~16e-6/°C) fighting concrete's ~10-12e-6 (carbon steel is ~12e-6).

Galvanized already sacrifices zinc at any coating break. Sika/Vector Galvashield XPX
embedded zinc anodes (330 g zinc, 20+ yr, ~$1,400 per box of 20) are a possible
sunken-garden-**wide** addition for the salt-splash walls; on these columns, over galvanized
bar at 2" cover, they are a belt on braces and are not taken.

**The cage is a PART, and the stock part does not fit.** Out-to-out of ties it is
**8.0"** — 6.625" bar circle + 0.625" (one #5 diameter) + 2 × 0.375" (a #3 ring each side),
which is also 12" less 2 × 2" cover. That is the trade's **"8-inch cage"**, and it is one
cross-section repeated **ten times house-wide** (the four court columns and the six
north-entry pours, which carry the identical `ENTRY_PIER_CAGE`), lengths per pour, **tied
not welded**.

The **catalog stock 8" cage was evaluated and rejected**: Bolsinger's PASC-series stock 8"
unit is **(4) #4 with #3 ties @ 12"**, 3–8 ft, $49–77 black, shipping Cascade IA to MN in
15–20 business days. It fails on **two** counts, either of which is fatal:

| stock 8" cage | authored 8" cage | limit |
|---|---|---|
| 4 #4 = **0.80 in²** | 4 #5 = **1.24 in²** | ACI 318-19 §10.6.1.1 floor is 0.01 A_g = **1.131 in²** on a 113.1 in² gross — the stock cage is **29% short** |
| #3 ties @ **12"** | #3 ties @ **10"** | §25.7.2.1 caps tie spacing at 16d_b, which is **8.0"** for a #4 and **10.0"** for a #5 — the authored spacing is exactly the limit, the stock spacing is 50% over it |

So the part to order is a **custom 8" cage in a stock format**, ten off, from Rebarfab
Inc (720 First St SW, New Brighton MN, 651-633-3337 — in-house detailing and fabrication) or
a Bolsinger custom. The **$49–77** stock row is the cost floor; budget roughly **$90–140
each** at (4) #5 with galvanizing.

**Note on the lap:** ψ_e is **1.0** for galvanized bar (§25.4.2.5). It is EPOXY that takes
1.2-1.5, and reading the epoxy row here would lengthen every lap in this house by half.

```
ld  = (60,000 / (25 √5,000)) × 0.625 = 21.2"     §25.4.2.4, #6 and smaller
class B lap = 1.3 × 21.2             = 27.6"     §25.5.2.1 — every bar spliced at one section
authored: 4 #5 galvanized dowels projecting ~30"+ from the wall pour
```

**This one was worth correcting for more than tidiness.** Worked at 3,000 psi — as it was
until 2026-09-15, while §4a had specified 5,000 since 2026-09-10 — ld came out 27.4" and the
class B lap 35.6", against ~30" of authored projection: the note read as though the dowels
were **5 1/2" short of their own splice**. At the real f'c they need 27.6" and the authored
30" covers it with 2 1/2" to spare. The bar never moved; the note was reading the wrong mix.
`ld` goes as 1/√f'c, so this is the term the mix change moves *most* — 23% — which is why it
showed up here as an apparent deficiency and nowhere else.

**The wall-top cold joint is the wettest, saltiest elevation on the column** and a documented
chloride path. Roughen it to 1/4" amplitude, remove laitance, set a bentonite or crystalline
waterstop strip inside the dowel circle. A 12" round on a 12" wall is flush on both faces, so
there is no ledge to pond on.

**No grout island at the beam seat.** An exposed non-shrink grout island is a 10-20 year
element — not air-entrained, sitting at the wettest point. Cast the top **to line** under the
beam footprint, screed the ≥15° wash and drip lip around it (BIA Tech Note 36A), and take up
tolerance in the 1/2"-1" **stainless** standoff's shim pack. If a levelling bed proves
unavoidable it is an **epoxy** grout confined under the standoff plate, never a cementitious
island with exposed shoulders. **The tie is a cast-in HETA20Z pair since 2026-09-21** (the HGAM10
that stood here needs its Titen Turbos kept out of the exterior environment —
`column_head_connector_options.md`); on a 12" round its spoons sit 4-1/4" from the edge
against FL11473's 1-1/2" minimum. Isolate the gusset from the stainless standoff with EPDM or
HDPE. (PT-SG-COL keeps its grout island for now; aligning that one is a follow-up.)

**Sequence.** Dowels cast with the wall pour (4 #5 galvanized projecting ~30" per column).
Tube seated over them in a **plywood saddle collar screwed to the wall FACES** — a flush tube
leaves no wall top to Tapcon a collar to — top kicked with two 2x4s to the porch deck framing
(~8' kickers, never down to the garden floor), and the four tubes tied together with a
temporary stick. Cage tied flat, dropped and wired to the dowels, 2" cover held by plastic
wheel spacers. **~0.26 cy per column, ~1.05 cy for the four** (0.785 ft²/ft × 9.01'), plus
PT-SG-FCOL's 0.29 cy: a bucket, or one small pump call. 12-18" lifts with a 1" pencil
vibrator in the core, never on the cage. Air verified at the point of placement; 3/4" or 3/8"
aggregate. Broom or float finish on the wash, never steel-trowelled (NRMCA CIP 2 — troweling
drives the entrained air out of exactly the layer that scales). Two-person day to form, an
hour to pour, strip at two days, wet-cure 7 days protected from freezing to 3,600 psi
(ACI 306), a week's cure before the glulam lands. Silane at 28 days, re-applied ~10-yearly —
maintenance, not a substitute for cover. Optional mineral paint to match the white centre
posts.

**If forming is unwanted:** precast the four columns off site with dowel sleeves and grout
them on. The stock steel posts stay the fallback.

---

## 8. The guards

Both guards became **Williams Architectural Products, ICC-ES ESR-3485, 42" black** (Menards;
Eagan MN, the Ultralox factory) on 2026-09-02, with **Fortress Al13 Home** as the alternate.
Same 6063/6005A alloys and an AAMA-grade powder coat at ~$30-45/LF material against Trex
Signature's $72-98: Signature's premium buys sightline, not life. ESR-3485's maximum post
spacing at 42" is **91.3"**; the model's 60" complies with room to spare. A China import
lands at $45-60/LF after Section 232 (50%) + 301 (25%) and carries no evaluation report:
rejected on the report, not on the price.

**The two mounts split, and the substrate is why.**

- **RL-SG-PORCH → surface mount.** Its west and east legs run along the inner face of
  W-SG-W1/E1, so each 5×5 baseplate lands on a 12" concrete wall top and takes ESR-3485's
  concrete-baseplate row: four 1/4" × 3" corrosion-resistant anchors, no bracket, no
  through-bolt. Top mount is cheaper and is taken wherever the substrate allows it. The
  SOUTH leg has no wall under it — it runs over BM-SG-FRW/FRE, whose tops carry
  TR-SG-CAP-FRW/FRE and their butyl — so those five posts bolt through the composite plank
  into solid blocking in the joist bay just north of the beam. **Never anchor through a beam
  cap:** a 304-stainless plate on 0.019" aluminium coil in a wet exterior location pits the
  aluminium (it is anodic), and the fastener pierces the butyl that IS the dielectric between
  that coil and the copper-treated framing.
- **RL-SG-BALCONY stays fascia mount.** `FS-SG-DECK`'s aluminium plank is the porch roof and
  carries **no penetrations at all** since the heat pumps went to grade. Surface posts would
  put ~36 holes through the one waterproof plane in this structure to save bracket money.
  Brackets through-bolt the PVC fascia and the 2x8 rim per **Ultralox's own fascia-mount
  instructions** — four 5/16" × 4" bolts with washers and nuts per bracket, bracket top 1/2"
  below the rim top, a foot block mid-panel — with nuts on the rim's inside face, reachable
  from the open joist bays below. Manufacturer's instructions are the accepted basis under
  IRC R106 / R301.1.3; no PE letter. A solid block between the rim and the first joist at
  each post stops the rim rolling under the 200 lb load, and is authored in
  `FS-SG-DECK.reinforcements`.

ESR-3485's fascia-bracket row is written for **concrete**, which is why the wood-rim detail
above comes from the manufacturer's instructions rather than from the report.

---

## 9. What this note does NOT cover

- **Base fixity itself — the wall-top JOINT is computed, here (§11); the foundation's
  rotational restraint is not.** `column_support/W-SG-W1` and `column_support/W-SG-E1`
  were deferred to the structural engineer of record from 2026-09-11 to 2026-09-20. They
  are a computed kind now (`engineering/column_support.py`): bearing on the wall top, dowel
  tension, shear friction across the cold joint and dowel development into the stem, each
  hand-worked in §11. Rotational restraint — the foundation stiffness the fixed base
  assumes — is graded as `base_rotation/PT-SG-BF1`, `-BF3`, `-BR1`, `-BR3`, one question and
  one item.

  Still open, and still the first thing a stamp should look at: **the stem's own flexure
  under the base moment it receives** — whether a pilaster or a local thickening is needed
  under each column — and the strip footing's bearing under the column points, which
  `engineering/spread_footing.py` scopes off a shared wall footing. Both walls declare
  `lateral_support="top_and_bottom"` and are answered by IRC Table R404.1.2(8), which
  publishes no surcharge column.
- **Seismic, beyond the screening below.** The lot sits in **SDC A**: Minnesota's mapped
  values (S_S ≈ 0.04 g, S_1 ≈ 0.02 g) satisfy ASCE 7 §11.4.2 on both counts (S_1 < 0.04 and
  S_S ≤ 0.15), and §11.7 then sends an SDC A structure to **§1.4 alone** — F_x = 0.01 W,
  about **50 lb per column**, against the **153 lb** wind shear §2b already carries. So no
  R, no 15%-axial limit and no overstrength foundation case applies, and *wind governs*.
  **The mapped values are statewide, not this lot's**: query the USGS/ASCE Hazard Tool at
  the site's own coordinates and record the result before the calc package goes out. This is
  a screening, not a seismic design.
- **Shear in the column** (the section is enormous against a few hundred pounds, but
  "enormous" is a judgement), torsion, and the diaphragm claim that delivers storey shear to
  four corners rather than six posts.
- **C_f.** §2b spends it at the Case A/B ceiling rather than reading the figure. An engineer
  with ASCE 7-16 to hand should read the real cell.
- **The two wood centre pillars**, which stay prescriptive under IRC R507.4 and are graded
  there.
- **A shielding factor** on the three-beam E-W band (§2b), which would only reduce a demand
  already at d/c 0.07.
- **The Simpson round-footing letters** — an unverified lead: Simpson publish engineering
  letters for some connectors on round concrete, which might supersede the edge-distance
  arithmetic in §7 if one covers the HGAM10. Not located. Moot since 2026-09-21: the tie is a
  cast-in HETA20Z pair.

---

## 10. Where the model reports this

```
haus engineering houses/catlin
haus engineering houses/catlin --item deck_post/PT-SG-BF1     # a corner column, term by term
haus engineering houses/catlin --fingerprint deck_post/PT-SG-BF1
```

Four `deck_post/PT-SG-B{R,F}{1,3}` records, all `draft`, all `unsealed`. **The three
`deck_beam/BM-SG-BL*` records are gone**, and §5 above is where that happened: the glulams
moved onto a `PublishedSpan` on 2026-09-11, which is a prescriptive read and not something
a seal adds to. `--item deck_beam/BM-SG-BLC` reports nothing now. `structural.lateral_racking` now names each corner column as the
deck's lateral system and delegates to the same `deck_post/<tag>` item — one design, one
stamp, two checks.

---

## 11. The wall-top joint — hand-worked (`column_support/W-SG-W1`, `-E1`)

Worked 2026-09-20 in a separate pass from `engineering/column_support.py`, from this note's
own §2-§4 quantities. `tests/test_column_support_calc.py` checks the engine against it.

**What each column hands the wall.** The §4 envelope's (Pu, magnified Mu) pairs — the same
ones the column is graded on. Rear row `PT-SG-BR1` (D 1,563, L 1,933 lb; M_w 1,408 and M_g
2,533 lb-ft ASD; h 109.96"), front row `PT-SG-BF1` (D 1,545; 1,385 / 2,502; h 108.13"):

| §2.3.1 | BR1 P_u | BR1 M_u | BF1 P_u | BF1 M_u |
|---|---:|---:|---:|---:|
| 1.4D | 2,188 | 0 | 2,163 | 0 |
| 1.2D + 1.6L + 0.5S | 4,969 | 4,178 | 4,947 | 4,122 |
| 1.2D + 1.6S + 0.5W | 1,875 | 1,187 | 1,854 | 1,167 |
| **1.2D + 1.0W + L + 0.5S** | **3,809** | **4,995** | **3,787** | **4,919** |
| 0.9D + 1.0W | 1,407 | 2,367 | 1,390 | 2,327 |

(lb and lb-ft; M_u carries δ = 1/(1 − P_u/0.75P_c), P_c 220,520 lb rear, 228,511 front.)

**The base is far outside the kern.** e = M_u/P_u = 59,940/3,809 = **15.7"** at the
governing combination (10.1" at 1.2D + 1.6L; 8.7" at SERVICE, 2,533 × 12 / 3,496, which is
the figure a first sketch quotes). The kern of a circle is **D/8 = 1.5"**, not the
rectangle's D/6 = 2". So the base is partly in tension and the load reaches the wall on a
compression block, not on the 113.1 in² gross section.

### 11a. Bearing, ACI 318-19 §22.8.3

**√(A₂/A₁) = 1.0, and that is a finding, not a default.** A₂ is the largest concentric
area similar to the loaded one that fits on the wall top. The round is 12" and the stem is
12", centred (§1: "flush with both wall faces"), so the largest concentric circle on the
wall top IS the column: A₂ = A₁ and ACI's confinement credit (up to 2) is worth nothing.

**The block.** §4's strain compatibility at each P_u gives the neutral axis; at the
governing 3,809 lb (BR1), c = 2.730", a = β₁c = 0.80 × 2.730 = **2.184"**:

```
chord offset above centre  = 6 − 2.184                          = 3.816"
A₁ = 36·acos(3.816/6) − 3.816·√(36 − 3.816²) = 36 × 0.8815 − 3.816 × 4.630
   = 31.73 − 17.67                                              = 14.06 in²
ȳ  = (2/3)(36 − 3.816²)^1.5 / 14.06 = (2/3)(99.26)/14.06        = 4.705" above centre
```

**The couple.** The dowels sit one bar inside the verticals (the contact lap
`resolve/rebar` lays): ring radius 3.3125 − 0.625 = **2.6875"**. Compression dowels are not
credited — every pound of compression goes on the concrete. Two orientations of the ring:

```
straddling (±45°): 2 bars in tension at 2.6875 × cos45 = 1.900" below centre
on-axis (0°):      1 bar in tension at 2.6875" below centre

moments about the centre:  C·ȳ + T·y_s = M_u,   C − T = P_u
  →  C = (M_u + P_u·y_s)/(ȳ + y_s)

±45°: C = (59,940 + 3,809 × 1.900)/(4.705 + 1.900) = 67,177/6.605 = 10,170 lb, T = 6,361
0°:   C = (59,940 + 3,809 × 2.6875)/(4.705 + 2.6875) = 70,177/7.3925 = 9,493 lb, T = 5,684
```

Bearing takes the larger C, **10,170 lb** (±45°).

```
φB_n = 0.65 × 0.85 × 5,000 × 14.06 × 1.0 = 38,850 lb       (wall f'c: EXPOSED_MIX, 5,000)
d/c  = 10,170 / 38,850                                     = 0.262   BR1
BF1: C 10,025 on a 14.06 in² block (c 2.729")               = 0.258
```

Every other combination is lower (1.2D + 1.6L: 9,033 / 39,307 = 0.23). Where no dowel
tension is needed (1.4D), C = P_u on the same block — 2,188 / 38,218 = 0.06.

### 11b. Dowel tension across the joint

Per bar, the worse orientation — on-axis, where ONE bar closes the couple:

```
T per bar = 5,684 lb (BR1), 5,574 lb (BF1)
φA_s f_y  = 0.90 × 0.31 × 60,000 = 16,740 lb
d/c       = 0.340 (BR1), 0.333 (BF1)
```

### 11c. Development into the stem, ACI 318-19 §25.4.2.4

```
ld = (60,000 / (25 √5,000)) × 0.625 = 21.2"   ψt 1.0 (a VERTICAL bar — 1.3 is for a
                                              horizontal bar with >12" of concrete below),
                                              ψe 1.0 (zinc, §25.4.2.5)
authored embedment                  = 24"     (params/sunken_garden.py, the dowel row)
stem                                = 109.44" − 3" cover = 106.4" ≥ 24"  (bound holds)
d/c = 21.2 / 24                     = 0.884
```

Straight, and the hook the layout turns at the dowel's foot is not credited. 24" is a
chosen detail, not a derived one: it is the smallest round number past ld. The stem bound is
the WALL's resolved height (`pier_basis` read a `FoundationWall.height` field that does not
exist until 2026-09-20, which silently gave 0.0).

### 11d. Shear friction across the cold joint, §22.9

**μ = 1.0λ is earned, not assumed**: §7 specifies the wall top roughened to 1/4" amplitude
with the laitance removed, which is Table 22.9.4.2's "intentionally roughened" row, and the
dowel row authors `joint_surface="roughened"` so the model carries it. Unroughened it
would be 0.6λ — and the verdict would not move.

Shear at the base, strength level: wind V_w = 1,408 / 9.163' = 153.7 lb ASD → /0.6 =
**256.1 lb**; the guard's 200 lb at 1.6L = 320 lb; combination 4 takes both at 1.0 →
**456.1 lb**. The dowel tension the couple spends is not available for clamping
(§22.9.4.2 + the tension-is-additive rule), and the axial compression is not credited:

```
φV_n = μ(φ A_s f_y − T) = 1.0 × (0.75 × 1.24 × 60,000 − 6,361)   = 49,439 lb
cap  = φ × min(0.2f'c, 480 + 0.08f'c, 1600)A_c = 0.75 × 880 × 113.1 = 74,644 lb
d/c  = 456.1 / 49,439                                            = 0.009
```

### 11e. Verdict

| state | BR1 | BF1 |
|---|---:|---:|
| bearing on the compression block | 0.262 | 0.258 |
| dowel tension per bar | 0.340 | 0.333 |
| shear friction | 0.009 | 0.009 |
| development into the stem | **0.884** | **0.884** |

**Development governs**, and only because 24" is a tight detail — the joint is not
stressed. The E1 wall is the mirror of W1 and reads the same. What is NOT here: rotational
restraint (`base_rotation/PT-SG-*`) and the stem's own flexure under the moment (§9).

---

## 12. The 17'-0" court frame (2026-09-22) — §2-§4 and §11 re-worked

The court went to 17'-0" clear and the centre support line retired (`PT-SG-BR2/BF2`,
`BM-SG-BLC`). `FS-SG-DECK` is 2x12 SP @ 12" spanning **18'-0"** between `BM-SG-BLW`/`-BLE`
with a 9" cantilever each side; the four corner columns are the only posts. Everything
below supersedes the matching figure above; the method is unchanged. The record's lever is
still the AUTHORED `Post.height` (108.125" front, 109.958" rear) although the resolved
column now stops ~4" lower under the deeper joists — the record errs long, i.e. safe.

### 12a. Gravity (§2a)

`pier_basis` gives each beam the WHOLE joist span as its strip (the rule's deliberate
overlap — the glulam's own record carries 9.75', §5a):

```
per column   18.00' × 9.667' / 2                  = 87.00 ft²
live         40 × 87.00                           = 3,480 lb
dead         10 × 87.00 + self weight              = 870 + 1,061.5 = 1,931.5 lb  (front)
             self weight 0.7854 ft² × 9.010' × 150 = 1,061.5; rear 9.163' → 1,079.5 → 1,949.5 lb
P_u          1.2 × 1,931.5 + 1.6 × 3,480           = 7,885.8 lb front; 7,907.4 rear
```

The strip rule makes the two columns under one beam carry 348 ft² of a 188.5 ft²
(19.5' × 9.667') deck — 1.85x. Conservative, printed on the record, and it is what drives
every axial below.

### 12b. Wind (§2b)

```
E-W bands:  TR-SG-FASCIA + deck edge 13" × 9.667'   = 10.47 sf
            BM-SG-BLW, -BLE  11 7/8" × 9.667' × 2   = 19.13 sf      A_s = 29.60 sf
N-S band:   13" × 19.50'                           = 21.13 sf      (361 lb; E-W governs)
F = 0.6 × 18.63 × 0.85 × 1.80 × 29.60              = 506 lb   / 4 = 126.6 lb per column
M_w = 126.6 × 9.010'                               = 1,140 lb-ft front
      126.6 × 9.163'                               = 1,160 lb-ft rear
```

The third beam's band left with `BM-SG-BLC`. The guard (§2c) is unchanged: **2,502 /
2,533 lb-ft**, and still governs.

### 12c. Slenderness and the section (§3, §4)

```
β_dns = 1.2 × 1,931.5 / 7,885.8 = 0.2939      EI = 0.4 × 4.0305e6 × 1,017.9 / 1.2939 = 1.2683e9
P_c = π² × 1.2683e9 / (2.1 × 108.125)²          = 242,781 lb   (rear 234,404)
δ = 1 / (1 − 7,885.8 / (0.75 × 242,781))       = 1.0453       (rear 1.0471)
M_u guard = 1.6 × 2,502.1 × 1.0453              = 4,185 lb-ft  (rear 4,243)
```

Strain compatibility at P_u 7,885.8, same bars at ±45°, β₁ 0.80:

```
c = 2.809"   a = 2.247"   chord offset 3.753"
A_seg = 14.65 in²   ȳ = 4.668"          C_c = 0.85 × 5,000 × 14.65 = 62,268 lb
tension pair   ε −0.00591, yielded      F = −37,200 lb at −2.342"
compr.-side    ε −0.000907              F = −29e6 × 0.000907 × 0.62 = −16,306 lb at +2.342"
P_n = 62,268 − 37,200 − 16,306 = 8,762 lb     φP_n = 0.90 × 8,762 = 7,886 = P_u ✓
M_n = 62,268 × 4.668 + 37,200 × 2.342 − 16,306 × 2.342 = 339,600 lb-in = 28,300 lb-ft
φM_n = 0.90 × 28,300 = 25,470 lb-ft front      (rear, P_u 7,907: 25,476)
```

More axial is more moment capacity below balance, so φM_n ROSE 24,700 → 25,470.

| case (front row) | demand | capacity | d/c |
|---|---:|---:|---:|
| wind, 1.0W | 1,901 lb-ft | 25,470 | 0.075 |
| guard, 1.6L | 4,003 lb-ft | 25,470 | 0.157 |
| guard magnified, δ 1.045 | 4,185 lb-ft | 25,470 | 0.164 |
| §2.3.1 envelope, 1.2D + 1.0W + L (P_u 5,798, δ 1.033) | 4,547 lb-ft | 24,925 | **0.182** |
| axial | 7,886 lb | 285,893 lb | 0.028 |

Rear row, the envelope: P_u 5,819, M_u 4,618 (δ 1.034) against 24,931 — 0.185.

### 12d. The wall-top joint (§11), at the governing 1.2D + 1.0W + L

```
                         BR1                         BF1
P_u, M_u (magnified)     5,819 lb, 4,618 lb-ft        5,798 lb, 4,547 lb-ft
c, a                     2.768", 2.215"               2.768", 2.214"
A₁, ȳ                    14.35 in², 4.687"            14.35 in², 4.687"
C (±45°) = (M_u + P_u × 1.900)/(ȳ + 1.900)
                         10,092 lb                    9,957 lb
φB_n = 0.65 × 0.85 × 5,000 × A₁                     39,644 lb / 39,636 lb   d/c 0.255 / 0.251
T, one bar on-axis = (M_u + P_u × 2.6875)/(ȳ + 2.6875) − P_u
                         3,817 lb                     3,715 lb    vs 16,740   d/c 0.228 / 0.222
V_u = 1,160/9.163'/0.6 + 200 = 210.9 + 200         = 410.9 lb  (both rows)
φV_n = 0.75 × 1.24 × 60,000 − T(±45°, C − P_u)     = 55,800 − 4,273 = 51,527 lb (BR1)
                                                     55,800 − 4,159 = 51,641 lb (BF1)   d/c 0.008
development                                          21.2" / 24"   0.884 — still governs
```

Unroughened (μ 0.6): 0.6 × 51,527 = 30,916 lb (§13c: 0.6 × 50,168 = 30,101 lb).

### 12e. Balcony gravity through the frame (`analytical_model_basis.md` §3c)

The solve hands the two columns under a beam 3,119 lb (front) and 3,842 lb (rear) of live
load against the record's equal 3,480 — the pair sum agrees (6,961 vs 6,960) and the split
follows the unequal cantilevers. See that note for the dead case and the base moment the
continuous frame puts on these columns under gravity, which no record grades.

---

## 13. Each edge beam on its own strip (2026-09-23) — §12 re-worked

`pier_basis`, `post_bearing`, `analytical/loads` and `structural.deck_*` now read §5a's rule
through `engineering/deck_tributary.py`: a beam carries half of each adjacent bay plus the
overhang past it, **9.75'** here, not the whole 18'. §12's gravity was 1.85× the deck.
Wind (§12b) and the guard do not move. Worked with a calculator from §3/§4's formulas.

### 13a. Gravity

```
per column   9.75' × 9.667' / 2                   = 47.13 ft²   (4 × 47.13 = 188.5 = 19.5' × 9.667')
live         40 × 47.13                           = 1,885 lb
dead         10 × 47.13 + 1,061.5                 = 1,532.8 lb front;  + 1,079.5 = 1,550.8 rear
P_u          1.2 × 1,532.8 + 1.6 × 1,885          = 4,855.3 lb front;  4,876.9 rear
```

### 13b. Slenderness and the section

```
β_dns = 1.2 × 1,532.8 / 4,855.3 = 0.3788      EI = 0.4 × 4.0305e6 × 1,017.9 / 1.3788 = 1.1902e9
P_c = π² × 1.1902e9 / (2.1 × 108.125)²          = 227,834 lb   (rear 219,862)
δ = 1 / (1 − 4,855.3 / (0.75 × 227,834))       = 1.0292       (rear 1.0305)
M_u guard = 1.6 × 2,502.1 × 1.0292              = 4,120 lb-ft  (rear 4,176)
```

Strain compatibility at P_u 4,855.3, bars at ±45° (2.342"), β₁ 0.80:

```
c = 2.750"   a = 2.200"   chord offset 3.800"
A_seg = 14.21 in²   ȳ = 4.696"          C_c = 0.85 × 5,000 × 14.21 = 60,403 lb
tension pair   ε −0.00610, yielded      F = −37,200 lb at −2.342"
compr.-side    ε −0.000990              F = −29e6 × 0.000990 × 0.62 = −17,808 lb at +2.342"
P_n = 60,403 − 37,200 − 17,808 = 5,395 lb     φP_n = 0.90 × 5,395 = 4,855 = P_u ✓
M_n = 60,403 × 4.696 + 37,200 × 2.342 − 17,808 × 2.342 = 27,421 lb-ft (unrounded c)
φM_n = 0.90 × 27,421 = 24,678 lb-ft front      (rear, P_u 4,877: 24,684)
```

Less axial is less moment capacity below balance: φM_n 25,470 → 24,678, back beside §4's
24,702 at a P_u (4,947) within 2% of this one.

| case (front row) | demand | capacity | d/c |
|---|---:|---:|---:|
| wind, 1.0W | 1,901 lb-ft | 24,678 | 0.077 |
| guard, 1.6L | 4,003 lb-ft | 24,678 | 0.162 |
| guard magnified, δ 1.029 | 4,120 lb-ft | 24,678 | 0.167 |
| §2.3.1 envelope, 1.2D + 1.0W + L (P_u 3,724, δ 1.022) | 4,501 lb-ft | 24,382 | **0.185** |
| axial | 4,855 lb | 285,893 lb | 0.017 |

Rear row, the envelope: P_u 3,746, M_u 4,569 (δ 1.023) against 24,388 — 0.187.

### 13c. The wall-top joint (§11), at 1.2D + 1.0W + L

```
                         BR1                         BF1
P_u, M_u (magnified)     3,746 lb, 4,569 lb-ft        3,724 lb, 4,501 lb-ft
c, a                     2.729", 2.183"               2.728", 2.182"
A₁, ȳ                    14.05 in², 4.706"            14.05 in², 4.706"
C (±45°)                 9,378 lb                     9,247 lb
φB_n                     38,825 lb   d/c 0.242        38,817 lb   d/c 0.238
T, one bar on-axis       5,032 lb    d/c 0.301        4,935 lb    d/c 0.295   (vs 16,740)
φV_n = 55,800 − (C − P_u)  50,168 lb                  50,277 lb   (V_u 410.9, d/c 0.008)
development              21.2" / 24"   0.884 — still governs
```

**The dowel tension ROSE, 0.228 → 0.301**: less axial leaves more of the moment to the bar.
(At 2" cover. §14b re-runs this joint at 2 1/2" and 3": the dowel ring shrinks and T rises 19%.)
A lighter column is not the safe side of every state, which is why each is re-worked.

### 13d. Through the frame (`analytical_model_basis.md` addendum 2026-09-23)

390 plf live over the 9.667' beam, 4.167' of the 7.333' bearing span toward the rear:
**2,142 lb at BR1, 1,628 at BF1** (solve 2,142.5 / 1,628.3); dead 97.5 plf → 536 / 407 lb.
The pair sums to the records' 2 × 1,885 = 3,770; each column is 14% off the equal split.

## 14. Cover: 3" asked for, 2" kept (2026-09-23)

**The owner asked for 3" of cover on every cast column (2026-09-23), with 2" or 2 1/2"
acceptable if the numbers are clearly better there or the smaller cage is a more standard
part.** 3" and 2 1/2" both fail one row — the north-entry pad dowels — so **2" stays**, on
all ten columns, one cage. Worked by hand at §13's loads with §3/§4's method; only the bar
circle moves:

```
bar-circle radius  r = 6 − cover − 0.375 − 0.3125     2": 3.3125   2 1/2": 2.8125   3": 2.3125
bar offset at ±45°  = r × cos 45°                          2.342          1.989         1.635
dowel ring (one bar inside the verticals) = r − 0.625      2.6875         2.1875        1.6875
cage out-to-out = 12 − 2 × cover                           8"             7"            6"
```

### 14a. The section at P_u 4,855.3 (front row, 1.2D + 1.6L)

```
cover   c        a        A_seg    ȳ        C_c       T (pair)   eps_t     Cs (pair)          phi     phi·Mn
2"      2.750"   2.200"   14.21    4.696"   60,403    −37,200    0.00610   −17,808 (−0.00099)   0.900   24,678
2 1/2"  2.867"   2.294"   15.09    4.641"   64,127    −37,200    0.00536   −21,532 (−0.00120)   0.900   24,657
3"      2.981"   2.385"   15.96    4.587"   67,826    −37,200    0.00468   −25,032 (−0.00139)   0.868   23,941
```

At 3", phi = 0.65 + 0.25 × (0.00468 − 0.00207)/0.003 = 0.868 (Table 21.2.2). **Cover costs
almost nothing in bending here.** Both bar pairs are in tension at this axial, so pulling the
cage in shortens the tension pair's arm and trims the far pair's negative moment; M_n rises
27,421 → 27,587 lb-ft. What 3" costs is phi: ε_t drops under ε_ty + 0.003 = 0.00507.

### 14b. §13c's joint at each cover (1.2D + 1.0W + L, the governing case)

The couple's tension lever is the dowel ring, so the DOWEL takes more as the cage shrinks —
the term §13c had not re-run. Same formulas as §11a-§11d:

| PT-SG-BR1 (BF1 in brackets) | 2" | 2 1/2" | 3" |
|---|---:|---:|---:|
| c / a, in | 2.729 / 2.183 | 2.846 / 2.277 | 2.959 / 2.367 |
| A₁ in², ȳ in | 14.05, 4.706 | 14.93, 4.651 | 15.79, 4.598 |
| bearing C, lb | 9,378 | 9,782 | 10,240 |
| φB_n, lb | 38,825 | 41,244 | 43,622 |
| bearing d/c | 0.242 (0.238) | 0.237 (0.234) | 0.235 (0.231) |
| T, one bar on-axis, lb | 5,032 | 5,471 | 5,984 |
| dowel tension d/c (vs 16,740) | 0.301 (0.295) | 0.327 (0.321) | **0.357 (0.351)** |
| φV_n = 55,800 − T(±45°), lb | 50,168 | 49,764 | 49,306 |
| shear friction d/c (V_u 410.9) | 0.008 | 0.008 | 0.008 |
| development into the stem | 0.884 | 0.884 | 0.884 |

Dowel tension rises 19% at 3" and bearing falls slightly (a deeper block). Development
still governs the joint at 0.884, untouched. Unroughened at 3": 0.6 × 49,306 = 29,584 lb.

### 14c. Every governing number, three ways

| state | 2" | 2 1/2" | 3" | 3" vs 2" |
|---|---:|---:|---:|---:|
| court corner, §2.3.1 envelope (front / rear) | 0.185 / 0.187 | 0.185 / 0.187 | 0.189 / 0.192 | +2.4% |
| court corner φM_n at P_u 4,855 | 24,678 | 24,657 | 23,941 | −3.0% |
| court corner, governing row (dowel development, §11c) | 0.884 | 0.884 | 0.884 | 0 |
| wall-top joint, dowel tension (not governing) | 0.301 | 0.327 | 0.357 | +19% |
| `PT-BW-RE`/`-RNE` §2.3.1 envelope | 0.546 | 0.546 | 0.561 | +2.7% |
| `PT-BW-RE`/`-RNE` pad-dowel hook, engine (12 − 3 − 0.625) | 0.850 | 0.850 | 0.850 | 0 |
| **north-entry pad dowels, hooked layout (`integrity.reinforcement_layout`)** | PASS | **FAIL ×6** | **FAIL ×6** | — |

**The last row decides it.** The dowels lap one bar inside the verticals, so four of them sit
on a ring of 2 × 1.6875 = 3.375" at 3" cover: adjacent centres 1.6875 × √2 = **2.39"** apart
(2 1/2": 3.09"). ACI 318-19 Table 25.4.3.2 takes ψ_r 1.0 only for hooked bars ≥ 6 d_b =
**3.75"** apart (or enclosed by Ath ≥ 0.4Ahs); otherwise 1.6. At 2" they are **3.80"** apart
and clear it by 0.05". So at 2 1/2" and 3":

```
ℓ_dh = 7.11" × 1.6 = 11.38"    against 12" pad − 3" bottom cover = 9.00"     FAIL, all six pads
```

A 2" cage is the largest ring that keeps ψ_r = 1.0 by spacing (cover ≤ 2.03"). The court
corners dowel STRAIGHT into the wall and do not see this row. Two ways back to 3", neither
taken here — both are design changes the owner has not asked for:

1. **15" pads** on the moment piers (12 − 3 → 11.38 needs ≥ 14.4"); the tops hold, bottoms
   drop 3", so bearing, frost cover and the hydrant clearances move (north_entry_piers.md §6).
2. **Hook ties through the pad** (Ath ≥ 0.4 × 4 × 0.31 = 0.50 in²), which `deck_post`'s
   record already ASSUMES ("hook enclosed by the column's ties through the joint") but which
   `BarSpec.hook_ties` cannot yet state on a `dowels` row, so the layout cannot credit it.

The four landing piers' dowels are withdrawn as demand (north_entry_piers.md §6) and kept as
built; dropping them would leave only `PT-BW-RE`/`-RNE` needing either fix.

**Durability, restated.** Table 20.5.1.3.1 asks 1 1/2" of a #5 exposed to weather; 3" is for
concrete cast against ground, which a formed column is not. R20.5.1.4.1 recommends ≥ 2 1/2"
in corrosive exposure for members other than walls and slabs, so 2" is under the
recommendation, meets the Code, and has galvanized bar as its margin (§7).

**On "stock".** §7's catalog 8" cage is real — Bolsinger's PASC-8X5, (4) #4 + #3 @ 12", 5 ft,
$56.99 — and was already rejected (under the 1% floor, ties over 16 d_b). The authored cage has
always been a custom tie-up in that format, so no cover is "the standard size" and none was
chosen for it. No catalog 6" cage was found.

`tests/test_balcony_column_cover.py` reproduces §14a, the envelope and §14b's bearing and
tension rows at all three covers.

---

## 15. The balcony 3" lower (2026-09-23) — §13 re-worked

Owner's call, to land `D-S-DECK-E` (R311.3): `balcony_level_ft` 10.0 → 9.75', and the
`court-upper` storey datum reads it. The fall and every seat are unchanged; the whole balcony
drops 3". The record's lever is still the AUTHORED `Post.height`, now **105.125"** front
(9.75' − 11 7/8" glulam) and **106.958"** rear (+ 1.833" rise) — still 11 1/4" (the joist
depth the resolver drops) longer than the built column, so it errs long, as before.

### 15a. Loads

```
h_app  = guard top 13.375' + court 9.120'          = 22.495'   (was 22.745')
q_h    = 18.631 × (22.495/22.745)^(2/7)            = 18.572 psf  (Exposure B, K_z ∝ z^(2/7))
F      = 0.6 × 18.572 × 0.85 × 1.80 × 29.60        = 504.6 lb  / 4 = 126.16 lb per column
M_w    = 126.16 × 8.760'                           = 1,105 lb-ft front;  × 8.913' = 1,125 rear
M_g    = 200 × (8.760' + 3.5')                     = 2,452 lb-ft front;  2,483 rear
self   0.7854 × 8.760' × 150                       = 1,032.1 lb front;   1,050.1 rear
D      471.3 + self                                = 1,503.3 lb front;   1,521.3 rear
P_u    1.2 × 1,503.3 + 1.6 × 1,885                 = 4,820.0 lb front;   4,841.6 rear
```

### 15b. Slenderness and the section

```
β_dns = 1.2 × 1,503.3 / 4,820.0 = 0.3743      EI = 0.4 × 4.0305e6 × 1,017.9 / 1.3743 = 1.1941e9
P_c = π² × 1.1941e9 / (2.1 × 105.125)²          = 241,820 lb   (rear 233,129)
δ = 1 / (1 − 4,820.0 / (0.75 × 241,820))       = 1.0273       (rear 1.0285)
M_u guard = 1.6 × 2,452.1 × 1.0273              = 4,030 lb-ft  (rear 4,085)
```

Strain compatibility at P_u 4,820.0 (2" cover, bars at ±2.342"): c = 2.749", a = 2.199",
A_seg 14.21 in², ȳ 4.696" — **φM_n = 24,669 lb-ft** front (rear 24,675), 9 lb-ft under §13.

| case (front row) | demand | capacity | d/c |
|---|---:|---:|---:|
| wind, 1.0W | 1,842 lb-ft | 24,669 | 0.075 |
| guard, 1.6L | 3,923 lb-ft | 24,669 | 0.159 |
| guard magnified, δ 1.027 | 4,030 lb-ft | 24,669 | 0.163 |
| §2.3.1 envelope, 1.2D + 1.0W + L (P_u 3,689, δ 1.021) | 4,383 lb-ft | 24,373 | **0.180** |
| axial | 4,820 lb | 285,893 lb | 0.017 |

Rear row, the envelope: P_u 3,711, M_u 4,451 (δ 1.022) against 24,379 — 0.183.

### 15c. The wall-top joint (§11), at 1.2D + 1.0W + L

```
                         BR1                         BF1
P_u, M_u (magnified)     3,711 lb, 4,451 lb-ft        3,689 lb, 4,383 lb-ft
c, a                     2.728", 2.182"               2.727", 2.182"
A₁, ȳ                    14.05 in², 4.706"            14.05 in², 4.706"
C (±45°)                 9,153 lb                     9,023 lb
φB_n                     38,811 lb   d/c 0.236        38,803 lb   d/c 0.233
T, one bar on-axis       4,863 lb    d/c 0.291        4,766 lb    d/c 0.285   (vs 16,740)
V_u = 126.16/0.6 + 200   410.3 lb
φV_n = 55,800 − (C − P_u)  50,358 lb                  50,466 lb   (d/c 0.008)
development              21.2" / 24"   0.884 — still governs
```

Unroughened (μ 0.6): 0.6 × 50,358 = 30,215 lb.

### 15d. §14 at the new loads

```
cover   c (P_u 4,820.0)  phi     φM_n     envelope φM_n (P_u 3,689)   BR1 joint C / φB_n / T
2"      2.749"           0.900   24,669   24,373                      9,153 / 38,811 / 4,863
2 1/2"  2.866"           0.900   24,649   24,372                      9,545 / 41,230 / 5,287
3"      2.981"           0.868   23,935   23,805                      9,988 / 43,608 / 5,784
```

Same shape as §14 — the dowel's tension rises 19% at 3" — and the pad-dowel row still decides
it: **2" stays.**

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- **ACI 318-19** — §19.3.3.4, §20.5.1.3, Table 20.5.1.3.1, §20.5.1.4.1 and R20.5.1.4.1,
  Table 21.2.2, §22.8.3, §22.9.4.2, §22.9.4.4, §25.4.2.4
- **ASCE 7-16** — Fig. 29.3-1, §2.3.1, §2.4.1, §29.3
- ASTM A767
- **AWC NDS 2018** — Table 5.3.1
- ICC-ES ESR-3485
- IRC R106, IRC R202, IRC R301.1.3, IRC R301.5, IRC R402.2, IRC R507.1, IRC R507.4, IRC Table R507.5(1
- MN Rules 1309.0301
