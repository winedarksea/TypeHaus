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
carry different assemblies for a reason that is not the section — though as of 2026-09-03 it
is no longer a reason about the concrete. `PIER_CONCRETE_12` now names `CATLIN_EXPOSED_MIX`,
the same 5,000 psi F3+C2 galvanized-bar mix `SUNKEN_GARDEN_COLUMN_12` is specified from in
prose. **What it named before was a mix that did not exist:** its source string said
"4,000 psi ... ACI 318-19 class F2", and Table 19.3.2.1 asks 4,500 psi of class F2. Nothing
could see that while the numbers were sentences.

**The two assemblies now differ only in what the engine can READ, and that difference is
live.** `PIER_CONCRETE_12` carries a `ConcreteSpec`; `SUNKEN_GARDEN_COLUMN_12` still carries
only prose, so §4's calculations grade `PT-SG-FCOL` at the presumptive 3,000 psi while
`PT-SG-COL` is graded at the 5,000 both are actually poured from. The front column therefore
reads *weaker* than the back one, which is the opposite of the truth and is an artefact of
the migration being unfinished rather than a finding. Attaching the mix to
`SUNKEN_GARDEN_COLUMN_12` re-oracles `notes/balcony_moment_columns.md`, which is the reason
it is a separate step. Retiring `PT-SG-COL`'s exposed grout island remains open.

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
| handed down by a centre pillar (`FS-SG-DECK` 207.83 / 6) | 34.64 ft² (BR2) | 34.64 ft² (BF2) |
| **tributary** | **116.97 ft²** | **116.97 ft²** |
| column self weight | 1,258 lb | 1,258 lb |
| the pillar's own 6x6, 35 pcf | 67 lb | 66 lb |
| **D** = trib×10 + self + carried | **2,495 lb** | **2,494 lb** |
| **L** = trib×40 | **4,679 lb** | **4,679 lb** |
| **service** D+L | **7,174 lb** | **7,173 lb** |
| **P_u** = 1.2D + 1.6L (IBC §1605.2) | **10,480 lb** | **10,479 lb** |

**`FS-SG-DECK` went 203.00 → 207.83 ft² on 2026-09-03**, when `joist_cantilever_in` went
6" → 9" so the balcony plank would drip clear of the 12" rounds' outer faces rather than
onto them (3" per side is the smallest step that keeps the deck width a whole number of
6" AridDek boards). That is +0.81 ft² of tributary on each of these two piers, and §3c is
where it is felt.

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
             (7,174 + 736) / 4.909  =  1,611 psf   vs 2,000   d/c 0.81   ✓
PT-SG-FCOL   bell 36" = 7.069 ft², 12" thick → 1,060 lb
             (7,173 + 1,060) / 7.069 =  1,165 psf  vs 2,000   d/c 0.58   ✓
```

Both clear, and **the two swapped places on 2026-09-03**. `PT-SG-FCOL` used to be the one to
watch at d/c 0.74; it fell to 0.58 when the column shrank from 20" round to 12" and shed
2,238 lb of its own concrete. `PT-SG-COL` rose from 0.62 to 0.80 when `PT-SG-BR2`'s
share of the balcony was finally handed to it, and to **0.81** when the deck grew to 21'-6"
later the same day. It is the pier with the least margin in this structure — on a 30" bell
against `PT-SG-FCOL`'s 36".

**Any growth in the balcony's loading lands here first, and that is now a live number rather
than a warning.** The deck's 4.83 ft² of new plank cost this pier 8 psf. **Widening the bell
to 36" would take it to 1,165 psf**, and is the obvious move if the balcony grows again; it
is not taken now, because 0.81 against a presumptive allowable with no boring is a screening
margin either way (§6). Two more 3" steps of `joist_cantilever_in` would reach roughly
1,627 psf — still clear, and still the wrong place to spend the margin quietly.

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
§7. `PT-SG-COL` was aligned onto `CATLIN_EXPOSED_MIX` on 2026-09-03 (§2); its exposed grout
island is still an open follow-up.

Both cages are the **minimum the Code permits**, which is the answer the "cheapest concrete"
brief asks for. There is no spare capacity being bought here — see §4d for how little of it
the load actually uses, and §4f for why that is not an argument for less steel.

### 4d. Axial capacity — and the 0.80 is doing more work than it looks

```
phi P_n,max = phi x 0.80 x [ 0.85 f'c (A_g - A_st) + f_y A_st ]
              §22.4.2.1 and Eq. 22.4.2.2; alpha = 0.80 for TIED (Table 22.4.2.1);
              phi = 0.65, compression-controlled tied (Table 21.2.2).
              f_y = 60,000 psi. f'c is now READ PER POUR, and the two differ — see §2.

COL   f'c 5,000 (CATLIN_EXPOSED_MIX, via PIER_CONCRETE_12)
             0.85 x 5,000 x 111.857 = 475,392  +  60,000 x 1.24 =  74,400
             P_o = 549,792 lb
             phi P_n,max = 0.65 x 0.80 x 549,792 = 285,893 lb
             P_u = 10,419 lb                            ->  d/c 0.036

FCOL  f'c 3,000 PRESUMPTIVE (SUNKEN_GARDEN_COLUMN_12 states no ConcreteSpec)
             0.85 x 3,000 x 111.86 = 285,236  +  74,400
             P_o = 359,636 lb
             phi P_n,max = 0.65 x 0.80 x 359,636 = 187,011 lb
             P_u = 10,418 lb                            ->  d/c 0.056
```

**`PT-SG-FCOL`'s 187,011 is not this column's capacity; it is the capacity of the mix the
model can prove.** Both are poured at 5,000, both would read 285,893, and the gap is the
unfinished migration in §2 rather than anything about the concrete. Grading the front column
on the lower number is the conservative direction and is left standing on purpose: an
UNSTATED mix should cost the design something, or nobody ever states it.

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
                                COL (5,000)      FCOL (3,000 presumptive)
E_c = 57,000 sqrt(f'c)          4,030,509 psi     3,122,019 psi
I_g = pi d^4 / 64                 1,017.9 in^4      1,017.9 in^4
beta_dns = 1.2 D / P_u                 0.2864            0.2864
EI = 0.4 E_c I_g / (1+beta)     1,275.7e6         988.3e6 lb-in^2
P_c = pi^2 EI / (k l_u)^2         766,227 lb        593,600 lb
delta_ns = 1/(1 - P_u/0.75 P_c)     1.0185            1.024
```

**A 1.9% magnifier on the back column and 2.4% on the front**, because both are at a few per
cent of capacity. The split is `E_c`, which goes as `sqrt(f'c)`: a stiffer column magnifies
less, so the pour that can prove its mix is rewarded twice — once in §4d's capacity and again
here. Neither figure is near binding. Now spend §4d's
eccentricity. §6.6.4.5.4 sets a minimum moment `M_2,min = P_u (0.6 + 0.03h)`, i.e. a minimum
eccentricity of `0.6 + 0.03h`:

```
                          PT-SG-COL          PT-SG-FCOL
e_min = 0.6 + 0.03h         0.960"              0.960"
magnified by delta_ns       0.978"              0.983"
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

## 5. The bell as a SECTION — flexure and the two shears

§3 asked whether the ground can carry the pressure. It never asked whether the **concrete**
can, and that is half a footing check: soil pressure is a demand on the bell as much as on
the soil, and a bell thin enough to punch through fails at a pressure the ground would have
carried without complaint. Added to `engineering/spread_footing.py` on 2026-09-03
(`BASIS_VERSION` 1 → 2); this section is its oracle, worked by hand in a separate pass.

### 5a. Plain concrete, and that is legal

Neither bell authors reinforcement, and neither needs to. **ACI 318-19 §14.1.4 permits plain
concrete in a footing.** That is a different sentence from §14.1.5, which does not permit a
plain concrete *column* at any stress — the reason `PT-SG-COL` would report INCOMPLETE if its
cage went missing while its bell does not. So the question here is simply whether the plain
section is enough.

Three Code decisions carry the whole derivation, and each is easy to get wrong:

- **The 12" round column becomes an equivalent SQUARE** of the same area (§13.2.7.3):
  `a = sqrt(pi x 12^2 / 4) = 10.635"`, half-side **5.3175"**. Every critical section is
  measured from that square's face.
- **`h` is 10", not 12"** (§14.5.1.7). A plain footing cast against soil gives up 2" of its
  thickness — the Code's allowance for an unformed bottom face poured against dirt. Flexural
  capacity goes as `h²`, so skipping this overstates the section by **44%**.
- **The bell's own weight is EXCLUDED**, unlike in §3. A footing does not punch itself: its
  self-weight goes straight down into the soil directly beneath it, crosses no critical
  perimeter and turns about no column face. §3 includes it because bearing is exactly the
  question of what the soil feels; here it would inflate every demand by about a tenth.

`f'c` is **5,000 psi**. Both bells name `CATLIN_PIER_BASE_12` as of 2026-09-03 — the 12"
plain pour shared with the four breezeway pads — which carries `CATLIN_BURIED_MIX`. Until
then neither `Footing` named an assembly at all and every capacity below was worked at the
presumptive 3,000; **each one in §5c-§5e is therefore 29.1% larger than the figure this note
previously carried**, because every one of them goes as `sqrt(f'c)` and
`sqrt(5000)/sqrt(3000) = 1.291`. The demands did not move: soil pressure does not care what
the concrete is. `sqrt(5000) = 70.711`. `phi = 0.60` throughout, ACI Table 21.2.1.

F0 rather than the court's F3 is earned, not inherited: these two bells carry 42" of true
cover and do not freeze (§5a's levelling-course diagram, and `CATLIN_BURIED_MIX`'s own note).

### 5b. Net pressure

```
                        PT-SG-COL          PT-SG-FCOL
bell diameter               30"                36"
bell area  pi R^2       706.86 in^2       1,017.88 in^2
P_u (§2)                 10,480 lb           10,479 lb
q_u = P_u / A            14.826 psi          10.295 psi   (2,135 / 1,483 psf)
```

### 5c. Two-way (punching) shear — ACI §14.5.5.1(b)

Critical perimeter at `h/2` from the equivalent square's face, i.e. a square of half-side
`5.3175 + 5.0 = 10.3175"`:

```
b_o = 8 x 10.3175                     =  82.54"
area inside = (2 x 10.3175)^2         = 425.75 in^2

V_u = q_u x (A_bell - 425.75)
  COL   14.826 x (706.86 - 425.75)  =  14.826 x 281.11  =  4,168 lb
  FCOL  10.295 x (1,017.88 - 425.75) =  10.295 x 592.13 =  6,096 lb

V_n = (4/3 + 8/3beta) lambda sqrt(f'c) b_o h,  capped at 2.66 lambda sqrt(f'c) b_o h
beta = 1.0 for a square, so the bracket is 4.0 and THE CAP GOVERNS.
phi V_n = 0.60 x 2.66 x 70.711 x 82.54 x 10  =  93,150 lb        (both bells)

  COL   4,168 / 93,150  =  d/c 0.045   OK
  FCOL  6,096 / 93,150  =  d/c 0.065   OK
```

### 5d. One-way shear — ACI §14.5.5.1(a)

Critical section at `h` from the column face, i.e. `5.3175 + 10 = 15.3175"` from the centre.

**On `PT-SG-COL` that falls outside the footing** — a 30" bell has only 15" of radius — so
there is no section to check. The record publishes the state at a zero demand rather than
omitting it: a limit state silently absent reads as one nobody thought of.

On `PT-SG-FCOL` (R = 18"):

```
half-chord = sqrt(18^2 - 15.3175^2) = sqrt(324 - 234.63) = 9.454"   ->  b = 18.91"
segment beyond = R^2 acos(x/R) - x sqrt(R^2 - x^2)
               = 324 x acos(0.85097) - 15.3175 x 9.454
               = 324 x 0.55396 - 144.81  =  179.48 - 144.81  =  34.67 in^2
V_u     = 10.295 x 34.67                        =    357 lb
phi V_n = 0.60 x (4/3) x 70.711 x 18.91 x 10    = 10,697 lb
                                                    d/c 0.033   OK
```

### 5e. Flexure at the column face — ACI §13.2.7.1 / §14.5.2.1(a)

The critical section is the equivalent square's face, `x = 5.3175"` from the centre. The
demand is the soil pressure on the circular segment beyond it, about that section:

```
segment area   A = R^2 acos(x/R) - x sqrt(R^2 - x^2)
segment centroid, FROM THE CENTRE:  xbar = (2/3)(R^2 - x^2)^1.5 / A
arm = xbar - x                     <- about the CUT, not the centre

PT-SG-COL   R = 15"
  sqrt(225 - 28.276) = 14.026 ;  acos(0.35450) = 1.20853 rad
  A    = 225 x 1.20853 - 5.3175 x 14.026  =  271.92 - 74.58  =  197.34 in^2
  xbar = (2/3)(196.72)^1.5 / 197.34 = (2/3)(2,759.2)/197.34  =    9.322"
  arm  = 9.322 - 5.3175                                      =    4.005"
  M_u  = 14.826 x 197.34 x 4.005                             = 11,718 lb-in
  b    = 2 x 14.026 = 28.05"    S_m = b h^2/6 = 28.05 x 100/6 = 467.5 in^3
  phi M_n = 0.60 x 5 x 70.711 x 467.5                        = 99,172 lb-in
                                                                 d/c 0.118   OK

PT-SG-FCOL  R = 18"
  sqrt(324 - 28.276) = 17.196 ;  acos(0.29542) = 1.27078 rad
  A    = 324 x 1.27078 - 5.3175 x 17.196  =  411.73 - 91.44  =  320.29 in^2
  xbar = (2/3)(295.72)^1.5 / 320.29 = (2/3)(5,085.4)/320.29  =   10.585"
  arm  = 10.585 - 5.3175                                     =    5.268"
  M_u  = 10.295 x 320.29 x 5.268                             = 17,371 lb-in
  b    = 2 x 17.196 = 34.39"    S_m = 34.39 x 100/6           = 573.2 in^3
  phi M_n = 0.60 x 5 x 70.711 x 573.2                        = 121,594 lb-in
                                                                 d/c 0.143   OK
```

### 5f. What this says

**Bearing still governs both bells, and by a wider margin than before** — 0.81 and 0.58
against a worst section d/c of 0.14, where the same comparison at the presumptive 3,000 psi
read 0.18. Giving the bells their real mix moved the section states further from governing,
which is the useful direction for a negative result to move: the conclusion below did not
depend on the 29% it gained. The bells are thick relative to their projection (a 9.68" cantilever on
an effective 10" section on `PT-SG-COL`), which is exactly the shape that makes flexure and
shear irrelevant and soil the whole question.

That is a useful negative result rather than a formality. It says the answer to a bearing
problem here is **width, not thickness**: widening `PT-SG-COL`'s bell to 36" — the move §3c
names — takes bearing from 0.81 to 0.58 and takes flexure only from 0.153 to 0.184, still
nowhere near governing. A 36" bell at 12" thick is a sound section, and nobody has to
re-check it after the fact.

---

## 6. What this note does NOT do

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
- **`f'c` was presumptive, and now only where a pour states nothing.** 3,000 psi from IRC
  Table R402.2 was hardcoded for the whole engine; since 2026-09-03 a `ConcreteSpec` on the
  pour's assembly is read instead, and every limit state's prose says which of the two it
  used. `f_y` is still 60,000 psi Grade 60, authored in the cage string and assumed by the
  calculation. MN Rules 1309.0402's **5,000 psi FOOTINGS row** is stated for the strip
  footings and, since 2026-09-03, for the two bells as well (`CATLIN_PIER_BASE_12` ->
  `CATLIN_BURIED_MIX`); whether an augered pier BELL is a "footing" for that amendment is
  still not a question this note answers, and at 5,000 psi either way the answer cannot bind.
  **The one pour still graded on the presumptive value is `SUNKEN_GARDEN_COLUMN_12`** — see
  §2 and §4d.
