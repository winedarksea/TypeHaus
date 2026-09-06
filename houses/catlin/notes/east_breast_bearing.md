# RM-M-LIVING fireplace surround — bearing, and the floor it passes through

**House:** catlin
**Structure:** `W-M-FIRE` (the 3 5/8" white-brick wythe), `FIREPLACE_BRICK_WYTHE` (its
assembly), `W-B-E1` (the 12" pour it stands on), `FS-M-EAST` (the floor it passes through),
`FO-M-FIRE` (the opening in that floor), `EQ-M-FIREPLACE` (the appliance in it),
`SB-M-FIRE-MANTEL` (the shelf that caps it).
**Written:** 2026-09-06, by hand.
**Oracle for:** no engine calculation — **this note is the whole basis.** Nothing in
`typehaus/engineering/` grades a masonry surround, and nothing in `haus check` looks at this
detail at all (§6). The geometry it rests on is pinned only by the model itself.
**Companions:** `notes/sunken_garden_veneer_beam.md` — the house's other freestanding brick
wythe, and the pattern this note follows; `notes/mixed_deck_movement_joint.md` — the
FS-M-EAST / SL-M-DECK boundary this opening sits south of.
**What is asked of the reviewer:** §4. The load path in §2-§3 is trivial by design; the
floor opening in §4 is the only place where somebody has to open a manufacturer's book.

> ⚠ **The brick does not bear on the floor, and the whole design depends on that.** It
> starts on `W-B-E1`'s pour at −1'-1 7/16" and rises **through** `FS-M-EAST`. If anyone
> "simplifies" this by starting the wythe on the subfloor, §3's 50 plf limit is exceeded
> roughly four-fold and the detail needs an engineer. That change would look like a
> one-line edit to `Wall.base_elevation` and it is not.

> ⚠ **These are 11 7/8" I-joists, and IRC R502.10 is a sawn-lumber rule.** §4's opening is
> under 4'-0" and would be prescriptive in sawn lumber. It is not sawn lumber. Cutting and
> heading I-joists follows the **manufacturer's** hole-and-header tables and needs their
> specified hangers and web stiffeners. **This must be confirmed against the joist maker's
> literature before framing**, and it must be on the drawing.

> ⚠ **Keep the appliance ELECTRIC.** `EQ-M-FIREPLACE` is `EQ-T-FIREPLACE-EL`, a 1.5 kW
> electric unit. IRC **R1001.2** requires a *masonry fireplace* to have a 12" concrete
> footing on undisturbed earth below the frost line, with **no wood-floor exception**.
> Keeping it electric keeps R1001 off the table entirely. Put a real firebox in this
> surround and no part of this note survives.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| wythe thickness | `FIREPLACE_BRICK_WYTHE`, one STRUCTURE layer | **3 5/8"** |
| face plane (x) | authored axis 35'-1 11/16" less half the wythe | **34'-11 7/8" = 419.875"** |
| back plane (x) | face + 3 5/8" | **35'-3 1/2" = 423.5"** |
| room finish face (x) | `W-M-E1` interior gwb | 35'-5 3/8" = 425.375" |
| gap behind the wythe | 425.375 − 423.5 | 1 7/8" (ties, and the firebox's framing) |
| panel width (y) | 29 1/2" masonry opening + 8" each side | **45 1/2"**, y 81.25"–126.75" |
| base | `W-B-E1` bearing seat | **−1'-1 7/16" = −13.4375"** |
| top | mantel underside, modular course 24 | **5'-4" = 64"** |
| height | 64 − (−13.4375) | **77 7/16"** |
| `W-B-E1` pour (x) | `CATLIN_BASEMENT_12`, outer face on the 36'-0" line | **420"–432"** |

**The whole footprint stands over the pour, bar 1/8".** The wythe runs 419.875"–423.5" and
the pour 420"–432"; the 0.125" of brick west of the pour's inner face is a mortar line, not
a cantilever. This is the reason the surround is minimal: the earlier 10 3/8"-deep breast
put its centroid 9" inboard of the pour and fully onto the joists. **Minimalism here is not
an aesthetic, it is what puts the brick on the foundation.**

## 2. The load, and where it goes

| term | working | value |
|---|---|---|
| panel volume | 45.5 × 77.4375 × 3.625 in³ = 12,772 in³ | **7.39 ft³** |
| masonry density | `white-brick`, 1,920 kg/m³ | **119.9 pcf** |
| panel weight | 7.39 × 119.9 | **≈ 886 lb** |
| as a line load | 886 lb ÷ 3.79 ft of panel | **≈ 234 plf** |

That 234 plf goes **brick → mortar bed → `W-B-E1`'s 12" pour → `FT-B-*` → soil.** There is
no wood in the path. `W-B-E1` is a 12" wall carrying `SL-M-DECK`'s 414 SF cast edge; 234 plf
on 12" of concrete is 0.16 psi of added bearing and is not worth a calculation.

**Why the east wall was already the right wall.** `params/main_deck.py` frames `FS-M-EAST`
with `JoistSpec(direction="x", bearing_refs=("W-B-CS", "W-B-CS3", "W-B-E1"))` — the joists
span **east–west and bear on `W-B-E1`**. Load standing near that wall is carried in near
direct shear rather than in bending. The sensitivity, for a point load at distance *a* from
a support on a simply supported span *L* (resolved joist span 214 3/4", east bearing face at
x = 430.75"):

| a | a/L | induced midspan moment `2a/L` | midspan deflection `(a/L)(3 − 4(a/L)²)` |
|---|---|---|---|
| 9 1/16" (this brick's centroid) | 0.042 | **8.4%** | **12.6%** |
| 9 3/8" (the deeper breast that was rejected) | 0.043 | 8.7% | 13.0% |
| L/2 (mid-room) | 0.500 | 100% | 100% |

Both rows are hypothetical: **as built, none of the brick's weight reaches a joist at all.**
The table is here because it is the argument for choosing this wall, and because it bounds
what an accidental floor-borne fraction would cost.

## 3. The 50 plf question does not arise

`preferences.toml` `max_guard_dead_load_on_wood_plf` is **50 plf**. A floor-borne full-brick
surround of this size would run:

| case | working | value |
|---|---|---|
| full panel on wood | 886 lb ÷ 3.79 ft | 234 plf — **4.7×** |
| only the part above the floor | 45.5 × 64 × 3.625 in³ = 6.11 ft³ × 119.9 ÷ 3.79 ft | 193 plf — **3.9×** |

Either way it fails by a wide margin, which is exactly why the brick starts on the pour.
**Result: zero brick dead load on wood, and no engineered item.**

## 4. Going around the joists — the one thing a reviewer must check

The joists' **ends** bear on the mudsill at x 426"–431 1/2"; inboard of 426" they are in
span. The brick face at x = 419.875" cuts them short of that bearing, so over the panel's
45 1/2" of y **no joist can reach its east support** and the strip from the brick face to the
rim is joist-free. Three or four joists are cut and headed. `FO-M-FIRE` is that hole:

| edge | x or y | what carries it |
|---|---|---|
| west | x = 34'-10 1/8" | the header — a 2-ply 1 3/4" × 11 7/8" LVL, axis on the edge, so its **east face lands exactly on the brick face** |
| east | x = 35'-10 3/4" | `FS-M-EAST`'s rim (1 1/4" × 11 7/8", axis 35'-11 3/8"): the trimmers die on its inboard face |
| north / south | y = 126 3/4" / 81 1/4" | a **doubled** trimmer each side |
| bearing | — | `bearing_refs=("W-B-E1",)` — the east edge stands over the pour, so no second header is emitted there |

**At 3'-9 1/2" the opening is under 4'-0"**, which is the threshold in IRC R502.10 for a
single header on single trimmers — and the resolver has given it doubled trimmers anyway.
**But R502.10 governs sawn lumber and these are I-joists.** The cut ends need the joist
maker's specified hangers and **web stiffeners**, and the header size must come off *their*
table, not off R502.10. That is a published table rather than a PE stamp, so this stays a
prescriptive detail — but it is the one place in this design where somebody has to open a
manufacturer's book, and it should be named in the drawing note.

**Timing is the real cost.** The opening, the hangers, the stiffeners and the coordination
between mason and framer are all cheap **only while the basement ceiling is open**, exactly
as `params/main_deck.py` already says of other work in this bay.

**Below, in `RM-B-GYM`, no brick shows** — the wythe is entirely inside the floor depth and
the gym's ceiling plane is under the joists — **but the ceiling is not untouched.**
`FS-M-EAST.ceiling_below` is 5/8" gypsum and this opening cuts it: the model draws the gym's
ceiling boundary stopping at the header, and three section goldens
(`detail_stack_width_change`, `detail_storey_stack-rim`, `detail_wall_foundation`, all
`CATLIN_BASEMENT_12`/`CATLIN_EXT_2X6`) were re-blessed on 2026-09-06 to record it. What is
built is the board closed back around the 3 5/8" wythe, which is trim work in a finished
room if it is left until after the mason.

## 5. What is NOT graded here

- **The ties.** The wythe stands 1 7/8" off `W-M-E1`'s gwb and must be tied back to its
  studs. Nothing here designs that tie. At 45 1/2" × 6'-5" of panel it is a light and
  ordinary condition, unlike `W-B-BRICK`'s ~10" reach through foam
  (`notes/sunken_garden_veneer_beam.md` §5.1), but it is not designed.
- **The lintel** over the 29 1/2" × 20 3/8" firebox opening — a rowlock course or a steel
  angle. It carries 11 5/8" of brick to the mantel and nothing else. Not sized here.
- **The mantel's supports.** `SB-M-FIRE-MANTEL` is a 45 1/2" × 10" × 2 1/4" walnut board
  projecting 4 1/2" proud. Concealed steel let into the coursing before it is laid; not
  designed here, and it cannot be added afterwards.
- **Differential movement** between a brick panel bearing on concrete and the wood floor it
  passes through. The floor shrinks and the brick does not. The 1 7/8" behind the wythe and
  a soft joint at the mantel are where that goes; no calculation is offered.
- **Seismic / out-of-plane.** Not considered. SDC A, an interior panel 6'-5" tall.

## 6. Nothing in `haus check` looks at any of this

Stated positively, because a clean report here is silence and not a verdict:

- `structural.masonry_guard_bearing` (`checks/structural/guards.py`) walks **`Wall.guard`
  walls only**. `W-M-FIRE` is not a guard, so that check never sees it.
- `checks/code/mn_residential/profile.py` **explicitly disclaims IRC R1001–R1004**, the
  fireplace and chimney chapter.
- `building_science.condensation` screens on `any(layer.function == "cladding")`;
  `FIREPLACE_BRICK_WYTHE`'s single layer is STRUCTURE, so it is out of the Glaser scope —
  correctly, since this is an interior panel and not an envelope assembly.
- `structural.floor_opening_header` **does** grade `FO-M-FIRE`, and passes. It is the only
  automatic opinion anything in the engine has about this detail, and it is about the floor,
  not about the brick.
- `structural.member_interference` also grades it, and **did FAIL four times** while the
  opening ran to the 36'-0" wall line and drove all four trimmers through the rim. That is
  what set the east edge at 35'-10 3/4". It is worth knowing the check caught a real
  framing error here.

**A 0-FAIL report on this house does not mean this detail was checked. It means nothing
looked.**

## Sources

- IRC 2018 §R502.10 — framed openings in floors: header and trimmer requirements, and the
  4'-0" threshold above which they double.
- IRC 2018 §R1001.2 — masonry fireplace footings: 12" of concrete on undisturbed earth,
  below the frost line, with no wood-floor exception.
- IRC 2018 §R703.8.4 — masonry veneer drainage cavity (cited for contrast: this is an
  *interior* panel and takes no cavity).
- TMS 402 — anchored masonry veneer ties (§5, not designed here).
- NFPA 211 — chimneys, fireplaces, vents and solid-fuel appliances. Cited to record that an
  electric firebox is **outside** its scope, which is why no hearth extension is drawn.
- Amantii BI-30-XTRASLIM (BI-X190030-1) installation manual, 2022 CSA revision — rough
  opening 29 × 20 3/8 × 4 1/2", 120 V / 1500 W / 5,118 Btu/h, hardwireable, mantel 4" from
  the trim, combustible facing allowed, no floor clearance and no air-intake slot. **The
  pre-2022 manual under the same model number states 1465 W / 5,000 Btu/h and contains no
  mantel and no hardwire section at all** — confirm which revision ships.
- Joist manufacturer's I-joist framing guide — **the document §4 requires and this note does
  not have.** Web stiffeners, hanger schedule and header table for a cut 11 7/8" I-joist.
