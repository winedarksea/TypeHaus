# The two centre balcony pillars — cross-grain bearing where they stand on the porch

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** `PT-SG-BR2` and `PT-SG-BF2`, the two 6x6 wood pillars in the middle of the
balcony's six. They are the only two that do not land on concrete: both stand on the porch
deck `FS-SG-PORCH` and carry `BM-SG-BLC`, the balcony's centre glulam.
**Written:** 2026-09-03, by hand, before the calculation it oracles was encoded.
**Oracle for:** `engineering/post_bearing.py`, reported by `structural.deck_post_bearing`;
reproduced by `tests/test_post_bearing.py`.
**Companions:** `balcony_moment_columns.md` (the four cast columns and the glulam above these
two), `sunken_garden_piers.md` (`PT-SG-COL`/`FCOL`, which is where this load goes next).

> ## ⚠ THIS JOINT WAS OVER, AND NOTHING IN THE MODEL SAW IT.
> Until this note and its calculation existed, catlin reported **0 FAIL** with `PT-SG-BF2`
> bearing at **d/c 2.36** and `PT-SG-BR2` at **1.24**. Neither was a modelling slip: the
> house's own comments carried the arithmetic, in prose, and got two things wrong that a
> calculation could not have got wrong.
>
> * **They graded a WET frame against a DRY allowable.** 425 psi is Fc⊥ for SPF in service;
>   NDS Table 4.3.1's `C_M` of 0.67 takes it to **285** on an open deck. `glulam_beam.py` has
>   applied wet service (`C_M` 0.53) to the glulam bearing on the *top* of these same posts
>   since the day it was written. One joint, two answers, and the wrong one was in the file
>   nobody grades.
> * **They divided the balcony six ways.** `BM-SG-BLC` runs the deck's full depth onto these
>   two pillars alone. A sixth of the deck is not what either of them carries — §2.
>
> What closed it was three plies of sister under each pillar, and moving `PT-SG-BF2` onto the
> front-beam axis. §5 is the before and after.

---

## 1. What is built

```
                    BM-SG-BLC  (3-1/2" x 11-7/8" treated glulam, 9'-8" long)
   N ──────┬───────────────────────────────────┬──────── S
        PT-SG-BR2                           PT-SG-BF2         6x6 KDAT, white
     20" overhang    7'-0" back span    12" overhang
           │                                   │
     ══════╪═══════════════════════════════════╪══════  FS-SG-PORCH, 2x8 @ 16" o.c.
           │                                   │        running N-S (direction="y")
     ┌─────┴─────┐                       ┌─────┴─────┐
     BM-SG-BKW/E                         BM-SG-FRW/E     4-1/2" 3-2x8 KDAT
     (joists CROSS it)                   (joists END on it, 2-1/4" bearing)
           │                                   │
       PT-SG-COL                          PT-SG-FCOL      12" round cast columns
```

Both pillars are 6x6 KDAT, dressed **5-1/2" square**. `PT-SG-BR2` stands 3" south of the
back-beam axis; `PT-SG-BF2` stands **on** the front-beam axis, which is also the porch deck's
south edge and `RL-SG-PORCH`'s guard line.

Each pillar's load crosses the grain **twice**:

1. its end grain onto the flat of the joist stock under it, and
2. that stock's flat onto the beam it lands on.

Both are compression perpendicular to grain, **AWC NDS 2018 §3.10.2**. Neither is a
prescriptive lookup: IRC R507.4 sizes a deck post's section against a tributary area and
R507.3.1 sizes what is under it *on the ground*, and no table in R507 publishes a wood-on-wood
bearing. That is what makes this an engineered item (decision #65).

---

## 2. The load — `BM-SG-BLC`'s reactions, by statics

`BM-SG-BLC` is `deck_beam/BM-SG-BLC`'s own subject and this note takes its line load from
there rather than re-deriving it: **50 psf (IRC R507.1: 40 live + 10 dead) over the 10'-0"
joist span the beam carries = 500 plf.**

The beam runs node to node from `N-SGB-NC` (y = −0'-10") to `N-SGB-SC` (y = −10'-6"), so it
is **9.667' long**, and it bears at two stations only:

```
station along the beam, from the north node:
   PT-SG-BR2   at  1.667'   (y = −2'-6")
   PT-SG-BF2   at  8.667'   (y = −9'-6")
   back span   =  7.000'
   overhangs   =  1.667' north (20"),  1.000' south (12")

total load   W = 500 × 9.667                        =  4,833 lb
```

**The overhangs are not symmetric and the split is not half each.** Taking moments about the
south support:

```
R_BR2 = W (s2 − L/2) / (s2 − s1)
      = 4,833 × (8.667 − 4.833) / 7.000
      = 4,833 × 3.833 / 7.000                        =  2,647 lb
R_BF2 = 4,833 − 2,647                                =  2,187 lb
```

An even split would have given 2,417 lb each — 9% light at the rear pillar. A 20" cantilever
does not merely add its own load to the support beside it, it levers load off the far one,
and the engine solves the two-support case exactly rather than approximating it.

**Where this differs from the tributary AREA the piers use.** `sunken_garden_piers.md` §2
hands each pillar 48.33 ft², which is half of `BM-SG-BLC`'s strip — the even split, on
purpose. A tributary area distributes a deck for a *bearing* check on the soil, where the pair
of piers is what matters; a bearing check on ONE pillar needs that pillar's own reaction. The
two numbers are 2,417 lb and 2,647 lb and they answer different questions.

---

## 3. What each bearing plane actually is

### 3a. Under the post — the joist ply pack

Each pillar has a `JoistReinforcement` at `plies=3` on the joist line at x = 18'-0": the
authored 2x8 plus two full-length sisters, **4-1/2" of stock**. Both pillars are on the same
joist line, so it is one pack of three serving both — a sister runs the whole joist, bearing
line to bearing line, so the plies asked for at the back beam already run under the front
pillar. (`resolve/floors.py` tops the line up to the deepest `plies` any entry on it asks for
rather than laying a second coincident pair.)

The bearing LENGTH is the pillar's own 5-1/2" **clipped to the joist field**:

* `PT-SG-BR2` sits well inside the field: the full **5-1/2"**.
* `PT-SG-BF2` sits on the field's south edge — the porch outline ends on the front beam axis —
  so half its footprint is over the deck edge with no joist under it: **2-3/4"**, and it is an
  END bearing.

```
PT-SG-BR2   A = 4.5 × 5.50  = 24.75 in²      2,647 / 24.75 = 107 psi
PT-SG-BF2   A = 4.5 × 2.75  = 12.38 in²      2,187 / 12.38 = 177 psi
```

### 3b. At the beam line — the joists' own bearing

What bears here is the JOIST, not the post, so the contact length is the geometric overlap of
the beam's 4-1/2" width with the joist field's own extent. The porch has one of each case on
the same deck, which is exactly why the beam's width cannot simply be used:

* **Back beam.** The joists run `column_south_offset_in` past it to the deck's north edge, so
  they cross the whole 4-1/2".
* **Front beam.** The joists **stop on its axis** (`JoistSpec.cantilever` is 0 at that end, so
  the deck stops there and each joist takes 2-1/4" of the 4-1/2"). Reading 4-1/2" here would
  credit twice the bearing that exists.

```
PT-SG-BR2   A = 4.5 × 4.50  = 20.25 in²      2,647 / 20.25 = 131 psi
PT-SG-BF2   A = 4.5 × 2.25  = 10.13 in²      2,187 / 10.13 = 216 psi
```

---

## 4. Capacity — and the two factors a casual check gets wrong

```
Fc⊥, SPF                        NDS Supplement Table 4A          425 psi
C_M, wet service                NDS Table 4.3.1, sawn lumber      0.67
C_D                             NOT APPLIED — §3.10.2 takes none  1.00
                                                                 -------
                                                            F'c⊥ = 285 psi
```

**SPF at 425, not SP at 565 or DF-L at 625.** The model records a nominal section and no
species, so the softest species this frame could reasonably be built from is what it is graded
against. A frame that passes at 425 passes at either of the others.

**`C_M` 0.67, and it is the whole argument in the box above.** These joists stand outdoors
under an open deck with no enclosure. 425 → 285 is a 33% reduction, and it is the difference
between `PT-SG-BR2` passing at d/c 1.02 and failing at 1.24 in the state that governs it.

**No `C_D`.** §3.10.2 takes no load duration factor on Fc⊥: it is a deformation limit, not a
strength one. Applying the 1.0 that a deck's occupancy live load would take anyway makes no
difference here — but a check that reached for snow's 1.15 or wind's 1.6 would come out that
much optimistic, and this is the clause that forbids it.

**`C_b`, NDS §3.10.4.** `(l_b + 0.375)/l_b`, for a bearing shorter than 6" that is at least 3"
from the member's end — the fibres just beyond a short bearing carry some of it. A bearing AT
the end earns nothing, because there are no fibres beyond it:

```
PT-SG-BR2  post on joist, l_b 5.50", interior    C_b = 5.875/5.50 = 1.068 → 304 psi
           joists on back beam, l_b 4.50"        C_b = 4.875/4.50 = 1.083 → 308 psi
PT-SG-BF2  post on joist, l_b 2.75", AT THE END  C_b = 1.000              → 285 psi
           joists on front beam, joist END       C_b = 1.000              → 285 psi
```

---

## 5. The verdict, and the before/after

| | plane | demand | capacity | **d/c** |
|---|---|---:|---:|---:|
| `PT-SG-BR2` | post on the joist top | 107 psi | 304 psi | **0.35** ✓ |
| | joists on `BM-SG-BKW` | 131 psi | 308 psi | **0.42** ✓ |
| `PT-SG-BF2` | post on the joist top | 177 psi | 285 psi | **0.62** ✓ |
| | joists on `BM-SG-FRW` | 216 psi | 285 psi | **0.76** ✓ |

**Before, at `plies=1` and with `PT-SG-BF2` 3" north of the front axis:**

| | plane | demand | capacity | **d/c** |
|---|---|---:|---:|---:|
| `PT-SG-BR2` | post on the joist top | 311 psi | 304 psi | **1.02** ✗ |
| | joists on `BM-SG-BKW` | 380 psi | 308 psi | **1.24** ✗ |
| `PT-SG-BF2` | post on the joist top | 311 psi | 304 psi | **1.02** ✗ |
| | joists on `BM-SG-FRW` | 672 psi | 285 psi | **2.36** ✗ |

**What each half of the fix bought.** The plies did nearly all of it — 1-1/2" of stock to
4-1/2" divides every demand by three. Moving `PT-SG-BF2` onto the front-beam axis bought the
bearing itself almost nothing (2-1/4" of joist-on-beam is 2-1/4" either side of the axis); what
it bought is everything else about that pillar: it stands over `PT-SG-FCOL` rather than 3"
off it, it *is* the `RL-SG-PORCH` guard post at x = 18'-0" instead of standing 3" behind a
2x2 that needed its own blocking, and the two `JoistReinforcement` entries 3" apart on one
joist line became one.

**The two blocks per pillar are still there and they are not what fixed this.** Their
`source` says they stop rollover, and that is exactly and only what they do: at ±3" from a
beam axis with 1-1/2" stock they ran 2-1/4"–3-3/4" from it against a beam whose face is at
2-1/4" — tangent to the beam, never over it, able to shed load into the neighbouring joists
only through their end nails. Rollover was never the binding limit state here. Cross-grain
bearing was, and no block fixes bearing.

---

## 6. The connector, and why it is not an ABU

Both pillars carried an **`ABU66SS`** stainless standoff post base until 2026-09-03. Two
things were wrong with it, and neither is about the part's quality:

* **It has no published value at this joint.** Every number an ABU has is measured with the
  stirrup bearing on CONCRETE through a 5/8" cast-in anchor, and ICC-ES ESR-1622 §5.6 puts
  even that anchor outside its own scope. On a deck there is no pour and no cast-in bolt.
  (`library/hardware.py` also records that the *stainless* ABU66SS is not in ESR-1622 at all —
  §3.2.1 evaluates ASTM A653 galvanised steel and Table 2 lists no SS model — so the part
  carried no published number even where it did stand on concrete.)
* **The reason for the standoff went when the pillars left the concrete.** The 1" gap was
  cited to IRC R317.1.4 Exception 1/3, which is about a wood column on CONCRETE standing on a
  pedestal 1" above the floor. Wood on wood is not that condition, and holding the post 1" off
  the framing would put its whole reaction through a base plate instead of through the wood
  this note grades.

**A `CCQ4.62-5.50SDS` column cap, installed INVERTED**, replaces it: the U-channel sits over
the three-ply joist pack, the straps rise onto the 6x6, 16 factory SDS 1/4" × 2-1/2" screws
into the pack and 14 into the post.

A **`DTT2Z`** deck tension tie held this place for part of 2026-09-03 and is recorded here
because the reasoning is worth keeping. It is a joint Simpson do publish for a post on
framing, and ESR-2330 §3.2.1 covers the -Z suffix (the report is **ESR-2330**, not ESR-2320 —
that one is take-up devices and has no DTT in it). But it is one-sided: eccentric on a 6x6,
needing a 1/2" rod driven through the joist pack to a nut in the beam bay, and contributing
nothing lateral at a base that is pinned by design.

**The objection that actually settled it was the species, and it was never about the base.**
ESR-2330 §3.2.2 requires a wood member of specific gravity ≥ 0.50. So does **ESR-2604
§3.2.2**, for *every* cap and base in that report — including the `CCQ46SDS2.5` that has sat
on top of these same two posts all along. At SPF 0.42, **nothing at either end of these
pillars had a published number.** Swapping base parts could never have fixed that.

So the pillars are specified **DF-L at SG 0.50** (`POST_WHITE_PAINT_DF`), which legitimises
both ends at once for about $180–450 of lumber. ESR-2604 Table 2 then gives the base
6,785 lbf uplift at C_D 1.6 and 30,940 lbf download at C_D 1.0.

**Two conditions still ride with it**, and both belong to the reviewer:

* **Moisture content.** §3.2.2 also wants ≤ 19%, and an open deck frame is not that. There is
  no published reduction for it in this report.
* **Orientation.** ESR-2604 contains no inverted installation, no orientation clause and no
  base-side table. Simpson illustrate the configuration in their product literature, but that
  is not the evaluation report. The mechanism is orientation-independent — uplift is tension
  in the straps and their screws either way — which is the argument for it, and it is an
  argument rather than a citation.

**It does not change a number in this note.** Inverted, the channel's floor plate lies on the
pack and the post stands on that plate: 7 gage steel in direct bearing, a bearing plate and
not a standoff, so the joint is still wood-on-wood in the sense §3 grades. The plate is
4-5/8" wide against the post's 5-1/2", and spreading through 0.18" of steel is ignored
entirely — §3a grades the post's own footprint straight onto the joists. The plate is spare
capacity, not a term.

---

## 7. What this note does NOT do

- **No uplift.** This is a gravity bearing check. What holds these two posts down is the
  inverted `CCQ4.62-5.50SDS` of §6 and `CN-SG-CAP-R2`/`-F2` (CCQ46SDS2.5) at the beam over
  them; `notes/uplift_load_path.md` owns that path, and **nothing in this model computes a net
  uplift demand at all** — `structural.uplift_path_coverage` is a coverage rule and says so.
  So the 6,785 lbf is an available capacity with no demand beside it. Sizing these two
  connectors by calculation, rather than by having a rated part present, is still open.
- **No eccentricity.** `PT-SG-BR2` stands 3" off the beam axis it delivers to, and
  `PT-SG-BF2`'s footprint is half over the deck edge. Both put the resultant somewhere other
  than the centroid of the bearing area, and neither is carried as a moment in the joist or in
  the post. Bearing stress is taken as uniform over the contact area, which is the ordinary
  §3.10 idealisation and is still an idealisation.
- **No fastener design.** The SDS screws, the 1/2" rod and the blocks' end nails are not
  checked against anything. §6's ESR conditions are as far as this goes.
- **No long-term deformation limit beyond Fc⊥ itself.** NDS §3.10.2's value corresponds to
  about 0.04" of deformation; nothing here bounds creep at the two joints under sustained
  load, and the composite plank's own creep at summer surface temperature is the reason
  `plan/assemblies.py` calls for a plank cut-out at both pillars in the first place.
- **No check of the joists in bending or shear under the point load.** `deck_joist_span` grades
  the field against DCA6 for a uniform load; a 2,647 lb point load 3" from a bearing is
  essentially all shear into that bearing, which is why bearing is the question — but "essentially"
  is a judgement, not a calculation.
