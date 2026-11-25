# Court sliding: which lever buys margin cheapest (study, 2026-11-23)

A design study (branch `study-sliding`). **Adopted 2026-11-24:** the 3'-0" rule and FT-SG-S +6"
with a #5 @ 9" heel bar are drawn; the current values are worked in
`sunken_garden_court_free_body.md` §15e and §15n. The tables below are the study as run: each
lever measured alone against the design before adoption. Replacing the brick with a concrete cross
wall is a separate study and is not modelled here.

Every number comes from the engine on the study branch (`retaining_system/W-SG-ARCH`,
`retaining_wall/*`, `thermal_break_transfer/W-SG-ARCH`, `column_support/*`, `base_rotation/*`)
or from a hand calculation shown below. Dollars come from `prices.toml` unless marked
**ESTIMATE**. The soil is the SPECIFIED basis: bed friction 0.43, native phi' 25 deg, at-rest 60
psf/ft, 110 pcf for sliding and 130 pcf for the restraint rows.

## The answer

**Tighten the backfill rule to 3'-0", and add 6" to FT-SG-S's heel.**

- The 3'-0" rule costs nothing. Alone it takes staged backfill from 1.529 to **1.721**. Dry
  sliding is already 1.93.
- The 6" heel costs about **$580-1,040** (part ESTIMATE). It is what keeps the rule comfortable
  when the crew slips: at a 4'-0" difference, one lift worse than the rule, staged is still
  **1.683**. It also lifts every other sliding row by about 0.05-0.09.
- Together: staged **1.787**, dry **2.026**, perched **1.644**, flooded **1.791**, deep plane
  **1.652**.
- Winter tension stays **0.998**, unchanged. Keeping it at or under 1.0 costs **$0**.

If the owner wants zero material, the 3'-0" rule alone meets the 1.65 target, with staged at
1.721 and dry at 1.930. It rests entirely on the crew following the lift rule.

## Today's design (the base every lever is measured against)

| Row | Value |
|---|---|
| staged backfill, H/2 rule (5'-0") | FS **1.529**: E2 at 5.06', S and W2 full; H 89,375 lb, N' 317,855 lb |
| dry sliding | FS 1.930 |
| perched at H/2 | FS 1.568 |
| flooded to the threshold | FS 1.702 |
| deep plane, soakaway full | FS 1.594 |
| one side empty, two full (a sequence the rule forbids) | FS 1.28 |
| thermal-break winter tension, side run (mu 1.00) | d/c 0.998 |
| retaining_wall stem flexure (x3) | d/c 0.865 |
| court-to-house joint closure | d/c 0.683 |

## Lever 1: a tighter backfill rule (no material)

The engine grades the drawn rule as a fraction of H on a grid of twelfths. This branch adds
`retaining_system_staged.RULE_FT`, which states the rule in feet on a 2" grid. It is off by
default, so the record still reads 1.529. To reproduce, run
`.venv/bin/python houses/catlin/notes/court_sliding_levers_study/scratch/staged_ft.py 4 3 2`.

| Rule: no side more than ... above another | Staged FS | Governing stage | H_stage / N' (lb) |
|---|---|---|---|
| 5'-0" (H/2, as drawn) | 1.529 | E2 at 5.06', S and W2 full | 89,375 / 317,855 |
| 4'-0" | 1.623 | E2 at 6.12', S and W2 full | 85,984 / 324,608 |
| **3'-0"** | **1.721** | E2 at 7.12', S and W2 full | 82,743 / 331,153 |
| 2'-8" (four 8" lifts) | 1.754 | W2 at 7.45', S and E2 full | — |
| 2'-0" | 1.817 | W2 and E2 at 8.12', S full | 76,808 / 324,608 |

- Nothing else moves. Dry, perched, flooded, the deep plane, winter tension and the joint are
  completed-court rows, so they do not change.
- Once the rule is 3'-0", perched at H/2 (1.568) becomes the court's governing sliding row.

**What the crew does.** Backfill already goes in lifts of 8" or less. The rule becomes: go round
the court W2, then S, then E2, one lift each in turn, and never let one side get more than
**four lifts (2'-8")** ahead of the lowest. That is graded at 1.754, and it leaves a 4"
allowance under the 3'-0" that the engine grades.

**Reliability.** This lever rests on crew discipline. Paint lift lines at 8" on the three wall
faces, or on stakes. The owner checks each round, and a lift log becomes a hold item on
AN-SG-BACKFILL. If one side is left empty while the other two are full, FS falls to 1.28. That
sequence is forbidden today too, and the rule does not change it.

## Lever 2: wider heels on the retained side

Each heel grows outboard only, so the toe line does not move. FT-SG-S still runs out to out of
the side strips. The heel's top bar was re-sized where the 130 pcf end of the soil band needed
it. Without that, `retaining_wall` goes OVER on heel flexure at the 130 pcf end: 1.10 at +6".
The variants in `variants.toml` are `sliding-s-heel-*` and `sliding-side-heel-*`.

| Variant | Staged | Dry | Perched | Flooded | Deep | Heel top bar (130 pcf d/c) | Concrete / stone / steel | Cost |
|---|---|---|---|---|---|---|---|---|
| S +6" | **1.584** | 2.026 | 1.644 | 1.791 | 1.652 | #5 @ 9" (0.833) | +0.47 cy / +2.09 cy / +140 lb | $580-1,040 |
| S +12" | 1.638 | 2.125 | 1.721 | 1.881 | 1.710 | #5 @ 7" (0.854) | +0.93 / +4.17 / +258 | $1,130-2,020 |
| S +18" | 1.691 | 2.206 | 1.787 | 1.956 | 1.761 | #6 @ 8" (0.884) | +1.39 / +6.25 / +452 | $1,780-3,170 |
| W2/E2 +6" | 1.566 | 1.976 | 1.606 | 1.748 | 1.617 | #5 @ 9" (0.833) | +0.74 / +3.31 / +72 | $720-1,330 |
| W2/E2 +12" | 1.600 | 2.020 | 1.641 | 1.791 | 1.637 | #5 @ 7" (0.854) | +1.47 / +6.62 / +197 | $1,510-2,760 |
| W2/E2 +18" | 1.602 | 2.060 | 1.674 | 1.830 | 1.655 | #6 @ 8" (0.884) | +2.21 / +9.92 / +381 | $2,380-4,330 |

**How the costs are built.**
- Concrete and stone are priced from `prices.toml`'s `[concrete] footing` and `[footing_bedding]`
  rows: S +6" is $240-375, for example.
- Steel is the bar-weight delta off the resolved rebar, priced at `prices.toml`'s #5 HDG rate of
  $1.30-2.15/lb.
- The widened cut is an **ESTIMATE**. `prices.toml` carries no excavation rate, because earthwork
  is a site allowance. The cut runs from the yard down to the soakaway bottom, 11.3' deep. It is
  priced at $30-70/cy for dig plus backfill: S +6" is 5.2 cy, $160-360.

**The footing's own rows still pass** (110 pcf shown; every variant is OK at 130 pcf with its bar).
- S +6/12/18:
  - heel flexure 0.720/0.737/0.764;
  - toe 0.700/0.669/0.650;
  - eccentricity 0.063/0.054/0.129;
  - bearing on the native 0.477/0.513/0.545;
  - overturning FS 3.55/4.11/4.64.
- W2/E2 +6/12/18:
  - eccentricity 0.511/0.344/0.233 (from 0.730);
  - native bearing 0.543/0.530/0.522.
- Heel soil does count in N'. The body reads it off the grown heel solid.

**Why S beats W2/E2 by more than two to one per yard.** Widening S adds heel soil and does not
widen the face the soil pushes on. Widening W2/E2 adds heel soil, but it also lengthens the
north-facing push on the two side faces. In the staged case, the E2 side at part height does not
fully cancel that push. Above about 12", the side heels stop paying (+12" gives 1.600, +18" gives
1.602). The governing stage moves onto the S face, which a side heel does not help.

**Other effects.**
- Winter tension stays 0.998 in every heel variant: the house side is W1/E1 and does not change.
- With the side heels, the spliced-joint winter row rises 0.391 to 0.620. It still passes.
- Corner delivery falls toward 0.
- The joint closure improves: 0.683 to 0.665 with S +6".
- `haus check` on S +6", S +12" and W2/E2 +12" shows 0 FAIL.
- The grown heel runs under the raised-garden apron's levelling pad, which is tangent to the
  footing edge today. The pad sits about 5' above the heel, in backfill, so nothing collides.
  `test_catlin_outdoor_structures`' "tangent, no overlap" statement would no longer hold.

**Reliability:** high. A wider heel is concrete and soil, inspected at the footing pour; there is
no field discipline to keep. **Buildability:** it is the same form line, moved out. There is one
bar change on one footing.

## Lever 3: thicker walls (+2")

The variants are `sliding-stem-14-retaining` (W2/E2/S) and `sliding-stem-14-all` (all five
walls). Each pour thickens about its axis, so the layout stays on the 12" grid, and the toe and
heel each lose 1".

| Variant | Staged | Dry | Perched | Flooded | Deep | Stem flexure | Winter | Added | Cost (`prices.toml`) |
|---|---|---|---|---|---|---|---|---|---|
| W2/E2/S 14" | 1.569 | 1.970 | 1.601 | 1.742 | 1.616 | **0.700** (from 0.865) | 1.000 | +2.86 cy wall | $1,450-2,600 |
| all five 14" | 1.591 | 1.995 | 1.621 | 1.766 | 1.630 | 0.700; column_support 0.578 to 0.467 | **1.019 OVER** | +4.03 cy | $2,040-3,660 |

**Effectiveness per cubic yard of added concrete (staged FS):**

| Option | Gain per cy |
|---|---|
| S heel | 0.117 |
| W2/E2 heel | 0.05 |
| 12" stone key | 0.11 |
| lean wall | 0.07 |
| 14" retaining stems | **0.014** |
| 14" all walls | **0.015** |

A thicker stem is the least efficient lever by a factor of eight. What it buys is stem flexure,
0.865 to 0.700, under the 0.85 cost-review trigger.

**Thickening W1/E1 does harm.**
- It adds weight to the house side, so winter tension goes OVER at 1.019.
- `haus check` gives 11 FAIL:
  - both deck ledgers run 1" into W1/E1;
  - the porch stair is buried in E1;
  - the winter row.
- Fixing the winter row alone would take one more #4 in each side run, about 30 lb, $40-65. The
  porch geometry would also have to move.

The 14" retaining-only variant is 0 FAIL.

## Lever 4: augered sonotube piers (the owner's idea)

### Capacity basis

The code text was read on UpCodes, Minnesota Building Code 2020 (IBC 2018 Ch. 18):

- **Table 1806.2, class 4** ("Sand, silty sand, clayey sand, silty gravel and clayey gravel (SW,
  SP, SM, SC, GM and GC)"): vertical 2,000 psf, lateral bearing **150 psf/ft below natural
  grade**, friction 0.25. Class 3 (GW and GP) is 3,000 / 200 / 0.35.
- **§1807.3.2.1**, the non-constrained case: `A = 2.34P/(S1 b)`, `d = 0.5A[1 + (1 + 4.36h/A)^0.5]`.
  - S1 is the allowable lateral bearing "based on a depth of one-third the depth of embedment".
  - d is "not over 12 feet ... for purpose of computing lateral pressure".
  - The repo's `engineering/pole_embedment.required_embedment_ft` is that solve. It is reused
    here, inverted for P.
- **§1806.3.1** lets lateral bearing combine with the friction of Table 1806.2.
- **§1806.3.3** lets the lateral value increase "by the tabular value for each additional foot of
  depth ... not greater than 15 times the tabular value".
- **§1806.3.4** doubles the lateral value only for poles "not adversely affected by a 1/2-inch
  ... motion at the ground surface due to **short-term** lateral loads". Earth pressure is
  sustained, so no doubling is taken.
- **§1807.3 itself states no deflection limit.** The only 1/2" is §1806.3.4's.

**What is credited.**
- Only the length below the stone is credited. Under S/W2/E2 the stone is 4.5' (42" bed plus the
  12" soakaway), from the footing underside at -10.12' to the native at -14.62'.
- The stone gives no lateral support. Placed #57 around a tube is loose, and an augered hole in
  it ravels.
- So h = 4.5', with the load at the footing underside. This is a free-head reading, which is
  conservative: the dowels are central and carry shear.

**Allowable P per pier.** "Conservative" takes S1 from the native surface, 150 x d/3.
"Depth-credited" takes §1806.3.3 from the -3'-4" yard, 150 x (11.29' + d/3), capped at 15x. The
second is an **interpretation** a building official or PE would have to accept: the stone and
backfill do restore the overburden on the native.

| Pier | d into native | Conservative | Depth-credited |
|---|---|---|---|
| 12" | 8' | 848 lb | 4,437 lb |
| 12" | 12' | 2,184 lb | 8,191 lb |
| 16" | 8' | 1,130 lb | 5,916 lb |
| 16" | 10' | 1,911 lb | 8,385 lb |
| 16" | 12' | 2,912 lb | 10,921 lb |

**The credit staged backfill needs.** A round pier resists in any direction, so FS = (mu N' +
n P) / H, re-searched over every stage the rule allows. The H/2 rule needs **6,323 lb** for
1.60, **10,792 lb** for 1.65 and **15,260 lb** for 1.70.

| Piers | Conservative: staged / dry / perched | Depth-credited: staged / dry / perched |
|---|---|---|
| 1 x 16" x 8' | 1.542 / 1.944 / 1.580 | 1.595 / 2.005 / 1.629 |
| 2 x 16" x 8' | 1.555 / 1.958 / 1.591 | **1.662** / 2.081 / 1.691 |
| 4 x 16" x 8' | 1.580 / 1.987 / 1.615 | 1.794 / 2.232 / 1.814 |
| 4 x 16" x 10' | 1.615 / 2.027 / 1.647 | 1.905 / 2.359 / 1.917 |
| 8 x 16" x 10' | **1.700** / 2.125 / 1.727 | 2.280 / 2.788 / 2.265 |

**Pier and dowel.** These are hand checks, the depth-credited 2 x 16" case being the worst.
- Pier shear: Vu = 1.6 x 5,916 = 9.5 kip, against phi Vc of about 15 kip (0.75 x 2 sqrt(4,000) x
  0.8 x 201 in²).
- Moment below the native surface: about P(h + 2z0/3), roughly 34 kip-ft service and 55 kip-ft
  factored. That wants a 16" cage of about 8 #6.
- Dowel into the footing: shear friction at mu 0.6, not roughened, the same basis as the
  fallback dowels in free body §15j.5. That needs Avf 0.35 in². The cage bars run up into the
  footing with hooks.
- At the conservative 1.1 kip, a 4 #5 cage is ample.

### Can pier resistance add to friction?

Not literally at service. Friction holds the body with almost no movement, and a pier only
pushes back once it has been pushed, so at FS 1.5 the pier carries next to nothing. What the
factor of safety asks is what resists once the body starts to move. Friction stays at its
plateau, and the pier comes up toward its allowable. §1806.3.1 combines the two without asking
for a compatibility check. The house's own convention reads the tabular value at about 1/4"
(free body §15g G8, from §1806.3.4's pairing of 2x with 1/2"). The question is whether the court
can take 1/4":

- **Staged backfill: yes.** The isolation boards are set *after* backfill (G8,
  `IsolationBoard.set_after_backfill`) and cut to the as-built slot. A 1/4" shift during backfill
  closes nothing. Piers may be combined with friction for the staged row, at a stated 1/4"
  movement.
- **Service rows after the boards are in** (perched, flooded, snow): no. The joint's residual
  closure is 0.125" less 0.0854" = **0.040"**. At 1/4" for the full tabular value, that is about
  16% of a pier's allowable, which is negligible. Piers should not be credited on those rows. The
  same question is open for the printed fallback lean wall. It is much stiffer than a slender
  pier in soil 4.5' down, but the engine credits it fully.

**Never under W1/E1.** A pier there adds restraint to the house side, and winter tension, at
0.998 today, goes over.

### Practical points

- **Sequence.** The native is only exposed while the dig is open at -14'-7 7/16".
  1. Auger the holes from the bed bottom before any stone goes in.
  2. Set sonotubes up through the future 4.5' of stone and pour the piers. That is a separate
     ticket and an extra visit.
  3. Place and plate the stone around the tubes. This is awkward: the plate cannot reach the tube,
     and a tube is easily knocked out of plumb.
  4. Cast the footing on the dowels.
- **Augering through placed #57 does not work.** The hole will not stand without casing.
- **A pier is a hard spot under a stone-bedded footing.** The 16" end bears about 2,800 lb on
  class 4, while the footing above wants to settle with the stone. Detail it, or accept local
  cracking.
- **Equipment, an ESTIMATE.**
  - A mini-excavator auger rents for about $250-450/day. It reaches 12-16" bits to 8-10' in GM,
    if the hole stays open.
  - Groundwater is unknown until the soil report. A cased hole or a drill rig would add about
    $1,500-3,000 of mobilisation.
- **Cost per pier, an ESTIMATE.** A 16" pier 12.5'-14.5' long is 0.65-0.78 cy. At `prices.toml`'s
  pier rate, $975-1,977/cy installed (`column:PIER_CONCRETE_12`), that is **$630-1,540 each**.
  Add the auger, a short-load fee and the extra visit: about $500-1,000 once.
- **Soil report dependence is double.** The native class sets the pier's capacity as well as the
  deep plane. A class 5 bed bottom (CL/ML, 100 psf/ft) cuts every pier figure by a third.

### Piers versus the shear key the owner was wary of

These are on the same body (mu 0.43). The key and the wall bear north only, so the directional
root is used. Submerged stone is taken at 0.6 for the flooded case, as in the engine's fallback.

| Option | Staged | Dry | Perched | Flooded | Concrete |
|---|---|---|---|---|---|
| Stone key 12" x 2'-0" x 25' under FT-SG-S | 1.717 | 2.185 | 1.776 | 1.857 | 1.85 cy |
| **Stone key 12" x 2'-6" x 25'** | **1.791** | 2.289 | 1.860 | 1.920 | 2.31 cy |
| Fallback lean wall (32,500 lb, formed before the stone) | 1.830 | 2.345 | 1.906 | ~1.95 | 4.2 cy lean |
| 2 x 16" x 8' piers, depth-credited | 1.662 | 2.081 | 1.691 | (not credited) | ~1.3 cy |
| 8 x 16" x 10' piers, conservative | 1.700 | 2.125 | 1.727 | (not credited) | ~6 cy |

The key bears on 25' of class-3 stone face, 200 psf/ft from the court floor. One key does what
eight conservative piers do, and it also helps the service rows. The owner's worry about the key
stands, though:
- A key formed in loose stone needs a permanent rigid form: rib lath, not plywood or EPS
  (§15f A').
- The lean wall avoids that by being formed in the open dig, at the cost of one extra pour.

**Piers are not recommended for sliding.** On the code reading that needs no interpretation,
they are the most expensive lever per unit of FS (about $400-750 per +0.01 staged). They help
only the staged row, which the free rule already fixes.

## Lever 5: anything else cheap in the free body

- **Credit W1/E1's heel soil by backfilling them with the court.** This is a hand estimate, not
  modelled.
  - Today W1/E1 stand empty until the porch braces them, and their heel soil is never credited.
  - If the porch beams go on first, W1/E1 can be filled with the rest.
  - Heel soil: 2 x 3' x 10.5' x (9.12' - 3.33' to the yard) x 110 = 40,124 lb, so +17,253 lb of
    friction at mu 0.43.
  - Staged at H/2 would be about (136,678 + 17,253) / 89,375 = **1.72**, and dry about 2.15, with
    no material.
  - Winter tension is unchanged: its house-side bound already takes that soil, to the stem top at
    130 pcf.
  - It needs two things: an engine basis change (crediting the soil) and a sequence change that
    costs schedule (porch framing before court backfill).
  - It is worth the owner's consideration. It is not graded here.
- **Lighter or drained backfill.** IBC Table 1610.1's at-rest 60 psf/ft is the same for every
  granular class (free body §2), so a better backfill buys nothing on the presumptive basis.
  - Lightweight fill (geofoam, foamed glass) is engineered, not tabular.
  - It also removes heel weight, which is a net loss for sliding.
  - A drained zone does nothing for the staged, dry or flooded rows (§15f). Not promising.
- **Let the walls move to active pressure.** The loop restrains the walls. At-rest is the stated
  basis (`AT_REST_IS_THE_GRADED_CASE`), and a permanent base restraint and an active wedge cannot
  both be claimed. This is a basis change, not a lever. Not taken.
- **A rougher bed.** Concrete cast on compacted #57 already interlocks. No table credits more
  than the specified or confirmed friction.
  - The soil report is itself the cheapest possible lever: each +0.01 of confirmed friction is
    about +0.036 staged. A report at 0.47 would give staged 1.67 with no change.
  - It cannot be banked in advance.
  - A report value above 1.00 FAILs `structural.soil_parameters_confirmed`, which is what holds
    winter tension at 0.998.

## The recommended combination

| | 3'-0" rule alone | **3'-0" rule + S heel +6"** | crew slips to 4'-0", with the heel |
|---|---|---|---|
| staged backfill | 1.721 | **1.787** | 1.683 |
| dry sliding | 1.930 | **2.026** | 2.026 |
| perched at H/2 | 1.568 | 1.644 | 1.644 |
| flooded | 1.702 | 1.791 | 1.791 |
| deep plane, soakaway full | 1.594 | 1.652 | 1.652 |
| winter tension | 0.998 | 0.998 | 0.998 |
| FT-SG-S heel flexure (130 pcf, #5 @ 9") | 0.810 | 0.833 | — |
| cost | $0 | about $580-1,040 (part ESTIMATE) | — |

**What the owner would draw for it.**
- AN-SG-BACKFILL reads: "no side more than four 8" lifts (2'-8") above another, filled W2, S, E2
  in turn".
- `RULE_FT = 3.0` in the engine, so the record grades the drawn rule.
- `south_heel_extension_in = 6` and `heel_top_spacing_in = 9` on FT-SG-S.
- The free body note §15e/§15h and `test_retaining_court`'s staged pins re-worked.

Winter tension needs nothing.

## Reproducing

The study's scratch scripts stay on branch `study-sliding`
(`houses/catlin/notes/court_sliding_levers_study/scratch/`). `RULE_FT` and the heel parameters
they drive are on main; the `sliding-*` variants in `variants.toml` reproduce levers 2 and 3
on top of the drawn heel.

## Findings for the engine (not fixed here)

- **`retaining_wall`'s INCOMPLETE summary is inverted when the 130 pcf end fails.** It says
  "checks at 130 pcf and does not at 110 pcf", and prints the 110 rows, all passing. The heel
  variants without a heavier bar showed it.
- **`resolve_wall_columns` crashes** (GEOS "Overlay input is mixed-dimension") when
  `sunken_garden.stem_thickness_in=14` moves the court axes, with an 86" footing. A sliver
  intersection returns lines. Filtering `piece` to its polygonal parts fixed it. The patch is not
  committed, because the `layer_thickness` variants do not need it.
