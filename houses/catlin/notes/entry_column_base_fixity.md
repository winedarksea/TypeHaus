# Base fixity of the cast columns — IBC 1807.3.2.1, hand-worked

**Oracle for** `engineering/column_base.py` and `engineering/spread_base.py` (§§1-6, §8),
`engineering/pole_embedment.py` (§9), and for `engineering/diaphragm_basis.py`,
`engineering/lateral_lines.py` and `engineering/lateral_system.py` (§7). Reproduced by
`tests/test_column_base_calcs.py` and `tests/test_lateral_system_calcs.py`. Worked
2026-09-18 and revised 2026-09-19 and 2026-09-20, each time in a separate pass from the code.

**2026-09-20 (basis 4), in one paragraph.** The pad is now part of the pole. Every column
here stands on a 12" pad cast in one placement with its shaft, the shaft's hooked dowels
developed into it; the two turn as one rigid body, so embedment is measured to the pad
**bottom** rather than its top, and the pad's extra width enters §1807.3.2.1 through an
effective width (§9). Every verdict improves — canopy 0.96 → **0.85**, landing W/E 0.73 →
**0.62** — and `PT-BW-GW`/`-GE` stop straddling §1806.3.4: they pass on Table 1806.2's own S1
at **0.96 / 0.98**, so the owner's isolated-pole claim buys nothing and is **withdrawn**
(§6e). Almost none of the gain is the pad's width: `b_eff` is 1.006–1.070. It is the datum.

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
the module makes no such judgement of its own: where they straddle, the record reports
INCOMPLETE naming it. That is the same convention `retaining_wall` applies to the soil unit
weight band, for the same reason.

**A HOUSE may make that judgement, and then it is a graded claim — §6e, 2026-09-20.**
`Post.isolated_pole_basis` states in prose what tolerates the half inch and on whose word,
and `column_base.py` grades the doubled formula and says so in the citation, quoting the
basis. A reader may never see a passing embedment here without learning §1806.3.4 was
invoked. Two ways the claim is refused, both INCOMPLETE naming why: an empty basis (§6g's
stale-declaration bullet, made checkable), and a governing lateral case §1806.3.4's own words
do not reach — the section permits the doubling for motion "due to **short-term** lateral
loads", and wind and an R301.5 guard push qualify where a sustained case does not. The
landing pair claimed it from 2026-09-20 until basis 4 made it unnecessary the same day;
**nothing in this house claims it now** (§6e). The mechanism stays, and its two refusals are
still tested.

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
   head the shaft is a PROPPED cantilever, and 182 lb applied at 11.17' on a 16.56' shaft
   makes 553 lb-ft at the base instead of 2,027. The balance goes UP into the deck, where it
   is distributed with everything else. That is not a discount applied to the old free body;
   it is the free body the declaration creates.

`Site.grade` is **-2'-10"**, and since 2026-09-20 **both** roof columns bear on one common
plane at **-10'-2"** (`north_entry_frame.ROOF_COLUMN_BASE_FT`), so each shaft is buried
**7.33'** and, with its 1'-0" pad, the pole is **8.33'** (§9). They were at -8'-11 7/16" and
-6'-4" — 6.12' and 3.50' of shaft — and §6a is where that moved and why it had to move for
both at once. **`h` below is measured from grade and does not move with §9**: the arm runs
from the pad TOP, so the shaft's 7.33' comes off it, never the pole's 8.33'.

The four landing columns (`PT-BW-W`/`-E`/`-GW`/`-GE`) are a different structure —
`FS-BW-FLOOR`, whose governing lateral case is not wind but the **IRC R301.5 guard load**,
200 lb at the top of the rail, taken wholly on one column. Its arm above grade is 4.54', and
nothing in this revision touches it: a guard load is delivered at a rail, not at a diaphragm.

## 3. The arithmetic, iterated

`S1 = 150 d / 3 = 50 d`, so `A = 2.34 P / (50 d)`. Starting at `d = 1'` and iterating to
four figures:

```
both roof columns   P = 496.1 lb,  h = 7.489',  b = 1.00'
  A = 23.218 / d                  4.36 h = 32.651
  d = 0.5 A [1 + sqrt(1 + 32.651/A)]
       d = 7.000 -> A = 3.3168 -> d = 7.095
       d = 7.095 -> A = 3.2724 -> d = 7.057
       d = 7.057 -> A = 3.2900 -> d = 7.072
       ...converges                d = 7.07'
  at 2 S1 (§1806.3.4):  A = 11.609 / d      converges   d = 5.40'   -- NOT claimed

  The two are ONE line of arithmetic now because the two columns are one column: equal
  shaft, equal stiffness, equal share. Before 2026-09-20 they read
  PT-BW-RE  P = 379.4 lb, h = 6.898' -> d = 6.25' against 6.12' (1.02, INCOMPLETE) and
  PT-BW-RNE P = 612.9 lb, h = 7.702' -> d = 7.73' against 3.50' (2.21, OVER).

the four landing columns  P = 200 lb,  h = 4.54',  b = 1.00'
  A = 9.36 / d
  d = 0.5 A [1 + sqrt(1 + 19.79/A)]          converges  d = 4.45'
  at 2 S1                                               d = 3.39'
```

These are the **constant-width** numbers, `b = 1.00'` — a bare shaft. They are still exact for
one: §9 shows a stepped pole of one width IS the code formula. §9 adds the pad.

> ⚠ **WITHDRAWN 2026-09-21 for the four LANDING columns** (`PT-BW-W`/`-E`/`-GW`/`-GE`): the landing
> is tied to the garage stem (`north_entry_piers.md` §10), so they lean and are no longer
> lateral columns; `column_base` stops enumerating them. Their rows below are history. `PT-BW-RE`/`-RNE`
> are untouched — the tie does not reach them (they stand 20' east, on the canopy's own line).

## 4. The verdicts

Since 2026-09-20 (basis 4) the capacity is the POLE — shaft plus pad, grade to pad bottom —
and the demand is §9's stepped solve at the worse end of the pivot band. The shaft-only
columns are kept beside them so the reader can see what the datum did.

| column | carries | shaft | pole | `B` | needs (S1) | needs (2 S1) | verdict | shaft-only, before |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `PT-BW-RE` | canopy, east | 7.33' | 8.33' | 1.5' | 7.06' | 5.36' | **ok, 0.85** | 7.07' / 0.96 |
| `PT-BW-RNE` | canopy, east | 7.33' | 8.33' | 2.0' | 7.04' | 5.33' | **ok, 0.85** | 7.07' / 0.96 |
| `PT-BW-W` | landing, guard | 6.12' | 7.12' | 1.5' | 4.39' | 3.30' | ok, 0.62 | 4.45' / 0.73 |
| `PT-BW-E` | landing, guard | 6.12' | 7.12' | 1.5' | 4.39' | 3.30' | ok, 0.62 | 4.45' / 0.73 |
| `PT-BW-GW` | landing, guard | 3.50' | 4.50' | 2.0' | 4.33' | 3.21' | **ok, 0.96** | 4.45' / straddle |
| `PT-BW-GE` | landing, guard | 3.50' | 4.50' | 1.5' | 4.39' | 3.30' | **ok, 0.98** | 4.45' / straddle |

**No column claims §1806.3.4 any more.** All six publish on Table 1806.2's own S1 with both
ends of §1806.3.4 and both ends of the pivot band agreeing — four agreements per record.

*The paragraphs below were written against the shaft-only column and are kept as the record
of how the design got here; the verdict column above supersedes their numbers.*

**Both canopy columns publish a graded verdict at the table's own lateral bearing**, and
§1806.3.4's isolated-pole doubling is not claimed for either — which is the part worth more
than the margin. A record that needs the doubling straddles the band and publishes nothing;
these two are decided on the S1 the table gives, so there is no judgement deferred to a
reader about half an inch of motion at grade.

**They are equal because they were MADE equal**, and that is §6a. `PT-BW-RE` was 1 1/2"
short at 6.12' against 6.25' and `PT-BW-RNE` was 2.2 times over at 3.50' against 7.73'; both
now stand 16'-6 3/4" from a common bearing plane at -10'-2" to the header soffit, so they
have the same stiffness, take 50% each of the governing E-W case, and need the same 7.07'.

**The two landing columns on the garage side still STRADDLE, and publish anyway since
2026-09-20 — on a claim, not on concrete.** `PT-BW-GW` and `-GE` need 4.45' at the table and
3.39' doubled against the 3.50' they have, exactly as `PT-BW-RE` used to; **the required
depths did not move and that is the point**. What moved is that the judgement the straddle
turns on has been made, authored and graded: §6e. Their case is the R301.5 guard load, not
the canopy's wind, and they carry no roof, which is why nothing in §6a or §7 ever reached
them. d/c **0.97** — a real pass, but thin, and worth revisiting on depth separately now that
the gate is open (a 4" drop gives 0.885 and still clears the hydrant cone).

**Read the two halves of this table together and the shape of the house is in it.** The four
columns decided on Table 1806.2's own S1 are decided by CONCRETE — `PT-BW-W`/`-E` were always
deep enough because the basement excavation was open to them, and the canopy pair was made
deep enough in §6a. The two decided on §1806.3.4 are decided by a JUDGEMENT, because the
concrete route is closed to them: §6e works why.

## 5. What this does NOT settle

- **How the base moment SPLITS between the buried shaft and the pad.** These are alternative
  load paths for one moment and not additive ones: a shaft that turns in soil sheds its
  moment into lateral bearing, and a pad that resists by bearing does so because the shaft
  above it does not. Adding them counts the same moment twice. The split is a soil-structure
  stiffness problem and nothing here computes it. **§9 does not answer it and must not be
  read as answering it**: §9 makes the pad part of the POLE — one rigid body turning in soil
  under the pole mechanism — and does not divide the moment between that and the pad's
  bearing mechanism. `base_rotation`'s deferral, "how the moment splits between the buried
  shaft and the pad", is as open as it was.
- **That the pad is not the mechanism is itself worth stating**, and since 2026-09-19 the
  record states it in graded arithmetic rather than prose — see §8. `PT-BW-RE`'s resultant
  sits **1.25'** off the footprint centroid against a kern of **0.42'**, so the base would
  lift at one edge before it did anything about the moment. **The deepening made that worse,
  not better** — the base moment rose from 4,940 to 7,354 lb-ft while the axial barely moved
  — and it is the clearest possible statement that the pad is not the mechanism: the thing
  that closed these columns was the shaft in the soil, and the pad's own arithmetic ran the
  other way while it happened.
- **Rotational stiffness.** This grades whether the base can turn the shear around, not how
  far it rotates first. `deck_post`'s sway magnifier assumes a base that does not rotate,
  and a real one does.
- **Group effect** with the pier line beside it, and the **long-term modulus** the magnifier
  implicitly assumes.
- **Passive on the pad's faces is no longer neglected — it is counted, once, as part of the
  pole** (§9): the pad's depth is embedment and its width beyond the shaft is `b_eff`, both in
  §1807.3.2.1's own pressure field. It is NOT a second resisting term added to the answer, and
  that is the whole design of §9. It is also worth very little: `b_eff` is 1.006–1.070.
  **Passive is NOT restored anywhere else.** `spread_base.py` stays passive-free — it is the
  ALTERNATIVE mechanism, and crediting passive there too resurrects the double count it exists
  to prevent. `retaining_basis.py`'s L23-30 convention (passive on the toe neglected) stands,
  and on the court walls it is not even a conservatism: the toe is buried 0" — the footing top
  IS the court floor and an `FO-SG-TOE-*` void clears the rim slab over each strip — so there
  is no soil to push against. The pier pads earn their credit by standing in the ground as
  part of a doweled rigid body; the court toes have no ground in front of them. A reader who
  sees the pier pads credited should not reach for the walls next.
- **Seismic.** `notes/balcony_moment_columns.md` §9 names the site-specific hazard lookup as
  an external deliverable and that is unchanged.

## 6. What closes it, worked

**Nothing here is decided.** Five closures have now been worked rather than listed, and the
scoreboard has changed twice: 6d was written off on 2026-09-18 as "a relative-rigidity
judgement this engine refuses to make" and is now §7, implemented; and 6f, the one the
2026-09-19 plan expected to carry `PT-BW-RNE`, turns out not to exist at all.

### 6a. Deepen both canopy shafts to ONE plane — **DONE 2026-09-20, and §6a was wrong**

**The 2026-09-19 version of this section is the thing §6g warns about**, so it is corrected
here rather than edited away. It said:

> **The required depth does not chase the embedment.** `h` is measured from grade to the
> point of application, and both the header and the drag resultant stand at fixed
> elevations, so `h` is invariant under deepening and `d` is a fixed target rather than an
> iteration.

— and on that basis it proposed `PD-BW-RE` down 1 1/2" to -9'-1" and `PD-BW-RNE` down 4'-3"
to -10'-7", the two taken as independent one-line fixes.

**The half about `h` is true. The half about `d` is false, and the reason is §7's own
distribution.** IBC §1604.4 shares the wind by relative rigidity, a cantilever's stiffness
is `3EI/h³`, and that `h` is the FULL shaft — base to header soffit, buried length included.
Deepening a column makes it SOFTER and sheds its share onto the other one. The two columns
are not two problems; they are one problem with two knobs, and turning either moves both.

Worked at the §6a elevations, the proposal makes `PT-BW-RE` worse than leaving it alone:

| | `PD-BW-RE` top | `PD-BW-RNE` top | `PT-BW-RE` d/c | `PT-BW-RNE` d/c |
|---|---|---|---:|---:|
| as built, 2026-09-19 | -8'-11 7/16" | -6'-4" | 1.02 INCOMPLETE | 2.21 OVER |
| §6a as written | -9'-1" | -10'-7" | **1.19 OVER** | 0.86 |
| §6a, both deeper | -9'-2" | -10'-8" | **1.17 OVER** | 0.85 |

`PT-BW-RNE` deepens by 4'-3", its stiffness falls by a factor of 2.2, and the E-W share it
sheds lands on `PT-BW-RE` — which gains an inch and a half of embedment against a demand
that rose by a third. There is no pair of elevations that closes `PT-BW-RNE` by deepening it
and leaves `PT-BW-RE` near -9'. Solved as the simultaneous fixed point it actually is, the
shallowest closure is `PD-BW-RE` at **-10'-3 1/8"** and `PD-BW-RNE` at **-10'-6 13/16"**.

**Which is the answer telling you to make them equal.** Put both on ONE plane and the two
columns become the same column — equal `h`, equal `3EI/h³`, 50% each — and the arithmetic
collapses to the single line in §3. What that buys, in the order it is worth having:

* **Both records publish.** 7.07' needed against 7.33' at the table's own S1, d/c 0.96, and
  §1806.3.4's doubling is not claimed for either. No straddle, no INCOMPLETE, no judgement
  handed to a reader.
* **The governing case stops depending on §7d.** With equal stiffnesses the E-W split is
  50/50 under a RIGID diaphragm and 50/50 under a tributary one. §7d's N-S ratio was 0.99x —
  "a factor of two from flipping", and flipping used to put `PT-BW-RE` back over. It cannot
  any more: the case that governs is indifferent to the answer. (For the record the ratio
  also *improved*, to 0.68x, because softer columns drift more — see §7d.)
* **ONE new bearing elevation, so one new S-100 row, not two.** `_pad_key` keys on `z0_m`
  and that sheet is 0.18" from its own schedule governing its height.
* **One dimension on the drawings instead of two, and two identical piers.**

**-10'-2" is the shallowest clean elevation clearing 0.96**, and shallowest is the one to
want: 4'-3" of extra 12" round is about 0.10 cy of concrete and costs nothing, while the
excavation it stands in costs a great deal. Both pads bottom at **-11'-2"**.

**What it owes, and neither is a modelling gap.** Both are sequencing notes for the
drawings, of exactly the class `PIER_BOTTOM_FT` already carries:

* **House side.** `FT-B-N1`..`-N4` bottom at -9'-9 7/16" and reach to within 7/8" of
  `PD-BW-RE` in plan, so the pad now bears 1'-4 9/16" below a footing an inch away. In the
  open basement excavation — the owner's premise, and why this depth is cheap — the pocket
  is dug and the pad cast BEFORE the strip bears beside it. Cast after, it is undermining,
  and the answer becomes benching or a local step in the strip.
* **Garage side.** `PD-BW-RNE` laps about 7 1/2" UNDER `FT-GF-S1`/`-S3` in plan and now sits
  3'-2" below them. Those are consolidated crushed stone under R403.5 (§6f), so there is no
  pour to undermine and no cold joint to key — but a stone strip placed over a backfilled
  pocket is a settlement question and not a non-issue. The pad goes in first and the stone is
  compacted around and over it in the 8" lifts R403.4.1 already requires.

**`PD-BW-RE` on bearing.** The 2026-09-19 note expected 0.94 -> about 0.95. The deeper shaft
adds 143 lb of axial, but the base moment rose to 7,354 lb-ft and the eccentricity with it,
to 1.25' against a 0.42' kern — see §5 and §8. That arithmetic is REPORTED and not graded,
for the reason §5 gives, and it moved the wrong way while the graded mechanism closed.

### 6b. Constrain the base at grade — still not available

Unchanged from 2026-09-18 and still the closure that would be dishonest. IBC 2018 §1807.3.2.2
applies "where lateral constraint is provided at the ground surface, such as by a rigid floor
or pavement", and these columns stand in open ground with a gravel apron. A strut between the
two columns restrains nothing: they stand on one N-S line and would lean together. To be
constrained the strut has to reach a mass — `PT-BW-RE` south to `W-B-N2/N3`, 10 3/4" away, or
`PT-BW-RNE` north into the garage stem — and both reverse the premises this design is built
on and put a rigid prop across the only movement joint. §6g's first bullet is about this.

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
demonstrably has one, which is §6g's third bullet exactly.

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

### 6e. Claim §1806.3.4's isolated-pole doubling for the landing pair — **WITHDRAWN 2026-09-20**

**Withdrawn the same day it was made, and the withdrawal is the closure.** Measured to the pad
BOTTOM (§9), `PT-BW-GW` and `-GE` have 4.50' against 4.33' and 4.39' needed on Table 1806.2's
own S1 — at both ends of the pivot band, and at 0.85 and 1.00 either side of it. The two ends
of §1806.3.4 now agree, so the verdict no longer turns on a judgement about the structure and
the claim buys nothing. `_ISOLATED_POLE_BASIS` was deleted from `params/north_entry_frame.py`
**in the same commit** as the code that made it unnecessary: a claim left standing where it
does no work is exactly §6g's stale declaration, and one the engine would have gone on
printing into a citation.

**Why dropping a claim counts as closing it.** A claim is a statement a reviewer has to
evaluate and a future reader has to keep true: §6g's last bullet names what could make this
one false (glaze the landing, clad it, hang a door off it) and admits the engine cannot catch
it. Withdrawn, none of that is owed. The verdict rests on the table's number and on concrete,
which is what §6a bought for the canopy, and nothing about what stands on the landing can
quietly make it untrue. What remains of the argument below is the record of why it was
reasonable at the time; `column_base.py` still grades the claim mechanism (`_pole_claim`, both
refusals tested) for the next house that needs it.

**And be honest about where the margin came from.** Not from the pad's width — `b_eff` is
1.070 on `PT-BW-GW`'s 24" pad and 1.034 on `-GE`'s 18", worth 0.12' and 0.06' of required
depth. It came from the datum: a foot of pad that was always there and was not being counted.
Without any width credit at all (b = 1.00) they need 4.45' against 4.50' and still pass.

*The 2026-09-20 claim, as it was made:*

`PT-BW-GW` and `-GE` straddle: 4.45' needed at Table 1806.2's own `S1`, 3.39' at the
isolated-pole double, **3.50'** in the ground. §1 says the module refuses to pick a side. The
owner has picked one.

**The lever the other closures used is not available here, and that is worked rather than
asserted.** Deepening to 4.45' puts `PD-BW-GE`'s bottom at **-8'-4"**, which drags
`PR-G-HYDRANT-CW` — invert **-8'-10"**, about **8"** away in plan — inside the pad's 45°
influence cone. `plan/mep_supply.py` states the constraint in its own words: *"all five
north-entry footings now bear BELOW this invert … Keep it that way if a pier ever moves."*
Clearing it properly means dropping roughly **2'** to bear below the invert — off the garage
strip footing plane these two are deliberately held near (`GARAGE_FOOTING_TOP_FT`), and into
the excavation-sequencing argument §6a's note carries for the canopy. Pouring 2' of concrete
to dodge a question the owner has already answered is the wrong lever. §6b (constrain at
grade) is not available for the reason it is not available anywhere here; §6c and §6d are
about a canopy FRAME and there is no frame under a landing guard.

**What tolerates the half inch.** The governing lateral case on these two is not wind at all:
it is IRC Table R301.5's **200 lb** guard push at the top of `RL-BW-ENTRY`, taken **wholly on
one column** (`pier_basis._base_moments`, the conservative bound) over a **4.54'** arm above
grade. What stands on them is a 4'-11 3/4" square open landing and its guard — no glazing, no
cladding, no finish plane, nothing bearing on the house or the garage. Half an inch of sway at
grade under a person leaning on a rail moves a free-standing landing half an inch and it comes
back. There is nothing there to crack, bind or rack out of plumb. Contrast the canopy pair,
whose heads carry an `HGAM10` gusset and a stainless standoff shim pack under a 24' header —
which is exactly the structure §1 was written cautious about, and exactly why §6a bought its
depth rather than claiming this.

**It is a CLAIM, so it is graded.** `Post.isolated_pole_basis` carries the statement in prose
— never a bare bool, because the failure mode of a flag is §6g's fifth bullet and a flag
carries nothing a reader could use to notice it went stale. `column_base.py` refuses it two
ways, each INCOMPLETE naming the reason: an empty basis, and a governing case §1806.3.4's own
words do not reach ("due to **short-term** lateral loads"). Wind and the R301.5 push are both
short-term; `_sustained_lateral_cases` scans the pier's base-moment terms and refuses anything
not deliberately listed as such, so the day a sustained lateral case appears on one of these
the claim stops being honoured rather than quietly surviving.

**What it costs and what it buys.** Cost: nothing built, and a judgement a reviewer must now
evaluate — which is the honest price and is why the citation quotes the basis rather than
merely citing the section. Buys: d/c **3.393 / 3.500 = 0.97**, a graded verdict where there
was an INCOMPLETE, and the last blocking checklist line on `haus print houses/catlin`.

**Not claimed on `PT-BW-RE`/`-RNE`, deliberately.** §6a chose -10'-2" partly *so that* the
canopy would be decided on the table's own number; claiming the doubling there would spend a
judgement on a question already closed and move the canopy's verdict from Table 1806.2 onto an
owner's statement. `tests/test_column_base_calcs.py` asserts the canopy pair does not claim it.

### 6f. Credit the pour that is already one — **NOT AVAILABLE, and this is a correction**

The 2026-09-19 plan proposed crediting `PD-BW-RNE`'s declared `cast_with` as a combined
footing: it is cast monolithic with `FT-GF-S3` + `FT-GF-E` at the corner where the garage's
E-W south run meets its N-S east return, so the union has the lever arm the overturning
wants. The mechanism is real and it is implemented (`engineering/spread_base.py`, §8).

**The premise is false, and it has been false since 2026-09-15.** (Past tense throughout
below: the `cast_with` declaration itself was DELETED from all three garage-side pads on
2026-09-20. What survives is the correction, which is why this section does.) `FT-GF-S1` … `FT-GF-W` are
**crushed-stone footings** under IRC R403.5 — `params/foundations.py` retyped all nine on
2026-09-15, five days after `PD-BW-RNE` declared it was cast with two of them. Nothing is
cast monolithically with consolidated stone. The `cast_with` declaration on the three
garage-side pads survived that retype for five days, saying something untrue about how the
concrete is placed, and was removed on 2026-09-20. `engineering/spread_base.pours_for`
refuses any named pour whose `Footing.material` is not concrete, by name, rather than quietly
crediting a smaller footprint, so the credit was never actually taken — what the stale
declaration cost was a reader's time, which is exactly §6g's fifth bullet.

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
* **Leaving a stale declaration in place.** 6f was the live example and is now the worked
  one: `cast_with` was true when written, false from 2026-09-15, and deleted 2026-09-20. A
  declaration that was true when it was written and is not true now reads exactly like one
  that is. **§6a is the second example and a worse one**, because it was prose about a
  calculation rather than about a pour: "`d` is a fixed target rather than an iteration" was
  half right, nobody re-derived it, and acting on it would have pushed `PT-BW-RE` from
  INCOMPLETE to OVER while appearing to fix it.
* **`h` is measured from the single global `Site.grade`.** A local apron or regrade at the
  canopy is invisible to the model and would change `h`, and so `d`, with no finding.
* **Letting §6e's claim outlive the structure it was written about.** This is the fifth
  bullet again, aimed at the closure that is most exposed to it — the whole of `PT-BW-GW`'s
  and `-GE`'s verdict rests on a sentence about what stands on them. The basis names an OPEN
  landing with no finish plane and a short-term guard push. Glaze that landing, wrap it,
  hang a door off it, put anything on it that half an inch of grade movement would rack or
  crack, or give either column a lateral case that does not go away — and the claim is false
  while the record still reads 0.97. **What the engine can catch:** an empty basis, and a
  base-moment term that is not one of the short-term cases. **What it cannot:** whether the
  prose is still true of the building. That one is a reader's, and it is why the basis is
  prose, dated and attributed, and printed into the citation on the calc sheet rather than
  hidden in a field. Re-read it whenever anything lands on that landing. **Retired with the
  claim (§6e, WITHDRAWN):** nothing on that landing now depends on the half inch. The bullet
  is kept because it is the reason a withdrawn claim beats a harmless one.
* **Crediting the pad without the joint that makes it part of the pole.** §9 rests on the
  pad and shaft being one body — one placement, the dowels developed into the pad
  (`deck_post`'s dowel anchorage, d/c 0.76). `column_base.py` refuses the pad credit where
  that state is over or ungraded and grades the shaft alone; a cold joint with no dowels is a
  post standing on a footing, and a footing resists by the OTHER mechanism.

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

`a = H - 10.785/2 = H - 5.392`. Both columns now stand on one plane, so there is one line:

```
both        H = 16.563', a = 11.170'  ->  M_base = 552.6 lb-ft   R_head =  96.0 lb
```

Those two head reactions join the deck, so the shear the diaphragm distributes is

```
E-W   629.3 + 192.0 =   821.3 lb           N-S   997.4 + 192.0 = 1,189.4 lb
```

### 7c. The stiffnesses

Cantilever `3EI/h³`. `PIER_CONCRETE_12` specifies f'c 5,000 psi, so `E = 57,000 sqrt(5000) =
4.031e6 psi`; a 12" round has `I = pi d^4 / 64 = 1,017.9 in^4` (gross — ACI 318-19 §6.6.3.1.1
permits 0.70 I_g, and taking the gross section makes the column stiffer and so hands it MORE
shear, which is the end that does not flatter the member being graded).

```
both        h = 198.75"   k = 3(4.031e6)(1017.9) / 198.75^3 = 1,568 lb/in
```

**Equal, and that is the design rather than a coincidence** — §6a put both bases on one
plane precisely so this line would have one entry. Before 2026-09-20 they read 1,970 and
3,453 lb/in on 184.19" and 152.75" shafts, and the 2.2x spread between them is what made the
short column govern its own worst case.

`W-BW-SCREEN` by SDPWS 4.3.2, `delta = 8vh³/(EAb) + vh/(1000 G_a) + h d_a / b`, on
6.573' x 4.083' with `G_a = 11 kips/in`, chords 2-2x4 (`A = 10.5 in²`, `E = 1.4e6 psi`) and
`d_a = 1/16"`.

**The panel’s stiffness and its share are each other’s input**, because SDPWS states the anchorage
term as a displacement AT the design shear rather than as a rate: push the panel harder and
the fixed 1/16" of take-up is a smaller fraction of a larger deflection, so it reads
stiffer. The pair is iterated from an equal share until it stops moving — three passes here.
At the share it settles on, 76.1% of the N-S case (905 lb, `v = 137.7 plf`):

```
bending   8(137.7)(4.083^3) / (1.4e6 x 10.5 x 6.573)  = 0.0008"
shear     137.7 x 4.083 / (1000 x 11)                 = 0.0511"
rotation  4.083 x 0.0625 / 6.573                      = 0.0388"
                                               delta  = 0.0907"  ->  k = 9,977 lb/in
```

**The panel now carries three quarters of the N-S case rather than five eighths**, because
the columns it shares that case with got softer. That is the same mechanism §6a is about,
seen from the other end, and §7f is where the panel is graded for it.

**The panel is evaluated a second time, at a different share, and that is deliberate.** ACI
318-19 §6.6.3.1.1 permits 0.70 I_g for a column in a lateral analysis, and which end of that
band is conservative depends on which member is being graded: gross columns are stiff and
take more (the column's own worse end, used above), cracked columns are soft and shed onto
the panel (the PANEL's worse end). At 0.70 I_g the columns fall to 1,097 lb/in each,
the panel's share rises to **82.5%** — 981 lb, `v = 149.2 plf` — and §7f grades the panel
there.

### 7d. Rigid or flexible, and it is decided rather than assumed

ASCE 7-16 §26.2 calls a diaphragm flexible when its own midspan deflection exceeds **twice**
the average storey drift of the vertical elements. Both are evaluated at the TRIBUTARY
distribution — the idealization under test — so the answer does not depend on the assumption
being tested. SDPWS 4.2.2 for the deck, with a 2x4 chord (`A = 5.25 in²`) and 0.03" of splice
slip at the peak:

```
N-S   L = 24.0', W = 6.0', v = 0.5(1189.4)/6.0 = 99.1 plf
      bending  5(99.1)(24^3) / (8 x 1.4e6 x 5.25 x 6.0)  = 0.0194"
      shear    0.25(99.1)(24) / (1000 x 12)              = 0.0496"
      splice                                             = 0.0300"
                                          delta_diaphragm = 0.0990"
      average line drift (tributary)                      = 0.1456"
                                        ratio 0.68x  ->  RIGID

E-W   L = 4.979', W = 26.667'   delta_diaphragm = 0.0316"   drift = 0.2619"
                                        ratio 0.12x  ->  RIGID
```

Both cases are rigid, and **the N-S margin that used to be the thing to watch is no longer
one**. It read 0.99x before 2026-09-20 — a factor of two from flipping to tributary, which
would have taken the two columns from 14%/24% to 25% each and put `PT-BW-RE` back over. Two
things changed it. The ratio itself improved to 0.68x, because §6a's deeper bases made the
columns softer and a softer vertical element DRIFTS more, which is the denominator. And more
to the point, **the flip no longer matters to the governing case**: E-W governs both columns,
the two columns are now identical, and an even split is an even split whether it is derived
from equal rigidities or from equal tributary widths. Worked at the tributary idealization
the N-S case reads d/c 0.86 and E-W is unchanged at 0.96 — so both verdicts survive the
assumption being wrong, which is the only kind of margin worth quoting on this page.

### 7e. The shares, and what they leave at each base

```
N-S   sum k = 1,568 + 1,568 + 9,977 = 13,113
      PT-BW-RE  12.0%   PT-BW-RNE  12.0%   W-BW-SCREEN  76.1%
E-W   sum k = 1,568 + 1,568 =  3,135      (the panel runs N-S and resists nothing here)
      PT-BW-RE  50.0%   PT-BW-RNE  50.0%
```

E-W governs both columns, and with the two identical there is one base demand:

```
both        top 0.500 x 821.3 = 410.6 lb   M = 410.6(16.563) + 552.6 = 7,354 lb-ft
            base shear 410.6 + (181.5 - 96.0) = 496.1 lb      arm 14.82'
```

The N-S case, for completeness: top 142.2 lb, `M` = 2,908 lb-ft, base shear 227.7 lb at an
arm of 12.77' — 0.66 on the same embedment, and it does not govern on either column.

### 7f. What the deck and the panel owe for it

```
deck span-to-depth   24.0 / 6.0                              = 4.00  vs 4.00 blocked  (1.00)
deck unit shear      0.7607 x 1,189.4 / 6.0                  = 150.8 plf vs 190       (0.79)
deck chord force     1,189.4 x 24.0 / (8 x 6.0)              = 595 lb  -- NOT graded
panel unit shear     981 / 6.573                             = 149.2 plf vs 182.5     (0.82)
panel aspect ratio   4.083 / 6.573                           = 0.62  vs 3.5           (0.18)
panel hold-down      981 x 4.083 / 6.573                     = 609 lb vs 2,190 ABU66SS (0.28)
```

**§6a moved every row here except the first.** Softer columns shed onto the panel, so the
panel and the deck line that delivers to it both work harder: 0.64 -> 0.79 on the deck and
0.69 -> 0.82 on the panel. That is the price of closing the two columns and it is worth
naming as a price — it is paid in the panel's remaining margin, not in concrete.

The hold-down is the `ABU66SS` standoff base already under each 6x6 — 2,190 lb of published
uplift, Simpson letter L-F-SSNAILS23 against the ABU66 row of ESR-1622 — and **no dead load
is credited against the overturning couple**, which is a bound rather than an approximation
and clears by a factor of four anyway. What ESR-1622 §5.6 does not cover is the anchor bolt
and the concrete under it; that link is an ACI 318 Ch. 17 design and the record says so.

**The span-to-depth row is the one to read twice**, and it is the one row §6a could not
touch. 4.00 against a limit of 4.00 is a pass with no margin at all, on a deck whose depth is
fixed by the passage and whose span is fixed by the columns — geometry, which deepening a
base does not reach. Unblocked the limit is 3.0 and this is a FAIL. There is nothing to
trade, and it is now the governing row on the whole canopy at d/c 1.00.

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

## 9. The pad as part of the pole — hand-worked (2026-09-20, basis 4)

**Oracle for** `engineering/pole_embedment.py` and `column_base.py`'s basis 4. Worked with a
calculator, not the engine.

### 9a. Why the pad is part of the pole, and on what claim

Every pad here is 12" thick, cast in ONE placement with its shaft, and the shaft's four #5
dowels are hooked into it — `deck_post`'s "dowel anchorage into the base", d/c **0.76** on all
six. A pad that is monolithic with the shaft turns WITH it: it is the bottom foot of a rigid
pole, not a footing under a post. Measuring embedment to the pad TOP, as basis 3 did, threw
that foot away. **The claim is the anchorage**, and `column_base.py` refuses the credit where
that state is over or ungraded.

This is the POLE mechanism, extended one foot down. It is not the pad's own bearing
mechanism (§8), which stays reported and ungraded, and it does not add a second resisting
term to the first: see 9g.

### 9b. What Eq. 18-1 is, rearranged

`d = 0.5 A [1 + sqrt(1 + 4.36 h / A)]` squares to `(2d/A - 1)² = 1 + 4.36 h / A`, i.e.

```
d² - A d = 1.09 A h     ->     d² = A (d + 1.09 h)
A = 2.34 P / (S1 b),  S1 = s d / 3     ->     A = 7.02 P / (s d b)
                                            s b d³ = 7.02 P (d + 1.09 h)
                                                   = 7.02 P d + 7.6518 P h
```

A rigid pole pivoting at depth `γd`, soil pressure `s z b` per foot of depth, moments about
the pivot, the reaction below the pivot taken at the pivot (zero arm):

```
P (h + γd) = ∫₀^{γd} s z b (γd - z) dz = s b [γd z²/2 - z³/3]₀^{γd} = s b γ³d³ / 6
     ->   s b d³ = (6/γ³) P h + (6/γ²) P d
```

One γ cannot match both coefficients, and that is the code's own inconsistency:

```
match the d term:     6/γ² = 7.02            γ = sqrt(0.854701) = 0.92450   (the 2.34)
match the ratio:      γ = 1/1.09 = 4/4.36                      = 0.91743   (the 4.36)
  check the h term:   6/0.92450³ = 6/0.790171 = 7.593   6/0.91743³ = 6/0.772180 = 7.770
                      Eq. 18-1's own: 7.02 x 1.09 = 7.652 — between the two
```

Both are run; a verdict publishes only where they agree (the `retaining_wall` band
convention). γ enters ONLY through the pad's credit (9c), never the baseline.

### 9c. The effective width

With `b(z)` = the shaft's `b` from grade to the pad top (`d - t`) and the pad's `B` below:

```
b_eff = ∫₀^{γd} z b(z) (γd - z) dz  /  (γ³d³/6)
      = b + (B - b) F,        F = [L³/6 - (L a²/2 - a³/3)] / (L³/6),  L = γd,  a = d - t
```

(F = 0 when the pivot is above the pad top, `L <= a`.) **If `B = b`, `b_eff = b` for every γ
and every d** — the second term is zero, not small — so a stepped pole of one width IS Eq.
18-1, bit for bit. That is the oracle property and the test asserts equality, not
approximation. `B` is the pad's dimension NORMAL to the motion: 1.5' for `PD-BW-RE`'s 30"x18"
under E-W motion; 2.0' for the 24" squares; for the landing (a guard push acts "in any
direction", no axis resolves) the LEAST plan dimension, 1.5' on the 30"x18" and 18" pads.

**By hand, `PT-BW-GW` at d = 4.33', γ = 0.91743, t = 1.00', B = 2.00':**

```
L = 0.91743 x 4.33 = 3.9725      a = 4.33 - 1.00 = 3.3300
L³/6            = 62.688 / 6                          = 10.4480
L a²/2 - a³/3   = 3.9725 x 11.0889 / 2 - 36.926 / 3   = 22.0252 - 12.3087 = 9.7165
pad share       = 10.4480 - 9.7165                    = 0.7315
F               = 0.7315 / 10.4480                    = 0.0700
b_eff           = 1.00 + (2.00 - 1.00) x 0.0700       = 1.070'
```

> ⚠ **WITHDRAWN 2026-09-21 for the four LANDING columns** (`PT-BW-W`/`-E`/`-GW`/`-GE`): the landing
> is tied to the garage stem (`north_entry_piers.md` §10), so they lean and are no longer
> lateral columns; `column_base` stops enumerating them. Their rows below are history. `PT-BW-RE`/`-RNE`
> are untouched — the tie does not reach them (they stand 20' east, on the canopy's own line).

### 9d. One column iterated by hand — `PT-BW-GW`, S1, γ = 0.91743

`P = 200 lb`, `h = 4.54'` **from grade** — the arm runs from the pad TOP, so the SHAFT's
3.50' comes off it, never the pole's 4.50'. Collapse the two and `h` drops a foot, unsafely.
`S1 = 50 d`, `A = 2.34 P / (50 d b_eff)`, `d' = 0.5 A [1 + sqrt(1 + 19.795/A)]`:

```
d = 4.4500  F 0.0646  b_eff 1.0646  A 1.9758  -> 4.2671
d = 4.2671  F 0.0731  b_eff 1.0731  A 2.0442  -> 4.3628
d = 4.3628  F 0.0685  b_eff 1.0685  A 2.0079  -> 4.3122
d = 4.3122  F 0.0709  b_eff 1.0709  A 2.0270  -> 4.3388
d = 4.3388  F 0.0696  b_eff 1.0696  A 2.0169  -> 4.3247
d = 4.3247  F 0.0703  b_eff 1.0703  A 2.0222  -> 4.3322
  ...oscillates in, converges                      d = 4.33'   against 4.50'   d/c 0.96
```

### 9e. All six, both ends of the pivot band

Required TOTAL embedment (grade to pad bottom), ft, with `b_eff` at the solution:

| column | `B` | S1, γ 0.91743 | S1, γ 0.92450 | 2 S1, γ 0.91743 | 2 S1, γ 0.92450 | has | d/c |
|---|---:|---:|---:|---:|---:|---:|---:|
| `PT-BW-RE` | 1.5 | 7.056 (1.006) | 7.052 (1.007) | 5.363 | 5.359 | 8.33 | **0.85** |
| `PT-BW-RNE` | 2.0 | 7.039 (1.012) | 7.031 (1.015) | 5.326 | 5.317 | 8.33 | **0.85** |
| `PT-BW-W`/`-E` | 1.5 | 4.389 (1.034) | 4.385 (1.036) | 3.302 | 3.298 | 7.12 | **0.62** |
| `PT-BW-GW` | 2.0 | 4.330 (1.070) | 4.320 (1.076) | 3.208 | 3.200 | 4.50 | **0.96** |
| `PT-BW-GE` | 1.5 | 4.389 (1.034) | 4.385 (1.036) | 3.302 | 3.298 | 4.50 | **0.98** |

The 0.91743 end governs every column (the shallower pivot credits less of the pad). All four
readings agree on every column, so all six publish on Table 1806.2's own S1.

**The verdicts do not flip anywhere in γ ∈ [0.85, 1.00]** — S1, total embedment needed:

| γ | RE | RNE | W/E | GW | GE |
|---|---:|---:|---:|---:|---:|
| 0.85 | 7.072 | 7.072 | 4.427 | 4.407 | 4.427 |
| 1.00 | 6.996 | 6.920 | 4.334 | 4.220 | 4.334 |

At γ = 0.85 the canopy's pivot (6.01') sits ABOVE its pad top (6.07'), so the pad's width
earns nothing and the answer is the bare-shaft 7.07' of §3 — still under 8.33'. The pad's
width is never what decides a verdict here.

### 9f. Where the gain came from — read this before quoting it

`b_eff` is **1.006 to 1.070**: the pad's width is worth 0.6% to 7%, i.e. 0.01'–0.12' of
required depth. Everything else in the move from §3's column to 9e's is the **datum** — a foot
of concrete that was always in the ground and was not being counted. A reader who skims will
credit "passive on the pad"; a reviewer who checks will find it worth almost nothing, and they
will be right. With b = 1.00 throughout the canopy needs 7.07' against 8.33' (0.85) and the
landing pair 4.45' against 4.50' (0.99) — every column passes on the datum alone.

### 9g. What this does NOT do

- **It does not add a resisting moment to §1807.3.2.1's answer.** `d` is a depth, not a
  moment; a term computed in a different free body cannot be added to it. The pad enters the
  code's own pressure field as a width, and the code's unmodified formula is solved.
- **It does not divide the base moment between the shaft and the pad.** See §5's first
  bullet: that is `base_rotation`'s open question and it stays open.
- **It does not restore passive on `spread_base.py` or `retaining_basis.py`.** See §5.
- **It does not reach a wall-borne column.** `column_base`'s scope is unchanged: a column on
  a foundation wall is `column_support/<wall>`, one question one item.

## Sources

- IBC 2018 §1807.3.2.1, §1807.3.2.2 (Eq. 18-3, S3 at the FULL depth), §1806.2 Table,
  §1806.3.4. Text confirmed 2026-09-18 against ICC Digital Codes, UpCodes and the 2015
  Seattle Building Code's verbatim reproduction of Chapter 18.
- `notes/north_entry_piers.md` §8b (the frame shear and the base moments), §6 (why the two
  pier lines bottom at different elevations), §8d (the prose this note replaces).
- `notes/balcony_moment_columns.md` §2c (the guard load taken wholly on one column).
