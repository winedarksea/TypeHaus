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
| `FT-B-S2/S3` south face | 20" strip, `offset` 2" off axis | −8" |
| wythe | 3-5/8", on the beam's north edge | −10.05" … −13.675" |
| backup finished face | EPS face, since 2026-09-05 | −6.05" |
| open cavity | EPS face (−6.05") to wythe | **4.0"** |
| foam behind the wythe | 4" XPS + 2" EPS | 6.0" |
| anchor reach | brick back to sheathing/stud | ~10.05" |

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

Simple span, 19.0 ft (bearing is 6" each end; taking the clear span is conservative):

```
M  = w L^2 / 8   = 0.530 × 19.0^2 / 8            = 23.9 ft-k
d  = 17.75 - 2.5 (cover + bar)                   = 15.25 in
As = M / (phi × fy × 0.9d)
   = 23.9 × 12 / (0.9 × 60 × 0.9 × 15.25)        = 0.39 in^2
```

**2-#5 bottom (0.62 in²) governs by detailing, not by demand** — d/c on the steel is 0.63,
and ACI 318-19 §9.6.1.2 minimum (3√f'c·b·d/fy = 3√4000 × 12 × 15.25 / 60000 = 0.58 in²)
is the binding number, not the moment. Mirror 2-#5 top for the pocket restraint at each end,
#3 stirrups at 8" o.c. Shear: V = wL/2 = 5.0 k against φVc = 0.75 × 2√4000 × 12 × 15.25 /
1000 = 17.4 k, d/c **0.29** — stirrups are detailing too.

## 4. Torsion from the eccentric wythe

The wythe sits on the beam's north edge, not its centreline, because centring it would cost
the cavity (the wythe's position is set by the beam and did not change
on 2026-09-05, so this is unaffected by the EPS):

```
e  = beam centre (-16") - wythe centre (-11.86")   = 4.14 in
t  = 308 plf × (4.14/12) ft                        = 106 ft-lb per foot
```

Equilibrium torsion is not the case here — the beam is cast into both side walls and the
garden slab bears against its full south face for the whole span, so the twist is compatible
and sheds into the slab. ACI 318-19 §22.7.1 permits compatibility torsion to be neglected
below the cracking threshold; T_cr for a 12×17.75 section at f'c 4000 is on the order of
9 ft-k against 106 ft-lb/ft × 19 ft / 2 = **1.0 ft-k** at the support. d/c ≈ 0.11.

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
2. **The pocket bearing** into `W-SG-W1`/`W-SG-E1`: 6" of bearing on a 12" wall, chipped and
   doweled into an existing pour. Reaction 5.0 k over 12"×6" = 139 psi against 4000 psi
   concrete is not the question; the question is the dowel development into a wall that was
   cast first, and that is the engineer's.
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
