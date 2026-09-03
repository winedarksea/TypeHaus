# Rebar back-out — the reconciliation, and why the rate cut is NOT taken yet

**Status: the quantity ships, the dollar does not.** `takeoff/reinforcement.py` bills
reinforcing steel by the pound as of 2026-09-03. `[reinforcement]` in `prices.toml` is
present and **empty**, so every row lands in the estimate's `unpriced` list and the total
does not move by one cent. This note is the independent oracle the back-out has to pass
before those rates are filled in and the `[concrete]` / `[wall_structure]` $/cy rates are
cut — and **it does not pass yet.** §5 says exactly what has to be authored first.

Worked by hand in a separate pass, in the discipline every calculation in this repo is held
to: *a back-out that only agrees with itself is not verified.*

---

## 1. What is billed today

`haus takeoff houses/catlin`, section `reinforcement`. Lengths are **net** — laps and
splices ride in `[waste]`, chairs, bolsters, tie wire and tie hooks ride inside the $/lb
rate.

| scope | bar | coating | length | weight | elements |
|---|---|---|---:|---:|---|
| column | #3 | hdg-a767 | 187.6 LF | 70.5 lb | all ten cast columns, ties |
| column | #5 | hdg-a767 | 292.1 LF | 304.7 lb | all ten cast columns, verticals |
| footing | #4 | hdg-a767 | 302.2 LF | 201.9 lb | `FT-SG-W2/E2/S` longitudinal |
| footing | #6 | hdg-a767 | 1,088.0 LF | 1,634.2 lb | `FT-SG-W2/E2/S` mat, top + bottom |
| foundation wall | #4 | hdg-a767 | 881.4 LF | 588.8 lb | `W-SG-W2/E2/S` horizontal |
| foundation wall | #5 | hdg-a767 | 208.0 LF | 216.9 lb | the eight 8" basement runs |
| foundation wall | #6 | hdg-a767 | 768.0 LF | 1,153.5 lb | `W-SG-*` verticals |
| | | | | **4,171 lb** | **2.09 ton** |

**Nine rows became seven on 2026-09-03, and not one pound moved.** `PIER_CONCRETE_12` was
given a real `ConcreteSpec`, and `bar_coating` is a property of the POUR, so the 149 lb in
`PT-SG-COL` and the four breezeway piers went from black to A767 with it. **Every bar in this
house is now galvanized**, which is the 2026-09-02 owner call reaching the last exterior cage
that black steel was still specified for.

That is a durability result and not only a tidier table. Black and galvanized bar in
electrical contact inside one pour is a dissimilar-metal couple — an anode, a cathode, and an
electrolyte as soon as moisture reaches them — and the standard advice is to use one material
throughout rather than to detail the isolation. The couple did not exist here yet, because the
black cages happened to sit in unreinforced pours with nothing to lap to. It would have
existed the day somebody authored a dowel.

The derivation for a spaced bar is `length = area / spacing`, which is the whole of it: a
bar every `s` inches across a plane of area `A` is `A/s` of bar whichever way it runs,
because the run length cancels. Column cages are `count x height`; ties are
`ceil(height/spacing) x pi x (d - 2 cover - tie diameter)`.

## 2. The concrete it sits in

Taken by the machine's own filter rather than by hand, so it is reproducible and so a
later reader gets the same number: every `structural_solids` row of category
footing/slab/pad/column **whose STRUCTURE layer material is `concrete`**, plus every
`wall_structure` row of material `concrete`. `tests/test_rebar_backout.py` recomputes it.

```
column   PIER_CONCRETE_12                       0.82 cy
column   SUNKEN_GARDEN_COLUMN_12                1.25
footing  CATLIN_FOOTING_20                     10.46
footing  CATLIN_PIER_BASE_12                    0.57
footing  CATLIN_PORCH_FOOTING_84                5.71
footing  CATLIN_RETAINING_FOOTING_96           16.79
footing  FOOTING_FPSF_20                        1.73
pad      CATLIN_PIER_BASE_12                    0.26
slab     CATLIN_DECK_EPS_INT                   18.37
slab     CATLIN_GARAGE_STEP_6                   0.17
slab     CATLIN_GARDEN_SLAB                     5.75
slab     CATLIN_SLAB_FLOOR                     14.00
slab     GARAGE_SLAB_ON_GRADE                   5.27
slab     HP_PAD_ON_GRADE                        0.49
                                     solids   81.64 cy

SUNKEN_GARDEN_WALL                            30.21
CATLIN_BASEMENT_8                             17.55
CATLIN_BASEMENT_12                            10.67
GARAGE_ICF_6                                   8.82
FOUNDATION_WALL_12_INT                         5.25
the two garden curbs                           0.21
                                      walls   72.71 cy

                                      TOTAL  154.35 cy
```

**Two things the filter tells you that a hand count would have hidden.**

`CATLIN_DECK_EPS_INT` is in there at **18.37 cy** — the largest single pour in the house, and
one whose steel is billed at zero (§4 item 3). It is 12% of the concrete and it is exactly
the hole.

And **the denominator grew by 6.54 cy on 2026-09-03 without a cubic inch of concrete being
added to the building.** This filter can only count a pour whose assembly confirms it is
concrete, and three sets of real pours named no assembly at all: the two sunken-garden porch
strips `FT-SG-W1/E1` (5.71 cy), the two belled pier footings (0.57), and the four breezeway
pads (0.26). They now name `CATLIN_PORCH_FOOTING_84` and `CATLIN_PIER_BASE_12`, so they are
counted — and **the rebar ratio in §3 got worse, 28.2 to 27.0 lb/cy, which is the honest
direction.** What was found was more unreinforced concrete, not more steel. A gap that
flatters a ratio by hiding from it is the worst kind.

(Giving those 13 pours their mixes moved the estimate by **+$4.50** on a $15,867 footing
line — per-group rounding as one group split into three — and changed no quantity anywhere.
A specification change should cost nothing, and this one did.)

## 3. The test, and it FAILS

```
billed          4,171 lb / 154.35 cy   =  27.0 lb/cy
register ~5 t  10,000 lb / 154.35 cy   =  64.8 lb/cy
```

At a black-bar material price of $1.05-1.35/lb, **4,171 lb is $4,380-5,630.** The allowance
register (`plans/cost-options.md`, `prices.toml` `[allowances]`) carries rebar at
**$10,000-18,000**, and the plan's acceptance condition is explicit:

> If the new section's subtotal lands outside $10,000-18,000, either the takeoff or the rate
> is wrong.

It lands at less than half. **So the rate cut is not authorised, and this is the check
working rather than failing.** Cutting the full embedded rebar out of the $/cy rates while
billing 42% of the steel would make the estimate FALL by the difference — the "an unpriced
type drops from the BOM and the saving looks real when it is an artifact" hazard, arriving
from the other direction and for about $6,000.

27.0 lb/cy is also low on its own terms. A lightly reinforced residential foundation runs
40-80 lb/cy; the register's 64.8 sits inside that and this house — with three 10'-tall
retaining walls at `#6 @ 10"` both ways — has no business being below it.

## 4. Where the missing ~2.9 tons is

Every item here is a **modelling** gap, not a design one. The steel exists in the building;
the model has nowhere to state it, or states it in a form nothing can read.

1. **Horizontal temperature-and-shrinkage steel on the basement walls** — 8 runs of 8" wall
   and the 12" east wall, ~28 cy. None is authored anywhere in this house, and none was
   invented when the vertical steel was migrated to `ReinforcementSpec`: adding a schedule
   nobody wrote would put tonnage into the estimate on a judgement rather than a decision.
   At ACI 318-19 §11.6.1's rho 0.0020 this is roughly as much again as the vertical.
   **Probably the single largest item.**
2. **The garage ICF stems' vertical steel**, `GARAGE_ICF_6`, 8.82 cy. Stated only as
   `MasonrySpec.rebar_spacing = 16"` — a spacing with **no bar size**, which is not a
   readable schedule. That field is marked superseded and read by nothing.
3. **`SL-M-DECK`'s cap steel.** `CATLIN_DECK_EPS_INT`'s own source cites BuildDeck's table at
   "4,000 psi concrete and 60 ksi rebar", so there is rebar in the 4 5/8" cap. The model
   carries no rib width or spacing for the EPS T-beam form, so the flexural schedule cannot
   be derived and was not guessed.
4. **Dowels** — every wall-to-footing and column-to-wall lap. Deliberately not billed: a
   dowel's length is a lap into the pour below and nothing in this model carries it.
5. **`FT-SG-COL`/`FCOL` bells and the four breezeway pads** state no reinforcement. All six
   now name `CATLIN_PIER_BASE_12` and so have a mix, but no steel: the bells are graded as
   PLAIN concrete and pass (`notes/sunken_garden_piers.md` §5), which ACI 318-19 §14.1.4
   expressly permits in a footing. Correct rather than missing.
6. **`FT-SG-W1`/`E1`** and the 26 house/garage strip footings are plain by design (IRC Table
   R403.1), so they are genuinely zero and not a gap. `FT-SG-W1/E1` gained an assembly on
   2026-09-03 (`CATLIN_PORCH_FOOTING_84`) and remain deliberately unreinforced.

**Not a gap, and worth saying so:** the slabs-on-grade carry no mesh any more. Fibre replaces
it, and `[basis_notes] concrete` prices "wire mesh $0.20-0.50/SF" inside the $/cy rate.
**Mesh is not bar**, it stays in the rate, and it must not be swept out with the rebar when
the cut is finally made.

**That sentence used to name the wrong mix, and the correction is a real one.** It read
"(`CATLIN_INTERIOR_MIX`, `CATLIN_EXPOSED_MIX`)". `CATLIN_EXPOSED_MIX` carries MACRO-synthetic
fibre at 4 lb/cy, which ACI 544.4R does recognise as a mesh replacement for drying-shrinkage
and thermal crack control, so the garage and garden slabs were correctly described. The
interior mix carried MICRO-monofilament at 1.5 lb/cy, which targets plastic shrinkage in the
first hours, carries no post-crack residual and **replaces nothing** — `SL-B-FLOOR`, 14 CY of
basement slab on grade, had neither mesh nor a fibre that does the job the mesh was deleted
for. Split into `CATLIN_POLISHED_MIX` (micro, `SL-M-DECK`) and `CATLIN_INTERIOR_SLAB_MIX`
(macro, `SL-B-FLOOR`) on 2026-09-03. Control joints are still required on that slab and are
not modelled anywhere.

## 5. What has to happen before the cut

In order, and the first is most of the money:

- author horizontal T&S steel on the basement walls (and the retaining walls already have
  it: `#4 @ 8"`, `_RET_STEM_STEEL`);
- give `GARAGE_ICF_6`'s stems a real `ReinforcementSpec` with a bar size, and retire
  `MasonrySpec.rebar_spacing`;
- decide `SL-M-DECK` — either author the BuildDeck schedule, or record the cap's steel as a
  deliberate hole with a dollar figure attached so the back-out can subtract it explicitly;
- **re-run §3.** If the billed subtotal lands inside $10,000-18,000, cut the rates. If it
  does not, this note says why before anyone touches a dollar.

Then, and only then, the cut itself — in ONE commit, per the standing condition
`prices.toml` states in two places and `plans/cost-options.md` in a third:

- **cut the MATERIAL half only.** `[basis_notes] concrete` is explicit that material is an
  independently sourced number (Twin Cities ready-mix $180-200/cy plus rebar) and that
  **labour is the residual**. Subtracting a rebar placer's wage out of a residual is
  judgement dressed as arithmetic; subtracting a sourced rebar material price out of a
  sourced material price is arithmetic. Hence `[basis] reinforcement = "material"`, on the
  doctrine `[hardware]` already uses — the labour to drive a screw is inside the `[framing]`
  labour rate;
- flip `[rebar_inclusive] concrete` and `wall_structure` to `false` in the same commit.
  Until they are, `cli/price_file._check_rebar_not_double_billed` **refuses to load a
  priced `[reinforcement]` table at all** — the standing condition is enforced now, not
  merely written down.

## 6. Proving it, when the day comes

Three independent mechanical checks. Two are already runnable.

1. **Nothing else may move.** `scripts/price_delta.py <base> <head>` diffs every section's
   subtotal between two refs in throwaway worktrees. Acceptance:
   `Δconcrete + Δwall_structure + Δreinforcement ~= 0`, **and every other section's Δ is
   exactly 0.00.** The second clause is the real protection.
   *Already earned its keep:* run against `eb740e9a`, it reported drainage, edge_trim,
   hardware, member_protection and railings all moving — correctly, and not from this work.
   It bisects to `f149aedf`, the first commit that staged `params/sunken_garden.py` and so
   carried another session's `joist_cantilever_in` 6" -> 9" balcony change. From `f149aedf`
   forward the report is clean.
2. **Quantities must be identical.** Same two refs, `haus takeoff --csv`, `diff`. The only
   permitted new rows are `reinforcement:*`. Anything else moving means an assembly-naming
   pass silently re-grouped a pour.
3. **This note.** `tests/test_rebar_backout.py` pins §1's tonnage and §3's verdict, so the
   day the tonnage rises past the gate a test says so out loud.
