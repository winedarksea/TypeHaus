# Sunken-garden veneer grade beam — hand-worked basis

**House:** catlin
**Structure:** `W-SG-BRKBM` (the beam), `W-B-BRICK` (the wythe it carries), `FT-B-S2` /
`FT-B-S3` (the footings it is isolated from), `SG_VENEER_BEAM_14` (the assembly).
**Written:** 2026-09-05, by hand.
**Oracle for:** no engine calculation — **this note is the whole basis**. Nothing in
`typehaus/engineering/` grades a spanning grade beam, a masonry-veneer tie, or a thermal
break, so every number below is hand-worked and none of it is reproduced by the engine.
The geometry it rests on IS pinned, by
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

> ⚠ **The veneer anchor is an engineered item.** The airspace itself is 2" and compliant,
> but the beam holds the wythe ~10" off the backup's structural face and no prescriptive
> table reaches that. See §5.1 — including why IRC R703.15's 4" foam limit does *not*
> apply here, and why the wythe must NOT be anchored to the side retaining walls.
> The ties are an engineered item under TMS 402 and are NOT designed in this note (§5).

---

## 1. Why the beam exists

`W-B-BRICK` is 129 SF of unglazed brick standing at the bottom of an open court, exposed on
**both** faces above the garden slab, so it sits at outdoor air temperature all winter
(design −20 °F, AFI 2500). Until 2026-09-05 it bore on `FT-B-BRICK`, a 10"×5" plinth cast on
`FT-B-S2`/`FT-B-S3`'s own projecting toe. That put the wythe in direct series with the house
footing — whose underside is level with the court floor and whose entire frost protection is
the R403.3 wings (`SL-SG-FROST-W/N/E`) plus the insulated form.

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
| beam clear span | court clear width, `_x_in_w` → `_x_in_e` | 19'-0" |
| beam bearing | 6" into each side wall (nodes on `_x_ax_w`/`_x_ax_e`) | 6" each end |
| beam section | `SPEC.wall_thickness_in` × (`_veneer_beam_top` − `_veneer_beam_bottom`) | 12" × 17-3/4" |
| beam concrete faces | −10" (north) … −22" (south) | |
| isolation board | 2" XPS, 40 psi, north face | −8" … −10" |
| `FT-B-S2/S3` south face | 20" strip, `offset` **6"** off axis since 2026-09-05 | −4" |
| wythe | 3-5/8", on the beam's north edge | −10.05" … −13.675" |
| backup finished face | EPS face, since 2026-09-05 | −6.05" |
| open cavity | EPS face (−6.05") to wythe | **4.0"** |
| foam behind the wythe | 4" XPS + 2" EPS | 6.0" |
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
exactly fills a void the court already had. The frost wings run continuous **underneath** it
— the beam spans to the side walls and delivers nothing to the foam.

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

## 5. What is NOT graded here, and what needs a seal

1. **The veneer ties — still engineered, but for a different reason since 2026-09-05.**
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
   it. The end condition is a sealant joint over compressible filler; **the model does not
   carry one and nothing in the engine grades it.**
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
   load into structure that is already broken from the house at `DW-SG-W1/E1-FOAM`. It does
   **not** compute a frost isotherm. A 2" XPS board at R-10 across 12.7 SF replaces a
   contact that had 16.0 SF of assumed-but-unplaced foam over 16.0 SF of placed stone; that
   is unambiguously better and it is not a number.
4. **Whether the beam helps the retaining walls.** It does not. See the banner.

## Sources

- IRC 2018 R703.8.4 — anchored masonry veneer, airspace and tie spacing.
- IRC 2018 R403.3 and Figure R403.3(3), Table R403.3(1) at AFI 2500 — the FPSF this beam
  must not compromise.
- IRC 2018 R404.1.2(8) — the table `W-SG-W1`/`E1` already satisfy.
- ACI 318-19 §9.6.1.2 (minimum flexural steel), §22.5 (one-way shear), §22.7.1
  (compatibility torsion).
- TMS 402/602-16 §6.2 — anchored veneer, and the engineered path a ~10" anchor reach requires.
- IRC 2021 R703.15 — cladding attachment over foam sheathing; **excepts anchored masonry
  veneer to R703.8**, which is why the 4" foam limit in `plans/cost-options.md` §6 is not
  this wall's limit. Note the Airspace column of Table R703.8.4(1) could NOT be sourced:
  ICC publishes the table with the rows "not shown for brevity" and the full text is
  paywalled. The 1" minimum is confirmed; the 4-1/2" ceiling rests on TMS 402, not on a
  quoted IRC row.
- BIA Technical Note 18 — clay masonry movement; the basis for the end soft joints in §5.1.
- `notes/sunken_garden_court_free_body.md` — the court's own free body, unchanged by this.
