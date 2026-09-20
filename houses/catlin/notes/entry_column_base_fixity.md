# Base fixity of the cast columns — IBC 1807.3.2.1, hand-worked

**Oracle for** `engineering/column_base.py` and `engineering/spread_base.py` (§§1-6, §8),
and for `engineering/diaphragm_basis.py`, `engineering/lateral_lines.py` and
`engineering/lateral_system.py` (§7). Reproduced by `tests/test_column_base_calcs.py` and
`tests/test_lateral_system_calcs.py`. Worked 2026-09-18 and revised 2026-09-19, each time in
a separate pass from the code.

**2026-09-19 revision, in one paragraph.** The canopy's frame shear stopped being loaded
wholly onto its two cast columns and is now shared with `W-BW-SCREEN` and the deck by
relative rigidity, IBC 2018 §1604.4 (§7). `PT-BW-RE` went from **FAIL at d/c 1.32** to a
§1806.3.4 straddle at **1.02**; `PT-BW-RNE` went from **2.31 to 2.21** and is still the open
item. Two of the closures §6 listed on 2026-09-18 turned out not to be what they looked like:
6d is implemented rather than refused, and 6f — crediting `PD-BW-RNE`'s declared monolithic
pour — **does not exist**, because the garage strip footings it names became crushed stone
under IRC R403.5 on 2026-09-15.

**What this note is about.** Six cast columns in this house are their structure's lateral
system, and every one of their `deck_post` records has carried this sentence since
2026-09-11:

> SCREENING: the base is taken as FIXED, which the doweled lap into the footing is detailed
> to deliver and which no calculation here proves — nothing here grades the EMBEDMENT that
> fixity needs against IBC 1807.3.2.1, and on a shallow-founded column that is the
> assumption most likely to be the weak one.

It was right about which assumption was weak. `notes/north_entry_piers.md` §8d put a rough
number on it — "4'-6" of embedment against roughly 5'-6" that the non-constrained formula
wants" — and never worked it. Worked properly, **the shortfall is larger than that**, and on
the two canopy columns it is a FAIL rather than a margin.

---

## 1. The provision, and why it is the non-constrained case

IBC 2018 §1807.3.2.1, poles **not** constrained at the ground surface:

```
d = 0.5 A { 1 + [ 1 + (4.36 h / A) ]^(1/2) }          A = 2.34 P / (S1 b)
```

* `P` — the applied lateral force, **lb, at allowable stress**. §1806.2's lateral bearing
  values are allowables; putting a strength-level shear into them would overstate the demand
  by a third and make the answer meaningless in the safe direction.
* `h` — the distance from **grade** to the point of application of `P`, ft.
* `b` — the diameter of a round post, ft. 1.00' here.
* `S1` — the allowable lateral soil bearing **at one third the embedment depth**, so `S1`
  depends on `d` and the pair is solved by iteration rather than in closed form. Class 4
  (GM, `Site.soil_class`) is **150 psf per foot of depth**, IBC Table 1806.2.
* `d` — the required embedment, ft.

**Non-constrained, not constrained, and the distinction is not academic.** §1807.3.2.2's
constrained formula applies where the pole is restrained at grade by a slab, a pavement or a
grade beam. Nothing restrains these: the canopy columns stand out of open ground with a
gravel apron around them. Taking the constrained case would roughly halve the required
depth and would be reading a provision about a structure this is not.

**§1806.3.4's doubling is a judgement about the building, not about the soil.** The section
permits the lateral bearing value to be doubled for an isolated pole "not adversely affected
by a 1/2 inch motion at the ground surface". Whether half an inch of sway at the base of a
canopy column — with an `HGAM10` gusset and a stainless standoff shim pack at its head —
harms what stands on it is a question about the structure. So both ends are worked below and
the verdict is only published where they agree; where they straddle, the record reports
INCOMPLETE naming the judgement. That is the same convention `retaining_wall` applies to the
soil unit weight band, for the same reason.

## 2. The demand, and who carries it

`notes/north_entry_piers.md` §8b derives the canopy's frame shear. **Until 2026-09-19 the
whole of it went on the two cast columns** — 1,360 lb ASD, N-S governing, 680 lb each —
because relative rigidity against `W-BW-SCREEN` was "a judgement the engine does not make".
That sentence was doing two jobs. Refusing to *guess* a panel's stiffness is right; a wall's
racking stiffness is a property of its FASTENER SCHEDULE and no geometry records one. But
once the schedule is written down, distributing by rigidity is **IBC 2018 §1604.4** in as
many words: *"The total lateral force shall be distributed to the various vertical elements
of the lateral force-resisting system in proportion to their rigidities, considering the
rigidity of the horizontal bracing system or diaphragm."*

§7 below works that distribution by hand. What comes out of it, and what this section now
takes as the demand:

| column | axis that governs | base shear (ASD) | base moment (ASD) | effective arm | `h` above grade |
|---|---|---:|---:|---:|---:|
| `PT-BW-RE` | **E-W** | 379 lb | 4,940 lb-ft | 13.02' | 6.90' |
| `PT-BW-RNE` | **E-W** | 613 lb | 6,866 lb-ft | 11.20' | 7.70' |

Three things moved at once and all three are §7's:

1. **N-S is shared and E-W is not.** `W-BW-SCREEN` runs north-south, so it resists
   north-south wind and nothing else. The north-south case drops to 14% and 24% on the two
   columns; the east-west case is still theirs alone, and it is now what governs both. The
   canopy's E-W lateral system was always only these two columns and nothing in the model
   said so out loud until the split was computed.
2. **The two columns stop sharing equally.** `PT-BW-RNE` is 12.73' from base to head against
   `PT-BW-RE`'s 15.35', and a cantilever's stiffness goes as `1/h³`, so the short one is
   1.75x the stiff one and takes 64% of the east-west case. That is why the WORSE column got
   worse in relative terms even as the total came down.
3. **The column drag stops being a cantilever load.** Wind on the shaft between grade and
   the roof reaches the base alone only while the head is free. With a diaphragm holding the
   head the shaft is a PROPPED cantilever, and 182 lb applied at 9.96' on a 15.35' shaft
   makes 523 lb-ft at the base instead of 1,807. The balance goes UP into the deck, where it
   is distributed with everything else. That is not a discount applied to the old free body;
   it is the free body the declaration creates.

`Site.grade` is **-2'-10"** and the top of `PD-BW-RE` is at **-8'-11 3/8"**, so that column
is embedded **6.12'**. `PT-BW-RNE` is on the garage side, its pad top is at **-6'-4"**, and
it has **3.50'**.

The four landing columns (`PT-BW-W`/`-E`/`-GW`/`-GE`) are a different structure —
`FS-BW-FLOOR`, whose governing lateral case is not wind but the **IRC R301.5 guard load**,
200 lb at the top of the rail, taken wholly on one column. Its arm above grade is 4.54', and
nothing in this revision touches it: a guard load is delivered at a rail, not at a diaphragm.

## 3. The arithmetic, iterated

`S1 = 150 d / 3 = 50 d`, so `A = 2.34 P / (50 d)`. Starting at `d = 1'` and iterating to
four figures:

```
PT-BW-RE       P = 379.4 lb,  h = 6.898',  b = 1.00'
  A = 17.758 / d                  4.36 h = 30.076
  d = 0.5 A [1 + sqrt(1 + 30.076/A)]
       d = 6.200 -> A = 2.8642 -> d = 6.289
       d = 6.289 -> A = 2.8236 -> d = 6.231
       d = 6.231 -> A = 2.8499 -> d = 6.268
       ...converges                d = 6.25'
  at 2 S1 (§1806.3.4):  A = 8.879 / d       converges   d = 4.78'

PT-BW-RNE      P = 612.9 lb,  h = 7.702',  b = 1.00'
  A = 28.683 / d                  4.36 h = 33.581
       d = 7.700 -> A = 3.7251 -> d = 7.757
       d = 7.757 -> A = 3.6977 -> d = 7.719
       ...converges                d = 7.74'
  at 2 S1                                              d = 5.90'

the four landing columns  P = 200 lb,  h = 4.54',  b = 1.00'
  A = 9.36 / d
  d = 0.5 A [1 + sqrt(1 + 19.79/A)]          converges  d = 4.45'
  at 2 S1                                               d = 3.39'
```

## 4. The verdicts

| column | carries | embedment | needs (S1) | needs (2 S1) | verdict |
|---|---|---:|---:|---:|---:|
| `PT-BW-RE` | canopy, east | 6.12' | 6.25' | 4.78' | **INCOMPLETE** (1.02 / 0.78) |
| `PT-BW-RNE` | canopy, east | 3.50' | 7.74' | 5.90' | **OVER, d/c 2.21** |
| `PT-BW-W` | landing, guard | 6.12' | 4.45' | 3.39' | ok, 0.73 |
| `PT-BW-E` | landing, guard | 6.12' | 4.45' | 3.39' | ok, 0.73 |
| `PT-BW-GW` | landing, guard | 3.50' | 4.45' | 3.39' | **INCOMPLETE** |
| `PT-BW-GE` | landing, guard | 3.50' | 4.45' | 3.39' | **INCOMPLETE** |

**`PT-BW-RE` moved from a published FAIL to the band convention's own INCOMPLETE**, and the
distance it moved is the whole of §7: 8.08' of required embedment became 6.25' against the
6.12' it has. It is 1 1/2 inches short at the table's lateral bearing and 1'-4" clear at
§1806.3.4's isolated-pole double, so the two ends straddle and the verdict turns on the one
question this engine will not answer for anybody — whether half an inch of motion at the
ground surface harms a canopy header and the standoff shims under it. It very likely does
not, and it is still a judgement. **A reader should not read that INCOMPLETE as "nearly
passes"**: at 1.02 the honest description is "exactly at the line, and the line is drawn on
presumptive soil with no boring behind it."

**`PT-BW-RNE` is still OVER and the margin is not a detail.** It needs 7.74' and has 3.50' —
2.2 times. Nothing in §7 can close that, and the reason is arithmetic rather than bad luck:
it is the SHORT column, a cantilever's stiffness goes as `1/h³`, so relative-rigidity
distribution hands it the larger share of exactly the case nobody else resists. Even a
column carrying *only its own wind drag* and no share at all of the roof's needs 4.1' at this
embedment. **3'-6" is not a fixed base at any load worth the name**, and §6 is where that
has to be settled.

## 5. What this does NOT settle

- **How the base moment SPLITS between the buried shaft and the pad.** These are alternative
  load paths for one moment and not additive ones: a shaft that turns in soil sheds its
  moment into lateral bearing, and a pad that resists by bearing does so because the shaft
  above it does not. Adding them counts the same moment twice. The split is a soil-structure
  stiffness problem and nothing here computes it.
- **That the pad is not the mechanism is itself worth stating**, and since 2026-09-19 the
  record states it in graded arithmetic rather than prose — see §8. `PT-BW-RE`'s resultant
  sits **0.79'** off the footprint centroid against a kern of **0.42'**, so the base would
  lift at one edge before it did anything about the moment.
- **Rotational stiffness.** This grades whether the base can turn the shear around, not how
  far it rotates first. `deck_post`'s sway magnifier assumes a base that does not rotate,
  and a real one does.
- **Group effect** with the pier line beside it, **passive resistance on the pad's own
  faces** (neglected, the conservative direction), and the **long-term modulus** the
  magnifier implicitly assumes.
- **Seismic.** `notes/balcony_moment_columns.md` §9 names the site-specific hazard lookup as
  an external deliverable and that is unchanged.

## 6. What closes it, worked

**Nothing here is decided.** Five closures have now been worked rather than listed, and the
scoreboard has changed twice: 6d was written off on 2026-09-18 as "a relative-rigidity
judgement this engine refuses to make" and is now §7, implemented; and 6f, the one the
2026-09-19 plan expected to carry `PT-BW-RNE`, turns out not to exist at all.

### 6a. Deepen the two canopy shafts — works, and the cost moved

`PT-BW-RE` needs 6.25' against 6.12'; `PT-BW-RNE` needs 7.74' against 3.50'.

**The required depth does not chase the embedment.** `h` is measured from grade to the point
of application, and both the header and the drag resultant stand at fixed elevations, so `h`
is invariant under deepening and `d` is a fixed target rather than an iteration.

* **`PD-BW-RE` is 1 1/2 inches short.** Its pad top would go from -8'-11 3/8" to -9'-1", its
  bottom to -10'-1". That is 3 3/4" below `FT-B-N1..N4`'s -9'-9 7/16" plane, 1 1/16" away in
  plan — a benching question in an excavation that is already open, not undermining, and by
  far the cheapest closure on this page. It costs 0.005 cy of concrete and one dimension.
  **What it also does is stop the record straddling §1806.3.4**, which is worth more than
  the inch and a half: the verdict becomes published rather than deferred to a judgement.
* **`PD-BW-RNE` needs 4'-3" more**, its pad top at -10'-7" and its bottom at -11'-7". The
  2026-09-18 reading of that was "4.9' below the garage strip footing it declares
  `cast_with`", which is undermining. **That reading is out of date and the reason is 6f.**
* **`PD-BW-RE` goes from 0.94 to about 0.95 on bearing**, not the 0.984 the deeper version in
  the 2026-09-18 note reached — 3 3/4" of extra shaft is 37 lb, not 231. It is still the
  tightest pad in the house.
* It still **adds a row to S-100** if the two house-side pads stop sharing a bearing
  elevation: `emit/draw/foundation_schedule._pad_key` carries it, and that sheet is 0.18"
  from its own schedule governing its height.

### 6b. Constrain the base at grade — still not available

Unchanged from 2026-09-18 and still the closure that would be dishonest. IBC 2018 §1807.3.2.2
applies "where lateral constraint is provided at the ground surface, such as by a rigid floor
or pavement", and these columns stand in open ground with a gravel apron. A strut between the
two columns restrains nothing: they stand on one N-S line and would lean together. To be
constrained the strut has to reach a mass — `PT-BW-RE` south to `W-B-N2/N3`, 10 3/4" away, or
`PT-BW-RNE` north into the garage stem — and both reverse the premises this design is built
on and put a rigid prop across the only movement joint. §6e's first bullet is about this.

At the reduced demand the constrained formula (Eq. 18-3, `S3` at the FULL depth) gives
`PT-BW-RE` `d = (4.25 M_g / (150))^(1/3)` with `M_g = 379.4 x 6.898 = 2,617 lb-ft`, i.e.
`d³ = 74.1`, `d = 4.20'` — comfortable. It is still a provision about a structure this is
not, and the arithmetic being comfortable is exactly why it has to stay refused.

### 6c. Brace the frame — closes both, and moves no geometry

A knee-braced portal with pinned bases develops **no base moment at all**; the columns revert
to leaning columns and `deck_post` grades them axially. Nothing is undermined, no pad changes
size or elevation, no row is added to S-100, and the owner has already accepted knee braces
here as a fallback.

**Two things it still owes, and one of them is new since §7 landed.** The old one: a pinned
base still delivers horizontal force at grade, and nothing in this engine grades that path —
pad friction plus passive on the pad faces is on the order of 1,750 lb against roughly 500
here, comfortable and not a calculation. The new one is worse. `pier_basis.knee_braced()`
short-circuits `roof_base_moments` **wholesale for the structure**, so one brace on this
canopy deletes both columns' records — `PT-BW-RE`'s included, the one that is now within an
inch and a half. After 6c the register would show no base-fixity question on a canopy that
demonstrably has one, which is §6e's third bullet exactly.

**The connector is still not solved.** `KBS1Z` is wood-to-wood and `APVKB45-6` is unrated in
ER-102 and ER-280. A knee brace landing on a 12" cast round needs a real part — a
through-bolted plate or a concrete-screw bracket at >= 3" edge distance, the family the
`HGAM10` head already uses — and `structural.lateral_racking` reports UNKNOWN for a brace
with no published lateral capacity, so this closure does not open the permit gate either.

### 6d. Share the shear with the panel and the deck — **DONE, and it is §7**

This was written on 2026-09-18 as "a relative-rigidity judgement, which is why this engine
refuses to make it ... the first question to put to the engineer of record, because it is the
only closure with no construction cost."

It is implemented. What made it available was separating two things the old sentence ran
together: *guessing* a panel's stiffness (still refused — `ShearPanelSpec` and `DiaphragmSpec`
are authored, with the SDPWS rows they are read at) from *distributing* by stiffness once
those are stated (IBC 2018 §1604.4, and not a judgement at all). §7 is the hand-working.

**It is not free, and the cost is parts rather than concrete.** The deck now has to BE a
diaphragm: blocked at every panel edge, a continuous chord at each end, a collector at each
header. `engineering/lateral_system.py` grades all of it and `AN-BW-ROOF` has to carry it.
The deck lands at **exactly 4.00** on SDPWS Table 4.2.4's blocked span-to-depth limit — 24'
between the lines over 6' of depth — so unblocked it would be a FAIL, and the blocking is
load-bearing in the literal sense.

It closes `PT-BW-RE` to within an inch and a half. **It does not close `PT-BW-RNE`** and
cannot: see §4.

### 6f. Credit the pour that is already one — **NOT AVAILABLE, and this is a correction**

The 2026-09-19 plan proposed crediting `PD-BW-RNE`'s declared `cast_with` as a combined
footing: it is cast monolithic with `FT-GF-S3` + `FT-GF-E` at the corner where the garage's
E-W south run meets its N-S east return, so the union has the lever arm the overturning
wants. The mechanism is real and it is implemented (`engineering/spread_base.py`, §8).

**The premise is false, and it has been false since 2026-09-15.** `FT-GF-S1` … `FT-GF-W` are
**crushed-stone footings** under IRC R403.5 — `params/foundations.py` retyped all nine on
2026-09-15, five days after `PD-BW-RNE` declared it was cast with two of them. Nothing is
cast monolithically with consolidated stone. The `cast_with` declaration on the three
garage-side pads survived that retype and now says something untrue about how the concrete is
placed; `engineering/spread_base.pours_for` refuses any named pour whose `Footing.material`
is not concrete, by name, rather than quietly crediting a smaller footprint.

So the combined-footing route reaches `PD-BW-RE` and not `PD-BW-RNE`, and §8 shows it does
not reach far enough there either.

### 6g. What would make a closure dishonest

* **Claiming "constrained" without modelling the restraint.** There is no constrained branch
  in `column_base.py` and no field naming a restraining element. Hand-swapping the formula
  more than halves a required depth on the strength of prose — see the numbers in 6b.
* **Authoring a `KneeBrace` to silence the check.** `pier_basis.knee_braced()` short-circuits
  `roof_base_moments` wholesale, so one element deletes every `column_base`, `base_rotation`
  and `column_head_joint` item and `deck_post`'s moment records in a single edit, at 0 FAIL —
  and a brace with an empty `connects` matches by plan centre, so a sloppy one can silence a
  column it was never attached to. Author `connects`, and assert the surviving item set.
* **Letting the item's disappearance read as a pass.** After 6c there is no fixed base to
  grade, and the gate opens because the question left rather than because it was answered.
* **Declaring a diaphragm to get §7's reduction without building one.** The reduction is
  bought entirely from blocking, chords and collectors. A `DiaphragmSpec` on a deck nobody
  blocks is the same act as claiming "constrained" — and it is graded, which is the point of
  `lateral_system/<roof>` existing at all.
* **Leaving a stale `cast_with` in place.** 6f is the live example. A declaration that was
  true when it was written and is not true now reads exactly like one that is.
* **`h` is measured from the single global `Site.grade`.** A local apron or regrade at the
  canopy is invisible to the model and would change `h`, and so `d`, with no finding.

## 7. The shear split, hand-worked

**Oracle for** `engineering/diaphragm_basis.py`, `engineering/lateral_lines.py` and
`engineering/lateral_system.py`. Reproduced by `tests/test_lateral_system_calcs.py`.

### 7a. The wind, unchanged

`q_h = 18.335 psf` at 21.52' above the ground beneath (12.396' ridge, -9.120' ground),
`G = 0.85`, `C_f = 1.80` — the §29.3 solid-sign surrogate `roof_moment` uses because ASCE
7-16 Fig. 27.3-4's free-roof `C_N` is not a grid this repository holds — and `0.6` for ASD.
The product is **16.831 psf** of ASD pressure on any projected band.

| case | bands | area |
|---|---|---:|
| **E-W** (`x`) | slope rise 4.444' x 6.000' = 26.67 sf; `BM-BW-RE` 0.938' x 5.719' = 5.36 sf; `BM-BW-RW` the same | **37.39 sf** |
| **N-S** (`y`) | gable-end triangle 2.222' x 26.667' | **59.26 sf** |
| column drag | two 1.00' rounds x 10.785' exposed | **21.57 sf** |

```
top shear, E-W   16.831 x 37.39 =   629.3 lb
top shear, N-S   16.831 x 59.26 =   997.4 lb
drag             16.831 x 21.57 =   363.0 lb   (181.5 lb per column)
```

### 7b. The propped shaft

A shaft fixed at its base and held at its head by the deck, one load `P` at `a` above the
base, total height `H`:

```
R_head = P a^2 (3H - a) / (2 H^3)        M_base = P a (H^2 - a^2) / (2 H^2)
```

`a = H - 10.785/2 = H - 5.392`.

```
PT-BW-RE    H = 15.349', a = 9.957'   ->  M_base = 523.4 lb-ft   R_head =  89.8 lb
PT-BW-RNE   H = 12.729', a =  7.337'  ->  M_base = 444.6 lb-ft   R_head =  73.1 lb
```

Those two head reactions join the deck, so the shear the diaphragm distributes is

```
E-W   629.3 + 162.9 =   792.2 lb           N-S   997.4 + 162.9 = 1,160.3 lb
```

### 7c. The stiffnesses

Cantilever `3EI/h³`. `PIER_CONCRETE_12` specifies f'c 5,000 psi, so `E = 57,000 sqrt(5000) =
4.031e6 psi`; a 12" round has `I = pi d^4 / 64 = 1,017.9 in^4` (gross — ACI 318-19 §6.6.3.1.1
permits 0.70 I_g, and taking the gross section makes the column stiffer and so hands it MORE
shear, which is the end that does not flatter the member being graded).

```
PT-BW-RE    h = 184.19"   k = 3(4.031e6)(1017.9) / 184.19^3 = 1,970 lb/in
PT-BW-RNE   h = 152.75"   k =                                 3,453 lb/in
```

`W-BW-SCREEN` by SDPWS 4.3.2, `delta = 8vh³/(EAb) + vh/(1000 G_a) + h d_a / b`, on
6.573' x 4.083' with `G_a = 11 kips/in`, chords 2-2x4 (`A = 10.5 in²`, `E = 1.4e6 psi`) and
`d_a = 1/16"`.

**Its stiffness and its share are each other's input**, because SDPWS states the anchorage
term as a displacement AT the design shear rather than as a rate: push the panel harder and
the fixed 1/16" of take-up is a smaller fraction of a larger deflection, so it reads
stiffer. The pair is iterated from an equal share until it stops moving — three passes here.
At the share it settles on, 62.4% of the N-S case (724 lb, `v = 110.2 plf`):

```
bending   8(110.2)(4.083^3) / (1.4e6 x 10.5 x 6.573)  = 0.0006"
shear     110.2 x 4.083 / (1000 x 11)                 = 0.0409"
rotation  4.083 x 0.0625 / 6.573                      = 0.0388"
                                               delta  = 0.0803"  ->  k = 9,017 lb/in
```

**The panel is evaluated a second time, at a different share, and that is deliberate.** ACI
318-19 §6.6.3.1.1 permits 0.70 I_g for a column in a lateral analysis, and which end of that
band is conservative depends on which member is being graded: gross columns are stiff and
take more (the column's own worse end, used above), cracked columns are soft and shed onto
the panel (the PANEL's worse end). At 0.70 I_g the columns fall to 1,379 and 2,417 lb/in,
the panel's share rises to **71.7%** — 832 lb, `v = 126.6 plf` — and §7f grades the panel
there.

### 7d. Rigid or flexible, and it is decided rather than assumed

ASCE 7-16 §26.2 calls a diaphragm flexible when its own midspan deflection exceeds **twice**
the average storey drift of the vertical elements. Both are evaluated at the TRIBUTARY
distribution — the idealization under test — so the answer does not depend on the assumption
being tested. SDPWS 4.2.2 for the deck, with a 2x4 chord (`A = 5.25 in²`) and 0.03" of splice
slip at the peak:

```
N-S   L = 24.0', W = 6.0', v = 0.5(1160.3)/6.0 = 96.7 plf
      bending  5(96.7)(24^3) / (8 x 1.4e6 x 5.25 x 6.0)  = 0.0189"
      shear    0.25(96.7)(24) / (1000 x 12)              = 0.0483"
      splice                                             = 0.0300"
                                          delta_diaphragm = 0.0973"
      average line drift (tributary)                      = 0.0986"
                                        ratio 0.99x  ->  RIGID

E-W   L = 4.979', W = 26.667'   delta_diaphragm = 0.0315"   drift = 0.1579"
                                        ratio 0.20x  ->  RIGID
```

Both cases are rigid, and only one of them with room. **The N-S margin is the one to watch:
at 0.99x it is a factor of two from flipping to tributary**, which would take the two
columns from 14%/24% to 25% each and put `PT-BW-RE` back over. A softer deck, a thinner
chord or a sloppier splice all push that way.

### 7e. The shares, and what they leave at each base

```
N-S   sum k = 1,970 + 3,453 + 9,017 = 14,440
      PT-BW-RE  13.6%   PT-BW-RNE  23.9%   W-BW-SCREEN  62.4%
E-W   sum k = 1,970 + 3,453 =  5,423     (the panel runs N-S and resists nothing here)
      PT-BW-RE  36.3%   PT-BW-RNE  63.7%
```

E-W governs both columns, and the base demands follow:

```
PT-BW-RE    top 0.3632 x 792.2 = 287.7 lb   M = 287.7(15.349) + 523.4 = 4,940 lb-ft
            base shear 287.7 + (181.5 - 89.8) = 379.4 lb      arm 13.02'
PT-BW-RNE   top 0.6368 x 792.2 = 504.4 lb   M = 504.4(12.729) + 444.6 = 6,866 lb-ft
            base shear 504.4 + (181.5 - 73.1) = 612.9 lb      arm 11.20'
```

### 7f. What the deck and the panel owe for it

```
deck span-to-depth   24.0 / 6.0                              = 4.00  vs 4.00 blocked  (1.00)
deck unit shear      0.6243 x 1,160.3 / 6.0                  = 120.7 plf vs 190       (0.64)
deck chord force     1,160.3 x 24.0 / (8 x 6.0)              = 580 lb  -- NOT graded
panel unit shear     832 / 6.573                             = 126.6 plf vs 182.5     (0.69)
panel aspect ratio   4.083 / 6.573                           = 0.62  vs 3.5           (0.18)
panel hold-down      832 x 4.083 / 6.573                     = 517 lb vs 2,190 ABU66SS (0.24)
```

The hold-down is the `ABU66SS` standoff base already under each 6x6 — 2,190 lb of published
uplift, Simpson letter L-F-SSNAILS23 against the ABU66 row of ESR-1622 — and **no dead load
is credited against the overturning couple**, which is a bound rather than an approximation
and clears by a factor of four anyway. What ESR-1622 §5.6 does not cover is the anchor bolt
and the concrete under it; that link is an ACI 318 Ch. 17 design and the record says so.

**The span-to-depth row is the one to read twice.** 4.00 against a limit of 4.00 is a pass
with no margin at all, on a deck whose depth is fixed by the passage and whose span is fixed
by the columns. Unblocked the limit is 3.0 and this is a FAIL. There is nothing to trade.

## 8. The spread base, worked — and why neither column uses it

`engineering/spread_base.py` grades a base as a rigid body on soil: eccentricity against the
kern, peak bearing against the presumptive allowable, and a factor of safety against
overturning. Where a `Pad` names `cast_with` pours it works the UNION — ACI 318-19 §13.3.4's
combined footing — on the polygon's real area, centroid and second moment. §13.3.4.3 forbids
assuming a uniform pressure under one and none is assumed: the distribution is the rigid-body
linear one, and where the resultant leaves the kern no pressure is published at all.

**Which mechanism is GRADED is authored** (`Pad.resists_base_moment`) and it is never
"whichever passes". An embedded shaft and a spread base are alternative paths for one moment,
and adding them counts it twice.

`PD-BW-RE`, on its own 30" x 18" footprint about the governing E-W axis:

```
area 3.75 ft2   centroid +30.00'   I = 1.953 ft4   kern = I/(c A) = 0.417'
vertical 5,719 lb  =  5,156 service on the column  +  563 of pad, at its OWN centroid
                                                                 M 4,940 lb-ft ASD
eccentricity 0.86' > 0.417'  ->  the base LIFTS at one edge; no linear pressure applies
FS overturning about the high edge at +31.25'   7,148 / 4,940     = 1.45  (< 1.5)
```

So **`PD-BW-RE` would fail BOTH graded states** if it claimed the mechanism — eccentricity at
2.07 and overturning at 1.03 — and no bearing pressure would be published at all, because
outside the kern the linear distribution it would be graded against does not describe the
contact. `resists_base_moment` stays unset, the embedment stays the graded mechanism, and
this arithmetic is printed on the record as the evidence that the choice is right.

**The pad's own weight is counted once, at its own centroid.** That is worth saying because
it was counted twice for an afternoon: the column's service axial already carries the base
slab in `column_base`'s evidence line, and `spread_base.analyse` weighs every pour in the
footprint independently. The padded figure read 6,281 lb under a base that weighs 5,719 and
put the second copy on the COLUMN's lever rather than on its own, which on a combined
footing — where the two are nowhere near each other — is the whole mechanism being graded.

**`PD-BW-RNE` cannot use it at all**, per §6f: the two pours it names are crushed stone.

**And extending `PD-BW-RE` north into `FT-B-N1..N4` would not rescue it either**, which is
worth working because it was the 2026-09-19 plan's step 3. Three reasons, in the order they
bite:

1. **The kern does not move.** For a rectangle the kern about the E-W axis is `L_x/6` —
   independent of the N-S dimension entirely. Growing the pad northward adds area and second
   moment in exactly the same proportion, and `e` is measured against a distance that has not
   changed.
2. **The overturning lever does not move either, in the direction that governs.** The union
   grows NORTH; the lever from the column to the SOUTH edge is still 9". Wind reverses, so
   both directions have to work, and a footprint extended one way answers one of them.
3. **Crediting the whole of a continuous strip is not defensible anyway.** How much of a
   forty-foot strip footing belongs to one column's combined footing is a DESIGN decision —
   the length over which the two loads are taken to act together — and no geometry answers
   it. `spread_base` will compute it if asked; a reviewer should refuse it. The module's own
   docstring says so.

What extending north *would* do is add weight, which lowers `e` — and that is the one term
it helps. It is not enough to cross the kern, and it would end "the canopy is freestanding /
the landing touches nothing on the house" to do it. That premise reversal is the owner's to
make and there is no reason on this page to ask for it.

## Sources

- IBC 2018 §1807.3.2.1, §1807.3.2.2 (Eq. 18-3, S3 at the FULL depth), §1806.2 Table,
  §1806.3.4. Text confirmed 2026-09-18 against ICC Digital Codes, UpCodes and the 2015
  Seattle Building Code's verbatim reproduction of Chapter 18.
- `notes/north_entry_piers.md` §8b (the frame shear and the base moments), §6 (why the two
  pier lines bottom at different elevations), §8d (the prose this note replaces).
- `notes/balcony_moment_columns.md` §2c (the guard load taken wholly on one column).
