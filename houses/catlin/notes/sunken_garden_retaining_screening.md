# Sunken-garden retaining walls — preliminary screening, NOT a design

> ## ⚠ THIS IS A SCREENING CALCULATION AND IT FINDS A PROBLEM.
> `W-SG-W2`, `W-SG-E2` and `W-SG-S` are free retaining walls under **IRC R404.4**, which
> requires an engineered design to a safety factor of 1.5 against sliding and overturning.
> The arithmetic below, on presumptive code values, **reaches 0.58–0.64 against sliding.**
> That is not a marginal call; it is a factor of two and a half short of what the code asks.
>
> This note exists to state that clearly and to hand a consultant the inputs. It is **not**
> a design, it does not substitute for one, and nothing in the model has been changed to make
> the check look better. `FoundationWall.engineering_spec` is deliberately **left unset**;
> see §6.
>
> ## ⚠ AND THE ENGINE NOW SAYS SO INDEPENDENTLY — CATLIN IS OFF 0 FAIL.
> `structural.foundation_unbalanced_fill` grew its own R404.4 sliding/overturning calculation
> the same day this note was written, from a different direction and by a different author.
> It reports **FAIL (error)** on all three walls: *"sliding is over by 162 % (d/c = 2.62,
> governed by sliding (IRC R404.4))"* — an implied factor of safety of **1.5 / 2.62 = 0.57**,
> against the **0.58** this note's §4 works by hand from the same code tables. **Two
> independent implementations agreeing to within a percent is the strongest evidence
> available that the finding is real**, and neither was written against the other.
>
> The check **refuses to run off the derived grade plane at all** — "the grade-plane proxy is
> not a safe input for a retaining-wall design" — so it needs the authored `unbalanced_fill`
> of §1 to evaluate. Removing that authored value would send it back to UNKNOWN, which would
> hide a real defect behind a modelling gap. It stays.
>
> **This takes the reference house off `scripts/verify.sh`'s 0-FAIL gate, and that is an
> owner's decision, not a modelling one.** The three ways out are: an engineer's stamped
> design (none exists), a geometry change (§4's lever table — and the screening explicitly
> declines to invent one), or a deliberate decision to carry these three reds the way
> `houses/starter` carries its own. Nothing here chooses for you.

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Written:** 2026-08-30, in the same pass that corrected the retained height (§1).
**Companion note:** `notes/balcony_lateral_bracing_design.md`. These are two asks to the same
consultant, not two problems — see §7.

---

## 1. The retained height was understated by 3'-4", and that is the first finding

Until 2026-08-30 the model derived these walls' unbalanced fill from the single global
`Site.grade` (−2'-10") down to the footing, giving **7.0'**. That is what a plane can see,
and the condition here is not a plane.

`params/raised_garden.py` builds a segmental retaining apron 3'-0" outboard of these walls'
outer faces, whose `TOP = ft(RETAINING_WALL_TOP_FT)` — the *same constant* these walls' tops
are set from. The apron therefore holds a terrace of soil at **+0'-6"**, standing 3'-4" proud
of the surrounding grade, **against the outer face of all three walls.**

```
unbalanced fill = wall top (+0'-6") − footing TOP (−9'-10 7/16")   = 10.37 ft
```

> **CORRECTION, 2026-08-30 (second pass).** The line above originally called −9'-10 7/16"
> the *footing underside*. It is the footing **top**: `resolve/envelope.py::_resolve_footing`
> resolves a wall-hosted footing at `z1 = wall.z0_m`, so the footing hangs entirely below the
> wall and `FT-SG-E2` runs −10'-10 7/16" to −9'-10 7/16". **10.37' is still the right number
> for what this line computes** — `unbalanced_fill` is the IRC quantity, fill against the
> wall measured to the wall's base, and that is what R404.1.1's 48" threshold and Table
> R404.1.2(8)'s rows are read against. Nothing authored in `params/sunken_garden.py` moves.
>
> What the slip did move is **§4**, which took 10.37' as `H` for a *stability* free body.
> There `H` runs to the **underside of the footing** — soil bears on the back of the heel as
> well as the back of the stem, and the plane being slid along is the footing's underside —
> so `H` = **11.37'** and the thrust is 20% larger. The engine made the identical slip in
> `engineering/retaining_wall._geometry()`, in a comment that asserted the opposite
> convention and arithmetic that followed the comment, and both are corrected under
> `BASIS_VERSION` 2.
>
> **§4's table below is NOT restated.** It is the frozen oracle for `analyse()` and
> `tests/test_retaining_wall_calc.py::ORACLE` reproduces it verbatim; re-deriving it here
> would test the correction against itself. §4 remains a correct hand pass *on its stated
> inputs*, and those inputs are a foot short. The corrected free body — and the resolution of
> the deficiency §4 found — is `notes/sunken_garden_court_free_body.md`.

`unbalanced_fill` is now authored on all three from `SPEC.retaining_top_ft +
SPEC.basement_depth_ft + 0.75`, the same arithmetic `_ret_top` and `_wall_bottom` are built
from, so it cannot drift from either. **This is a correctness fix, not a judgement**: the
apron was already in the model and the check simply could not see it.

**On the day it was made it moved no verdict**, which is what was checked before and after:
all three read UNKNOWN — engineered on either figure, because both are far past the 48" at
which R404.1.1 engages. What moved was what the engineer is being asked to design for, by
nearly half again. Within hours the check itself grew an R404.4 calculation (see the banner)
and that calculation **requires** this authored value — it will not run off a grade plane — so
what was a message-text correction is now the input that makes the whole grading possible.

---

## 2. Geometry, as modelled

| | |
|---|---|
| stem | 12" cast concrete, 9'-4 7/16" tall |
| footing | 7'-0" wide × 1'-0" deep, **centred on the wall axis** (`Footing.center_on="axis"`) |
| toe / heel | 3'-0" / 3'-0" |
| total height, top of wall to underside of footing | 10.37' |
| retained face | outboard (south / east / west), terrace at +0'-6" |
| resisting face | inboard, sunken-garden floor at −9'-4" — so the toe is buried **6 1/2"**, not 12" |
| assembly | `SUNKEN_GARDEN_WALL`, plain concrete, no vertical reinforcement authored |

---

## 3. Geotechnical inputs — every one from a code table, and a sensitivity band

**There is no geotechnical report for this site.** Every value below is a presumptive one,
which is precisely why the result should be read as a screening and not a design.

| quantity | value | source |
|---|---|---|
| soil class | GM (silty gravel) | `checks/code/mn_residential/profile.py` — and note the profile cites a *Hennepin* soil survey for a *Ramsey* parcel; see `plans/TODO.md` |
| active equivalent fluid pressure | 45 psf/ft | IBC Table 1610.1, SM/SC/GM/GC — the value the engine already uses |
| at-rest equivalent fluid pressure | 60 psf/ft | IBC Table 1610.1, same row |
| allowable vertical bearing | 2,000 psf | IBC Table 1806.2, class 4 |
| lateral bearing (passive) | 150 psf/ft below natural grade | IBC Table 1806.2, class 4 |
| coefficient of friction | 0.25 | IBC Table 1806.2, class 4, footnote a: **multiplied by the dead load** |
| cohesion | none | class 4 carries no cohesion value; class 5 is the row with 130 psf |
| soil unit weight | **110–130 pcf, carried as a band** | not a code value at all — see below |
| concrete unit weight | 150 pcf | conventional |

**Soil unit weight is a band and never a picked number.** No code table gives it, and it is
the one input here that directly scales the stabilising weight on the heel. 110 pcf is a
loose-to-medium silty gravel; 130 pcf is well-compacted. Both are run below, and the spread
between them turns out not to change the answer — which is itself worth knowing, because it
means a compaction spec is not the lever.

**Two lateral cases are run.** Active (45) presumes the wall can rotate enough to mobilise the
active wedge; at-rest (60) presumes it cannot. A free cantilever retaining wall is normally
designed active, and it is the more favourable of the two, so the active case is the one the
headline number comes from. The at-rest case is shown because these walls also form the
*enclosure* of a sunken court with a slab inside it, and a reviewer may well argue the
inboard restraint pushes them toward at-rest.

---

## 4. The calculation

Per lineal foot of wall, moments taken about the toe.

```
P    = ½ · EFP · H²                                    (lateral thrust, triangular)
W    = W_stem + W_footing + W_soil-on-heel             (all dead load)
F    = μ · W  +  ½ · 150 · d_toe²                      (friction + passive on the buried toe)
FS_sliding    = F / P                                  (required: 1.5)
FS_overturning = M_resisting / (P · H/3)               (required: 1.5)
q_max         from  x̄ = (M_r − M_ot)/W,  e = B/2 − x̄
```

| case | FS sliding | FS overturning | q<sub>max</sub> | eccentricity |
|---|---|---|---|---|
| **as built**, active 45, soil 110 pcf | **0.58** | 3.06 | 1,060 psf | 0.39' |
| **as built**, active 45, soil 130 pcf | **0.64** | 3.43 | 1,002 psf | 0.17' |
| **as built**, at-rest 60, soil 130 pcf | **0.48** | 2.57 | 1,344 psf | 0.63' |
| required | 1.5 | 1.5 | ≤ 2,000 psf | within B/6 = 1.17' |

**Sliding governs, and it is not close.** Overturning has a factor of 2× over its requirement
and bearing uses barely half the presumptive allowable, so a reviewer's attention belongs at
the base, not at the section. The whole soil-density band moves sliding by 0.06 — compaction
is not the answer.

### Why sliding is the one that fails

The footing is **centred on the wall**, 3'-0" toe and 3'-0" heel. That is a normal shape for a
bearing footing and a poor one for a retaining wall: the heel is what carries the column of
soil whose weight generates friction, and half the footing width here is on the wrong side of
the stem doing nothing for sliding at all. Compounding it, the toe is buried only 6 1/2"
because the sunken-garden floor is *below* the natural grade the passive term is measured
from, so passive resistance contributes about 26 plf against a 2,420 plf thrust — under 1 %.

### What would fix it, in ascending cost

| change | FS sliding | note |
|---|---|---|
| as built | 0.58–0.64 | |
| rebalance to a 1'-0" toe, same 7'-0" width | 0.84 | free at design time, impossible after the pour |
| widen to 9'-0" with a 1'-0" toe | 1.11 | +2 CY of concrete per wall run |
| the above + a 2'-0" shear key | 1.30 | key is cheap; it is a form, not a pour |
| widen to 11'-0", 1'-0" toe, 2'-0" key | **1.56** | clears 1.5 |

None of these is authored, and none should be. They are here so a consultant can see the shape
of the solution space and so that nobody concludes the walls need to be re-sectioned when what
they need is a base.

---

## 5. What this note does NOT do

- **No drainage or hydrostatic design.** Every number above presumes the drainage behind
  these walls works perfectly and no water pressure ever develops. A saturated backfill
  roughly doubles the thrust and would take sliding under 0.35. `DRW-SG-MAIN` and the
  fabric-wrapped stone exist; nothing here verifies they are adequate, and drainage is
  usually the first thing a retaining-wall design nails down.
- **No seismic.** Minnesota is SDC A/B and wind and soil govern, but that is asserted, not
  demonstrated, and no Mononobe-Okabe increment is applied.
- **No reinforcement design.** The stem is plain concrete in the model. A wall that has to be
  designed to R404.4 will almost certainly need vertical steel, and sizing it is not attempted
  here. No `vertical_reinforcement` string has been invented for these walls.
- **No frost-key interaction.** `FT-SG-*` sit 12"–21" below the sunken garden's own floor
  against a 42" frost depth, resolved on 2026-08-29 by ASCE 32 soil replacement. Whether that
  detail and a widened or keyed footing can coexist is not checked.
- **No global stability, no settlement, no construction sequencing.** A 10'-4" retained cut
  next to a tiered apron has a slip-circle question this note does not open.
- **No verification of the soil class itself.** GM comes from a soil survey for the *wrong
  county* (§3). The single highest-value thing anyone can buy before pouring differently is a
  geotechnical boring: μ = 0.25 is the presumptive floor for a broad class, and a real test on
  a genuine silty gravel could plausibly support 0.35–0.45, which would change the answer more
  than any amount of concrete.

---

## 6. Why `engineering_spec` is deliberately NOT authored

`FoundationWall.engineering_spec` is the field that says "an engineer designed this wall, here
is the citation", and authoring it makes `structural.foundation_unbalanced_fill` report PASS
and stand the prescriptive table down.

**It must not be authored here.** This screening did not find a wall that works and lacks
paperwork; it found a wall that does not reach the code's own safety factor on the code's own
presumptive values. Setting the field would convert an honest UNKNOWN into a fabricated PASS
on a calculation that found a failure — strictly worse than leaving the question open, because
the open question is visible and the PASS would not be.

What is authored instead: the corrected `unbalanced_fill` (§1), a pointer to this note from
`params/sunken_garden.py`'s `WALLS` block beside the existing `lateral_support="unsupported"`
justification, and an entry in `plans/TODO.md`. Whether the schema should grow an
`engineering_status`-style field — "screened, found deficient, awaiting design" — is a real
question and a separate decision; it should not ride in on this wall.

---

## 7. This and the balcony are one ask, not two

`notes/balcony_lateral_bracing_design.md` covers the structure standing *on* these walls, and
the two belong in the same envelope to the same consultant:

- **The apron is already documented as defective.** `params/raised_garden.py` carries its own
  "THE BASE COURSE HAS NEGATIVE EMBEDMENT" section. That apron is what creates the terrace
  §1 corrects for, so it and these three walls are **one coupled tiered system** — the upper
  tier's surcharge is the lower tier's load, and fixing either in isolation is guesswork.
- **The balcony bears on the same concrete.** `PT-SG-BR1`/`BR3`/`BF1`/`BF3` land on
  `W-SG-W1`/`E1`'s tops, and the porch bears directly on those two side walls — so the porch's
  own east-west lateral path, which `plans/TODO.md` has open, is a concrete-and-geotech
  question about these walls rather than a framing question.
- **No `prices.toml` change accompanies this note**, deliberately. The screening recommends no
  geometry change, because the cheapest real lever (§5) is a geotechnical boring, not concrete
  — and pricing a footing widening nobody has designed would put a number in the estimate that
  the estimate cannot defend.
