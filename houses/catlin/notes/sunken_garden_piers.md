# Sunken-garden piers — the two cast columns and their belled footings

> ## ⚠ A SCREENING — AND IT NOW REACHES BOTH ENDS OF THE PIER.
> `PT-SG-COL` (12" round) and `PT-SG-FCOL` (20" round) carry the porch's two beam lines onto
> augered, belled piers. **The ground checks out** — 1,245 and 1,477 psf against the 2,000 psf
> IBC Table 1806.2 presumes for this site's GM. **And so do the columns, now that they have
> cages:** (4) #5 and (8) #6, both a hair over ACI 318-19 §10.6.1.1's 1% floor, at d/c 0.042
> and 0.025 against §22.4.2's tied-column axial cap.
>
> **What changed on 2026-08-30 is the MODEL, not the concrete.** `Post` grew a
> `vertical_reinforcement` field. Until it had one, §14.1.5 — which does not permit a plain
> concrete COLUMN at any stress — left `deck_post/*` with nowhere to record an answer, so it
> reported INCOMPLETE however well the section did. The bars in §4 are the minimum the Code
> permits, which is also the cheapest; the pour is unchanged.

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Written:** 2026-08-30, by hand, before the calculations it oracles were encoded.
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
                              ||  20" round, 10'-8 3/16"
                              ||  SUNKEN_GARDEN_COLUMN_20 — one concrete layer
                              ||         ...and PT-SG-BF2, a 6x6 balcony
                              ||            pillar, stands on its TOP
   garden floor  ------------ || ------------------------------------  -9'-1 7/16"
                          +---++---+
                          |  bell   |   30" / 36" dia x 12", augered
        -12'-7 7/16"      +---------+   to frost depth on undisturbed soil
                          | 7" levelling course (NOT a soil replacement) |
```

Both columns are **10'-8 3/16" (128.1875")** and both are **one plain concrete STRUCTURE
layer** — the assemblies state a thickness and a material and nothing else. `Post` has no
`vertical_reinforcement` field; that is §4's whole finding.

**`PT-SG-FCOL` carries a second post.** `PT-SG-BF2`, one of the balcony's six 6x6 pillars,
bears on its top rather than on the porch framing (`params/sunken_garden.py`, and
`SUNKEN_GARDEN_COLUMN_20`'s own comment records that this is why the column went 16" → 20").
`structural.deck_footing_size` reports N/A on that pillar and says in as many words that
"this item's bearing design has to include this post's share" — so it does, below, and that
sentence is the only thing tying the two together.

---

## 2. Loads

IRC Table R301.5 via R507.1: **40 psf live, 10 psf dead.** Tributary is the deck's plan area
divided evenly among the posts its beams name — exact on a regular post grid, which this is,
and printed on every record so a reviewer can disagree with it.

| | `PT-SG-COL` | `PT-SG-FCOL` |
|---|---|---|
| own deck share, `FS-SG-PORCH` 164.67 ft² / 2 | 82.33 ft² | 82.33 ft² |
| handed down by `PT-SG-BF2` (`FS-SG-DECK` 203.00 / 6) | — | 33.83 ft² |
| **tributary** | **82.33 ft²** | **116.17 ft²** |
| column self weight | 1,258 lb | 3,496 lb |
| `PT-SG-BF2`'s own 6x6, 35 pcf | — | 78 lb |
| **D** = trib×10 + self + carried | **2,082 lb** | **4,735 lb** |
| **L** = trib×40 | **3,293 lb** | **4,647 lb** |
| **service** D+L | **5,375 lb** | **9,382 lb** |
| **P_u** = 1.2D + 1.6L (IBC §1605.2) | **7,768 lb** | **13,117 lb** |

Column self weight, worked once: 12" round is `π×6² = 113.1 in²` = 0.7854 ft², × 10.682' ×
150 pcf = **1,258 lb**. 20" round is `π×10² = 314.2 in²` = 2.182 ft², × 10.682' × 150 =
**3,496 lb**.

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
             (5,375 + 736) / 4.909  =  1,245 psf   vs 2,000   d/c 0.62   ✓
PT-SG-FCOL   bell 36" = 7.069 ft², 12" thick → 1,060 lb
             (9,382 + 1,060) / 7.069 =  1,477 psf  vs 2,000   d/c 0.74   ✓
```

Both clear. **`PT-SG-FCOL` is the one to watch**: it is at 0.74 and it is the one carrying a
second post, so any growth in the balcony's loading lands here first.

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
PT-SG-FCOL   128.1875 / 20  =   6.4          }  both are COLUMNS.
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
| gross area `A_g` | — | π×6² = **113.10 in²** | π×10² = **314.16 in²** |
| minimum steel `0.01 A_g` | §10.6.1.1 | **1.131 in²** | **3.142 in²** |
| maximum steel `0.08 A_g` | §10.6.1.1 | 9.05 in² | 25.13 in² |
| minimum bar count | §10.7.3.1(b) | **4** within circular ties | **4** |
| tie bar size | §25.7.2.1 | **#3** (verticals are #10 or smaller) | **#3** |
| tie spacing, least of `16 d_b` / `48 d_t` / `h` | §25.7.2.2 | min(10.0, 18.0, 12.0) = **10.0"** | min(12.0, 18.0, 20.0) = **12.0"** |

§10.7.3.1's floor is **four** within rectangular *or circular* ties — six is the spiral case,
not the circular-tie case, and the two get confused constantly. Neither of these piers is
spirally reinforced.

### 4c. The cages, and the cheaper ones that were rejected

**`PT-SG-COL`: (4) #5 vertical, #3 ties @ 10" o.c.**
`A_st` = 4 × 0.31 = **1.24 in²**, ρ = **1.096%**, clearing the 1.131 in² floor by 9.6%.
The only other cage that clears is 6-#4 at 1.20 in² — 4.01 lb/ft against 4.17, about a nickel
of steel, and two extra bars to cut, bend and tie. Four #5 is both the Code's own floor for a
circular tie and the cheaper cage once labour is counted.

**`PT-SG-FCOL`: (8) #6 vertical, #3 ties @ 12" o.c.**
`A_st` = 8 × 0.44 = **3.52 in²**, ρ = **1.120%**, clearing the 3.142 in² floor by 12%.
Two lighter cages were considered and rejected:

* **4-#8 = 3.16 in²** is the lightest thing that clears at all (10.68 lb/ft against 12.02),
  and it clears by **0.6%**. A 20" column held over its legal minimum by half a percent has
  no room for a substituted grade, a re-rounded bar area or any revision to the load — and
  four bars in a 20" circle sit about 11" apart, which is a poor cage whatever the arithmetic
  says. **Rejected on margin, not on arithmetic.**
* **6-#6 = 2.64 in²** is the trap: it looks like a perfectly reasonable cage for a 20" round
  and it is **16% SHORT** of the minimum. Anyone re-deriving this by eye should check it
  against 3.142 in² before believing it.

Both cages are the **minimum the Code permits**, which is the answer the "cheapest concrete"
brief asks for. There is no spare capacity being bought here — see §4d for how little of it
the load actually uses, and §4f for why that is not an argument for less steel.

### 4d. Axial capacity — and the 0.80 is doing more work than it looks

```
phi P_n,max = phi x 0.80 x [ 0.85 f'c (A_g - A_st) + f_y A_st ]
              §22.4.2.1 and Eq. 22.4.2.2; alpha = 0.80 for TIED (Table 22.4.2.1);
              phi = 0.65, compression-controlled tied (Table 21.2.2).
              f'c = 3,000 psi (IRC Table R402.2), f_y = 60,000 psi.

PT-SG-COL    0.85 x 3,000 x 111.86 = 285,236  +  60,000 x 1.24 =  74,400
             P_o = 359,636 lb
             phi P_n,max = 0.65 x 0.80 x 359,636 = 187,011 lb
             P_u = 7,768 lb                      ->  d/c 0.042

PT-SG-FCOL   0.85 x 3,000 x 310.64 = 792,130  +  60,000 x 3.52 = 211,200
             P_o = 1,003,330 lb
             phi P_n,max = 0.65 x 0.80 x 1,003,330 = 521,732 lb
             P_u = 13,117 lb                      ->  d/c 0.025
```

**The 0.80 is not a safety factor; it is an eccentricity.** R22.4.2 records that the 0.80
(tied) and 0.85 (spiral) caps were introduced to replace the explicit minimum-eccentricity
design ACI 318-71 carried, and that they correspond to **e = 0.10h and 0.05h**. So the cap
above already has a **1.20"** eccentricity built into it on the 12" column and **2.00"** on
the 20". That is not trivia — §4e spends it.

### 4e. Slenderness — not neglectable on the 12", and still not binding

`r` = `d`/4 for a circular section, and `k` = 1.0 because **these are leaning columns**.
`structural.lateral_racking` reports both of them as carrying no knee brace, with every pound
of storey shear handed to the braced bays on the deck-and-rail diaphragm claim. A leaning
column is designed non-sway for its own load; the P-Δ it sheds belongs to the bays that brace
it, and **that** is the open question, reported where it belongs rather than smuggled in here.

```
                          PT-SG-COL          PT-SG-FCOL
r = d/4                     3.00"               5.00"
k l_u / r                    42.7                25.6
§6.2.5 non-sway floor          34                  34
                        NOT neglectable      neglectable outright
```

So the 12" column gets magnified (§6.6.4.4.4(a), §6.6.4.5.2):

```
E_c = 57,000 sqrt(3,000)                      = 3,122,019 psi
I_g = pi d^4 / 64                             = 1,017.9 in^4
beta_dns = 1.2 D / P_u = 2,498 / 7,768        = 0.3216
EI = 0.4 E_c I_g / (1 + beta_dns)             = 961.8e6 lb-in^2
P_c = pi^2 EI / (k l_u)^2                     = 577,683 lb
delta_ns = 1 / (1 - P_u / 0.75 P_c) = 1/(1 - 0.0179) = 1.018
```

**A 1.8% magnifier**, because the column is at 4% of its capacity. Now spend §4d's
eccentricity. §6.6.4.5.4 sets a minimum moment `M_2,min = P_u (0.6 + 0.03h)`, i.e. a minimum
eccentricity of `0.6 + 0.03h`:

```
                          PT-SG-COL          PT-SG-FCOL
e_min = 0.6 + 0.03h         0.960"              1.200"
magnified by delta_ns       0.978"              1.205"
e already in the 0.80 cap   1.200"              2.000"
                            COVERED             COVERED
```

**The magnified minimum eccentricity is inside the eccentricity the axial cap was calibrated
for, on both piers.** That is why §4d's single axial comparison is the whole check and no
interaction diagram is needed: the moment case the Code would make us carry is smaller than
the one already priced into the number we compared against.

### 4f. What the spare capacity is NOT an argument for

Both columns land at d/c 0.042 and 0.025 — a factor of 24 and 40. **Nobody should read that
as room to shrink them, and the cage is not what is holding them at this size.**

* `PT-SG-FCOL` is 20" for a **bearing-width** reason: it seats `PT-SG-BF2` on its top as well
  as the two front beams (§1), and that is what took it from 16" to 20".
* `PT-SG-COL` is 12" because that is the smallest sonotube the beam pockets and the HGAM
  gusset's 1½" edge distance will take (`params/sunken_garden.py`, the `CN-SG-TIE-COL` note).
* And the steel is already at the Code minimum, so there is nothing to remove from it. The
  1% floor is not a strength requirement — it is there for creep, shrinkage and the accidental
  moment no analysis names, all of which are indifferent to how lightly the column is loaded.

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
