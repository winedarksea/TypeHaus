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

## 6. What closes it

Three fixes, and the choice is the owner's — none is this note's to take:

1. **Deepen the two canopy shafts.** `PT-BW-RE` needs 8.08' against 6.12', `PT-BW-RNE` 8.08'
   against 3.50'. On the house side that is 2' more of an augered shaft in an excavation
   that is already open. On the garage side it means the pier line stops being level with
   the garage strip footing, which `notes/north_entry_piers.md` §6 explains was the whole
   reason it is at -7'-0".
2. **Constrain the base at grade** — a grade beam between the two, or the slab apron carried
   to the columns — which moves the design onto §1807.3.2.2's constrained formula and
   roughly halves the required depth.
3. **Brace the frame instead.** The owner has already accepted knee braces as a fallback at
   the canopy (`plans/`), and a braced frame has no base moment to develop at all; the
   columns revert to leaning columns and `deck_post` grades them axially.

## Sources

- IBC 2018 §1807.3.2.1, §1807.3.2.2, §1806.2 Table, §1806.3.4.
- `notes/north_entry_piers.md` §8b (the frame shear and the base moments), §6 (why the two
  pier lines bottom at different elevations), §8d (the prose this note replaces).
- `notes/balcony_moment_columns.md` §2c (the guard load taken wholly on one column).
