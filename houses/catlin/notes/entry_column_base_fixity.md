# Base fixity of the cast columns — IBC 1807.3.2.1, hand-worked

**Oracle for** `engineering/column_base.py`. Reproduced by
`tests/test_column_base_calcs.py`. Worked 2026-09-18 in a separate pass from the code.

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

## 2. The demand

`notes/north_entry_piers.md` §8b derives the canopy's frame shear: **1,360 lb ASD**, N-S
governing, taken wholly on the two cast columns because relative rigidity against
`W-BW-SCREEN` is a judgement the engine does not make. **680 lb each.**

`h` is measured from grade, and the moment those two shears produce is the thing that has to
be preserved when they are collapsed into one force at one arm. §8b's table gives
`PT-BW-RE` a base moment of **9,461 lb-ft ASD** about its own base, so the equivalent single
arm about the base is `9,461 / 680 = 13.91'`. `Site.grade` is **-2'-10"** and the top of
`PD-BW-RE` is at **-8'-11 3/8"**, so the column is embedded **6.12'** and

```
h = 13.91 - 6.12 = 7.79' above grade
```

`PT-BW-RNE` carries the same 680 lb at the same absolute elevation, so its `h` is the same
7.79'. What differs is its embedment: it is on the garage side, its pad top is at **-6'-4"**,
and it has **3.50'**.

The four landing columns (`PT-BW-W`/`-E`/`-GW`/`-GE`) are a different structure —
`FS-BW-FLOOR`, whose governing lateral case is not wind but the **IRC R301.5 guard load**,
200 lb at the top of the rail, taken wholly on one column. Its arm above grade is 4.54'.

## 3. The arithmetic, iterated

`S1 = 150 d / 3 = 50 d`, so `A = 2.34 P / (50 d)`. Starting at `d = 1'` and iterating to
four figures:

```
PT-BW-RE / -RNE      P = 680 lb,  h = 7.79',  b = 1.00'
  A = 31.82 / d
  d = 0.5 A [1 + sqrt(1 + 33.96/A)]
       d = 8.000 -> A = 3.978 -> d = 8.133
       d = 8.133 -> A = 3.913 -> d = 8.043
       d = 8.043 -> A = 3.957 -> d = 8.104
       ...converges                d = 8.08'

  at 2 S1 (§1806.3.4):  A = 15.91 / d       converges   d = 6.15'

the four landing columns  P = 200 lb,  h = 4.54',  b = 1.00'
  A = 9.36 / d
  d = 0.5 A [1 + sqrt(1 + 19.79/A)]          converges  d = 4.45'
  at 2 S1                                               d = 3.39'
```

## 4. The verdicts

| column | carries | embedment | needs (S1) | needs (2 S1) | verdict |
|---|---|---|---:|---:|---:|
| `PT-BW-RE` | canopy, east | 6.12' | 8.08' | 6.15' | **OVER, d/c 1.32** |
| `PT-BW-RNE` | canopy, east | 3.50' | 8.08' | 6.15' | **OVER, d/c 2.31** |
| `PT-BW-W` | landing, guard | 6.12' | 4.45' | 3.39' | ok, 0.73 |
| `PT-BW-E` | landing, guard | 6.12' | 4.45' | 3.39' | ok, 0.73 |
| `PT-BW-GW` | landing, guard | 3.50' | 4.45' | 3.39' | **INCOMPLETE** |
| `PT-BW-GE` | landing, guard | 3.50' | 4.45' | 3.39' | **INCOMPLETE** |

**Both canopy columns fail at BOTH ends of §1806.3.4**, so the doubling is not the question
there and the verdict is published: the north entry canopy's assumed fixed base is not
delivered by the ground it stands in. `PT-BW-RNE` is the worse of the two by a wide margin
and for a reason that has nothing to do with its load: the garage-side pier line stops at
-7'-0", the garage strip footing's own underside, where the house-side line reaches
-9'-9 7/16" because the basement excavation was already open to it
(`notes/north_entry_piers.md` §6).

**The two garage-side landing columns straddle it**, which is exactly the case the band
convention exists for: 3.50' of embedment against 4.45' needed at the table value and 3.39'
at the double. Somebody has to decide whether half an inch of motion at grade matters to a
landing guard rail. It very likely does not — a guard is a serviceability element and R301.5
is a life-safety load, not a stiffness one — but that is a judgement and this engine does
not make it.

## 5. What this does NOT settle

- **How the base moment SPLITS between the buried shaft and the pad.** These are alternative
  load paths for one moment and not additive ones: a shaft that turns in soil sheds its
  moment into lateral bearing, and a pad that resists by bearing does so because the shaft
  above it does not. Adding them counts the same moment twice. The split is a soil-structure
  stiffness problem and nothing here computes it.
- **That the pad is not the mechanism is itself worth stating**, and the record states it.
  Taken as a rigid spread base with no help from the shaft, `PT-BW-RE`'s resultant sits
  **1.65'** off centre on a 1.50' least plan dimension — past the kern (0.25') and past the
  half-width (0.75'), so the pad alone would have **no contact at all**. That is not a
  failure; it is the arithmetic showing which mechanism is carrying the moment.
- **Rotational stiffness.** This grades whether the base can turn the shear around, not how
  far it rotates first. `deck_post`'s sway magnifier assumes a base that does not rotate,
  and a real one does.
- **Group effect** with the pier line beside it, **passive resistance on the pad's own
  faces** (neglected, the conservative direction), and the **long-term modulus** the
  magnifier implicitly assumes.
- **Seismic.** `notes/balcony_moment_columns.md` §9 names the site-specific hazard lookup as
  an external deliverable and that is unchanged.

## 6. What closes it, worked

**Nothing here is decided.** Three closures were named on 2026-09-18 and all three have now
been worked rather than listed, because two of them do not do what the list implied. The
choice is still the owner's and the engineer of record's; what follows is the arithmetic
they need to take it.

### 6a. Deepen the two canopy shafts — works, and undermines two footings

`PT-BW-RE` needs 8.08' against 6.12', `PT-BW-RNE` 8.08' against 3.50'.

**The required depth does not chase the embedment.** `h` is measured from grade to the
point of application, and the base moment's arm is measured from the base; deepening moves
both by the same Δ, so `h` stays 7.79' and `d = 8.08'` is a fixed target rather than an
iteration. That part is clean.

What it costs is not concrete — 0.057 and 0.133 cy — it is what the shafts end up beside:

* `PD-BW-RE`'s pad top goes to **-10'-11"** and its bottom to -11'-11", which is **2.13'
  below `FT-B-N1..N4`**, sitting 1 1/16" away in plan on the -9'-9 7/16" plane. That is
  undermining a strip footing, and **no check in this repo sees it**:
  `structural.concrete_interference` grades shared VOLUME, and these two solids share none.
* `PD-BW-RNE` is worse: 4.58' deeper, and 4.9' below the garage strip footing it declares
  `cast_with`. §6 of `north_entry_piers.md` explains that the garage-side line bottoms at
  -7'-0" precisely because that is the garage footing's own underside.
* **`PD-BW-RE` goes from 0.94 to 0.984 on bearing.** 1.96' more of 12" shaft is 231 lb;
  (5,156 + 231 + 563 - 413) / 3.75 = 1,477 psf against 1,500. It is already the tightest pad
  in the house and `houses/catlin/CLAUDE.md` says so — closing this properly means widening
  all three house-side pads together, which is the S-100 FOUNDATION SCHEDULE constraint.
* It **adds a row to S-100**: `emit/draw/foundation_schedule._pad_key` carries the bearing
  elevation, so `PD-BW-E` and `PD-BW-RE` stop sharing a mark. That sheet is 0.18" from its
  own schedule governing its height.

### 6b. Constrain the base at grade — closes ONE of the two, and not the one that needs it

IBC 2018 §1807.3.2.2 applies "where lateral constraint is provided at the ground surface,
such as by a rigid floor or pavement", and reads

```
d = sqrt( 4.25 Mg / (S3 b) )              (Eq. 18-3)
```

**`S3` is the allowable lateral bearing at the FULL depth `d`**, not at `d/3` — a difference
that halves the answer, and the easiest error to make here. At `Mg = 680 x 7.79 = 5,297
lb-ft`, `b = 1.00'`, `S3 = 150 d`:

```
d^2 = 4.25 (5,297) / (150 d)  ->  d^3 = 150.09  ->  d = 5.31'
  check: S3 = 150(5.314) = 797 psf; 4.25(5,297)/797 = 28.24; sqrt = 5.314  ok
at 2 S3 (§1806.3.4):            d^3 =  75.04  ->  d = 4.22'
```

| column | have | needs (S3) | needs (2 S3) | verdict, constrained |
|---|---:|---:|---:|---|
| `PT-BW-RE` | 6.12' | 5.31' | 4.22' | **passes**, 0.87, both ends agree |
| `PT-BW-RNE` | 3.50' | 5.31' | 4.22' | **still OVER**, 1.52, both ends agree |

So this closes `PT-BW-RE` and leaves `PT-BW-RNE` 1'-10" short — it would want its pad top at
-8'-2", which is the same abandonment of the -7'-0" garage plane that 6a runs into.

**And the restraining element has to exist and has to be in the right direction.** A grade
beam *between* the two columns restrains nothing that matters: N-S governs (1,360 lb against
992), the two columns stand on a N-S line, and a beam joining them lies in the frame's own
plane — both columns simply lean together. To be constrained the strut has to reach a mass:
`PT-BW-RE` south to `W-B-N2/N3` (10 3/4" away) or `PT-BW-RNE` north into the garage stem.
Both reverse the two premises this design is built on — the canopy is freestanding, and the
landing touches nothing on the house — and put a rigid prop across the only movement joint.
A slab apron is not on offer either: these columns stand in open ground with a gravel apron.

### 6c. Brace the frame — closes both, and moves no geometry

A knee-braced portal with pinned bases develops **no base moment at all**; the columns
revert to leaning columns and `deck_post` grades them axially. Nothing is undermined, no pad
changes size or elevation, no row is added to S-100, and the owner has already accepted knee
braces here as a fallback.

**What it still owes, and this note says it rather than letting the item's disappearance
read as a pass:** a pinned base still delivers 680 lb horizontally at grade. Nothing in this
engine grades that path. The real resistance is pad friction plus passive on the pad faces —
IBC Table 1806.2 friction on 3.75-4.00 ft² at roughly 5,000 lb service is on the order of
1,750 lb, comfortably enough — but "on the order of" is not a calculation, and it should be
carried as a named deferral rather than as silence.

**The connector is not solved.** `KBS1Z` is wood-to-wood and `APVKB45-6` is unrated in
ER-102 and ER-280. A knee brace landing on a 12" cast round needs a real part — a
through-bolted plate or a concrete-screw bracket at >= 3" edge distance, the family the
`HGAM10` head already uses.

### 6d. A fourth route, and it may cost nothing at all

§1807.3.2.1 is **doubly** conditioned: it governs where there is no constraint at grade
**and none above grade "such as by a structural diaphragm."** This house already models
exactly that — seven `LSTA24` straps at 4'-0" o.c. (`CN-BW-JOINT-1..7`) tying the canopy and
garage sheathing into one plane, and the record for that strap line says it "carries in-plane
shear and tension." If the garage's shear walls take the canopy shear, then neither pole
formula applies, both columns are leaning columns, and no element moves.

That is a **relative-rigidity judgement**, which is why this engine refuses to make it — the
same refusal §2 states when it takes the whole 1,360 lb on the two cast columns rather than
sharing it with `W-BW-SCREEN`. It is the engineer of record's to make, and it is the first
question to put to them, because it is the only closure with no construction cost.

### 6e. What would make a closure dishonest

* **Claiming "constrained" without modelling the restraint.** There is no constrained branch
  in `column_base.py` and no field naming a restraining element. Hand-swapping the formula
  halves a required depth on the strength of prose.
* **Authoring a `KneeBrace` to silence the check.** `pier_basis.knee_braced()` short-circuits
  `roof_base_moments` wholesale, so one element deletes every `column_base`, `base_rotation`
  and `column_head_joint` item and `deck_post`'s moment records in a single edit, at 0 FAIL —
  and a brace with an empty `connects` matches by plan centre, so a sloppy one can silence a
  column it was never attached to. Author `connects`, and assert the surviving item set.
* **Letting the item's disappearance read as a pass.** After 6c or 6d there is no fixed base
  to grade, and the gate opens because the question left rather than because it was answered.
* **`h` is measured from the single global `Site.grade`.** A local apron or regrade at the
  canopy is invisible to the model and would change `h`, and so `d`, with no finding.

## Sources

- IBC 2018 §1807.3.2.1, §1807.3.2.2 (Eq. 18-3, S3 at the FULL depth), §1806.2 Table,
  §1806.3.4. Text confirmed 2026-09-18 against ICC Digital Codes, UpCodes and the 2015
  Seattle Building Code's verbatim reproduction of Chapter 18.
- `notes/north_entry_piers.md` §8b (the frame shear and the base moments), §6 (why the two
  pier lines bottom at different elevations), §8d (the prose this note replaces).
- `notes/balcony_moment_columns.md` §2c (the guard load taken wholly on one column).
