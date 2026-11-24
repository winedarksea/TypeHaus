# A1: Court retaining structure (W-SG-E2 / -S / -W2, W-SG-ARCH): structural and geotechnical review

Reviewer: A1. Scope: `retaining_wall/W-SG-E2|S|W2`, `retaining_system/W-SG-ARCH`, the
`retaining_court/` study, the oracle notes and the authored plan (`params/sunken_garden.py`).
Method: I read the sources and wrote standalone scripts with no typehaus import:
`out/review/scratch/A1/court_sliding.py` and `wet_credit.py`. I ran no `haus` command and no pytest.

## 0. Bottom line

* **Sliding arithmetic reproduces exactly.** Thrust 3,122.79 plf = ½·60·10.1198² + 50.48 (apron).
  Side-wall weight W = 1,368 stem + 1,050 footing + 3,009.6 heel soil = 5,427.5 plf, and the south
  wall 5,627.5 plf. The south thrust 3,122.79 × 18.0 = 56,210 lb is the whole resultant, because
  E2 and W2 cancel identically. Base friction 0.35 × (5,427.5 × 32.667 + 5,627.5 × 18) = 97,508 lb,
  giving **FS 1.7347 (d/c 0.865)**. Overturning, bearing, eccentricity, stem flexure, toe flexure
  and heel flexure all reproduce to the digit (§6).
* **The group free body is legitimate only if two load paths exist, and one of them is not graded
  and probably does not work with the bars as authored.** E2 and W2 can spend their base friction
  north-south only if their own east-west thrusts reach the strut and the corner through the
  structure. When the court sits at FS 1.5, at least ~75% of each side wall's 51 kip thrust has
  to travel that way, and it travels as **in-plan bending of FT-SG-W2/E2**: an 84"-deep beam
  spanning 16'-4" from the south corner to W-SG-ARCH. The authored longitudinal steel is `#4 @ 18"`,
  "distribution steel; carries no graded limit state". See finding A1-01.
* **The strut demand is understated by 1.3-1.8x** (A1-02). It still passes.
* **The cheapest robust sliding fix costs no concrete** (A1-03). Concrete already cast in the same
  placement and spliced to the loop (FT-SG-W1/E1, plus the two corner squares) is left out of the
  friction sum. Counting it gives FS 2.20 at μ 0.35, and **1.57 at μ 0.25 with no stone bed**.
  That removes the design's stated dependence on how the bed is built. Pair it with A1-01's tie
  bars (~400 lb of #5) and, for PE comfort, the optional key in A1-03b.
* **The study's 7.66 is reproduced exactly.** It is a per-foot, isolated-cantilever sliding ratio
  in a 5'-head wet case that double-counts water. It is not the court's ratio. At that head the
  equivalent *system* case is FS **1.49**, which is still the honest adverse case, and the package
  carries no wet case at all (A1-05, A1-06).

## 1. Findings: what is wrong or open, most important first

### A1-01 · GAP, likely ERROR-unconservative in effect · plan bending of FT-SG-W2/E2 is the hidden load path of the system FS, and it is ungraded

**What and where.** `retaining_system.py:387-399` (`_free_body`) sums isotropic friction under all
three footings against the 2-D resultant. That is correct as a lower bound only if the friction
under E2/W2 can point north-south while their east-west thrust is carried internally.
`_corner_transfer` (`:477-523`) grades only the south wall's shortfall. `strut_reaction_lb`
(`:431-464`) grades only the strut. Nothing grades how E2's base shear *gets to* the strut and
the corner. That path is the footing (with the stem on it) bending in plan between the SE corner
and W-SG-ARCH. `params/sunken_garden.py:1214-1215` authors the bars that would carry it as
`bottom-y #4 @ 18"`, "longitudinal distribution steel; carries no graded limit state".

**Evidence** (`court_sliding.py`, "FT-SG-E2 plan bending"). Friction is a vector limited to one
disc per footing. At the code FS of 1.5, E2 and W2 must each supply 16,288 lb north-south. That
leaves √(20,685² − 16,288²) = 12,750 lb of their 20,685 lb (FS-1.5) disc for east-west. So **≥75%
of the 51,006 lb side thrust must go into plan bending**. At service with no FS margin the minimum
is 43%. Rough strut-and-tie, lever arm z ≈ 62" in an 84" deep beam, span 16.33', φ 0.75:

| share in plan bending | end condition | Mu ft-lb | Tu lb | As req'd in² |
|---|---|---|---|---|
| 100% | simple | 166,618 | 32,249 | 0.72 |
| 75% (FS-1.5 minimum) | simple | 124,963 | 24,186 | 0.54 |
| 75% | ~fixed (wL²/12) | 83,309 | 16,124 | 0.36 |
| 43% (service minimum) | simple | 71,646 | 13,867 | 0.31 |

Only the one or two `#4` nearest the court-side (toe) edge, 0.20-0.40 in², sit where a tie can
work. Rough d/c is 1.3-1.8 simple and 0.9-1.3 with end fixity. The heel-side edge needs a hogging
tie over the strut too, because the footing runs on into FT-SG-E1. **Confidence: medium.** The
STM lever arm and the end fixity are judgment, and the arching may be shallower. What I am
confident of is that the path is real, carries tens of kips, and is graded nowhere.

**Class: SMALL-FIX (design) + engine row.**
* Plan (`params/sunken_garden.py`, `_spliced_mat` for W2/E2): add `BarSpec(role="edge-y", bar=5,
  count=3, …)` along the toe edge and along the heel edge of FT-SG-W2/E2, inside the 3" cover.
  Splice them class B into FT-SG-S and FT-SG-W1/E1, as the `#4` already are. About
  2 footings × 2 edges × 3 bars × ~32 ft ≈ 390 LF of #5 ≈ 400 lb galvanized.
* Engine: add a `footing plan bending` limit state to `retaining_system` (ACI 318-19 Ch. 23 STM,
  or deep-beam flexure). Use w = (side thrust − the east-west friction the FS-1.5 allocation
  leaves) over the corner-to-strut span, pinned and fixed bounds, against the authored edge bars.
  Expected d/c ≈ 0.6-0.8 with 3 #5 per edge.

### A1-02 · ERROR-unconservative (mild; still passes) · strut force omits the braced legs and footing continuity; capacity uses 3,000 psi against a 5,000 psi mix

**Where.** `retaining_system.py:431-464` and `:526-571`. The reaction is taken as 0.5·w·L from
W2/E2 alone. FT-SG-E2 is cast and spliced continuously into FT-SG-E1, and W-SG-ARCH is also the
bottom brace of the *braced* W1/E1 legs. Their bottom reactions (≈2/3 of an at-rest stem thrust,
~1,660 plf over 10.44') cancel through ARCH and BRKBM too. The record ignores them.

**Evidence.** I assumed E1 retains the same height (UNVERIFIED; it is a load path for another
reviewer).

| model | service R, lb | Pu | d/c at 3,000 psi | d/c at 5,000 psi |
|---|---|---|---|---|
| engine (0.5 wL, E2 only) | 25,503 | 40,804 | 0.512 | 0.307 |
| simple spans E2 + E1 | 34,188 | 54,701 | 0.686 | 0.412 |
| continuous E2/E1 over ARCH | 45,548 | 72,878 | 0.914 | 0.548 |

Capacity uses `PRESUMPTIVE_FC_PSI` 3,000 even though W-SG-ARCH's assembly takes the EXPOSED_MIX
5,000 ticket. The wall records read the specified f'c via `concrete_spec_for`, so the package
mixes the two. **Confidence: medium-high.**

**Class: SMALL-FIX.** In `strut_reaction_lb`, add the base reactions of every wall whose
`base`/`top_and_bottom` brace is this cross-member (W1/E1). Take the continuous-beam reaction as
the governing bound. In `_strut` and `_corner_transfer`, read f'c from the cross-member's assembly
(as `retaining_basis._geometry` does) and fall back to 3,000 only when none is authored.
`BASIS_VERSION` → 4. Expected strut d/c ≈ 0.55 (5,000 psi, continuous).

### A1-03 · ERROR-conservative / DECISION (the recommended sliding fix) · friction under concrete already in the loop is not counted, which is why the design "depends on the bed"

**What.** `_free_body` counts each member as a unit section × axis length, for three members. It
leaves out:
* (a) FT-SG-W1/E1 (2 × 10.443', placement 1, `#4` spliced through, `sunken_garden.py:1244-1258`);
* (b) the two 3'-6" corner squares FT-SG-S has owned since 2026-10-10 (§12b of the free-body note,
  net 12,267.6 lb each);
* (c) ARCH's own weight (≈2.7 kip, ignored here).

The note's own §13 *does* credit W1/E1 for staged backfill, so the final and staged states are
counted differently.

**Evidence** (`court_sliding.py`):

| credited | μ 0.35 | μ 0.25 (no-stone case) |
|---|---|---|
| as graded | 1.735 | **1.239** ✗ |
| + corner squares | 1.887 | 1.348 ✗ |
| + corners + W1/E1 concrete only | **2.202** | **1.573** ✓ |
| + corners + W1/E1 with heel soil | 2.593 | 1.852 ✓ |

The middle row needs no assumption about W1/E1's retained soil. **This takes the "the bed is the
reason the walls stand" exposure (note §5) off the table.**

**Statically legitimate if:**
* W1/E1's own east-west base reactions cancel through ARCH and BRKBM, both cast struts (true as
  authored);
* W1/E1's tops really are braced by the porch framing. That is a dependency for the porch/ledger
  reviewer: if the porch cannot strut wall to wall, W1/E1 are retaining walls in their own right;
* S's net push can travel north along the E2/W2 footings into W1/E1 as axial compression, across
  a monolithic 84" × 12" section. That holds trivially.

**Class: DECISION.**
* (a) Credit as above. Engine: in `_loops`/`_members`, add every wall on the same cast cycle whose
  footing is spliced to a member as a weight-only member (zero net thrust, because its own
  reactions cancel internally). Add the footing extensions from the resolved footing solids
  rather than wall × axis length. This is cheap and needs no field change. Sliding d/c goes from
  0.865 to ~0.68.
* (b) Optional belt-and-braces, a shear key under FT-SG-S only: 12" wide × 24" deep × 25' long,
  ≈1.9 cy plus 2 #5 longitudinals. With IBC Table 1806.2 class 3 lateral bearing at 200 psf/ft
  measured from the court floor, P ≈ 20 kip, FS goes to 2.09 at μ 0.35 and 1.60 at μ 0.25.
  Combining lateral bearing with friction relies on IBC §1806.3.1 (UNVERIFIED; not paraphrased in
  the repo).
* (c) Not recommended: a wider south heel. It buys only +0.13 FS per foot and still fails at μ 0.25.

**Recommendation:** (a) plus A1-01's bars. That puts the court at FS > 1.5 for any presumptive μ
from 0.25 up, which is the "nothing to argue about" state.

### A1-04 · ERROR (arithmetic in the oracle note; unconservative for the drawn rule, still passes) · staged-backfill W1/E1 weight

**Where.** `notes/sunken_garden_court_free_body.md:2995`:
`2 × 10.443' × (5,974.8 − 3 × 9.12 × 110 = 2,965.2 plf) × 0.35 = 21,676 lb`. The 5,974.8 is the
130 pcf weight, and subtracting 110 pcf soil leaves 547 plf of phantom soil on an empty wall. The
empty W1/E1 weight is stem + footing = 1,368 + 1,050 = **2,418 plf**, which gives 17,676 lb.

**Evidence.** My twelfths grid reproduces the note's table *exactly* with its number: H/4 1.92,
H/3 1.82, H/2 1.64, unrestricted 1.37. Corrected: **1.86 / 1.76 / 1.58 / 1.31**. The drawn H/2
rule (AN-SG-BACKFILL) still clears 1.50. **Confidence: high.**

**Class: SMALL-FIX.** Note §13, line 2995: replace `5,974.8 − 3 × 9.12 × 110 = 2,965.2` with
`1,368.0 + 1,050.0 = 2,418.0`, then 17,676 lb. Results row H/2 becomes **1.58**, and "one side
empty" 1.31. Re-pin `test_retaining_court.test_staged_backfill_holds_at_half_a_wall_of_difference`
if it reads the note's figure.

### A1-05 · GAP · no wet / blocked-drain case anywhere in the register

**Where.** 04-assumptions `retaining_wall` #4 ("No hydrostatic case … A saturated backfill
roughly doubles the thrust"). IRC R404.4 lists hydrostatic pressure among the loads a retaining
wall is designed for, and the earlier review asked for an agreed blocked-drain case.

**Evidence** (`court_sliding.py`, `wet_credit.py`). Perched water in the backfill at height hw
above the footing underside, with the stone bed still draining (no uplift). Below water the
pressure is K0·γ′ + γw, with K0 = 60/110 and γsat 125 (UNVERIFIED; a typical value). Water also
loads the heel.

| hw above underside | system FS as graded | + A1-03(a) credit | + credit, μ 0.25 |
|---|---|---|---|
| 4 ft | 1.63 | 2.05 | 1.47 |
| 6 ft (= the study's 5' above footing top) | **1.49** | 1.88 | 1.34 |
| 8 ft | 1.33 | 1.67 | 1.20 |
| full height | 1.17 | 1.46 | 1.04 |

There is a second scenario. The bed fills to its lip (-127 7/16", 6" under the footings: the
`drainage.soakaway_storage` UNKNOWN), and if `FD-SG-OVERFLOW`/the sump fail the court floods to
the footing top. That gives uplift and no net water thrust (equal heads): **FS 1.59** as graded.

**Class: DECISION.** Pick one wet design case and register it as a `sliding (wet)` row.
Recommended: perched water at H/2 above the footing top, plus the flooded-court case. No code
publishes a wet FS. Many designers accept 1.1-1.25 for an unusual case. Stating it is a PE
judgment, so the cleanest owner-side close is to make the as-graded FS ≥ 1.5 *with* the case.
A1-03(a) does that up to hw ≈ 8 ft above the underside, and A1-07's granular backfill makes a
perched head implausible.

### A1-06 · REVIEWABILITY (and the earlier review's 7.66) · the `retaining_court/` study is unreconciled and should not ship as is

**Where.** `engineering/retaining_court/comparison.py:99-107` (`_cases`), `stability.py`,
`loads.py:52-82`, `inputs.py:155-185`.

**What 7.66 is.** I reproduced it to two decimals (`court_sliding.py` last block): per-foot sliding
of ONE isolated wall, with no loop, no strut and no corner. The case is "blocked-drain-wet" with
a 5.0' head above the footing top. Thrust 5,341 plf against W 2,988 plf gives FS 0.196, and
1.5/0.196 = **7.66**. Three modelling errors inflate it:
* (i) water is *added* to a total-stress EFP of 60 (`loads.py:79-81`) instead of using K0·γ′ + γw,
  so below the water line it applies 122 psf/ft against ~96;
* (ii) concrete *and soil* are taken buoyant over their whole height, including everything above
  the water line (`stability.py:47-52`);
* (iii) friction is applied with no loop credit, the very free body `params/sunken_garden.py:981`
  calls "the arithmetic of a wall nobody built" (FS 0.73 dry).

The study is also stale against the design. It uses the `#6 @ 10"` stem (`comparison.py:179`),
120 pcf, "SM" labels for GM, 45 active, and "GFRP dowels" (deleted at basis 5).

**Reconciled now?** No. The register omits it, and nothing maps its cases to the system record.
The comparable system number is A1-05's **1.49 at the same head**, which is a ~1.0 ratio, not
7.66.

**Class: SMALL-FIX.** Either delete the per-foot wet/compaction sweep from the study or re-base it
on `retaining_system._members` (K0·γ′ + γw, buoyant only below water). The package should carry
the single system wet row from A1-05 plus one sentence explaining why a per-foot sweep is not
the court's check. It should not carry 7.66.

### A1-07 · GAP (presumed soil drives the answer) · the retained-soil class is the largest sensitivity, and a material spec can remove it

**Evidence.** If the backfill behind the stems is a CL/ML-CL till, IBC 1610.1 gives at-rest
100 psf/ft (`soil.py:45-50`) and system **FS 1.05**. Des Moines-lobe till is often loam or clay
loam (UNVERIFIED; that is exactly what the presumed-GM flag admits). For comparison: active 40
gives 2.58, 130 pcf gives 1.91, apron off gives 1.76.

**Class: DECISION.** Specify an imported free-draining granular backfill (GW/GP/SW/SP; Table
1610.1 at-rest 60, active 30) behind the three stems. It runs from the footing to ~12" under the
terrace, across the heel and out to a 1:1 line from the heel's back edge. That is roughly 60-90 cy
for the three walls (rough; the bid price is the owner's). It makes the EFP a specification
instead of a regional presumption, and it is also the drainage answer to A1-05. Have the engine
read the backfill material (the `FootingBedding` precedent) and print which row it graded. I
found no authored backfill material for the court. If one exists, the engine should cite it.

### A1-08 · GAP (handed to "the geotechnical engineer") · the deep plane under the 54" of stone

**Where.** 04-assumptions `retaining_system` #2: "Deep-seated slip … stays the geotechnical
engineer's". Under goal 2 that is a decision handed out of the package.

**Evidence.** The beds are trenches as wide as the footings: 7.0 ft, and 8.33 ft at S. Below them
are 42" of frost section plus a 12" soakaway course, so the stone sits on native GM. The
stone/native plane is not weaker than concrete/stone in the *trench-only* sense. With μ 0.25 plus
the stone's own weight (#57 at ~100 pcf, UNVERIFIED), ΣN = 449 kip gives 0.25·ΣN / 56.2 kip =
2.00 dry and ~1.75 with 48" of stone submerged. But a block sliding at -175" also carries the
thrust down the trench face. At-rest over 14.6 ft on the S trench is ~116 kip. Whole-block FS is
~1.35 at-rest with no passive and ~2.0 active, and higher once the native core's base shear and
the court-side passive (IBC class 4, 150 psf/ft) are credited.

**Class: DECISION.** Either put this screening (whole-block, active, passive at the IBC allowable)
in the package as a graded row, or accept that a boring closes it. One boring closes soil class,
μ, EFP, groundwater and this row at once. The free-body note §5 already says so.

### A1-09 · GAP (minor, closable by calculation) · rows a reviewer will expect

* **Stem one-way shear.** Vu ≈ 1.6 × (½·60·9.12² + apron) ≈ 4.06 kip/ft against φVc 11.06 gives
  **0.37**. Add the row.
* **Bearing on native under the stone.** The engine grades 3,000 psf (class 3) on the stone only.
  At the bed base the average is 1,225 psf (E2) / 1,125 psf (S) against class 4 2,000 psf, so it
  passes. Add the row.
* **Corner detailing.** "Corner bar development is ordinary practice and is not something this
  engine has looked at" (04-assumptions #6) is a PE handoff. Close it on the drawing: stem
  horizontals `#4 @ 16"` EF lapped round both south corners with L-bars (class B), and the
  footing edge bars of A1-01 continuous through the corner.
* **Compaction surcharge.** The study runs 250 psf, and the register and §13 do not. Close it with
  the house's own backfill rule (only hand-guided plates within H/2 of a stem; note §4 of
  `foundation_aggregate_and_backfill.md` already says ~3' for the house) put on AN-SG-BACKFILL.

### A1-10 · REVIEWABILITY · `corner shear transfer` grades a different mechanism from the one that acts

`_corner_transfer` passes the *whole* S shortfall (20,757 lb) as in-plane shear through *one*
stem section. The real path is FT-SG-S bending in plan over 18' with reactions of ½ × 20,757 into
the W2/E2 footings as axial load. It is conservative (Vu doubled), so not an error. But a PE will
ask for the S plan bending: Mu = 1.6 × 20,757 × 18/8 = 74.7 kip-ft, Tu ≈ 12.8 kip ≈ one #5 of the
authored `bottom-y #5 @ 12"` out to out, so it passes. **SMALL-FIX:** rename the row
`S footing plan bending / corner delivery`, grade it that way, and print both halves of the
lower-bound friction allocation (A1-01) on the sheet with a one-line plan sketch.

### A1-11 · REVIEWABILITY · stale oracle note text a PE will stumble on (earlier review item 9, still open)

`notes/sunken_garden_court_free_body.md` §1 (lines 129-151) and §3 (269-277) still show a
"19'-0" × 26'-0"" court, W-SG-S "20'-0"", ARCH "12" × 17 1/2", 20'-0" clear, buried", `#5 @ 7"`,
and FS 1.63 / no-stone 1.16 / 1.29. The design is 17'-0" clear, S 18.0' on axes, ARCH 12" × 12"
in the footing plane, `#5 @ 10"`, FS 1.735, and no-stone **1.24**. The current numbers exist only
in §12a/§12b near the end. The earlier review's "1.16 no-stone sensitivity" is likewise **1.24**
today. **SMALL-FIX:** move §12a/§12b's numbers into §1/§3/§4 and mark the older sections
"history", per the review's own close-out recommendation.

## 2. Answers to the specific questions

1. **Free body rebuilt** (§0). H = 10.1198' (stem 9.1198' + 12" footing) to the terrace at
   0'-0". At-rest 60 psf/ft for GM (IBC 1610.1 row as read in `soil.py`). Drained, with no
   hydrostatic term. Apron +50.48 plf at 5.44'. No house surcharge, no vehicle, no snow or patio
   live load on the terrace. The patio is retired, the terrace is planted, and the 04-assumptions
   list does not exclude terrace live load. I'd add one line saying none is applied, or apply
   100 psf×K0 as a sensitivity: at 54 psf × 10.12 ≈ +550 plf it gives FS ≈ 1.47 as graded and
   ≈ 1.87 with A1-03(a). Water: none.
2. **Resistance side.**
   * Cancellation through ARCH is statically legitimate, conditional on A1-01. Friction under
     E2/W2 *is* partly needed east-west unless the plan-bending path exists.
   * N = ΣW does not change with overturning while e < B/6, which holds (0.851 vs 1.167;
     0.302 vs 1.389).
   * Heel soil is legitimately counted on the virtual-back convention the thrust uses.
   * μ 0.35 is the IBC class 3 GP row. For concrete cast directly on open #57 it is conservative,
     because the paste keys into the stone. The geotextile listed "on the soil face and the top"
     of the court beds (`foundation_aggregate_and_backfill.md` §d) must not lie between footing
     and stone. If it does, the interface is the fabric's and no code row covers it: say "no
     fabric under footings" on the drawing.
   * The weakest plane is either concrete/stone or the deep plane (A1-08).
   * Passive is not used, and correctly so (toe embedment 0").
   * Load path from S into E2/W2: fine through FT-SG-S (A1-10). The weak link is E2/W2's own
     plan bending (A1-01), not the corners.
3. **North end.** It stands against the house only through compliant isolation boards (EPDM
   capped at 3.5 psi, note §11l). The system is designed not to need the house. The house side is
   graded under `thermal_break_transfer/*` (register: W-SG-BRKBM 0.68). The ~28.8 kip the boards
   can pass is a reserve that is rightly not credited.
4. **Individual walls.** Overturning 2.351 (E2/W2) and 3.044 (S). Bearing 1,341 / 822 psf.
   e 0.851 / 0.302 against kerns 1.167 / 1.389. All verified. Per-wall sliding with no system:
   **E2/W2 0.61, S 0.63 at-rest; 0.91 / 0.94 active**. The per-wall records are consistent with
   the system only once A1-01 is closed. ARCH bears at mid-footing depth, so crediting it would
   slightly help overturning; ignoring it is conservative.
5. **Sensitivities** (system FS, at-rest, 110 pcf unless noted):

   | case | as graded | with A1-03(a) |
   |---|---|---|
   | μ 0.25 | 1.24 | 1.57 |
   | μ 0.30 | 1.49 | 1.89 |
   | μ 0.35 | 1.735 | 2.20 |
   | μ 0.45 | 2.23 | 2.83 |
   | active 40 | 2.58 | — |
   | 130 pcf | 1.91 | — |
   | apron off | 1.76 | — |
   | CL backfill (at-rest 100) | 1.05 | — |
   | wet, hw 6' | 1.49 | 1.88 |
   | court flooded | 1.59 | — |

   The earlier review's "no-stone 1.16" is now **1.24**. The study's 7.66 is explained in A1-06.
6. **Recommended fix.** A1-03(a): count the concrete already in the placement. Add A1-01's 3 #5
   edge ties per footing edge (~400 lb steel). Add A1-07's granular backfill spec. Optionally add
   A1-03(b)'s 12" × 24" key under FT-SG-S (~1.9 cy). Result: sliding ≥ 1.5 at μ 0.25 and in the
   H/2 perched-water case, with no dependence on bed quality or on the presumed native class for
   the EFP.

## 3. Earlier review (2026-09-18) items in this area: status

| item | status |
|---|---|
| §3 system FS 1.628, conditional on the bed | geometry moved: FS **1.735**. The bed dependence is **still open** (no-stone 1.24) and closable by A1-03 |
| §3 corner transfer / development | **partly closed** (corner shear row). Development and detailing are still open (A1-09, A1-10), and the real open path is A1-01 |
| §3 construction-stage / differential backfill | **closed** by note §13 + AN-SG-BACKFILL, with the arithmetic slip in A1-04 |
| §3 compaction surcharge | **open** (A1-09) |
| §3 settlement / global stability / 42" stone on native | **open**, handed to geotech (A1-08) |
| §3 drainage basis, blocked-drain case | dimpleboard and collector are modelled (closed). The wet design case is **open** (A1-05), as is the lip-inside-the-section UNKNOWN |
| §3 study 7.66 omitted | **open**, now explained (A1-06) |
| §9 stale oracle notes | **open** (A1-11) |
| §10 f'c / reinforcement outside the fingerprint | **closed for `retaining_wall`**: `fc`, `fy`, both covers, bar sizes and spacings are inputs with quanta (W-SG-S sheet §3), and `fingerprint.py` hashes every input. `retaining_system` capacities read the constant 3,000 psi, covered by `BASIS_VERSION`. A1-02's fix should add the cross-member's f'c as an input |

## 4. Prescriptive route

None. IRC R404.1.1 / R404.4 send a 10'-retained cantilever to engineering, and no IRC table or
major-manufacturer cast-in-place table covers it. The item stays engineered. Goal 2 is reachable
by A1-01 through A1-09, every one closable by calculation or a small design change except A1-08,
which needs a boring.

## 5. Verified correct (independent recomputation)

* System sliding: 56,210 / 97,508 / 1.7347, and the per-footing shortfalls 19,978 and 20,757.
* Strut capacity: 0.60 × 0.45 × 3,000 × 144 × 0.6836 = 79,734 lb. Corner φVn
  0.75 × 2√3000 × 12 × 87.55 = 86,316 lb.
* E2: FSot 2.351, e 0.851, q 1,341. S: FSot 3.044, e 0.302, q 822.
* Stem: Mu 12,277 against φMn 14,177 (d 8.6875", a 0.438", εt 0.045, tension-controlled).
* Toe and heel rows match note §7/§12a. Hook ℓdh 7.11" < 7.875" with ψr 1.0 (spacing 10" ≥ 6db).
  The ACI 318-19 Table 25.4.3.2 factors are from my reading and are not paraphrased in the repo,
  so they are UNVERIFIED there.
* Minimum steel: vertical 0.372 ≥ 0.173. Horizontal `#4 @ 16"` EF = 0.30 ≥ 0.288 (ρ 0.0020).
  Cover 3" stem (C2/F3 choice) and 3" footing (cast against ground).
* Staged-backfill grid reproduces the note's table exactly (before A1-04).
* Study 7.66 reproduced (A1-06).

## 6. Not verified

* The porch's ability to brace W1/E1 tops.
* E1's actual retained height.
* Whether any geotextile lies under the footings.
* The #57 unit weight.
* The geotextile and native interface values.
* IBC §1806.3.1 combined-resistance wording and ACI hook factor text (from memory, marked
  UNVERIFIED above).
* The apron surcharge derivation (accepted from the sheet; the W-RG-* items belong to the
  tiered_retaining reviewer).
* No model was loaded and no test was run.
