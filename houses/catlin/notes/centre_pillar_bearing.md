# The two centre balcony pillars — cross-grain bearing where they stand on the porch

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** `PT-SG-BR2` and `PT-SG-BF2`, the two 6x6 wood pillars in the middle of the
balcony's six. They are the only two that do not land on concrete: both stand on the porch
deck `FS-SG-PORCH` and carry `BM-SG-BLC`, the balcony's centre glulam.
**Written:** 2026-09-03, by hand, before the calculation it oracles was encoded.
**Oracle for:** `engineering/post_bearing.py`, reported by `structural.deck_post_bearing`;
reproduced by `tests/test_post_bearing.py`.
**Companions:** `notes/balcony_moment_columns.md` (the four cast columns and the glulam above
these two), `notes/sunken_garden_piers.md` (`PT-SG-COL`/`FCOL`, which is where this load goes
next).

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
     (joists CROSS it,                   (joists CROSS it too, since 2026-09-03:
      17" cantilever)                     2-3/4" cantilever_start = 4-1/2" bearing)
           │                                   │
       PT-SG-COL                          PT-SG-FCOL      12" round cast columns
```

Both pillars are 6x6 KDAT, dressed **5-1/2" square**. `PT-SG-BR2` stands 3" south of the
back-beam axis; `PT-SG-BF2` stands **on** the front-beam axis, which is `RL-SG-PORCH`'s guard
line.

**The framing changed under `PT-SG-BF2` on 2026-09-03 and the pillar did not move.**
`FS-SG-PORCH`'s `JoistSpec` gained `cantilever_start = 2-3/4"`, so the joists run past the
front beam instead of dying on its centreline. In inches, the joist field now ends at
y = −116.75", the front beam's far face is at −116.25" and the post's own south face is at
−116.75": the joists clear the beam by 1/2" and end flush with the post. Nothing about §2's
statics changes — the pillar carries the same reaction from the same beam at the same
station. What changes is which NDS case each of the two planes below is in.

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
* `PT-SG-BF2` now does too — **5-1/2"**, and NOT an end bearing. It was 2-3/4" while the
  joists stopped on the front beam axis: half the footprint was over the deck edge with no
  joist under it. The 2-3/4" `cantilever_start` was chosen to be exactly the post's half
  width, so the field's south edge and the post's south face coincide at y = −116.75" and
  the whole footprint is over wood. `at_end` in `_post_on_field_in` tests for the field
  ending *inside* the footprint, so a flush coincidence is not an end bearing.

```
PT-SG-BR2   A = 4.5 × 5.50  = 24.75 in²      2,647 / 24.75 = 107 psi
PT-SG-BF2   A = 4.5 × 5.50  = 24.75 in²      2,187 / 24.75 =  88 psi
```

### 3b. At the beam line — the joists' own bearing

What bears here is the JOIST, not the post, so the contact length is the geometric overlap of
the beam's 4-1/2" width with the joist field's own extent. The porch has one of each case on
the same deck, which is exactly why the beam's width cannot simply be used:

* **Back beam.** The joists run `column_south_offset_in` (17") past it to the deck's north
  edge, so they cross the whole 4-1/2".
* **Front beam.** They now cross it too. The beam's band is y = −116.25"…−111.75" and the
  field runs −116.75"…north, so the overlap is the beam's full **4-1/2"**. It was 2-1/4"
  while the joists stopped on the axis — the ONE number this whole change turns on, because
  `_beam_bearing_in` measures the overlap of the beam's plan width with the joist field's
  extent and nothing else.

```
PT-SG-BR2   A = 4.5 × 4.50  = 20.25 in²      2,647 / 20.25 = 131 psi
PT-SG-BF2   A = 4.5 × 4.50  = 20.25 in²      2,187 / 20.25 = 108 psi
```

**This is not a trick to pass a check.** A joist should bear ACROSS the beam it lands on
rather than stop on its centreline; 2-1/4" met IRC R507.6's 1-1/2" minimum and no more. That
the correct framing also halves the governing ratio is the calculation agreeing with the
detail, and the 2-3/4" oversail is well inside the 8" `bearing_plan_tolerance_in` past which
the uplift check would find neither a derived tie nor a hanger and FAIL all 32 members.

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
PT-SG-BF2  post on joist, l_b 5.50", interior    C_b = 5.875/5.50 = 1.068 → 304 psi
           joists on front beam, l_b 4.50"       C_b = 4.875/4.50 = 1.083 → 308 psi
```

Both pillars now read the same two rows, which is the point: the two ends of this porch are
framed alike. Until 2026-09-03 `PT-SG-BF2` earned **C_b = 1.000 at both planes** — an end
bearing has no fibres beyond it — so it was penalised twice over, once on area and once on
the factor. Extending the joists lifted both at once.

---

## 5. The verdict, and the before/after

| | plane | demand | capacity | **d/c** |
|---|---|---:|---:|---:|
| `PT-SG-BR2` | post on the joist top | 107 psi | 304 psi | **0.35** ✓ |
| | joists on `BM-SG-BKW` | 131 psi | 308 psi | **0.42** ✓ |
| `PT-SG-BF2` | post on the joist top | 88 psi | 304 psi | **0.29** ✓ |
| | joists on `BM-SG-FRW` | 108 psi | 308 psi | **0.35** ✓ |

**One step back, with the joists stopping on the front beam axis** (`PT-SG-BF2` on the axis,
`plies=3` — the state this note recorded earlier on 2026-09-03):

| | plane | demand | capacity | **d/c** |
|---|---|---:|---:|---:|
| `PT-SG-BF2` | post on the joist top | 177 psi | 285 psi | **0.62** |
| | joists on `BM-SG-FRW` | 216 psi | 285 psi | **0.76** |

Half the improvement is area (2-3/4"→5-1/2" and 2-1/4"→4-1/2", each halving a stress) and
half is `C_b` coming back at both planes. `PT-SG-BR2`'s rows do not move: it was never at a
field end, and its beam was already crossed.

**Two steps back, at `plies=1` and with `PT-SG-BF2` 3" north of the front axis:**

| | plane | demand | capacity | **d/c** |
|---|---|---:|---:|---:|
| `PT-SG-BR2` | post on the joist top | 311 psi | 304 psi | **1.02** ✗ |
| | joists on `BM-SG-BKW` | 380 psi | 308 psi | **1.24** ✗ |
| `PT-SG-BF2` | post on the joist top | 311 psi | 304 psi | **1.02** ✗ |
| | joists on `BM-SG-FRW` | 672 psi | 285 psi | **2.36** ✗ |

**What each part of the fix bought.** The plies did most of it — 1-1/2" of stock to 4-1/2"
divides every demand by three. Extending the joists 2-3/4" past the front beam did the rest
at `PT-SG-BF2`, halving both areas and restoring `C_b` at both planes, for the price of a
2-3/4" longer joist. Moving `PT-SG-BF2` onto the front-beam axis bought the bearing itself
almost nothing; what it bought is everything else about that pillar: it stands over `PT-SG-FCOL` rather than 3"
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

## 6. The base tie — a strap and angles, and the three parts that came before

This section is a **capacity inventory, not a design.** Nothing in this model computes a net
uplift demand at this joint (§7), so what follows sizes the parts against a hand estimate and
records what each report actually publishes.

**The demand, worked from this house's own wind basis.** `typehaus/wind.py`, V_ult 115 mph
(MN Rules 1309.0301), Exposure B, RC II: q_h ≈ 16.5 psf at the 15 ft balcony height. Treating
the balcony as a free roof, C_N ≈ 1.2, and 0.6 for ASD gives ≈ 11.9 psf net upward. Over this
pillar's ≈ 48 ft² tributary that is ≈ 575 lb up, against 0.6 D ≈ 290 lb of dead load holding
it down: **≈ 285 lb net**, call it **300–600 lbf** for design. Every number in that chain is a
judgement — the tributary area especially — which is why §7 leaves the sizing open.

### The parts, and what each face has beside it

| pillar | west face (flush) | north face | south face | east face |
|---|---|---|---|---|
| `PT-SG-BR2` | 1 × `MSTA12Z` | 1 × `L50Z` | 1 × `L50Z` | — |
| `PT-SG-BF2` | 1 × `MSTA12Z` | 1 × `L50Z` | — | — |

**The strap takes the one flush vertical pair in the joint.** The post's west face and the
joist pack's west face are both at x = 213.25" at *both* pillars — the post spans
213.25"…218.75" and the pack 213.25"…217.75", so the west faces are coplanar and the east
face has a 1" step. A 12" `MSTA12Z` lies flat across that pair with 6" in each member. Its
2-1/2" nails cross the 1-1/2" outer joist and land 1" into the first sister, so two of the
three plies are engaged. **ICC-ES ESR-2105 Table 3, MSTA12 row: 940 lbf allowable tension at
C_D 1.6**, through 10 − 10d × 2-1/2" common nails, five per member.

**The angle earns its place only where there is pack beside the post.** An `L50Z`'s 5" leg
sits inside the pack's 4-1/2" width with 1/4" over each edge; an `L70Z`'s 7" leg would
overhang by 1-1/4" each side. The E/W faces offer 1-1/2" of squash block and nothing more, so
an angle there would be fiction — and after the joist extension `PT-SG-BF2`'s south face has
the deck edge behind it. **ESR-3096 Table 4, L50 row: F1 535 lbf and F2 820 lbf, both at
C_D 1.6**, through 6 SD9112 screws, three per leg.

**Wet service is applied, not deferred.** ESR-2105 §4.1 and ESR-3096 §4.1 carry the same
sentence: where wet service is expected the allowable loads "must be adjusted by the wet
service factor, C_M, specified in the NDS" for dowel-type fasteners. An open deck frame is
that condition. **C_M = 0.70:**

```
MSTA12Z   uplift   940 × 0.70 = 658 lbf
L50Z      F1       535 × 0.70 = 375 lbf
L50Z      F2       820 × 0.70 = 574 lbf
```

```
PT-SG-BR2   658 + 375 + 375 = 1,408 lbf   against a 300-600 lbf demand
PT-SG-BF2   658 + 375       = 1,033 lbf
```

That the strap's 940 lbf is *not* footnote 5 in Table 3 is what makes the derate apply: the
nails govern, not the steel, and §4.1's clause is written about fastener lateral design
values. A steel-governed row would not take C_M.

### The three parts that stood here before

* **`ABU66SS` stainless standoff base, until 2026-09-03.** It has no published value at this
  joint: every ABU number is measured with the stirrup bearing on CONCRETE through a 5/8"
  cast-in anchor, and ESR-1622 §5.6 puts even that anchor outside its own scope. On a deck
  there is no pour and no cast-in bolt. (The stainless ABU66SS is still absent from ESR-1622
  — §3.2.1 evaluates ASTM A653 galvanised steel and Table 2 lists no SS model — but since
  2026-09-11 that is no longer a capacity objection: Simpson letter L-F-SSNAILS rates it at
  the galvanised ABU66's values. The objection here survives it, because those values are
  measured bearing on CONCRETE and this joint is wood-on-wood.) And the reason for the
  standoff went with the concrete: the
  1" gap was cited to IRC R317.1.4 Exception 1/3, which governs a wood column on CONCRETE.
* **`DTT2Z` deck tension tie, for part of the same day.** A joint Simpson do publish for a
  post on framing, and ESR-2330 §3.2.1 covers the -Z suffix (the report is **ESR-2330**, not
  ESR-2320 — that one is take-up devices and has no DTT in it). But one-sided: eccentric on a
  6x6, needing a 1/2" rod driven through the joist pack to a nut in the beam bay, and
  contributing nothing lateral at a base that is pinned by design.
* **`CCQ4.62-5.50SDS` column cap installed INVERTED, for the rest of it — and it does not
  fit.** This is the one worth remembering, because it read as correct on paper for a day. At
  `PT-SG-BF2` the rim, the joist tips, the beam axis and the post centre are all one line: a
  T, with no orientation for a channel. At `PT-SG-BR2` the squash blocks sit in the bays
  flanking the pack, exactly where an inverted channel's side plates must hang. It also
  carried 6,785 lbf against the ≈ 285 lb above — about twenty times the joint — and ESR-2604
  evaluates no inverted installation, so the orientation would have ridden on the seal.

### The species clause is family-wide, and that is why it survived all of this

ESR-2330 §3.2.2, ESR-2604 §3.2.2, **ESR-2105 §3.5.2** and **ESR-3096 §3.2.2** are the same
sentence: sawn or engineered lumber, specific gravity ≥ 0.50, moisture content ≤ 19%. At
SPF 0.42, **nothing at either end of these pillars had a published number** — the
`CCQ46SDS2.5` cap that has sat on top of them all along included. Swapping base parts could
never have fixed that, and swapping base parts has not unfixed it: the pillars are specified
**DF-L at SG 0.50** (`POST_WHITE_PAINT_DF`), which legitimises both ends at once for about
$180–450 of lumber, and only the citation moved when the part did.

Both reports also require the member to be at least as thick as the fastener is long. The
10d × 2-1/2" nail against a 4-1/2" pack and a 5-1/2" post, and the 1-1/2" SD9112 against the
same, are both met.

**One condition still rides with the parts**, and it belongs to the reviewer: **moisture
content**. §3.5.2 / §3.2.2 want ≤ 19% and an open deck frame is not that; there is no
published reduction for it in either report. Note that this is a *different* clause from
§4.1's wet service factor, which IS resolvable and IS applied above. The two are easy to
conflate, and conflating them either double-counts the derate or drops it.

**None of this changes a number in §3-§5.** The post stands directly on the joist pack, wood
on wood, with no plate between — which is one thing the strap-and-angle tie does that the
inverted cap did not, since the cap interposed a 7 gage channel floor plate. §3a graded the
post's own footprint onto the joists either way, so the plate was spare capacity rather than
a term, and removing it removes nothing.

**Field detail.** `PT-SG-BF2` sits square on `TR-SG-CAP-FRW/FRE`. A galvanised part bearing
on 0.019" aluminium coil in a wet exterior location drives a dissimilar-metal couple, and any
fastener through it penetrates the butyl tape that IS the dielectric between that coil and
the copper-treated KDAT. An **EPDM or HDPE isolator pad** goes between the connector steel
and the cap, and every penetration is sealed. ESR-3096 §3.2.1 adds that the lumber treater's
own recommendations govern corrosion resistance against a specific proprietary preservative;
G185 (the Z suffix) is the coating both parts carry, with hot-dip galvanised nails.

---

## 7. What this note does NOT do

- **No uplift.** This is a gravity bearing check. What holds these two posts down is §6's
  `MSTA12Z` strap and `L50Z` angles, and `CN-SG-CAP-R2`/`-F2` (CCQ46SDS2.5) at the beam over
  them; `notes/uplift_load_path.md` owns that path, and **nothing in this model computes a net
  uplift demand at all** — `structural.uplift_path_coverage` is a coverage rule and says so.
  §6's ≈ 285 lb is worked by hand from this house's wind basis, on a tributary area taken by
  eye; it is a sanity yardstick for choosing parts, not a demand this engine derived. Sizing
  these connectors by calculation is still open.
- **No eccentricity.** `PT-SG-BR2` stands 3" off the beam axis it delivers to. The strap is
  on one face and the angles on one or two others, so the tie itself is not concentric on the
  post either. Neither is carried as a moment in the joist or in the post. Bearing stress is taken as uniform over the contact area, which is the ordinary
  §3.10 idealisation and is still an idealisation.
- **No fastener design.** The strap's 10d nails, the angles' SD9112 screws and the blocks'
  end nails are not checked against anything beyond the published allowables §6 quotes and
  the conditions attached to them. In particular ESR-3096 Table 4 footnote 3 requires the
  terminating member to be constrained against rotation for the F1 direction where angles are
  not used in pairs, and footnote 5 requires angles on both sides to resist F2 both ways —
  `PT-SG-BF2` has a north angle only. Neither is verified here.
- **No long-term deformation limit beyond Fc⊥ itself.** NDS §3.10.2's value corresponds to
  about 0.04" of deformation; nothing here bounds creep at the two joints under sustained
  load, and the composite plank's own creep at summer surface temperature is the reason
  `plan/assemblies.py` calls for a plank cut-out at both pillars in the first place.
- **No check of the joists in bending or shear under the point load.** `deck_joist_span` grades
  the field against DCA6 for a uniform load; a 2,647 lb point load 3" from a bearing is
  essentially all shear into that bearing, which is why bearing is the question — but "essentially"
  is a judgement, not a calculation.

---

## Sources

Every standard and document this note rests on, collected from the citations above.
Citation style is the house style: issue year on first use (`ASCE 7-16 §29.3`),
section form after. A document is listed here only if a number in this note came
out of it.

- ASTM A653
- **AWC NDS 2018** — §3.10.2
- ICC-ES ESR-2105
- IRC R317.1.4, IRC R507.1, IRC R507.4, IRC R507.6
- MN Rules 1309.0301
