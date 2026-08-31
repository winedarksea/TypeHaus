# Sunken-garden piers — the two cast columns and their belled footings

> ## ⚠ A SCREENING. THE GROUND CHECKS OUT; THE COLUMNS ARE NOT FINISHED.
> `PT-SG-COL` (12" round) and `PT-SG-FCOL` (20" round) carry the porch's two beam lines onto
> augered, belled piers. **Bearing on the ground checks out** — 1,245 and 1,477 psf against
> the 2,000 psf IBC Table 1806.2 presumes for this site's GM, so `spread_footing/PT-SG-COL`
> and `/PT-SG-FCOL` report OK.
>
> **The COLUMNS do not, and not because they are overstressed.** They run at about a
> twentieth of their section's capacity. What is missing is reinforcement: ACI 318 does not
> permit a *column* to be plain concrete at any stress, both of these are columns rather than
> pedestals by a wide margin, and `Post` carries no field in which this model could state the
> bars. So `deck_post/*` reports **INCOMPLETE naming that**, which is the honest verdict — a
> check that cannot evaluate says so rather than guessing that a sonotube probably has bars
> in it.

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

## 4. The columns — where this stops being a calculation

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

### 4b. The section is not the problem, and saying so is important

Worked anyway, on ACI 318 §14.5.4's plain-concrete expression (the same one
`retaining_system` uses on the court's strut, and with the same φ = 0.60):

```
φPn = 0.60 × 0.45 f'c Ag [1 − (lc / 32h)²]        f'c = 3,000 psi

PT-SG-COL    Ag 113.1 in²   λ = 1 − (128.19/384)² = 0.8886
             φPn = 0.60 × 0.45 × 3,000 × 113.1 × 0.8886 =  81,400 lb
             Pu 7,768 lb    →  d/c 0.095
PT-SG-FCOL   Ag 314.2 in²   λ = 1 − (128.19/640)² = 0.9599
             φPn = 0.60 × 0.45 × 3,000 × 314.2 × 0.9599 = 244,300 lb
             Pu 13,117 lb   →  d/c 0.054
```

**A factor of ten and of nineteen.** Nobody should read the INCOMPLETE below as "the columns
might be too small" — they are enormous for what they carry, and the front one is 20" for a
*bearing-width* reason (it took on `PT-SG-BF2`), not a stress one.

### 4c. What is actually missing

A column may not be plain concrete, whatever its stress. Per **ACI 318-19 §10.6.1.1** a
12" round column takes at least **1.13 in²** of longitudinal steel and a 20" round at least
**3.14 in²** (0.01 A_g, and not more than 0.08 A_g), plus ties.

**One escape a reviewer will reach for, and it does not reach.** §14.1.2 excludes
*"cast-in-place piles and piers embedded in ground"* from Chapter 14 altogether, and these
are augered piers. But only the **bell** is embedded: the shaft stands free in an open court
for its whole 10'-8", which is the condition §14.1.2 is not describing. **`Post` has no field to record any of it**, so this model cannot state a bar schedule
even if the owner had one — and the calculation refuses to assume that an augered sonotube
"probably" has bars in it. That is #32's rule: a check that cannot evaluate reports UNKNOWN
naming the missing datum, and never a pass.

Two ways to close it, and they are different sizes of job:

1. **The engineer specifies the cages** and they are recorded in `engineering.toml` under
   `deck_post/PT-SG-COL` and `/PT-SG-FCOL`. Nothing in the model changes.
2. **`Post` grows a `vertical_reinforcement` field**, the way `FoundationWall` has one, and
   these two author it. Then the calc can grade the section instead of declining to. That is
   the better answer and it is a schema change, so it is not made here.

---

## 5. What this note does NOT do

- **No moment.** The beams land eccentrically on both columns and nothing here computes the
  resulting bending, the slenderness amplification it would want, or the interaction. Axial
  only.
- **No lateral case.** The porch's own east-west path is open (`plans/TODO.md`), and these
  two columns are part of whatever answers it. Nothing here carries wind or seismic into the
  shafts, and `structural.lateral_racking` already reports both as unbraced leaning columns.
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
- **`f'c` is presumptive.** 3,000 psi from IRC Table R402.2. And note that MN Rules 1309.0402
  amends that table with a **5,000 psi FOOTINGS row**; whether an augered pier bell is a
  "footing" for that amendment is not a question this note answers, and it should be asked
  before anyone orders concrete.
