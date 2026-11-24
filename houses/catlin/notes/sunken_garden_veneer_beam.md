# Sunken-garden veneer grade beam — hand-worked basis

**House:** catlin
**Structure:** `W-SG-BRKBM` (the beam), `W-B-BRICK` (the wythe it carries), `FT-B-S2` /
`FT-B-S3` (the footings it is isolated from), `SG_VENEER_BEAM_14` (the assembly).
**Written:** 2026-09-05, by hand. §6e re-worked 2026-09-21 (hooks, enclosing ties, footing
dowels); §6f added 2026-09-22 (TMS ℓ/600, end fixity, the joint rows) and §6d superseded by it.
**§6n (2026-11-23, owner: adjustable slotted tie, stainless flashing) closes §6m's UNKNOWN.** **§6m (2026-11-23, owner G8: a bond break at the base) refines §6l:** the ties are graded on drag and wind, not travel. **§6l (2026-11-23, decisions 10/11/29) refines §6k:** ties on the 2024 IRC's W2.8 row and on the studs only, steel
lintels over flat-headed reveals, the beam graded on its bed. **§6k (2026-11-04) is the basis now:** the beam is bedded on stone (`FB-SG-BRKBM`) flush on
the house strips, a soil-supported veneer footing; `veneer_beam/W-SG-BRKBM` retired, and the
brick stands 6 1/2" off the studs, inside the 2024 IRC's W2.8 tie row. §6j (the 11'-0" span
on the toes) is kept as the record of the member as it was graded.
**Oracle for:** `checks/structural/masonry_joint.py` (§6g/§6k, `tests/test_masonry_joint.py`),
`checks/structural/veneer_cavity.py` and the `veneer_anchor` keys (§6k,
`tests/test_veneer_cavity.py`), and `engineering/veneer_beam.py` — §6j's arithmetic, at a
synthetic span now that catlin keys no beam (`tests/test_veneer_beam_calc.py`); §3/§4 still
oracle the report-side `engineering/retaining_court/veneer_beam.py` at their literals.
The geometry is pinned by
`tests/test_catlin_contract_m3.py::test_the_veneer_beam_isolates_the_house_footing`.
**Companions:** `notes/sunken_garden_court_free_body.md` — the court's retaining system,
which this beam deliberately does **not** change.
**What is asked of the reviewer:** §3's flexural arithmetic and §5's tie question. §5 is the
one that needs a seal.

> ⚠ **The beam is not a strut for the retaining walls, and must not be sold as one.** The
> obvious hope — that a beam closing the court's north end props `W-SG-W1`/`W-SG-E1` — is
> false. Those two are already restrained top and bottom (porch beams pocketed in
> HUCQ410-SDS hangers, the deck diaphragm above, the garden slab at their feet) and pass
> `structural.foundation_unbalanced_fill` on the last published row of IRC Table
> R404.1.2(8). This beam is a thermal device that happens to be made of concrete.

> ⚠ **The ties are prescriptive on the 2024 IRC, and the permit application waits for Minnesota's
> 2024-based code (§6k, §6l).** 6 1/2" back of brick to face of stud: W2.8 adjustable wire reaches
> 6 5/8"; the 2018 table stops at 4 1/2". `veneer_anchor/W-B-BRICK` is the dated dependency (an
> R104.11 request is the fallback). §5.1's reasons not to anchor the wythe to the side walls, and
> why R703.15 does not govern, stand.

---

## 1. Why the beam exists

`W-B-BRICK` is 129 SF of unglazed brick standing at the bottom of an open court, exposed on
**both** faces above the garden slab, so it sits at outdoor air temperature all winter
(design −20 °F, AFI 3000). Until 2026-09-05 it bore on `FT-B-BRICK`, a 10"×5" plinth cast on
`FT-B-S2`/`FT-B-S3`'s own projecting toe. That put the wythe in direct series with the house
footing — whose underside is level with the court floor and whose entire frost protection is
its 34" drained #57 bed (ASCE 32; the R403.3 wings `SL-SG-FROST-W/N/E` are retired, C3-E10) plus the insulated form.

The break intended to interrupt that path was stated twice and drawn never:

| spelling | what it ordered | what it placed |
|---|---|---|
| `FT-B-BRICK.assembly = FOOTING_FPSF_20` | 16.0 SF of 2" XPS, via `takeoff/envelope.py` | nothing — a Footing resolves to one extruded blob |
| `FB-B-BRICK.cast_foam_in_aggregate = True` | nothing (a bool with no thickness, material or R) | nothing |
| `FB-B-BRICK.undercut = 2"` | 0.1 cy of ASTM C33 #57 washed crushed stone | the only modelled occupant of the gap |

One order of foam and one order of stone for the same 2" of space, no geometry for either,
and no check anywhere in the engine that grades a thermal break for continuity. The whole
condition sat at 0 FAIL.

## 2. Geometry

| term | working | value |
|---|---|---|
| beam clear span | court clear width, `_x_in_w` → `_x_in_e` (**superseded**: §6j, 11'-0" between the court footings' toes) | 19'-0" |
| beam bearing | 6" into each side wall (nodes on `_x_ax_w`/`_x_ax_e`) | 6" each end |
| beam section | `SPEC.wall_thickness_in` × (`_veneer_beam_top` − `_veneer_beam_bottom`) | 12" × 17-3/4" |
| beam concrete faces | −10" (north) … −22" (south) | |
| isolation board | 2" XPS, 40 psi, north face | −8" … −10" |
| `FT-B-S2/S3` south face | 25" strip (2026-11-05; widened inboard), `offset` **6"** off axis since 2026-09-05 | −4" |
| wythe | 3-5/8", on the beam's north edge | −10.05" … −13.675" |
| backup finished face | EPS face, since 2026-09-05 (**superseded** §6k: XPS face −4.06") | −6.05" |
| open cavity | EPS face (−6.05") to wythe (**superseded** §6k: 1 15/16") | **4.0"** |
| foam behind the wythe | 4" XPS + 2" EPS (**superseded** §6k: 2+2" XPS, no EPS) | 6.0" |
| anchor reach | brick back to sheathing/stud | ~10.05" |

**The strip retreated to −4" and the board did not follow it.** All four south strips are
on one face now, because the sunken garden's side-wall closure needs 2" of board across the
whole 84" of its own joint and could not have it while S2/S3 stood at −8" (see
`params/foundations._GARDEN_END_TRIMMED`). This beam's board stays at −8"…−10", so between
it and the house strip there are now 4" of bedding stone rather than a flush bearing. That
is a longer path through a worse insulator **in series with** the same 2" of XPS, so the
break is no weaker; and the beam bears nothing on that toe — it spans to the side walls,
which §2 is about. What the 2" trim was genuinely load-bearing for is the BEAM's own north
face at −10", and that is a fact about this beam and does not move with the strip.

Top and bottom are both borrowed, not invented: the top **is** `W-B-BRICK`'s authored
underside (−8'-6 7/16") and the bottom **is** the garden slab's (−10'-0 3/16"), so the beam
exactly fills a void the court already had. The garden slab's stone course runs continuous **underneath** it
— the beam spans to the side walls and delivers nothing to the strips' bed.

## 3. Flexure

Loads, per foot of span:

| term | working | value |
|---|---|---|
| wythe | 8.5 ft × (3.625/12) ft × 120 pcf | 308 plf |
| beam self-weight | (12/12) × (17.75/12) × 150 pcf | 222 plf |
| **w** | | **530 plf** |

The wythe top dropped to −8" on 2026-09-16 (under the porch joists): 7.87 ft, 285 plf. 308 is
kept as a conservative envelope; nothing below is re-worked.

### ⚠ Corrected 2026-09-14. The superseded pass is kept below it.

Two things were wrong with the original and they compounded: a **service** moment was
divided by a **φ-reduced** resistance, and the minimum steel was computed at **f'c 4,000**
on a member cast from a 5,000 psi mix. The first understated the demand, the second
understated the minimum, and between them the selected 2 #5 read as clearing a bar it does
not clear.

**Load factor.** ACI 318-19 Table 5.3.1: this member carries a brick wythe and its own
concrete and nothing else, so (5.3.1b) `1.2D + 1.6L` collapses to 1.2D — which is not a
combination the code publishes — and **(5.3.1a) `U = 1.4D` governs**.

**Effective span.** §6.3.2.1: the lesser of clear span + d and centre-to-centre of supports.
With 6" of bearing each end, centre-to-centre is 19.5 ft and clear + d is 20.26 ft, so
**19.5 ft** governs. (The original took 19.0 ft "conservatively"; on a simple span the
longer span is the conservative one, so that reasoning had the sign backwards too.)

```
w   = 308 + 222                                       =   530 plf   (service, dead only)
wu  = 1.4 × 530                                       =   742 plf
L   = min(19.0 + 15.06/12, 19.0 + 0.5)                =  19.5 ft
Mu  = 742 × 19.5² / 8                                 = 35,268 ft-lb  = 35.3 ft-k
Vu  = 742 × 19.5 / 2                                  =  7,234 lb
d   = 17.75 − 2.0 cover − 0.375 stirrup − 0.625/2     =  15.0625 in
As  = Mu × 12 / (0.9 × 60,000 × 0.9 × 15.0625)        =  0.578 in²   (demand)
```

**ACI 318-19 §9.6.1.2 is the GREATER of two expressions, at the mix actually specified:**

```
3 √5,000 × 12 × 15.0625 / 60,000                      =  0.639 in²   <- governs
200 × 12 × 15.0625 / 60,000                           =  0.603 in²
```

**2 #5 is 0.620 in² and does not clear 0.639.** It is about 3% short — small, and a minimum
is a minimum. §9.6.1.3's escape (steel one third over the demand) does not rescue it either:
4/3 × 0.578 = **0.771 in²**, larger still.

**3 #5 bottom (0.93 in²) is the section.** Checking it:

```
a     = 0.93 × 60,000 / (0.85 × 5,000 × 12)           =  1.094 in
φMn   = 0.9 × 0.93 × 60,000 × (15.0625 − 0.547) / 12  = 60,747 ft-lb   d/c 0.58  ✓
φVc   = 0.75 × 2 √5,000 × 12 × 15.0625                = 19,174 lb      d/c 0.38  ✓
```

Mirror 3 #5 top for the pocket restraint at each end. **The stirrups are no longer
detailing** — see §4: the torsion is above ACI's threshold, so they must be closed hoops
with 135° hooks, not the open #3 the superseded pass called for.

#### Superseded: the 1.2D / f'c 4,000 pass (retired 2026-09-14)

```
M  = w L^2 / 8   = 0.530 × 19.0^2 / 8            = 23.9 ft-k     <- SERVICE moment
d  = 17.75 - 2.5 (cover + bar)                   = 15.25 in
As = M / (phi × fy × 0.9d)
   = 23.9 × 12 / (0.9 × 60 × 0.9 × 15.25)        = 0.39 in^2     <- service ÷ φ-reduced
```

It concluded "2-#5 bottom (0.62 in²) governs by detailing, not by demand — d/c on the steel
is 0.63, and ACI 318-19 §9.6.1.2 minimum (3√f'c·b·d/fy = 3√4000 × 12 × 15.25 / 60000 = 0.58
in²) is the binding number", with #3 stirrups at 8" o.c. and shear d/c 0.29 at f'c 4,000.
Every number in that paragraph is superseded. **The engine moved to 3 #5 before this note
did**, which is the wrong way round and is why the correction is written out in full here
rather than quietly swapped.

## 4. Torsion from the eccentric wythe

The wythe sits on the beam's north edge, not its centreline, because centring it would cost
the cavity (the wythe's position is set by the beam and did not change
on 2026-09-05, so this is unaffected by the EPS):

```
e  = beam centre (-16") - wythe centre (-11.86")   = 4.14 in
t  = 308 plf × (4.14/12) ft                        = 106 ft-lb per foot
```

### ⚠ Corrected 2026-09-14: two provisions, two answers, and only one was quoted

The original said "compatibility torsion may be neglected below the cracking threshold" and
compared the demand against a T_cr it put "on the order of 9 ft-k at f'c 4000". That
conflates ACI 318-19 **§22.7.4.1**, the *threshold* below which torsion may be ignored
outright, with **§22.7.5.1**, the *cracking* torsion below which an indeterminate member may
redistribute. They differ by a factor of sixteen — 0.25 against 4.0 on the same section
term — and the demand lands between them.

At the mix actually specified, Acp = 12 × 17.75 = 213 in², pcp = 2(12 + 17.75) = 59.5 in,
so Acp²/pcp = 762.5 in³:

```
Tu     = 1.4 × 106.26 ft-lb/ft × 19.5 / 2               =  1,450 ft-lb   (factored, support)
φT_th  = 0.75 × 0.25 √5,000 × 762.5 / 12                =    842 ft-lb   §22.7.4.1
φT_cr  = 0.75 × 4.00 √5,000 × 762.5 / 12                = 13,479 ft-lb   §22.7.5.1
```

**Below cracking, so it does redistribute.** Tu is 11% of φT_cr. The beam is cast into both
side walls and the garden slab bears against its full south face for the whole span, so
§22.7.3.2's redistribution is available and the beam is not asked to resist the twist in
equilibrium. That part of the original conclusion stands.

**Above the threshold, so the detailing is still owed.** Tu is **1.7×** φT_th, and §22.7.4.1
only permits torsion to be ignored *below* that line. So §9.6.4's minimum torsional
reinforcement applies: **closed hoops with 135° hooks plus longitudinal torsional steel**,
not the open #3 stirrups §3 originally specified. That is a real change to what gets tied,
and it was hidden by comparing against the wrong provision.

The redistribution argument depends on the slab bearing being real. It is carried as an
unresolved item rather than assumed, because a slab that is poured short of the beam's face
takes the twist from compatibility back to equilibrium.

### 4a. The steel §4 owes, sized (addendum 2026-09-17)

§4 established that the torsion is above ACI 318-19's threshold and below cracking, so the
beam needs §9.6.4's **minimum** torsional reinforcement and no more. Section 12" × 17 3/4",
cover 2", #3 hoops, f'c 5,000, fy = fyt = 60,000.

```
hoop centreline  x1 = 12 − 2(2) − 0.375   = 7.625"     y1 = 17.75 − 4 − 0.375 = 13.375"
ph = 2 (7.625 + 13.375)                   = 42.0"
§9.7.6.3.3  s ≤ min(ph/8, 12")            = min(5.25, 12) = 5.25"    -> #3 closed hoops @ 5"
§9.6.4.2    (Av + 2At)/s ≥ max(0.75 √f'c bw/fyt, 50 bw/fyt)
                         = max(0.01061, 0.01000) = 0.0106 in²/in
            provided 2 legs × 0.11 / 5    = 0.0440 in²/in             ✓
§9.6.4.3    Al,min = 5 √f'c Acp / fy − (At/s) ph (fyt/fy)
            At/s at its floor 25 bw/fyt   = 0.0050 in²/in   (the conservative reading:
                                             no torsion is designed, so none is credited)
                   = 5 × 70.711 × 213 / 60,000 − 0.0050 × 42.0 = 1.255 − 0.210 = 1.045 in²
```

**Where it goes (§9.7.5.1–.2).** Longitudinal torsion steel runs inside the hoops, one bar in
each corner, at no more than 12" around the perimeter, each bar at least 0.042 s = 0.21" and
not smaller than #3. The 3 #5 top and 3 #5 bottom already occupy the corners, but their
centres are 15.0625 − 2.6875 = **12.375" apart** vertically — over 12" — so each side face
takes **one #4 at mid-depth**. Total longitudinal steel against the combined demand, flexure
plus torsion (§9.5.4.3 permits combining them):

```
required   0.639 (§3, flexural minimum) + 1.045 (Al,min)   = 1.684 in²
provided   3 #5 + 3 #5 + 2 #4 = 0.93 + 0.93 + 0.40        = 2.260 in²   ✓
```

Authored on `W-SG-BRKBM` (`params/sunken_garden.py`): `top-y` 3 #5, `bottom-y` 3 #5,
`ties` #3 @ 5" (closed, 135° hooks), `horizontal` #4 count 1 per face (`layers=2`). The
corner continuity into the side walls (§5.2) is still the engineer's.

## 5. What is NOT graded here, and what needs a seal

1. **The veneer ties.** ⛔ *Superseded by §6k (2026-11-04): the brick is 6 1/2" off the studs
   and the EPS is gone. The R703.15 and side-wall paragraphs below still hold.*
   **Still engineered, but for a different reason since 2026-09-05.**
   The airspace is **4"** now, not 6", which is inside IRC R703.8.4's 1"-minimum and inside
   the 4-1/2" the prescriptive tables stop at. That is not what makes this hard. The beam
   fixes the wythe's foot 6" off the backup's structural face, so the anchor must reach
   **~10" from brick to stud** whatever fills the gap, and no prescriptive table contemplates
   a standoff like that. It stays a TMS 402 engineered item: eccentric compression on the
   anchor, buckling over its unbraced length, and the wythe's out-of-plane bending between
   anchor rows. **Not designed in this note** — the engine has no masonry-anchor calculation
   and nothing in `haus engineering` will ever report a ratio for it.

   What the 2026-09-05 EPS bought is that the problem became *designable*. Of the 10", 8" is
   now solid foam and only 4" is open air; before, 6" was unbraced. Specify a two-piece
   adjustable anchor rated for the full insulation thickness and **confirm the manufacturer
   publishes that thickness** — 6" is at the top of the standard catalog.
   That confirmation is a procurement item, not an assumption this note is entitled to make.

   **`IRC R703.15` does not govern this wall, and the distinction matters** because
   `plans/cost-options.md` §6 kills a different foam swap in this house on R703.15's 4"
   limit — and this wall now carries 6". R703.15 covers cladding *attached through* foam,
   where the fastener carries the cladding's dead weight in bending; it explicitly excepts
   anchored masonry veneer to R703.8. This wythe carries its own weight to **this beam**, so
   the anchors take wind only. Different load, different section, and the 4" limit is not
   this wall's. (The board is ASTM C578 Type II at 15 psi, so it would satisfy R703.15's
   compressive floor regardless.)

   **Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to reduce anchor count.** Two reasons,
   and the second is the real one. (a) It cannot work: unreinforced 3-5/8" brick spanning
   18'-8" horizontally develops roughly 400 psi of flexural tension at a 20 psf wind, against
   an allowable near 50 psi parallel to the bed joints — an order of magnitude short, and no
   anchor pattern at the ends changes it. (b) It is the wrong detail even if it did: clay
   brick grows irreversibly and concrete shrinks, so over 18'-8" the run wants roughly 0.15"
   of moisture plus thermal movement (BIA TN 18). Those two ends need a **soft joint**, not
   an anchor. Restraining a long wythe between two rigid concrete returns is how you crack
   it. The end condition is a sealant joint over compressible filler — authored and graded
   since 2026-09-22 (§6g).
2. **The end condition: CAST MONOLITHIC, settled 2026-09-14.** This note contradicted
   itself for as long as it existed — §4's torsion argument rested on the beam being "cast
   into both side walls", and this bullet described it as "chipped and doweled into an
   existing pour". Those are different members with different end restraints, and the
   `AN-SG-PLACEMENTS` record named `W-SG-BRKBM` in **no placement at all**, so the model
   broke no tie either way.

   It is cast with placement (2), in the same form as the five court walls. Three reasons,
   and the first is decisive: **the pour is not there yet.** Placement (2) is where
   `W-SG-W1`/`W-SG-E1` themselves are cast, so there is no "existing pour" to chip into
   unless the beam is deliberately deferred to a fourth placement — which
   `AN-SG-COLDWEATHER` is specifically about not doing. Second, the beam's top (−8'-6 7/16")
   and bottom (−10'-0 3/16") both sit inside placement (2)'s single form height, so it costs
   a blockout and no extra mobilisation. Third, §4's redistribution argument needs the fixed
   ends, and a doweled pocket into cured concrete is the one detail that would not provide
   them.

   The bearing itself was never the question: 7.2 k over 12"×6" = 100 psi against a 5,000 psi
   mix. What a doweled pocket *would* have made the question is dowel development into a wall
   cast first — and casting monolithic is how that question stops being asked.

   **What is still the engineer's** is the reinforcement continuity through the corner: the
   beam's 3 #5 top and bottom have to develop into the side walls' vertical steel, and this
   note does not design that lap.
3. **The thermal path itself.** §1 says the old detail was wrong and the new one routes the
   load into structure that is already broken from the house at the `TB-SG-*` isolation boards. It does
   **not** compute a frost isotherm. A 2" XPS board at R-9 (4.5 per inch, vertical, IRC Table R403.3(1) fn 3) across 12.7 SF replaces a
   contact that had 16.0 SF of assumed-but-unplaced foam over 16.0 SF of placed stone; that
   is unambiguously better and it is not a number.
4. **Whether the beam helps the retaining walls.** It does not. See the banner.

## 6. The registered record, at the model's own geometry (addendum 2026-09-20)

§3–§4 were worked at literals (a 308 plf envelope, 4.14" of eccentricity). `veneer_beam/
W-SG-BRKBM` reads the plan instead, so this section re-works every number at what the model
resolves. Worked by hand (a calculator, not the engine), then reproduced by
`tests/test_veneer_beam_calc.py`. Nothing in §3–§5 is withdrawn; §6 is the record's basis.

### 6a. Inputs, read off the model

| term | source | value |
|---|---|---|
| section width | `SG_VENEER_BEAM_14`'s `concrete` layer ONLY — the 2" `xps-break` is not section | **12.0"** |
| section depth | beam z −120.1875" … −102.4375" | 17.75" |
| concrete faces | resolved `concrete` polygon, y −22" … −10" | centre −16.0" |
| supports | `W-SG-W1` concrete x 90"…102", `W-SG-E1` x 330"…342"; beam concrete x 96"…336" | |
| clear span | 330 − 102 | **228" = 19.0 ft** |
| bearing | 102 − 96 = 336 − 330 | 6" each end |
| wythe | `W-B-BRICK` `brick` layer, y −13.685" … −10.06", z −102.4375" … −8" | 3.625" × 94.4375" |
| brick density | `brown-brick` 1,920 kg/m³ × 0.062428 | 119.86 pcf |
| mix, cover | `EXPOSED_MIX` f'c 5,000; `_VENEER_BEAM_STEEL` cover 2" | |
| steel | 3 #5 `bottom-y`, 3 #5 `top-y`, #3 `ties` @ 5", 1 #4 `horizontal` × 2 faces | |

The steel is authored as COUNTS. `retaining_basis.bar_for_roles` refuses a count on purpose (a
strip footing is graded per foot), so the record reads it through a sibling accessor,
`bar_count_for_roles`, and that refusal is untouched.

### 6b. Load, flexure and shear at U = 1.4D (ACI 318-19 Eq. 5.3.1a)

```
wythe  119.86 × (3.625/12) × (94.4375/12)               =   284.95 plf
beam   150 × (12/12) × (17.75/12)                       =   221.875 plf
w                                                        =   506.83 plf
wu     1.4 × 506.83                                      =   709.56 plf
L      min(19.0 + 15.0625/12, 19.0 + 6/12)               =    19.5 ft
Mu     709.56 × 19.5² / 8                                = 33,726 ft-lb
Vu     709.56 × 19.5 / 2                                 =  6,918 lb
φMn    (§3, unchanged: 3 #5, d 15.0625, a 1.094)         = 60,747 ft-lb   d/c 0.555
As,min (§3, unchanged)                                   =  0.639 in² of 0.93   0.687
φVc    0.75 × 2 √5,000 × 12 × 15.0625                    = 19,171 lb      d/c 0.361
```

`2λ√f'c` is Table 22.5.5.1(a), and it is earned: the hoops give Av/s = 2 × 0.11/5 = 0.044
in²/in against Av,min = 0.0106 (§9.6.3.4). The 308 plf envelope in §3 stays the report's
number; the record grades the wythe that is drawn.

### 6c. Torsion — designed in EQUILIBRIUM, not redistributed

§4 relied on §22.7.3.2 redistribution, which needs the garden slab to bear on the beam's
south face — an assumption no record can check. The record does not use it: it designs the
full factored twist as equilibrium torsion, which is conservative and still passes by a wide
margin.

```
e      −11.8725 − (−16.0)   (brick centre vs concrete centre)   = 4.1275 in
t      284.95 × 4.1275 / 12                                      =  98.01 ft-lb/ft
Tu     1.4 × 98.01 × 19.5 / 2                                    =  1,337.9 ft-lb
φTth   §4, unchanged                                             =    842.5 ft-lb  (Tu is 1.59×)
x1 = 12 − 4 − 0.375 = 7.625    y1 = 17.75 − 4 − 0.375 = 13.375
ph = 42.0    Aoh = 101.98 in²    Ao = 0.85 Aoh = 86.69 in²
§22.7.6.1  At/s = 1,337.9 × 12 / (2 × 0.75 × 86.69 × 60,000)     = 0.002058 in²/in
           provided, one leg  0.11 / 5                           = 0.0220     d/c 0.094
§22.7.7.1  √[(6,918/(12×15.0625))² + (16,054 × 42/(1.7 × 101.98²))²]
           = √(38.27² + 38.13²)                                  =  54.03 psi
           φ(2√f'c + 8√f'c) = 0.75 × 10 × 70.711                 = 530.3 psi   d/c 0.102
```

The four detailing rows, the §4a steel, now graded:

```
§9.7.6.3.3  s ≤ min(ph/8, 12) = 5.25"; provided 5"                        d/c 0.952
§9.6.4.2    (Av+2At)/s ≥ max(0.0106, 0.0100); provided 0.044            d/c 0.241
§9.6.4.3    Al,min = lesser of  1.2552 − 0.002058 × 42 = 1.1687
                              and 1.2552 − 0.0050 × 42   = 1.0451      = 1.0451 in²
            Al (§22.7.6.1b) = 0.002058 × 42 = 0.0864 — the minimum governs
§9.5.4.3    required  0.639 (flexural minimum) + 1.0451                  = 1.684 in²
            provided  0.93 + 0.93 + 2 × 0.20                             = 2.26 in²  d/c 0.745
§9.7.5.1    perimeter spacing: top-to-bottom 17.75 − 2 × 2.6875 = 12.375,
            one side bar each face → 6.19"; across a row 3.31"; ≤ 12"    d/c 0.516
```

**Torsion detailing closes.** The hoops at 5" sit 5% inside §9.7.6.3.3's 5.25".

### ⛔ 6d. SUPERSEDED 2026-09-22 by §6f — the limit is ℓ/600 and the fixity is credited

§6d graded the simple span against ACI's ℓ/480 and printed TMS's ℓ/600 as NOT GRADED. **Both
halves of that are withdrawn**: TMS 402-22 §13.1.2.3 puts ℓ/600 on any horizontally spanning
member supporting veneer — a concrete beam included, which is what the 2016 edition's §5.2
placement left arguable — and the end restraint §6e designed is now credited, for
serviceability only. §6f is the record's deflection basis. The arithmetic below is unchanged
and still correct **at α = 0**, which is the row §6f's table opens with, and is kept because
every cracked-section term in §6f (Ec, Ig, Mcr, kd, Icr, λΔ) is worked here and not repeated.

### 6d. Deflection at α = 0 — the right limit, and it is close

`check_veneer_beam` compared a gross-section, ×3 deflection against **ℓ/240**. That is ACI's
limit for a floor NOT supporting anything a deflection damages, and a brick wythe is the
textbook thing it damages. The record grades ACI 318-19 Table 24.2.2's row for exactly this —
the part of the deflection occurring after the nonstructural element is attached, ≤ ℓ/480 —
on the simple span, because §6e does not establish the end restraint a fixed-end stiffness
would need.

```
Ec   57,000 √5,000                 = 4,030,509 psi     n = 29e6 / Ec = 7.195
Ig   12 × 17.75³ / 12              = 5,592.36 in⁴
Mcr  7.5√5,000 × 5,592.36 / 8.875  = 27,848 ft-lb       ⅔Mcr = 18,565 ft-lb
kd   6 kd² + 6.6915 kd − 100.79 = 0 → kd = 3.5787 in
Icr  12 × 3.5787³/3 + 6.6915 × (15.0625 − 3.5787)²      = 1,065.8 in⁴
all dead   Ma = 506.83 × 19.5²/8 = 24,090 ft-lb > ⅔Mcr
           Ie = 1,065.8 / [1 − (18,565/24,090)² (1 − 1,065.8/5,592.36)] = 2,052.5 in⁴
           Δi = 5 (506.83/12) 234⁴ / (384 Ec Ie)                     = 0.1993 in
beam only  Ma = 10,546 < ⅔Mcr → Ie = Ig;  Δi = 0.0320 in
λΔ   ξ 2.0 / (1 + 50 × 0.93/(12 × 15.0625)) = 2.0 / 1.2573          = 1.5908
after attachment  1.5908 × 0.1993 + (0.1993 − 0.0320)                = 0.4844 in
limit  234 / 480                                                     = 0.4875 in   d/c 0.994
```

**0.994 is a pass on ACI's row, and it is not comfortable — and the governing limit is
stricter still.** Every simplification is the conservative one (the wythe's two arched
openings are not deducted; the whole of the beam's own creep is counted after the brick goes
on), so the true number is lower — but a reviewer will see a 0.99. And the masonry industry's
number is **ℓ/600 = 0.390"**, which this simple span misses at **1.242**. §6f grades that row
with the end restraint credited, and that is what closes it.

### 6e. End restraint — closed 2026-09-21 (was INCOMPLETE)

The beam is cast monolithic with `W-SG-W1`/`W-SG-E1` (`AN-SG-PLACEMENTS` placement 2), and the
torsion of §6c and any fixity in §6d are delivered through that joint. It is anchorage: each
corner bar is longitudinal torsion steel and must develop fy at the support face, so the
§25.4.10.1 excess-steel reduction is not taken. Common terms (§25.4.3.1(a), ψe 1.0 galvanized
per §25.4.2.5, λ 1.0, ψc = 5,000/15,000 + 0.6 = 0.9333):

```
fy ψc / (55 √f'c) = 60,000 × 0.9333 / (55 × 70.711)       = 14.399
db^1.5            = 0.625^1.5                              = 0.49411
```

**Until 2026-09-21 neither row authored a hook, and the bottom row met a footing.** A straight
#5 needs ℓd = 60,000 × 0.625 / (25 × 70.711) = 21.21" against a 12" wall, and hooking the
3 #5 as laid out gave ψr 1.6 (centres 3.3125" < 6db 3.75", no ties) → ℓdh 11.38" against 9.00",
d/c 1.26. The bottom row (centre −117.50") sits inside `FT-SG-W1`/`-E1` (z −121.4375…−109.4375,
cast in placement 1), below the walls' −109.4375" start. Both are now detailed:

**Top row — hooked into the wall, with ties enclosing the hooks (ACI 318-19 Table 25.4.3.2).**
ψr is 1.0 for a #11-or-smaller hooked bar with **Ath ≥ 0.4 Ahs** *or* s ≥ 6db. The spacing
leg fails (3.3125 < 3.75), so the credit has to come from Ath: two closed #4 ties per end,
perpendicular to ℓdh, enclosing the three hooked bars. §25.4.3.3(b) counts them only if there
are two or more, evenly distributed along ℓdh at ≤ 8db centres.

```
Ahs         3 #5 hooked at the critical section   3 × 0.31            = 0.93 in²
0.4 Ahs                                                               = 0.372 in²
Ath         2 ties × 2 legs × 0.20                                    = 0.80 in²  ≥ 0.372 ✓
            (one leg per tie, the stingiest reading: 2 × 0.20 = 0.40 ≥ 0.372 ✓ — why #4, not #3)
§25.4.3.3   count 2 ≥ 2 ✓;  spacing 5.00" ≤ 8db 5.00" ✓;  spread (2−1) × 5.00 = 5.00" ≤ ℓdh 7.11" ✓
ψr 1.0,  ψo 1.0 (side cover 12.375 − 6.185 = 6.19" ≥ 6db 3.75")
ℓdh         14.399 × 1.0 × 1.0 × 0.49411                              = 7.11 in
available   W-SG-W1 12.0" − 3.0" far-face cover                       = 9.00 in   d/c 0.790 ✓
            (W-SG-E1 is the mirror: same 7.11 / 9.00)
```

**Since §6f this hook is also the NEGATIVE-MOMENT anchorage.** It was authored for torsion —
a corner bar developing fy at the support face, no §25.4.10.1 excess-steel reduction — and
the fixity credit gives the same row 5,621 ft-lb of end moment to deliver. The requirement
does not change (fy at the face was already the demand; a flexural anchorage asking less is
covered by it), but the reason it may not be relaxed now has two halves instead of one.

The hooks turn **up** into the wall: the top row is at −105.125" and a #5 90° hook needs
3.75/2 + 0.625 + 7.5 = 10.0" of leg, so turned down it would end at −115.1", 5.7" into the
footing below the wall's −109.4375" start — concrete of placement 1, which a placement-2 tail
cannot enter. ACI 318-19 §25.3.1 and R25.4.3 put a hook's tail in the concrete that develops
it, and here that is the wall rising above the joint. Authored `hook_turn="up"` (2026-09-21),
the layout turns both ends up to −95.125", inside `W-SG-W1`/`-E1`; the row reaches the walls'
far face less 3" cover (x 93"/339", u −3"/243"), the station the 9.00" above is measured to,
and the two ties per end sit along ℓdh at u −3"/2" (and 238"/243").

**Bottom row — the footing is the anchorage solid, through dowels cast in it.** The beam's
own bottom bars cannot enter a footing poured a placement earlier, so 3 #5 dowels per end are
cast horizontally in `FT-SG-W1`/`-E1` in placement 1, projecting through the footing's
court-side face (the cold joint) and lapping the bottom row there. In the beam's frame
(origin its west end): support faces u 6" / 234"; `FT-SG-W1` u −42…42, `FT-SG-E1` u 198…282;
3" cover and f'c 5,000 on both (`COURT_FOOTING_12`, their own schedule).

```
ℓd          STRAIGHT, §25.4.2.4: 60,000 × 0.625 / (25 × 70.711)      = 21.21 in
            ψt 1.0: 3.94" of concrete below the bar (−117.50 − −121.4375) < 12"
            ψe 1.0 galvanized (§25.4.2.5)
embedment   authored 66", measured from the joint (u 42 / u 198) back into the footing
past face   66 − (42 − 6)                                             = 30.00 in
geometric   6 − (−42) − 3 cover                                       = 45.00 in
available   min(30.00, 45.00)                                         = 30.00 in  d/c 0.707 ✓
            (east: 66 − (234 − 198) = 30.00; 282 − 3 − 234 = 45.00 — the mirror)
dowel steel 3 #5 = 0.93 in² against the row's 3 #5 = 0.93 in²                   d/c 1.000 ✓
lap         class B, §25.5.2.1: 1.3 × 21.21                           = 27.58 in
projection  authored `BarSpec.projection` on the dowels                = 30.00 in  d/c 0.919 ✓
```

**The lap is a graded row since 2026-09-22.** The dowel is 66" + 30" = a clean 8'-0" stock
length, which is where the 30" comes from; it clears the class B lap by 2.42". Until the
projection was authored the note printed the 27.58" and compared it with nothing. The ties'
**135° hooks** are authored the same way (`BarSpec.tie_hook_degrees=135`) and graded against
ACI 318-19 §25.7.1.3/§25.7.1.6 — a closed hoop resisting torsion may not be closed with 90°
bends, and "135°" had been prose in a `note=` string that no rule could read.

The bottom row itself **stops at the two joints**, u 42"…198" (156"), where the dowels take
over; until 2026-09-21 the layout ran it on to the beam's own cover at u 2"/238", 40" into each
footing, which placement 2 cannot reach — 20.0 LF of #5 billed and unbuildable
(`rebar_backout.md` §1).

A hook buys nothing here: straight at 45" of room it develops with 50% to spare, and a hook
turned in a 12" footing with the bar 3.94" off its underside has nowhere to go.

### 6f. ℓ/600, and the end fixity that closes it — SERVICEABILITY ONLY (2026-09-22)

**The limit.** TMS 402-22 **§13.1.2.3** holds *any* horizontally spanning member supporting
veneer — not only a masonry beam — to ℓ/600 under allowable-stress D + L. It is the
governing deflection limit on this beam and it is graded. ACI 318-19 Table 24.2.2's ℓ/480 is
graded beside it as the looser of the pair, not instead of it. (The 2016 edition's
§5.2.1.4.2 sat inside a masonry-beam clause, which is why §6d printed it as an unresolved
judgement; the 2022 renumbering settles the scope and the judgement goes away.)

**The model.** Equal rotational springs at the two monolithic joints, symmetric UDL, one
scalar **α** — the fraction of the fully fixed end moment the joint actually delivers:

```
M_end  = α wL²/12          α = 1 is fully fixed, α = 0 is the simple span of §6d
M_mid  = wL²/8 − M_end
Δ      = wL⁴(5 − 4α)/(384 E Ie)
Ie,avg = 0.70 Ie,mid + 0.30 Ie,end          ACI 318-19 §24.2.3.6, both ends continuous
```

`Ie,mid` and `Ie,end` are each Table 24.2.3.5's ⅔Mcr expression at that section's own `Ma`,
with Ec, Ig, Mcr, kd and Icr exactly as §6d works them. **At α = 0 the average is not taken**
— §24.2.3.6 is written for a member continuous at both ends and a simple span is neither, so
α = 0 reads Ie,mid alone and reproduces §6d's 0.4844" to the last digit. That is a
discontinuity in the model and it is the code's own; it is asserted in
`tests/test_veneer_beam_calc.py` so the credit can never quietly restate the old row.

**The elastic estimate, on the stingiest reading available.** Only the wall standing *above*
the joint is counted (the wall below is `FT-SG-W1`/`-E1`'s placement and is left out), its
far end is taken as pinned, the effective width is the beam's own 12" rather than the 36"
`b + 2t` the moment is actually spread over, and the section is gross:

```
I_w    = 12 × 12³/12                                     = 1,728 in⁴
h      = beam top −102.4375" to wall top 0'-0"           = 102.4375 in
k_θ    = 3 E I_w / h = 3 × 4,030,509 × 1,728 / 102.4375  = 2.040e8 lb-in/rad
α      = 1 / (1 + 2 E I_beam / (k_θ L))                  (equal springs, both ends)
       = 1 / (1 + 2 × 4,030,509 × 5,592.36 / (2.040e8 × 234))
α_elastic                                                = 0.514
```

**CLAIMED α = 0.25** — a 2:1 derate on that estimate, and the number the record is authored
with (`EndRestraint(fixity=0.25, elastic_fixity=0.514, effective_width=36")` on
`W-SG-BRKBM`).

| α | Ie,mid | Ie,end | Ie,avg | Δ after attachment | ℓ/600 (0.390") | ℓ/480 (0.4875") |
|---|---:|---:|---:|---:|---:|---:|
| 0.00 (§6d, simple span) | 2,052.5 | — | 2,052.5 | 0.4844 | **1.242** | 0.994 |
| 0.10 | 2,378.2 | 5,592.4 | 3,342.5 | 0.2623 | 0.672 | 0.538 |
| **0.25 CLAIMED** | **3,463.1** | **5,592.4** | **4,101.9** | **0.1811** | **0.464** | 0.371 |
| 0.344 | 5,591.9 | 5,592.4 | 5,592.0 | 0.1142 | 0.293 | 0.234 |
| 0.514 (elastic) | 5,592.4 | 5,592.4 | 5,592.4 | 0.0927 | 0.238 | 0.190 |

**The claim has 2.7× the fixity it needs**: ℓ/600 is met at α ≈ 0.092, and 0.25 is claimed.
It also sits **below α = 0.344**, which is where M_mid falls to ⅔Mcr and the beam would read
uncracked at service — so no part of this credit rests on the beam staying uncracked, which
is the assumption a restraint crack would take away.

**The credit is serviceability only, and that is the whole safety of it.** Midspan flexure is
still graded at **α = 0** (Mu 33,726 against φMn 60,747, **d/c 0.555**, unchanged from §6b).
A joint softer than claimed therefore costs deflection and nothing else — it can never buy
strength, and the record cannot be made to pass by assuming a stiffer wall. Everything the
fixity *adds* is graded separately below, at the claimed α and again at the full elastic α.

**Shrinkage restraint is ACI's own allowance, not a new question.** Casting the beam between
two walls restrains its shrinkage, and Eq. 24.2.3.5a's ⅔Mcr — rather than the full Mcr the
older editions used — is exactly the code's allowance for restraint cracking in service. The
section is also distributed: ρ = 2.26 in² / (12 × 17.75) = **1.06%** of longitudinal steel,
so a restrained crack is shared out rather than opened at one plane.

#### The rows the fixity adds

**Negative flexure at the supports.** Mirror 3 #5 top is already in the section (§3), so the
capacity is φMn 60,747 ft-lb, the same as midspan:

```
M_end,u  = α wu L²/12 = 0.25 × 709.56 × 19.5²/12        =  5,621 ft-lb   d/c 0.093
```

**The end moment into `W-SG-W1` / `W-SG-E1`, graded PLAIN.** The wall carries no steel that
crosses this joint in the right direction (`_BRACED_STEM_STEEL` is `#6 @ 38"` VERTICAL), so
the honest reading is structural plain concrete. **ACI 318-19 Table 14.5.2.1 in US customary
units is `Mn = 5λ√f'c · Sm`** with f'c in psi and Sm = b h²/6 — confirmed 2026-09-22 against
published summaries of the table (the 0.42λ√f'c form quoted elsewhere is the SI expression,
f'c in MPa; the 5λ√f'c modulus of rupture and φ = 0.60 for plain concrete flexure are the
inch-pound pair). Had the text read otherwise the wall would have had to go reinforced over
b_eff and this row would be a bar schedule instead; it does not, so it is a plain section.
The moment spreads over an effective width `b_eff = b + 2t = 12 + 2(12)` = **36"**:

```
Sm    = 36 × 12²/6                                       =    864 in³
φMn   = 0.60 × 5 × √5,000 × 864 / 12                     = 15,273 ft-lb
demand 5,621 (α 0.25)                                                   d/c 0.368  ×2 ends
```

**The wall receives even the full elastic end moment**: at α = 0.514 the demand is 11,557
ft-lb, d/c **0.757**, still a pass on the plain section. **`#6 @ 38"` does not change**, and
that invariance is the check on the derate — the claim is conservative in deflection and the
wall is not asked to be stiffer than the claim while being graded for the moment a stiffer
wall would send it.

**End-moment shear.** The end moment arrives at the joint as a couple in the top and bottom
rows, `T = C = M_end/d`, and the wall carries that force across b_eff as one-way shear
(d_wall = 12" − 3" cover − #6/2 = 8.625"):

```
V      = 5,621 × 12 / 15.0625                            =  4,478 lb
φVc    = 0.75 × 2 √5,000 × 36 × 8.625                    = 32,933 lb    d/c 0.136  ×2 ends
```

#### Prose, not rows

* **The inflection point is at u = 10.19"** from each support face at α = 0.25
  (`x = [L − √(L² − 8 M_end/w)]/2` on the factored diagram). ACI 318-19 §9.7.3.8.4 asks a
  negative-moment bar to run d, 12 db or ℓn/16 past it — 15.06", 7.50" or 14.63" — all of
  which the 3 #5 top clears with room, because the row runs the beam's **full length** (§6e)
  rather than being cut off. Nothing to grade, and nothing to change.
* **Torsion into the wall is in-plane and negligible.** The §6c twist arrives at the joint
  about the beam's own axis, which is the wall's *strong* plan direction: it is resisted over
  the wall's ~125" of run as in-plane bending, at a stress two orders below anything that
  governs. Not a row.
* **If the beam ever stops being cast monolithic with `W-SG-W1`/`W-SG-E1`, `end_restraint`
  comes off with it** and this record goes straight back to 1.242 OVER. That is a test
  (`test_the_fixity_credit_is_never_assumed`), not a comment.

### 6g. What left this record, and where it went

* **The masonry anchors** are `veneer_anchor/W-B-BRICK`, their own deferral with their own
  permit line (`structural.veneer_anchor`) — folding them in would be a record whose §9 denies
  its own scope. §5.1 is the reasoning; the deliverable is a TMS 402 anchor design for the
  ~10" reach and the supplier's confirmation of the insulation thickness.
* **The soft joints are AUTHORED and GRADED since 2026-09-22 (owner, A6)** — not engineering,
  a published guide read. The wythe runs x 106"…329.625" (N-B-BRICK-E moved 3/8" west the same
  day so the east end had room), and each end is a `MovementJoint` in `plan/masonry_joints.py`,
  billed by the foot in `[edge_trim]` and graded by `structural.masonry_movement_joint`
  (`tests/test_masonry_joint.py` reproduces the arithmetic below). The wythe loses 0.3 SF
  (112.5 → 112.2 SF).

  **The rule — BIA Technical Note 18A (May 2019), Eq. 1**, `S_e = w_j e_j / 0.09`: unrestrained
  clay brickwork moves `0.0009 x length` (TN 18's moisture + freezing + thermal), and a joint
  of width `w` whose least compressible part takes `e` percent absorbs `w e / 100`. In a series
  each joint takes half a panel from either side; a wythe jointed at BOTH ends gives each end
  half its run. The concrete returns shrink, which opens the joints — it adds no demand.

      run            329.625 − 106.000                       = 223.625"
      per joint      0.0009 x 223.625 / 2                    = 0.1006"
      EAST  3/8"     DOWSIL 790, ASTM C920 Class 100/50 → 50% in compression
                     0.375 x 0.50 = 0.1875"      d/c 0.1006 / 0.1875 = 0.537
                     seal 1/4" deep over 1/2" Nomaco HBR closed-cell rod (C1330 Type C);
                     TN 18A: depth ≈ w/2, never under 1/4", rod ~25% over the width
      WEST  4"       Sika Emseal Seismic Colorseal 4", ±50% of nominal
                     4.000 x 0.50 = 2.000"       d/c 0.1006 / 2.000   = 0.050
                     4 1/2" deep (its size table) — the back 7/8" stands in the cavity

  **Sensitivity, and the one number to watch.** If the wythe does not grow symmetrically —
  friction on the beam's flashing, an anchor that binds — one joint can take more than half.
  The east joint taking the WHOLE run reads 0.2013 / 0.1875 = **1.073**; so does a Class 25
  sealant in it at the half-run. The margin is in the west joint's 4", not the east's 3/8".
  Widening the east end to 1/2" (another 1/8" off N-B-BRICK-E) would take the whole-run case to
  0.81; recorded, not taken.

  **Why a precompressed seal at the west**: a 4" gun-grade bead is far outside the 3/8"–1/2"
  TN 18A calls typical, and Seismic Colorseal is published from 1/2" to 10" and names brick and
  masonry cavity walls. The check measures each joint's drawn width against the gap it stands
  in (1/16"), so moving either node stales it loudly.

### 6g′. The joints at the 17'-0" court (2026-09-22)

The wythe runs 118" .. 317.625" now, **199.625"** (it was 223.625"). TN 18A Eq. 1 at 0.0009 in/in
gives 0.0009 × 199.625 / 2 = **0.0898"** per joint: east d/c 0.0898 / 0.1875 (3/8" at 50%) =
**0.479**, west **0.045**. The whole run on the east joint alone is 0.1797 / 0.1875 = **0.958** — it
now passes by itself, so "the margin is in the west joint's 4\"" no longer holds; both joints
stay authored because TN 18A wants a soft joint at each end regardless.

### 6h. The record, row by row

| limit state | demand | capacity | d/c |
|---|---:|---:|---:|
| flexure, simple span (α = 0, no fixity credited) | 33,726 ft-lb | 60,747 | **0.555** |
| minimum flexural steel (detailing) | 0.639 in² | 0.93 | 0.687 |
| one-way shear | 6,918 lb | 19,171 | 0.361 |
| torsion transverse steel, equilibrium | 0.002058 in²/in | 0.0220 | 0.094 |
| torsion section limit | 54.03 psi | 530.3 | 0.102 |
| hoop spacing (detailing) | 5.00 in | 5.25 | 0.952 |
| minimum transverse steel (detailing) | 0.0106 in²/in | 0.044 | 0.241 |
| longitudinal steel, flexure + torsion (detailing) | 1.684 in² | 2.26 | 0.745 |
| longitudinal perimeter spacing (detailing) | 6.19 in | 12.0 | 0.516 |
| deflection after attachment, **TMS ℓ/600** (α 0.25) | 0.1811 in | 0.390 | 0.464 |
| deflection after attachment, ACI ℓ/480 (α 0.25) | 0.1811 in | 0.4875 | 0.371 |
| negative flexure at the supports (α 0.25) | 5,621 ft-lb | 60,747 | 0.093 |
| end moment into W-SG-W1 / W-SG-E1, plain over b_eff 36" | 5,621 ft-lb | 15,273 | 0.368 |
| end-moment shear into W-SG-W1 / W-SG-E1 | 4,478 lb | 32,933 | 0.136 |
| hooked development of top-y into W-SG-W1 / W-SG-E1 (ψr 1.0 on Ath) | 7.11 in | 9.00 | 0.790 |
| dowel development of bottom-y into FT-SG-W1 / FT-SG-E1 | 21.21 in | 30.00 | 0.707 |
| dowel lap of bottom-y past each joint (detailing) | 27.58 in | 30.00 | 0.919 |
| dowel steel against the bottom row, each end (detailing) | 0.93 in² | 0.93 | 1.000 |
| tie hook angle (detailing) | 135 ° | 135 | 1.000 |

Status on catlin: **OK** — every row passes. The governing row is now **§6e's hooked
development of the top row, 0.790**; deflection has stopped governing, and the strength rows
rank flexure 0.555, ℓ/600 deflection 0.464, dowel development 0.707, one-way shear 0.361,
end moment into the wall 0.368. It was OK-governed-by-deflection-at-0.994 from 2026-09-21
(ACI ℓ/480, simple span) until §6f moved the limit to ℓ/600 and credited the fixity; before
2026-09-21 it was INCOMPLETE on the end restraint.

**What governs is now an ANCHORAGE length, and that is worth saying out loud.** The beam's
own section is comfortable everywhere (flexure 0.555, shear 0.361, torsion 0.102); the
binding number is 7.11" of hook in 9.00" of wall. Anything that thins `W-SG-W1`/`W-SG-E1`,
raises their cover, or loses the two #4 confining ties per end (which is worth ψr 1.6, ℓdh
11.38" against 9.00" — an immediate FAIL) moves the governing row before it moves anything
else here.

**Why the hook is a graded row and not detailing (owner, A4, 2026-09-22).** A development
LENGTH is a capacity, as on every development row in the engine (`deck_post.py` agrees); a bar
count, lap or hook angle is detailing. Reclassifying the hook would not hand the record to
flexure anyway — the dowel development row, 0.707, would govern.

### 6i. The court narrowed to 17'-0" (2026-09-22)

The side walls came 1'-0" in each (DESIGN-LOG.md, "Sunken garden court"), so the clear span is
**17.0'** and the design span `L = min(17.0 + 15.0625/12, 17.0 + 6/12)` = **17.5' = 210"**. The
wythe also got shorter: its top dropped to −13 1/3" so the porch's 2x12s clear it, 89.104" tall
where it was 94.4375".

```
wythe  119.86 × (3.625/12) × (89.104/12)                =  268.86 plf
w      268.86 + 221.875                                 =  490.735 plf     wu = 687.03 plf
Mu     687.03 × 17.5² / 8                               = 26,300 ft-lb    d/c 0.433
M_end,u  0.25 × 687.03 × 17.5² / 12                     =  4,383 ft-lb   (−) d/c 0.072
                                                         wall, plain, 36": d/c 0.287
```

**Deflection at the claimed α = 0.25.** Service Ma,mid = 490.735 × 17.5²/8 − 0.25 × 490.735 ×
17.5²/12 = 18,786 − 3,131 = 15,655 ft-lb, under ⅔Mcr (18,565), so Ie = Ig at both sections:

```
Δ all dead   40.895 × 210⁴ × (5 − 1) / (384 × 4,030,509 × 5,592.36)   = 0.03676 in
Δ beam only  18.490 × 210⁴ × 4 / (same)                               = 0.01662 in
after attachment  1.5908 × 0.03676 + (0.03676 − 0.01662)              = 0.0786 in
ℓ/600 = 210/600 = 0.350 in                                                d/c 0.225
```

**⚠ THE FIXITY IS NO LONGER NEEDED, AND IT IS REPORTED RATHER THAN REMOVED.** At α = 0 the
simple span's Ma = 18,786 ft-lb just clears ⅔Mcr, Ie,mid = 5,087 in⁴, Δ all dead 0.0505",
beam only 0.0208", after attachment **0.110" against 0.350" — d/c 0.315**. The shorter span
closes ℓ/600 on its own. The elastic estimate at the new span is α = 1/(1 + 2 × 4,030,509 ×
5,592.36/(2.040e8 × 210)) = **0.487**. `end_restraint` stays authored because the beam is still
cast monolithic with the walls (placement 2) and its added rows all pass; whether to keep
claiming it is the engineer's call, and nothing now depends on it.

### 6j. The beam bears on the court footings' toes (2026-10-10) — ⛔ superseded by §6k

> **Supersedes §3's span, §4a's steel, §6c–§6f and §6i as the graded basis.** They are kept
> as written: each was right about the member the engine was then asked to grade.

**The geometry nobody had read.** `W-SG-BRKBM` runs z −120 3/16"..−102 7/16"; `FT-SG-W1`/`E1`
run z −121 7/16"..−109 7/16" and x 5'-6"..12'-6" / 23'-6"..30'-6", across the beam's whole
y band (−10"..−22"; their north edge is −6.68"). So the beam's lower 10 3/4" sits **inside**
each toe for 3'-6" from the wall axis, and its upper 7" sits **on** it. A pour cast on a
footing bears on that footing: the clear span is between the toe faces, not the walls.

| term | working | value |
|---|---|---|
| clear span | 23.500 − 12.500 | **11.00'** |
| bearing | 12.5 − 9.0 (axis to toe face) | 42" |
| cover | 3" — the soffit between the toes is cast on the bed (ACI Table 20.5.1.3.1); was 2" until 2026-10-11 | 3" |
| d | 17.75 − 3.0 − 0.375 − 0.625/2 | 14.0625" |
| design span | min(11.00 + 14.0625/12, 11.00 + 42/12) = min(12.172, 14.5) | **12.172'** |

**Strength at U = 1.4D**, w = 268.86 + 221.875 = 490.735 plf, wu = 687.03 plf:

```
Mu      687.03 × 12.172² / 8                             = 12,723 ft-lb
Vu      687.03 × 12.172 / 2                              =  4,181 lb
As,req  12,723 × 12 / (0.9 × 60,000 × 0.9 × 14.0625)      =  0.2234 in²
§9.6.1.3  4/3 × 0.2234 = 0.2979 < §9.6.1.2's 0.597 — the 4/3 rule governs the minimum
2 #5    a = 0.62 × 60,000 / (0.85 × 5,000 × 12)           =  0.7294 in
        φMn = 0.9 × 0.62 × 60,000 × (14.0625 − 0.3647)/12  = 38,217 ft-lb    d/c 0.333
        0.62 ≥ 0.2979                                                       d/c 0.480
        (and 0.62 ≥ §9.6.1.2's 0.597 outright: at 3" the waiver is not leaned on)
φVc     0.75 × 2 × 70.711 × 12 × 14.0625                   = 17,899 lb      d/c 0.234
```

**Torsion falls below the threshold.**

```
t       268.86 × 4.1275 / 12                               =  92.48 ft-lb/ft
Tu      1.4 × 92.48 × 12.172 / 2                           =  787.9 ft-lb
φT_th   0.75 × 0.25 × 70.711 × 762.5 / 12                  =  842.5 ft-lb    d/c 0.935
```

ACI 318-19 §22.7.4.1: below φT_th torsion **may be neglected**. §4's closed hoops at ph/8,
§4a's side bars and Al, and §6e's requirement that every corner bar develop fy at the face
all fall away. The margin is 6.5%, but the threshold is itself ¼ of the cracking torque, so
factored Tu is ~23% of Tcr; at the face less d (§22.7.3.2's critical section, not taken) it
would be ~0.75 of the threshold. Cover does not enter it (Acp and pcp are gross). The eccentricity is still 4.13": nothing here moved the brick.

**No shear steel is owed.** §9.6.3.1 asks Av,min only where Vu > φλ√f'c bw d =
0.75 × 70.711 × 12 × 14.0625 = **8,949 lb**; Vu is 4,181 (d/c 0.467). The #3 ties @ 12" are
cage ties.

**Deflection, with no end fixity.** Service Ma = 490.735 × 12.172²/8 = 9,088 ft-lb, under
⅔Mcr = 18,565, so Ie = Ig = 5,592.36 in⁴; span 146.06".

```
Δ all dead   40.895 × 146.06⁴ × 5 / (384 × 4,030,509 × 5,592.36) = 0.01075 in
Δ beam only  × 221.875 / 490.735                                 = 0.00486 in
λΔ           2 / (1 + 50 × 0.40 / (12 × 14.0625))                = 1.7881   (2 #4 top)
after attachment  1.7881 × 0.01075 + (0.01075 − 0.00486)          = 0.0251 in
ℓ/600 = 146.06 / 600 = 0.243 in                                      d/c 0.103
ℓ/480 = 0.304 in                                                     d/c 0.083
```

`end_restraint` is **removed**: it was a serviceability credit and nothing needs it.

**The bottom row into its support (§9.7.3.8.1).** At a simple support ⅓ of the positive
steel continues 6" in. The row sits inside the toe zone, so it stops at the toe face and
2 #5 dowels per end, cast straight in FT-SG-W1/E1 in placement 1, carry it: 0.62 in² against
⅓ × 0.62 = 0.207 (d/c 0.333), 12" of embedment against 6" (0.500), and a 30" projection
against the 27.58" class B lap (ℓd 21.21 × 1.3; 0.919). A 3'-6" bar.

**The steel, then and now.**

| | was (§4a, §6e) | now |
|---|---|---|
| bottom | 3 #5 | 2 #5 |
| top | 3 #5, hooked into the walls, 2 #4 confining ties each end | 2 #4 straight hangers |
| hoops / ties | #3 closed @ 5", 135° | #3 @ 12" (cage) |
| side bars | 1 #4 each face | — |
| dowels | 3 #5 per end, 66" + 30" | 2 #5 per end, 12" + 30" |
| cover | 2" | 3" (2026-10-11) |
| laid weight | 251.2 lb | **87.1 lb** (91.9 at 2" cover) |

**The brick's placement tolerance is graded (2026-10-11).** The threshold margin above is
6.5%, and the brick line could eat it. φT_th is reached at

```
e_max = 842.46 / (1.4 × 268.86/12 × 12.172/2) = 4.413"   — 0.286" past the modelled 4.128"
```

So the drawing states ±1/4" on W-B-BRICK's bearing line (`AN-SG-PLACEMENTS`), and the record
grades at it (`FoundationWall.bearing_tolerance`):

```
Tu = 1.4 × 268.86 × (4.1275 + 0.25)/12 × 12.172/2 = 835.7 ft-lb       d/c 0.992
```

The tolerance IS the margin now. A looser tolerance, a heavier wythe or a longer span each
put the torsion cage back. That trade was made knowingly; restoring the cage costs about
100 lb.

**As laid (2026-10-11).** The cage now matches its two placements:

- The 12 #3 ties stop at the toe faces (19 were laid, 8 of them inside the toes, which are
  poured a placement earlier).
- Each dowel sits one #5 diameter inboard of its bottom bar: a contact lap, not a shared
  centreline.
- The dowel is laid at its authored 12" + 30", not cut back to the 27.58" minimum.

The ties stay closed. An open U saves about 4 lb and would be a new stirrup shape in the
engine for no structural gain. 78.5 lb laid.

**What would undo this.** Taking the toes away (narrowing FT-SG-W1/E1, or a beam bottom raised
above the footing top that leaves it bearing on a 7" lip) puts the span back to 17'-0" and Tu
back to 1.35 φT_th; `test_without_the_toe_bearing_the_light_cage_would_not_do` shows the
record failing at once. So does moving the brick further off the beam's centre.

### 6k. Bedded on stone, flush on the house strips (2026-11-04, owner) — the basis now

**The member.** `W-SG-BRKBM` was always cast on the court's bed; grading it as an 11'-0" span
(§6j) was an assumption. It now states its bed — `FB-SG-BRKBM`, drained NFS stone on the
court's wall-bed plane (−163 7/16"), 12" wide, 43 1/4" under the beam, pipeless, letting go
through FB-SG-W1's stone into FB-SG-W2's course — and `engineering/veneer_beam` skips a wall a
bedding hosts. `veneer_beam/W-SG-BRKBM` retires; the kind stays for a true spanning beam. The
§6j cage is kept as nominal. **Nothing grades its bearing**: the wythe's 268.86 plf (§6j) plus
12" × 17 3/4" at 150 pcf = 221.9 plf is 490.8 plf on 12", ≈ 0.49 ksf — the same gap
`W-SG-ARCH` has.

**The geometry (y, inches; north toward the house).**

| element | before | now |
|---|---|---|
| FT-B-S1..S4 south face | −4 | −4 |
| beam board (2" XPS) | −8..−10, 4" stone behind | **−4..−6**, flush on the strips |
| beam concrete | −10..−22 | **−6..−18** (same 12" × 17 3/4", same z) |
| FT-SG-W1/E1 north end | −6.685 | **−6** (0.685" extension) |
| TB-SG-W1/E1 (footing level) | 2.5", −4.185..−6.685 | **2", −4..−6** — one plane with the beam's |
| backup foam | 4" XPS + 2" EPS, face −6.06 | **4" XPS**, face −4.06 |
| W-B-BRICK back / front | −10.06 / −13.685 | **−6.000 / −9.625** |
| N-B-BRICK-W / -E (x) | 9'-10" / 26'-5 5/8" | **9'-6 1/2" / 26'-5 1/2"** |

**The cavity, by hand.** Sheathing (or curb concrete) outer face y = 0; stud face +1/2"
(1/2" plywood). Membrane 0.06 + 2 × 2" XPS: foam face −4.06.

    airspace           6.000 − 4.060                 = 1.940"   ≥ 1" nominal          ✓
    brick to studs     6.000 + 0.500                 = 6.500"   W-B-S2-FR / W-B-S3-FR
    brick to concrete  6.000 + 0                     = 6.000"   W-B-S1 / W-B-S4 ends
    2024 W2.8 row      6.625 − 6.500                 = 0.125" of margin
    2018 W1.7 row      4.500 < 6.500                 → past the adopted table

No sheathing change moves the margin: brick-to-stud is set by the strip face, the 2" board and
the stud line. **Field note for the section: 6 1/2" max, back of brick to face of stud** — the
mason lines the brick off the studs, not off the beam's edge, so the pour's tolerance cannot
spend it. Fallback, not planned: the strips 5/8" north (deepened to keep P ≤ T).

**Table R703.8.4(1), by edition (checked 2026-11-03).** Maximum is to the BACKING; minimum
airspace 1" nominal from the sheathing or foam in every edition.

| edition | W1.7 adjustable wire | W2.8 adjustable wire |
|---|---|---|
| 2018 IRC (MN 2020, adopted) | 4 1/2" | no row |
| 2021 / 2024 IRC (= TMS 402-16) | 4 5/8" | **6 5/8"** |

**The anchors.** Basis (owner, 2026-11-03): the 2024 IRC W2.8 row, claimed under R104.11 as an
alternate to MN 2020 — one AHJ request, no seal. W2.8 adjustable wire (3/16"), screwed to the
studs through 4" XPS and 1/2" plywood, ~40 ea. R703.8.4.1: one tie per 2.67 sf, ≤ 32" o.c.
horizontally and 24" vertically; 2 sf only over 30 psf. ASD Zone 5 wall suction at h = 25.5',
V 115, Exp B: q_h = 0.00256 × 0.669 × 0.85 × 115² = 19.25 psf; × (1.4 + 0.18) = 30.42 psf;
× 0.6 = **18.25 psf** < 30 → 2.67 sf. `structural.veneer_cavity_width` grades all of this;
under the 2018 base it reports `veneer_anchor/W-B-BRICK`, which keys off the same measurement
and retires with no house edit when the profile adopts the 2021 or 2024 IRC.

**The joints (both 1/2", Class 50).** Run 317.5 − 114.5 = **203.0"**. TN 18A Eq. 1:
0.0009 × 203.0 / 2 = **0.09135"** per joint against 0.5 × 0.50 = 0.25" → **d/c 0.365** each.
One joint taking the whole run: 0.1827 / 0.25 = **0.731**. A general-purpose Class 25 silicone
doubles both (0.731 / **1.462, FAIL**), which is why the spec names ASTM C920 Type S Grade NS
Class 50 neutral cure (DOWSIL 790/795, GE SCS2000, Pecora 890NST as equals); acetoxy cure is
not for alkaline masonry. Tooled 1/4" deep over 5/8" closed-cell rod (C1330 Type C).

**What did not move.** The beam's section, z and steel; `W-SG-ARCH`; the free body's
`thermal_break_transfer` inputs (board height and length) — only the board's plane, and the
footing-level boards' thickness (2.5" → 2"), which `notes/sunken_garden_court_free_body.md`
§11o records. The sunken-garden door's tread over the cavity is
`notes/french_door_catalog_installation.md` §6.

### 6l. Ties on the 2024 row, steel lintels, the bed graded (2026-11-23, decisions 10, 11, 29; review F-01..F-04)

**Table R703.8.4(1), read on UpCodes for every edition** (MN 2018, Colorado 2021, Oklahoma 2024,
2026-11-23; the 2024 text is the model code's as the Oklahoma mirror prints it). Wood-stud rows only,
in every edition: no row has concrete or masonry backing, so **no tie goes into concrete** (F-02).

| edition | rows (maximum back of brick to the backing) | footnotes on the W2.8 row |
|---|---|---|
| 2018 (MN 2020, adopted) | corrugated (nominal 1" air); adjustable W1.7, 4 1/2" | none; no W2.8 row |
| 2021 | W1.7 4 5/8"; **W2.8 "greater than 4 5/8" ... maximum 6 5/8""** | pintle: at least 2 legs, offset at most 1 1/4"; brick face to pintle end at most 2"; backing eye W2.8, barrel at least 1/4" OD or plate at least 0.074" x 1 1/4" |
| 2024 | the same two rows | the same; 2024 adds R703.8.3.1's 3x3x3/16 angle alternatives (§6l lintels) |

R703.8.4.1 (all three): 2.67 sf a tie, 32" o.c. horizontally and 24" vertically (2 sf over 30 psf).
R703.8.4.1.1 (2021 and 2024): openings over 16" in either dimension take extra ties within 12", at most
3 ft o.c.

**The detail names the edition** (it prints on the finding and the wall section): *2024 IRC Table
R703.8.4(1), W2.8 (3/16") adjustable wire tie, 2 pintle legs, offset at most 1 1/4", brick face to pintle
end at most 2", backing eye or barrel per the table; fastener not smaller than an 8d common nail, long
enough to seat in the stud through the 4" foam and 1/2" sheathing.* 6.500" against 6.625": 0.125".

**Dependency, not a design left undone.** Minnesota's code is the 2018 IRC (MN Rules 1309.0010); the 2024
row is not in the book the building official holds today. The owner files the permit application on or
after the date Minnesota's 2024-based residential code takes effect (the engine's profile then carries the
row and `veneer_anchor/W-B-BRICK` retires with no house edit); failing that, the written R104.11 request is
made before the application. Decision 31: the adoption date is the one open item of this lane.

**Where the ties go, derived** (`veneer_tie_layout.py`). Studs of the framed backing, projected on the
wythe (inches from its east end, x = 317.5" minus that): 4.25, 13.5 (`W-B-S3-FR`'s end studs), 27.6,
24.6 (the east pack's kings), 93.9, 96.9 (the west pack), then 109.5, 125.5, 141.5, 157.5, 173.5, 189.5,
198.75 (`W-B-S2-FR` at 16"): **13 stations** over the 203.0" wythe. A tie carries 2.67 x 144 / 24 =
**16.02"** of width on 24" rows; the widest tributary is **16.00"** (a full 16" stud bay), so every
station is within it. **The concrete ends** are 3.5" each (`W-B-S1`, `W-B-S4`, x 114.5"-118.0" and
314.0"-317.5"): tied from the first stud 4.25" in, so none goes into the pour, and the end strip is
4.25" + half a 9.25" bay = 8.9" of one tie. Openings over 16": `AO-B-BRICK-WIN` (14" x 20", tall enough)
has a stud tie 1.0" from each jamb, `AO-B-BRICK-DOOR` 2.25" from its west jamb and 0.75" from its east (the packs' nearest studs). The head over the door lands on
the head cripples (`W-B-S3-FR`, 16" o.c.).

**Wind (re-pinned after L7):** mean roof height 34.76 ft from adjacent ground, q_h 21.03 psf; ASD Zone 5
wall suction at the tie's 2.67 sf, x (1.4 + 0.18) x 0.6 = **19.93 psf** (it was 18.25), under 30: still
2.67 sf a tie, the 16.02" bay.

**What the ties must take (decision 29).** The boards and the ties go in after the three retained sides
are backfilled (`IsolationBoard.set_after_backfill`), so the ties take only the closure the thermal-break
record bounds: thermal 0.0533" + sliding 0.0321" = **0.0854"** against the board's 0.125" (read from
`thermal_break_transfer/W-SG-ARCH`'s "court-to-house joint closure", not copied). An adjustable tie is
rigid along its own axis, which is the wall's normal: its pintle and eye are held to **at most 1/16"
(0.0625") of movement between the two parts** (TMS 402-16 as summarized in Heckmann's 2018 catalog p.70),
and its published travel is VERTICAL (Heckmann Pos-I-Tie: 1 1/4" above and below the barrel; H&B's
joint-reinforcement ties disengage at 1 1/4"). No maker publishes travel normal to the wall. 0.0854 / 0.0625
= 1.37, so the finding is UNKNOWN and **gate G8** is reported to the coordinator with the options
(a tie with published wall-normal travel; a different joint width or board; the brick's own tilt about its
ties, 0.0854 x (1 - z / 89.1") against 0.0625" above the 24" row, not a code basis).

**Lintels (F-01, decision 11).** R703.8.3 (2018 and 2024 text the same): veneer over an opening is on a
noncombustible lintel, 4" of bearing; a steel one is shop-painted or galvanized or corrosion-resistant;
spans per Table R703.8.3.1. Both reveals are flat-headed now (the arches are gone: R703.8.3 has no arch
alternative) on **L3x3x1/4, long leg vertical, hot-dip galvanized (ASTM A123)**, 4" of bearing a side, a
22" angle over the 14" window and a 71 5/16" one over the 63 5/16" door; the table's 3x3x1/4 row is
**6'-0" with no story above**, and 63 5/16" = 5.276 ft. Nothing bears on the wythe (the porch joists'
soffit -11 1/4" is 2 1/12" over its top). The horizontal leg is 3" under a 3 5/8" brick: the brick overhangs
it 5/8". **Options for G7, and why none was needed:**

| option | a table read? | long-lived? | verdict |
|---|---|---|---|
| **HDG carbon angle** | **yes: the row IS the angle** | A123 Table 1: structural shapes 1/4" to under 5/8" take **grade 100 = 3.9 mils (100 microns)**; AGA: a 3.9-5.0 mil coating on structural steel is **70 to 90+ years to first maintenance in an industrial atmosphere** (time to first maintenance is not service life) | **chosen** |
| stainless angle | no: Table R703.8.3.1 lists carbon-steel angles; stainless is "other steel members meeting structural design" (note 3), a design not a read | longest | not a read |
| precast concrete | no: the table's reinforced lintel is a masonry lintel with bars; a precast lintel is the maker's own load table | longest | not the table |

The cavity is wetter than the AGA atmospheric chart (wet alkaline mortar over the angle): the flashing over
every lintel (R703.8.5) and the weeps (R703.8.6) keep it drained, and the chart's age (AGA says it
understates today's lives) and that caveat are stated. Cost: 7.8 ft of angle in all (22" + 71 5/16"), billed by the foot
in `[steel_members]` with a galvanizing lot, against an arch's masonry labour. `structural.veneer_lintel` grades the read.

**The bed (F-04), at each real interface** (`structural.veneer_bed_bearing`, `scratch/L3/hand.py`). Wythe
268.86 plf (7.424 ft x 3.625" x 120 pcf) at y -7.8125"; beam 12" x 17.75" x 150 pcf = 221.9 plf at -12";
total **490.7 plf**; resultant 2.29" north of the beam's centre; kern of the 12" contact 2.00":
**outside the kern**, so contact is partial. a = 6 - 2.29 = 3.71"; contact 3a = 11.1"; peak 2P / 3a =
**1,059 psf** against the site's presumptive 2,000 psf (R401.4.1, GM): **0.53**. The soil under the 43 1/4"
stone sees 491 psf on the 12" with no spread credited: 0.25. **Widening the stone 4" south (review option
1) changes nothing**: the contact is the beam's own bottom, still 12", still 2.29" off its centre; the
bed's centroid moves 2" south, away from the load. A beam widened 4" south (16": 295.8 plf of its own)
lowers the peak to 894 psf (0.45) for 74 plf more concrete and a form change; not needed at 0.53. The
tilt a one-sided peak settles into is not graded (the beam is cast with the court walls' toes, which hold
it); the wythe's own bearing on the beam top (6.2 psi) is not graded.

### 6m. A bond break at the base, the ties on force, the perimeter and the bed's wind (2026-11-23, owner: "bond break at the base")

**The bond break (model fact).** The wythe stands on a brake-formed steel flashing sheet on the beam's
top (`FL-B-BRICK-BASE-W` x 114.5"-224.34", `-E` x 287.66"-317.5"; none under the door's reveal), dry,
the first course bedded on it, the inboard leg turned up the backup 2", the drip 3/8" past the face:
IRC R703.8.5's flashing beneath the first course and BIA TN 28D's bond break in one ("A bond break is
recommended between the exterior brick wythe and the foundation. This permits differential movement
among the materials", TN 28D). The same sheet is lapped over each lintel (`FL-B-BRICK-WIN-HEAD`,
`-DOOR-HEAD`). Weeps (R703.8.6, at least 3/16", at most 33" o.c., immediately over the flashing) are
open head joints, in `notes/veneer_opening_detail.md` and on the sheet; the model carries none.
`structural.veneer_cavity_width` reads the base runs and FAILs a wythe whose base they leave bare.
Drawn on `SL-D-VENEER-HEAD` (through the door's centre, x 21'-4") and `SL-D-VENEER-BASE`; the wall
section at x=10' cuts where neither reveal is, so it could not show the lintel flashing, and
`TR-CATLIN-VENEER-OPENING` (its old "arch, no lintel" reason gone) is un-suppressed.

**The ties on force.** The court slides under the wythe, so each tie carries friction drag in both
directions (summer closing 0.0854", winter opening about 0.089" on the court record's own thermal basis, the 50 F set to the 0 F minimum; §6m first read 70 F, a local range, and the load-path review M8 corrected it),
not stiffness x displacement (which would be 2,500 lb/in x 0.0854" = 214 lb a tie, over the 125 lb
allowable and the 210 lb design strength: the check FAILs a wythe with no bond break). The table is
TMS 402-22 Table 6 as BIA TN 3C (2022) prints it: adjustable two-leg pintle 2,500 lb/in, 125 lb
allowable, 210 lb design; adjustable slotted 3,000 lb/in, 200 / 330 lb. Wind by TN 3C's tributary method
(Table 7, k <= 2,500 lb/in: 2 p At): 2 x 19.93 x 2.67 = **106.4 lb** of 125. Drag: net wythe weight
268.86 plf / 7.425 ft x (203" x 89.1" - 14" x 20" - 63.3" x 80") / 144 = **3,204 lb** over
**65 ties** (13 stations x 5 rows) = **49.3 lb per tie per unit of friction**. Drag plus wind stays
under 125 lb for a friction up to **0.38**; drag alone for up to 2.54; the slotted 200 lb tie allows
1.90 with wind. **The friction of brick and mortar on the flashing is not sourced**: no maker publishes
it, and the study that tested it with common flashings (McGinley and Borchelt, "Friction at Supports of
Clay Brick Walls", TMS Journal 9(2), 1991, DOI 10.70803/001c.141510) is paywalled (abstract only);
a 2025 Canadian masonry symposium paper puts clay-brick friction at about 0.25 to over 1.0 with design
standards at about 0.25-0.45 (a search summary, unverified). So the row is **UNKNOWN naming that input**
(`veneer_ties.FRICTION_BRICK_ON_FLASHING`), with the bound printed. Over 0.38, the options are the
slotted tie (a Table 6 row, a tie-type swap) or 12" stud bays (2 sf a tie, 1.22).

**The perimeter (verifier defect).** R703.8.4.1.1 takes ties around the WHOLE perimeter, within 12" and
at most 3 ft o.c. The door's jambs are 64.8" apart; its head band over the lintel (the angle's top
at 83" over the base, up 12" and to the wythe's top) holds the three head cripples at 16" o.c. and the
packs: 7 stations, widest 17.6" o.c., on the head cripples' range 83"-87.6" over the base. The window's
head and sill bands hold its two jamb studs. Rows are bed joints (a 2 2/3" course module), at most 24"
apart: **16", 34 2/3" (the window sill band), 48", 61 1/3" (its head band) and 85 1/3" (the door head, on
the cripples)** over the base. `veneer_tie_layout` now stations cripples for the head and sill bands
and grades the rows.

**The bed under wind (verifier defect).** The strip between the flashing (a pin) and the first tie row
at 16" takes half of p x its height at the base: 19.93 x (16/12) / 2 = 13.3 plf, acting at the beam's top
17.75" over the bed: 236 lb-in per ft, which moves the resultant 0.48" (worst sign): e 2.29" -> **2.77"**,
contact 9.7" of 12", peak **1,217 psf, 0.61** of 2,000. At 130 pcf brick (the house's is 1920 kg/m3 =
120 pcf) it is 1,298 psf, 0.65 (dead alone 0.57); `scratch/L3/hand.py` section 4.

**Not closed here:** the TJ-8000 rim joint 8.34" from the door's west jamb (see
`sunken_door_band_header.md`).

### 6n. The slotted tie on a stated friction bound, stainless flashing isolated from the zinc (2026-11-23, owner)

**The tie.** TMS 402-22 Table 6 (BIA TN 3C, 2022): adjustable slotted **3,000 lb/in, 200 lb allowable,
330 lb design** (the two-leg pintle it replaces: 2,500 / 125 / 210). TN 3C Table 7 puts a tie of stiffness
2,500 < k <= 5,000 lb/in at **2.5 p At** (2 p At was the pintle's). The product is **Hohmann & Barnard
HB-213-2X**: a plate anchor (14 or 12 ga, its depth "equal to the thickness of insulation", here 4", for
rigid insulation up to 6") with 3/16" compressed-leg hooks (**W2.8, two legs**: 400H-2X, 4"; the pintle end
lies 1 1/2"-2" in the brick, confirmed at the first course), "tested and designed to withstand over
200-lbf, in tension or compression, at maximum allowed offset ... of 1 1/4"" (the data sheet). Its working
load at a 1 1/4" offset and .05" deflection, from the sheet's table (cavities of 4 1/2" and 7 1/2", the
6 1/2" between): **235 to 332 lb**, tension and compression, over the 200 lb the row allows. "Needs 3/4" to 1"
minimum air cavity" (ours 1.94"); "H&B recommends 16" x 16" spacing" (ours 16" x 24" at most). The plate's
slot as the table's "adjustable slotted" type is **my reading of the maker's sheet, which does not use that
word**: H&B to confirm. Fastener not smaller than an 8d common nail, long enough through the 4" foam and 1/2"
sheathing to seat in the stud. HDG (ASTM A153 B2) is the stock finish; stainless is on the sheet if wanted.

**The grade, on a bound.** Wind 2.5 x 19.93 x 2.67 = **133.1 lb**; drag at a friction of **1.0**, a stated
UPPER BOUND, unverified (no maker publishes it; McGinley and Borchelt, TMS J. 9(2), 1991, was not opened):
1.0 x 49.3 = **49.3 lb**; together **182.4 lb of 200: d/c 0.91** (design strength 330). PASS without a
sourced friction. It is over decision 30's 0.85 cost-review trigger, printed, not a limit (the product's own
working load is 235 lb or more). A sourced friction replaces the bound (`veneer_ties.FRICTION_BRICK_ON_FLASHING`).

**The flashing is Type 316 stainless** (`stainless-steel-flashing`, `plan/veneer_materials.py`; the court's salt:
the house's standoff shims and screws are 316 for the same reason). Stainless and galvanized stay out of one
joint, so **each head sheet stands on a 1/16" EPDM strip (`FL-B-BRICK-WIN-ISOL`, `-DOOR-ISOL`) laid on the HDG
angle's top, its ends 1/2" past the sheet**, and is fixed with 316 screws; the sheet never touches the zinc.
`structural.veneer_lintel` FAILs a stainless sheet lying on the galvanized angle with no EPDM strip between.
The base sheet lies on concrete, under mortar and a dry bed; the HDG tie plates and hooks are in the mortar
joints and the studs, not on the sheet.  No price is entered.

**The rim joint is closed** by running one rim board past the seam (`sunken_door_band_header.md`). **The tie's reading:** H&B's sheet does not call the HB-213 plate slotted; Table 6's adjustable slotted row is read onto it, and the maker's own test (over 200 lbf, tension and compression, at the 1 1/4" maximum offset) equals the row's 200 lb.

## Sources

- IRC 2018 R703.8.4 — anchored masonry veneer, airspace and tie spacing.
- IRC 2018 R403.3 and Figure R403.3(3), Table R403.3(1) at AFI 3000 — read for the retired wings;
  the strips are now on a deep drained bed (ASCE 32, R403.1.4.1) this beam must not compromise.
- IRC 2018 R404.1.2(8) — the table `W-SG-W1`/`E1` already satisfy.
- ACI 318-19 §9.6.1.2 (minimum flexural steel), §22.5 (one-way shear), §22.7.1
  (compatibility torsion).
- TMS 402/602-16 §6.2 — anchored veneer, and the engineered path a ~10" anchor reach requires.
- IRC 2021 R703.15 — cladding attachment over foam sheathing; **excepts anchored masonry
  veneer to R703.8**, which is why the 4" foam limit in `plans/cost-options.md` §6 is not
  this wall's limit. Table R703.8.4(1) by edition is §6k's (checked 2026-11-03).
- IRC 2018 / 2021 / 2024 Table R703.8.4(1) and R703.8.4.1 — tie types, the maximum distance
  to the backing (W1.7 4 1/2" in 2018; 4 5/8" and W2.8 6 5/8" in 2021/2024, = TMS 402-16),
  1" nominal airspace, 2.67 sf per tie (2 sf over 30 psf), 32"/24" o.c.; IRC R104.11
  (alternative materials and methods). TMS 402-22 / BIA TN 3C measure 6" to the face of
  ≥100 psi sheathing instead; not the basis here.
- IRC 2018 (MN, UpCodes), 2021 (Colorado, UpCodes), 2024 (Oklahoma, UpCodes; model text) R703.8.3, Table
  R703.8.3.1, R703.8.4, Table R703.8.4(1), R703.8.4.1, R703.8.4.1.1, R703.8.5, R703.8.6 — §6l. Table R602.7.5 is
  `sunken_door_band_header.md`'s. Heckmann Building Products catalog (2018 TMS 402-16 anchor summary p.70;
  Pos-I-Tie ThermalClip p.71; ties p.81), buildsite.com. ASTM A123 Tables 1 and 2 and AGA's "Estimating the
  Life of Hot-Dip Galvanized Coatings" (galvanizeit.org), §6l.
- BIA Technical Note 18 — clay masonry movement; the basis for the end soft joints in §5.1.
- BIA Technical Note 18A, *Accommodating Expansion of Brickwork* (May 2019), Eq. 1, sealant
  and backer-rod guidance — §6g.
  https://www.gobrick.com/content/userfiles/files/tn18a-Accommodating-Expansion-of-Brickwork.pdf
- Dow, DOWSIL 790 Silicone Building Sealant TDS, form 61-884-01 (C920 Type S, NS, Class
  100/50; +100/−50). https://www.dow.com/en-us/pdp.dowsil-790-silicone-building-sealant.01397737z.html
- Nomaco HBR closed-cell backer rod, ASTM C1330 Type C.
  https://www.nomaco.com/wp-content/uploads/2016/09/cp_0032_hbr_0916.pdf
- Sika Emseal Seismic Colorseal product data sheet (±50%; 4" size, 4 1/2" depth; brick and
  masonry cavity walls). https://www.emseal.com/product/seismic-colorseal-wall-expansion-joint-3/
- ACI 318-19 §22.7.6.1, §22.7.7.1, §9.6.4, §9.7.5, §9.7.6.3.3 (torsion, §6c); §24.2.3.5,
  §24.2.4.1 and Table 24.2.2 (deflection, §6d); §25.4.2.3 and §25.4.3.1 (anchorage, §6e).
- ACI 318-19 Table 25.4.3.2 (ψr 1.0 for #11 and smaller with Ath ≥ 0.4 Ahs or s ≥ 6db,
  else 1.6) and §25.4.3.3 (Ath counts ≥ 2 ties, ≤ 8db apart; perpendicular ties evenly
  distributed along ℓdh), §25.4.2.4 (straight ℓd), §25.5.2.1 (class B lap) — §6e. Table
  reproduced in S. K. Ghosh, "The most notable changes from ACI 318-14 to ACI 318-19",
  PCI Journal Mar–Apr 2024, Table 2
  (https://www.pci.org/PCI_Docs/Publications/PCI%20Journal/2024/March-April/23-0001_Feature_Ghosh_MA24.pdf);
  §25.4.3.3's wording via ideCAD's ACI 318-19 development notes
  (https://help.idecad.com/ideCAD/development-of-reinforcement).
- **TMS 402-22 §13.1.2.3** — ℓ/600 (allowable-stress D + L) on any horizontally spanning
  member supporting veneer. This is the GOVERNING deflection limit and it is graded (§6f). It
  supersedes this note's earlier citation of TMS 402-16 §5.2.1.4.2, which sat inside a
  masonry-beam clause and was printed NOT GRADED for that reason.
- ACI 318-19 **§24.2.3.6** (Ie,avg = 0.70 Ie,mid + 0.30 Ie,end for a member continuous at both
  ends) and **Table 14.5.2.1** (structural plain concrete, `Mn = 5λ√f'c · Sm` in US customary
  units, φ 0.60 per Table 21.2.1) — §6f. The US coefficient was confirmed 2026-09-22 before
  the wall row was printed: the 0.42λ√f'c form is the SI expression with f'c in MPa. Sources:
  Eng-Tips "Plain (UnReinforced) Concrete Allowable Stress" and the CalcTree ACI 318-19
  plain-concrete-wall template, both reproducing the 5√f'c modulus of rupture with φ = 0.60.
- `notes/sunken_garden_court_free_body.md` — the court's own free body, unchanged by this.
