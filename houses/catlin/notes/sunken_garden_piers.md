# Sunken-garden piers — the two cast columns and their belled footings

> ## ⚠ A SCREENING — AND IT NOW REACHES BOTH ENDS OF THE PIER.
> `PT-SG-COL` and `PT-SG-FCOL`, **both 12" round**, carry the porch's two beam lines onto
> augered, belled piers. **The ground checks out** — 1,603 and 1,159 psf against the 2,000 psf
> IBC Table 1806.2 presumes for this site's GM. **And so do the columns:** (4) #5 each, a hair
> over ACI 318-19 §10.6.1.1's 1% floor, at d/c 0.056 against §22.4.2's tied-column axial cap.
>
> **What changed on 2026-08-30 is the MODEL, not the concrete.** `Post` grew a
> `vertical_reinforcement` field. Until it had one, §14.1.5 — which does not permit a plain
> concrete COLUMN at any stress — left `deck_post/*` with nowhere to record an answer, so it
> reported INCOMPLETE however well the section did. The bars in §4 are the minimum the Code
> permits, which is also the cheapest.
>
> **REVISED 2026-09-03 for the balcony redesign** (`notes/balcony_moment_columns.md`), and
> two things moved:
> * **`PT-SG-FCOL` fell from 20" round to 12".** It was 20" only because `PT-SG-BF2`, a
>   balcony pillar, stood on its top and one pour had to span from the front beams' north
>   face to that pillar's south face. BF2 moved north onto the porch deck, so this column
>   seats two collinear beam ends and nothing else, and sits ON the beam axis. Its cage came
>   down from (8) #6 to the same (4) #5 the other four cast columns carry.
> * **`PT-SG-COL`'s tributary rose from 82.33 to 116.17 ft².** That is a FIX, not a change of
>   design: `PT-SG-BR2` has always stood on the porch deck 3" from the back-beam line, and
>   `pier_basis` only handed load down post-to-post, so a third of the balcony was landing on
>   this column and being counted nowhere. Both centre pillars now hand their share through
>   the deck's beams. Bearing rose from 1,245 to 1,603 psf and still clears.
>
> The four balcony corner columns `PT-SG-B{R,F}{1,3}` are the same product at the same cage
> and are graded in **`notes/balcony_moment_columns.md`**, not here — they stand on wall tops
> rather than on their own belled piers, and bending, not bearing, is their question.

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Written:** 2026-08-30, by hand, before the calculations it oracles were encoded; revised
2026-09-03 for the balcony redesign (see the box above).
**Oracles:** `engineering/pier_basis.py`, `engineering/spread_footing.py`,
`engineering/deck_post.py`; reproduced by `tests/test_pier_calcs.py`.
**Companion:** `notes/sunken_garden_court_free_body.md` — same structure, same missing boring,
and its §2 geotechnical table is the one used here.

---

## 1. What is built, and what stands on it

```
                        porch deck FS-SG-PORCH, 164.67 ft2
        BM-SG-BKW  ====================================  BM-SG-BKE      y = -2.25'
                              ||  PT-SG-COL
                              ||  12" round, 10'-8 3/16"
                              ||  PIER_CONCRETE_12 — one concrete layer
        BM-SG-FRW  ====================================  BM-SG-FRE      y = -9.50'
                              ||  PT-SG-FCOL
                              ||  12" round, 10'-8 3/16"
                              ||  SUNKEN_GARDEN_COLUMN_12 — one concrete layer
   garden floor  ------------ || ------------------------------------  -9'-1 7/16"
                          +---++---+
                          |  bell   |   30" / 36" dia x 12", augered
        -12'-7 7/16"      +---------+   to frost depth on undisturbed soil
                          | 7" levelling course (NOT a soil replacement) |
```

Both columns are **10'-8 3/16" (128.1875")**, both are 12" round, and both are **one concrete
STRUCTURE layer** — the assemblies state a thickness and a material and nothing else. They
carry different assemblies for a reason that is not the section: `PIER_CONCRETE_12` is the
4,000 psi F2 sonotube mix that also serves the four breezeway piers, and
`SUNKEN_GARDEN_COLUMN_12` is the 5,000 psi F3+C2 galvanized-cage mix the balcony redesign
introduced (`notes/balcony_moment_columns.md` §7). Aligning `PT-SG-COL` onto the better mix
and retiring its exposed grout island is an open follow-up.

**BOTH columns carry a balcony pillar's share.** `PT-SG-BR2` stands on the porch deck 3"
south of the back-beam line, and `PT-SG-BF2` stands on it 3" north of the front-beam line —
each a mirror of the other, each a third of the balcony, and each delivering that load into
the beam line beside it and so into the column under it. `structural.deck_footing_size`
reports N/A on both pillars and says in as many words that "this item's bearing design has
to include this post's share"; `pier_basis._piers_below` is what makes that true, and it did
not exist for the deck-borne case until 2026-09-03.

---

## 2. Loads

IRC Table R301.5 via R507.1: **40 psf live, 10 psf dead.** Tributary is the deck's plan area
divided evenly among the posts its beams name — exact on a regular post grid, which this is,
and printed on every record so a reviewer can disagree with it.

| | `PT-SG-COL` | `PT-SG-FCOL` |
|---|---|---|
| own deck share, `FS-SG-PORCH` 164.67 ft² / 2 | 82.33 ft² | 82.33 ft² |
| handed down by a centre pillar (`FS-SG-DECK` 203.00 / 6) | 33.83 ft² (BR2) | 33.83 ft² (BF2) |
| **tributary** | **116.17 ft²** | **116.17 ft²** |
| column self weight | 1,258 lb | 1,258 lb |
| the pillar's own 6x6, 35 pcf | 67 lb | 66 lb |
| **D** = trib×10 + self + carried | **2,487 lb** | **2,486 lb** |
| **L** = trib×40 | **4,647 lb** | **4,647 lb** |
| **service** D+L | **7,134 lb** | **7,132 lb** |
| **P_u** = 1.2D + 1.6L (IBC §1605.2) | **10,419 lb** | **10,418 lb** |

The two differ by a pound, and only because `PT-SG-BR2` is 2" taller than `PT-SG-BF2` (the
rear pillar row runs proud for the deck's drainage crown), so its 6x6 weighs a pound more.

Column self weight, worked once: 12" round is `π×6² = 113.1 in²` = 0.7854 ft², × 10.682' ×
150 pcf = **1,258 lb**. (`PT-SG-FCOL` was a 20" round until 2026-09-03 — `π×10² = 314.2 in²`
= 2.182 ft², × 10.682' × 150 = **3,496 lb** — which is where its old 4,735 lb dead load and
13,117 lb factored load came from. The column shrank; the deck did not.)

---

## 3. Bearing — and the two places the model's shape is not the pier's

### 3a. The bell is a CIRCLE and the resolved solid is a SQUARE

`resolve/envelope.py::_resolve_footing` draws a post-hosted footing as a square of side
`width`, because that is what a `Ring` carries cheaply. But `params/sunken_garden.py` names
the very same number **"bell diameter under the 12" sonotube"** — it is an augered shaft with
a belled base, not a formed pad. The difference is not cosmetic:

```
30" square  = 2.5 × 2.5     = 6.250 ft²
30" circle  = π × 1.25²     = 4.909 ft²      27% less
```

Reading the square would credit bearing area that does not exist, in the **unconservative**
direction. The calculation reads the circle.

### 3b. The bells bear on the SITE's soil, not on a replacement section

This is the one judgement in the bearing module, and it goes the opposite way to the
retaining walls'. Those sit on **42"** of ASTM C33 #57 washed stone, and
`retaining_basis._base_interface` correctly reads IBC Table 1806.2 **class 3** (3,000 psf,
μ 0.35) off `FootingBedding.non_frost_susceptible` because a 42" section *is* the bearing
material. These two are different: `params/sunken_garden.py` augered both bells to frost
depth on 2026-08-29 **precisely so they would bear on undisturbed soil**, and what they carry
is a **7" levelling course** (`SPEC.pier_levelling_bedding_in`). A 7" course spreads load into
the native soil within inches of the bell.

**So the site's own class 4 governs: 2,000 psf, not 3,000.** Crediting the stone's number
here would be reading a 42" section's allowable off a bedding one sixth as deep.

### 3c. The numbers

```
q = (service + bell self weight) / bell area

PT-SG-COL    bell 30" = 4.909 ft², 12" thick → 736 lb
             (7,134 + 736) / 4.909  =  1,603 psf   vs 2,000   d/c 0.80   ✓
PT-SG-FCOL   bell 36" = 7.069 ft², 12" thick → 1,060 lb
             (7,132 + 1,060) / 7.069 =  1,159 psf  vs 2,000   d/c 0.58   ✓
```

Both clear, and **the two swapped places on 2026-09-03**. `PT-SG-FCOL` used to be the one to
watch at d/c 0.74; it fell to 0.58 when the column shrank from 20" round to 12" and shed
2,238 lb of its own concrete. `PT-SG-COL` rose from 0.62 to **0.80** when `PT-SG-BR2`'s
share of the balcony was finally handed to it, and it is now the pier with the least margin
in this structure — on a 30" bell against `PT-SG-FCOL`'s 36". Any growth in the balcony's
loading lands here first. **Widening that bell to 36" would take it to 1,159 psf** and is the
obvious move if it is ever wanted; it is not taken now, because 0.80 against a presumptive
allowable with no boring is a screening margin either way (§5).

---

## 4. The columns — the cage, and why this one and not a cheaper one

### 4a. Both are COLUMNS, not pedestals, and the ratio is the whole question

ACI 318-19 §2.3 defines a **pedestal** as a member whose height-to-least-lateral-dimension
ratio is **not more than 3**, and §14.3.3.1 restates it as a design limit ("ratio of
unsupported height to average least lateral dimension shall not exceed 3"). It matters
because §14.1.3(d) permits a plain concrete **pedestal** and **§14.1.5 does not permit a
plain concrete COLUMN** — *"plain concrete shall not be permitted for columns and pile
caps"*. R14.1.5 gives the reason: a column lacks the ductility it should have, and a random
crack in an unreinforced one endangers its structural integrity. (ACI 318-11 carries the same
prohibition in §22.2.1's closing sentence.)

```
PT-SG-COL    128.1875 / 12  =  10.7          }  both far past 3.
PT-SG-FCOL   128.1875 / 12  =  10.7          }  both are COLUMNS.
```

**One escape a reviewer will reach for, and it does not reach.** §14.1.2 excludes
*"cast-in-place piles and piers embedded in ground"* from Chapter 14 altogether, and these
are augered piers. But only the **bell** is embedded: the shaft stands free in an open court
for its whole 10'-8", which is the condition §14.1.2 is not describing.

So these two take cages, and the rest of this section designs them.

### 4b. What the Code demands of a cage, before any load is considered

Six limits, none of them a function of the load. This is the part that decides the bars:

| | clause | `PT-SG-COL` | `PT-SG-FCOL` |
|---|---|---|---|
| gross area `A_g` | — | π×6² = **113.10 in²** | π×6² = **113.10 in²** |
| minimum steel `0.01 A_g` | §10.6.1.1 | **1.131 in²** | **1.131 in²** |
| maximum steel `0.08 A_g` | §10.6.1.1 | 9.05 in² | 9.05 in² |
| minimum bar count | §10.7.3.1(b) | **4** within circular ties | **4** |
| tie bar size | §25.7.2.1 | **#3** (verticals are #10 or smaller) | **#3** |
| tie spacing, least of `16 d_b` / `48 d_t` / `h` | §25.7.2.2 | min(10.0, 18.0, 12.0) = **10.0"** | min(10.0, 18.0, 12.0) = **10.0"** |

Since 2026-09-03 the two columns are the same section, so the two columns of this table are
the same numbers twice. It is kept as two columns anyway: the reason they agree is that
`PT-SG-FCOL` shrank, and a table that quietly merged them would lose the fact that they were
ever different.

§10.7.3.1's floor is **four** within rectangular *or circular* ties — six is the spiral case,
not the circular-tie case, and the two get confused constantly. Neither of these piers is
spirally reinforced.

### 4c. The cages, and the cheaper ones that were rejected

**`PT-SG-COL`: (4) #5 vertical, #3 ties @ 10" o.c.**
`A_st` = 4 × 0.31 = **1.24 in²**, ρ = **1.096%**, clearing the 1.131 in² floor by 9.6%.
The only other cage that clears is 6-#4 at 1.20 in² — 4.01 lb/ft against 4.17, about a nickel
of steel, and two extra bars to cut, bend and tie. Four #5 is both the Code's own floor for a
circular tie and the cheaper cage once labour is counted.

**`PT-SG-FCOL`: (4) #5 vertical, #3 ties @ 10" o.c., 2" cover, hot-dip galvanized.**
The same cage, since 2026-09-03 — the column is the same section now, so the same six limits
give the same answer. It carried **(8) #6 @ 12"** while it was a 20" round, against a
3.142 in² floor, and two lighter cages were rejected then: **4-#8 = 3.16 in²** cleared by
0.6% with four bars 11" apart in a 20" circle (rejected on margin, not arithmetic), and
**6-#6 = 2.64 in²** looked reasonable and was **16% SHORT**. Both are recorded because
anyone reverting to a 20" round will re-derive them.

The galvanizing and the 2" cover come with the balcony redesign's F3+C2 durability case and
are specified for every cast column in this structure; see `notes/balcony_moment_columns.md`
§7. `PT-SG-COL` keeps its 4,000 psi F2 sonotube mix and its exposed grout island for now —
an open follow-up, not an oversight.

Both cages are the **minimum the Code permits**, which is the answer the "cheapest concrete"
brief asks for. There is no spare capacity being bought here — see §4d for how little of it
the load actually uses, and §4f for why that is not an argument for less steel.

### 4d. Axial capacity — and the 0.80 is doing more work than it looks

```
phi P_n,max = phi x 0.80 x [ 0.85 f'c (A_g - A_st) + f_y A_st ]
              §22.4.2.1 and Eq. 22.4.2.2; alpha = 0.80 for TIED (Table 22.4.2.1);
              phi = 0.65, compression-controlled tied (Table 21.2.2).
              f'c = 3,000 psi (IRC Table R402.2), f_y = 60,000 psi.

BOTH         0.85 x 3,000 x 111.86 = 285,236  +  60,000 x 1.24 =  74,400
             P_o = 359,636 lb
             phi P_n,max = 0.65 x 0.80 x 359,636 = 187,011 lb
             P_u = 10,419 lb  (COL) / 10,418 lb (FCOL)  ->  d/c 0.056
```

(`PT-SG-FCOL` at 20" round was `phi P_n,max` = 521,732 lb against P_u 13,117 lb, d/c 0.025.
Shrinking it to 12" more than doubled its d/c and left it at a factor of eighteen.)

**The 0.80 is not a safety factor; it is an eccentricity.** R22.4.2 records that the 0.80
(tied) and 0.85 (spiral) caps were introduced to replace the explicit minimum-eccentricity
design ACI 318-71 carried, and that they correspond to **e = 0.10h and 0.05h**. So the cap
above already has a **1.20"** eccentricity built into both of these 12" columns (and had
2.00" on the 20" round `PT-SG-FCOL` was). That is not trivia — §4e spends it.

### 4e. Slenderness — not neglectable on either, and still not binding

`r` = `d`/4 for a circular section, and `k` = 1.0 because **these are leaning columns**.
`structural.lateral_racking` reports both of them as carrying no knee brace, with every pound
of storey shear handed to the braced bays on the deck-and-rail diaphragm claim. A leaning
column is designed non-sway for its own load; the P-Δ it sheds belongs to the bays that brace
it, and **that** is the open question, reported where it belongs rather than smuggled in here.

```
                          PT-SG-COL          PT-SG-FCOL
r = d/4                     3.00"               3.00"
k l_u / r                    42.7                42.7
§6.2.5 non-sway floor          34                  34
                        NOT neglectable     NOT neglectable
```

(`PT-SG-FCOL` was at 25.6 and neglectable outright while it was a 20" round. Shrinking a
column is the one edit that makes slenderness *appear*, which is why it is checked here
rather than assumed to have stayed benign.)

So both get magnified (§6.6.4.4.4(a), §6.6.4.5.2):

```
E_c = 57,000 sqrt(3,000)                      = 3,122,019 psi
I_g = pi d^4 / 64                             = 1,017.9 in^4
beta_dns = 1.2 D / P_u = 2,984 / 10,419       = 0.2864
EI = 0.4 E_c I_g / (1 + beta_dns)             = 988.3e6 lb-in^2
P_c = pi^2 EI / (k l_u)^2                     = 593,600 lb
delta_ns = 1 / (1 - P_u / 0.75 P_c) = 1/(1 - 0.0234) = 1.024
```

**A 2.4% magnifier**, because the column is at 6% of its capacity. Now spend §4d's
eccentricity. §6.6.4.5.4 sets a minimum moment `M_2,min = P_u (0.6 + 0.03h)`, i.e. a minimum
eccentricity of `0.6 + 0.03h`:

```
                          PT-SG-COL          PT-SG-FCOL
e_min = 0.6 + 0.03h         0.960"              0.960"
magnified by delta_ns       0.983"              0.983"
e already in the 0.80 cap   1.200"              1.200"
                            COVERED             COVERED
```

**The magnified minimum eccentricity is inside the eccentricity the axial cap was calibrated
for, on both piers.** That is why §4d's single axial comparison is the whole check and no
interaction diagram is needed: the moment case the Code would make us carry is smaller than
the one already priced into the number we compared against.

### 4f. What the spare capacity is NOT an argument for

Both columns land at d/c 0.056 — a factor of eighteen. **Nobody should read that as room to
shrink them, and the cage is not what is holding them at this size.**

* Both are 12" because that is the smallest sonotube the beam pockets and the HGAM gusset's
  1½" edge distance will take (`params/sunken_garden.py`, the `CN-SG-TIE-COL` note) — and
  because 12" is what 2" of cover needs on a #5 cage, which is the durability case the
  balcony redesign made house-wide (`notes/balcony_moment_columns.md` §1).
* `PT-SG-FCOL` was 20" for a **bearing-width** reason and is not any more: it seated
  `PT-SG-BF2` on its top as well as the two front beams, and that is what took it from 16" to
  20". BF2 moved onto the porch deck on 2026-09-03 and the reason went with it.
* And the steel is already at the Code minimum, so there is nothing to remove from it. The
  1% floor is not a strength requirement — it is there for creep, shrinkage and the accidental
  moment no analysis names, all of which are indifferent to how lightly the column is loaded.

---

## 4g. The four balcony corner columns are graded elsewhere

`PT-SG-BR1`, `PT-SG-BR3`, `PT-SG-BF1` and `PT-SG-BF3` are the same 12" round, the same
(4) #5 galvanized cage and the same `SUNKEN_GARDEN_COLUMN_12` assembly as `PT-SG-FCOL`.
They are **not** in this note, and the split is not filing: they stand on the 12" tops of
W-SG-W1/E1 rather than on their own belled piers, so there is no bearing question here to
answer, and what governs them is BENDING at a fixed base — they are the balcony's entire
lateral system since the knee braces were deleted. That is
**`notes/balcony_moment_columns.md`**, which works the base moments, the P-M interaction and
the dowel lap by hand. `engineering/spread_footing.py` deliberately declines to grade the
wall footings under them (`_Pier.shared_wall_footing`) for the reason §3 gives about two
authorities on one number: those footings are graded as `retaining_wall/*`.

---

## 5. What this note does NOT do

- **No moment BEYOND the Code minimum.** §4e carries `M_2,min` and magnifies it, and shows
  it is inside the eccentricity §22.4.2's 0.80 cap already embeds. What is *not* carried is
  the real bending from the beams landing eccentrically on the column tops: no beam reaction
  is resolved to an offset, so no interaction diagram is drawn. On this loading that is a
  small omission and it is still an omission.
- **No lateral case, and this is the one that matters.** The porch's own east-west path is
  open (`plans/TODO.md`). §4e takes `k` = 1.0 on the strength of the leaning-column
  assumption, and `structural.lateral_racking` reports that assumption as UNKNOWN in as many
  words: every pound of storey shear was given to the braced bays on a diaphragm claim this
  model does not check. **If that claim fails, these two columns are cantilevers, `k` goes to
  2.0, and §4e is re-run against a sway frame's threshold of 22 rather than 34.** Nothing
  here carries wind or seismic into the shafts.
- **No uplift.** `notes/uplift_load_path.md` covers what holds the beams down; nothing here
  checks the pier against net uplift, and a belled shaft is good at resisting it — an
  argument nobody has made in numbers.
- **No settlement and no group effect.** Both would need the boring this site does not have.
- **And there is no depth or width bearing bonus to claim.** IBC §1806.3.3's "increase for
  depth" raises **lateral** bearing only, and all of §1806.3 is scoped to resistance to
  lateral loads; the 2018 IBC has no provision raising presumptive **vertical** pressure for
  a deeper or wider footing. (The +20% per foot to a 3× cap that some references remember is
  1997 UBC Table 18-I-A and did not carry forward.) The only sanctioned escalators are
  §1806.1's one-third with the alternative wind/seismic combinations and §1806.2's *"data to
  substantiate the use of higher values"* — which means a boring, not a table adjustment.
- **No frost check** — `structural.frost_depth` owns that and passes both bells on 42" of
  true cover since 2026-08-29.
- **The tributary rule is a division, not an analysis.** Deck area over post count is exact
  on a regular grid. `FS-SG-PORCH` is two beam lines on two columns and two walls, so the
  columns do not really take half the deck each — the walls take a share. **That makes these
  numbers conservative**, and it is worth saying rather than quietly banking.
- **No development, splice or dowel detail.** §4 sizes a cage; it does not lap it into the
  bell, hook it, or check the tie hooks and the bar's clear cover against §20.5.1.3. That is
  drawing work and it is not here.
- **`f'c` is presumptive.** 3,000 psi from IRC Table R402.2, and `f_y` is 60,000 psi Grade 60,
  authored in the cage string and assumed by the calculation. And note that MN Rules 1309.0402
  amends that table with a **5,000 psi FOOTINGS row**; whether an augered pier bell is a
  "footing" for that amendment is not a question this note answers, and it should be asked
  before anyone orders concrete.
